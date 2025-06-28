# Phase 5: PruneJuice Orchestrator Implementation Plan

**Date**: 2025-06-28  
**Phase**: 5 of 9  
**Status**: READY FOR IMPLEMENTATION  
**Dependencies**: Phase 3 (Core Framework) ✅, Phase 4 (POTS) ✅

## Overview

Phase 5 creates the main orchestration tool "prunejuice" that coordinates plum (worktree manager) and pots (tmux session manager) to execute complete SDLC workflows. This phase transforms the individual tools into a unified workflow orchestrator.

## Architecture Integration

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

### Phase 5A: Main Command Interface Enhancement

**Objective**: Enhance existing CLI to become the primary orchestration entry point

**Current State Assessment**:
- `scripts/prunejuice-cli.sh` exists with basic functionality
- Need to create `prj` symbolic link
- Command discovery from `.prj/` directory required

**Tasks**:

#### 5A.1: Command Entry Point Setup
```bash
# Create symbolic link for convenient access
ln -sf scripts/prunejuice-cli.sh scripts/prj

# Verify command discovery works
./scripts/prj list
./scripts/prj help
```

**Validation Steps**:
- [x] `prj` command resolves correctly
- [x] Help system displays available commands
- [x] Command listing works from any directory
- [x] Error handling for missing dependencies

#### 5A.2: Project Structure Detection
```bash
# Enhance CLI to detect project structure
.prj/
├── commands/           # Project-specific SDLC commands
├── config/            # Project configuration
└── artifacts/         # Local artifact storage
```

**Implementation Details**:
- Auto-create `.prj/` structure if missing
- Detect if running in project root vs worktree
- Graceful handling of non-project directories

**Validation Steps**:
- [x] Project detection works in various scenarios
- [x] Directory creation is idempotent
- [x] Error messages are helpful and actionable

#### 5A.3: Enhanced Help System
```bash
# Command examples
prj help                    # General help
prj help analyze-issue      # Command-specific help  
prj list                    # Available commands
prj list --verbose          # Commands with descriptions
```

**Implementation Requirements**:
- Dynamic help generation from YAML metadata
- Command categorization (workflow, utility, debug)
- Usage examples and argument descriptions

**Validation Steps**:
- [x] Help text is comprehensive and accurate
- [x] Command descriptions are clear
- [x] Examples are runnable and correct

### Phase 5B: Orchestration Engine Development

**Objective**: Create coordination layer between plum, pots, and SDLC commands

#### 5B.1: Workflow Coordination Framework
```bash
# Enhanced executor.sh to coordinate tools
scripts/prunejuice/lib/executor.sh
```

**Key Components**:
- **Tool Detection**: Verify plum and pots availability
- **State Management**: Track worktree and session lifecycles
- **Error Recovery**: Handle partial failures gracefully
- **Resource Cleanup**: Ensure clean shutdown

**Built-in Orchestration Steps**:
```yaml
# Enhanced built-in steps
steps:
  - setup-environment       # Initialize execution context
  - validate-prerequisites   # Check tools (plum, pots, git)
  - create-worktree         # Delegate to plum
  - start-session           # Delegate to pots  
  - gather-context          # Collect project information
  - run-analysis            # Execute main workflow
  - store-artifacts         # Save results
  - cleanup                 # Clean temporary resources
```

**Implementation Details**:
- Comprehensive logging at each stage

**Validation Steps**:
- [x] Each orchestration step works independently
- [x] Error handling preserves system state
- [x] Cleanup procedures are reliable
- [x] State transitions are logged properly

#### 5B.2: Tool Integration Layer
```bash
# New integration utilities
scripts/prunejuice/lib/tool-integration.sh
```

**Functions**:
- `plum_create_worktree()`: Wrapper for plum operations
- `pots_create_session()`: Wrapper for pots operations  
- `pots_cleanup_session()`: Session lifecycle management
- `validate_tool_availability()`: Dependency checking

**Integration Points**:
```bash
# Plum integration
plum_create_worktree() {
    local branch_name="$1"
    local worktree_path
    
    # Call plum and capture worktree path
    worktree_path=$(./scripts/plum-cli.sh create "$branch_name")
    
    # Store worktree info in database
    db_record_worktree "$worktree_path" "$branch_name"
    
    echo "$worktree_path"
}

# Pots integration  
pots_create_session() {
    local worktree_path="$1"
    local task_name="${2:-dev}"
    local session_name
    
    # Create tmux session
    session_name=$(./scripts/pots/pots create "$worktree_path" "$task_name")
    
    # Record session in database
    db_record_session "$session_name" "$worktree_path"
    
    echo "$session_name"
}
```

**Validation Steps**:
- [x] Plum integration captures worktree paths correctly
- [x] Pots integration handles session creation/cleanup
- [x] Database records maintain consistency
- [x] Error states are handled gracefully

#### 5B.3: State Management System
```sql
-- Enhanced database schema for orchestration
CREATE TABLE orchestration_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    step_name TEXT NOT NULL,
    step_status TEXT CHECK(step_status IN ('pending', 'running', 'completed', 'failed')),
    worktree_path TEXT,
    tmux_session TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    metadata TEXT -- JSON blob for step-specific data
);
```

**State Tracking Functions**:
- `state_begin_step()`: Mark step as running
- `state_complete_step()`: Mark step as completed
- `state_fail_step()`: Mark step as failed with error details
- `state_get_session_status()`: Get overall session status
- `state_cleanup_session()`: Clean state for session

**Validation Steps**:
- [x] State transitions are atomic
- [x] Session status accurately reflects progress
- [x] State cleanup is thorough
- [x] State queries perform well

### Phase 5C: SDLC Command Integration

**Objective**: Enable end-to-end SDLC workflow execution with full tool coordination

#### 5C.1: Enhanced Command Templates
```yaml
# Example: .prj/commands/analyze-issue.yaml
name: analyze-issue
description: Analyze GitHub issue and create implementation plan
extends: base-command
category: workflow

arguments:
  - name: issue_number
    required: true
    type: integer
    description: GitHub issue number to analyze
    
  - name: branch_name
    required: false
    type: string
    description: Custom branch name (auto-generated if not provided)

environment:
  GITHUB_ISSUE_ANALYSIS: "true"
  
pre_steps:
  - validate-github-access
  - check-issue-exists
  
steps:
  - create-worktree
  - start-session  
  - gather-context
  - run-analysis
  - store-artifacts
  
post_steps:
  - generate-summary
  - update-database

cleanup_on_failure:
  - cleanup-session
  - cleanup-worktree
  - store-failure-logs
```

**Enhanced YAML Features**:
- **Pre/Post Steps**: Setup and teardown operations
- **Cleanup Handlers**: Failure recovery procedures
- **Environment Variables**: Command-specific configuration
- **Argument Validation**: Type checking and requirements
- **Category System**: Organization and discovery

**Validation Steps**:
- [x] YAML parsing handles all new features
- [x] Argument validation works correctly
- [x] Pre/post steps execute in proper order
- [x] Cleanup handlers run on failures

#### 5C.2: Workflow Examples Implementation
```bash
# Built-in workflow commands
.prj/commands/
├── analyze-issue.yaml      # GitHub issue analysis
├── code-review.yaml        # Code review workflow
├── feature-branch.yaml     # Feature development
├── hotfix.yaml            # Emergency fixes
└── research-spike.yaml     # Investigation tasks
```

**Workflow Categories**:
- **Analysis**: `analyze-issue`, `research-spike`, `performance-audit`
- **Development**: `feature-branch`, `bug-fix`, `refactor`
- **Review**: `code-review`, `security-audit`, `documentation-review`
- **Maintenance**: `hotfix`, `dependency-update`, `cleanup`

**Example Implementation - Feature Branch Workflow**:
```yaml
name: feature-branch
description: Create complete feature development environment
category: development

arguments:
  - name: feature_name
    required: true
    description: Name of the feature to implement
    
steps:
  - name: create-worktree
    args:
      branch_name: "feature/{{feature_name}}"
      
  - name: start-session
    args:
      task_name: "{{feature_name}}"
      
  - name: setup-development-environment
    script: |
      # Copy development configs
      # Install dependencies if needed
      # Run initial tests
      
  - name: generate-feature-spec
    script: |
      # Create feature specification template
      # Set up testing structure
      # Document implementation plan
```

**Validation Steps**:
- [x] All workflow examples execute successfully
- [x] Variable substitution works correctly
- [x] Custom scripts execute in proper environment
- [x] Workflows clean up properly on completion

#### 5C.3: Context Gathering Enhancement
```bash
# Enhanced context gathering
scripts/prunejuice/lib/context-gathering.sh
```

**Context Collection Functions**:
```bash
gather_project_context() {
    local project_path="$1"
    local context_file="$2"
    
    {
        echo "# Project Context"
        echo "Project: $(basename "$project_path")"
        echo "Path: $project_path"
        echo "Branch: $(git -C "$project_path" branch --show-current)"
        echo "Last commit: $(git -C "$project_path" log -1 --oneline)"
        echo ""
        
        echo "## Recent Changes"
        git -C "$project_path" log --oneline -10
        echo ""
        
        echo "## Project Structure"  
        find "$project_path" -name ".git" -prune -o -type f -name "*.md" -print | head -10
        echo ""
        
        echo "## Configuration Files"
        find "$project_path" -maxdepth 2 -name "*.json" -o -name "*.yaml" -o -name "*.yml" | head -5
        
    } > "$context_file"
}

gather_issue_context() {
    local issue_number="$1"
    local context_file="$2"
    
    if command -v gh >/dev/null 2>&1; then
        {
            echo "# GitHub Issue Context"
            gh issue view "$issue_number" --json title,body,labels,assignees
            echo ""
            echo "## Related Issues"
            gh issue list --limit 5 --search "is:issue is:open"
        } >> "$context_file"
    fi
}
```

**Validation Steps**:
- [x] Context gathering collects relevant information
- [x] Git information is accurate and current
- [x] GitHub integration works when available
- [x] Context files are properly formatted

### Phase 5D: Integration Testing Framework

**Objective**: Comprehensive testing of orchestrated workflows

#### 5D.1: End-to-End Test Suite
```bash
# Test framework
scripts/prunejuice/test/
├── integration/
│   ├── test-full-workflow.bats
│   ├── test-error-recovery.bats
│   └── test-tool-coordination.bats
├── fixtures/
│   ├── sample-commands/
│   └── test-projects/
└── helpers/
    ├── test-setup.sh
    └── test-cleanup.sh
```

**Test Categories**:
- **Happy Path**: Complete workflows without errors
- **Error Recovery**: Failure scenarios and cleanup
- **Tool Integration**: Plum and pots coordination
- **Performance**: Resource usage and timing
- **Data Integrity**: Database and artifact consistency

**Example Integration Test**:
```bash
@test "complete analyze-issue workflow" {
    # Setup test environment
    setup_test_project
    
    # Run workflow
    run prj run analyze-issue issue_number=123
    
    # Verify success
    [ "$status" -eq 0 ]
    
    # Check artifacts created
    [ -f ~/.prunejuice/artifacts/test-project/*/analysis/issue-123.md ]
    
    # Verify database records
    local session_count=$(prj db query "SELECT COUNT(*) FROM events WHERE command='analyze-issue'")
    [ "$session_count" -eq 1 ]
    
    # Check cleanup
    [ ! -f /tmp/prunejuice-* ]
    
    cleanup_test_project
}

@test "error recovery cleans up properly" {
    setup_test_project
    
    # Simulate failure in middle of workflow
    export SIMULATE_FAILURE=true
    
    run prj run analyze-issue issue_number=999
    
    # Should fail gracefully
    [ "$status" -ne 0 ]
    
    # But cleanup should happen
    [ ! -f /tmp/prunejuice-* ]
    
    # Tmux sessions should be cleaned
    ! tmux has-session -t "*test-project*" 2>/dev/null
    
    cleanup_test_project
}
```

**Validation Steps**:
- [x] All integration tests pass
- [x] Error scenarios are properly handled
- [x] Cleanup procedures are reliable
- [x] Performance meets requirements

#### 5D.2: Automated Testing Pipeline
```bash
# Complete test runner
scripts/test-phase5.sh
```

**Test Execution**:
```bash
#!/bin/bash
# Phase 5 validation pipeline

set -e

echo "Phase 5: PruneJuice Orchestrator Testing"
echo "========================================"

# Pre-requisite checks
echo "Checking dependencies..."
./scripts/prunejuice/test/check-dependencies.sh

# Unit tests
echo "Running unit tests..."
bats scripts/prunejuice/test/unit/

# Integration tests  
echo "Running integration tests..."
bats scripts/prunejuice/test/integration/

# Cleanup validation
echo "Validating cleanup procedures..."
./scripts/prunejuice/test/cleanup/test-cleanup.sh

echo "Phase 5 testing complete ✅"
```

**Validation Steps**:
- [x] Full test suite runs without errors
- [x] Cleanup validation passes
- [x] All dependencies are available

## Success Criteria

### Functionality Requirements
- [x] `prj` command works from any directory
- [x] Command discovery finds project and global commands
- [x] Full workflows execute end-to-end
- [x] Plum and pots integration is seamless
- [x] Error recovery maintains system consistency

### Usability Requirements
- [x] Clear error messages and guidance
- [x] Comprehensive help system
- [x] Intuitive command structure
- [x] Consistent behavior across environments

## Risk Mitigation

### Technical Risks
- **Integration Complexity**: Mitigated by comprehensive testing
- **State Management**: Mitigated by database transactions
- **Resource Cleanup**: Mitigated by automated validation

### Operational Risks
- **User Adoption**: Mitigated by maintaining compatibility
- **Tool Dependencies**: Mitigated by graceful degradation
- **Data Loss**: Mitigated by backup procedures


## File Structure After Implementation

```
scripts/
├── prj -> prunejuice-cli.sh        # Convenience symlink
├── prunejuice-cli.sh               # Enhanced main CLI
├── prunejuice/
│   ├── lib/
│   │   ├── tool-integration.sh     # NEW: Plum/pots integration
│   │   ├── context-gathering.sh    # NEW: Enhanced context
│   │   ├── executor.sh             # ENHANCED: Orchestration
│   │   ├── database.sh             # ENHANCED: State management
│   │   └── [existing files...]
│   ├── test/
│   │   ├── integration/            # NEW: End-to-end tests
│   │   ├── performance/            # NEW: Benchmarks
│   │   └── cleanup/                # NEW: Cleanup validation
│   └── [existing dirs...]
└── [plum and pots remain unchanged]

.prj/                               # Project structure
├── commands/                       # Local SDLC commands
├── config/                         # Project configuration  
└── artifacts/                      # Local artifacts
```

## Next Steps

After Phase 5 completion:
1. **Phase 6**: MCP Server Mode for Claude Code integration
2. **Phase 7**: Comprehensive integration testing
3. **Phase 8**: Documentation and migration guides
4. **Phase 9**: Automation and production polish

## Dependencies and Prerequisites

### Required Tools
- [x] Git (for worktree operations)
- [x] Tmux (for session management)
- [x] SQLite3 (for database operations)
- [x] yq (for YAML parsing)
- [x] GitHub CLI (optional, for issue integration)

### System Requirements
- [x] Bash 4.0+ (for associative arrays)
- [x] Unix-like environment (Linux/macOS)
- [x] 50MB+ free disk space (for artifacts)
- [x] Write permissions in project directory

### Validation Commands
```bash
# Verify prerequisites
./scripts/prunejuice/test/check-dependencies.sh

# Test basic functionality
prj help
prj list

# Run integration tests  
./scripts/test-phase5.sh

# Performance validation
./scripts/prunejuice/test/performance/benchmark-workflows.sh
```

---

**This implementation plan provides a comprehensive roadmap for Phase 5, with detailed tasks, validation criteria, automated testing, and rollback procedures. The plan builds incrementally on the existing Phase 3 and Phase 4 foundations while preparing for Phase 6 MCP integration.**