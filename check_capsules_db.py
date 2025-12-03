#!/usr/bin/env python3
"""Quick script to check what's in the capsules table."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import DatabaseManager
from sqlalchemy import text


async def check_capsules():
    db = DatabaseManager()
    await db.connect()

    print("=" * 80)
    print("CAPSULES DATABASE CHECK")
    print("=" * 80)

    async with db.get_session() as session:
        # Count total capsules
        result = await session.execute(text("SELECT COUNT(*) FROM capsules"))
        count = result.scalar()
        print(f"\n📊 Total capsules in database: {count}")

        # Get sample
        result = await session.execute(
            text(
                """
            SELECT capsule_id, capsule_type, timestamp
            FROM capsules
            ORDER BY timestamp DESC
            LIMIT 5
        """
            )
        )
        rows = result.fetchall()

        if rows:
            print(f"\n📝 Sample capsules (newest 5):")
            for row in rows:
                print(f"   • {row[0][:20]}... | {row[1]} | {row[2]}")
        else:
            print("\n❌ No capsules found!")

    await db.close()
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(check_capsules())
