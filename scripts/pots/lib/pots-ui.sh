#!/bin/bash

# User interface functions for POTS
# Extends the base ui.sh with POTS-specific help

# Source the base UI functions
source "$(dirname "${BASH_SOURCE[0]}")/shared/ui.sh"

# Override show_help for POTS-specific commands
show_help() {
    local script_name="${1:-pots}"
    local subcommand="${2:-}"
    
    if [ "$subcommand" = "create" ]; then
        cat << 'EOF'
Usage: pots create [OPTIONS] WORKTREE_PATH

Creates a new tmux session for the specified worktree.

OPTIONS:
  -h, --help              Show this help message
  -t, --task TASK         Task name for session (default: dev)
  --no-attach             Don't attach to session after creation

ARGUMENTS:
  WORKTREE_PATH          Path to the worktree directory

EXAMPLES:
  pots create /path/to/worktree           # Create session for worktree
  pots create -t backend /path/to/wt      # Create session with task suffix
  pots create --no-attach /path/to/wt     # Create without attaching

EOF
    elif [ "$subcommand" = "list" ]; then
        cat << 'EOF'
Usage: pots list [OPTIONS] [FILTER]

Lists tmux sessions, optionally filtered by pattern.

OPTIONS:
  -h, --help              Show this help message
  -v, --verbose           Show detailed session information
  -f, --filter PATTERN    Filter sessions by pattern

ARGUMENTS:
  FILTER                 Optional pattern to filter sessions

EXAMPLES:
  pots list                      # List all sessions
  pots list prunejuice           # List sessions matching 'prunejuice'
  pots list -v                   # List with detailed information

EOF
    elif [ "$subcommand" = "attach" ]; then
        cat << 'EOF'
Usage: pots attach [OPTIONS] SESSION_NAME

Attaches to an existing tmux session.

OPTIONS:
  -h, --help              Show this help message

ARGUMENTS:
  SESSION_NAME           Name of the session to attach to

EXAMPLES:
  pots attach prunejuice-help-dev    # Attach to specific session

EOF
    elif [ "$subcommand" = "kill" ]; then
        cat << 'EOF'
Usage: pots kill [OPTIONS] SESSION_NAME

Terminates a tmux session.

OPTIONS:
  -h, --help              Show this help message
  -f, --force             Kill without confirmation

ARGUMENTS:
  SESSION_NAME           Name of the session to kill

EXAMPLES:
  pots kill prunejuice-help-dev      # Kill session with confirmation
  pots kill -f old-session           # Kill without confirmation

EOF
    elif [ "$subcommand" = "cleanup" ]; then
        cat << 'EOF'
Usage: pots cleanup [OPTIONS]

Removes orphaned sessions (sessions for non-existent worktrees).

OPTIONS:
  -h, --help              Show this help message
  -p, --project PROJECT   Filter by project name
  -n, --dry-run           Show what would be removed without removing
  -y, --yes               Remove without confirmation

EXAMPLES:
  pots cleanup                   # Interactive cleanup of orphaned sessions
  pots cleanup -p prunejuice     # Cleanup sessions for prunejuice project
  pots cleanup --dry-run         # Preview what would be cleaned up
  pots cleanup -y                # Cleanup without confirmation

EOF
    else
        cat << 'EOF'
POTS - tmux Session Manager for Worktrees

Usage: pots COMMAND [OPTIONS]

COMMANDS:
  create     Create a new tmux session for a worktree
  list       List existing tmux sessions
  attach     Attach to an existing session
  kill       Terminate a session
  cleanup    Remove orphaned sessions

OPTIONS:
  -h, --help              Show this help message

EXAMPLES:
  pots create /path/to/worktree      # Create session for worktree
  pots list                          # List all sessions
  pots attach session-name           # Attach to session
  pots kill session-name             # Kill session
  pots cleanup                       # Remove orphaned sessions

Use 'pots COMMAND --help' for more information on a specific command.

EOF
    fi
}