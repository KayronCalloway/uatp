#!/bin/bash
# Claude Code Auto-Capture Hook
# Automatically captures conversations after each user message

UATP_DIR="/Users/kay/uatp-capsule-engine"
CAPTURE_SCRIPT="$UATP_DIR/capture_this_session.py"
LOG_FILE="$UATP_DIR/hook_capture.log"
COUNTER_FILE="/tmp/claude_code_capture_counter"

# Critical keywords that trigger INSTANT capture (no delay)
CRITICAL_KEYWORDS=(
    "life defining"
    "critical"
    "emergency"
    "important decision"
    "breakthrough"
    "capture now"
    "save this"
    "urgent"
)

# Get user message from stdin (if available)
USER_MESSAGE=""
if [ -p /dev/stdin ]; then
    USER_MESSAGE=$(cat)
fi

# Check for critical keywords
SHOULD_CAPTURE_NOW=false
for keyword in "${CRITICAL_KEYWORDS[@]}"; do
    if echo "$USER_MESSAGE" | grep -qi "$keyword"; then
        SHOULD_CAPTURE_NOW=true
        echo "[$(date)] INSTANT CAPTURE triggered by keyword: $keyword" >> "$LOG_FILE"
        break
    fi
done

# If critical, capture immediately
if [ "$SHOULD_CAPTURE_NOW" = true ]; then
    echo "[$(date)] CRITICAL: Immediate capture triggered" >> "$LOG_FILE"
    (cd "$UATP_DIR" && python3 "$CAPTURE_SCRIPT" >> "$LOG_FILE" 2>&1) &
    echo "0" > "$COUNTER_FILE"  # Reset counter
    exit 0
fi

# Otherwise, use normal throttled capture
# Initialize counter
if [ ! -f "$COUNTER_FILE" ]; then
    echo "0" > "$COUNTER_FILE"
fi

# Read and increment counter
COUNTER=$(cat "$COUNTER_FILE")
COUNTER=$((COUNTER + 1))

# Capture every 5 interactions
if [ $((COUNTER % 5)) -eq 0 ]; then
    echo "[$(date)] Auto-capture (interaction #$COUNTER)" >> "$LOG_FILE"
    (cd "$UATP_DIR" && python3 "$CAPTURE_SCRIPT" >> "$LOG_FILE" 2>&1) &
    echo "0" > "$COUNTER_FILE"  # Reset counter
else
    echo "$COUNTER" > "$COUNTER_FILE"
fi
