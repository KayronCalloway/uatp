#!/usr/bin/env python3
"""
Antigravity → UATP Integration v2 (Enhanced)
=============================================

Key improvements over v1:
1. Captures ALL .resolved files (full conversation evolution)
2. Proper de-duplication using database, not in-memory set
3. Tracks artifact versions via metadata
4. Creates rich capsules with version history
5. Per-session hash tracking (not single global hash)
6. Real content-based hashing for verification
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

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import UATP v7 crypto for real Ed25519 signing
try:
    from src.security.uatp_crypto_v7 import UATPCryptoV7

    CRYPTO_AVAILABLE = True
except ImportError:
    UATPCryptoV7 = None  # type: ignore
    CRYPTO_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(__file__), "antigravity_capture_v2.log")
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class AntigravityCaptureV2:
    """Enhanced Antigravity capture with full artifact history."""

    def __init__(self):
        self.api_base = os.getenv("UATP_API_URL", "http://localhost:8000")
        self.api_key = os.getenv("UATP_API_KEY", "test-api-key")
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        # Antigravity paths
        self.antigravity_home = Path.home() / ".gemini" / "antigravity"
        self.brain_dir = self.antigravity_home / "brain"

        # Database path (same as Claude Code)
        self.db_path = os.path.join(os.path.dirname(__file__), "live_capture.db")

        # Per-session content hashes for change detection
        self.session_hashes: Dict[str, str] = {}

        # Initialize cryptographic signing
        self.crypto: Optional[UATPCryptoV7] = None
        if CRYPTO_AVAILABLE:
            try:
                self.crypto = UATPCryptoV7(
                    key_dir=".uatp_keys", signer_id="antigravity_capture_v2"
                )
                logger.info("🔐 Ed25519 cryptographic signing enabled")
            except Exception as e:
                logger.warning(f"⚠️ Crypto initialization failed: {e}")
        else:
            logger.warning(
                "⚠️ Crypto module not available - using hash-only verification"
            )

        self.init_database()
        self._load_existing_hashes()

        logger.info("🤖 Antigravity Capture v2 initialized")
        logger.info(f"   Brain dir: {self.brain_dir}")
        logger.info(f"   Database: {self.db_path}")

    def init_database(self):
        """Initialize database with enhanced schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Existing tables (compatible with v1)
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
                content_hash TEXT,
                last_captured_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS capture_artifacts (
                artifact_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                artifact_path TEXT NOT NULL,
                content TEXT,
                metadata TEXT,
                version INTEGER DEFAULT 0,
                content_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES capture_sessions (session_id)
            )
        """
        )

        # New: capsule tracking table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS captured_capsules (
                capsule_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES capture_sessions (session_id)
            )
        """
        )

        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")

    def _load_existing_hashes(self):
        """Load existing session hashes from database for de-duplication."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT session_id, content_hash FROM capture_sessions
                WHERE platform = 'google_antigravity' AND content_hash IS NOT NULL
            """
            )
            for row in cursor.fetchall():
                self.session_hashes[row[0]] = row[1]
            conn.close()
            logger.info(f"📚 Loaded {len(self.session_hashes)} existing session hashes")
        except Exception as e:
            logger.warning(f"Could not load existing hashes: {e}")

    def _compute_session_hash(self, session_dir: Path) -> str:
        """Compute hash of all artifacts in a session for change detection."""
        content_parts = []

        # Get all artifact files sorted by name for consistent hashing
        artifact_files = sorted(session_dir.glob("*.md")) + sorted(
            session_dir.glob("*.resolved*")
        )

        for artifact_path in artifact_files:
            try:
                content = artifact_path.read_text()
                content_parts.append(f"{artifact_path.name}:{content}")
            except Exception:
                pass

        combined = "\n".join(content_parts)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    def _was_already_captured(self, session_id: str, content_hash: str) -> bool:
        """Check if this exact content was already captured."""
        # Check in-memory cache first
        if self.session_hashes.get(session_id) == content_hash:
            return True

        # Check database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 1 FROM captured_capsules
                WHERE session_id = ? AND content_hash = ?
            """,
                (session_id, content_hash),
            )
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except Exception:
            return False

    def _get_all_artifacts(self, session_dir: Path) -> Dict[str, Any]:
        """Get all artifacts including resolved versions with metadata."""
        artifacts = {
            "base_files": {},
            "resolved_versions": {},
            "metadata": {},
            "version_history": [],
        }

        # Base artifact files
        for artifact_name in [
            "task.md",
            "walkthrough.md",
            "action_items.md",
            "implementation_plan.md",
            "explanation.md",
            "daily_audit.md",
        ]:
            artifact_path = session_dir / artifact_name
            if artifact_path.exists():
                try:
                    artifacts["base_files"][artifact_name] = artifact_path.read_text()
                except Exception as e:
                    logger.warning(f"Could not read {artifact_path}: {e}")

            # Metadata
            metadata_path = session_dir / f"{artifact_name}.metadata.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path) as f:
                        meta = json.load(f)
                        artifacts["metadata"][artifact_name] = meta
                        artifacts["version_history"].append(
                            {
                                "artifact": artifact_name,
                                "version": meta.get("version", "0"),
                                "summary": meta.get("summary", ""),
                                "updated_at": meta.get("updatedAt", ""),
                            }
                        )
                except Exception as e:
                    logger.warning(f"Could not read metadata {metadata_path}: {e}")

        # Resolved versions (conversation evolution)
        for resolved_path in sorted(session_dir.glob("*.resolved*")):
            try:
                base_name = resolved_path.name.split(".resolved")[0]
                version = resolved_path.name.split(".resolved")[-1].lstrip(".")
                if version == "":
                    version = "latest"

                if base_name not in artifacts["resolved_versions"]:
                    artifacts["resolved_versions"][base_name] = {}

                artifacts["resolved_versions"][base_name][version] = (
                    resolved_path.read_text()
                )
            except Exception as e:
                logger.warning(f"Could not read resolved file {resolved_path}: {e}")

        return artifacts

    def _extract_reasoning_steps(self, artifacts: Dict[str, Any]) -> List[Dict]:
        """Extract reasoning steps from artifact content and version history."""
        steps = []
        step_num = 1

        # Add version history as reasoning steps
        for hist in sorted(
            artifacts.get("version_history", []), key=lambda x: x.get("updated_at", "")
        ):
            if hist.get("summary"):
                steps.append(
                    {
                        "step_id": step_num,
                        "operation": "artifact_update",
                        "reasoning": hist["summary"],
                        "artifact": hist["artifact"],
                        "version": hist["version"],
                        "timestamp": hist["updated_at"],
                        "confidence": 0.85,
                    }
                )
                step_num += 1

        # Extract task items as reasoning steps
        task_content = artifacts.get("base_files", {}).get("task.md", "")
        for line in task_content.split("\n"):
            line = line.strip()
            if line.startswith("- [x]"):
                # Completed task
                task_text = line.replace("- [x]", "").split("<!--")[0].strip()
                steps.append(
                    {
                        "step_id": step_num,
                        "operation": "task_completed",
                        "reasoning": task_text,
                        "confidence": 0.95,
                        "status": "completed",
                    }
                )
                step_num += 1
            elif line.startswith("- [/]"):
                # In-progress task
                task_text = line.replace("- [/]", "").split("<!--")[0].strip()
                steps.append(
                    {
                        "step_id": step_num,
                        "operation": "task_in_progress",
                        "reasoning": task_text,
                        "confidence": 0.70,
                        "status": "in_progress",
                    }
                )
                step_num += 1
            elif line.startswith("- [ ]"):
                # Pending task
                task_text = line.replace("- [ ]", "").split("<!--")[0].strip()
                steps.append(
                    {
                        "step_id": step_num,
                        "operation": "task_pending",
                        "reasoning": task_text,
                        "confidence": 0.50,
                        "status": "pending",
                    }
                )
                step_num += 1

        return steps

    def capture_session(self, session_dir: Path) -> Optional[str]:
        """Capture a session with full artifact history."""
        session_id = session_dir.name

        # Compute content hash for de-duplication
        content_hash = self._compute_session_hash(session_dir)

        # Check if already captured with this exact content
        if self._was_already_captured(session_id, content_hash):
            logger.debug(f"⏭️  Session {session_id[:8]} unchanged, skipping")
            return None

        # Get all artifacts
        artifacts = self._get_all_artifacts(session_dir)

        if not artifacts["base_files"] and not artifacts["resolved_versions"]:
            logger.debug(f"⏭️  Session {session_id[:8]} has no artifacts")
            return None

        logger.info(f"📦 Capturing session {session_id[:8]}...")
        logger.info(f"   Base files: {len(artifacts['base_files'])}")
        logger.info(
            f"   Resolved versions: {sum(len(v) for v in artifacts['resolved_versions'].values())}"
        )

        # Extract reasoning steps
        reasoning_steps = self._extract_reasoning_steps(artifacts)

        # Get task title
        task_content = artifacts.get("base_files", {}).get("task.md", "")
        first_line = (
            task_content.split("\n")[0].replace("#", "").strip()
            if task_content
            else "Antigravity session"
        )

        # Calculate overall confidence based on completed tasks
        completed = len([s for s in reasoning_steps if s.get("status") == "completed"])
        total_tasks = len(
            [
                s
                for s in reasoning_steps
                if s.get("status") in ["completed", "in_progress", "pending"]
            ]
        )
        overall_confidence = completed / total_tasks if total_tasks > 0 else 0.7

        # Create capsule
        capsule_id = f"antigravity_{session_id[:8]}_{int(time.time())}"

        capsule_data = {
            "capsule_id": capsule_id,
            "type": "reasoning_trace",
            "version": "7.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "prompt": first_line,
                "reasoning_steps": reasoning_steps,
                "final_answer": f"Session with {len(reasoning_steps)} tracked steps, {completed}/{total_tasks} tasks completed",
                "confidence": round(overall_confidence, 3),
                "model_used": "gemini-2.5-pro",
                "created_by": "kay",
                "session_metadata": {
                    "session_id": session_id,
                    "platform": "google_antigravity",
                    "artifact_count": len(artifacts["base_files"]),
                    "version_count": sum(
                        len(v) for v in artifacts["resolved_versions"].values()
                    ),
                    "capture_method": "antigravity_v2",
                },
                "artifacts_summary": {
                    name: content[:500] + "..." if len(content) > 500 else content
                    for name, content in artifacts["base_files"].items()
                },
            },
        }

        # Add cryptographic verification
        if self.crypto and self.crypto.enabled:
            # Real Ed25519 signature
            verification = self.crypto.sign_capsule(capsule_data)
            capsule_data["verification"] = verification
            logger.debug(
                f"🔐 Capsule signed with Ed25519: {verification.get('signature', '')[:32]}..."
            )
        else:
            # Fallback to hash-only verification
            capsule_data["verification"] = {
                "signer": "antigravity_capture_v2",
                "verify_key": None,
                "hash": f"sha256:{content_hash}",
                "signature": None,
                "merkle_root": None,
            }

        # Submit to API
        try:
            response = requests.post(
                f"{self.api_base}/capsules",
                headers=self.headers,
                json=capsule_data,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                # Update tracking
                self.session_hashes[session_id] = content_hash
                self._record_capture(session_id, capsule_id, content_hash)

                logger.info(f"✅ Captured: {capsule_id}")
                logger.info(
                    f"   Steps: {len(reasoning_steps)}, Confidence: {overall_confidence:.2f}"
                )
                return capsule_id
            else:
                logger.error(
                    f"❌ API error: {response.status_code} - {response.text[:200]}"
                )
                return None

        except Exception as e:
            logger.error(f"❌ Capture failed: {e}")
            return None

    def _record_capture(self, session_id: str, capsule_id: str, content_hash: str):
        """Record successful capture in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Update session
            cursor.execute(
                """
                INSERT OR REPLACE INTO capture_sessions
                (session_id, user_id, platform, start_time, content_hash, last_captured_at, capsule_created)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    "kay",
                    "google_antigravity",
                    datetime.now(timezone.utc).isoformat(),
                    content_hash,
                    datetime.now(timezone.utc).isoformat(),
                    True,
                ),
            )

            # Record capsule
            cursor.execute(
                """
                INSERT OR REPLACE INTO captured_capsules
                (capsule_id, session_id, content_hash)
                VALUES (?, ?, ?)
            """,
                (capsule_id, session_id, content_hash),
            )

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to record capture: {e}")

    def scan_all_sessions(self):
        """Scan and capture all sessions with changes."""
        if not self.brain_dir.exists():
            logger.warning(f"Brain directory not found: {self.brain_dir}")
            return

        captured = 0
        skipped = 0

        for session_dir in self.brain_dir.iterdir():
            if session_dir.is_dir() and not session_dir.name.startswith("."):
                result = self.capture_session(session_dir)
                if result:
                    captured += 1
                else:
                    skipped += 1

        logger.info(f"📊 Scan complete: {captured} captured, {skipped} unchanged")

    def monitor(self, interval: int = 60):
        """Monitor for changes with configurable interval."""
        logger.info(f"🔍 Starting monitor (interval: {interval}s)...")

        while True:
            try:
                self.scan_all_sessions()
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("🛑 Monitor stopped")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(interval * 2)


class ArtifactWatcher(FileSystemEventHandler):
    """Watch for artifact file changes."""

    def __init__(self, capture_service: AntigravityCaptureV2):
        self.service = capture_service
        self.last_event_time = 0
        self.debounce_seconds = 5  # Wait for multiple rapid changes

    def on_modified(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)

        # Only care about .md and .resolved files
        if not (path.suffix == ".md" or ".resolved" in path.name):
            return

        # Debounce rapid changes
        now = time.time()
        if now - self.last_event_time < self.debounce_seconds:
            return
        self.last_event_time = now

        # Find session directory
        session_dir = path.parent
        if session_dir.parent.name == "brain":
            logger.info(f"📝 Artifact changed: {path.name}")
            self.service.capture_session(session_dir)


def main():
    logger.info("=" * 60)
    logger.info("🤖 Antigravity Capture v2 - Enhanced Edition")
    logger.info("   Full artifact history + proper de-duplication")
    logger.info("=" * 60)

    service = AntigravityCaptureV2()

    if not service.brain_dir.exists():
        logger.error(f"❌ Antigravity brain directory not found: {service.brain_dir}")
        return

    # Check API
    try:
        response = requests.get(f"{service.api_base}/health", timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ API accessible at {service.api_base}")
    except Exception as e:
        logger.warning(f"⚠️  API not reachable: {e}")

    # Initial scan
    logger.info("📡 Performing initial scan...")
    service.scan_all_sessions()

    # Set up file watcher
    observer = Observer()
    watcher = ArtifactWatcher(service)
    observer.schedule(watcher, str(service.brain_dir), recursive=True)
    observer.start()

    logger.info("👁️  Watching for artifact changes...")
    logger.info("   Press Ctrl+C to stop")

    try:
        service.monitor(interval=60)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()

    logger.info("✅ Capture service stopped")


if __name__ == "__main__":
    main()
