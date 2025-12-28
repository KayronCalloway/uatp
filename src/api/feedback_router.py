"""
Feedback API Router
===================

API endpoints for the hybrid outcome inference and calibration system.

Endpoints:
- POST /feedback/infer: Auto-infer outcome from follow-up message
- GET /feedback/queue: Get pending review items
- POST /feedback/queue/{id}/review: Submit human review
- GET /feedback/queue/stats: Queue statistics
- GET /feedback/calibration: Calibration metrics
- POST /feedback/calibration/record: Record outcome for calibration
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.feedback import (
    ReviewPriority,
    ReviewQueueManager,
    get_calibration_manager,
    get_inference_engine,
)

router = APIRouter(prefix="/feedback", tags=["Feedback & Calibration"])


# ============================================================================
# Request/Response Models
# ============================================================================


class InferOutcomeRequest(BaseModel):
    """Request to infer outcome from follow-up message."""

    follow_up_message: str = Field(..., description="User's follow-up message")
    capsule_id: Optional[str] = Field(None, description="Associated capsule ID")
    original_message: Optional[str] = Field(None, description="Original AI response")
    auto_queue_for_review: bool = Field(
        True, description="Automatically queue uncertain inferences for review"
    )


class InferOutcomeResponse(BaseModel):
    """Response from outcome inference."""

    status: str
    confidence: float
    method: str
    signals: List[str]
    needs_review: bool
    raw_scores: Dict[str, Any]
    queued_for_review: bool = False
    review_item_id: Optional[str] = None


class ReviewItemResponse(BaseModel):
    """A review queue item."""

    id: str
    capsule_id: str
    inferred_status: Optional[str]
    inference_confidence: Optional[float]
    inference_method: Optional[str]
    original_message: Optional[str]
    follow_up_message: Optional[str]
    priority: str
    status: str
    created_at: datetime


class SubmitReviewRequest(BaseModel):
    """Request to submit a human review."""

    human_status: str = Field(
        ..., description="Human-determined outcome: success/failure/partial"
    )
    reviewer_id: str = Field(..., description="ID of the reviewer")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Reviewer's confidence")
    notes: Optional[str] = Field(None, description="Optional review notes")


class QueueStatsResponse(BaseModel):
    """Review queue statistics."""

    total_pending: int
    total_completed: int
    by_priority: Dict[str, int]
    inference_accuracy: Optional[float]
    accuracy_by_method: Dict[str, float]


class CalibrationMetricsResponse(BaseModel):
    """Calibration metrics."""

    brier_score: float
    log_loss: float
    calibration_error: float
    sample_size: int
    reliability_diagram: Dict[str, float]


class RecordOutcomeRequest(BaseModel):
    """Request to record an outcome for calibration."""

    predicted_confidence: float = Field(..., ge=0.0, le=1.0)
    actual_outcome: str = Field(..., description="success/partial/failure")
    domain: str = Field("global", description="Domain/context for calibration")


class CalibrateRequest(BaseModel):
    """Request to calibrate a confidence score."""

    raw_confidence: float = Field(..., ge=0.0, le=1.0)
    domain: str = Field("global", description="Domain/context")


class CalibrateResponse(BaseModel):
    """Response with calibrated confidence."""

    raw_confidence: float
    calibrated_confidence: float
    domain: str
    adjustment: float


# ============================================================================
# Dependencies
# ============================================================================


# Session factory - will be set by app
_session_factory = None
_review_queue_manager: Optional[ReviewQueueManager] = None


def set_session_factory(factory):
    """Set the session factory (called during app startup)."""
    global _session_factory, _review_queue_manager
    _session_factory = factory
    _review_queue_manager = ReviewQueueManager(factory)


def get_review_queue() -> ReviewQueueManager:
    """Get the review queue manager."""
    if _review_queue_manager is None:
        raise HTTPException(
            status_code=500,
            detail="Review queue not initialized. Session factory not set.",
        )
    return _review_queue_manager


# ============================================================================
# Inference Endpoints
# ============================================================================


@router.post("/infer", response_model=InferOutcomeResponse)
async def infer_outcome(
    request: InferOutcomeRequest,
    queue: ReviewQueueManager = Depends(get_review_queue),
):
    """
    Infer outcome from a follow-up message.

    Uses hybrid approach:
    1. High-confidence keyword patterns (fast)
    2. Sentence embedding similarity (for ambiguous cases)
    3. Routes uncertain cases to human review queue
    """
    engine = get_inference_engine(use_embeddings=True)
    inference = engine.infer_outcome(request.follow_up_message)

    response = InferOutcomeResponse(
        status=inference.status.value,
        confidence=inference.confidence,
        method=inference.method,
        signals=inference.signals,
        needs_review=inference.needs_review,
        raw_scores=inference.raw_scores,
        queued_for_review=False,
    )

    # Auto-queue uncertain inferences for review
    if request.auto_queue_for_review and inference.needs_review and request.capsule_id:
        review_id = await queue.add_to_queue(
            capsule_id=request.capsule_id,
            inference=inference,
            original_message=request.original_message or "",
            follow_up_message=request.follow_up_message,
        )
        response.queued_for_review = True
        response.review_item_id = review_id

    return response


@router.post("/infer/behavioral", response_model=InferOutcomeResponse)
async def infer_from_behavior(
    time_to_next_message_seconds: Optional[float] = None,
    next_message_is_new_topic: Optional[bool] = None,
    user_implemented_suggestion: Optional[bool] = None,
    edit_distance_ratio: Optional[float] = None,
):
    """
    Infer outcome from behavioral signals (implicit feedback).

    Uses signals like:
    - Time until next message
    - Whether user moved to new topic
    - Whether suggestion was implemented in code
    - How much user modified the suggestion
    """
    engine = get_inference_engine()
    inference = engine.infer_from_behavioral_signals(
        time_to_next_message_seconds=time_to_next_message_seconds,
        next_message_is_new_topic=next_message_is_new_topic,
        user_implemented_suggestion=user_implemented_suggestion,
        edit_distance_ratio=edit_distance_ratio,
    )

    if inference is None:
        raise HTTPException(
            status_code=400, detail="Insufficient behavioral signals to infer outcome"
        )

    return InferOutcomeResponse(
        status=inference.status.value,
        confidence=inference.confidence,
        method=inference.method,
        signals=inference.signals,
        needs_review=inference.needs_review,
        raw_scores=inference.raw_scores,
    )


# ============================================================================
# Review Queue Endpoints
# ============================================================================


@router.get("/queue", response_model=List[ReviewItemResponse])
async def get_review_queue_items(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    queue: ReviewQueueManager = Depends(get_review_queue),
):
    """Get pending items in the review queue."""
    priority_filter = None
    if priority:
        try:
            priority_filter = [ReviewPriority(priority)]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid priority: {priority}. Valid: critical, high, medium, low",
            )

    items = await queue.get_pending_items(
        limit=limit,
        offset=offset,
        priority_filter=priority_filter,
    )

    return [
        ReviewItemResponse(
            id=item.id,
            capsule_id=item.capsule_id,
            inferred_status=item.inferred_status,
            inference_confidence=item.inference_confidence,
            inference_method=item.inference_method,
            original_message=item.original_message,
            follow_up_message=item.follow_up_message,
            priority=item.priority,
            status=item.status,
            created_at=item.created_at,
        )
        for item in items
    ]


@router.get("/queue/next", response_model=Optional[ReviewItemResponse])
async def get_next_review_item(
    reviewer_id: Optional[str] = Query(None, description="Reviewer ID for assignment"),
    queue: ReviewQueueManager = Depends(get_review_queue),
):
    """
    Get the next item for review (active learning priority).

    Items are returned by lowest confidence first (most uncertain = most informative).
    """
    item = await queue.get_next_for_review(reviewer_id=reviewer_id)

    if item is None:
        return None

    return ReviewItemResponse(
        id=item.id,
        capsule_id=item.capsule_id,
        inferred_status=item.inferred_status,
        inference_confidence=item.inference_confidence,
        inference_method=item.inference_method,
        original_message=item.original_message,
        follow_up_message=item.follow_up_message,
        priority=item.priority,
        status=item.status,
        created_at=item.created_at,
    )


@router.post("/queue/{item_id}/review")
async def submit_review(
    item_id: str,
    request: SubmitReviewRequest,
    queue: ReviewQueueManager = Depends(get_review_queue),
):
    """
    Submit a human review result.

    The human label will be used to:
    1. Update the capsule's actual outcome
    2. Track inference accuracy
    3. Improve calibration over time
    """
    # Validate status
    valid_statuses = {"success", "failure", "partial"}
    if request.human_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {request.human_status}. Valid: {valid_statuses}",
        )

    success = await queue.submit_review(
        item_id=item_id,
        human_status=request.human_status,
        reviewer_id=request.reviewer_id,
        human_confidence=request.confidence,
        notes=request.notes,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Review item not found")

    # Record for calibration
    manager = get_calibration_manager()
    outcome_map = {"success": 1.0, "partial": 0.5, "failure": 0.0}
    # We'd need to look up the original confidence - for now skip this
    # In production, this would update the calibrator

    return {"status": "reviewed", "item_id": item_id}


@router.get("/queue/stats", response_model=QueueStatsResponse)
async def get_queue_stats(
    queue: ReviewQueueManager = Depends(get_review_queue),
):
    """Get review queue statistics including inference accuracy."""
    stats = await queue.get_queue_stats()

    return QueueStatsResponse(
        total_pending=stats.total_pending,
        total_completed=stats.total_completed,
        by_priority=stats.by_priority,
        inference_accuracy=stats.inference_accuracy,
        accuracy_by_method=stats.accuracy_by_method,
    )


@router.get("/queue/training-data")
async def get_training_data(
    limit: int = Query(1000, ge=1, le=10000),
    only_unused: bool = Query(
        True, description="Only return data not yet used for training"
    ),
    queue: ReviewQueueManager = Depends(get_review_queue),
):
    """
    Get human-reviewed data for model training.

    Returns input/output pairs that can be used to improve
    the inference model.
    """
    data = await queue.get_training_data(limit=limit, only_unused=only_unused)
    return {"count": len(data), "data": data}


# ============================================================================
# Calibration Endpoints
# ============================================================================


@router.get("/calibration", response_model=Dict[str, CalibrationMetricsResponse])
async def get_calibration_metrics():
    """Get calibration metrics for all domains."""
    manager = get_calibration_manager()
    all_metrics = manager.get_all_metrics()

    def safe_float(val: float) -> float:
        """Convert inf to a safe JSON value."""
        import math

        if math.isinf(val):
            return 999999.0 if val > 0 else -999999.0
        return val

    return {
        domain: CalibrationMetricsResponse(
            brier_score=safe_float(metrics.brier_score),
            log_loss=safe_float(metrics.log_loss),
            calibration_error=safe_float(metrics.calibration_error),
            sample_size=metrics.sample_size,
            reliability_diagram=metrics.reliability_diagram,
        )
        for domain, metrics in all_metrics.items()
    }


@router.post("/calibration/record")
async def record_outcome_for_calibration(request: RecordOutcomeRequest):
    """
    Record an outcome for calibration tracking.

    This updates the calibration model to improve future predictions.
    """
    outcome_map = {"success": 1.0, "partial": 0.5, "failure": 0.0}

    if request.actual_outcome not in outcome_map:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid outcome: {request.actual_outcome}. Valid: success/partial/failure",
        )

    manager = get_calibration_manager()
    manager.record_outcome(
        predicted_confidence=request.predicted_confidence,
        actual_outcome=outcome_map[request.actual_outcome],
        domain=request.domain,
    )

    # Return updated metrics for this domain
    metrics = manager.get_calibrator(request.domain).get_metrics()

    return {
        "recorded": True,
        "domain": request.domain,
        "sample_size": metrics.sample_size,
        "calibration_error": metrics.calibration_error,
    }


@router.post("/calibration/calibrate", response_model=CalibrateResponse)
async def calibrate_confidence(request: CalibrateRequest):
    """
    Apply calibration to a raw confidence score.

    Returns the calibrated confidence based on historical data.
    """
    manager = get_calibration_manager()
    calibrated = manager.calibrate(request.raw_confidence, request.domain)

    return CalibrateResponse(
        raw_confidence=request.raw_confidence,
        calibrated_confidence=calibrated,
        domain=request.domain,
        adjustment=calibrated - request.raw_confidence,
    )


@router.get("/calibration/drift")
async def check_calibration_drift(
    threshold: float = Query(0.15, ge=0.05, le=0.5),
):
    """
    Check for calibration drift.

    Returns alerts for domains with concerning drift from predicted
    to actual outcomes.
    """
    manager = get_calibration_manager()
    alerts = manager.check_drift(threshold=threshold)

    return {
        "alerts": alerts,
        "has_drift": len(alerts) > 0,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
