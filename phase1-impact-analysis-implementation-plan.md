# Phase 1: Impact Analysis - Implementation Plan

## Objective
Conduct comprehensive impact analysis to identify all external dependencies, references, and configurations that will be affected by the migration from worktree-manager to plum, ensuring no breaking changes are overlooked.

## Requirements Analysis

### 1. List All MCP Template References to Update
- **Requirement**: Identify all MCP template files and their references
- **Scope**: Template discovery, content analysis, reference mapping
- **Output**: Complete MCP template update checklist

### 2. Identify External Scripts Calling worktree-manager
- **Requirement**: Find all external dependencies on current tool names/paths
- **Scope**: System scripts, user scripts, CI/CD, documentation examples
- **Output**: External dependency impact map

### 3. Map Configuration Files Requiring Changes
- **Requirement**: Catalog all configuration files needing updates
- **Scope**: User configs, project configs, environment files, settings
- **Output**: Configuration migration matrix

## Implementation Steps

### Step 1: MCP Template Impact Analysis
```bash
# Discover MCP template directory and contents
find . -name "*mcp*" -type d
find . -name "*.mcp.json" -o -name "*mcp*.json"

# Analyze MCP template contents for hardcoded references
grep -r "worktree-manager" scripts/worktree-manager/mcp-templates/ 2>/dev/null || echo "No MCP templates found"
grep -r "WORKTREE_" scripts/worktree-manager/mcp-templates/ 2>/dev/null || echo "No WORKTREE_ refs in templates"

# Check for MCP template usage in current system
grep -r "mcp-templates" . --include="*.sh" --include="*.json"
```

### Step 2: External Script Dependency Analysis
```bash
# Search for external references to worktree-manager
grep -r "worktree-manager" . --exclude-dir=backups --include="*.sh" --include="*.json" --include="*.md"

# Search for references to specific script names
grep -r "worktree-create" . --exclude-dir=backups --include="*.sh" --include="*.json" --include="*.md"
grep -r "worktree-cli" . --exclude-dir=backups --include="*.sh" --include="*.json" --include="*.md"

# Check for hardcoded paths that will break
grep -r "scripts/worktree-manager" . --exclude-dir=backups
```

### Step 3: Configuration File Impact Analysis
```bash
# Identify all configuration file types and locations
find . -name "*config*" -o -name "*.conf" -o -name "*.cfg" -type f
find . -name ".env*" -o -name "settings*" -type f

# Check for WORKTREE_ environment variable usage
grep -r "WORKTREE_" . --exclude-dir=backups --include="*.sh" --include="*.md" --include="*.json" --include="*.env"

# Analyze configuration loading patterns
grep -r "source.*config" scripts/ --include="*.sh"
grep -r "\.config.*worktree" . --exclude-dir=backups
```

### Step 4: User Impact Assessment
```bash
# Check for user-facing commands and aliases
grep -r "alias.*worktree" ~ 2>/dev/null || echo "No user aliases found"
find ~ -name "*worktree*" -type f 2>/dev/null || echo "No user worktree files found"

# Check common shell configuration files for references
for file in ~/.bashrc ~/.zshrc ~/.bash_profile ~/.profile; do
    if [ -f "$file" ]; then
        echo "Checking $file:"
        grep -n "worktree" "$file" 2>/dev/null || echo "  No references found"
    fi
done
```

### Step 5: Documentation Impact Analysis
```bash
# Find all documentation with examples that need updating
find . -name "*.md" -exec grep -l "worktree-manager\|WORKTREE_\|worktree-create" {} \;

# Check for hardcoded examples in documentation
grep -n "scripts/worktree-manager" *.md 2>/dev/null || echo "No hardcoded paths in root docs"
grep -n "WORKTREE_" *.md 2>/dev/null || echo "No WORKTREE_ vars in root docs"
```

### Step 6: Integration Impact Analysis
```bash
# Check Claude Code integration points
find . -name "settings*.json" -exec grep -l "worktree" {} \;
find . -name ".claude*" -type f -exec grep -l "worktree" {} \;

# Check for CI/CD and automation references
find . -name "Makefile" -o -name "*.yml" -o -name "*.yaml" | xargs grep -l "worktree" 2>/dev/null || echo "No CI/CD worktree references"

# Check for any test scripts that might reference current tools
find . -name "*test*" -type f | xargs grep -l "worktree" 2>/dev/null || echo "No test script references"
```

### Step 7: Create Impact Matrix
Generate comprehensive impact assessment matrix:

```bash
# Create impact analysis output file
cat > impact-analysis-matrix.md << 'EOF'
# Impact Analysis Matrix - worktree-manager → plum Migration

## High Impact Changes (Breaking)
| Component | Current | New | Impact Level | Action Required |
|-----------|---------|-----|--------------|-----------------|
| Directory Path | scripts/worktree-manager/ | scripts/plum/ | HIGH | Update all path references |
| Main Executable | worktree-create | plum | HIGH | Update command references |
| Environment Variables | WORKTREE_* | PLUM_* | HIGH | Update all variable names |

## Medium Impact Changes (Configurable)
| Component | Current | New | Impact Level | Action Required |
|-----------|---------|-----|--------------|-----------------|
| CLI Script | worktree-cli.sh | plum-cli.sh | MEDIUM | Update script name references |
| Config Files | worktree-config | plum-config | MEDIUM | Update config file names |

## Low Impact Changes (Internal)
| Component | Current | New | Impact Level | Action Required |
|-----------|---------|-----|--------------|-----------------|
| Function Names | worktree_* | plum_* (optional) | LOW | Optional refactoring |
| Library Names | lib/*.sh | lib/*.sh | LOW | No changes needed |
EOF
```

## Validation Steps

### 1. External Reference Completeness
- [ ] All MCP template references identified and catalogued
- [ ] All external script dependencies mapped
- [ ] All configuration file impacts documented
- [ ] All user-facing impacts assessed

### 2. Impact Assessment Accuracy
- [ ] Breaking changes clearly identified
- [ ] Non-breaking changes distinguished
- [ ] Migration complexity assessed for each component
- [ ] Required actions documented for each impact

### 3. Coverage Verification
- [ ] No external dependencies overlooked
- [ ] All integration points considered
- [ ] User impact thoroughly assessed
- [ ] Documentation impact completely mapped

## Deliverables

1. **mcp-template-analysis.md**: Complete MCP template impact assessment
2. **external-dependencies-map.md**: External script and system dependencies
3. **configuration-migration-matrix.md**: All configuration files requiring changes
4. **impact-analysis-matrix.md**: Comprehensive impact assessment with action items
5. **user-impact-assessment.md**: User-facing changes and communication needs
6. **integration-points-analysis.md**: All integration impacts (Claude, CI/CD, etc.)

## Success Criteria

- [ ] All MCP template references identified and update plan created
- [ ] All external script dependencies mapped with impact assessment
- [ ] All configuration files catalogued with migration requirements
- [ ] Complete impact matrix created with action items
- [ ] User communication needs identified
- [ ] No external dependencies overlooked
- [ ] Migration complexity accurately assessed for planning

## Risk Assessment Output

### High Risk (Breaking Changes)
- Components that will definitely break without updates
- Required immediate attention during migration
- Need user communication and coordination

### Medium Risk (Configuration Required)
- Components that need configuration updates
- May have backward compatibility options
- Can be phased or made optional

### Low Risk (Internal Changes)
- Components with minimal external impact
- Can be changed without affecting users
- Optional improvements for consistency

## Next Steps After Completion

1. **Use impact analysis** to refine migration timeline
2. **Prioritize high-impact changes** for careful handling
3. **Plan user communication** for breaking changes
4. **Begin Phase 2**: Plum Migration with complete impact awareness