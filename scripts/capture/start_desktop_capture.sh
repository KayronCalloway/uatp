#!/bin/bash
# Start Desktop Apps Auto-Capture Service

echo " Starting Desktop Apps Auto-Capture Service..."
echo "Monitoring: Claude Desktop & Windsurf"
echo "Press Ctrl+C to stop"
echo ""

# Run the desktop apps auto-capture service
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
python3 "$REPO_ROOT/claude_desktop_windsurf_capture.py"
