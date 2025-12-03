#!/usr/bin/env python3
"""
Direct test of monitor functionality - bypass API to test core logic.
"""

import sys
import os
import asyncio
from datetime import datetime

# Add path for imports
sys.path.append("/Users/kay/uatp-capsule-engine/src")

from live_capture.conversation_monitor import get_monitor


async def test_monitor_directly():
    """Test monitor functionality directly."""

    print("🧪 Direct Monitor Test")
    print("=" * 50)

    # Get monitor instance
    monitor = get_monitor()
    print(f"Monitor instance: {monitor}")
    print(f"Initial active conversations: {len(monitor.active_conversations)}")

    session_id = f"direct-test-{int(datetime.now().timestamp())}"

    # Add messages directly
    print(f"\\n📝 Adding messages to session: {session_id}")

    # Message 1: User
    monitor.add_conversation_message(
        session_id=session_id,
        user_id="kay",
        platform="claude_code",
        role="user",
        content="I need help with the UATP (Universal Attribution and Trust Protocol) conversation capture system. The significance analyzer isn't working properly.",
    )

    print(f"After message 1: {len(monitor.active_conversations)} conversations")

    # Message 2: Assistant
    monitor.add_conversation_message(
        session_id=session_id,
        user_id="kay",
        platform="claude_code",
        role="assistant",
        content="I can help you debug the UATP significance analyzer. Let me examine the conversation monitor and reasoning pipeline to identify why technical discussions about the Universal Attribution and Trust Protocol aren't being scored correctly.",
    )

    print(f"After message 2: {len(monitor.active_conversations)} conversations")

    # Check the conversation context
    if session_id in monitor.active_conversations:
        context = monitor.active_conversations[session_id]
        print(f"\\n📊 Conversation Context:")
        print(f"   Session ID: {context.session_id}")
        print(f"   Messages: {len(context.messages)}")
        print(f"   Current significance: {context.significance_score}")
        print(f"   Should create capsule: {context.should_create_capsule}")

        # Manually run significance analysis
        print(f"\\n🔍 Running significance analysis manually...")

        try:
            from reasoning.analyzer import analyze_conversation_significance

            # Analyze significance
            significance_result = await analyze_conversation_significance(
                messages=context.messages,
                context={
                    "session_id": context.session_id,
                    "user_id": context.user_id,
                    "platform": context.platform,
                    "conversation_length": len(context.messages),
                },
            )

            score = significance_result.get("score", 0.0)
            factors = significance_result.get("factors", [])

            print(f"   📈 Significance Score: {score:.3f}")
            print(f"   🎯 Factors: {factors}")

            # Update context
            context.significance_score = score
            context.should_create_capsule = score >= monitor.significance_threshold

            print(f"   ✅ Updated context:")
            print(f"      Significance: {context.significance_score:.3f}")
            print(f"      Should create capsule: {context.should_create_capsule}")
            print(f"      Threshold: {monitor.significance_threshold}")

            if score >= 0.6:
                print(
                    f"\\n🎉 SUCCESS! Direct monitor test shows significance analysis works!"
                )
            else:
                print(f"\\n⚠️  Issue: Score {score:.3f} < 0.6 threshold")

        except Exception as e:
            print(f"   ❌ Analysis error: {e}")
            import traceback

            traceback.print_exc()
    else:
        print(f"\\n❌ Session {session_id} not found in active conversations!")

    print(f"\\n📊 Final monitor state:")
    print(f"   Active conversations: {len(monitor.active_conversations)}")
    for sid, ctx in monitor.active_conversations.items():
        print(
            f"   {sid}: {len(ctx.messages)} msgs, score: {ctx.significance_score:.3f}"
        )


if __name__ == "__main__":
    asyncio.run(test_monitor_directly())
