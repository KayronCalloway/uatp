#!/bin/bash
# Show the last session walkthrough to avoid token waste on recaps

UATP_DIR="$(git rev-parse --show-toplevel 2>/dev/null || cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo " Last Session Walkthrough"
echo "=" | head -c 60 && echo ""
echo ""

cd "$UATP_DIR" && python3 generate_session_walkthrough.py --latest
