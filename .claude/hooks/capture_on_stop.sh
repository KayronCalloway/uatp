#!/bin/bash
# Claude Code Stop Hook - Captures assistant response after generation
# This hook fires AFTER Claude finishes responding, receiving the full response

UATP_API="${UATP_API_URL:-http://localhost:8000}"
LOG_FILE="/Users/kay/uatp-capsule-engine/hook_capture.log"
SESSION_FILE="/tmp/claude_code_session.json"
DEBUG_LOG="/tmp/hook_debug.log"

# Log hook invocation
echo "[$(date)] Stop hook invoked" >> "$DEBUG_LOG"

# Read JSON input from stdin (includes last_assistant_message)
INPUT_JSON=$(cat)
echo "[$(date)] Stop hook input: ${INPUT_JSON:0:300}..." >> "$DEBUG_LOG"

# Extract assistant message from JSON
ASSISTANT_MESSAGE=$(echo "$INPUT_JSON" | jq -r '.last_assistant_message // empty' 2>/dev/null)

# Exit if no assistant message
if [ -z "$ASSISTANT_MESSAGE" ]; then
    echo "[$(date)] Stop hook: No assistant message" >> "$DEBUG_LOG"
    exit 0
fi

# Skip very short responses (likely just tool calls)
MSG_LENGTH=${#ASSISTANT_MESSAGE}
if [ "$MSG_LENGTH" -lt 50 ]; then
    echo "[$(date)] Stop hook: Skipping short response ($MSG_LENGTH chars)" >> "$DEBUG_LOG"
    exit 0
fi

echo "[$(date)] Stop hook: Capturing assistant response ($MSG_LENGTH chars)" >> "$DEBUG_LOG"

# Get session ID (same as UserPromptSubmit hook)
SESSION_ID=""
if [ -f "$SESSION_FILE" ]; then
    SESSION_ID=$(jq -r '.session_id' "$SESSION_FILE" 2>/dev/null || echo "")
fi

if [ -z "$SESSION_ID" ]; then
    SESSION_ID="claude-code-$(date +%s)-$$"
    echo "{\"session_id\": \"$SESSION_ID\", \"started\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > "$SESSION_FILE"
fi

# Truncate very long responses for the API
TRUNCATED_MESSAGE="${ASSISTANT_MESSAGE:0:15000}"

# Create JSON payload for assistant message
PAYLOAD=$(jq -n \
    --arg sid "$SESSION_ID" \
    --arg uid "${USER:-unknown}" \
    --arg msg "$TRUNCATED_MESSAGE" \
    --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{
        session_id: $sid,
        user_id: $uid,
        platform: "claude-code",
        role: "assistant",
        content: $msg,
        metadata: {
            capture_method: "stop_hook",
            timestamp: $ts,
            original_length: ($msg | length)
        }
    }')

# Post to FastAPI endpoint
echo "[$(date)] Sending assistant response to $UATP_API/live/capture/message" >> "$DEBUG_LOG"

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$UATP_API/live/capture/message" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE:")

# Log result
echo "[$(date)] Captured assistant response to session $SESSION_ID ($MSG_LENGTH chars)" >> "$LOG_FILE"
echo "[$(date)] Response (HTTP $HTTP_CODE): $BODY" >> "$DEBUG_LOG"

if [ "$HTTP_CODE" != "200" ]; then
    echo "[$(date)] ERROR: HTTP $HTTP_CODE" >> "$DEBUG_LOG"
fi

exit 0
