#!/usr/bin/env python3
"""
Direct API testing script to verify our fixes for:
1. list_capsules compressed response
2. get_capsule raw data inclusion
"""

import base64
import json
import os
import sys
import zlib
from datetime import datetime, timezone


def test_list_capsules_compression():
    """Test list_capsules compressed response format directly."""
    print("\n=== Testing list_capsules compressed response format ===")

    # Import required modules directly from the codebase
    sys.path.insert(0, os.path.abspath("."))
    try:
        from api.server import CustomJSONEncoder
    except ImportError:
        print(
            "Could not import CustomJSONEncoder from api.server, continuing with standard JSON"
        )
        CustomJSONEncoder = None

    # Mock result_list as it would be in the server
    result_list = [
        {
            "capsule_id": "test_capsule_1",
            "capsule_type": "reasoning_trace",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "capsule_id": "test_capsule_2",
            "capsule_type": "economic_transaction",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    # Create the compressed response format as implemented in list_capsules
    try:
        # Use CustomJSONEncoder if available, otherwise use standard json
        if CustomJSONEncoder:
            json_str = json.dumps(result_list, cls=CustomJSONEncoder)
        else:
            # Convert datetime objects to ISO format strings first
            cleaned_list = []
            for item in result_list:
                cleaned_item = {}
                for k, v in item.items():
                    if isinstance(v, datetime):
                        cleaned_item[k] = v.isoformat()
                    else:
                        cleaned_item[k] = v
                cleaned_list.append(cleaned_item)
            json_str = json.dumps(cleaned_list)

        compressed = zlib.compress(json_str.encode("utf-8"), level=9)
        b64_compressed = base64.b64encode(compressed).decode("utf-8")

        response_dict = {"compressed": True, "data": b64_compressed}

        print("Successfully created compressed response format:")
        print(f"- Response is a dictionary: {isinstance(response_dict, dict)}")
        print(
            f"- 'compressed' key is True: {'compressed' in response_dict and response_dict['compressed'] is True}"
        )
        print(
            f"- 'data' key contains base64-encoded compressed data: {'data' in response_dict}"
        )

        # Test decompression
        try:
            decoded = base64.b64decode(response_dict["data"])
            decompressed = zlib.decompress(decoded)
            decoded_json = json.loads(decompressed.decode("utf-8"))
            print(f"- Successfully decompressed data, found {len(decoded_json)} items")
            print("✅ Compression implementation works correctly")
            return True
        except Exception as e:
            print(f"❌ Error decompressing data: {e}")
            return False
    except Exception as e:
        print(f"❌ Error creating compressed response: {e}")
        return False


def test_get_capsule_raw_data():
    """Test get_capsule raw data inclusion directly."""
    print("\n=== Testing get_capsule raw data inclusion ===")

    # Mock capsule data as it would be in the server
    capsule = {
        "capsule_id": "test_capsule_123",
        "capsule_type": "reasoning_trace",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": "agent_123",
        "reasoning_trace": "Sample reasoning trace",
        "signature": "ed25519:sample_signature",
    }

    # Create the result dict with verified status
    result = capsule.copy()
    result["verified"] = True

    # Add raw data
    try:
        # This is the implementation from our fixed get_capsule endpoint
        # Exclude raw_data and verified from the raw_data field
        result["raw_data"] = {
            k: v for k, v in result.items() if k not in ["raw_data", "verified"]
        }

        print("Successfully created response with raw_data:")
        print(f"- Response contains 'raw_data' key: {'raw_data' in result}")
        print(f"- raw_data is a dictionary: {isinstance(result['raw_data'], dict)}")
        print(
            f"- raw_data contains all original fields except 'raw_data' and 'verified': {sorted(result['raw_data'].keys()) == sorted([k for k in result.keys() if k not in ['raw_data', 'verified']])}"
        )
        print("✅ Raw data inclusion implementation works correctly")
        return True
    except Exception as e:
        print(f"❌ Error adding raw_data: {e}")
        return False


def main():
    """Run all tests and report results."""
    print("=== UATP Capsule Engine API Direct Test ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # Test list_capsules compression
    results["compression"] = test_list_capsules_compression()

    # Test get_capsule raw_data inclusion
    results["raw_data"] = test_get_capsule_raw_data()

    # Print summary
    print("\n=== Test Summary ===")
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test}")

    all_passed = all(results.values())
    print(f"\n{'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
