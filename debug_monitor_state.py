#!/usr/bin/env python3
"""
Debug the monitor state and fix the analysis pipeline.
"""

import requests
import json
import sys
import os
import asyncio
from datetime import datetime

# Add path for imports
sys.path.append("/Users/kay/uatp-capsule-engine/src")

from live_capture.conversation_monitor import get_monitor, _monitor_instance


async def debug_and_fix_monitor():
    """Debug the monitor state and manually fix significance scoring."""

    print("🔍 Debugging Monitor State")
    print("=" * 50)

    # Check global monitor instance
    print(f"Global monitor instance: {_monitor_instance}")

    # Get the API's monitor
    api_monitor = get_monitor()
    print(f"API monitor: {api_monitor}")
    print(
        f"Active conversations in API monitor: {len(api_monitor.active_conversations)}"
    )

    if api_monitor.active_conversations:
        print("\\n📝 Conversations in API monitor:")
        for session_id, context in api_monitor.active_conversations.items():
            print(f"   {session_id}: {len(context.messages)} messages")

    # Get conversations from API to see what should be there
    api_base = "http://localhost:9090"
    headers = {"X-API-Key": "dev-key-001"}

    response = requests.get(
        f"{api_base}/api/v1/live/capture/conversations", headers=headers
    )
    if response.ok:
        data = response.json()
        api_conversations = data.get("conversations", [])
        print(f"\\n🌐 API shows {len(api_conversations)} conversations:")

        for conv in api_conversations:
            session_id = conv["session_id"]
            message_count = conv["message_count"]
            current_score = conv["significance_score"]
            print(
                f"   {session_id[:30]}... → {message_count} msgs, score: {current_score}"
            )

            # Check if this conversation exists in the monitor
            if session_id in api_monitor.active_conversations:
                context = api_monitor.active_conversations[session_id]
                print(f"     ✅ Found in monitor: {len(context.messages)} messages")

                # Manually analyze this conversation
                if len(context.messages) > 0:
                    print(f"     🔄 Running significance analysis...")

                    try:
                        from reasoning.analyzer import analyze_conversation_significance

                        # Analyze significance
                        recent_messages = context.messages[-5:]  # Last 5 messages
                        significance_result = await analyze_conversation_significance(
                            messages=recent_messages,
                            context={
                                "session_id": context.session_id,
                                "user_id": context.user_id,
                                "platform": context.platform,
                                "conversation_length": len(context.messages),
                            },
                        )

                        # Get the score
                        score = significance_result.get("score", 0.0)
                        factors = significance_result.get("factors", [])

                        print(f"     📊 Analyzer returned: {score:.3f}")
                        print(f"     🎯 Factors: {factors}")

                        # Update the context
                        context.significance_score = score
                        context.should_create_capsule = (
                            score >= api_monitor.significance_threshold
                        )

                        print(
                            f"     ✅ Updated context: score={context.significance_score:.3f}, should_create={context.should_create_capsule}"
                        )

                    except Exception as e:
                        print(f"     ❌ Analysis error: {e}")
                        import traceback

                        traceback.print_exc()
            else:
                print(f"     ❌ Not found in monitor - this is the problem!")

    print(f"\\n🎯 Manual Analysis Complete")

    # Check API again to see if scores updated
    print(f"\\n🔄 Checking API again...")
    response2 = requests.get(
        f"{api_base}/api/v1/live/capture/conversations", headers=headers
    )
    if response2.ok:
        data2 = response2.json()
        updated_conversations = data2.get("conversations", [])
        print(f"📊 Updated API Results:")

        for conv in updated_conversations:
            score = conv["significance_score"]
            session = conv["session_id"][:30]
            should_create = conv["should_create_capsule"]
            print(
                f"   {session}... → Score: {score:.3f}, Create: {should_create} ({'✅ HIGH' if score >= 0.6 else '⚠️ LOW'})"
            )


if __name__ == "__main__":
    asyncio.run(debug_and_fix_monitor())
