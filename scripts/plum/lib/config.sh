#!/bin/bash

# Configuration loading module for plum

# Load configuration from file and environment variables
load_config() {
    local config_file="${PLUM_CONFIG_FILE:-}"
    
    # Try to find config file in various locations
    if [ -z "$config_file" ]; then
        local possible_configs=(
            "$HOME/.worktree-config"
            "$HOME/.config/plum/config"
            "$(dirname "${BASH_SOURCE[0]}")/../plum-config"
        )
        
        for config in "${possible_configs[@]}"; do
            if [ -f "$config" ]; then
                config_file="$config"
                break
            fi
        done
    fi
    
    # Source the config file if found
    if [ -n "$config_file" ] && [ -f "$config_file" ]; then
        source "$config_file"
    else
        echo "Warning: No configuration file found. Using environment variables and defaults." >&2
    fi
    
    # Set defaults for any missing configuration
    PLUM_GITHUB_USERNAME="${PLUM_GITHUB_USERNAME:-${GITHUB_USERNAME:-unbracketed}}"
    PLUM_DEFAULT_BRANCH="${PLUM_DEFAULT_BRANCH:-main}"
    PLUM_PARENT_DIR="${PLUM_PARENT_DIR:-../}"
    PLUM_EDITOR="${PLUM_EDITOR:-${VISUAL:-${EDITOR:-code}}}"
    PLUM_EDITOR_ARGS="${PLUM_EDITOR_ARGS:---new-window}"
    PLUM_MCP_TEMPLATE_DIR="${PLUM_MCP_TEMPLATE_DIR:-mcp-json-templates}"
    PLUM_MCP_AUTO_ACTIVATE="${PLUM_MCP_AUTO_ACTIVATE:-false}"
    
    # Set default files to copy if not already set
    if [ ${#PLUM_FILES_TO_COPY[@]} -eq 0 ]; then
        PLUM_FILES_TO_COPY=(
            ".vscode/tasks.json"
            "mcp-json-templates/.secrets"
        )
    fi
    
    # Configure editor arguments based on editor type
    if [ -z "$PLUM_EDITOR_ARGS" ]; then
        case "$PLUM_EDITOR" in
            code*) PLUM_EDITOR_ARGS="--new-window" ;;
            vim|nvim) PLUM_EDITOR_ARGS="" ;;
            subl) PLUM_EDITOR_ARGS="-n" ;;
            *) PLUM_EDITOR_ARGS="" ;;
        esac
    fi
}

# Display current configuration
show_config() {
    echo "Current Plum Configuration:"
    echo "  GitHub Username: $PLUM_GITHUB_USERNAME"
    echo "  Default Branch: $PLUM_DEFAULT_BRANCH"
    echo "  Parent Directory: $PLUM_PARENT_DIR"
    echo "  Editor: $PLUM_EDITOR $PLUM_EDITOR_ARGS"
    echo "  MCP Template Dir: $PLUM_MCP_TEMPLATE_DIR"
    echo "  Files to Copy:"
    for file in "${PLUM_FILES_TO_COPY[@]}"; do
        echo "    - $file"
    done
}