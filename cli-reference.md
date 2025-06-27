# CLI Reference - Current PruneJuice Implementation

## Main Commands

### worktree-create
**Primary executable for worktree management**

#### Usage
```bash
worktree-create [OPTIONS] [branch-suffix]
```

#### Options
| Option | Description | Default |
|--------|-------------|---------|
| `-h, --help` | Show help message | - |
| `-m, --mcp` | Interactive MCP template selection | - |
| `--mcp TEMPLATE` | Activate specific MCP template | - |
| `--pattern PATTERN` | Branch naming pattern | `{username}/{suffix}` |
| `--from BRANCH` | Create from specific branch | `$WORKTREE_DEFAULT_BRANCH` |
| `--no-copy-files` | Skip file copying | false |
| `--dry-run` | Preview actions without executing | false |
| `--config` | Show current configuration | - |
| `-i, --interactive` | Interactive mode with all options | false |

#### Arguments
- `branch-suffix` - Optional branch name suffix (default: `patch-{timestamp}`)

#### Examples
```bash
# Basic usage with auto-generated branch
worktree-create

# Create with specific branch suffix  
worktree-create fix-bug

# Create with MCP template
worktree-create --mcp dwh fix-bug

# Interactive MCP selection
worktree-create -m

# Custom branch pattern
worktree-create --pattern "feature/{suffix}" new-feature

# Create from specific branch
worktree-create --from develop hotfix

# Preview without executing
worktree-create --dry-run experimental

# Interactive mode with all options
worktree-create -i

# Show current configuration
worktree-create --config
```

### worktree-cli.sh
**Interactive worktree management interface**

#### Usage
```bash
./scripts/worktree-cli.sh
```

#### Interface
- **No command-line options** - Starts in interactive mode immediately
- **Keyboard Controls**:
  - `↑/↓` or `j/k` - Navigate through worktrees
  - `Space` - Select/deselect worktree for deletion
  - `d` - Delete selected worktrees
  - `a` - Select all non-main worktrees
  - `m` - Select all merged worktrees
  - `q` - Quit application

#### Features
- **Real-time PR status checking** using GitHub CLI
- **Merge status detection** for safe cleanup
- **Batch worktree deletion** with confirmation
- **Color-coded interface** (green=merged, yellow=no PR)
- **Safety protection** for main worktree

#### Display Columns
| Column | Description |
|--------|-------------|
| [ ] | Selection checkbox |
| WORKTREE | Worktree directory name |
| PR STATUS | GitHub PR status (PR #123, NO PR, MERGED, etc.) |
| MERGED | Boolean merge status |

### create-worktree-with-branch.sh
**Legacy worktree creation script**

#### Usage
```bash
./scripts/create-worktree-with-branch.sh <branch-name>
```

#### Arguments
- `branch-name` - Required branch name (used as-is, no pattern transformation)

#### Features
- **Simple worktree creation** with basic file copying
- **MCP template activation** (hardcoded list)
- **Fixed file copy list** (no configuration)
- **Direct VS Code opening** (hardcoded)

## Environment Variables

### Core Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `WORKTREE_GITHUB_USERNAME` | GitHub username for branch names | `$GITHUB_USERNAME` or `unbracketed` |
| `WORKTREE_EDITOR` | Editor command to use | `$VISUAL`, `$EDITOR`, or `code` |
| `WORKTREE_EDITOR_ARGS` | Editor command arguments | `--new-window` |
| `WORKTREE_DEFAULT_BRANCH` | Default base branch | `main` |
| `WORKTREE_PARENT_DIR` | Parent directory for worktrees | `../` |

### Advanced Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `WORKTREE_CONFIG_FILE` | Custom configuration file path | See config locations |
| `WORKTREE_MCP_TEMPLATE_DIR` | MCP templates directory | `mcp-json-templates` |
| `WORKTREE_MCP_AUTO_ACTIVATE` | Auto-activate MCP templates | `false` |
| `WORKTREE_SKIP_FILE_COPY` | Skip file copying entirely | `false` |
| `WORKTREE_FILES_TO_COPY` | Array of files to copy | See default list |

### Configuration File Locations
Checked in order (first found is used):
1. `$WORKTREE_CONFIG_FILE` (if set)
2. `~/.config/worktree-manager/config`
3. `scripts/worktree-manager/worktree-config`

## Branch Naming Patterns

### Pattern Variables
- `{username}` - Replaced with `$WORKTREE_GITHUB_USERNAME`
- `{suffix}` - Replaced with provided branch suffix
- `{timestamp}` - Replaced with current timestamp (if used in suffix)

### Pattern Examples
| Pattern | Input | Result |
|---------|-------|--------|
| `{username}/{suffix}` | `fix-bug` | `brian/fix-bug` |
| `feature/{suffix}` | `new-api` | `feature/new-api` |
| `{suffix}` | `hotfix` | `hotfix` |
| `hotfix/{username}/{suffix}` | `urgent` | `hotfix/brian/urgent` |

### Auto-generated Suffixes
When no suffix provided:
- Format: `patch-{timestamp}`
- Example: `patch-20240627-143022`

## Default File Copy List

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

## MCP Template System

### Template Selection
- **Interactive mode**: `worktree-create -m` - Shows selection menu
- **Direct specification**: `worktree-create --mcp template-name`
- **Template directory**: Configurable via `WORKTREE_MCP_TEMPLATE_DIR`

### Template Activation Process
1. **Discovery**: Find templates in configured directory
2. **Selection**: User chooses template (interactive or specified)
3. **Copying**: Template JSON copied to new worktree as `.mcp.json`
4. **Validation**: Basic JSON validation performed

### Available Templates (project-specific)
Templates are stored in `scripts/worktree-manager/mcp-templates/`:
- Each template is a JSON file
- Templates define MCP server configurations
- Templates are copied to worktree root as `.mcp.json`

## Error Handling

### Git Repository Validation
- **Check**: Repository exists and is valid Git repo
- **Error**: Exit with error message if not in Git repo
- **Location**: Performed in `git-utils.sh:validate_git_repo()`

### External Tool Checks
- **gum**: Graceful degradation if not available
- **gh**: Warning message if GitHub CLI not installed
- **jq**: Error handling in PR status parsing

### Worktree Creation Errors
- **Branch conflicts**: Git handles branch name conflicts
- **Directory conflicts**: Git handles existing directory conflicts  
- **Permission errors**: Standard filesystem error handling

## Output and Logging

### Standard Output
- **Progress messages**: Worktree creation steps
- **Configuration display**: When `--config` used
- **Dry run output**: Preview of actions when `--dry-run` used

### Error Output
- **Validation errors**: Git repository issues
- **Tool availability**: Missing external commands
- **Operation failures**: Git command failures

### Color Coding (worktree-cli.sh)
- **Green**: Merged PRs (safe to delete)
- **Yellow**: No PR found
- **Red**: Error states
- **Blue**: UI elements and borders
- **Bold**: Headers and emphasis
- **Reverse**: Current selection highlight