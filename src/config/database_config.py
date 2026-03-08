#!/usr/bin/env python3
"""
Database Configuration for UATP Capsule Engine
==============================================

This module provides database configuration and connection management
for both SQLite and PostgreSQL backends.
"""

import logging
import os
from enum import Enum
from typing import Any, Dict

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Database type enumeration."""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


class DatabaseConfig:
    """Database configuration manager."""

    def __init__(self):
        self.db_type = self._get_database_type()
        self.config = self._load_config()

        logger.info(f"️ Database configuration loaded: {self.db_type.value}")

    def _get_database_type(self) -> DatabaseType:
        """Determine database type from environment."""

        db_type = os.getenv("DATABASE_TYPE", "sqlite").lower()

        if db_type == "postgresql":
            return DatabaseType.POSTGRESQL
        else:
            return DatabaseType.SQLITE

    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration."""

        if self.db_type == DatabaseType.POSTGRESQL:
            return self._load_postgresql_config()
        else:
            return self._load_sqlite_config()

    def _load_sqlite_config(self) -> Dict[str, Any]:
        """Load SQLite configuration."""

        return {
            "type": "sqlite",
            "database_path": os.getenv("SQLITE_PATH", "capsule_engine.db"),
            "jsonl_fallback": os.getenv("JSONL_FALLBACK", "capsule_chain.jsonl"),
            "connection_timeout": int(os.getenv("SQLITE_TIMEOUT", "30")),
            "journal_mode": os.getenv("SQLITE_JOURNAL_MODE", "WAL"),
            "synchronous": os.getenv("SQLITE_SYNCHRONOUS", "NORMAL"),
        }

    def _load_postgresql_config(self) -> Dict[str, Any]:
        """Load PostgreSQL configuration."""

        return {
            "type": "postgresql",
            "host": os.getenv("PG_HOST", "localhost"),
            "port": int(os.getenv("PG_PORT", "5432")),
            "database": os.getenv("PG_DATABASE", "uatp"),
            "user": os.getenv("PG_USER", "uatp"),
            "password": os.getenv("PG_PASSWORD", "uatp"),
            "min_connections": int(os.getenv("PG_MIN_CONNECTIONS", "5")),
            "max_connections": int(os.getenv("PG_MAX_CONNECTIONS", "20")),
            "command_timeout": int(os.getenv("PG_COMMAND_TIMEOUT", "30")),
            "ssl_mode": os.getenv("PG_SSL_MODE", "prefer"),
        }

    def get_connection_string(self) -> str:
        """Get database connection string."""

        if self.db_type == DatabaseType.POSTGRESQL:
            config = self.config
            return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        else:
            return f"sqlite:///{self.config['database_path']}"

    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL."""
        return self.db_type == DatabaseType.POSTGRESQL

    def is_sqlite(self) -> bool:
        """Check if using SQLite."""
        return self.db_type == DatabaseType.SQLITE

    def get_config(self) -> Dict[str, Any]:
        """Get configuration dictionary."""
        return self.config.copy()


class DatabaseFactory:
    """Database factory for creating appropriate database connections."""

    @staticmethod
    def create_adapter(config: DatabaseConfig = None):
        """Create appropriate database adapter."""

        if config is None:
            config = DatabaseConfig()

        if config.is_postgresql():
            try:
                from database.postgresql_adapter import get_postgresql_adapter

                return get_postgresql_adapter()
            except ImportError:
                logger.error("PostgreSQL adapter not available, falling back to SQLite")
                return DatabaseFactory._create_sqlite_adapter()
        else:
            return DatabaseFactory._create_sqlite_adapter()

    @staticmethod
    def _create_sqlite_adapter():
        """Create SQLite adapter."""

        try:
            # Import existing SQLite database interface
            import os
            import sys

            sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

            from src.database.models import CapsuleDatabase

            return CapsuleDatabase()
        except ImportError:
            logger.error("SQLite adapter not available")
            return None


# Global configuration instance
_database_config = None


def get_database_config() -> DatabaseConfig:
    """Get global database configuration."""
    global _database_config
    if _database_config is None:
        _database_config = DatabaseConfig()
    return _database_config


def get_database_adapter():
    """Get appropriate database adapter."""
    config = get_database_config()
    return DatabaseFactory.create_adapter(config)


def create_environment_template():
    """Create environment template for database configuration."""

    template = """
# Database Configuration
# ======================

# Database type: sqlite or postgresql
DATABASE_TYPE=sqlite

# SQLite Configuration (when DATABASE_TYPE=sqlite)
SQLITE_PATH=capsule_engine.db
JSONL_FALLBACK=capsule_chain.jsonl
SQLITE_TIMEOUT=30
SQLITE_JOURNAL_MODE=WAL
SQLITE_SYNCHRONOUS=NORMAL

# PostgreSQL Configuration (when DATABASE_TYPE=postgresql)
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=uatp
PG_USER=uatp
PG_PASSWORD=uatp
PG_MIN_CONNECTIONS=5
PG_MAX_CONNECTIONS=20
PG_COMMAND_TIMEOUT=30
PG_SSL_MODE=prefer

# Database URL (alternative to individual settings)
# DATABASE_URL=postgresql://uatp:uatp@localhost:5432/uatp
"""

    return template.strip()


def main():
    """Test database configuration."""

    print("️ Testing Database Configuration")
    print("=" * 40)

    # Test configuration loading
    config = get_database_config()

    print(f"\nDatabase Type: {config.db_type.value}")
    print(f"Connection String: {config.get_connection_string()}")

    print("\nConfiguration Details:")
    for key, value in config.get_config().items():
        if "password" in key.lower():
            print(f"  {key}: {'*' * len(str(value))}")
        else:
            print(f"  {key}: {value}")

    # Test adapter creation
    print("\n Testing adapter creation...")
    adapter = get_database_adapter()

    if adapter:
        print(f"[OK] Adapter created: {type(adapter).__name__}")
    else:
        print("[ERROR] Failed to create adapter")

    # Show environment template
    print("\n Environment Template:")
    print(create_environment_template())

    print("\n[OK] Database configuration test completed!")


if __name__ == "__main__":
    main()
