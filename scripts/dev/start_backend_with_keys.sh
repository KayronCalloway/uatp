#!/bin/bash

# Set API keys for development
export UATP_API_KEYS='{"dev-key-001": {"agent_id": "dev-agent-001", "permissions": ["read", "write", "admin", "ai", "capsule:create", "capsule:read", "capsule:list"], "description": "Development test key with full permissions"}}'

echo "Starting UATP backend with API keys..."
echo "API Key: dev-key-001"
echo "Permissions: read, write, admin, ai, capsule:create, capsule:read, capsule:list"

# Start the server
python3 -m src.api.server --host 0.0.0.0 --port 9090
