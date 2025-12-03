#!/usr/bin/env python3
"""Test the live capture API endpoint."""

import requests
import json

API_BASE = "http://localhost:8000"
API_KEY = "test-api-key"

headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# Test message data
message_data = {
    "session_id": "test-session-123",
    "user_id": "kay",
    "platform": "claude_code_test",
    "role": "user",
    "content": "This is a test message to verify the live capture API works correctly.",
}

print("Testing live capture API...")
print(f"URL: {API_BASE}/live/capture/message")
print(f"Data: {json.dumps(message_data, indent=2)}")
print()

try:
    response = requests.post(
        f"{API_BASE}/live/capture/message",
        headers=headers,
        json=message_data,
        timeout=5,
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.ok:
        print("\n✅ API works correctly!")
    else:
        print("\n❌ API returned an error")

except Exception as e:
    print(f"\n❌ Exception: {e}")
