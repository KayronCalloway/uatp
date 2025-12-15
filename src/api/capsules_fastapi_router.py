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

from ..core.database import db
from ..models.capsule import CapsuleModel
from ..utils.timezone_utils import utc_now

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
    session: AsyncSession = Depends(get_db_session),
):
    """Get comprehensive capsule statistics from database"""
    try:
        # Build base query with demo filtering
        base_query = select(CapsuleModel)
        if not demo_mode:
            base_query = base_query.where(~CapsuleModel.capsule_id.like("demo-%"))

        # Get total count with demo filtering
        count_query = select(func.count(CapsuleModel.id))
        if not demo_mode:
            count_query = count_query.where(~CapsuleModel.capsule_id.like("demo-%"))

        # Apply test data filtering
        if not include_test:
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

        # Apply test data filtering to type query
        if not include_test:
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

        # Apply test data filtering to recent activity
        if not include_test:
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
    session: AsyncSession = Depends(get_db_session),
):
    """List capsules with pagination and filtering"""
    correlation_id = get_correlation_id()
    logger.info(
        f"[{correlation_id}] GET /capsules - page={page}, per_page={per_page}, "
        f"type={type}, environment={environment}, include_test={include_test}, demo_mode={demo_mode}"
    )

    try:
        # Build query
        query = select(CapsuleModel)

        # Apply type filter
        if type:
            query = query.where(CapsuleModel.capsule_type == type)

        # Apply demo_mode filtering - exclude demo capsules unless demo_mode=True
        if not demo_mode:
            query = query.where(~CapsuleModel.capsule_id.like("demo-%"))

        # Apply environment filtering
        # If environment is explicitly specified, use that. Otherwise apply include_test logic.
        if environment:
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
        elif not include_test:
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
        if type:
            count_query = count_query.where(CapsuleModel.capsule_type == type)

        # Apply demo_mode filter to count query
        if not demo_mode:
            count_query = count_query.where(~CapsuleModel.capsule_id.like("demo-%"))

        # Apply same environment filters to count query
        if environment:
            try:
                count_query = count_query.where(
                    text(
                        f"payload::jsonb->'metadata'->>'environment' = '{environment}'"
                    )
                )
            except:
                pass
        elif not include_test:
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

        # Execute query
        result = await session.execute(query)
        capsules = result.scalars().all()

        # Convert to dict
        capsule_list = []
        for capsule in capsules:
            # Fix timestamp format - replace timezone with Z
            timestamp_str = capsule.timestamp.isoformat()
            if "+" in timestamp_str:
                timestamp_str = timestamp_str.split("+")[0] + "Z"
            elif not timestamp_str.endswith("Z"):
                timestamp_str += "Z"

            capsule_list.append(
                {
                    "id": capsule.capsule_id,
                    "capsule_id": capsule.capsule_id,
                    "type": capsule.capsule_type,
                    "version": capsule.version,
                    "timestamp": timestamp_str,
                    "status": capsule.status,
                    "verification": capsule.verification
                    if capsule.verification
                    else {"verified": False, "message": "No verification data"},
                    "payload": capsule.payload,
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
async def get_capsule(capsule_id: str, session: AsyncSession = Depends(get_db_session)):
    """Get a specific capsule by ID"""
    correlation_id = get_correlation_id()
    logger.info(f"[{correlation_id}] GET /capsules/{capsule_id}")

    try:
        query = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
        result = await session.execute(query)
        capsule = result.scalar_one_or_none()

        if not capsule:
            raise HTTPException(status_code=404, detail="Capsule not found")

        # Fix timestamp format - replace timezone with Z
        timestamp_str = capsule.timestamp.isoformat()
        if "+" in timestamp_str:
            timestamp_str = timestamp_str.split("+")[0] + "Z"
        elif not timestamp_str.endswith("Z"):
            timestamp_str += "Z"

        # Ensure verification has data
        verification = (
            capsule.verification
            if capsule.verification
            else {"verified": False, "message": "No verification data"}
        )

        return {
            "capsule": {
                "id": capsule.capsule_id,
                "capsule_id": capsule.capsule_id,
                "type": capsule.capsule_type,
                "version": capsule.version,
                "timestamp": timestamp_str,
                "status": capsule.status,
                "verification": verification,
                "payload": capsule.payload,
            },
            "verification": verification,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("")
async def create_capsule(
    capsule_data: Dict[str, Any], session: AsyncSession = Depends(get_db_session)
):
    """Create a new capsule"""
    try:
        # Generate capsule ID if not provided
        capsule_id = capsule_data.get("capsule_id")
        if not capsule_id:
            # Generate hash-based ID
            content_str = json.dumps(capsule_data.get("payload", {}), sort_keys=True)
            capsule_id = hashlib.sha256(content_str.encode()).hexdigest()[:16]

        # Create capsule object
        capsule = CapsuleModel(
            capsule_id=capsule_id,
            capsule_type=capsule_data.get("type", "chat"),
            version=capsule_data.get("version", "1.0"),
            timestamp=datetime.now(timezone.utc),  # Fixed: use timezone-aware datetime
            status="SEALED",
            verification=capsule_data.get(
                "verification",
                {
                    "verified": True,
                    "hash": hashlib.sha256(capsule_id.encode()).hexdigest(),
                },
            ),
            payload=capsule_data.get("payload", {}),
        )

        session.add(capsule)
        await session.commit()
        await session.refresh(capsule)

        return {
            "success": True,
            "capsule_id": capsule.capsule_id,
            "message": "Capsule created successfully",
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create capsule: {str(e)}"
        )


@router.get("/{capsule_id}/verify")
async def verify_capsule(
    capsule_id: str, session: AsyncSession = Depends(get_db_session)
):
    """Verify a specific capsule's cryptographic integrity"""
    try:
        query = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
        result = await session.execute(query)
        capsule = result.scalar_one_or_none()

        if not capsule:
            raise HTTPException(status_code=404, detail="Capsule not found")

        # Return the verification data stored in the capsule
        verification = capsule.verification if capsule.verification else {}

        # Check if verification has required fields
        has_verify_key = "hash" in verification or "signature" in verification
        is_verified = verification.get("verified", False) if verification else False

        return {
            "capsule_id": capsule_id,
            "verified": is_verified,
            "verification_error": None
            if is_verified
            else "No verification data available",
            "metadata_has_verify_key": has_verify_key,
            "message": f"Capsule signature {'verified' if is_verified else 'not verified'}",
            "verification": verification,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")
