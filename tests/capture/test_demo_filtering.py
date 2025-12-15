#!/usr/bin/env python3
"""
Direct test of demo mode filtering logic
"""

import asyncio

from src.core.database import db
from src.engine.capsule_engine import CapsuleEngine


async def test_filtering():
    """Test the demo mode filtering"""
    # Initialize database
    from src.core.config import DATABASE_URL

    print(f"Database URL: {DATABASE_URL}")

    # Initialize engine
    engine = CapsuleEngine(db_manager=db)

    print("\n=== TEST 1: Load ALL capsules (exclude_demo=False) ===")
    all_capsules = await engine.load_chain_async(skip=0, limit=100, exclude_demo=False)
    print(f"Total capsules: {len(all_capsules)}")
    demo_count = sum(1 for c in all_capsules if c.capsule_id.startswith("demo-"))
    print(f"Demo capsules: {demo_count}")
    print(f"Real capsules: {len(all_capsules) - demo_count}")

    print("\n=== TEST 2: Load FILTERED capsules (exclude_demo=True) ===")
    filtered_capsules = await engine.load_chain_async(
        skip=0, limit=100, exclude_demo=True
    )
    print(f"Total capsules: {len(filtered_capsules)}")
    demo_count_filtered = sum(
        1 for c in filtered_capsules if c.capsule_id.startswith("demo-")
    )
    print(f"Demo capsules: {demo_count_filtered}")
    print(f"Real capsules: {len(filtered_capsules) - demo_count_filtered}")

    if demo_count_filtered == 0:
        print("\n✅ SUCCESS: Filtering is working correctly!")
    else:
        print(
            f"\n❌ FAILURE: Filtering not working - found {demo_count_filtered} demo capsules when there should be 0"
        )
        print("\nDemo capsules that leaked through:")
        for c in filtered_capsules:
            if c.capsule_id.startswith("demo-"):
                print(f"  - {c.capsule_id}")


if __name__ == "__main__":
    asyncio.run(test_filtering())
