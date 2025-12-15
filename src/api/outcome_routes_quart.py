"""
Outcome Tracking API Routes (Quart Blueprint)
Endpoints for recording and retrieving capsule outcomes
"""

from datetime import datetime, timezone

from quart import Blueprint, jsonify, request
from sqlalchemy import and_, func, select

from src.core.database import db
from src.models.outcome import (
    CapsuleOutcomeModel,
    ConfidenceCalibrationModel,
    ReasoningPatternModel,
)

outcome_bp = Blueprint("outcomes", __name__)


@outcome_bp.route("/outcomes", methods=["POST"])
async def create_outcome():
    """
    Record an outcome for a capsule.

    Body:
        {
            "capsule_id": "caps_...",
            "predicted_outcome": "...",
            "actual_outcome": "...",
            "outcome_quality_score": 0.8,
            "validation_method": "user_feedback",
            "validator_id": "user_123",
            "notes": "..."
        }
    """
    data = await request.get_json()

    outcome_model = CapsuleOutcomeModel(
        capsule_id=data["capsule_id"],
        predicted_outcome=data.get("predicted_outcome"),
        actual_outcome=data["actual_outcome"],
        outcome_quality_score=data.get("outcome_quality_score"),
        validation_method=data.get("validation_method"),
        validator_id=data.get("validator_id"),
        notes=data.get("notes"),
        outcome_timestamp=datetime.now(timezone.utc),
    )

    async with db.get_session() as session:
        session.add(outcome_model)
        await session.commit()
        await session.refresh(outcome_model)

        return (
            jsonify(
                {
                    "id": outcome_model.id,
                    "capsule_id": outcome_model.capsule_id,
                    "actual_outcome": outcome_model.actual_outcome,
                    "outcome_quality_score": outcome_model.outcome_quality_score,
                    "created_at": outcome_model.created_at.isoformat(),
                }
            ),
            201,
        )


@outcome_bp.route("/outcomes/<capsule_id>", methods=["GET"])
async def get_outcomes_for_capsule(capsule_id: str):
    """Get all outcomes recorded for a specific capsule."""
    async with db.get_session() as session:
        query = (
            select(CapsuleOutcomeModel)
            .where(CapsuleOutcomeModel.capsule_id == capsule_id)
            .order_by(CapsuleOutcomeModel.outcome_timestamp.desc())
        )

        result = await session.execute(query)
        outcomes = result.scalars().all()

        return jsonify(
            {
                "outcomes": [
                    {
                        "id": o.id,
                        "capsule_id": o.capsule_id,
                        "predicted_outcome": o.predicted_outcome,
                        "actual_outcome": o.actual_outcome,
                        "outcome_quality_score": o.outcome_quality_score,
                        "outcome_timestamp": o.outcome_timestamp.isoformat(),
                        "validation_method": o.validation_method,
                        "validator_id": o.validator_id,
                        "notes": o.notes,
                        "created_at": o.created_at.isoformat(),
                    }
                    for o in outcomes
                ],
                "total": len(outcomes),
            }
        )


@outcome_bp.route("/outcomes/pending", methods=["GET"])
async def get_pending_outcomes():
    """Get capsules that don't have outcomes yet (pending validation)."""
    limit = int(request.args.get("limit", 50))

    from src.models.capsule import CapsuleModel

    async with db.get_session() as session:
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

        return jsonify(
            {
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
        )


@outcome_bp.route("/outcomes/calibration/data", methods=["GET"])
async def get_calibration_data():
    """Get confidence calibration data."""
    domain = request.args.get("domain")

    async with db.get_session() as session:
        query = select(ConfidenceCalibrationModel)

        if domain:
            query = query.where(ConfidenceCalibrationModel.domain == domain)

        query = query.order_by(ConfidenceCalibrationModel.confidence_bucket)

        result = await session.execute(query)
        calibration_data = result.scalars().all()

        return jsonify(
            {
                "calibration_data": [
                    {
                        "domain": cd.domain,
                        "confidence_bucket": cd.confidence_bucket,
                        "predicted_count": cd.predicted_count,
                        "actual_success_count": cd.actual_success_count,
                        "calibration_error": cd.calibration_error,
                        "recommended_adjustment": cd.recommended_adjustment,
                        "success_rate": (
                            cd.actual_success_count / cd.predicted_count
                            if cd.predicted_count > 0
                            else 0.0
                        ),
                    }
                    for cd in calibration_data
                ],
                "total": len(calibration_data),
            }
        )


@outcome_bp.route("/outcomes/calibration/update", methods=["POST"])
async def update_calibration():
    """Recalculate calibration data based on recorded outcomes."""
    from src.models.capsule import CapsuleModel

    async with db.get_session() as session:
        # Get all outcomes with their capsules
        query = select(CapsuleOutcomeModel, CapsuleModel).join(
            CapsuleModel, CapsuleOutcomeModel.capsule_id == CapsuleModel.capsule_id
        )

        result = await session.execute(query)
        outcome_capsule_pairs = result.all()

        if not outcome_capsule_pairs:
            return jsonify({"message": "No outcomes to calibrate", "updated": 0})

        # Group by domain and confidence bucket
        calibration_buckets = {}

        for outcome, capsule in outcome_capsule_pairs:
            # Extract confidence from capsule
            confidence = None
            if isinstance(capsule.payload, dict):
                confidence = capsule.payload.get("confidence")

            if confidence is None:
                continue

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
            recommended_adjustment = -calibration_error * 0.5

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
                existing.sample_capsule_ids = data["capsule_ids"][:10]
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

        return jsonify(
            {
                "message": f"Updated calibration for {updated} buckets",
                "updated": updated,
                "total_outcomes_processed": len(outcome_capsule_pairs),
            }
        )


@outcome_bp.route("/outcomes/patterns", methods=["GET"])
async def get_reasoning_patterns():
    """Get discovered reasoning patterns."""
    pattern_type = request.args.get("pattern_type")
    min_success_rate = request.args.get("min_success_rate", type=float)
    limit = int(request.args.get("limit", 50))

    async with db.get_session() as session:
        query = select(ReasoningPatternModel)

        if pattern_type:
            query = query.where(ReasoningPatternModel.pattern_type == pattern_type)

        if min_success_rate is not None:
            query = query.where(ReasoningPatternModel.success_rate >= min_success_rate)

        query = query.order_by(ReasoningPatternModel.success_rate.desc()).limit(limit)

        result = await session.execute(query)
        patterns = result.scalars().all()

        return jsonify(
            {
                "patterns": [
                    {
                        "pattern_id": p.pattern_id,
                        "pattern_type": p.pattern_type,
                        "pattern_name": p.pattern_name,
                        "pattern_description": p.pattern_description,
                        "pattern_structure": p.pattern_structure,
                        "success_rate": p.success_rate,
                        "usage_count": p.usage_count,
                        "applicable_domains": p.applicable_domains,
                        "example_capsule_ids": p.example_capsule_ids,
                        "confidence_impact": p.confidence_impact,
                        "created_at": p.created_at.isoformat(),
                    }
                    for p in patterns
                ],
                "total": len(patterns),
            }
        )


@outcome_bp.route("/outcomes/stats", methods=["GET"])
async def get_outcome_stats():
    """Get summary statistics for outcomes."""
    async with db.get_session() as session:
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

        return jsonify(
            {
                "total_outcomes": total_outcomes,
                "average_quality_score": round(float(avg_quality), 3),
                "outcomes_by_validation_method": by_method,
                "total_patterns_discovered": total_patterns,
            }
        )
