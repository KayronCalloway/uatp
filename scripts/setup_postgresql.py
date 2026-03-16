#!/usr/bin/env python3
"""
PostgreSQL Setup Script
=======================

This script helps set up PostgreSQL for the UATP system.
"""

import asyncio
import os
import subprocess
import sys
import time

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def check_docker():
    """Check if Docker is available."""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_postgresql_running():
    """Check if PostgreSQL is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=uatp_postgresql"],
            capture_output=True,
            text=True,
        )
        return "uatp_postgresql" in result.stdout
    except Exception:
        return False


def start_postgresql():
    """Start PostgreSQL using Docker Compose."""

    print(" Starting PostgreSQL with Docker Compose...")

    try:
        # Check if docker-compose.postgresql.yml exists
        if not os.path.exists("docker-compose.postgresql.yml"):
            print("[ERROR] docker-compose.postgresql.yml not found")
            return False

        # Start services
        result = subprocess.run(
            [
                "docker-compose",
                "-f",
                "docker-compose.postgresql.yml",
                "up",
                "-d",
                "postgresql",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"[ERROR] Failed to start PostgreSQL: {result.stderr}")
            return False

        # Wait for PostgreSQL to be ready
        print("⏳ Waiting for PostgreSQL to be ready...")
        max_attempts = 30
        for attempt in range(max_attempts):
            if check_postgresql_running():
                # Test connection
                test_result = subprocess.run(
                    [
                        "docker",
                        "exec",
                        "uatp_postgresql",
                        "pg_isready",
                        "-U",
                        "uatp",
                        "-d",
                        "uatp",
                    ],
                    capture_output=True,
                    text=True,
                )

                if test_result.returncode == 0:
                    print("[OK] PostgreSQL is ready!")
                    return True

            time.sleep(2)

        print("[ERROR] PostgreSQL failed to start within timeout")
        return False

    except Exception as e:
        print(f"[ERROR] Error starting PostgreSQL: {e}")
        return False


def stop_postgresql():
    """Stop PostgreSQL Docker containers."""

    print(" Stopping PostgreSQL...")

    try:
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.postgresql.yml", "down"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("[OK] PostgreSQL stopped")
            return True
        else:
            print(f"[ERROR] Failed to stop PostgreSQL: {result.stderr}")
            return False

    except Exception as e:
        print(f"[ERROR] Error stopping PostgreSQL: {e}")
        return False


def show_connection_info():
    """Show PostgreSQL connection information."""

    print("\n PostgreSQL Connection Information")
    print("=" * 40)
    print("Host: localhost")
    print("Port: 5432")
    print("Database: uatp")
    print("Username: uatp")
    print("Password: uatp")
    print("\nConnection String:")
    print("postgresql://uatp:uatp@localhost:5432/uatp")
    print("\nPgAdmin URL: http://localhost:8080")
    print("PgAdmin Email: admin@uatp.com")
    print("PgAdmin Password: admin")


def create_env_file():
    """Create .env file with PostgreSQL configuration."""

    env_content = """# Database Configuration
DATABASE_TYPE=postgresql
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=uatp
PG_USER=uatp
PG_PASSWORD=uatp
PG_MIN_CONNECTIONS=5
PG_MAX_CONNECTIONS=20
PG_COMMAND_TIMEOUT=30
PG_SSL_MODE=prefer

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_DAYS=7

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
"""

    env_file = ".env.postgresql"

    with open(env_file, "w") as f:
        f.write(env_content)

    print(f"[OK] Created {env_file}")
    print(" Copy this to .env to use PostgreSQL configuration")


async def setup_database_schema():
    """Set up database schema."""

    print("\n Setting up database schema...")

    try:
        # Import and run schema setup
        from src.database.postgresql_schema import get_postgresql_manager

        pg_manager = get_postgresql_manager()

        # Create connection pool
        await pg_manager.create_connection_pool()

        # Create schema
        await pg_manager.create_schema()

        # Create indexes
        await pg_manager.create_indexes()

        # Create functions
        await pg_manager.create_functions()

        print("[OK] Database schema created successfully")

        # Close connection
        await pg_manager.close_connection_pool()

        return True

    except Exception as e:
        print(f"[ERROR] Failed to set up database schema: {e}")
        return False


def main():
    """Main setup function."""

    print(" PostgreSQL Setup for UATP")
    print("=" * 40)

    # Check Docker
    if not check_docker():
        print("[ERROR] Docker not found. Please install Docker first.")
        return

    print("[OK] Docker is available")

    # Check current status
    if check_postgresql_running():
        print("[OK] PostgreSQL is already running")
    else:
        # Start PostgreSQL
        if not start_postgresql():
            print("[ERROR] Failed to start PostgreSQL")
            return

    # Show connection info
    show_connection_info()

    # Create environment file
    create_env_file()

    # Set up database schema
    print("\n Setting up database schema...")
    try:
        asyncio.run(setup_database_schema())
    except Exception as e:
        print(f"[ERROR] Schema setup failed: {e}")
        print("You can run this manually later with:")
        print("python3 src/database/postgresql_schema.py")

    print("\n[OK] PostgreSQL setup completed!")
    print("\nNext steps:")
    print("1. Copy .env.postgresql to .env")
    print("2. Run the migration script: python3 scripts/migrate_to_postgresql.py")
    print("3. Test the system with PostgreSQL")


if __name__ == "__main__":
    main()
