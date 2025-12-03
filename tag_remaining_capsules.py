#!/usr/bin/env python3
"""
Tag the 4 remaining capsules that don't have a metadata field
"""
import asyncio
from sqlalchemy import text
import os

# Force PostgreSQL
os.environ[
    "DATABASE_URL"
] = "postgresql+asyncpg://uatp_user:uatp_password@localhost:5432/uatp_capsule_engine"

from src.core.database import db


async def tag_remaining():
    """Add metadata field with environment='test' to capsules without metadata"""
    db.init_app(None)

    try:
        async with db.get_session() as session:
            # Update capsules that don't have metadata field at all
            sql = text(
                """
                UPDATE capsules
                SET payload = jsonb_set(
                    payload::jsonb,
                    '{metadata}',
                    '{"environment": "test"}'::jsonb,
                    true
                )::json
                WHERE (payload::jsonb->'metadata') IS NULL
            """
            )

            result = await session.execute(sql)
            await session.commit()

            print(
                f"✅ Updated {result.rowcount} capsules (created metadata field with environment='test')"
            )

            # Final verification - count all capsules by environment
            verify_sql = text(
                """
                SELECT
                    payload::jsonb->'metadata'->>'environment' as env,
                    COUNT(*) as count
                FROM capsules
                GROUP BY env
                ORDER BY env NULLS LAST
            """
            )

            result = await session.execute(verify_sql)
            rows = result.fetchall()

            print("\n" + "=" * 60)
            print("FINAL VERIFICATION - All Capsules by Environment:")
            print("=" * 60)
            total = 0
            for row in rows:
                env_value = row[0] if row[0] else "NULL"
                print(f"  environment={env_value}: {row[1]} capsules")
                total += row[1]
            print("=" * 60)
            print(f"  TOTAL: {total} capsules")
            print("=" * 60)

            # Check if any capsules still have NULL environment
            null_count = sum(row[1] for row in rows if row[0] is None)
            if null_count == 0:
                print("\n✅ SUCCESS: All capsules tagged with environment='test'")
            else:
                print(
                    f"\n⚠️  WARNING: {null_count} capsules still have NULL environment"
                )

    finally:
        if db.engine:
            await db.engine.dispose()


if __name__ == "__main__":
    asyncio.run(tag_remaining())
