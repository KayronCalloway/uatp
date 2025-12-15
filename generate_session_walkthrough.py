#!/usr/bin/env python3
"""
Automatic Session Walkthrough Generator
Creates markdown documentation for each session to avoid token waste on recaps
"""

import asyncio
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Load environment
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))


class WalkthroughGenerator:
    """Generates walkthrough documentation from captured sessions."""

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "live_capture.db")
        self.walkthrough_dir = Path.home() / ".uatp" / "session_walkthroughs"
        self.walkthrough_dir.mkdir(parents=True, exist_ok=True)

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages from a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT role, content, token_count, model_info, timestamp
            FROM capture_messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """,
            (session_id,),
        )

        messages = []
        for row in cursor.fetchall():
            messages.append(
                {
                    "role": row[0],
                    "content": row[1],
                    "token_count": row[2],
                    "model_info": row[3],
                    "timestamp": row[4],
                }
            )

        conn.close()
        return messages

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session metadata."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT user_id, platform, start_time, end_time, message_count,
                   significance_score, total_tokens, topics, capsule_created
            FROM capture_sessions
            WHERE session_id = ?
        """,
            (session_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "session_id": session_id,
            "user_id": row[0],
            "platform": row[1],
            "start_time": row[2],
            "end_time": row[3],
            "message_count": row[4],
            "significance_score": row[5],
            "total_tokens": row[6],
            "topics": json.loads(row[7]) if row[7] else [],
            "capsule_created": bool(row[8]),
        }

    def extract_accomplishments(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract key accomplishments from messages."""
        accomplishments = []

        for msg in messages:
            content = msg["content"].lower()

            # Look for completion indicators
            if msg["role"] == "assistant":
                # Check for success indicators
                if any(
                    indicator in content
                    for indicator in [
                        "✅",
                        "completed",
                        "success",
                        "created",
                        "implemented",
                        "fixed",
                        "deployed",
                        "updated",
                        "added",
                        "built",
                    ]
                ):
                    # Extract first meaningful sentence
                    lines = msg["content"].split("\n")
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 20 and len(line) < 200:
                            if any(
                                ind in line.lower()
                                for ind in [
                                    "✅",
                                    "completed",
                                    "created",
                                    "implemented",
                                    "fixed",
                                ]
                            ):
                                accomplishments.append(line)
                                break

        return accomplishments[:10]  # Limit to top 10

    def extract_key_decisions(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract important decisions made during the session."""
        decisions = []

        for msg in messages:
            content = msg["content"].lower()

            # Look for decision indicators
            if any(
                indicator in content
                for indicator in [
                    "decided",
                    "chose",
                    "selected",
                    "opted for",
                    "approach:",
                    "strategy:",
                    "using",
                    "will use",
                ]
            ):
                # Extract the decision
                lines = msg["content"].split("\n")
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 30 and len(line) < 200:
                        if any(
                            ind in line.lower()
                            for ind in ["decided", "chose", "approach", "using"]
                        ):
                            decisions.append(line)
                            break

        return decisions[:5]  # Limit to top 5

    def extract_next_steps(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract next steps or TODO items."""
        next_steps = []

        # Look in the last few messages
        for msg in messages[-5:]:
            content = msg["content"]

            # Look for TODO indicators
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if any(
                    indicator in line.lower()
                    for indicator in [
                        "todo",
                        "next:",
                        "next steps",
                        "- [ ]",
                        "need to",
                        "should",
                        "will need",
                        "remaining",
                    ]
                ):
                    if len(line) > 20 and len(line) < 200:
                        next_steps.append(line)

        return next_steps[:7]  # Limit to top 7

    def generate_walkthrough_markdown(self, session_id: str) -> str:
        """Generate walkthrough markdown for a session."""

        session_info = self.get_session_info(session_id)
        if not session_info:
            return f"# Session {session_id}\n\n❌ Session not found in database."

        messages = self.get_session_messages(session_id)

        # Calculate duration
        duration = "Unknown"
        if session_info["end_time"] and session_info["start_time"]:
            start = datetime.fromisoformat(session_info["start_time"])
            end = datetime.fromisoformat(session_info["end_time"])
            duration_seconds = (end - start).total_seconds()
            duration_minutes = int(duration_seconds / 60)
            duration = f"{duration_minutes} minutes"

        # Build markdown
        md = f"""# Session Walkthrough
**Session ID:** `{session_id[:16]}...`
**Platform:** {session_info['platform']}
**Date:** {session_info['start_time'][:10]}
**Duration:** {duration}
**Messages:** {session_info['message_count']}
**Tokens Used:** ~{session_info['total_tokens']}
**Significance:** {session_info['significance_score']:.2f}
**Capsule Created:** {'✅ Yes' if session_info['capsule_created'] else '❌ No'}

---

## 📋 Topics Covered
{chr(10).join(f'- {topic}' for topic in session_info['topics']) if session_info['topics'] else '- General discussion'}

---

## ✅ Key Accomplishments
"""

        accomplishments = self.extract_accomplishments(messages)
        if accomplishments:
            for acc in accomplishments:
                md += f"\n- {acc}"
        else:
            md += "\n- No specific accomplishments extracted"

        md += "\n\n---\n\n## 🎯 Important Decisions\n"

        decisions = self.extract_key_decisions(messages)
        if decisions:
            for dec in decisions:
                md += f"\n- {dec}"
        else:
            md += "\n- No major decisions recorded"

        md += "\n\n---\n\n## 📝 Next Steps / TODO\n"

        next_steps = self.extract_next_steps(messages)
        if next_steps:
            for step in next_steps:
                md += f"\n- {step}"
        else:
            md += "\n- No pending tasks identified"

        md += "\n\n---\n\n## 💬 Conversation Summary\n\n"
        md += (
            f"Total exchanges: {len([m for m in messages if m['role'] == 'user'])}\n\n"
        )

        # Add brief summary of conversation flow
        md += "### Flow:\n"
        for i, msg in enumerate(messages[:10], 1):  # First 10 messages
            role_emoji = "👤" if msg["role"] == "user" else "🤖"
            preview = msg["content"][:100].replace("\n", " ")
            md += f"{i}. {role_emoji} {preview}...\n"

        if len(messages) > 10:
            md += f"\n... and {len(messages) - 10} more messages\n"

        md += "\n\n---\n\n## 🔗 References\n\n"
        md += "- **Session Database:** `live_capture.db`\n"
        md += f"- **Session ID:** `{session_id}`\n"
        md += f"- **Timestamp:** `{datetime.now(timezone.utc).isoformat()}`\n"

        return md

    def save_walkthrough(self, session_id: str, content: str) -> Path:
        """Save walkthrough to file."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"session_{timestamp}_{session_id[:8]}.md"
        filepath = self.walkthrough_dir / filename

        with open(filepath, "w") as f:
            f.write(content)

        return filepath

    def get_latest_walkthrough(self) -> Optional[Path]:
        """Get the most recent walkthrough file."""
        walkthroughs = sorted(self.walkthrough_dir.glob("session_*.md"), reverse=True)
        return walkthroughs[0] if walkthroughs else None


async def generate_walkthrough_for_session(session_id: Optional[str] = None):
    """Generate walkthrough for a session."""

    generator = WalkthroughGenerator()

    # If no session ID provided, use the active session
    if not session_id:
        session_file = Path("/tmp/claude_code_active_session.json")
        if session_file.exists():
            with open(session_file) as f:
                session_data = json.load(f)
                session_id = session_data.get("session_id")

    if not session_id:
        print("❌ No active session found")
        print("   Usage: python generate_session_walkthrough.py [session_id]")
        return

    print(f"📝 Generating walkthrough for session: {session_id[:16]}...")

    # Generate walkthrough
    content = generator.generate_walkthrough_markdown(session_id)

    # Save to file
    filepath = generator.save_walkthrough(session_id, content)

    print(f"✅ Walkthrough saved: {filepath}")
    print(f"   Location: {generator.walkthrough_dir}")
    print()
    print("📖 To view:")
    print(f"   cat {filepath}")
    print()
    print("💡 Tip: Reference this at the start of your next session to avoid recap!")

    return filepath


async def show_latest_walkthrough():
    """Show the latest walkthrough."""
    generator = WalkthroughGenerator()
    latest = generator.get_latest_walkthrough()

    if not latest:
        print("❌ No walkthroughs found")
        return

    print(f"📖 Latest Walkthrough: {latest.name}")
    print("=" * 60)
    with open(latest) as f:
        print(f.read())


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--latest":
            asyncio.run(show_latest_walkthrough())
        else:
            asyncio.run(generate_walkthrough_for_session(sys.argv[1]))
    else:
        asyncio.run(generate_walkthrough_for_session())
