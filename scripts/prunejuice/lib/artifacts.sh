#!/bin/bash
# Artifact management system for PruneJuice

# Source database functions
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$SCRIPT_DIR/database.sh"

# Artifact configuration
ARTIFACTS_BASE_DIR="${PRUNEJUICE_ARTIFACTS_DIR:-$HOME/.prunejuice/artifacts}"
SPECS_DIR="${PRUNEJUICE_SPECS_DIR:-$HOME/.prunejuice/specs}"

# Artifact types - using case statement for compatibility with bash 3.x
VALID_ARTIFACT_TYPES="spec log output prompt analysis plan config temp"

# Get artifact type description
get_artifact_description() {
    local type="$1"
    case "$type" in
        spec) echo "Specification and requirements documents" ;;
        log) echo "Command execution logs" ;;
        output) echo "Command output files" ;;
        prompt) echo "Claude Code prompts and responses" ;;
        analysis) echo "Analysis reports and findings" ;;
        plan) echo "Implementation plans and strategies" ;;
        config) echo "Configuration files and settings" ;;
        temp) echo "Temporary files and intermediates" ;;
        *) echo "Unknown artifact type" ;;
    esac
}

# Check if artifact type is valid
is_valid_artifact_type() {
    local type="$1"
    echo "$VALID_ARTIFACT_TYPES" | grep -q "\b$type\b"
}

# Ensure artifact directories exist
ensure_artifact_dirs() {
    local project_path="$1"
    local session_id="$2"
    
    local project_name
    project_name=$(basename "$project_path")
    
    local artifact_dir="$ARTIFACTS_BASE_DIR/$project_name/$session_id"
    local specs_dir="$SPECS_DIR/$project_name/$session_id"
    
    mkdir -p "$artifact_dir"/{specs,logs,outputs,prompts,analysis,plans,configs,temp}
    mkdir -p "$specs_dir"
    
    echo "$artifact_dir"
}

# Create artifact directory structure for a session
create_session_artifacts() {
    local project_path="$1"
    local session_id="$2"
    local command="$3"
    
    local artifact_dir
    artifact_dir=$(ensure_artifact_dirs "$project_path" "$session_id")
    
    # Create session metadata file
    local metadata_file="$artifact_dir/session-metadata.json"
    cat > "$metadata_file" << EOF
{
    "session_id": "$session_id",
    "project_path": "$project_path",
    "command": "$command",
    "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "artifacts": []
}
EOF
    
    echo "$artifact_dir"
}

# Store an artifact file
store_artifact() {
    local event_id="$1"
    local artifact_type="$2"
    local source_file="$3"
    local artifact_name="$4"
    local description="$5"
    
    if [[ ! -f "$source_file" ]]; then
        echo "Error: Source file not found: $source_file" >&2
        return 1
    fi
    
    if ! is_valid_artifact_type "$artifact_type"; then
        echo "Error: Invalid artifact type: $artifact_type" >&2
        echo "Valid types: $VALID_ARTIFACT_TYPES" >&2
        return 1
    fi
    
    # Get event details from database
    local event_details
    event_details=$(execute_sql "SELECT project_path, session_id, artifacts_path FROM events WHERE id = $event_id;")
    
    if [[ -z "$event_details" ]]; then
        echo "Error: Event ID $event_id not found" >&2
        return 1
    fi
    
    # Parse event details
    local project_path session_id artifacts_path
    IFS='|' read -r project_path session_id artifacts_path <<< "$event_details"
    
    # Ensure artifact directory exists
    local artifact_dir
    artifact_dir=$(ensure_artifact_dirs "$project_path" "$session_id")
    
    # Determine target file path
    local target_file="$artifact_dir/$artifact_type/$artifact_name"
    
    # Copy file to artifact location
    cp "$source_file" "$target_file"
    
    local file_size
    file_size=$(stat -f%z "$target_file" 2>/dev/null || stat -c%s "$target_file" 2>/dev/null || echo "0")
    
    # Record artifact in database
    add_artifact "$event_id" "$artifact_type" "$target_file" "$file_size"
    
    # Update session metadata
    update_session_metadata "$project_path" "$session_id" "$artifact_type" "$target_file" "$description"
    
    echo "Artifact stored: $target_file"
}

# Update session metadata with new artifact
update_session_metadata() {
    local project_path="$1"
    local session_id="$2"
    local artifact_type="$3"
    local file_path="$4"
    local description="$5"
    
    local project_name
    project_name=$(basename "$project_path")
    
    local metadata_file="$ARTIFACTS_BASE_DIR/$project_name/$session_id/session-metadata.json"
    
    if [[ -f "$metadata_file" ]]; then
        # Use jq to update metadata if available, otherwise append manually
        if command -v jq &> /dev/null; then
            local temp_file
            temp_file=$(mktemp)
            jq --arg type "$artifact_type" \
               --arg path "$file_path" \
               --arg desc "$description" \
               --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
               '.artifacts += [{"type": $type, "path": $path, "description": $desc, "created_at": $timestamp}]' \
               "$metadata_file" > "$temp_file"
            mv "$temp_file" "$metadata_file"
        else
            echo "Artifact: $artifact_type - $file_path - $description - $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "$metadata_file.log"
        fi
    fi
}

# Get artifacts for a session
get_session_artifacts() {
    local project_path="$1"
    local session_id="$2"
    local artifact_type="$3"  # Optional filter
    
    local project_name
    project_name=$(basename "$project_path")
    
    local artifact_dir="$ARTIFACTS_BASE_DIR/$project_name/$session_id"
    
    if [[ ! -d "$artifact_dir" ]]; then
        echo "No artifacts found for session: $session_id" >&2
        return 1
    fi
    
    if [[ -n "$artifact_type" ]]; then
        # Show specific artifact type
        if [[ -d "$artifact_dir/$artifact_type" ]]; then
            find "$artifact_dir/$artifact_type" -type f -exec ls -la {} \;
        fi
    else
        # Show all artifacts
        find "$artifact_dir" -type f -not -path "*/.*" -exec ls -la {} \; | sort
    fi
}

# Create a specification document
create_spec() {
    local project_path="$1"
    local session_id="$2"
    local spec_name="$3"
    local spec_content="$4"
    
    local project_name
    project_name=$(basename "$project_path")
    
    local specs_dir="$SPECS_DIR/$project_name/$session_id"
    mkdir -p "$specs_dir"
    
    local spec_file="$specs_dir/$spec_name.md"
    
    cat > "$spec_file" << EOF
# $spec_name

**Project**: $project_name  
**Session**: $session_id  
**Created**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

## Specification

$spec_content

## Metadata

- **Project Path**: $project_path
- **Session ID**: $session_id
- **Generated By**: PruneJuice Artifact Management System
EOF
    
    echo "$spec_file"
}

# List all specifications for a project
list_specs() {
    local project_path="$1"
    local project_name
    project_name=$(basename "$project_path")
    
    local project_specs_dir="$SPECS_DIR/$project_name"
    
    if [[ ! -d "$project_specs_dir" ]]; then
        echo "No specifications found for project: $project_name" >&2
        return 1
    fi
    
    echo "Specifications for $project_name:"
    find "$project_specs_dir" -name "*.md" -type f | while read -r spec_file; do
        local session_dir
        session_dir=$(dirname "$spec_file")
        local session_id
        session_id=$(basename "$session_dir")
        local spec_name
        spec_name=$(basename "$spec_file" .md)
        
        echo "  [$session_id] $spec_name"
    done
}

# Clean up old artifacts
cleanup_artifacts() {
    local days="${1:-30}"
    local project_path="$2"  # Optional: specific project
    
    if [[ -n "$project_path" ]]; then
        local project_name
        project_name=$(basename "$project_path")
        local project_dir="$ARTIFACTS_BASE_DIR/$project_name"
        
        if [[ -d "$project_dir" ]]; then
            find "$project_dir" -type f -mtime "+$days" -delete
            find "$project_dir" -type d -empty -delete
        fi
    else
        # Clean up all projects
        find "$ARTIFACTS_BASE_DIR" -type f -mtime "+$days" -delete
        find "$ARTIFACTS_BASE_DIR" -type d -empty -delete
    fi
    
    echo "Cleaned up artifacts older than $days days"
}

# Get artifact statistics
get_artifact_stats() {
    local project_path="$1"  # Optional: specific project
    
    if [[ -n "$project_path" ]]; then
        local project_name
        project_name=$(basename "$project_path")
        local project_dir="$ARTIFACTS_BASE_DIR/$project_name"
        
        if [[ -d "$project_dir" ]]; then
            echo "Artifact statistics for $project_name:"
            find "$project_dir" -type f | wc -l | xargs echo "  Total files:"
            du -sh "$project_dir" 2>/dev/null | cut -f1 | xargs echo "  Total size:"
            
            for artifact_type in $VALID_ARTIFACT_TYPES; do
                local count
                count=$(find "$project_dir" -path "*/$artifact_type/*" -type f | wc -l)
                if [[ "$count" -gt 0 ]]; then
                    echo "  $artifact_type: $count files"
                fi
            done
        fi
    else
        echo "Global artifact statistics:"
        find "$ARTIFACTS_BASE_DIR" -type f | wc -l | xargs echo "  Total files:"
        du -sh "$ARTIFACTS_BASE_DIR" 2>/dev/null | cut -f1 | xargs echo "  Total size:"
    fi
}

# Archive session artifacts
archive_session() {
    local project_path="$1"
    local session_id="$2"
    local archive_name="$3"
    
    local project_name
    project_name=$(basename "$project_path")
    
    local session_dir="$ARTIFACTS_BASE_DIR/$project_name/$session_id"
    
    if [[ ! -d "$session_dir" ]]; then
        echo "Error: Session directory not found: $session_dir" >&2
        return 1
    fi
    
    local archive_dir="$ARTIFACTS_BASE_DIR/$project_name/archives"
    mkdir -p "$archive_dir"
    
    local archive_file="$archive_dir/${archive_name:-$session_id}-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    tar -czf "$archive_file" -C "$ARTIFACTS_BASE_DIR/$project_name" "$session_id"
    
    echo "Session archived: $archive_file"
}