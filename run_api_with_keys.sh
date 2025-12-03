#!/bin/bash

# Stop any existing server
pkill -f "python3 api/server.py" || true

# Export API keys from test file
export UATP_API_KEYS=$(cat tests/test_api_keys.json)

# Set API port to 8888
export UATP_API_PORT=8888

# Start the API server
python3 api/server.py
