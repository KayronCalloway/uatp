#!/usr/bin/env python3
"""
Import properly formatted UATP 7.0 capsules into the SQLite database.
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import text

from src.core.database import db


async def import_uatp7_capsules():
    """Import UATP 7.0 capsules from JSONL file into database."""

    # Initialize database connection
    class MockApp:
        pass

    app = MockApp()
    db.init_app(app)

    # Create tables if they don't exist
    await db.create_all()

    # Read capsules from UATP 7.0 test data
    jsonl_path = Path("visualizer/test_data/uatp7_test_chain.jsonl")
    if not jsonl_path.exists():
        print(f"❌ File not found: {jsonl_path}")
        return

    capsules_data = []
    with open(jsonl_path) as f:
        for line in f:
            if line.strip():
                capsules_data.append(json.loads(line))

    print(f"📖 Found {len(capsules_data)} UATP 7.0 capsules in {jsonl_path}")

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

            # These capsules are already in UATP 7.0 format
            # Insert directly into database
            from datetime import datetime

            # Parse timestamp
            timestamp_str = capsule_data.get("timestamp")
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                timestamp = datetime.now()

            # Create verification object from signature data
            verification = {
                "verified": True,
                "signer": capsule_data.get("agent_id", "uatp7-test-agent"),
                "signature": capsule_data.get("signature", ""),
                "timestamp": timestamp.isoformat(),
            }

            # The capsule_data itself is the payload in UATP 7.0 format
            capsule_type = capsule_data.get("capsule_type", "Base")

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
                    "version": capsule_data.get("schema_version", "7.0"),
                    "timestamp": timestamp,
                    "status": "SEALED",
                    "verification": json.dumps(verification),
                    "payload": json.dumps(capsule_data),
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
    asyncio.run(import_uatp7_capsules())
