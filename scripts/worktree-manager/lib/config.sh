#!/bin/bash

# Configuration loading module for worktree manager

# Load configuration from file and environment variables
load_config() {
    local config_file="${WORKTREE_CONFIG_FILE:-}"
    
    # Try to find config file in various locations
    if [ -z "$config_file" ]; then
        local possible_configs=(
            "$HOME/.worktree-config"
            "$HOME/.config/worktree-manager/config"
            "$(dirname "${BASH_SOURCE[0]}")/../worktree-config"
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
    WORKTREE_GITHUB_USERNAME="${WORKTREE_GITHUB_USERNAME:-${GITHUB_USERNAME:-tadasant}}"
    WORKTREE_DEFAULT_BRANCH="${WORKTREE_DEFAULT_BRANCH:-main}"
    WORKTREE_PARENT_DIR="${WORKTREE_PARENT_DIR:-../}"
    WORKTREE_EDITOR="${WORKTREE_EDITOR:-${VISUAL:-${EDITOR:-code-insiders}}}"
    WORKTREE_EDITOR_ARGS="${WORKTREE_EDITOR_ARGS:---new-window}"
    WORKTREE_MCP_TEMPLATE_DIR="${WORKTREE_MCP_TEMPLATE_DIR:-mcp-json-templates}"
    WORKTREE_MCP_AUTO_ACTIVATE="${WORKTREE_MCP_AUTO_ACTIVATE:-false}"
    
    # Set default files to copy if not already set
    if [ ${#WORKTREE_FILES_TO_COPY[@]} -eq 0 ]; then
        WORKTREE_FILES_TO_COPY=(
            ".vscode/tasks.json"
            "mcp-json-templates/.secrets"
        )
    fi
    
    # Configure editor arguments based on editor type
    if [ -z "$WORKTREE_EDITOR_ARGS" ]; then
        case "$WORKTREE_EDITOR" in
            code*) WORKTREE_EDITOR_ARGS="--new-window" ;;
            vim|nvim) WORKTREE_EDITOR_ARGS="" ;;
            subl) WORKTREE_EDITOR_ARGS="-n" ;;
            *) WORKTREE_EDITOR_ARGS="" ;;
        esac
    fi
}

# Display current configuration
show_config() {
    echo "Current Worktree Manager Configuration:"
    echo "  GitHub Username: $WORKTREE_GITHUB_USERNAME"
    echo "  Default Branch: $WORKTREE_DEFAULT_BRANCH"
    echo "  Parent Directory: $WORKTREE_PARENT_DIR"
    echo "  Editor: $WORKTREE_EDITOR $WORKTREE_EDITOR_ARGS"
    echo "  MCP Template Dir: $WORKTREE_MCP_TEMPLATE_DIR"
    echo "  Files to Copy:"
    for file in "${WORKTREE_FILES_TO_COPY[@]}"; do
        echo "    - $file"
    done
}