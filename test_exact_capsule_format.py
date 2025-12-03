#!/usr/bin/env python3
"""
Test Exact Capsule Format
Creates a capsule that exactly matches the format of existing working capsules
"""

import requests
import json
from datetime import datetime, timezone


def test_exact_format():
    """Test with exact format from existing working capsule."""

    api_base = "http://localhost:9090"
    headers = {"X-API-Key": "dev-key-001", "Content-Type": "application/json"}

    print("🔍 Testing Exact Format from Working Capsule")
    print("=" * 50)

    # Get a working capsule first to see the exact format
    try:
        response = requests.get(f"{api_base}/capsules?per_page=1", headers=headers)
        if response.ok:
            data = response.json()
            existing_capsule = data["capsules"][0]
            print("📋 Existing capsule format:")
            print(json.dumps(existing_capsule, indent=2))
            print()
        else:
            print("❌ Could not get existing capsule")
            return False
    except Exception as e:
        print(f"❌ Error getting existing capsule: {e}")
        return False

    # Create new capsule with identical structure but new content
    new_capsule = {
        "capsule_type": "reasoning_trace",
        "reasoning_trace": {
            "reasoning_steps": [
                {
                    "step_id": "fix_001",
                    "reasoning": "Testing capsule creation with exact format match to resolve 400 API errors",
                    "confidence_level": 0.92,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metadata": {"operation": "format_testing", "debug_attempt": True},
                }
            ],
            "total_confidence": 0.92,
        },
    }

    print("📦 Creating capsule with exact format...")
    print("Request data:")
    print(json.dumps(new_capsule, indent=2))
    print()

    try:
        response = requests.post(
            f"{api_base}/capsules", headers=headers, json=new_capsule
        )

        print(f"Response Status: {response.status_code}")
        print(
            f"Response Content-Type: {response.headers.get('content-type', 'unknown')}"
        )

        if response.ok:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"Created capsule: {result.get('capsule_id', 'unknown')}")
            return True
        else:
            print("❌ FAILED")
            print(f"Response: {response.text}")

            # Check if it's JSON error
            if "application/json" in response.headers.get("content-type", ""):
                try:
                    error_data = response.json()
                    print("Error details:")
                    print(json.dumps(error_data, indent=2))
                except:
                    pass

            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_minimal_format():
    """Test with absolutely minimal format."""

    api_base = "http://localhost:9090"
    headers = {"X-API-Key": "dev-key-001", "Content-Type": "application/json"}

    print("\n🔬 Testing Minimal Format")
    print("=" * 30)

    minimal_capsule = {
        "capsule_type": "reasoning_trace",
        "reasoning_trace": {"reasoning_steps": [], "total_confidence": 1.0},
    }

    print("📦 Creating minimal capsule...")

    try:
        response = requests.post(
            f"{api_base}/capsules", headers=headers, json=minimal_capsule
        )

        print(f"Status: {response.status_code}")

        if response.ok:
            result = response.json()
            print("✅ Minimal format worked!")
            print(f"Created: {result.get('capsule_id', 'unknown')}")
            return True
        else:
            print("❌ Minimal format failed")
            print(f"Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


if __name__ == "__main__":
    print("🧪 UATP Capsule Format Testing")
    print("=" * 60)

    success1 = test_exact_format()
    success2 = test_minimal_format()

    if success1 or success2:
        print(f"\n🎉 Found working format!")
        print(f"Now can implement automatic capsule creation from live captures")
    else:
        print(f"\n❌ Both formats failed")
        print(f"Issue may be with:")
        print(f"  • API key permissions ('write' permission)")
        print(f"  • Request validation decorator")
        print(f"  • Missing required fields in schema")
        print(f"  • Blueprint registration issue")
