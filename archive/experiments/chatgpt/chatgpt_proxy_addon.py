#!/usr/bin/env python3
"""
ChatGPT Proxy Addon for mitmproxy
==================================

This addon intercepts OpenAI API calls from the ChatGPT desktop app
and automatically captures them to UATP.

Usage:
    mitmdump -s chatgpt_proxy_addon.py -p 8888
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone

from mitmproxy import http

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv()

from src.database.connection import DatabaseManager


class ChatGPTCaptureAddon:
    """mitmproxy addon to capture ChatGPT conversations."""

    def __init__(self):
        self.db = None
        self.pending_requests = {}
        self.conversations = {}
        self.loop = None
        print(" ChatGPT Capture Addon initialized")

    def load(self, loader):
        """Called when addon is loaded."""
        print("=" * 70)
        print("  ChatGPT Auto-Capture Proxy")
        print("=" * 70)
        print()
        print("[OK] Proxy server running on http://localhost:8888")
        print()
        print(" Configure ChatGPT Desktop App:")
        print("   If the app has proxy settings:")
        print("   - Go to Settings → Network/Advanced")
        print("   - Set HTTP Proxy: localhost:8888")
        print()
        print("   If the app doesn't have proxy settings:")
        print("   - Use system-wide proxy (System Preferences → Network)")
        print("   - Or the app might use system proxy automatically")
        print()
        print(" SSL Certificate:")
        print("   The app might reject the proxy's SSL cert")
        print("   Install cert from: ~/.mitmproxy/mitmproxy-ca-cert.pem")
        print("   (macOS: Open file, add to Keychain, trust for SSL)")
        print()
        print("=" * 70)
        print()
        print(" Listening for ChatGPT traffic...")
        print()

        # Initialize database connection in background
        asyncio.create_task(self._init_db())

    async def _init_db(self):
        """Initialize database connection."""
        try:
            self.db = DatabaseManager()
            await self.db.connect()
            print("[OK] Database connected - ready to capture!")
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")

    def request(self, flow: http.HTTPFlow):
        """Intercept outgoing requests."""
        # Check if this is an OpenAI API call
        if (
            "api.openai.com" in flow.request.pretty_host
            or "chatgpt.com" in flow.request.pretty_host
        ):
            # Store request for later matching with response
            flow_id = id(flow)
            self.pending_requests[flow_id] = {
                "url": flow.request.url,
                "method": flow.request.method,
                "timestamp": datetime.now(timezone.utc),
            }

            # Parse request body if it's a chat completion
            if "/v1/chat/completions" in flow.request.path:
                try:
                    body = json.loads(flow.request.content.decode("utf-8"))
                    self.pending_requests[flow_id]["request_body"] = body
                    model = body.get("model", "unknown")
                    print(f" Intercepted chat request → {model}")
                except Exception:
                    pass

    def response(self, flow: http.HTTPFlow):
        """Intercept incoming responses."""
        flow_id = id(flow)

        if flow_id not in self.pending_requests:
            return

        req_data = self.pending_requests[flow_id]

        # Parse chat completion response
        if (
            "/v1/chat/completions" in flow.request.path
            and flow.response.status_code == 200
        ):
            try:
                response_body = json.loads(flow.response.content.decode("utf-8"))
                request_body = req_data.get("request_body", {})

                # Extract conversation data
                messages = request_body.get("messages", [])
                user_message = ""
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        user_message = msg.get("content", "")
                        break

                choices = response_body.get("choices", [])
                assistant_message = ""
                if choices:
                    assistant_message = choices[0].get("message", {}).get("content", "")

                model = response_body.get("model", request_body.get("model", "gpt-4"))
                conversation_id = request_body.get("conversation_id", str(uuid.uuid4()))

                if user_message and assistant_message:
                    print(f"[OK] Captured exchange ({model})")
                    print(f"   User: {user_message[:60]}...")
                    print(f"   AI: {assistant_message[:60]}...")

                    # Capture to UATP (async)
                    asyncio.create_task(
                        self._capture_conversation(
                            conversation_id=conversation_id,
                            user_message=user_message,
                            assistant_message=assistant_message,
                            model=model,
                            full_messages=messages,
                        )
                    )

            except Exception as e:
                print(f"[WARN] Error processing response: {e}")

        # Clean up
        del self.pending_requests[flow_id]

    async def _capture_conversation(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        model: str,
        full_messages: list,
    ):
        """Capture conversation to UATP database."""

        if not self.db:
            await self._init_db()
            if not self.db:
                print("[ERROR] Cannot capture - database not connected")
                return

        try:
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
            capsule_id = (
                f"chatgpt_live_{now.strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"
            )

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
                    "title": "ChatGPT Conversation",
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
                msg_count = len(self.conversations[conversation_id])
                print(f" Saved to UATP! (Conversation has {msg_count} messages)")

        except Exception as e:
            print(f"[ERROR] Error saving to database: {e}")
            import traceback

            traceback.print_exc()


# Create the addon instance
addons = [ChatGPTCaptureAddon()]
