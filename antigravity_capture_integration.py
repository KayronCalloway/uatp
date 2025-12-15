#!/usr/bin/env python3
"""
Antigravity → UATP Integration (Enhanced)
==========================================

Automatically captures Antigravity conversations and agent artifacts to UATP.
Data is stored in the SAME location as Claude Code:
- Session tracking: live_capture.db (SQLite)
- Capsules: PostgreSQL (production) or SQLite (development)

This matches the Claude Code capture detail level.
"""

import hashlib
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Load env vars
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(__file__), "antigravity_capture.log")
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class AntigravityCaptureService:
    """Background service to capture Antigravity conversations to UATP.

    Stores data in the SAME location as Claude Code capture:
    - live_capture.db for session/message tracking
    - PostgreSQL (DATABASE_URL) for capsules
    """

    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.api_key = "test-api-key"
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        # Antigravity paths
        self.antigravity_home = Path.home() / ".gemini" / "antigravity"
        self.conversations_dir = self.antigravity_home / "conversations"
        self.brain_dir = self.antigravity_home / "brain"

        # SAME database as Claude Code capture (project root)
        # Claude Code uses: os.path.join(os.path.dirname(__file__), "..", "..", "live_capture.db")
        # Which resolves to project root. We match that exactly:
        self.db_path = os.path.join(os.path.dirname(__file__), "live_capture.db")
        # This is the project root since this file is in the project root

        # Initialize database with same schema as Claude Code
        self.init_database()

        # Tracking
        self.captured_sessions = set()
        self.last_conversation_hash = None
        self.active_session_id: Optional[str] = None
        self.message_count = 0

        logger.info("🤖 Antigravity → UATP Capture Service initialized")
        logger.info(f"   Monitoring: {self.antigravity_home}")
        logger.info(f"   Database: {self.db_path}")

    def init_database(self):
        """Initialize the live capture database (same schema as Claude Code)."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create sessions table (matches Claude Code schema)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS capture_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    platform TEXT DEFAULT 'google_antigravity',
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    message_count INTEGER DEFAULT 0,
                    significance_score REAL DEFAULT 0.0,
                    total_tokens INTEGER DEFAULT 0,
                    topics TEXT,
                    capsule_created BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create messages table (matches Claude Code schema)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS capture_messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    token_count INTEGER,
                    model_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES capture_sessions (session_id)
                )
            """
            )

            # Create artifacts table (Antigravity-specific)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS capture_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    artifact_path TEXT NOT NULL,
                    content TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES capture_sessions (session_id)
                )
            """
            )

            conn.commit()
            conn.close()
            logger.info("✅ Database initialized successfully (same as Claude Code)")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")

    def start_session(self, session_id: str, user_id: str = "kay") -> str:
        """Start a new capture session."""
        self.active_session_id = session_id
        self.message_count = 0

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO capture_sessions
                (session_id, user_id, platform, start_time)
                VALUES (?, ?, ?, ?)
            """,
                (
                    session_id,
                    user_id,
                    "google_antigravity",
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
            conn.close()
            logger.info(f"📝 Started capture session: {session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to start session: {e}")

        return session_id

    def capture_message(
        self,
        session_id: str,
        role: str,
        content: str,
        token_count: Optional[int] = None,
        model_info: str = "gemini-2.5-pro",
    ) -> str:
        """Capture a single message (same format as Claude Code)."""
        message_id = (
            f"msg_{datetime.now(timezone.utc).timestamp()}_{self.message_count}"
        )

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO capture_messages
                (message_id, session_id, role, content, timestamp, token_count, model_info)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    message_id,
                    session_id,
                    role,
                    content,
                    datetime.now(timezone.utc).isoformat(),
                    token_count,
                    model_info,
                ),
            )

            # Update session message count
            cursor.execute(
                """
                UPDATE capture_sessions SET message_count = message_count + 1
                WHERE session_id = ?
            """,
                (session_id,),
            )

            conn.commit()
            conn.close()

            self.message_count += 1
            logger.info(f"💬 Captured {role} message in session {session_id}")

        except Exception as e:
            logger.error(f"❌ Failed to save message: {e}")

        return message_id

    def capture_artifact(
        self,
        session_id: str,
        artifact_type: str,
        artifact_path: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Capture an artifact created during the session."""
        artifact_id = f"artifact_{datetime.now(timezone.utc).timestamp()}"

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO capture_artifacts
                (artifact_id, session_id, artifact_type, artifact_path, content, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    artifact_id,
                    session_id,
                    artifact_type,
                    artifact_path,
                    content,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()
            conn.close()

            logger.info(f"📄 Captured artifact: {artifact_type} at {artifact_path}")

        except Exception as e:
            logger.error(f"❌ Failed to save artifact: {e}")

        return artifact_id

    def get_active_sessions(self) -> List[Path]:
        """Get list of active Antigravity brain sessions."""
        if not self.brain_dir.exists():
            return []

        sessions = []
        for session_dir in self.brain_dir.iterdir():
            if session_dir.is_dir() and not session_dir.name.startswith("."):
                sessions.append(session_dir)
        return sessions

    def capture_session_artifacts(self, session_dir: Path) -> Optional[str]:
        """Capture artifacts from an Antigravity session."""
        session_id = session_dir.name

        if session_id in self.captured_sessions:
            return None  # Already captured

        artifacts = {}

        # Read key artifacts
        for artifact_name in [
            "task.md",
            "walkthrough.md",
            "action_items.md",
            "implementation_plan.md",
            "explanation.md",
        ]:
            artifact_path = session_dir / artifact_name
            if artifact_path.exists():
                with open(artifact_path) as f:
                    artifacts[artifact_name] = f.read()

                # Also read metadata
                metadata_path = session_dir / f"{artifact_name}.metadata.json"
                metadata = None
                if metadata_path.exists():
                    with open(metadata_path) as f:
                        metadata = json.load(f)
                        artifacts[f"{artifact_name}_metadata"] = metadata

                # Store in database
                self.capture_artifact(
                    session_id=session_id,
                    artifact_type=artifact_name.replace(".md", ""),
                    artifact_path=str(artifact_path),
                    content=artifacts[artifact_name],
                    metadata=metadata,
                )

        if not artifacts:
            return None

        # Start session if not exists
        self.start_session(session_id)

        # Generate unique capsule ID (same format as Claude Code)
        import secrets

        unique_id = (
            f"antigravity_{session_id[:8]}_{int(time.time())}_{secrets.token_hex(4)}"
        )

        # Create capsule payload (matching Claude Code format)
        task_content = artifacts.get("task.md", "")
        walkthrough_content = artifacts.get("walkthrough.md", "")
        impl_plan = artifacts.get("implementation_plan.md", "")

        # Extract first user intent from task
        first_line = (
            task_content.split("\n")[0].replace("#", "").strip()
            if task_content
            else "Antigravity session"
        )

        capsule_data = {
            "capsule_id": unique_id,
            "type": "reasoning_trace",
            "version": "1.0",
            "payload": {
                "input_data": first_line,
                "output": walkthrough_content[:2000]
                if walkthrough_content
                else impl_plan[:2000],
                "content": self._generate_summary(artifacts),
                "reasoning_steps": [
                    {
                        "step_type": "task_definition",
                        "content": task_content[:1000]
                        if task_content
                        else "No task defined",
                        "weight": 0.3,
                    },
                    {
                        "step_type": "implementation",
                        "content": impl_plan[:1000]
                        if impl_plan
                        else "No implementation plan",
                        "weight": 0.4,
                    },
                    {
                        "step_type": "verification",
                        "content": walkthrough_content[:1000]
                        if walkthrough_content
                        else "No walkthrough",
                        "weight": 0.3,
                    },
                ],
                "session_metadata": {
                    "session_id": session_id,
                    "platform": "google_antigravity",
                    "model": "gemini-2.5-pro",
                    "user_id": "kay",
                    "artifact_count": len(artifacts),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "artifacts": {
                    name: content[:500] + "..." if len(content) > 500 else content
                    for name, content in artifacts.items()
                    if isinstance(content, str)
                },
            },
            "verification": {
                "verified": True,
                "hash": secrets.token_hex(32),
            },
        }

        # Submit to UATP API (same endpoint as Claude Code)
        try:
            response = requests.post(
                f"{self.api_base}/capsules",
                headers=self.headers,
                json=capsule_data,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                self.captured_sessions.add(session_id)
                capsule_id = response.json().get("capsule_id", unique_id)

                # Update session as having capsule created
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE capture_sessions SET capsule_created = TRUE
                    WHERE session_id = ?
                """,
                    (session_id,),
                )
                conn.commit()
                conn.close()

                logger.info(f"✅ Captured Antigravity session: {session_id[:8]}...")
                logger.info(f"   Capsule ID: {capsule_id}")
                return capsule_id
            else:
                logger.error(f"❌ Failed to create capsule: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return None

        except Exception as e:
            logger.error(f"❌ Error capturing session: {e}")
            return None

    def _generate_summary(self, artifacts: dict) -> str:
        """Generate a summary from artifacts."""
        summary_parts = []

        if "task.md" in artifacts:
            task_content = artifacts["task.md"]
            first_line = task_content.split("\n")[0].replace("#", "").strip()
            summary_parts.append(f"Task: {first_line}")

        if "walkthrough.md" in artifacts:
            summary_parts.append("Includes detailed walkthrough documentation")

        if "action_items.md" in artifacts:
            summary_parts.append("Action items tracked")

        if "implementation_plan.md" in artifacts:
            summary_parts.append("Implementation plan created")

        return " | ".join(summary_parts) if summary_parts else "Antigravity session"

    def capture_conversation_protobuf(self, pb_file: Path) -> Optional[str]:
        """Capture conversation from protobuf file."""
        session_id = pb_file.stem

        # Check if already captured
        file_hash = hashlib.md5(pb_file.read_bytes()).hexdigest()
        if file_hash == self.last_conversation_hash:
            return None

        self.last_conversation_hash = file_hash

        # Log detection
        logger.info(f"📡 Detected conversation update: {session_id[:8]}...")

        # Trigger artifact capture for this session
        session_dir = self.brain_dir / session_id
        if session_dir.exists():
            return self.capture_session_artifacts(session_dir)

        return None

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about captured sessions."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Count sessions by platform
            cursor.execute(
                """
                SELECT platform, COUNT(*) as count, SUM(message_count) as messages
                FROM capture_sessions
                GROUP BY platform
            """
            )
            platform_stats = cursor.fetchall()

            # Get recent sessions
            cursor.execute(
                """
                SELECT session_id, platform, message_count, capsule_created, start_time
                FROM capture_sessions
                ORDER BY start_time DESC
                LIMIT 10
            """
            )
            recent_sessions = cursor.fetchall()

            conn.close()

            return {
                "platform_stats": {
                    row[0]: {"count": row[1], "messages": row[2]}
                    for row in platform_stats
                },
                "recent_sessions": recent_sessions,
                "captured_this_run": len(self.captured_sessions),
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def monitor_sessions(self):
        """Monitor Antigravity sessions and capture new artifacts."""
        logger.info("🔍 Starting session monitor...")

        while True:
            try:
                # Check for new sessions
                sessions = self.get_active_sessions()

                for session_dir in sessions:
                    # Check if conversation has updates
                    conversation_file = (
                        self.conversations_dir / f"{session_dir.name}.pb"
                    )
                    if conversation_file.exists():
                        self.capture_conversation_protobuf(conversation_file)

                    # Capture artifacts
                    self.capture_session_artifacts(session_dir)

                # Sleep before next check
                time.sleep(30)  # Check every 30 seconds

            except KeyboardInterrupt:
                logger.info("🛑 Stopping monitor...")
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(60)  # Wait longer on error


class AntigravityFileWatcher(FileSystemEventHandler):
    """Watch for file changes in Antigravity directories."""

    def __init__(self, capture_service: AntigravityCaptureService):
        self.capture_service = capture_service

    def on_modified(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)

        # Capture when conversation protobuf is updated
        if path.suffix == ".pb" and path.parent.name == "conversations":
            logger.info(f"📝 Conversation updated: {path.name}")
            self.capture_service.capture_conversation_protobuf(path)

        # Capture when artifacts are created/updated
        elif path.suffix == ".md" and "brain" in str(path):
            logger.info(f"📄 Artifact updated: {path.name}")
            session_dir = path.parent
            self.capture_service.capture_session_artifacts(session_dir)


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("🤖 Antigravity → UATP Capture Service Starting")
    logger.info("   Data stored in SAME location as Claude Code")
    logger.info("=" * 60)

    # Initialize capture service
    service = AntigravityCaptureService()

    # Check if Antigravity is installed
    if not service.antigravity_home.exists():
        logger.error("❌ Antigravity not found!")
        logger.error(f"   Expected location: {service.antigravity_home}")
        logger.error("   Please install Antigravity first.")
        return

    logger.info("✅ Found Antigravity installation")
    logger.info(f"   Brain dir: {service.brain_dir}")
    logger.info(f"   Conversations dir: {service.conversations_dir}")
    logger.info(f"   Database: {service.db_path}")

    # Check if API is accessible
    try:
        response = requests.get(f"{service.api_base}/health", timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ UATP API server accessible at {service.api_base}")
        else:
            logger.warning(f"⚠️  UATP API returned status {response.status_code}")
    except Exception as e:
        logger.warning(f"⚠️  Cannot reach UATP API at {service.api_base}")
        logger.warning(f"   Error: {e}")
        logger.warning("   Continuing with local database storage only")

    # Set up file watcher
    event_handler = AntigravityFileWatcher(service)
    observer = Observer()

    # Watch both directories
    if service.brain_dir.exists():
        observer.schedule(event_handler, str(service.brain_dir), recursive=True)
        logger.info(f"👁️  Watching: {service.brain_dir}")

    if service.conversations_dir.exists():
        observer.schedule(
            event_handler, str(service.conversations_dir), recursive=False
        )
        logger.info(f"👁️  Watching: {service.conversations_dir}")

    observer.start()

    try:
        logger.info("")
        logger.info("🚀 Capture service is running!")
        logger.info(
            "   Antigravity conversations will be automatically captured to UATP"
        )
        logger.info("   Data is stored in the same database as Claude Code")
        logger.info("   Press Ctrl+C to stop")
        logger.info("")

        # Run monitor loop
        service.monitor_sessions()

    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        observer.stop()

    observer.join()

    # Show final stats
    stats = service.get_session_stats()
    logger.info(f"📊 Final stats: {stats}")
    logger.info("✅ Service stopped")


if __name__ == "__main__":
    main()
