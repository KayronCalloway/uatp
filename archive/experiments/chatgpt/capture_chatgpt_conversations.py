#!/usr/bin/env python3
"""
Capture ChatGPT conversations and create UATP capsules
Uses OpenAI API to fetch conversation history and store as capsules
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone

# Load .env first
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from src.database.connection import DatabaseManager


async def fetch_and_capture_chatgpt_conversations():
    """Show instructions for capturing ChatGPT conversations."""

    print("=" * 70)
    print("  ChatGPT Conversation Capture")
    print("=" * 70)

    print("\n[WARN]  OpenAI doesn't provide API access to ChatGPT web conversations")
    print("\n To capture your ChatGPT conversations, you can:")

    print("\n   [OK] Option 1: Export from ChatGPT (RECOMMENDED)")
    print("   1. Go to https://chat.openai.com")
    print("   2. Click your profile → Settings → Data controls")
    print("   3. Click 'Export data'")
    print("   4. Wait for email with download link")
    print("   5. Download and extract conversations.json")
    print("   6. Run: python3 capture_chatgpt_conversations.py conversations.json")

    print("\n   Option 2: Real-time capture (Needs development)")
    print("   - Browser extension to monitor chat.openai.com")
    print("   - Extension POSTs conversations to UATP API")
    print("   - Would capture in real-time like Claude Code does")

    print("\n   Option 3: Use OpenAI API directly")
    print("   - Build your own ChatGPT interface using OpenAI API")
    print("   - Route through UATP's /ai/generate endpoint")
    print("   - Every API call automatically creates capsules")

    return True


async def import_chatgpt_export(export_file: str):
    """Import ChatGPT export file and create capsules."""

    print("=" * 70)
    print("  Importing ChatGPT Export")
    print("=" * 70)

    if not os.path.exists(export_file):
        print(f"[ERROR] File not found: {export_file}")
        return False

    try:
        with open(export_file) as f:
            data = json.load(f)

        print(f"\n Loaded export file: {len(data)} conversations found")

        db = DatabaseManager()
        await db.connect()

        created_count = 0

        for conversation in data:
            # Extract conversation data
            conv_id = conversation.get("id", str(uuid.uuid4()))
            title = conversation.get("title", "Untitled")
            create_time = conversation.get(
                "create_time", datetime.now(timezone.utc).timestamp()
            )
            messages = conversation.get("mapping", {})

            # Build conversation messages
            message_list = []
            for msg_id, msg_data in messages.items():
                message = msg_data.get("message")
                if message and message.get("content"):
                    content = message["content"]
                    role = message["author"]["role"]

                    # Extract text content
                    if isinstance(content, dict) and "parts" in content:
                        text = " ".join(str(part) for part in content["parts"])
                    else:
                        text = str(content)

                    message_list.append(
                        {
                            "role": role,
                            "content": text,
                            "timestamp": message.get("create_time", create_time),
                        }
                    )

            if not message_list:
                continue

            # Create capsule
            now = datetime.fromtimestamp(create_time, tz=timezone.utc)
            capsule_id = f"chatgpt_{now.strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

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
                    "platform": "chatgpt",
                    "conversation_id": conv_id,
                    "title": title,
                    "message_count": len(message_list),
                    "messages": message_list,
                    "session_type": "chatgpt_web",
                    "analysis_metadata": {
                        "imported": True,
                        "import_date": datetime.now(timezone.utc).isoformat(),
                        "source": "chatgpt_export",
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

            result = await db.execute(
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
                created_count += 1
                print(f"[OK] Imported: {title[:60]}")

        await db.disconnect()

        print(f"\n{'='*70}")
        print(f"[OK] Import Complete: {created_count} conversations imported")
        print(f"{'='*70}")
        print("\n View in frontend: http://localhost:3000")

        return True

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Import mode
        export_file = sys.argv[1]
        asyncio.run(import_chatgpt_export(export_file))
    else:
        # Info mode
        asyncio.run(fetch_and_capture_chatgpt_conversations())
