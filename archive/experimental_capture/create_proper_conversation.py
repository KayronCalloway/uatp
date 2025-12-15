#!/usr/bin/env python3
"""
Create a proper multi-message conversation to test significance analysis.
"""

import time
from datetime import datetime

import requests


def create_conversation():
    """Create a proper conversation with multiple messages."""

    api_base = "http://localhost:9090"
    headers = {"X-API-Key": "dev-key-001", "Content-Type": "application/json"}

    session_id = f"proper-uatp-conversation-{int(datetime.now().timestamp())}"

    print("🔄 Creating Proper UATP Conversation")
    print("=" * 50)
    print(f"Session ID: {session_id}")

    # Message 1: User starts conversation about UATP
    message1 = {
        "session_id": session_id,
        "user_id": "kay",
        "platform": "claude_code",
        "role": "user",
        "content": "I'm having issues with the UATP (Universal Attribution and Trust Protocol) conversation capture system. The significance analyzer is returning 0.0 scores for technical conversations that should be getting 0.6+ scores.",
        "metadata": {"step": 1},
    }

    response1 = requests.post(
        f"{api_base}/api/v1/live/capture/message", headers=headers, json=message1
    )
    print(
        f"Message 1: {'✅' if response1.ok else '❌'} User message - {response1.status_code}"
    )

    time.sleep(1)

    # Message 2: Assistant responds with technical analysis
    message2 = {
        "session_id": session_id,
        "user_id": "kay",
        "platform": "claude_code",
        "role": "assistant",
        "content": "I can help you debug the UATP significance analyzer. Let me examine the current implementation to identify why technical conversations about the Universal Attribution and Trust Protocol aren't being scored properly. The issue likely involves the pattern matching algorithms in the reasoning analyzer module.",
        "metadata": {"step": 2},
    }

    response2 = requests.post(
        f"{api_base}/api/v1/live/capture/message", headers=headers, json=message2
    )
    print(
        f"Message 2: {'✅' if response2.ok else '❌'} Assistant message - {response2.status_code}"
    )

    time.sleep(1)

    # Message 3: User provides more technical details
    message3 = {
        "session_id": session_id,
        "user_id": "kay",
        "platform": "claude_code",
        "role": "user",
        "content": "The problem is in the conversation monitor and significance scoring pipeline. I've modified the analyzer.py file to include UATP-specific patterns, but the API endpoints are still returning 0.0 significance scores. The capsule creation threshold is 0.6, so conversations about the capsule engine and live capture system should easily exceed this.",
        "metadata": {"step": 3},
    }

    response3 = requests.post(
        f"{api_base}/api/v1/live/capture/message", headers=headers, json=message3
    )
    print(
        f"Message 3: {'✅' if response3.ok else '❌'} User technical details - {response3.status_code}"
    )

    time.sleep(1)

    # Message 4: Assistant provides implementation solution
    message4 = {
        "session_id": session_id,
        "user_id": "kay",
        "platform": "claude_code",
        "role": "assistant",
        "content": "The issue is likely in the conversation monitor's analyze_conversation_significance method. The UATP patterns should trigger high scores (0.6-0.9) for system discussions. Let me check the reasoning steps and make sure the significance analyzer is properly integrated with the live capture API endpoints. We need to verify the conversation formatting and pattern matching algorithms.",
        "metadata": {"step": 4},
    }

    response4 = requests.post(
        f"{api_base}/api/v1/live/capture/message", headers=headers, json=message4
    )
    print(
        f"Message 4: {'✅' if response4.ok else '❌'} Assistant solution - {response4.status_code}"
    )

    # Wait for processing
    print("\\n⏳ Waiting for significance analysis...")
    time.sleep(3)

    # Check the conversation status
    status_response = requests.get(
        f"{api_base}/api/v1/live/capture/conversations", headers=headers
    )

    if status_response.ok:
        data = status_response.json()
        conversations = data.get("conversations", [])

        print("\\n📊 Conversation Analysis Results:")

        target_conversation = None
        for conv in conversations:
            if conv["session_id"] == session_id:
                target_conversation = conv
                break

        if target_conversation:
            print(f"   Session: {session_id[:30]}...")
            print(f"   Messages: {target_conversation['message_count']}")
            print(
                f"   Significance Score: {target_conversation['significance_score']:.3f}"
            )
            print(
                f"   Should Create Capsule: {target_conversation['should_create_capsule']}"
            )
            print(f"   Platform: {target_conversation['platform']}")

            if target_conversation["significance_score"] >= 0.6:
                print("\\n🎉 SUCCESS! Significance analyzer is working properly!")
                print(
                    f"   Score {target_conversation['significance_score']:.3f} exceeds threshold of 0.6"
                )
            else:
                print(
                    f"\\n⚠️  Still not working. Score {target_conversation['significance_score']:.3f} < 0.6"
                )
                print("   Need to investigate the conversation monitor integration")
        else:
            print(f"\\n❌ Could not find conversation {session_id}")
            print(f"   Available conversations: {len(conversations)}")
    else:
        print(f"\\n❌ Failed to get conversation status: {status_response.status_code}")


if __name__ == "__main__":
    create_conversation()
