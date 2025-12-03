#!/usr/bin/env python3
"""
UATP Server Monitor and Auto-Restart Script
Ensures the UATP server stays running and automatically restarts if it crashes
"""
import os
import sys
import time
import signal
import subprocess
import requests
from pathlib import Path
from datetime import datetime


class ServerMonitor:
    def __init__(self, server_script="start_production_server.py", check_interval=30):
        self.server_script = Path(__file__).parent / server_script
        self.check_interval = check_interval
        self.server_process = None
        self.running = True
        self.restart_count = 0
        self.max_restarts = 10
        self.health_url = "http://localhost:9090/health"

    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        sys.stdout.flush()

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.log(f"Received signal {signum}. Shutting down monitor...")
        self.running = False
        if self.server_process:
            self.stop_server()
        sys.exit(0)

    def start_server(self):
        """Start the UATP server"""
        try:
            self.log("Starting UATP server...")
            self.server_process = subprocess.Popen(
                [sys.executable, str(self.server_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.server_script.parent,
            )

            # Give server time to start
            time.sleep(5)

            if self.server_process.poll() is None:
                self.log(
                    f"✅ Server started successfully (PID: {self.server_process.pid})"
                )
                return True
            else:
                stdout, stderr = self.server_process.communicate()
                self.log(f"❌ Server failed to start:")
                self.log(f"STDOUT: {stdout.decode()}")
                self.log(f"STDERR: {stderr.decode()}")
                return False

        except Exception as e:
            self.log(f"❌ Failed to start server: {e}")
            return False

    def stop_server(self):
        """Stop the UATP server gracefully"""
        if self.server_process and self.server_process.poll() is None:
            self.log("Stopping UATP server...")
            try:
                # Try graceful shutdown first
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
                self.log("✅ Server stopped gracefully")
            except subprocess.TimeoutExpired:
                self.log("⚠️  Server didn't stop gracefully, forcing shutdown...")
                self.server_process.kill()
                self.server_process.wait()
                self.log("✅ Server force stopped")

    def check_server_health(self):
        """Check if server is responding to health checks"""
        try:
            response = requests.get(self.health_url, timeout=5)
            if response.status_code == 200:
                return True
            else:
                self.log(f"⚠️  Health check failed with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log(f"⚠️  Health check failed: {e}")
            return False

    def is_server_running(self):
        """Check if server process is still running"""
        if not self.server_process:
            return False

        # Check if process is still alive
        if self.server_process.poll() is not None:
            return False

        # Check if server is responding
        return self.check_server_health()

    def restart_server(self):
        """Restart the server"""
        self.restart_count += 1

        if self.restart_count > self.max_restarts:
            self.log(
                f"❌ Maximum restart attempts ({self.max_restarts}) reached. Giving up."
            )
            self.running = False
            return False

        self.log(
            f"🔄 Restarting server (attempt {self.restart_count}/{self.max_restarts})..."
        )

        # Stop existing server
        self.stop_server()

        # Wait a bit before restarting
        time.sleep(2)

        # Start new server
        return self.start_server()

    def monitor_loop(self):
        """Main monitoring loop"""
        self.log("🔍 Starting UATP server monitor...")

        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Start initial server
        if not self.start_server():
            self.log("❌ Failed to start initial server. Exiting.")
            return

        # Main monitoring loop
        while self.running:
            try:
                time.sleep(self.check_interval)

                if not self.is_server_running():
                    self.log("❌ Server is not running or not responding")

                    if not self.restart_server():
                        break
                else:
                    # Reset restart count on successful health check
                    if self.restart_count > 0:
                        self.log(
                            f"✅ Server recovered successfully after {self.restart_count} restart(s)"
                        )
                        self.restart_count = 0

                    # Log periodic status
                    if int(time.time()) % 300 == 0:  # Every 5 minutes
                        self.log(
                            f"✅ Server running normally (PID: {self.server_process.pid})"
                        )

            except KeyboardInterrupt:
                self.log("🛑 Monitor interrupted by user")
                break
            except Exception as e:
                self.log(f"❌ Monitor error: {e}")
                time.sleep(5)  # Wait before continuing

        # Cleanup
        self.stop_server()
        self.log("🏁 Monitor shutdown complete")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="UATP Server Monitor")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Health check interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--max-restarts",
        type=int,
        default=10,
        help="Maximum restart attempts (default: 10)",
    )
    parser.add_argument(
        "--server-script",
        default="start_production_server.py",
        help="Server script to monitor (default: start_production_server.py)",
    )

    args = parser.parse_args()

    monitor = ServerMonitor(
        server_script=args.server_script, check_interval=args.interval
    )
    monitor.max_restarts = args.max_restarts

    try:
        monitor.monitor_loop()
    except Exception as e:
        print(f"❌ Monitor failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
