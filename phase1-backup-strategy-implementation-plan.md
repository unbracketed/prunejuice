# Phase 1: Backup Strategy - Implementation Plan

## Objective
Create a comprehensive backup and restoration strategy to ensure safe migration from the current worktree-manager system to the new plum tool, with full rollback capability.

## Requirements Analysis

### 1. Create Comprehensive Backup of Working System
- **Requirement**: Preserve all current functionality and configurations
- **Scope**: Source code, configurations, documentation, user settings
- **Output**: Complete system snapshot with restoration procedures

### 2. Document Current Worktree Configurations
- **Requirement**: Capture all active worktree states and settings
- **Scope**: Git worktree list, branch states, MCP configurations
- **Output**: Configuration inventory for validation after migration

### 3. Test Backup Restoration Procedures
- **Requirement**: Verify backup integrity and restoration process
- **Scope**: Full system restore, functionality verification
- **Output**: Validated restoration procedures and rollback plan

## Implementation Steps

### Step 1: Create Git Branch for Migration
```bash
# Create development branch for migration work
git checkout -b plum-migration
git push -u origin plum-migration

# Tag current state as backup reference
git tag -a v-pre-plum-migration -m "Pre-migration backup point"
git push origin v-pre-plum-migration
```

### Step 2: Create Complete System Backup
```bash
# Create backup directory
mkdir -p backups/pre-plum-migration

# Backup entire project (excluding .git to save space)
rsync -av --exclude='.git' /Users/brian/code/prunejuice/ backups/pre-plum-migration/

# Create compressed archive
tar -czf backups/prunejuice-pre-plum-$(date +%Y%m%d-%H%M%S).tar.gz -C backups pre-plum-migration/

# Backup user configuration files
mkdir -p backups/user-configs
[ -f ~/.config/worktree-manager/config ] && cp ~/.config/worktree-manager/config backups/user-configs/
[ -f ~/.claude/settings.json ] && cp ~/.claude/settings.json backups/user-configs/
[ -f ~/.claude/settings.local.json ] && cp ~/.claude/settings.local.json backups/user-configs/
```

### Step 3: Document Current Worktree State
```bash
# Capture current worktree configuration
git worktree list > backups/current-worktrees.txt

# Capture current branch states
git branch -a > backups/current-branches.txt

# Capture current git configuration
git config --list > backups/current-git-config.txt

# Document current environment variables
env | grep WORKTREE_ > backups/current-worktree-env.txt 2>/dev/null || touch backups/current-worktree-env.txt
```

### Step 4: Test Current System Functionality
```bash
# Create test worktree to verify current functionality
./scripts/worktree-manager/worktree-create --dry-run backup-test

# Test interactive CLI (non-destructive)
echo "q" | ./scripts/worktree-cli.sh >/dev/null 2>&1 || echo "Interactive CLI test completed"

# Test configuration display
./scripts/worktree-manager/worktree-create --config > backups/current-config-output.txt
```

### Step 5: Create Backup Validation Script
Create script to validate backup integrity and test restoration:

```bash
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
    
    echo "✓ Backup validation passed"
    return 0
}

test_restoration() {
    local backup_dir="$1"
    local test_dir="/tmp/prunejuice-restore-test"
    
    echo "Testing restoration process..."
    
    # Create test restoration
    rm -rf "$test_dir"
    cp -r "$backup_dir" "$test_dir"
    
    # Test basic functionality in restored copy
    cd "$test_dir"
    if ./scripts/worktree-manager/worktree-create --config >/dev/null 2>&1; then
        echo "✓ Restoration test passed"
        rm -rf "$test_dir"
        return 0
    else
        echo "ERROR: Restored system failed basic functionality test"
        rm -rf "$test_dir"
        return 1
    fi
}
```

### Step 6: Create Rollback Procedures
Document complete rollback process:

```bash
#!/bin/bash
# rollback-to-worktree-manager.sh - Complete rollback procedure

rollback_system() {
    echo "Starting rollback to worktree-manager system..."
    
    # Confirm rollback intent
    read -p "This will restore the pre-migration system. Continue? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Rollback cancelled"
        return 1
    fi
    
    # Switch to main branch
    git checkout main
    
    # Reset to pre-migration tag
    git reset --hard v-pre-plum-migration
    
    # Restore user configuration files
    if [ -f backups/user-configs/config ]; then
        mkdir -p ~/.config/worktree-manager/
        cp backups/user-configs/config ~/.config/worktree-manager/
    fi
    
    # Restore Claude settings if backed up
    if [ -f backups/user-configs/settings.json ]; then
        cp backups/user-configs/settings.json ~/.claude/
    fi
    if [ -f backups/user-configs/settings.local.json ]; then
        cp backups/user-configs/settings.local.json ~/.claude/
    fi
    
    echo "✓ Rollback completed successfully"
    echo "Please restart any active worktree sessions"
}
```

## Validation Steps

### 1. Backup Completeness Validation
- [ ] All source files preserved in backup
- [ ] All configuration files captured
- [ ] User settings and preferences backed up
- [ ] Git state and worktree information documented

### 2. Restoration Process Testing
- [ ] Backup validation script passes
- [ ] Test restoration to temporary location succeeds
- [ ] Restored system passes functionality tests
- [ ] Rollback procedures documented and tested

### 3. Git State Preservation
- [ ] Migration branch created successfully
- [ ] Pre-migration tag created and pushed
- [ ] Current worktree states documented
- [ ] Branch and configuration states captured

## Deliverables

1. **backups/prunejuice-pre-plum-TIMESTAMP.tar.gz**: Complete compressed backup
2. **backups/pre-plum-migration/**: Full system backup directory
3. **backups/user-configs/**: User configuration files backup
4. **backups/current-*.txt**: System state documentation files
5. **backup-validation.sh**: Backup integrity validation script
6. **rollback-to-worktree-manager.sh**: Complete rollback procedure
7. **backup-procedures.md**: Documentation of backup and restoration process

## Success Criteria

- [ ] Complete system backup created and validated
- [ ] All user configurations preserved
- [ ] Current worktree states documented
- [ ] Restoration process tested and verified
- [ ] Rollback procedures documented and accessible
- [ ] Git tags and branches created for safe migration
- [ ] Backup integrity validated with automated scripts

## Risk Mitigation

### Backup Integrity
- Multiple backup formats (directory + compressed archive)
- Automated validation scripts to verify completeness
- Test restoration process before migration begins

### User Data Protection
- Separate backup of user configuration files
- Documentation of current environment variables
- Preservation of active worktree states

### Rollback Safety
- Git tags for easy version restoration
- Complete rollback procedures documented and tested
- User configuration restoration included in rollback

## Next Steps After Completion

1. **Validate all backup procedures** work correctly
2. **Communicate backup location** to stakeholders
3. **Proceed with Phase 1, Task 3**: Impact Analysis
4. **Begin migration** only after backup validation passes