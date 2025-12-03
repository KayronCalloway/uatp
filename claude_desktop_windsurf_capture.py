#!/usr/bin/env python3
"""
Claude Desktop & Windsurf Auto-Capture Service
Monitors and captures conversations from Claude Desktop app and Windsurf
"""

import asyncio
import json
import logging
import os
import requests
import time
import threading
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import psutil

try:
    from AppKit import NSWorkspace, NSRunningApplication
    import Cocoa

    HAS_APPKIT = True
except ImportError:
    HAS_APPKIT = False
    logger.warning("⚠️ AppKit not available - using fallback app detection")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/Users/kay/uatp-capsule-engine/desktop_apps_capture.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class DesktopAppsAutoCapture:
    """Auto-capture service for Claude Desktop and Windsurf."""

    def __init__(self):
        self.api_base = "http://localhost:9090"
        self.api_key = "dev-key-001"
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        # App monitoring state
        self.running = True
        self.sessions = {"claude_desktop": None, "windsurf": None}
        self.message_counts = {"claude_desktop": 0, "windsurf": 0}

        # Conversation tracking
        self.last_captured_content = {}
        self.app_windows = {}

        logger.info("🚀 Desktop Apps Auto-Capture initialized")

    def get_running_apps(self) -> Dict[str, bool]:
        """Check which target apps are currently running."""
        apps = {"claude_desktop": False, "windsurf": False}

        try:
            if HAS_APPKIT:
                # Use AppKit for detailed app info
                workspace = NSWorkspace.sharedWorkspace()
                running_apps = workspace.runningApplications()

                for app in running_apps:
                    app_name = app.localizedName().lower()
                    bundle_id = app.bundleIdentifier() or ""

                    if "claude" in app_name and "desktop" in app_name:
                        apps["claude_desktop"] = True
                    elif "windsurf" in app_name or "windsurf" in bundle_id.lower():
                        apps["windsurf"] = True
                    elif "codeium" in bundle_id.lower():  # Windsurf is made by Codeium
                        apps["windsurf"] = True
            else:
                # Fallback using psutil
                for proc in psutil.process_iter(["pid", "name"]):
                    try:
                        name = proc.info["name"].lower()
                        if "claude" in name:
                            apps["claude_desktop"] = True
                        elif "windsurf" in name or "codeium" in name:
                            apps["windsurf"] = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

        except Exception as e:
            logger.error(f"❌ Error checking running apps: {e}")

        return apps

    def start_session(self, app_name: str):
        """Start new session for an app."""
        session_id = f"{app_name}-auto-{int(time.time())}"
        self.sessions[app_name] = session_id
        self.message_counts[app_name] = 0
        logger.info(f"📝 Started {app_name} session: {session_id}")
        return session_id

    def capture_message(
        self, app_name: str, role: str, content: str, metadata: Optional[Dict] = None
    ):
        """Capture message from desktop app."""
        if not self.sessions[app_name]:
            self.start_session(app_name)

        if not content or len(content.strip()) < 10:
            return False

        # Avoid duplicates
        content_hash = hashlib.md5(f"{app_name}:{role}:{content}".encode()).hexdigest()
        if content_hash == self.last_captured_content.get(app_name):
            return False

        try:
            message_data = {
                "session_id": self.sessions[app_name],
                "user_id": "kay" if role == "user" else f"{app_name}-assistant",
                "platform": app_name,
                "role": role,
                "content": content.strip(),
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": f"{app_name}_auto_capture",
                    "conversation_type": "desktop_app_interaction",
                    "app_name": app_name,
                    "message_index": self.message_counts[app_name] + 1,
                    "auto_captured": True,
                    **(metadata or {}),
                },
            }

            response = requests.post(
                f"{self.api_base}/api/v1/live/capture/message",
                headers=self.headers,
                json=message_data,
                timeout=5,
            )

            if response.ok:
                self.message_counts[app_name] += 1
                self.last_captured_content[app_name] = content_hash
                logger.info(
                    f"✅ {app_name}: captured {role} message ({len(content)} chars)"
                )
                return True
            else:
                logger.error(
                    f"❌ {app_name}: failed to capture - {response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ {app_name}: capture error - {e}")
            return False

    def monitor_claude_desktop(self):
        """Monitor Claude Desktop app."""
        logger.info("🖥️ Starting Claude Desktop monitoring...")

        last_clipboard = ""

        while self.running:
            try:
                apps = self.get_running_apps()

                if apps["claude_desktop"]:
                    # Monitor clipboard when Claude Desktop is active
                    try:
                        result = subprocess.run(
                            ["pbpaste"], capture_output=True, text=True, timeout=2
                        )
                        clipboard_content = result.stdout.strip()

                        if (
                            clipboard_content != last_clipboard
                            and len(clipboard_content) > 50
                            and self.looks_like_claude_conversation(clipboard_content)
                        ):
                            messages = self.parse_conversation(clipboard_content)
                            for msg in messages:
                                self.capture_message(
                                    "claude_desktop",
                                    msg["role"],
                                    msg["content"],
                                    {
                                        "capture_method": "clipboard_monitoring",
                                        "app_active": True,
                                    },
                                )

                            last_clipboard = clipboard_content
                            logger.info(
                                f"🖥️ Claude Desktop: captured {len(messages)} messages"
                            )

                    except subprocess.TimeoutExpired:
                        pass
                    except Exception as e:
                        logger.warning(f"⚠️ Claude Desktop clipboard error: {e}")

                time.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"❌ Claude Desktop monitoring error: {e}")
                time.sleep(10)

    def monitor_windsurf(self):
        """Monitor Windsurf editor."""
        logger.info("🏄 Starting Windsurf monitoring...")

        # Windsurf project paths to monitor
        windsurf_paths = [
            "/Users/kay/uatp-capsule-engine",
            "/Users/kay/Documents",
            "/Users/kay/Desktop",
        ]

        last_ai_interaction = time.time()

        while self.running:
            try:
                apps = self.get_running_apps()

                if apps["windsurf"]:
                    # Monitor for AI interactions in Windsurf
                    self.check_windsurf_ai_activity(windsurf_paths)

                    # Check clipboard for code/AI interactions
                    try:
                        result = subprocess.run(
                            ["pbpaste"], capture_output=True, text=True, timeout=2
                        )
                        clipboard_content = result.stdout.strip()

                        if len(
                            clipboard_content
                        ) > 50 and self.looks_like_windsurf_interaction(
                            clipboard_content
                        ):
                            # Capture as AI coding interaction
                            self.capture_message(
                                "windsurf",
                                "user",
                                "AI coding assistance request",
                                {
                                    "capture_method": "windsurf_interaction",
                                    "code_snippet": clipboard_content[:500],
                                    "interaction_type": "code_assistance",
                                },
                            )

                            logger.info("🏄 Windsurf: captured AI interaction")

                    except Exception as e:
                        logger.warning(f"⚠️ Windsurf clipboard error: {e}")

                time.sleep(3)  # Check every 3 seconds

            except Exception as e:
                logger.error(f"❌ Windsurf monitoring error: {e}")
                time.sleep(10)

    def check_windsurf_ai_activity(self, paths: List[str]):
        """Check for AI activity in Windsurf projects."""
        try:
            # Look for recent .cursorrules or AI-related files
            for path in paths:
                if os.path.exists(path):
                    # Check for AI conversation files
                    ai_files = [
                        ".cursorrules",
                        ".windsurf",
                        "ai_conversation.md",
                        "chat_history.json",
                        ".ai_session",
                    ]

                    for ai_file in ai_files:
                        file_path = os.path.join(path, ai_file)
                        if os.path.exists(file_path):
                            # Check if file was recently modified
                            mod_time = os.path.getmtime(file_path)
                            if time.time() - mod_time < 60:  # Modified in last minute
                                try:
                                    with open(file_path, "r") as f:
                                        content = f.read()

                                    if len(content) > 100:
                                        self.capture_message(
                                            "windsurf",
                                            "assistant",
                                            f"AI assistance in {ai_file}",
                                            {
                                                "file_path": file_path,
                                                "file_content": content[:1000],
                                                "interaction_type": "ai_file_update",
                                            },
                                        )

                                except Exception as e:
                                    logger.warning(f"⚠️ Error reading {file_path}: {e}")

        except Exception as e:
            logger.warning(f"⚠️ Error checking Windsurf AI activity: {e}")

    def looks_like_claude_conversation(self, content: str) -> bool:
        """Check if content looks like Claude conversation."""
        indicators = [
            "claude",
            "assistant:",
            "user:",
            "human:",
            "i'm claude",
            "how can i help",
            "i'd be happy to",
            "```",
            "let me",
            "i can help",
        ]

        content_lower = content.lower()
        return any(indicator in content_lower for indicator in indicators)

    def looks_like_windsurf_interaction(self, content: str) -> bool:
        """Check if content looks like Windsurf AI interaction."""
        indicators = [
            "function",
            "class",
            "import",
            "export",
            "const",
            "let",
            "var",
            "def ",
            "async ",
            "await ",
            "return",
            "if __name__",
            "// ",
            "# ",
            "/* ",
            "*/",
            "<!DOCTYPE",
            "<html",
        ]

        return any(indicator in content for indicator in indicators)

    def parse_conversation(self, content: str) -> List[Dict]:
        """Parse conversation content into messages."""
        messages = []
        lines = content.split("\n")
        current_role = None
        current_content = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect role changes
            if line.lower().startswith(("user:", "human:", "you:")):
                if current_role and current_content:
                    messages.append(
                        {"role": current_role, "content": "\n".join(current_content)}
                    )
                current_role = "user"
                current_content = [
                    line.split(":", 1)[1].strip() if ":" in line else line
                ]
            elif line.lower().startswith(("assistant:", "claude:", "ai:")):
                if current_role and current_content:
                    messages.append(
                        {"role": current_role, "content": "\n".join(current_content)}
                    )
                current_role = "assistant"
                current_content = [
                    line.split(":", 1)[1].strip() if ":" in line else line
                ]
            else:
                if current_role:
                    current_content.append(line)

        # Add final message
        if current_role and current_content:
            messages.append(
                {"role": current_role, "content": "\n".join(current_content)}
            )

        return messages

    def show_status(self):
        """Show monitoring status."""
        apps = self.get_running_apps()

        print("\n" + "=" * 70)
        print("🖥️ Desktop Apps Auto-Capture Status")
        print("=" * 70)

        for app_name in ["claude_desktop", "windsurf"]:
            status = "🟢 Running" if apps[app_name] else "⚪ Not Running"
            session = self.sessions[app_name] or "None"
            count = self.message_counts[app_name]

            print(f"{app_name.replace('_', ' ').title():<15}: {status}")
            print(f"  Session: {session}")
            print(f"  Messages: {count}")
            print()

        print(f"🔗 Dashboard: http://localhost:3000")
        print(f"📱 Mobile: http://192.168.1.79:3000")
        print("=" * 70)

    def run_service(self):
        """Run the desktop apps monitoring service."""
        logger.info("🚀 Starting Desktop Apps Auto-Capture service...")

        # Start monitoring threads
        claude_thread = threading.Thread(
            target=self.monitor_claude_desktop, daemon=True
        )
        windsurf_thread = threading.Thread(target=self.monitor_windsurf, daemon=True)

        claude_thread.start()
        windsurf_thread.start()

        # Capture initial status
        apps = self.get_running_apps()
        for app_name, is_running in apps.items():
            if is_running:
                self.capture_message(
                    app_name,
                    "user",
                    f"Started monitoring {app_name}",
                    {"event_type": "monitoring_started", "app_detected": True},
                )

        # Main status loop
        try:
            while self.running:
                self.show_status()
                time.sleep(30)  # Status update every 30 seconds

        except KeyboardInterrupt:
            logger.info("🛑 Stopping desktop apps auto-capture...")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Service error: {e}")
        finally:
            self.running = False
            logger.info("📴 Desktop apps auto-capture stopped")


def main():
    """Main entry point."""
    print(
        """
🖥️ Claude Desktop & Windsurf Auto-Capture Service
=================================================

This service monitors and automatically captures:
• 🖥️ Claude Desktop app conversations
• 🏄 Windsurf AI coding interactions  
• 📋 Clipboard monitoring when apps are active
• 📁 Project file AI interactions
• 🔄 Continuous session management

Features:
• Real-time app detection
• Intelligent conversation parsing
• Full UATP attribution tracking
• Separate sessions per app
• Background monitoring

Press Ctrl+C to stop
"""
    )

    try:
        capture_service = DesktopAppsAutoCapture()
        capture_service.run_service()
    except ImportError as e:
        print("❌ Missing required dependencies. Install with:")
        print("pip install psutil pyobjc-framework-Cocoa")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
