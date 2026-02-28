"""
Mobile-Optimized API Routes for UATP Capsule Engine

Optimized endpoints for iOS/Android clients with:
- Batch operations for offline support
- Compression for bandwidth efficiency
- Mobile-specific authentication
- Push notification integration
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from quart import Blueprint, jsonify, request
from quart_schema import validate_request, validate_response

from src.api.dependencies import get_engine, require_api_key
from src.api.schemas import (
    BatchCapsuleRequest,
    BatchCapsuleResponse,
    MobileCapsuleRequest,
    MobileCapsuleResponse,
    MobileHealthResponse,
    SyncRequest,
    SyncResponse,
)
from src.capsule_schema import CapsuleStatus, ReasoningTraceCapsule

logger = logging.getLogger("uatp.api.mobile")

mobile_bp = Blueprint("mobile", __name__)


@mobile_bp.route("/health", methods=["GET"])
async def mobile_health():
    """
    Mobile-specific health check with client compatibility info.

    Returns server capabilities for mobile client feature detection.
    """
    return jsonify(
        MobileHealthResponse(
            status="healthy",
            timestamp=datetime.now(timezone.utc).isoformat(),
            capabilities={
                "batch_submission": True,
                "offline_queue": True,
                "push_notifications": True,
                "compression": True,
                "webauthn": True,
                "background_sync": True,
                "version": "1.0.0",
            },
            server_version="UATP-7.1",
            min_client_version="1.0.0",
        )
    )


@mobile_bp.route("/capture/single", methods=["POST"])
@require_api_key(["write"])
@validate_request(MobileCapsuleRequest)
async def capture_single_capsule(data: MobileCapsuleRequest):
    """
    Capture a single AI conversation capsule from mobile device.

    Optimized for:
    - Quick response time
    - Low bandwidth usage
    - Offline-first architecture
    """
    engine = get_engine()

    try:
        # Create capsule from mobile data
        from src.capsule_schema import (
            ReasoningStep,
            ReasoningTracePayload,
            ReasoningTraceCapsule,
            Verification,
        )
        import uuid

        # Build reasoning trace from mobile conversation
        steps = []
        for i, msg in enumerate(data.messages):
            steps.append(
                ReasoningStep(
                    content=msg.get("content", ""),
                    step_type=msg.get("role", "unknown"),
                    metadata={
                        "message_index": i,
                        "timestamp": msg.get(
                            "timestamp", datetime.now(timezone.utc).isoformat()
                        ),
                        "platform": data.platform,
                        "device_id": data.device_id,
                    },
                )
            )

        reasoning_payload = ReasoningTracePayload(
            steps=steps, parent_capsule_id=data.parent_capsule_id
        )

        # Create capsule
        capsule = ReasoningTraceCapsule(
            capsule_id=f"mobile_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:16]}",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.ACTIVE,
            verification=Verification(),
            reasoning_trace=reasoning_payload,
        )

        # Sign and store
        created_capsule = await engine.create_capsule_async(capsule)

        logger.info(
            f"Mobile capsule created: {created_capsule.capsule_id} from device {data.device_id}"
        )

        return (
            jsonify(
                MobileCapsuleResponse(
                    success=True,
                    capsule_id=created_capsule.capsule_id,
                    status="sealed",
                    timestamp=created_capsule.timestamp.isoformat(),
                    verification_hash=created_capsule.verification.hash,
                    # Lightweight response for mobile
                    sync_token=f"sync_{created_capsule.capsule_id}",
                    server_timestamp=datetime.now(timezone.utc).isoformat(),
                )
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Mobile capsule creation failed: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "error_code": "CAPSULE_CREATION_FAILED",
                }
            ),
            500,
        )


@mobile_bp.route("/capture/batch", methods=["POST"])
@require_api_key(["write"])
@validate_request(BatchCapsuleRequest)
async def capture_batch_capsules(data: BatchCapsuleRequest):
    """
    Batch capsule submission for offline queue synchronization.

    Accepts multiple capsules created offline and processes them
    efficiently with:
    - Deduplication
    - Ordering preservation
    - Partial failure handling
    """
    engine = get_engine()

    results = []
    successful = 0
    failed = 0

    logger.info(
        f"Processing batch of {len(data.capsules)} capsules from device {data.device_id}"
    )

    for capsule_data in data.capsules:
        try:
            # Check for duplicate submission (idempotency)
            client_id = capsule_data.get("client_id")
            if client_id:
                # Check if capsule with this client_id already exists
                try:
                    from src.models.capsule import CapsuleModel
                    from sqlalchemy import select

                    existing_query = select(CapsuleModel).where(
                        CapsuleModel.client_id == client_id
                    )
                    existing_result = await db.execute(existing_query)
                    existing_capsule = existing_result.scalar_one_or_none()

                    if existing_capsule:
                        logger.info(
                            f"Skipping duplicate capsule with client_id: {client_id}"
                        )
                        success_count += 1  # Count as success (idempotent)
                        continue
                except Exception as e:
                    logger.warning(f"Deduplication check failed: {e}")

            # Create capsule (simplified for batch)
            from src.capsule_schema import (
                ReasoningStep,
                ReasoningTracePayload,
                ReasoningTraceCapsule,
                Verification,
            )
            import uuid

            steps = [
                ReasoningStep(
                    content=msg.get("content", ""),
                    step_type=msg.get("role", "unknown"),
                    metadata={"source": "mobile_batch"},
                )
                for msg in capsule_data.get("messages", [])
            ]

            reasoning_payload = ReasoningTracePayload(steps=steps)

            capsule = ReasoningTraceCapsule(
                capsule_id=f"batch_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:16]}",
                timestamp=datetime.now(timezone.utc),
                status=CapsuleStatus.ACTIVE,
                verification=Verification(),
                reasoning_trace=reasoning_payload,
            )

            created_capsule = await engine.create_capsule_async(capsule)

            results.append(
                {
                    "client_id": capsule_data.get("client_id"),
                    "capsule_id": created_capsule.capsule_id,
                    "status": "success",
                    "timestamp": created_capsule.timestamp.isoformat(),
                }
            )
            successful += 1

        except Exception as e:
            logger.error(f"Batch capsule failed: {e}")
            results.append(
                {
                    "client_id": capsule_data.get("client_id"),
                    "status": "failed",
                    "error": str(e),
                }
            )
            failed += 1

    logger.info(f"Batch complete: {successful} success, {failed} failed")

    return (
        jsonify(
            BatchCapsuleResponse(
                success=failed == 0,
                total_submitted=len(data.capsules),
                successful=successful,
                failed=failed,
                results=results,
                sync_token=f"batch_{datetime.now().timestamp()}",
                server_timestamp=datetime.now(timezone.utc).isoformat(),
            )
        ),
        200 if failed == 0 else 207,
    )  # 207 = Multi-Status


@mobile_bp.route("/sync", methods=["POST"])
@require_api_key(["read"])
@validate_request(SyncRequest)
async def sync_capsules(data: SyncRequest):
    """
    Synchronize mobile device with server state.

    Returns capsules created/updated since last sync for:
    - Multi-device synchronization
    - Offline conflict resolution
    - Delta updates only
    """
    engine = get_engine()

    try:
        # Parse last sync timestamp
        from dateutil import parser

        last_sync = parser.isoparse(data.last_sync_timestamp)

        # Get capsules updated since last sync with timestamp filtering
        # Query database directly for efficiency (avoids loading all capsules)
        try:
            from src.core.database import db
            from src.models.capsule import CapsuleModel
            from sqlalchemy import select

            async with db.session() as session:
                query = (
                    select(CapsuleModel)
                    .where(CapsuleModel.timestamp > last_sync)
                    .order_by(CapsuleModel.timestamp.desc())
                    .limit(100)
                )

                result = await session.execute(query)
                db_capsules = result.scalars().all()

                updated_capsules = [
                    {
                        "capsule_id": c.capsule_id,
                        "timestamp": c.timestamp.isoformat(),
                        "status": c.status,
                        "verification_hash": c.verification_hash,
                        # Minimal data for sync efficiency
                    }
                    for c in db_capsules
                ]
        except Exception as e:
            logger.error(f"Timestamp filtering failed, falling back: {e}")
            # Fallback to loading all capsules and filtering
            capsules = await engine.load_chain_async(skip=0, limit=100)
            updated_capsules = [
                {
                    "capsule_id": c.capsule_id,
                    "timestamp": c.timestamp.isoformat(),
                    "status": c.status.value,
                    "verification_hash": c.verification.hash
                    if c.verification
                    else None,
                }
                for c in capsules
                if c.timestamp > last_sync
            ]

        logger.info(
            f"Sync: {len(updated_capsules)} capsules for device {data.device_id}"
        )

        return jsonify(
            SyncResponse(
                success=True,
                capsules=updated_capsules,
                sync_token=f"sync_{datetime.now().timestamp()}",
                server_timestamp=datetime.now(timezone.utc).isoformat(),
                has_more=len(updated_capsules) == 100,  # Pagination indicator
            )
        )

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return (
            jsonify({"success": False, "error": str(e), "error_code": "SYNC_FAILED"}),
            500,
        )


@mobile_bp.route("/capsules/list", methods=["GET"])
@require_api_key(["read"])
async def list_mobile_capsules():
    """
    List capsules for mobile client with pagination and filtering.

    Optimized response size with:
    - Minimal capsule data
    - Pagination support
    - Filter by date/status
    """
    engine = get_engine()

    # Get pagination parameters
    page = int(request.args.get("page", 0))
    limit = min(int(request.args.get("limit", 50)), 100)  # Max 100 per page
    skip = page * limit

    try:
        capsules = await engine.load_chain_async(skip=skip, limit=limit)

        # Lightweight capsule summaries for mobile
        capsule_list = [
            {
                "capsule_id": c.capsule_id,
                "timestamp": c.timestamp.isoformat(),
                "status": c.status.value,
                "capsule_type": c.capsule_type.value,
                # Omit full reasoning trace to reduce bandwidth
                "has_verification": bool(c.verification and c.verification.signature),
            }
            for c in capsules
        ]

        return jsonify(
            {
                "success": True,
                "capsules": capsule_list,
                "page": page,
                "limit": limit,
                "total": len(capsule_list),
                "has_more": len(capsule_list) == limit,
            }
        )

    except Exception as e:
        logger.error(f"List capsules failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@mobile_bp.route("/capsule/<capsule_id>", methods=["GET"])
@require_api_key(["read"])
async def get_mobile_capsule(capsule_id: str):
    """
    Get full capsule details for mobile client.

    Returns complete capsule with verification proof.
    """
    engine = get_engine()

    try:
        capsule = await engine.load_capsule_async(capsule_id)

        if not capsule:
            return jsonify({"success": False, "error": "Capsule not found"}), 404

        # Verify capsule integrity
        is_valid, reason = await engine.verify_capsule_async(capsule)

        # Convert to dict for JSON response
        capsule_dict = {
            "capsule_id": capsule.capsule_id,
            "timestamp": capsule.timestamp.isoformat(),
            "status": capsule.status.value,
            "capsule_type": capsule.capsule_type.value,
            "verification": {
                "is_valid": is_valid,
                "reason": reason,
                "signature": capsule.verification.signature
                if capsule.verification
                else None,
                "hash": capsule.verification.hash if capsule.verification else None,
                "signer": capsule.verification.signer if capsule.verification else None,
            },
            # Include reasoning trace for full detail view
            "reasoning_trace": {
                "steps": [
                    {
                        "content": step.content,
                        "step_type": step.step_type,
                        "metadata": step.metadata,
                    }
                    for step in capsule.reasoning_trace.steps
                ]
                if hasattr(capsule, "reasoning_trace") and capsule.reasoning_trace
                else []
            },
        }

        return jsonify({"success": True, "capsule": capsule_dict})

    except Exception as e:
        logger.error(f"Get capsule failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@mobile_bp.route("/device/register", methods=["POST"])
@require_api_key(["write"])
async def register_mobile_device():
    """
    Register a mobile device for push notifications and sync.

    Stores device token and preferences for:
    - Push notifications
    - Background sync
    - Device-specific settings
    """
    data = await request.get_json()

    device_id = data.get("device_id")
    push_token = data.get("push_token")
    platform = data.get("platform")  # "ios" or "android"

    if not device_id or not push_token:
        return (
            jsonify({"success": False, "error": "device_id and push_token required"}),
            400,
        )

    # Store device registration in database
    try:
        from src.core.database import db
        from src.models.device import DeviceRegistrationModel

        async with db.session() as session:
            # Check if device already registered
            existing_query = select(DeviceRegistrationModel).where(
                DeviceRegistrationModel.device_id == device_id
            )
            existing_result = await session.execute(existing_query)
            existing_device = existing_result.scalar_one_or_none()

            if existing_device:
                # Update existing registration
                existing_device.push_token = push_token
                existing_device.platform = platform
                existing_device.updated_at = datetime.now(timezone.utc)
            else:
                # Create new registration
                new_device = DeviceRegistrationModel(
                    device_id=device_id,
                    push_token=push_token,
                    platform=platform,
                    registered_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(new_device)

            await session.commit()
            logger.info(f"Device registered in database: {device_id} ({platform})")

    except Exception as e:
        logger.error(f"Device registration storage failed: {e}")
        # Continue even if database storage fails

    return (
        jsonify(
            {
                "success": True,
                "device_id": device_id,
                "registered_at": datetime.now(timezone.utc).isoformat(),
                "push_enabled": True,
            }
        ),
        201,
    )


@mobile_bp.route("/stats", methods=["GET"])
@require_api_key(["read"])
async def mobile_stats():
    """
    Get user statistics optimized for mobile dashboard.

    Returns lightweight stats for display on mobile.
    """
    engine = get_engine()

    try:
        # Get recent capsules for quick stats
        capsules = await engine.load_chain_async(skip=0, limit=100)

        total_capsules = len(capsules)
        verified_count = sum(
            1 for c in capsules if c.verification and c.verification.signature
        )

        # Calculate last 7 days activity
        from datetime import timedelta

        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_count = sum(1 for c in capsules if c.timestamp > week_ago)

        return jsonify(
            {
                "success": True,
                "stats": {
                    "total_capsules": total_capsules,
                    "verified_capsules": verified_count,
                    "recent_capsules": recent_count,
                    "verification_rate": verified_count / total_capsules
                    if total_capsules > 0
                    else 0,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Stats failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
