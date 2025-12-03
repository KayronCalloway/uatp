#!/usr/bin/env python3
"""
Test the Fixed Significance Scoring

This directly tests the significance analyzer with our metadata scores.
"""

import asyncio
import sys
import os

sys.path.append("/Users/kay/uatp-capsule-engine")

from src.reasoning.fixed_analyzer import analyze_conversation_significance


async def test_significance_fix():
    """Test that the fixed analyzer respects metadata significance scores."""

    print("🔬 Testing Fixed Significance Scoring Algorithm...")
    print("=" * 60)

    # Test message with explicit significance score
    test_messages = [
        {
            "role": "user",
            "content": "i have given my openai keys and as claude code you should be aple to give anthropic key",
            "metadata": {
                "significance_score": 2.5,
                "context": "Critical API key configuration for UATP system",
                "importance_level": "high",
                "economic_impact": "trillion_dollar_vision",
            },
        }
    ]

    context = {
        "session_id": "test-significance",
        "user_id": "kay",
        "platform": "claude_code",
        "conversation_length": 1,
    }

    print("📊 Testing Message:")
    print(f"   Content: {test_messages[0]['content'][:50]}...")
    print(f"   Metadata Score: {test_messages[0]['metadata']['significance_score']}")

    # Analyze significance
    result = await analyze_conversation_significance(test_messages, context)

    print(f"\n📈 Analysis Results:")
    print(f"   Significance Score: {result.get('significance_score', 'N/A')}")
    print(f"   Score (alt): {result.get('score', 'N/A')}")
    print(f"   Should Create Capsule: {result.get('should_create_capsule', False)}")
    print(f"   Confidence: {result.get('confidence', 0):.2f}")
    print(f"   Analyzer Version: {result.get('analyzer_version', 'unknown')}")

    if result.get("factors"):
        print(f"   Factors: {result['factors'][0] if result['factors'] else 'None'}")

    # Test without metadata score for comparison
    print(f"\n🔍 Testing Same Message Without Metadata Score:")

    test_messages_no_metadata = [
        {
            "role": "user",
            "content": "i have given my openai keys and as claude code you should be aple to give anthropic key",
        }
    ]

    result_no_metadata = await analyze_conversation_significance(
        test_messages_no_metadata, context
    )

    print(
        f"   Significance Score: {result_no_metadata.get('significance_score', 'N/A')}"
    )
    print(
        f"   Should Create Capsule: {result_no_metadata.get('should_create_capsule', False)}"
    )

    # Test results
    print(f"\n" + "=" * 60)
    print(f"🎯 Test Results:")

    if result.get("significance_score", 0) == 2.5:
        print("   ✅ PASS: Metadata score properly respected (2.5)")
    else:
        print(f"   ❌ FAIL: Expected 2.5, got {result.get('significance_score', 'N/A')}")

    if result.get("should_create_capsule", False):
        print("   ✅ PASS: Should create capsule (above 0.6 threshold)")
    else:
        print("   ❌ FAIL: Should create capsule but didn't")

    if result.get("analyzer_version", "").startswith("fixed_2.1"):
        print("   ✅ PASS: Using updated analyzer version")
    else:
        print(
            f"   ❌ FAIL: Using old analyzer version: {result.get('analyzer_version', 'unknown')}"
        )

    return result


if __name__ == "__main__":
    asyncio.run(test_significance_fix())
