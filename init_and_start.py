#!/usr/bin/env python3
"""
Initialize database and start the full UATP backend server
"""
import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def initialize_database():
    """Initialize the database with all required tables"""
    try:
        from src.core.database import db
        from src.core.config import DATABASE_URL

        print(f"Initializing database: {DATABASE_URL}")

        # Create a dummy app to initialize the database
        class DummyApp:
            def __init__(self):
                self.config = {
                    "VERSION": "1.0.0",
                    "ENVIRONMENT": "development",
                    "CACHE_ENABLED": False,
                    "TESTING": False,
                    "PYTHON_VERSION": "3.11",
                }

        app = DummyApp()
        db.init_app(app)

        # Create all tables
        await db.create_all()

        print("Database initialized successfully!")
        return True

    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False


def start_server():
    """Start the full UATP backend server"""
    try:
        from src.api.server import create_app

        print("Creating UATP application...")
        app = create_app()

        print("Starting UATP server on port 9090...")
        app.run(host="0.0.0.0", port=9090, debug=True)

    except Exception as e:
        print(f"Server startup failed: {e}")
        sys.exit(1)


async def main():
    """Main initialization and startup routine"""
    print("=== UATP Capsule Engine Full System Startup ===")

    # Set environment variables
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("UATP_API_KEY", "dev-key-12345")
    os.environ.setdefault("UATP_SECRET_KEY", "dev-secret-key-67890")

    # Initialize database
    print("Step 1: Initializing database...")
    db_success = await initialize_database()

    if not db_success:
        print("Database initialization failed. Exiting.")
        sys.exit(1)

    # Start server
    print("Step 2: Starting server...")
    start_server()


if __name__ == "__main__":
    asyncio.run(main())
