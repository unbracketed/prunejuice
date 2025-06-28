# Complete Implementation Plan: PruneJuice Tool Suite Refactoring

## Overview

This plan transforms the current PruneJuice project into a comprehensive three-tool suite for managing parallel agentic coding workflows:

```
Current State:           Target State:
prunejuice               plum (Git worktree manager)
(worktree-manager)   ->  pots (Tmux session manager)
                         prunejuice (SDLC orchestrator)
```

## Architecture & Dependencies

```
                    +-------------+
                    | prunejuice  |
                    | (orchestr.) |
                    +------+------+
                           |
                  +--------+--------+
                  |                 |
            +-----+-----+     +-----+-----+
            |    plum   |     |    pots   |
            | (worktree)|     |  (tmux)   |
            +-----------+     +-----------+
                  |                 |
            +-----+-----+     +-----+-----+
            |    Git    |     |   tmux    |
            | worktrees |     | sessions  |
            +-----------+     +-----------+
```

## Implementation Phases

### Phase 1: Preparation & Analysis

**Objectives:**
- Assess current system and create safety net
- Document existing interfaces and behaviors
- Prepare for safe migration

**Tasks:**
1. **System Inventory**
   - Map all script files and their dependencies
   - Document current CLI commands and options
   - Identify all file references requiring updates

2. **Backup Strategy**
   - Create comprehensive backup of working system
   - Document current worktree configurations
   - Test backup restoration procedures

3. **Impact Analysis**
   - List all MCP template references to update
   - Identify external scripts calling worktree-manager
   - Map configuration files requiring changes

### Phase 2: Plum Migration

**Objectives:**
- Rename worktree-manager to plum
- Maintain all existing functionality
- Update all references and configurations

**Tasks:**
1. **Directory Structure**
   ```
   scripts/worktree-manager/  ->  scripts/plum/
   ├── lib/                       ├── lib/
   ├── mcp-templates/             ├── mcp-templates/
   └── worktree-config            └── plum-config
   ```

2. **Script Updates**
   - Update entry point: `./scripts/worktree-cli.sh` -> `./scripts/plum-cli.sh`
   - Modify all internal imports and source statements
   - Update command names and help text

3. **Configuration Migration**
   - Rename environment variables: `WORKTREE_*` -> `PLUM_*`
   - Update MCP templates to reference plum
   - Modify any hardcoded paths or references

4. **Validation Testing**
   - Test all existing worktree operations
   - Verify MCP template compatibility
   - Confirm editor integration still works

### Phase 3: Core Framework Development

**Objectives:**
- Build SDLC command infrastructure
- Implement event tracking system
- Create foundation for orchestration

**Tasks:**
1. **Database Schema**
   ```sql
   CREATE TABLE events (
     id INTEGER PRIMARY KEY,
     command TEXT,
     project_path TEXT,
     worktree_name TEXT,
     session_id TEXT,
     start_time DATETIME,
     end_time DATETIME,
     status TEXT,
     artifacts_path TEXT
   );
   ```

2. **YAML Command System**
   - Create command definition parser
   - Implement inheritance from base commands
   - Build validation for command structure
   - Create command execution engine

3. **Artifact Management**
   - Implement specs/ directory structure
   - Create artifact storage utilities
   - Build session logging system
   - Design prompt assembly framework

`### Phase 4: Pots Development
`
**Objectives:**
- Create tmux session manager
- Integrate with plum worktree system
- Enable parallel session management

**Tasks:**
1. **Core Session Management**
   - Create tmux session lifecycle utilities
   - Implement naming conventions: `project-worktree-task`
   - Build session discovery and listing
   - Add session cleanup and management

2. **Worktree Integration**
   - Query plum for available worktrees
   - Automatically set working directories
   - Coordinate session naming with worktree names
   - Handle worktree cleanup -> session cleanup

3. **Command Interface**
   ```bash
   pots create <project> <worktree> [task]
   pots list [project]
   pots attach <session-name>
   pots kill <session-name>
   pots cleanup [project]
   ```

### Phase 5: Prunejuice Orchestrator

**Objectives:**
- Create main orchestration tool
- Integrate plum + pots + framework
- Enable SDLC command execution

**Tasks:**
1. **Main Command Interface**
   - Create `prunejuice` / `prj` command entry point
   - Implement command discovery from `.prj/` directory
   - Build help system and command listing

2. **Orchestration Engine**
   - Coordinate plum worktree creation
   - Manage pots session lifecycle
   - Execute SDLC command sequences
   - Handle prompt assembly and Claude Code integration

3. **SDLC Command Examples**
   ```yaml
   # .prj/commands/analyze-issue.yaml
   name: analyze-issue
   desc: Analyze GitHub issue and create implementation plan
   arguments:
     - issue_number: required
   steps:
     - create-worktree
     - start-session
     - gather-context
     - run-analysis
     - store-artifacts
   ```
### Phase 6 MCP Server mode

1. **MCP Server Mode**
   - Expose SDLC commands as MCP tools
   - Enable Claude Code to call commands directly
   - Implement command result formatting

### Phase 7: Integration & Testing

**Objectives:**
- Validate end-to-end workflows
- Test performance and reliability
- Ensure robust error handling

**Tasks:**
1. **Workflow Testing**
   - Test complete SDLC command execution
   - Verify artifact generation and storage
   - Validate session and worktree cleanup

2. **Performance Validation**
   - Test multiple concurrent sessions
   - Measure resource usage and cleanup
   - Validate database performance

3. **Error Handling**
   - Test failure scenarios and recovery
   - Implement graceful degradation
   - Add comprehensive logging

### Phase 8: Documentation & Migration

**Objectives:**
- Update all documentation
- Create migration guides
- Provide example configurations

**Tasks:**
1. **Documentation Updates**
   - Update README files for new structure
   - Document SDLC command format
   - Create user guides for each tool

2. **Migration Resources**
   - Create automated migration scripts
   - Document breaking changes
   - Provide rollback procedures

3. **Example Configurations**
   - Create default SDLC command sets
   - Provide sample project configurations
   - Document best practices

### Phase 9: Automation & Polish

**Objectives:**
- Add comprehensive automation
- Implement quality assurance
- Prepare for production use

**Tasks:**
1. **Testing Automation**
   - Create CI/CD pipeline for all tools
   - Implement automated integration tests
   - Add performance benchmarking

2. **Quality Improvements**
   - Add comprehensive error handling
   - Implement configuration validation
   - Create diagnostic utilities

3. **Installation & Setup**
   - Create automated installation scripts
   - Build configuration wizards
   - Add system requirements validation

## Key Automation Features

### Automated Testing Pipeline
```bash
#!/bin/bash
# Test all three tools together
./test/test-plum.sh
./test/test-pots.sh  
./test/test-prunejuice.sh
./test/test-integration.sh
```

### Configuration Generation
- Auto-generate MCP templates from schemas
- Create command definitions from templates
- Validate configurations automatically

### Migration Scripts
- Automated backup and restore
- Configuration migration utilities
- Rollback procedures

## Success Criteria

1. **Functionality**: All three tools work independently and together
2. **Compatibility**: Existing workflows continue to function
3. **Performance**: New system matches or exceeds current performance
4. **Usability**: Clear interfaces and comprehensive documentation
5. **Reliability**: Robust error handling and recovery procedures

## Risk Mitigation

- **Daily backups** during migration phases
- **Feature flags** for new functionality
- **Parallel systems** during transition
- **Comprehensive testing** at each phase
- **User feedback loops** after major milestones

## Next Steps

1. **Start Phase 1**: Run system audit and create backup
2. **Set up development environment**: Create feature branch
3. **Begin implementation**: Start with preparation tasks

## Implementation Process

For each task in each Phase:
1. Analyze the task for requirements and validation steps
2. Write out the implementation plan to a doc with title `<phase>-<task>-implementation-plan.md`
3. Implement the `<phase>-<task>-implementation-plan`
4. When the plan is implemented and validated, write a summary to `<phase>-<task>-implementation-summary.md`

This ensures thorough planning, implementation, and documentation of each step in the refactoring process.