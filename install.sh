#!/bin/bash

# UATP Capsule Engine Installation Script
# This script sets up the UATP Capsule Engine for development or production use

set -e  # Exit on any error

UATP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_MIN_VERSION="3.11"
VENV_DIR="$UATP_ROOT/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo "════════════════════════════════════════════════════════════════"
echo "   🚀 UATP Capsule Engine Installation"
echo "   Unified Agent Trust Protocol - Enterprise AI Attribution"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check Python version
check_python_version() {
    log_info "Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        log_error "Please install Python 3.11+ from https://python.org"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')

    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
        log_success "Python $PYTHON_VERSION detected (✓ >= $PYTHON_MIN_VERSION)"
    else
        log_error "Python $PYTHON_VERSION detected (✗ < $PYTHON_MIN_VERSION required)"
        log_error "Please upgrade to Python 3.11 or higher"
        exit 1
    fi
}

# Create virtual environment
create_virtual_environment() {
    log_info "Setting up Python virtual environment..."

    if [ -d "$VENV_DIR" ]; then
        log_warn "Virtual environment already exists at $VENV_DIR"
        read -p "Remove and recreate? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
        else
            log_info "Using existing virtual environment"
            return 0
        fi
    fi

    python3 -m venv "$VENV_DIR"
    log_success "Virtual environment created at $VENV_DIR"
}

# Activate virtual environment
activate_virtual_environment() {
    log_info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    # Upgrade pip
    pip install --upgrade pip
    log_success "Virtual environment activated and pip upgraded"
}

# Install dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."

    # Check if requirements.txt exists
    if [ ! -f "$UATP_ROOT/requirements.txt" ]; then
        log_error "requirements.txt not found"
        exit 1
    fi

    # Install requirements
    pip install -r "$UATP_ROOT/requirements.txt"
    log_success "Python dependencies installed"
}

# Setup database
setup_database() {
    log_info "Setting up database..."

    # Check if PostgreSQL is available
    if command -v psql &> /dev/null; then
        log_info "PostgreSQL detected"

        # Check if database exists
        if ! psql -lqt | cut -d \| -f 1 | grep -qw uatp_capsule_engine; then
            log_warn "Database 'uatp_capsule_engine' not found"
            read -p "Create database? [Y/n]: " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                createdb uatp_capsule_engine
                log_success "Database 'uatp_capsule_engine' created"
            fi
        else
            log_success "Database 'uatp_capsule_engine' exists"
        fi

        # Run migrations
        if [ -f "$UATP_ROOT/alembic.ini" ]; then
            log_info "Running database migrations..."
            cd "$UATP_ROOT"
            alembic upgrade head
            log_success "Database migrations completed"
        fi
    else
        log_warn "PostgreSQL not detected - using SQLite fallback"
        log_info "For production use, install PostgreSQL"
    fi
}

# Setup Redis
setup_redis() {
    log_info "Checking Redis..."

    if command -v redis-server &> /dev/null; then
        if pgrep redis-server > /dev/null; then
            log_success "Redis is running"
        else
            log_warn "Redis is installed but not running"
            log_info "Start Redis with: redis-server"
        fi
    else
        log_warn "Redis not detected"
        log_info "Install Redis for caching: brew install redis (macOS) or apt-get install redis (Ubuntu)"
    fi
}

# Create environment file
create_environment_file() {
    log_info "Setting up environment configuration..."

    ENV_FILE="$UATP_ROOT/.env"

    if [ -f "$ENV_FILE" ]; then
        log_warn ".env file already exists"
        return 0
    fi

    cat > "$ENV_FILE" << 'EOF'
# UATP Capsule Engine Configuration

# Core Settings
UATP_AGENT_ID=demo-agent-007
UATP_CHAIN_PATH=capsule_chain.jsonl
UATP_DEFAULT_AI_MODEL=gpt-4-turbo

# Database Configuration
DATABASE_URL=postgresql://localhost:5432/uatp_capsule_engine
# Alternative SQLite: DATABASE_URL=sqlite:///uatp_capsule.db

# Redis Configuration
REDIS_URL=redis://localhost:6379

# API Configuration
API_PORT=5006
API_HOST=0.0.0.0

# Security Configuration
UATP_SIGNING_KEY=your-ed25519-private-key-here
UATP_ETHICS_STRICT_MODE=false

# AI Integration
OPENAI_API_KEY=your-openai-key-here
# ANTHROPIC_API_KEY=your-anthropic-key-here

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=uatp-capsule-engine
PROMETHEUS_METRICS_PORT=9090

# Secrets Management (optional)
# VAULT_URL=https://vault.example.com
# VAULT_TOKEN=your-vault-token
# AWS_SECRETS_REGION=us-east-1
EOF

    log_success "Environment file created at $ENV_FILE"
    log_warn "⚠️  Please edit .env file and add your API keys and configuration"
}

# Generate cryptographic keys
generate_keys() {
    log_info "Generating cryptographic keys..."

    python3 << 'EOF'
import os
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

# Generate a new signing key
signing_key = SigningKey.generate()
verify_key = signing_key.verify_key

# Encode as hex
signing_key_hex = signing_key.encode(encoder=HexEncoder).decode('ascii')
verify_key_hex = verify_key.encode(encoder=HexEncoder).decode('ascii')

print(f"Generated cryptographic keys:")
print(f"UATP_SIGNING_KEY={signing_key_hex}")
print(f"UATP_VERIFY_KEY={verify_key_hex}")

# Update .env file
env_file = ".env"
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        content = f.read()

    # Replace the placeholder signing key
    content = content.replace(
        "UATP_SIGNING_KEY=your-ed25519-private-key-here",
        f"UATP_SIGNING_KEY={signing_key_hex}"
    )

    with open(env_file, 'w') as f:
        f.write(content)

    print("✅ Updated .env file with generated keys")
else:
    print("⚠️  .env file not found - please add keys manually")
EOF

    log_success "Cryptographic keys generated"
}

# Create startup scripts
create_startup_scripts() {
    log_info "Creating startup scripts..."

    # Development startup script
    cat > "$UATP_ROOT/start-dev.sh" << 'EOF'
#!/bin/bash

# UATP Capsule Engine - Development Startup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting UATP Capsule Engine (Development Mode)"
echo "=================================================="

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Run ./install.sh first"
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  .env file not found - using defaults"
fi

# Start services in parallel
echo ""
echo "Starting services..."

# Start API server
echo "🌐 Starting API server on port ${API_PORT:-5006}..."
python -m src.api.server &
API_PID=$!

# Start visualizer (optional)
if command -v streamlit &> /dev/null; then
    echo "📊 Starting visualizer on port 8501..."
    streamlit run visualizer/app.py --server.headless true --server.port 8501 &
    VIZ_PID=$!
else
    echo "⚠️  Streamlit not installed - visualizer not started"
    VIZ_PID=""
fi

# Store PIDs for cleanup
echo $API_PID > .api.pid
if [ -n "$VIZ_PID" ]; then
    echo $VIZ_PID > .viz.pid
fi

echo ""
echo "🎉 UATP Capsule Engine started successfully!"
echo "   API: http://localhost:${API_PORT:-5006}"
echo "   Visualizer: http://localhost:8501"
echo "   Docs: http://localhost:${API_PORT:-5006}/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo ""; echo "🛑 Stopping services..."; kill $API_PID 2>/dev/null || true; [ -n "$VIZ_PID" ] && kill $VIZ_PID 2>/dev/null || true; exit 0' INT
wait
EOF

    # Production startup script
    cat > "$UATP_ROOT/start-prod.sh" << 'EOF'
#!/bin/bash

# UATP Capsule Engine - Production Startup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting UATP Capsule Engine (Production Mode)"
echo "================================================="

# Activate virtual environment
source venv/bin/activate

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Start with gunicorn for production
echo "🌐 Starting production server..."
gunicorn --bind 0.0.0.0:${API_PORT:-5006} \
         --workers 4 \
         --worker-class uvicorn.workers.UvicornWorker \
         --access-logfile - \
         --error-logfile - \
         src.api.server:create_app
EOF

    # Stop script
    cat > "$UATP_ROOT/stop.sh" << 'EOF'
#!/bin/bash

# UATP Capsule Engine - Stop Services

echo "🛑 Stopping UATP Capsule Engine services..."

# Kill API server
if [ -f ".api.pid" ]; then
    API_PID=$(cat .api.pid)
    kill $API_PID 2>/dev/null || true
    rm .api.pid
    echo "✅ API server stopped"
fi

# Kill visualizer
if [ -f ".viz.pid" ]; then
    VIZ_PID=$(cat .viz.pid)
    kill $VIZ_PID 2>/dev/null || true
    rm .viz.pid
    echo "✅ Visualizer stopped"
fi

# Kill any remaining processes
pkill -f "src.api.server" 2>/dev/null || true
pkill -f "streamlit.*visualizer" 2>/dev/null || true

echo "🎉 All services stopped"
EOF

    # Make scripts executable
    chmod +x "$UATP_ROOT/start-dev.sh"
    chmod +x "$UATP_ROOT/start-prod.sh"
    chmod +x "$UATP_ROOT/stop.sh"

    log_success "Startup scripts created"
}

# Create Makefile
create_makefile() {
    log_info "Creating Makefile..."

    cat > "$UATP_ROOT/Makefile" << 'EOF'
# UATP Capsule Engine Makefile

.PHONY: help install dev prod stop test clean lint format docs

# Default target
help:
	@echo "UATP Capsule Engine - Available Commands"
	@echo "========================================"
	@echo ""
	@echo "🔧 Setup & Installation:"
	@echo "  install     Install dependencies and setup environment"
	@echo "  clean       Clean up generated files and caches"
	@echo ""
	@echo "🚀 Running:"
	@echo "  dev         Start development server"
	@echo "  prod        Start production server"
	@echo "  stop        Stop all services"
	@echo ""
	@echo "🧪 Development:"
	@echo "  test        Run test suite"
	@echo "  lint        Run code linting"
	@echo "  format      Format code"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  docs        Generate documentation"
	@echo ""

# Installation
install:
	@echo "📦 Installing UATP Capsule Engine..."
	./install.sh

# Development server
dev:
	@echo "🚀 Starting development server..."
	./start-dev.sh

# Production server
prod:
	@echo "🚀 Starting production server..."
	./start-prod.sh

# Stop services
stop:
	@echo "🛑 Stopping services..."
	./stop.sh

# Run tests
test:
	@echo "🧪 Running tests..."
	source venv/bin/activate && python -m pytest tests/ -v

# Lint code
lint:
	@echo "🔍 Running linters..."
	source venv/bin/activate && \
	flake8 src/ --max-line-length=100 --ignore=E203,W503 && \
	mypy src/ --ignore-missing-imports

# Format code
format:
	@echo "✨ Formatting code..."
	source venv/bin/activate && \
	black src/ tests/ --line-length=100 && \
	isort src/ tests/

# Generate documentation
docs:
	@echo "📚 Generating documentation..."
	python3 create_manual_formats.py

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -f .api.pid .viz.pid
EOF

    log_success "Makefile created"
}

# Run installation
main() {
    log_info "Starting UATP Capsule Engine installation..."

    # Change to script directory
    cd "$UATP_ROOT"

    # Run installation steps
    check_python_version
    create_virtual_environment
    activate_virtual_environment
    install_dependencies
    setup_database
    setup_redis
    create_environment_file
    generate_keys
    create_startup_scripts
    create_makefile

    echo ""
    echo "════════════════════════════════════════════════════════════════"
    log_success "🎉 UATP Capsule Engine installation completed!"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Edit .env file with your API keys and configuration"
    echo "   2. Start development server: make dev"
    echo "   3. View API docs: http://localhost:5006/docs"
    echo "   4. View visualizer: http://localhost:8501"
    echo ""
    echo "🔧 Available Commands:"
    echo "   make help    - Show all available commands"
    echo "   make dev     - Start development server"
    echo "   make test    - Run test suite"
    echo "   make docs    - Generate documentation"
    echo ""
    log_warn "⚠️  Don't forget to add your API keys to .env file!"
}

# Run main function
main "$@"
