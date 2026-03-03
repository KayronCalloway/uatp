"""
Model Registry API Router - UATP 7.2 Training Provenance

Provides REST API endpoints for:
- Model registration with provenance
- Model lineage queries
- Training session management
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth_middleware import get_current_user
from ..core.database import db
from ..services.model_registry_service import model_registry_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["Model Registry"])


# --- Request/Response Models ---


class DatasetRefInput(BaseModel):
    """Dataset reference input for model registration."""

    dataset_id: str = Field(description="Unique dataset identifier")
    dataset_name: str = Field(description="Human-readable dataset name")
    version: str = Field(description="Dataset version")
    source_url: Optional[str] = Field(None, description="Dataset source URL")
    license: Optional[str] = Field(None, description="Dataset license")
    content_hash: Optional[str] = Field(None, description="SHA-256 hash of dataset")
    record_count: Optional[int] = Field(None, ge=0, description="Number of records")
    attribution: Optional[Dict[str, Any]] = Field(
        None, description="Attribution metadata"
    )


class ModelRegistrationRequest(BaseModel):
    """Request body for model registration."""

    model_id: str = Field(description="Unique model identifier")
    model_hash: str = Field(description="SHA-256 hash of model weights")
    model_type: str = Field(description="Type: base, fine_tune, adapter, merged")
    version: str = Field(description="Model version string")
    name: Optional[str] = Field(None, description="Human-readable model name")
    description: Optional[str] = Field(None, description="Model description")
    base_model_id: Optional[str] = Field(
        None, description="Parent model ID for lineage"
    )
    training_config: Optional[Dict[str, Any]] = Field(
        None, description="Training configuration"
    )
    dataset_provenance: Optional[List[DatasetRefInput]] = Field(
        None, description="Datasets used in training"
    )
    license_info: Optional[Dict[str, Any]] = Field(
        None, description="License information"
    )
    capabilities: Optional[List[str]] = Field(
        None, description="Declared model capabilities"
    )
    safety_evaluations: Optional[Dict[str, Any]] = Field(
        None, description="Safety benchmark results"
    )


class TrainingSessionRequest(BaseModel):
    """Request body for creating a training session."""

    model_id: str = Field(description="Model being trained")
    session_type: str = Field(
        description="Type: pre_training, fine_tuning, rlhf, dpo, sft, adapter"
    )
    dataset_refs: List[DatasetRefInput] = Field(
        description="References to training datasets"
    )
    hyperparameters: Optional[Dict[str, Any]] = Field(
        None, description="Training hyperparameters"
    )
    compute_resources: Optional[Dict[str, Any]] = Field(
        None, description="GPU/TPU configuration"
    )


class TrainingSessionCompleteRequest(BaseModel):
    """Request body for completing a training session."""

    status: str = Field(
        default="completed",
        description="Final status: completed, failed, cancelled",
    )
    metrics: Optional[Dict[str, Any]] = Field(
        None, description="Training metrics and evaluation results"
    )
    checkpoints: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of checkpoint references"
    )


# --- Dependency ---


async def get_db_session():
    """Dependency to get database session."""
    async with db.get_session() as session:
        yield session


# --- Endpoints ---
# IMPORTANT: Static routes (/stats, /register) MUST come before parameterized routes (/{id})
# to prevent FastAPI from capturing "stats" as a model_id parameter


@router.get("/stats")
async def get_model_registry_stats(
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get aggregate statistics for the model registry.

    Returns counts by model type and training status.
    """
    from sqlalchemy import func, select

    from ..models.model_registry import ModelRegistryModel
    from ..models.training_session import TrainingSessionModel

    # Count models by type
    type_query = select(
        ModelRegistryModel.model_type, func.count(ModelRegistryModel.id)
    ).group_by(ModelRegistryModel.model_type)
    type_result = await session.execute(type_query)
    by_type = {row[0]: row[1] for row in type_result.fetchall()}

    # Total models
    total_models = await session.execute(select(func.count(ModelRegistryModel.id)))
    total_model_count = total_models.scalar() or 0

    # Count training sessions by status
    session_query = select(
        TrainingSessionModel.status, func.count(TrainingSessionModel.id)
    ).group_by(TrainingSessionModel.status)
    session_result = await session.execute(session_query)
    by_status = {row[0]: row[1] for row in session_result.fetchall()}

    # Total sessions
    total_sessions = await session.execute(select(func.count(TrainingSessionModel.id)))
    total_session_count = total_sessions.scalar() or 0

    return {
        "models": {
            "total": total_model_count,
            "by_type": by_type,
        },
        "training_sessions": {
            "total": total_session_count,
            "by_status": by_status,
        },
    }


@router.post("/register")
async def register_model(
    request: ModelRegistrationRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Register a new model with provenance metadata.

    Creates a model registry entry tracking:
    - Model hash and version
    - Base model lineage
    - Training configuration
    - Dataset provenance
    - License information
    """
    user_id = current_user.get("user_id")

    # Convert dataset_provenance to dicts
    dataset_prov = None
    if request.dataset_provenance:
        dataset_prov = [ds.model_dump() for ds in request.dataset_provenance]

    result = await model_registry_service.register_model(
        model_id=request.model_id,
        model_hash=request.model_hash,
        model_type=request.model_type,
        version=request.version,
        session=session,
        name=request.name,
        description=request.description,
        base_model_id=request.base_model_id,
        training_config=request.training_config,
        dataset_provenance=dataset_prov,
        license_info=request.license_info,
        capabilities=request.capabilities,
        safety_evaluations=request.safety_evaluations,
        owner_id=user_id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    logger.info(f"Model {request.model_id} registered by user {user_id}")
    return result


@router.get("/{model_id}")
async def get_model(
    model_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get model details by ID.

    Returns full model metadata including provenance information.

    SECURITY NOTE: This endpoint is intentionally public (no authentication required).
    Model metadata including provenance information is designed to be publicly
    accessible for transparency and reproducibility. This is consistent with
    UATP 7.2 design principles where model identity and lineage are public,
    while access to model weights/artifacts may be restricted separately.
    """
    model = await model_registry_service.get_model(model_id, session)

    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    return {"model": model}


@router.get("/{model_id}/lineage")
async def get_model_lineage(
    model_id: str,
    max_depth: int = Query(10, ge=1, le=100, description="Maximum lineage depth"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get the lineage tree for a model.

    Returns:
    - Ancestors: Chain of base models back to root
    - Descendants: Models derived from this model
    - Lineage depth: Number of generations from root
    """
    lineage = await model_registry_service.get_model_lineage(
        model_id, session, max_depth=max_depth
    )

    if "error" in lineage:
        raise HTTPException(status_code=404, detail=lineage["error"])

    return {"lineage": lineage}


@router.get("")
async def list_models(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    base_model_id: Optional[str] = Query(None, description="Filter by base model"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List registered models with pagination.

    Optional filters:
    - model_type: base, fine_tune, adapter, merged
    - base_model_id: Filter descendants of a specific model
    """
    from sqlalchemy import func, select

    from ..models.model_registry import ModelRegistryModel

    # Build query
    query = select(ModelRegistryModel)

    if model_type:
        query = query.where(ModelRegistryModel.model_type == model_type)
    if base_model_id:
        query = query.where(ModelRegistryModel.base_model_id == base_model_id)

    # Get total count
    count_query = select(func.count(ModelRegistryModel.id))
    if model_type:
        count_query = count_query.where(ModelRegistryModel.model_type == model_type)
    if base_model_id:
        count_query = count_query.where(
            ModelRegistryModel.base_model_id == base_model_id
        )

    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(ModelRegistryModel.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await session.execute(query)
    models = [m.to_dict() for m in result.scalars().all()]

    return {
        "models": models,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


# --- Training Session Endpoints ---


@router.post("/training-sessions")
async def create_training_session(
    request: TrainingSessionRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new training session.

    Records a training run with:
    - Dataset references and provenance
    - Hyperparameters
    - Compute resource configuration
    """
    user_id = current_user.get("user_id")

    # Convert dataset_refs to dicts
    dataset_refs = [ds.model_dump() for ds in request.dataset_refs]

    result = await model_registry_service.create_training_session(
        model_id=request.model_id,
        session_type=request.session_type,
        dataset_refs=dataset_refs,
        session=session,
        hyperparameters=request.hyperparameters,
        compute_resources=request.compute_resources,
        owner_id=user_id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    logger.info(
        f"Training session {result['session_id']} created for model {request.model_id}"
    )
    return result


@router.get("/training-sessions/{session_id}")
async def get_training_session(
    session_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get training session details.

    Returns full session metadata including metrics if completed.
    """
    training_session = await model_registry_service.get_training_session(
        session_id, session
    )

    if not training_session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return {"session": training_session}


@router.post("/training-sessions/{session_id}/complete")
async def complete_training_session(
    session_id: str,
    request: TrainingSessionCompleteRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Mark a training session as complete.

    Updates the session with:
    - Final status (completed, failed, cancelled)
    - Training metrics
    - Checkpoint references
    """
    result = await model_registry_service.complete_training_session(
        session_id=session_id,
        session=session,
        status=request.status,
        metrics=request.metrics,
        checkpoints=request.checkpoints,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    logger.info(f"Training session {session_id} completed with status {request.status}")
    return result


@router.get("/{model_id}/training-sessions")
async def list_model_training_sessions(
    model_id: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum sessions to return"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List training sessions for a specific model.

    Returns sessions ordered by start time (most recent first).
    """
    # First verify model exists
    model = await model_registry_service.get_model(model_id, session)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    sessions = await model_registry_service.list_model_sessions(
        model_id, session, limit=limit
    )

    return {
        "model_id": model_id,
        "sessions": sessions,
        "total": len(sessions),
    }
