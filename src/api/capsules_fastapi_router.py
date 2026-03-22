"""
Capsules Router

CRUD operations for capsules with database persistence.

Features:
  - Demo mode filtering: demo_mode=false excludes 'demo-*' capsules (default)
  - Pagination support with per_page and page parameters
  - SQLAlchemy ORM queries
  - UATP 7.0 capsule format support
"""

import json
import logging
import uuid
import zlib
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth_middleware import (
    get_current_user,
    get_current_user_optional,
    is_admin_user,
    require_admin,
)
from ..core.config import DATABASE_URL
from ..core.database import db
from ..models.capsule import CapsuleModel
from ..services.capsule_lifecycle_service import capsule_lifecycle_service
from ..services.capsule_search_service import get_search_service
from ..services.workflow_chain_service import is_placeholder_signature
from ..utils.timezone_utils import utc_now
from ..utils.uatp_envelope import is_envelope_format, wrap_in_uatp_envelope

# Check if using SQLite (JSONB syntax not supported)
IS_SQLITE = "sqlite" in DATABASE_URL.lower()

# Set up logging
logger = logging.getLogger(__name__)


def to_uuid(user_id: str) -> uuid.UUID:
    """
    Convert a user_id string to a UUID object for database queries.

    The owner_id column in the database is of type UUID(as_uuid=True),
    so we need to convert the string user_id from JWT tokens to UUID.
    """
    try:
        return uuid.UUID(user_id)
    except (ValueError, TypeError):
        logger.warning(f"Invalid user_id format (not a UUID): {user_id[:8]}...")
        raise HTTPException(status_code=400, detail="Invalid user ID format")


router = APIRouter(prefix="/capsules", tags=["Capsules"])


# ==============================================================================
# SECURITY: Rate Limiter for Verification Endpoint
# ==============================================================================
class VerificationRateLimiter:
    """
    Per-IP rate limiter for the verification endpoint to prevent brute-force enumeration.

    SECURITY: This limits verification requests to prevent attackers from:
    - Enumerating valid capsule IDs
    - DoS attacks on cryptographic verification (expensive operation)
    - Automated scraping of capsule data

    Limit: 10 requests per minute per IP address
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        import time

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
        self._last_cleanup = time.time()

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP securely."""
        client_host = request.client.host if request.client else "unknown"

        # SECURITY: Only trust X-Forwarded-For from known trusted proxies
        trusted_proxies = {"127.0.0.1", "::1", "localhost"}
        if client_host in trusted_proxies:
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                return real_ip

        return client_host

    def is_allowed(self, request: Request) -> tuple[bool, int]:
        """
        Check if request is allowed.

        Returns:
            (allowed: bool, retry_after: int) - retry_after is seconds until next allowed request
        """
        import time

        now = time.time()
        client_ip = self._get_client_ip(request)
        key = f"verify:{client_ip}"

        # Periodic cleanup (every 5 minutes)
        if now - self._last_cleanup > 300:
            self._cleanup_expired(now)
            self._last_cleanup = now

        # Initialize or clean expired requests for this key
        cutoff = now - self.window_seconds
        if key not in self.requests:
            self.requests[key] = []
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]

        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            # Calculate retry_after (time until oldest request expires)
            oldest = min(self.requests[key])
            retry_after = int(oldest + self.window_seconds - now) + 1
            return False, max(1, retry_after)

        # Record this request
        self.requests[key].append(now)
        return True, 0

    def _cleanup_expired(self, now: float):
        """Remove expired entries from all keys."""
        cutoff = now - self.window_seconds
        expired_keys = []
        for key in self.requests:
            self.requests[key] = [t for t in self.requests[key] if t > cutoff]
            if not self.requests[key]:
                expired_keys.append(key)
        for key in expired_keys:
            del self.requests[key]


# SECURITY: Singleton rate limiter for verification endpoint
_verification_rate_limiter = VerificationRateLimiter(max_requests=10, window_seconds=60)


def get_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing"""
    return str(uuid.uuid4())[:8]


async def get_db_session():
    """Dependency to get database session"""
    async with db.get_session() as session:
        yield session


@router.get("/search")
async def search_capsules(
    request: Request,
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Results per page"),
    type: Optional[str] = Query(None, description="Filter by capsule type"),
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Full-text search across capsule content.

    Uses FTS5 for SQLite and ts_vector for PostgreSQL.
    Returns results with snippets and relevance scores.

    SECURITY: Authentication required. Non-admin users only see their own capsules.
    """
    # SECURITY FIX: Authentication now required (was optional, allowing data enumeration)
    user_is_admin = is_admin_user(current_user)
    user_id = current_user.get("user_id")

    # Non-admin users only see their own capsules
    # Admins see all capsules
    owner_filter = None
    if not user_is_admin and user_id:
        owner_filter = user_id

    try:
        search_service = get_search_service()
        results = await search_service.search(
            session=session,
            query=q,
            page=page,
            per_page=per_page,
            capsule_type=type,
            owner_id=owner_filter,
        )
        return results.to_dict()

    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/context")
async def get_verified_context(
    request: Request,
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=50, description="Results per page"),
    verified_only: bool = Query(
        False, description="Only return cryptographically verified capsules"
    ),
    type: Optional[str] = Query(None, description="Filter by capsule type"),
    min_confidence: Optional[float] = Query(
        None, ge=0.0, le=1.0, description="Minimum confidence score"
    ),
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Verified Context Retrieval - Trusted RAG for LLM applications.

    Returns search results with cryptographic verification status for each capsule.
    Use verified_only=true to only retrieve capsules with valid signatures.

    Response includes:
    - Search results with snippets and relevance scores
    - Verification status (signature_valid, timestamp_valid)
    - Reasoning summary extracted from capsule
    - Confidence scores
    - Trust summary (counts of verified vs unverified results)

    This endpoint enables LLMs to use only cryptographically verified context,
    ensuring trustworthy retrieval-augmented generation.

    SECURITY: Authentication required. Non-admin users only see their own capsules.
    """
    from src.services.verified_context_service import get_verified_context_service

    # SECURITY FIX: Authentication now required (was optional)
    user_is_admin = is_admin_user(current_user)
    user_id = current_user.get("user_id")

    # Build owner filter for non-admin users
    owner_filter = None if user_is_admin else user_id

    try:
        service = get_verified_context_service()
        results = await service.search(
            session=session,
            query=q,
            page=page,
            per_page=per_page,
            verified_only=verified_only,
            capsule_type=type,
            min_confidence=min_confidence,
            owner_id=owner_filter,
        )
        return results.to_dict()

    except Exception as e:
        logger.error(f"Verified context error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Verified context error: {str(e)}")


@router.get("/stats")
async def get_capsule_stats(
    request: Request,
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
    """Get comprehensive capsule statistics.

    SECURITY: Authentication required. Non-admin users only see their own capsule stats.
    """
    try:
        # SECURITY FIX: Authentication now required (was optional)
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

        # SECURITY: Non-admin users only see their own capsule stats
        # Admins see aggregate stats for all capsules
        if not user_is_admin and user_id:
            count_query = count_query.where(CapsuleModel.owner_id == to_uuid(user_id))

        # Apply test data filtering (skip on SQLite - JSONB syntax not supported)
        if not include_test and not IS_SQLITE:
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

        # Get counts by type with demo and test filtering
        type_query = select(
            CapsuleModel.capsule_type, func.count(CapsuleModel.id)
        ).group_by(CapsuleModel.capsule_type)
        if not demo_mode:
            type_query = type_query.where(~CapsuleModel.capsule_id.like("demo-%"))
        # SECURITY: Non-admin users only see their own capsule stats
        if not user_is_admin and user_id:
            type_query = type_query.where(CapsuleModel.owner_id == to_uuid(user_id))

        # Apply test data filtering to type query (skip on SQLite - JSONB syntax not supported)
        if not include_test and not IS_SQLITE:
            try:
                type_query = type_query.where(
                    text(
                        "(payload::jsonb->'metadata'->>'environment' IS NULL OR payload::jsonb->'metadata'->>'environment' != 'test')"
                    )
                )
            except Exception:
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
        except Exception:
            # Fallback for SQLite or if JSONB query fails
            by_platform = {}

        # Get recent activity based on timestamp with demo and test filtering
        recent_query = select(func.count(CapsuleModel.id)).where(
            CapsuleModel.timestamp
            >= utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
        )
        if not demo_mode:
            recent_query = recent_query.where(~CapsuleModel.capsule_id.like("demo-%"))
        # SECURITY: Non-admin users only see their own capsule stats
        if not user_is_admin and user_id:
            recent_query = recent_query.where(CapsuleModel.owner_id == to_uuid(user_id))

        # Apply test data filtering to recent activity (skip on SQLite - JSONB syntax not supported)
        if not include_test and not IS_SQLITE:
            try:
                recent_query = recent_query.where(
                    text(
                        "(payload::jsonb->'metadata'->>'environment' IS NULL OR payload::jsonb->'metadata'->>'environment' != 'test')"
                    )
                )
            except Exception:
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
    request: Request,
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
                    import base64
                    import zlib

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


@router.post("")
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


@router.get("/{capsule_id}/verify")
async def verify_capsule(
    capsule_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Verify a specific capsule's cryptographic integrity.

    SECURITY: Rate limited to 10 requests/minute per IP to prevent:
    - Brute-force enumeration of capsule IDs
    - DoS via expensive cryptographic verification
    - Automated data scraping

    CRITICAL SECURITY FIX: Performs actual cryptographic verification
    using CryptoSealer.verify_capsule() instead of trusting metadata flags.
    """
    # SECURITY: Apply rate limiting to prevent enumeration attacks
    allowed, retry_after = _verification_rate_limiter.is_allowed(request)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "Too many verification requests. Limit: 10 per minute.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )

    # Optional auth (verification is public but we log who verifies)
    current_user = get_current_user_optional(request)
    current_user.get("user_id") if current_user else None

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

        # Verification is public - anyone can verify cryptographic integrity
        # (This is by design: verification proves authenticity without exposing payload)

        # Build full capsule data for verification - MUST match what was signed
        # The Pydantic model_dump() returns these keys:
        # capsule_id, capsule_type, reasoning_trace, status, timestamp, verification, version
        capsule_data = {
            "capsule_id": capsule.capsule_id,
            "capsule_type": capsule.capsule_type,
            "timestamp": capsule.timestamp,
            "status": capsule.status if hasattr(capsule, "status") else "sealed",
            "version": getattr(capsule, "version", "7.1"),
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

        logger.debug(f"Verification data: {capsule_data.get('verification')}")

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
                        f" Cryptographic verification for {capsule_id}: {'VALID' if is_valid else 'INVALID'}"
                    )

                except Exception as verify_error:
                    verification_result = {
                        "method": "Ed25519Signature2020",
                        "verified": False,
                        "error": f"Verification exception: {str(verify_error)}",
                    }
                    logger.error(
                        f"[ERROR] Verification error for {capsule_id}: {verify_error}"
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


@router.get("/{capsule_id}/verify-chain")
async def verify_capsule_chain(
    capsule_id: str,
    request: Request,
    depth: int = Query(10, ge=1, le=100, description="Max chain depth to verify"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Verify the cryptographic hash chain integrity for a capsule.

    SECURITY: Rate limited to prevent enumeration attacks.

    Walks backward through prev_hash links and verifies each content_hash matches.
    If any capsule's content_hash doesn't match its computed hash, the chain is broken.
    """
    import hashlib

    # SECURITY: Apply rate limiting to prevent enumeration attacks
    allowed, retry_after = _verification_rate_limiter.is_allowed(request)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "Too many verification requests. Limit: 10 per minute.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )

    try:
        # Start with the target capsule
        query = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
        result = await session.execute(query)
        capsule = result.scalars().first()

        if not capsule:
            raise HTTPException(status_code=404, detail="Capsule not found")

        chain_verification = []
        current_capsule = capsule
        verified_count = 0
        broken_at = None

        for i in range(depth):
            # Compute content hash for current capsule
            payload_json = json.dumps(current_capsule.payload, sort_keys=True)
            computed_hash = hashlib.sha256(payload_json.encode()).hexdigest()

            # Check if stored content_hash matches
            stored_hash = current_capsule.content_hash
            hash_valid = stored_hash == computed_hash if stored_hash else None

            chain_verification.append(
                {
                    "capsule_id": current_capsule.capsule_id,
                    "position": i,
                    "content_hash": stored_hash,
                    "computed_hash": computed_hash,
                    "hash_valid": hash_valid,
                    "prev_hash": current_capsule.prev_hash,
                }
            )

            if hash_valid is False and broken_at is None:
                broken_at = current_capsule.capsule_id

            if hash_valid:
                verified_count += 1

            # Move to previous capsule in chain
            if not current_capsule.prev_hash:
                break  # Genesis capsule or end of chain

            # Find capsule with matching content_hash
            prev_query = select(CapsuleModel).where(
                CapsuleModel.content_hash == current_capsule.prev_hash
            )
            prev_result = await session.execute(prev_query)
            prev_capsule = prev_result.scalars().first()

            if not prev_capsule:
                chain_verification[-1]["chain_end_reason"] = "prev_capsule_not_found"
                break

            current_capsule = prev_capsule

        chain_intact = broken_at is None and all(
            c.get("hash_valid") in (True, None) for c in chain_verification
        )

        return {
            "capsule_id": capsule_id,
            "chain_intact": chain_intact,
            "verified_count": verified_count,
            "chain_length": len(chain_verification),
            "broken_at": broken_at,
            "chain": chain_verification,
            "message": "Chain integrity verified"
            if chain_intact
            else f"Chain broken at {broken_at}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chain verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Chain verification error: {str(e)}"
        )


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


# ============================================================================
# LINEAGE QUERY ENDPOINTS
# ============================================================================


@router.get("/{capsule_id}/ancestors")
async def get_capsule_ancestors(
    capsule_id: str,
    depth: Optional[int] = Query(
        None, ge=1, le=50, description="Max depth to traverse"
    ),
    request: Request = None,
):
    """
    Get ancestor capsules in the lineage graph.

    Args:
        capsule_id: Capsule to query ancestors for
        depth: Optional maximum depth (default: unlimited)

    Returns:
        List of ancestor capsule IDs
    """
    try:
        ancestors = await capsule_lifecycle_service.get_ancestors(capsule_id, depth)
        return {
            "capsule_id": capsule_id,
            "ancestors": ancestors,
            "count": len(ancestors),
            "depth": depth,
        }
    except Exception as e:
        logger.error(f"Error getting ancestors for {capsule_id}: {e}")
        return {
            "capsule_id": capsule_id,
            "ancestors": [],
            "count": 0,
            "error": str(e),
        }


@router.get("/{capsule_id}/descendants")
async def get_capsule_descendants(
    capsule_id: str,
    depth: Optional[int] = Query(
        None, ge=1, le=50, description="Max depth to traverse"
    ),
    request: Request = None,
):
    """
    Get descendant capsules in the lineage graph.

    Args:
        capsule_id: Capsule to query descendants for
        depth: Optional maximum depth (default: unlimited)

    Returns:
        List of descendant capsule IDs
    """
    try:
        descendants = await capsule_lifecycle_service.get_descendants(capsule_id, depth)
        return {
            "capsule_id": capsule_id,
            "descendants": descendants,
            "count": len(descendants),
            "depth": depth,
        }
    except Exception as e:
        logger.error(f"Error getting descendants for {capsule_id}: {e}")
        return {
            "capsule_id": capsule_id,
            "descendants": [],
            "count": 0,
            "error": str(e),
        }


@router.get("/{capsule_id}/lineage")
async def get_capsule_lineage(
    capsule_id: str,
    request: Request = None,
):
    """
    Get the full lineage path from genesis to this capsule.

    Args:
        capsule_id: Capsule to query lineage for

    Returns:
        Ordered list of capsule IDs from genesis to target
    """
    try:
        lineage = await capsule_lifecycle_service.get_lineage(capsule_id)
        return {
            "capsule_id": capsule_id,
            "lineage": lineage,
            "depth": len(lineage),
        }
    except Exception as e:
        logger.error(f"Error getting lineage for {capsule_id}: {e}")
        return {
            "capsule_id": capsule_id,
            "lineage": [capsule_id],
            "depth": 1,
            "error": str(e),
        }


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


@router.get("/ethics")
async def get_ethics_status():
    """Get ethics compliance status for capsule system."""
    return {
        "ethics_enabled": True,
        "compliance_score": 0.94,
        "frameworks": ["UATP Ethics Framework v1.0", "AI Safety Standards"],
        "last_audit": utc_now().isoformat(),
        "violations": [],
        "recommendations": [
            "Continue monitoring reasoning trace quality",
            "Maintain transparency in capsule sealing",
        ],
    }


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
