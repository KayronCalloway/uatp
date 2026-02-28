"""
FastAPI Capsules Router - Full Operational System
Provides real capsule CRUD operations with database persistence

⚠️  ACTIVE ROUTER - This file is used by the production API
⚠️  DO NOT EDIT: src/api/DEPRECATED_capsule_routes.py.old (old Quart version)

Request Flow:
  run.py → src.main:app → app_factory.create_app() → THIS ROUTER

Key Features:
  - Demo mode filtering: demo_mode=false excludes 'demo-*' capsules (default)
  - Environment filtering: include_test parameter
  - Pagination support with per_page and page parameters
  - SQLAlchemy ORM queries with async PostgreSQL
  - UATP 7.0 capsule format support
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth_middleware import (
    get_current_user,
    is_admin_user,
    require_admin,
)
from ..core.config import DATABASE_URL
from ..core.database import db
from ..models.capsule import CapsuleModel
from ..utils.timezone_utils import utc_now
from ..utils.uatp_envelope import is_envelope_format, wrap_in_uatp_envelope

# Check if using SQLite (JSONB syntax not supported)
IS_SQLITE = "sqlite" in DATABASE_URL.lower()

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/capsules", tags=["Capsules"])


def get_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing"""
    return str(uuid.uuid4())[:8]


async def get_db_session():
    """Dependency to get database session"""
    async with db.get_session() as session:
        yield session


@router.get("/stats")
async def get_capsule_stats(
    demo_mode: bool = Query(
        False,
        description="Include demo capsules (default: exclude demo capsules with 'demo-' prefix)",
    ),
    include_test: bool = Query(
        False, description="Include test data in results (default: exclude)"
    ),
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get comprehensive capsule statistics from database (user sees own capsules only)"""
    try:
        # Determine if user is admin
        user_is_admin = is_admin_user(current_user)
        user_id = current_user.get("user_id")

        # Build base query with demo filtering
        base_query = select(CapsuleModel)
        if not demo_mode:
            base_query = base_query.where(~CapsuleModel.capsule_id.like("demo-%"))

        # Get total count with demo filtering
        count_query = select(func.count(CapsuleModel.id))
        if not demo_mode:
            count_query = count_query.where(~CapsuleModel.capsule_id.like("demo-%"))

        # Non-admin users only see their own capsules
        if not user_is_admin:
            count_query = count_query.where(CapsuleModel.owner_id == user_id)

        # Apply test data filtering (skip on SQLite - JSONB syntax not supported)
        if not include_test and not IS_SQLITE:
            try:
                count_query = count_query.where(
                    text(
                        "(payload::jsonb->'metadata'->>'environment' IS NULL OR payload::jsonb->'metadata'->>'environment' != 'test')"
                    )
                )
            except:
                pass

        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Get counts by type with demo and test filtering
        type_query = select(
            CapsuleModel.capsule_type, func.count(CapsuleModel.id)
        ).group_by(CapsuleModel.capsule_type)
        if not demo_mode:
            type_query = type_query.where(~CapsuleModel.capsule_id.like("demo-%"))
        # Non-admin users only see their own capsules
        if not user_is_admin:
            type_query = type_query.where(CapsuleModel.owner_id == user_id)

        # Apply test data filtering to type query (skip on SQLite - JSONB syntax not supported)
        if not include_test and not IS_SQLITE:
            try:
                type_query = type_query.where(
                    text(
                        "(payload::jsonb->'metadata'->>'environment' IS NULL OR payload::jsonb->'metadata'->>'environment' != 'test')"
                    )
                )
            except:
                pass

        type_result = await session.execute(type_query)
        by_type = {row[0]: row[1] for row in type_result.fetchall()}

        # Get platform and significance data from JSONB
        # Note: This uses PostgreSQL JSONB syntax, will adapt for SQLite if needed
        platform_query = text(
            """
            SELECT
                payload->'analysis_metadata'->>'platform' as platform,
                COUNT(*) as count
            FROM capsules
            WHERE payload->'analysis_metadata'->>'platform' IS NOT NULL
            GROUP BY payload->'analysis_metadata'->>'platform'
        """
        )

        try:
            platform_result = await session.execute(platform_query)
            by_platform = {row[0]: row[1] for row in platform_result.fetchall()}
        except:
            # Fallback for SQLite or if JSONB query fails
            by_platform = {}

        # Get recent activity based on timestamp with demo and test filtering
        recent_query = select(func.count(CapsuleModel.id)).where(
            CapsuleModel.timestamp
            >= utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
        )
        if not demo_mode:
            recent_query = recent_query.where(~CapsuleModel.capsule_id.like("demo-%"))
        # Non-admin users only see their own capsules
        if not user_is_admin:
            recent_query = recent_query.where(CapsuleModel.owner_id == user_id)

        # Apply test data filtering to recent activity (skip on SQLite - JSONB syntax not supported)
        if not include_test and not IS_SQLITE:
            try:
                recent_query = recent_query.where(
                    text(
                        "(payload::jsonb->'metadata'->>'environment' IS NULL OR payload::jsonb->'metadata'->>'environment' != 'test')"
                    )
                )
            except:
                pass

        recent_24h_result = await session.execute(recent_query)
        recent_24h = recent_24h_result.scalar() or 0

        return {
            "total_capsules": total,
            "by_type": by_type,
            "by_platform": by_platform,
            "recent_activity": {
                "last_24h": recent_24h,
                "last_week": total,  # Simplified for now
                "last_month": total,
            },
            "database_connected": True,
        }

    except Exception as e:
        # If database query fails, return empty stats
        return {
            "total_capsules": 0,
            "by_type": {},
            "by_platform": {},
            "recent_activity": {"last_24h": 0, "last_week": 0, "last_month": 0},
            "database_connected": False,
            "error": str(e),
        }


@router.get("")
async def list_capsules(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    type: Optional[str] = None,
    environment: Optional[str] = Query(
        None,
        regex="^(test|development|production)$",
        description="Filter by environment",
    ),
    include_test: bool = Query(
        False, description="Include test data in results (default: exclude)"
    ),
    demo_mode: bool = Query(
        False,
        description="Include demo capsules (default: exclude demo capsules with 'demo-' prefix)",
    ),
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List capsules with pagination and filtering (user sees own capsules only)"""
    correlation_id = get_correlation_id()
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

        # Non-admin users only see their own capsules
        if not user_is_admin:
            query = query.where(CapsuleModel.owner_id == user_id)

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
                        f"payload::jsonb->'metadata'->>'environment' = '{environment}'"
                    )
                )
            except:
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
            except:
                # Fallback if JSON query fails (e.g., SQLite)
                pass

        # Get total count
        count_query = select(func.count(CapsuleModel.id))

        # Non-admin users only see their own capsules
        if not user_is_admin:
            count_query = count_query.where(CapsuleModel.owner_id == user_id)

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
                        f"payload::jsonb->'metadata'->>'environment' = '{environment}'"
                    )
                )
            except:
                pass
        elif not include_test and not IS_SQLITE:
            try:
                count_query = count_query.where(
                    text(
                        "(payload::jsonb->'metadata'->>'environment' IS NULL OR payload::jsonb->'metadata'->>'environment' != 'test')"
                    )
                )
            except:
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
                except:
                    verification = {"verified": False, "message": "Invalid JSON"}
            if not verification:
                verification = {"verified": False, "message": "No verification data"}

            # Get payload data
            payload = capsule.payload
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except:
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
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get a specific capsule by ID (users can only access their own capsules)"""
    correlation_id = get_correlation_id()
    user_is_admin = is_admin_user(current_user)
    user_id = current_user.get("user_id")

    logger.info(f"[{correlation_id}] GET /capsules/{capsule_id} by user {user_id}")

    try:
        # Use ORM query
        query = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
        result = await session.execute(query)
        capsule = result.scalars().first()

        if not capsule:
            raise HTTPException(status_code=404, detail="Capsule not found")

        # Verify ownership: non-admin users can only access their own capsules
        # Legacy capsules (owner_id=NULL) are only accessible to admins
        if not user_is_admin:
            if capsule.owner_id is None:
                raise HTTPException(
                    status_code=403, detail="Access denied: legacy capsule"
                )
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
            except:
                verification = {"verified": False, "message": "Invalid JSON"}
        if not verification:
            verification = {"verified": False, "message": "No verification data"}

        # Get payload data
        payload = capsule.payload
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except:
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

        capsule_data = {
            "id": capsule.capsule_id,
            "capsule_id": capsule.capsule_id,
            "type": capsule.capsule_type,
            "version": capsule.version,
            "timestamp": timestamp_str,
            "status": capsule.status,
            "verification": verification,
            "payload": payload,
        }

        return {
            "capsule": capsule_data,
            "verification": verification,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("")
async def create_capsule(
    capsule_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new capsule (assigned to the authenticated user)"""
    user_id = current_user.get("user_id")

    try:
        # Generate capsule ID if not provided
        capsule_id = capsule_data.get("capsule_id")
        if not capsule_id:
            # Generate hash-based ID
            content_str = json.dumps(capsule_data.get("payload", {}), sort_keys=True)
            capsule_id = hashlib.sha256(content_str.encode()).hexdigest()[:16]

        # CRITICAL: Preserve original timestamp if provided (for signature verification)
        # If we override the timestamp, the signature hash won't match
        original_timestamp = capsule_data.get("timestamp")
        if original_timestamp:
            if isinstance(original_timestamp, str):
                # Parse ISO format timestamp
                try:
                    timestamp = datetime.fromisoformat(
                        original_timestamp.replace("Z", "+00:00")
                    )
                except ValueError:
                    timestamp = datetime.now(timezone.utc)
            else:
                timestamp = original_timestamp
        else:
            timestamp = datetime.now(timezone.utc)

        # Create capsule object with owner_id from authenticated user
        capsule = CapsuleModel(
            capsule_id=capsule_id,
            owner_id=user_id,  # Assign to authenticated user for isolation
            capsule_type=capsule_data.get("type", "chat"),
            version=capsule_data.get("version", "1.0"),
            timestamp=timestamp,  # Use original timestamp to preserve signature validity
            status="SEALED",
            verification=capsule_data.get(
                "verification",
                {
                    "verified": True,
                    "hash": hashlib.sha256(capsule_id.encode()).hexdigest(),
                },
            ),
            payload=capsule_data.get("payload", {}),
            # Support encrypted payloads from client
            encrypted_payload=capsule_data.get("encrypted_payload"),
            encryption_metadata=capsule_data.get("encryption_metadata"),
        )

        session.add(capsule)
        await session.commit()

        return {
            "success": True,
            "capsule_id": capsule_id,
            "message": "Capsule created successfully",
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create capsule: {str(e)}"
        )


@router.get("/{capsule_id}/verify")
async def verify_capsule(
    capsule_id: str,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Verify a specific capsule's cryptographic integrity.

    CRITICAL SECURITY FIX: Now performs actual cryptographic verification
    using CryptoSealer.verify_capsule() instead of trusting metadata flags.

    Users can only verify capsules they own (privacy-first model).
    """
    user_is_admin = is_admin_user(current_user)
    user_id = current_user.get("user_id")

    try:
        # Import CryptoSealer for verification
        try:
            from src.security.crypto_sealer import CryptoSealer

            crypto_sealer = CryptoSealer()
        except ImportError:
            crypto_sealer = None
            logger.warning("CryptoSealer not available for verification")

        query = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
        result = await session.execute(query)
        capsule = result.scalar_one_or_none()

        if not capsule:
            raise HTTPException(status_code=404, detail="Capsule not found")

        # Verify ownership: non-admin users can only verify their own capsules
        if not user_is_admin:
            if capsule.owner_id is None:
                raise HTTPException(
                    status_code=403, detail="Access denied: legacy capsule"
                )
            if str(capsule.owner_id) != user_id:
                raise HTTPException(status_code=403, detail="Access denied")

        # Build full capsule data for verification - MUST match what was signed
        # The Pydantic model_dump() returns these keys:
        # capsule_id, capsule_type, reasoning_trace, status, timestamp, verification, version
        capsule_data = {
            "capsule_id": capsule.capsule_id,
            "capsule_type": capsule.capsule_type,
            "timestamp": capsule.timestamp,
            "status": capsule.status if hasattr(capsule, "status") else "sealed",
            "version": getattr(capsule, "version", "7.0"),
            "verification": capsule.verification
            if hasattr(capsule, "verification") and capsule.verification
            else None,
        }
        # Add reasoning_trace if it exists (stored in payload for reasoning_trace capsules)
        if capsule.capsule_type == "reasoning_trace":
            # Extract reasoning_trace from payload if stored there
            payload = capsule.payload or {}
            if "reasoning_trace" in payload:
                capsule_data["reasoning_trace"] = payload["reasoning_trace"]
            elif hasattr(capsule, "reasoning_trace") and capsule.reasoning_trace:
                capsule_data["reasoning_trace"] = capsule.reasoning_trace
            else:
                # Construct from payload structure - handle various formats safely
                trace_data = (
                    payload.get("trace", {})
                    if isinstance(payload.get("trace"), dict)
                    else {}
                )
                content_data = (
                    payload.get("content", {})
                    if isinstance(payload.get("content"), dict)
                    else {}
                )
                metadata = (
                    payload.get("metadata", {})
                    if isinstance(payload.get("metadata"), dict)
                    else {}
                )

                # Try to extract conclusion from nested structure, fall back to simple content string
                conclusion = "Auto-captured"
                if isinstance(content_data, dict) and isinstance(
                    content_data.get("data"), dict
                ):
                    reasoning_steps = content_data.get("data", {}).get(
                        "reasoning_steps", []
                    )
                    if reasoning_steps and isinstance(reasoning_steps[0], dict):
                        conclusion = reasoning_steps[0].get("content", "Auto-captured")
                elif isinstance(payload.get("content"), str):
                    conclusion = payload.get("content", "Auto-captured")

                capsule_data["reasoning_trace"] = {
                    "steps": trace_data.get("reasoning_steps", [])
                    if isinstance(trace_data, dict)
                    else [],
                    "conclusion": conclusion,
                    "confidence_score": metadata.get("significance_score", 0.8)
                    if isinstance(metadata, dict)
                    else 0.8,
                    "alternatives_considered": [],
                }

        logger.info(f"🔍 DEBUG Verification data: {capsule_data.get('verification')}")

        payload = capsule.payload or {}

        # CRITICAL: Perform actual cryptographic verification
        verification_result = {"method": "none", "verified": False, "error": None}

        if crypto_sealer and crypto_sealer.enabled:
            # Check if capsule has signature (v7.0 stores in root-level verification.signature)
            verification_data = capsule_data.get("verification", {}) or payload.get(
                "verification", {}
            )
            # Ensure verification_data is a dict before checking for key
            has_signature = "signature" in payload or (
                isinstance(verification_data, dict) and "signature" in verification_data
            )

            if has_signature:
                try:
                    # Perform ACTUAL cryptographic verification
                    is_valid = crypto_sealer.verify_capsule(capsule_data)

                    verification_result = {
                        "method": "Ed25519Signature2020",
                        "verified": is_valid,
                        "error": None
                        if is_valid
                        else "Signature verification failed - content may have been tampered",
                    }

                    logger.info(
                        f"🔐 Cryptographic verification for {capsule_id}: {'VALID' if is_valid else 'INVALID'}"
                    )

                except Exception as verify_error:
                    verification_result = {
                        "method": "Ed25519Signature2020",
                        "verified": False,
                        "error": f"Verification exception: {str(verify_error)}",
                    }
                    logger.error(
                        f"❌ Verification error for {capsule_id}: {verify_error}"
                    )
            else:
                verification_result = {
                    "method": "none",
                    "verified": False,
                    "error": "No cryptographic signature found in capsule",
                }
        else:
            verification_result = {
                "method": "none",
                "verified": False,
                "error": "CryptoSealer not available or disabled",
            }

        # Extract signature metadata for response (check both root and payload locations)
        signature_info = payload.get("signature", {})
        if not signature_info:
            # Check root-level verification (v7.0 format)
            verification_data = capsule_data.get("verification", {}) or payload.get(
                "verification", {}
            )
            # Ensure verification_data is a dict before calling .get()
            if verification_data and isinstance(verification_data, dict):
                signature_info = {
                    "signature": verification_data.get("signature"),
                    "signer": verification_data.get("signer"),
                    "verify_key": verification_data.get("verify_key"),
                    "hash": verification_data.get("hash"),
                }

        return {
            "capsule_id": capsule_id,
            "verified": verification_result["verified"],
            "verification_method": verification_result["method"],
            "verification_error": verification_result["error"],
            "signature_present": bool(
                signature_info and signature_info.get("signature")
            ),
            "signature_metadata": signature_info if signature_info else None,
            "message": f"Capsule signature {'VERIFIED' if verification_result['verified'] else 'NOT VERIFIED'}",
            "status": capsule.status,
            "timestamp": capsule.timestamp.isoformat() if capsule.timestamp else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verification endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")


# ============================================================================
# OUTCOME TRACKING ENDPOINTS
# ============================================================================


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

        logger.info(f"📊 Recorded outcome for {capsule_id}: {outcome_status}")

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
            status_query = status_query.where(CapsuleModel.owner_id == user_id)
        status_result = await session.execute(status_query)
        status_counts = {
            status or "untracked": count for status, count in status_result.fetchall()
        }

        # Average rating
        rating_query = select(func.avg(CapsuleModel.user_feedback_rating)).where(
            CapsuleModel.user_feedback_rating.isnot(None)
        )
        if not user_is_admin:
            rating_query = rating_query.where(CapsuleModel.owner_id == user_id)
        rating_result = await session.execute(rating_query)
        avg_rating = rating_result.scalar()

        # Count with feedback
        feedback_count_query = select(func.count(CapsuleModel.id)).where(
            CapsuleModel.user_feedback_text.isnot(None)
        )
        if not user_is_admin:
            feedback_count_query = feedback_count_query.where(
                CapsuleModel.owner_id == user_id
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


# ============================================================================
# ADMIN METADATA-ONLY ENDPOINT
# ============================================================================


@router.get("/admin/stats")
async def admin_capsule_stats(
    admin: Dict = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Admin-only endpoint: aggregate capsule statistics without payloads.

    Returns metadata only (counts, types, timestamps) - NO sensitive payloads.
    This supports the privacy model where admins see metadata but not content.
    """
    try:
        # Total capsules
        total_query = select(func.count(CapsuleModel.id))
        total_result = await session.execute(total_query)
        total = total_result.scalar() or 0

        # Count by type
        type_query = select(
            CapsuleModel.capsule_type, func.count(CapsuleModel.id)
        ).group_by(CapsuleModel.capsule_type)
        type_result = await session.execute(type_query)
        by_type = {row[0]: row[1] for row in type_result.fetchall()}

        # Count by owner (shows user distribution without exposing data)
        owner_query = select(
            CapsuleModel.owner_id, func.count(CapsuleModel.id)
        ).group_by(CapsuleModel.owner_id)
        owner_result = await session.execute(owner_query)
        by_owner_raw = {
            str(row[0]) if row[0] else "legacy": row[1]
            for row in owner_result.fetchall()
        }

        # Summary by owner (don't expose UUIDs)
        owner_count = len([k for k in by_owner_raw.keys() if k != "legacy"])
        legacy_count = by_owner_raw.get("legacy", 0)

        # Count by outcome status
        outcome_query = select(
            CapsuleModel.outcome_status, func.count(CapsuleModel.id)
        ).group_by(CapsuleModel.outcome_status)
        outcome_result = await session.execute(outcome_query)
        by_outcome = {
            (row[0] or "untracked"): row[1] for row in outcome_result.fetchall()
        }

        # Recent activity (last 24h, last 7d, last 30d)
        now = utc_now()
        recent_24h_query = select(func.count(CapsuleModel.id)).where(
            CapsuleModel.timestamp
            >= now.replace(hour=0, minute=0, second=0, microsecond=0)
        )
        recent_24h_result = await session.execute(recent_24h_query)
        recent_24h = recent_24h_result.scalar() or 0

        # Count encrypted capsules
        encrypted_query = select(func.count(CapsuleModel.id)).where(
            CapsuleModel.encrypted_payload.isnot(None)
        )
        encrypted_result = await session.execute(encrypted_query)
        encrypted_count = encrypted_result.scalar() or 0

        return {
            "total_capsules": total,
            "by_type": by_type,
            "by_outcome": by_outcome,
            "ownership": {
                "total_owners": owner_count,
                "legacy_capsules": legacy_count,
                "user_owned": total - legacy_count,
            },
            "encryption": {
                "encrypted_capsules": encrypted_count,
                "unencrypted_capsules": total - encrypted_count,
            },
            "recent_activity": {
                "last_24h": recent_24h,
            },
            "message": "Admin statistics (metadata only, no payloads)",
        }

    except Exception as e:
        logger.error(f"Admin stats error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get admin stats: {str(e)}"
        )
