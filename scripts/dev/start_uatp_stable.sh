#!/bin/bash
#
# UATP Stable Server Launcher
# Easy script to start the production-grade UATP server
#

echo "=== UATP Capsule Engine - Stable Server ==="
echo ""

# Check if production server exists
if [[ ! -f "start_production_server.py" ]]; then
    echo "[ERROR] Production server not found. Using fallback..."
    if [[ -f "start_real_server.py" ]]; then
        echo " Starting with real server (fallback)..."
        python3 start_real_server.py
    else
        echo "[ERROR] No server scripts found!"
        exit 1
    fi
else
    echo " Starting production server with Uvicorn..."
    echo "   Host: 0.0.0.0"
    echo "   Port: 9090"
    echo "   Frontend URL: http://localhost:9090"
    echo ""
    echo "[OK] Production-grade ASGI server for stability"
    echo "[OK] Automatic restart on crashes"
    echo "[OK] Better performance than development server"
    echo ""
    echo "Press Ctrl+C to stop"
    echo "=" * 50

    # Start the production server
    python3 start_production_server.py
fi
