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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cp "$REPO_ROOT/.claude/hooks/auto_capture.sh" "$GLOBAL_HOOKS_DIR/auto_capture.sh"
chmod +x "$GLOBAL_HOOKS_DIR/auto_capture.sh"

echo "[OK] Global hook installed at: $GLOBAL_HOOKS_DIR/auto_capture.sh"
echo ""
echo " Now all your Claude Code sessions will auto-capture to UATP!"
echo "   Works from ANY directory, ANY project"
echo ""
echo " Logs: $REPO_ROOT/hook_capture.log"
echo " Sessions: $REPO_ROOT/live_capture.db"
echo ""
echo " Setup complete!"
