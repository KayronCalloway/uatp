#!/usr/bin/env python
"""
UATP Capsule Engine Enhanced API Test Script

This script demonstrates the enhanced security features of the UATP Capsule Engine API:
1. Authentication with API keys
2. Rate limiting for API endpoints
3. Capsule compression for storage efficiency
4. Chain sealing for legal admissibility

Usage:
    python test_enhanced_api.py [--host HOST] [--port PORT] [--api-key KEY]

Requirements:
    - requests
    - tabulate
    - python-dotenv
"""

import argparse
import base64
import json
import os
import signal
import subprocess
import sys
import time
import uuid
import zlib
from typing import Dict, Optional

import requests
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
load_dotenv()


class UATAPITester:
    """Test client for UATP Capsule Engine Enhanced API"""

    def __init__(self, host: str, port: int, api_key: Optional[str] = None):
        """Initialize the API tester"""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.api_key = api_key
        self.session = requests.Session()
        self.server_process = None

        if api_key:
            self.session.headers.update({"X-API-Key": api_key})

    def decompress_data(self, compressed_data: str) -> Dict:
        """Decompress base64+zlib compressed data"""
        try:
            binary_data = base64.b64decode(compressed_data)
            decompressed_data = zlib.decompress(binary_data)
            return json.loads(decompressed_data.decode("utf-8"))
        except Exception as e:
            print(f"Error decompressing data: {e}")
            return {"error": "Decompression failed"}

    def test_authentication(self):
        """Test authentication with and without API key"""
        print("\n[Testing Authentication]")

        # Test with API key
        headers = {"X-API-Key": self.api_key} if self.api_key else {}
        response = requests.get(f"{self.base_url}/capsules", headers=headers)

        if response.status_code == 200:
            print("[OK] Authentication successful with API key")
        else:
            print(f"[ERROR] Authentication failed with API key: {response.status_code}")
            print(f"Response: {response.text}")

        # Test without API key (should fail if auth is enabled)
        if self.api_key:
            response_no_key = requests.get(f"{self.base_url}/capsules")
            if response_no_key.status_code == 401:
                print("[OK] Authentication correctly rejected request without API key")
            else:
                print(
                    f"[WARN] Request without API key returned status {response_no_key.status_code}"
                )

    def test_rate_limiting(self):
        """Test rate limiting by making multiple rapid requests"""
        print("\n[Testing Rate Limiting]")

        endpoint = f"{self.base_url}/capsules"
        request_count = 10
        results = []

        print(f"Making {request_count} rapid requests to test rate limiting...")

        for i in range(request_count):
            start_time = time.time()
            response = self.session.get(endpoint)
            elapsed = time.time() - start_time

            results.append(
                {
                    "request": i + 1,
                    "status": response.status_code,
                    "time": f"{elapsed:.3f}s",
                    "limited": response.status_code == 429,
                }
            )

            # Don't sleep, to intentionally trigger rate limiting

        # Display results
        table_data = [
            [r["request"], r["status"], r["time"], "Yes" if r["limited"] else "No"]
            for r in results
        ]
        print(
            tabulate(table_data, headers=["Request", "Status", "Time", "Rate Limited"])
        )

        limited_count = sum(1 for r in results if r["limited"])
        if limited_count > 0:
            print(
                f"[OK] Rate limiting working: {limited_count} of {request_count} requests were limited"
            )
        else:
            print("[WARN] No rate limiting detected, all requests succeeded")

    def test_compression(self):
        """Test compression of the full capsule list."""
        print("\n[Testing Capsule Compression]")

        # Get uncompressed list size
        response_normal = self.session.get(f"{self.base_url}/capsules?compress=false")
        if response_normal.status_code != 200:
            print(
                f"[ERROR] Failed to get normal capsule list: {response_normal.status_code}"
            )
            return
        normal_size = len(response_normal.content)

        # Get compressed list size
        response_compressed = self.session.get(
            f"{self.base_url}/capsules?compress=true"
        )
        if response_compressed.status_code != 200:
            print(
                f"[ERROR] Failed to get compressed capsule list: {response_compressed.status_code}"
            )
            return

        compressed_response_size = len(response_compressed.content)
        compressed_data = response_compressed.json()

        if compressed_data.get("compressed") and "data" in compressed_data:
            print("[OK] Received correctly formatted compressed response.")
            # To verify, we decompress and check the data, but for size comparison,
            # we use the raw response sizes.
            try:
                decompressed_data = self.decompress_data(compressed_data["data"])
                print(
                    f"[OK] Decompressed data successfully. (contains {len(decompressed_data)} capsules)"
                )
            except Exception as e:
                print(f"[ERROR] Failed to decompress data: {e}")

        if compressed_response_size < normal_size:
            ratio = (1 - compressed_response_size / normal_size) * 100
            print(f"[OK] Compression successful! Ratio: {ratio:.1f}%")
        else:
            ratio = (
                (compressed_response_size / normal_size - 1) * 100
                if normal_size > 0
                else 0
            )
            print(f"Normal response size: {normal_size} bytes")
            print(f"Compressed response size: {compressed_response_size} bytes")
            print(f"Compression ratio: {ratio:.1f}%")
            print("[WARN] Compression was not effective.")

    def test_chain_sealing(self):
        """Test chain sealing functionality"""
        print("\n[Testing Chain Sealing]")

        # List existing seals
        response = self.session.get(f"{self.base_url}/chain/seals")

        if response.status_code != 200:
            print(f"[ERROR] Failed to list chain seals: {response.status_code}")
            print(f"Response: {response.text}")
            return

        existing_seals = response.json()
        print(f"Found {existing_seals.get('count', 0)} existing chain seals")

        # Create a new seal
        chain_id = f"test-chain-{uuid.uuid4().hex[:8]}"
        seal_data = {
            "chain_id": chain_id,
            "signer_id": "test-signer",
            "note": "Test seal for API verification",
        }

        response = self.session.post(f"{self.base_url}/chain/seal", json=seal_data)

        if response.status_code != 200:
            print(f"[ERROR] Failed to create chain seal: {response.status_code}")
            print(f"Response: {response.text}")
            return

        new_seal = response.json().get("seal", {})
        print(f"[OK] Created new chain seal: {new_seal.get('seal_id')}")

        # Verify the seal
        verify_key = new_seal.get("verify_key")
        if not verify_key:
            print("[ERROR] No verify key in seal response")
            return

        response = self.session.get(
            f"{self.base_url}/chain/verify-seal/{chain_id}",
            params={"verify_key": verify_key},
        )

        if response.status_code != 200:
            print(f"[ERROR] Failed to verify chain seal: {response.status_code}")
            print(f"Response: {response.text}")
            return

        verify_result = response.json()
        if verify_result.get("verified"):
            print("[OK] Chain seal verified successfully")
        else:
            print(
                f"[ERROR] Chain seal verification failed: {verify_result.get('error')}"
            )

    def test_capsule_stats(self):
        """Test capsule statistics endpoint"""
        print("\n[Testing Capsule Statistics]")

        response = self.session.get(f"{self.base_url}/capsules/stats")

        if response.status_code != 200:
            print(f"[ERROR] Failed to get capsule statistics: {response.status_code}")
            print(f"Response: {response.text}")
            return

        stats = response.json()
        print("Capsule Statistics:")
        print(f"Total capsules: {stats.get('total_capsules', 0)}")
        print(f"Types distribution: {json.dumps(stats.get('types', {}), indent=2)}")
        print(f"Unique agents: {stats.get('unique_agents', 0)}")
        print(
            f"Chain duration: {stats.get('chain_duration_seconds', 0) / 86400:.1f} days"
        )

    def start_server(self):
        """Start the Flask API server in a background process."""
        print(f"\nAttempting to start server on {self.host}:{self.port}...")
        env = os.environ.copy()
        env["UATP_API_PORT"] = str(self.port)
        command = [sys.executable, "-m", "api.server"]
        self.server_process = subprocess.Popen(command, env=env, preexec_fn=os.setsid)
        time.sleep(3)  # Give the server time to start

        # Check if server is running
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print(f"[OK] Server is running on {self.base_url}")
            else:
                raise ConnectionError(f"Server responded with {response.status_code}")
        except requests.ConnectionError as e:
            print("[ERROR] Server failed to start.")
            self.stop_server()
            raise e

    def stop_server(self):
        """Stop the background server process."""
        if self.server_process:
            print("\nShutting down server...")
            os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
            self.server_process.wait()
            print("[OK] Server shut down.")

    def run_all_tests(self):
        """Run all test cases, managing the server lifecycle."""
        try:
            self.start_server()
            print("\n===== UATP Capsule Engine Enhanced API Tests =====")
            print(f"Server: {self.base_url}")
            print(f"API Key: {'Configured' if self.api_key else 'Not configured'}")
            print("=" * 50)

            self.test_authentication()
            self.test_compression()
            self.test_chain_sealing()
            self.test_capsule_stats()
            self.test_rate_limiting()

            print("\n===== All Tests Completed =====")
        except Exception as e:
            print(f"[ERROR] A critical error occurred during testing: {e}")
        finally:
            self.stop_server()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="UATP Capsule Engine Enhanced API Test"
    )
    parser.add_argument("--host", default="localhost", help="API server host")
    parser.add_argument("--port", type=int, default=5006, help="API server port")
    parser.add_argument("--api-key", help="API key for authentication")

    args = parser.parse_args()

    api_key = args.api_key or os.getenv("UATP_TEST_API_KEY")

    tester = UATAPITester(host=args.host, port=args.port, api_key=api_key)
    tester.run_all_tests()
