#!/usr/bin/env python3
"""
Test end-to-end capsule creation and verification.
Create a new capsule and verify it shows up in both database and API.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import DatabaseManager
from src.engine.capsule_engine import CapsuleEngine


async def test_capsule_loading():
    """Test whether existing capsules can be loaded from the database."""

    print("=" * 80)
    print("CAPSULE LOADING DIAGNOSIS")
    print("=" * 80)

    # Initialize database
    print("\n1️⃣  Initializing database connection...")
    db = DatabaseManager()
    await db.connect()

    # Check current capsule count via direct SQL
    print("\n2️⃣  Checking capsule count via direct SQL...")
    count = await db.fetchval("SELECT COUNT(*) FROM capsules")
    print(f"   📊 Total capsules in database: {count}")

    # Sample the database directly
    print("\n3️⃣  Sampling database directly (raw SQL)...")
    try:
        rows = await db.fetch(
            """
            SELECT capsule_id, capsule_type, timestamp, created_at
            FROM capsules
            ORDER BY created_at DESC
            LIMIT 5
        """
        )
        if rows:
            print(f"   ✅ Found {len(rows)} capsules via direct SQL:")
            for row in rows:
                cap_id = (
                    row["capsule_id"][:40]
                    if len(row["capsule_id"]) > 40
                    else row["capsule_id"]
                )
                print(
                    f"      • {cap_id}... | {row['capsule_type']} | {row['timestamp']}"
                )
        else:
            print(f"   ❌ No capsules found via direct SQL!")
    except Exception as e:
        print(f"   ❌ Error querying database: {e}")
        import traceback

        traceback.print_exc()

    # Initialize engine and try to load capsules
    print("\n4️⃣  Initializing capsule engine...")
    engine = CapsuleEngine(db_manager=db, agent_id="test-load-diagnosis")

    # Try to load capsules using engine
    print("\n5️⃣  Loading capsules via engine.load_chain_async()...")
    try:
        chain = await engine.load_chain_async(skip=0, limit=5)
        print(f"   📊 Capsules returned by load_chain_async(): {len(chain)}")

        if chain:
            print(f"   ✅ Engine can load capsules!")
            print(f"\n   Recent capsules from engine:")
            for i, c in enumerate(chain[:3], 1):
                cap_id = c.capsule_id[:40] if len(c.capsule_id) > 40 else c.capsule_id
                print(f"      {i}. {cap_id}... | {c.capsule_type} | {c.timestamp}")
        else:
            print(f"   ❌ Engine returns empty chain despite {count} capsules in DB!")
            print(f"   🔍 THIS IS THE ROOT CAUSE!")
    except Exception as e:
        print(f"   ❌ Error loading chain: {e}")
        import traceback

        traceback.print_exc()

    await db.disconnect()

    print("\n" + "=" * 80)
    print("DIAGNOSIS COMPLETE")
    print("=" * 80)
    print("\n📋 Summary:")
    print(f"   • Capsules in database (via SQL): {count}")
    print(
        f"   • Capsules from engine: {len(chain) if 'chain' in locals() else 'ERROR'}"
    )
    if "chain" in locals() and len(chain) == 0 and count > 0:
        print(f"\n⚠️  ROOT CAUSE IDENTIFIED:")
        print(
            f"   Database has {count} capsules but engine.load_chain_async() returns 0"
        )
        print(f"   This explains why:")
        print(f"   - /capsules API endpoint returns empty array")
        print(f"   - Frontend Capsules tab shows 'No capsules available'")
        print(
            f"\n🔍 Next step: Investigate why load_chain_async() can't read from capsules table"
        )
    print()


if __name__ == "__main__":
    asyncio.run(test_capsule_loading())
