#!/usr/bin/env python3
"""
Debug script to test the list_capsules endpoint with compression.
"""

import requests


def debug_list_capsules_compressed():
    """Test list_capsules endpoint with compression."""
    base_url = "http://127.0.0.1:5006"
    api_key = "test-key-123"

    headers = {"Content-Type": "application/json", "X-API-Key": api_key}

    # Test with explicit compress=true parameter
    params = {"compress": "true"}
    response = requests.get(f"{base_url}/capsules", headers=headers, params=params)

    print(f"Status code: {response.status_code}")
    print(f"Response headers: {response.headers}")

    try:
        data = response.json()
        print(f"Response data type: {type(data)}")
        print(f"Response is dict: {isinstance(data, dict)}")
        print(f"Compressed flag in response: {data.get('compressed', 'NOT PRESENT')}")

        # Pretty print the first few keys
        if isinstance(data, dict):
            print(f"Response keys: {list(data.keys())}")
        elif isinstance(data, list):
            print(f"Response is a list of {len(data)} items")
            if data:
                print(
                    f"First item keys: {list(data[0].keys() if isinstance(data[0], dict) else [])}"
                )
        else:
            print(f"Response is not a dict or list: {data}")

        return True
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Raw response: {response.text[:200]}...")  # Print first 200 chars
        return False


if __name__ == "__main__":
    print("Debug: Testing list_capsules endpoint with compression")
    debug_list_capsules_compressed()
    print("\nDone!")
