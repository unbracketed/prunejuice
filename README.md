# 🧃 PruneJuice

**Parallel Agentic Coding Workflow Orchestrator**

A secure, Python-based SDLC orchestrator designed for managing parallel agentic coding sessions across multiple Git worktrees. Execute complex workflows with sequential step execution, rich CLI output, and comprehensive security.

## ✨ Features

- 🔒 **Security First**: SQL injection protection, input validation, no code execution
- 🎨 **Rich CLI**: Beautiful terminal output with tables, colors, and progress
- 📦 **Artifact Management**: Organized storage with execution history  
- 🗄️ **Database Tracking**: SQLite with proper parameter binding
- 🔧 **Extensible**: Easy YAML command definitions
- 🧪 **Comprehensive Testing**: Security tests, unit tests, integration tests
- ⚡ **Fast**: Sub-second startup, efficient execution

## 🚀 Quick Start

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install PruneJuice
make install

# Initialize a project
prj init

# List available commands
prj list-commands

# Run a workflow
prj run analyze-issue issue_number=123
```

## 📋 Commands

```bash
prj init                    # Initialize PruneJuice project
prj list-commands          # List available workflows  
prj run <command> [args]   # Execute workflow
prj status                 # Show execution history
prj cleanup --days 30     # Clean old artifacts
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   PruneJuice (Python)                   │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ CLI Layer   │  │ Orchestrator │  │ State Manager  │ │
│  │ (Typer)     │  │   Engine     │  │  (SQLite)     │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ YAML Parser │  │ Task Runner  │  │ Artifact Store │ │
│  │ (Pydantic)  │  │ (sequential) │  │                │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
└─────────────────────────┬───────────────────────────────┘
                          │ subprocess calls
         ┌────────────────┴────────────────┐
         │                                 │
    ┌────┴────┐                      ┌────┴────┐
    │  plum   │                      │  pots   │
    │ (shell) │                      │ (shell) │
    └─────────┘                      └─────────┘
```

## 📝 Custom Workflows

Create YAML files in `.prj/commands/`:

```yaml
name: my-workflow
description: Custom development workflow
category: development
arguments:
  - name: feature_name
    required: true
    description: Name of the feature
environment:
  PRUNEJUICE_TASK: "feature-development"
steps:
  - setup-environment
  - validate-prerequisites  
  - create-worktree
  - gather-context
  - start-session
  - store-artifacts
timeout: 1800
```

## 🔒 Security

- **SQL Injection Prevention**: All database queries use parameter binding
- **Input Validation**: Pydantic models validate all user inputs
- **No Code Execution**: Commands parsed as structured YAML, not executed
- **Subprocess Safety**: Proper argument escaping
- **Path Traversal Protection**: File operations validate paths

Security verified by comprehensive test suite.

## 🧪 Testing & Development

```bash
# Run tests
make test

# Run full validation suite  
make all

# Development setup
make dev-link

# Before committing
make all
```

## 📚 Documentation

- [Installation Guide](INSTALLATION.md) - Complete setup instructions
- [Implementation Summary](python-implementation/IMPLEMENTATION_SUMMARY.md) - Technical details
- [Python Implementation README](python-implementation/prunejuice/README.md) - Detailed docs

## 🛠️ Supporting Tools

PruneJuice integrates with:

- **plum**: Git worktree manager for parallel development
- **pots**: Tmux session manager for organized workflows

These tools are automatically installed with PruneJuice.

## 📊 Example Session

```bash
$ prj init
🧃 Initializing PruneJuice project...
✅ Project initialized successfully!

$ prj list-commands
                               Available Commands                               
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Command        ┃ Category    ┃ Description                                   ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ analyze-issue  │ analysis    │ Analyze a GitHub issue and create             │
│                │             │ implementation plan                           │
│ code-review    │ quality     │ Perform comprehensive code review             │
│ feature-branch │ development │ Create feature branch with full development   │
│                │             │ environment                                   │
└────────────────┴─────────────┴───────────────────────────────────────────────┘

$ prj run analyze-issue issue_number=456
🚀 Executing command: analyze-issue
[Step-by-step execution with logging...]
✅ Command completed successfully!

$ prj status
📊 PruneJuice Project Status
                        Recent Events                         
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Command       ┃ Status    ┃ Start Time          ┃ Duration ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ analyze-issue │ completed │ 2025-06-28 16:03:47 │ 1.0s     │
└───────────────┴───────────┴─────────────────────┴──────────┘
```

## 🤝 Contributing

1. Set up development environment: `make dev-link`
2. Run tests frequently: `make test`
3. Validate before committing: `make all`

## 📄 License

[License details]

---

🧃 **PruneJuice** - Where parallel agentic coding meets secure workflow orchestration.