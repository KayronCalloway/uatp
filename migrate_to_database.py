#!/usr/bin/env python3
"""
JSONL to Database Migration Script
=================================

This script migrates existing JSONL capsules to the PostgreSQL database
while maintaining all attribution data and metadata.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from filters.database_capsule_creator import (
    get_database_capsule_creator,
    initialize_database_capsule_creator,
)
from database.connection import get_database_manager, initialize_database
from database.migrations import create_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def setup_database():
    """Set up database connection and create tables if needed."""

    print("🔧 Setting up database connection...")

    try:
        # Initialize database manager
        db_manager = await initialize_database()

        # Create tables if they don't exist
        await create_tables(db_manager)

        print("✅ Database setup completed")
        return db_manager

    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        raise


async def analyze_jsonl_file(jsonl_file: str):
    """Analyze the JSONL file before migration."""

    print(f"📊 Analyzing {jsonl_file}...")

    stats = {
        "total_lines": 0,
        "valid_capsules": 0,
        "auto_filtered_capsules": 0,
        "platforms": {},
        "date_range": {"earliest": None, "latest": None},
        "significance_distribution": {"low": 0, "medium": 0, "high": 0, "very_high": 0},
        "sample_capsules": [],
    }

    try:
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                stats["total_lines"] += 1

                if not line.strip():
                    continue

                try:
                    capsule_data = json.loads(line)
                    stats["valid_capsules"] += 1

                    # Check if auto-filtered
                    if capsule_data.get("metadata", {}).get("auto_encapsulated"):
                        stats["auto_filtered_capsules"] += 1

                    # Platform stats
                    platform = capsule_data.get("metadata", {}).get(
                        "platform", "unknown"
                    )
                    stats["platforms"][platform] = (
                        stats["platforms"].get(platform, 0) + 1
                    )

                    # Date range
                    timestamp_str = capsule_data.get("timestamp")
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromisoformat(
                                timestamp_str.replace("Z", "+00:00")
                            )
                            if (
                                not stats["date_range"]["earliest"]
                                or timestamp < stats["date_range"]["earliest"]
                            ):
                                stats["date_range"]["earliest"] = timestamp
                            if (
                                not stats["date_range"]["latest"]
                                or timestamp > stats["date_range"]["latest"]
                            ):
                                stats["date_range"]["latest"] = timestamp
                        except:
                            pass

                    # Significance distribution
                    significance_score = capsule_data.get("metadata", {}).get(
                        "significance_score", 0.0
                    )
                    if significance_score < 0.6:
                        stats["significance_distribution"]["low"] += 1
                    elif significance_score < 1.0:
                        stats["significance_distribution"]["medium"] += 1
                    elif significance_score < 2.0:
                        stats["significance_distribution"]["high"] += 1
                    else:
                        stats["significance_distribution"]["very_high"] += 1

                    # Sample capsules
                    if len(stats["sample_capsules"]) < 3:
                        stats["sample_capsules"].append(
                            {
                                "capsule_id": capsule_data.get("capsule_id"),
                                "type": capsule_data.get("type"),
                                "platform": platform,
                                "significance_score": significance_score,
                                "timestamp": timestamp_str,
                            }
                        )

                except json.JSONDecodeError:
                    continue

        print(f"📈 Analysis Results:")
        print(f"   Total lines: {stats['total_lines']}")
        print(f"   Valid capsules: {stats['valid_capsules']}")
        print(f"   Auto-filtered capsules: {stats['auto_filtered_capsules']}")
        print(f"   Platforms: {dict(stats['platforms'])}")
        print(
            f"   Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}"
        )
        print(
            f"   Significance distribution: {dict(stats['significance_distribution'])}"
        )

        return stats

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None


async def perform_migration(jsonl_file: str, force: bool = False):
    """Perform the actual migration."""

    print(f"🚀 Starting migration from {jsonl_file}")

    try:
        # Initialize database capsule creator
        creator = await initialize_database_capsule_creator()

        # Check if database is available
        if not creator._db_connected:
            print("❌ Database not connected - cannot perform migration")
            return None

        # Perform migration
        migration_stats = await creator.migrate_from_jsonl(jsonl_file)

        print(f"✅ Migration completed!")
        print(f"   Processed: {migration_stats['total_processed']}")
        print(f"   Successful: {migration_stats['successful_migrations']}")
        print(f"   Failed: {migration_stats['failed_migrations']}")
        print(f"   Skipped (duplicates): {migration_stats['skipped_duplicates']}")

        if migration_stats["errors"]:
            print(f"   Errors: {len(migration_stats['errors'])}")
            for error in migration_stats["errors"][:5]:  # Show first 5 errors
                print(f"     {error}")

        return migration_stats

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return None


async def verify_migration(jsonl_file: str):
    """Verify the migration was successful."""

    print("🔍 Verifying migration...")

    try:
        creator = get_database_capsule_creator()

        # Get database stats
        db_stats = await creator.get_capsule_stats()

        print(f"📊 Database Statistics:")
        print(f"   Total capsules: {db_stats.total_capsules}")
        print(f"   Auto-filtered capsules: {db_stats.auto_filtered_capsules}")
        print(f"   Database size: {db_stats.database_size / 1024 / 1024:.1f} MB")
        print(f"   Platforms: {dict(db_stats.platforms)}")
        print(
            f"   Significance distribution: {dict(db_stats.significance_distribution)}"
        )

        # Get some recent capsules
        recent_capsules = await creator.get_recent_capsules(5)

        if recent_capsules:
            print(f"\n🔄 Recent Capsules:")
            for capsule in recent_capsules:
                print(
                    f"   • {capsule['capsule_id']} ({capsule['platform']}) - {capsule['significance_score']:.2f}"
                )

        return db_stats

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return None


async def backup_jsonl_file(jsonl_file: str):
    """Create a backup of the JSONL file."""

    backup_file = f"{jsonl_file}.backup.{int(datetime.now().timestamp())}"

    try:
        import shutil

        shutil.copy2(jsonl_file, backup_file)
        print(f"💾 Backup created: {backup_file}")
        return backup_file

    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None


async def main():
    """Main migration function."""

    print("🚀 UATP Capsule Engine - JSONL to Database Migration")
    print("=" * 60)

    # Check for JSONL file
    jsonl_file = "/Users/kay/uatp-capsule-engine/capsule_chain.jsonl"

    if not os.path.exists(jsonl_file):
        print(f"❌ JSONL file not found: {jsonl_file}")
        return

    try:
        # Step 1: Set up database
        db_manager = await setup_database()

        # Step 2: Analyze JSONL file
        analysis_stats = await analyze_jsonl_file(jsonl_file)
        if not analysis_stats:
            print("❌ Analysis failed - aborting migration")
            return

        # Step 3: Confirm migration
        print(
            f"\n❓ Ready to migrate {analysis_stats['valid_capsules']} capsules to database?"
        )
        print(f"   This will preserve all attribution data and metadata.")
        print(f"   The original JSONL file will be backed up.")

        # Auto-confirm for demo
        confirm = True  # input("Continue? (y/N): ").lower().strip() == 'y'

        if not confirm:
            print("Migration cancelled")
            return

        # Step 4: Create backup
        backup_file = await backup_jsonl_file(jsonl_file)
        if not backup_file:
            print("❌ Backup failed - aborting migration")
            return

        # Step 5: Perform migration
        migration_stats = await perform_migration(jsonl_file)
        if not migration_stats:
            print("❌ Migration failed")
            return

        # Step 6: Verify migration
        verification_stats = await verify_migration(jsonl_file)

        print(f"\n✅ MIGRATION SUCCESSFUL!")
        print(f"   Capsules are now stored in PostgreSQL database")
        print(f"   Original JSONL backed up to: {backup_file}")
        print(f"   Database contains {verification_stats.total_capsules} capsules")

        # Update real-time generator to use database
        print(f"\n📝 Next Steps:")
        print(f"   1. Update real-time generator to use database storage")
        print(f"   2. Test live capsule creation with database backend")
        print(f"   3. Set up database indexing for optimal performance")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Clean up database connection
        if "db_manager" in locals():
            await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
