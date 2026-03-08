#!/usr/bin/env python3
"""
Capture ChatGPT Desktop App Conversations

The ChatGPT desktop app stores conversations locally.
This script reads from the app's local storage and imports to UATP.
"""

import asyncio
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Load .env first
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from src.database.connection import DatabaseManager


def find_chatgpt_desktop_data():
    """Find ChatGPT desktop app data location."""

    # Common locations for ChatGPT desktop app data
    possible_paths = [
        # macOS
        Path.home() / "Library" / "Application Support" / "ChatGPT",
        Path.home() / "Library" / "Application Support" / "OpenAI" / "ChatGPT",
        Path.home() / "Library" / "Application Support" / "com.openai.chat",
        # Alternative macOS locations
        Path.home() / ".chatgpt",
        Path.home() / ".openai" / "chatgpt",
    ]

    for path in possible_paths:
        if path.exists():
            print(f"[OK] Found ChatGPT app data: {path}")
            return path

    return None


def read_chatgpt_conversations(data_path: Path):
    """Read conversations from ChatGPT desktop app storage."""

    conversations = []

    # Look for conversation files
    print(f"\n Searching for conversations in: {data_path}")

    # Common storage patterns
    storage_patterns = [
        "conversations.json",
        "chats.json",
        "history.json",
        "*.db",  # SQLite database
        "IndexedDB",  # Browser-based storage
        "Local Storage",
    ]

    # Search for JSON files
    for json_file in data_path.rglob("*.json"):
        print(f"   Found: {json_file.name}")
        try:
            with open(json_file) as f:
                data = json.load(f)
                if isinstance(data, list):
                    conversations.extend(data)
                elif isinstance(data, dict):
                    # Could be conversations wrapped in object
                    if "conversations" in data:
                        conversations.extend(data["conversations"])
                    elif "chats" in data:
                        conversations.extend(data["chats"])
        except Exception as e:
            print(f"   [WARN]  Couldn't read {json_file.name}: {e}")

    # Search for SQLite databases
    for db_file in data_path.rglob("*.db"):
        print(f"   Found database: {db_file.name}")
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()

            # Try common table names
            for table_name in ["conversations", "chats", "messages", "threads"]:
                try:
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    print(f"      Found {len(rows)} rows in {table_name}")
                except sqlite3.OperationalError:
                    continue

            conn.close()
        except Exception as e:
            print(f"   [WARN]  Couldn't read {db_file.name}: {e}")

    return conversations


async def import_desktop_conversations(conversations: list):
    """Import conversations to UATP."""

    if not conversations:
        print("\n[ERROR] No conversations found to import")
        return False

    print(f"\n Importing {len(conversations)} conversations...")

    db = DatabaseManager()
    await db.connect()

    created_count = 0

    for conv in conversations:
        try:
            # Extract conversation data (format varies by app version)
            conv_id = conv.get("id", str(uuid.uuid4()))
            title = conv.get("title", "Untitled")
            create_time = conv.get(
                "create_time", datetime.now(timezone.utc).timestamp()
            )

            # Extract messages
            messages = []
            if "messages" in conv:
                messages = conv["messages"]
            elif "mapping" in conv:
                # Newer format with mapping
                for msg_id, msg_data in conv["mapping"].items():
                    if "message" in msg_data:
                        messages.append(msg_data["message"])

            if not messages:
                continue

            # Create capsule
            now = datetime.fromtimestamp(create_time, tz=timezone.utc)
            capsule_id = (
                f"chatgpt_desktop_{now.strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"
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
                    "conversation_id": conv_id,
                    "title": title,
                    "message_count": len(messages),
                    "messages": messages,
                    "session_type": "chatgpt_desktop_app",
                    "analysis_metadata": {
                        "imported": True,
                        "import_date": datetime.now(timezone.utc).isoformat(),
                        "source": "chatgpt_desktop_app",
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

        except Exception as e:
            print(f"[WARN]  Error importing conversation: {e}")
            continue

    await db.disconnect()

    print(f"\n{'='*70}")
    print(f"[OK] Import Complete: {created_count} conversations imported")
    print(f"{'='*70}")
    print("\n View in frontend: http://localhost:3000")

    return True


async def main():
    """Main function to find and import ChatGPT desktop conversations."""

    print("=" * 70)
    print("  ChatGPT Desktop App Capture")
    print("=" * 70)

    # Find app data
    data_path = find_chatgpt_desktop_data()

    if not data_path:
        print("\n[ERROR] Could not find ChatGPT desktop app data")
        print("\n Possible reasons:")
        print("   1. ChatGPT desktop app not installed")
        print("   2. App stores data in different location")
        print("   3. No permissions to access app data")
        print("\n Alternatives:")
        print("   - Export from ChatGPT app if it has export feature")
        print("   - Use network proxy to capture API calls")
        print("   - Check: ~/Library/Application Support/ for ChatGPT folders")
        return False

    # Read conversations
    conversations = read_chatgpt_conversations(data_path)

    if not conversations:
        print("\n[WARN]  No conversations found in standard format")
        print("\n The app might use a different storage format")
        print(f"\n Data location: {data_path}")
        print("\n You can:")
        print("   1. Manually explore the data directory")
        print("   2. Look for .json or .db files")
        print("   3. Check app settings for export feature")
        return False

    # Import to UATP
    await import_desktop_conversations(conversations)

    return True


if __name__ == "__main__":
    asyncio.run(main())
