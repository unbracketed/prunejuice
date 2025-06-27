# Worktree Manager

A powerful, configurable Git worktree management tool that simplifies creating new worktrees with branches and integrates with MCP templates.

## Features

- **Configurable**: Use config files or environment variables
- **Multi-editor support**: Works with VS Code, Vim, Sublime Text, and more
- **Flexible file copying**: Copy project files to new worktrees
- **MCP integration**: Activate MCP templates in new worktrees
- **Branch strategies**: Customizable branch naming patterns
- **Dry run mode**: Preview actions before execution
- **Interactive mode**: Step-by-step guided workflow

## Installation

1. Clone or copy the `worktree-manager` directory to your project's `scripts/` folder
2. Make the main script executable:
   ```bash
   chmod +x scripts/worktree-manager/worktree-create
   ```
3. Optionally, create a symlink for easier access:
   ```bash
   ln -s "$PWD/scripts/worktree-manager/worktree-create" /usr/local/bin/worktree-create
   ```

## Quick Start

```bash
# Basic usage - creates worktree with auto-generated branch name
./scripts/worktree-manager/worktree-create

# Create worktree with specific branch suffix
./scripts/worktree-manager/worktree-create fix-login-bug

# Interactive mode with guided prompts
./scripts/worktree-manager/worktree-create -i

# Preview what would be done (dry run)
./scripts/worktree-manager/worktree-create --dry-run experimental-feature
```

## Configuration

### Configuration File

Create a configuration file in one of these locations:
- `~/.worktree-config`
- `~/.config/worktree-manager/config`
- `scripts/worktree-manager/worktree-config` (included)

Example configuration:
```bash
# User settings
WORKTREE_GITHUB_USERNAME="your-username"

# Git settings  
WORKTREE_DEFAULT_BRANCH="main"
WORKTREE_PARENT_DIR="../"

# Editor settings
WORKTREE_EDITOR="code"
WORKTREE_EDITOR_ARGS="--new-window"

# Files to copy to new worktrees
WORKTREE_FILES_TO_COPY=(
  ".vscode/tasks.json"
  "mcp-json-templates/.secrets"
  ".env.example"
)

# MCP settings
WORKTREE_MCP_TEMPLATE_DIR="mcp-json-templates"
```

### Environment Variables

All configuration can be overridden with environment variables:

- `WORKTREE_GITHUB_USERNAME` - GitHub username for branch names
- `WORKTREE_EDITOR` - Editor command (default: code-insiders)
- `WORKTREE_DEFAULT_BRANCH` - Default base branch (default: main)
- `WORKTREE_CONFIG_FILE` - Custom config file location
- `WORKTREE_PARENT_DIR` - Where to create worktrees (default: ../)
- `WORKTREE_MCP_TEMPLATE_DIR` - MCP templates directory
- `WORKTREE_SKIP_FILE_COPY` - Skip file copying (true/false)

## Command Reference

### Basic Usage
```bash
worktree-create [OPTIONS] [branch-suffix]
```

### Options

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message |
| `-m, --mcp [TEMPLATE]` | Select MCP template (interactive if no template specified) |
| `--pattern PATTERN` | Branch naming pattern (default: `{username}/{suffix}`) |
| `--from BRANCH` | Create from different base branch |
| `--no-copy-files` | Skip copying files to new worktree |
| `--dry-run` | Show what would be done without executing |
| `--config` | Show current configuration |
| `-i, --interactive` | Interactive mode with all options |

### Examples

```bash
# Create with default settings
worktree-create

# Create with specific branch name
worktree-create feature-authentication

# Use custom branch pattern
worktree-create --pattern "feature/{suffix}" authentication

# Create from develop branch instead of main
worktree-create --from develop hotfix-critical

# Skip file copying
worktree-create --no-copy-files quick-test

# Interactive MCP template selection
worktree-create -m feature-backend

# Specific MCP template
worktree-create --mcp dwh analytics-work

# Preview actions (dry run)
worktree-create --dry-run experimental

# Interactive mode with all prompts
worktree-create -i

# Override username for this run
WORKTREE_GITHUB_USERNAME=collaborator worktree-create shared-feature

# Use different editor
WORKTREE_EDITOR=nvim worktree-create terminal-work
```

## MCP Integration

The worktree manager integrates with MCP (Model Context Protocol) templates:

1. **Template Directory**: Configure `WORKTREE_MCP_TEMPLATE_DIR` (default: `mcp-json-templates`)
2. **Template Files**: Use `.mcp.{name}.json` format
3. **Activation**: Templates are copied as `.mcp.json` in new worktrees

### MCP Usage Examples

```bash
# Interactive template selection
worktree-create -m

# Specific template
worktree-create --mcp dwh data-processing

# List available templates
ls mcp-json-templates/.mcp.*.json
```

## Branch Naming Patterns

Customize branch naming with patterns:

| Pattern | Example Result |
|---------|----------------|
| `{username}/{suffix}` | `john/fix-bug` |
| `feature/{suffix}` | `feature/fix-bug` |
| `{suffix}` | `fix-bug` |
| `{username}/{type}/{suffix}` | `john/feature/fix-bug` |

## File Copying

The tool can copy files from your main worktree to new worktrees:

### Default Files
- `.vscode/tasks.json` - VS Code tasks
- `mcp-json-templates/.secrets` - MCP secrets

### Custom Files
Configure in your config file:
```bash
WORKTREE_FILES_TO_COPY=(
  ".vscode/tasks.json"
  ".vscode/settings.json"
  ".env.example"
  "config/development.key"
  "secrets/*"
)
```

## Multi-Editor Support

The tool auto-detects editor arguments:

| Editor | Default Args |
|--------|--------------|
| `code*` | `--new-window` |
| `vim`, `nvim` | (none) |
| `subl` | `-n` |
| Others | (none) |

Override with `WORKTREE_EDITOR_ARGS`.

## Error Handling

The tool includes comprehensive error handling:

- Validates git repository
- Checks for uncommitted changes (auto-stashes)
- Verifies branch and template existence
- Rollback support on failures
- Clear error messages

## Troubleshooting

### Common Issues

**"Not in a git repository"**
- Ensure you're running from within a git repository

**"MCP template not found"**
- Check template exists: `ls mcp-json-templates/.mcp.*.json`
- Verify `WORKTREE_MCP_TEMPLATE_DIR` path

**"Failed to create worktree"**
- Ensure parent directory exists and is writable
- Check for conflicting branch names
- Verify git permissions

**Editor doesn't open**
- Check `WORKTREE_EDITOR` is in your PATH
- Test editor command manually
- Verify editor arguments with `--config`

### Debug Mode

Show current configuration:
```bash
worktree-create --config
```

Preview actions without executing:
```bash
worktree-create --dry-run your-branch
```

## Migration from Original Script

If migrating from `create-worktree-with-branch.sh`:

1. **Configuration**: Move hardcoded values to config file
2. **Usage**: New command structure (see examples above)
3. **Features**: All original functionality preserved plus new features

### Comparison

| Old Script | New Tool |
|------------|----------|
| `./create-worktree-with-branch.sh fix-bug` | `worktree-create fix-bug` |
| `./create-worktree-with-branch.sh --mcp dwh fix` | `worktree-create --mcp dwh fix` |
| `./create-worktree-with-branch.sh -m` | `worktree-create -m` |

## Contributing

To extend the worktree manager:

1. **Add features**: Modify modules in `lib/` directory
2. **Test changes**: Use `--dry-run` mode
3. **Update help**: Modify `ui.sh` help functions
4. **Document**: Update this README

### Module Structure

- `lib/config.sh` - Configuration loading
- `lib/git-utils.sh` - Git operations  
- `lib/files.sh` - File copying
- `lib/mcp.sh` - MCP template handling
- `lib/ui.sh` - User interface functions

## License

This tool is part of your project and follows the same license terms.