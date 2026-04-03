"""
Calibration API Router - Expose calibration metrics via REST API.

Endpoints:
- GET /calibration/metrics - Get overall calibration metrics
- GET /calibration/pending - Get capsules awaiting outcome recording
- POST /calibration/outcomes - Record an outcome for a capsule
- GET /calibration/context - Get calibration context for prompt injection
"""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.calibration.metrics import build_calibration_context, calculate_calibration
from src.calibration.queries import CalibrationQueries

router = APIRouter(prefix="/calibration", tags=["calibration"])


class OutcomeRequest(BaseModel):
    """Request body for recording an outcome."""

    capsule_id: str = Field(..., description="The capsule to record outcome for")
    outcome_type: str = Field(
        ...,
        description="worked, failed, partial, accepted, rejected, refined, abandoned",
    )
    evidence: Optional[str] = Field(
        None, description="Evidence or notes about the outcome"
    )
    confidence: float = Field(
        0.9, ge=0.0, le=1.0, description="How confident are we about this outcome?"
    )


class CalibrationResponse(BaseModel):
    """Response containing calibration metrics."""

    total_predictions: int
    predictions_with_outcomes: int
    overconfidence_score: float
    calibration_quality: str
    confidence_buckets: dict
    outcome_distribution: dict
    uncertainty_hit_rate: float
    missed_error_rate: float
    calculated_at: Optional[str]


class PendingCapsule(BaseModel):
    """A capsule awaiting outcome recording."""

    capsule_id: str
    timestamp: str
    claimed_confidence: float
    prompt_preview: str


@router.get("/metrics", response_model=CalibrationResponse)
async def get_calibration_metrics(
    model: Optional[str] = Query(None, description="Filter by model (e.g., 'gemma')"),
    since_days: Optional[int] = Query(
        None, description="Only include data from last N days"
    ),
):
    """
    Get calibration metrics calculated from historical comparison.

    These metrics measure the gap between model self-assessment and actual outcomes.
    The learning happens in the comparison, not the reflection.
    """
    since = None
    if since_days:
        from datetime import timedelta

        since = datetime.now() - timedelta(days=since_days)

    metrics = calculate_calibration(model=model, since=since)

    return CalibrationResponse(
        total_predictions=metrics.total_predictions,
        predictions_with_outcomes=metrics.predictions_with_outcomes,
        overconfidence_score=metrics.overconfidence_score,
        calibration_quality=metrics.calibration_quality(),
        confidence_buckets=metrics.confidence_buckets,
        outcome_distribution=metrics.outcome_distribution,
        uncertainty_hit_rate=metrics.uncertainty_hit_rate,
        missed_error_rate=metrics.missed_error_rate,
        calculated_at=metrics.calculated_at.isoformat()
        if metrics.calculated_at
        else None,
    )


@router.get("/pending")
async def get_pending_outcomes():
    """
    Get capsules that have self-assessments but no outcomes yet.

    These are candidates for outcome recording.
    """
    queries = CalibrationQueries()
    pending = queries.get_capsules_pending_outcomes()

    return {"count": len(pending), "capsules": pending}


@router.post("/outcomes")
async def record_outcome(request: OutcomeRequest):
    """
    Record an outcome for a capsule.

    This creates a new outcome capsule linked to the original,
    enabling calibration measurement.
    """
    from src.integrations.outcome_recorder import OutcomeRecorder, OutcomeType

    # Map string to enum
    try:
        outcome_type = OutcomeType(request.outcome_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid outcome_type. Must be one of: {[e.value for e in OutcomeType]}",
        )

    recorder = OutcomeRecorder()
    result = recorder.record_outcome(
        capsule_id=request.capsule_id,
        outcome_type=outcome_type,
        evidence=request.evidence,
        outcome_confidence=request.confidence,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Capsule not found or could not record outcome: {request.capsule_id}",
        )

    return {
        "outcome_capsule_id": result,
        "original_capsule_id": request.capsule_id,
        "outcome_type": request.outcome_type,
        "message": "Outcome recorded successfully",
    }


@router.get("/context")
async def get_calibration_context(
    model: Optional[str] = Query(None, description="Filter by model"),
    min_samples: int = Query(10, description="Minimum samples required for context"),
):
    """
    Get calibration context for prompt injection.

    This is the feedback loop: inject historical calibration data
    into new prompts so the model can adjust its confidence.

    The feedback comes from MEASURED OUTCOMES, not model self-assessment.
    """
    context = build_calibration_context(model=model, min_samples=min_samples)

    return {
        "context": context,
        "min_samples_required": min_samples,
        "note": "Inject this context into prompts to help models calibrate confidence",
    }


@router.get("/data")
async def get_calibration_data(
    limit: int = Query(100, le=1000, description="Maximum records to return"),
):
    """
    Get raw calibration data points for custom analysis.

    Each data point contains:
    - Original capsule info
    - Self-assessment claims
    - Measured outcome
    - Calculated deviation
    """
    queries = CalibrationQueries()
    data_points = queries.get_calibration_data(limit=limit)

    return {
        "count": len(data_points),
        "data": [
            {
                "capsule_id": dp.capsule_id,
                "timestamp": dp.timestamp.isoformat(),
                "claimed_confidence": dp.claimed_confidence,
                "uncertainty_areas": dp.uncertainty_areas,
                "outcome_type": dp.outcome_type,
                "deviation": dp.deviation,
                "prompt_preview": dp.prompt_preview,
                "model": dp.model,
            }
            for dp in data_points
        ],
    }
