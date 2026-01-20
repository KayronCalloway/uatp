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

from src.live_capture.claude_code_capture import ClaudeCodeCapture  # noqa: E402


async def capture_rich_session():
    """Capture current Claude Code session with RICH metadata."""

    capture = ClaudeCodeCapture()

    # Read user message from stdin (provided by hook)
    user_message = ""
    if not sys.stdin.isatty():
        try:
            user_message = sys.stdin.read().strip()
        except Exception:
            pass

    # Get or create persistent session
    session_file = Path("/tmp/claude_code_active_session.json")
    session_id = None

    try:
        if session_file.exists():
            with open(session_file) as f:
                session_data = json.load(f)
                session_id = session_data.get("session_id")
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

    # Capture recent assistant responses from Claude Code conversation transcript
    try:
        # Find the conversation transcript file
        # Convert current working directory to Claude project format
        import os

        cwd = os.getcwd()
        project_name = cwd.replace("/", "-")
        if project_name.startswith("-"):
            project_name = project_name  # Keep leading dash
        project_dir = Path.home() / ".claude" / "projects" / project_name
        transcript_files = sorted(
            project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
        )

        if transcript_files:
            transcript_file = transcript_files[0]  # Most recent

            # Read last N lines to find recent assistant responses
            with open(transcript_file) as f:
                lines = f.readlines()

            # Get assistant responses from last 20 lines
            recent_assistant_responses = []
            for line in lines[-20:]:
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "assistant":
                        content = entry.get("message", {}).get("content", [])
                        # Extract text content from the message
                        text_parts = []
                        if isinstance(content, list):
                            for part in content:
                                if isinstance(part, dict):
                                    if part.get("type") == "text":
                                        text_parts.append(part.get("text", ""))
                                elif isinstance(part, str):
                                    text_parts.append(part)
                        elif isinstance(content, str):
                            text_parts.append(content)

                        if text_parts:
                            combined_text = " ".join(text_parts)
                            if len(combined_text) > 50:  # Skip very short responses
                                recent_assistant_responses.append(combined_text)
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue

            # Capture the most recent assistant response if not already captured
            if recent_assistant_responses:
                assistant_response = recent_assistant_responses[-1]

                # Only capture if it's new (check against last captured)
                last_captured = session_data.get("last_assistant_response", "")[:100]
                if assistant_response[:100] != last_captured:
                    await capture.capture_message(
                        session_id=session_id,
                        role="assistant",
                        content=assistant_response[:10000],  # Limit size
                        token_count=int(len(assistant_response.split()) * 1.3),
                        model_info="claude-opus-4-5",
                    )
                    session_data["message_count"] += 1
                    session_data["last_assistant_response"] = assistant_response[:100]
                    print(
                        f"✅ Captured assistant response ({len(assistant_response)} chars)"
                    )

    except Exception as e:
        print(f"⚠️ Assistant capture skipped: {e}")

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
