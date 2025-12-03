#!/usr/bin/env python3
"""
Create a test capsule in the correct 7.0 format to verify frontend display.
"""

import asyncio
from datetime import datetime, timezone
import uuid
import json

from src.database.connection import DatabaseManager


async def create_test_capsule():
    """Create a simple test capsule directly in the database."""

    db = DatabaseManager()
    await db.connect()

    # Generate capsule ID in correct format: caps_YYYY_MM_DD_hexstring
    now = datetime.now(timezone.utc)
    capsule_id = f"caps_{now.strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

    # Create capsule data
    capsule_data = {
        "capsule_id": capsule_id,
        "version": "7.0",
        "timestamp": now.isoformat(),
        "status": "sealed",
        "capsule_type": "reasoning_trace",
        "verification": {
            "verified": True,
            "hash": "test123abc",
            "signature": "sig123",
            "method": "ed25519",
        },
        "payload": {
            "content": "Test capsule - verifying frontend display",
            "reasoning_steps": ["Step 1: Test creation", "Step 2: Verify display"],
            "confidence": 0.9,
            "metadata": {"test": True, "created_by": "create_test_capsule.py"},
        },
    }

    # Insert into database
    query = """
        INSERT INTO capsules (capsule_id, version, timestamp, status, capsule_type, verification, payload)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """

    await db.execute(
        query,
        capsule_data["capsule_id"],
        capsule_data["version"],
        now,
        capsule_data["status"],
        capsule_data["capsule_type"],
        json.dumps(capsule_data["verification"]),
        json.dumps(capsule_data["payload"]),
    )

    print("✅ Test capsule created successfully!")
    print(f"   Capsule ID: {capsule_id}")
    print(f"   Type: reasoning_trace")
    print(f"   Timestamp: {now}")
    print("\n📝 You should now see this capsule in the frontend Capsules tab")

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(create_test_capsule())
