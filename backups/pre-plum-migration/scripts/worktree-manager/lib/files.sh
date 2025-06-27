#!/bin/bash

# File operations module for worktree manager

# Copy files from source worktree to new worktree
copy_files() {
    local source_root="$1"
    local target_root="$2"
    local files_to_copy=("${@:3}")
    
    echo "Copying project, claude, and VS Code settings..."
    
    # Use default files if none provided
    if [ ${#files_to_copy[@]} -eq 0 ]; then
        files_to_copy=("${WORKTREE_FILES_TO_COPY[@]}")
    fi
    
    local copied_count=0
    local failed_count=0
    
    # Copy each file if it exists
    for file in "${files_to_copy[@]}"; do
        local source_file="$source_root/$file"
        if [ -f "$source_file" ]; then
            local target_file="$target_root/$file"
            local target_dir
            target_dir=$(dirname "$target_file")
            
            # Create target directory if it doesn't exist
            mkdir -p "$target_dir"
            
            # Copy the file
            if cp "$source_file" "$target_file" 2>/dev/null; then
                echo "  ✓ Copied $file"
                ((copied_count++))
            else
                echo "  ✗ Failed to copy $file"
                ((failed_count++))
            fi
        else
            echo "  ⚠ $file not found in source directory"
        fi
    done
    
    echo "  Files copied: $copied_count, failed: $failed_count"
    return $failed_count
}

# Copy files matching glob patterns
copy_files_with_patterns() {
    local source_root="$1"
    local target_root="$2"
    local patterns=("${@:3}")
    
    echo "Copying files matching patterns..."
    
    local copied_count=0
    local failed_count=0
    
    for pattern in "${patterns[@]}"; do
        # Use bash globbing to expand pattern
        local files=("$source_root"/$pattern)
        
        for file in "${files[@]}"; do
            # Skip if glob didn't match anything
            if [ ! -e "$file" ]; then
                continue
            fi
            
            # Get relative path
            local rel_path="${file#$source_root/}"
            local target_file="$target_root/$rel_path"
            local target_dir
            target_dir=$(dirname "$target_file")
            
            # Create target directory if it doesn't exist
            mkdir -p "$target_dir"
            
            # Copy the file
            if cp "$file" "$target_file" 2>/dev/null; then
                echo "  ✓ Copied $rel_path"
                ((copied_count++))
            else
                echo "  ✗ Failed to copy $rel_path"
                ((failed_count++))
            fi
        done
    done
    
    echo "  Files copied: $copied_count, failed: $failed_count"
    return $failed_count
}

# Check if file copying should be skipped
should_skip_file_copy() {
    [ "$WORKTREE_SKIP_FILE_COPY" = "true" ]
}