#!/bin/bash
# Database utility functions for PruneJuice

# Database configuration
DB_DIR="${PRUNEJUICE_DATA_DIR:-$HOME/.prunejuice}"
DB_FILE="${DB_DIR}/prunejuice.db"
SCHEMA_FILE="$(dirname "${BASH_SOURCE[0]}")/../db/schema.sql"

# Ensure database directory exists
ensure_db_dir() {
    if [[ ! -d "$DB_DIR" ]]; then
        mkdir -p "$DB_DIR"
    fi
}

# Initialize database with schema
init_database() {
    ensure_db_dir
    
    if [[ ! -f "$DB_FILE" ]]; then
        echo "Initializing PruneJuice database..."
        sqlite3 "$DB_FILE" < "$SCHEMA_FILE"
        echo "Database initialized at: $DB_FILE"
    fi
}

# Execute SQL query
execute_sql() {
    local sql="$1"
    ensure_db_dir
    init_database
    sqlite3 "$DB_FILE" "$sql"
}

# Insert new event and return event ID
start_event() {
    local command="$1"
    local project_path="$2"
    local worktree_name="$3"
    local session_id="$4"
    local artifacts_path="$5"
    local metadata="$6"
    
    local sql="INSERT INTO events (command, project_path, worktree_name, session_id, artifacts_path, metadata) 
               VALUES ('$command', '$project_path', '$worktree_name', '$session_id', '$artifacts_path', '$metadata');
               SELECT last_insert_rowid();"
    
    execute_sql "$sql"
}

# Update event status and end time
end_event() {
    local event_id="$1"
    local status="$2"
    local exit_code="$3"
    local error_message="$4"
    
    local sql="UPDATE events SET 
               end_time = CURRENT_TIMESTAMP, 
               status = '$status',
               exit_code = $exit_code,
               error_message = '$error_message'
               WHERE id = $event_id;"
    
    execute_sql "$sql"
}

# Get active events
get_active_events() {
    local sql="SELECT id, command, project_path, worktree_name, session_id, start_time 
               FROM active_events;"
    execute_sql "$sql"
}

# Get recent events
get_recent_events() {
    local limit="${1:-10}"
    local sql="SELECT id, command, project_path, status, start_time, end_time 
               FROM events 
               ORDER BY start_time DESC 
               LIMIT $limit;"
    execute_sql "$sql"
}

# Add artifact record
add_artifact() {
    local event_id="$1"
    local artifact_type="$2"
    local file_path="$3"
    local file_size="$4"
    
    local sql="INSERT INTO artifacts (event_id, artifact_type, file_path, file_size)
               VALUES ($event_id, '$artifact_type', '$file_path', $file_size);"
    
    execute_sql "$sql"
}

# Get artifacts for event
get_artifacts() {
    local event_id="$1"
    local sql="SELECT artifact_type, file_path, file_size, created_at 
               FROM artifacts 
               WHERE event_id = $event_id
               ORDER BY created_at;"
    execute_sql "$sql"
}

# Session management
create_session() {
    local session_name="$1"
    local project_path="$2"
    local worktree_name="$3"
    local tmux_session_id="$4"
    
    local sql="INSERT OR REPLACE INTO sessions (session_name, project_path, worktree_name, tmux_session_id)
               VALUES ('$session_name', '$project_path', '$worktree_name', '$tmux_session_id');"
    
    execute_sql "$sql"
}

# Update session activity
update_session_activity() {
    local session_name="$1"
    local sql="UPDATE sessions SET last_activity = CURRENT_TIMESTAMP WHERE session_name = '$session_name';"
    execute_sql "$sql"
}

# Get active sessions
get_active_sessions() {
    local sql="SELECT session_name, project_path, worktree_name, tmux_session_id, created_at 
               FROM sessions 
               WHERE status = 'active'
               ORDER BY last_activity DESC;"
    execute_sql "$sql"
}

# Kill session
kill_session() {
    local session_name="$1"
    local sql="UPDATE sessions SET status = 'killed' WHERE session_name = '$session_name';"
    execute_sql "$sql"
}

# Project settings
get_project_settings() {
    local project_path="$1"
    local sql="SELECT config_json FROM project_settings WHERE project_path = '$project_path';"
    execute_sql "$sql"
}

# Set project settings
set_project_settings() {
    local project_path="$1"
    local config_json="$2"
    local sql="INSERT OR REPLACE INTO project_settings (project_path, config_json, updated_at)
               VALUES ('$project_path', '$config_json', CURRENT_TIMESTAMP);"
    execute_sql "$sql"
}

# Database maintenance
vacuum_database() {
    execute_sql "VACUUM;"
}

# Cleanup old records (older than 30 days by default)
cleanup_old_records() {
    local days="${1:-30}"
    local sql="DELETE FROM events WHERE start_time < datetime('now', '-$days days');"
    execute_sql "$sql"
}

# Get database stats
get_db_stats() {
    local sql="SELECT 
               (SELECT COUNT(*) FROM events) as total_events,
               (SELECT COUNT(*) FROM events WHERE status = 'running') as active_events,
               (SELECT COUNT(*) FROM sessions WHERE status = 'active') as active_sessions,
               (SELECT COUNT(*) FROM command_definitions) as command_definitions,
               (SELECT COUNT(*) FROM artifacts) as total_artifacts;"
    execute_sql "$sql"
}