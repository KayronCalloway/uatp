"""
Agent Execution Traces API Router - UATP 7.4

Provides REST and WebSocket API endpoints for:
- Agent session management
- Tool call tracking
- Action trace recording
- Decision point capture
- Environment snapshot management
- Real-time trace streaming
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth_middleware import get_current_user
from ..core.database import db
from ..services.agent_execution_service import agent_execution_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agent Execution Traces"])


# --- Request/Response Models ---


class AgentSessionRequest(BaseModel):
    """Request body for creating an agent session."""

    agent_type: str = Field(description="Agent type: openclaw, claude_code, custom")
    agent_version: Optional[str] = Field(None, description="Agent version")
    scheduler_type: Optional[str] = Field(
        None, description="Scheduler: heartbeat, on_demand, scheduled"
    )
    trigger_message: Optional[str] = Field(
        None, description="Message that initiated the session"
    )
    trigger_source: Optional[str] = Field(
        None, description="Source: whatsapp, telegram, cli, api, web"
    )
    user_id_hash: Optional[str] = Field(
        None, description="Privacy-preserving user ID hash"
    )
    goals: List[str] = Field(
        default_factory=list, description="Goals the agent is trying to achieve"
    )


class AgentSessionCompleteRequest(BaseModel):
    """Request body for completing an agent session."""

    status: str = Field(
        default="completed", description="Status: completed, failed, cancelled"
    )
    outcome_summary: Optional[str] = Field(None, description="Summary of outcomes")
    error_message: Optional[str] = Field(None, description="Error if failed")


class ToolCallRequest(BaseModel):
    """Request body for recording a tool call."""

    session_id: str = Field(description="Agent session ID")
    tool_name: str = Field(description="Tool name: Bash, Read, Edit, WebFetch, etc.")
    tool_category: str = Field(
        description="Category: terminal, file, browser, api, mcp, custom"
    )
    step_index: int = Field(ge=0, description="Order within session")
    tool_inputs: Optional[Dict[str, Any]] = Field(None, description="Input parameters")
    tool_outputs: Optional[Dict[str, Any]] = Field(None, description="Output/result")
    started_at: Optional[datetime] = Field(None, description="When tool call started")
    completed_at: Optional[datetime] = Field(
        None, description="When tool call completed"
    )
    duration_ms: Optional[int] = Field(
        None, ge=0, description="Duration in milliseconds"
    )
    status: str = Field(
        default="success", description="Status: pending, success, error, timeout"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")
    parent_call_id: Optional[str] = Field(None, description="For nested tool calls")


class BatchToolCallRequest(BaseModel):
    """Request body for batch tool call submission."""

    tool_calls: List[ToolCallRequest] = Field(
        description="List of tool calls to record"
    )


class ActionTraceRequest(BaseModel):
    """Request body for recording an action trace."""

    session_id: str = Field(description="Agent session ID")
    action_type: str = Field(description="Type: terminal, browser, file, api")
    executed_at: datetime = Field(description="When action was executed")
    duration_ms: int = Field(ge=0, description="Duration in milliseconds")
    tool_call_id: Optional[str] = Field(None, description="Link to parent tool call")
    # Terminal actions
    command: Optional[str] = Field(None, description="Terminal command executed")
    exit_code: Optional[int] = Field(None, description="Command exit code")
    stdout_hash: Optional[str] = Field(None, description="SHA-256 hash of stdout")
    stderr_hash: Optional[str] = Field(None, description="SHA-256 hash of stderr")
    # Browser actions
    url: Optional[str] = Field(None, description="URL for browser actions")
    selector: Optional[str] = Field(None, description="CSS selector")
    browser_action: Optional[str] = Field(
        None, description="Action: navigate, click, type, screenshot"
    )
    # File actions
    file_path: Optional[str] = Field(None, description="File path")
    file_operation: Optional[str] = Field(
        None, description="Operation: read, write, edit, delete, glob, grep"
    )
    bytes_affected: Optional[int] = Field(None, ge=0, description="Bytes affected")


class DecisionPointRequest(BaseModel):
    """Request body for recording a decision point."""

    session_id: str = Field(description="Agent session ID")
    step_index: int = Field(ge=0, description="Step index within session")
    reasoning: str = Field(description="Why this action was chosen")
    selected_action: str = Field(description="What was chosen")
    alternatives_considered: List[str] = Field(
        default_factory=list, description="Other options evaluated"
    )
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence score 0.0-1.0"
    )
    context_summary: Optional[str] = Field(
        None, description="Relevant context for decision"
    )
    constraints_applied: List[str] = Field(
        default_factory=list, description="Safety, permissions, etc."
    )
    timestamp: Optional[datetime] = Field(None, description="When decision was made")


class EnvironmentSnapshotRequest(BaseModel):
    """Request body for recording an environment snapshot."""

    session_id: str = Field(description="Agent session ID")
    working_directory: str = Field(description="Current working directory")
    env_vars_hash: str = Field(description="Hash of environment variables")
    git_branch: Optional[str] = Field(None, description="Current git branch")
    git_commit_hash: Optional[str] = Field(None, description="Current commit hash")
    git_dirty: Optional[bool] = Field(None, description="Whether working tree is dirty")
    open_files: List[str] = Field(
        default_factory=list, description="Files being tracked"
    )
    system_load: Optional[float] = Field(None, ge=0, description="System load average")
    memory_available_gb: Optional[float] = Field(
        None, ge=0, description="Available memory in GB"
    )
    timestamp: Optional[datetime] = Field(None, description="Snapshot timestamp")


# --- Dependency ---


async def get_db_session():
    """Dependency to get database session."""
    async with db.get_session() as session:
        yield session


# --- Agent Session Endpoints ---


@router.get("/stats")
async def get_agent_stats(
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get aggregate statistics for agent sessions.

    Returns counts by status and agent type, plus average duration.
    """
    stats = await agent_execution_service.get_session_stats(session)
    return stats


@router.post("/sessions")
async def create_agent_session(
    request: AgentSessionRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new agent session.

    Records a session with:
    - Agent type and version
    - Trigger context (message, source)
    - Goals to achieve
    """
    user_id = current_user.get("user_id")

    result = await agent_execution_service.create_agent_session(
        agent_type=request.agent_type,
        session=session,
        agent_version=request.agent_version,
        scheduler_type=request.scheduler_type,
        trigger_message=request.trigger_message,
        trigger_source=request.trigger_source,
        user_id_hash=request.user_id_hash,
        goals=request.goals,
        owner_id=user_id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    logger.info(
        f"Agent session {result['session_id']} created for {request.agent_type}"
    )
    return result


@router.get("/sessions/{session_id}")
async def get_agent_session(
    session_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get agent session details.

    Returns full session metadata including execution counts.
    """
    agent_session = await agent_execution_service.get_agent_session(session_id, session)

    if not agent_session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return {"session": agent_session}


@router.post("/sessions/{session_id}/complete")
async def complete_agent_session(
    session_id: str,
    request: AgentSessionCompleteRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Mark an agent session as complete.

    Updates the session with final status and outcome.
    """
    result = await agent_execution_service.complete_agent_session(
        session_id=session_id,
        session=session,
        status=request.status,
        outcome_summary=request.outcome_summary,
        error_message=request.error_message,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    logger.info(f"Agent session {session_id} completed with status {request.status}")
    return result


@router.get("/sessions/{session_id}/statistics")
async def get_session_statistics(
    session_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get aggregate statistics for a session.

    Returns metrics by tool category, action type, and decision confidence.
    """
    stats = await agent_execution_service.get_session_statistics(session_id, session)

    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])

    return {"statistics": stats}


# --- Tool Call Endpoints ---


@router.post("/tools")
async def submit_tool_call(
    request: ToolCallRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Record a single tool call.

    Records tool invocation with inputs, outputs, and timing.
    """
    result = await agent_execution_service.record_tool_call(
        session_id=request.session_id,
        tool_name=request.tool_name,
        tool_category=request.tool_category,
        step_index=request.step_index,
        session=session,
        tool_inputs=request.tool_inputs,
        tool_outputs=request.tool_outputs,
        started_at=request.started_at,
        completed_at=request.completed_at,
        duration_ms=request.duration_ms,
        status=request.status,
        error_message=request.error_message,
        parent_call_id=request.parent_call_id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/tools/batch")
async def submit_tool_batch(
    request: BatchToolCallRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Submit batch of tool calls.

    Optimized for recording multiple tool calls at once.
    """
    tool_calls = []
    for call_req in request.tool_calls:
        tool_calls.append(
            {
                "session_id": call_req.session_id,
                "tool_name": call_req.tool_name,
                "tool_category": call_req.tool_category,
                "step_index": call_req.step_index,
                "tool_inputs": call_req.tool_inputs,
                "tool_outputs": call_req.tool_outputs,
                "started_at": call_req.started_at,
                "completed_at": call_req.completed_at,
                "duration_ms": call_req.duration_ms,
                "status": call_req.status,
                "error_message": call_req.error_message,
                "parent_call_id": call_req.parent_call_id,
            }
        )

    result = await agent_execution_service.batch_record_tool_calls(
        tool_calls=tool_calls,
        session=session,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/sessions/{session_id}/tools")
async def list_session_tools(
    session_id: str,
    tool_name: Optional[str] = Query(None, description="Filter by tool name"),
    tool_category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List tool calls for a session.

    Supports filtering by tool name and category.
    """
    tools = await agent_execution_service.list_tool_calls(
        session_id=session_id,
        session=session,
        tool_name=tool_name,
        tool_category=tool_category,
        limit=limit,
        offset=offset,
    )

    return {
        "session_id": session_id,
        "tool_calls": tools,
        "count": len(tools),
        "limit": limit,
        "offset": offset,
    }


# --- Action Trace Endpoints ---


@router.post("/actions")
async def submit_action_trace(
    request: ActionTraceRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Record an action trace.

    Records terminal, browser, or file action with type-specific details.
    """
    result = await agent_execution_service.record_action_trace(
        session_id=request.session_id,
        action_type=request.action_type,
        executed_at=request.executed_at,
        duration_ms=request.duration_ms,
        session=session,
        tool_call_id=request.tool_call_id,
        command=request.command,
        exit_code=request.exit_code,
        stdout_hash=request.stdout_hash,
        stderr_hash=request.stderr_hash,
        url=request.url,
        selector=request.selector,
        browser_action=request.browser_action,
        file_path=request.file_path,
        file_operation=request.file_operation,
        bytes_affected=request.bytes_affected,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/sessions/{session_id}/actions")
async def list_session_actions(
    session_id: str,
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List action traces for a session.

    Supports filtering by action type.
    """
    actions = await agent_execution_service.list_action_traces(
        session_id=session_id,
        session=session,
        action_type=action_type,
        limit=limit,
        offset=offset,
    )

    return {
        "session_id": session_id,
        "actions": actions,
        "count": len(actions),
        "limit": limit,
        "offset": offset,
    }


# --- Decision Point Endpoints ---


@router.post("/decisions")
async def submit_decision_point(
    request: DecisionPointRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Record a decision point.

    Records agent reasoning, alternatives considered, and confidence.
    """
    result = await agent_execution_service.record_decision_point(
        session_id=request.session_id,
        step_index=request.step_index,
        reasoning=request.reasoning,
        selected_action=request.selected_action,
        session=session,
        alternatives_considered=request.alternatives_considered,
        confidence=request.confidence,
        context_summary=request.context_summary,
        constraints_applied=request.constraints_applied,
        timestamp=request.timestamp,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/sessions/{session_id}/decisions")
async def list_session_decisions(
    session_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List decision points for a session.
    """
    decisions = await agent_execution_service.list_decision_points(
        session_id=session_id,
        session=session,
        limit=limit,
        offset=offset,
    )

    return {
        "session_id": session_id,
        "decisions": decisions,
        "count": len(decisions),
        "limit": limit,
        "offset": offset,
    }


# --- Environment Snapshot Endpoints ---


@router.post("/snapshots")
async def submit_environment_snapshot(
    request: EnvironmentSnapshotRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Record an environment snapshot.

    Records system state including working directory, git state, and resources.
    """
    result = await agent_execution_service.record_environment_snapshot(
        session_id=request.session_id,
        working_directory=request.working_directory,
        env_vars_hash=request.env_vars_hash,
        session=session,
        git_branch=request.git_branch,
        git_commit_hash=request.git_commit_hash,
        git_dirty=request.git_dirty,
        open_files=request.open_files,
        system_load=request.system_load,
        memory_available_gb=request.memory_available_gb,
        timestamp=request.timestamp,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/sessions/{session_id}/snapshots")
async def list_session_snapshots(
    session_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List environment snapshots for a session.
    """
    snapshots = await agent_execution_service.list_environment_snapshots(
        session_id=session_id,
        session=session,
        limit=limit,
        offset=offset,
    )

    return {
        "session_id": session_id,
        "snapshots": snapshots,
        "count": len(snapshots),
        "limit": limit,
        "offset": offset,
    }


# --- WebSocket for Real-time Streaming ---

_trace_connections: Dict[str, List[WebSocket]] = {}


@router.websocket("/stream/{session_id}")
async def trace_stream(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for real-time trace streaming.

    Clients connect to receive live tool calls, actions, and decisions for a session.
    """
    await websocket.accept()

    # Register connection
    if session_id not in _trace_connections:
        _trace_connections[session_id] = []
    _trace_connections[session_id].append(websocket)

    logger.info(f"Trace stream connected for session {session_id}")

    try:
        while True:
            # Wait for incoming messages (heartbeat or subscription updates)
            data = await websocket.receive_json()

            # Handle ping/pong for connection keepalive
            if data.get("type") == "ping":
                await websocket.send_json(
                    {
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"Trace stream disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"Trace stream error: {e}")
    finally:
        # Unregister connection
        if session_id in _trace_connections:
            if websocket in _trace_connections[session_id]:
                _trace_connections[session_id].remove(websocket)
            if not _trace_connections[session_id]:
                del _trace_connections[session_id]


async def broadcast_trace(session_id: str, trace_type: str, trace_data: Dict[str, Any]):
    """
    Broadcast trace event to all connected WebSocket clients for a session.

    Args:
        session_id: Agent session ID
        trace_type: Type of trace (tool_call, action, decision, snapshot)
        trace_data: Trace data to broadcast
    """
    if session_id not in _trace_connections:
        return

    dead_connections = []
    for websocket in _trace_connections[session_id]:
        try:
            await websocket.send_json(
                {
                    "type": trace_type,
                    "session_id": session_id,
                    "data": trace_data,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception:
            dead_connections.append(websocket)

    # Clean up dead connections
    for websocket in dead_connections:
        _trace_connections[session_id].remove(websocket)
