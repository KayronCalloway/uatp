#!/usr/bin/env python3
"""
UATP Application Entry Point
Runs the FastAPI application using uvicorn
"""

import os

import uvicorn


def main():
    """Main entry point for running the UATP application"""
    # Get configuration from environment
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    reload = os.getenv("ENVIRONMENT") == "development"
    log_level = os.getenv("LOG_LEVEL", "info")

    # Run the application using canonical ASGI pattern for proper reload support
    uvicorn.run(
        "src.main:app",  # Import string enables reload and workers
        host=host,
        port=port,
        log_level=log_level,
        access_log=True,
        reload=reload,
        reload_dirs=["src"] if reload else None,
        # Production optimizations
        loop="uvloop" if not reload else "asyncio",
        http="httptools" if not reload else "h11",
    )


if __name__ == "__main__":
    main()
