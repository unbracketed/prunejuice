#!/bin/bash

# User interface functions for plum

# Display help message
show_help() {
    local script_name="${1:-plum}"
    
    cat << 'EOF'
Usage: plum [OPTIONS] [branch-suffix]

Creates a new git worktree with a branch and opens it in your configured editor.

OPTIONS:
  -h, --help              Show this help message
  -m, --mcp               Select and activate an MCP configuration template
  --mcp TEMPLATE          Activate a specific MCP template (e.g., --mcp dwh)
  --pattern PATTERN       Branch naming pattern (default: {username}/{suffix})
  --from BRANCH           Create from branch other than default
  --no-copy-files         Skip copying files to new worktree
  --dry-run               Show what would be done without doing it
  --config                Show current configuration
  -i, --interactive       Interactive mode with all options

ARGUMENTS:
  branch-suffix          Optional branch name suffix (default: patch-{timestamp})

ENVIRONMENT VARIABLES:
  WORKTREE_NAME_PREFIX    Prefix for worktree names (default: auto-detect from project)
  PLUM_EDITOR            Editor command to use
  PLUM_DEFAULT_BRANCH    Default base branch
  PLUM_CONFIG_FILE       Custom configuration file path

EXAMPLES:
  plum                    # Create worktree with auto-generated branch name
  plum fix-bug            # Create worktree with branch {project-name}-fix-bug
  plum --mcp dwh fix-bug  # Create worktree and activate dwh MCP template
  plum -m                 # Interactive MCP template selection
  plum --pattern "feature/{suffix}" new-feature  # Custom branch pattern
  plum --from develop hotfix      # Create from develop branch
  plum --dry-run experimental     # Preview actions without executing

EOF
}

# Show current configuration
show_config_ui() {
    echo "Current Plum Configuration:"
    echo "  Worktree Name Prefix: ${WORKTREE_NAME_PREFIX:-auto-detect}"
    echo "  Default Branch: $PLUM_DEFAULT_BRANCH"
    echo "  Parent Directory: $PLUM_PARENT_DIR"
    echo "  Editor: $PLUM_EDITOR $PLUM_EDITOR_ARGS"
    echo "  MCP Template Dir: $PLUM_MCP_TEMPLATE_DIR"
    echo "  Files to Copy:"
    for file in "${PLUM_FILES_TO_COPY[@]}"; do
        echo "    - $file"
    done
}

# Interactive mode prompts
interactive_mode() {
    local branch_suffix=""
    local mcp_template=""
    local branch_pattern="{username}/{suffix}"
    local base_branch="$PLUM_DEFAULT_BRANCH"
    local copy_files=true
    
    echo "=== Interactive Plum Worktree Creation ==="
    echo
    
    # Branch suffix
    read -p "Branch suffix (default: patch-$(date +%s)): " branch_suffix
    if [ -z "$branch_suffix" ]; then
        branch_suffix="patch-$(date +%s)"
    fi
    
    # Branch pattern
    read -p "Branch pattern (default: {username}/{suffix}): " input_pattern
    if [ -n "$input_pattern" ]; then
        branch_pattern="$input_pattern"
    fi
    
    # Base branch
    read -p "Base branch (default: $PLUM_DEFAULT_BRANCH): " input_branch
    if [ -n "$input_branch" ]; then
        base_branch="$input_branch"
    fi
    
    # File copying
    read -p "Copy files to new worktree? [Y/n]: " copy_input
    if [[ "$copy_input" =~ ^[Nn]$ ]]; then
        copy_files=false
    fi
    
    # MCP template
    read -p "Use MCP template? [y/N]: " mcp_input
    if [[ "$mcp_input" =~ ^[Yy]$ ]]; then
        local templates_dir
        templates_dir=$(get_templates_dir "$MAIN_WORKTREE")
        mcp_template=$(select_mcp_template "$templates_dir")
        if [ $? -ne 0 ] || [ -z "$mcp_template" ]; then
            echo "MCP template selection cancelled"
            mcp_template=""
        fi
    fi
    
    # Summary
    echo
    echo "=== Summary ==="
    echo "Branch: $(generate_branch_name "$branch_suffix" "$WORKTREE_NAME_PREFIX")"
    echo "Base: $base_branch"
    echo "Copy files: $copy_files"
    echo "MCP template: ${mcp_template:-none}"
    echo
    
    read -p "Proceed with creation? [Y/n]: " confirm
    if [[ "$confirm" =~ ^[Nn]$ ]]; then
        echo "Cancelled"
        return 1
    fi
    
    # Export values for main script
    export INTERACTIVE_BRANCH_SUFFIX="$branch_suffix"
    export INTERACTIVE_BRANCH_PATTERN="$branch_pattern"
    export INTERACTIVE_BASE_BRANCH="$base_branch"
    export INTERACTIVE_COPY_FILES="$copy_files"
    export INTERACTIVE_MCP_TEMPLATE="$mcp_template"
    
    return 0
}

# Display dry run information
show_dry_run() {
    local branch_name="$1"
    local worktree_path="$2"
    local base_branch="$3"
    local copy_files="$4"
    local mcp_template="$5"
    
    echo "=== DRY RUN: What would be done ==="
    echo "1. Check for uncommitted changes and stash if needed"
    echo "2. Switch to base branch: $base_branch"
    echo "3. Pull latest changes from origin/$base_branch"
    echo "4. Create worktree: $worktree_path"
    echo "5. Create branch: $branch_name"
    
    if [ "$copy_files" = true ]; then
        echo "6. Copy files:"
        for file in "${PLUM_FILES_TO_COPY[@]}"; do
            echo "   - $file"
        done
    else
        echo "6. Skip file copying"
    fi
    
    if [ -n "$mcp_template" ]; then
        echo "7. Activate MCP template: $mcp_template"
    else
        echo "7. No MCP template activation"
    fi
    
    echo "8. Open in editor: $PLUM_EDITOR $PLUM_EDITOR_ARGS"
    echo "9. Restore stashed changes if any"
    echo "=========================="
}

# Display success message
show_success() {
    local worktree_path="$1"
    local branch_name="$2"
    
    echo "✅ Worktree created successfully!"
    echo "   Path: $worktree_path"
    echo "   Branch: $branch_name"
}

# Display error message
show_error() {
    local message="$1"
    echo "❌ Error: $message" >&2
}