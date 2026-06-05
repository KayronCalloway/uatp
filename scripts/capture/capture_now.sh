#!/bin/bash
# INSTANT CAPTURE - Run this anytime for immediate capture

cd "$(git rev-parse --show-toplevel 2>/dev/null || dirname "$0"/../..)"
python3 capture_this_session.py

echo ""
echo "[OK] Conversation captured immediately!"
echo " View at: http://localhost:3000"
