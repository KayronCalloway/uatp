#!/usr/bin/env python3
"""
Set up Live Capture for Real Conversations
This script helps you configure live capture for actual AI conversations
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:9090"
API_KEY = "dev-key-001"


def capture_real_conversation(session_id, user_msg, ai_response, platform="manual"):
    """Capture a real conversation interaction."""

    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    # Capture user message
    user_data = {
        "session_id": session_id,
        "user_id": "real-user",
        "platform": platform,
        "role": "user",
        "content": user_msg,
        "metadata": {"timestamp": datetime.utcnow().isoformat(), "real_data": True},
    }

    response = requests.post(
        f"{API_BASE}/api/v1/live/capture/message", headers=headers, json=user_data
    )
    print(f"User message captured: {response.json()}")

    # Capture AI response
    ai_data = {
        "session_id": session_id,
        "user_id": "ai-assistant",
        "platform": platform,
        "role": "assistant",
        "content": ai_response,
        "metadata": {"timestamp": datetime.utcnow().isoformat(), "real_data": True},
    }

    response = requests.post(
        f"{API_BASE}/api/v1/live/capture/message", headers=headers, json=ai_data
    )
    print(f"AI response captured: {response.json()}")


def main():
    print("🎯 Live Capture Setup for Real Data")
    print("=" * 40)

    print("\n📝 Manual conversation capture example:")

    # Example real conversation
    session_id = f"real-session-{int(time.time())}"

    conversations = [
        {
            "user": "How do I implement a secure authentication system?",
            "ai": "To implement secure authentication, use these key principles: 1) Hash passwords with bcrypt or similar, 2) Use JWT tokens with proper expiration, 3) Implement rate limiting, 4) Use HTTPS everywhere, 5) Add two-factor authentication for sensitive operations.",
        },
        {
            "user": "What are the best practices for API security?",
            "ai": "API security best practices include: 1) API key authentication, 2) Rate limiting to prevent abuse, 3) Input validation and sanitization, 4) CORS configuration, 5) Request/response logging, 6) Use API gateways for centralized security controls.",
        },
    ]

    for i, conv in enumerate(conversations):
        print(f"\n🔄 Capturing conversation {i+1}")
        capture_real_conversation(session_id, conv["user"], conv["ai"], "manual-input")
        time.sleep(1)  # Small delay between messages

    print("\n✅ Real conversation data captured!")
    print(f"💡 Session ID: {session_id}")
    print("🔗 Check your Live Capture Dashboard to see the real data!")


if __name__ == "__main__":
    main()
