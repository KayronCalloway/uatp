"""
Authentication Middleware
FastAPI authentication middleware with JWT token validation
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt_manager import verify_access_token

logger = logging.getLogger(__name__)

# OAuth2 scheme for Swagger documentation
security = HTTPBearer()


class AuthenticationError(Exception):
    """Custom authentication error"""

    pass


class AuthorizationError(Exception):
    """Custom authorization error"""

    pass


def extract_token_from_request(request: Request) -> Optional[str]:
    """
    Extract JWT token from request.

    Checks in order:
    1. Authorization header (Bearer token) - explicit auth
    2. access_token cookie (HTTP-only) - automatic, more secure

    SECURITY: Cookie auth is preferred for browser clients as it's
    not accessible to JavaScript (XSS protection).
    """
    # Check Authorization header first (explicit takes precedence)
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ")[1]

    # Fall back to HTTP-only cookie
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    return None


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.

    Checks in order:
    1. Authorization header (Bearer token)
    2. HTTP-only cookie (access_token)
    """
    # First try Authorization header
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    else:
        # Fall back to cookie
        token = extract_token_from_request(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Normalize: JWT standard uses 'sub', internal code uses 'user_id'
    payload["user_id"] = payload.get("sub")
    return payload


def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, otherwise None"""
    token = extract_token_from_request(request)
    if not token:
        return None

    payload = verify_access_token(token)
    if payload:
        # Normalize: JWT standard uses 'sub', internal code uses 'user_id'
        payload["user_id"] = payload.get("sub")
    return payload


def require_scopes(required_scopes: List[str]):
    """Decorator to require specific scopes"""

    def scope_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_scopes = current_user.get("scopes", [])

        for scope in required_scopes:
            if scope not in user_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required scope: {scope}",
                )

        return current_user

    return scope_checker


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Require admin permissions"""
    user_scopes = current_user.get("scopes", [])

    if "admin" not in user_scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required"
        )

    return current_user


def require_user_or_admin(
    user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Require user to be the owner or admin"""
    if current_user["user_id"] != user_id and "admin" not in current_user.get(
        "scopes", []
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only access your own resources.",
        )

    return current_user


class RateLimiter:
    """
    SECURITY WARNING: In-memory rate limiter for LOCAL DEVELOPMENT AND TESTING ONLY.

    This rate limiter is NOT suitable for production because:
    - State is lost on restart
    - State is not shared across multiple workers/instances
    - Can be bypassed by restarting the service or hitting different workers

    For production, use the Redis-backed rate limiter in src/middleware/rate_limiting.py
    """

    def __init__(self):
        import os

        env = os.getenv("ENVIRONMENT", os.getenv("UATP_ENV", "development")).lower()
        if env in ("production", "prod", "staging"):
            # SECURITY: Hard fail in production - in-memory rate limiting is not safe
            raise RuntimeError(
                "CRITICAL: In-memory RateLimiter cannot be used in production. "
                "Use Redis-backed rate limiting from src/middleware/rate_limiting.py. "
                "Set RATE_LIMIT_USE_REDIS=true and configure REDIS_HOST."
            )
        self.attempts = {}  # SECURITY: In-memory only - use Redis in production

    def is_rate_limited(
        self, identifier: str, max_attempts: int = 5, window_minutes: int = 15
    ) -> bool:
        """Check if identifier is rate limited"""
        import time

        current_time = time.time()
        window_start = current_time - (window_minutes * 60)

        if identifier not in self.attempts:
            self.attempts[identifier] = []

        # Clean old attempts
        self.attempts[identifier] = [
            attempt_time
            for attempt_time in self.attempts[identifier]
            if attempt_time > window_start
        ]

        return len(self.attempts[identifier]) >= max_attempts

    def record_attempt(self, identifier: str):
        """Record an authentication attempt"""
        import time

        if identifier not in self.attempts:
            self.attempts[identifier] = []

        self.attempts[identifier].append(time.time())


# Global rate limiter instance (lazy initialization)
# SECURITY: This is for local development only. Production uses Redis-backed limiter.
_rate_limiter: Optional[RateLimiter] = None


def _get_rate_limiter() -> RateLimiter:
    """Lazy initialization of rate limiter to prevent import-time crashes in production."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def check_rate_limit(request: Request, identifier: str = None):
    """
    Check rate limit for authentication attempts.

    SECURITY NOTE: This uses the in-memory rate limiter which is only suitable
    for local development. In production, the Redis-backed middleware in
    src/middleware/rate_limiting.py provides distributed rate limiting.
    """
    if identifier is None:
        identifier = request.client.host

    if _get_rate_limiter().is_rate_limited(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again later.",
        )

    _get_rate_limiter().record_attempt(identifier)


# Authentication middleware for FastAPI
async def authentication_middleware(request: Request, call_next):
    """Authentication middleware to validate JWT tokens"""

    # Skip authentication for certain paths
    skip_paths = [
        "/health",
        "/ready",
        "/startup",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/",
    ]

    # NOTE: Capsules API auth bypass removed (2026-02-27)
    # Capsules now require authentication for user-scoped isolation
    # Legacy/system capsules (owner_id = NULL) are admin-only

    if request.url.path in skip_paths:
        return await call_next(request)

    # Extract token
    token = extract_token_from_request(request)

    # For public endpoints, continue without authentication
    if request.url.path.startswith("/api/v1/public/"):
        return await call_next(request)

    # For live capture endpoints, they use API key authentication via @require_api_key decorator
    # So skip Bearer token authentication for these routes
    if request.url.path.startswith("/api/v1/live/"):
        return await call_next(request)

    # For protected endpoints, require authentication
    if request.url.path.startswith("/api/v1/"):
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = verify_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Add user info to request state
        request.state.user = payload

    response = await call_next(request)
    return response


# Security headers middleware
async def security_headers_middleware(request: Request, call_next):
    """
    Add security headers to all responses.

    SECURITY: These headers protect against common web vulnerabilities:
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking
    - Strict-Transport-Security: Forces HTTPS (HSTS)
    - Content-Security-Policy: Prevents XSS and data injection
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Disables unused browser features
    - Cache-Control: Prevents caching of sensitive data
    - X-Permitted-Cross-Domain-Policies: Restricts Adobe Flash/PDF cross-domain access
    """
    import os

    response = await call_next(request)

    # Determine if we're in production for stricter CSP
    env = os.getenv("ENVIRONMENT", os.getenv("UATP_ENV", "development"))
    is_production = env in ("production", "prod", "staging")

    # X-Content-Type-Options: Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # X-Frame-Options: Prevent clickjacking
    # DENY = no framing allowed, SAMEORIGIN = only same origin can frame
    response.headers["X-Frame-Options"] = "DENY"

    # Strict-Transport-Security: Force HTTPS for 1 year
    # includeSubDomains ensures all subdomains use HTTPS
    # preload allows inclusion in browser HSTS preload lists
    if is_production:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
    else:
        # Shorter max-age for development (1 hour)
        response.headers["Strict-Transport-Security"] = "max-age=3600"

    # Content-Security-Policy: Prevent XSS and data injection attacks
    # SECURITY: This is the most important header for XSS protection
    if is_production:
        # Strict CSP for production
        csp_directives = [
            "default-src 'self'",  # Default: only same origin
            "script-src 'self'",  # Scripts: only same origin (no inline/eval)
            "style-src 'self' 'unsafe-inline'",  # Styles: allow inline for frameworks
            "img-src 'self' data: https:",  # Images: self, data URIs, and HTTPS
            "font-src 'self'",  # Fonts: only same origin
            "connect-src 'self'",  # XHR/WebSocket: only same origin
            "frame-ancestors 'none'",  # Prevent framing (stronger than X-Frame-Options)
            "base-uri 'self'",  # Prevent base tag hijacking
            "form-action 'self'",  # Form submissions: only same origin
            "object-src 'none'",  # No plugins (Flash, Java, etc.)
            "upgrade-insecure-requests",  # Upgrade HTTP to HTTPS automatically
        ]
    else:
        # Relaxed CSP for development (allows inline scripts for hot reload)
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Dev tools need eval
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https: http:",
            "font-src 'self' data:",
            "connect-src 'self' ws: wss: http: https:",  # WebSocket for hot reload
            "frame-ancestors 'self'",
            "base-uri 'self'",
            "form-action 'self'",
        ]

    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

    # Referrer-Policy: Control referrer header
    # strict-origin-when-cross-origin: Full URL for same-origin, origin only for cross-origin
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Permissions-Policy: Disable unused browser features
    # This reduces attack surface by disabling APIs the app doesn't need
    response.headers["Permissions-Policy"] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "accelerometer=()"
    )

    # Cache-Control: Prevent caching of sensitive API responses
    # Only apply to API endpoints, not static assets
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, private"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    # X-Permitted-Cross-Domain-Policies: Restrict Adobe cross-domain access
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

    return response


# CORS security middleware
async def cors_security_middleware(request: Request, call_next):
    """
    Enhanced CORS security.

    SECURITY: CORS origins are controlled via CORS_ORIGINS environment variable.
    In production, this MUST be set to your actual frontend domain(s).
    Format: comma-separated list (e.g., "https://app.example.com,https://admin.example.com")
    """
    import os

    response = await call_next(request)

    # SECURITY: Get allowed origins from environment - no hardcoded defaults
    cors_origins_env = os.getenv("CORS_ORIGINS", "")
    allowed_origins = [
        origin.strip() for origin in cors_origins_env.split(",") if origin.strip()
    ]

    # Development fallback: allow localhost if no origins configured and not in production
    env = os.getenv("ENVIRONMENT", os.getenv("UATP_ENV", "development")).lower()
    if not allowed_origins and env not in ("production", "prod", "staging"):
        allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

    origin = request.headers.get("origin")
    if origin and origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response


# Example usage in FastAPI
def setup_auth_middleware(app):
    """Setup authentication middleware for FastAPI app"""
    app.middleware("http")(authentication_middleware)
    app.middleware("http")(security_headers_middleware)
    app.middleware("http")(cors_security_middleware)

    logger.info("Authentication middleware configured")


# Helper functions for common operations
def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from JWT token"""
    payload = verify_access_token(token)
    return payload.get("sub") if payload else None


def is_admin_user(current_user: Dict[str, Any]) -> bool:
    """Check if current user is admin"""
    return "admin" in current_user.get("scopes", [])


def has_scope(current_user: Dict[str, Any], scope: str) -> bool:
    """Check if current user has specific scope"""
    return scope in current_user.get("scopes", [])


# Example usage and testing
if __name__ == "__main__":
    print(" Testing Authentication Middleware...")

    # Test rate limiter
    print("Testing rate limiter...")
    limiter = _get_rate_limiter()
    for i in range(7):
        is_limited = limiter.is_rate_limited(f"test_user_{i}")
        limiter.record_attempt(f"test_user_{i}")
        print(f"Attempt {i + 1}: Rate limited: {is_limited}")

    print("[OK] Authentication Middleware tests completed")
