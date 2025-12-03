"""
Database Migration System
Production-ready database migrations for UATP
"""

import logging
import os
import sys
from dotenv import load_dotenv

load_dotenv()
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import text

from .connection import get_database_manager

db_manager = get_database_manager()
from src.core.database import db

Base = db.Base

logger = logging.getLogger(__name__)


class MigrationManager:
    """Database migration management system"""

    def __init__(self, migrations_dir: str = "migrations"):
        self.migrations_dir = Path(migrations_dir)
        self.migrations_dir.mkdir(exist_ok=True)

    async def create_migration_table(self):
        """Create migrations tracking table"""
        async with db.get_session() as session:
            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )
            await session.commit()
            logger.info("Schema migrations table created")

    async def get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations"""
        try:
            async with db.get_session() as session:
                result = await session.execute(
                    text("SELECT version FROM schema_migrations ORDER BY version")
                )
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not read migrations table: {e}")
            return []

    async def mark_migration_applied(self, version: str):
        """Mark migration as applied"""
        async with db.get_session() as session:
            await session.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                {"version": version},
            )
            logger.info(f"Migration {version} marked as applied")

    async def run_migrations(self, target_version: Optional[str] = None):
        """Run pending migrations (async)"""
        logger.info("Starting database migrations...")

        # Ensure migration table exists
        await self.create_migration_table()
        # Get applied migrations
        applied_migrations = await self.get_applied_migrations()

        # Mark initial migration as applied if no migrations exist
        if not applied_migrations:
            initial_version = "001_initial_schema"
            await self.run_migration(initial_version)
            await self.mark_migration_applied(initial_version)
            logger.info("Initial schema migration marked as applied")

        # Run additional migrations
        pending_migrations = await self.get_pending_migrations()

        for migration in pending_migrations:
            if target_version and migration > target_version:
                break

            logger.info(f"Running migration: {migration}")
            await self.run_migration(migration)
            await self.mark_migration_applied(migration)

        logger.info("Database migrations completed")

    async def get_pending_migrations(self) -> List[str]:
        """Get list of pending migrations"""
        applied = set(await self.get_applied_migrations())

        # Define available migrations
        available_migrations = [
            "001_initial_schema",
            "002_add_indexes",
            "003_add_audit_triggers",
            "004_add_partitioning",
        ]

        return [m for m in available_migrations if m not in applied]

    async def run_migration(self, version: str):
        """Run a specific migration (async)"""
        migration_method = getattr(self, f"migrate_{version}", None)

        if migration_method:
            await migration_method()
        else:
            logger.warning(f"Migration method not found: {version}")

    async def migrate_001_initial_schema(self):
        """Initial schema migration: create all tables."""
        logger.info("Creating all tables for initial schema...")

        # Create capsules table
        async with db.get_session() as session:
            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS capsules (
                    id SERIAL PRIMARY KEY,
                    capsule_id VARCHAR(255) UNIQUE NOT NULL,
                    capsule_type VARCHAR(50) NOT NULL,
                    version VARCHAR(10) NOT NULL DEFAULT '1.0',
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'SEALED',
                    verification JSONB NOT NULL,
                    payload JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )

            # Create attributions table
            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS attributions (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    conversation_id VARCHAR(255) NOT NULL,
                    capsule_id VARCHAR(255) NOT NULL,
                    platform VARCHAR(50) NOT NULL,
                    significance_score FLOAT NOT NULL DEFAULT 0.0,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )

            await session.commit()

        logger.info("All tables created.")

    async def migrate_002_add_indexes(self):
        """Add performance indexes"""
        logger.info("Adding performance indexes...")

        from src.core.config import DATABASE_URL

        is_sqlite = "sqlite" in DATABASE_URL.lower()

        # Common indexes that work on both SQLite and PostgreSQL
        indexes = [
            # Capsules table indexes
            "CREATE INDEX IF NOT EXISTS idx_capsules_capsule_id ON capsules(capsule_id)",
            "CREATE INDEX IF NOT EXISTS idx_capsules_type ON capsules(capsule_type)",
            "CREATE INDEX IF NOT EXISTS idx_capsules_timestamp ON capsules(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_capsules_status ON capsules(status)",
            # Attributions table indexes
            "CREATE INDEX IF NOT EXISTS idx_attributions_user_id ON attributions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_attributions_capsule_id ON attributions(capsule_id)",
            "CREATE INDEX IF NOT EXISTS idx_attributions_platform ON attributions(platform)",
            "CREATE INDEX IF NOT EXISTS idx_attributions_timestamp ON attributions(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_attributions_user_platform ON attributions(user_id, platform)",
            "CREATE INDEX IF NOT EXISTS idx_attributions_significance ON attributions(significance_score)",
        ]

        # PostgreSQL-specific JSONB indexes
        if not is_sqlite:
            indexes.extend(
                [
                    "CREATE INDEX IF NOT EXISTS idx_capsules_platform ON capsules USING GIN ((payload->'analysis_metadata'->>'platform'))",
                    "CREATE INDEX IF NOT EXISTS idx_capsules_user_id ON capsules USING GIN ((payload->'analysis_metadata'->>'user_id'))",
                    "CREATE INDEX IF NOT EXISTS idx_capsules_significance_score ON capsules USING BTREE (((payload->'analysis_metadata'->>'significance_score')::float))",
                    "CREATE INDEX IF NOT EXISTS idx_capsules_auto_filtered ON capsules USING GIN ((payload->'analysis_metadata'->>'auto_filtered'))",
                ]
            )

        async with db.get_session() as session:
            for index_sql in indexes:
                try:
                    await session.execute(text(index_sql))
                except Exception as e:
                    logger.warning(f"Could not create index: {e}")

        logger.info("Performance indexes added")

    async def migrate_003_add_audit_triggers(self):
        """Add audit triggers for important tables"""
        logger.info("Adding audit triggers...")

        from src.core.config import DATABASE_URL

        # Only add if PostgreSQL
        if "postgresql" in DATABASE_URL.lower():
            audit_function = """
                CREATE OR REPLACE FUNCTION audit_trigger_function()
                RETURNS TRIGGER AS $$
                BEGIN
                    IF TG_OP = 'UPDATE' THEN
                        INSERT INTO audit_logs (
                            user_id,
                            event_type,
                            event_data,
                            timestamp
                        ) VALUES (
                            NEW.user_id,
                            TG_TABLE_NAME || '_updated',
                            json_build_object(
                                'old', row_to_json(OLD),
                                'new', row_to_json(NEW)
                            ),
                            NOW()
                        );
                        RETURN NEW;
                    ELSIF TG_OP = 'DELETE' THEN
                        INSERT INTO audit_logs (
                            user_id,
                            event_type,
                            event_data,
                            timestamp
                        ) VALUES (
                            OLD.user_id,
                            TG_TABLE_NAME || '_deleted',
                            row_to_json(OLD),
                            NOW()
                        );
                        RETURN OLD;
                    END IF;
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;
            """

            triggers = [
                "CREATE TRIGGER audit_users AFTER UPDATE OR DELETE ON users FOR EACH ROW EXECUTE FUNCTION audit_trigger_function()",
                "CREATE TRIGGER audit_payments AFTER UPDATE OR DELETE ON payment_transactions FOR EACH ROW EXECUTE FUNCTION audit_trigger_function()",
                "CREATE TRIGGER audit_consents AFTER UPDATE OR DELETE ON consents FOR EACH ROW EXECUTE FUNCTION audit_trigger_function()",
            ]

            async with db.get_session() as session:
                await session.execute(text(audit_function))

                for trigger_sql in triggers:
                    try:
                        await session.execute(text(trigger_sql))
                    except Exception as e:
                        logger.warning(f"Could not create trigger: {e}")

        logger.info("Audit triggers added")

    async def migrate_004_add_partitioning(self):
        """Add table partitioning for large tables"""
        logger.info("Setting up table partitioning...")

        from src.core.config import DATABASE_URL

        # Only for PostgreSQL
        if "postgresql" in DATABASE_URL.lower():
            # Partition attributions table by month
            partition_sql = """
                -- Create partitioned table for new attributions
                CREATE TABLE IF NOT EXISTS attributions_partitioned (
                    LIKE attributions INCLUDING ALL
                ) PARTITION BY RANGE (timestamp);

                -- Create partition for current month
                CREATE TABLE IF NOT EXISTS attributions_y2024m07
                PARTITION OF attributions_partitioned
                FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');

                -- Create partition for next month
                CREATE TABLE IF NOT EXISTS attributions_y2024m08
                PARTITION OF attributions_partitioned
                FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');
            """

            async with db.get_session() as session:
                try:
                    await session.execute(text(partition_sql))
                    logger.info("Table partitioning configured")
                except Exception as e:
                    logger.warning(f"Could not create partitioning: {e}")

    async def rollback_migration(self, version: str):
        """Rollback a migration"""
        logger.info(f"Rolling back migration: {version}")

        rollback_method = getattr(self, f"rollback_{version}", None)

        if rollback_method:
            await rollback_method()

            # Remove from applied migrations
            async with db.get_session() as session:
                await session.execute(
                    text("DELETE FROM schema_migrations WHERE version = :version"),
                    {"version": version},
                )
        else:
            logger.warning(f"Rollback method not found: {version}")

    def get_migration_status(self) -> Dict:
        """Get migration status"""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()

        return {
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied_migrations": applied,
            "pending_migrations": pending,
            "last_applied": applied[-1] if applied else None,
        }


# Global migration manager
migration_manager = MigrationManager()


async def run_migrations(target_version: Optional[str] = None):
    """Run database migrations (async version)"""
    await migration_manager.run_migrations(target_version)


def init_db_for_cli():
    """Initialize SQLAlchemy async DB for CLI/standalone usage."""
    db.init_app(None)


def run_migrations_sync(target_version: Optional[str] = None):
    init_db_for_cli()
    import asyncio

    asyncio.run(run_migrations(target_version))


def check_migration_status():
    """Check migration status"""
    try:
        status = migration_manager.get_migration_status()

        print("📊 Migration Status:")
        print(f"   Applied: {status['applied_count']}")
        print(f"   Pending: {status['pending_count']}")

        if status["last_applied"]:
            print(f"   Last applied: {status['last_applied']}")

        if status["pending_migrations"]:
            print(f"   Pending migrations: {', '.join(status['pending_migrations'])}")

        return status
    except Exception as e:
        print(f"❌ Could not check migration status: {e}")
        return None


# CLI functions
def create_database():
    """Create database with initial schema"""
    print("🗄️  Creating database with initial schema...")

    try:
        # Initialize database
        db_manager.initialize()

        # Run migrations
        run_migrations_sync()

        print("✅ Database created successfully!")

        # Create test data if in development
        if os.getenv("ENVIRONMENT", "development") == "development":
            from .connection import create_test_data

            create_test_data()
            print("✅ Test data created!")

    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        logger.error(f"Database creation error: {e}")


def reset_database():
    """Reset database (drop and recreate)"""
    print("⚠️  Resetting database (this will delete all data)...")

    try:
        # Initialize database
        db_manager.initialize()

        # Drop all tables
        db_manager.drop_tables()

        # Run migrations
        run_migrations_sync()

        print("✅ Database reset successfully!")

    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        logger.error(f"Database reset error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "create":
            create_database()
        elif command == "reset":
            reset_database()
        elif command == "migrate":
            run_migrations_sync()
        elif command == "status":
            check_migration_status()
        else:
            print("Usage: python migrations.py [create|reset|migrate|status]")
    else:
        print("Usage: python migrations.py [create|reset|migrate|status]")
