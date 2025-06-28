#!/usr/bin/env bats

# Test pots command-line interface

setup() {
    # Path to pots executable
    POTS="${BATS_TEST_DIRNAME}/../pots"
    
    # Test worktree path (should be an actual worktree)
    TEST_WORKTREE="/Users/brian/code/prunejuice-help"
    
    # Test session name
    TEST_SESSION="bats-test-session"
}

teardown() {
    # Clean up any test sessions
    tmux kill-session -t "$TEST_SESSION" 2>/dev/null || true
    tmux list-sessions -F "#{session_name}" 2>/dev/null | grep "^bats-" | while read -r session; do
        tmux kill-session -t "$session" 2>/dev/null || true
    done
}

@test "pots should show help with --help" {
    run "$POTS" --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "POTS - tmux Session Manager for Worktrees" ]]
}

@test "pots should show help with no arguments" {
    run "$POTS"
    [ "$status" -eq 1 ]
    [[ "$output" =~ "POTS - tmux Session Manager for Worktrees" ]]
}

@test "pots create --help should show create help" {
    run "$POTS" create --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Creates a new tmux session" ]]
}

@test "pots list should work with no sessions" {
    # Kill all test sessions first
    tmux list-sessions -F "#{session_name}" 2>/dev/null | grep "^prunejuice-" | while read -r session; do
        tmux kill-session -t "$session" 2>/dev/null || true
    done
    
    run "$POTS" list
    [ "$status" -eq 0 ]
    [[ "$output" =~ "No tmux sessions found" ]]
}

@test "pots create should create a session for valid worktree" {
    # Skip if worktree doesn't exist
    if [ ! -d "$TEST_WORKTREE" ]; then
        skip "Test worktree not available"
    fi
    
    run "$POTS" create --no-attach "$TEST_WORKTREE"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Created session" ]]
    
    # Verify session was created
    tmux has-session -t "prunejuice-help-dev" 2>/dev/null
    
    # Clean up
    tmux kill-session -t "prunejuice-help-dev" 2>/dev/null || true
}

@test "pots create should fail for non-existent directory" {
    run "$POTS" create --no-attach "/non/existent/path"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Working directory does not exist" ]]
}

@test "pots create with --task should use custom task name" {
    # Skip if worktree doesn't exist
    if [ ! -d "$TEST_WORKTREE" ]; then
        skip "Test worktree not available"
    fi
    
    run "$POTS" create --no-attach --task backend "$TEST_WORKTREE"
    [ "$status" -eq 0 ]
    
    # Verify session with custom task was created
    tmux has-session -t "prunejuice-help-backend" 2>/dev/null
    
    # Clean up
    tmux kill-session -t "prunejuice-help-backend" 2>/dev/null || true
}

@test "pots list should show created sessions" {
    # Create a test session manually
    tmux new-session -d -s "$TEST_SESSION" -c "$HOME" 2>/dev/null
    
    run "$POTS" list
    [ "$status" -eq 0 ]
    [[ "$output" =~ "$TEST_SESSION" ]]
}

@test "pots list --verbose should show detailed information" {
    # Create a test session manually
    tmux new-session -d -s "$TEST_SESSION" -c "$HOME" 2>/dev/null
    
    run "$POTS" list --verbose
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Session: $TEST_SESSION" ]]
    [[ "$output" =~ "Working Directory:" ]]
    [[ "$output" =~ "Created:" ]]
    [[ "$output" =~ "Attached:" ]]
}

@test "pots list with filter should filter results" {
    # Create test sessions
    tmux new-session -d -s "bats-test-1" -c "$HOME" 2>/dev/null
    tmux new-session -d -s "bats-test-2" -c "$HOME" 2>/dev/null
    tmux new-session -d -s "other-session" -c "$HOME" 2>/dev/null
    
    run "$POTS" list "bats-test"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "bats-test-1" ]]
    [[ "$output" =~ "bats-test-2" ]]
    [[ ! "$output" =~ "other-session" ]]
    
    # Clean up
    tmux kill-session -t "other-session" 2>/dev/null || true
}

@test "pots kill should terminate a session" {
    # Create a test session
    tmux new-session -d -s "$TEST_SESSION" -c "$HOME" 2>/dev/null
    
    # Kill it with force flag
    run "$POTS" kill --force "$TEST_SESSION"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Killed session" ]]
    
    # Verify it's gone
    ! tmux has-session -t "$TEST_SESSION" 2>/dev/null
}

@test "pots kill should fail for non-existent session" {
    run "$POTS" kill --force "non-existent-session-xyz"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "does not exist" ]]
}

@test "pots cleanup --dry-run should preview cleanup" {
    run "$POTS" cleanup --dry-run
    [ "$status" -eq 0 ]
    [[ "$output" =~ "orphaned sessions" ]] || [[ "$output" =~ "No orphaned sessions" ]]
}

@test "pots should handle unknown commands" {
    run "$POTS" unknown-command
    [ "$status" -eq 1 ]
    [[ "$output" =~ "Unknown command" ]]
}

@test "pots should handle unknown options" {
    run "$POTS" --unknown-option
    [ "$status" -eq 1 ]
    [[ "$output" =~ "Unknown option" ]]
}