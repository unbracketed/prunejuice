#!/bin/bash
# PruneJuice SDLC Orchestrator - Main Entry Point

set -euo pipefail

# Script directory and library loading
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/prunejuice/lib"

# Source required libraries
source "$LIB_DIR/database.sh"
source "$LIB_DIR/yaml-parser.sh"
source "$LIB_DIR/executor.sh"
source "$LIB_DIR/artifacts.sh"
source "$LIB_DIR/prompt-assembly.sh"

# Configuration
PRUNEJUICE_VERSION="0.1.0-alpha"
PROJECT_PATH="${PWD}"
COMMANDS_DIR="$PROJECT_PATH/.prj/commands"
GLOBAL_COMMANDS_DIR="$SCRIPT_DIR/prunejuice/commands"

# Color output (if terminal supports it)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    NC='\033[0m' # No Color
else
    RED='' GREEN='' YELLOW='' BLUE='' CYAN='' NC=''
fi

# Utility functions
print_header() {
    echo -e "${CYAN}🧃 PruneJuice SDLC Orchestrator v$PRUNEJUICE_VERSION${NC}"
    echo -e "${BLUE}   Parallel Agentic Coding Workflow Manager${NC}"
    echo
}

print_usage() {
    cat << EOF
Usage: $(basename "$0") <command> [options] [arguments]

Commands:
  list                     List available SDLC commands
  run <command> [args...]  Execute an SDLC command
  help <command>           Show help for a specific command
  init                     Initialize project for PruneJuice
  status                   Show current project status
  history                  Show recent command execution history
  cleanup                  Clean up old artifacts and logs
  db                       Database management commands

Global Options:
  -v, --verbose           Enable verbose output
  -h, --help             Show this help message
  --version              Show version information

Examples:
  $(basename "$0") list
  $(basename "$0") run analyze-issue issue_number=123
  $(basename "$0") help code-review
  $(basename "$0") status
  $(basename "$0") history --limit 10

For more information about specific commands, use:
  $(basename "$0") help <command>
EOF
}

# Command implementations

cmd_list() {
    echo -e "${GREEN}Available SDLC Commands:${NC}"
    echo
    
    # List project-specific commands
    if [[ -d "$COMMANDS_DIR" ]]; then
        echo -e "${YELLOW}Project Commands (in .prj/commands/):${NC}"
        list_commands "$COMMANDS_DIR"
        echo
    fi
    
    # List global commands
    if [[ -d "$GLOBAL_COMMANDS_DIR" ]]; then
        echo -e "${YELLOW}Global Commands:${NC}"
        list_commands "$GLOBAL_COMMANDS_DIR"
    fi
    
    if [[ ! -d "$COMMANDS_DIR" && ! -d "$GLOBAL_COMMANDS_DIR" ]]; then
        echo -e "${RED}No commands found. Run '$(basename "$0") init' to initialize the project.${NC}"
        return 1
    fi
}

cmd_run() {
    local command_name="${1:-}"
    if [[ $# -gt 0 ]]; then
        shift
    fi
    local args=("$@")
    
    if [[ -z "$command_name" ]]; then
        echo -e "${RED}Error: Command name required${NC}" >&2
        echo "Usage: $(basename "$0") run <command> [args...]" >&2
        return 1
    fi
    
    echo -e "${GREEN}Executing command: $command_name${NC}"
    echo -e "${BLUE}Arguments: ${args[*]:-none}${NC}"
    echo
    
    # Initialize database
    init_database
    
    # Execute command
    if main_execute "$command_name" "$PROJECT_PATH" "${args[@]}"; then
        echo -e "${GREEN}✓ Command completed successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ Command execution failed${NC}"
        return 1
    fi
}

cmd_help() {
    local command_name="${1:-}"
    
    if [[ -z "$command_name" ]]; then
        print_usage
        return 0
    fi
    
    # Find command file
    local command_file=""
    if [[ -f "$COMMANDS_DIR/$command_name.yaml" ]]; then
        command_file="$COMMANDS_DIR/$command_name.yaml"
    elif [[ -f "$GLOBAL_COMMANDS_DIR/$command_name.yaml" ]]; then
        command_file="$GLOBAL_COMMANDS_DIR/$command_name.yaml"
    else
        echo -e "${RED}Command not found: $command_name${NC}" >&2
        return 1
    fi
    
    echo -e "${GREEN}Help for command: $command_name${NC}"
    echo
    show_command_help "$command_file"
}

cmd_init() {
    echo -e "${GREEN}Initializing PruneJuice project...${NC}"
    
    # Create project structure
    mkdir -p .prj/{commands,steps,configs}
    
    # Initialize database
    init_database
    
    # Create default project configuration
    cat > .prj/config.yaml << EOF
project:
  name: $(basename "$PROJECT_PATH")
  description: "PruneJuice managed project"
  type: "$(detect_project_type "$PROJECT_PATH")"

settings:
  default_timeout: 3600
  artifact_retention_days: 30
  log_level: INFO

integrations:
  plum:
    enabled: true
    auto_create_worktree: true
  pots:
    enabled: false
    auto_start_session: false
  claude_code:
    enabled: true
    auto_prompt: true
EOF
    
    # Copy example commands
    if [[ -d "$SCRIPT_DIR/prunejuice/templates" ]]; then
        cp "$SCRIPT_DIR/prunejuice/templates"/*.yaml .prj/commands/
        echo -e "${BLUE}Copied example commands to .prj/commands/${NC}"
    fi
    
    # Create .gitignore entries
    if [[ -f .gitignore ]]; then
        if ! grep -q ".prunejuice" .gitignore; then
            echo "" >> .gitignore
            echo "# PruneJuice artifacts" >> .gitignore
            echo ".prunejuice/" >> .gitignore
        fi
    fi
    
    echo -e "${GREEN}✓ Project initialized successfully${NC}"
    echo
    echo "Next steps:"
    echo "  1. Review and customize commands in .prj/commands/"
    echo "  2. Run: $(basename "$0") list"
    echo "  3. Try: $(basename "$0") run <command>"
}

cmd_status() {
    echo -e "${GREEN}PruneJuice Project Status${NC}"
    echo
    
    # Project info
    echo -e "${YELLOW}Project Information:${NC}"
    echo "  Path: $PROJECT_PATH"
    echo "  Type: $(detect_project_type "$PROJECT_PATH")"
    echo
    
    # Database info
    if [[ -f "$DB_FILE" ]]; then
        echo -e "${YELLOW}Database Status:${NC}"
        get_db_stats | while IFS='|' read -r total_events active_events active_sessions command_defs artifacts; do
            echo "  Total Events: $total_events"
            echo "  Active Events: $active_events"
            echo "  Active Sessions: $active_sessions"
            echo "  Command Definitions: $command_defs"
            echo "  Total Artifacts: $artifacts"
        done
        echo
    fi
    
    # Available commands
    local cmd_count=0
    if [[ -d "$COMMANDS_DIR" ]]; then
        cmd_count=$(find "$COMMANDS_DIR" -name "*.yaml" | wc -l)
    fi
    local global_cmd_count=0
    if [[ -d "$GLOBAL_COMMANDS_DIR" ]]; then
        global_cmd_count=$(find "$GLOBAL_COMMANDS_DIR" -name "*.yaml" | wc -l)
    fi
    
    echo -e "${YELLOW}Available Commands:${NC}"
    echo "  Project Commands: $cmd_count"
    echo "  Global Commands: $global_cmd_count"
    echo
    
    # Recent activity
    if [[ -f "$DB_FILE" ]]; then
        echo -e "${YELLOW}Recent Activity:${NC}"
        get_recent_events 5 | while IFS='|' read -r id command project status start_time end_time; do
            echo "  [$id] $command - $status ($start_time)"
        done
    fi
}

cmd_history() {
    local limit=10
    
    # Parse options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --limit)
                limit="$2"
                shift 2
                ;;
            *)
                break
                ;;
        esac
    done
    
    echo -e "${GREEN}Command Execution History${NC}"
    echo
    
    if [[ ! -f "$DB_FILE" ]]; then
        echo -e "${YELLOW}No history available. Database not initialized.${NC}"
        return 0
    fi
    
    get_recent_events "$limit" | while IFS='|' read -r id command project status start_time end_time; do
        local duration=""
        if [[ -n "$end_time" && "$end_time" != "null" ]]; then
            duration=" (completed)"
        else
            duration=" (running)"
        fi
        
        echo "[$id] $command - $status$duration"
        echo "      Project: $(basename "$project")"
        echo "      Started: $start_time"
        echo
    done
}

cmd_cleanup() {
    echo -e "${GREEN}Cleaning up PruneJuice artifacts...${NC}"
    
    # Clean up old database records
    cleanup_old_records 30
    echo -e "${BLUE}✓ Cleaned up old database records${NC}"
    
    # Clean up old artifacts
    cleanup_artifacts 30
    echo -e "${BLUE}✓ Cleaned up old artifacts${NC}"
    
    # Clean up old prompts
    cleanup_prompts 30
    echo -e "${BLUE}✓ Cleaned up old prompts${NC}"
    
    # Vacuum database
    vacuum_database
    echo -e "${BLUE}✓ Optimized database${NC}"
    
    echo -e "${GREEN}✓ Cleanup completed${NC}"
}

cmd_db() {
    local subcommand="${1:-}"
    if [[ $# -gt 0 ]]; then
        shift
    fi
    
    case "$subcommand" in
        "init")
            init_database
            echo -e "${GREEN}✓ Database initialized${NC}"
            ;;
        "stats")
            get_db_stats | while IFS='|' read -r total_events active_events active_sessions command_defs artifacts; do
                echo "Database Statistics:"
                echo "  Total Events: $total_events"
                echo "  Active Events: $active_events"
                echo "  Active Sessions: $active_sessions"
                echo "  Command Definitions: $command_defs"
                echo "  Total Artifacts: $artifacts"
            done
            ;;
        "vacuum")
            vacuum_database
            echo -e "${GREEN}✓ Database optimized${NC}"
            ;;
        "backup")
            local backup_file="${1:-prunejuice-backup-$(date +%Y%m%d-%H%M%S).db}"
            cp "$DB_FILE" "$backup_file"
            echo -e "${GREEN}✓ Database backed up to: $backup_file${NC}"
            ;;
        *)
            echo "Database commands: init, stats, vacuum, backup"
            ;;
    esac
}

# Main command dispatcher
main() {
    local verbose=false
    
    # Parse global options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -v|--verbose)
                verbose=true
                export PRUNEJUICE_LOG_LEVEL="DEBUG"
                shift
                ;;
            -h|--help)
                print_header
                print_usage
                exit 0
                ;;
            --version)
                echo "PruneJuice $PRUNEJUICE_VERSION"
                exit 0
                ;;
            -*)
                echo -e "${RED}Unknown option: $1${NC}" >&2
                exit 1
                ;;
            *)
                break
                ;;
        esac
    done
    
    if [[ $# -eq 0 ]]; then
        print_header
        print_usage
        exit 0
    fi
    
    local command="${1:-}"
    if [[ $# -gt 0 ]]; then
        shift
    fi
    
    # Show header for all commands except help
    if [[ "$command" != "help" ]]; then
        print_header
    fi
    
    case "$command" in
        "list")
            cmd_list "$@"
            ;;
        "run")
            cmd_run "$@"
            ;;
        "help")
            cmd_help "$@"
            ;;
        "init")
            cmd_init "$@"
            ;;
        "status")
            cmd_status "$@"
            ;;
        "history")
            cmd_history "$@"
            ;;
        "cleanup")
            cmd_cleanup "$@"
            ;;
        "db")
            cmd_db "$@"
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}" >&2
            echo "Run '$(basename "$0") help' for usage information." >&2
            exit 1
            ;;
    esac
}

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    # Required tools
    local required_tools=("sqlite3" "yq")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_deps+=("$tool")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        echo -e "${RED}Missing required dependencies: ${missing_deps[*]}${NC}" >&2
        echo "Please install the missing tools and try again." >&2
        exit 1
    fi
}

# Initialize and run
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Don't check dependencies for help and version
    if [[ "${1:-}" == "--help" || "${1:-}" == "-h" || "${1:-}" == "--version" ]]; then
        main "$@"
    else
        check_dependencies
        main "$@"
    fi
fi