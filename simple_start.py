#!/usr/bin/env python3
"""
Simple UATP System Starter
"""
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path


def setup_database():
    """Initialize SQLite database."""
    print("🗄️  Setting up database...")

    # Create database directory
    os.makedirs("data", exist_ok=True)

    # Create basic SQLite database
    db_path = "data/uatp.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create basic tables
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS capsules (
            id TEXT PRIMARY KEY,
            capsule_type TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            creator_id TEXT,
            timestamp REAL NOT NULL,
            verification_status TEXT DEFAULT 'pending',
            attribution_data TEXT,
            economic_data TEXT
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attributions (
            id TEXT PRIMARY KEY,
            capsule_id TEXT,
            user_id TEXT,
            platform TEXT,
            model TEXT,
            confidence_score REAL,
            timestamp REAL NOT NULL,
            FOREIGN KEY (capsule_id) REFERENCES capsules (id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rewards (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            attribution_id TEXT,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            status TEXT DEFAULT 'pending',
            timestamp REAL NOT NULL,
            FOREIGN KEY (attribution_id) REFERENCES attributions (id)
        )
    """
    )

    conn.commit()
    conn.close()

    print("✅ Database initialized")
    return True


def create_env_file():
    """Create environment file with default values."""
    print("⚙️  Creating environment configuration...")

    env_content = """
# UATP Configuration
UATP_API_PORT=8000
UATP_DEBUG=true
UATP_DATABASE_URL=sqlite:///data/uatp.db
ENVIRONMENT=development

# Security (development only)
JWT_SECRET_KEY=uatp_development_jwt_secret_change_in_production
CSRF_SECRET_KEY=uatp_development_csrf_secret_change_in_production
"""

    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content.strip())
        print("✅ Environment file created")
    else:
        print("✅ Environment file exists")

    return True


def start_backend():
    """Start the UATP backend server."""
    print("🚀 Starting UATP backend server...")

    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    env["ENVIRONMENT"] = "development"

    # Start backend
    backend_cmd = [
        sys.executable,
        "-m",
        "quart",
        "--app",
        "src.api.server:app",
        "run",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--debug",
    ]

    print(f"Running: {' '.join(backend_cmd)}")

    backend_process = subprocess.Popen(backend_cmd, env=env)

    return backend_process


def start_frontend():
    """Start the frontend development server."""
    print("🌐 Starting frontend development server...")

    # Create frontend env file
    frontend_env = """
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_UATP_API_KEY=development_key
"""

    frontend_env_path = Path("frontend/.env.local")
    if not frontend_env_path.exists():
        with open(frontend_env_path, "w") as f:
            f.write(frontend_env.strip())

    # Start frontend
    frontend_process = subprocess.Popen(["npm", "run", "dev"], cwd="frontend")

    return frontend_process


def main():
    """Main function."""
    print("🚀 UATP Simple System Launcher")
    print("===============================")

    # Setup steps
    setup_database()
    create_env_file()

    # Start services
    print("\n🚀 Starting services...")

    backend_process = start_backend()
    print("✅ Backend server starting on http://localhost:8000")

    time.sleep(2)

    frontend_process = start_frontend()
    print("✅ Frontend server starting on http://localhost:3000")

    print(
        """
🎉 UATP SYSTEM STARTING!

Access Points:
🌐 Frontend: http://localhost:3000
📡 Backend API: http://localhost:8000

Press Ctrl+C to stop all services.
"""
    )

    # Keep running
    try:
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Services stopped")


if __name__ == "__main__":
    main()
