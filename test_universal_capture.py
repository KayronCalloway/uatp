#!/usr/bin/env python3
"""
Test script demonstrating Universal Capture Philosophy.
Creates conversations with varying significance levels to verify
ALL are captured, with significance used as economic weight.
"""

import asyncio
import requests
import json
from datetime import datetime

API_URL = "http://localhost:8000"

# Test conversations with varying significance levels
test_cases = [
    {
        "name": "High Significance - Technical Problem Solving",
        "expected_significance": "0.8-1.0",
        "messages": [
            {
                "role": "user",
                "content": "I need to implement a distributed consensus algorithm with Byzantine fault tolerance for a financial transaction system.",
            },
            {
                "role": "assistant",
                "content": "I'll help you implement a BFT consensus algorithm. Here's a comprehensive approach using PBFT (Practical Byzantine Fault Tolerance)...",
            },
        ],
    },
    {
        "name": "Medium Significance - Code Review",
        "expected_significance": "0.5-0.8",
        "messages": [
            {
                "role": "user",
                "content": "Can you review this function for potential bugs?",
            },
            {
                "role": "assistant",
                "content": "I see a few issues: 1) Missing null check on line 5, 2) Potential memory leak in the loop...",
            },
        ],
    },
    {
        "name": "Low Significance - Simple Question",
        "expected_significance": "0.2-0.5",
        "messages": [
            {"role": "user", "content": "How do I center a div?"},
            {
                "role": "assistant",
                "content": "You can use flexbox: display: flex; justify-content: center; align-items: center;",
            },
        ],
    },
    {
        "name": "Very Low Significance - Casual Interaction",
        "expected_significance": "0.0-0.2",
        "messages": [
            {"role": "user", "content": "ok"},
            {
                "role": "assistant",
                "content": "Understood. Let me know if you need anything else.",
            },
        ],
    },
]


async def test_universal_capture():
    """Test that ALL conversations are captured regardless of significance."""

    print("=" * 80)
    print("UNIVERSAL CAPTURE PHILOSOPHY TEST")
    print("=" * 80)
    print("\nTesting: 'Capture All, Weight Fairly' principle")
    print("Expected: ALL conversations captured, significance varies\n")

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"Test {i}/4: {test_case['name']}")
        print(f"Expected Significance Range: {test_case['expected_significance']}")
        print(f"{'─' * 80}")

        # Create unique session ID
        session_id = f"test-universal-{i}-{int(datetime.now().timestamp())}"

        # Send messages
        for msg in test_case["messages"]:
            payload = {
                "session_id": session_id,
                "user_id": "test-user",
                "platform": "test",
                "role": msg["role"],
                "content": msg["content"],
                "metadata": {},
            }

            try:
                response = requests.post(
                    f"{API_URL}/live/capture/message", json=payload, timeout=10
                )
                if response.status_code == 200:
                    print(f"  ✓ Captured {msg['role']} message")
                else:
                    print(f"  ✗ Failed to capture message: {response.status_code}")
            except Exception as e:
                print(f"  ✗ Error: {e}")

        # Wait a moment for processing
        await asyncio.sleep(2)

        # Check conversation status
        try:
            status_response = requests.get(
                f"{API_URL}/live/capture/conversation/{session_id}", timeout=10
            )

            if status_response.status_code == 200:
                result = status_response.json()
                if result.get("success"):
                    conv = result.get("conversation", {})
                    significance = conv.get("significance_score", 0.0)
                    capsule_created = conv.get("capsule_created", False)

                    print(f"\n  📊 Results:")
                    print(f"     Messages: {conv.get('message_count', 0)}")
                    print(f"     Significance Score: {significance:.3f}")
                    print(
                        f"     Capsule Created: {'✅ YES' if capsule_created else '❌ NO (pending)'}"
                    )
                    print(
                        f"     Economic Weight: {significance:.3f} (for value distribution)"
                    )

                    results.append(
                        {
                            "test": test_case["name"],
                            "significance": significance,
                            "captured": True,
                            "capsule_created": capsule_created,
                        }
                    )
                else:
                    print(f"  ⚠️  Status check failed")
                    results.append(
                        {
                            "test": test_case["name"],
                            "significance": 0.0,
                            "captured": False,
                            "capsule_created": False,
                        }
                    )
        except Exception as e:
            print(f"  ✗ Error checking status: {e}")
            results.append(
                {
                    "test": test_case["name"],
                    "significance": 0.0,
                    "captured": False,
                    "capsule_created": False,
                }
            )

    # Print summary
    print(f"\n\n{'=' * 80}")
    print("SUMMARY: Universal Capture Verification")
    print(f"{'=' * 80}\n")

    all_captured = all(r["captured"] for r in results)

    if all_captured:
        print("✅ SUCCESS: ALL conversations captured (universal capture working)")
    else:
        print("❌ FAILURE: Some conversations not captured (elitist filtering detected)")

    print("\nSignificance Distribution (Economic Weighting):")
    for result in results:
        stars = "★" * int(result["significance"] * 10)
        print(f"  {result['test']:.<50} {result['significance']:.3f} {stars}")

    print("\n📌 Key Principle:")
    print("   Significance determines ECONOMIC VALUE, not whether to CAPTURE")
    print("   Low significance = captured with low weight")
    print("   High significance = captured with high weight")
    print("\n📚 See: UNIVERSAL_CAPTURE_PHILOSOPHY.md")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    asyncio.run(test_universal_capture())
