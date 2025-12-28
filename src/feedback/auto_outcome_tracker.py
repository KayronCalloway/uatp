"""
Auto-Outcome Tracker
====================

Integrates outcome inference with the capsule capture flow.

When a new message arrives:
1. Check if it's a follow-up to a previous AI response
2. Run outcome inference on the follow-up
3. Update the original capsule's outcome status
4. Route uncertain cases to human review
5. Update calibration with confirmed outcomes

This creates the self-improvement flywheel:
Capture → Infer → Review → Calibrate → Improve → Capture...
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.capsule import CapsuleModel


@dataclass
class TrackedInteraction:
    """An AI response waiting for follow-up outcome detection."""

    capsule_id: str
    response_text: str
    predicted_confidence: float
    domain: str
    timestamp: datetime
    conversation_id: Optional[str] = None


class AutoOutcomeTracker:
    """
    Tracks AI responses and automatically infers outcomes from follow-ups.

    Architecture:
    - Maintains a sliding window of recent AI responses
    - When a user message arrives, checks if it's a follow-up
    - Runs hybrid inference (keywords + embeddings)
    - High-confidence inferences update capsules automatically
    - Low-confidence cases go to human review queue
    """

    # How long to wait for follow-up before marking as "unknown"
    FOLLOW_UP_WINDOW = timedelta(hours=24)

    # Confidence threshold for auto-updating capsule
    AUTO_UPDATE_THRESHOLD = 0.85

    def __init__(
        self,
        session_factory,
        use_embeddings: bool = True,
        auto_update_capsules: bool = True,
    ):
        """
        Initialize auto-outcome tracker.

        Args:
            session_factory: SQLAlchemy async session factory
            use_embeddings: Whether to use embedding similarity
            auto_update_capsules: Whether to automatically update capsule outcomes
        """
        self.session_factory = session_factory
        self.use_embeddings = use_embeddings
        self.auto_update_capsules = auto_update_capsules

        # In-memory cache of recent AI responses awaiting follow-up
        self._pending_interactions: Dict[str, TrackedInteraction] = {}

        # Initialize components lazily
        self._inference_engine = None
        self._review_queue = None
        self._calibration_manager = None

    def _get_inference_engine(self):
        """Lazy load inference engine."""
        if self._inference_engine is None:
            from .outcome_inference import OutcomeInferenceEngine

            self._inference_engine = OutcomeInferenceEngine(
                use_embeddings=self.use_embeddings
            )
        return self._inference_engine

    def _get_review_queue(self):
        """Lazy load review queue manager."""
        if self._review_queue is None:
            from .review_queue import ReviewQueueManager

            self._review_queue = ReviewQueueManager(self.session_factory)
        return self._review_queue

    def _get_calibration_manager(self):
        """Lazy load calibration manager."""
        if self._calibration_manager is None:
            from .calibration import CalibrationManager

            self._calibration_manager = CalibrationManager(
                storage_path=Path("data/calibration_state.json")
            )
        return self._calibration_manager

    def track_ai_response(
        self,
        capsule_id: str,
        response_text: str,
        predicted_confidence: float,
        domain: str = "general",
        conversation_id: Optional[str] = None,
    ):
        """
        Track an AI response for future outcome detection.

        Call this after creating a capsule to enable auto-outcome tracking.

        Args:
            capsule_id: ID of the capsule containing the response
            response_text: The AI's response text (truncated is fine)
            predicted_confidence: The capsule's confidence score
            domain: Domain/topic for calibration
            conversation_id: Optional conversation ID for grouping
        """
        interaction = TrackedInteraction(
            capsule_id=capsule_id,
            response_text=response_text[:2000],  # Truncate for memory
            predicted_confidence=predicted_confidence,
            domain=domain,
            timestamp=datetime.now(timezone.utc),
            conversation_id=conversation_id,
        )

        # Use capsule_id as key (one pending interaction per capsule)
        self._pending_interactions[capsule_id] = interaction

        # Cleanup old interactions
        self._cleanup_expired()

    def _cleanup_expired(self):
        """Remove interactions outside the follow-up window."""
        cutoff = datetime.now(timezone.utc) - self.FOLLOW_UP_WINDOW
        expired = [
            cid
            for cid, interaction in self._pending_interactions.items()
            if interaction.timestamp < cutoff
        ]
        for cid in expired:
            del self._pending_interactions[cid]

    async def process_follow_up(
        self,
        follow_up_text: str,
        conversation_id: Optional[str] = None,
        capsule_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a user's follow-up message for outcome inference.

        Args:
            follow_up_text: The user's follow-up message
            conversation_id: Optional conversation ID to find matching interaction
            capsule_id: Optional specific capsule ID to check

        Returns:
            Dict with inference results and actions taken
        """
        # Find the relevant pending interaction
        interaction = None

        if capsule_id and capsule_id in self._pending_interactions:
            interaction = self._pending_interactions[capsule_id]
        elif conversation_id:
            # Find most recent interaction in this conversation
            candidates = [
                i
                for i in self._pending_interactions.values()
                if i.conversation_id == conversation_id
            ]
            if candidates:
                interaction = max(candidates, key=lambda x: x.timestamp)

        if not interaction:
            return {
                "status": "no_pending_interaction",
                "message": "No recent AI response found to match follow-up with",
            }

        # Run inference
        engine = self._get_inference_engine()
        inference = engine.infer_outcome(follow_up_text)

        result = {
            "capsule_id": interaction.capsule_id,
            "inference": {
                "status": inference.status.value,
                "confidence": inference.confidence,
                "method": inference.method,
                "signals": inference.signals,
            },
            "needs_review": inference.needs_review,
            "actions_taken": [],
        }

        # High confidence: auto-update capsule
        if (
            inference.confidence >= self.AUTO_UPDATE_THRESHOLD
            and self.auto_update_capsules
        ):
            await self._update_capsule_outcome(
                capsule_id=interaction.capsule_id,
                status=inference.status.value,
                notes=f"Auto-inferred via {inference.method}",
                signals=inference.signals,
            )
            result["actions_taken"].append("updated_capsule_outcome")

            # Record for calibration
            outcome_map = {"success": 1.0, "partial": 0.5, "failure": 0.0}
            if inference.status.value in outcome_map:
                manager = self._get_calibration_manager()
                manager.record_outcome(
                    predicted_confidence=interaction.predicted_confidence,
                    actual_outcome=outcome_map[inference.status.value],
                    domain=interaction.domain,
                )
                result["actions_taken"].append("recorded_calibration")

            # Remove from pending
            del self._pending_interactions[interaction.capsule_id]

        # Low confidence: queue for review
        elif inference.needs_review:
            queue = self._get_review_queue()
            review_id = await queue.add_to_queue(
                capsule_id=interaction.capsule_id,
                inference=inference,
                original_message=interaction.response_text,
                follow_up_message=follow_up_text,
            )
            result["review_item_id"] = review_id
            result["actions_taken"].append("queued_for_review")

        return result

    async def _update_capsule_outcome(
        self,
        capsule_id: str,
        status: str,
        notes: Optional[str] = None,
        signals: Optional[List[str]] = None,
    ):
        """Update a capsule's outcome in the database."""
        async with self.session_factory() as session:
            await session.execute(
                update(CapsuleModel)
                .where(CapsuleModel.capsule_id == capsule_id)
                .values(
                    outcome_status=status,
                    outcome_timestamp=datetime.now(timezone.utc),
                    outcome_notes=notes,
                    outcome_metrics={"inference_signals": signals} if signals else None,
                )
            )
            await session.commit()

    async def process_review_completion(
        self,
        review_item_id: str,
        human_status: str,
    ):
        """
        Handle completion of a human review.

        Updates calibration with the human-verified outcome.

        Args:
            review_item_id: ID of the completed review item
            human_status: Human-determined outcome
        """
        queue = self._get_review_queue()

        # Get the review item to find original prediction
        async with self.session_factory() as session:
            from .review_queue import ReviewQueueItem

            result = await session.execute(
                select(ReviewQueueItem).where(ReviewQueueItem.id == review_item_id)
            )
            item = result.scalar_one_or_none()

            if item and item.inference_confidence is not None:
                # Get the original capsule to find its confidence
                capsule_result = await session.execute(
                    select(CapsuleModel).where(
                        CapsuleModel.capsule_id == item.capsule_id
                    )
                )
                capsule = capsule_result.scalar_one_or_none()

                if capsule:
                    # Record for calibration
                    payload = capsule.payload or {}
                    original_confidence = payload.get("confidence", 0.5)
                    domain = (payload.get("session_metadata") or {}).get(
                        "domain", "general"
                    )

                    outcome_map = {"success": 1.0, "partial": 0.5, "failure": 0.0}
                    if human_status in outcome_map:
                        manager = self._get_calibration_manager()
                        manager.record_outcome(
                            predicted_confidence=original_confidence,
                            actual_outcome=outcome_map[human_status],
                            domain=domain,
                        )

                    # Update capsule outcome
                    await self._update_capsule_outcome(
                        capsule_id=item.capsule_id,
                        status=human_status,
                        notes=f"Human-reviewed (was: {item.inferred_status})",
                    )

    def get_pending_count(self) -> int:
        """Get count of interactions awaiting follow-up."""
        self._cleanup_expired()
        return len(self._pending_interactions)

    async def get_calibration_health(self) -> Dict[str, Any]:
        """Get calibration health summary."""
        manager = self._get_calibration_manager()
        metrics = manager.get_all_metrics()
        drift_alerts = manager.check_drift()

        return {
            "domains": {
                domain: {
                    "sample_size": m.sample_size,
                    "brier_score": m.brier_score,
                    "calibration_error": m.calibration_error,
                }
                for domain, m in metrics.items()
            },
            "drift_alerts": drift_alerts,
            "pending_interactions": self.get_pending_count(),
        }


# Singleton instance
_tracker: Optional[AutoOutcomeTracker] = None


def get_auto_tracker(session_factory=None) -> AutoOutcomeTracker:
    """Get or create the auto-outcome tracker."""
    global _tracker
    if _tracker is None and session_factory is not None:
        _tracker = AutoOutcomeTracker(session_factory)
    if _tracker is None:
        raise RuntimeError(
            "AutoOutcomeTracker not initialized - provide session_factory"
        )
    return _tracker


def initialize_tracker(session_factory, **kwargs) -> AutoOutcomeTracker:
    """Initialize the global auto-outcome tracker."""
    global _tracker
    _tracker = AutoOutcomeTracker(session_factory, **kwargs)
    return _tracker
