#!/usr/bin/env python3
"""
PostgreSQL Migration Script
==========================

This script migrates the UATP system from SQLite/JSONL to PostgreSQL.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Import required modules
from src.database.postgresql_adapter import get_postgresql_adapter
from src.database.postgresql_schema import get_postgresql_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PostgreSQLMigrator:
    """PostgreSQL migration manager."""

    def __init__(self):
        self.pg_manager = get_postgresql_manager()
        self.pg_adapter = get_postgresql_adapter()

        logger.info(" PostgreSQL Migrator initialized")

    async def check_prerequisites(self) -> bool:
        """Check if prerequisites are met."""

        logger.info(" Checking prerequisites...")

        try:
            # Test PostgreSQL connection
            await self.pg_manager.create_connection_pool()
            health = await self.pg_manager.health_check()

            if health["status"] != "healthy":
                logger.error("[ERROR] PostgreSQL is not healthy")
                return False

            logger.info("[OK] PostgreSQL connection verified")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Prerequisites check failed: {e}")
            return False

    async def setup_database(self) -> bool:
        """Set up the PostgreSQL database."""

        logger.info(" Setting up PostgreSQL database...")

        try:
            # Create schema
            await self.pg_manager.create_schema()

            # Create indexes
            await self.pg_manager.create_indexes()

            # Create functions
            await self.pg_manager.create_functions()

            logger.info("[OK] PostgreSQL database setup completed")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Database setup failed: {e}")
            return False

    async def migrate_data(self, jsonl_files: List[str] = None) -> bool:
        """Migrate data from JSONL files to PostgreSQL."""

        if jsonl_files is None:
            jsonl_files = ["capsule_chain.jsonl", "src/filters/capsule_creator.jsonl"]

        logger.info(f" Migrating data from {len(jsonl_files)} files...")

        total_migrated = 0

        for jsonl_file in jsonl_files:
            if not os.path.exists(jsonl_file):
                logger.warning(f"[WARN] File not found: {jsonl_file}")
                continue

            logger.info(f" Processing {jsonl_file}...")

            try:
                with open(jsonl_file) as f:
                    file_count = 0
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            capsule_data = json.loads(line)

                            # Standardize capsule data
                            capsule_data = self._standardize_capsule_data(capsule_data)

                            # Create capsule in PostgreSQL
                            capsule_id = await self.pg_adapter.create_capsule(
                                capsule_data
                            )

                            if capsule_id:
                                file_count += 1
                                total_migrated += 1

                                if file_count % 10 == 0:
                                    logger.info(
                                        f"   Migrated {file_count} capsules from {jsonl_file}"
                                    )

                        except json.JSONDecodeError:
                            logger.warning(
                                f"Invalid JSON in {jsonl_file}: {line[:100]}..."
                            )
                            continue
                        except Exception as e:
                            logger.warning(f"Failed to migrate capsule: {e}")
                            continue

                    logger.info(
                        f"[OK] Migrated {file_count} capsules from {jsonl_file}"
                    )

            except Exception as e:
                logger.error(f"[ERROR] Failed to process {jsonl_file}: {e}")
                continue

        logger.info(f"[OK] Total migration completed: {total_migrated} capsules")
        return total_migrated > 0

    def _standardize_capsule_data(self, capsule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize capsule data for PostgreSQL."""

        standardized = {
            "capsule_id": capsule_data.get(
                "capsule_id", f"migrated_{datetime.now().timestamp()}"
            ),
            "type": self._map_capsule_type(
                capsule_data.get("type", "interaction_capsule")
            ),
            "platform": self._map_platform(capsule_data.get("platform", "other")),
            "user_id": capsule_data.get("user_id", "system"),
            "session_id": capsule_data.get("session_id"),
            "model": capsule_data.get("model"),
            "user_message": capsule_data.get("user_message"),
            "ai_response": capsule_data.get("ai_response"),
            "content": capsule_data.get("content"),
            "reasoning_trace": capsule_data.get("reasoning_trace", {}),
            "metadata": capsule_data.get("metadata", {}),
            "significance_score": float(capsule_data.get("significance_score", 0.0)),
            "confidence_score": float(capsule_data.get("confidence_score", 0.0)),
            "timestamp": capsule_data.get("timestamp", datetime.now().isoformat()),
        }

        # Ensure timestamp is properly formatted
        if isinstance(standardized["timestamp"], str):
            try:
                # Try to parse and reformat
                dt = datetime.fromisoformat(
                    standardized["timestamp"].replace("Z", "+00:00")
                )
                standardized["timestamp"] = dt.isoformat()
            except:
                standardized["timestamp"] = datetime.now().isoformat()

        return standardized

    def _map_capsule_type(self, capsule_type: str) -> str:
        """Map capsule type to PostgreSQL enum."""

        type_mapping = {
            "interaction_capsule": "interaction_capsule",
            "reasoning_capsule": "reasoning_capsule",
            "consent_capsule": "consent_capsule",
            "perspective_capsule": "perspective_capsule",
            "economic_capsule": "economic_capsule",
            "specialized_capsule": "specialized_capsule",
        }

        return type_mapping.get(capsule_type, "interaction_capsule")

    def _map_platform(self, platform: str) -> str:
        """Map platform to PostgreSQL enum."""

        platform_mapping = {
            "openai": "openai",
            "anthropic": "anthropic",
            "cursor": "cursor",
            "windsurf": "windsurf",
            "claude_code": "claude_code",
        }

        return platform_mapping.get(platform, "other")

    async def verify_migration(self) -> bool:
        """Verify the migration was successful."""

        logger.info(" Verifying migration...")

        try:
            # Get statistics
            stats = await self.pg_adapter.get_capsule_stats()

            logger.info(" Migration verification:")
            logger.info(f"   Total capsules: {stats['total_capsules']}")
            logger.info(f"   Active capsules: {stats['active_capsules']}")
            logger.info(f"   Platforms: {list(stats['platforms'].keys())}")
            logger.info(f"   Average significance: {stats['avg_significance']:.2f}")

            # Test basic operations
            recent_capsules = await self.pg_adapter.get_recent_capsules(limit=5)
            logger.info(f"   Recent capsules: {len(recent_capsules)}")

            if stats["total_capsules"] > 0:
                logger.info("[OK] Migration verification successful")
                return True
            else:
                logger.warning("[WARN] No capsules found in PostgreSQL")
                return False

        except Exception as e:
            logger.error(f"[ERROR] Migration verification failed: {e}")
            return False

    async def create_backup(self) -> bool:
        """Create a backup of existing data."""

        logger.info(" Creating backup of existing data...")

        try:
            backup_dir = f"backups/migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(backup_dir, exist_ok=True)

            # List of files to backup
            files_to_backup = [
                "capsule_chain.jsonl",
                "src/filters/capsule_creator.jsonl",
                "chain_seals.json",
            ]

            for file_path in files_to_backup:
                if os.path.exists(file_path):
                    backup_path = os.path.join(backup_dir, os.path.basename(file_path))

                    # Copy file
                    with open(file_path) as src, open(backup_path, "w") as dst:
                        dst.write(src.read())

                    logger.info(f" Backed up {file_path} to {backup_path}")

            logger.info(f"[OK] Backup created in {backup_dir}")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Backup creation failed: {e}")
            return False

    async def cleanup(self):
        """Clean up resources."""

        logger.info(" Cleaning up...")

        try:
            if self.pg_manager.pool:
                await self.pg_manager.close_connection_pool()

            logger.info("[OK] Cleanup completed")

        except Exception as e:
            logger.error(f"[ERROR] Cleanup failed: {e}")


async def main():
    """Main migration function."""

    print(" PostgreSQL Migration Tool")
    print("=" * 40)

    migrator = PostgreSQLMigrator()

    try:
        # Check prerequisites
        if not await migrator.check_prerequisites():
            print("[ERROR] Prerequisites not met. Please check PostgreSQL connection.")
            return

        # Create backup
        if not await migrator.create_backup():
            print("[ERROR] Backup creation failed. Migration aborted.")
            return

        # Setup database
        if not await migrator.setup_database():
            print("[ERROR] Database setup failed. Migration aborted.")
            return

        # Migrate data
        if not await migrator.migrate_data():
            print("[ERROR] Data migration failed.")
            return

        # Verify migration
        if not await migrator.verify_migration():
            print("[ERROR] Migration verification failed.")
            return

        print("\n[OK] PostgreSQL migration completed successfully!")
        print("\nNext steps:")
        print("1. Update your configuration to use PostgreSQL")
        print("2. Test the system with the new database")
        print("3. Monitor performance and adjust as needed")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")

    finally:
        await migrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
