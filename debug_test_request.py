#!/usr/bin/env python3
"""
Debug script to emulate exactly what the integration test is doing for raw data.
"""

import json
import os
import sys

import requests

# Test configuration
API_HOST = os.getenv("UATP_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("UATP_API_PORT", "9090"))
API_URL = f"http://{API_HOST}:{API_PORT}"
TEST_API_KEYS_FILE = os.path.join(os.path.dirname(__file__), "tests/test_api_keys.json")

print(f"API URL: {API_URL}")
print(
    f"API keys file: {TEST_API_KEYS_FILE} (exists: {os.path.exists(TEST_API_KEYS_FILE)})"
)

# Load API key from test file
api_key = "test-key-123"
if os.path.exists(TEST_API_KEYS_FILE):
    with open(TEST_API_KEYS_FILE) as f:
        keys = json.load(f)
        api_key = list(keys.keys())[0]
        print(f"Using API key: {api_key}")

# Set up headers exactly like the integration test
HEADERS = {
    "X-API-Key": api_key,
    "X-Request-ID": "debug-integration-test",
    "Content-Type": "application/json",
}

# First, get a new capsule using the create_capsule endpoint just like the test
try:
    # Create a new capsule for testing
    test_data = {
        "capsule_type": "consent",
        "confidence": 0.95,  # Required field
        "consent_details": {
            "purpose": "Integration Test",
            "scope": "API",
            "duration": "1h",
        },
    }

    response = requests.post(f"{API_URL}/capsules", headers=HEADERS, json=test_data)

    if response.status_code == 201:
        capsule_id = response.json().get("capsule_id")
        print(f"Created test capsule with ID: {capsule_id}")
    else:
        print(f"Failed to create test capsule: {response.status_code}")
        print(response.text)
        sys.exit(1)
except Exception as e:
    print(f"Error creating test capsule: {str(e)}")
    sys.exit(1)

# Now test get_capsule with raw data exactly as the integration test does
try:
    # This is EXACTLY how the test makes the call
    params = {"include_raw": "true"}
    response = requests.get(
        f"{API_URL}/capsules/{capsule_id}", headers=HEADERS, params=params
    )

    print(f"Response status: {response.status_code}")
    print(f"Response headers: {response.headers}")

    # Print request details for debugging
    print(f"Request URL: {response.request.url}")
    print(f"Request headers: {response.request.headers}")

    if response.status_code == 200:
        data = response.json()
        has_raw = "raw_data" in data
        print(f"Has raw_data: {has_raw}")

        # Print all available keys
        print(f"Available keys: {sorted(data.keys())}")

        if not has_raw:
            print("ERROR: Raw data not included in response!")
        else:
            print("SUCCESS: Raw data included in response!")
    else:
        print(f"Error response: {response.text}")
except Exception as e:
    print(f"Error: {str(e)}")
