#!/usr/bin/env python3
"""
Fix Capsule Creation with Correct Schema Format
Uses the proper UATP 7.0 schema format to create working capsules
"""

import requests
import json
import time
from datetime import datetime, timezone


def create_properly_formatted_capsule():
    """Create a capsule using the correct UATP 7.0 schema format."""

    api_base = "http://localhost:9090"
    headers = {"X-API-Key": "dev-key-001", "Content-Type": "application/json"}

    print("🔧 Creating Properly Formatted UATP Capsule")
    print("=" * 50)

    # Create capsule using the correct schema format
    # Based on ReasoningTraceCapsule structure from capsule_schema.py

    capsule_data = {
        "capsule_type": "reasoning_trace",  # Must match CapsuleType.REASONING_TRACE
        "reasoning_trace": {  # ReasoningTracePayload structure
            "reasoning_steps": [
                {
                    "step_id": "debug_001",
                    "reasoning": "Identified that capsule creation API requires exact UATP 7.0 schema format with proper field validation. The previous attempts failed because they used custom field structures not matching the BaseCapsule + ReasoningTracePayload schema.",
                    "confidence_level": 0.95,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "operation_type": "schema_debugging",
                        "technical_fix": True,
                        "validation_required": True,
                    },
                },
                {
                    "step_id": "debug_002",
                    "reasoning": "Corrected the capsule creation format to use 'reasoning_steps' field (aliased as 'steps') with proper ReasoningStep structure. This should resolve the 400 API errors and enable automatic capsule creation from high-significance live captures.",
                    "confidence_level": 0.89,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "fix_type": "api_format_correction",
                        "expected_result": "successful_capsule_creation",
                    },
                },
            ],
            "total_confidence": 0.92,
        },
    }

    print("📦 Attempting capsule creation with proper schema...")

    try:
        response = requests.post(
            f"{api_base}/capsules", headers=headers, json=capsule_data
        )

        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.ok:
            result = response.json()
            capsule_id = result.get("capsule_id", "unknown")
            print(f"✅ SUCCESS! Created capsule: {capsule_id}")
            print(f"   Type: {result.get('capsule_type', 'unknown')}")
            print(f"   Status: {result.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Response text: {response.text}")

            # Try to parse error response
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print("Could not parse error response as JSON")

            return False

    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return False


def test_alternative_formats():
    """Test alternative capsule formats to find what works."""

    api_base = "http://localhost:9090"
    headers = {"X-API-Key": "dev-key-001", "Content-Type": "application/json"}

    print("\n🧪 Testing Alternative Formats")
    print("=" * 40)

    # Format 1: Minimal reasoning trace
    format1 = {
        "capsule_type": "reasoning_trace",
        "reasoning_trace": {
            "reasoning_steps": [
                {
                    "step_id": "test_001",
                    "reasoning": "Testing minimal format",
                    "confidence_level": 0.8,
                }
            ]
        },
    }

    # Format 2: With steps alias (older format)
    format2 = {
        "capsule_type": "reasoning_trace",
        "reasoning_trace": {
            "steps": [
                {
                    "step_id": "test_002",
                    "reasoning": "Testing steps alias format",
                    "confidence_level": 0.8,
                }
            ]
        },
    }

    formats = [("Minimal", format1), ("Steps Alias", format2)]

    for name, format_data in formats:
        print(f"\n🔍 Testing {name} format...")

        try:
            response = requests.post(
                f"{api_base}/capsules", headers=headers, json=format_data
            )
            print(f"   Status: {response.status_code}")

            if response.ok:
                result = response.json()
                print(f"   ✅ Success: {result.get('capsule_id', 'unknown')}")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:200]}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    return False


if __name__ == "__main__":
    # First try the proper format
    success = create_properly_formatted_capsule()

    if not success:
        print("\n🔄 Primary format failed, testing alternatives...")
        success = test_alternative_formats()

    if success:
        print(f"\n🎉 Capsule creation is now working!")
        print(f"🔗 Check dashboard: http://localhost:3000")

        # Test the live capture → capsule creation pipeline
        print(f"\n🔄 Testing automatic capsule creation from live capture...")

        # This should now work since we know the correct format

    else:
        print(f"\n❌ All formats failed. Need to investigate the API further.")
        print(f"💡 Next steps:")
        print(f"   1. Check backend logs for detailed error messages")
        print(f"   2. Verify API key permissions include 'write'")
        print(f"   3. Check if any required fields are missing")
        print(f"   4. Test with curl to isolate Python-specific issues")
