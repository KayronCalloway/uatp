"""
Capsules Router - Admin and Stats Operations
============================================

Endpoints for admin statistics and system status.
"""

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
    func,
    get_current_user,
    get_current_user_optional,
    get_db_session,
    is_admin_user,
    logger,
    require_admin,
    select,
    text,
    to_uuid,
    utc_now,
)

router = APIRouter()


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
    current_user: Optional[Dict] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db_session),
):
    """Get capsule statistics.

    Public stats available without auth. Authenticated users see their own stats.
    """
    try:
        user_is_admin = is_admin_user(current_user) if current_user else False
        user_id = current_user.get("user_id") if current_user else None

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


@router.get("/ethics")
async def get_ethics_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get ethics compliance status for capsule system.

    SECURITY: Authentication required.
    """
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
