#!/usr/bin/env python3
"""
Tag capsules with environment='test' using the correct payload structure
"""
import asyncio
from sqlalchemy import text
import os

# Force PostgreSQL
os.environ[
    "DATABASE_URL"
] = "postgresql+asyncpg://uatp_user:uatp_password@localhost:5432/uatp_capsule_engine"

from src.core.database import db


async def tag_with_correct_path():
    """Add environment tag to payload->metadata (not analysis_metadata)"""
    db.init_app(None)

    try:
        async with db.get_session() as session:
            # First, check the current structure
            check_sql = text(
                """
                SELECT
                    capsule_id,
                    payload::jsonb->'metadata' as metadata,
                    payload::jsonb->'metadata'->>'environment' as env
                FROM capsules
                LIMIT 1
            """
            )
            result = await session.execute(check_sql)
            row = result.fetchone()
            print(f"Sample capsule: {row[0]}")
            print(f"Current metadata: {row[1]}")
            print(f"Current environment: {row[2]}\n")

            # Update all capsules - add environment to metadata field
            sql = text(
                """
                UPDATE capsules
                SET payload = jsonb_set(
                    COALESCE(payload::jsonb, '{}'::jsonb),
                    '{metadata,environment}',
                    '"test"',
                    true
                )::json
                WHERE (payload::jsonb->'metadata'->>'environment') IS NULL
            """
            )

            result = await session.execute(sql)
            await session.commit()

            print(
                f"✅ Updated {result.rowcount} capsules with metadata.environment='test'"
            )

            # Verify
            verify_sql = text(
                """
                SELECT
                    payload::jsonb->'metadata'->>'environment' as env,
                    COUNT(*) as count
                FROM capsules
                GROUP BY env
            """
            )

            result = await session.execute(verify_sql)
            rows = result.fetchall()

            print("\nVerification:")
            for row in rows:
                env_value = row[0] if row[0] else "NULL"
                print(f"  metadata.environment={env_value}: {row[1]} capsules")

    finally:
        if db.engine:
            await db.engine.dispose()


if __name__ == "__main__":
    asyncio.run(tag_with_correct_path())
