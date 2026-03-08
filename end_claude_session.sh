#!/bin/bash
# End Claude Code Session and Create Final RICH Capsule + Walkthrough

UATP_DIR="/Users/kay/uatp-capsule-engine"

echo " Ending Claude Code session and creating final RICH capsule..."
cd "$UATP_DIR" && python3 rich_hook_capture.py --end-session

echo ""
echo " Generating session walkthrough documentation..."
cd "$UATP_DIR" && python3 generate_session_walkthrough.py

echo ""
echo "[OK] Session ended. You can start a new session on your next message."
echo " Tip: Run './show_last_session.sh' at next session start to avoid recap!"
