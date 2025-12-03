#!/usr/bin/env python3
"""
Demonstration: Filter THIS Current Conversation
===============================================

This script demonstrates how the current conversation between you and Claude
would be processed through the universal filter system.
"""

import asyncio
import json
from datetime import datetime

# Add project root to path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from filters.integration_layer import process_claude_code_interaction


async def demo_current_conversation():
    """Demonstrate filtering the current conversation."""

    print("🎯 DEMO: Filtering Current Conversation")
    print("=" * 50)
    print("This demonstrates how our current conversation would be processed")
    print("through the universal filter system.\n")

    # Simulate our current conversation
    current_conversation = [
        {"role": "user", "content": "everything should be encapsulated if we can"},
        {
            "role": "assistant",
            "content": "You're absolutely right! Let's make **everything** get encapsulated automatically. I'll set up comprehensive auto-encapsulation that captures all your AI interactions without you having to think about it.",
        },
        {
            "role": "user",
            "content": "wait everything goes through filter to determined if its encapsulated",
        },
        {
            "role": "assistant",
            "content": "Exactly! That's the perfect approach. Let me set up a **universal filter system** that routes ALL AI interactions through significance analysis to determine what gets encapsulated.",
        },
        {"role": "user", "content": "ok lets do it"},
        {
            "role": "assistant",
            "content": "Let's do it! I'll start by setting up real-time capsule generation to capture your actual AI interactions. This is the most impactful next step.\n\n[Implementation of universal filter system, significance analysis, platform integration, etc...]",
        },
    ]

    print("📝 Current Conversation Messages:")
    for i, msg in enumerate(current_conversation, 1):
        role_emoji = "👤" if msg["role"] == "user" else "🤖"
        preview = (
            msg["content"][:100] + "..."
            if len(msg["content"]) > 100
            else msg["content"]
        )
        print(f"   {i}. {role_emoji} {msg['role']}: {preview}")

    print(f"\n🔍 Processing through Universal Filter...")
    print("-" * 40)

    # Process through the filter
    try:
        result = await process_claude_code_interaction(
            messages=current_conversation,
            user_id="kay",
            session_id="current-claude-code-session",
        )

        # Show results
        decision_emojis = {
            "encapsulate": "✅ ENCAPSULATE",
            "discard": "❌ DISCARD",
            "defer": "⏳ DEFER",
            "review": "👁️ REVIEW",
        }

        decision_text = decision_emojis.get(
            result.decision.value, f"❓ {result.decision.value}"
        )

        print(f"Decision: {decision_text}")
        print(f"Significance Score: {result.significance_score:.2f}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Platform Weight Applied: Claude Code (1.2x)")

        if result.reasoning:
            print(f"\nReasoning Factors:")
            for factor in result.reasoning:
                print(f"  • {factor}")

        print(f"\nWould Create Capsule: {'YES' if result.should_encapsulate else 'NO'}")

        if result.should_encapsulate:
            print("\n📦 CAPSULE PREVIEW:")
            print(f"   Type: reasoning_trace")
            print(
                f"   Content: Claude Code interaction: {current_conversation[0]['content'][:50]}..."
            )
            print(f"   Agent: claude-code-auto-capsule-system")
            print(f"   Confidence: {result.confidence:.2f}")
            print(f"   Reasoning Steps: {len(result.reasoning)}")
            print(f"   Metadata: Auto-encapsulated via universal filter")

        # Show what makes this significant
        print(f"\n🎯 WHY THIS CONVERSATION IS SIGNIFICANT:")

        factors_explanation = {
            "Technical depth in response": "Discussion involves complex system architecture",
            "Code generation detected": "Contains code examples and implementation details",
            "Problem-solving discussion": "Addresses specific technical challenges",
            "Learning/explanation content": "Provides educational content about attribution systems",
            "Workflow improvement discussion": "Focuses on optimizing development processes",
            "Performance optimization": "Discusses system performance and scalability",
        }

        for factor in result.reasoning:
            if factor in factors_explanation:
                print(f"  • {factor}: {factors_explanation[factor]}")

        # Show platform bonus
        if result.significance_score > 0.5:
            print(f"\n🚀 PLATFORM BONUS:")
            print(f"   • Claude Code interactions get 1.2x weight multiplier")
            print(
                f"   • This recognizes the technical nature of code-focused conversations"
            )

        print(f"\n💡 FILTER THRESHOLD: {0.6}")
        print(
            f"   Score: {result.significance_score:.2f} {'✅ ABOVE' if result.significance_score >= 0.6 else '❌ BELOW'} threshold"
        )

    except Exception as e:
        print(f"❌ Error processing conversation: {e}")
        import traceback

        traceback.print_exc()


async def demo_threshold_scenarios():
    """Show how different thresholds would affect this conversation."""

    print(f"\n🎛️  THRESHOLD SCENARIOS")
    print("=" * 50)

    # Test conversation
    test_conversation = [
        {"role": "user", "content": "help me implement the universal filter system"},
        {
            "role": "assistant",
            "content": "I'll help you implement the universal filter system. This involves setting up significance analysis, platform integration, and auto-encapsulation logic...",
        },
    ]

    thresholds = [0.3, 0.6, 0.9, 1.2]

    for threshold in thresholds:
        print(f"\nThreshold: {threshold}")
        print("-" * 20)

        # Import filter to change threshold
        from filters.universal_filter import get_universal_filter

        filter_instance = get_universal_filter()
        filter_instance.update_config({"significance_threshold": threshold})

        # Process conversation
        result = await process_claude_code_interaction(
            messages=test_conversation,
            user_id="kay",
            session_id=f"threshold-test-{threshold}",
        )

        status = "✅ ENCAPSULATE" if result.should_encapsulate else "❌ DISCARD"
        print(f"   Score: {result.significance_score:.2f} → {status}")

        if threshold == 0.6:
            print(f"   ⭐ DEFAULT THRESHOLD")

    # Reset to default
    filter_instance.update_config({"significance_threshold": 0.6})


async def main():
    """Run the demonstration."""

    print("🎭 UATP Universal Filter - Live Demonstration")
    print("=" * 60)
    print("Demonstrating how AI conversations are filtered for encapsulation")
    print()

    # Demo current conversation
    await demo_current_conversation()

    # Demo threshold scenarios
    await demo_threshold_scenarios()

    print(f"\n" + "=" * 60)
    print("✅ DEMONSTRATION COMPLETE!")
    print("🎯 The universal filter successfully analyzed our conversation")
    print("📦 Significant conversations will be automatically encapsulated")
    print("🔧 Thresholds can be adjusted in real-time via the dashboard")
    print(f"\n🌐 Dashboard: http://localhost:8502")
    print(f"📊 Visualizer: http://localhost:8501")


if __name__ == "__main__":
    asyncio.run(main())
