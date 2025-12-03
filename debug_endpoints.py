#!/usr/bin/env python3
"""
Debug script for failing endpoints - adds logging to help diagnose issues.
"""

import base64
import json
import zlib

import requests


def debug_endpoints():
    """
    Debug list_capsules compressed response and get_capsule with raw_data inclusion.
    This will make direct API calls and analyze the responses.
    """
    print("=== DEBUGGING UATP CAPSULE ENGINE API ===")
    api_url = "http://127.0.0.1:5006"
    headers = {"X-API-Key": "test-key-123"}

    # 1. Test list_capsules with compression
    print("\nTesting list_capsules with compression:")
    response = requests.get(
        f"{api_url}/capsules", headers=headers, params={"compress": "true"}
    )

    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Response type: {type(response.json())}")

    # Try to manually check if we can get the compressed data
    try:
        data = response.json()
        print(
            f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dictionary'}"
        )
        if isinstance(data, dict) and "compressed" in data and data["compressed"]:
            print("Response is properly formatted as a dictionary with compressed=True")
            if "data" in data:
                print("Response contains compressed data field")
                # Try to decompress
                try:
                    compressed_bytes = base64.b64decode(data["data"])
                    decompressed_bytes = zlib.decompress(compressed_bytes)
                    decompressed_data = json.loads(decompressed_bytes.decode("utf-8"))
                    print(
                        f"Successfully decompressed data, found {len(decompressed_data)} items"
                    )
                except Exception as e:
                    print(f"Error decompressing data: {e}")
            else:
                print("Response does not contain data field")
        else:
            print("Response does not have the expected compressed format")
    except Exception as e:
        print(f"Error parsing response: {e}")

    # 2. Test get_capsule with raw_data
    print("\nTesting get_capsule with raw_data:")
    # First, list capsules to get a valid ID
    response = requests.get(f"{api_url}/capsules", headers=headers)
    capsule_id = None
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            capsule_id = data[0].get("capsule_id")
            print(f"Found capsule ID: {capsule_id}")

    if capsule_id:
        response = requests.get(
            f"{api_url}/capsules/{capsule_id}",
            headers=headers,
            params={"include_raw": "true"},
        )
        print(f"Status Code: {response.status_code}")

        try:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            if "raw_data" in data:
                print("Response contains raw_data field")
                print(f"raw_data type: {type(data['raw_data'])}")
                print(
                    f"raw_data keys: {list(data['raw_data'].keys()) if isinstance(data['raw_data'], dict) else 'Not a dictionary'}"
                )
            else:
                print("Response does not contain raw_data field")
                print(f"Available keys: {list(data.keys())}")
        except Exception as e:
            print(f"Error parsing response: {e}")
    else:
        print("Could not find a valid capsule ID to test")

    print("\n=== DEBUG COMPLETE ===")


if __name__ == "__main__":
    debug_endpoints()
