"""
Human Review Queue
==================

Active learning system for uncertain outcome inferences.

When the auto-inference engine isn't confident enough, cases are
queued for human review. Human labels feed back into the system
to improve inference over time.

Design principles:
- Priority queue (most uncertain cases first for active learning)
- Tracks inference accuracy over time
- Supports batch review workflows
- Preserves full context for reviewers
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

if TYPE_CHECKING:
    from src.feedback.outcome_inference import OutcomeInference

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    String,
    func,
    select,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ReviewPriority(str, Enum):
    """Priority levels for review queue."""

    CRITICAL = "critical"  # High-stakes capsules (e.g., insurance decisions)
    HIGH = "high"  # Low inference confidence
    MEDIUM = "medium"  # Moderate confidence, conflicting signals
    LOW = "low"  # High confidence but flagged for spot-check


class ReviewStatus(str, Enum):
    """Status of a review item."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class ReviewQueueItem(Base):
    """Database model for review queue items."""

    __tablename__ = "outcome_review_queue"

    id = Column(String, primary_key=True)
    capsule_id = Column(String, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Inference details
    inferred_status = Column(String, nullable=True)  # What the engine guessed
    inference_confidence = Column(Float, nullable=True)
    inference_method = Column(String, nullable=True)
    inference_signals = Column(JSON, nullable=True)
    inference_scores = Column(JSON, nullable=True)

    # Context for reviewer
    original_message = Column(String, nullable=True)  # AI's response
    follow_up_message = Column(String, nullable=True)  # User's follow-up
    conversation_context = Column(JSON, nullable=True)  # Surrounding messages

    # Review metadata
    priority = Column(String, default=ReviewPriority.MEDIUM.value)
    status = Column(String, default=ReviewStatus.PENDING.value, index=True)
    assigned_to = Column(String, nullable=True)  # Reviewer ID
    assigned_at = Column(DateTime(timezone=True), nullable=True)

    # Review result
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(String, nullable=True)
    human_status = Column(String, nullable=True)  # Human-determined outcome
    human_confidence = Column(Float, nullable=True)  # How sure the reviewer is
    review_notes = Column(String, nullable=True)

    # Feedback for model improvement
    inference_was_correct = Column(Boolean, nullable=True)
    feedback_used_for_training = Column(Boolean, default=False)


@dataclass
class ReviewQueueStats:
    """Statistics about the review queue."""

    total_pending: int
    total_completed: int
    by_priority: Dict[str, int]
    avg_review_time_seconds: Optional[float]
    inference_accuracy: Optional[float]  # % of auto-inferences that were correct
    accuracy_by_method: Dict[str, float]


class ReviewQueueManager:
    """
    Manages the human review queue for uncertain outcomes.

    Key features:
    - Active learning: Prioritizes most informative cases
    - Tracks inference accuracy for calibration
    - Supports multiple reviewers
    - Batch operations for efficiency
    """

    def __init__(self, session_factory):
        """
        Initialize queue manager.

        Args:
            session_factory: SQLAlchemy async session factory
        """
        self.session_factory = session_factory

    async def add_to_queue(
        self,
        capsule_id: str,
        inference: "OutcomeInference",
        original_message: str,
        follow_up_message: str,
        conversation_context: Optional[List[Dict[str, Any]]] = None,
        priority: Optional[ReviewPriority] = None,
    ) -> str:
        """
        Add an uncertain inference to the review queue.

        Args:
            capsule_id: ID of the capsule to review
            inference: The auto-inference result
            original_message: The AI's original response
            follow_up_message: User's follow-up that triggered inference
            conversation_context: Optional surrounding conversation
            priority: Override priority (otherwise computed from confidence)

        Returns:
            Review item ID
        """
        from .outcome_inference import OutcomeStatus

        # Compute priority if not specified
        if priority is None:
            if inference.confidence < 0.3:
                priority = ReviewPriority.HIGH
            elif inference.confidence < 0.6:
                priority = ReviewPriority.MEDIUM
            elif inference.status == OutcomeStatus.UNCERTAIN:
                priority = ReviewPriority.HIGH
            else:
                priority = ReviewPriority.LOW

        item_id = f"review_{uuid4().hex[:12]}"

        async with self.session_factory() as session:
            item = ReviewQueueItem(
                id=item_id,
                capsule_id=capsule_id,
                inferred_status=inference.status.value if inference.status else None,
                inference_confidence=inference.confidence,
                inference_method=inference.method,
                inference_signals=inference.signals,
                inference_scores=inference.raw_scores,
                original_message=original_message[:2000] if original_message else None,
                follow_up_message=follow_up_message[:2000]
                if follow_up_message
                else None,
                conversation_context=conversation_context,
                priority=priority.value,
                status=ReviewStatus.PENDING.value,
            )
            session.add(item)
            await session.commit()

        return item_id

    async def get_next_for_review(
        self,
        reviewer_id: Optional[str] = None,
        priority_filter: Optional[List[ReviewPriority]] = None,
    ) -> Optional[ReviewQueueItem]:
        """
        Get the next item for review (active learning priority).

        Items are returned in order:
        1. Critical priority first
        2. Then by lowest confidence (most uncertain = most informative)
        3. Then by creation time (FIFO within same confidence)

        Args:
            reviewer_id: ID of reviewer (for assignment)
            priority_filter: Only return items of these priorities

        Returns:
            Next review item or None if queue is empty
        """
        async with self.session_factory() as session:
            query = select(ReviewQueueItem).where(
                ReviewQueueItem.status == ReviewStatus.PENDING.value
            )

            if priority_filter:
                query = query.where(
                    ReviewQueueItem.priority.in_([p.value for p in priority_filter])
                )

            # Order by priority (critical first), then confidence (lowest first)

            query = query.order_by(
                # Custom priority ordering would require case statement
                # For now, use confidence as primary sort
                ReviewQueueItem.inference_confidence.asc(),
                ReviewQueueItem.created_at.asc(),
            ).limit(1)

            result = await session.execute(query)
            item = result.scalar_one_or_none()

            if item and reviewer_id:
                # Assign to reviewer
                item.status = ReviewStatus.IN_PROGRESS.value
                item.assigned_to = reviewer_id
                item.assigned_at = datetime.now(timezone.utc)
                await session.commit()
                await session.refresh(item)

            return item

    async def submit_review(
        self,
        item_id: str,
        human_status: str,
        reviewer_id: str,
        human_confidence: float = 1.0,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Submit a human review result.

        Args:
            item_id: Review item ID
            human_status: Human-determined outcome (success/failure/partial)
            reviewer_id: ID of the reviewer
            human_confidence: How confident the reviewer is (0-1)
            notes: Optional review notes

        Returns:
            True if successful
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(ReviewQueueItem).where(ReviewQueueItem.id == item_id)
            )
            item = result.scalar_one_or_none()

            if not item:
                return False

            # Update review result
            item.status = ReviewStatus.COMPLETED.value
            item.reviewed_at = datetime.now(timezone.utc)
            item.reviewed_by = reviewer_id
            item.human_status = human_status
            item.human_confidence = human_confidence
            item.review_notes = notes

            # Check if inference was correct
            if item.inferred_status:
                item.inference_was_correct = item.inferred_status == human_status

            await session.commit()

        return True

    async def get_queue_stats(self) -> ReviewQueueStats:
        """Get statistics about the review queue."""
        async with self.session_factory() as session:
            # Count pending
            pending_result = await session.execute(
                select(func.count(ReviewQueueItem.id)).where(
                    ReviewQueueItem.status == ReviewStatus.PENDING.value
                )
            )
            total_pending = pending_result.scalar() or 0

            # Count completed
            completed_result = await session.execute(
                select(func.count(ReviewQueueItem.id)).where(
                    ReviewQueueItem.status == ReviewStatus.COMPLETED.value
                )
            )
            total_completed = completed_result.scalar() or 0

            # Count by priority (pending only)
            by_priority = {}
            for priority in ReviewPriority:
                result = await session.execute(
                    select(func.count(ReviewQueueItem.id)).where(
                        ReviewQueueItem.status == ReviewStatus.PENDING.value,
                        ReviewQueueItem.priority == priority.value,
                    )
                )
                by_priority[priority.value] = result.scalar() or 0

            # Calculate inference accuracy
            accuracy_result = await session.execute(
                select(
                    func.count(ReviewQueueItem.id).filter(
                        ReviewQueueItem.inference_was_correct
                    ),
                    func.count(ReviewQueueItem.id).filter(
                        ReviewQueueItem.inference_was_correct.isnot(None)
                    ),
                )
            )
            accuracy_row = accuracy_result.one()
            correct_count = accuracy_row[0] or 0
            total_reviewed = accuracy_row[1] or 0

            inference_accuracy = None
            if total_reviewed > 0:
                inference_accuracy = correct_count / total_reviewed

            # Accuracy by method
            accuracy_by_method = {}
            methods_result = await session.execute(
                select(
                    ReviewQueueItem.inference_method,
                    func.count(ReviewQueueItem.id).filter(
                        ReviewQueueItem.inference_was_correct
                    ),
                    func.count(ReviewQueueItem.id),
                )
                .where(ReviewQueueItem.inference_was_correct.isnot(None))
                .group_by(ReviewQueueItem.inference_method)
            )
            for row in methods_result:
                method, correct, total = row
                if method and total > 0:
                    accuracy_by_method[method] = correct / total

            return ReviewQueueStats(
                total_pending=total_pending,
                total_completed=total_completed,
                by_priority=by_priority,
                avg_review_time_seconds=None,  # Would need to calculate from timestamps
                inference_accuracy=inference_accuracy,
                accuracy_by_method=accuracy_by_method,
            )

    async def get_pending_items(
        self,
        limit: int = 50,
        offset: int = 0,
        priority_filter: Optional[List[ReviewPriority]] = None,
    ) -> List[ReviewQueueItem]:
        """Get pending review items with pagination."""
        async with self.session_factory() as session:
            query = select(ReviewQueueItem).where(
                ReviewQueueItem.status == ReviewStatus.PENDING.value
            )

            if priority_filter:
                query = query.where(
                    ReviewQueueItem.priority.in_([p.value for p in priority_filter])
                )

            query = (
                query.order_by(
                    ReviewQueueItem.inference_confidence.asc(),
                    ReviewQueueItem.created_at.asc(),
                )
                .offset(offset)
                .limit(limit)
            )

            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_training_data(
        self,
        limit: int = 1000,
        only_unused: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get reviewed items for model training/improvement.

        Returns items with human labels that can be used to
        improve the inference model.

        Args:
            limit: Maximum items to return
            only_unused: Only return items not yet used for training

        Returns:
            List of training examples with input/output pairs
        """
        async with self.session_factory() as session:
            query = select(ReviewQueueItem).where(
                ReviewQueueItem.status == ReviewStatus.COMPLETED.value,
                ReviewQueueItem.human_status.isnot(None),
            )

            if only_unused:
                query = query.where(not ReviewQueueItem.feedback_used_for_training)

            query = query.limit(limit)

            result = await session.execute(query)
            items = result.scalars().all()

            training_data = []
            for item in items:
                training_data.append(
                    {
                        "input": {
                            "follow_up_message": item.follow_up_message,
                            "original_message": item.original_message,
                            "context": item.conversation_context,
                        },
                        "output": {
                            "status": item.human_status,
                            "confidence": item.human_confidence,
                        },
                        "inference": {
                            "status": item.inferred_status,
                            "confidence": item.inference_confidence,
                            "method": item.inference_method,
                            "was_correct": item.inference_was_correct,
                        },
                        "metadata": {
                            "review_id": item.id,
                            "capsule_id": item.capsule_id,
                            "reviewed_at": item.reviewed_at.isoformat()
                            if item.reviewed_at
                            else None,
                        },
                    }
                )

            return training_data

    async def mark_as_used_for_training(self, item_ids: List[str]) -> int:
        """Mark items as used for training (prevents re-use)."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(ReviewQueueItem).where(ReviewQueueItem.id.in_(item_ids))
            )
            items = result.scalars().all()

            for item in items:
                item.feedback_used_for_training = True

            await session.commit()
            return len(items)
