#!/usr/bin/env python3
"""
Manually trigger significance analysis for active conversations.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Add path for imports
sys.path.append("/Users/kay/uatp-capsule-engine/src")

from live_capture.conversation_monitor import get_monitor


def trigger_analysis():
    """Manually trigger significance analysis for all active conversations."""

    print("🔄 Manually Triggering Significance Analysis")
    print("=" * 50)

    # Get the monitor instance (same one the API uses)
    monitor = get_monitor()

    print(f"📊 Active conversations: {len(monitor.active_conversations)}")

    # Process each active conversation
    for session_id, context in monitor.active_conversations.items():
        print(f"\\n🔍 Analyzing conversation: {session_id[:30]}...")
        print(f"   Messages: {len(context.messages)}")
        print(f"   Current significance: {context.significance_score}")

        try:
            # Import the async function
            import asyncio
            from reasoning.analyzer import analyze_conversation_significance

            # Manually run the significance analysis
            async def run_analysis():
                # Get recent messages for analysis
                recent_messages = context.messages[-5:]  # Last 5 messages

                # Call the analyzer
                significance_result = await analyze_conversation_significance(
                    messages=recent_messages,
                    context={
                        "session_id": context.session_id,
                        "user_id": context.user_id,
                        "platform": context.platform,
                        "conversation_length": len(context.messages),
                    },
                )

                print(f"   📈 Analyzer result:")
                print(f"      Score: {significance_result.get('score', 'NOT_FOUND')}")
                print(
                    f"      Confidence: {significance_result.get('confidence', 'NOT_FOUND')}"
                )
                print(f"      Factors: {significance_result.get('factors', [])}")

                # Update the context
                context.significance_score = significance_result.get("score", 0.0)
                context.should_create_capsule = (
                    context.significance_score >= monitor.significance_threshold
                )

                print(f"   ✅ Updated significance: {context.significance_score:.3f}")
                print(f"   ✅ Should create capsule: {context.should_create_capsule}")

            # Run the async analysis
            asyncio.run(run_analysis())

        except Exception as e:
            print(f"   ❌ Error analyzing conversation: {e}")
            import traceback

            traceback.print_exc()

    print(f"\\n🎯 Analysis Complete!")

    # Show updated status via API
    api_base = "http://localhost:9090"
    headers = {"X-API-Key": "dev-key-001"}

    response = requests.get(
        f"{api_base}/api/v1/live/capture/conversations", headers=headers
    )
    if response.ok:
        data = response.json()
        conversations = data.get("conversations", [])

        print(f"\\n📊 Updated API Results:")
        for conv in conversations:
            score = conv["significance_score"]
            session = conv["session_id"][:30]
            print(
                f"   {session}... → Score: {score:.3f} ({'✅ HIGH' if score >= 0.6 else '⚠️ LOW'})"
            )
    else:
        print(f"\\n❌ Failed to get API status: {response.status_code}")


if __name__ == "__main__":
    trigger_analysis()
