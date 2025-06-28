#!/usr/bin/env bats

# Test worktree-sync.sh functions

setup() {
    # Load the worktree sync utilities
    source "${BATS_TEST_DIRNAME}/../lib/worktree-sync.sh"
    
    # Set test variables
    TEST_WORKTREE_PATH="/Users/brian/code/prunejuice-test"
    TEST_PROJECT="prunejuice"
}

@test "parse_worktree_info should extract path and branch" {
    worktree_line="/Users/brian/code/prunejuice-help          7dd53aa [prunejuice-help]"
    result=$(parse_worktree_info "$worktree_line")
    
    # Extract path and branch from result
    path="${result%%:*}"
    branch="${result#*:}"
    
    [ "$path" = "/Users/brian/code/prunejuice-help" ]
    [ "$branch" = "prunejuice-help" ]
}

@test "extract_project_name should identify prunejuice project" {
    result=$(extract_project_name "/Users/brian/code/prunejuice-help")
    [ "$result" = "prunejuice" ]
}

@test "extract_project_name should handle base project directory" {
    result=$(extract_project_name "/Users/brian/code/prunejuice")
    [ "$result" = "prunejuice" ]
}

@test "extract_worktree_name should extract worktree suffix" {
    result=$(extract_worktree_name "/Users/brian/code/prunejuice-help")
    [ "$result" = "help" ]
}

@test "extract_worktree_name should handle complex suffixes" {
    result=$(extract_worktree_name "/Users/brian/code/prunejuice-phase-4-impl")
    [ "$result" = "phase-4-impl" ]
}

@test "generate_session_from_worktree should create proper session name" {
    result=$(generate_session_from_worktree "/Users/brian/code/prunejuice-help" "dev")
    [ "$result" = "prunejuice-help-dev" ]
}

@test "generate_session_from_worktree should use default task" {
    result=$(generate_session_from_worktree "/Users/brian/code/prunejuice-help")
    [ "$result" = "prunejuice-help-dev" ]
}

@test "find_worktree_sessions should match worktree pattern" {
    # Create test sessions
    tmux new-session -d -s "prunejuice-test-dev" -c "$HOME" 2>/dev/null || true
    tmux new-session -d -s "prunejuice-test-backend" -c "$HOME" 2>/dev/null || true
    
    # Find sessions for worktree
    result=$(find_worktree_sessions "/Users/brian/code/prunejuice-test")
    
    # Clean up
    tmux kill-session -t "prunejuice-test-dev" 2>/dev/null || true
    tmux kill-session -t "prunejuice-test-backend" 2>/dev/null || true
    
    # Verify results
    [[ "$result" =~ "prunejuice-test-dev" ]]
    [[ "$result" =~ "prunejuice-test-backend" ]]
}

@test "validate_session_worktree should fail for non-worktree session" {
    # Create a session in a non-worktree directory
    tmux new-session -d -s "test-session" -c "$HOME" 2>/dev/null
    
    # Validate (should fail since $HOME is not a worktree)
    run validate_session_worktree "test-session"
    
    # Clean up
    tmux kill-session -t "test-session" 2>/dev/null || true
    
    [ "$status" -ne 0 ]
}

@test "create_worktree_session should validate worktree path" {
    # Try to create session for non-worktree directory
    run create_worktree_session "$HOME" "dev"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "not a valid worktree" ]]
}

# Integration test (requires actual worktree)
@test "get_worktrees_from_plum should list worktrees" {
    # Skip if not in a git repo with worktrees
    if ! command -v git >/dev/null 2>&1 || ! git worktree list >/dev/null 2>&1; then
        skip "Git worktrees not available"
    fi
    
    result=$(get_worktrees_from_plum)
    [ -n "$result" ]
}

# Test cleanup functions
teardown() {
    # Clean up any test sessions created
    tmux list-sessions -F "#{session_name}" 2>/dev/null | grep "^prunejuice-test" | while read -r session; do
        tmux kill-session -t "$session" 2>/dev/null || true
    done
}