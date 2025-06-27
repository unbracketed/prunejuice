# Backup Procedures - PruneJuice Migration

## Overview

This document outlines the comprehensive backup and restoration procedures created for the safe migration from worktree-manager to plum. All backup procedures have been implemented and validated.

## Backup Components

### 1. Git-Based Backup
- **Migration branch**: `plum-migration` - All migration work isolated
- **Backup tag**: `v-pre-plum-migration` - Exact state before any changes
- **Purpose**: Enables clean Git-based rollback to known good state

### 2. Complete System Backup
- **Location**: `backups/pre-plum-migration/`
- **Contents**: Full project directory (excluding .git)
- **Purpose**: Complete filesystem-level backup for restoration

### 3. Compressed Archive
- **Location**: `backups/prunejuice-pre-plum-TIMESTAMP.tar.gz`
- **Contents**: Complete system backup in portable format
- **Purpose**: Archival storage and external backup

### 4. User Configuration Backup
- **Location**: `backups/user-configs/`
- **Contents**: User-specific configuration files
- **Files Backed Up**:
  - `~/.config/worktree-manager/config` (if exists)
  - `~/.claude/settings.json` (if exists)  
  - `~/.claude/settings.local.json` (if exists)

### 5. System State Documentation
- **Location**: `backups/`
- **Files Created**:
  - `current-worktrees.txt` - Active worktree states
  - `current-branches.txt` - All Git branches
  - `current-git-config.txt` - Git configuration
  - `current-worktree-env.txt` - WORKTREE_* environment variables
  - `current-config-output.txt` - Current system configuration

## Backup Scripts

### backup-validation.sh
**Purpose**: Validate backup completeness and test restoration

**Features**:
- Validates all critical files are present
- Checks executable permissions
- Tests restoration process in isolated environment
- Confirms restored system passes functionality tests

**Usage**:
```bash
./backup-validation.sh [backup-directory]
```

**Validation Checks**:
- [x] All critical source files present
- [x] Executable permissions preserved
- [x] Directory structure intact
- [x] Restoration process works
- [x] Restored system passes functionality tests

### rollback-to-worktree-manager.sh
**Purpose**: Complete rollback to pre-migration state

**Features**:
- Interactive confirmation before rollback
- Git-based restoration to tagged state
- User configuration file restoration
- Cleanup of migration artifacts
- Status checking and backup validation

**Usage**:
```bash
# Check backup status
./rollback-to-worktree-manager.sh status

# Perform complete rollback
./rollback-to-worktree-manager.sh rollback
```

**Rollback Process**:
1. Confirms user intent with detailed explanation
2. Switches to main branch
3. Resets to `v-pre-plum-migration` tag
4. Restores user configuration files from backup
5. Cleans up any migration artifacts
6. Provides post-rollback verification steps

## Backup Validation Results

### ✅ Backup Completeness
- All critical files preserved in backup
- All configuration files captured
- User settings and preferences backed up
- Git state and worktree information documented

### ✅ Restoration Process
- Backup validation script passes all checks
- Test restoration to isolated location succeeds
- Restored system passes functionality tests
- Rollback procedures documented and accessible

### ✅ Git State Preservation
- Migration branch created successfully: `plum-migration`
- Pre-migration tag created and available: `v-pre-plum-migration`
- Current worktree states documented in `backups/current-worktrees.txt`
- Branch and configuration states captured

## Backup File Inventory

```
backups/
├── pre-plum-migration/                    # Complete system backup
│   ├── scripts/worktree-manager/         # Original tool directory
│   ├── .claude/settings.local.json       # Project Claude settings
│   ├── CLAUDE.md                         # Project instructions
│   └── [all other project files]
├── user-configs/                         # User-specific configurations
│   └── settings.local.json              # User Claude settings
├── prunejuice-pre-plum-TIMESTAMP.tar.gz # Compressed archive
├── current-worktrees.txt                # Worktree state snapshot
├── current-branches.txt                 # Git branch snapshot
├── current-git-config.txt               # Git configuration
├── current-worktree-env.txt             # Environment variables
└── current-config-output.txt            # System configuration
```

## Recovery Procedures

### Quick Recovery (Git-based)
For situations where only source code needs to be restored:
```bash
git checkout main
git reset --hard v-pre-plum-migration
```

### Complete Recovery (Full restoration)
For situations requiring complete system restoration:
```bash
./rollback-to-worktree-manager.sh rollback
```

### Manual Recovery (Filesystem-based)
For situations where scripts are unavailable:
```bash
# Remove current system
rm -rf scripts/

# Restore from backup
cp -r backups/pre-plum-migration/* .

# Restore user configs manually
cp backups/user-configs/* ~/.claude/ 2>/dev/null || true
```

### Archive-based Recovery
For recovery from compressed backup:
```bash
# Extract archive
tar -xzf backups/prunejuice-pre-plum-*.tar.gz -C recovery/

# Copy to current location
cp -r recovery/pre-plum-migration/* .
```

## Verification After Recovery

### System Functionality Test
```bash
# Test basic functionality
./scripts/worktree-manager/worktree-create --config

# Test dry run
./scripts/worktree-manager/worktree-create --dry-run test

# Test interactive CLI
echo "q" | ./scripts/worktree-cli.sh
```

### Configuration Verification
```bash
# Check environment variables
env | grep WORKTREE_

# Verify file permissions
ls -la scripts/worktree-manager/worktree-create

# Test MCP integration (if applicable)
./scripts/worktree-manager/worktree-create --mcp
```

## Security Considerations

### Backup Security
- Backups contain project source code and configurations
- Claude settings may contain sensitive MCP configurations
- Store backups in secure location if needed
- Consider encryption for sensitive environments

### Rollback Safety
- All rollback procedures preserve current work in migration branch
- Git tags provide safe restoration points
- User data is preserved during rollback process
- No data loss should occur during properly executed rollback

## Next Steps

With comprehensive backup procedures validated and in place:

1. **Migration can proceed safely** knowing rollback is always available
2. **Continue to Phase 1, Task 3**: Impact Analysis with confidence
3. **Begin actual migration work** in isolated `plum-migration` branch
4. **Regular validation** of backup integrity throughout migration process

## Emergency Contacts

If rollback procedures fail or backup corruption is suspected:
1. **Stop all migration work immediately**
2. **Do not modify any backup files**
3. **Use Git tag `v-pre-plum-migration` as authoritative source**
4. **Restore from compressed archive as last resort**