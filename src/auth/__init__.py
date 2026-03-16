"""
Authentication and Authorization Package
=======================================

Production-grade authentication and authorization system for the UATP Capsule Engine
with JWT tokens, role-based access control, and comprehensive security middleware.
"""

from .jwt_handler import JWTHandler, create_access_token, verify_token
from .middleware import AuthMiddleware, require_auth, require_permission, require_role
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
    "AuthMiddleware",
    "require_auth",
    "require_role",
    "require_permission",
    # RBAC
    "RBACManager",
    "check_permission",
    # Security utilities
    "SecurityManager",
    "hash_password",
    "verify_password",
]
