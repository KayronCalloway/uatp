#!/bin/bash

# UATP Live Capture System Startup Script
# ========================================

echo " Starting UATP Live Capture System"
echo "===================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed or not in PATH"
    exit 1
fi

# Check if required packages are installed
echo " Checking dependencies..."
python3 -c "import aiohttp, requests, asyncio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo " Installing required dependencies..."
    pip3 install aiohttp requests python-dotenv
fi

# Set up environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Start the UATP server in the background
echo "  Starting UATP server..."
python3 src/api/server.py &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 5

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "[ERROR] Server failed to start"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo "[OK] Server is running at http://localhost:8000"

# Start the live capture client
echo " Starting live capture client..."
python3 live_capture_client.py

# Clean up on exit
echo " Cleaning up..."
kill $SERVER_PID 2>/dev/null
echo "[OK] Live capture system stopped"
