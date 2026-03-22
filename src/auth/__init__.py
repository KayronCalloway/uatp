"""
Authentication and Authorization Package
=======================================

Production-grade authentication and authorization system for the UATP Capsule Engine
with JWT tokens, role-based access control, and comprehensive security middleware.
"""

from .auth_middleware import (
    check_rate_limit,
    get_current_user,
    get_current_user_optional,
    require_admin,
    require_scopes,
    setup_auth_middleware,
)
from .jwt_handler import JWTHandler, create_access_token, verify_token
from .models import Permission, Role, User, UserRole
from .rbac import RBACManager, check_permission
from .security import SecurityManager, hash_password, verify_password

__all__ = [
    # JWT handling
    "JWTHandler",
    "create_access_token",
    "verify_token",
    # Authentication models
    "User",
    "Role",
    "Permission",
    "UserRole",
    # Middleware
    "get_current_user",
    "get_current_user_optional",
    "require_admin",
    "require_scopes",
    "check_rate_limit",
    "setup_auth_middleware",
    # RBAC
    "RBACManager",
    "check_permission",
    # Security utilities
    "SecurityManager",
    "hash_password",
    "verify_password",
]
