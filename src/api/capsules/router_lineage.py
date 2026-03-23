"""
Capsules Router - Lineage Operations
====================================

Endpoints for querying capsule ancestry and lineage graphs.
"""

from fastapi import APIRouter

from ._shared import (
    Any,
    AsyncSession,
    CapsuleModel,
    Depends,
    Dict,
    HTTPException,
    Optional,
    Query,
    capsule_lifecycle_service,
    get_current_user,
    get_db_session,
    is_admin_user,
    logger,
    select,
)

router = APIRouter()


@router.get("/{capsule_id}/ancestors")
async def get_capsule_ancestors(
    capsule_id: str,
    depth: Optional[int] = Query(
        None, ge=1, le=50, description="Max depth to traverse"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get ancestor capsules in the lineage graph.

    SECURITY: Authentication required. Users can only query lineage for their own capsules.

    Args:
        capsule_id: Capsule to query ancestors for
        depth: Optional maximum depth (default: unlimited)

    Returns:
        List of ancestor capsule IDs
    """
    user_is_admin = is_admin_user(current_user)
    user_id = current_user.get("user_id")

    try:
        # Verify ownership of the capsule being queried
        query = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
        result = await session.execute(query)
        capsule = result.scalars().first()

        if not capsule:
            raise HTTPException(status_code=404, detail="Capsule not found")

        if not user_is_admin:
            if capsule.owner_id is None:
                raise HTTPException(
                    status_code=403, detail="Access denied: legacy capsule (admin-only)"
                )
            if str(capsule.owner_id) != user_id:
                raise HTTPException(status_code=403, detail="Access denied")

        ancestors = await capsule_lifecycle_service.get_ancestors(capsule_id, depth)
        return {
            "capsule_id": capsule_id,
            "ancestors": ancestors,
            "count": len(ancestors),
            "depth": depth,
        }
    except HTTPException:
        raise
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
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get descendant capsules in the lineage graph.

    SECURITY: Authentication required. Users can only query lineage for their own capsules.

    Args:
        capsule_id: Capsule to query descendants for
        depth: Optional maximum depth (default: unlimited)

    Returns:
        List of descendant capsule IDs
    """
    user_is_admin = is_admin_user(current_user)
    user_id = current_user.get("user_id")

    try:
        # Verify ownership of the capsule being queried
        query = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
        result = await session.execute(query)
        capsule = result.scalars().first()

        if not capsule:
            raise HTTPException(status_code=404, detail="Capsule not found")

        if not user_is_admin:
            if capsule.owner_id is None:
                raise HTTPException(
                    status_code=403, detail="Access denied: legacy capsule (admin-only)"
                )
            if str(capsule.owner_id) != user_id:
                raise HTTPException(status_code=403, detail="Access denied")

        descendants = await capsule_lifecycle_service.get_descendants(capsule_id, depth)
        return {
            "capsule_id": capsule_id,
            "descendants": descendants,
            "count": len(descendants),
            "depth": depth,
        }
    except HTTPException:
        raise
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
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get the full lineage path from genesis to this capsule.

    SECURITY: Authentication required. Users can only query lineage for their own capsules.

    Args:
        capsule_id: Capsule to query lineage for

    Returns:
        Ordered list of capsule IDs from genesis to target
    """
    user_is_admin = is_admin_user(current_user)
    user_id = current_user.get("user_id")

    try:
        # Verify ownership of the capsule being queried
        query = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
        result = await session.execute(query)
        capsule = result.scalars().first()

        if not capsule:
            raise HTTPException(status_code=404, detail="Capsule not found")

        if not user_is_admin:
            if capsule.owner_id is None:
                raise HTTPException(
                    status_code=403, detail="Access denied: legacy capsule (admin-only)"
                )
            if str(capsule.owner_id) != user_id:
                raise HTTPException(status_code=403, detail="Access denied")

        lineage = await capsule_lifecycle_service.get_lineage(capsule_id)
        return {
            "capsule_id": capsule_id,
            "lineage": lineage,
            "depth": len(lineage),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lineage for {capsule_id}: {e}")
        return {
            "capsule_id": capsule_id,
            "lineage": [capsule_id],
            "depth": 1,
            "error": str(e),
        }
