#!/usr/bin/env python3
"""
Start the Quart server with the correct imports
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, "/Users/kay/uatp-capsule-engine")

from src.api.server import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=8002, debug=True)
