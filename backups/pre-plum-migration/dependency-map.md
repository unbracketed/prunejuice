# Dependency Map - PruneJuice System

## Module Dependency Graph

```
External Tools
├── git (core Git operations)
├── gum (interactive CLI components)
├── gh (GitHub CLI for PR operations)
├── jq (JSON parsing)
└── tmux (planned for pots tool)

Entry Points
├── worktree-cli.sh (standalone)
│   ├── git worktree commands
│   ├── gh CLI for PR status
│   └── jq for JSON parsing
│
├── worktree-create (main executable)
│   ├── config.sh
│   ├── git-utils.sh
│   ├── files.sh
│   ├── mcp.sh
│   └── ui.sh
│
└── create-worktree-with-branch.sh (legacy)
    ├── git worktree commands
    └── basic file operations

Library Modules
├── config.sh (configuration management)
│   ├── Environment variable loading
│   ├── Config file parsing
│   └── Default value setting
│
├── git-utils.sh (Git operations)
│   ├── git worktree commands
│   ├── git branch operations
│   └── repository validation
│
├── files.sh (file synchronization)
│   ├── File copying utilities
│   ├── Pattern matching
│   └── Depends on: config.sh
│
├── mcp.sh (MCP template handling)
│   ├── Template discovery
│   ├── Template activation
│   └── JSON file operations
│
└── ui.sh (user interface)
    ├── Interactive prompts
    ├── Help text display
    ├── gum utility integration
    └── Depends on: git-utils.sh
```

## Source Dependencies

### worktree-create Sources
```bash
source "$LIB_DIR/config.sh"
source "$LIB_DIR/git-utils.sh"
source "$LIB_DIR/files.sh"
source "$LIB_DIR/mcp.sh"
source "$LIB_DIR/ui.sh"
```

### config.sh Sources
```bash
# Sources user configuration files when they exist:
source "$config_file"  # from WORKTREE_CONFIG_FILE or default locations
```

### No Internal Sources
- worktree-cli.sh (standalone)
- create-worktree-with-branch.sh (standalone)
- git-utils.sh (no internal dependencies)
- mcp.sh (no internal dependencies)

### Cross-Module Dependencies
- files.sh → config.sh (for WORKTREE_FILES_TO_COPY array)
- ui.sh → git-utils.sh (for repository operations in interactive mode)

## External Command Dependencies

### Required Commands
```bash
git          # Core Git operations, checked in validate_git_repo()
```

### Optional Commands (graceful degradation)
```bash
gum          # Interactive CLI, checked before use
gh           # GitHub CLI, checked before PR operations
jq           # JSON parsing, checked in worktree-cli.sh
```

### Editor Commands (configurable)
```bash
code         # Default editor
vim/nvim     # Alternative editors
subl         # Sublime Text
# Any command specified in WORKTREE_EDITOR
```

## Data Flow

### Configuration Loading Flow
```
1. Environment Variables (WORKTREE_*)
2. Default config file (~/.config/worktree-manager/config)
3. Project config file (scripts/worktree-manager/worktree-config)
4. Custom config file (WORKTREE_CONFIG_FILE)
5. Command-line overrides
```

### Worktree Creation Flow
```
1. config.sh loads configuration
2. git-utils.sh validates repository
3. ui.sh handles user interaction (if interactive)
4. git-utils.sh creates worktree and branch
5. files.sh copies specified files
6. mcp.sh activates templates (if requested)
7. Editor opens new worktree
```

### File Copy Dependencies
```
files.sh
├── Reads WORKTREE_FILES_TO_COPY from config.sh
├── Checks WORKTREE_SKIP_FILE_COPY flag
├── Uses main worktree path from git-utils.sh
└── Copies to new worktree path
```

## Integration Points

### Claude Code Integration
```
MCP Templates
├── Template discovery in mcp.sh
├── JSON file generation and copying
├── Path resolution for template directory
└── Integration with worktree creation flow
```

### GitHub Integration
```
PR Status Checking (worktree-cli.sh)
├── gh CLI command execution
├── JSON response parsing with jq
├── Branch name matching
└── Merge status detection
```

### Editor Integration
```
Editor Opening
├── Command construction from WORKTREE_EDITOR + WORKTREE_EDITOR_ARGS
├── Path passing to editor
├── Background process handling
└── Error handling for missing editors
```

## Migration Dependencies

### Rename Dependencies (scripts/worktree-manager → scripts/plum)
```
Direct Path References:
├── .claude/settings.local.json (hardcoded paths)
├── README.md examples
├── CLAUDE.md documentation
└── Any external scripts calling worktree-manager

Environment Variable Dependencies (WORKTREE_ → PLUM_):
├── config.sh (all WORKTREE_ variable references)
├── lib/*.sh files (variable usage)
├── Documentation examples
└── Configuration file examples
```

### Library Path Dependencies
```
worktree-create
├── SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
├── LIB_DIR="$SCRIPT_DIR/lib"
└── source statements using $LIB_DIR

# These are relative and will work after directory rename
```

### Configuration File Dependencies
```
Default Locations to Update:
├── ~/.config/worktree-manager/config → ~/.config/plum/config
├── scripts/worktree-manager/worktree-config → scripts/plum/plum-config
└── Any WORKTREE_CONFIG_FILE references
```

## Risk Assessment

### High Risk Dependencies
1. **External scripts** calling worktree-manager paths
2. **MCP templates** with hardcoded references
3. **User configuration files** with old paths

### Medium Risk Dependencies  
1. **Environment variable** changes in user environments
2. **Documentation** path references
3. **Claude settings** file updates

### Low Risk Dependencies
1. **Internal library** sourcing (relative paths)
2. **Function names** (can remain unchanged initially)
3. **Command-line interfaces** (can maintain compatibility)