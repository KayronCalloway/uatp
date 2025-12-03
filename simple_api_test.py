#!/usr/bin/env python3
"""
Simple API server to test capsule access.
"""

import json
import sqlite3
import sys
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


class CapsuleAPIHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for capsule API."""

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        logger.info(f"GET request: {path}")

        # Handle CORS
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "http://localhost:3000")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        if path == "/health":
            response = {"status": "healthy", "version": "1.0.0"}
            self.wfile.write(json.dumps(response).encode())
            return

        # Handle live monitor/capture endpoints
        if path == "/api/v1/live/monitor/status":
            response = {"monitoring": False, "status": "inactive"}
            self.wfile.write(json.dumps(response).encode())
            return

        if path == "/api/v1/live/capture/conversations":
            response = {"conversations": []}
            self.wfile.write(json.dumps(response).encode())
            return

        if path.startswith("/capsules/"):
            capsule_id = path.split("/")[-1]

            if path.endswith("/verify"):
                # Handle verification endpoint
                capsule_id = path.split("/")[-2]
                response = self.verify_capsule(capsule_id)
            else:
                # Handle capsule detail endpoint
                response = self.get_capsule(capsule_id)

            self.wfile.write(json.dumps(response).encode())
            return

        if path == "/capsules":
            # Handle capsules list endpoint
            response = self.list_capsules()
            self.wfile.write(json.dumps(response).encode())
            return

        # 404 for unknown paths
        self.send_response(404)
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "http://localhost:3000")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
        self.end_headers()

    def get_capsule(self, capsule_id):
        """Get capsule from database."""
        try:
            conn = sqlite3.connect("uatp_dev.db")
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT capsule_id, capsule_type, version, timestamp, status, verification, payload 
                FROM capsules WHERE capsule_id = ?
            """,
                (capsule_id,),
            )

            row = cursor.fetchone()
            conn.close()

            if not row:
                return {"error": "Capsule not found"}

            # Parse the payload
            payload = json.loads(row[6]) if row[6] else {}

            # Build capsule response
            capsule = {
                "capsule_id": row[0],
                "type": row[1] or "reasoning_trace",
                "capsule_type": row[1] or "reasoning_trace",
                "version": row[2],
                "timestamp": row[3],
                "status": row[4],
                "verification": json.loads(row[5]) if row[5] else {},
                "agent_id": payload.get("verification", {}).get("signer", "unknown"),
                "reasoning_trace": payload.get("reasoning_trace", {}),
                "content": payload.get("content", ""),
                "metadata": payload.get("metadata", {}),
            }

            return {"capsule": capsule, "raw_data": None}

        except Exception as e:
            logger.error(f"Error getting capsule {capsule_id}: {e}")
            return {"error": f"Database error: {e}"}

    def verify_capsule(self, capsule_id):
        """Verify capsule."""
        try:
            conn = sqlite3.connect("uatp_dev.db")
            cursor = conn.cursor()

            cursor.execute(
                "SELECT verification FROM capsules WHERE capsule_id = ?", (capsule_id,)
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                return {
                    "capsule_id": capsule_id,
                    "verified": False,
                    "error": "Capsule not found",
                    "verification_error": "Capsule does not exist",
                    "from_cache": False,
                    "metadata_has_verify_key": None,
                }

            # For our test, assume verified if it has verification data
            verification = json.loads(row[0]) if row[0] else {}
            has_signature = bool(verification.get("signature"))

            return {
                "capsule_id": capsule_id,
                "verified": has_signature,
                "error": None,
                "verification_error": None if has_signature else "No signature found",
                "from_cache": False,
                "metadata_has_verify_key": bool(verification.get("verify_key")),
            }

        except Exception as e:
            logger.error(f"Error verifying capsule {capsule_id}: {e}")
            return {
                "capsule_id": capsule_id,
                "verified": False,
                "error": f"Verification error: {e}",
                "verification_error": str(e),
                "from_cache": False,
                "metadata_has_verify_key": None,
            }

    def list_capsules(self):
        """List all capsules."""
        try:
            conn = sqlite3.connect("uatp_dev.db")
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT capsule_id, capsule_type, timestamp, status, payload
                FROM capsules ORDER BY timestamp DESC LIMIT 100
            """
            )

            rows = cursor.fetchall()
            conn.close()

            capsules = []
            for row in rows:
                payload = json.loads(row[4]) if row[4] else {}
                verification = payload.get("verification", {})

                capsule = {
                    "capsule_id": row[0],
                    "id": row[0],  # Frontend compatibility
                    "type": row[1],
                    "timestamp": row[2],
                    "status": row[3],
                    "agent_id": verification.get("signer", "unknown"),
                    "content": payload.get("content", "")[:100] + "..."
                    if payload.get("content", "")
                    else "",
                }
                capsules.append(capsule)

            return {"capsules": capsules}

        except Exception as e:
            logger.error(f"Error listing capsules: {e}")
            return {"capsules": [], "error": str(e)}

    def log_message(self, format, *args):
        """Override log message to reduce noise."""
        return


def run_server(port=9090):
    """Run the simple API server."""
    server_address = ("", port)
    httpd = HTTPServer(server_address, CapsuleAPIHandler)
    logger.info(f"Starting simple API server on port {port}")
    logger.info(f"Test with: curl http://localhost:{port}/health")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")
        httpd.shutdown()


if __name__ == "__main__":
    run_server()
