#!/bin/bash

# UATP Capsule Engine Uninstaller
# Comprehensive removal script with data preservation options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
UATP_DIR="$(pwd)"
USER_DATA_DIR="$HOME/.uatp"
CONFIG_DIR="$UATP_DIR/config"
STORAGE_DIR="$UATP_DIR/storage"
LOG_DIR="$UATP_DIR/logs"

# Default options
KEEP_USER_DATA=false
KEEP_CAPSULES=false
KEEP_CONFIG=false
FORCE_REMOVE=false
BACKUP_DATA=false
INTERACTIVE=true

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    cat << EOF
UATP Capsule Engine Uninstaller

Usage: $0 [OPTIONS]

OPTIONS:
    --keep-user-data    Keep user data and settings (~/.uatp/)
    --keep-capsules     Keep capsule data (capsule_chain.jsonl, etc.)
    --keep-config       Keep configuration files
    --backup-data       Create backup before removal
    --force             Skip confirmation prompts
    --non-interactive   Run without interactive prompts
    --help              Show this help message

EXAMPLES:
    $0                          # Interactive uninstall with prompts
    $0 --keep-capsules          # Remove everything except capsule data
    $0 --backup-data --force    # Backup data and force remove everything
    $0 --keep-user-data         # Keep user settings and preferences

WHAT GETS REMOVED:
    - UATP application files and directories
    - Running UATP processes
    - Database files (unless --keep-capsules)
    - Configuration files (unless --keep-config)
    - Log files and temporary data
    - Python virtual environment (if created by installer)
    - System integrations and environment variables

WHAT CAN BE PRESERVED:
    - User data and preferences (~/.uatp/)
    - Capsule chain data (capsule_chain.jsonl)
    - API keys and configuration
    - Custom settings and themes

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --keep-user-data)
                KEEP_USER_DATA=true
                shift
                ;;
            --keep-capsules)
                KEEP_CAPSULES=true
                shift
                ;;
            --keep-config)
                KEEP_CONFIG=true
                shift
                ;;
            --backup-data)
                BACKUP_DATA=true
                shift
                ;;
            --force)
                FORCE_REMOVE=true
                INTERACTIVE=false
                shift
                ;;
            --non-interactive)
                INTERACTIVE=false
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Function to check if running as root
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. This will remove system-wide installations."
        if [[ "$INTERACTIVE" == "true" ]]; then
            read -p "Continue? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_status "Uninstall cancelled."
                exit 0
            fi
        fi
    fi
}

# Function to detect UATP installation
detect_installation() {
    print_status "Detecting UATP installation..."

    local found_components=()

    # Check for main application files
    if [[ -f "$UATP_DIR/run.py" ]]; then
        found_components+=("Main application")
    fi

    if [[ -f "$UATP_DIR/capsule_chain.jsonl" ]]; then
        found_components+=("Capsule data")
    fi

    if [[ -d "$USER_DATA_DIR" ]]; then
        found_components+=("User data directory")
    fi

    if [[ -d "$CONFIG_DIR" ]]; then
        found_components+=("Configuration files")
    fi

    if [[ -d "$STORAGE_DIR" ]]; then
        found_components+=("Storage directory")
    fi

    if [[ ${#found_components[@]} -eq 0 ]]; then
        print_warning "No UATP installation detected in current directory."
        print_status "Current directory: $UATP_DIR"
        if [[ "$INTERACTIVE" == "true" ]]; then
            read -p "Continue with cleanup anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 0
            fi
        else
            exit 1
        fi
    else
        print_status "Found UATP components:"
        for component in "${found_components[@]}"; do
            echo "  - $component"
        done
    fi
}

# Function to stop running processes
stop_processes() {
    print_status "Stopping UATP processes..."

    # Stop Python processes running UATP
    local pids=$(pgrep -f "python.*run.py\|python.*uatp\|python.*capsule" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        print_status "Stopping UATP Python processes..."
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        # Force kill if still running
        echo "$pids" | xargs kill -KILL 2>/dev/null || true
        print_success "UATP processes stopped."
    fi

    # Stop any Node.js frontend processes
    local node_pids=$(pgrep -f "node.*uatp\|npm.*dev\|next.*dev" 2>/dev/null || true)
    if [[ -n "$node_pids" ]]; then
        print_status "Stopping frontend processes..."
        echo "$node_pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        echo "$node_pids" | xargs kill -KILL 2>/dev/null || true
        print_success "Frontend processes stopped."
    fi

    # Check for any remaining processes
    sleep 1
    local remaining=$(pgrep -f "uatp\|capsule.*engine" 2>/dev/null || true)
    if [[ -n "$remaining" ]]; then
        print_warning "Some UATP processes may still be running."
    fi
}

# Function to create backup
create_backup() {
    if [[ "$BACKUP_DATA" == "true" ]]; then
        local backup_dir="$HOME/uatp_backup_$(date +%Y%m%d_%H%M%S)"
        print_status "Creating backup at: $backup_dir"

        mkdir -p "$backup_dir"

        # Backup capsule data
        if [[ -f "$UATP_DIR/capsule_chain.jsonl" ]]; then
            cp "$UATP_DIR/capsule_chain.jsonl" "$backup_dir/"
            print_status "Backed up capsule chain data"
        fi

        # Backup user data
        if [[ -d "$USER_DATA_DIR" ]]; then
            cp -r "$USER_DATA_DIR" "$backup_dir/user_data/"
            print_status "Backed up user data directory"
        fi

        # Backup configuration
        if [[ -d "$CONFIG_DIR" ]]; then
            cp -r "$CONFIG_DIR" "$backup_dir/config/"
            print_status "Backed up configuration files"
        fi

        # Backup environment files
        for env_file in ".env" ".env.local" ".env.example"; do
            if [[ -f "$UATP_DIR/$env_file" ]]; then
                cp "$UATP_DIR/$env_file" "$backup_dir/"
            fi
        done

        print_success "Backup created at: $backup_dir"
        echo "You can restore from this backup later if needed."
    fi
}

# Function to remove application files
remove_application() {
    print_status "Removing UATP application files..."

    # Remove main application directories
    local dirs_to_remove=(
        "src"
        "tests"
        "docs"
        "scripts"
        "deployment"
        "k8s"
        "helm"
        "examples"
        "visualizer"
        "frontend/node_modules"
        "frontend/.next"
        "__pycache__"
        "*.egg-info"
        ".pytest_cache"
        ".hypothesis"
        ".pre-commit-cache"
    )

    for dir in "${dirs_to_remove[@]}"; do
        if [[ -d "$UATP_DIR/$dir" ]]; then
            rm -rf "$UATP_DIR/$dir"
            print_status "Removed $dir"
        fi
    done

    # Remove main application files
    local files_to_remove=(
        "run.py"
        "setup.py"
        "requirements*.txt"
        "pyproject.toml"
        "pytest.ini"
        "alembic.ini"
        "docker-compose*.yml"
        "Dockerfile"
        "*.log"
        "*.pid"
        "output.log"
        "server.log"
        "backend.log"
        "frontend.log"
    )

    for file in "${files_to_remove[@]}"; do
        if [[ -f "$UATP_DIR/$file" ]]; then
            rm -f "$UATP_DIR/$file"
            print_status "Removed $file"
        fi
    done

    print_success "Application files removed."
}

# Function to remove capsule data
remove_capsule_data() {
    if [[ "$KEEP_CAPSULES" == "false" ]]; then
        print_status "Removing capsule data..."

        local capsule_files=(
            "capsule_chain.jsonl*"
            "chain_seals.json"
            "chain_seals/"
            "*.db"
            "*.sqlite"
            "*.sqlite3"
        )

        for pattern in "${capsule_files[@]}"; do
            if ls $UATP_DIR/$pattern 1> /dev/null 2>&1; then
                rm -rf $UATP_DIR/$pattern
                print_status "Removed $pattern"
            fi
        done

        print_success "Capsule data removed."
    else
        print_status "Keeping capsule data as requested."
    fi
}

# Function to remove configuration
remove_configuration() {
    if [[ "$KEEP_CONFIG" == "false" ]]; then
        print_status "Removing configuration files..."

        if [[ -d "$CONFIG_DIR" ]]; then
            rm -rf "$CONFIG_DIR"
            print_status "Removed config directory"
        fi

        local config_files=(
            ".env*"
            "config.json"
            "settings.json"
            "uatp_config.yaml"
        )

        for pattern in "${config_files[@]}"; do
            if ls $UATP_DIR/$pattern 1> /dev/null 2>&1; then
                rm -f $UATP_DIR/$pattern
                print_status "Removed $pattern"
            fi
        done

        print_success "Configuration files removed."
    else
        print_status "Keeping configuration files as requested."
    fi
}

# Function to remove storage and logs
remove_storage_and_logs() {
    print_status "Removing storage and log files..."

    # Remove storage directory
    if [[ -d "$STORAGE_DIR" ]]; then
        rm -rf "$STORAGE_DIR"
        print_status "Removed storage directory"
    fi

    # Remove log directory
    if [[ -d "$LOG_DIR" ]]; then
        rm -rf "$LOG_DIR"
        print_status "Removed logs directory"
    fi

    # Remove temporary files
    local temp_patterns=(
        "tmp/"
        "temp/"
        ".cache/"
        "*.tmp"
        "*.temp"
        "core"
    )

    for pattern in "${temp_patterns[@]}"; do
        if ls $UATP_DIR/$pattern 1> /dev/null 2>&1; then
            rm -rf $UATP_DIR/$pattern
            print_status "Removed $pattern"
        fi
    done

    print_success "Storage and log files removed."
}

# Function to remove user data
remove_user_data() {
    if [[ "$KEEP_USER_DATA" == "false" ]]; then
        if [[ -d "$USER_DATA_DIR" ]]; then
            print_status "Removing user data directory: $USER_DATA_DIR"
            rm -rf "$USER_DATA_DIR"
            print_success "User data directory removed."
        fi
    else
        print_status "Keeping user data directory as requested."
    fi
}

# Function to remove Python virtual environment
remove_virtual_env() {
    local venv_dirs=("venv" ".venv" "env" ".env" "uatp-env")

    for venv_dir in "${venv_dirs[@]}"; do
        if [[ -d "$UATP_DIR/$venv_dir" ]] && [[ -f "$UATP_DIR/$venv_dir/pyvenv.cfg" ]]; then
            print_status "Removing Python virtual environment: $venv_dir"
            rm -rf "$UATP_DIR/$venv_dir"
            print_success "Virtual environment removed."
            break
        fi
    done
}

# Function to clean environment variables
clean_environment_variables() {
    print_status "Checking for UATP environment variables..."

    local env_vars=(
        "UATP_API_KEY"
        "UATP_CONFIG_PATH"
        "UATP_DATA_DIR"
        "OPENAI_API_KEY"
        "ANTHROPIC_API_KEY"
    )

    local shell_files=(
        "$HOME/.bashrc"
        "$HOME/.zshrc"
        "$HOME/.profile"
        "$HOME/.bash_profile"
    )

    for shell_file in "${shell_files[@]}"; do
        if [[ -f "$shell_file" ]]; then
            local modified=false
            for var in "${env_vars[@]}"; do
                if grep -q "export $var" "$shell_file" 2>/dev/null; then
                    if [[ "$INTERACTIVE" == "true" ]]; then
                        read -p "Remove $var from $shell_file? (y/N): " -n 1 -r
                        echo
                        if [[ $REPLY =~ ^[Yy]$ ]]; then
                            sed -i.bak "/export $var/d" "$shell_file"
                            modified=true
                        fi
                    else
                        print_status "Found $var in $shell_file (not removed in non-interactive mode)"
                    fi
                fi
            done
            if [[ "$modified" == "true" ]]; then
                print_status "Updated $shell_file"
            fi
        fi
    done
}

# Function to show summary
show_summary() {
    print_status "Uninstall Summary:"
    echo "=================="

    if [[ "$KEEP_CAPSULES" == "true" ]]; then
        print_status " Capsule data preserved"
    else
        print_status " Capsule data removed"
    fi

    if [[ "$KEEP_CONFIG" == "true" ]]; then
        print_status " Configuration files preserved"
    else
        print_status " Configuration files removed"
    fi

    if [[ "$KEEP_USER_DATA" == "true" ]]; then
        print_status " User data preserved"
    else
        print_status " User data removed"
    fi

    echo ""
    print_success "UATP Capsule Engine has been uninstalled."

    if [[ "$BACKUP_DATA" == "true" ]]; then
        print_status "Your data backup is available in ~/uatp_backup_*"
    fi

    if [[ "$KEEP_CAPSULES" == "true" || "$KEEP_CONFIG" == "true" || "$KEEP_USER_DATA" == "true" ]]; then
        echo ""
        print_status "To reinstall UATP later, run: ./install.sh"
        print_status "Your preserved data will be automatically detected."
    fi
}

# Function to get user confirmation
get_confirmation() {
    if [[ "$FORCE_REMOVE" == "true" ]]; then
        return 0
    fi

    if [[ "$INTERACTIVE" == "false" ]]; then
        return 0
    fi

    echo ""
    print_warning "This will uninstall UATP Capsule Engine from:"
    echo "  Directory: $UATP_DIR"
    if [[ "$KEEP_USER_DATA" == "false" ]]; then
        echo "  User data: $USER_DATA_DIR (WILL BE REMOVED)"
    else
        echo "  User data: $USER_DATA_DIR (will be preserved)"
    fi

    if [[ "$KEEP_CAPSULES" == "false" ]]; then
        echo "  Capsule data: WILL BE REMOVED"
    else
        echo "  Capsule data: will be preserved"
    fi

    echo ""
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Uninstall cancelled."
        exit 0
    fi
}

# Main execution
main() {
    # Show header
    echo "================================================"
    echo "    UATP Capsule Engine Uninstaller v1.0"
    echo "================================================"
    echo ""

    # Parse arguments
    parse_args "$@"

    # Check permissions
    check_permissions

    # Detect installation
    detect_installation

    # Get user confirmation
    get_confirmation

    # Create backup if requested
    create_backup

    # Stop running processes
    stop_processes

    # Remove components
    remove_application
    remove_capsule_data
    remove_configuration
    remove_storage_and_logs
    remove_user_data
    remove_virtual_env
    clean_environment_variables

    # Show summary
    show_summary

    echo ""
    print_success "Uninstall completed successfully!"
}

# Handle script interruption
trap 'print_error "Uninstall interrupted. System may be in incomplete state."; exit 1' INT TERM

# Run main function with all arguments
main "$@"
