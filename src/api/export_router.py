"""
Training Data Export Router
===========================

Exports capsules in formats suitable for LLM fine-tuning:
- JSONL (OpenAI fine-tuning format)
- Preference pairs (RLHF/DPO training)
- Raw capsule data (custom training pipelines)

Usage:
    GET /export/training?format=jsonl&min_confidence=0.7
    GET /export/preferences
    GET /export/outcomes
"""

import json
import logging
from datetime import datetime
from io import StringIO
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import db
from ..models.capsule import CapsuleModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Export"])


async def get_db_session():
    """Dependency to get database session"""
    async with db.get_session() as session:
        yield session


def capsule_to_openai_format(capsule: CapsuleModel) -> Optional[Dict[str, Any]]:
    """
    Convert a capsule to OpenAI fine-tuning JSONL format.

    Creates clean user→assistant pairs from capsule data.
    Each capsule becomes ONE training example with:
    - system: context about the task
    - user: the prompt/request
    - assistant: synthesized response from reasoning steps

    Format:
    {"messages": [{"role": "system", "content": "..."},
                  {"role": "user", "content": "..."},
                  {"role": "assistant", "content": "..."}]}
    """
    try:
        payload = capsule.payload
        if isinstance(payload, str):
            payload = json.loads(payload)

        # Get the user's request
        prompt = payload.get('prompt', '')
        if not prompt or len(prompt) < 10:
            return None

        # Get reasoning steps for the response
        reasoning_steps = payload.get("reasoning_steps", [])
        if not reasoning_steps:
            return None

        # Build assistant response from unique, high-quality steps
        seen_content = set()
        response_parts = []

        # Prioritize final_answer if available
        final_answer = payload.get("final_answer", "")
        if final_answer and len(final_answer) > 20:
            response_parts.append(final_answer)
            seen_content.add(hash(final_answer[:100]))

        # Add key reasoning steps (deduplicated)
        for step in reasoning_steps:
            if not isinstance(step, dict):
                continue

            content = step.get("reasoning", "")
            if not content or len(content) < 20:
                continue

            # Deduplicate
            content_hash = hash(content[:100])
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)

            # Only include substantive steps (skip meta-commentary)
            operation = step.get("operation", "").lower()
            if operation in {"analysis", "implementation", "synthesis", "answer"}:
                # Limit to first 500 chars of each step
                response_parts.append(content[:500])

            # Cap at 5 steps to keep response reasonable
            if len(response_parts) >= 5:
                break

        if not response_parts:
            return None

        # Combine into final response
        assistant_response = "\n\n".join(response_parts)

        # Ensure reasonable length (OpenAI has token limits)
        if len(assistant_response) > 4000:
            assistant_response = assistant_response[:4000] + "..."

        # Build the training example
        messages = [
            {"role": "system", "content": "You are an expert AI assistant helping with software development, code review, and technical problem-solving."},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": assistant_response}
        ]

        return {"messages": messages}

    except Exception as e:
        logger.debug(f"Failed to convert capsule {capsule.capsule_id}: {e}")
        return None


def capsule_to_preference_pair(
    capsule_a: CapsuleModel,
    capsule_b: CapsuleModel
) -> Optional[Dict[str, Any]]:
    """
    Create a preference pair from two capsules (for DPO/RLHF training).

    The capsule with higher outcome quality is preferred.
    """
    try:
        # Get outcome scores
        metrics_a = capsule_a.outcome_metrics or {}
        metrics_b = capsule_b.outcome_metrics or {}

        conf_a = metrics_a.get("inference_confidence", 0)
        conf_b = metrics_b.get("inference_confidence", 0)

        outcome_a = capsule_a.outcome_status
        outcome_b = capsule_b.outcome_status

        # Score outcomes
        outcome_scores = {"success": 1.0, "partial": 0.5, "failure": 0.0}
        score_a = outcome_scores.get(outcome_a, 0.5)
        score_b = outcome_scores.get(outcome_b, 0.5)

        # Need different outcomes to form a preference
        if score_a == score_b:
            return None

        # Get prompts
        payload_a = capsule_a.payload if isinstance(capsule_a.payload, dict) else json.loads(capsule_a.payload)
        payload_b = capsule_b.payload if isinstance(capsule_b.payload, dict) else json.loads(capsule_b.payload)

        # Extract assistant responses
        def get_assistant_response(payload):
            steps = payload.get("reasoning_steps", [])
            for step in steps:
                if isinstance(step, dict) and step.get("operation") not in ["request", "query"]:
                    return step.get("reasoning", "")
            return ""

        response_a = get_assistant_response(payload_a)
        response_b = get_assistant_response(payload_b)

        if not response_a or not response_b:
            return None

        # Determine preferred response
        if score_a > score_b:
            chosen = response_a
            rejected = response_b
        else:
            chosen = response_b
            rejected = response_a

        return {
            "prompt": payload_a.get("prompt", ""),
            "chosen": chosen,
            "rejected": rejected,
            "chosen_score": max(score_a, score_b),
            "rejected_score": min(score_a, score_b),
        }

    except Exception as e:
        logger.debug(f"Failed to create preference pair: {e}")
        return None


@router.get("/training")
async def export_training_data(
    format: str = Query("jsonl", description="Export format: jsonl, raw"),
    min_confidence: float = Query(0.5, description="Minimum confidence threshold"),
    min_steps: int = Query(2, description="Minimum reasoning steps"),
    limit: int = Query(1000, description="Maximum records to export"),
    with_outcomes_only: bool = Query(False, description="Only include capsules with outcomes"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Export capsules as training data for LLM fine-tuning.

    Returns JSONL format compatible with OpenAI fine-tuning API.
    """
    try:
        # Build query
        query = select(CapsuleModel).where(
            ~CapsuleModel.capsule_id.like("demo-%")
        )

        if with_outcomes_only:
            query = query.where(CapsuleModel.outcome_status.isnot(None))

        query = query.order_by(CapsuleModel.timestamp.desc()).limit(limit)

        result = await session.execute(query)
        capsules = result.scalars().all()

        # Convert to training format
        training_data = []
        skipped = 0

        for capsule in capsules:
            payload = capsule.payload
            if isinstance(payload, str):
                payload = json.loads(payload)

            # Check minimum steps
            steps = payload.get("reasoning_steps", [])
            if len(steps) < min_steps:
                skipped += 1
                continue

            # Check confidence
            confidence = payload.get("confidence", 0.5)
            if confidence < min_confidence:
                skipped += 1
                continue

            if format == "jsonl":
                converted = capsule_to_openai_format(capsule)
                if converted:
                    training_data.append(converted)
                else:
                    skipped += 1
            else:
                # Raw format
                training_data.append({
                    "capsule_id": capsule.capsule_id,
                    "timestamp": capsule.timestamp.isoformat() if capsule.timestamp else None,
                    "prompt": payload.get("prompt"),
                    "reasoning_steps": steps,
                    "confidence": confidence,
                    "outcome": capsule.outcome_status,
                })

        if format == "jsonl":
            # Return as downloadable JSONL file
            output = StringIO()
            for item in training_data:
                output.write(json.dumps(item) + "\n")
            output.seek(0)

            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="application/jsonl",
                headers={
                    "Content-Disposition": f"attachment; filename=training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
                }
            )

        return {
            "format": format,
            "total_exported": len(training_data),
            "skipped": skipped,
            "data": training_data,
        }

    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outcomes")
async def export_outcomes(
    limit: int = Query(500, description="Maximum records"),
    outcome_status: Optional[str] = Query(None, description="Filter by outcome: success, failure, partial"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Export capsules with outcomes for calibration analysis.

    Useful for:
    - Analyzing prediction accuracy
    - Building calibration datasets
    - Debugging outcome inference
    """
    try:
        query = select(CapsuleModel).where(
            and_(
                CapsuleModel.outcome_status.isnot(None),
                ~CapsuleModel.capsule_id.like("demo-%")
            )
        )

        if outcome_status:
            query = query.where(CapsuleModel.outcome_status == outcome_status)

        query = query.order_by(CapsuleModel.timestamp.desc()).limit(limit)

        result = await session.execute(query)
        capsules = result.scalars().all()

        outcomes = []
        for capsule in capsules:
            payload = capsule.payload
            if isinstance(payload, str):
                payload = json.loads(payload)

            outcomes.append({
                "capsule_id": capsule.capsule_id,
                "timestamp": capsule.timestamp.isoformat() if capsule.timestamp else None,
                "predicted_confidence": payload.get("confidence", 0.5),
                "outcome_status": capsule.outcome_status,
                "outcome_timestamp": capsule.outcome_timestamp.isoformat() if capsule.outcome_timestamp else None,
                "outcome_notes": capsule.outcome_notes,
                "outcome_metrics": capsule.outcome_metrics,
                "prompt": payload.get("prompt"),
            })

        # Calculate summary stats
        success_count = sum(1 for o in outcomes if o["outcome_status"] == "success")
        failure_count = sum(1 for o in outcomes if o["outcome_status"] == "failure")
        partial_count = sum(1 for o in outcomes if o["outcome_status"] == "partial")

        return {
            "total": len(outcomes),
            "summary": {
                "success": success_count,
                "failure": failure_count,
                "partial": partial_count,
            },
            "outcomes": outcomes,
        }

    except Exception as e:
        logger.error(f"Outcome export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def export_stats(
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get statistics about exportable training data.
    """
    try:
        # Total capsules
        total_query = select(func.count(CapsuleModel.id)).where(
            ~CapsuleModel.capsule_id.like("demo-%")
        )
        total_result = await session.execute(total_query)
        total = total_result.scalar()

        # With outcomes
        outcomes_query = select(func.count(CapsuleModel.id)).where(
            and_(
                CapsuleModel.outcome_status.isnot(None),
                ~CapsuleModel.capsule_id.like("demo-%")
            )
        )
        outcomes_result = await session.execute(outcomes_query)
        with_outcomes = outcomes_result.scalar()

        # With embeddings
        embeddings_query = select(func.count(CapsuleModel.id)).where(
            and_(
                CapsuleModel.embedding.isnot(None),
                ~CapsuleModel.capsule_id.like("demo-%")
            )
        )
        embeddings_result = await session.execute(embeddings_query)
        with_embeddings = embeddings_result.scalar()

        # Outcome breakdown
        outcome_breakdown = {}
        for status in ["success", "failure", "partial"]:
            status_query = select(func.count(CapsuleModel.id)).where(
                and_(
                    CapsuleModel.outcome_status == status,
                    ~CapsuleModel.capsule_id.like("demo-%")
                )
            )
            status_result = await session.execute(status_query)
            outcome_breakdown[status] = status_result.scalar()

        return {
            "total_capsules": total,
            "with_outcomes": with_outcomes,
            "with_embeddings": with_embeddings,
            "outcome_coverage": f"{(with_outcomes/total*100):.1f}%" if total > 0 else "0%",
            "embedding_coverage": f"{(with_embeddings/total*100):.1f}%" if total > 0 else "0%",
            "outcome_breakdown": outcome_breakdown,
            "exportable_for_training": with_outcomes,  # Capsules ready for supervised fine-tuning
        }

    except Exception as e:
        logger.error(f"Stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
