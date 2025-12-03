#!/usr/bin/env python3
"""
Development API Keys Configuration
Simple script to create development API keys for testing
"""

import os

# Set up development API keys for the Quart server
dev_keys = {
    "dev-key-001": {
        "agent_id": "dev-agent-001",
        "permissions": [
            "read",
            "write",
            "admin",
            "ai",
            "capsule:create",
            "capsule:read",
            "capsule:list",
        ],
        "description": "Development test key with full permissions",
    }
}

# Export as environment variable for the server
api_keys_str = str(dev_keys).replace("'", '"')
print(f"UATP_API_KEYS='{api_keys_str}'")

# Also create a simple .env file for development
with open(".env.development", "w") as f:
    f.write("ENVIRONMENT=development\n")
    f.write("UATP_API_PORT=9090\n")
    f.write(f"UATP_API_KEYS='{api_keys_str}'\n")
    f.write(
        "CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000\n"
    )

print("\nDevelopment configuration created!")
print("API Key for testing: dev-key-001")
print("Use header: X-API-Key: dev-key-001")
