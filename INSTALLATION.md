# PruneJuice Installation Guide

🧃 **PruneJuice** - Parallel Agentic Coding Workflow Orchestrator

## Quick Start

```bash
# Install globally (recommended)
make install

# Or for development
make dev-link
```

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

## Installation Options

### 1. Global Installation (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install PruneJuice globally
make install
```

This installs:
- `prj` command (main PruneJuice interface)
- `prunejuice` command (alias for prj)
- `plum` command (worktree manager)
- `pots` command (tmux session manager)

### 2. Development Installation

```bash
# For development work on PruneJuice itself
make dev-link
```

### 3. Manual Installation

```bash
cd python-implementation/prunejuice
uvx install .
```

## Key Features

- 🔒 **Security**: SQL injection protection, input validation
- ⚡ **Performance**: Fast startup, efficient execution  
- 🎨 **Rich CLI**: Beautiful tables, colors, progress indicators
- 📦 **Artifact Management**: Organized storage with history
- 🗄️ **Database Tracking**: SQLite with execution history
- 🧪 **Testing**: Comprehensive test suite with security tests
- 🔧 **Extensible**: Easy YAML command definitions

## Usage Examples

```bash
# Initialize project
prj init

# List available commands
prj list-commands

# Run command with arguments
prj run analyze-issue issue_number=123

# Show project status and history
prj status

# Clean up old artifacts
prj cleanup --days 30

# Use supporting tools
plum create feature-branch    # Create worktree
pots create-session          # Start tmux session
```

## Uninstallation

```bash
# Remove installation
make uninstall

# Remove development installation
make dev-unlink
```

## Testing & Development

```bash
# Run tests
make test

# Run full validation suite
make all

# Create test environment
make test-env
```

## Troubleshooting

### Installation Issues

**"uvx not found" error:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

**"Module not found" error:**
```bash
# Reinstall in development mode
make dev-unlink && make dev-link
```

**"Command not found" error:**
```bash
# Check if installed
which prj
which plum
which pots

# Add to PATH if needed
export PATH="$HOME/.local/bin:$PATH"
```

## Development Workflow

### Contributing to PruneJuice
```bash
# Set up development environment
make dev-link

# Run tests frequently
make test

# Before committing
make all
```

### Using PruneJuice
```bash
# Initialize your project
cd your-project
prj init

# Create custom commands
vim .prj/commands/my-workflow.yaml

# Run your workflows
prj run my-workflow arg1=value1
```

## Get Started

```bash
# Quick start
make install
prj init
prj list-commands
prj run analyze-issue issue_number=123
```