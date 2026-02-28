"""
Outcome Tracking API Routes
Endpoints for recording and retrieving capsule outcomes
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import db
from src.models.outcome import (
    CalibrationDataResponse,
    CapsuleOutcomeModel,
    ConfidenceCalibrationModel,
    OutcomeCreate,
    OutcomeListResponse,
    OutcomeResponse,
    ReasoningPatternListResponse,
    ReasoningPatternModel,
    ReasoningPatternResponse,
)

router = APIRouter(prefix="/outcomes", tags=["outcomes"])


@router.post("/", response_model=OutcomeResponse, status_code=201)
async def create_outcome(
    outcome: OutcomeCreate, session: AsyncSession = Depends(db.get_session)
):
    """
    Record an outcome for a capsule.

    This allows tracking what actually happened after a capsule's prediction,
    enabling confidence calibration and learning.
    """
    outcome_model = CapsuleOutcomeModel(
        capsule_id=outcome.capsule_id,
        predicted_outcome=outcome.predicted_outcome,
        actual_outcome=outcome.actual_outcome,
        outcome_quality_score=outcome.outcome_quality_score,
        validation_method=outcome.validation_method,
        validator_id=outcome.validator_id,
        notes=outcome.notes,
        outcome_timestamp=datetime.now(timezone.utc),
    )

    session.add(outcome_model)
    await session.commit()
    await session.refresh(outcome_model)

    return OutcomeResponse.model_validate(outcome_model)


@router.get("/{capsule_id}", response_model=OutcomeListResponse)
async def get_outcomes_for_capsule(
    capsule_id: str, session: AsyncSession = Depends(db.get_session)
):
    """
    Get all outcomes recorded for a specific capsule.
    """
    query = (
        select(CapsuleOutcomeModel)
        .where(CapsuleOutcomeModel.capsule_id == capsule_id)
        .order_by(CapsuleOutcomeModel.outcome_timestamp.desc())
    )

    result = await session.execute(query)
    outcomes = result.scalars().all()
    outcomes = [o for o in outcomes if o is not None]  # Filter None values

    return OutcomeListResponse(
        outcomes=[OutcomeResponse.model_validate(o) for o in outcomes],
        total=len(outcomes),
    )


@router.get("/pending/list", response_model=dict)
async def get_pending_outcomes(
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(db.get_session),
):
    """
    Get capsules that don't have outcomes yet (pending validation).

    Returns capsules from the last 7 days that haven't been validated.
    """
    # This is a complex query - get capsules without outcomes
    from src.models.capsule import CapsuleModel

    # Subquery for capsule IDs that have outcomes
    outcome_subquery = select(CapsuleOutcomeModel.capsule_id).distinct()

    # Get capsules without outcomes
    query = (
        select(CapsuleModel)
        .where(CapsuleModel.capsule_id.notin_(outcome_subquery))
        .order_by(CapsuleModel.timestamp.desc())
        .limit(limit)
    )

    result = await session.execute(query)
    capsules = result.scalars().all()
    capsules = [c for c in capsules if c is not None]  # Filter None values

    return {
        "pending_capsules": [
            {
                "capsule_id": c.capsule_id,
                "capsule_type": c.capsule_type,
                "timestamp": c.timestamp.isoformat(),
                "payload_preview": (
                    c.payload.get("prompt", "")[:100]
                    if isinstance(c.payload, dict)
                    else str(c.payload)[:100]
                ),
            }
            for c in capsules
        ],
        "total": len(capsules),
    }


@router.get("/calibration/data", response_model=List[CalibrationDataResponse])
async def get_calibration_data(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    session: AsyncSession = Depends(db.get_session),
):
    """
    Get confidence calibration data.

    Shows how well confidence predictions match actual outcomes.
    """
    query = select(ConfidenceCalibrationModel)

    if domain:
        query = query.where(ConfidenceCalibrationModel.domain == domain)

    query = query.order_by(ConfidenceCalibrationModel.confidence_bucket)

    result = await session.execute(query)
    calibration_data = result.scalars().all()
    calibration_data = [cd for cd in calibration_data if cd is not None]  # Filter None values

    return [
        CalibrationDataResponse(
            domain=cd.domain,
            confidence_bucket=cd.confidence_bucket,
            predicted_count=cd.predicted_count,
            actual_success_count=cd.actual_success_count,
            calibration_error=cd.calibration_error,
            recommended_adjustment=cd.recommended_adjustment,
            success_rate=(
                cd.actual_success_count / cd.predicted_count
                if cd.predicted_count > 0
                else 0.0
            ),
        )
        for cd in calibration_data
    ]


@router.post("/calibration/update", status_code=200)
async def update_calibration(session: AsyncSession = Depends(db.get_session)):
    """
    Recalculate calibration data based on recorded outcomes.

    This analyzes all outcomes and updates the calibration table.
    """
    # This is a complex operation - get all outcomes with their capsule confidence
    from src.models.capsule import CapsuleModel

    # Get all outcomes with their capsules
    query = select(CapsuleOutcomeModel, CapsuleModel).join(
        CapsuleModel, CapsuleOutcomeModel.capsule_id == CapsuleModel.capsule_id
    )

    result = await session.execute(query)
    outcome_capsule_pairs = result.all()

    if not outcome_capsule_pairs:
        return {"message": "No outcomes to calibrate", "updated": 0}

    # Group by domain and confidence bucket
    calibration_buckets = {}

    for outcome, capsule in outcome_capsule_pairs:
        # Extract confidence from capsule
        confidence = None
        if isinstance(capsule.payload, dict):
            confidence = capsule.payload.get("confidence")

        if confidence is None:
            continue  # Skip capsules without confidence

        # Extract domain from session_metadata
        domain = "general"
        if isinstance(capsule.payload, dict):
            session_metadata = capsule.payload.get("session_metadata", {})
            domain = session_metadata.get("problem_domain", "general")

        # Round confidence to nearest 0.1 for bucketing
        confidence_bucket = round(confidence * 10) / 10

        # Create bucket key
        key = (domain, confidence_bucket)

        if key not in calibration_buckets:
            calibration_buckets[key] = {
                "domain": domain,
                "confidence_bucket": confidence_bucket,
                "predicted_count": 0,
                "actual_success_count": 0,
                "capsule_ids": [],
            }

        calibration_buckets[key]["predicted_count"] += 1
        calibration_buckets[key]["capsule_ids"].append(capsule.capsule_id)

        # Count as success if quality score > 0.7 or if no score but actual matches predicted
        is_success = (
            outcome.outcome_quality_score > 0.7
            if outcome.outcome_quality_score
            else outcome.actual_outcome == outcome.predicted_outcome
        )

        if is_success:
            calibration_buckets[key]["actual_success_count"] += 1

    # Update calibration table
    updated = 0
    for (domain, bucket), data in calibration_buckets.items():
        actual_rate = data["actual_success_count"] / data["predicted_count"]
        calibration_error = bucket - actual_rate
        recommended_adjustment = -calibration_error * 0.5  # Conservative adjustment

        # Upsert calibration data
        existing_query = select(ConfidenceCalibrationModel).where(
            and_(
                ConfidenceCalibrationModel.domain == domain,
                ConfidenceCalibrationModel.confidence_bucket == bucket,
            )
        )
        existing_result = await session.execute(existing_query)
        existing = existing_result.scalar_one_or_none()

        if existing:
            existing.predicted_count = data["predicted_count"]
            existing.actual_success_count = data["actual_success_count"]
            existing.calibration_error = calibration_error
            existing.recommended_adjustment = recommended_adjustment
            existing.sample_capsule_ids = data["capsule_ids"][
                :10
            ]  # Keep max 10 samples
            existing.last_updated = datetime.now(timezone.utc)
        else:
            new_calibration = ConfidenceCalibrationModel(
                domain=domain,
                confidence_bucket=bucket,
                predicted_count=data["predicted_count"],
                actual_success_count=data["actual_success_count"],
                calibration_error=calibration_error,
                recommended_adjustment=recommended_adjustment,
                sample_capsule_ids=data["capsule_ids"][:10],
                last_updated=datetime.now(timezone.utc),
            )
            session.add(new_calibration)

        updated += 1

    await session.commit()

    return {
        "message": f"Updated calibration for {updated} buckets",
        "updated": updated,
        "total_outcomes_processed": len(outcome_capsule_pairs),
    }


@router.get("/patterns/list", response_model=ReasoningPatternListResponse)
async def get_reasoning_patterns(
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type"),
    min_success_rate: Optional[float] = Query(
        None, ge=0, le=1, description="Minimum success rate"
    ),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(db.get_session),
):
    """
    Get discovered reasoning patterns.

    Returns patterns that have been identified across multiple capsules.
    """
    query = select(ReasoningPatternModel)

    if pattern_type:
        query = query.where(ReasoningPatternModel.pattern_type == pattern_type)

    if min_success_rate is not None:
        query = query.where(ReasoningPatternModel.success_rate >= min_success_rate)

    query = query.order_by(ReasoningPatternModel.success_rate.desc()).limit(limit)

    result = await session.execute(query)
    patterns = result.scalars().all()
    patterns = [p for p in patterns if p is not None]  # Filter None values

    return ReasoningPatternListResponse(
        patterns=[ReasoningPatternResponse.model_validate(p) for p in patterns],
        total=len(patterns),
    )


@router.get("/patterns/{pattern_id}", response_model=ReasoningPatternResponse)
async def get_pattern(pattern_id: str, session: AsyncSession = Depends(db.get_session)):
    """
    Get details of a specific reasoning pattern.
    """
    query = select(ReasoningPatternModel).where(
        ReasoningPatternModel.pattern_id == pattern_id
    )

    result = await session.execute(query)
    pattern = result.scalar_one_or_none()

    if not pattern:
        raise HTTPException(status_code=404, detail=f"Pattern {pattern_id} not found")

    return ReasoningPatternResponse.model_validate(pattern)


@router.get("/stats/summary", response_model=dict)
async def get_outcome_stats(session: AsyncSession = Depends(db.get_session)):
    """
    Get summary statistics for outcomes.
    """
    # Total outcomes
    total_query = select(func.count()).select_from(CapsuleOutcomeModel)
    total_result = await session.execute(total_query)
    total_outcomes = total_result.scalar()

    # Average quality score
    avg_query = select(func.avg(CapsuleOutcomeModel.outcome_quality_score)).where(
        CapsuleOutcomeModel.outcome_quality_score.isnot(None)
    )
    avg_result = await session.execute(avg_query)
    avg_quality = avg_result.scalar() or 0.0

    # By validation method
    method_query = select(
        CapsuleOutcomeModel.validation_method, func.count().label("count")
    ).group_by(CapsuleOutcomeModel.validation_method)
    method_result = await session.execute(method_query)
    by_method = {row[0] or "unknown": row[1] for row in method_result}

    # Total patterns
    pattern_query = select(func.count()).select_from(ReasoningPatternModel)
    pattern_result = await session.execute(pattern_query)
    total_patterns = pattern_result.scalar()

    return {
        "total_outcomes": total_outcomes,
        "average_quality_score": round(float(avg_quality), 3),
        "outcomes_by_validation_method": by_method,
        "total_patterns_discovered": total_patterns,
    }
