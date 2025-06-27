# External Dependencies Map - worktree-manager → plum Migration

## Overview

Comprehensive mapping of all external dependencies and references that will be affected by the migration from worktree-manager to plum tool.

## External Reference Analysis

### Claude Code Integration (HIGH IMPACT)

#### .claude/settings.local.json
**Critical external dependency requiring immediate updates**

Current references requiring updates:
```json
{
  "permissions": {
    "allow": [
      "Bash(../../scripts/worktree-manager/worktree-create:*)",
      "Bash(WORKTREE_GITHUB_USERNAME=brian ../../scripts/worktree-manager/worktree-create:*)",
      "Bash(WORKTREE_EDITOR=echo ../../scripts/worktree-manager/worktree-create test-actual)",
      "Bash(WORKTREE_EDITOR=echo ../../scripts/worktree-manager/worktree-create --mcp dwh test-mcp)",
      "Bash(WORKTREE_EDITOR=echo WORKTREE_GITHUB_USERNAME=brian ../../scripts/worktree-manager/worktree-create --pattern \"hotfix/{suffix}\" --no-copy-files --from main urgent-fix)",
      "Bash(./scripts/worktree-manager/lib/security.sh:*)"
    ]
  }
}
```

**Required Updates:**
```json
{
  "permissions": {
    "allow": [
      "Bash(../../scripts/plum/plum:*)",
      "Bash(PLUM_GITHUB_USERNAME=brian ../../scripts/plum/plum:*)",
      "Bash(PLUM_EDITOR=echo ../../scripts/plum/plum test-actual)",
      "Bash(PLUM_EDITOR=echo ../../scripts/plum/plum --mcp dwh test-mcp)",
      "Bash(PLUM_EDITOR=echo PLUM_GITHUB_USERNAME=brian ../../scripts/plum/plum --pattern \"hotfix/{suffix}\" --no-copy-files --from main urgent-fix)",
      "Bash(./scripts/plum/lib/security.sh:*)"
    ]
  }
}
```

**Impact Level**: 🔴 **CRITICAL** - Claude Code permissions will break without updates

### User Environment Dependencies (HIGH IMPACT)

#### User Shell Configuration Files
**Potential external dependencies in user environments**

Common locations that may contain references:
- `~/.bashrc`
- `~/.zshrc` 
- `~/.bash_profile`
- `~/.profile`
- `~/.aliases`

**Potential References:**
```bash
# User aliases (if any exist)
alias wtree="./scripts/worktree-manager/worktree-create"
alias wt-create="./scripts/worktree-manager/worktree-create"

# Environment variables (if customized)
export WORKTREE_GITHUB_USERNAME="username"
export WORKTREE_EDITOR="code"

# PATH additions (if symlinked)
export PATH="$PATH:/path/to/project/scripts/worktree-manager"
```

**Required User Actions:**
- Update any custom aliases to use new paths/commands
- Update environment variable names (WORKTREE_* → PLUM_*)
- Update any PATH additions

**Impact Level**: 🟡 **HIGH** - User environment may break without manual updates

### User Configuration Files (MEDIUM IMPACT)

#### ~/.config/worktree-manager/config
**User-specific configuration directory**

Current analysis shows:
- ✅ **No existing user configurations found** in current environment
- ❓ **Potential user configurations** on other systems

**Migration Requirements:**
```bash
# OLD location
~/.config/worktree-manager/config

# NEW location (recommended)
~/.config/plum/config

# Migration command
mv ~/.config/worktree-manager ~/.config/plum 2>/dev/null || echo "No user config to migrate"
```

**Impact Level**: 🟡 **MEDIUM** - Affects users with custom configurations

### External Scripts and Automation (MEDIUM IMPACT)

#### CI/CD and Automation Scripts
**External scripts that may call worktree-manager**

Current analysis shows:
- ✅ **No CI/CD references found** in current project
- ✅ **No automation scripts found** referencing worktree-manager
- ❓ **Potential external scripts** on user systems or other projects

**Potential External References:**
```bash
# Build scripts
./scripts/worktree-manager/worktree-create feature-branch

# Development automation
WORKTREE_EDITOR=nvim ./scripts/worktree-manager/worktree-create

# CI/CD pipelines (example)
- name: Create test worktree
  run: ./scripts/worktree-manager/worktree-create test-${{ github.run_id }}
```

**Impact Level**: 🟡 **MEDIUM** - External automation may break

### Project Documentation References (LOW-MEDIUM IMPACT)

#### README and Documentation Files
**Documentation files containing examples and references**

Files requiring updates (126 total references found):
- `scripts/worktree-manager/README.md` (primary documentation)
- `CLAUDE.md` (project instructions)
- `guide.md` (refactoring context)
- All phase documentation files (created during this migration)

**Reference Types:**
1. **Installation commands**: Path references in setup instructions
2. **Usage examples**: Command examples with worktree-create
3. **Configuration examples**: Environment variable examples
4. **Troubleshooting guides**: References to tool names and paths

**Impact Level**: 🟢 **LOW-MEDIUM** - Documentation inconsistency, no functional impact

## External Tool Integration Points

### GitHub CLI Integration
**gh command integration**

Current status:
- ✅ **No breaking changes** - GitHub CLI usage is internal
- ✅ **No external references** to update
- ✅ **Functionality unchanged** after migration

### gum (Interactive CLI) Integration
**gum command integration**

Current status:
- ✅ **No breaking changes** - gum usage is internal
- ✅ **No external references** to update
- ✅ **Functionality unchanged** after migration

### Editor Integration
**External editor integration**

Current status:
- ✅ **No breaking changes** - Editor commands unchanged
- ✅ **Configuration method changes** - Environment variable names
- 🟡 **User impact** - Variable name changes (WORKTREE_EDITOR → PLUM_EDITOR)

## Symlinks and PATH Dependencies

### System-wide Installation
**Potential symlinks to worktree-manager tools**

Common installation patterns that may exist:
```bash
# Symlinks that would break
ln -s /path/to/project/scripts/worktree-manager/worktree-create /usr/local/bin/worktree-create
ln -s /path/to/project/scripts/worktree-manager/worktree-create ~/bin/wt-create

# PATH additions that would break
export PATH="$PATH:/path/to/project/scripts/worktree-manager"
```

**Impact Level**: 🟡 **MEDIUM** - System-wide installations may break

## Third-Party Integration

### IDE Extensions or Plugins
**Potential IDE integrations**

Current analysis:
- ✅ **No known IDE extensions** using worktree-manager
- ❓ **Potential custom integrations** in user environments
- 📝 **VS Code tasks** may reference worktree-manager paths

### External Projects
**Other projects that may depend on worktree-manager**

Current analysis:
- ✅ **No known external projects** depending on this tool
- ❓ **Potential forks or derivatives** using current names
- ❓ **User projects** with hardcoded references

## Migration Communication Plan

### High Priority Communications
1. **Claude Code users**: Settings file requires immediate updates
2. **Users with custom configs**: Environment variable changes
3. **Users with aliases/symlinks**: Command name and path changes

### Medium Priority Communications
1. **Documentation updates**: New tool names and examples
2. **External script owners**: Automation requiring updates
3. **Tutorial and guide authors**: Example code updates

### Communication Channels
- **Project README**: Migration guide and breaking changes notice
- **CHANGELOG**: Detailed list of breaking changes
- **GitHub Releases**: Migration instructions and compatibility notes

## Backward Compatibility Strategy

### Option 1: Hard Migration (Recommended)
- **Pros**: Clean break, clear new identity, no confusion
- **Cons**: All external references break immediately
- **Recommendation**: ✅ **Recommended** for clarity

### Option 2: Symlink Compatibility
- **Pros**: Maintains backward compatibility temporarily
- **Cons**: Confusion between old/new names, maintenance overhead
- **Recommendation**: ❌ Not recommended

### Option 3: Deprecation Period
- **Pros**: Gradual migration, less user disruption
- **Cons**: Complex to maintain, delayed benefits
- **Recommendation**: ❌ Not recommended for tool this size

## Risk Assessment by Category

### 🔴 CRITICAL (Immediate attention required)
- **Claude Code settings**: Will break Claude integration
- **Scope**: All users using Claude Code with current permissions

### 🟡 HIGH (User action required)
- **User aliases and scripts**: May break user workflows
- **Environment variables**: User configurations need updates
- **Scope**: Power users with custom setups

### 🟡 MEDIUM (May cause confusion)
- **Documentation**: Outdated examples and instructions
- **External automation**: Scripts calling worktree-manager
- **Scope**: Users following documentation or using automation

### 🟢 LOW (Cosmetic impact)
- **Internal references**: Function names, comments
- **Optional updates**: Non-breaking improvements
- **Scope**: Code maintainers and contributors

## Validation Checklist

### Pre-Migration Validation
- [ ] Identify all user environments that may have custom configurations
- [ ] Document all known external scripts or automation
- [ ] Backup all critical configuration files
- [ ] Prepare migration instructions for each dependency type

### Post-Migration Validation
- [ ] Update Claude Code settings and test integration
- [ ] Verify no broken symlinks or PATH references
- [ ] Test common user workflows with new tool names
- [ ] Validate documentation accuracy and completeness

### User Support
- [ ] Create migration guide for common scenarios
- [ ] Provide troubleshooting guide for broken references
- [ ] Document rollback procedures if needed
- [ ] Plan user communication timeline