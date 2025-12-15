#!/usr/bin/env python3
"""
Test CaptureOrchestrator
========================

Demonstrates the unified capture interface across all platforms.
"""

import asyncio
import logging

from src.live_capture.capture_orchestrator import CaptureOrchestrator, capture

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_orchestrator():
    """Test the capture orchestrator with multiple platforms."""

    print("🎭 Testing Capture Orchestrator")
    print("=" * 60)

    # Create orchestrator instance
    orchestrator = CaptureOrchestrator(user_id="test_user")

    # Test 1: OpenAI capture
    print("\n1️⃣ Testing OpenAI capture...")
    openai_capsule = await orchestrator.capture(
        platform="openai",
        user_input="Write a Python function to calculate factorial",
        assistant_response="Here's a Python function to calculate factorial using recursion...",
        model="gpt-4",
        interaction_type="code_generation"
    )
    print(f"   Result: {'✅ Captured' if openai_capsule else '❌ Not significant'}")
    if openai_capsule:
        print(f"   Capsule ID: {openai_capsule}")

    # Test 2: Anthropic capture
    print("\n2️⃣ Testing Anthropic capture...")
    anthropic_capsule = await orchestrator.capture(
        platform="anthropic",
        user_input="Explain quantum computing in simple terms",
        assistant_response="Quantum computing uses quantum mechanics principles like superposition...",
        model="claude-3-sonnet-20240229",
        interaction_type="explanation"
    )
    print(f"   Result: {'✅ Captured' if anthropic_capsule else '❌ Not significant'}")
    if anthropic_capsule:
        print(f"   Capsule ID: {anthropic_capsule}")

    # Test 3: Cursor capture
    print("\n3️⃣ Testing Cursor IDE capture...")
    cursor_capsule = await orchestrator.capture(
        platform="cursor",
        user_input="Debug this React component",
        assistant_response="I see the issue in your useState hook...",
        model="claude-3.5-sonnet",
        interaction_type="debugging",
        file_context="src/components/App.tsx"
    )
    print(f"   Result: {'✅ Captured' if cursor_capsule else '❌ Not significant'}")
    if cursor_capsule:
        print(f"   Capsule ID: {cursor_capsule}")

    # Test 4: Convenience function
    print("\n4️⃣ Testing convenience function...")
    convenience_capsule = await capture(
        platform="windsurf",
        user_input="Create a new React component",
        assistant_response="Here's a new React component with TypeScript...",
        user_id="test_user"
    )
    print(f"   Result: {'✅ Captured' if convenience_capsule else '❌ Not significant'}")
    if convenience_capsule:
        print(f"   Capsule ID: {convenience_capsule}")

    # Show platform info
    print("\n📊 Platform Information:")
    print(f"   Supported platforms: {orchestrator.get_supported_platforms()}")

    openai_info = orchestrator.get_platform_info("openai")
    print(f"\n   OpenAI: {openai_info['emoji']} {openai_info['name']}")
    print(f"   Models: {', '.join(openai_info['models'])}")
    print(f"   Type: {openai_info['type']}")

    # Show active hooks
    print("\n🔧 Active Hooks:")
    active_hooks = orchestrator.get_active_hooks()
    for platform, info in active_hooks.items():
        print(f"   {platform}: {info['platform']} (session: {info['session_id']})")

    print("\n✅ Orchestrator test complete!")


async def test_platform_aliases():
    """Test that platform aliases work correctly."""

    print("\n🔀 Testing Platform Aliases")
    print("=" * 60)

    orchestrator = CaptureOrchestrator(user_id="alias_test")

    aliases = [
        ("openai", "gpt"),
        ("anthropic", "claude"),
        ("cursor", "cursor_ide"),
        ("antigravity", "gemini")
    ]

    for canonical, alias in aliases:
        print(f"\n   Testing {alias} → {canonical}...")
        try:
            # This should work and route to the correct hook
            await orchestrator.capture(
                platform=alias,
                user_input="Test message",
                assistant_response="Test response"
            )
            print(f"   ✅ {alias} alias works")
        except Exception as e:
            print(f"   ❌ {alias} alias failed: {e}")

    print("\n✅ Alias test complete!")


async def test_error_handling():
    """Test error handling for invalid platforms."""

    print("\n⚠️ Testing Error Handling")
    print("=" * 60)

    orchestrator = CaptureOrchestrator(user_id="error_test")

    # Test invalid platform
    print("\n   Testing invalid platform...")
    try:
        await orchestrator.capture(
            platform="invalid_platform",
            user_input="Test",
            assistant_response="Test"
        )
        print("   ❌ Should have raised ValueError")
    except ValueError as e:
        print(f"   ✅ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"   ⚠️ Unexpected error: {e}")

    print("\n✅ Error handling test complete!")


async def main():
    """Run all tests."""

    print("🚀 Capture Orchestrator Test Suite")
    print("=" * 60)

    try:
        await test_orchestrator()
        await test_platform_aliases()
        await test_error_handling()

        print("\n" + "=" * 60)
        print("🎉 All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
