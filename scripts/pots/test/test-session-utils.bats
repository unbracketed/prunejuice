#!/usr/bin/env bats

# Test session-utils.sh functions

setup() {
    # Load the session utilities
    source "${BATS_TEST_DIRNAME}/../lib/session-utils.sh"
    
    # Set a test session prefix to avoid conflicts
    TEST_PREFIX="bats-test"
    TEST_SESSION="${TEST_PREFIX}-session"
}

teardown() {
    # Clean up any test sessions
    tmux kill-session -t "$TEST_SESSION" 2>/dev/null || true
    
    # Clean up any sessions starting with the test prefix
    tmux list-sessions -F "#{session_name}" 2>/dev/null | grep "^${TEST_PREFIX}-" | while read -r session; do
        tmux kill-session -t "$session" 2>/dev/null || true
    done
}

@test "validate_tmux_available should succeed when tmux is installed" {
    run validate_tmux_available
    [ "$status" -eq 0 ]
}

@test "session_name_sanitize should convert to lowercase" {
    result=$(session_name_sanitize "TestSession")
    [ "$result" = "testsession" ]
}

@test "session_name_sanitize should replace invalid characters with hyphens" {
    result=$(session_name_sanitize "Test@Session#123")
    [ "$result" = "test-session-123" ]
}

@test "session_name_sanitize should remove multiple consecutive hyphens" {
    result=$(session_name_sanitize "Test---Session")
    [ "$result" = "test-session" ]
}

@test "session_name_sanitize should remove leading and trailing hyphens" {
    result=$(session_name_sanitize "-Test-Session-")
    [ "$result" = "test-session" ]
}

@test "generate_session_name should create proper session names" {
    result=$(generate_session_name "project" "feature" "dev")
    [ "$result" = "project-feature-dev" ]
}

@test "generate_session_name should work without task suffix" {
    result=$(generate_session_name "project" "feature")
    [ "$result" = "project-feature" ]
}

@test "generate_session_name should fail with missing required parameters" {
    run generate_session_name "" "feature"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Project and worktree names are required" ]]
}

@test "session_exists should return false for non-existent session" {
    run session_exists "non-existent-session-xyz"
    [ "$status" -ne 0 ]
}

@test "create_session should create a new tmux session" {
    run create_session "$TEST_SESSION" "$HOME"
    [ "$status" -eq 0 ]
    
    # Verify session was created
    run session_exists "$TEST_SESSION"
    [ "$status" -eq 0 ]
}

@test "create_session should fail with invalid working directory" {
    run create_session "$TEST_SESSION" "/non/existent/directory"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Working directory does not exist" ]]
}

@test "create_session should fail if session already exists" {
    # Create initial session
    create_session "$TEST_SESSION" "$HOME"
    
    # Try to create again
    run create_session "$TEST_SESSION" "$HOME"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "already exists" ]]
}

@test "list_sessions should list created sessions" {
    # Create a test session
    create_session "$TEST_SESSION" "$HOME"
    
    # List sessions
    result=$(list_sessions "$TEST_PREFIX")
    [[ "$result" =~ "$TEST_SESSION" ]]
}

@test "kill_session should terminate an existing session" {
    # Create a test session
    create_session "$TEST_SESSION" "$HOME"
    
    # Kill it
    run kill_session "$TEST_SESSION"
    [ "$status" -eq 0 ]
    
    # Verify it's gone
    run session_exists "$TEST_SESSION"
    [ "$status" -ne 0 ]
}

@test "kill_session should fail for non-existent session" {
    run kill_session "non-existent-session-xyz"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "does not exist" ]]
}

@test "get_session_working_dir should return session path" {
    # Create a test session with known directory
    create_session "$TEST_SESSION" "$HOME"
    
    # Get working directory
    result=$(get_session_working_dir "$TEST_SESSION")
    [ "$result" = "$HOME" ]
}

@test "is_session_attached should return false for detached session" {
    # Create a detached session
    create_session "$TEST_SESSION" "$HOME"
    
    # Check attachment status
    run is_session_attached "$TEST_SESSION"
    [ "$status" -ne 0 ]
}

@test "validate_working_directory should succeed for valid directory" {
    run validate_working_directory "$HOME"
    [ "$status" -eq 0 ]
}

@test "validate_working_directory should fail for non-existent directory" {
    run validate_working_directory "/non/existent/path"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "does not exist" ]]
}

@test "find_project_sessions should find sessions by project name" {
    # Create test sessions
    create_session "${TEST_PREFIX}-project-feature1-dev" "$HOME"
    create_session "${TEST_PREFIX}-project-feature2-dev" "$HOME"
    
    # Find project sessions
    result=$(find_project_sessions "${TEST_PREFIX}-project")
    [[ "$result" =~ "feature1" ]]
    [[ "$result" =~ "feature2" ]]
}