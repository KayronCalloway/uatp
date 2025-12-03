#!/usr/bin/env python3
"""
SQLite Database Setup
====================

This script sets up the SQLite database with the required tables for capsule storage.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.core.database import db
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def create_sqlite_tables():
    """Create tables for SQLite database."""

    logger.info("🗄️  Creating SQLite database tables...")

    # Initialize database
    db.init_app(None)

    # Create tables using SQLAlchemy
    try:
        await db.create_all()
        logger.info("✅ SQLAlchemy tables created")
    except Exception as e:
        logger.error(f"❌ SQLAlchemy table creation failed: {e}")

    # Create additional tables manually for compatibility
    async with db.get_session() as session:
        # Create capsules table if not exists (SQLite compatible)
        await session.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS capsules_filter (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capsule_id TEXT UNIQUE NOT NULL,
                capsule_type TEXT NOT NULL,
                version TEXT NOT NULL DEFAULT '1.0',
                timestamp DATETIME NOT NULL,
                status TEXT NOT NULL DEFAULT 'SEALED',
                verification TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Create attributions table if not exists
        await session.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS attributions_filter (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                capsule_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                significance_score REAL NOT NULL DEFAULT 0.0,
                timestamp DATETIME NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Create indexes for SQLite
        sqlite_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_capsules_filter_capsule_id ON capsules_filter(capsule_id)",
            "CREATE INDEX IF NOT EXISTS idx_capsules_filter_type ON capsules_filter(capsule_type)",
            "CREATE INDEX IF NOT EXISTS idx_capsules_filter_timestamp ON capsules_filter(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_capsules_filter_status ON capsules_filter(status)",
            "CREATE INDEX IF NOT EXISTS idx_attributions_filter_user_id ON attributions_filter(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_attributions_filter_capsule_id ON attributions_filter(capsule_id)",
            "CREATE INDEX IF NOT EXISTS idx_attributions_filter_platform ON attributions_filter(platform)",
            "CREATE INDEX IF NOT EXISTS idx_attributions_filter_timestamp ON attributions_filter(timestamp)",
        ]

        for index_sql in sqlite_indexes:
            await session.execute(text(index_sql))

        await session.commit()

        logger.info("✅ Additional SQLite tables and indexes created")


async def verify_database():
    """Verify database setup."""

    logger.info("🔍 Verifying database setup...")

    async with db.get_session() as session:
        # Check if tables exist
        result = await session.execute(
            text(
                """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%capsules%'
        """
            )
        )

        capsule_tables = [row[0] for row in result.fetchall()]

        logger.info(f"📊 Found capsule tables: {capsule_tables}")

        # Check if we can insert and query data
        try:
            # Insert test data
            await session.execute(
                text(
                    """
                INSERT OR IGNORE INTO capsules_filter 
                (capsule_id, capsule_type, timestamp, verification, payload) 
                VALUES ('test-capsule-1', 'reasoning_trace', datetime('now'), '{}', '{}')
            """
                )
            )

            # Query test data
            result = await session.execute(
                text(
                    """
                SELECT capsule_id, capsule_type FROM capsules_filter 
                WHERE capsule_id = 'test-capsule-1'
            """
                )
            )

            test_row = result.fetchone()

            if test_row:
                logger.info(f"✅ Database test successful: {test_row}")

                # Clean up test data
                await session.execute(
                    text(
                        """
                    DELETE FROM capsules_filter WHERE capsule_id = 'test-capsule-1'
                """
                    )
                )
            else:
                logger.warning("⚠️  Database test failed - no test data found")

            await session.commit()

        except Exception as e:
            logger.error(f"❌ Database test failed: {e}")
            await session.rollback()
            raise


async def get_database_stats():
    """Get database statistics."""

    logger.info("📊 Getting database statistics...")

    async with db.get_session() as session:
        # Get table counts
        tables_to_check = [
            ("capsules", "Main capsule table"),
            ("capsules_filter", "Filter capsule table"),
            ("attributions_filter", "Attribution table"),
        ]

        stats = {}

        for table_name, description in tables_to_check:
            try:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                )
                count = result.scalar()
                stats[table_name] = count
                logger.info(f"   {description}: {count} rows")
            except Exception as e:
                logger.debug(f"   {description}: Table not found or error - {e}")
                stats[table_name] = 0

        # Get database file size
        db_path = "./uatp_dev.db"
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            size_mb = size_bytes / (1024 * 1024)
            logger.info(f"   Database file size: {size_mb:.2f} MB")
            stats["database_size_mb"] = size_mb

        return stats


async def main():
    """Main setup function."""

    print("🚀 UATP Capsule Engine - SQLite Database Setup")
    print("=" * 60)

    try:
        # Create tables
        await create_sqlite_tables()

        # Verify setup
        await verify_database()

        # Get stats
        stats = await get_database_stats()

        print(f"\n✅ SQLite Database Setup Complete!")
        print(f"   Database file: ./uatp_dev.db")
        print(f"   Tables created with indexes")
        print(f"   Ready for capsule storage")

        # Check if we have existing JSONL data to migrate
        jsonl_file = "./capsule_chain.jsonl"
        if os.path.exists(jsonl_file):
            with open(jsonl_file, "r") as f:
                lines = f.readlines()

            valid_lines = [line for line in lines if line.strip()]

            if valid_lines:
                print(f"\n📄 Found existing JSONL data:")
                print(f"   File: {jsonl_file}")
                print(f"   Lines: {len(valid_lines)}")
                print(f"   Ready for migration to database")

        return True

    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
