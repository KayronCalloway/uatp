#!/usr/bin/env python3
"""
Direct test of the significance analyzer to see what it returns.
"""

import asyncio
import sys
import os

# Add path
sys.path.append("/Users/kay/uatp-capsule-engine/src")

from reasoning.analyzer import analyze_conversation_significance


async def test_analyzer():
    """Test the analyzer directly."""

    # Create test messages with UATP content
    test_messages = [
        {
            "role": "user",
            "content": "I'm working on fixing the UATP (Universal Attribution and Trust Protocol) conversation capture system. The current significance analyzer is giving 0.0-0.2 scores to technical conversations that should be 0.6-0.9.",
        },
        {
            "role": "assistant",
            "content": "I can help you fix the UATP significance analyzer. Let me analyze the current implementation and see what patterns we need to improve for better scoring of technical conversations.",
        },
    ]

    # Test context
    test_context = {
        "session_id": "test-session",
        "user_id": "kay",
        "platform": "claude_code",
        "conversation_length": 2,
    }

    print("🧪 Testing significance analyzer directly...")
    print("=" * 50)

    try:
        # Call the analyzer
        result = await analyze_conversation_significance(test_messages, test_context)

        print(f"📊 Raw analyzer result:")
        print(f"   Type: {type(result)}")
        print(
            f"   Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}"
        )
        print()

        if isinstance(result, dict):
            score = result.get("score", "NOT_FOUND")
            significance_score = result.get("significance_score", "NOT_FOUND")
            factors = result.get("factors", [])

            print(f"📈 Significance Analysis:")
            print(f"   Score field: {score}")
            print(f"   Significance_score field: {significance_score}")
            print(f"   Factors count: {len(factors)}")
            print(f"   Factors: {factors}")
            print()

            # Look for UATP patterns specifically
            uatp_factors = [
                f
                for f in factors
                if "uatp" in f.lower() or "universal attribution" in f.lower()
            ]
            print(f"🎯 UATP-specific factors: {uatp_factors}")

        else:
            print(f"❌ Unexpected result type: {type(result)}")
            print(f"   Content: {result}")

    except Exception as e:
        print(f"❌ Error calling analyzer: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_analyzer())
