# System Inventory - Current PruneJuice Implementation

## File Structure

```
/Users/brian/code/prunejuice/
├── scripts/
│   ├── create-worktree-with-branch.sh    # Legacy worktree creation script
│   ├── worktree-cli.sh                   # Interactive worktree management CLI
│   └── worktree-manager/                 # Core worktree management system
│       ├── README.md                     # Documentation
│       ├── worktree-config              # Default configuration file
│       ├── worktree-create              # Main executable
│       ├── lib/                         # Modular library system
│       │   ├── config.sh               # Configuration loading
│       │   ├── files.sh                # File synchronization
│       │   ├── git-utils.sh            # Git operations
│       │   ├── mcp.sh                  # MCP template handling
│       │   └── ui.sh                   # User interface utilities
│       └── mcp-templates/              # MCP configuration templates
├── .claude/
│   └── settings.local.json             # Claude settings with worktree references
├── purpose.md                          # Project vision
├── CLAUDE.md                          # Project instructions for Claude
└── other documentation files...
```

## Script Dependencies

### Primary Entry Points
1. **worktree-cli.sh** - Interactive CLI (standalone, no library dependencies)
2. **worktree-manager/worktree-create** - Main executable (uses all lib modules)
3. **create-worktree-with-branch.sh** - Legacy script (minimal dependencies)

### Library Module Dependencies
```
worktree-create
├── config.sh      (loads configuration)
├── git-utils.sh   (Git operations)
├── files.sh       (file copying, uses config.sh)
├── mcp.sh         (MCP template handling)
└── ui.sh          (user interface, uses git-utils.sh)
```

### External Tool Dependencies
- **git** - Core Git operations, worktree management
- **gum** - Interactive CLI components (selection, input)
- **gh** - GitHub CLI for PR operations
- **jq** - JSON parsing (used in worktree-cli.sh)
- **tmux** - Future dependency for pots tool

## Current CLI Interfaces

### worktree-create Command
```bash
Usage: worktree-create [OPTIONS] [branch-suffix]

OPTIONS:
  -h, --help              Show help message
  -m, --mcp               Interactive MCP template selection
  --mcp TEMPLATE          Activate specific MCP template
  --pattern PATTERN       Branch naming pattern (default: {username}/{suffix})
  --from BRANCH           Create from specific branch
  --no-copy-files         Skip file copying
  --dry-run               Preview actions
  --config                Show configuration
  -i, --interactive       Interactive mode

ARGUMENTS:
  branch-suffix          Branch name suffix (default: patch-{timestamp})
```

### worktree-cli.sh Interface
- Interactive terminal UI with keyboard controls
- No command-line arguments (starts interactive mode immediately)
- Keyboard controls: ↑/↓, j/k (navigate), Space (select), d (delete), q (quit)

## Environment Variables (WORKTREE_*)

### Core Configuration
- `WORKTREE_GITHUB_USERNAME` - GitHub username for branch names
- `WORKTREE_EDITOR` - Editor command (default: code)
- `WORKTREE_EDITOR_ARGS` - Editor arguments (default: --new-window)
- `WORKTREE_DEFAULT_BRANCH` - Default base branch (default: main)
- `WORKTREE_PARENT_DIR` - Worktree parent directory (default: ../)

### Advanced Configuration  
- `WORKTREE_CONFIG_FILE` - Custom config file location
- `WORKTREE_MCP_TEMPLATE_DIR` - MCP templates directory (default: mcp-json-templates)
- `WORKTREE_MCP_AUTO_ACTIVATE` - Auto-activate MCP templates (default: false)
- `WORKTREE_SKIP_FILE_COPY` - Skip file copying (true/false)
- `WORKTREE_FILES_TO_COPY` - Array of files to copy between worktrees

## Hardcoded References Requiring Updates

### Directory and File References
1. **scripts/worktree-manager/** - Main directory path
2. **worktree-manager** - String references in documentation
3. **worktree-create** - Executable filename
4. **worktree-cli.sh** - CLI script filename
5. **worktree-config** - Configuration filename

### Environment Variable References
All `WORKTREE_*` environment variables need to be renamed to `PLUM_*`:
- Configuration files: lib/config.sh, lib/ui.sh
- Documentation: README.md, CLAUDE.md
- Usage examples: Settings files, documentation

### MCP Template References
- **.claude/settings.local.json** - Contains hardcoded paths to worktree-manager
- **MCP template files** - May contain references to worktree-manager
- **Configuration examples** - Documentation with hardcoded paths

### Documentation References
- **README.md files** - Multiple references to worktree-manager paths
- **CLAUDE.md** - Project instructions referencing WORKTREE_ variables
- **guide.md** - Contains refactoring context
- **purpose.md** - May contain references to current tool names

## Configuration Files

### Default Configuration Locations
1. `~/.config/worktree-manager/config` - User-level configuration
2. `scripts/worktree-manager/worktree-config` - Project-level defaults
3. Custom location via `WORKTREE_CONFIG_FILE` environment variable

### Default File Copy List
```bash
WORKTREE_FILES_TO_COPY=(
    ".claude/settings.json"
    ".claude/settings.local.json" 
    ".vscode/settings.json"
    ".vscode/launch.json"
    ".env"
    ".env.local"
    "credentials.json"
    "package-lock.json"
    "yarn.lock"
    "Pipfile.lock"
)
```

## Integration Points

### Claude Code Integration
- MCP templates in `scripts/worktree-manager/mcp-templates/`
- Settings references in `.claude/settings.local.json`
- Project instructions in `CLAUDE.md`

### Editor Integration
- Configurable editor command via `WORKTREE_EDITOR`
- Automatic editor opening after worktree creation
- Support for VS Code, Vim, Sublime Text editor arguments

### GitHub Integration
- PR status checking via GitHub CLI (`gh`)
- Branch naming with username integration
- PR merge status detection for cleanup decisions

## Migration Impact Assessment

### High Impact Changes
1. **Directory rename**: scripts/worktree-manager/ → scripts/plum/
2. **Executable rename**: worktree-create → plum-create (or just plum)
3. **Environment variables**: All WORKTREE_* → PLUM_*
4. **Configuration files**: worktree-config → plum-config

### Medium Impact Changes
1. **CLI script rename**: worktree-cli.sh → plum-cli.sh
2. **Documentation updates**: All README and help text
3. **MCP template updates**: Path references and tool names

### Low Impact Changes
1. **Internal function names**: Can remain unchanged initially
2. **Comment updates**: Non-functional documentation
3. **Example updates**: Usage examples in documentation

## Validation Requirements

### Functional Validation
- [ ] All worktree operations continue to work
- [ ] MCP template activation functions correctly
- [ ] File copying between worktrees works
- [ ] GitHub CLI integration remains functional
- [ ] Editor integration opens correctly

### Integration Validation
- [ ] Claude Code can find and use MCP templates
- [ ] Configuration loading works from all expected locations
- [ ] Environment variable overrides function properly
- [ ] Interactive CLI modes operate correctly

### Compatibility Validation
- [ ] Existing worktrees remain accessible
- [ ] Configuration files continue to be recognized
- [ ] External scripts calling worktree-manager still work (with updates)