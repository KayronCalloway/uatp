#!/bin/bash
# Show the last session walkthrough to avoid token waste on recaps

UATP_DIR="/Users/kay/uatp-capsule-engine"

echo "📖 Last Session Walkthrough"
echo "=" | head -c 60 && echo ""
echo ""

cd "$UATP_DIR" && python3 generate_session_walkthrough.py --latest
