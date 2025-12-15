#!/usr/bin/env python3
"""
Real-World Data Capture for UATP Testing
Multiple methods to capture actual AI conversations for system testing
"""

import time
from datetime import datetime

import requests


class UATProadDataCapture:
    def __init__(self):
        self.api_base = "http://localhost:9090"
        self.api_key = "dev-key-001"
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    def capture_conversation(
        self,
        user_msg: str,
        ai_response: str,
        platform: str = "manual",
        session_id: str = None,
    ):
        """Capture a real conversation pair to UATP."""

        if not session_id:
            session_id = f"real-data-{int(time.time())}"

        try:
            # Capture user message
            user_data = {
                "session_id": session_id,
                "user_id": "real-user",
                "platform": platform,
                "role": "user",
                "content": user_msg,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "data_source": "real_world_capture",
                    "capture_method": "manual_input",
                },
            }

            user_response = requests.post(
                f"{self.api_base}/api/v1/live/capture/message",
                headers=self.headers,
                json=user_data,
            )

            # Capture AI response
            ai_data = {
                "session_id": session_id,
                "user_id": "ai-assistant",
                "platform": platform,
                "role": "assistant",
                "content": ai_response,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "data_source": "real_world_capture",
                    "capture_method": "manual_input",
                },
            }

            ai_response_req = requests.post(
                f"{self.api_base}/api/v1/live/capture/message",
                headers=self.headers,
                json=ai_data,
            )

            if user_response.ok and ai_response_req.ok:
                print(f"✅ Captured conversation to session: {session_id}")
                return session_id
            else:
                print("❌ Failed to capture conversation")
                return None

        except Exception as e:
            print(f"❌ Error capturing conversation: {e}")
            return None

    def batch_capture_from_file(self, filepath: str):
        """Capture conversations from a text file."""

        print(f"📁 Reading conversations from: {filepath}")

        try:
            with open(filepath) as f:
                content = f.read()

            # Simple parsing - assumes conversations are separated by "---"
            conversations = content.split("---")

            for i, conv in enumerate(conversations):
                if not conv.strip():
                    continue

                lines = [
                    line.strip() for line in conv.strip().split("\n") if line.strip()
                ]

                if len(lines) >= 2:
                    # Assume first line is user, second is AI
                    user_msg = (
                        lines[0].replace("User:", "").replace("Human:", "").strip()
                    )
                    ai_msg = (
                        lines[1].replace("AI:", "").replace("Assistant:", "").strip()
                    )

                    if user_msg and ai_msg:
                        session_id = self.capture_conversation(
                            user_msg, ai_msg, "file_import", f"batch-{i}"
                        )
                        time.sleep(0.5)  # Rate limiting

            print("✅ Batch import complete")

        except Exception as e:
            print(f"❌ Error reading file: {e}")

    def interactive_capture(self):
        """Interactive mode for real-time conversation capture."""

        print("🎯 Interactive Real-Data Capture Mode")
        print("=" * 50)
        print("Paste your real AI conversations here")
        print("Type 'quit' to exit, 'stats' to see captured data")
        print()

        session_count = 0

        while True:
            try:
                user_input = input("👤 Your message: ").strip()

                if user_input.lower() == "quit":
                    break
                elif user_input.lower() == "stats":
                    self.show_capture_stats()
                    continue
                elif not user_input:
                    continue

                ai_input = input("🤖 AI response: ").strip()

                if not ai_input:
                    continue

                platform = (
                    input("📱 Platform (chatgpt/claude/other): ").strip() or "manual"
                )

                session_id = self.capture_conversation(user_input, ai_input, platform)
                if session_id:
                    session_count += 1
                    print(f"📊 Total captured: {session_count} conversations")

                print()

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")

        print(f"\n🎉 Captured {session_count} real conversations!")

    def show_capture_stats(self):
        """Show current capture statistics."""

        try:
            response = requests.get(
                f"{self.api_base}/api/v1/live/capture/conversations",
                headers=self.headers,
            )

            if response.ok:
                data = response.json()
                print("\n📊 Current Stats:")
                print(f"   Active conversations: {data.get('count', 0)}")
                print(f"   Total conversations: {len(data.get('conversations', []))}")

                # Show recent conversations
                convs = data.get("conversations", [])[-3:]
                if convs:
                    print("   Recent sessions:")
                    for conv in convs:
                        print(
                            f"     • {conv['session_id']} ({conv['message_count']} messages)"
                        )
                print()

        except Exception as e:
            print(f"❌ Error getting stats: {e}")

    def clipboard_monitor(self):
        """Monitor clipboard for AI conversations (macOS)."""

        print("📋 Clipboard Monitor Mode")
        print("Copy AI conversations to clipboard - they'll be auto-captured!")
        print("Press Ctrl+C to stop")
        print()

        try:
            import subprocess

            last_clipboard = ""

            while True:
                try:
                    # Get clipboard content (macOS)
                    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
                    clipboard_content = result.stdout.strip()

                    if (
                        clipboard_content != last_clipboard
                        and len(clipboard_content) > 50
                    ):
                        # Try to parse as conversation
                        if self.parse_and_capture_clipboard(clipboard_content):
                            print("✅ Auto-captured from clipboard")
                            last_clipboard = clipboard_content

                    time.sleep(2)  # Check every 2 seconds

                except KeyboardInterrupt:
                    break

        except ImportError:
            print("❌ Clipboard monitoring requires macOS")

    def parse_and_capture_clipboard(self, content: str) -> bool:
        """Try to parse clipboard content as AI conversation."""

        # Simple heuristics to detect AI conversations
        lines = [line.strip() for line in content.split("\n") if line.strip()]

        if len(lines) < 2:
            return False

        # Look for common AI conversation patterns
        user_indicators = ["you:", "user:", "human:", "me:"]
        ai_indicators = ["ai:", "assistant:", "chatgpt:", "claude:"]

        user_msg = None
        ai_msg = None

        for line in lines:
            line_lower = line.lower()

            # Check if line starts with user indicator
            for indicator in user_indicators:
                if line_lower.startswith(indicator):
                    user_msg = line[len(indicator) :].strip()
                    break

            # Check if line starts with AI indicator
            for indicator in ai_indicators:
                if line_lower.startswith(indicator):
                    ai_msg = line[len(indicator) :].strip()
                    break

            # If no indicators, assume alternating pattern
            if not user_msg and len(line) > 20:
                user_msg = line
            elif user_msg and not ai_msg and len(line) > 20:
                ai_msg = line
                break

        if user_msg and ai_msg:
            session_id = self.capture_conversation(user_msg, ai_msg, "clipboard")
            return session_id is not None

        return False


def create_sample_conversations_file():
    """Create a sample file with real-style conversations for testing."""

    sample_conversations = """User: How do I implement authentication in a React app?
AI: To implement authentication in React, you should use a combination of JWT tokens, protected routes, and context for state management. Here's a basic approach: 1) Create an AuthContext, 2) Set up login/logout functions, 3) Use protected route components, 4) Store tokens securely in httpOnly cookies.

---

User: What's the best way to optimize database queries?
AI: Database query optimization involves several strategies: 1) Use proper indexing on frequently queried columns, 2) Avoid SELECT *, instead specify needed columns, 3) Use LIMIT for pagination, 4) Optimize JOIN operations, 5) Consider query caching, 6) Use EXPLAIN to analyze query execution plans.

---

User: Explain how blockchain technology works
AI: Blockchain is a distributed ledger technology that maintains a continuously growing list of records (blocks) linked using cryptography. Each block contains: 1) A hash of the previous block, 2) Transaction data, 3) A timestamp. This creates an immutable chain where altering any block would require changing all subsequent blocks, making it highly secure and transparent.

---

User: How can I improve my Python code performance?
AI: Python performance can be improved through: 1) Use built-in functions and libraries (they're optimized in C), 2) Avoid global variables, 3) Use list comprehensions instead of loops, 4) Profile your code to find bottlenecks, 5) Consider using NumPy for numerical operations, 6) Use generators for memory efficiency, 7) Cache expensive computations.
"""

    with open("sample_conversations.txt", "w") as f:
        f.write(sample_conversations)

    print("📝 Created sample_conversations.txt for testing")


def main():
    print("🌟 UATP Real-World Data Capture")
    print("=" * 50)

    capture = UATProadDataCapture()

    print("\nChoose capture method:")
    print("1. Interactive capture (paste conversations manually)")
    print("2. Batch import from file")
    print("3. Clipboard monitor (auto-capture copied conversations)")
    print("4. Create sample conversations file")
    print("5. Show current stats")

    choice = input("\nSelect option (1-5): ").strip()

    if choice == "1":
        capture.interactive_capture()
    elif choice == "2":
        filepath = input("Enter file path (or 'sample_conversations.txt'): ").strip()
        if not filepath:
            filepath = "sample_conversations.txt"
        capture.batch_capture_from_file(filepath)
    elif choice == "3":
        capture.clipboard_monitor()
    elif choice == "4":
        create_sample_conversations_file()
    elif choice == "5":
        capture.show_capture_stats()
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
