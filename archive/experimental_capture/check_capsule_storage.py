#!/usr/bin/env python3
"""Check how capsules are stored in the database"""

import asyncio
import json

import asyncpg


async def check_storage():
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        database="uatp_capsule_engine",
        user="uatp_user",
        password="uatp_password",
    )

    try:
        # Get a few capsules to see the structure
        rows = await conn.fetch(
            """
            SELECT capsule_id, capsule_type, payload
            FROM capsules
            ORDER BY timestamp DESC
            LIMIT 10
        """
        )

        for row in rows:
            print(f"\n{'='*60}")
            print(f"Database capsule_id column: {row['capsule_id']}")
            print(f"Database capsule_type: {row['capsule_type']}")

            payload = row["payload"]
            if isinstance(payload, str):
                payload = json.loads(payload)

            if isinstance(payload, dict):
                if "capsule_id" in payload:
                    print(f"Payload capsule_id field: {payload['capsule_id']}")
                    print(
                        "✓ Payload contains full capsule data (backwards compat mode)"
                    )
                else:
                    print("✗ Payload contains only type-specific data (new format)")

            print(f"Match: {row['capsule_id'] == payload.get('capsule_id', 'N/A')}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_storage())
