#!/usr/bin/env python3
"""
Production UATP Server with Uvicorn ASGI Server
Replaces the development server for better stability and performance
"""
import os
import sys
import signal
import asyncio
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    sys.exit(0)


def main():
    """Main production server startup"""
    print("=== UATP Capsule Engine Production Server ===")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Set development environment variables (production-grade server, dev database)
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("UATP_API_KEY", "dev-key-12345")
    os.environ.setdefault("UATP_SECRET_KEY", "dev-secret-key-67890")

    # Server configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 9090))
    workers = int(os.getenv("WORKERS", 1))  # Start with 1 worker for development
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    try:
        # Import uvicorn for ASGI server
        try:
            import uvicorn
        except ImportError:
            print("❌ Uvicorn not found. Installing...")
            os.system("pip install uvicorn[standard]")
            import uvicorn

        from src.api.server import create_app

        print("Creating UATP application...")
        app = create_app()

        print(f"🚀 Starting production UATP server:")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   Workers: {workers}")
        print(f"   Log Level: {log_level}")
        print(f"   Environment: {os.getenv('ENVIRONMENT')}")
        print("")
        print("✅ Frontend can connect at http://localhost:9090")
        print("✅ API docs available at http://localhost:9090/docs")
        print("✅ Health check at http://localhost:9090/health")
        print("")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)

        # Configure uvicorn with production settings
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            workers=workers,
            log_level=log_level,
            access_log=True,
            use_colors=True,
            reload=False,  # Disable auto-reload in production
            reload_dirs=None,
            # Performance optimizations
            loop="auto",  # Use the fastest event loop available
            http="auto",  # Use the fastest HTTP implementation
            ws="auto",  # Use the fastest WebSocket implementation
            # Graceful shutdown
            timeout_keep_alive=30,
            timeout_graceful_shutdown=30,
        )

        server = uvicorn.Server(config)

        # Run the server
        if sys.version_info >= (3, 7):
            asyncio.run(server.serve())
        else:
            # Python 3.6 compatibility
            loop = asyncio.get_event_loop()
            loop.run_until_complete(server.serve())

    except KeyboardInterrupt:
        print("\n🛑 Server shutdown by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def start_with_gunicorn():
    """Alternative startup using Gunicorn (for Linux/Unix systems)"""
    print("=== Starting UATP with Gunicorn ===")

    try:
        import gunicorn
    except ImportError:
        print("❌ Gunicorn not found. Installing...")
        os.system("pip install gunicorn")

    # Gunicorn command
    cmd = [
        "gunicorn",
        "--bind",
        "0.0.0.0:9090",
        "--workers",
        "2",
        "--worker-class",
        "uvicorn.workers.UvicornWorker",
        "--access-logfile",
        "-",
        "--error-logfile",
        "-",
        "--log-level",
        "info",
        "--timeout",
        "120",
        "--keep-alive",
        "30",
        "--max-requests",
        "1000",
        "--max-requests-jitter",
        "100",
        "src.api.server:create_app()",
    ]

    print(f"Running: {' '.join(cmd)}")
    os.execvp("gunicorn", cmd)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="UATP Production Server")
    parser.add_argument(
        "--server",
        choices=["uvicorn", "gunicorn"],
        default="uvicorn",
        help="ASGI server to use (default: uvicorn)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9090, help="Port to listen on")
    parser.add_argument(
        "--workers", type=int, default=1, help="Number of worker processes"
    )

    args = parser.parse_args()

    # Set environment variables from args
    os.environ["HOST"] = args.host
    os.environ["PORT"] = str(args.port)
    os.environ["WORKERS"] = str(args.workers)

    if (
        args.server == "gunicorn" and os.name != "nt"
    ):  # Gunicorn doesn't work on Windows
        start_with_gunicorn()
    else:
        main()
