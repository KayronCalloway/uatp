"""
Authentication Middleware
========================

FastAPI middleware for JWT authentication, role-based access control,
and security enforcement across all API endpoints.
"""

import logging
from typing import List, Optional, Callable, Any
from fastapi import Request, Response, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt

from .jwt_handler import get_jwt_handler, TokenPayload
from .models import User, PermissionScope, UserType
from .rbac import RBACManager

logger = logging.getLogger(__name__)

security = HTTPBearer()


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for FastAPI applications."""

    def __init__(self, app, excluded_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
        ]
        self.jwt_handler = get_jwt_handler()
        self.rbac = RBACManager()

    async def dispatch(self, request: Request, call_next):
        """Process request through authentication middleware."""
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        try:
            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"error": "Missing or invalid authorization header"},
                )

            token = auth_header.split(" ")[1]

            # Verify token
            try:
                payload = self.jwt_handler.verify_token(token)

                # Add user context to request
                request.state.user_id = payload.sub
                request.state.username = payload.username
                request.state.user_type = payload.user_type
                request.state.permissions = payload.permissions
                request.state.session_id = payload.session_id
                request.state.token_payload = payload

                logger.debug(
                    f"Authenticated user {payload.username} for {request.method} {request.url.path}"
                )

            except jwt.InvalidTokenError as e:
                logger.warning(
                    f"Invalid token for {request.method} {request.url.path}: {e}"
                )
                return JSONResponse(
                    status_code=401, content={"error": "Invalid or expired token"}
                )

            # Process request
            response = await call_next(request)

            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"

            return response

        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return JSONResponse(
                status_code=500, content={"error": "Internal authentication error"}
            )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    """FastAPI dependency to get current authenticated user."""
    try:
        jwt_handler = get_jwt_handler()
        payload = jwt_handler.verify_token(credentials.credentials)
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_id(current_user: TokenPayload = Depends(get_current_user)) -> str:
    """Get current user ID from token."""
    return current_user.sub


def get_current_user_permissions(
    current_user: TokenPayload = Depends(get_current_user),
) -> List[str]:
    """Get current user permissions from token."""
    return current_user.permissions


def require_auth(
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Require authentication for endpoint."""
    return current_user


def require_role(required_role: UserType):
    """Require specific user role for endpoint."""

    def role_checker(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        if current_user.user_type != required_role.value:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {required_role.value}",
            )
        return current_user

    return role_checker


def require_permission(required_permission: PermissionScope):
    """Require specific permission for endpoint."""

    def permission_checker(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        if required_permission.value not in current_user.permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required permission: {required_permission.value}",
            )
        return current_user

    return permission_checker


def require_permissions(required_permissions: List[PermissionScope]):
    """Require multiple permissions for endpoint."""

    def permissions_checker(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        user_permissions = set(current_user.permissions)
        required_perms = set(p.value for p in required_permissions)

        if not required_perms.issubset(user_permissions):
            missing_perms = required_perms - user_permissions
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Missing permissions: {', '.join(missing_perms)}",
            )
        return current_user

    return permissions_checker


def require_any_permission(required_permissions: List[PermissionScope]):
    """Require at least one of the specified permissions."""

    def any_permission_checker(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        user_permissions = set(current_user.permissions)
        required_perms = set(p.value for p in required_permissions)

        if not required_perms.intersection(user_permissions):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Requires one of: {', '.join(required_perms)}",
            )
        return current_user

    return any_permission_checker


class OwnershipValidator:
    """Validate resource ownership and access rights."""

    @staticmethod
    def require_agent_ownership(agent_id: str):
        """Require user to own the specified agent."""

        def ownership_checker(
            current_user: TokenPayload = Depends(get_current_user),
        ) -> TokenPayload:
            # Admin users can access any agent
            if current_user.user_type == UserType.ADMIN.value:
                return current_user

            # For now, we'll implement a basic check
            # In production, this would query the database to verify ownership
            # agent = get_agent_by_id(agent_id)
            # if agent.owner_id != current_user.sub:
            #     raise HTTPException(status_code=403, detail="Access denied. Agent not owned by user")

            logger.debug(
                f"Ownership check for agent {agent_id} by user {current_user.username}"
            )
            return current_user

        return ownership_checker

    @staticmethod
    def require_citizenship_access(citizenship_id: str):
        """Require user to have access to the specified citizenship."""

        def citizenship_checker(
            current_user: TokenPayload = Depends(get_current_user),
        ) -> TokenPayload:
            # Admin and compliance officers can access any citizenship
            if current_user.user_type in [
                UserType.ADMIN.value,
                UserType.COMPLIANCE_OFFICER.value,
            ]:
                return current_user

            # Agent owners can access their agents' citizenships
            # In production, verify through database lookup
            logger.debug(
                f"Citizenship access check for {citizenship_id} by user {current_user.username}"
            )
            return current_user

        return citizenship_checker

    @staticmethod
    def require_bond_access(bond_id: str):
        """Require user to have access to the specified bond."""

        def bond_checker(
            current_user: TokenPayload = Depends(get_current_user),
        ) -> TokenPayload:
            # Admin and financial managers can access any bond
            if current_user.user_type in [
                UserType.ADMIN.value,
                UserType.FINANCIAL_MANAGER.value,
            ]:
                return current_user

            # Agent owners can access their bonds
            # In production, verify through database lookup
            logger.debug(
                f"Bond access check for {bond_id} by user {current_user.username}"
            )
            return current_user

        return bond_checker


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}  # In production, use Redis

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting based on user or IP."""
        # Get identifier (user ID if authenticated, otherwise IP)
        identifier = getattr(request.state, "user_id", None) or request.client.host

        # Check rate limit (simplified implementation)
        # In production, use Redis with sliding window
        current_count = self.request_counts.get(identifier, 0)

        if current_count >= self.requests_per_minute:
            return JSONResponse(
                status_code=429, content={"error": "Rate limit exceeded"}
            )

        self.request_counts[identifier] = current_count + 1

        response = await call_next(request)
        return response


class SecurityMiddleware(BaseHTTPMiddleware):
    """Additional security middleware."""

    async def dispatch(self, request: Request, call_next):
        """Apply security headers and checks."""
        # Check for common attack patterns
        user_agent = request.headers.get("User-Agent", "")
        if any(
            pattern in user_agent.lower() for pattern in ["sqlmap", "nikto", "nmap"]
        ):
            logger.warning(f"Suspicious user agent detected: {user_agent}")
            return JSONResponse(status_code=403, content={"error": "Access denied"})

        response = await call_next(request)

        # Add security headers
        response.headers[
            "Strict-Transport-Security"
        ] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


# Convenience decorators for common permission checks
def require_admin_access():
    """Require admin access."""
    return require_role(UserType.ADMIN)


def require_agent_management():
    """Require agent management permissions."""
    return require_any_permission(
        [
            PermissionScope.AGENTS_CREATE,
            PermissionScope.AGENTS_UPDATE,
            PermissionScope.AGENTS_DELETE,
        ]
    )


def require_financial_access():
    """Require financial operations access."""
    return require_any_permission(
        [
            PermissionScope.BONDS_CREATE,
            PermissionScope.BONDS_UPDATE,
            PermissionScope.PAYMENTS_PROCESS,
        ]
    )


def require_compliance_access():
    """Require compliance and risk access."""
    return require_any_permission(
        [
            PermissionScope.COMPLIANCE_READ,
            PermissionScope.COMPLIANCE_REVIEW,
            PermissionScope.RISK_ASSESS,
        ]
    )
