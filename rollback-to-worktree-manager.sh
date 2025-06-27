#!/bin/bash
# rollback-to-worktree-manager.sh - Complete rollback procedure

rollback_system() {
    echo "Starting rollback to worktree-manager system..."
    echo
    echo "This will:"
    echo "  - Reset to pre-migration state (tag: v-pre-plum-migration)"
    echo "  - Restore user configuration files from backup"
    echo "  - Revert all plum changes back to worktree-manager"
    echo
    
    # Confirm rollback intent
    read -p "Continue with rollback? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Rollback cancelled"
        return 1
    fi
    
    echo
    echo "Starting rollback process..."
    
    # Check if we're in the right directory
    if [ ! -f "scripts/worktree-manager/worktree-create" ] && [ ! -f "scripts/plum/plum" ]; then
        echo "ERROR: Not in prunejuice project directory"
        return 1
    fi
    
    # Check if backup tag exists
    if ! git tag -l | grep -q "v-pre-plum-migration"; then
        echo "ERROR: Backup tag 'v-pre-plum-migration' not found"
        echo "Cannot perform safe rollback without backup point"
        return 1
    fi
    
    # Switch to main branch
    echo "Switching to main branch..."
    git checkout main
    
    # Reset to pre-migration tag
    echo "Resetting to pre-migration state..."
    git reset --hard v-pre-plum-migration
    
    # Restore user configuration files if they exist in backup
    echo "Restoring user configuration files..."
    
    if [ -f backups/user-configs/config ]; then
        echo "  Restoring worktree-manager config..."
        mkdir -p ~/.config/worktree-manager/
        cp backups/user-configs/config ~/.config/worktree-manager/
    fi
    
    if [ -f backups/user-configs/settings.json ]; then
        echo "  Restoring Claude settings.json..."
        cp backups/user-configs/settings.json ~/.claude/
    fi
    
    if [ -f backups/user-configs/settings.local.json ]; then
        echo "  Restoring Claude settings.local.json..."
        cp backups/user-configs/settings.local.json ~/.claude/
    fi
    
    # Clean up any potential plum artifacts
    echo "Cleaning up migration artifacts..."
    rm -f scripts/plum* 2>/dev/null || true
    rm -rf scripts/plum/ 2>/dev/null || true
    
    echo
    echo "✅ Rollback completed successfully!"
    echo
    echo "The system has been restored to the pre-migration state."
    echo "All worktree-manager functionality should be available."
    echo
    echo "Recommended next steps:"
    echo "  1. Test worktree-manager functionality"
    echo "  2. Restart any active worktree sessions"
    echo "  3. Verify MCP templates still work"
    echo
    
    return 0
}

show_backup_status() {
    echo "=== Backup Status ==="
    echo
    
    if git tag -l | grep -q "v-pre-plum-migration"; then
        echo "✅ Backup tag found: v-pre-plum-migration"
        git show --stat v-pre-plum-migration | head -10
    else
        echo "❌ Backup tag not found: v-pre-plum-migration"
    fi
    
    echo
    echo "=== Available Backups ==="
    
    if [ -d "backups/pre-plum-migration" ]; then
        echo "✅ System backup: backups/pre-plum-migration/"
        ls -la backups/pre-plum-migration/ | head -5
    else
        echo "❌ System backup not found: backups/pre-plum-migration/"
    fi
    
    if [ -d "backups/user-configs" ]; then
        echo "✅ User configs backup: backups/user-configs/"
        ls -la backups/user-configs/
    else
        echo "❌ User configs backup not found: backups/user-configs/"
    fi
    
    if ls backups/prunejuice-pre-plum-*.tar.gz >/dev/null 2>&1; then
        echo "✅ Compressed backup:"
        ls -la backups/prunejuice-pre-plum-*.tar.gz
    else
        echo "❌ Compressed backup not found"
    fi
}

# Main execution
case "${1:-status}" in
    "rollback"|"restore")
        rollback_system
        ;;
    "status"|"check")
        show_backup_status
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  rollback, restore  - Perform complete rollback to worktree-manager"
        echo "  status, check      - Show backup status and availability"
        echo "  help              - Show this help message"
        echo
        echo "Examples:"
        echo "  $0 status          - Check backup availability"
        echo "  $0 rollback        - Perform complete rollback"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac