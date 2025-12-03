#!/usr/bin/env python3
"""
Trigger significance analysis via the API itself using a custom endpoint.
"""

import requests
import json
import time
from datetime import datetime


def create_and_analyze_conversation():
    """Create a conversation and trigger immediate analysis."""

    api_base = "http://localhost:9090"
    headers = {"X-API-Key": "dev-key-001", "Content-Type": "application/json"}

    session_id = f"immediate-analysis-{int(datetime.now().timestamp())}"

    print("🚀 Creating Conversation with Immediate Analysis")
    print("=" * 60)
    print(f"Session ID: {session_id}")

    # Create a high-value UATP conversation
    messages = [
        {
            "session_id": session_id,
            "user_id": "kay",
            "platform": "claude_code",
            "role": "user",
            "content": "I'm debugging the UATP (Universal Attribution and Trust Protocol) significance analyzer. The conversation capture system should score technical discussions about the capsule engine at 0.6+ but it's returning 0.0. This is a critical issue with the live capture API endpoints.",
            "metadata": {"test": "high_significance_uatp"},
        },
        {
            "session_id": session_id,
            "user_id": "kay",
            "platform": "claude_code",
            "role": "assistant",
            "content": "I can help fix the UATP significance analyzer issue. The problem is likely in the conversation monitor's integration with the reasoning analyzer. Let me examine the live capture routes and significance scoring pipeline to identify why technical conversations about Universal Attribution and Trust Protocol aren't triggering proper capsule creation.",
            "metadata": {"test": "technical_response"},
        },
    ]

    # Send all messages
    for i, message in enumerate(messages, 1):
        response = requests.post(
            f"{api_base}/api/v1/live/capture/message", headers=headers, json=message
        )
        status = "✅" if response.ok else "❌"
        print(f"Message {i}: {status} {message['role']} - {response.status_code}")
        time.sleep(0.5)

    # Wait a moment
    print("\\n⏳ Waiting for processing...")
    time.sleep(2)

    # Check initial status
    response = requests.get(
        f"{api_base}/api/v1/live/capture/conversations", headers=headers
    )
    if response.ok:
        data = response.json()
        conversations = data.get("conversations", [])

        target_conv = None
        for conv in conversations:
            if conv["session_id"] == session_id:
                target_conv = conv
                break

        if target_conv:
            print(f"\\n📊 Initial Conversation Status:")
            print(f"   Messages: {target_conv['message_count']}")
            print(f"   Significance: {target_conv['significance_score']:.3f}")
            print(f"   Should Create Capsule: {target_conv['should_create_capsule']}")

            if target_conv["significance_score"] == 0.0:
                print(
                    f"\\n🔧 Score is 0.0 - this confirms the API monitor isn't running analysis"
                )
                print(f"   This means the background monitoring loop isn't started")
                print(f"   OR the should_check_conversation method isn't triggering")
            else:
                print(
                    f"\\n🎉 SUCCESS! API analysis is working with score {target_conv['significance_score']:.3f}"
                )
        else:
            print(f"\\n❌ Conversation {session_id} not found in API response")

    # Now let's try to force trigger analysis by accessing the conversation multiple times
    print(f"\\n🔄 Attempting to trigger analysis by repeated access...")

    for attempt in range(3):
        print(f"   Attempt {attempt + 1}...")

        # Get conversation status (this should trigger the monitor check)
        status_response = requests.get(
            f"{api_base}/api/v1/live/capture/conversation/{session_id}", headers=headers
        )

        if status_response.ok:
            conv_data = status_response.json()
            if conv_data.get("success"):
                conversation = conv_data.get("conversation", {})
                score = conversation.get("significance_score", 0.0)
                print(f"      Status check: Score = {score:.3f}")
            else:
                print(
                    f"      Status check failed: {conv_data.get('error', 'Unknown error')}"
                )

        time.sleep(1)

    # Final check
    print(f"\\n🎯 Final Status Check:")
    final_response = requests.get(
        f"{api_base}/api/v1/live/capture/conversations", headers=headers
    )
    if final_response.ok:
        final_data = final_response.json()
        final_conversations = final_data.get("conversations", [])

        for conv in final_conversations:
            if conv["session_id"] == session_id:
                score = conv["significance_score"]
                should_create = conv["should_create_capsule"]

                print(f"   Session: {session_id[:30]}...")
                print(f"   Final Score: {score:.3f}")
                print(f"   Should Create Capsule: {should_create}")

                if score >= 0.6:
                    print(f"   ✅ SUCCESS! High significance detected")
                else:
                    print(f"   ⚠️  Issue: Score still {score:.3f} < 0.6")
                    print(
                        f"   💡 This suggests the monitor's background loop isn't running"
                    )
                break


if __name__ == "__main__":
    create_and_analyze_conversation()
