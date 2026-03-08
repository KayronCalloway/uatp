#!/bin/bash
#
# UATP Capsule Engine - Stop Servers
# Double-click this file to stop running servers
#

echo "Stopping UATP Capsule Engine..."

# Kill by saved PIDs
if [ -f /tmp/uatp-backend.pid ]; then
    kill $(cat /tmp/uatp-backend.pid) 2>/dev/null && echo "[OK] Backend stopped"
    rm -f /tmp/uatp-backend.pid
fi

if [ -f /tmp/uatp-frontend.pid ]; then
    kill $(cat /tmp/uatp-frontend.pid) 2>/dev/null && echo "[OK] Frontend stopped"
    rm -f /tmp/uatp-frontend.pid
fi

# Also kill by port in case PIDs are stale
lsof -ti :8000 | xargs kill -9 2>/dev/null
lsof -ti :3000 | xargs kill -9 2>/dev/null

echo "[OK] All servers stopped"
