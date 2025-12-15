#!/usr/bin/env python3
"""
Rich Claude Code Hook Capture
Captures full conversation context with maximum metadata richness
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Load environment
from dotenv import load_dotenv

load_dotenv()

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from src.live_capture.claude_code_capture import ClaudeCodeCapture


async def capture_rich_session():
    """Capture current Claude Code session with RICH metadata."""

    capture = ClaudeCodeCapture()

    # Read user message from stdin (provided by hook)
    user_message = ""
    if not sys.stdin.isatty():
        try:
            user_message = sys.stdin.read().strip()
        except:
            pass

    # Get or create persistent session
    session_file = Path("/tmp/claude_code_active_session.json")
    session_id = None

    try:
        if session_file.exists():
            with open(session_file) as f:
                session_data = json.load(f)
                session_id = session_data.get("session_id")
                message_count = session_data.get("message_count", 0)
        else:
            # Start new session
            session_id = await capture.start_session(user_id="kay")
            session_data = {
                "session_id": session_id,
                "message_count": 0,
                "started": datetime.now(timezone.utc).isoformat(),
            }
    except Exception as e:
        print(f"⚠️  Session file error: {e}, creating new session")
        session_id = await capture.start_session(user_id="kay")
        session_data = {
            "session_id": session_id,
            "message_count": 0,
            "started": datetime.now(timezone.utc).isoformat(),
        }

    # Capture user message with rich metadata
    if user_message:
        try:
            # Analyze message complexity for token estimation
            estimated_tokens = len(user_message.split()) * 1.3  # Rough estimate

            await capture.capture_message(
                session_id=session_id,
                role="user",
                content=user_message,
                token_count=int(estimated_tokens),
                model_info="claude-sonnet-4.5",
            )

            session_data["message_count"] += 1
            session_data["last_user_message"] = user_message[:100]

            print(f"✅ Captured user message (session: {session_id[:8]}...)")
            print(f"   Message #{session_data['message_count']}")
            print(f"   Tokens: ~{int(estimated_tokens)}")

        except Exception as e:
            print(f"❌ Failed to capture user message: {e}")

    # Try to capture recent assistant response from conversation history
    # (This would require Claude Code API access - for now we'll note the limitation)
    try:
        # Attempt to read from Claude Code's conversation cache if available
        # This is a placeholder for future integration
        assistant_response = None  # Would fetch from Claude Code session

        if assistant_response:
            await capture.capture_message(
                session_id=session_id,
                role="assistant",
                content=assistant_response,
                token_count=len(assistant_response.split()) * 1.3,
                model_info="claude-sonnet-4.5",
            )
            session_data["message_count"] += 1

    except Exception:
        pass  # Assistant capture is optional for now

    # Every 10 messages, create a checkpoint capsule
    if (
        session_data.get("message_count", 0) % 10 == 0
        and session_data.get("message_count", 0) > 0
    ):
        try:
            # Get the session from active sessions
            if session_id in capture.active_sessions:
                session = capture.active_sessions[session_id]

                # Create intermediate capsule with RICH metadata
                capsule_id = await capture.create_capsule_from_session(session)

                if capsule_id:
                    print(f"🔥 Created RICH checkpoint capsule: {capsule_id}")
                    print(f"   Messages: {len(session.messages)}")
                    print(f"   Significance: {session.significance_score:.2f}")
                    print(f"   Topics: {', '.join(session.topics)}")

        except Exception as e:
            print(f"⚠️  Checkpoint capsule creation skipped: {e}")

    # Update session file
    try:
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)
    except Exception as e:
        print(f"⚠️  Could not save session state: {e}")

    # Show session stats
    print(f"📊 Session: {session_id[:16]}...")
    print(f"   Total messages: {session_data.get('message_count', 0)}")
    print(f"   Duration: Active since {session_data.get('started', 'unknown')[:19]}")


async def end_session_and_create_capsule():
    """Manually end session and create final capsule."""

    session_file = Path("/tmp/claude_code_active_session.json")

    if not session_file.exists():
        print("⚠️  No active session found")
        return

    try:
        with open(session_file) as f:
            session_data = json.load(f)
            session_id = session_data.get("session_id")

        if not session_id:
            print("❌ Invalid session data")
            return

        capture = ClaudeCodeCapture()

        # End the session
        session = await capture.end_session(session_id)

        if session:
            # Create final RICH capsule
            capsule_id = await capture.create_capsule_from_session(session)

            if capsule_id:
                print(f"✨ Created final RICH capsule: {capsule_id}")
                print(f"   Messages: {len(session.messages)}")
                print(f"   Significance: {session.significance_score:.2f}")
                print(f"   Topics: {', '.join(session.topics)}")
                print(f"   Duration: {session.start_time} - {session.end_time}")
            else:
                print("ℹ️  Session didn't meet capsule criteria")
                print(f"   Messages: {len(session.messages)}")
                print(f"   Significance: {session.significance_score:.2f}")

        # Remove session file
        session_file.unlink()
        print("🧹 Session ended and cleaned up")

    except Exception as e:
        print(f"❌ Error ending session: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Check if we should end the session (via command line flag)
    if len(sys.argv) > 1 and sys.argv[1] == "--end-session":
        asyncio.run(end_session_and_create_capsule())
    else:
        # Normal capture
        asyncio.run(capture_rich_session())
