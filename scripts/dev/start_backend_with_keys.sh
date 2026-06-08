#!/bin/bash
set -euo pipefail

# Start the development backend with caller-provided API keys.
# Example:
#   export UATP_API_KEYS='{"local-dev-key": {"agent_id": "dev-agent", "permissions": ["read", "write"]}}'
#   ./scripts/dev/start_backend_with_keys.sh

if [ -z "${UATP_API_KEYS:-}" ]; then
    echo "[ERROR] UATP_API_KEYS must be set before starting the backend."
    echo "        Do not commit or print real API keys; keep them in your local shell or secret manager."
    exit 1
fi

echo "Starting UATP backend with caller-provided API key configuration."
echo "API keys are configured but not printed."

python3 -m src.api.server --host "${UATP_API_HOST:-127.0.0.1}" --port "${UATP_API_PORT:-9090}"
