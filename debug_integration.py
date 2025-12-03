#!/usr/bin/env python3
"""
Debug script for troubleshooting integration test failures.
This script runs just the raw data test portion of the integration test with debugging.
"""

import json
import os
import sys

import requests

# Import the test code directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tests.test_api_endpoints import API_URL, HEADERS

print(f"DEBUG: Using API URL: {API_URL}")
print(f"DEBUG: Using headers: {HEADERS}")

# Create a test capsule first
try:
    test_data = {
        "capsule_type": "consent",
        "confidence": 0.95,
        "consent_details": {"purpose": "Debug Test", "scope": "API", "duration": "1h"},
    }

    print(f"DEBUG: Creating test capsule with data: {json.dumps(test_data)}")

    response = requests.post(f"{API_URL}/capsules", headers=HEADERS, json=test_data)

    print(f"DEBUG: Create response status: {response.status_code}")
    print(f"DEBUG: Create response: {response.text}")

    if response.status_code == 201:
        capsule_id = response.json().get("capsule_id")
        print(f"DEBUG: Created test capsule with ID: {capsule_id}")
    else:
        print(f"DEBUG: Failed to create test capsule: {response.status_code}")
        print(response.text)
        sys.exit(1)
except Exception as e:
    print(f"DEBUG: Error creating test capsule: {str(e)}")
    sys.exit(1)

# Now test get_capsule with raw data
try:
    print("\nDEBUG: Testing get_capsule with raw data")
    params = {"include_raw": "true"}

    print(f"DEBUG: Request URL: {API_URL}/capsules/{capsule_id}")
    print(f"DEBUG: Request params: {params}")
    print(f"DEBUG: Request headers: {HEADERS}")

    response = requests.get(
        f"{API_URL}/capsules/{capsule_id}", headers=HEADERS, params=params
    )

    print(f"DEBUG: Response status: {response.status_code}")
    print(f"DEBUG: Response headers: {dict(response.headers)}")

    if response.status_code == 200:
        data = response.json()
        print(f"DEBUG: Response data type: {type(data)}")
        has_raw = "raw_data" in data
        print(f"DEBUG: Has raw_data: {has_raw}")

        # Print keys
        print(f"DEBUG: Available keys: {sorted(data.keys())}")

        # Check using the same logic as the integration test
        if has_raw:
            print("SUCCESS: Raw data included in response!")
        else:
            print("ERROR: Raw data not included in response!")
            print(f"DEBUG: Full response: {json.dumps(data)[:500]}...")
    else:
        print(f"DEBUG: Error response: {response.text}")
except Exception as e:
    print(f"DEBUG: Error during get_capsule: {str(e)}")
    import traceback

    traceback.print_exc()
