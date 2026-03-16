#!/usr/bin/env bash
#
# UATP Development Launcher
# One command. Everything starts.
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo -e "${DIM}Shutting down...${NC}"
    [[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null
    [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

print_banner() {
    echo ""
    echo -e "${CYAN}${BOLD}"
    echo "  ╔═══════════════════════════════════════════════════════════╗"
    echo "  ║                                                           ║"
    echo "  ║   █    █  █████  ██████ ████                              ║"
    echo "  ║   █    █  █   █    █    █   █                             ║"
    echo "  ║   █    █  █████    █    ████                              ║"
    echo "  ║   █    █  █   █    █    █                                 ║"
    echo "  ║    ████   █   █    █    █                                 ║"
    echo "  ║                                                           ║"
    echo "  ║   Cryptographic Audit Trails for AI Decisions             ║"
    echo "  ║                                                           ║"
    echo "  ╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}✗ $1 not found${NC}"
        return 1
    fi
    echo -e "${GREEN}✓${NC} $1 $(command -v "$1" | head -1)"
    return 0
}

step() {
    echo -e "\n${BLUE}▸${NC} ${BOLD}$1${NC}"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}!${NC} $1"
}

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

print_banner

step "Checking dependencies"

MISSING=0
check_command python3 || MISSING=1
check_command node || MISSING=1
check_command npm || MISSING=1

if [[ $MISSING -eq 1 ]]; then
    echo ""
    echo -e "${RED}Missing dependencies. Please install:${NC}"
    echo "  - Python 3.10+: https://python.org"
    echo "  - Node.js 18+:  https://nodejs.org"
    exit 1
fi

# Check Python version
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [[ $PY_MAJOR -lt 3 ]] || [[ $PY_MAJOR -eq 3 && $PY_MINOR -lt 10 ]]; then
    echo -e "${RED}✗ Python 3.10+ required (found $PY_VERSION)${NC}"
    exit 1
fi
success "Python $PY_VERSION"

# ─────────────────────────────────────────────────────────────────────────────
# Backend Setup
# ─────────────────────────────────────────────────────────────────────────────

step "Setting up backend"

cd "$SCRIPT_DIR"

# Create venv if needed
if [[ ! -d ".venv" ]]; then
    echo -e "${DIM}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate
success "Virtual environment activated"

# Install dependencies
if [[ ! -f ".venv/.deps_installed" ]] || [[ "requirements.txt" -nt ".venv/.deps_installed" ]]; then
    echo -e "${DIM}Installing Python dependencies...${NC}"
    pip install -q --upgrade pip
    pip install -q -e ".[dev]" 2>/dev/null || pip install -q -e .
    touch .venv/.deps_installed
fi
success "Python dependencies ready"

# ─────────────────────────────────────────────────────────────────────────────
# Frontend Setup
# ─────────────────────────────────────────────────────────────────────────────

step "Setting up frontend"

cd "$SCRIPT_DIR/frontend"

# Create .env.local if missing
if [[ ! -f ".env.local" ]]; then
    if [[ -f ".env.example" ]]; then
        cp .env.example .env.local
        success "Created .env.local from template"
    else
        echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
        success "Created .env.local"
    fi
fi

# Install node dependencies
if [[ ! -d "node_modules" ]] || [[ "package.json" -nt "node_modules/.package-lock.json" ]]; then
    echo -e "${DIM}Installing Node dependencies...${NC}"
    npm install --silent 2>/dev/null
fi
success "Node dependencies ready"

cd "$SCRIPT_DIR"

# ─────────────────────────────────────────────────────────────────────────────
# Launch Services
# ─────────────────────────────────────────────────────────────────────────────

step "Starting services"

# Start backend
echo -e "${DIM}Starting backend on port 8000...${NC}"
python3 run.py > /tmp/uatp-backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        success "Backend running at http://localhost:8000"
        break
    fi
    if [[ $i -eq 30 ]]; then
        echo -e "${RED}✗ Backend failed to start. Check /tmp/uatp-backend.log${NC}"
        exit 1
    fi
    sleep 0.5
done

# Start frontend
echo -e "${DIM}Starting frontend on port 3000...${NC}"
cd "$SCRIPT_DIR/frontend"
npm run dev > /tmp/uatp-frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        success "Frontend running at http://localhost:3000"
        break
    fi
    if [[ $i -eq 30 ]]; then
        warn "Frontend may still be compiling..."
    fi
    sleep 0.5
done

cd "$SCRIPT_DIR"

# ─────────────────────────────────────────────────────────────────────────────
# Ready
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}UATP is running!${NC}"
echo ""
echo -e "  ${CYAN}Dashboard:${NC}  http://localhost:3000"
echo -e "  ${CYAN}API:${NC}        http://localhost:8000"
echo -e "  ${CYAN}API Docs:${NC}   http://localhost:8000/docs"
echo ""
echo -e "  ${DIM}Press Ctrl+C to stop${NC}"
echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Open browser (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    sleep 2
    open "http://localhost:3000" 2>/dev/null || true
fi

# Keep running
wait
