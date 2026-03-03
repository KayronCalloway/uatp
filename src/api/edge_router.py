"""
Edge Sync API Router - UATP 7.2 Edge-Native Capsules

Provides REST API endpoints for:
- Syncing edge capsules to cloud
- Managing offline signatures
- Device registration
- Batch sync operations
"""

import base64
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth_middleware import get_current_user, get_current_user_optional
from ..core.database import db
from ..edge import (
    CompactCapsuleDecoder,
    CompactCapsuleEncoder,
    SyncDirection,
    SyncStatus,
    edge_sync_service,
    offline_signer_registry,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/edge", tags=["Edge Sync"])


# --- Request/Response Models ---


class CompactCapsuleSubmitRequest(BaseModel):
    """Request to submit a compact capsule."""

    capsule_data: str = Field(description="Base64-encoded compact capsule")
    device_id: str = Field(description="Device identifier")
    device_secret: str = Field(description="Device authentication secret")


class CompactCapsuleResponse(BaseModel):
    """Response for compact capsule submission."""

    accepted: bool
    capsule_id: str
    queued: bool
    message: str


class SyncRequest(BaseModel):
    """Request to sync edge capsules."""

    device_id: str = Field(description="Device identifier")
    direction: str = Field(
        default="edge_to_cloud",
        description="Sync direction: edge_to_cloud, cloud_to_edge, bidirectional",
    )
    max_capsules: Optional[int] = Field(
        None, description="Maximum capsules to sync in this request"
    )


class SyncResponse(BaseModel):
    """Response from sync operation."""

    batch_id: str
    status: str
    synced_count: int
    failed_count: int
    conflict_count: int
    checkpoint_id: Optional[str]
    errors: List[str]


class BatchSyncRequest(BaseModel):
    """Request for batch sync with multiple capsules."""

    device_id: str = Field(description="Device identifier")
    capsules: List[str] = Field(description="List of base64-encoded compact capsules")


class BatchSyncResponse(BaseModel):
    """Response from batch sync."""

    batch_id: str
    status: str
    total_submitted: int
    synced_count: int
    failed_count: int
    errors: List[str]


class DeviceRegistrationRequest(BaseModel):
    """Request to register an edge device."""

    device_id: str = Field(description="Unique device identifier")
    public_key: str = Field(description="Hex-encoded Ed25519 public key")
    device_type: Optional[str] = Field(None, description="Device type/model")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DeviceRegistrationResponse(BaseModel):
    """Response from device registration."""

    registered: bool
    device_id: str
    message: str


class PendingCapsuleResponse(BaseModel):
    """Response listing pending capsules."""

    device_id: str
    pending_count: int
    capsule_ids: List[str]


# --- Dependency ---


async def get_db_session():
    """Dependency to get database session."""
    async with db.get_session() as session:
        yield session


# --- Endpoints ---


@router.post("/capsule")
async def submit_compact_capsule(
    request: CompactCapsuleSubmitRequest,
    current_user: Dict = Depends(get_current_user_optional),
) -> CompactCapsuleResponse:
    """
    Submit a compact binary capsule from an edge device.

    The capsule is queued for sync if offline, or processed
    immediately if connected.

    SECURITY: Requires device authentication via device_secret.
    """
    # SECURITY: Authenticate device before accepting capsule
    device = edge_sync_service.authenticate_device(
        request.device_id, request.device_secret
    )
    if not device:
        logger.warning(f"Device authentication failed for {request.device_id[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Device authentication failed",
        )

    # SECURITY: Check base64 size before decoding (max 10MB encoded = ~7.5MB decoded)
    MAX_CAPSULE_BASE64_SIZE = 10 * 1024 * 1024
    if len(request.capsule_data) > MAX_CAPSULE_BASE64_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Capsule data too large (max {MAX_CAPSULE_BASE64_SIZE // (1024*1024)}MB)",
        )

    try:
        # Decode base64 capsule data
        capsule_data = base64.b64decode(request.capsule_data)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid base64 capsule_data: {e}",
        )

    try:
        # Validate capsule format
        decoder = CompactCapsuleDecoder()
        capsule = decoder.decode(capsule_data)
        capsule_id = capsule.capsule_id_hex
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid compact capsule format: {e}",
        )

    # Queue for sync (device already authenticated)
    queued = edge_sync_service.queue_capsule(request.device_id, capsule_data)

    logger.info(
        f"Received compact capsule {capsule_id[:16]}... from device {request.device_id}"
    )

    return CompactCapsuleResponse(
        accepted=True,
        capsule_id=capsule_id,
        queued=queued,
        message="Capsule queued for sync",
    )


@router.post("/sync")
async def sync_device_capsules(
    request: SyncRequest,
    current_user: Dict = Depends(get_current_user),
) -> SyncResponse:
    """
    Sync pending capsules for a device.

    Processes the queue of offline capsules and syncs them
    to the cloud database.
    """
    # Validate direction
    try:
        direction = SyncDirection(request.direction)
    except ValueError:
        valid_directions = [d.value for d in SyncDirection]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid direction. Must be one of: {valid_directions}",
        )

    # Perform sync
    result = edge_sync_service.sync_device(
        device_id=request.device_id,
        cloud_capsule_ids=[],  # Would query existing IDs in production
    )

    logger.info(
        f"Sync for device {request.device_id}: "
        f"{result.synced_count} synced, {result.failed_count} failed"
    )

    return SyncResponse(
        batch_id=result.batch_id,
        status=result.status.value,
        synced_count=result.synced_count,
        failed_count=result.failed_count,
        conflict_count=result.conflict_count,
        checkpoint_id=result.checkpoint.checkpoint_id if result.checkpoint else None,
        errors=result.errors,
    )


@router.post("/batch-sync")
async def batch_sync_capsules(
    request: BatchSyncRequest,
    current_user: Dict = Depends(get_current_user),
) -> BatchSyncResponse:
    """
    Submit and sync multiple capsules in a single request.

    More efficient than individual submissions for batch uploads.
    """
    total = len(request.capsules)
    synced = 0
    failed = 0
    errors = []

    decoder = CompactCapsuleDecoder()

    for i, capsule_b64 in enumerate(request.capsules):
        try:
            capsule_data = base64.b64decode(capsule_b64)
            # Validate format
            decoder.decode(capsule_data)
            # Queue
            edge_sync_service.queue_capsule(request.device_id, capsule_data)
            synced += 1
        except Exception as e:
            failed += 1
            errors.append(f"Capsule {i}: {str(e)}")

    # Trigger sync
    result = edge_sync_service.sync_device(request.device_id)

    logger.info(
        f"Batch sync for device {request.device_id}: "
        f"{synced} submitted, {result.synced_count} synced"
    )

    return BatchSyncResponse(
        batch_id=result.batch_id,
        status=result.status.value,
        total_submitted=total,
        synced_count=result.synced_count,
        failed_count=failed + result.failed_count,
        errors=errors + result.errors,
    )


@router.get("/pending")
async def get_pending_capsules(
    device_id: str = Query(..., description="Device identifier"),
    current_user: Dict = Depends(get_current_user),
) -> PendingCapsuleResponse:
    """
    Get pending (unsynced) capsules for a device.
    """
    pending = edge_sync_service.get_pending_capsules(device_id)

    # Extract capsule IDs
    decoder = CompactCapsuleDecoder()
    capsule_ids = []
    for capsule_data in pending:
        try:
            capsule = decoder.decode(capsule_data)
            capsule_ids.append(capsule.capsule_id_hex)
        except Exception:
            capsule_ids.append("invalid")

    return PendingCapsuleResponse(
        device_id=device_id,
        pending_count=len(pending),
        capsule_ids=capsule_ids,
    )


@router.post("/devices/register")
async def register_edge_device(
    request: DeviceRegistrationRequest,
    current_user: Dict = Depends(get_current_user),
) -> DeviceRegistrationResponse:
    """
    Register an edge device's public key for offline signature verification.
    """
    try:
        public_key = bytes.fromhex(request.public_key)
        if len(public_key) != 32:
            raise ValueError("Public key must be 32 bytes")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid public key: {e}",
        )

    registered = offline_signer_registry.register_device(
        device_id=request.device_id,
        public_key=public_key,
        metadata={
            "device_type": request.device_type,
            **(request.metadata or {}),
        },
    )

    logger.info(f"Registered edge device: {request.device_id}")

    return DeviceRegistrationResponse(
        registered=registered,
        device_id=request.device_id,
        message="Device registered successfully",
    )


@router.get("/devices")
async def list_registered_devices(
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    List all registered edge devices.
    """
    devices = offline_signer_registry.list_devices()
    return {
        "devices": devices,
        "total": len(devices),
    }


@router.get("/checkpoint/{device_id}")
async def get_device_checkpoint(
    device_id: str,
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get the current sync checkpoint for a device.
    """
    checkpoint = edge_sync_service.get_checkpoint(device_id)
    if not checkpoint:
        return {
            "device_id": device_id,
            "checkpoint": None,
            "message": "No checkpoint found",
        }

    return {
        "device_id": device_id,
        "checkpoint": checkpoint.to_dict(),
    }


@router.get("/sync-history")
async def get_sync_history(
    device_id: Optional[str] = Query(None, description="Filter by device"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get sync history.
    """
    history = edge_sync_service.get_sync_history(device_id=device_id, limit=limit)
    return {
        "history": [r.to_dict() for r in history],
        "total": len(history),
    }


@router.get("/stats")
async def get_edge_stats(
    current_user: Dict = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """
    Get edge sync statistics.
    """
    devices = offline_signer_registry.list_devices()
    history = edge_sync_service.get_sync_history(limit=1000)

    total_synced = sum(r.synced_count for r in history)
    total_failed = sum(r.failed_count for r in history)

    return {
        "registered_devices": len(devices),
        "total_synced_capsules": total_synced,
        "total_failed_syncs": total_failed,
        "sync_operations": len(history),
    }
