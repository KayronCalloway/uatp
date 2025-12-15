#!/usr/bin/env python3
"""Test demo mode filtering directly at the engine level"""

import asyncio

from src.core.database import db
from src.engine.capsule_engine import CapsuleEngine


async def test_filtering():
    """Test the filtering logic directly"""

    # Initialize database
    await db.connect()

    # Create engine
    engine = CapsuleEngine(db_manager=db)

    print("Testing demo mode filtering...")
    print("=" * 60)

    # Test 1: Load with exclude_demo=True (live mode)
    print("\n1. Loading capsules with exclude_demo=True (LIVE MODE):")
    live_capsules = await engine.load_chain_async(skip=0, limit=100, exclude_demo=True)
    demo_count = sum(1 for c in live_capsules if c.capsule_id.startswith("demo-"))
    real_count = len(live_capsules) - demo_count
    print(f"   Total: {len(live_capsules)}")
    print(f"   Demo: {demo_count}")
    print(f"   Real: {real_count}")
    print("   Expected: 0 demo, ~83 real")
    print(
        f"   Result: {'✅ PASS' if demo_count == 0 else '❌ FAIL (contains demo capsules!)'}"
    )

    if demo_count > 0:
        print("\n   Demo capsules found:")
        for c in live_capsules:
            if c.capsule_id.startswith("demo-"):
                print(f"     - {c.capsule_id}")

    # Test 2: Load with exclude_demo=False (demo mode)
    print("\n2. Loading capsules with exclude_demo=False (DEMO MODE):")
    all_capsules = await engine.load_chain_async(skip=0, limit=100, exclude_demo=False)
    demo_count_all = sum(1 for c in all_capsules if c.capsule_id.startswith("demo-"))
    real_count_all = len(all_capsules) - demo_count_all
    print(f"   Total: {len(all_capsules)}")
    print(f"   Demo: {demo_count_all}")
    print(f"   Real: {real_count_all}")
    print("   Expected: 5 demo, ~83 real (88 total)")
    print(
        f"   Result: {'✅ PASS' if demo_count_all == 5 else '⚠️  PARTIAL (expected 5 demo)'}"
    )

    # Cleanup
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_filtering())
