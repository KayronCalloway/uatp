#!/usr/bin/env python3
"""
Compare successful and failing API requests for raw data inclusion.
This script performs two identical requests, one using our debug approach
and one using the integration test approach, to identify any differences.
"""

import os
import sys
import time

import requests

# Import from the test file
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tests.test_api_endpoints import API_URL, HEADERS

print("=== Comparing API Raw Data Requests ===")
print(f"API URL: {API_URL}")


# Create a test capsule
def create_test_capsule():
    print("\n=== Creating test capsule ===")
    test_data = {
        "capsule_type": "consent",
        "confidence": 0.95,
        "consent_details": {
            "purpose": "Comparison Test",
            "scope": "API",
            "duration": "1h",
        },
    }

    try:
        response = requests.post(f"{API_URL}/capsules", headers=HEADERS, json=test_data)

        if response.status_code == 201:
            capsule_id = response.json().get("capsule_id")
            print(f"Created test capsule with ID: {capsule_id}")
            return capsule_id
        else:
            print(
                f"Failed to create test capsule: {response.status_code} - {response.text}"
            )
            return None
    except Exception as e:
        print(f"Error creating test capsule: {e}")
        return None


# Test debug-style request
def test_debug_request(capsule_id):
    print("\n=== Debug-style request ===")
    debug_headers = {
        "X-API-Key": HEADERS["X-API-Key"],
        "X-Request-ID": "debug-comparison",
        "Content-Type": "application/json",
    }

    params = {"include_raw": "true"}
    print(f"Request URL: {API_URL}/capsules/{capsule_id}")
    print(f"Params: {params}")
    print(f"Headers: {debug_headers}")

    try:
        response = requests.get(
            f"{API_URL}/capsules/{capsule_id}", headers=debug_headers, params=params
        )

        print(f"Response status: {response.status_code}")
        print(f"Actual request URL: {response.request.url}")

        if response.status_code == 200:
            data = response.json()
            has_raw = "raw_data" in data
            print(f"Has raw_data: {has_raw}")
            print(f"Keys: {sorted(data.keys())[:10]}...")
            return has_raw
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Request error: {e}")
        return False


# Test integration-test-style request
def test_integration_request(capsule_id):
    print("\n=== Integration test-style request ===")
    params = {"include_raw": "true"}
    print(f"Request URL: {API_URL}/capsules/{capsule_id}")
    print(f"Params: {params}")
    print(f"Headers: {HEADERS}")

    try:
        response = requests.get(
            f"{API_URL}/capsules/{capsule_id}", headers=HEADERS, params=params
        )

        print(f"Response status: {response.status_code}")
        print(f"Actual request URL: {response.request.url}")

        if response.status_code == 200:
            data = response.json()
            has_raw = "raw_data" in data
            print(f"Has raw_data: {has_raw}")
            print(f"Keys: {sorted(data.keys())[:10]}...")
            return has_raw
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Request error: {e}")
        return False


# Test direct URL approach
def test_direct_url(capsule_id):
    print("\n=== Direct URL request ===")
    direct_url = f"{API_URL}/capsules/{capsule_id}?include_raw=true"
    print(f"Direct URL: {direct_url}")
    print(f"Headers: {HEADERS}")

    try:
        response = requests.get(direct_url, headers=HEADERS)

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            has_raw = "raw_data" in data
            print(f"Has raw_data: {has_raw}")
            print(f"Keys: {sorted(data.keys())[:10]}...")
            return has_raw
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Request error: {e}")
        return False


# Main execution
if __name__ == "__main__":
    capsule_id = create_test_capsule()
    if not capsule_id:
        print("Cannot proceed without a test capsule")
        sys.exit(1)

    # Add a small delay to ensure capsule is fully saved
    time.sleep(1)

    debug_result = test_debug_request(capsule_id)
    integration_result = test_integration_request(capsule_id)
    direct_result = test_direct_url(capsule_id)

    print("\n=== COMPARISON RESULTS ===")
    print(f"Debug-style request has raw_data: {debug_result}")
    print(f"Integration-style request has raw_data: {integration_result}")
    print(f"Direct URL request has raw_data: {direct_result}")

    if debug_result == integration_result == direct_result:
        print("All approaches are CONSISTENT!")
        if debug_result:
            print("✅ All approaches include raw data as expected")
        else:
            print("❌ No approach includes raw data - endpoint still broken")
    else:
        print("WARNING: Inconsistent behavior detected!")
        print("This indicates a subtle difference in request handling")
