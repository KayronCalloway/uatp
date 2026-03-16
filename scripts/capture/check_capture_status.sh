#!/bin/bash
# Check UATP Auto-Capture Status

echo "======================================"
echo " UATP Auto-Capture Status"
echo "======================================"
echo ""

# Check API Server
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "[OK] API Server (Port 8000): Running"
else
    echo "[ERROR] API Server (Port 8000): Not Running"
fi

# Check Antigravity Capture
if pgrep -f "antigravity_capture_integration.py" > /dev/null; then
    echo "[OK] Antigravity Capture: Running"
    echo "   Log: tail -f antigravity_capture.log"
else
    echo "[ERROR] Antigravity Capture: Not Running"
fi

# Check Claude Code Hook
if [ -f ".claude/hooks/auto_capture.sh" ] && [ -x ".claude/hooks/auto_capture.sh" ]; then
    echo "[OK] Claude Code Hook: Configured"
    if [ -f "hook_capture.log" ]; then
        LAST_CAPTURE=$(tail -1 hook_capture.log 2>/dev/null | grep -oE '\[[^]]+\]' | head -1)
        if [ -n "$LAST_CAPTURE" ]; then
            echo "   Last run: $LAST_CAPTURE"
        fi
    fi
    echo "   Log: tail -f hook_capture.log"
    # Check counter
    if [ -f "/tmp/claude_code_capture_counter" ]; then
        COUNTER=$(cat /tmp/claude_code_capture_counter)
        REMAINING=$((5 - COUNTER))
        echo "   Next capture in $REMAINING interactions"
    fi
else
    echo "[ERROR] Claude Code Hook: Not Configured"
fi

echo ""
echo " Recent Capsules:"
curl -s "http://localhost:8000/capsules?limit=3" 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for cap in data.get('capsules', [])[:3]:
        print(f\"   • {cap['id'][:30]}... ({cap['type']})\")
except: pass
" 2>/dev/null || echo "   (API server not responding)"

echo ""
echo "======================================"
