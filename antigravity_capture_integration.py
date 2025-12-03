#!/usr/bin/env python3
"""
Antigravity → UATP Integration
Automatically captures Antigravity conversations and agent artifacts to UATP
"""

import asyncio
import json
import time
import os
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import requests
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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
    """Background service to capture Antigravity conversations to UATP."""

    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.api_key = "test-api-key"
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        # Antigravity paths
        self.antigravity_home = Path.home() / ".gemini" / "antigravity"
        self.conversations_dir = self.antigravity_home / "conversations"
        self.brain_dir = self.antigravity_home / "brain"

        # Tracking
        self.captured_sessions = set()
        self.last_conversation_hash = None

        logger.info("🤖 Antigravity → UATP Capture Service initialized")
        logger.info(f"   Monitoring: {self.antigravity_home}")

    def get_active_sessions(self):
        """Get list of active Antigravity brain sessions."""
        if not self.brain_dir.exists():
            return []

        sessions = []
        for session_dir in self.brain_dir.iterdir():
            if session_dir.is_dir() and not session_dir.name.startswith("."):
                sessions.append(session_dir)
        return sessions

    def capture_session_artifacts(self, session_dir: Path):
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
                with open(artifact_path, "r") as f:
                    artifacts[artifact_name] = f.read()

                # Also read metadata
                metadata_path = session_dir / f"{artifact_name}.metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, "r") as f:
                        artifacts[f"{artifact_name}_metadata"] = json.load(f)

        if not artifacts:
            return None

        # Generate unique capsule ID
        import secrets

        unique_id = (
            f"antigravity_{session_id[:8]}_{int(time.time())}_{secrets.token_hex(4)}"
        )

        # Create capsule payload
        capsule_data = {
            "capsule_id": unique_id,
            "type": "conversation",
            "agent_id": "google-antigravity-gemini-3",
            "content": {
                "conversation_summary": self._generate_summary(artifacts),
                "session_id": session_id,
                "platform": "google_antigravity",
                "artifacts": artifacts,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        # Submit to UATP
        try:
            response = requests.post(
                f"{self.api_base}/capsules",
                headers=self.headers,
                json=capsule_data,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                self.captured_sessions.add(session_id)
                capsule_id = response.json().get("capsule_id", "unknown")
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

    def capture_conversation_protobuf(self, pb_file: Path):
        """Capture conversation from protobuf file."""
        session_id = pb_file.stem

        # Check if already captured
        file_hash = hashlib.md5(pb_file.read_bytes()).hexdigest()
        if file_hash == self.last_conversation_hash:
            return None

        self.last_conversation_hash = file_hash

        # For now, just log that we detected it
        # Full protobuf parsing would require the .proto schema
        logger.info(f"📡 Detected conversation update: {session_id[:8]}...")

        # Trigger artifact capture for this session
        session_dir = self.brain_dir / session_id
        if session_dir.exists():
            return self.capture_session_artifacts(session_dir)

        return None

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

    def __init__(self, capture_service):
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
    logger.info("=" * 60)

    # Initialize capture service
    service = AntigravityCaptureService()

    # Check if Antigravity is installed
    if not service.antigravity_home.exists():
        logger.error("❌ Antigravity not found!")
        logger.error(f"   Expected location: {service.antigravity_home}")
        logger.error("   Please install Antigravity first.")
        return

    logger.info(f"✅ Found Antigravity installation")
    logger.info(f"   Brain dir: {service.brain_dir}")
    logger.info(f"   Conversations dir: {service.conversations_dir}")

    # Check if API is accessible
    try:
        response = requests.get(f"{service.api_base}/health", timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ UATP API server accessible at {service.api_base}")
        else:
            logger.warning(f"⚠️  UATP API returned status {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Cannot reach UATP API at {service.api_base}")
        logger.error(f"   Error: {e}")
        logger.error("   Please start the API server with: python3 run.py")
        return

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
        logger.info("   Press Ctrl+C to stop")
        logger.info("")

        # Run monitor loop
        service.monitor_sessions()

    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        observer.stop()

    observer.join()
    logger.info("✅ Service stopped")


if __name__ == "__main__":
    main()
