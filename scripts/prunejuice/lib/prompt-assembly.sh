#!/bin/bash
# Prompt assembly framework for Claude Code integration

# Source required libraries
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$SCRIPT_DIR/database.sh"
source "$SCRIPT_DIR/artifacts.sh"

# Prompt configuration
PROMPTS_DIR="${PRUNEJUICE_PROMPTS_DIR:-$HOME/.prunejuice/prompts}"
TEMPLATES_DIR="${PRUNEJUICE_TEMPLATES_DIR:-$(dirname "$SCRIPT_DIR")/templates}"

# Prompt types - using case statement for bash 3.x compatibility
VALID_PROMPT_TYPES="analysis implementation review planning debugging documentation"

# Get prompt type description
get_prompt_description() {
    local type="$1"
    case "$type" in
        analysis) echo "Code analysis and investigation prompts" ;;
        implementation) echo "Implementation and coding prompts" ;;
        review) echo "Code review and quality assurance prompts" ;;
        planning) echo "Planning and design prompts" ;;
        debugging) echo "Debugging and troubleshooting prompts" ;;
        documentation) echo "Documentation generation prompts" ;;
        *) echo "Unknown prompt type" ;;
    esac
}

# Initialize prompt system
init_prompt_system() {
    mkdir -p "$PROMPTS_DIR"/{templates,sessions,history}
    
    # Create default prompt templates if they don't exist
    create_default_templates
}

# Create default prompt templates
create_default_templates() {
    local templates_needed=(
        "analysis-base"
        "implementation-base"
        "review-base"
        "planning-base"
        "debugging-base"
    )
    
    for template in "${templates_needed[@]}"; do
        local template_file="$PROMPTS_DIR/templates/$template.md"
        if [[ ! -f "$template_file" ]]; then
            create_template "$template"
        fi
    done
}

# Create a specific template
create_template() {
    local template_name="$1"
    local template_file="$PROMPTS_DIR/templates/$template_name.md"
    
    case "$template_name" in
        "analysis-base")
            cat > "$template_file" << 'EOF'
# Code Analysis Task

## Context
Project: {{project_name}}
Session: {{session_id}}
Command: {{command_name}}

## Analysis Request
{{analysis_request}}

## Codebase Context
{{codebase_context}}

## Files to Analyze
{{files_list}}

## Focus Areas
{{focus_areas}}

## Expected Deliverables
- Detailed analysis report
- Findings and recommendations
- Potential issues identified
- Improvement suggestions

## Additional Context
{{additional_context}}
EOF
            ;;
        "implementation-base")
            cat > "$template_file" << 'EOF'
# Implementation Task

## Context
Project: {{project_name}}
Session: {{session_id}}
Command: {{command_name}}

## Implementation Request
{{implementation_request}}

## Requirements
{{requirements}}

## Existing Code Context
{{existing_context}}

## Architecture Constraints
{{architecture_constraints}}

## Expected Deliverables
- Working implementation
- Tests (if applicable)
- Documentation updates
- Code that follows project conventions

## Additional Notes
{{additional_notes}}
EOF
            ;;
        "review-base")
            cat > "$template_file" << 'EOF'
# Code Review Task

## Context
Project: {{project_name}}
Session: {{session_id}}
Command: {{command_name}}

## Review Scope
{{review_scope}}

## Files Changed
{{changed_files}}

## Review Focus Areas
{{focus_areas}}

## Quality Criteria
- Code quality and maintainability
- Security considerations
- Performance implications
- Testing coverage
- Documentation completeness

## Context and Background
{{background_context}}

## Expected Deliverables
- Comprehensive review report
- Issue prioritization
- Recommendations for improvement
- Approval/rejection with reasoning
EOF
            ;;
        "planning-base")
            cat > "$template_file" << 'EOF'
# Planning Task

## Context
Project: {{project_name}}
Session: {{session_id}}
Command: {{command_name}}

## Planning Objective
{{planning_objective}}

## Current State
{{current_state}}

## Desired End State
{{desired_state}}

## Constraints and Requirements
{{constraints}}

## Stakeholders and Impact
{{stakeholders}}

## Expected Deliverables
- Detailed implementation plan
- Task breakdown and timeline
- Risk assessment
- Resource requirements
- Success criteria

## Additional Information
{{additional_info}}
EOF
            ;;
        "debugging-base")
            cat > "$template_file" << 'EOF'
# Debugging Task

## Context
Project: {{project_name}}
Session: {{session_id}}
Command: {{command_name}}

## Problem Description
{{problem_description}}

## Error Messages/Symptoms
{{error_messages}}

## Steps to Reproduce
{{reproduction_steps}}

## Expected vs Actual Behavior
**Expected:** {{expected_behavior}}
**Actual:** {{actual_behavior}}

## Environment Information
{{environment_info}}

## Recent Changes
{{recent_changes}}

## Debugging Approach
- Root cause analysis
- Step-by-step investigation
- Proposed solution
- Testing strategy

## Additional Context
{{additional_context}}
EOF
            ;;
    esac
    
    echo "Created template: $template_file"
}

# Assemble a prompt from template and context
assemble_prompt() {
    local template_name="$1"
    local session_id="$2"
    local project_path="$3"
    shift 3
    local context_vars=("$@")
    
    local template_file="$PROMPTS_DIR/templates/$template_name.md"
    
    if [[ ! -f "$template_file" ]]; then
        echo "Error: Template not found: $template_file" >&2
        return 1
    fi
    
    local project_name
    project_name=$(basename "$project_path")
    
    # Create prompt session directory
    local session_prompt_dir="$PROMPTS_DIR/sessions/$project_name/$session_id"
    mkdir -p "$session_prompt_dir"
    
    local assembled_prompt="$session_prompt_dir/$template_name-$(date +%s).md"
    
    # Start with template content
    cp "$template_file" "$assembled_prompt"
    
    # Replace standard variables
    sed -i.bak "s/{{project_name}}/$project_name/g" "$assembled_prompt"
    sed -i.bak "s/{{session_id}}/$session_id/g" "$assembled_prompt"
    sed -i.bak "s/{{command_name}}/${PRUNEJUICE_COMMAND_NAME:-unknown}/g" "$assembled_prompt"
    
    # Replace custom context variables
    for context_var in "${context_vars[@]}"; do
        if [[ "$context_var" == *"="* ]]; then
            local var_name var_value
            var_name=$(echo "$context_var" | cut -d= -f1)
            var_value=$(echo "$context_var" | cut -d= -f2-)
            
            # Escape special characters for sed
            var_value=$(echo "$var_value" | sed 's/[[\.*^$()+?{|]/\\&/g')
            
            sed -i.bak "s/{{$var_name}}/$var_value/g" "$assembled_prompt"
        fi
    done
    
    # Clean up backup files
    rm -f "$assembled_prompt.bak"
    
    echo "$assembled_prompt"
}

# Gather project context for prompts
gather_project_context() {
    local project_path="$1"
    local context_type="$2"  # "full", "summary", "files-only"
    
    local context_file
    context_file=$(mktemp)
    
    case "$context_type" in
        "full")
            echo "# Project Structure" >> "$context_file"
            if command -v tree &> /dev/null; then
                tree -I 'node_modules|.git|*.log' "$project_path" | head -50 >> "$context_file"
            else
                find "$project_path" -type f -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.yaml" | head -20 >> "$context_file"
            fi
            echo "" >> "$context_file"
            
            echo "# Key Files" >> "$context_file"
            for key_file in README.md CLAUDE.md package.json requirements.txt; do
                if [[ -f "$project_path/$key_file" ]]; then
                    echo "## $key_file" >> "$context_file"
                    head -20 "$project_path/$key_file" >> "$context_file"
                    echo "" >> "$context_file"
                fi
            done
            ;;
        "summary")
            echo "# Project Summary" >> "$context_file"
            echo "Path: $project_path" >> "$context_file"
            echo "Type: $(detect_project_type "$project_path")" >> "$context_file"
            echo "" >> "$context_file"
            
            if [[ -f "$project_path/README.md" ]]; then
                echo "## README Summary" >> "$context_file"
                head -10 "$project_path/README.md" >> "$context_file"
                echo "" >> "$context_file"
            fi
            ;;
        "files-only")
            find "$project_path" -type f \( -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.yaml" -o -name "*.md" \) | head -30 >> "$context_file"
            ;;
    esac
    
    echo "$context_file"
}

# Detect project type
detect_project_type() {
    local project_path="$1"
    
    if [[ -f "$project_path/package.json" ]]; then
        echo "Node.js/JavaScript"
    elif [[ -f "$project_path/requirements.txt" ]] || [[ -f "$project_path/pyproject.toml" ]]; then
        echo "Python"
    elif [[ -f "$project_path/Cargo.toml" ]]; then
        echo "Rust"
    elif [[ -f "$project_path/go.mod" ]]; then
        echo "Go"
    elif find "$project_path" -name "*.sh" | head -1 | grep -q .; then
        echo "Shell Script"
    else
        echo "Unknown"
    fi
}

# Create a context-aware prompt for Claude Code
create_claude_code_prompt() {
    local prompt_type="$1"  # analysis, implementation, review, etc.
    local project_path="$2"
    local session_id="$3"
    local task_description="$4"
    shift 4
    local additional_context=("$@")
    
    init_prompt_system
    
    local template_name="${prompt_type}-base"
    local project_context_file
    project_context_file=$(gather_project_context "$project_path" "summary")
    
    # Prepare context variables
    local context_vars=(
        "${prompt_type}_request=$task_description"
        "codebase_context=$(cat "$project_context_file")"
        "focus_areas=${PRUNEJUICE_FOCUS_AREAS:-general}"
        "additional_context=${additional_context[*]}"
    )
    
    # Add any additional context variables passed in
    context_vars+=("${additional_context[@]}")
    
    local assembled_prompt
    assembled_prompt=$(assemble_prompt "$template_name" "$session_id" "$project_path" "${context_vars[@]}")
    
    # Clean up temporary files
    rm -f "$project_context_file"
    
    echo "$assembled_prompt"
}

# Log prompt usage for session tracking
log_prompt_usage() {
    local session_id="$1"
    local prompt_file="$2"
    local prompt_type="$3"
    local event_id="$4"
    
    local usage_log="$PROMPTS_DIR/history/prompt-usage.log"
    
    echo "$(date -u +"%Y-%m-%d %H:%M:%S") | $session_id | $prompt_type | $prompt_file | $event_id" >> "$usage_log"
    
    # Store as artifact if event_id is provided
    if [[ -n "$event_id" && "$event_id" != "null" ]]; then
        store_artifact "$event_id" "prompt" "$prompt_file" "$(basename "$prompt_file")" "Assembled Claude Code prompt"
    fi
}

# Get prompt history for a session
get_prompt_history() {
    local session_id="$1"
    local usage_log="$PROMPTS_DIR/history/prompt-usage.log"
    
    if [[ -f "$usage_log" ]]; then
        grep "| $session_id |" "$usage_log" | while IFS='|' read -r timestamp session type file event; do
            echo "[$timestamp] $type: $(basename "$file")"
        done
    fi
}

# Create a comprehensive prompt with file contents
create_detailed_prompt() {
    local prompt_type="$1"
    local project_path="$2"
    local session_id="$3"
    local task_description="$4"
    local files_to_include=("${@:5}")
    
    local base_prompt
    base_prompt=$(create_claude_code_prompt "$prompt_type" "$project_path" "$session_id" "$task_description")
    
    local detailed_prompt="${base_prompt%.md}-detailed.md"
    cp "$base_prompt" "$detailed_prompt"
    
    # Add file contents if specified
    if [[ ${#files_to_include[@]} -gt 0 ]]; then
        echo "" >> "$detailed_prompt"
        echo "## Relevant File Contents" >> "$detailed_prompt"
        
        for file in "${files_to_include[@]}"; do
            if [[ -f "$file" ]]; then
                echo "" >> "$detailed_prompt"
                echo "### $(basename "$file")" >> "$detailed_prompt"
                echo "\`\`\`$(get_file_extension "$file")" >> "$detailed_prompt"
                cat "$file" >> "$detailed_prompt"
                echo "\`\`\`" >> "$detailed_prompt"
            fi
        done
    fi
    
    echo "$detailed_prompt"
}

# Get file extension for syntax highlighting
get_file_extension() {
    local file="$1"
    local ext="${file##*.}"
    
    case "$ext" in
        "sh") echo "bash" ;;
        "py") echo "python" ;;
        "js") echo "javascript" ;;
        "ts") echo "typescript" ;;
        "yaml"|"yml") echo "yaml" ;;
        "json") echo "json" ;;
        "md") echo "markdown" ;;
        *) echo "$ext" ;;
    esac
}

# Clean up old prompts
cleanup_prompts() {
    local days="${1:-30}"
    
    # Clean up old session prompts
    find "$PROMPTS_DIR/sessions" -type f -mtime "+$days" -delete
    find "$PROMPTS_DIR/sessions" -type d -empty -delete
    
    # Trim history log
    local history_log="$PROMPTS_DIR/history/prompt-usage.log"
    if [[ -f "$history_log" ]]; then
        local temp_log
        temp_log=$(mktemp)
        tail -1000 "$history_log" > "$temp_log"
        mv "$temp_log" "$history_log"
    fi
    
    echo "Cleaned up prompts older than $days days"
}

# Main prompt creation interface
main_create_prompt() {
    local command="$1"
    shift
    
    case "$command" in
        "create")
            create_claude_code_prompt "$@"
            ;;
        "detailed")
            create_detailed_prompt "$@"
            ;;
        "history")
            get_prompt_history "$@"
            ;;
        "cleanup")
            cleanup_prompts "$@"
            ;;
        "templates")
            list_templates
            ;;
        *)
            echo "Usage: $0 {create|detailed|history|cleanup|templates}" >&2
            return 1
            ;;
    esac
}

# List available templates
list_templates() {
    echo "Available prompt templates:"
    for template_file in "$PROMPTS_DIR/templates"/*.md; do
        if [[ -f "$template_file" ]]; then
            local template_name
            template_name=$(basename "$template_file" .md)
            local description
            description=$(grep "^# " "$template_file" | head -1 | sed 's/^# //')
            printf "  %-20s %s\n" "$template_name" "$description"
        fi
    done
}