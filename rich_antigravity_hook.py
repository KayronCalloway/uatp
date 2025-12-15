#!/usr/bin/env python3
"""
Rich Antigravity Hook - Matches Claude Code's capture richness
Captures conversations + artifacts with uniform metadata structure
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Load environment
from dotenv import load_dotenv

load_dotenv()

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from src.live_capture.claude_code_capture import ClaudeCodeCapture
from src.live_capture.rich_capture_integration import RichCaptureEnhancer


class AntigravityRichCapture:
    """Rich capture for Antigravity matching Claude Code's detail level."""

    def __init__(self):
        self.capture = ClaudeCodeCapture()
        self.antigravity_home = Path.home() / ".gemini" / "antigravity"
        self.brain_dir = self.antigravity_home / "brain"
        self.conversations_dir = self.antigravity_home / "conversations"
        self.sessions_file = Path("/tmp/antigravity_active_sessions.json")

    def load_sessions(self) -> Dict[str, Any]:
        """Load active Antigravity sessions."""
        if self.sessions_file.exists():
            with open(self.sessions_file) as f:
                return json.load(f)
        return {}

    def save_sessions(self, sessions: Dict[str, Any]):
        """Save active sessions state."""
        with open(self.sessions_file, "w") as f:
            json.dump(sessions, f, indent=2)

    async def parse_brain_session(self, session_dir: Path) -> Dict[str, Any]:
        """Parse artifacts from Antigravity brain session."""
        artifacts = {}

        # Read all artifacts
        for artifact_name in [
            "task.md",
            "walkthrough.md",
            "implementation_plan.md",
            "action_items.md",
            "explanation.md",
        ]:
            artifact_path = session_dir / artifact_name
            if artifact_path.exists():
                with open(artifact_path) as f:
                    artifacts[artifact_name] = f.read()

        # Extract conversation-like data from task.md
        task_content = artifacts.get("task.md", "")
        user_queries = []

        # Simple heuristic: lines starting with "- [ ]" or "- [x]" are user intents
        for line in task_content.split("\n"):
            if line.strip().startswith("- ["):
                # Extract the query
                query = line.split("]", 1)[-1].strip()
                if query:
                    user_queries.append(query)

        return {
            "session_id": session_dir.name,
            "artifacts": artifacts,
            "user_queries": user_queries,
            "has_task": "task.md" in artifacts,
            "has_walkthrough": "walkthrough.md" in artifacts,
            "has_implementation": "implementation_plan.md" in artifacts,
        }

    async def capture_brain_session(self, session_dir: Path) -> Optional[str]:
        """Capture an Antigravity brain session with RICH metadata."""

        session_data = await self.parse_brain_session(session_dir)
        session_id = session_data["session_id"]

        # Load active sessions
        active_sessions = self.load_sessions()

        # Check if already captured
        if session_id in active_sessions and active_sessions[session_id].get(
            "capsule_created"
        ):
            print(f"ℹ️  Session {session_id[:8]}... already captured")
            return None

        # Start or resume UATP session
        uatp_session_id = active_sessions.get(session_id, {}).get("uatp_session_id")

        if not uatp_session_id:
            # New session
            uatp_session_id = await self.capture.start_session(user_id="kay")
            active_sessions[session_id] = {
                "uatp_session_id": uatp_session_id,
                "started": datetime.now(timezone.utc).isoformat(),
                "message_count": 0,
                "capsule_created": False,
            }

        # Capture user queries as messages
        task_content = session_data["artifacts"].get("task.md", "")
        walkthrough_content = session_data["artifacts"].get("walkthrough.md", "")
        impl_content = session_data["artifacts"].get("implementation_plan.md", "")

        # Extract main task (first heading or first line)
        main_task = "Antigravity session"
        if task_content:
            lines = task_content.split("\n")
            for line in lines:
                if line.strip().startswith("#"):
                    main_task = line.replace("#", "").strip()
                    break

        # Capture as user message
        await self.capture.capture_message(
            session_id=uatp_session_id,
            role="user",
            content=main_task,
            token_count=len(main_task.split()) * 1.3,
            model_info="gemini-2.5-pro",
        )
        active_sessions[session_id]["message_count"] += 1

        # Capture implementation plan as assistant response (planning phase)
        if impl_content:
            await self.capture.capture_message(
                session_id=uatp_session_id,
                role="assistant",
                content=f"[PLANNING] {impl_content[:1000]}",
                token_count=len(impl_content.split()) * 1.3,
                model_info="gemini-2.5-pro",
            )
            active_sessions[session_id]["message_count"] += 1

        # Capture walkthrough as assistant response (verification phase)
        if walkthrough_content:
            await self.capture.capture_message(
                session_id=uatp_session_id,
                role="assistant",
                content=f"[VERIFICATION] {walkthrough_content[:1000]}",
                token_count=len(walkthrough_content.split()) * 1.3,
                model_info="gemini-2.5-pro",
            )
            active_sessions[session_id]["message_count"] += 1

        # Store artifacts in database
        conn = __import__("sqlite3").connect(self.capture.db_path)
        cursor = conn.cursor()

        for artifact_name, content in session_data["artifacts"].items():
            artifact_id = f"artifact_{datetime.now(timezone.utc).timestamp()}"
            artifact_type = artifact_name.replace(".md", "")

            cursor.execute(
                """
                INSERT INTO capture_artifacts
                (artifact_id, session_id, artifact_type, artifact_path, content, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    uatp_session_id,
                    artifact_type,
                    str(session_dir / artifact_name),
                    content,
                    json.dumps(
                        {
                            "platform": "google_antigravity",
                            "original_session": session_id,
                            "artifact_size": len(content),
                            "captured_at": datetime.now(timezone.utc).isoformat(),
                        }
                    ),
                ),
            )

        conn.commit()
        conn.close()

        # End session and create RICH capsule
        session = await self.capture.end_session(uatp_session_id)

        if session:
            # Boost significance for artifact-rich Antigravity sessions
            artifact_count = len(session_data["artifacts"])
            session.significance_score = max(
                session.significance_score,
                min(artifact_count * 0.15, 0.9),  # 0.15 per artifact, max 0.9
            )

            # For Antigravity with artifacts, force capsule creation (bypass checks)
            # These are already valuable due to artifacts
            if artifact_count >= 2:
                # Create capsule directly - artifacts make it automatically valuable
                import asyncpg

                from src.core.config import DATABASE_URL

                try:
                    capsule_data = RichCaptureEnhancer.create_capsule_from_session_with_rich_metadata(
                        session=session, user_id="kay"
                    )

                    # Store to PostgreSQL
                    conn = await asyncpg.connect(
                        DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
                    )

                    await conn.execute(
                        """
                        INSERT INTO capsules (capsule_id, capsule_type, version, timestamp, status, verification, payload)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                        capsule_data["capsule_id"],
                        capsule_data["type"],
                        capsule_data["version"],
                        __import__("datetime").datetime.fromisoformat(
                            capsule_data["timestamp"].replace("Z", "+00:00")
                        ),
                        capsule_data["status"],
                        __import__("json").dumps(capsule_data["verification"]),
                        __import__("json").dumps(capsule_data["payload"]),
                    )

                    await conn.close()
                    capsule_id = capsule_data["capsule_id"]
                    session.capsule_created = True

                    print(
                        "✅ Forced capsule creation for artifact-rich Antigravity session"
                    )

                except Exception as e:
                    print(f"⚠️  PostgreSQL insert failed, trying standard method: {e}")
                    capsule_id = await self.capture.create_capsule_from_session(session)
            else:
                # Standard path for sessions without many artifacts
                capsule_id = await self.capture.create_capsule_from_session(session)

            if capsule_id:
                active_sessions[session_id]["capsule_created"] = True
                active_sessions[session_id]["capsule_id"] = capsule_id
                active_sessions[session_id]["completed"] = datetime.now(
                    timezone.utc
                ).isoformat()

                print(f"✨ Created RICH Antigravity capsule: {capsule_id}")
                print(f"   Session: {session_id[:8]}...")
                print(f"   Messages: {active_sessions[session_id]['message_count']}")
                print(f"   Artifacts: {len(session_data['artifacts'])}")
                print(f"   Significance: {session.significance_score:.2f}")
                print(f"   Topics: {', '.join(session.topics)}")

                self.save_sessions(active_sessions)
                return capsule_id
            else:
                print("ℹ️  Session didn't meet capsule criteria")
                print(f"   Messages: {len(session.messages)}")
                print(f"   Significance: {session.significance_score:.2f}")

        self.save_sessions(active_sessions)
        return None

    async def scan_and_capture_all(self):
        """Scan all Antigravity brain sessions and capture them."""

        if not self.brain_dir.exists():
            print(f"⚠️  Antigravity brain directory not found: {self.brain_dir}")
            return

        print("🤖 Scanning Antigravity brain sessions...")
        print(f"   Location: {self.brain_dir}")

        captured_count = 0
        skipped_count = 0

        for session_dir in self.brain_dir.iterdir():
            if session_dir.is_dir() and not session_dir.name.startswith("."):
                capsule_id = await self.capture_brain_session(session_dir)

                if capsule_id:
                    captured_count += 1
                else:
                    skipped_count += 1

        print("\n📊 Capture Summary:")
        print(f"   ✅ Captured: {captured_count}")
        print(f"   ⏭️  Skipped: {skipped_count}")


async def main():
    """Main entry point."""

    print("=" * 60)
    print("🤖 Antigravity Rich Capture")
    print("   Matching Claude Code's capture detail level")
    print("=" * 60)
    print()

    capture = AntigravityRichCapture()

    # Check if command line argument provided
    if len(sys.argv) > 1:
        session_path = Path(sys.argv[1])
        if session_path.exists():
            print(f"📂 Capturing specific session: {session_path.name}")
            await capture.capture_brain_session(session_path)
        else:
            print(f"❌ Session path not found: {session_path}")
    else:
        # Scan all sessions
        await capture.scan_and_capture_all()

    print()
    print("✅ Rich capture complete!")


if __name__ == "__main__":
    asyncio.run(main())
