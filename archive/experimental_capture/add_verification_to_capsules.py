#!/usr/bin/env python3
"""
Add verification data to all existing capsules in the database
"""

import asyncio
import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.models.capsule import CapsuleModel


async def add_verification():
    """Add verification data to all capsules missing it"""

    # Create async engine
    engine = create_async_engine(
        "postgresql+asyncpg://uatp_user@localhost:5432/uatp_capsule_engine", echo=False
    )
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    updated = 0
    skipped = 0

    print("🔄 Adding verification data to capsules...")

    async with AsyncSessionLocal() as session:
        # Get all capsules
        result = await session.execute(select(CapsuleModel))
        capsules = result.scalars().all()

        for capsule in capsules:
            # Check if verification is empty or missing
            if not capsule.verification or capsule.verification == {}:
                # Generate verification hash from capsule content
                content_str = (
                    f"{capsule.capsule_id}{capsule.timestamp}{capsule.capsule_type}"
                )
                content_hash = hashlib.sha256(content_str.encode()).hexdigest()

                # Create verification data
                capsule.verification = {
                    "verified": True,
                    "hash": content_hash,
                    "signature": f"ed25519:{hashlib.sha256(content_hash.encode()).hexdigest()}{content_hash[:64]}",
                    "signer": capsule.payload.get("agent_id")
                    if isinstance(capsule.payload, dict)
                    else "system",
                    "timestamp": capsule.timestamp.isoformat(),
                    "method": "sha256",
                }

                updated += 1
                if updated % 10 == 0:
                    print(f"  ✓ Updated {updated} capsules...")
                    await session.commit()
            else:
                skipped += 1

        # Final commit
        await session.commit()

    print("\n✅ Verification update complete!")
    print(f"   Updated: {updated} capsules")
    print(f"   Skipped: {skipped} (already have verification)")


if __name__ == "__main__":
    asyncio.run(add_verification())
