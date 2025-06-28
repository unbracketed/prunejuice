#!/bin/bash

# Manual test script for POTS

set -e

echo "=== POTS Manual Test Suite ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Test counter
TESTS=0
PASSED=0
FAILED=0

# Helper functions
test_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

run_test() {
    local test_name="$1"
    local command="$2"
    local expected_result="$3"  # 0 for success, 1 for failure
    
    ((TESTS++))
    echo -n "Testing: $test_name... "
    
    if eval "$command" >/dev/null 2>&1; then
        if [ "$expected_result" -eq 0 ]; then
            test_pass "OK"
        else
            test_fail "Expected failure but succeeded"
        fi
    else
        if [ "$expected_result" -eq 1 ]; then
            test_pass "OK (expected failure)"
        else
            test_fail "Failed unexpectedly"
        fi
    fi
}

# Get paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POTS="$SCRIPT_DIR/../pots"

# Clean up function
cleanup() {
    echo
    echo "Cleaning up test sessions..."
    tmux list-sessions -F "#{session_name}" 2>/dev/null | grep "^test-pots-" | while read -r session; do
        tmux kill-session -t "$session" 2>/dev/null || true
    done
}

# Set up trap for cleanup
trap cleanup EXIT

echo "1. Testing help commands..."
run_test "pots --help" "$POTS --help" 0
run_test "pots create --help" "$POTS create --help" 0
run_test "pots list --help" "$POTS list --help" 0

echo
echo "2. Testing list command..."
run_test "pots list (empty)" "$POTS list | grep -q 'No tmux sessions found'" 0

echo
echo "3. Testing create command..."
TEST_SESSION="test-pots-manual"
run_test "create session" "tmux new-session -d -s $TEST_SESSION -c $HOME" 0
run_test "pots list (with session)" "$POTS list | grep -q '$TEST_SESSION'" 0

echo
echo "4. Testing session operations..."
run_test "session exists" "tmux has-session -t $TEST_SESSION" 0
run_test "kill session" "$POTS kill --force $TEST_SESSION" 0
run_test "session gone" "tmux has-session -t $TEST_SESSION" 1

echo
echo "5. Testing error cases..."
run_test "create with bad path" "$POTS create --no-attach /non/existent/path" 1
run_test "kill non-existent" "$POTS kill --force non-existent-xyz" 1
run_test "unknown command" "$POTS unknown-command" 1

echo
echo "6. Testing worktree integration..."
if [ -d "/Users/brian/code/prunejuice-help" ]; then
    run_test "create for worktree" "$POTS create --no-attach /Users/brian/code/prunejuice-help" 0
    run_test "verify worktree session" "tmux has-session -t prunejuice-help-dev" 0
    run_test "cleanup worktree session" "tmux kill-session -t prunejuice-help-dev" 0
else
    echo "Skipping worktree tests (worktree not found)"
fi

# Summary
echo
echo "=== Test Summary ==="
echo "Total tests: $TESTS"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi