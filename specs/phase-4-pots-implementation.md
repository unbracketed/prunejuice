# Phase 4: Pots Development - Implementation Plan

## Overview

Phase 4 creates **Pots**, a tmux session manager that integrates seamlessly with the plum worktree system. This tool enables developers to manage multiple tmux sessions aligned with their git worktrees for efficient parallel development workflows.

## Architecture

```
                    Pots Integration Architecture
                    
    +----------------+        +----------------+
    |      pots      |        |      plum      |
    | (tmux manager) |<------>| (worktree mgr) |
    +----------------+        +----------------+
             |                         |
             v                         v
    +----------------+        +----------------+
    |  tmux sessions |        |  git worktrees |
    | project-wt-task|        |  project-name  |
    +----------------+        +----------------+
```

### Directory Structure

```
scripts/pots/
├── pots                    # Main executable
├── lib/
│   ├── session-utils.sh   # Core tmux session management
│   ├── worktree-sync.sh   # Integration with plum
│   └── shared/            # Symlinked shared libraries
│       ├── config.sh      → ../../plum/lib/config.sh
│       ├── git-utils.sh   → ../../plum/lib/git-utils.sh
│       └── ui.sh          → ../../plum/lib/ui.sh
└── pots-config            # Default configuration
```

## Implementation Phases

### Phase 1: Foundation Setup

**Objectives:**
- Create directory structure
- Establish shared library integration
- Build basic session utilities

**Tasks:**

1. **Directory Creation**
   ```bash
   mkdir -p scripts/pots/lib/shared
   ```

2. **Shared Library Integration**
   ```bash
   # Create symlinks to plum libraries
   ln -s ../../plum/lib/config.sh scripts/pots/lib/shared/
   ln -s ../../plum/lib/git-utils.sh scripts/pots/lib/shared/
   ln -s ../../plum/lib/ui.sh scripts/pots/lib/shared/
   ```

3. **Core Session Utilities (session-utils.sh)**
   - `session_exists()` - Check if tmux session exists
   - `create_session()` - Create new tmux session with working directory
   - `list_sessions()` - List tmux sessions with filtering
   - `kill_session()` - Terminate tmux session
   - `session_name_sanitize()` - Clean names for tmux compatibility

4. **Session Naming Convention**
   - Format: `{project}-{worktree}-{task}`
   - Sanitization: Alphanumeric and hyphens only
   - Example: `prunejuice-feature-impl-backend`

### Phase 2: Core Session Management

**Objectives:**
- Complete session lifecycle operations
- Implement tmux command wrappers
- Add error handling and validation

**Tasks:**

1. **Session Lifecycle Functions**
   ```bash
   # Core tmux operations
   tmux new-session -d -s "$session_name" -c "$working_dir"
   tmux list-sessions -F "#{session_name}"
   tmux kill-session -t "$session_name"
   tmux attach-session -t "$session_name"
   ```

2. **Working Directory Management**
   - Automatically set session working directory to worktree path
   - Validate worktree exists before session creation
   - Handle path resolution and symbolic links

3. **Session Discovery**
   - Parse tmux session list output
   - Match sessions to project naming patterns
   - Filter sessions by project or worktree

### Phase 3: Worktree Integration

**Objectives:**
- Query plum for worktree information
- Map sessions to worktrees
- Coordinate cleanup operations

**Tasks:**

1. **Plum Integration (worktree-sync.sh)**
   ```bash
   # Query plum for worktree data
   get_worktrees_from_plum() {
       plum list | parse_worktree_output
   }
   ```

2. **Session-Worktree Mapping**
   - Extract project name from worktree paths
   - Generate session names from worktree directories
   - Validate worktree accessibility

3. **Cleanup Coordination**
   - Detect orphaned sessions (worktree removed)
   - Provide cleanup suggestions
   - Handle batch cleanup operations

### Phase 4: Command Interface

**Objectives:**
- Build user-facing CLI commands
- Implement help system
- Add interactive features

**Tasks:**

1. **Command Structure**
   ```bash
   pots create <project> <worktree> [task]
   pots list [project]
   pots attach <session-name>
   pots kill <session-name>
   pots cleanup [project]
   ```

2. **Command Implementations**

   **Create Command:**
   - Validate worktree exists via plum
   - Generate session name
   - Create tmux session in worktree directory
   - Optional task suffix for multiple sessions per worktree

   **List Command:**
   - Show sessions with worktree mapping
   - Filter by project if specified
   - Display session status and working directory

   **Attach Command:**
   - Connect to existing tmux session
   - Handle session not found errors
   - Support partial name matching

   **Kill Command:**
   - Terminate specified session
   - Confirm before deletion
   - Handle session not found gracefully

   **Cleanup Command:**
   - Find orphaned sessions
   - Interactive or batch removal
   - Report cleanup results

3. **Help System**
   - Command-specific help
   - Usage examples
   - Integration with plum help patterns

### Phase 5: Configuration & Error Handling

**Objectives:**
- Extend configuration system
- Add robust error handling
- Implement validation

**Tasks:**

1. **Configuration Extension**
   ```bash
   # Add to existing plum config files
   POTS_AUTO_START_SESSION=false
   POTS_DEFAULT_TASK="dev"
   POTS_SESSION_PREFIX=""
   ```

2. **Error Handling**
   - Tmux not available
   - Session already exists
   - Worktree not found
   - Permission issues
   - Session naming conflicts

3. **Validation**
   - Verify tmux installation
   - Check session name validity
   - Validate worktree accessibility
   - Confirm operations before execution

### Phase 6: Testing & Documentation

**Objectives:**
- Comprehensive test coverage
- Integration testing with plum
- Documentation updates

**Tasks:**

1. **Unit Testing (using bats)**
   ```bash
   test/test-session-utils.bats
   test/test-worktree-sync.bats
   test/test-pots-commands.bats
   ```

2. **Integration Testing**
   - Create worktree with plum
   - Create session with pots
   - Verify working directory setup
   - Test cleanup coordination

3. **Documentation**
   - Update README with pots usage
   - Document integration workflows
   - Provide troubleshooting guide

## Key Features

### Session Naming
- **Format**: `project-worktree-task`
- **Sanitization**: Remove special characters for tmux compatibility
- **Uniqueness**: Prevent naming conflicts

### Worktree Integration
- **Discovery**: Query plum for available worktrees
- **Mapping**: Automatic session-to-worktree association
- **Coordination**: Cleanup orphaned sessions when worktrees removed

### Command Interface
- **Simple Commands**: Easy-to-remember command structure
- **Interactive Mode**: Guided session creation
- **Batch Operations**: Cleanup multiple sessions

### Error Handling
- **Graceful Degradation**: Continue operation when possible
- **Clear Messages**: Helpful error descriptions
- **Recovery Suggestions**: Guide user to resolution

## Success Criteria

1. **Functionality**: All five commands work reliably
2. **Integration**: Seamless coordination with plum worktrees
3. **Performance**: Fast session operations (< 1 second)
4. **Reliability**: Handle edge cases without data loss
5. **Usability**: Intuitive command interface with helpful feedback

## Dependencies

- tmux installed and available in PATH
- plum worktree manager functional
- Bash 4.0+ for array and function support
- Git repository with worktrees configured

---

Ready to begin implementation? I can help implement specific phases or use the continuation ID `d923ed11-2cc5-44a5-8163-afe12b84107a` for related planning sessions.