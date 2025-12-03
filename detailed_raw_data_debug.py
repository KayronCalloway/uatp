#!/usr/bin/env python3
"""
Detailed debug script for raw data inclusion in get_capsule endpoint.
This script will trace the entire request-response cycle for raw data inclusion.
"""

import json
import os
import sys
import time

import requests

# Test configuration
API_HOST = os.getenv("UATP_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("UATP_API_PORT", "9090"))
API_URL = f"http://{API_HOST}:{API_PORT}"
TEST_API_KEYS_FILE = os.path.join(os.path.dirname(__file__), "tests/test_api_keys.json")

# Print debug information
print(f"API URL: {API_URL}")
print(f"API keys file path: {TEST_API_KEYS_FILE}")
print(f"API keys file exists: {os.path.exists(TEST_API_KEYS_FILE)}")

# Get API key
api_key = "test-key-123"  # Default
if os.path.exists(TEST_API_KEYS_FILE):
    with open(TEST_API_KEYS_FILE) as f:
        keys = json.load(f)
        api_key = next(iter(keys.keys()))
        print(f"Using API key: {api_key}")
else:
    print("WARNING: API keys file not found, using default key")

# Headers
headers = {
    "X-API-Key": api_key,
    "X-Request-ID": "debug-raw-data-test",
    "Content-Type": "application/json",
}

# First get a list of capsules to use for testing
try:
    response = requests.get(f"{API_URL}/capsules", headers=headers, timeout=10)

    if response.status_code == 200:
        capsules = response.json()
        print(f"Found {len(capsules)} capsules")

        if len(capsules) > 0:
            # Use the first capsule ID for testing
            capsule_id = capsules[0]["capsule_id"]
            print(f"Using capsule ID: {capsule_id}")
        else:
            print("No capsules found, cannot proceed")
            sys.exit(1)
    else:
        print(f"Failed to get capsules: {response.status_code} - {response.text}")
        sys.exit(1)
except Exception as e:
    print(f"Error getting capsules: {e}")
    sys.exit(1)

# Now let's test various ways of requesting raw data
test_params = [
    {"include_raw": "true"},
    {"include_raw": True},
    {"include_raw": "1"},
    {"include_raw": "yes"},
    {"include_raw": "t"},
    {"include_raw": "y"},
]

for i, params in enumerate(test_params):
    print(f"\n== Test {i+1}: {params} ==")
    param_str = "&".join([f"{k}={v}" for k, v in params.items()])
    print(f"Request URL: {API_URL}/capsules/{capsule_id}?{param_str}")

    try:
        response = requests.get(
            f"{API_URL}/capsules/{capsule_id}",
            params=params,
            headers=headers,
            timeout=10,
        )

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            has_raw = "raw_data" in data
            print(f"Has raw_data: {has_raw}")

            # Print out all keys for debugging
            keys = sorted(data.keys())
            print(f"Available keys: {keys}")

            # Print actual request URL with query parameters
            print(f"Actual request URL: {response.request.url}")

            # Print any additional debug data from the response headers
            if "X-Debug-Info" in response.headers:
                print(f"Server debug info: {response.headers['X-Debug-Info']}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Error during request: {e}")

    # Add a small delay between requests
    time.sleep(0.5)

print("\n== Testing Direct URL access ==")
# Try direct URL access with the query parameter in the URL
direct_url = f"{API_URL}/capsules/{capsule_id}?include_raw=true"
print(f"Direct URL request: {direct_url}")

try:
    response = requests.get(direct_url, headers=headers, timeout=10)

    print(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        has_raw = "raw_data" in data
        print(f"Has raw_data: {has_raw}")

        # Print out all keys for debugging
        keys = sorted(data.keys())
        print(f"Available keys: {keys}")
    else:
        print(f"Error response: {response.text}")
except Exception as e:
    print(f"Error during direct URL request: {e}")
