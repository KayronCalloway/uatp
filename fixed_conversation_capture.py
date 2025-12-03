#!/usr/bin/env python3
"""
Fixed Cross-Platform Conversation Capture
Properly captures Claude Desktop, Windsurf, and Claude Code conversations in real-time
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
import hashlib
import psutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/Users/kay/uatp-capsule-engine/fixed_capture.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class RealTimeConversationCapture:
    """Fixed real-time conversation capture for all platforms."""

    def __init__(self):
        self.api_base = "http://localhost:9090"
        self.api_key = "dev-key-001"
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        # Active conversations tracking
        self.active_conversations = {}
        self.last_clipboard_content = ""
        self.last_clipboard_hash = ""
        self.running = True

        # Platform detection patterns
        self.platform_patterns = {
            "claude_desktop": [
                r"Claude.*?Desktop",
                r"Anthropic.*?Claude",
                r"claude\.ai",
            ],
            "windsurf": [r"Windsurf", r"Codeium.*?Windsurf", r"windsurf\.codeium"],
            "claude_code": [r"Claude.*?Code", r"claude-code", r"Terminal.*?claude"],
        }

        logger.info("🚀 Starting Real-Time Conversation Capture Service")

    def get_active_apps(self) -> List[str]:
        """Get list of currently active applications."""
        try:
            active_apps = []
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    app_name = proc.info["name"]
                    if app_name:
                        active_apps.append(app_name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return active_apps
        except Exception as e:
            logger.error(f"Error getting active apps: {e}")
            return []

    def detect_platform(self, content: str, apps: List[str]) -> Optional[str]:
        """Detect which platform the conversation is from."""

        # Check app processes first
        app_names_str = " ".join(apps).lower()

        if any(app in app_names_str for app in ["claude", "anthropic"]):
            if "windsurf" in app_names_str or "codeium" in app_names_str:
                return "windsurf"
            elif "desktop" in content.lower() or "claude.ai" in content.lower():
                return "claude_desktop"
            else:
                return "claude_code"

        # Check content patterns
        content_lower = content.lower()

        if any(pattern in content_lower for pattern in ["windsurf", "codeium"]):
            return "windsurf"
        elif any(
            pattern in content_lower
            for pattern in ["claude.ai", "desktop", "anthropic"]
        ):
            return "claude_desktop"
        elif any(
            pattern in content_lower for pattern in ["terminal", "cli", "command"]
        ):
            return "claude_code"

        # Default to claude_code if running from terminal
        return "claude_code"

    def get_clipboard_content(self) -> Optional[str]:
        """Get current clipboard content."""
        try:
            result = subprocess.run(
                ["pbpaste"], capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.debug(f"Clipboard access error: {e}")
        return None

    def is_conversation_content(self, content: str) -> bool:
        """Determine if content looks like a conversation."""
        if not content or len(content.strip()) < 20:
            return False

        # Look for conversation indicators
        conversation_indicators = [
            "user:",
            "assistant:",
            "human:",
            "ai:",
            "you:",
            "me:",
            "claude:",
            "gpt:",
            "question:",
            "answer:",
            "response:",
            "how do i",
            "can you",
            "please help",
            "explain",
            "what is",
            "how to",
            "```",
            "def ",
            "class ",
            "function",
            "import ",
            "from ",
            "const ",
            "let ",
            "error:",
            "exception:",
            "traceback",
        ]

        content_lower = content.lower()
        indicator_count = sum(
            1 for indicator in conversation_indicators if indicator in content_lower
        )

        # If it has multiple indicators, likely a conversation
        if indicator_count >= 2:
            return True

        # Check for code or technical content
        code_patterns = [
            r"```[\s\S]*?```",  # Code blocks
            r"def\s+\w+\s*\(",  # Function definitions
            r"class\s+\w+",  # Class definitions
            r"import\s+\w+",  # Imports
            r"<[^>]+>",  # HTML tags
        ]

        code_matches = sum(
            1 for pattern in code_patterns if re.search(pattern, content)
        )
        if code_matches > 0:
            return True

        # Check length and complexity
        if len(content) > 100 and len(content.split()) > 10:
            return True

        return False

    def extract_conversation_parts(self, content: str) -> Dict:
        """Extract user and assistant parts from conversation content."""

        # Try to split by common conversation patterns
        user_patterns = [
            r"(?:user|human|you|me):\s*(.*?)(?=(?:assistant|ai|claude|gpt):|$)",
            r"(?:question|ask):\s*(.*?)(?=(?:answer|response):|$)",
        ]

        assistant_patterns = [
            r"(?:assistant|ai|claude|gpt):\s*(.*?)(?=(?:user|human):|$)",
            r"(?:answer|response):\s*(.*?)(?=(?:question|ask):|$)",
        ]

        user_content = ""
        assistant_content = ""

        # Try to extract structured conversation
        for pattern in user_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            if matches:
                user_content = " ".join(matches).strip()
                break

        for pattern in assistant_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            if matches:
                assistant_content = " ".join(matches).strip()
                break

        # If no structured format found, treat as single message
        if not user_content and not assistant_content:
            # Try to determine if it's a question (user) or answer (assistant)
            if any(
                indicator in content.lower()
                for indicator in ["how do", "can you", "what is", "please", "?"]
            ):
                user_content = content
            else:
                assistant_content = content

        return {
            "user_content": user_content,
            "assistant_content": assistant_content,
            "full_content": content,
        }

    def calculate_significance(self, content: str) -> float:
        """Calculate conversation significance score."""
        if not content:
            return 0.0

        score = 0.0
        content_lower = content.lower()

        # Technical content indicators
        technical_terms = [
            "algorithm",
            "implementation",
            "function",
            "class",
            "method",
            "database",
            "api",
            "framework",
            "library",
            "programming",
            "code",
            "script",
            "debug",
            "error",
            "exception",
            "traceback",
            "deployment",
            "architecture",
            "design",
            "optimization",
            "security",
            "authentication",
            "encryption",
            "protocol",
        ]

        tech_count = sum(1 for term in technical_terms if term in content_lower)
        score += min(tech_count * 0.1, 0.4)  # Max 0.4 for technical content

        # Code presence
        if "```" in content or re.search(
            r"def\s+\w+|class\s+\w+|import\s+\w+", content
        ):
            score += 0.2

        # Length and complexity
        word_count = len(content.split())
        if word_count > 50:
            score += 0.1
        if word_count > 200:
            score += 0.1

        # Problem-solving indicators
        problem_terms = ["error", "issue", "problem", "fix", "solve", "debug", "help"]
        problem_count = sum(1 for term in problem_terms if term in content_lower)
        score += min(problem_count * 0.05, 0.2)

        return min(score, 1.0)

    async def send_message_to_api(
        self,
        session_id: str,
        platform: str,
        role: str,
        content: str,
        metadata: Dict = None,
    ):
        """Send message to live capture API."""

        message_data = {
            "session_id": session_id,
            "user_id": "real-user",
            "platform": platform,
            "role": role,
            "content": content,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "fixed_capture_service",
                "auto_detected": True,
                "platform_detection": "improved",
                **(metadata or {}),
            },
        }

        try:
            response = requests.post(
                f"{self.api_base}/api/v1/live/capture/message",
                headers=self.headers,
                json=message_data,
                timeout=5,
            )

            if response.ok:
                logger.info(f"✅ Sent {role} message to session {session_id}")
                return True
            else:
                logger.error(f"❌ Failed to send message: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ API error: {e}")
            return False

    async def process_conversation_content(self, content: str, apps: List[str]):
        """Process detected conversation content."""

        # Detect platform
        platform = self.detect_platform(content, apps)

        # Extract conversation parts
        conversation_parts = self.extract_conversation_parts(content)

        # Calculate significance
        significance = self.calculate_significance(content)

        # Create session ID
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        session_id = f"{platform}-conversation-{int(time.time())}-{content_hash}"

        logger.info(
            f"🎯 Processing conversation: platform={platform}, significance={significance:.2f}"
        )

        # Send user message if present
        if conversation_parts["user_content"]:
            await self.send_message_to_api(
                session_id,
                platform,
                "user",
                conversation_parts["user_content"],
                {"significance": significance, "content_type": "user_query"},
            )

        # Send assistant message if present
        if conversation_parts["assistant_content"]:
            await self.send_message_to_api(
                session_id,
                platform,
                "assistant",
                conversation_parts["assistant_content"],
                {"significance": significance, "content_type": "assistant_response"},
            )

        # If no structured parts, send as single message
        if (
            not conversation_parts["user_content"]
            and not conversation_parts["assistant_content"]
        ):
            role = (
                "user"
                if any(
                    indicator in content.lower()
                    for indicator in ["?", "how", "what", "can you"]
                )
                else "assistant"
            )
            await self.send_message_to_api(
                session_id,
                platform,
                role,
                content,
                {"significance": significance, "content_type": "unstructured"},
            )

        # Track conversation
        self.active_conversations[session_id] = {
            "platform": platform,
            "last_activity": time.time(),
            "significance": significance,
            "message_count": 1
            if conversation_parts["user_content"]
            and conversation_parts["assistant_content"]
            else 1,
        }

        logger.info(f"📝 Created conversation session: {session_id}")

    async def monitor_conversations(self):
        """Main monitoring loop."""

        logger.info("🔍 Starting conversation monitoring...")

        while self.running:
            try:
                # Get current apps
                active_apps = self.get_active_apps()

                # Get clipboard content
                clipboard_content = self.get_clipboard_content()

                if clipboard_content:
                    # Check if content changed
                    content_hash = hashlib.md5(clipboard_content.encode()).hexdigest()

                    if (
                        content_hash != self.last_clipboard_hash
                        and clipboard_content != self.last_clipboard_content
                    ):
                        # Check if it looks like conversation content
                        if self.is_conversation_content(clipboard_content):
                            logger.info(
                                f"📋 New conversation content detected ({len(clipboard_content)} chars)"
                            )
                            await self.process_conversation_content(
                                clipboard_content, active_apps
                            )

                        self.last_clipboard_content = clipboard_content
                        self.last_clipboard_hash = content_hash

                # Clean up old conversations
                current_time = time.time()
                expired_sessions = [
                    session_id
                    for session_id, info in self.active_conversations.items()
                    if current_time - info["last_activity"] > 300  # 5 minutes
                ]

                for session_id in expired_sessions:
                    del self.active_conversations[session_id]
                    logger.debug(f"🧹 Cleaned up expired session: {session_id}")

                # Wait before next check
                await asyncio.sleep(2)  # Check every 2 seconds

            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(5)

    async def start_capture(self):
        """Start the capture service."""
        logger.info("🚀 Fixed Conversation Capture Service Started")
        logger.info("💡 To capture conversations:")
        logger.info("   1. Copy conversation content to clipboard (Cmd+C)")
        logger.info("   2. Service will auto-detect and process it")
        logger.info("   3. High-significance conversations will create UATP capsules")

        try:
            await self.monitor_conversations()
        except KeyboardInterrupt:
            logger.info("⏹️ Capture service stopped by user")
        except Exception as e:
            logger.error(f"❌ Service error: {e}")
        finally:
            self.running = False


def main():
    """Main entry point."""
    capture_service = RealTimeConversationCapture()

    # Run the async service
    try:
        asyncio.run(capture_service.start_capture())
    except KeyboardInterrupt:
        print("\n⏹️ Service stopped")


if __name__ == "__main__":
    main()
