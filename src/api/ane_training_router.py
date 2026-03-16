"""
ANE Training Provenance API Router - UATP 7.3

Provides REST and WebSocket API endpoints for:
- Hardware profile registration and retrieval
- ANE training session management
- Per-kernel execution tracking
- MIL compile artifact management
- Real-time telemetry streaming
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
from ..services.ane_training_service import ane_training_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ane", tags=["ANE Training Provenance"])


# --- Request/Response Models ---


class HybridComputeAttributionInput(BaseModel):
    """Hybrid compute attribution input."""

    compute_unit: str = Field(description="Compute unit: ane, cpu, gpu, or hybrid")
    ane_percentage: float = Field(ge=0, le=100, description="Percentage on ANE")
    cpu_percentage: float = Field(ge=0, le=100, description="Percentage on CPU")
    gpu_percentage: float = Field(
        ge=0, le=100, default=0.0, description="Percentage on GPU"
    )
    dispatch_reason: Optional[str] = Field(None, description="Reason for selection")


class MILFusionOptimizationInput(BaseModel):
    """MIL fusion optimization input."""

    fusion_name: str = Field(description="Name of fusion optimization")
    source_ops: List[str] = Field(description="Original operations fused")
    target_op: str = Field(description="Resulting fused operation")
    speedup_factor: Optional[float] = Field(None, ge=1.0, description="Speedup factor")
    memory_reduction_bytes: Optional[int] = Field(
        None, ge=0, description="Memory savings"
    )


class HardwareProfileRequest(BaseModel):
    """Request body for hardware profile registration."""

    device_class: str = Field(description="Device class: mac, iphone, ipad")
    chip_identifier: str = Field(description="Chip: M1, M2, M3, M4, A17, etc.")
    chip_variant: Optional[str] = Field(None, description="Variant: Pro, Max, Ultra")
    ane_available: bool = Field(default=True, description="ANE availability")
    ane_version: Optional[str] = Field(None, description="ANE version")
    ane_tops: Optional[float] = Field(None, ge=0, description="ANE TOPS")
    ane_compile_limit: Optional[int] = Field(None, ge=0, description="Compile limit")
    memory_bandwidth_gbps: Optional[float] = Field(
        None, ge=0, description="Memory bandwidth"
    )
    unified_memory_gb: Optional[float] = Field(None, ge=0, description="Unified memory")
    private_apis_used: List[str] = Field(
        default_factory=list, description="Private APIs used"
    )
    device_id_hash: str = Field(description="SHA-256 hash of device ID")
    os_version: Optional[str] = Field(None, description="OS version")
    coreml_version: Optional[str] = Field(None, description="CoreML version")


class ANETrainingSessionRequest(BaseModel):
    """Request body for creating an ANE training session."""

    model_id: str = Field(description="Model being trained")
    model_name: Optional[str] = Field(None, description="Human-readable model name")
    hardware_profile_id: str = Field(description="Hardware profile ID")
    total_steps: Optional[int] = Field(None, ge=0, description="Total training steps")
    hyperparameters: Optional[Dict[str, Any]] = Field(
        None, description="Training hyperparameters"
    )
    dataset_refs: Optional[List[Dict[str, Any]]] = Field(
        None, description="Dataset references"
    )
    private_apis_used: List[str] = Field(
        default_factory=list, description="Private APIs used"
    )
    dmca_1201f_claim: bool = Field(
        default=False, description="DMCA 1201(f) interoperability claim"
    )
    research_purpose: Optional[str] = Field(
        None, description="Research purpose declaration"
    )


class ANESessionCompleteRequest(BaseModel):
    """Request body for completing an ANE training session."""

    status: str = Field(
        default="completed", description="Status: completed, failed, cancelled"
    )
    final_loss: Optional[float] = Field(None, description="Final training loss")
    avg_ms_per_step: Optional[float] = Field(None, ge=0, description="Avg ms per step")
    avg_ane_utilization: Optional[float] = Field(
        None, ge=0, le=100, description="Avg ANE utilization"
    )
    total_ane_time_seconds: Optional[float] = Field(
        None, ge=0, description="Total ANE time"
    )
    total_cpu_time_seconds: Optional[float] = Field(
        None, ge=0, description="Total CPU time"
    )
    session_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata"
    )


class KernelExecutionRequest(BaseModel):
    """Request body for kernel execution record."""

    session_id: str = Field(description="ANE training session ID")
    kernel_type: str = Field(
        description="Type: kFwdAttn, kFwdFFN, kFFNBwd, kSdpaBwd1, kSdpaBwd2, kQKVb"
    )
    step_index: int = Field(ge=0, description="Training step index")
    dispatch_index: int = Field(ge=0, description="Dispatch index within step")
    execution_time_us: int = Field(ge=0, description="Execution time in microseconds")
    iosurface_format: Optional[str] = Field(None, description="IOSurface format")
    input_shape: Optional[List[int]] = Field(None, description="Input tensor shape")
    output_shape: Optional[List[int]] = Field(None, description="Output tensor shape")
    compute_attribution: Optional[HybridComputeAttributionInput] = Field(
        None, description="Compute attribution"
    )
    ane_program_hash: Optional[str] = Field(None, description="ANE program hash")


class BatchKernelExecutionRequest(BaseModel):
    """Request body for batch kernel execution submission."""

    executions: List[KernelExecutionRequest] = Field(
        description="List of kernel executions (typically 6 per step)"
    )


class CompileArtifactRequest(BaseModel):
    """Request body for compile artifact upload."""

    session_id: str = Field(description="ANE training session ID")
    mil_program_hash: str = Field(description="SHA-256 hash of MIL program")
    weight_blob_hash: Optional[str] = Field(None, description="Weight blob hash")
    compiled_model_hash: Optional[str] = Field(None, description="Compiled model hash")
    fusion_optimizations: List[MILFusionOptimizationInput] = Field(
        default_factory=list, description="Fusion optimizations"
    )
    compile_time_ms: Optional[int] = Field(None, ge=0, description="Compile time")
    target_device: Optional[str] = Field(None, description="Target device")
    coreml_spec_version: Optional[int] = Field(None, description="CoreML spec version")
    mlmodel_size_bytes: Optional[int] = Field(None, ge=0, description="Model size")
    storage_uri: Optional[str] = Field(None, description="Storage URI")


class TelemetryBatchRequest(BaseModel):
    """Request body for telemetry batch submission."""

    session_id: str = Field(description="ANE training session ID")
    measurements: List[Dict[str, Any]] = Field(
        description="List of telemetry measurements"
    )


# --- Dependency ---


async def get_db_session():
    """Dependency to get database session."""
    async with db.get_session() as session:
        yield session


# --- Hardware Profile Endpoints ---


@router.get("/profiles/stats")
async def get_hardware_profile_stats(
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get aggregate statistics for hardware profiles.

    Returns counts by chip identifier and device class.
    """
    stats = await ane_training_service.get_profile_stats(session)
    return stats


@router.post("/profiles")
async def register_hardware_profile(
    request: HardwareProfileRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Register a hardware profile with ANE capabilities.

    Records device information including:
    - Chip identifier and variant
    - ANE availability and performance
    - Private API usage declarations
    """
    current_user.get("user_id")

    result = await ane_training_service.register_hardware_profile(
        device_class=request.device_class,
        chip_identifier=request.chip_identifier,
        device_id_hash=request.device_id_hash,
        session=session,
        chip_variant=request.chip_variant,
        ane_available=request.ane_available,
        ane_version=request.ane_version,
        ane_tops=request.ane_tops,
        ane_compile_limit=request.ane_compile_limit,
        memory_bandwidth_gbps=request.memory_bandwidth_gbps,
        unified_memory_gb=request.unified_memory_gb,
        private_apis_used=request.private_apis_used,
        os_version=request.os_version,
        coreml_version=request.coreml_version,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    logger.info(
        f"Hardware profile {result['profile_id']} registered "
        f"for chip {request.chip_identifier}"
    )
    return result


@router.get("/profiles/{profile_id}")
async def get_hardware_profile(
    profile_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get hardware profile by ID.

    Returns full profile including ANE capabilities.
    """
    profile = await ane_training_service.get_hardware_profile(profile_id, session)

    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

    return {"profile": profile}


# --- ANE Training Session Endpoints ---


@router.get("/sessions/stats")
async def get_session_stats(
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get aggregate statistics for ANE training sessions.

    Returns counts by status and performance metrics.
    """
    stats = await ane_training_service.get_session_stats(session)
    return stats


@router.post("/sessions")
async def create_ane_session(
    request: ANETrainingSessionRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new ANE training session.

    Records a training session with:
    - Model and hardware profile references
    - Private API usage declarations
    - DMCA 1201(f) interoperability claims
    """
    user_id = current_user.get("user_id")

    result = await ane_training_service.create_ane_session(
        model_id=request.model_id,
        hardware_profile_id=request.hardware_profile_id,
        session=session,
        model_name=request.model_name,
        total_steps=request.total_steps,
        hyperparameters=request.hyperparameters,
        dataset_refs=request.dataset_refs,
        private_apis_used=request.private_apis_used,
        dmca_1201f_claim=request.dmca_1201f_claim,
        research_purpose=request.research_purpose,
        owner_id=user_id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    logger.info(
        f"ANE session {result['session_id']} created for model {request.model_id}"
    )
    return result


@router.get("/sessions/{session_id}")
async def get_ane_session(
    session_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get ANE training session details.

    Returns full session metadata including performance metrics.
    """
    ane_session = await ane_training_service.get_ane_session(session_id, session)

    if not ane_session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return {"session": ane_session}


@router.post("/sessions/{session_id}/complete")
async def complete_ane_session(
    session_id: str,
    request: ANESessionCompleteRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Mark an ANE training session as complete.

    Updates the session with final metrics and status.
    """
    result = await ane_training_service.complete_ane_session(
        session_id=session_id,
        session=session,
        status=request.status,
        final_loss=request.final_loss,
        avg_ms_per_step=request.avg_ms_per_step,
        avg_ane_utilization=request.avg_ane_utilization,
        total_ane_time_seconds=request.total_ane_time_seconds,
        total_cpu_time_seconds=request.total_cpu_time_seconds,
        session_metadata=request.session_metadata,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    logger.info(f"ANE session {session_id} completed with status {request.status}")
    return result


@router.get("/sessions/{session_id}/statistics")
async def get_session_statistics(
    session_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get aggregate kernel statistics for a session.

    Returns metrics aggregated across all kernel executions:
    - Execution counts by kernel type
    - Average execution times
    - ANE vs CPU attribution breakdown
    """
    stats = await ane_training_service.get_session_statistics(session_id, session)

    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])

    return {"statistics": stats}


# --- Kernel Execution Endpoints ---


@router.post("/kernels")
async def submit_kernel_execution(
    request: KernelExecutionRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Submit a single kernel execution record.

    Records per-kernel dispatch with timing and attribution.
    """
    compute_attr = None
    if request.compute_attribution:
        compute_attr = request.compute_attribution.model_dump()

    result = await ane_training_service.record_kernel_execution(
        session_id=request.session_id,
        kernel_type=request.kernel_type,
        step_index=request.step_index,
        dispatch_index=request.dispatch_index,
        execution_time_us=request.execution_time_us,
        session=session,
        iosurface_format=request.iosurface_format,
        input_shape=request.input_shape,
        output_shape=request.output_shape,
        compute_attribution=compute_attr,
        ane_program_hash=request.ane_program_hash,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/kernels/batch")
async def submit_kernel_batch(
    request: BatchKernelExecutionRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Submit batch of kernel executions.

    Optimized for submitting all 6 kernels per training step.
    """
    executions = []
    for exec_req in request.executions:
        compute_attr = None
        if exec_req.compute_attribution:
            compute_attr = exec_req.compute_attribution.model_dump()
        executions.append(
            {
                "session_id": exec_req.session_id,
                "kernel_type": exec_req.kernel_type,
                "step_index": exec_req.step_index,
                "dispatch_index": exec_req.dispatch_index,
                "execution_time_us": exec_req.execution_time_us,
                "iosurface_format": exec_req.iosurface_format,
                "input_shape": exec_req.input_shape,
                "output_shape": exec_req.output_shape,
                "compute_attribution": compute_attr,
                "ane_program_hash": exec_req.ane_program_hash,
            }
        )

    result = await ane_training_service.batch_record_kernel_executions(
        executions=executions,
        session=session,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/sessions/{session_id}/kernels")
async def list_session_kernels(
    session_id: str,
    step_index: Optional[int] = Query(None, ge=0, description="Filter by step"),
    kernel_type: Optional[str] = Query(None, description="Filter by kernel type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List kernel executions for a session.

    Supports filtering by step index and kernel type.
    """
    kernels = await ane_training_service.list_kernel_executions(
        session_id=session_id,
        session=session,
        step_index=step_index,
        kernel_type=kernel_type,
        limit=limit,
        offset=offset,
    )

    return {
        "session_id": session_id,
        "kernels": kernels,
        "count": len(kernels),
        "limit": limit,
        "offset": offset,
    }


# --- Compile Artifact Endpoints ---


@router.post("/artifacts")
async def upload_compile_artifact(
    request: CompileArtifactRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Upload a MIL compile artifact.

    Records compiled ANE model with content hashes and fusion optimizations.
    """
    fusion_opts = [f.model_dump() for f in request.fusion_optimizations]

    result = await ane_training_service.record_compile_artifact(
        session_id=request.session_id,
        mil_program_hash=request.mil_program_hash,
        session=session,
        weight_blob_hash=request.weight_blob_hash,
        compiled_model_hash=request.compiled_model_hash,
        fusion_optimizations=fusion_opts,
        compile_time_ms=request.compile_time_ms,
        target_device=request.target_device,
        coreml_spec_version=request.coreml_spec_version,
        mlmodel_size_bytes=request.mlmodel_size_bytes,
        storage_uri=request.storage_uri,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    logger.info(f"Compile artifact {result['artifact_id']} uploaded")
    return result


@router.get("/sessions/{session_id}/artifacts")
async def list_session_artifacts(
    session_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    List compile artifacts for a session.
    """
    artifacts = await ane_training_service.list_compile_artifacts(
        session_id=session_id,
        session=session,
    )

    return {
        "session_id": session_id,
        "artifacts": artifacts,
        "count": len(artifacts),
    }


# --- Telemetry Endpoints ---


@router.post("/telemetry")
async def submit_telemetry_batch(
    request: TelemetryBatchRequest,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Submit a batch of telemetry measurements.

    Records real-time training metrics for dashboard monitoring.
    """
    result = await ane_training_service.record_telemetry_batch(
        session_id=request.session_id,
        measurements=request.measurements,
        session=session,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


# WebSocket connections for real-time telemetry
_telemetry_connections: Dict[str, List[WebSocket]] = {}


@router.websocket("/telemetry/stream/{session_id}")
async def telemetry_stream(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for real-time telemetry streaming.

    Clients connect to receive live training metrics for a session.
    """
    await websocket.accept()

    # Register connection
    if session_id not in _telemetry_connections:
        _telemetry_connections[session_id] = []
    _telemetry_connections[session_id].append(websocket)

    logger.info(f"Telemetry stream connected for session {session_id}")

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
        logger.info(f"Telemetry stream disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"Telemetry stream error: {e}")
    finally:
        # Unregister connection
        if session_id in _telemetry_connections:
            if websocket in _telemetry_connections[session_id]:
                _telemetry_connections[session_id].remove(websocket)
            if not _telemetry_connections[session_id]:
                del _telemetry_connections[session_id]


async def broadcast_telemetry(session_id: str, telemetry: Dict[str, Any]):
    """
    Broadcast telemetry to all connected WebSocket clients for a session.

    Called by the service layer when new telemetry is recorded.
    """
    if session_id not in _telemetry_connections:
        return

    dead_connections = []
    for websocket in _telemetry_connections[session_id]:
        try:
            await websocket.send_json(
                {
                    "type": "telemetry",
                    "session_id": session_id,
                    "data": telemetry,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception:
            dead_connections.append(websocket)

    # Clean up dead connections
    for websocket in dead_connections:
        _telemetry_connections[session_id].remove(websocket)
