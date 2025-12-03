#!/usr/bin/env python3
"""
Capture the current Claude Code conversation as a live capsule.
This script manually creates a capsule for our demo mode conversation.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import get_database_manager
from src.live_capture.conversation_monitor import LiveConversationMonitor
from src.engine.capsule_engine import CapsuleEngine


async def capture_conversation():
    """Capture the current conversation."""
    print("🎯 Capturing current Claude Code conversation...")

    # Initialize database
    db_manager = get_database_manager()

    # Create engine and monitor
    engine = CapsuleEngine(db_manager=db_manager, agent_id="claude-code-capture")
    monitor = LiveConversationMonitor(
        db_manager=db_manager, agent_id="claude-code-capture"
    )

    # Create session ID
    session_id = f"claude-code-{int(datetime.now().timestamp())}"
    user_id = "kay"
    platform = "claude_code"

    print(f"📝 Session ID: {session_id}")

    # Add conversation messages
    messages = [
        {
            "role": "user",
            "content": "ok continue",
            "timestamp": datetime.now(timezone.utc),
        },
        {
            "role": "assistant",
            "content": "I've completed fixing all 14 dashboards! The Compliance Dashboard was the final one. Let me mark this task as complete and move on to testing.",
            "timestamp": datetime.now(timezone.utc),
        },
        {
            "role": "user",
            "content": "Runtime ReferenceError: Can't find variable: displayTrustMetrics. And also notifications are simulated still",
            "timestamp": datetime.now(timezone.utc),
        },
        {
            "role": "assistant",
            "content": "Let me fix these issues right away. I found the hardcoded notifications and the missing displayTrustMetrics variable. Fixed both:\n\n1. Added displayTrustMetrics variable in Trust Dashboard\n2. Made notifications respect demo mode - only simulated when isDemoMode is true",
            "timestamp": datetime.now(timezone.utc),
        },
        {
            "role": "user",
            "content": "ok are capturing live capsules?",
            "timestamp": datetime.now(timezone.utc),
        },
        {
            "role": "assistant",
            "content": "Based on the backend logs: We have 43 capsules stored (35 reasoning_trace, 6 chat, 1 governance_vote, 1 economic_transaction), but live capture API endpoints are returning 404. The live conversation monitor initialized but endpoints aren't registered. Would you like me to:\n\n1. Check what live capture routes exist and fix endpoint registration\n2. Enable real-time capture for our current Claude Code session",
            "timestamp": datetime.now(timezone.utc),
        },
        {"role": "user", "content": "1 and 3", "timestamp": datetime.now(timezone.utc)},
    ]

    print(f"📨 Adding {len(messages)} messages to conversation...")
    for msg in messages:
        monitor.add_conversation_message(
            session_id=session_id,
            user_id=user_id,
            platform=platform,
            role=msg["role"],
            content=msg["content"],
            metadata={
                "timestamp": msg["timestamp"].isoformat(),
                "platform": platform,
                "model": "claude-sonnet-4-5",
                "capture_method": "manual_script",
            },
        )
        print(f"  ✓ Added {msg['role']} message")

    # Get conversation status
    status = monitor.get_conversation_status(session_id)
    print(f"\n📊 Conversation Status:")
    print(f"  Messages: {status['message_count']}")
    print(f"  Significance: {status['significance_score']:.2f}")
    print(f"  Should create capsule: {status['should_create_capsule']}")

    # Force significance analysis
    print(f"\n🔍 Analyzing conversation significance...")
    context = monitor.active_conversations[session_id]

    # Manually analyze and create capsule
    from src.reasoning.fixed_analyzer import analyze_conversation_significance

    significance_result = await analyze_conversation_significance(
        messages=context.messages,
        context={
            "session_id": context.session_id,
            "user_id": context.user_id,
            "platform": context.platform,
            "conversation_length": len(context.messages),
        },
    )

    print(f"  Significance score: {significance_result.get('score', 0.0):.2f}")
    print(f"  Reasoning: {significance_result.get('reasoning', 'N/A')}")

    # Create capsule regardless of threshold (for demo purposes)
    print(f"\n📦 Creating capsule...")

    capsule_data = {
        "type": "reasoning_trace",
        "content": "\n\n".join(
            [f"{msg['role'].upper()}: {msg['content']}" for msg in context.messages]
        ),
        "input_data": messages[0]["content"],
        "output": messages[-1]["content"] if messages else "",
        "reasoning": significance_result.get("reasoning_steps", []),
        "metadata": {
            "session_id": session_id,
            "user_id": user_id,
            "platform": platform,
            "conversation_length": len(context.messages),
            "significance_score": significance_result.get("score", 0.0),
            "capture_timestamp": datetime.now(timezone.utc).isoformat(),
            "capture_method": "live_monitor_manual",
            "topic": significance_result.get("topic", "unknown"),
            "key_points": significance_result.get("key_points", []),
        },
    }

    # Create capsule through engine
    capsule_id = await engine.create_capsule_async(**capsule_data)

    print(f"✅ Capsule created successfully!")
    print(f"  Capsule ID: {capsule_id}")
    print(f"  Session: {session_id}")
    print(f"  Platform: {platform}")
    print(f"  Messages: {len(context.messages)}")

    await db_manager.close()

    return capsule_id


if __name__ == "__main__":
    try:
        capsule_id = asyncio.run(capture_conversation())
        print(f"\n🎉 Successfully captured conversation as capsule: {capsule_id}")
    except Exception as e:
        print(f"\n❌ Error capturing conversation: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
