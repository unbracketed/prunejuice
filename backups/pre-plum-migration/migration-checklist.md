# Migration Checklist - worktree-manager → plum

## Directory and File Renames

### [ ] Primary Directory Structure
- [ ] Rename `scripts/worktree-manager/` → `scripts/plum/`
- [ ] Rename `scripts/worktree-manager/worktree-create` → `scripts/plum/plum`
- [ ] Rename `scripts/worktree-manager/worktree-config` → `scripts/plum/plum-config`
- [ ] Rename `scripts/worktree-cli.sh` → `scripts/plum-cli.sh`

### [ ] Library Directory (no renames needed)
- [ ] Verify `scripts/plum/lib/` structure remains intact
- [ ] Confirm all lib/*.sh files work with new parent directory

## Environment Variable Updates

### [ ] Core Variables (WORKTREE_ → PLUM_)
- [ ] `WORKTREE_GITHUB_USERNAME` → `PLUM_GITHUB_USERNAME`
- [ ] `WORKTREE_EDITOR` → `PLUM_EDITOR`
- [ ] `WORKTREE_EDITOR_ARGS` → `PLUM_EDITOR_ARGS`
- [ ] `WORKTREE_DEFAULT_BRANCH` → `PLUM_DEFAULT_BRANCH`
- [ ] `WORKTREE_PARENT_DIR` → `PLUM_PARENT_DIR`

### [ ] Advanced Variables (WORKTREE_ → PLUM_)
- [ ] `WORKTREE_CONFIG_FILE` → `PLUM_CONFIG_FILE`
- [ ] `WORKTREE_MCP_TEMPLATE_DIR` → `PLUM_MCP_TEMPLATE_DIR`
- [ ] `WORKTREE_MCP_AUTO_ACTIVATE` → `PLUM_MCP_AUTO_ACTIVATE`
- [ ] `WORKTREE_SKIP_FILE_COPY` → `PLUM_SKIP_FILE_COPY`
- [ ] `WORKTREE_FILES_TO_COPY` → `PLUM_FILES_TO_COPY`

## Source Code Updates

### [ ] lib/config.sh
- [ ] Update all `WORKTREE_*` variable references
- [ ] Update default config file paths:
  - `~/.config/worktree-manager/config` → `~/.config/plum/config`
  - `scripts/worktree-manager/worktree-config` → `scripts/plum/plum-config`
- [ ] Update variable name validation and defaults

### [ ] lib/files.sh
- [ ] Update `WORKTREE_FILES_TO_COPY` → `PLUM_FILES_TO_COPY`
- [ ] Update `WORKTREE_SKIP_FILE_COPY` → `PLUM_SKIP_FILE_COPY`

### [ ] lib/mcp.sh
- [ ] Update `WORKTREE_MCP_TEMPLATE_DIR` → `PLUM_MCP_TEMPLATE_DIR`

### [ ] lib/ui.sh
- [ ] Update all `WORKTREE_*` variable references in help text
- [ ] Update environment variable documentation
- [ ] Update interactive prompts and displays

### [ ] lib/git-utils.sh
- [ ] Update `WORKTREE_DEFAULT_BRANCH` → `PLUM_DEFAULT_BRANCH`
- [ ] Update `WORKTREE_GITHUB_USERNAME` → `PLUM_GITHUB_USERNAME`

## Configuration File Updates

### [ ] Default Configuration Files
- [ ] Update `scripts/plum/plum-config` with new variable names
- [ ] Verify all PLUM_* variables are documented
- [ ] Update any example configurations

### [ ] User Configuration Migration
- [ ] Create migration script for user configs
- [ ] Document migration path for existing users
- [ ] Plan backward compatibility strategy

## Documentation Updates

### [ ] README Files
- [ ] Update `scripts/plum/README.md`:
  - [ ] Change all worktree-manager references to plum
  - [ ] Update installation paths and commands
  - [ ] Update environment variable names
  - [ ] Update usage examples
- [ ] Update main project README.md

### [ ] Project Documentation
- [ ] Update `CLAUDE.md`:
  - [ ] Change worktree-manager references to plum
  - [ ] Update WORKTREE_* → PLUM_* environment variables
  - [ ] Update script paths and commands
- [ ] Update `purpose.md` with new tool names

### [ ] Help Text and CLI Documentation
- [ ] Update help text in lib/ui.sh
- [ ] Update command examples and usage patterns
- [ ] Update error messages with new tool names

## MCP Integration Updates

### [ ] Claude Settings
- [ ] Update `.claude/settings.local.json`:
  - [ ] Change `scripts/worktree-manager/` → `scripts/plum/`
  - [ ] Update executable name references
  - [ ] Update environment variable examples

### [ ] MCP Templates
- [ ] Review MCP template directory location
- [ ] Update any templates with hardcoded references
- [ ] Verify template discovery still works

## External References

### [ ] Build and Test Scripts
- [ ] Update any Makefile references
- [ ] Update test script paths
- [ ] Update CI/CD pipeline references

### [ ] User Scripts and Aliases
- [ ] Document changes needed in user aliases
- [ ] Update any wrapper scripts
- [ ] Plan communication for breaking changes

## Validation Checklist

### [ ] Functional Testing
- [ ] Test basic worktree creation with new plum command
- [ ] Test interactive CLI with plum-cli.sh
- [ ] Test MCP template activation
- [ ] Test file copying functionality
- [ ] Test configuration loading from all sources

### [ ] Integration Testing
- [ ] Test Claude Code integration with new MCP paths
- [ ] Test GitHub CLI integration
- [ ] Test editor opening functionality
- [ ] Test gum-based interactive features

### [ ] Configuration Testing
- [ ] Test environment variable overrides
- [ ] Test config file loading priority
- [ ] Test custom config file paths
- [ ] Test default value fallbacks

### [ ] Backward Compatibility
- [ ] Document what breaks and why
- [ ] Create migration guides for users
- [ ] Plan deprecation warnings if maintaining old names temporarily

## Command Interface Changes

### [ ] Primary Commands
- [ ] `worktree-create` → `plum` (or `plum-create`)
- [ ] `worktree-cli.sh` → `plum-cli.sh`
- [ ] Maintain same command-line options and behavior
- [ ] Update help text and usage examples

### [ ] Alias and Symlink Strategy
- [ ] Consider creating temporary symlinks for transition
- [ ] Plan communication about command name changes
- [ ] Document new command structure

## Error Messages and Logging

### [ ] Error Message Updates
- [ ] Update tool names in error messages
- [ ] Update file path references in errors
- [ ] Update help suggestions with new command names

### [ ] Debug and Logging Output
- [ ] Update debug messages with new tool names
- [ ] Update log file names if any
- [ ] Update progress indicators

## Testing Strategy

### [ ] Pre-Migration Testing
- [ ] Document current functionality completely
- [ ] Create test cases for all features
- [ ] Backup current working system

### [ ] Post-Migration Testing
- [ ] Run all functionality tests with new names
- [ ] Test edge cases and error conditions
- [ ] Validate performance is unchanged

### [ ] User Acceptance Testing
- [ ] Test with real projects and worktrees
- [ ] Test configuration migration process
- [ ] Test integration with development workflows

## Rollback Plan

### [ ] Backup Strategy
- [ ] Complete backup of working system
- [ ] Git branch for migration work
- [ ] Tagged release before changes

### [ ] Rollback Procedures
- [ ] Document how to restore old system
- [ ] Plan for reverting configuration changes
- [ ] Communication plan for rollback if needed