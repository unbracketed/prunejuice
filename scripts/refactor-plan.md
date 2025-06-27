# Refactoring Plan for create-worktree-with-branch.sh

## Overview
This document outlines the refactoring plan to transform the current bash script into a more modular, configurable, and maintainable solution.

## Current Issues
1. **Hardcoded values** - Username "tadasant", editor "code-insiders", branch "main"
2. **Monolithic script** - All functionality in a single file
3. **Limited configurability** - No config file or environment variable support
4. **Rails-specific assumptions** - Hardcoded Rails credential files

## Proposed Architecture

### 1. Configuration System
Create a configuration file (`.worktree-config` or similar) that supports:
```yaml
# Example configuration
user:
  github_username: "${GITHUB_USERNAME:-unbracketed}"
  
git:
  default_branch: main
  worktree_parent: ".git"
  
editor:
  command: "code-insiders"
  args: "--new-window"
  
files_to_copy:
  - "web-app/config/master.key"
  - "web-app/config/credentials/*.key"
  - ".vscode/tasks.json"
  - "mcp-json-templates/.secrets"
  
mcp:
  template_dir: "mcp-json-templates"
  auto_activate: false
```

### 2. Modular Structure
Break the script into modules:

```
scripts/
├── worktree-manager/
│   ├── lib/
│   │   ├── config.sh      # Configuration loading
│   │   ├── git-utils.sh   # Git operations
│   │   ├── mcp.sh         # MCP template handling
│   │   ├── files.sh       # File copying operations
│   │   └── ui.sh          # User interface functions
│   ├── worktree-create    # Main executable
│   └── worktree-config    # Default configuration
```

### 3. Environment Variable Support
Support environment variables for all configurable options:
- `WORKTREE_GITHUB_USERNAME` - Override GitHub username
- `WORKTREE_EDITOR` - Override editor command
- `WORKTREE_DEFAULT_BRANCH` - Override default branch
- `WORKTREE_CONFIG_FILE` - Custom config file location

### 4. Enhanced Features

#### A. Multi-editor Support
```bash
# Auto-detect editor
EDITOR="${WORKTREE_EDITOR:-${VISUAL:-${EDITOR:-code}}}"

# Support different editors
case "$EDITOR" in
  code*) EDITOR_ARGS="--new-window" ;;
  vim|nvim) EDITOR_ARGS="" ;;
  subl) EDITOR_ARGS="-n" ;;
esac
```

#### B. Flexible File Copying
- Support glob patterns
- Optional file copying
- Custom copy lists per project

#### C. Branch Strategies
```bash
# Support different branch naming conventions
--branch-pattern "feature/{suffix}"
--branch-pattern "{username}/{type}/{suffix}"
--from-branch "develop"  # Create from branch other than main
```

#### D. Dry Run Mode
```bash
--dry-run  # Show what would be done without doing it
```

### 5. Improved Error Handling
- Validate all operations before execution
- Rollback on failure
- Better error messages

### 6. Testing Support
- Unit tests for individual functions
- Integration tests for full workflow
- Mock git operations for testing

## Implementation Plan

### Phase 1: Extract Configuration
1. Create config loading module
2. Move hardcoded values to config
3. Add environment variable support

### Phase 2: Modularize
1. Extract functions into separate modules
2. Create proper sourcing mechanism
3. Maintain backward compatibility

### Phase 3: Enhance Features
1. Add multi-editor support
2. Implement flexible file copying
3. Add branch strategies

### Phase 4: Polish
1. Add dry-run mode
2. Improve error handling
3. Add comprehensive help

## Migration Strategy
1. Keep original script working during refactor
2. Create new `worktree` command as wrapper
3. Deprecate old script once new one is stable

## Example Usage After Refactoring

```bash
# Using config file
worktree create fix-bug

# Override username
WORKTREE_GITHUB_USERNAME=brian worktree create fix-bug

# Custom branch pattern
worktree create --pattern "feature/{suffix}" new-feature

# Dry run
worktree create --dry-run experimental

# From different branch
worktree create --from develop hotfix

# Skip file copying
worktree create --no-copy-files quick-fix

# Interactive mode with all options
worktree create -i
```

## Benefits
1. **Flexibility** - Easy to customize for different projects
2. **Maintainability** - Modular code is easier to update
3. **Testability** - Can test individual components
4. **Extensibility** - Easy to add new features
5. **User-friendly** - Better defaults and error messages