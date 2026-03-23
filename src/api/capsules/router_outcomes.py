"""
Capsules Router - Outcome Tracking Operations
=============================================

Endpoints for recording and retrieving capsule outcomes.
"""

from fastapi import APIRouter

from ._shared import (
    AsyncSession,
    CapsuleModel,
    Depends,
    Dict,
    HTTPException,
    Optional,
    Query,
    func,
    get_current_user,
    get_db_session,
    is_admin_user,
    json,
    logger,
    select,
    to_uuid,
    utc_now,
)

router = APIRouter()


@router.post("/{capsule_id}/outcome")
async def record_capsule_outcome(
    capsule_id: str,
    outcome_status: str = Query(
        ...,
        description="Outcome status: success, failure, partial, pending, unknown",
    ),
    notes: Optional[str] = Query(None, description="Notes about the outcome"),
    rating: Optional[float] = Query(
        None, ge=1, le=5, description="User rating from 1-5"
    ),
    feedback: Optional[str] = Query(None, description="User feedback text"),
    metrics: Optional[str] = Query(
        None, description="JSON string of structured metrics"
    ),
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Record the outcome of a capsule's suggestions/decisions.

    This enables tracking whether AI suggestions worked out,
    which is critical for:
    - Confidence calibration
    - Model improvement
    - Identifying failure patterns

    Users can only record outcomes for their own capsules.
    """
    user_is_admin = is_admin_user(current_user)
    user_id = current_user.get("user_id")

    try:
        # Validate outcome status
        valid_statuses = {"success", "failure", "partial", "pending", "unknown"}
        if outcome_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid outcome_status. Must be one of: {valid_statuses}",
            )

        # Find the capsule
        query = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
        result = await session.execute(query)
        capsule = result.scalar_one_or_none()

        if not capsule:
            raise HTTPException(status_code=404, detail="Capsule not found")

        # Verify ownership
        if not user_is_admin:
            if capsule.owner_id is None:
                raise HTTPException(
                    status_code=403, detail="Access denied: legacy capsule"
                )
            if str(capsule.owner_id) != user_id:
                raise HTTPException(status_code=403, detail="Access denied")

        # Parse metrics if provided
        parsed_metrics = None
        if metrics:
            try:
                parsed_metrics = json.loads(metrics)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, detail="Invalid JSON in metrics parameter"
                )

        # Update the capsule with outcome data
        capsule.outcome_status = outcome_status
        capsule.outcome_timestamp = utc_now()
        capsule.outcome_notes = notes
        capsule.outcome_metrics = parsed_metrics
        capsule.user_feedback_rating = rating
        capsule.user_feedback_text = feedback

        await session.commit()

        logger.info(f" Recorded outcome for {capsule_id}: {outcome_status}")

        return {
            "capsule_id": capsule_id,
            "outcome_status": outcome_status,
            "outcome_timestamp": capsule.outcome_timestamp.isoformat(),
            "message": f"Outcome recorded: {outcome_status}",
            "rating": rating,
            "has_metrics": parsed_metrics is not None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Outcome recording error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to record outcome: {str(e)}"
        )


@router.get("/{capsule_id}/outcome")
async def get_capsule_outcome(
    capsule_id: str,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get the recorded outcome for a specific capsule (users see own capsules only)."""
    user_is_admin = is_admin_user(current_user)
    user_id = current_user.get("user_id")

    try:
        query = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
        result = await session.execute(query)
        capsule = result.scalar_one_or_none()

        if not capsule:
            raise HTTPException(status_code=404, detail="Capsule not found")

        # Verify ownership
        if not user_is_admin:
            if capsule.owner_id is None:
                raise HTTPException(
                    status_code=403, detail="Access denied: legacy capsule"
                )
            if str(capsule.owner_id) != user_id:
                raise HTTPException(status_code=403, detail="Access denied")

        return {
            "capsule_id": capsule_id,
            "outcome_status": capsule.outcome_status,
            "outcome_timestamp": capsule.outcome_timestamp.isoformat()
            if capsule.outcome_timestamp
            else None,
            "outcome_notes": capsule.outcome_notes,
            "outcome_metrics": capsule.outcome_metrics,
            "user_feedback_rating": capsule.user_feedback_rating,
            "user_feedback_text": capsule.user_feedback_text,
            "follow_up_capsule_ids": capsule.follow_up_capsule_ids,
            "has_outcome": capsule.outcome_status is not None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get outcome error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get outcome: {str(e)}")


@router.get("/outcomes/stats")
async def get_outcome_statistics(
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get aggregate statistics on capsule outcomes (user sees own capsule stats only).

    Useful for:
    - Tracking overall system accuracy
    - Identifying areas needing improvement
    - Confidence calibration analysis
    """
    user_is_admin = is_admin_user(current_user)
    user_id = current_user.get("user_id")

    try:
        # Count by outcome status
        status_query = select(
            CapsuleModel.outcome_status, func.count(CapsuleModel.id)
        ).group_by(CapsuleModel.outcome_status)
        # Non-admin users only see their own capsule stats
        if not user_is_admin:
            status_query = status_query.where(CapsuleModel.owner_id == to_uuid(user_id))
        status_result = await session.execute(status_query)
        status_counts = {
            status or "untracked": count for status, count in status_result.fetchall()
        }

        # Average rating
        rating_query = select(func.avg(CapsuleModel.user_feedback_rating)).where(
            CapsuleModel.user_feedback_rating.isnot(None)
        )
        if not user_is_admin:
            rating_query = rating_query.where(CapsuleModel.owner_id == to_uuid(user_id))
        rating_result = await session.execute(rating_query)
        avg_rating = rating_result.scalar()

        # Count with feedback
        feedback_count_query = select(func.count(CapsuleModel.id)).where(
            CapsuleModel.user_feedback_text.isnot(None)
        )
        if not user_is_admin:
            feedback_count_query = feedback_count_query.where(
                CapsuleModel.owner_id == to_uuid(user_id)
            )
        feedback_result = await session.execute(feedback_count_query)
        feedback_count = feedback_result.scalar() or 0

        # Calculate success rate
        total_tracked = sum(
            count
            for status, count in status_counts.items()
            if status not in ("untracked", "pending", "unknown", None)
        )
        success_count = (
            status_counts.get("success", 0) + status_counts.get("partial", 0) * 0.5
        )
        success_rate = (success_count / total_tracked * 100) if total_tracked > 0 else 0

        return {
            "outcome_counts": status_counts,
            "total_tracked": total_tracked,
            "total_untracked": status_counts.get("untracked", 0),
            "success_rate_percent": round(success_rate, 1),
            "average_rating": round(avg_rating, 2) if avg_rating else None,
            "capsules_with_feedback": feedback_count,
            "message": "Outcome statistics calculated",
        }

    except Exception as e:
        logger.error(f"Outcome stats error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get outcome stats: {str(e)}"
        )


@router.post("/{capsule_id}/link-followup")
async def link_followup_capsule(
    capsule_id: str,
    followup_capsule_id: str = Query(..., description="ID of the follow-up capsule"),
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Link a follow-up capsule to an original capsule.

    This tracks conversation chains and related decisions.
    Users can only link their own capsules.
    """
    user_is_admin = is_admin_user(current_user)
    user_id = current_user.get("user_id")
    try:
        # Find the original capsule
        query = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
        result = await session.execute(query)
        capsule = result.scalar_one_or_none()

        if not capsule:
            raise HTTPException(status_code=404, detail="Original capsule not found")

        # Verify ownership of original capsule
        if not user_is_admin:
            if capsule.owner_id is None:
                raise HTTPException(
                    status_code=403, detail="Access denied: legacy capsule"
                )
            if str(capsule.owner_id) != user_id:
                raise HTTPException(status_code=403, detail="Access denied")

        # Verify follow-up capsule exists
        followup_query = select(CapsuleModel).where(
            CapsuleModel.capsule_id == followup_capsule_id
        )
        followup_result = await session.execute(followup_query)
        followup = followup_result.scalar_one_or_none()

        if not followup:
            raise HTTPException(status_code=404, detail="Follow-up capsule not found")

        # Verify ownership of follow-up capsule (must also own it)
        if not user_is_admin:
            if followup.owner_id is None:
                raise HTTPException(
                    status_code=403, detail="Access denied: legacy follow-up capsule"
                )
            if str(followup.owner_id) != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: cannot link capsule you don't own",
                )

        # Add to follow-up list
        current_followups = capsule.follow_up_capsule_ids or []
        if followup_capsule_id not in current_followups:
            current_followups.append(followup_capsule_id)
            capsule.follow_up_capsule_ids = current_followups
            await session.commit()

        return {
            "capsule_id": capsule_id,
            "followup_capsule_id": followup_capsule_id,
            "total_followups": len(current_followups),
            "message": "Follow-up capsule linked",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Link followup error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to link follow-up: {str(e)}"
        )
