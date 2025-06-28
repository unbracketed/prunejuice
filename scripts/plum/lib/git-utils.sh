#!/bin/bash

# Git utilities module for worktree manager

# Get the git repository root (works in both main repo and worktrees)
get_git_root() {
    git rev-parse --show-toplevel 2>/dev/null
}

# Find the main worktree (the actual git directory)
get_main_worktree() {
    local current_root="$1"
    local git_common_dir
    
    git_common_dir="$(git rev-parse --git-common-dir 2>/dev/null)"
    
    if [ "$git_common_dir" = ".git" ] || [ "$git_common_dir" = "$(pwd)/.git" ]; then
        # We're in the main repository
        echo "$current_root"
    else
        # We're in a worktree, find the main worktree
        dirname "$git_common_dir"
    fi
}

# Check if we're in a git repository
validate_git_repo() {
    if ! get_git_root >/dev/null 2>&1; then
        echo "Error: Not in a git repository" >&2
        return 1
    fi
}

# Stash uncommitted changes if any
stash_changes() {
    local branch_name="$1"
    
    echo "Checking for uncommitted changes..."
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "Stashing uncommitted changes..."
        git stash push -m "Auto-stash before creating worktree $branch_name"
        return 0  # Stashed
    else
        return 1  # Nothing to stash
    fi
}

# Switch to specified branch and pull latest
prepare_base_branch() {
    local target_branch="$1"
    local current_branch
    
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "$target_branch" ]; then
        echo "Switching to $target_branch branch..."
        git checkout "$target_branch" || return 1
    fi
    
    # Only pull if origin remote exists
    if git remote get-url origin >/dev/null 2>&1; then
        echo "Pulling latest $target_branch branch..."
        git pull origin "$target_branch"
    else
        echo "No origin remote found, skipping pull"
    fi
}

# Create the git worktree
create_worktree() {
    local worktree_path="$1"
    local branch_name="$2"
    local base_branch="${3:-$PLUM_DEFAULT_BRANCH}"
    
    echo "Creating worktree: $(basename "$worktree_path")"
    echo "With branch: $branch_name"
    echo "From base: $base_branch"
    
    git worktree add "$worktree_path" -b "$branch_name" "$base_branch"
}

# Get project name from the main worktree directory
get_project_name() {
    local main_worktree="$1"
    if [ -n "$main_worktree" ]; then
        basename "$main_worktree"
    else
        basename "$(get_main_worktree "$(get_git_root)")"
    fi
}

# Generate branch name with prefix
generate_branch_name() {
    local suffix="$1"
    local prefix="${2:-}"
    
    # Use prefix if provided, otherwise use project name
    if [ -z "$prefix" ]; then
        prefix=$(get_project_name)
    fi
    
    echo "$prefix-$suffix"
}

# Generate worktree directory name (replace / with -)
generate_worktree_dir() {
    local branch_name="$1"
    echo "$branch_name" | tr '/' '-'
}

# Apply stashed changes back to the original location
restore_stash() {
    local original_root="$1"
    
    echo "Returning to original location and applying stashed changes..."
    cd "$original_root" || return 1
    git stash pop
}