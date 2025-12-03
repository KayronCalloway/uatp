#!/usr/bin/env python3
"""
Force Capsule Creation from Live Captures
Converts captured conversations into full UATP capsules with all features
"""

import requests
import json
import time
from datetime import datetime


def force_create_capsules():
    """Force creation of full UATP capsules from live captures."""

    api_base = "http://localhost:9090"
    headers = {"X-API-Key": "dev-key-001", "Content-Type": "application/json"}

    print("🔍 Checking captured conversations...")

    # Get all live conversations
    try:
        response = requests.get(
            f"{api_base}/api/v1/live/capture/conversations", headers=headers
        )
        if not response.ok:
            print(f"❌ Failed to get conversations: {response.status_code}")
            return

        conversations = response.json().get("conversations", [])
        print(f"📋 Found {len(conversations)} captured conversations")

        created_count = 0

        for conv in conversations:
            session_id = conv["session_id"]
            platform = conv["platform"]
            message_count = conv["message_count"]

            print(f"\n🔄 Processing {platform} session: {session_id}")
            print(f"   Messages: {message_count}")

            # Get detailed conversation messages
            try:
                detail_response = requests.get(
                    f"{api_base}/api/v1/live/capture/conversation/{session_id}",
                    headers=headers,
                )

                if detail_response.ok:
                    detail_data = detail_response.json()
                    messages = detail_data.get("conversation", {}).get("messages", [])

                    if len(messages) >= 2:  # Need at least user + assistant
                        # Create full-featured capsule
                        capsule_created = create_enhanced_capsule(
                            session_id, platform, messages, headers, api_base
                        )
                        if capsule_created:
                            created_count += 1
                    else:
                        print(
                            f"   ⚠️  Not enough messages for capsule ({len(messages)})"
                        )
                else:
                    print(f"   ❌ Failed to get conversation details")

            except Exception as e:
                print(f"   ❌ Error processing conversation: {e}")

        print(f"\n🎉 Created {created_count} enhanced capsules!")
        print(f"🔗 View at: http://localhost:3000")

    except Exception as e:
        print(f"❌ Error: {e}")


def create_enhanced_capsule(session_id, platform, messages, headers, api_base):
    """Create an enhanced capsule with full UATP features."""

    try:
        # Extract user and assistant messages
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]

        if not user_messages or not assistant_messages:
            print(f"   ⚠️  Missing user or assistant messages")
            return False

        # Combine conversation content
        conversation_text = ""
        reasoning_steps = []
        step_count = 0

        for i, msg in enumerate(messages[:10]):  # Limit to 10 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:500]  # Limit content length

            conversation_text += f"{role.title()}: {content}\n\n"

            if content and len(content) > 20:
                step_count += 1
                reasoning_steps.append(
                    {
                        "step_id": f"step_{step_count:03d}",
                        "operation": f"{role}_interaction",
                        "reasoning": content[:300] + "..."
                        if len(content) > 300
                        else content,
                        "confidence": 0.85 + (i * 0.02),  # Increasing confidence
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": {
                            "platform": platform,
                            "session_id": session_id,
                            "message_index": i + 1,
                            "role": role,
                        },
                    }
                )

        # Calculate significance based on content
        significance_factors = {
            "technical_content": any(
                word in conversation_text.lower()
                for word in ["code", "function", "api", "system", "implementation"]
            ),
            "length": len(conversation_text) > 200,
            "multi_turn": len(messages) > 2,
            "platform_quality": platform
            in ["claude_code", "claude_desktop", "windsurf"],
        }

        base_confidence = 0.75 + sum(
            0.05 for factor in significance_factors.values() if factor
        )
        economic_value = len(conversation_text) * 0.02 + (len(messages) * 2.5)

        # Create comprehensive capsule
        capsule_data = {
            "capsule_type": "conversation_trace",
            "agent_id": f"{platform}-enhanced-agent",
            "reasoning_trace": {
                "reasoning_steps": reasoning_steps,
                "total_confidence": min(base_confidence, 0.95),
                "metadata": {
                    "conversation_type": "enhanced_live_capture",
                    "platform": platform,
                    "session_id": session_id,
                    "message_count": len(messages),
                    "complexity_score": min(0.9, len(reasoning_steps) * 0.1),
                    "economic_value": min(economic_value, 50.0),
                    "significance_factors": significance_factors,
                    "conversation_length": len(conversation_text),
                },
            },
            "context_metadata": {
                "session_type": "live_captured_conversation",
                "user_intent": "real_world_interaction",
                "platform": platform,
                "conversation_quality": "enhanced_processing",
                "attribution_eligible": True,
                "processing_timestamp": datetime.utcnow().isoformat(),
                "source_session": session_id,
            },
        }

        # Create the capsule
        response = requests.post(
            f"{api_base}/capsules", headers=headers, json=capsule_data
        )

        if response.ok:
            capsule_result = response.json()
            capsule_id = capsule_result.get("capsule_id", "unknown")
            print(f"   ✅ Created enhanced capsule: {capsule_id[:20]}...")
            print(f"      Confidence: {base_confidence:.2f}")
            print(f"      Economic value: ${economic_value:.2f}")
            print(f"      Steps: {len(reasoning_steps)}")
            return True
        else:
            print(f"   ❌ Failed to create capsule: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"      Error: {error_detail}")
            except:
                print(f"      Error: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"   ❌ Error creating enhanced capsule: {e}")
        return False


if __name__ == "__main__":
    print("🚀 UATP Force Capsule Creation")
    print("=" * 50)
    print("Converting live captures into full-featured capsules...")
    print()

    force_create_capsules()

    print("\n🔍 Checking final status...")

    # Show final capsule count
    try:
        response = requests.get(
            "http://localhost:9090/capsules?per_page=5",
            headers={"X-API-Key": "dev-key-001"},
        )

        if response.ok:
            data = response.json()
            print(f"📦 Total capsules now: {data.get('total', 0)}")

            recent = data.get("capsules", [])[:3]
            if recent:
                print("Recent capsules:")
                for capsule in recent:
                    confidence = capsule.get("reasoning_trace", {}).get(
                        "total_confidence", 0
                    )
                    print(
                        f"  • {capsule.get('capsule_id', 'unknown')[:20]}... (confidence: {confidence:.2f})"
                    )

    except Exception as e:
        print(f"❌ Error getting final status: {e}")

    print(f"\n🎉 Enhanced capsules should now show full UATP features!")
    print(f"🔗 Dashboard: http://localhost:3000")
    print(f"📱 Mobile: http://192.168.1.79:3000")
