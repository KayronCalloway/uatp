#!/bin/bash
# Instant Capture Hook - NO DELAY for critical conversations

UATP_DIR="/Users/kay/uatp-capsule-engine"
CAPTURE_SCRIPT="$UATP_DIR/capture_this_session.py"
LOG_FILE="$UATP_DIR/instant_capture.log"

echo "[$(date)] INSTANT CAPTURE triggered" >> "$LOG_FILE"

# Run capture immediately in background
(cd "$UATP_DIR" && python3 "$CAPTURE_SCRIPT" >> "$LOG_FILE" 2>&1) &

echo "[$(date)] Capture started in background" >> "$LOG_FILE"
