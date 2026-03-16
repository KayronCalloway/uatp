#!/usr/bin/env python3
"""
Production Database Setup Script
Sets up PostgreSQL database for UATP production deployment
"""

import argparse
import asyncio
import os
import sys

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def setup_production_database(
    admin_user: str = "postgres",
    admin_password: str = None,
    db_host: str = "localhost",
    db_port: int = 5432,
    db_name: str = "uatp_production",
    db_user: str = "uatp_user",
    db_password: str = None,
    create_user: bool = True,
    create_database: bool = True,
):
    """Setup PostgreSQL database for production."""

    print(" Setting up UATP Production Database...")
    print("=" * 60)

    if not admin_password:
        admin_password = input(
            f"Enter password for PostgreSQL admin user '{admin_user}': "
        )

    if not db_password:
        db_password = input(f"Enter password for UATP database user '{db_user}': ")

    try:
        # Connect to PostgreSQL as admin
        print(f" Connecting to PostgreSQL as {admin_user}...")
        admin_conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=admin_user,
            password=admin_password,
            database="postgres",
        )
        admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = admin_conn.cursor()

        # Create database user if needed
        if create_user:
            print(f" Creating database user '{db_user}'...")
            try:
                cursor.execute(
                    f"CREATE USER {db_user} WITH PASSWORD %s;", (db_password,)
                )
                print(f"[OK] User '{db_user}' created successfully")
            except psycopg2.Error as e:
                if "already exists" in str(e):
                    print(f"ℹ️ User '{db_user}' already exists")
                    # Update password
                    cursor.execute(
                        f"ALTER USER {db_user} WITH PASSWORD %s;", (db_password,)
                    )
                    print(f"[OK] Password updated for user '{db_user}'")
                else:
                    raise

        # Create database if needed
        if create_database:
            print(f"️ Creating database '{db_name}'...")
            try:
                cursor.execute(f"CREATE DATABASE {db_name} OWNER {db_user};")
                print(f"[OK] Database '{db_name}' created successfully")
            except psycopg2.Error as e:
                if "already exists" in str(e):
                    print(f"ℹ️ Database '{db_name}' already exists")
                else:
                    raise

        # Grant permissions
        print(f" Granting permissions to user '{db_user}'...")
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};")
        print("[OK] Permissions granted")

        # Close admin connection
        cursor.close()
        admin_conn.close()

        # Test connection with new user
        print(f" Testing connection as '{db_user}'...")
        test_conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
        )
        test_conn.close()
        print("[OK] Connection test successful")

        # Create SQLAlchemy engine and run migrations
        print(" Running database migrations...")
        database_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

        engine = create_async_engine(database_url, echo=False)

        # Import and run migrations
        from src.core.database import db

        # Mock app to initialize database
        class MockApp:
            def __init__(self):
                self.logger = None

        mock_app = MockApp()

        # Set database URL for production
        os.environ["DATABASE_URL"] = database_url

        # Initialize database with production settings
        db.init_app(mock_app)
        await db.create_all()

        print("[OK] Database migrations completed")

        # Create database extensions if needed
        print(" Setting up database extensions...")
        async with engine.begin() as conn:
            # Enable UUID extension
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            # Enable cryptographic extensions
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))
            print("[OK] Database extensions configured")

        await engine.dispose()

        print("\n" + "=" * 60)
        print(" Production Database Setup Complete!")
        print("=" * 60)
        print(f" Database: {db_name}")
        print(f" User: {db_user}")
        print(f" Host: {db_host}:{db_port}")
        print(
            f" Connection URL: postgresql+asyncpg://{db_user}:***@{db_host}:{db_port}/{db_name}"
        )
        print("\n Next Steps:")
        print(
            "1. Update your .env.production file with the database connection details"
        )
        print("2. Ensure PostgreSQL is configured for SSL in production")
        print("3. Set up automated backups")
        print("4. Configure connection pooling")

        return True

    except Exception as e:
        print(f"[ERROR] Database setup failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Setup UATP Production Database")
    parser.add_argument(
        "--admin-user", default="postgres", help="PostgreSQL admin user"
    )
    parser.add_argument("--admin-password", help="PostgreSQL admin password")
    parser.add_argument("--db-host", default="localhost", help="Database host")
    parser.add_argument("--db-port", type=int, default=5432, help="Database port")
    parser.add_argument("--db-name", default="uatp_production", help="Database name")
    parser.add_argument("--db-user", default="uatp_user", help="UATP database user")
    parser.add_argument("--db-password", help="UATP database user password")
    parser.add_argument("--skip-user", action="store_true", help="Skip user creation")
    parser.add_argument(
        "--skip-database", action="store_true", help="Skip database creation"
    )

    args = parser.parse_args()

    success = asyncio.run(
        setup_production_database(
            admin_user=args.admin_user,
            admin_password=args.admin_password,
            db_host=args.db_host,
            db_port=args.db_port,
            db_name=args.db_name,
            db_user=args.db_user,
            db_password=args.db_password,
            create_user=not args.skip_user,
            create_database=not args.skip_database,
        )
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
