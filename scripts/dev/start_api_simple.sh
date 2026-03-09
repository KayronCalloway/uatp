#!/bin/bash
# Start API server without anthropic (for demo mode testing)
unset ANTHROPIC_API_KEY
export UATP_DEMO_MODE=true

python3 run.py &> api_server.log &
echo $! > api_server.pid
sleep 3
curl -s http://localhost:8000/health | head -20
echo ""
echo "API server running (PID: $(cat api_server.pid))"
