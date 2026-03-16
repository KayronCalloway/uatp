"""
Test the UATP SDK against the live backend
"""

import json
from datetime import datetime

import requests


# Test creating a capsule directly via API
def test_create_capsule_direct():
    print("=" * 60)
    print("TEST 1: Create capsule via direct API call")
    print("=" * 60)

    url = "http://localhost:8000/capsules"

    # Format that current backend expects
    capsule_data = {
        "type": "reasoning_trace",
        "version": "1.0",
        "payload": {
            "task": "Book doctor appointment",
            "decision": "Booked Dr. Smith for Dec 17 at 3PM",
            "reasoning_chain": [
                {
                    "step": 1,
                    "thought": "User requested Tuesday afternoon",
                    "confidence": 0.95,
                },
                {
                    "step": 2,
                    "thought": "Found available slot at 3PM",
                    "confidence": 0.92,
                },
            ],
            "confidence": 0.93,
            "metadata": {
                "model": "test-model",
                "timestamp": datetime.utcnow().isoformat(),
            },
        },
    }

    try:
        response = requests.post(url, json=capsule_data)
        response.raise_for_status()
        result = response.json()

        print("[OK] Success!")
        print(f"Capsule ID: {result['capsule_id']}")
        print(f"Message: {result['message']}")

        return result["capsule_id"]

    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        if hasattr(e, "response"):
            print(f"Response: {e.response.text}")
        return None


def test_retrieve_capsule(capsule_id):
    print("\n" + "=" * 60)
    print("TEST 2: Retrieve capsule")
    print("=" * 60)

    url = "http://localhost:8000/capsules?demo_mode=false&per_page=1"

    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()

        if result["capsules"]:
            capsule = result["capsules"][0]
            print("[OK] Retrieved capsule:")
            print(f"ID: {capsule['capsule_id']}")
            print(f"Type: {capsule['type']}")
            print(f"Status: {capsule['status']}")

            if "payload" in capsule and "task" in capsule["payload"]:
                print(f"Task: {capsule['payload']['task']}")
                print(f"Decision: {capsule['payload'].get('decision', 'N/A')}")
        else:
            print("[ERROR] No capsules found")

    except Exception as e:
        print(f"[ERROR] Failed: {e}")


def test_verify_capsule(capsule_id):
    print("\n" + "=" * 60)
    print("TEST 3: Verify capsule signature")
    print("=" * 60)

    url = f"http://localhost:8000/capsules/{capsule_id}/verify"

    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()

        print("[OK] Verification result:")
        print(f"Verified: {result['verified']}")
        print(f"Message: {result['message']}")

    except Exception as e:
        print(f"[ERROR] Failed: {e}")


def test_stats():
    print("\n" + "=" * 60)
    print("TEST 4: Get capsule stats")
    print("=" * 60)

    url = "http://localhost:8000/capsules/stats?demo_mode=false"

    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()

        print("[OK] Stats:")
        print(f"Total capsules: {result['total_capsules']}")
        print(f"By type: {json.dumps(result['capsules_by_type'], indent=2)}")

    except Exception as e:
        print(f"[ERROR] Failed: {e}")


if __name__ == "__main__":
    print("\n UATP SDK Test Suite")
    print("Testing against: http://localhost:8000")
    print()

    # Run tests
    capsule_id = test_create_capsule_direct()

    if capsule_id:
        test_verify_capsule(capsule_id)

    test_retrieve_capsule(capsule_id)
    test_stats()

    print("\n" + "=" * 60)
    print("[OK] All tests completed!")
    print("=" * 60)
