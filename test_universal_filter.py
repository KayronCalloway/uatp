#!/usr/bin/env python3
"""
Test script for the Universal Filter System
"""

import asyncio
import json
import time
from datetime import datetime

# Add project root to path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from filters.integration_layer import (
    process_ai_interaction,
    process_openai_interaction,
    process_claude_interaction,
    process_claude_code_interaction,
)
from filters.universal_filter import get_universal_filter


async def test_filter_system():
    """Test the universal filter system with different scenarios."""

    print("🧪 Testing Universal Filter System")
    print("=" * 50)

    # Test scenarios
    test_cases = [
        {
            "name": "High Significance - Code Generation",
            "messages": [
                {
                    "role": "user",
                    "content": "How do I implement a binary search algorithm in Python?",
                },
                {
                    "role": "assistant",
                    "content": "Here's a binary search implementation:\n\n```python\ndef binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    \n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    \n    return -1\n```\n\nThis algorithm has O(log n) time complexity...",
                },
            ],
            "platform": "openai",
            "user_id": "test-user-1",
        },
        {
            "name": "Medium Significance - Problem Solving",
            "messages": [
                {
                    "role": "user",
                    "content": "I'm having trouble understanding recursion. Can you help?",
                },
                {
                    "role": "assistant",
                    "content": "Recursion can be tricky at first! Think of it like a Russian nesting doll - each function call opens another smaller version of the same problem. The key is having a base case to stop the recursion...",
                },
            ],
            "platform": "claude",
            "user_id": "test-user-2",
        },
        {
            "name": "Low Significance - Casual Chat",
            "messages": [
                {"role": "user", "content": "What's the weather like today?"},
                {
                    "role": "assistant",
                    "content": "I don't have access to real-time weather data, but I'd recommend checking a weather app or website for current conditions in your area!",
                },
            ],
            "platform": "claude_code",
            "user_id": "test-user-3",
        },
        {
            "name": "High Significance - Debugging",
            "messages": [
                {
                    "role": "user",
                    "content": "I'm getting a 'TypeError: unsupported operand type(s)' error in my Python code. Here's the stack trace...",
                },
                {
                    "role": "assistant",
                    "content": "This TypeError typically occurs when you're trying to perform an operation between incompatible types. Let's debug this step by step:\n\n1. Check the variable types using type()\n2. Look at the line where the error occurs\n3. Make sure you're not mixing strings and numbers\n\nCan you show me the specific line that's causing the error?",
                },
            ],
            "platform": "openai",
            "user_id": "test-user-4",
        },
        {
            "name": "Very Low Significance - Short Response",
            "messages": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello! How can I help you today?"},
            ],
            "platform": "claude",
            "user_id": "test-user-5",
        },
    ]

    # Test each case
    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print("-" * 40)

        try:
            # Process through the filter
            result = await process_ai_interaction(
                messages=test_case["messages"],
                user_id=test_case["user_id"],
                platform=test_case["platform"],
                context={"test_case": test_case["name"]},
                session_id=f"test-session-{i}",
            )

            # Display result
            decision_emoji = {
                "encapsulate": "✅",
                "discard": "❌",
                "defer": "⏳",
                "review": "👁️",
            }

            emoji = decision_emoji.get(result.decision.value, "❓")

            print(f"   Decision: {emoji} {result.decision.value.upper()}")
            print(f"   Significance Score: {result.significance_score:.2f}")
            print(f"   Confidence: {result.confidence:.2f}")
            print(f"   Reasoning: {', '.join(result.reasoning[:3])}")

            if result.should_encapsulate:
                print(f"   📦 WILL CREATE CAPSULE")
            else:
                print(f"   🗑️  Will not create capsule")

            results.append(
                {
                    "test_case": test_case["name"],
                    "decision": result.decision.value,
                    "score": result.significance_score,
                    "confidence": result.confidence,
                    "encapsulated": result.should_encapsulate,
                }
            )

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(
                {
                    "test_case": test_case["name"],
                    "decision": "error",
                    "score": 0.0,
                    "confidence": 0.0,
                    "encapsulated": False,
                }
            )

    # Summary
    print("\n" + "=" * 50)
    print("📊 FILTER TEST SUMMARY")
    print("=" * 50)

    encapsulated_count = sum(1 for r in results if r["encapsulated"])
    total_count = len(results)

    print(f"Total Tests: {total_count}")
    print(f"Encapsulated: {encapsulated_count}")
    print(f"Discarded: {total_count - encapsulated_count}")
    print(f"Encapsulation Rate: {encapsulated_count/total_count:.1%}")

    # Show filter stats
    filter_instance = get_universal_filter()
    stats = filter_instance.get_stats()

    print(f"\nFilter Statistics:")
    print(f"  Significance Threshold: {stats['config']['significance_threshold']}")
    print(f"  Total Processed: {stats['total_processed']}")
    print(f"  Total Encapsulated: {stats['total_encapsulated']}")
    print(f"  Total Discarded: {stats['total_discarded']}")

    return results


async def test_platform_specific_functions():
    """Test platform-specific convenience functions."""

    print("\n🔧 Testing Platform-Specific Functions")
    print("=" * 50)

    # Test OpenAI
    print("\n1. Testing OpenAI Integration")
    openai_result = await process_openai_interaction(
        messages=[
            {
                "role": "user",
                "content": "Write a Python function to calculate factorial",
            },
            {
                "role": "assistant",
                "content": "Here's a factorial function:\n\n```python\ndef factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n```",
            },
        ],
        user_id="openai-test-user",
        model="gpt-4",
    )

    print(
        f"   OpenAI Result: {openai_result.decision.value} (Score: {openai_result.significance_score:.2f})"
    )

    # Test Claude
    print("\n2. Testing Claude Integration")
    claude_result = await process_claude_interaction(
        messages=[
            {"role": "user", "content": "Explain machine learning in simple terms"},
            {
                "role": "assistant",
                "content": "Machine learning is like teaching a computer to recognize patterns and make predictions, similar to how humans learn from experience...",
            },
        ],
        user_id="claude-test-user",
        model="claude-3",
    )

    print(
        f"   Claude Result: {claude_result.decision.value} (Score: {claude_result.significance_score:.2f})"
    )

    # Test Claude Code
    print("\n3. Testing Claude Code Integration")
    claude_code_result = await process_claude_code_interaction(
        messages=[
            {"role": "user", "content": "Help me debug this React component"},
            {
                "role": "assistant",
                "content": "I'd be happy to help debug your React component! Could you share the component code and describe what issue you're experiencing?",
            },
        ],
        user_id="claude-code-test-user",
    )

    print(
        f"   Claude Code Result: {claude_code_result.decision.value} (Score: {claude_code_result.significance_score:.2f})"
    )


async def test_threshold_adjustment():
    """Test how threshold adjustment affects filtering."""

    print("\n⚙️  Testing Threshold Adjustment")
    print("=" * 50)

    filter_instance = get_universal_filter()

    # Test message
    test_messages = [
        {"role": "user", "content": "Can you help me optimize this algorithm?"},
        {
            "role": "assistant",
            "content": "Sure! Let's look at ways to optimize your algorithm. What specific performance issues are you experiencing?",
        },
    ]

    # Test with different thresholds
    thresholds = [0.3, 0.6, 0.9, 1.2]

    for threshold in thresholds:
        print(f"\nTesting with threshold: {threshold}")

        # Update threshold
        filter_instance.update_config({"significance_threshold": threshold})

        # Test the same interaction
        result = await process_ai_interaction(
            messages=test_messages,
            user_id="threshold-test-user",
            platform="openai",
            context={"threshold_test": threshold},
        )

        print(f"   Score: {result.significance_score:.2f}")
        print(f"   Decision: {result.decision.value}")
        print(f"   Encapsulated: {result.should_encapsulate}")

    # Reset to default
    filter_instance.update_config({"significance_threshold": 0.6})


async def main():
    """Run all tests."""

    print("🚀 UATP Universal Filter Test Suite")
    print("=" * 60)

    try:
        # Run basic filter tests
        await test_filter_system()

        # Test platform-specific functions
        await test_platform_specific_functions()

        # Test threshold adjustment
        await test_threshold_adjustment()

        print("\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
