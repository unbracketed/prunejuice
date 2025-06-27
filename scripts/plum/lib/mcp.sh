#!/bin/bash

# MCP template handling module for plum

# Get the templates directory path
get_templates_dir() {
    local main_worktree="${1:-$MAIN_WORKTREE}"
    echo "$main_worktree/$PLUM_MCP_TEMPLATE_DIR"
}

# List available MCP templates with descriptions
list_mcp_templates() {
    local templates_dir="$1"
    
    if [ ! -d "$templates_dir" ]; then
        echo "No MCP templates directory found at: $templates_dir" >&2
        return 1
    fi
    
    echo "Available MCP templates:"
    
    for template in "$templates_dir"/.mcp.*.json; do
        if [ -f "$template" ]; then
            local template_name
            template_name=$(basename "$template" | sed 's/^\.mcp\.//' | sed 's/\.json$//')
            echo -n "  - $template_name"
            
            # Extract description from README.md if available
            local readme="$templates_dir/README.md"
            if [ -f "$readme" ]; then
                local desc
                desc=$(grep -A1 "\.mcp\.$template_name\.json" "$readme" | tail -n1 | sed 's/^[[:space:]]*//')
                if [ -n "$desc" ] && [ "$desc" != "$(grep "\.mcp\.$template_name\.json" "$readme")" ]; then
                    echo ": $desc"
                else
                    echo ""
                fi
            else
                echo ""
            fi
        fi
    done
}

# Select MCP template interactively
select_mcp_template() {
    local templates_dir="$1"
    local templates=()
    local descriptions=()
    
    if [ ! -d "$templates_dir" ]; then
        echo "No MCP templates directory found at: $templates_dir" >&2
        return 1
    fi
    
    # Collect available templates
    for template in "$templates_dir"/.mcp.*.json; do
        if [ -f "$template" ]; then
            local template_name
            template_name=$(basename "$template" | sed 's/^\.mcp\.//' | sed 's/\.json$//')
            templates+=("$template_name")
            
            # Get description from README if available
            local readme="$templates_dir/README.md"
            local desc=""
            if [ -f "$readme" ]; then
                desc=$(grep -A1 "\.mcp\.$template_name\.json" "$readme" | tail -n1 | sed 's/^[[:space:]]*//')
                if [ -z "$desc" ] || [ "$desc" = "$(grep "\.mcp\.$template_name\.json" "$readme")" ]; then
                    desc="No description available"
                fi
            else
                desc="No description available"
            fi
            descriptions+=("$desc")
        fi
    done
    
    if [ ${#templates[@]} -eq 0 ]; then
        echo "No MCP templates found in $templates_dir" >&2
        return 1
    fi
    
    # Display templates for selection
    echo "Available MCP templates:" >&2
    echo "" >&2
    for i in "${!templates[@]}"; do
        echo "  $((i+1)). ${templates[$i]}" >&2
        echo "     ${descriptions[$i]}" >&2
        echo "" >&2
    done
    
    read -p "Select template (1-${#templates[@]}): " selection
    
    if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le ${#templates[@]} ]; then
        echo "${templates[$((selection-1))]}"
    else
        echo "Invalid selection" >&2
        return 1
    fi
}

# Activate MCP template in worktree
activate_mcp_template() {
    local template_name="$1"
    local worktree_path="$2"
    local main_worktree="${3:-$MAIN_WORKTREE}"
    local templates_dir
    
    templates_dir=$(get_templates_dir "$main_worktree")
    local template_file="$templates_dir/.mcp.$template_name.json"
    
    if [ ! -f "$template_file" ]; then
        echo "Error: MCP template '$template_name' not found at $template_file" >&2
        return 1
    fi
    
    echo "Activating MCP template: $template_name"
    if cp "$template_file" "$worktree_path/.mcp.json"; then
        echo "  ✓ Copied .mcp.$template_name.json to .mcp.json"
        return 0
    else
        echo "  ✗ Failed to activate MCP template" >&2
        return 1
    fi
}

# Check if MCP template exists
template_exists() {
    local template_name="$1"
    local main_worktree="${2:-$MAIN_WORKTREE}"
    local templates_dir
    
    templates_dir=$(get_templates_dir "$main_worktree")
    local template_file="$templates_dir/.mcp.$template_name.json"
    
    [ -f "$template_file" ]
}