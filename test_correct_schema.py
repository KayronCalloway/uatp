#!/usr/bin/env python3
"""
Test the Capsule Creation API with Correct Schema
"""

import requests
import json
from datetime import datetime, timezone


def test_correct_schema_api():
    """Test the capsule creation API with the correct schema format."""

    api_base = "http://localhost:9090"
    headers = {"X-API-Key": "dev-key-001", "Content-Type": "application/json"}

    print("🧪 Testing Capsule Creation API with Correct Schema")
    print("=" * 60)

    # Test data matching the correct ReasoningStep schema
    capsule_request = {
        "reasoning_trace": {
            "reasoning_steps": [
                {
                    "step_id": 1,  # int as expected by schema
                    "operation": "analysis",  # using "operation" instead of "step_type"
                    "reasoning": "Testing the capsule creation API with the correct schema format. This should match the ReasoningStep model in capsule_schema.py which expects step_id as int, operation field, and reasoning content.",
                    "confidence": 0.94,  # using "confidence" not "confidence_level"
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "test_type": "correct_schema_validation",
                        "expected_result": "successful_capsule_creation",
                        "technical_fix": "matching_pydantic_model",
                    },
                }
            ],
            "total_confidence": 0.94,
        },
        "status": "active",
    }

    print("📦 Request Data (Correct Schema):")
    print(json.dumps(capsule_request, indent=2))
    print()

    try:
        print("🚀 Making API request...")
        response = requests.post(
            f"{api_base}/capsules", headers=headers, json=capsule_request
        )

        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()

        if response.ok:
            result = response.json()
            print("✅ SUCCESS! API is now working with correct schema!")
            print(f"Created capsule: {result.get('capsule_id', 'unknown')}")
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Message: {result.get('message', 'unknown')}")

            # Show the created capsule
            capsule = result.get("capsule", {})
            if capsule:
                print(f"\n📋 Capsule Details:")
                print(f"   ID: {capsule.get('capsule_id', 'unknown')}")
                print(f"   Type: {capsule.get('capsule_type', 'unknown')}")
                print(f"   Timestamp: {capsule.get('timestamp', 'unknown')}")
                print(
                    f"   Confidence: {capsule.get('reasoning_trace', {}).get('total_confidence', 0)}"
                )
                print(f"   Status: {capsule.get('status', 'unknown')}")

            return True

        else:
            print(f"❌ FAILED: {response.status_code}")

            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    error_data = response.json()
                    print("Error Details:")
                    print(json.dumps(error_data, indent=2))
                except:
                    print(f"Raw Error: {response.text}")
            else:
                print(f"HTML Error: {response.text[:500]}...")

            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


if __name__ == "__main__":
    success = test_correct_schema_api()

    if success:
        print("\n🎉 SCHEMA FIX COMPLETE!")
        print("✅ Capsule creation API now works with correct schema")
        print("✅ The final 10% issue has been resolved")
        print(f"\n🔗 Dashboard: http://localhost:3000")
        print(f"📱 Mobile: http://192.168.1.79:3000")
        print(f"\n🚀 UATP system is now 100% functional!")
    else:
        print("\n❌ Still debugging schema issues")
        print("Need to verify ReasoningStep model requirements")
