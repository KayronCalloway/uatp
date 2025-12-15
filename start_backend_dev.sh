#!/bin/bash
# Start UATP backend with development environment

# Kill existing backend on port 8000
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

# Wait for port to be released
sleep 2

# Start backend with development environment
ENVIRONMENT=development python3 run.py > api_server.log 2>&1 &
NEW_PID=$!

# Save PID
echo $NEW_PID > api_server.pid

# Wait for startup
sleep 3

# Test connection
echo "Backend started with PID: $NEW_PID"
curl -s http://localhost:8000/health | head -3
