#!/bin/bash
#
# UATP Capsule Engine - Full Stack Launcher
# Double-click this file to start both backend and frontend
#

# Change to project directory
cd "$(dirname "$0")"

echo "========================================"
echo "  UATP Capsule Engine - Starting Up"
echo "========================================"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "[OK] Virtual environment activated"
fi

# Kill any existing processes on our ports
echo "[..] Cleaning up existing processes..."
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :3000 | xargs kill -9 2>/dev/null || true
sleep 1

# Start Backend (FastAPI on port 8000)
echo "[..] Starting backend server (port 8000)..."
ENVIRONMENT=development .venv/bin/python run.py > /tmp/uatp-backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > /tmp/uatp-backend.pid

# Start Frontend (Next.js on port 3000)
echo "[..] Starting frontend server (port 3000)..."
cd frontend
npm run dev > /tmp/uatp-frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > /tmp/uatp-frontend.pid
cd ..

# Wait for servers to initialize
echo "[..] Waiting for servers to start..."
sleep 4

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "[OK] Backend running at http://localhost:8000"
else
    echo "[!!] Backend may still be starting - check /tmp/uatp-backend.log"
fi

# Check if frontend is running
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "[OK] Frontend running at http://localhost:3000"
else
    echo "[!!] Frontend may still be starting - check /tmp/uatp-frontend.log"
fi

echo ""
echo "========================================"
echo "  Capsule Engine is Running!"
echo "========================================"
echo ""
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "  Press Ctrl+C to stop both servers"
echo "========================================"
echo ""

# Open browser
open http://localhost:3000

# Cleanup function
cleanup() {
    echo ""
    echo "[..] Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    rm -f /tmp/uatp-backend.pid /tmp/uatp-frontend.pid
    echo "[OK] Servers stopped. Goodbye!"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

# Keep script running
wait
