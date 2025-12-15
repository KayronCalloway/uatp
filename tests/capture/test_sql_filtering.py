#!/usr/bin/env python3
"""Test SQL filtering directly"""

import asyncio

import asyncpg


async def test_sql():
    """Test the SQL filtering"""
    conn = await asyncpg.connect(
        user="uatp_user",
        password="uatp_password",
        database="uatp_capsule_engine",
        host="localhost",
    )

    print("=== Testing SQL queries ===\n")

    # Test 1: Count all capsules
    total = await conn.fetchval("SELECT COUNT(*) FROM capsules")
    print(f"Total capsules: {total}")

    # Test 2: Count demo capsules
    demo = await conn.fetchval(
        "SELECT COUNT(*) FROM capsules WHERE capsule_id LIKE 'demo-%'"
    )
    print(f"Demo capsules (LIKE 'demo-%'): {demo}")

    # Test 3: Count real capsules
    real = await conn.fetchval(
        "SELECT COUNT(*) FROM capsules WHERE capsule_id NOT LIKE 'demo-%'"
    )
    print(f"Real capsules (NOT LIKE 'demo-%'): {real}")

    # Test 4: Get first 10 capsule IDs (all)
    rows = await conn.fetch(
        "SELECT capsule_id FROM capsules ORDER BY timestamp DESC LIMIT 10"
    )
    print("\nFirst 10 capsule IDs (all):")
    for row in rows:
        prefix = "DEMO" if row["capsule_id"].startswith("demo-") else "REAL"
        print(f"  [{prefix}] {row['capsule_id']}")

    # Test 5: Get first 10 capsule IDs (excluding demo)
    rows_filtered = await conn.fetch(
        "SELECT capsule_id FROM capsules WHERE capsule_id NOT LIKE 'demo-%' ORDER BY timestamp DESC LIMIT 10"
    )
    print("\nFirst 10 capsule IDs (excluding demo):")
    for row in rows_filtered:
        prefix = "DEMO" if row["capsule_id"].startswith("demo-") else "REAL"
        print(f"  [{prefix}] {row['capsule_id']}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(test_sql())
