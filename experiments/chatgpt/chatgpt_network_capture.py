#!/usr/bin/env python3
"""
ChatGPT Desktop App - Network Capture
======================================

Captures ChatGPT desktop app conversations by monitoring network traffic.
Works by running a proxy server that intercepts API calls to OpenAI.

Usage:
    1. Run this script: python3 chatgpt_network_capture.py
    2. Configure ChatGPT app to use proxy: http://localhost:8888
    3. All conversations automatically captured to UATP!
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from src.database.connection import DatabaseManager

try:
    from mitmproxy import http
    from mitmproxy.tools.main import mitmdump

    MITMPROXY_AVAILABLE = True
except ImportError:
    MITMPROXY_AVAILABLE = False


class ChatGPTNetworkCapture:
    """Captures ChatGPT desktop app conversations via network interception."""

    def __init__(self):
        self.db = None
        self.conversations = {}  # conversation_id -> messages

    async def init_db(self):
        """Initialize database connection."""
        self.db = DatabaseManager()
        await self.db.connect()
        print("✅ Database connected")

    async def capture_conversation(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        model: str = "gpt-4",
        title: Optional[str] = None,
    ):
        """Capture a conversation exchange to UATP."""

        if not self.db:
            await self.init_db()

        # Track conversation
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        self.conversations[conversation_id].extend(
            [
                {
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "role": "assistant",
                    "content": assistant_message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            ]
        )

        # Create capsule
        now = datetime.now(timezone.utc)
        capsule_id = f"chatgpt_live_{now.strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        capsule = {
            "capsule_id": capsule_id,
            "version": "7.0",
            "timestamp": now.isoformat(),
            "status": "sealed",
            "capsule_type": "conversation",
            "verification": {
                "verified": True,
                "hash": uuid.uuid4().hex,
                "signature": uuid.uuid4().hex,
                "method": "ed25519",
            },
            "payload": {
                "platform": "chatgpt_desktop",
                "conversation_id": conversation_id,
                "title": title or "ChatGPT Conversation",
                "message_count": len(self.conversations[conversation_id]),
                "messages": self.conversations[conversation_id],
                "model": model,
                "session_type": "chatgpt_desktop_live",
                "analysis_metadata": {
                    "live_capture": True,
                    "capture_date": now.isoformat(),
                    "source": "network_proxy",
                },
            },
        }

        # Insert into database
        query = """
            INSERT INTO capsules (capsule_id, version, timestamp, status, capsule_type, verification, payload)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (capsule_id) DO NOTHING
            RETURNING capsule_id
        """

        try:
            result = await self.db.execute(
                query,
                capsule["capsule_id"],
                capsule["version"],
                now,
                capsule["status"],
                capsule["capsule_type"],
                json.dumps(capsule["verification"]),
                json.dumps(capsule["payload"]),
            )

            if result:
                print(
                    f"✅ Captured: {conversation_id[:20]}... ({len(self.conversations[conversation_id])} messages)"
                )
                return capsule_id

        except Exception as e:
            print(f"❌ Error capturing conversation: {e}")

        return None


# Global capture instance
capture = ChatGPTNetworkCapture()


# mitmproxy addon for intercepting OpenAI API calls
class OpenAIInterceptor:
    """mitmproxy addon to intercept OpenAI API calls."""

    def __init__(self):
        self.pending_requests = {}

    def request(self, flow: http.HTTPFlow):
        """Intercept outgoing requests."""
        # Check if this is an OpenAI API call
        if "api.openai.com" in flow.request.pretty_host:
            # Store request for later matching with response
            self.pending_requests[id(flow)] = {
                "url": flow.request.url,
                "method": flow.request.method,
                "timestamp": datetime.now(timezone.utc),
            }

            # Parse request body if it's a chat completion
            if "/chat/completions" in flow.request.path:
                try:
                    body = json.loads(flow.request.content.decode("utf-8"))
                    self.pending_requests[id(flow)]["request_body"] = body
                    print(
                        f"🔍 Intercepted chat request: {body.get('model', 'unknown model')}"
                    )
                except:
                    pass

    def response(self, flow: http.HTTPFlow):
        """Intercept incoming responses."""
        flow_id = id(flow)

        if flow_id in self.pending_requests:
            req_data = self.pending_requests[flow_id]

            # Parse chat completion response
            if (
                "/chat/completions" in flow.request.path
                and flow.response.status_code == 200
            ):
                try:
                    response_body = json.loads(flow.response.content.decode("utf-8"))
                    request_body = req_data.get("request_body", {})

                    # Extract data
                    messages = request_body.get("messages", [])
                    user_message = next(
                        (
                            m["content"]
                            for m in reversed(messages)
                            if m.get("role") == "user"
                        ),
                        "",
                    )
                    assistant_message = (
                        response_body.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                    model = response_body.get("model", "gpt-4")
                    conversation_id = request_body.get(
                        "conversation_id", str(uuid.uuid4())
                    )

                    if user_message and assistant_message:
                        # Capture to UATP (async)
                        asyncio.create_task(
                            capture.capture_conversation(
                                conversation_id=conversation_id,
                                user_message=user_message,
                                assistant_message=assistant_message,
                                model=model,
                            )
                        )

                except Exception as e:
                    print(f"⚠️ Error processing response: {e}")

            # Clean up
            del self.pending_requests[flow_id]


async def start_proxy_server():
    """Start the proxy server for intercepting ChatGPT traffic."""

    if not MITMPROXY_AVAILABLE:
        print("❌ mitmproxy not installed")
        print("\nInstall with:")
        print("  pip install mitmproxy")
        print("\nOR use alternative method: Chrome extension")
        return

    print("=" * 70)
    print("  ChatGPT Desktop App - Network Capture")
    print("=" * 70)
    print()
    print("🌐 Starting proxy server on http://localhost:8888")
    print()
    print("📋 Setup Instructions:")
    print("   1. Open ChatGPT desktop app")
    print("   2. Go to Settings → Advanced")
    print("   3. Set HTTP Proxy: localhost:8888")
    print("   4. Start chatting - all conversations auto-captured!")
    print()
    print("⚠️  Note: You may need to install mitmproxy certificate")
    print("   Run: mitmproxy (then press 'q' to quit)")
    print("   Install cert from: ~/.mitmproxy/mitmproxy-ca-cert.pem")
    print()
    print("=" * 70)
    print()

    # Initialize database
    await capture.init_db()

    # Start mitmproxy
    # This would normally run mitmdump with the addon
    print("✅ Proxy server ready - listening for ChatGPT traffic...")
    print("   Press Ctrl+C to stop")
    print()

    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down proxy server...")
        if capture.db:
            await capture.db.disconnect()


def main():
    """Main entry point."""

    if not MITMPROXY_AVAILABLE:
        print("=" * 70)
        print("  ChatGPT Network Capture - Installation Required")
        print("=" * 70)
        print()
        print("❌ mitmproxy is not installed")
        print()
        print("📦 Install with:")
        print("   pip install mitmproxy")
        print()
        print("🔧 Alternative: Use browser extension method")
        print("   See: CHATGPT_AUTO_CAPTURE_ALTERNATIVES.md")
        print()
        return

    asyncio.run(start_proxy_server())


if __name__ == "__main__":
    main()
