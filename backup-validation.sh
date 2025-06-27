#!/bin/bash
# backup-validation.sh - Validate backup completeness and test restoration

validate_backup() {
    local backup_dir="$1"
    
    echo "Validating backup in: $backup_dir"
    
    # Check critical files exist
    critical_files=(
        "scripts/worktree-manager/worktree-create"
        "scripts/worktree-cli.sh"
        "scripts/worktree-manager/lib/config.sh"
        "scripts/worktree-manager/lib/git-utils.sh"
        "scripts/worktree-manager/lib/files.sh"
        "scripts/worktree-manager/lib/mcp.sh"
        "scripts/worktree-manager/lib/ui.sh"
        "scripts/worktree-manager/worktree-config"
        "CLAUDE.md"
        ".claude/settings.local.json"
    )
    
    for file in "${critical_files[@]}"; do
        if [ ! -f "$backup_dir/$file" ]; then
            echo "ERROR: Missing critical file: $file"
            return 1
        fi
    done
    
    # Check executability
    if [ ! -x "$backup_dir/scripts/worktree-manager/worktree-create" ]; then
        echo "ERROR: worktree-create is not executable"
        return 1
    fi
    
    # Check directory structure
    if [ ! -d "$backup_dir/scripts/worktree-manager/lib" ]; then
        echo "ERROR: Missing lib directory"
        return 1
    fi
    
    echo "✓ Backup validation passed"
    return 0
}

test_restoration() {
    local backup_dir="$1"
    local test_dir="test-restore"
    local original_dir="$(pwd)"
    
    echo "Testing restoration process..."
    
    # Create test restoration in current directory
    rm -rf "$test_dir"
    cp -r "$backup_dir" "$test_dir"
    
    # Test basic functionality in restored copy
    cd "$test_dir"
    if ./scripts/worktree-manager/worktree-create --config >/dev/null 2>&1; then
        echo "✓ Restoration test passed"
        cd "$original_dir"
        rm -rf "$test_dir"
        return 0
    else
        echo "ERROR: Restored system failed basic functionality test"
        cd "$original_dir"
        rm -rf "$test_dir"
        return 1
    fi
}

# Main execution
backup_dir="${1:-backups/pre-plum-migration}"

if [ ! -d "$backup_dir" ]; then
    echo "ERROR: Backup directory not found: $backup_dir"
    exit 1
fi

echo "=== Backup Validation ==="
if validate_backup "$backup_dir"; then
    echo
    echo "=== Restoration Test ==="
    if test_restoration "$backup_dir"; then
        echo
        echo "✅ All validation tests passed!"
        echo "Backup is complete and restoration process verified."
    else
        echo "❌ Restoration test failed!"
        exit 1
    fi
else
    echo "❌ Backup validation failed!"
    exit 1
fi