# MCP Template Analysis - worktree-manager → plum Migration

## Overview

Analysis of MCP (Model Context Protocol) template system impact during the migration from worktree-manager to plum tool.

## Current MCP Template System

### Template Directory Configuration
- **Default directory**: `mcp-json-templates` (configurable)
- **Environment variable**: `WORKTREE_MCP_TEMPLATE_DIR`
- **Configuration locations**:
  - `scripts/worktree-manager/lib/config.sh`
  - `scripts/worktree-manager/worktree-config`
  - User configuration files

### Template Discovery and Usage
- **Template discovery**: Done in `scripts/worktree-manager/lib/mcp.sh`
- **Template activation**: Copies `.mcp.*.json` files to new worktree
- **Template types**: Project-specific MCP configurations for Claude Code

## Current Template References

### 1. Code References (requiring updates)
| File | Reference Type | Impact |
|------|----------------|--------|
| `lib/config.sh` | Default directory name | MEDIUM |
| `lib/mcp.sh` | Template directory path resolution | LOW |
| `worktree-config` | Default configuration | MEDIUM |
| `create-worktree-with-branch.sh` | Hardcoded path | HIGH |

### 2. Documentation References (requiring updates)
| File | Reference Count | Impact |
|------|----------------|--------|
| `scripts/worktree-manager/README.md` | 8 references | HIGH |
| `scripts/refactor-plan.md` | 3 references | MEDIUM |
| `system-inventory.md` | 1 reference | LOW |
| `cli-reference.md` | 1 reference | LOW |

### 3. Environment Variable References
```bash
# Current variable name (needs updating)
WORKTREE_MCP_TEMPLATE_DIR="${WORKTREE_MCP_TEMPLATE_DIR:-mcp-json-templates}"

# New variable name (after migration)
PLUM_MCP_TEMPLATE_DIR="${PLUM_MCP_TEMPLATE_DIR:-mcp-json-templates}"
```

## No Actual MCP Templates Found

### Current State
- **No MCP template directory exists** in the current project
- **No `.mcp.json` files found** in the codebase
- **System is configured for MCP templates** but none are currently defined
- **Template functionality is implemented** but not actively used

### Implications
- **Lower migration risk** - No existing templates to break
- **Configuration updates needed** - Environment variables and documentation
- **Future template creation** will use new plum system
- **Backward compatibility consideration** for users with existing templates

## Migration Impact Assessment

### HIGH Impact Changes
1. **Environment Variable**: `WORKTREE_MCP_TEMPLATE_DIR` → `PLUM_MCP_TEMPLATE_DIR`
2. **Documentation Examples**: All references to worktree-manager in MCP docs
3. **Legacy Script**: `create-worktree-with-branch.sh` hardcoded path

### MEDIUM Impact Changes
1. **Configuration Files**: Default directory references
2. **Help Text**: MCP-related help and configuration display
3. **User Guides**: Template setup and usage documentation

### LOW Impact Changes
1. **Internal Functions**: MCP template discovery logic (paths are relative)
2. **Template Format**: No changes to actual MCP JSON structure needed
3. **Claude Integration**: Templates work the same way with new tool

## Required Updates

### 1. Environment Variables
```bash
# OLD (in all configuration files)
WORKTREE_MCP_TEMPLATE_DIR="${WORKTREE_MCP_TEMPLATE_DIR:-mcp-json-templates}"

# NEW (after migration)
PLUM_MCP_TEMPLATE_DIR="${PLUM_MCP_TEMPLATE_DIR:-mcp-json-templates}"
```

### 2. Documentation Updates
- **README.md**: Update all MCP configuration examples
- **Help text**: Update environment variable references
- **Configuration guides**: Update variable names and paths

### 3. Code Updates
- **lib/config.sh**: Update variable name
- **lib/mcp.sh**: Update variable reference (already uses config variable)
- **create-worktree-with-branch.sh**: Update hardcoded path
- **worktree-config**: Update default configuration

### 4. User Communication
- **Breaking change notice**: Environment variable name change
- **Migration guide**: How to update existing configurations
- **Backward compatibility**: Consider transition period support

## User Impact

### Existing Users with Custom Templates
- **Configuration update required**: Environment variable name change
- **Template files unaffected**: No changes to actual MCP JSON files
- **Directory location can remain same**: `mcp-json-templates` still default
- **Functionality unchanged**: Template activation works identically

### New Users
- **Clean start**: No legacy references to cause confusion
- **Updated documentation**: All examples use new plum variable names
- **Consistent naming**: PLUM_* environment variables throughout

## Template Directory Strategy

### Option 1: Keep Same Directory Name
- **Pros**: Minimal user impact, existing templates continue working
- **Cons**: Name doesn't match new tool name
- **Recommendation**: ✅ **RECOMMENDED** for minimal disruption

### Option 2: Change Directory Name to match Tool
- **Pros**: Consistent naming with plum tool
- **Cons**: Breaking change for existing users with templates
- **Recommendation**: ❌ Not recommended due to unnecessary breaking change

### Final Decision: Keep `mcp-json-templates` as default directory name

## Migration Checklist

### Configuration Updates
- [ ] Update `WORKTREE_MCP_TEMPLATE_DIR` → `PLUM_MCP_TEMPLATE_DIR` in lib/config.sh
- [ ] Update variable reference in worktree-config
- [ ] Update documentation examples
- [ ] Update help text and usage information

### Code Updates
- [ ] Update hardcoded path in create-worktree-with-branch.sh
- [ ] Verify lib/mcp.sh uses config variable (no hardcoded references)
- [ ] Test MCP template discovery with new variable name
- [ ] Validate template activation functionality

### Documentation Updates
- [ ] Update README.md MCP configuration section
- [ ] Update environment variable documentation
- [ ] Update configuration examples
- [ ] Update troubleshooting guides

### User Communication
- [ ] Document breaking change (environment variable)
- [ ] Provide migration instructions
- [ ] Update any external documentation or tutorials

## Testing Requirements

### Functional Testing
- [ ] Test MCP template discovery with new environment variable
- [ ] Test template activation in new plum tool
- [ ] Test fallback to default directory when variable not set
- [ ] Test with custom template directory paths

### Backward Compatibility Testing
- [ ] Test behavior when old WORKTREE_MCP_TEMPLATE_DIR is set
- [ ] Document any legacy support or warnings
- [ ] Plan deprecation timeline if supporting old variable temporarily

## Risk Assessment

### Risk Level: **MEDIUM**
- **Primary risk**: Environment variable name change affects existing users
- **Mitigation**: Clear documentation and migration guide
- **Impact scope**: Limited to users with custom MCP template configurations
- **Recovery**: Easy rollback to old environment variable names

### Success Criteria
- [x] No existing MCP templates to break during migration
- [ ] Environment variable updated throughout codebase
- [ ] Documentation reflects new variable names
- [ ] Template functionality works identically with plum tool
- [ ] User migration path clearly documented