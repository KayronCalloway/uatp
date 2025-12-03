#!/usr/bin/env python3
"""
Tag existing capsules as test data by adding environment metadata.
This preserves the data but marks it for filtering.
"""
import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to path
sys.path.insert(0, "/Users/kay/uatp-capsule-engine")

# Force use of PostgreSQL production database
os.environ[
    "DATABASE_URL"
] = "postgresql+asyncpg://uatp_user:uatp_password@localhost:5432/uatp_capsule_engine"

from src.core.database import db
from src.models.capsule import CapsuleModel


async def tag_capsules_as_test():
    """Tag all existing capsules with environment='test' metadata"""

    # Initialize database
    db.init_app(None)

    try:
        async with db.get_session() as session:
            # Get all capsules
            query = select(CapsuleModel)
            result = await session.execute(query)
            all_capsules = result.scalars().all()

            print("=" * 80)
            print("Tagging Capsules as Test Data")
            print("=" * 80)
            print(f"\nTotal capsules to tag: {len(all_capsules)}")

            tagged_count = 0
            already_tagged = 0

            for capsule in all_capsules:
                # Initialize payload if None
                if capsule.payload is None:
                    capsule.payload = {}

                # Initialize analysis_metadata if not present
                if "analysis_metadata" not in capsule.payload:
                    capsule.payload["analysis_metadata"] = {}

                # Check if already tagged
                if capsule.payload["analysis_metadata"].get("environment") == "test":
                    already_tagged += 1
                    continue

                # Tag as test
                capsule.payload["analysis_metadata"]["environment"] = "test"
                capsule.payload["analysis_metadata"][
                    "tagged_at"
                ] = datetime.utcnow().isoformat()
                capsule.payload["analysis_metadata"][
                    "tagged_reason"
                ] = "Bulk test data classification"

                # Mark as modified
                session.add(capsule)
                tagged_count += 1

            # Commit changes
            await session.commit()

            print(f"\n✅ Successfully tagged {tagged_count} capsules as test data")
            if already_tagged > 0:
                print(f"ℹ️  {already_tagged} capsules were already tagged")

            print("\n" + "=" * 80)
            print("Data Access:")
            print("  Default queries: Test data hidden")
            print("  With ?include_test=true: Test data visible")
            print("  With ?environment=test: Only test data shown")
            print("=" * 80)

    finally:
        if db.engine:
            await db.engine.dispose()


if __name__ == "__main__":
    asyncio.run(tag_capsules_as_test())
