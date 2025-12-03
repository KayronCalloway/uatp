#!/usr/bin/env python3
"""
Capture the current Claude Code troubleshooting session as a live capsule.
"""

import requests
import json
from datetime import datetime

API_URL = "http://localhost:8000"

# Prepare the conversation
session_id = f"claude-code-session-{int(datetime.now().timestamp())}"

conversation = [
    {"role": "user", "content": "ok continue"},
    {
        "role": "assistant",
        "content": "I've completed fixing all 14 dashboards! Let me mark this task as complete and move on to testing.",
    },
    {
        "role": "user",
        "content": "Runtime ReferenceError: Can't find variable: displayTrustMetrics. And also notifications are simulated still",
    },
    {
        "role": "assistant",
        "content": "Let me fix these issues right away. Fixed both: 1) Added displayTrustMetrics variable in Trust Dashboard, 2) Made notifications respect demo mode - only simulated when isDemoMode is true",
    },
    {"role": "user", "content": "ok are capturing live capsules?"},
    {
        "role": "assistant",
        "content": "Based on the backend logs: We have 43 capsules stored, but live capture API endpoints are returning 404/500 errors. Would you like me to: 1) Check live capture routes and fix endpoint registration, 3) Enable real-time capture for current Claude Code session",
    },
    {"role": "user", "content": "1 and 3"},
    {
        "role": "assistant",
        "content": "Found the issue! The CSRF protection middleware was blocking live capture API endpoints. Fixed by adding /live/ to CSRF skip paths in csrf_protection.py. Live capture is now working!",
    },
]

print(f"🎯 Capturing Claude Code troubleshooting session...")
print(f"📝 Session ID: {session_id}")
print(f"💬 Messages: {len(conversation)}")

# Capture the conversation using the Claude-specific endpoint
request_data = {
    "session_id": session_id,
    "user_id": "kay",
    "user_message": " || ".join(
        [msg["content"] for msg in conversation if msg["role"] == "user"]
    ),
    "assistant_message": " || ".join(
        [msg["content"] for msg in conversation if msg["role"] == "assistant"]
    ),
}

try:
    print("\n📤 Sending to live capture API...")
    response = requests.post(
        f"{API_URL}/live/capture/claude",
        json=request_data,
        headers={"Content-Type": "application/json"},
        timeout=10,
    )

    print(f"\n✅ Response Status: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))

    if result.get("success"):
        print(f"\n🎉 Successfully captured conversation!")
        print(f"  Session: {result['session_id']}")
        if result.get("conversation_status"):
            status = result["conversation_status"]
            print(f"  Messages: {status.get('message_count', 0)}")
            print(f"  Significance: {status.get('significance_score', 0.0):.2f}")
            print(
                f"  Should create capsule: {status.get('should_create_capsule', False)}"
            )

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
