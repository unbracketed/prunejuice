#!/bin/bash

# Worktree synchronization module for POTS-Plum integration

# Source shared libraries
# Get the directory of this script file
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

# Check if we can source relative to script location
if [ -f "${SCRIPT_DIR}/shared/git-utils.sh" ]; then
    source "${SCRIPT_DIR}/shared/git-utils.sh"
    source "${SCRIPT_DIR}/session-utils.sh"
elif [ -f "lib/shared/git-utils.sh" ]; then
    # Fallback: source relative to current working directory
    source "lib/shared/git-utils.sh"
    source "lib/session-utils.sh"
else
    echo "Error: Could not find shared libraries" >&2
    return 1
fi

# Get worktrees from plum's git operations
get_worktrees_from_plum() {
    local format="${1:-simple}"
    
    # Use plum's git-utils list_worktrees function
    list_worktrees "$format"
}

# Parse worktree output to extract components
parse_worktree_info() {
    local worktree_line="$1"
    
    # Extract path (first field) and branch (last field in brackets)
    local path branch
    
    # Use parameter expansion instead of external commands
    path="${worktree_line%% *}"  # Get everything before first space
    
    # Extract branch from brackets if present
    if [[ "$worktree_line" =~ \[([^]]+)\] ]]; then
        branch="${BASH_REMATCH[1]}"
    else
        branch=""
    fi
    
    echo "$path:$branch"
}

# Extract project name from worktree path
extract_project_name() {
    local worktree_path="$1"
    
    if [ -z "$worktree_path" ]; then
        echo "Error: Worktree path is required" >&2
        return 1
    fi
    
    # Get the directory name using parameter expansion instead of basename
    local dir_name="${worktree_path##*/}"
    
    # For worktree paths that follow pattern like "project-feature", extract "project"
    # Common project prefixes
    for prefix in "prunejuice" "plum" "pots"; do
        if [[ "$dir_name" == "$prefix"-* ]] || [[ "$dir_name" == "$prefix" ]]; then
            echo "$prefix"
            return 0
        fi
    done
    
    # If no known prefix pattern, try to extract base project name
    # by removing the last dash and everything after it
    local base_name="${dir_name%-*}"
    if [ "$base_name" != "$dir_name" ]; then
        echo "$base_name"
    else
        echo "$dir_name"
    fi
}

# Extract worktree name from path (usually the directory name)
extract_worktree_name() {
    local worktree_path="$1"
    
    if [ -z "$worktree_path" ]; then
        echo "Error: Worktree path is required" >&2
        return 1
    fi
    
    # Get just the worktree directory name using parameter expansion
    local dir_name="${worktree_path##*/}"
    
    # For worktrees, try to extract the meaningful part after the project name
    # e.g., "prunejuice-help" -> "help", "prunejuice-phase-4-impl" -> "phase-4-impl"
    
    # Common project prefixes to strip
    for prefix in "prunejuice" "plum" "pots"; do
        if [[ "$dir_name" == "$prefix"-* ]]; then
            echo "${dir_name#$prefix-}"
            return 0
        fi
    done
    
    # If no known prefix, return the full directory name
    echo "$dir_name"
}

# Generate session name from worktree
generate_session_from_worktree() {
    local worktree_path="$1"
    local task="${2:-dev}"
    
    if [ -z "$worktree_path" ]; then
        echo "Error: Worktree path is required" >&2
        return 1
    fi
    
    local project_name worktree_name
    project_name=$(extract_project_name "$worktree_path")
    worktree_name=$(extract_worktree_name "$worktree_path")
    
    # Use the session-utils generate_session_name function
    generate_session_name "$project_name" "$worktree_name" "$task"
}

# Map worktrees to potential session names
map_worktrees_to_sessions() {
    local task="${1:-dev}"
    local worktrees
    
    worktrees=$(get_worktrees_from_plum "simple")
    
    if [ -z "$worktrees" ]; then
        return 0
    fi
    
    while IFS= read -r worktree_line; do
        # Skip empty lines
        [ -z "$worktree_line" ] && continue
        
        local worktree_info path session_name
        worktree_info=$(parse_worktree_info "$worktree_line")
        
        # Extract path from worktree_info using parameter expansion
        path="${worktree_info%%:*}"
        
        if [ -n "$path" ]; then
            session_name=$(generate_session_from_worktree "$path" "$task")
            echo "$path:$session_name"
        fi
    done <<< "$worktrees"
}

# Find sessions for existing worktrees
find_worktree_sessions() {
    local worktree_path="$1"
    
    if [ -z "$worktree_path" ]; then
        echo "Error: Worktree path is required" >&2
        return 1
    fi
    
    local project_name worktree_name
    project_name=$(extract_project_name "$worktree_path")
    worktree_name=$(extract_worktree_name "$worktree_path")
    
    # Find all sessions that match this worktree pattern
    local session_pattern
    session_pattern=$(session_name_sanitize "${project_name}-${worktree_name}")
    
    list_sessions "^${session_pattern}-\\|^${session_pattern}$"
}

# Check if worktree exists for a session
validate_session_worktree() {
    local session_name="$1"
    
    if [ -z "$session_name" ]; then
        echo "Error: Session name is required" >&2
        return 1
    fi
    
    if ! session_exists "$session_name"; then
        echo "Error: Session '$session_name' does not exist" >&2
        return 1
    fi
    
    local working_dir
    working_dir=$(get_session_working_dir "$session_name")
    
    if [ -z "$working_dir" ]; then
        echo "Error: Could not get working directory for session '$session_name'" >&2
        return 1
    fi
    
    # Check if the working directory is actually a worktree
    local worktrees
    worktrees=$(get_worktrees_from_plum "simple")
    
    if echo "$worktrees" | grep -q "^$working_dir "; then
        return 0
    else
        echo "Warning: Session '$session_name' working directory '$working_dir' is not a valid worktree" >&2
        return 1
    fi
}

# Find orphaned sessions (sessions without valid worktrees)
find_sessions_without_worktrees() {
    local sessions worktrees
    sessions=$(list_sessions)
    worktrees=$(get_worktrees_from_plum "simple" | awk '{print $1}')
    
    if [ -z "$sessions" ]; then
        return 0
    fi
    
    local orphaned=""
    while IFS= read -r session_name; do
        local working_dir
        working_dir=$(get_session_working_dir "$session_name" 2>/dev/null)
        
        if [ -n "$working_dir" ]; then
            if ! echo "$worktrees" | grep -q "^$working_dir$"; then
                if [ -n "$orphaned" ]; then
                    orphaned="${orphaned}\n${session_name}"
                else
                    orphaned="$session_name"
                fi
            fi
        fi
    done <<< "$sessions"
    
    if [ -n "$orphaned" ]; then
        echo -e "$orphaned"
    fi
}

# Create session for a worktree
create_worktree_session() {
    local worktree_path="$1"
    local task="${2:-dev}"
    
    if [ -z "$worktree_path" ]; then
        echo "Error: Worktree path is required" >&2
        return 1
    fi
    
    if ! validate_working_directory "$worktree_path"; then
        return 1
    fi
    
    # Verify this is actually a worktree
    local worktrees
    worktrees=$(get_worktrees_from_plum "simple")
    if ! echo "$worktrees" | grep -q "^$worktree_path "; then
        echo "Error: '$worktree_path' is not a valid worktree" >&2
        return 1
    fi
    
    local session_name
    session_name=$(generate_session_from_worktree "$worktree_path" "$task")
    
    if [ -z "$session_name" ]; then
        echo "Error: Could not generate session name for worktree" >&2
        return 1
    fi
    
    create_session "$session_name" "$worktree_path"
}