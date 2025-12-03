#!/usr/bin/env python3
"""
Quick test to verify capsule filtering is working
"""
import requests

print("=" * 80)
print("Testing Capsule Filtering")
print("=" * 80)

try:
    # Test default query (should exclude test data)
    print("\n1. Default Query (should hide test data):")
    response = requests.get("http://localhost:8000/capsules")
    data = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Total capsules: {data.get('total', 0)}")
    print(f"   Returned: {len(data.get('capsules', []))} capsules")

    # Test with include_test=true (should show all data)
    print("\n2. With include_test=true (should show all 43 capsules):")
    response = requests.get("http://localhost:8000/capsules?include_test=true")
    data = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Total capsules: {data.get('total', 0)}")
    print(f"   Returned: {len(data.get('capsules', []))} capsules")

    # Test with environment=test (should show test data)
    print("\n3. With environment=test (should show test capsules):")
    response = requests.get("http://localhost:8000/capsules?environment=test")
    data = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Total capsules: {data.get('total', 0)}")
    print(f"   Returned: {len(data.get('capsules', []))} capsules")

    print("\n" + "=" * 80)
    print("✅ Test Complete")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback

    traceback.print_exc()
