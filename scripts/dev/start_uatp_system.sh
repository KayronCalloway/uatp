#!/bin/bash
# UATP System Launcher - Production Mode
# Ensures both frontend and backend run in background

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo " Starting UATP Capsule Engine System..."

# Kill any existing processes
pkill -f "next-server" 2>/dev/null || true
pkill -f "quart.*src.api.server" 2>/dev/null || true
sleep 2

# Start backend API
echo " Starting Backend API (port 8000)..."
cd "$SCRIPT_DIR"
UATP_DEMO_MODE=true python3 -m quart --app src.api.server:app run --host 0.0.0.0 --port 8000 > api_server.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > api_server.pid
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to be ready
sleep 3
if ! curl -s http://localhost:8000/onboarding/api/platforms > /dev/null 2>&1; then
    echo "[WARN]  Backend API not responding, checking logs..."
    tail -10 api_server.log
fi

# Start frontend
echo " Starting Frontend (port 3000)..."
cd "$SCRIPT_DIR/frontend"
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > frontend.pid
echo "   Frontend PID: $FRONTEND_PID"

# Wait for frontend to be ready
sleep 3

echo ""
echo "[OK] UATP System Running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Frontend:  http://localhost:3000"
echo " Backend:   http://localhost:8000"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Process IDs saved to:"
echo "  - api_server.pid (Backend: $BACKEND_PID)"
echo "  - frontend/frontend.pid (Frontend: $FRONTEND_PID)"
echo ""
echo "To stop: pkill -f 'next-server' && pkill -f 'quart.*src.api.server'"
echo "Logs: api_server.log, frontend.log"
