#!/usr/bin/env python3
"""Capture current conversation via API"""

import requests
import json
from datetime import datetime

# API endpoint
API_URL = "http://localhost:8000"

# Prepare capsule data
capsule_data = {
    "type": "reasoning_trace",
    "content": """USER: ok continue

ASSISTANT: I've completed fixing all 14 dashboards! The Compliance Dashboard was the final one. Let me mark this task as complete and move on to testing.

USER: Runtime ReferenceError: Can't find variable: displayTrustMetrics. And also notifications are simulated still

ASSISTANT: Let me fix these issues right away. I found the hardcoded notifications and the missing displayTrustMetrics variable. Fixed both:
1. Added displayTrustMetrics variable in Trust Dashboard
2. Made notifications respect demo mode - only simulated when isDemoMode is true

USER: ok are capturing live capsules?

ASSISTANT: Based on the backend logs: We have 43 capsules stored (35 reasoning_trace, 6 chat, 1 governance_vote, 1 economic_transaction), but live capture API endpoints are returning 404. The live conversation monitor initialized but endpoints aren't registered.

USER: 1 and 3

ASSISTANT: Perfect! Let me check the live capture routes and enable real-time capture for our session.""",
    "metadata": {
        "session_id": f"claude-code-{int(datetime.now().timestamp())}",
        "user_id": "kay",
        "platform": "claude_code",
        "model": "claude-sonnet-4-5",
        "capture_method": "manual_api",
        "conversation_length": 7,
        "significance_score": 1.0,
        "topic": "demo_mode_integration_and_live_capture",
        "key_points": [
            "Fixed displayTrustMetrics runtime error in Trust Dashboard",
            "Made notifications respect demo mode",
            "Investigated live capture system status",
            "Found 43 existing capsules in database",
            "Identified live capture API endpoint issues",
        ],
    },
}

print("🎯 Capturing conversation via API...")
print(f"📝 Session: {capsule_data['metadata']['session_id']}")

try:
    response = requests.post(
        f"{API_URL}/capsules",
        json=capsule_data,
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 200 or response.status_code == 201:
        result = response.json()
        print(f"✅ Capsule created successfully!")
        print(f"  Capsule ID: {result.get('capsule_id', result.get('id', 'unknown'))}")
        print(f"  Platform: {capsule_data['metadata']['platform']}")
        print(f"  Significance: {capsule_data['metadata']['significance_score']}")
        print(f"\n📊 Verify at: http://localhost:3000")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"  Response: {response.text}")

except Exception as e:
    print(f"❌ Error: {e}")
