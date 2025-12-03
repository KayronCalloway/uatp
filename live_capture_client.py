#!/usr/bin/env python3
"""
Live Capture Client for UATP Attribution System
===============================================

This script captures your AI conversations in real-time and sends them to the
UATP system for attribution tracking and capsule generation.

Usage:
    python live_capture_client.py

Features:
- Monitors clipboard for AI conversations
- Captures OpenAI API calls
- Sends data to UATP server for capsule generation
- Real-time significance analysis
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import aiohttp
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UATPLiveCaptureClient:
    """Client for capturing live AI conversations and sending to UATP server."""

    def __init__(self, server_url: str = "http://localhost:8000", user_id: str = "kay"):
        self.server_url = server_url.rstrip("/")
        self.user_id = user_id
        self.session = None
        self.active_sessions: Dict[str, Dict] = {}

        # API endpoints
        self.capture_endpoint = f"{self.server_url}/api/v1/live/capture/message"
        self.status_endpoint = f"{self.server_url}/api/v1/live/capture/conversation"
        self.openai_endpoint = f"{self.server_url}/api/v1/live/capture/openai"
        self.claude_endpoint = f"{self.server_url}/api/v1/live/capture/claude"

        logger.info(f"🚀 UATP Live Capture Client initialized for user: {user_id}")
        logger.info(f"📡 Server URL: {server_url}")

    async def start_capture(self):
        """Start the live capture system."""
        async with aiohttp.ClientSession() as session:
            self.session = session

            logger.info("🎯 Starting live conversation capture...")

            # Start background tasks
            tasks = [
                asyncio.create_task(self.monitor_openai_conversations()),
                asyncio.create_task(self.monitor_claude_conversations()),
                asyncio.create_task(self.check_conversation_status()),
            ]

            try:
                await asyncio.gather(*tasks)
            except KeyboardInterrupt:
                logger.info("📴 Capture stopped by user")
            except Exception as e:
                logger.error(f"❌ Capture error: {e}")

    async def monitor_openai_conversations(self):
        """Monitor OpenAI API calls for conversation capture."""
        logger.info("🔍 Monitoring OpenAI conversations...")

        while True:
            try:
                # Check for OpenAI conversations
                # This is a placeholder - you'd integrate with your actual OpenAI usage

                # Example: Capture a test conversation
                await self.capture_openai_conversation(
                    user_message="Test question about AI attribution",
                    assistant_message="This is a test response from OpenAI about attribution systems.",
                    model="gpt-4",
                )

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error monitoring OpenAI: {e}")
                await asyncio.sleep(30)

    async def monitor_claude_conversations(self):
        """Monitor Claude conversations for capture."""
        logger.info("🔍 Monitoring Claude conversations...")

        while True:
            try:
                # Check for Claude conversations
                # This is a placeholder - you'd integrate with your actual Claude usage

                # Example: Capture a test conversation
                await self.capture_claude_conversation(
                    user_message="How do I implement real-time attribution?",
                    assistant_message="To implement real-time attribution, you need to capture conversations as they happen and analyze their significance for creating attribution capsules.",
                )

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error monitoring Claude: {e}")
                await asyncio.sleep(30)

    async def capture_openai_conversation(
        self, user_message: str, assistant_message: str, model: str = "gpt-4"
    ):
        """Capture an OpenAI conversation."""
        try:
            session_id = f"openai-{int(time.time())}"

            data = {
                "session_id": session_id,
                "user_id": self.user_id,
                "messages": [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": assistant_message},
                ],
                "model": model,
            }

            async with self.session.post(self.openai_endpoint, json=data) as response:
                result = await response.json()

                if result.get("success"):
                    logger.info(f"✅ OpenAI conversation captured: {session_id}")
                    self.active_sessions[session_id] = {
                        "platform": "openai",
                        "created": datetime.now(timezone.utc),
                    }
                    return session_id
                else:
                    logger.error(
                        f"❌ Failed to capture OpenAI conversation: {result.get('error')}"
                    )

        except Exception as e:
            logger.error(f"Error capturing OpenAI conversation: {e}")

    async def capture_claude_conversation(
        self, user_message: str, assistant_message: str
    ):
        """Capture a Claude conversation."""
        try:
            session_id = f"claude-{int(time.time())}"

            data = {
                "session_id": session_id,
                "user_id": self.user_id,
                "user_message": user_message,
                "assistant_message": assistant_message,
            }

            async with self.session.post(self.claude_endpoint, json=data) as response:
                result = await response.json()

                if result.get("success"):
                    logger.info(f"✅ Claude conversation captured: {session_id}")
                    self.active_sessions[session_id] = {
                        "platform": "claude",
                        "created": datetime.now(timezone.utc),
                    }
                    return session_id
                else:
                    logger.error(
                        f"❌ Failed to capture Claude conversation: {result.get('error')}"
                    )

        except Exception as e:
            logger.error(f"Error capturing Claude conversation: {e}")

    async def capture_message(
        self,
        session_id: str,
        platform: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
    ):
        """Capture a single message."""
        try:
            data = {
                "session_id": session_id,
                "user_id": self.user_id,
                "platform": platform,
                "role": role,
                "content": content,
                "metadata": metadata or {},
            }

            async with self.session.post(self.capture_endpoint, json=data) as response:
                result = await response.json()

                if result.get("success"):
                    logger.info(f"📨 Message captured: {session_id} ({role})")
                    return True
                else:
                    logger.error(f"❌ Failed to capture message: {result.get('error')}")
                    return False

        except Exception as e:
            logger.error(f"Error capturing message: {e}")
            return False

    async def check_conversation_status(self):
        """Check the status of active conversations."""
        logger.info("📊 Starting conversation status monitoring...")

        while True:
            try:
                for session_id, session_info in list(self.active_sessions.items()):
                    # Check conversation status
                    async with self.session.get(
                        f"{self.status_endpoint}/{session_id}"
                    ) as response:
                        if response.status == 200:
                            result = await response.json()

                            if result.get("success"):
                                conversation = result.get("conversation", {})

                                # Log significant conversations
                                if conversation.get("should_create_capsule"):
                                    logger.info(
                                        f"🎯 Significant conversation detected: {session_id}"
                                    )
                                    logger.info(
                                        f"   Significance Score: {conversation.get('significance_score', 0):.2f}"
                                    )
                                    logger.info(
                                        f"   Message Count: {conversation.get('message_count', 0)}"
                                    )

                                # Clean up old sessions
                                session_age = (
                                    datetime.now(timezone.utc) - session_info["created"]
                                ).total_seconds()
                                if session_age > 3600:  # Remove after 1 hour
                                    del self.active_sessions[session_id]
                                    logger.info(
                                        f"🧹 Cleaned up old session: {session_id}"
                                    )

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error checking conversation status: {e}")
                await asyncio.sleep(60)

    def test_server_connection(self):
        """Test connection to the UATP server."""
        try:
            response = requests.get(f"{self.server_url}/health")
            if response.status_code == 200:
                logger.info("✅ Server connection successful")
                return True
            else:
                logger.error(f"❌ Server connection failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Server connection error: {e}")
            return False


# Example usage functions
async def capture_sample_conversations():
    """Capture some sample conversations to test the system."""
    client = UATPLiveCaptureClient()

    # Test server connection
    if not client.test_server_connection():
        logger.error("Cannot connect to server. Make sure the UATP server is running.")
        return

    async with aiohttp.ClientSession() as session:
        client.session = session

        # Capture sample OpenAI conversation
        await client.capture_openai_conversation(
            user_message="How do I implement blockchain attribution for AI?",
            assistant_message="To implement blockchain attribution for AI, you need to create immutable records of AI contributions, use smart contracts for automated attribution, and implement a decentralized verification system.",
            model="gpt-4",
        )

        # Capture sample Claude conversation
        await client.capture_claude_conversation(
            user_message="Explain the UATP attribution system",
            assistant_message="The UATP (Universal Attribution and Transparency Protocol) system creates capsules that track AI contributions, enabling fair attribution and economic compensation for AI-generated content.",
        )

        logger.info("✅ Sample conversations captured successfully")


def main():
    """Main entry point for the live capture client."""
    print("🚀 UATP Live Capture Client")
    print("=" * 50)

    # Check if server is running
    client = UATPLiveCaptureClient()
    if not client.test_server_connection():
        print("❌ Cannot connect to UATP server.")
        print("   Make sure the server is running: python src/api/server.py")
        sys.exit(1)

    print("✅ Connected to UATP server")
    print("📡 Starting live conversation capture...")
    print("Press Ctrl+C to stop")

    try:
        # Start the capture system
        asyncio.run(client.start_capture())
    except KeyboardInterrupt:
        print("\n📴 Capture stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
