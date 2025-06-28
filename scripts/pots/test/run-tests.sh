#!/bin/bash

# Run all POTS tests

set -e

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if bats is installed
if ! command -v bats >/dev/null 2>&1; then
    echo "Error: bats is not installed. Please install bats-core to run tests."
    echo "Install with: brew install bats-core (on macOS)"
    exit 1
fi

echo "Running POTS test suite..."
echo

# Run each test file
for test_file in "$SCRIPT_DIR"/*.bats; do
    if [ -f "$test_file" ]; then
        echo "Running $(basename "$test_file")..."
        bats "$test_file"
        echo
    fi
done

echo "All tests completed!"