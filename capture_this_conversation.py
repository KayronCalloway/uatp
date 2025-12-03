#!/usr/bin/env python3
"""
Capture This Conversation Demo
=============================

This script demonstrates capturing the current conversation between the user and Claude Code
and creating a live attribution capsule.
"""

import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from live_capture import get_real_time_generator, capture_live_interaction


async def capture_current_conversation():
    """Demonstrate capturing the current conversation."""

    print("🎯 Capturing Current Conversation with Claude Code")
    print("=" * 60)

    generator = get_real_time_generator()

    # Add callbacks for real-time monitoring
    async def on_live_capsule_created(interaction, capsule_id):
        print(f"\n🎉 LIVE CAPSULE CREATED FROM CURRENT CONVERSATION!")
        print(f"   Capsule ID: {capsule_id}")
        print(f"   User: {interaction.user_id}")
        print(f"   Platform: {interaction.platform}")
        print(f"   Session: {interaction.session_id}")
        print(f"   Messages: {len(interaction.messages)}")
        print(f"   Auto-encapsulated: {interaction.auto_encapsulated}")

    generator.add_callback("capsule_created", on_live_capsule_created)

    # This is the actual conversation we're having right now
    current_conversation = {
        "user": "ok whats next Immediate Next Steps... Let's implement real-time capsule generation for live AI interactions",
        "assistant": """Looking at the immediate next steps, I think **Real-Time Capsule Generation** is the most logical continuation since we've just completed the filter integration. Let me set up automatic capsule creation during actual AI interactions.

I'll create a real-time capsule generation system that can automatically capture and create attribution capsules during live AI interactions. This will include:

1. Live conversation capture
2. Real-time significance analysis  
3. Automatic capsule creation
4. Session tracking
5. Platform integration hooks

Let me build the RealTimeCapsuleGenerator class that can process live interactions and create capsules automatically when they meet the significance threshold.""",
    }

    session_id = "current-conversation-demo"

    print(f"📝 Capturing current conversation exchange...")
    print(f"   User: {current_conversation['user'][:60]}...")
    print(f"   Assistant: {current_conversation['assistant'][:60]}...")

    # Capture this actual conversation
    capsule_id = await capture_live_interaction(
        session_id=session_id,
        user_message=current_conversation["user"],
        ai_response=current_conversation["assistant"],
        user_id="kay",
        platform="claude_code",
        model="claude-sonnet-4",
        metadata={
            "conversation_type": "real_time_system_implementation",
            "topic": "uatp_capsule_generation",
            "significance": "high",
            "implementation_phase": "live_capture_demo",
        },
    )

    if capsule_id:
        print(f"\n✅ SUCCESS: Created live capsule from current conversation!")
        print(f"   Capsule ID: {capsule_id}")

        # Show capsule details
        stats = generator.get_stats()
        print(f"\n📊 Generator Statistics:")
        print(f"   Total interactions: {stats['total_interactions']}")
        print(f"   Total capsules created: {stats['total_capsules_created']}")
        print(f"   Active sessions: {stats['active_sessions']}")

        # Check the actual capsule in the chain
        print(f"\n🔍 Checking capsule chain file...")
        try:
            with open("/Users/kay/uatp-capsule-engine/capsule_chain.jsonl", "r") as f:
                lines = f.readlines()

            print(f"   Chain now has {len(lines)} total capsules")

            # Show the last capsule (should be ours)
            if lines:
                import json

                last_capsule = json.loads(lines[-1])
                if last_capsule.get("metadata", {}).get("auto_encapsulated"):
                    print(
                        f"   ✅ Last capsule is auto-encapsulated: {last_capsule['capsule_id']}"
                    )
                    print(
                        f"   Platform: {last_capsule.get('metadata', {}).get('platform', 'unknown')}"
                    )
                    print(
                        f"   Significance: {last_capsule.get('metadata', {}).get('significance_score', 0):.2f}"
                    )
                    print(
                        f"   Created by: {last_capsule.get('metadata', {}).get('created_by', 'unknown')}"
                    )
        except Exception as e:
            print(f"   Error checking chain: {e}")

    else:
        print(f"\n❌ No capsule created from current conversation")
        print(f"   (May not have met significance threshold)")

    return capsule_id


async def main():
    """Main demonstration function."""

    print("🚀 Real-Time Capsule Generation Demo")
    print("This demonstrates capturing live AI conversations!")
    print("=" * 70)

    try:
        capsule_id = await capture_current_conversation()

        if capsule_id:
            print(f"\n🎯 DEMO SUCCESSFUL!")
            print(f"   Created capsule: {capsule_id}")
            print(
                f"   The system is now capturing and creating capsules from live conversations!"
            )
            print(f"   📁 View in visualizer: http://localhost:8501")
            print(f"   🔧 Monitor in dashboard: http://localhost:8502")
        else:
            print(f"\n⚠️  Demo completed but no capsule created")
            print(f"   The conversation may not have met the significance threshold")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
