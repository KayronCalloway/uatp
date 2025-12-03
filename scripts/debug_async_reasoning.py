#!/usr/bin/env python3
"""
Debug script to test the /reasoning/generate endpoint under load
and diagnose 500 INTERNAL SERVER ERROR issues.
"""

import json
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import requests

# Load API key from test file
API_KEY_FILE = os.path.join(os.path.dirname(__file__), "test_api_keys.json")
API_BASE_URL = "http://localhost:9090"  # Update if your server is on a different port


def load_api_key():
    """Load API key from test file - handles dict format with keys as the API keys themselves"""
    try:
        with open(API_KEY_FILE) as f:
            keys_dict = json.load(f)
            # The keys in the dict are the actual API keys
            if keys_dict and len(keys_dict) > 0:
                # Return the first key that has write permissions
                for api_key, details in keys_dict.items():
                    if "roles" in details and "write" in details["roles"]:
                        print(f"Using API key with write permissions: {api_key[:5]}...")
                        return api_key
                # If no key with write permission is found, return the first key
                api_key = next(iter(keys_dict))
                print(
                    f"No key with write permissions found, using first key: {api_key[:5]}..."
                )
                return api_key
    except Exception as e:
        print(f"Error loading API key: {e}")
        traceback.print_exc()
    return None


def make_request(session, prompt="Tell me about UATP.", model="gpt-4"):
    """Make a single request to the /reasoning/generate endpoint"""
    api_key = load_api_key()
    if not api_key:
        print("No API key available. Please check the test_api_keys.json file.")
        return None

    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    data = {"prompt": prompt, "model": model}

    try:
        start_time = time.time()
        response = session.post(
            f"{API_BASE_URL}/reasoning/generate", headers=headers, json=data, timeout=30
        )
        end_time = time.time()

        print(
            f"Response status: {response.status_code}, Time: {end_time - start_time:.2f}s"
        )

        if response.status_code == 200 or response.status_code == 201:
            print(
                f"Success! Capsule ID: {response.json().get('capsule_id', 'unknown')}"
            )
            return response.json()
        else:
            print(f"Error response: {response.text}")
            return None
    except Exception as e:
        print(f"Request failed with exception: {e}")
        traceback.print_exc()
        return None


def sequential_test(num_requests=5):
    """Test the endpoint with sequential requests"""
    print(f"\n===== Testing with {num_requests} sequential requests =====")
    session = requests.Session()
    results = []

    for i in range(num_requests):
        print(f"\nRequest {i+1}/{num_requests}")
        result = make_request(session, f"Tell me about UATP (request {i+1})")
        results.append(result)
        time.sleep(1)  # Small delay between requests

    success_count = sum(1 for r in results if r is not None)
    print(f"\nResults: {success_count}/{num_requests} successful requests")


def concurrent_test(num_requests=5, max_workers=3):
    """Test the endpoint with concurrent requests using ThreadPoolExecutor"""
    print(
        f"\n===== Testing with {num_requests} concurrent requests (max_workers={max_workers}) ====="
    )
    session = requests.Session()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(num_requests):
            futures.append(
                executor.submit(
                    make_request,
                    session,
                    f"Tell me about UATP (concurrent request {i+1})",
                )
            )

        # Wait for all futures to complete
        results = [future.result() for future in futures]

    success_count = sum(1 for r in results if r is not None)
    print(f"\nResults: {success_count}/{num_requests} successful requests")


if __name__ == "__main__":
    print("Starting debug test for /reasoning/generate endpoint")

    # First test with sequential requests
    sequential_test(3)

    # Then test with concurrent requests
    concurrent_test(5, max_workers=3)

    print("\nTest completed.")
