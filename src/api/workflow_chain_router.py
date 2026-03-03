"""
Workflow Chain API Router - UATP 7.2 Agentic Workflow Chains

Provides REST API endpoints for:
- Creating workflow containers
- Adding steps to workflows
- Querying workflow state and steps
- Aggregating attribution
- Completing workflows
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth_middleware import get_current_user
from ..core.database import db
from ..services.workflow_chain_service import workflow_chain_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["Workflow Chains"])


# --- Request/Response Models ---


class WorkflowCreateRequest(BaseModel):
    """Request body for workflow creation."""

    workflow_name: str = Field(description="Human-readable workflow name")
    workflow_type: str = Field(
        default="linear",
        description="Type: linear, branching, iterative, parallel",
    )
    dag_definition: Optional[Dict[str, Any]] = Field(
        None, description="Initial DAG structure"
    )


class WorkflowStepRequest(BaseModel):
    """Request body for adding a workflow step."""

    step_type: str = Field(
        description="Type: plan, tool_call, inference, output, human_input, verification"
    )
    step_name: Optional[str] = Field(None, description="Human-readable step name")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Step input")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Step output")
    depends_on_steps: Optional[List[int]] = Field(
        None, description="Indices of dependency steps"
    )
    tool_name: Optional[str] = Field(None, description="Tool used (for tool_call)")
    model_id: Optional[str] = Field(None, description="Model used (for inference)")
    execution_time_ms: Optional[int] = Field(
        None, ge=0, description="Step execution time"
    )
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Step confidence")


class WorkflowCompleteRequest(BaseModel):
    """Request body for completing a workflow."""

    final_output: Optional[Dict[str, Any]] = Field(
        None, description="Final workflow output"
    )
    status: str = Field(
        default="completed",
        description="Final status: completed, failed, cancelled",
    )


# --- Dependency ---


async def get_db_session():
    """Dependency to get database session."""
    async with db.get_session() as session:
        yield session


# --- Endpoints ---
# IMPORTANT: Static routes (/stats, /types) MUST come before parameterized routes (/{id})
# to prevent FastAPI from capturing "stats" as a workflow_id parameter


@router.get("/stats")
async def get_workflow_stats(
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get aggregate statistics for workflows.

    Returns counts by status and workflow type.
    """
    from sqlalchemy import func, select

    from ..models.workflow_capsule import WorkflowCapsuleModel

    # Count by status
    status_query = select(
        WorkflowCapsuleModel.status, func.count(WorkflowCapsuleModel.id)
    ).group_by(WorkflowCapsuleModel.status)
    status_result = await session.execute(status_query)
    by_status = {row[0]: row[1] for row in status_result.fetchall()}

    # Count by type
    type_query = select(
        WorkflowCapsuleModel.workflow_type, func.count(WorkflowCapsuleModel.id)
    ).group_by(WorkflowCapsuleModel.workflow_type)
    type_result = await session.execute(type_query)
    by_type = {row[0]: row[1] for row in type_result.fetchall()}

    # Total
    total_result = await session.execute(select(func.count(WorkflowCapsuleModel.id)))
    total = total_result.scalar() or 0

    # Average steps per workflow
    avg_steps_query = select(func.avg(WorkflowCapsuleModel.step_count))
    avg_result = await session.execute(avg_steps_query)
    avg_steps = avg_result.scalar() or 0

    return {
        "total_workflows": total,
        "by_status": by_status,
        "by_type": by_type,
        "average_steps": round(float(avg_steps), 1),
    }


@router.post("")
async def create_workflow(
    request: WorkflowCreateRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new workflow container.

    A workflow groups multiple step capsules together with DAG-based
    dependency tracking and aggregated attribution.
    """
    user_id = current_user.get("user_id")

    result = await workflow_chain_service.create_workflow(
        workflow_name=request.workflow_name,
        workflow_type=request.workflow_type,
        session=session,
        owner_id=user_id,
        dag_definition=request.dag_definition,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    logger.info(f"Workflow {result['workflow_capsule_id']} created by user {user_id}")
    return result


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get workflow details with all steps.

    Returns the workflow metadata, DAG structure, and all step capsules.
    """
    workflow = await workflow_chain_service.get_workflow(workflow_id, session)

    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    return {"workflow": workflow}


@router.get("/{workflow_id}/steps")
async def get_workflow_steps(
    workflow_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get all steps for a workflow in order.

    Returns steps sorted by step_index with their dependency information.
    """
    steps = await workflow_chain_service.get_workflow_steps(workflow_id, session)

    return {
        "workflow_capsule_id": workflow_id,
        "steps": steps,
        "total_steps": len(steps),
    }


@router.post("/{workflow_id}/steps")
async def add_workflow_step(
    workflow_id: str,
    request: WorkflowStepRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Add a step to an existing workflow.

    Creates a new step capsule linked to the workflow.
    Steps are automatically assigned the next step_index.
    """
    user_id = current_user.get("user_id")

    result = await workflow_chain_service.add_step(
        workflow_capsule_id=workflow_id,
        step_type=request.step_type,
        session=session,
        step_name=request.step_name,
        input_data=request.input_data,
        output_data=request.output_data,
        depends_on_steps=request.depends_on_steps,
        tool_name=request.tool_name,
        model_id=request.model_id,
        execution_time_ms=request.execution_time_ms,
        confidence=request.confidence,
        owner_id=user_id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    logger.info(
        f"Step {result['step_index']} added to workflow {workflow_id} by user {user_id}"
    )
    return result


@router.get("/{workflow_id}/attribution")
async def get_workflow_attribution(
    workflow_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get aggregated attribution for a workflow.

    Combines attribution from all steps using weighted aggregation.
    """
    attribution = await workflow_chain_service.get_aggregated_attribution(
        workflow_id, session
    )

    if "error" in attribution:
        raise HTTPException(status_code=404, detail=attribution["error"])

    return {"attribution": attribution}


@router.post("/{workflow_id}/complete")
async def complete_workflow(
    workflow_id: str,
    request: WorkflowCompleteRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Mark a workflow as complete and seal it.

    Finalizes the workflow with:
    - Final output data
    - Computed DAG structure
    - Aggregated attribution
    - Completion timestamp
    """
    user_id = current_user.get("user_id")

    result = await workflow_chain_service.complete_workflow(
        workflow_capsule_id=workflow_id,
        session=session,
        final_output=request.final_output,
        status=request.status,
        owner_id=user_id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    logger.info(f"Workflow {workflow_id} completed with status {request.status}")
    return result


@router.get("")
async def list_workflows(
    status: Optional[str] = Query(None, description="Filter by status"),
    workflow_type: Optional[str] = Query(None, description="Filter by workflow type"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List workflows with pagination.

    Non-admin users see only their own workflows.
    """
    from sqlalchemy import func, select

    from ..auth.auth_middleware import is_admin_user
    from ..models.workflow_capsule import WorkflowCapsuleModel

    user_id = current_user.get("user_id")
    user_is_admin = is_admin_user(current_user)

    # Build query
    query = select(WorkflowCapsuleModel)

    # Non-admin users only see their own workflows
    if not user_is_admin:
        query = query.where(WorkflowCapsuleModel.owner_id == user_id)

    if status:
        query = query.where(WorkflowCapsuleModel.status == status)
    if workflow_type:
        query = query.where(WorkflowCapsuleModel.workflow_type == workflow_type)

    # Get total count
    count_query = select(func.count(WorkflowCapsuleModel.id))
    if not user_is_admin:
        count_query = count_query.where(WorkflowCapsuleModel.owner_id == user_id)
    if status:
        count_query = count_query.where(WorkflowCapsuleModel.status == status)
    if workflow_type:
        count_query = count_query.where(
            WorkflowCapsuleModel.workflow_type == workflow_type
        )

    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(WorkflowCapsuleModel.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await session.execute(query)
    workflows = [w.to_dict() for w in result.scalars().all()]

    return {
        "workflows": workflows,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }
