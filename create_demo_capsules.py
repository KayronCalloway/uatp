#!/usr/bin/env python3
"""
Demo script to create UATP capsules from our conversation.

This demonstrates how the UATP system creates capsules from AI conversations
and shows why you're not seeing new capsules automatically.
"""

import asyncio
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"
API_KEY = "test-api-key"


async def create_capsules_from_conversation():
    """Create capsules representing our conversation about implementing UATP security."""

    print("🔮 Creating UATP Capsules from our Conversation...")
    print("=" * 60)

    # Our conversation messages that should become capsules
    conversation_messages = [
        {
            "role": "user",
            "content": "yes",  # Your initial request to continue with security
            "timestamp": "2025-09-01T19:30:00Z",
        },
        {
            "role": "assistant",
            "content": "I implemented comprehensive security middleware integrating all 9 AI-centric security systems with automatic request/response protection, fixed method name mismatches, created unified security dashboard, and successfully connected frontend to backend with proper CORS handling.",
            "timestamp": "2025-09-01T19:45:00Z",
            "metadata": {
                "systems_implemented": 9,
                "security_level": "HIGH",
                "significance_score": 1.8,
            },
        },
        {
            "role": "user",
            "content": "is everything integrated with frontend?",
            "timestamp": "2025-09-01T19:46:00Z",
        },
        {
            "role": "assistant",
            "content": "Yes, everything is now fully integrated! Frontend runs on localhost:3000, backend on localhost:8000, all 9 security systems operational with 100% success rate, CORS working properly, and security dashboard showing real-time monitoring.",
            "timestamp": "2025-09-01T19:48:00Z",
            "metadata": {
                "integration_complete": True,
                "systems_operational": 9,
                "success_rate": 1.0,
                "significance_score": 1.5,
            },
        },
    ]

    # Start monitoring this conversation
    session_data = {
        "session_id": "claude-code-security-implementation",
        "user_id": "kay",
        "platform": "claude_code",
        "significance_threshold": 0.6,
        "auto_create_capsules": True,
    }

    try:
        response = requests.post(
            f"{API_BASE}/api/v1/live/monitor/start",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json=session_data,
        )
        print(f"📡 Monitor started: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")

    except Exception as e:
        print(f"❌ Failed to start monitor: {e}")

    # Add each message to create capsules
    for i, message in enumerate(conversation_messages, 1):
        try:
            message_data = {
                "session_id": "claude-code-security-implementation",
                "user_id": "kay",
                "platform": "claude_code",
                "role": message["role"],
                "content": message["content"],
                "timestamp": message["timestamp"],
                "metadata": message.get("metadata", {}),
            }

            response = requests.post(
                f"{API_BASE}/api/v1/live/capture/message",
                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                json=message_data,
            )

            print(f"💬 Message {i}/{len(conversation_messages)}: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                if result.get("capsule_created"):
                    print(f"   ✅ Capsule created: {result.get('capsule_id')}")
                else:
                    print(
                        f"   📝 Message captured (significance: {result.get('significance_score', 0):.2f})"
                    )
            else:
                print(f"   ❌ Error: {response.text}")

        except Exception as e:
            print(f"❌ Failed to capture message {i}: {e}")

    # Check final status
    try:
        response = requests.get(
            f"{API_BASE}/api/v1/live/monitor/status", headers={"X-API-Key": API_KEY}
        )

        if response.status_code == 200:
            status = response.json()
            print(f"\n📊 Final Monitor Status:")
            print(
                f"   Active conversations: {status['status']['active_conversations']}"
            )
            print(
                f"   Significance threshold: {status['status']['significance_threshold']}"
            )

    except Exception as e:
        print(f"❌ Failed to get status: {e}")

    # Check if capsules were created
    try:
        response = requests.get(f"{API_BASE}/capsules", headers={"X-API-Key": API_KEY})

        if response.status_code == 200:
            data = response.json()
            capsule_count = data.get("total", 0)
            print(f"\n🔮 Total Capsules in System: {capsule_count}")

            if capsule_count > 0:
                print("   Recent capsules:")
                for capsule in data.get("capsules", [])[:3]:
                    print(
                        f"   - {capsule.get('capsule_id', 'unknown')}: {capsule.get('capsule_type', 'unknown')}"
                    )
            else:
                print("   No capsules found.")
                print("\n💡 Why no capsules?")
                print(
                    "   1. The system needs an AI API key (OpenAI/Anthropic) to generate reasoning content"
                )
                print(
                    "   2. Conversations need significance scores > 0.6 to trigger capsule creation"
                )
                print(
                    "   3. The live capture system monitors real AI conversations, not API calls"
                )
                print("   4. Manual capsule creation requires proper schema format")

        else:
            print(f"❌ Failed to get capsules: {response.status_code}")

    except Exception as e:
        print(f"❌ Failed to check capsules: {e}")

    print("\n" + "=" * 60)
    print("🎯 To see capsules created automatically:")
    print("1. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
    print("2. Use the UATP system during actual AI conversations")
    print(
        "3. The system will automatically create capsules for significant interactions"
    )
    print("4. View them at: http://localhost:3000 (Capsule Explorer)")


if __name__ == "__main__":
    asyncio.run(create_capsules_from_conversation())
