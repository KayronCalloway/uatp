#!/bin/bash
# Start Desktop Apps Auto-Capture Service

echo " Starting Desktop Apps Auto-Capture Service..."
echo "Monitoring: Claude Desktop & Windsurf"
echo "Press Ctrl+C to stop"
echo ""

# Run the desktop apps auto-capture service
python3 /Users/kay/uatp-capsule-engine/claude_desktop_windsurf_capture.py
