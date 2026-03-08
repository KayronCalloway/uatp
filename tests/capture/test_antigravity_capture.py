#!/usr/bin/env python3
"""
Test Antigravity Capture - Captures This Current Conversation
=============================================================

This script tests the Antigravity capture by creating a capsule from
the current conversation session.
"""

import asyncio
import os
import sqlite3
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.live_capture import (
    get_antigravity_capture,
)


async def capture_this_conversation():
    """Capture the current Antigravity conversation."""

    print(" Antigravity Conversation Capture Test")
    print("=" * 60)

    # Current conversation session ID
    session_id = "8068748a-1dea-4e5c-9b1d-b3e84dd584fc"

    # Initialize capture with this session
    capture = get_antigravity_capture(
        user_id="kay",
        session_id=f"antigravity_{session_id[:8]}",
        model="gemini-2.5-pro",
    )

    print(f" Session ID: {capture.session_id}")
    print(f" User ID: {capture.user_id}")
    print(f" Model: {capture.model}")
    print()

    # Capture the key exchanges from this conversation
    exchanges = [
        {
            "user": "ok ive made plenty changes since we last integrated. but what i want you to do is help me capture all of the conversations for ruatp through this wrapper that im using (google's antigravity) i need it to capture at the detail that i capture for claude code that i set up before you do anything are you able to do that",
            "assistant": "I understand you want me to help set up conversation capture for RUATP through Google's Antigravity wrapper, matching the detail level you already have for Claude Code. Before implementing anything, let me first explore your current Claude Code conversation capture setup to understand the pattern.",
            "type": "agentic_coding",
            "mode": "PLANNING",
        },
        {
            "user": "i am talking to you through antigravity. i want to be able to capture all the detail for uatp here through all the different llm's as i do through claude code",
            "assistant": "I understand now - you're talking to me (Gemini via Antigravity) and you want the same conversation capture detail that you have for Claude Code, but for all LLMs including this Antigravity/Gemini session. Since I'm running inside Antigravity, I can help build this. The key insight is that while the .pb files are binary, I can create a capture system that hooks into the conversation as it happens.",
            "type": "agentic_coding",
            "mode": "PLANNING",
        },
        {
            "user": "the most recent claude code work is the reference",
            "assistant": "Understood - I'll reference the most recent Claude Code work. Reviewed claude_code_auto_capture.py and claude_code_integration.py as the reference implementations with session-based capture, significance analysis, and rich metadata.",
            "type": "agentic_coding",
            "mode": "EXECUTION",
        },
        {
            "user": "and please send the information to the same place that claude code is being sent as far as the database",
            "assistant": "Fixed database path to match Claude Code's path exactly - both now use live_capture.db in the project root. Created antigravity_hook.py, updated antigravity_capture_integration.py, and added exports to __init__.py.",
            "type": "agentic_coding",
            "mode": "EXECUTION",
        },
    ]

    print(f" Capturing {len(exchanges)} conversation exchanges...")
    print()

    capsule_ids = []
    for i, exchange in enumerate(exchanges, 1):
        print(f"Exchange {i}: {exchange['type']} ({exchange['mode']})")
        print(f"  User: {exchange['user'][:60]}...")
        print(f"  Assistant: {exchange['assistant'][:60]}...")

        capsule_id = await capture.capture_antigravity_interaction(
            user_input=exchange["user"],
            assistant_response=exchange["assistant"],
            interaction_type=exchange["type"],
            task_mode=exchange["mode"],
            workspace_context="/Users/kay/uatp-capsule-engine",
            artifacts_created=["task.md", "implementation_plan.md"] if i == 2 else None,
        )

        if capsule_id:
            capsule_ids.append(capsule_id)
            print(f"  [OK] Capsule created: {capsule_id}")
        else:
            print("   Captured (no capsule threshold met)")
        print()

    # Show session stats
    stats = capture.get_session_stats()
    print(" Session Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Check the database
    print()
    print(" Checking live_capture.db...")
    db_path = os.path.join(os.path.dirname(__file__), "live_capture.db")

    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check sessions
        cursor.execute("SELECT COUNT(*) FROM capture_sessions")
        session_count = cursor.fetchone()[0]
        print(f"   Total sessions: {session_count}")

        # Check messages
        cursor.execute("SELECT COUNT(*) FROM capture_messages")
        message_count = cursor.fetchone()[0]
        print(f"   Total messages: {message_count}")

        # Show recent sessions
        cursor.execute(
            """
            SELECT session_id, platform, message_count, start_time
            FROM capture_sessions
            ORDER BY start_time DESC
            LIMIT 5
        """
        )
        recent = cursor.fetchall()
        print()
        print("   Recent sessions:")
        for row in recent:
            print(f"     - {row[0][:20]}... ({row[1]}) - {row[2]} messages")

        conn.close()
    else:
        print(f"   [WARN] Database not found at {db_path}")

    print()
    print("=" * 60)
    print("[OK] Antigravity capture test complete!")
    print(f"   Capsules created: {len(capsule_ids)}")
    print(f"   Total exchanges captured: {len(exchanges)}")

    return capsule_ids


if __name__ == "__main__":
    asyncio.run(capture_this_conversation())
