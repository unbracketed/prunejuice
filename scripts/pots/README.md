# POTS - tmux Session Manager for Worktrees

POTS (Plain Old Tmux Sessions) is a tmux session manager that integrates seamlessly with the plum worktree system. It enables developers to manage multiple tmux sessions aligned with their git worktrees for efficient parallel development workflows.

## Features

- **Automatic Session Naming**: Sessions are named based on project, worktree, and task
- **Worktree Integration**: Create and manage sessions tied to git worktrees
- **Session Lifecycle Management**: Create, list, attach, kill, and cleanup sessions
- **Orphaned Session Detection**: Find and cleanup sessions for deleted worktrees
- **Configuration Support**: Customizable through configuration files and environment variables

## Installation

1. Ensure tmux is installed:
   ```bash
   tmux -V  # Should show tmux version
   ```

2. The POTS tool is included in the PruneJuice repository at `scripts/pots/`

3. Add to your PATH (optional):
   ```bash
   export PATH="$PATH:/path/to/prunejuice/scripts/pots"
   ```

   Or create an alias:
   ```bash
   alias pots="/path/to/prunejuice/scripts/pots/pots"
   ```

## Usage

### Create a Session

Create a new tmux session for a worktree:

```bash
pots create /path/to/worktree
```

With custom task name:

```bash
pots create --task backend /path/to/worktree
```

Without auto-attaching:

```bash
pots create --no-attach /path/to/worktree
```

### List Sessions

List all tmux sessions:

```bash
pots list
```

List with detailed information:

```bash
pots list --verbose
```

Filter sessions by pattern:

```bash
pots list prunejuice
```

### Attach to Session

Attach to an existing session:

```bash
pots attach session-name
```

### Kill Session

Terminate a session with confirmation:

```bash
pots kill session-name
```

Force kill without confirmation:

```bash
pots kill --force session-name
```

### Cleanup Orphaned Sessions

Find and remove sessions for non-existent worktrees:

```bash
pots cleanup
```

Preview what would be cleaned:

```bash
pots cleanup --dry-run
```

Filter by project:

```bash
pots cleanup --project prunejuice
```

## Session Naming Convention

Sessions follow the pattern: `{project}-{worktree}-{task}`

Examples:
- `prunejuice-help-dev`
- `prunejuice-feature-impl-backend`
- `plum-bugfix-dev`

## Configuration

POTS looks for configuration in these locations (in order):

1. `scripts/pots/pots-config` (bundled with POTS)
2. `~/.pots-config`
3. `~/.config/pots/config`

### Configuration Variables

```bash
# Session settings
POTS_AUTO_START_SESSION=false    # Auto-start session on create
POTS_DEFAULT_TASK=dev            # Default task suffix
POTS_SESSION_PREFIX=""           # Optional session name prefix

# Tmux settings
POTS_TMUX_SESSION_PREFIX=plum    # Prefix for session identification
POTS_AUTO_ATTACH=true            # Auto-attach after creation

# Integration settings
POTS_PLUM_INTEGRATION=true       # Enable plum integration
POTS_CLEANUP_ON_WORKTREE_REMOVE=true  # Cleanup on worktree removal
```

## Integration with Plum

POTS is designed to work seamlessly with plum worktrees:

1. Create a worktree with plum:
   ```bash
   plum create feature-branch
   ```

2. Create a tmux session for the worktree:
   ```bash
   pots create ../prunejuice-feature-branch
   ```

3. The session will be created in the worktree directory

## Architecture

```
scripts/pots/
├── pots                    # Main executable
├── lib/
│   ├── session-utils.sh   # Core tmux session management
│   ├── worktree-sync.sh   # Integration with plum
│   ├── pots-ui.sh         # User interface and help
│   └── shared/            # Symlinked shared libraries
│       ├── config.sh      → ../../plum/lib/config.sh
│       ├── git-utils.sh   → ../../plum/lib/git-utils.sh
│       └── ui.sh          → ../../plum/lib/ui.sh
├── pots-config            # Default configuration
├── test/                  # Test suite
│   ├── test-session-utils.bats
│   ├── test-worktree-sync.bats
│   ├── test-pots-commands.bats
│   ├── run-tests.sh
│   └── manual-test.sh
└── README.md              # This file
```

## Testing

POTS includes a comprehensive test suite using bats:

```bash
# Install bats (if not already installed)
brew install bats-core  # macOS
# or
apt-get install bats    # Debian/Ubuntu

# Run all tests
cd scripts/pots/test
./run-tests.sh
```

For manual testing without bats:

```bash
./manual-test.sh
```

## Troubleshooting

### "tmux is not installed or not in PATH"

Install tmux:
- macOS: `brew install tmux`
- Ubuntu/Debian: `apt-get install tmux`
- Other: Check your package manager

### "Working directory does not exist"

Ensure the worktree path exists and is accessible. Use absolute paths.

### "Session already exists"

A session with that name already exists. Either:
- Attach to it: `pots attach session-name`
- Kill it first: `pots kill session-name`
- Use a different task name: `pots create --task other /path/to/worktree`

### Sessions not cleaned up automatically

Run manual cleanup:
```bash
pots cleanup
```

## Contributing

When contributing to POTS:

1. Follow the existing code patterns from plum
2. Add tests for new functionality
3. Update this README if adding features
4. Test with real worktrees before submitting

## License

POTS is part of the PruneJuice project and follows the same license terms.