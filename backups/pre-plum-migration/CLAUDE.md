# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PruneJuice is a collection of shell script utilities for managing parallel agentic coding sessions across multiple projects using Git worktrees. The project facilitates workflow management for developers working on multiple isolated development lines while integrating with Claude Code through MCP templates.

## Development Commands

### Testing and Validation
```bash
# Run all tests
make test

# Run shellcheck linting
make shellcheck

# Check for todo items
make check-todos

# Run full validation suite
make all
```

### Core Usage
```bash
# Interactive worktree management (primary interface)
./scripts/worktree-cli.sh

# Legacy worktree creation
./scripts/create-worktree-with-branch.sh <branch-name>
```

## Architecture Overview

### Core Components

**Modular Library System** (`scripts/worktree-manager/lib/`):
- `config.sh`: Configuration loading with environment variable support
- `git-utils.sh`: Git worktree and branch operations
- `mcp.sh`: MCP template discovery and activation for Claude Code integration
- `files.sh`: File synchronization between worktrees
- `ui.sh`: Interactive user interface utilities

**MCP Template System**: 
- Templates in `scripts/worktree-manager/mcp-templates/` define Claude Code configurations
- Supports different profiles (e.g., "dwh" for data warehouse contexts)
- Templates are copied as `.mcp.json` files to provide context-specific AI assistance

**Configuration Architecture**:
- Environment variables with `WORKTREE_*` prefix
- Hierarchical config file support (user-level and project-level)
- Defaults in `scripts/worktree-manager/worktree-config`

### Key Environment Variables
```bash
WORKTREE_GITHUB_USERNAME    # GitHub username for PR operations
WORKTREE_EDITOR            # Editor command (default: code)
WORKTREE_BASE_DIR          # Base directory for worktrees
```

### Development Workflow

1. **Worktree Creation**: Creates isolated Git worktree environments
2. **MCP Template Selection**: Chooses appropriate Claude Code context
3. **File Synchronization**: Copies configuration files between worktrees
4. **Editor Integration**: Opens new worktrees in configured editor
5. **PR Status Tracking**: Monitors GitHub PR status for cleanup

## Technical Details

**Dependencies**: 
- `gum` for interactive CLI components
- GitHub CLI (`gh`) for PR operations
- Git worktrees for isolation
- `tmux` for session management (planned)

**Current Evolution**: The project is transitioning from monolithic scripts (`create-worktree-with-branch.sh`) to a modular architecture. The refactor plan in `scripts/refactor-plan.md` outlines the migration strategy.

**File Synchronization**: The system automatically copies important files (VS Code settings, credentials, etc.) between worktrees to maintain consistent development environments.

## Key Files to Understand

- `purpose.md`: Project vision and requirements
- `scripts/worktree-manager/lib/`: Core modular libraries
- `scripts/refactor-plan.md`: Architecture evolution strategy
- `worktree-mgr-explanation.md`: Technical documentation