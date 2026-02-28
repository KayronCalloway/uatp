"""
Outcome Tracking Integration - Gap 1 Implementation
Wires outcome inference into the live capture flow.

When a new message arrives:
1. Check if it's a follow-up to a previous AI response
2. Run outcome inference on the message
3. Update the original capsule with outcome data

This creates the learning loop:
Capture -> Infer Outcome -> Update Capsule -> Historical Accuracy Uses Outcome
"""

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Import outcome inference
try:
    from src.feedback.outcome_inference import OutcomeInferenceEngine

    INFERENCE_AVAILABLE = True
except ImportError:
    INFERENCE_AVAILABLE = False
    logger.warning("Outcome inference not available")

# Import calibration for feedback loop
try:
    from src.ml.calibration_integration import get_capsule_calibrator

    CALIBRATION_AVAILABLE = True
except ImportError:
    CALIBRATION_AVAILABLE = False


@dataclass
class PendingOutcome:
    """A capsule waiting for outcome determination."""

    capsule_id: str
    response_summary: str  # First 500 chars of assistant response
    confidence: float
    timestamp: datetime
    topics: List[str]


class OutcomeTracker:
    """
    Tracks capsules and infers outcomes from follow-up messages.

    Simple, synchronous design that works with SQLite.
    Integrates with the existing capture flow via file-based state.
    """

    # How long to wait for follow-up before giving up
    FOLLOW_UP_WINDOW_HOURS = 24

    # Confidence threshold for auto-updating (below this, mark as uncertain)
    AUTO_UPDATE_THRESHOLD = 0.75

    # State file for tracking pending capsules
    STATE_FILE = Path("/tmp/uatp_pending_outcomes.json")

    def __init__(self, db_path: str = None, use_embeddings: bool = False):
        """
        Initialize outcome tracker.

        Args:
            db_path: Path to SQLite database
            use_embeddings: Whether to use sentence embeddings (slower but better)
        """
        self.db_path = db_path or "uatp_dev.db"
        self.use_embeddings = use_embeddings

        # Initialize inference engine
        if INFERENCE_AVAILABLE:
            self._inference_engine = OutcomeInferenceEngine(
                use_embeddings=use_embeddings
            )
        else:
            self._inference_engine = None

        # Load pending outcomes from state file
        self._pending: Dict[str, PendingOutcome] = {}
        self._load_state()

    def _load_state(self):
        """Load pending outcomes from state file."""
        if self.STATE_FILE.exists():
            try:
                with open(self.STATE_FILE) as f:
                    data = json.load(f)
                    for capsule_id, info in data.items():
                        self._pending[capsule_id] = PendingOutcome(
                            capsule_id=capsule_id,
                            response_summary=info["response_summary"],
                            confidence=info["confidence"],
                            timestamp=datetime.fromisoformat(info["timestamp"]),
                            topics=info.get("topics", []),
                        )
                logger.debug(f"Loaded {len(self._pending)} pending outcomes")
            except Exception as e:
                logger.warning(f"Failed to load outcome state: {e}")
                self._pending = {}

    def _save_state(self):
        """Save pending outcomes to state file."""
        try:
            data = {}
            for capsule_id, pending in self._pending.items():
                data[capsule_id] = {
                    "response_summary": pending.response_summary,
                    "confidence": pending.confidence,
                    "timestamp": pending.timestamp.isoformat(),
                    "topics": pending.topics,
                }
            with open(self.STATE_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save outcome state: {e}")

    def _cleanup_expired(self):
        """Remove pending outcomes that are too old."""
        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=self.FOLLOW_UP_WINDOW_HOURS
        )
        expired = [cid for cid, p in self._pending.items() if p.timestamp < cutoff]
        for cid in expired:
            del self._pending[cid]
            logger.debug(f"Expired pending outcome for {cid}")

        if expired:
            self._save_state()

    def register_capsule(
        self,
        capsule_id: str,
        response_text: str,
        confidence: float,
        topics: List[str] = None,
    ):
        """
        Register a capsule for outcome tracking.

        Call this after creating a capsule to enable outcome inference.

        Args:
            capsule_id: The capsule's ID
            response_text: The assistant's response (will be truncated)
            confidence: The capsule's confidence score
            topics: Optional list of topics
        """
        self._cleanup_expired()

        self._pending[capsule_id] = PendingOutcome(
            capsule_id=capsule_id,
            response_summary=response_text[:500],
            confidence=confidence,
            timestamp=datetime.now(timezone.utc),
            topics=topics or [],
        )

        self._save_state()
        logger.debug(f"Registered capsule {capsule_id} for outcome tracking")

    def process_follow_up(
        self,
        user_message: str,
        capsule_id: str = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Process a follow-up message and infer outcome.

        Args:
            user_message: The user's follow-up message
            capsule_id: Optional specific capsule ID (otherwise uses most recent)

        Returns:
            Dict with outcome info, or None if no matching capsule
        """
        if not INFERENCE_AVAILABLE or not self._inference_engine:
            logger.debug("Outcome inference not available")
            return None

        self._cleanup_expired()

        # Find the relevant pending capsule
        pending = None
        if capsule_id and capsule_id in self._pending:
            pending = self._pending[capsule_id]
        elif self._pending:
            # Use most recent pending capsule
            pending = max(self._pending.values(), key=lambda p: p.timestamp)

        if not pending:
            logger.debug("No pending capsule for outcome tracking")
            return None

        # Run inference
        inference = self._inference_engine.infer_outcome(user_message)

        result = {
            "capsule_id": pending.capsule_id,
            "status": inference.status.value,
            "confidence": inference.confidence,
            "method": inference.method,
            "signals": inference.signals,
            "needs_review": inference.needs_review,
            "updated_capsule": False,
        }

        # Update capsule if confidence is high enough
        if inference.confidence >= self.AUTO_UPDATE_THRESHOLD:
            updated = self._update_capsule_outcome(
                capsule_id=pending.capsule_id,
                status=inference.status.value,
                confidence=inference.confidence,
                method=inference.method,
                signals=inference.signals,
                follow_up_text=user_message[:500],
            )
            result["updated_capsule"] = updated

            if updated:
                # Remove from pending
                del self._pending[pending.capsule_id]
                self._save_state()
                logger.info(
                    f"✅ Outcome inferred for {pending.capsule_id}: "
                    f"{inference.status.value} (confidence: {inference.confidence:.0%})"
                )
        else:
            logger.debug(
                f"Outcome uncertain for {pending.capsule_id}: "
                f"{inference.status.value} (confidence: {inference.confidence:.0%})"
            )

        return result

    def _update_capsule_outcome(
        self,
        capsule_id: str,
        status: str,
        confidence: float,
        method: str,
        signals: List[str],
        follow_up_text: str,
    ) -> bool:
        """
        Update a capsule's outcome in the database.

        Also feeds the outcome to the calibrator for Gap 5 (Calibration Feedback).

        Returns:
            True if update succeeded
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get the original capsule's confidence for calibration
            cursor.execute(
                """
                SELECT payload FROM capsules WHERE capsule_id = ?
            """,
                (capsule_id,),
            )
            row = cursor.fetchone()

            original_confidence = 0.5
            topics = []
            if row and row[0]:
                payload = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                # Get the original confidence (before any adjustments)
                original_confidence = (
                    payload.get("confidence_original")
                    or payload.get("confidence_pre_calibration")
                    or payload.get("confidence", 0.5)
                )
                topics = payload.get("session_metadata", {}).get("topics", [])

            # Build outcome metrics JSON
            outcome_metrics = json.dumps(
                {
                    "inference_confidence": confidence,
                    "inference_method": method,
                    "inference_signals": signals,
                    "follow_up_preview": follow_up_text[:200],
                }
            )

            cursor.execute(
                """
                UPDATE capsules
                SET outcome_status = ?,
                    outcome_timestamp = ?,
                    outcome_notes = ?,
                    outcome_metrics = ?
                WHERE capsule_id = ?
            """,
                (
                    status,
                    datetime.now(timezone.utc).isoformat(),
                    f"Auto-inferred via {method}",
                    outcome_metrics,
                    capsule_id,
                ),
            )

            conn.commit()
            updated = cursor.rowcount > 0
            conn.close()

            # Feed outcome to calibrator (Gap 5)
            if updated and CALIBRATION_AVAILABLE:
                try:
                    calibrator = get_capsule_calibrator(self.db_path)
                    calibrator.record_outcome(
                        confidence=original_confidence,
                        outcome=status,
                        topics=topics,
                    )
                    logger.debug(
                        f"Fed outcome to calibrator: {status} (confidence was {original_confidence:.0%})"
                    )
                except Exception as ce:
                    logger.debug(f"Calibrator update skipped: {ce}")

            return updated

        except Exception as e:
            logger.error(f"Failed to update capsule outcome: {e}")
            return False

    def get_pending_count(self) -> int:
        """Get count of capsules awaiting outcome."""
        self._cleanup_expired()
        return len(self._pending)

    def get_recent_outcomes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recently tracked outcomes from the database.

        Args:
            limit: Maximum number to return

        Returns:
            List of outcome dicts
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT capsule_id, outcome_status, outcome_timestamp,
                       outcome_notes, outcome_metrics
                FROM capsules
                WHERE outcome_status IS NOT NULL
                ORDER BY outcome_timestamp DESC
                LIMIT ?
            """,
                (limit,),
            )

            outcomes = []
            for row in cursor.fetchall():
                outcomes.append(
                    {
                        "capsule_id": row[0],
                        "status": row[1],
                        "timestamp": row[2],
                        "notes": row[3],
                        "metrics": json.loads(row[4]) if row[4] else None,
                    }
                )

            conn.close()
            return outcomes

        except Exception as e:
            logger.error(f"Failed to get recent outcomes: {e}")
            return []

    def get_outcome_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked outcomes."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT outcome_status, COUNT(*) as count
                FROM capsules
                WHERE outcome_status IS NOT NULL
                GROUP BY outcome_status
            """
            )

            by_status = {row[0]: row[1] for row in cursor.fetchall()}
            total = sum(by_status.values())

            conn.close()

            return {
                "total_with_outcomes": total,
                "by_status": by_status,
                "pending_count": self.get_pending_count(),
                "success_rate": by_status.get("success", 0) / total
                if total > 0
                else None,
            }

        except Exception as e:
            logger.error(f"Failed to get outcome stats: {e}")
            return {"error": str(e)}


# Singleton instance
_tracker: Optional[OutcomeTracker] = None


def get_outcome_tracker(db_path: str = None) -> OutcomeTracker:
    """Get or create the outcome tracker."""
    global _tracker
    if _tracker is None:
        _tracker = OutcomeTracker(db_path=db_path)
    return _tracker


def register_capsule_for_tracking(
    capsule_id: str,
    response_text: str,
    confidence: float,
    topics: List[str] = None,
):
    """
    Convenience function to register a capsule for outcome tracking.

    Call this after creating a capsule.
    """
    tracker = get_outcome_tracker()
    tracker.register_capsule(capsule_id, response_text, confidence, topics)


def process_user_message_for_outcome(user_message: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to process a user message for outcome inference.

    Call this when a new user message comes in.
    """
    tracker = get_outcome_tracker()
    return tracker.process_follow_up(user_message)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Outcome Tracking")
    parser.add_argument("--stats", action="store_true", help="Show outcome stats")
    parser.add_argument("--recent", type=int, default=0, help="Show N recent outcomes")
    parser.add_argument("--test", type=str, help="Test inference on a message")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    tracker = OutcomeTracker(db_path="/Users/kay/uatp-capsule-engine/uatp_dev.db")

    if args.stats:
        stats = tracker.get_outcome_stats()
        print("\nOutcome Statistics:")
        print(f"  Total with outcomes: {stats.get('total_with_outcomes', 0)}")
        print(f"  By status: {stats.get('by_status', {})}")
        print(f"  Pending: {stats.get('pending_count', 0)}")
        if stats.get("success_rate") is not None:
            print(f"  Success rate: {stats['success_rate']:.1%}")

    if args.recent:
        outcomes = tracker.get_recent_outcomes(args.recent)
        print(f"\nRecent Outcomes ({len(outcomes)}):")
        for o in outcomes:
            print(
                f"  - {o['capsule_id'][:30]}... {o['status']} ({o['timestamp'][:19]})"
            )

    if args.test:
        print(f"\nTesting inference on: '{args.test}'")
        if INFERENCE_AVAILABLE:
            engine = OutcomeInferenceEngine(use_embeddings=False)
            result = engine.infer_outcome(args.test)
            print(f"  Status: {result.status.value}")
            print(f"  Confidence: {result.confidence:.0%}")
            print(f"  Method: {result.method}")
            print(f"  Signals: {result.signals}")
            print(f"  Needs review: {result.needs_review}")
        else:
            print("  Inference not available")
