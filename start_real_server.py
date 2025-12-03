#!/usr/bin/env python3
"""
Start the full UATP backend server
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    """Main startup routine"""
    print("=== UATP Capsule Engine Full System Startup ===")

    # Set environment variables
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("UATP_API_KEY", "dev-key-12345")
    os.environ.setdefault("UATP_SECRET_KEY", "dev-secret-key-67890")

    try:
        from src.api.server import create_app

        print("Creating UATP application...")
        app = create_app()

        print("Starting UATP server on port 9090...")
        print("Server is running! Frontend can connect at http://localhost:9090")
        print("Press Ctrl+C to stop the server")

        app.run(host="0.0.0.0", port=9090, debug=True)

    except Exception as e:
        print(f"Server startup failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
