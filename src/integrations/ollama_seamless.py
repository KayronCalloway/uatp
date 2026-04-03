#!/usr/bin/env python3
"""
UATP Ollama Seamless Integration
=================================

Makes UATP capture completely transparent for all Ollama usage.

Strategy:
1. Ollama runs on port 11433 (moved from default)
2. UATP Proxy runs on port 11434 (the default Ollama port)
3. All clients automatically go through capture without config changes

Installation:
    python -m src.integrations.ollama_seamless install

This will:
1. Create a launchd/systemd service for the proxy
2. Configure Ollama to use port 11433
3. Start the proxy on port 11434
4. Every Ollama request is now captured automatically

Usage after install:
    ollama run gemma4  # Just works - captured automatically
    # Any app using Ollama - captured automatically
"""

import argparse
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Detect paths
UATP_ROOT = Path(__file__).parent.parent.parent
PROXY_SCRIPT = UATP_ROOT / "src" / "integrations" / "ollama_proxy.py"
PID_FILE = Path.home() / ".uatp" / "ollama_proxy.pid"
LOG_FILE = Path.home() / ".uatp" / "ollama_proxy.log"

# Ports - Alternative approach: proxy on 11435, Ollama stays on 11434
# Users set OLLAMA_HOST=http://localhost:11435 to use capture
PROXY_PORT = 11435  # Proxy listens here
OLLAMA_PORT = 11434  # Ollama stays on default


def get_system():
    """Detect operating system."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    return system


def ensure_dirs():
    """Ensure UATP directories exist."""
    (Path.home() / ".uatp").mkdir(exist_ok=True)


def is_proxy_running() -> bool:
    """Check if proxy is already running."""
    if not PID_FILE.exists():
        return False

    try:
        pid = int(PID_FILE.read_text().strip())
        # Check if process exists
        os.kill(pid, 0)
        return True
    except (ValueError, ProcessLookupError, PermissionError):
        # Clean up stale PID file
        PID_FILE.unlink(missing_ok=True)
        return False


def is_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def start_proxy(ollama_port: int = OLLAMA_PORT, assess: bool = True) -> Optional[int]:
    """Start the UATP proxy daemon."""
    ensure_dirs()

    if is_proxy_running():
        pid = int(PID_FILE.read_text().strip())
        print(f"Proxy already running (PID: {pid})")
        return pid

    # Build command
    cmd = [
        sys.executable,
        "-m",
        "src.integrations.ollama_proxy",
        "--port",
        str(PROXY_PORT),
        "--ollama-url",
        f"http://localhost:{ollama_port}",
    ]
    if assess:
        cmd.append("--assess")

    # Start as daemon
    with open(LOG_FILE, "a") as log:
        log.write(
            f"\n{'=' * 60}\nStarting proxy at {time.strftime('%Y-%m-%d %H:%M:%S')}\n{'=' * 60}\n"
        )
        process = subprocess.Popen(
            cmd,
            cwd=str(UATP_ROOT),
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    # Save PID
    PID_FILE.write_text(str(process.pid))

    # Wait for startup
    for _ in range(10):
        time.sleep(0.5)
        if is_port_in_use(PROXY_PORT):
            print(f"UATP Proxy started (PID: {process.pid})")
            return process.pid

    print("Warning: Proxy may not have started correctly")
    return process.pid


def stop_proxy():
    """Stop the UATP proxy daemon."""
    if not PID_FILE.exists():
        print("Proxy not running")
        return

    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        print(f"Stopped proxy (PID: {pid})")
    except (ValueError, ProcessLookupError):
        print("Proxy was not running")
    finally:
        PID_FILE.unlink(missing_ok=True)


def status():
    """Show proxy status."""
    proxy_running = is_proxy_running() or is_port_in_use(PROXY_PORT)

    if proxy_running:
        if PID_FILE.exists():
            pid = int(PID_FILE.read_text().strip())
            print(f"UATP Proxy: RUNNING (PID: {pid})")
        else:
            print("UATP Proxy: RUNNING (via LaunchAgent)")
        print(f"  Listening: http://localhost:{PROXY_PORT}")
        print(f"  Forwarding to: http://localhost:{OLLAMA_PORT}")
        print(f"  Log file: {LOG_FILE}")
    else:
        print("UATP Proxy: NOT RUNNING")

    # Check Ollama
    if is_port_in_use(OLLAMA_PORT):
        print(f"Ollama: RUNNING on port {OLLAMA_PORT}")
    else:
        print("Ollama: NOT RUNNING")

    # Show how to enable
    print()
    if proxy_running and is_port_in_use(OLLAMA_PORT):
        print("To enable capture, set:")
        print(f"  export OLLAMA_HOST=http://localhost:{PROXY_PORT}")
    elif not proxy_running:
        print("Start the proxy with:")
        print("  python3 -m src.integrations.ollama_seamless start")


def install_macos():
    """Install LaunchAgent for macOS."""
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_dir.mkdir(parents=True, exist_ok=True)

    plist_path = plist_dir / "com.uatp.ollama-proxy.plist"

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.uatp.ollama-proxy</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>-m</string>
        <string>src.integrations.ollama_proxy</string>
        <string>--port</string>
        <string>{PROXY_PORT}</string>
        <string>--ollama-url</string>
        <string>http://localhost:{OLLAMA_PORT}</string>
        <string>--assess</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{UATP_ROOT}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{LOG_FILE}</string>
    <key>StandardErrorPath</key>
    <string>{LOG_FILE}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:{Path(sys.executable).parent}</string>
    </dict>
</dict>
</plist>
"""

    plist_path.write_text(plist_content)
    print(f"Created LaunchAgent: {plist_path}")

    # Load the agent
    subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
    subprocess.run(["launchctl", "load", str(plist_path)], check=True)
    print("LaunchAgent loaded - proxy will start automatically on login")

    return plist_path


def install_linux():
    """Install systemd user service for Linux."""
    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)

    service_path = service_dir / "uatp-ollama-proxy.service"

    service_content = f"""[Unit]
Description=UATP Ollama Capture Proxy
After=network.target

[Service]
Type=simple
WorkingDirectory={UATP_ROOT}
ExecStart={sys.executable} -m src.integrations.ollama_proxy --port {PROXY_PORT} --ollama-url http://localhost:{OLLAMA_PORT} --assess
Restart=always
RestartSec=5
StandardOutput=append:{LOG_FILE}
StandardError=append:{LOG_FILE}

[Install]
WantedBy=default.target
"""

    service_path.write_text(service_content)
    print(f"Created systemd service: {service_path}")

    # Enable and start
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "uatp-ollama-proxy"], check=True)
    subprocess.run(["systemctl", "--user", "start", "uatp-ollama-proxy"], check=True)
    print("Service enabled - proxy will start automatically on login")

    return service_path


def create_ollama_wrapper():
    """Create wrapper script that ensures Ollama uses the right port."""
    wrapper_dir = Path.home() / ".uatp" / "bin"
    wrapper_dir.mkdir(parents=True, exist_ok=True)

    # Find real ollama
    result = subprocess.run(["which", "ollama"], capture_output=True, text=True)
    real_ollama = (
        result.stdout.strip() if result.returncode == 0 else "/usr/local/bin/ollama"
    )

    wrapper_content = f"""#!/bin/bash
# UATP Ollama Wrapper - Ensures capture is active

REAL_OLLAMA="{real_ollama}"
PROXY_PORT={PROXY_PORT}
OLLAMA_PORT={OLLAMA_PORT}

# Check if we're running 'serve' command
if [[ "$1" == "serve" ]]; then
    # Start Ollama on the alternate port
    export OLLAMA_HOST="0.0.0.0:{OLLAMA_PORT}"
    exec "$REAL_OLLAMA" "$@"
else
    # For all other commands, ensure proxy is running and use it
    if ! curl -s "http://localhost:$PROXY_PORT/api/tags" > /dev/null 2>&1; then
        echo "[UATP] Starting capture proxy..." >&2
        python3 -m src.integrations.ollama_seamless start --quiet 2>/dev/null &
        sleep 2
    fi

    # Use proxy
    export OLLAMA_HOST="http://localhost:$PROXY_PORT"
    exec "$REAL_OLLAMA" "$@"
fi
"""

    wrapper_path = wrapper_dir / "ollama"
    wrapper_path.write_text(wrapper_content)
    wrapper_path.chmod(0o755)

    print(f"Created wrapper: {wrapper_path}")
    return wrapper_path


def create_shell_integration():
    """Create shell integration for automatic setup."""
    integration = f"""
# UATP Ollama Capture Integration
# Add this to your ~/.bashrc or ~/.zshrc

# Point Ollama clients to the capture proxy
export OLLAMA_HOST="http://localhost:{PROXY_PORT}"

# Function to ensure proxy is running
uatp-ollama-ensure() {{
    if ! curl -s "http://localhost:{PROXY_PORT}/api/tags" > /dev/null 2>&1; then
        echo "[UATP] Starting capture proxy..." >&2
        cd {UATP_ROOT} && python3 -m src.integrations.ollama_seamless start --quiet 2>/dev/null
        sleep 2
    fi
}}

# Auto-ensure proxy on first ollama command
ollama() {{
    uatp-ollama-ensure
    command ollama "$@"
}}

# Convenience commands
alias uatp-status='python3 -m src.integrations.ollama_seamless status'
alias uatp-logs='python3 -m src.integrations.ollama_seamless logs'

# Auto-start proxy if not running (runs once on shell init)
uatp-ollama-ensure 2>/dev/null &
"""

    integration_path = Path.home() / ".uatp" / "shell-integration.sh"
    integration_path.write_text(integration)

    print(f"\nShell integration saved to: {integration_path}")
    print("\nAdd this to your ~/.bashrc or ~/.zshrc:")
    print(f'  source "{integration_path}"')

    return integration_path


def configure_ollama_port():
    """Show how to enable capture (no Ollama config needed)."""
    print("\nNo Ollama configuration needed!")
    print()
    print("The shell integration automatically:")
    print(f"  1. Sets OLLAMA_HOST to point to the capture proxy (port {PROXY_PORT})")
    print("  2. Starts the proxy if not running")
    print("  3. All ollama commands go through capture transparently")
    print()
    print("Just add to your ~/.zshrc or ~/.bashrc:")
    print(f'  source "{Path.home()}/.uatp/shell-integration.sh"')


def install():
    """Full installation for seamless capture."""
    ensure_dirs()
    system = get_system()

    print("=" * 60)
    print("UATP Ollama Seamless Capture - Installation")
    print("=" * 60)
    print()

    # 1. Create wrapper
    print("1. Creating Ollama wrapper...")
    wrapper_path = create_ollama_wrapper()

    # 2. Install service
    print(f"\n2. Installing system service ({system})...")
    if system == "macos":
        install_macos()
    elif system == "linux":
        install_linux()
    else:
        print(f"   Automatic service not supported on {system}")
        print("   Use 'python -m src.integrations.ollama_seamless start' manually")

    # 3. Shell integration
    print("\n3. Creating shell integration...")
    create_shell_integration()

    # 4. Configure Ollama
    print("\n4. Ollama configuration needed:")
    configure_ollama_port()

    print()
    print("=" * 60)
    print("Installation complete!")
    print("=" * 60)
    print()
    print("Quick start:")
    print("  1. Restart your terminal (to get PATH update)")
    print(f"  2. Configure Ollama to use port {OLLAMA_PORT} (see above)")
    print("  3. Restart Ollama")
    print("  4. Use Ollama normally - all interactions are captured!")
    print()
    print("Verify with:")
    print("  python -m src.integrations.ollama_seamless status")


def uninstall():
    """Remove seamless integration."""
    system = get_system()

    print("Uninstalling UATP Ollama integration...")

    # Stop proxy
    stop_proxy()

    # Remove service
    if system == "macos":
        plist = Path.home() / "Library" / "LaunchAgents" / "com.uatp.ollama-proxy.plist"
        if plist.exists():
            subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
            plist.unlink()
            print("Removed LaunchAgent")
    elif system == "linux":
        subprocess.run(
            ["systemctl", "--user", "stop", "uatp-ollama-proxy"], capture_output=True
        )
        subprocess.run(
            ["systemctl", "--user", "disable", "uatp-ollama-proxy"], capture_output=True
        )
        service = (
            Path.home() / ".config" / "systemd" / "user" / "uatp-ollama-proxy.service"
        )
        if service.exists():
            service.unlink()
            print("Removed systemd service")

    # Remove wrapper
    wrapper = Path.home() / ".uatp" / "bin" / "ollama"
    if wrapper.exists():
        wrapper.unlink()
        print("Removed wrapper script")

    print()
    print("Uninstall complete. Remember to:")
    print("  1. Remove 'source ~/.uatp/shell-integration.sh' from your shell rc file")
    print("  2. Reconfigure Ollama to use default port 11434 if needed")


def switch_ports():
    """Start proxy alongside Ollama (non-invasive approach)."""
    print("Starting UATP capture mode...")
    print()
    print("This approach runs the proxy alongside Ollama (doesn't modify Ollama).")
    print()

    # 1. Check Ollama is running
    if not is_port_in_use(OLLAMA_PORT):
        print(f"1. Ollama not running on port {OLLAMA_PORT}, starting it...")
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        for _ in range(20):
            time.sleep(0.5)
            if is_port_in_use(OLLAMA_PORT):
                break
    else:
        print(f"1. Ollama already running on port {OLLAMA_PORT}")

    # 2. Stop any existing proxy
    stop_proxy()
    subprocess.run(["pkill", "-f", "ollama_proxy"], capture_output=True)
    time.sleep(1)

    # 3. Start proxy
    print(f"2. Starting UATP Proxy on port {PROXY_PORT}...")
    start_proxy(ollama_port=OLLAMA_PORT)

    # 4. Verify
    time.sleep(2)
    print()
    print("=" * 60)
    status()
    print("=" * 60)
    print()
    print("Capture proxy is running!")
    print()
    print("To enable capture, use ONE of these methods:")
    print()
    print("Method 1 - Environment variable (recommended):")
    print(f"  export OLLAMA_HOST=http://localhost:{PROXY_PORT}")
    print()
    print("Method 2 - Per-command:")
    print(f"  OLLAMA_HOST=http://localhost:{PROXY_PORT} ollama run gemma4")
    print()
    print("Method 3 - Direct curl:")
    print(
        f'  curl http://localhost:{PROXY_PORT}/api/generate -d \'{{"model": "gemma4", "prompt": "Hello", "stream": false}}\''
    )


def main():
    parser = argparse.ArgumentParser(description="UATP Ollama Seamless Integration")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Install
    subparsers.add_parser("install", help="Install seamless integration")

    # Uninstall
    subparsers.add_parser("uninstall", help="Remove integration")

    # Switch
    subparsers.add_parser(
        "switch", help="Switch Ollama to alt port and start proxy (one-time setup)"
    )

    # Start
    start_parser = subparsers.add_parser("start", help="Start proxy daemon")
    start_parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")

    # Stop
    subparsers.add_parser("stop", help="Stop proxy daemon")

    # Status
    subparsers.add_parser("status", help="Show status")

    # Logs
    subparsers.add_parser("logs", help="Show proxy logs")

    args = parser.parse_args()

    if args.command == "install":
        install()
    elif args.command == "uninstall":
        uninstall()
    elif args.command == "switch":
        switch_ports()
    elif args.command == "start":
        if not args.quiet:
            print("Starting UATP Ollama Proxy...")
        start_proxy()
    elif args.command == "stop":
        stop_proxy()
    elif args.command == "status":
        status()
    elif args.command == "logs":
        if LOG_FILE.exists():
            subprocess.run(["tail", "-f", str(LOG_FILE)])
        else:
            print("No logs yet")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
