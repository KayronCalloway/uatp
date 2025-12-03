#!/usr/bin/env python3
"""
Debug script to verify raw data inclusion in get_capsule endpoint
"""

import json
import os
import uuid

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


def debug_get_capsule_with_raw():
    # Load API keys
    try:
        with open(TEST_API_KEYS_FILE) as f:
            api_keys = json.load(f)
            # Get the first key from the dictionary
            api_key = next(iter(api_keys.keys()))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading API key: {e}")
        return

    # Set headers
    headers = {
        "X-API-Key": api_key,
        "X-Request-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }

    # First, list capsules to get an ID
    try:
        response = requests.get(f"{API_URL}/capsules", headers=headers)
        if response.status_code == 200:
            capsules = response.json()
            if not capsules:
                print("No capsules found")
                return
            capsule_id = capsules[0]["capsule_id"]
            print(f"Using capsule ID: {capsule_id}")
        else:
            print(f"Failed to list capsules: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"Error listing capsules: {e}")
        return

    # Test without raw data
    try:
        print("\n== Testing GET /capsules/{capsule_id} without raw data ==")
        response = requests.get(f"{API_URL}/capsules/{capsule_id}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            has_raw = "raw_data" in data
            print(f"Response status: {response.status_code}")
            print(f"Has raw_data: {has_raw}")
            print(f"Available keys: {list(data.keys())}")
        else:
            print(f"Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

    # Test with raw data
    try:
        print("\n== Testing GET /capsules/{capsule_id}?include_raw=true ==")
        response = requests.get(
            f"{API_URL}/capsules/{capsule_id}",
            headers=headers,
            params={"include_raw": "true"},
        )
        if response.status_code == 200:
            data = response.json()
            has_raw = "raw_data" in data
            print(f"Response status: {response.status_code}")
            print(f"Has raw_data: {has_raw}")
            print(f"Available keys: {list(data.keys())}")

            # Debug raw data handling in server.py
            print("\n== Debugging include_raw parameter ==")
            print(f"Request URL: {response.request.url}")
            print(f"Request headers: {response.request.headers}")
        else:
            print(f"Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    debug_get_capsule_with_raw()
