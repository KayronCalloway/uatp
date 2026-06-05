#!/bin/bash
# Start Claude Code Auto-Capture Service

echo " Starting Claude Code Auto-Capture Service..."
echo "This will run in the background and capture all Claude Code conversations"
echo "Press Ctrl+C to stop, or close this terminal window"
echo ""

# Run the auto-capture service
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
python3 "$REPO_ROOT/claude_code_auto_capture.py"
