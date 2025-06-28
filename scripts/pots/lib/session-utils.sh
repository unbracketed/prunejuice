#!/bin/bash

# Session utilities module for POTS tmux session manager

# Ensure proper PATH for external commands
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"

# Check if tmux is available
validate_tmux_available() {
    if ! command -v tmux >/dev/null 2>&1; then
        echo "Error: tmux is not installed or not in PATH" >&2
        return 1
    fi
}

# Check if a tmux session exists
session_exists() {
    local session_name="$1"
    
    if [ -z "$session_name" ]; then
        echo "Error: Session name is required" >&2
        return 1
    fi
    
    tmux has-session -t "$session_name" 2>/dev/null
}

# Sanitize session name for tmux compatibility
session_name_sanitize() {
    local raw_name="$1"
    
    # Convert to lowercase and replace invalid characters
    echo "$raw_name" | /usr/bin/tr '[:upper:]' '[:lower:]' | /usr/bin/sed 's/[^a-z0-9-]/-/g' | /usr/bin/sed 's/--*/-/g' | /usr/bin/sed 's/^-//' | /usr/bin/sed 's/-$//'
}

# Generate session name from components
generate_session_name() {
    local project="$1"
    local worktree="$2"
    local task="$3"
    
    if [ -z "$project" ] || [ -z "$worktree" ]; then
        echo "Error: Project and worktree names are required" >&2
        return 1
    fi
    
    local session_name
    if [ -n "$task" ]; then
        session_name="${project}-${worktree}-${task}"
    else
        session_name="${project}-${worktree}"
    fi
    
    session_name_sanitize "$session_name"
}

# Create a new tmux session
create_session() {
    local session_name="$1"
    local working_dir="$2"
    
    if [ -z "$session_name" ]; then
        echo "Error: Session name is required" >&2
        return 1
    fi
    
    if [ -z "$working_dir" ]; then
        echo "Error: Working directory is required" >&2
        return 1
    fi
    
    if [ ! -d "$working_dir" ]; then
        echo "Error: Working directory does not exist: $working_dir" >&2
        return 1
    fi
    
    if session_exists "$session_name"; then
        echo "Error: Session '$session_name' already exists" >&2
        return 1
    fi
    
    tmux new-session -d -s "$session_name" -c "$working_dir"
}

# List tmux sessions with optional filtering
list_sessions() {
    local filter_pattern="$1"
    
    if ! validate_tmux_available; then
        return 1
    fi
    
    if [ -n "$filter_pattern" ]; then
        tmux list-sessions -F "#{session_name}" 2>/dev/null | grep "$filter_pattern" || true
    else
        tmux list-sessions -F "#{session_name}" 2>/dev/null || true
    fi
}

# Kill a tmux session
kill_session() {
    local session_name="$1"
    
    if [ -z "$session_name" ]; then
        echo "Error: Session name is required" >&2
        return 1
    fi
    
    if ! session_exists "$session_name"; then
        echo "Error: Session '$session_name' does not exist" >&2
        return 1
    fi
    
    tmux kill-session -t "$session_name"
}

# Attach to a tmux session
attach_session() {
    local session_name="$1"
    
    if [ -z "$session_name" ]; then
        echo "Error: Session name is required" >&2
        return 1
    fi
    
    if ! session_exists "$session_name"; then
        echo "Error: Session '$session_name' does not exist" >&2
        return 1
    fi
    
    tmux attach-session -t "$session_name"
}

# Get session working directory
get_session_working_dir() {
    local session_name="$1"
    
    if [ -z "$session_name" ]; then
        echo "Error: Session name is required" >&2
        return 1
    fi
    
    if ! session_exists "$session_name"; then
        echo "Error: Session '$session_name' does not exist" >&2
        return 1
    fi
    
    tmux display-message -t "$session_name" -p "#{session_path}"
}

# List sessions with detailed information
list_sessions_detailed() {
    local filter_pattern="$1"
    
    if ! validate_tmux_available; then
        return 1
    fi
    
    local format="#{session_name}:#{session_path}:#{session_created}:#{session_attached}"
    
    if [ -n "$filter_pattern" ]; then
        tmux list-sessions -F "$format" 2>/dev/null | grep "$filter_pattern" || true
    else
        tmux list-sessions -F "$format" 2>/dev/null || true
    fi
}

# Validate working directory exists and is accessible
validate_working_directory() {
    local working_dir="$1"
    
    if [ -z "$working_dir" ]; then
        echo "Error: Working directory path is required" >&2
        return 1
    fi
    
    if [ ! -d "$working_dir" ]; then
        echo "Error: Working directory does not exist: $working_dir" >&2
        return 1
    fi
    
    if [ ! -r "$working_dir" ]; then
        echo "Error: Working directory is not readable: $working_dir" >&2
        return 1
    fi
    
    return 0
}

# Find sessions matching a project pattern
find_project_sessions() {
    local project_name="$1"
    
    if [ -z "$project_name" ]; then
        echo "Error: Project name is required" >&2
        return 1
    fi
    
    local sanitized_project
    sanitized_project=$(session_name_sanitize "$project_name")
    
    list_sessions "^${sanitized_project}-"
}

# Find orphaned sessions (sessions for non-existent worktrees)
find_orphaned_sessions() {
    local sessions
    sessions=$(list_sessions)
    
    if [ -z "$sessions" ]; then
        return 0
    fi
    
    local orphaned_sessions=""
    while IFS= read -r session_name; do
        local working_dir
        working_dir=$(get_session_working_dir "$session_name" 2>/dev/null)
        
        if [ -n "$working_dir" ] && [ ! -d "$working_dir" ]; then
            if [ -n "$orphaned_sessions" ]; then
                orphaned_sessions="${orphaned_sessions}\n${session_name}"
            else
                orphaned_sessions="$session_name"
            fi
        fi
    done <<< "$sessions"
    
    if [ -n "$orphaned_sessions" ]; then
        echo -e "$orphaned_sessions"
    fi
}

# Check if session is attached
is_session_attached() {
    local session_name="$1"
    
    if [ -z "$session_name" ]; then
        echo "Error: Session name is required" >&2
        return 1
    fi
    
    if ! session_exists "$session_name"; then
        return 1
    fi
    
    local attached
    attached=$(tmux display-message -t "$session_name" -p "#{session_attached}")
    [ "$attached" -gt 0 ]
}

# Get session information as formatted output
get_session_info() {
    local session_name="$1"
    
    if [ -z "$session_name" ]; then
        echo "Error: Session name is required" >&2
        return 1
    fi
    
    if ! session_exists "$session_name"; then
        echo "Error: Session '$session_name' does not exist" >&2
        return 1
    fi
    
    local working_dir created attached
    working_dir=$(tmux display-message -t "$session_name" -p "#{session_path}")
    created=$(tmux display-message -t "$session_name" -p "#{session_created}")
    attached=$(tmux display-message -t "$session_name" -p "#{session_attached}")
    
    echo "Session: $session_name"
    echo "Working Directory: $working_dir"
    echo "Created: $(date -r "$created" 2>/dev/null || echo "$created")"
    echo "Attached: $([ "$attached" -gt 0 ] && echo "Yes" || echo "No")"
}