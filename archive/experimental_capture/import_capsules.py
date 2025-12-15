#!/usr/bin/env python3
"""
Import capsules from capsule_chain.jsonl into the SQLite database.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

from src.core.database import db


async def import_capsules():
    """Import capsules from JSONL file into database."""

    # Initialize database connection
    class MockApp:
        pass

    app = MockApp()
    db.init_app(app)

    # Create tables if they don't exist
    await db.create_all()

    # Read capsules from JSONL file
    jsonl_path = Path("capsule_chain.jsonl")
    if not jsonl_path.exists():
        print(f"❌ File not found: {jsonl_path}")
        return

    capsules_data = []
    with open(jsonl_path) as f:
        for line in f:
            if line.strip():
                capsules_data.append(json.loads(line))

    print(f"📖 Found {len(capsules_data)} capsules in {jsonl_path}")

    # Import each capsule
    imported = 0
    skipped = 0

    async with db.engine.begin() as conn:
        for capsule_data in capsules_data:
            capsule_id = capsule_data.get("capsule_id")

            # Check if capsule already exists
            result = await conn.execute(
                text(
                    "SELECT COUNT(*) as count FROM capsules WHERE capsule_id = :capsule_id"
                ),
                {"capsule_id": capsule_id},
            )
            count = result.scalar()

            if count > 0:
                print(f"⏭️  Skipping {capsule_id} (already exists)")
                skipped += 1
                continue

            # Convert simplified format to full schema
            capsule_type = capsule_data.get("type", "reasoning_trace")
            timestamp_str = capsule_data.get("timestamp")

            # Parse timestamp
            if timestamp_str:
                if isinstance(timestamp_str, str):
                    # Try parsing different formats
                    try:
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                    except ValueError:
                        timestamp = datetime.now()
                else:
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()

            # Create verification object
            verification = {
                "verified": True,
                "signer": capsule_data.get("agent_id", "demo-agent"),
                "signature": f"mock-signature-{capsule_id}",
                "timestamp": timestamp.isoformat(),
            }

            # Create payload - contains the capsule-specific data
            payload = {
                "capsule_id": capsule_id,
                "capsule_type": capsule_type,
                "version": "7.0",
                "timestamp": timestamp.isoformat(),
                "status": capsule_data.get("status", "SEALED"),
                "verification": verification,
                capsule_type: {
                    "content": capsule_data.get("content", ""),
                    "agent_id": capsule_data.get("agent_id", "demo-agent"),
                },
            }

            # Insert into database
            await conn.execute(
                text(
                    """
                    INSERT INTO capsules (
                        capsule_id, capsule_type, version, timestamp,
                        status, verification, payload
                    ) VALUES (
                        :capsule_id, :capsule_type, :version, :timestamp,
                        :status, :verification, :payload
                    )
                """
                ),
                {
                    "capsule_id": capsule_id,
                    "capsule_type": capsule_type,
                    "version": "7.0",
                    "timestamp": timestamp,
                    "status": capsule_data.get("status", "SEALED"),
                    "verification": json.dumps(verification),
                    "payload": json.dumps(payload),
                },
            )

            print(f"✅ Imported {capsule_id}")
            imported += 1

    print("\n📊 Import Summary:")
    print(f"   Imported: {imported}")
    print(f"   Skipped:  {skipped}")
    print(f"   Total:    {len(capsules_data)}")

    # Verify import
    async with db.engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) as count FROM capsules"))
        total_count = result.scalar()
        print(f"\n✅ Database now contains {total_count} capsules")


if __name__ == "__main__":
    asyncio.run(import_capsules())
