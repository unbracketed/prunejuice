# Phase 1: System Inventory - Implementation Plan

## Objective
Create a comprehensive inventory of the current PruneJuice system to understand all components, dependencies, and interfaces that need to be updated during the refactoring.

## Requirements Analysis

### 1. Map All Script Files and Dependencies
- **Requirement**: Identify every script file in the project
- **Scope**: All `.sh`, `.py`, and executable files
- **Dependencies**: Internal sourcing, external tool dependencies
- **Output**: Complete file dependency map

### 2. Document Current CLI Commands and Options
- **Requirement**: Catalog all user-facing commands and their parameters
- **Scope**: Main entry points, all command-line options, help text
- **Output**: CLI interface documentation

### 3. Identify File References Requiring Updates
- **Requirement**: Find all hardcoded paths and references that will change
- **Scope**: Internal paths, configuration references, documentation
- **Output**: Reference update checklist

## Implementation Steps

### Step 1: Discover All Script Files
```bash
# Find all executable and script files
find . -type f \( -name "*.sh" -o -name "*.py" -o -perm +111 \) | grep -v .git
```

### Step 2: Analyze Script Dependencies
For each script file:
- Identify `source` statements and imports
- Document external tool dependencies (gum, gh, git, etc.)
- Map inter-script relationships

### Step 3: Document CLI Interfaces
- Run each entry point script with `--help` or `-h`
- Document all command-line options and arguments
- Capture current help text and usage patterns

### Step 4: Identify Reference Points
Search for hardcoded references that will need updates:
- "worktree-manager" strings in code
- "WORKTREE_" environment variable references
- Path references to scripts/worktree-manager/
- MCP template references

### Step 5: Create Inventory Documentation
Generate comprehensive documentation including:
- File structure diagram
- Dependency graph
- CLI command reference
- Update checklist for migration

## Validation Steps

1. **Completeness Check**: Verify all scripts in project are catalogued
2. **Dependency Verification**: Test that all identified dependencies are accurate
3. **CLI Documentation**: Confirm all commands and options are documented
4. **Reference Accuracy**: Validate that file reference mapping captures all update points

## Deliverables

1. **system-inventory.md**: Complete system documentation
2. **dependency-map.md**: Visual dependency relationships  
3. **cli-reference.md**: Current command interface documentation
4. **migration-checklist.md**: List of all references requiring updates

## Success Criteria

- [ ] All script files identified and documented
- [ ] All dependencies mapped accurately
- [ ] Complete CLI interface documented
- [ ] All hardcoded references catalogued
- [ ] Documentation validated by testing current functionality