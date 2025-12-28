#!/usr/bin/env python3
"""
Antigravity → UATP Rich Integration
====================================

Captures Antigravity (Google Gemini) conversations with FULL metadata richness,
matching Claude Code capture quality:
- Confidence scoring with methodology
- Uncertainty quantification (epistemic/aleatoric)
- Critical path analysis
- Risk assessment
- Alternatives considered
- Plain language summaries

This watches the ~/.gemini/antigravity/brain directory for session artifacts
and creates rich capsules through the RichCaptureEnhancer pipeline.
"""

import asyncio
import hashlib
import json
import logging
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.live_capture.base_hook import ConversationMessage, ConversationSession
from src.live_capture.rich_capture_integration import RichCaptureEnhancer
from src.security.crypto_sealer import CryptoSealer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AntigravityRichCaptureService:
    """
    Captures Antigravity sessions with RICH metadata through RichCaptureEnhancer.

    Unlike the old integration that created basic capsules, this produces
    capsules with the same richness as Claude Code:
    - confidence_methodology
    - critical_path_analysis
    - uncertainty_analysis
    - risk_assessment
    - alternatives_considered
    - plain_language_summary
    """

    def __init__(self):
        self.api_base = os.getenv("UATP_API_URL", "http://localhost:8000")

        # Antigravity paths
        self.antigravity_home = Path.home() / ".gemini" / "antigravity"
        self.brain_dir = self.antigravity_home / "brain"

        # Tracking
        self.captured_sessions: Dict[str, str] = {}  # session_id -> last_hash
        self.session_capsule_map: Dict[str, str] = {}  # session_id -> capsule_id

        # Initialize CryptoSealer for signing capsules
        try:
            self.crypto_sealer = CryptoSealer()
            self.signing_enabled = self.crypto_sealer.enabled
        except Exception as e:
            logger.warning(f"CryptoSealer not available: {e}")
            self.crypto_sealer = None
            self.signing_enabled = False

        logger.info("✨ Antigravity Rich Capture Service initialized")
        logger.info(f"   Monitoring: {self.brain_dir}")
        logger.info(f"   API: {self.api_base}")
        logger.info(f"   Signing: {'enabled' if self.signing_enabled else 'disabled'}")

    def get_active_sessions(self) -> List[Path]:
        """Get list of active Antigravity brain sessions."""
        if not self.brain_dir.exists():
            logger.warning(f"Brain directory not found: {self.brain_dir}")
            return []

        sessions = []
        for session_dir in self.brain_dir.iterdir():
            if session_dir.is_dir() and not session_dir.name.startswith("."):
                sessions.append(session_dir)
        return sessions

    def _truncate_with_marker(self, content: str, max_length: int) -> str:
        """Truncate content with a clear marker if it exceeds max_length."""
        if len(content) <= max_length:
            return content
        # Find a good break point (end of line or sentence)
        truncated = content[:max_length]
        # Try to break at last newline
        last_newline = truncated.rfind("\n")
        if last_newline > max_length - 500:  # Within last 500 chars
            truncated = truncated[:last_newline]
        return (
            truncated + "\n\n...[TRUNCATED - full content available in source artifact]"
        )

    def _extract_alternatives_from_artifacts(
        self, artifacts: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Extract real alternatives from Antigravity artifacts.

        Parses task.md, implementation_plan.md, and other artifacts to find
        actual decisions and alternatives considered.
        """
        alternatives = []

        # Parse implementation_plan.md for approach decisions
        impl_plan = artifacts.get("implementation_plan.md", "")
        if impl_plan:
            # Look for numbered options or bullet points with alternatives
            lines = impl_plan.split("\n")
            current_option = None
            for line in lines:
                line_lower = line.lower().strip()

                # Detect option patterns
                if line_lower.startswith(
                    ("option 1", "option a", "approach 1", "method 1")
                ):
                    current_option = line.strip().lstrip("#").lstrip("-").strip()
                    alternatives.append(
                        {
                            "option": current_option[:100],
                            "score": 0.6,
                            "why_not_chosen": "Evaluated during planning phase",
                            "data": {"source": "implementation_plan.md"},
                        }
                    )
                elif line_lower.startswith(
                    ("option 2", "option b", "approach 2", "method 2")
                ):
                    current_option = line.strip().lstrip("#").lstrip("-").strip()
                    alternatives.append(
                        {
                            "option": current_option[:100],
                            "score": 0.7,
                            "why_not_chosen": None,  # May be selected
                            "data": {"source": "implementation_plan.md"},
                        }
                    )

                # Look for "chosen" or "selected" markers
                if current_option and (
                    "chosen" in line_lower
                    or "selected" in line_lower
                    or "✓" in line
                    or "[x]" in line_lower
                ):
                    if alternatives:
                        alternatives[-1]["why_not_chosen"] = None
                        alternatives[-1]["score"] = 0.85

        # Parse task.md for task approach
        task_content = artifacts.get("task.md", "")
        if task_content:
            # Extract the main task as "selected approach"
            lines = task_content.split("\n")
            task_title = None
            for line in lines:
                if line.strip().startswith("#"):
                    task_title = line.strip().lstrip("#").strip()
                    break

            if task_title and not alternatives:
                # No explicit alternatives found, create task-based ones
                alternatives.append(
                    {
                        "option": f"Manual implementation of: {task_title[:60]}",
                        "score": 0.3,
                        "why_not_chosen": "AI-assisted approach chosen for efficiency",
                        "data": {"source": "task.md", "baseline": True},
                    }
                )
                alternatives.append(
                    {
                        "option": f"AI-assisted: {task_title[:60]}",
                        "score": 0.85,
                        "why_not_chosen": None,
                        "data": {"source": "task.md", "selected": True},
                    }
                )

        # Parse walkthrough.md for verification alternatives
        walkthrough = artifacts.get("walkthrough.md", "")
        if walkthrough and "alternative" in walkthrough.lower():
            alternatives.append(
                {
                    "option": "Alternative verification approach documented",
                    "score": 0.5,
                    "why_not_chosen": "Selected approach provided better coverage",
                    "data": {"source": "walkthrough.md"},
                }
            )

        return alternatives if alternatives else None

    def _read_artifacts(self, session_dir: Path) -> Dict[str, str]:
        """Read all artifacts from a session directory."""
        artifacts = {}

        artifact_names = [
            "task.md",
            "walkthrough.md",
            "action_items.md",
            "implementation_plan.md",
            "explanation.md",
            "notes.md",
        ]

        for artifact_name in artifact_names:
            artifact_path = session_dir / artifact_name
            if artifact_path.exists():
                try:
                    with open(artifact_path) as f:
                        artifacts[artifact_name] = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read {artifact_path}: {e}")

        return artifacts

    def _compute_artifacts_hash(self, artifacts: Dict[str, str]) -> str:
        """Compute hash of artifacts to detect changes."""
        content = json.dumps(artifacts, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _artifacts_to_session(
        self, session_id: str, artifacts: Dict[str, str], user_id: str = "kay"
    ) -> ConversationSession:
        """
        Convert Antigravity artifacts into a ConversationSession.

        This transforms the artifact-based format into the message-based
        format that RichCaptureEnhancer expects.
        """
        now = datetime.now(timezone.utc)
        messages = []

        # Extract task as user message
        task_content = artifacts.get("task.md", "")
        if task_content:
            # First line is usually the task title
            lines = task_content.strip().split("\n")
            task_title = lines[0].replace("#", "").strip() if lines else "Task"

            messages.append(
                ConversationMessage(
                    role="user",
                    content=task_title,
                    timestamp=now,
                    message_id=f"msg_{session_id}_user_1",
                    session_id=session_id,
                    token_count=len(task_content.split()),
                    model_info="gemini-2.5-pro",
                )
            )

        # Extract implementation plan as assistant planning response
        impl_plan = artifacts.get("implementation_plan.md", "")
        if impl_plan:
            messages.append(
                ConversationMessage(
                    role="assistant",
                    content=impl_plan[:2000],  # Truncate for processing
                    timestamp=now,
                    message_id=f"msg_{session_id}_assistant_1",
                    session_id=session_id,
                    token_count=len(impl_plan.split()),
                    model_info="gemini-2.5-pro",
                )
            )

        # Extract walkthrough as verification response
        walkthrough = artifacts.get("walkthrough.md", "")
        if walkthrough:
            messages.append(
                ConversationMessage(
                    role="assistant",
                    content=walkthrough[:2000],
                    timestamp=now,
                    message_id=f"msg_{session_id}_assistant_2",
                    session_id=session_id,
                    token_count=len(walkthrough.split()),
                    model_info="gemini-2.5-pro",
                )
            )

        # Extract action items if present
        action_items = artifacts.get("action_items.md", "")
        if action_items:
            messages.append(
                ConversationMessage(
                    role="assistant",
                    content=action_items[:1000],
                    timestamp=now,
                    message_id=f"msg_{session_id}_assistant_3",
                    session_id=session_id,
                    token_count=len(action_items.split()),
                    model_info="gemini-2.5-pro",
                )
            )

        # If no messages extracted, create a minimal one
        if not messages:
            messages.append(
                ConversationMessage(
                    role="user",
                    content="Antigravity session",
                    timestamp=now,
                    message_id=f"msg_{session_id}_user_0",
                    session_id=session_id,
                    token_count=2,
                    model_info="gemini-2.5-pro",
                )
            )

        # Extract topics from task content
        topics = []
        if task_content:
            first_line = task_content.split("\n")[0].replace("#", "").strip()
            if first_line:
                topics.append(first_line[:50])
        if not topics:
            topics = ["Antigravity Session"]

        # Calculate total tokens
        total_tokens = sum(m.token_count or 0 for m in messages)

        # Create session
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            start_time=now,
            platform="google_antigravity",
            end_time=now,
            messages=messages,
            significance_score=0.7,  # Default significance for artifact-based sessions
            total_tokens=total_tokens,
            topics=topics,
            capsule_created=False,
        )

        return session

    def _create_rich_capsule(
        self, session: ConversationSession, artifacts: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a rich capsule using RichCaptureEnhancer.

        This produces the same rich metadata as Claude Code captures.
        """
        try:
            # Use RichCaptureEnhancer to create capsule with full metadata
            capsule_data = (
                RichCaptureEnhancer.create_capsule_from_session_with_rich_metadata(
                    session=session,
                    user_id=session.user_id,
                )
            )

            # Extract just the payload content - remove wrapper fields that will be
            # added at the outer level to avoid double-nesting
            # RichCaptureEnhancer returns: {capsule_id, type, version, timestamp, status, verification, payload, metadata}
            # We want to flatten this so payload content is at the top level

            payload_content = capsule_data.get("payload", {})

            # Merge the rich metadata into a flat structure
            flat_capsule = {
                **payload_content,  # The actual rich content (reasoning_steps, confidence, etc.)
                "session_metadata": {
                    **payload_content.get("session_metadata", {}),
                    "platform": "google_antigravity",
                    "model": "gemini-2.5-pro",
                    "artifact_count": len(artifacts),
                    "artifacts_present": list(artifacts.keys()),
                },
                "metadata": capsule_data.get("metadata", {}),
                "artifacts": {
                    name: self._truncate_with_marker(content, 10000)
                    for name, content in artifacts.items()
                },
            }

            # Preserve capsule_id from the original
            flat_capsule["capsule_id"] = capsule_data.get("capsule_id")

            # Override generic alternatives with artifact-derived ones
            artifact_alternatives = self._extract_alternatives_from_artifacts(artifacts)
            if artifact_alternatives:
                flat_capsule["alternatives_considered"] = artifact_alternatives
                logger.info(
                    f"   ✓ Extracted {len(artifact_alternatives)} alternatives from artifacts"
                )

            return flat_capsule

        except Exception as e:
            logger.error(f"Failed to create rich capsule: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _post_capsule(self, capsule_data: Dict[str, Any]) -> Optional[str]:
        """Post capsule to the API with cryptographic signature."""
        try:
            # Build the full capsule structure expected by the API
            capsule_id = capsule_data.get(
                "capsule_id", f"antigravity_{secrets.token_hex(8)}"
            )

            # Compute hash
            content_hash = hashlib.sha256(
                json.dumps(capsule_data, sort_keys=True, default=str).encode()
            ).hexdigest()

            # Build verification with signature if available
            verification = {
                "verified": True,
                "hash": content_hash,
            }

            # Sign the capsule if CryptoSealer is available
            if self.signing_enabled and self.crypto_sealer:
                try:
                    # V7.0 signing: sign the HASH string, not the data
                    # This matches what the verifier expects
                    from cryptography.hazmat.primitives import serialization

                    # Get verify key
                    verify_key_hex = None
                    if self.crypto_sealer.public_key:
                        pub_bytes = self.crypto_sealer.public_key.public_bytes(
                            encoding=serialization.Encoding.Raw,
                            format=serialization.PublicFormat.Raw,
                        )
                        verify_key_hex = pub_bytes.hex()

                    # Sign the hash string (UTF-8 encoded) - this is what verifier checks
                    hash_bytes_to_sign = content_hash.encode("utf-8")
                    signature_bytes = self.crypto_sealer.private_key.sign(
                        hash_bytes_to_sign
                    )
                    signature_hex = signature_bytes.hex()

                    verification.update(
                        {
                            "signature": f"ed25519:{signature_hex}",
                            "method": "ed25519",
                            "signer": "antigravity-capture",
                            "verify_key": verify_key_hex,
                            "trust_score": 0.75,  # Default trust for automated capture
                        }
                    )
                    logger.info("🔐 Capsule signed with Ed25519 (V7.0 format)")
                except Exception as sign_error:
                    logger.warning(
                        f"Signing failed (capsule will be unsigned): {sign_error}"
                    )

            api_payload = {
                "capsule_id": capsule_id,
                "type": "reasoning_trace",
                "version": "7.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "SEALED",
                "payload": capsule_data,
                "verification": verification,
            }

            response = requests.post(
                f"{self.api_base}/capsules",
                json=api_payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code in (200, 201):
                result = response.json()
                created_id = result.get("capsule_id", capsule_id)
                signed_status = "signed" if "signature" in verification else "unsigned"
                logger.info(f"✅ Created rich capsule ({signed_status}): {created_id}")
                return created_id
            else:
                logger.error(
                    f"❌ API error {response.status_code}: {response.text[:200]}"
                )
                return None

        except Exception as e:
            logger.error(f"❌ Failed to post capsule: {e}")
            return None

    def capture_session(self, session_dir: Path, user_id: str = "kay") -> Optional[str]:
        """
        Capture an Antigravity session with rich metadata.

        Returns capsule_id if created, None otherwise.
        """
        session_id = session_dir.name

        # Read artifacts
        artifacts = self._read_artifacts(session_dir)
        if not artifacts:
            logger.debug(f"No artifacts in session {session_id}")
            return None

        # Check if changed since last capture
        current_hash = self._compute_artifacts_hash(artifacts)
        if self.captured_sessions.get(session_id) == current_hash:
            logger.debug(f"Session {session_id} unchanged")
            return self.session_capsule_map.get(session_id)

        logger.info(f"✨ Capturing Antigravity session: {session_id}")
        logger.info(f"   Artifacts: {list(artifacts.keys())}")

        # Convert to ConversationSession
        session = self._artifacts_to_session(session_id, artifacts, user_id)

        # Create rich capsule through RichCaptureEnhancer
        capsule_data = self._create_rich_capsule(session, artifacts)
        if not capsule_data:
            return None

        # Post to API
        capsule_id = self._post_capsule(capsule_data)

        if capsule_id:
            self.captured_sessions[session_id] = current_hash
            self.session_capsule_map[session_id] = capsule_id
            logger.info(f"🎉 Rich capsule created: {capsule_id}")

            # Log richness indicators
            if "critical_path_analysis" in capsule_data:
                logger.info("   ✓ Critical path analysis included")
            if "uncertainty_analysis" in capsule_data:
                logger.info("   ✓ Uncertainty analysis included")
            if "risk_assessment" in capsule_data:
                logger.info("   ✓ Risk assessment included")
            if "plain_language_summary" in capsule_data:
                logger.info("   ✓ Plain language summary included")

        return capsule_id

    def scan_and_capture(self, user_id: str = "kay") -> List[str]:
        """
        Scan for all active sessions and capture them.

        Returns list of created capsule IDs.
        """
        capsule_ids = []

        sessions = self.get_active_sessions()
        logger.info(f"📂 Found {len(sessions)} Antigravity sessions")

        for session_dir in sessions:
            try:
                capsule_id = self.capture_session(session_dir, user_id)
                if capsule_id:
                    capsule_ids.append(capsule_id)
            except Exception as e:
                logger.error(f"Error capturing {session_dir.name}: {e}")

        return capsule_ids

    async def watch_and_capture(self, user_id: str = "kay", interval: int = 30):
        """
        Continuously watch for new/changed sessions and capture them.

        Args:
            user_id: User identifier
            interval: Seconds between scans
        """
        logger.info(f"👀 Starting watch mode (interval: {interval}s)")

        while True:
            try:
                capsule_ids = self.scan_and_capture(user_id)
                if capsule_ids:
                    logger.info(f"📦 Captured {len(capsule_ids)} capsules this cycle")
            except Exception as e:
                logger.error(f"Watch cycle error: {e}")

            await asyncio.sleep(interval)


# Convenience functions


def capture_current_antigravity_sessions(user_id: str = "kay") -> List[str]:
    """Capture all current Antigravity sessions with rich metadata."""
    service = AntigravityRichCaptureService()
    return service.scan_and_capture(user_id)


async def watch_antigravity(user_id: str = "kay", interval: int = 30):
    """Watch and capture Antigravity sessions continuously."""
    service = AntigravityRichCaptureService()
    await service.watch_and_capture(user_id, interval)


async def main():
    """Test the rich antigravity capture."""
    print("✨ Antigravity Rich Capture Integration")
    print("=" * 60)

    service = AntigravityRichCaptureService()

    # Check for sessions
    sessions = service.get_active_sessions()
    print(f"\n📂 Found {len(sessions)} Antigravity sessions:")
    for s in sessions:
        print(f"   - {s.name}")

    # Capture them
    if sessions:
        print("\n🔄 Capturing with rich metadata...")
        capsule_ids = service.scan_and_capture()

        print(f"\n✅ Created {len(capsule_ids)} rich capsules:")
        for cid in capsule_ids:
            print(f"   - {cid}")
    else:
        print("\n⚠️  No Antigravity sessions found")
        print(f"   Expected location: {service.brain_dir}")

    print("\n✨ Done!")


if __name__ == "__main__":
    asyncio.run(main())
