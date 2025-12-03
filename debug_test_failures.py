#!/usr/bin/env python3
"""
Debug script to test the failing endpoints independently.
"""

import base64
import json
import time
import uuid
import zlib

import requests

BASE_URL = "http://127.0.0.1:5006"
API_KEY = "test-key-123"

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY,
    "X-Request-ID": str(uuid.uuid4()),
}

TEST_CAPSULE = {
    "capsule_type": "debug_test_capsule",
    "confidence": 0.95,
    "reasoning_trace": ["Step 1: Debug API", "Step 2: Verify endpoint"],
    "metadata": {"test_id": str(uuid.uuid4()), "test_name": "debug_api_endpoint_test"},
    "additional_data": {"test_value": "This is a debug test capsule"},
}


def decompress_data(compressed_data):
    """Decompress base64-encoded zlib-compressed data."""
    compressed_bytes = base64.b64decode(compressed_data)
    decompressed_bytes = zlib.decompress(compressed_bytes)
    return json.loads(decompressed_bytes.decode("utf-8"))


def debug_list_capsules_compressed():
    """Debug the list_capsules endpoint with compression."""
    print("\n=== Testing list_capsules with compression ===")

    params = {"compress": "true"}
    response = requests.get(f"{BASE_URL}/capsules", headers=HEADERS, params=params)

    print(f"Status code: {response.status_code}")

    try:
        data = response.json()
        print(f"Response is a dict: {isinstance(data, dict)}")
        print(f"Compressed flag in response: {data.get('compressed', 'NOT PRESENT')}")

        if isinstance(data, dict) and data.get("compressed"):
            print("✓ SUCCESS: Response has compressed flag set to True")
            # Try to decompress the data
            try:
                capsules = decompress_data(data["data"])
                print(
                    f"✓ SUCCESS: Successfully decompressed data with {len(capsules)} capsules"
                )
                return True
            except Exception as e:
                print(f"✗ FAILURE: Failed to decompress data: {str(e)}")
                return False
        else:
            print("✗ FAILURE: Response not properly compressed")
            return False
    except Exception as e:
        print(f"✗ FAILURE: Error processing response: {str(e)}")
        print(f"Raw response: {response.text[:200]}...")
        return False


def debug_get_capsule_with_raw():
    """Debug the get_capsule endpoint with raw data."""
    print("\n=== Testing get_capsule with raw data ===")

    # First create a test capsule
    print("Creating test capsule...")
    create_response = requests.post(
        f"{BASE_URL}/capsules", headers=HEADERS, json=TEST_CAPSULE
    )

    if create_response.status_code != 201:
        print(
            f"✗ FAILURE: Failed to create test capsule: {create_response.status_code}"
        )
        return False

    create_data = create_response.json()
    capsule_id = create_data.get("capsule_id")
    print(f"Created capsule with ID: {capsule_id}")

    # Now request the capsule with raw data
    params = {"include_raw": "true"}
    get_response = requests.get(
        f"{BASE_URL}/capsules/{capsule_id}", headers=HEADERS, params=params
    )

    if get_response.status_code != 200:
        print(f"✗ FAILURE: Failed to get capsule: {get_response.status_code}")
        return False

    data = get_response.json()
    has_raw = "raw_data" in data

    print(f"Response keys: {list(data.keys())}")
    print(f"Has raw_data field: {has_raw}")

    if has_raw:
        print("✓ SUCCESS: Response includes raw_data")
        return True
    else:
        print("✗ FAILURE: Response does not include raw_data")
        return False


def debug_caching():
    """Debug the caching behavior."""
    print("\n=== Testing caching behavior ===")

    # Make first request to ensure it's cached
    start_time = time.time()
    first_response = requests.get(f"{BASE_URL}/capsules", headers=HEADERS)
    first_time = time.time() - start_time

    if first_response.status_code != 200:
        print(f"✗ FAILURE: Failed to get capsules: {first_response.status_code}")
        return False

    print(f"First request time: {first_time:.6f}s")

    # Make second request which should be faster due to caching
    start_time = time.time()
    second_response = requests.get(f"{BASE_URL}/capsules", headers=HEADERS)
    second_time = time.time() - start_time

    if second_response.status_code != 200:
        print(f"✗ FAILURE: Failed to get capsules: {second_response.status_code}")
        return False

    print(f"Second request time: {second_time:.6f}s")

    # Check if second request was faster (indicating cache hit)
    if second_time < first_time:
        print(
            f"✓ SUCCESS: Caching appears to be working (second request faster by {first_time - second_time:.6f}s)"
        )
        return True
    else:
        print(
            f"✗ FAILURE: Second request not faster ({second_time - first_time:.6f}s slower), cache might not be working"
        )
        return False


def run_all_tests():
    """Run all debug tests."""
    results = {
        "list_capsules_compressed": debug_list_capsules_compressed(),
        "get_capsule_with_raw": debug_get_capsule_with_raw(),
        "caching": debug_caching(),
    }

    print("\n=== SUMMARY ===")
    for test, passed in results.items():
        status = "✓ SUCCESS" if passed else "✗ FAILURE"
        print(f"{status}: {test}")


if __name__ == "__main__":
    run_all_tests()
