#!/bin/bash
# Start Claude Code Auto-Capture Service

echo " Starting Claude Code Auto-Capture Service..."
echo "This will run in the background and capture all Claude Code conversations"
echo "Press Ctrl+C to stop, or close this terminal window"
echo ""

# Run the auto-capture service
python3 /Users/kay/uatp-capsule-engine/claude_code_auto_capture.py
