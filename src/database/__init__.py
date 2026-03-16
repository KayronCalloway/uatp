"""
Database Package
================

Production-grade database layer for the UATP Capsule Engine with PostgreSQL
support, connection pooling, migrations, and comprehensive data persistence.
"""

from .connection import DatabaseManager, get_database_manager
from .migrations import MigrationManager, run_migrations
from .models import Attribution, Base

__all__ = [
    # Core database management
    "DatabaseManager",
    "get_database_manager",
    # Migrations
    "MigrationManager",
    "run_migrations",
    # Models and repositories will be exported from their respective modules
]
