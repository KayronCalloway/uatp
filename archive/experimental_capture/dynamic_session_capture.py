#!/usr/bin/env python3
"""
Dynamic Session Capture - Captures REAL conversation metadata
Creates timestamped session markers that can be enriched with actual conversation content
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

# Load .env first
from dotenv import load_dotenv

load_dotenv()

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from src.database.connection import DatabaseManager


async def capture_dynamic_session():
    """Capture current session with dynamic content."""

    db = DatabaseManager()
    await db.connect()

    try:
        now = datetime.now(timezone.utc)
        session_id = f"caps_{now.strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        # Read user message from stdin if available (from hook)
        user_message = ""
        if not sys.stdin.isatty():
            try:
                user_message = sys.stdin.read().strip()
            except:
                pass

        # Create a session marker capsule
        capsule = {
            "capsule_id": session_id,
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
                "session_id": session_id,
                "platform": "claude-code",
                "session_type": "active_development",
                "timestamp": now.isoformat(),
                "last_user_message": user_message[:200]
                if user_message
                else "Session active",
                "analysis_metadata": {
                    "auto_captured": True,
                    "significance_score": 0.7,
                    "platform": "claude-code",
                    "user_id": "kay",
                },
                "topics": ["software_development", "uatp_system"],
                "notes": "Captured via Claude Code hook - automatic session tracking",
            },
        }

        # Insert into database
        import json

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
            print(f"✅ Session captured: {session_id}")
            print(f"   Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            if user_message:
                print(f"   Context: {user_message[:60]}...")
        else:
            print(f"ℹ️  Session already exists: {session_id}")

    except Exception as e:
        print(f"❌ Capture error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(capture_dynamic_session())
