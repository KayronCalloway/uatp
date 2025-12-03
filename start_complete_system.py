#!/usr/bin/env python3
"""
Complete UATP System Launcher

This script starts the complete UATP system including:
- Backend API server
- Frontend Next.js application  
- Database initialization
- All integrated services
"""

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path


def print_banner():
    print(
        """
🚀 UATP COMPLETE SYSTEM LAUNCHER
================================

Starting civilization-grade AI attribution infrastructure:
- Attribution tracking across all AI platforms
- Economic reward distribution system
- Democratic governance infrastructure
- Zero-knowledge privacy proofs
- 2025 breakthrough watermarking
- Global federation coordination

"""
    )


def check_prerequisites():
    """Check if required dependencies are available."""
    print("🔍 Checking prerequisites...")

    # Check Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version}")

    # Check Node.js
    try:
        node_version = subprocess.check_output(["node", "--version"], text=True).strip()
        print(f"✅ Node.js {node_version}")
    except:
        print("❌ Node.js not found")
        return False

    return True


def install_python_dependencies():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
        )
        print("✅ Python dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python dependencies: {e}")
        return False
    return True


def install_frontend_dependencies():
    """Install frontend dependencies."""
    print("📦 Installing frontend dependencies...")
    try:
        subprocess.run(
            ["npm", "install"], cwd="frontend", check=True, capture_output=True
        )
        print("✅ Frontend dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install frontend dependencies: {e}")
        return False
    return True


def setup_database():
    """Initialize SQLite database."""
    print("🗄️  Setting up database...")

    # Create database directory
    os.makedirs("data", exist_ok=True)

    # Create basic SQLite database
    import sqlite3

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

# API Keys (add your keys here)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
HUGGINGFACE_API_KEY=your_huggingface_key_here

# Security (generate secure keys for production)
JWT_SECRET_KEY=uatp_development_jwt_secret_change_in_production
CSRF_SECRET_KEY=uatp_development_csrf_secret_change_in_production

# External Services (optional)
STRIPE_API_KEY=
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=

# Federation (optional)
FEDERATION_NODE_ID=local_dev_node
FEDERATION_REGION=development
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

    # Start backend in background
    backend_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--reload",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait a moment for startup
    time.sleep(3)

    if backend_process.poll() is None:
        print("✅ Backend server started on http://localhost:8000")
        return backend_process
    else:
        stdout, stderr = backend_process.communicate()
        print(f"❌ Backend failed to start:")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return None


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

    # Start frontend in background
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd="frontend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait a moment for startup
    time.sleep(5)

    if frontend_process.poll() is None:
        print("✅ Frontend server started on http://localhost:3000")
        return frontend_process
    else:
        stdout, stderr = frontend_process.communicate()
        print(f"❌ Frontend failed to start:")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return None


def print_success_message():
    """Print success message with access information."""
    print(
        """
🎉 UATP COMPLETE SYSTEM IS NOW RUNNING!

Access Points:
--------------
🌐 Frontend Application: http://localhost:3000
📡 Backend API: http://localhost:8000
📚 API Documentation: http://localhost:8000/docs

Quick Start:
-----------
1. Open http://localhost:3000 in your browser
2. Complete the onboarding wizard
3. Start tracking AI interactions for attribution
4. Explore the comprehensive dashboard system

Features Available:
------------------
✅ Real-time AI attribution tracking
✅ Economic reward distribution
✅ Democratic governance participation  
✅ Zero-knowledge privacy proofs
✅ Advanced watermarking (2025 tech)
✅ Global federation coordination
✅ Comprehensive analytics dashboard

Development:
-----------
- Frontend: Next.js with TypeScript and Tailwind CSS
- Backend: FastAPI/Quart with async Python
- Database: SQLite (upgradeable to PostgreSQL)
- Authentication: JWT-based with secure defaults

Ready to build the future of AI attribution! 🚀

Press Ctrl+C to stop all services.
"""
    )


def main():
    """Main launcher function."""
    print_banner()

    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites not met. Please install required dependencies.")
        return 1

    # Setup steps
    steps = [
        ("Installing Python dependencies", install_python_dependencies),
        ("Installing frontend dependencies", install_frontend_dependencies),
        ("Setting up database", setup_database),
        ("Creating environment configuration", create_env_file),
    ]

    for description, func in steps:
        print(f"⚡ {description}...")
        if not func():
            print(f"❌ Failed: {description}")
            return 1

    # Start services
    print("\n🚀 Starting UATP services...\n")

    backend_process = start_backend()
    if not backend_process:
        return 1

    frontend_process = start_frontend()
    if not frontend_process:
        if backend_process:
            backend_process.terminate()
        return 1

    # Print success message
    print_success_message()

    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)

            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process stopped unexpectedly")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend process stopped unexpectedly")
                break

    except KeyboardInterrupt:
        print("\n🛑 Shutting down UATP system...")

        # Terminate processes gracefully
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()

        print("✅ All services stopped. Thank you for using UATP!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
