"""
Capsules Router - Search Operations
===================================

Endpoints for full-text search and verified context retrieval.
"""

from fastapi import APIRouter

from ._shared import (
    AsyncSession,
    Depends,
    Dict,
    HTTPException,
    Optional,
    Query,
    Request,
    get_current_user,
    get_db_session,
    get_search_service,
    is_admin_user,
    logger,
)

router = APIRouter()


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
