#!/bin/bash
# Command execution engine for PruneJuice

# Source required libraries
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$SCRIPT_DIR/database.sh"
source "$SCRIPT_DIR/yaml-parser.sh"
source "$SCRIPT_DIR/artifacts.sh"

# Execution configuration
EXECUTION_LOG_LEVEL="${PRUNEJUICE_LOG_LEVEL:-INFO}"
STEP_TIMEOUT="${PRUNEJUICE_STEP_TIMEOUT:-300}"  # 5 minutes default per step

# Built-in step implementations - using case statement for bash 3.x compatibility
get_builtin_step_function() {
    local step="$1"
    case "$step" in
        setup-environment) echo "setup_environment_step" ;;
        validate-prerequisites) echo "validate_prerequisites_step" ;;
        create-worktree) echo "create_worktree_step" ;;
        start-session) echo "start_session_step" ;;
        store-artifacts) echo "store_artifacts_step" ;;
        cleanup) echo "cleanup_step" ;;
        *) echo "" ;;
    esac
}

# Logging functions
log_info() {
    if [[ "$EXECUTION_LOG_LEVEL" =~ ^(DEBUG|INFO)$ ]]; then
        echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
    fi
}

log_debug() {
    if [[ "$EXECUTION_LOG_LEVEL" == "DEBUG" ]]; then
        echo "[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
    fi
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
}

log_warn() {
    echo "[WARN] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
}

# Execute a single command with full lifecycle management
execute_command() {
    local yaml_file="$1"
    local project_path="$2"
    shift 2
    local command_args=("$@")
    
    log_info "Starting command execution: $(basename "$yaml_file" .yaml)"
    
    # Validate command file
    if ! validate_command_yaml "$yaml_file"; then
        log_error "Command validation failed: $yaml_file"
        return 1
    fi
    
    # Validate arguments
    if ! validate_command_arguments "$yaml_file" "${command_args[@]}"; then
        log_error "Argument validation failed"
        return 1
    fi
    
    # Parse command metadata
    local command_data
    command_data=$(parse_command_yaml "$yaml_file")
    
    # Extract metadata using eval (secure since we control the input)
    eval "$command_data"
    
    log_debug "Command: $NAME"
    log_debug "Description: $DESCRIPTION"
    log_debug "Steps: $STEPS"
    
    # Create session ID and artifacts directory
    local session_id
    session_id="$(basename "$project_path")-$(date +%s)-$$"
    
    local artifact_dir
    artifact_dir=$(create_session_artifacts "$project_path" "$session_id" "$NAME")
    
    # Start event tracking
    local event_id
    event_id=$(start_event "$NAME" "$project_path" "" "$session_id" "$artifact_dir" "{}")
    
    log_info "Event ID: $event_id, Session ID: $session_id"
    
    # Set up execution environment
    local execution_env_file="$artifact_dir/temp/execution-env.sh"
    mkdir -p "$(dirname "$execution_env_file")"
    
    # Export execution context
    cat > "$execution_env_file" << EOF
export PRUNEJUICE_EVENT_ID="$event_id"
export PRUNEJUICE_SESSION_ID="$session_id"
export PRUNEJUICE_PROJECT_PATH="$project_path"
export PRUNEJUICE_ARTIFACT_DIR="$artifact_dir"
export PRUNEJUICE_COMMAND_NAME="$NAME"
export PRUNEJUICE_WORKING_DIR="${WORKING_DIRECTORY:-$project_path}"
EOF
    
    # Add command arguments to environment
    for arg in "${command_args[@]}"; do
        if [[ "$arg" == *"="* ]]; then
            local key value
            key=$(echo "$arg" | cut -d= -f1)
            value=$(echo "$arg" | cut -d= -f2-)
            echo "export PRUNEJUICE_ARG_${key^^}=\"$value\"" >> "$execution_env_file"
        fi
    done
    
    # Add command environment variables
    if [[ "$ENVIRONMENT" != "{}" ]]; then
        echo "$ENVIRONMENT" | yq eval -o=shell 'to_entries[] | "export " + .key + "=\"" + .value + "\""' >> "$execution_env_file" 2>/dev/null || true
    fi
    
    source "$execution_env_file"
    
    # Execute steps
    local step_count=0
    local failed_step=""
    local overall_exit_code=0
    
    while IFS= read -r step; do
        if [[ -n "$step" && "$step" != "null" ]]; then
            ((step_count++))
            log_info "Executing step $step_count: $step"
            
            if ! execute_step "$step" "$artifact_dir" "$step_count"; then
                failed_step="$step"
                overall_exit_code=1
                log_error "Step failed: $step"
                break
            fi
            
            log_info "Step completed: $step"
        fi
    done < <(echo "$STEPS" | yq eval '.[]' -)
    
    # Determine final status
    local final_status
    if [[ $overall_exit_code -eq 0 ]]; then
        final_status="completed"
        log_info "Command completed successfully"
    else
        final_status="failed"
        log_error "Command failed at step: $failed_step"
    fi
    
    # End event tracking
    end_event "$event_id" "$final_status" "$overall_exit_code" "$failed_step"
    
    # Store final execution log
    local execution_log="$artifact_dir/logs/execution.log"
    cat > "$execution_log" << EOF
Command: $NAME
Description: $DESCRIPTION
Project: $project_path
Session: $session_id
Event ID: $event_id
Status: $final_status
Exit Code: $overall_exit_code
Steps Executed: $step_count
Failed Step: $failed_step
Started: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Artifact Directory: $artifact_dir
EOF
    
    store_artifact "$event_id" "log" "$execution_log" "execution.log" "Command execution log"
    
    return $overall_exit_code
}

# Execute a single step
execute_step() {
    local step="$1"
    local artifact_dir="$2"
    local step_number="$3"
    
    local step_log="$artifact_dir/logs/step-$step_number-$step.log"
    local step_start_time
    step_start_time=$(date +%s)
    
    log_debug "Starting step: $step"
    
    # Check if it's a built-in step
    local step_function
    step_function=$(get_builtin_step_function "$step")
    
    if [[ -n "$step_function" ]]; then
        log_debug "Executing built-in step: $step_function"
        
        # Execute built-in step with logging
        if timeout "$STEP_TIMEOUT" bash -c "$step_function" &> "$step_log"; then
            local exit_code=0
        else
            local exit_code=$?
        fi
    else
        # Look for custom step script
        local step_script_locations=(
            "$PRUNEJUICE_PROJECT_PATH/.prj/steps/$step.sh"
            "$(dirname "${BASH_SOURCE[0]}")/../steps/$step.sh"
            "$HOME/.prunejuice/steps/$step.sh"
        )
        
        local step_script=""
        for location in "${step_script_locations[@]}"; do
            if [[ -f "$location" && -x "$location" ]]; then
                step_script="$location"
                break
            fi
        done
        
        if [[ -n "$step_script" ]]; then
            log_debug "Executing custom step script: $step_script"
            
            # Execute custom step with environment and logging
            if timeout "$STEP_TIMEOUT" bash -c "source '$execution_env_file' && '$step_script'" &> "$step_log"; then
                local exit_code=0
            else
                local exit_code=$?
            fi
        else
            log_error "Step not found: $step"
            echo "Step not found: $step" > "$step_log"
            local exit_code=127
        fi
    fi
    
    local step_end_time
    step_end_time=$(date +%s)
    local step_duration=$((step_end_time - step_start_time))
    
    # Add step timing to log
    echo "" >> "$step_log"
    echo "=== Step Metadata ===" >> "$step_log"
    echo "Step: $step" >> "$step_log"
    echo "Duration: ${step_duration}s" >> "$step_log"
    echo "Exit Code: $exit_code" >> "$step_log"
    echo "Timeout: ${STEP_TIMEOUT}s" >> "$step_log"
    
    log_debug "Step completed: $step (${step_duration}s, exit code: $exit_code)"
    
    return $exit_code
}

# Built-in step implementations

setup_environment_step() {
    log_info "Setting up execution environment"
    
    # Ensure required directories exist
    mkdir -p "$PRUNEJUICE_ARTIFACT_DIR"/{logs,outputs,temp}
    
    # Log environment info
    echo "Environment setup completed at $(date)" > "$PRUNEJUICE_ARTIFACT_DIR/temp/environment.txt"
    echo "Working directory: $PWD" >> "$PRUNEJUICE_ARTIFACT_DIR/temp/environment.txt"
    echo "Project path: $PRUNEJUICE_PROJECT_PATH" >> "$PRUNEJUICE_ARTIFACT_DIR/temp/environment.txt"
    echo "Session ID: $PRUNEJUICE_SESSION_ID" >> "$PRUNEJUICE_ARTIFACT_DIR/temp/environment.txt"
    
    return 0
}

validate_prerequisites_step() {
    log_info "Validating prerequisites"
    
    local prereq_log="$PRUNEJUICE_ARTIFACT_DIR/temp/prerequisites.txt"
    
    # Check required tools
    local required_tools=("git" "sqlite3")
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            echo "✓ $tool: $(command -v "$tool")" >> "$prereq_log"
        else
            echo "✗ $tool: NOT FOUND" >> "$prereq_log"
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        return 1
    fi
    
    return 0
}

create_worktree_step() {
    log_info "Creating worktree (delegating to plum)"
    
    # This would delegate to the plum tool
    if command -v "$PRUNEJUICE_PROJECT_PATH/scripts/plum-cli.sh" &> /dev/null; then
        "$PRUNEJUICE_PROJECT_PATH/scripts/plum-cli.sh" create-worktree
    else
        log_warn "Plum CLI not found, skipping worktree creation"
        return 0
    fi
}

start_session_step() {
    log_info "Starting session (placeholder for pots integration)"
    
    # This would delegate to the pots tool when implemented
    create_session "$PRUNEJUICE_SESSION_ID" "$PRUNEJUICE_PROJECT_PATH" "" ""
    
    return 0
}

store_artifacts_step() {
    log_info "Storing artifacts"
    
    # This step is typically called automatically, but can be used to force artifact storage
    local artifacts_stored=0
    
    # Store any outputs in the working directory
    if [[ -d "$PRUNEJUICE_WORKING_DIR/outputs" ]]; then
        for output_file in "$PRUNEJUICE_WORKING_DIR/outputs"/*; do
            if [[ -f "$output_file" ]]; then
                store_artifact "$PRUNEJUICE_EVENT_ID" "output" "$output_file" "$(basename "$output_file")" "Command output"
                ((artifacts_stored++))
            fi
        done
    fi
    
    log_info "Stored $artifacts_stored artifacts"
    return 0
}

cleanup_step() {
    log_info "Cleaning up temporary files"
    
    # Clean up temp directory but preserve logs and outputs
    if [[ -d "$PRUNEJUICE_ARTIFACT_DIR/temp" ]]; then
        find "$PRUNEJUICE_ARTIFACT_DIR/temp" -name "*.tmp" -delete
        find "$PRUNEJUICE_ARTIFACT_DIR/temp" -type f -mmin +60 -delete  # Files older than 1 hour
    fi
    
    return 0
}

# List available commands
list_available_commands() {
    local commands_dir="$1"
    
    if [[ -d "$commands_dir" ]]; then
        list_commands "$commands_dir"
    else
        echo "No commands directory found: $commands_dir"
        return 1
    fi
}

# Get command help
show_command_help() {
    local yaml_file="$1"
    
    if [[ ! -f "$yaml_file" ]]; then
        echo "Command file not found: $yaml_file"
        return 1
    fi
    
    generate_command_help "$yaml_file"
}

# Main execution function with error handling
main_execute() {
    local command_name="$1"
    local project_path="$2"
    shift 2
    local args=("$@")
    
    # Find command file
    local commands_dir="$project_path/.prj/commands"
    local command_file="$commands_dir/$command_name.yaml"
    
    if [[ ! -f "$command_file" ]]; then
        # Try global commands
        command_file="$(dirname "${BASH_SOURCE[0]}")/../commands/$command_name.yaml"
        
        if [[ ! -f "$command_file" ]]; then
            log_error "Command not found: $command_name"
            return 1
        fi
    fi
    
    # Execute command with error handling
    if execute_command "$command_file" "$project_path" "${args[@]}"; then
        log_info "Command executed successfully: $command_name"
        return 0
    else
        log_error "Command execution failed: $command_name"
        return 1
    fi
}