#!/usr/bin/env python3
"""
Capture Assistant Response - Stop Hook Handler
Captures Claude's response after generation completes.

This script receives JSON input from the Claude Code Stop hook:
{
    "session_id": "abc123",
    "transcript_path": "/path/to/transcript.jsonl",
    "last_assistant_message": "Claude's full response text"
}
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Load environment and add project to path before local imports
load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from src.live_capture.claude_code_capture import ClaudeCodeCapture  # noqa: E402


async def capture_assistant_response() -> None:
    """Capture the assistant response from Stop hook input."""

    # Read JSON input from stdin
    input_json = ""
    if not sys.stdin.isatty():
        try:
            input_json = sys.stdin.read().strip()
        except Exception:
            pass

    if not input_json:
        print("No input received from Stop hook")
        return

    try:
        hook_data = json.loads(input_json)
    except json.JSONDecodeError as e:
        print(f"Failed to parse hook input: {e}")
        return

    # Extract assistant response (session_id and transcript_path available but not used)
    assistant_message = hook_data.get("last_assistant_message", "")

    if not assistant_message:
        print("No assistant message in hook data")
        return

    # Skip very short responses (likely just tool calls)
    if len(assistant_message) < 50:
        print(f"Skipping short response ({len(assistant_message)} chars)")
        return

    capture = ClaudeCodeCapture()

    # Get or create persistent session
    session_file = Path("/tmp/claude_code_active_session.json")
    session_id = None
    session_data = {}

    try:
        if session_file.exists():
            with open(session_file) as f:
                session_data = json.load(f)
                session_id = session_data.get("session_id")

        if not session_id:
            # Start new session if none exists
            session_id = await capture.start_session(user_id="kay")
            session_data = {
                "session_id": session_id,
                "message_count": 0,
                "started": datetime.now(timezone.utc).isoformat(),
            }
    except Exception as e:
        print(f"Session file error: {e}, creating new session")
        session_id = await capture.start_session(user_id="kay")
        session_data = {
            "session_id": session_id,
            "message_count": 0,
            "started": datetime.now(timezone.utc).isoformat(),
        }

    # Check if this response was already captured
    last_captured = session_data.get("last_assistant_response", "")[:100]
    if assistant_message[:100] == last_captured:
        print("Response already captured, skipping")
        return

    # Capture the assistant response
    try:
        estimated_tokens = int(len(assistant_message.split()) * 1.3)

        await capture.capture_message(
            session_id=session_id,
            role="assistant",
            content=assistant_message[:15000],  # Limit size
            token_count=estimated_tokens,
            model_info="claude-opus-4-5",
        )

        session_data["message_count"] = session_data.get("message_count", 0) + 1
        session_data["last_assistant_response"] = assistant_message[:100]
        session_data["last_assistant_captured_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        print(
            f"Captured assistant response ({len(assistant_message)} chars, ~{estimated_tokens} tokens)"
        )
        print(f"   Session: {session_id[:16]}...")

        # Update session file
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)

    except Exception as e:
        print(f"Failed to capture assistant response: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(capture_assistant_response())
