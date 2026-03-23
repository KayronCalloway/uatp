"""
Capsules Router - CRUD Operations
=================================

Endpoints for creating, reading, updating capsules.
"""

import base64
import zlib

from fastapi import APIRouter

from ._shared import (
    IS_SQLITE,
    Any,
    AsyncSession,
    CapsuleModel,
    Depends,
    Dict,
    HTTPException,
    Optional,
    Query,
    Request,
    capsule_lifecycle_service,
    func,
    get_correlation_id,
    get_current_user,
    get_current_user_optional,
    get_db_session,
    is_admin_user,
    is_envelope_format,
    is_placeholder_signature,
    json,
    logger,
    select,
    text,
    to_uuid,
    utc_now,
    uuid,
    wrap_in_uatp_envelope,
)

router = APIRouter()


@router.get("/")
async def list_capsules(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    type: Optional[str] = None,
    environment: Optional[str] = Query(
        None,
        pattern="^(test|development|production)$",
        description="Filter by environment",
    ),
    include_test: bool = Query(
        False, description="Include test data in results (default: exclude)"
    ),
    demo_mode: bool = Query(
        False,
        description="Include demo capsules (default: exclude demo capsules with 'demo-' prefix)",
    ),
    session: AsyncSession = Depends(get_db_session),
    current_user: Dict = Depends(get_current_user),
):
    """List capsules with pagination and filtering.

    SECURITY: Authentication required. Non-admin users only see their own capsules.
    """
    correlation_id = get_correlation_id()

    # SECURITY FIX: Authentication now required (was optional)
    user_is_admin = is_admin_user(current_user)
    user_id = current_user.get("user_id")

    logger.info(
        f"[{correlation_id}] GET /capsules - page={page}, per_page={per_page}, "
        f"type={type}, environment={environment}, include_test={include_test}, demo_mode={demo_mode}, "
        f"user_id={user_id}, is_admin={user_is_admin}"
    )

    try:
        # Build query
        query = select(CapsuleModel)

        # SECURITY: Non-admin users only see their own capsules (excludes legacy/NULL owner)
        # Admins see all capsules
        if not user_is_admin and user_id:
            query = query.where(CapsuleModel.owner_id == to_uuid(user_id))

        # Apply type filter
        if type:
            query = query.where(CapsuleModel.capsule_type == type)

        # Apply demo_mode filtering - exclude demo capsules unless demo_mode=True
        if not demo_mode:
            query = query.where(~CapsuleModel.capsule_id.like("demo-%"))

        # Apply environment filtering (skip JSONB on SQLite)
        # If environment is explicitly specified, use that. Otherwise apply include_test logic.
        if environment and not IS_SQLITE:
            # Filter by specific environment (overrides include_test)
            try:
                query = query.where(
                    text(
                        "payload::jsonb->'metadata'->>'environment' = :env"
                    ).bindparams(env=environment)
                )
            except Exception:
                # Fallback if JSON query fails
                pass
        elif not include_test and not IS_SQLITE:
            # Exclude test data by default - check if environment field exists and is not 'test'
            # Using JSON/JSONB query for PostgreSQL (payload->metadata->environment)
            try:
                query = query.where(
                    text(
                        "(payload::jsonb->'metadata'->>'environment' IS NULL OR payload::jsonb->'metadata'->>'environment' != 'test')"
                    )
                )
            except Exception:
                # Fallback if JSON query fails (e.g., SQLite)
                pass

        # Get total count
        count_query = select(func.count(CapsuleModel.id))

        # SECURITY: Non-admin users only see their own capsules
        if not user_is_admin and user_id:
            count_query = count_query.where(CapsuleModel.owner_id == to_uuid(user_id))

        if type:
            count_query = count_query.where(CapsuleModel.capsule_type == type)

        # Apply demo_mode filter to count query
        if not demo_mode:
            count_query = count_query.where(~CapsuleModel.capsule_id.like("demo-%"))

        # Apply same environment filters to count query (skip JSONB on SQLite)
        if environment and not IS_SQLITE:
            try:
                count_query = count_query.where(
                    text(
                        "payload::jsonb->'metadata'->>'environment' = :env"
                    ).bindparams(env=environment)
                )
            except Exception:
                pass
        elif not include_test and not IS_SQLITE:
            try:
                count_query = count_query.where(
                    text(
                        "(payload::jsonb->'metadata'->>'environment' IS NULL OR payload::jsonb->'metadata'->>'environment' != 'test')"
                    )
                )
            except Exception:
                pass

        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.order_by(CapsuleModel.timestamp.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        # Execute ORM query
        result = await session.execute(query)
        all_rows = result.all()
        logger.info(f"[{correlation_id}] Raw result rows: {len(all_rows)}")
        # Debug: check which rows have None objects
        none_count = sum(1 for row in all_rows if row[0] is None)
        if none_count > 0:
            logger.warning(
                f"[{correlation_id}] {none_count} rows returned None ORM objects - possible NULL primary keys"
            )
        capsules = [row[0] for row in all_rows if row[0] is not None]

        logger.info(f"[{correlation_id}] Query returned {len(capsules)} capsules")

        # Convert ORM objects to response format
        capsule_list = []
        for capsule in capsules:
            # Fix timestamp format - replace timezone with Z
            timestamp_str = None
            if capsule.timestamp:
                timestamp_str = capsule.timestamp.isoformat()
                if "+" in timestamp_str:
                    timestamp_str = timestamp_str.split("+")[0] + "Z"
                elif not timestamp_str.endswith("Z"):
                    timestamp_str += "Z"

            # Get verification data
            verification = capsule.verification
            if isinstance(verification, str):
                try:
                    verification = json.loads(verification)
                except Exception:
                    verification = {"verified": False, "message": "Invalid JSON"}
            if not verification:
                verification = {"verified": False, "message": "No verification data"}

            # Get payload data
            payload = capsule.payload
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {}

            # Wrap in UATP 7.0 envelope if not already wrapped
            if payload and not is_envelope_format(payload):
                agent_id = (
                    verification.get("signer", "claude-code")
                    if isinstance(verification, dict)
                    else "claude-code"
                )
                payload = wrap_in_uatp_envelope(
                    payload_data=payload,
                    capsule_id=capsule.capsule_id,
                    capsule_type=capsule.capsule_type,
                    agent_id=agent_id,
                    parent_capsules=[capsule.parent_capsule_id]
                    if capsule.parent_capsule_id
                    else None,
                )

            capsule_list.append(
                {
                    "id": capsule.capsule_id,
                    "capsule_id": capsule.capsule_id,
                    "type": capsule.capsule_type,
                    "version": capsule.version,
                    "timestamp": timestamp_str,
                    "status": capsule.status,
                    "verification": verification,
                    "payload": payload,
                }
            )

        logger.info(
            f"[{correlation_id}] Returning {len(capsule_list)} capsules, "
            f"total={total}, demo_mode={demo_mode}"
        )

        return {
            "capsules": capsule_list,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }

    except Exception as e:
        logger.error(f"[{correlation_id}] Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{capsule_id}")
async def get_capsule(
    capsule_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Get a specific capsule by ID (public: legacy capsules, auth: user's own capsules)"""
    correlation_id = get_correlation_id()

    # Optional auth
    current_user = get_current_user_optional(request)
    user_is_admin = is_admin_user(current_user) if current_user else False
    user_id = current_user.get("user_id") if current_user else None

    logger.info(f"[{correlation_id}] GET /capsules/{capsule_id} by user {user_id}")

    try:
        # Use ORM query
        query = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
        result = await session.execute(query)
        capsule = result.scalars().first()

        if not capsule:
            raise HTTPException(status_code=404, detail="Capsule not found")

        # SECURITY FIX: Strict ownership verification
        # - Legacy capsules (owner_id=NULL) are admin-only (system/migration data)
        # - Authenticated non-admin users can only access their own capsules
        # - Admins can access all capsules
        # - Unauthenticated users cannot access any capsules
        if not current_user:
            # Unauthenticated users cannot access individual capsules
            raise HTTPException(status_code=401, detail="Authentication required")

        if not user_is_admin:
            # Non-admin users cannot access legacy capsules (owner_id=NULL)
            if capsule.owner_id is None:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: legacy capsule (admin-only)",
                )
            # Non-admin users can only access their own capsules
            if str(capsule.owner_id) != user_id:
                raise HTTPException(status_code=403, detail="Access denied")

        # Fix timestamp format
        timestamp_str = None
        if capsule.timestamp:
            timestamp_str = capsule.timestamp.isoformat()
            if "+" in timestamp_str:
                timestamp_str = timestamp_str.split("+")[0] + "Z"
            elif not timestamp_str.endswith("Z"):
                timestamp_str += "Z"

        # Get verification data
        verification = capsule.verification
        if isinstance(verification, str):
            try:
                verification = json.loads(verification)
            except Exception:
                verification = {"verified": False, "message": "Invalid JSON"}
        if not verification:
            verification = {"verified": False, "message": "No verification data"}

        # Get payload data
        payload = capsule.payload
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}

        # Decompress payload if compressed
        compression_info = None
        if capsule.is_compressed and payload:
            try:
                compressed_data = payload.get("compressed_payload")
                if compressed_data:
                    compressed_bytes = base64.b64decode(compressed_data)

                    # SECURITY: Bounded decompression to prevent zip bombs (DoS)
                    max_decompressed_size = 10 * 1024 * 1024  # 10MB limit
                    decompressor = zlib.decompressobj()
                    decompressed_bytes = decompressor.decompress(
                        compressed_bytes, max_length=max_decompressed_size
                    )

                    if decompressor.unconsumed_tail:
                        raise ValueError(
                            f"Decompressed payload exceeds maximum size of {max_decompressed_size} bytes"
                        )

                    payload = json.loads(decompressed_bytes.decode("utf-8"))
                    compression_info = {
                        "was_compressed": True,
                        "method": capsule.compression_method,
                        "original_size": capsule.original_size,
                        "compressed_size": capsule.compressed_size,
                        "ratio": round(
                            capsule.compressed_size / capsule.original_size, 3
                        )
                        if capsule.original_size
                        else None,
                    }
            except Exception as e:
                logger.warning(f"Failed to decompress payload for {capsule_id}: {e}")

        # Wrap in UATP 7.0 envelope if not already wrapped
        if payload and not is_envelope_format(payload):
            agent_id = (
                verification.get("signer", "claude-code")
                if isinstance(verification, dict)
                else "claude-code"
            )
            payload = wrap_in_uatp_envelope(
                payload_data=payload,
                capsule_id=capsule.capsule_id,
                capsule_type=capsule.capsule_type,
                agent_id=agent_id,
                parent_capsules=[capsule.parent_capsule_id]
                if capsule.parent_capsule_id
                else None,
            )

        capsule_data = {
            "id": capsule.capsule_id,
            "capsule_id": capsule.capsule_id,
            "type": capsule.capsule_type,
            "version": capsule.version,
            "timestamp": timestamp_str,
            "status": capsule.status,
            "verification": verification,
            "payload": payload,
            "content_hash": capsule.content_hash,
            "prev_hash": capsule.prev_hash,
        }

        # Add compression info if payload was compressed
        if compression_info:
            capsule_data["compression"] = compression_info

        return {
            "capsule": capsule_data,
            "verification": verification,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/store")
async def store_presigned_capsule(
    capsule_data: Dict[str, Any],
    request: Request,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Store a pre-signed capsule (zero-trust mode).

    ZERO-TRUST: This endpoint accepts capsules that were signed locally by the SDK.
    The server does NOT sign on behalf of the user - it only stores and timestamps.

    The capsule MUST contain:
    - verification.signature: Ed25519 signature created by user's local key
    - verification.verify_key: User's public key for verification
    - verification.hash: SHA-256 hash of content

    Args:
        capsule_data: Pre-signed capsule data with verification block

    Returns:
        Success response with capsule_id
    """
    correlation_id = get_correlation_id()

    # SECURITY FIX: Authentication now required to store capsules
    user_id = current_user.get("sub") or current_user.get("user_id")
    try:
        user_uuid = uuid.UUID(str(user_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    try:
        # Validate that the capsule has a signature
        verification = capsule_data.get("verification", {})
        if not verification.get("signature"):
            raise HTTPException(
                status_code=400,
                detail="Pre-signed capsule must include verification.signature. "
                "Use the SDK's certify() method with local signing.",
            )

        # SECURITY: Reject placeholder signatures
        if is_placeholder_signature(verification.get("signature")):
            raise HTTPException(
                status_code=400,
                detail="Placeholder signatures are not allowed. "
                "Use the SDK's certify() method for cryptographic signing.",
            )

        if not verification.get("verify_key"):
            raise HTTPException(
                status_code=400,
                detail="Pre-signed capsule must include verification.verify_key",
            )

        # Mark as user-signed (not server-signed)
        if "signer" not in verification:
            verification["signer"] = "user"
        capsule_data["verification"] = verification

        # Extract or generate capsule_id
        capsule_id = capsule_data.get("capsule_id")
        if not capsule_id:
            capsule_id = (
                f"caps_{utc_now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"
            )
            capsule_data["capsule_id"] = capsule_id

        # Normalize capsule_type field name
        if "type" in capsule_data and "capsule_type" not in capsule_data:
            capsule_data["capsule_type"] = capsule_data.pop("type")

        # Create database record
        capsule = CapsuleModel(
            capsule_id=capsule_id,
            capsule_type=capsule_data.get("capsule_type", "user_signed"),
            status="sealed",
            version=capsule_data.get("version", "7.2"),
            payload=capsule_data.get("payload") or capsule_data.get("content", {}),
            verification=verification,
            timestamp=utc_now(),
            owner_id=user_uuid,
            content_hash=verification.get("hash"),
        )

        session.add(capsule)
        await session.commit()
        await session.refresh(capsule)

        logger.info(
            f"[{correlation_id}] Stored pre-signed capsule: {capsule_id} "
            f"(signer: user, verify_key: {verification.get('verify_key', '')[:16]}...)"
        )

        return {
            "success": True,
            "capsule_id": capsule_id,
            "message": "Pre-signed capsule stored successfully",
            "signer": "user",
            "zero_trust": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(
            f"[{correlation_id}] Failed to store pre-signed capsule: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to store capsule: {str(e)}"
        )


@router.post("/")
async def create_capsule(
    capsule_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new capsule with automatic lineage and chain tracking.

    DEPRECATED: This endpoint signs on the server. For zero-trust architecture,
    use the SDK's certify() method which signs locally, then POST to /capsules/store.

    If parent_capsule_id is provided, lineage edges are automatically registered.
    If chain_id is provided, the capsule is tracked for chain sealing.

    Args:
        capsule_data: Capsule data including optional parent_capsule_id and chain_id
        current_user: Authenticated user (injected by dependency)
        session: Database session (injected by dependency)

    Returns:
        Success response with capsule_id
    """
    user_id = current_user.get("sub") or current_user.get("user_id")
    try:
        user_uuid = uuid.UUID(str(user_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # Log deprecation warning
    logger.warning(
        "DEPRECATED: POST /capsules with server-side signing. "
        "Use SDK certify() + POST /capsules/store for zero-trust."
    )

    try:
        # Extract lineage and chain parameters
        parent_capsule_id = capsule_data.pop("parent_capsule_id", None)
        chain_id = capsule_data.pop("chain_id", None)

        # Normalize capsule_type field name
        if "type" in capsule_data and "capsule_type" not in capsule_data:
            capsule_data["capsule_type"] = capsule_data.pop("type")

        # Use lifecycle service for capsule creation with lineage/chain integration
        capsule = await capsule_lifecycle_service.create_capsule(
            capsule_data=capsule_data,
            session=session,
            parent_capsule_id=parent_capsule_id,
            chain_id=chain_id,
            owner_id=user_uuid,
        )

        return {
            "success": True,
            "capsule_id": capsule.capsule_id,
            "message": "Capsule created successfully",
            "lineage_registered": parent_capsule_id is not None,
            "chain_tracked": chain_id is not None,
            "warning": "DEPRECATED: Server-side signing. Use SDK certify() for zero-trust.",
        }

    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to create capsule: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to create capsule: {str(e)}"
        )


@router.post("/from-conversation")
async def create_capsule_from_conversation(
    request: Request,
    data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a capsule from a live conversation session.

    This endpoint captures conversation data and creates a sealed reasoning capsule.
    """
    correlation_id = get_correlation_id()

    try:
        session_id = data.get("session_id")
        conversation_data = data.get("conversation_data", {})

        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")

        # Extract user ID
        user_id = current_user.get("sub") or current_user.get("user_id")
        try:
            user_uuid = uuid.UUID(str(user_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        # Generate capsule ID
        capsule_id = f"caps_{utc_now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        # Create capsule from conversation
        # NOTE: This is an internal/system endpoint - capsules are NOT cryptographically signed.
        # For cryptographically signed capsules, use the SDK's certify() method.
        capsule_data = {
            "capsule_id": capsule_id,
            "capsule_type": "conversation_capture",
            "version": "7.1",
            "timestamp": utc_now().isoformat(),
            "status": "sealed",
            "payload": {
                "session_id": session_id,
                "conversation_data": conversation_data,
                "captured_at": utc_now().isoformat(),
            },
            "verification": {
                "signer": "system",  # Indicates NOT user-signed
                "signature": None,  # No cryptographic signature
                "note": "System-generated capsule without cryptographic signature. Use SDK certify() for signed capsules.",
            },
        }

        # Wrap in UATP envelope
        envelope = wrap_in_uatp_envelope(
            payload_data=capsule_data["payload"],
            capsule_id=capsule_id,
            capsule_type="conversation_capture",
        )

        # Create database record
        capsule = CapsuleModel(
            capsule_id=capsule_id,
            capsule_type="conversation_capture",
            status="sealed",
            version="7.1",
            payload=envelope,
            verification=capsule_data["verification"],
            timestamp=utc_now(),
            owner_id=user_uuid,
        )

        session.add(capsule)
        await session.commit()
        await session.refresh(capsule)

        logger.info(
            f"[{correlation_id}] Created capsule from conversation: {capsule_id}"
        )

        return {
            "success": True,
            "capsule_id": capsule_id,
            "session_id": session_id,
            "status": "sealed",
            "created_at": capsule.timestamp.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[{correlation_id}] Error creating capsule from conversation: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create capsule from conversation: {str(e)}",
        )


@router.post("/generic")
async def create_generic_capsule(
    request: Request,
    capsule_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a generic capsule with custom payload.

    This endpoint allows creating capsules of any type with custom data.
    """
    correlation_id = get_correlation_id()

    try:
        # Extract user ID
        user_id = current_user.get("sub") or current_user.get("user_id")
        try:
            user_uuid = uuid.UUID(str(user_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        # Generate capsule ID if not provided
        capsule_id = capsule_data.get(
            "capsule_id",
            f"caps_{utc_now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}",
        )
        capsule_type = capsule_data.get("capsule_type", "generic")

        # Get verification data - if not provided, mark as system-generated (not signed)
        # NOTE: For cryptographically signed capsules, use the SDK's certify() method.
        verification = capsule_data.get("verification")
        if not verification:
            verification = {
                "signer": "system",  # Indicates NOT user-signed
                "signature": None,  # No cryptographic signature
                "note": "System-generated capsule without cryptographic signature. Use SDK certify() for signed capsules.",
            }
        elif is_placeholder_signature(verification.get("signature")):
            # Reject placeholder signatures - they give false appearance of signing
            raise HTTPException(
                status_code=400,
                detail="Placeholder signatures are not allowed. Use SDK certify() for cryptographic signing, or omit verification for system-generated capsules.",
            )

        # Create database record
        capsule = CapsuleModel(
            capsule_id=capsule_id,
            capsule_type=capsule_type,
            status=capsule_data.get("status", "sealed"),
            version=capsule_data.get("version", "7.1"),
            payload=capsule_data.get("payload", {}),
            verification=verification,
            timestamp=utc_now(),
            owner_id=user_uuid,
        )

        session.add(capsule)
        await session.commit()
        await session.refresh(capsule)

        logger.info(f"[{correlation_id}] Created generic capsule: {capsule_id}")

        return {
            "success": True,
            "capsule_id": capsule_id,
            "capsule_type": capsule_type,
            "status": capsule.status,
            "created_at": capsule.timestamp.isoformat(),
        }

    except Exception as e:
        logger.error(
            f"[{correlation_id}] Error creating generic capsule: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create generic capsule: {str(e)}",
        )
