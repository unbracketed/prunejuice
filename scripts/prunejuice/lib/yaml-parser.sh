#!/bin/bash
# YAML command parser and validation for PruneJuice

# Check if yq is available (required for YAML parsing)
check_yaml_dependencies() {
    if ! command -v yq &> /dev/null; then
        echo "Error: yq is required for YAML parsing. Please install it:" >&2
        echo "  brew install yq    # macOS" >&2
        echo "  apt install yq     # Ubuntu/Debian" >&2
        return 1
    fi
    return 0
}

# Validate YAML command structure
validate_command_yaml() {
    local yaml_file="$1"
    
    if [[ ! -f "$yaml_file" ]]; then
        echo "Error: YAML file not found: $yaml_file" >&2
        return 1
    fi
    
    if ! check_yaml_dependencies; then
        return 1
    fi
    
    # Check if it's valid YAML
    if ! yq eval '.' "$yaml_file" >/dev/null 2>&1; then
        echo "Error: Invalid YAML syntax in $yaml_file" >&2
        return 1
    fi
    
    # Required fields validation
    local required_fields=("name" "description" "steps")
    for field in "${required_fields[@]}"; do
        if ! yq eval "has(\"$field\")" "$yaml_file" | grep -q "true"; then
            echo "Error: Missing required field '$field' in $yaml_file" >&2
            return 1
        fi
    done
    
    # Validate steps is an array
    if ! yq eval '.steps | type' "$yaml_file" | grep -q "!!seq"; then
        echo "Error: 'steps' must be an array in $yaml_file" >&2
        return 1
    fi
    
    return 0
}

# Parse YAML command file and extract metadata
parse_command_yaml() {
    local yaml_file="$1"
    
    if ! validate_command_yaml "$yaml_file"; then
        return 1
    fi
    
    # Extract basic metadata
    local name description
    name=$(yq eval '.name' "$yaml_file")
    description=$(yq eval '.description' "$yaml_file")
    
    echo "NAME=$name"
    echo "DESCRIPTION=$description"
    
    # Extract arguments if present
    if yq eval 'has("arguments")' "$yaml_file" | grep -q "true"; then
        echo "ARGUMENTS=$(yq eval '.arguments | @json' "$yaml_file")"
    else
        echo "ARGUMENTS=[]"
    fi
    
    # Extract environment variables if present
    if yq eval 'has("environment")' "$yaml_file" | grep -q "true"; then
        echo "ENVIRONMENT=$(yq eval '.environment | @json' "$yaml_file")"
    else
        echo "ENVIRONMENT={}"
    fi
    
    # Extract steps
    echo "STEPS=$(yq eval '.steps | @json' "$yaml_file")"
    
    # Extract base command if present (for inheritance)
    if yq eval 'has("extends")' "$yaml_file" | grep -q "true"; then
        echo "EXTENDS=$(yq eval '.extends' "$yaml_file")"
    fi
    
    # Extract timeout if present
    if yq eval 'has("timeout")' "$yaml_file" | grep -q "true"; then
        echo "TIMEOUT=$(yq eval '.timeout' "$yaml_file")"
    else
        echo "TIMEOUT=3600"  # Default 1 hour
    fi
    
    # Extract working directory if present
    if yq eval 'has("working_directory")' "$yaml_file" | grep -q "true"; then
        echo "WORKING_DIRECTORY=$(yq eval '.working_directory' "$yaml_file")"
    fi
}

# Get command steps as array
get_command_steps() {
    local yaml_file="$1"
    
    if ! validate_command_yaml "$yaml_file"; then
        return 1
    fi
    
    yq eval '.steps[]' "$yaml_file"
}

# Get command arguments
get_command_arguments() {
    local yaml_file="$1"
    
    if ! validate_command_yaml "$yaml_file"; then
        return 1
    fi
    
    if yq eval 'has("arguments")' "$yaml_file" | grep -q "true"; then
        yq eval '.arguments[]' "$yaml_file"
    fi
}

# Check if command extends another command
get_base_command() {
    local yaml_file="$1"
    
    if yq eval 'has("extends")' "$yaml_file" | grep -q "true"; then
        yq eval '.extends' "$yaml_file"
    fi
}

# Resolve command inheritance
resolve_command_inheritance() {
    local yaml_file="$1"
    local commands_dir="$2"
    local temp_file
    temp_file=$(mktemp)
    
    # Copy original file
    cp "$yaml_file" "$temp_file"
    
    # Check if it extends another command
    local base_command
    base_command=$(get_base_command "$yaml_file")
    
    if [[ -n "$base_command" && "$base_command" != "null" ]]; then
        local base_file="$commands_dir/$base_command.yaml"
        
        if [[ ! -f "$base_file" ]]; then
            echo "Error: Base command file not found: $base_file" >&2
            rm -f "$temp_file"
            return 1
        fi
        
        # Recursively resolve base command inheritance
        local resolved_base
        resolved_base=$(resolve_command_inheritance "$base_file" "$commands_dir")
        if [[ $? -ne 0 ]]; then
            rm -f "$temp_file"
            return 1
        fi
        
        # Merge base command with current command
        # Current command takes precedence over base command
        yq eval-all 'select(fileIndex == 0) * select(fileIndex == 1)' "$resolved_base" "$yaml_file" > "$temp_file"
        
        # Clean up temporary base file if it was created
        if [[ "$resolved_base" != "$base_file" ]]; then
            rm -f "$resolved_base"
        fi
    fi
    
    echo "$temp_file"
}

# Validate command arguments against definition
validate_command_arguments() {
    local yaml_file="$1"
    shift
    local provided_args=("$@")
    
    if ! validate_command_yaml "$yaml_file"; then
        return 1
    fi
    
    # Get required arguments
    local required_args=()
    while IFS= read -r arg; do
        if [[ "$arg" != "null" ]]; then
            required_args+=("$arg")
        fi
    done < <(yq eval '.arguments[] | select(. | type == "!!str") // (.name // empty)' "$yaml_file")
    
    # Check if all required arguments are provided
    for req_arg in "${required_args[@]}"; do
        local found=false
        for provided_arg in "${provided_args[@]}"; do
            if [[ "$provided_arg" == "$req_arg="* ]]; then
                found=true
                break
            fi
        done
        
        if [[ "$found" == false ]]; then
            echo "Error: Missing required argument: $req_arg" >&2
            return 1
        fi
    done
    
    return 0
}

# Generate command help text from YAML
generate_command_help() {
    local yaml_file="$1"
    
    if ! validate_command_yaml "$yaml_file"; then
        return 1
    fi
    
    local name description
    name=$(yq eval '.name' "$yaml_file")
    description=$(yq eval '.description' "$yaml_file")
    
    echo "Command: $name"
    echo "Description: $description"
    echo
    
    # Show arguments if present
    if yq eval 'has("arguments")' "$yaml_file" | grep -q "true"; then
        echo "Arguments:"
        yq eval '.arguments[]' "$yaml_file" | while IFS= read -r arg; do
            if [[ "$arg" != "null" ]]; then
                echo "  - $arg"
            fi
        done
        echo
    fi
    
    # Show steps
    echo "Steps:"
    yq eval '.steps[]' "$yaml_file" | while IFS= read -r step; do
        echo "  - $step"
    done
}

# List all available commands in a directory
list_commands() {
    local commands_dir="$1"
    
    if [[ ! -d "$commands_dir" ]]; then
        echo "Error: Commands directory not found: $commands_dir" >&2
        return 1
    fi
    
    echo "Available commands:"
    for yaml_file in "$commands_dir"/*.yaml; do
        if [[ -f "$yaml_file" ]]; then
            local name description
            name=$(yq eval '.name' "$yaml_file" 2>/dev/null || echo "$(basename "$yaml_file" .yaml)")
            description=$(yq eval '.description' "$yaml_file" 2>/dev/null || echo "No description")
            
            printf "  %-20s %s\n" "$name" "$description"
        fi
    done
}