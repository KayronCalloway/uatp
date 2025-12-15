#!/usr/bin/env python3
"""
Test script for the UATP Live Capture System
"""

import json
import time
from datetime import datetime

import requests


def test_server_connection():
    """Test if the UATP server is running."""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False


def test_capture_endpoints():
    """Test the live capture endpoints."""
    print("\n🧪 Testing capture endpoints...")

    # Test OpenAI capture
    print("1. Testing OpenAI capture...")
    openai_data = {
        "session_id": f"test-openai-{int(time.time())}",
        "user_id": "kay",
        "messages": [
            {"role": "user", "content": "How do I implement real-time attribution?"},
            {
                "role": "assistant",
                "content": "To implement real-time attribution, you need to capture conversations as they happen and analyze their significance for creating attribution capsules.",
            },
        ],
        "model": "gpt-4",
    }

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/live/capture/openai", json=openai_data
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("   ✅ OpenAI capture successful")
                session_id = result.get("session_id")

                # Test conversation status
                status_response = requests.get(
                    f"http://localhost:8000/api/v1/live/capture/conversation/{session_id}"
                )
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    if status_result.get("success"):
                        print("   ✅ Conversation status retrieval successful")
                        conv = status_result.get("conversation", {})
                        print(f"      Messages: {conv.get('message_count', 0)}")
                        print(
                            f"      Significance: {conv.get('significance_score', 0):.2f}"
                        )
                    else:
                        print("   ❌ Conversation status retrieval failed")
                else:
                    print("   ❌ Conversation status endpoint failed")
            else:
                print(f"   ❌ OpenAI capture failed: {result.get('error')}")
        else:
            print(f"   ❌ OpenAI endpoint returned status {response.status_code}")
    except Exception as e:
        print(f"   ❌ OpenAI capture error: {e}")

    # Test Claude capture
    print("\n2. Testing Claude capture...")
    claude_data = {
        "session_id": f"test-claude-{int(time.time())}",
        "user_id": "kay",
        "user_message": "What is the UATP attribution system?",
        "assistant_message": "The UATP system creates capsules that track AI contributions, enabling fair attribution and economic compensation for AI-generated content.",
    }

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/live/capture/claude", json=claude_data
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("   ✅ Claude capture successful")
            else:
                print(f"   ❌ Claude capture failed: {result.get('error')}")
        else:
            print(f"   ❌ Claude endpoint returned status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Claude capture error: {e}")

    # Test active conversations list
    print("\n3. Testing active conversations list...")
    try:
        response = requests.get(
            "http://localhost:8000/api/v1/live/capture/conversations"
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                conversations = result.get("conversations", [])
                print(f"   ✅ Active conversations: {len(conversations)}")
                for conv in conversations[:3]:  # Show first 3
                    print(
                        f"      - {conv.get('session_id')} ({conv.get('platform')}) - {conv.get('message_count')} messages"
                    )
            else:
                print(f"   ❌ Conversations list failed: {result.get('error')}")
        else:
            print(
                f"   ❌ Conversations endpoint returned status {response.status_code}"
            )
    except Exception as e:
        print(f"   ❌ Conversations list error: {e}")


def test_capsule_creation():
    """Test if capsules are being created from the captured conversations."""
    print("\n🎯 Testing capsule creation...")

    # Check if capsules were created
    import os

    capsule_file = "capsule_chain.jsonl"

    if os.path.exists(capsule_file):
        # Count lines in the file
        with open(capsule_file) as f:
            lines = f.readlines()

        print(f"✅ Capsule chain file exists with {len(lines)} capsules")

        # Check for recent capsules
        recent_capsules = []
        current_time = datetime.now().timestamp()

        for line in lines[-10:]:  # Check last 10 capsules
            try:
                capsule = json.loads(line)
                capsule_time = datetime.fromisoformat(
                    capsule.get("timestamp", "").replace("Z", "+00:00")
                ).timestamp()

                # If capsule is less than 5 minutes old
                if current_time - capsule_time < 300:
                    recent_capsules.append(capsule)
            except:
                continue

        if recent_capsules:
            print(f"✅ Found {len(recent_capsules)} recent capsules")
            for capsule in recent_capsules[:3]:
                print(f"   - {capsule.get('capsule_id')} ({capsule.get('type')})")
        else:
            print(
                "⚠️  No recent capsules found (may need to wait for significance analysis)"
            )
    else:
        print("❌ Capsule chain file not found")


def main():
    """Run the test suite."""
    print("🧪 UATP Live Capture System Test Suite")
    print("=" * 50)

    # Test server connection
    if not test_server_connection():
        print("\n❌ Server is not running. Please start the server first:")
        print("   python src/api/server.py")
        return

    # Test capture endpoints
    test_capture_endpoints()

    # Wait a bit for processing
    print("\n⏳ Waiting 10 seconds for processing...")
    time.sleep(10)

    # Test capsule creation
    test_capsule_creation()

    print("\n✅ Test suite completed!")
    print("\nNext steps:")
    print("1. Run the live capture client: python live_capture_client.py")
    print("2. Open the visualizer: python -m streamlit run visualizer/app.py")
    print("3. Start having AI conversations to see real-time attribution!")


if __name__ == "__main__":
    main()
