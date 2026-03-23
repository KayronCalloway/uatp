"""
Capsules Router Package
=======================

CRUD operations for capsules with database persistence.

Features:
  - Demo mode filtering: demo_mode=false excludes 'demo-*' capsules (default)
  - Pagination support with per_page and page parameters
  - SQLAlchemy ORM queries
  - UATP 7.0 capsule format support

This package splits the original 2000+ line router into focused modules:
  - router_crud.py: Create, read, update operations
  - router_verify.py: Cryptographic verification endpoints
  - router_outcomes.py: Outcome tracking and feedback
  - router_lineage.py: Ancestry and lineage graph queries
  - router_search.py: Full-text search and context retrieval
  - router_admin.py: Admin statistics and system status
  - _shared.py: Common utilities, dependencies, and rate limiters
"""

from fastapi import APIRouter

# Import sub-routers for non-root routes
from .router_admin import router as admin_router

# Import endpoint functions directly for root-level routes
from .router_crud import (
    create_capsule,
    create_capsule_from_conversation,
    create_generic_capsule,
    get_capsule,
    list_capsules,
    store_presigned_capsule,
)
from .router_lineage import router as lineage_router
from .router_outcomes import router as outcomes_router
from .router_search import router as search_router
from .router_verify import router as verify_router

# Create the combined router with the same prefix as the original
router = APIRouter(prefix="/capsules", tags=["Capsules"])

# Include all sub-routers FIRST (more specific routes)
# Note: Order matters for route matching - more specific routes first

# Search routes (/search, /context) - must come before /{capsule_id}
router.include_router(search_router)

# Admin and stats routes (/stats, /admin/stats, /ethics)
router.include_router(admin_router)

# Outcome routes (/outcomes/stats must come before /{capsule_id}/outcome)
router.include_router(outcomes_router)

# Verification routes (/{capsule_id}/verify, /{capsule_id}/verify-chain)
router.include_router(verify_router)

# Lineage routes (/{capsule_id}/ancestors, /descendants, /lineage)
router.include_router(lineage_router)

# Add CRUD routes directly to main router with explicit paths
# This avoids the trailing slash issue with sub-router inclusion

# Root-level routes (must be added AFTER more specific routes)
router.add_api_route("", list_capsules, methods=["GET"], name="list_capsules")
router.add_api_route("", create_capsule, methods=["POST"], name="create_capsule")
router.add_api_route(
    "/store", store_presigned_capsule, methods=["POST"], name="store_presigned_capsule"
)
router.add_api_route(
    "/from-conversation",
    create_capsule_from_conversation,
    methods=["POST"],
    name="create_capsule_from_conversation",
)
router.add_api_route(
    "/generic", create_generic_capsule, methods=["POST"], name="create_generic_capsule"
)
router.add_api_route("/{capsule_id}", get_capsule, methods=["GET"], name="get_capsule")


# Export the combined router as the default
__all__ = ["router"]
