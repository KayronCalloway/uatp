#!/usr/bin/env python3
"""
Directly update capsules with SQL to add environment tags
"""
import asyncio
from sqlalchemy import text
import os

# Force PostgreSQL
os.environ[
    "DATABASE_URL"
] = "postgresql+asyncpg://uatp_user:uatp_password@localhost:5432/uatp_capsule_engine"

from src.core.database import db


async def tag_with_sql():
    """Use raw SQL to update JSONB field"""
    db.init_app(None)

    try:
        async with db.get_session() as session:
            # Update all capsules to add test environment tag
            sql = text(
                """
                UPDATE capsules
                SET payload = jsonb_set(
                    COALESCE(payload, '{}'::jsonb),
                    '{analysis_metadata,environment}',
                    '"test"'
                )
                WHERE payload->'analysis_metadata'->>'environment' IS NULL
            """
            )

            result = await session.execute(sql)
            await session.commit()

            print(f"✅ Updated {result.rowcount} capsules with environment='test'")

            # Verify
            verify_sql = text(
                """
                SELECT
                    payload->'analysis_metadata'->>'environment' as env,
                    COUNT(*) as count
                FROM capsules
                GROUP BY env
            """
            )

            result = await session.execute(verify_sql)
            rows = result.fetchall()

            print("\nVerification:")
            for row in rows:
                print(f"  environment={row[0]}: {row[1]} capsules")

    finally:
        if db.engine:
            await db.engine.dispose()


if __name__ == "__main__":
    asyncio.run(tag_with_sql())
