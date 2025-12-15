#!/usr/bin/env python3
"""
Import existing capsules from capsule_chain.jsonl into PostgreSQL database
"""

import asyncio
import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.models.capsule import CapsuleModel


async def import_capsules():
    """Import all capsules from JSONL file to database"""

    # Create async engine
    engine = create_async_engine(
        "postgresql+asyncpg://uatp_user@localhost:5432/uatp_capsule_engine", echo=False
    )
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    imported = 0
    skipped = 0
    errors = []

    print("🔄 Starting capsule import from capsule_chain.jsonl...")

    async with AsyncSessionLocal() as session:
        with open("capsule_chain.jsonl") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    capsule_data = json.loads(line.strip())

                    # Check if capsule already exists
                    existing = await session.execute(
                        select(CapsuleModel).where(
                            CapsuleModel.capsule_id == capsule_data.get("capsule_id")
                        )
                    )
                    if existing.scalar_one_or_none():
                        skipped += 1
                        continue

                    # Parse timestamp
                    timestamp_str = capsule_data.get("timestamp", "")
                    try:
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                    except:
                        timestamp = datetime.utcnow()

                    # Create capsule model
                    capsule = CapsuleModel(
                        capsule_id=capsule_data.get("capsule_id"),
                        capsule_type=capsule_data.get("type", "chat"),
                        version=capsule_data.get("version", "1.0"),
                        timestamp=timestamp,
                        status=capsule_data.get("status", "SEALED"),
                        verification=capsule_data.get("verification", {}),
                        payload=capsule_data.get("payload", capsule_data),
                    )

                    session.add(capsule)
                    imported += 1

                    if imported % 10 == 0:
                        print(f"  ✓ Imported {imported} capsules...")
                        await session.commit()

                except Exception as e:
                    errors.append(f"Line {line_num}: {str(e)}")
                    continue

        # Final commit
        await session.commit()

    print("\n✅ Import complete!")
    print(f"   Imported: {imported} capsules")
    print(f"   Skipped: {skipped} (already exist)")
    if errors:
        print(f"   Errors: {len(errors)}")
        for error in errors[:5]:
            print(f"     - {error}")


if __name__ == "__main__":
    asyncio.run(import_capsules())
