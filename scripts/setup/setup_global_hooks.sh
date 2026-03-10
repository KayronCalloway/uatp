#!/bin/bash
# Setup global Claude Code hooks for UATP capture

echo " Setting up global Claude Code hooks for UATP capture..."
echo ""

# Claude Code global hooks directory
GLOBAL_HOOKS_DIR="$HOME/.config/claude-code/hooks"

# Create global hooks directory if it doesn't exist
mkdir -p "$GLOBAL_HOOKS_DIR"

# Copy the rich capture hook
echo " Copying auto_capture.sh to global hooks..."
cp /Users/kay/uatp-capsule-engine/.claude/hooks/auto_capture.sh "$GLOBAL_HOOKS_DIR/auto_capture.sh"
chmod +x "$GLOBAL_HOOKS_DIR/auto_capture.sh"

echo "[OK] Global hook installed at: $GLOBAL_HOOKS_DIR/auto_capture.sh"
echo ""
echo " Now all your Claude Code sessions will auto-capture to UATP!"
echo "   Works from ANY directory, ANY project"
echo ""
echo " Logs: /Users/kay/uatp-capsule-engine/hook_capture.log"
echo " Sessions: /Users/kay/uatp-capsule-engine/live_capture.db"
echo ""
echo " Setup complete!"
