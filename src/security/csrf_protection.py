"""
CSRF Protection
Cross-Site Request Forgery protection for FastAPI applications
"""

import hashlib
import hmac
import logging
import os
import secrets
import time
from typing import Optional

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


class CSRFTokenStore:
    """
    Redis-backed CSRF token store with in-memory fallback for development.

    SECURITY: In production, Redis is REQUIRED. This prevents:
    - Token bypass by restarting the service
    - State loss in multi-worker/multi-instance deployments
    - Session fixation attacks

    In development, falls back to in-memory storage with a warning.
    """

    def __init__(self):
        self._redis_client = None
        self._in_memory_fallback = {}
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection with production enforcement."""
        env = os.getenv("ENVIRONMENT", os.getenv("UATP_ENV", "development")).lower()

        try:
            import redis

            self._redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                password=os.getenv("REDIS_PASSWORD"),
                db=int(os.getenv("REDIS_CSRF_DB", "3")),
                decode_responses=True,
            )
            # Test connection
            self._redis_client.ping()
            logger.info("CSRF token store: Redis connection established")
        except Exception as e:
            # SECURITY: Hard fail in production - Redis is required
            if env in ("production", "prod", "staging"):
                raise RuntimeError(
                    f"CRITICAL: Redis required for CSRF in production but unavailable: {e}. "
                    f"Set REDIS_HOST and ensure Redis is running."
                )
            # Development only - allow in-memory fallback with warning
            logger.warning(
                f"CSRF token store: Redis unavailable ({e}), "
                f"using in-memory fallback (development only)"
            )
            self._redis_client = None

    def store(self, token: str, token_info: dict, ttl: int = 3600):
        """Store a CSRF token with expiry."""
        import json

        if self._redis_client:
            self._redis_client.setex(
                f"csrf:{token}",
                ttl,
                json.dumps(token_info),
            )
        else:
            self._in_memory_fallback[token] = token_info

    def get(self, token: str) -> Optional[dict]:
        """Retrieve a CSRF token's info."""
        import json

        if self._redis_client:
            data = self._redis_client.get(f"csrf:{token}")
            if data:
                return json.loads(data)
            return None
        else:
            return self._in_memory_fallback.get(token)

    def delete(self, token: str):
        """Delete a CSRF token."""
        if self._redis_client:
            self._redis_client.delete(f"csrf:{token}")
        else:
            self._in_memory_fallback.pop(token, None)

    def cleanup_expired(self):
        """Clean up expired tokens (only needed for in-memory store)."""
        if self._redis_client:
            # Redis handles expiry automatically via TTL
            return

        current_time = int(time.time())
        expired_tokens = [
            token
            for token, info in self._in_memory_fallback.items()
            if current_time > info.get("expires_at", 0)
        ]

        for token in expired_tokens:
            self._in_memory_fallback.pop(token, None)

        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired CSRF tokens")

    # Dict-like interface for backward compatibility with tests
    def __getitem__(self, token: str) -> dict:
        """Allow dict-style access: store[token]"""
        result = self.get(token)
        if result is None:
            raise KeyError(token)
        return result

    def __setitem__(self, token: str, token_info: dict):
        """Allow dict-style assignment: store[token] = info"""
        self.store(token, token_info)

    def __contains__(self, token: str) -> bool:
        """Allow 'in' operator: token in store"""
        return self.get(token) is not None

    def __len__(self) -> int:
        """Allow len(store)"""
        if self._redis_client:
            # Count csrf:* keys in Redis
            keys = self._redis_client.keys("csrf:*")
            return len(keys) if keys else 0
        else:
            return len(self._in_memory_fallback)


class CSRFProtection:
    """CSRF protection implementation with Redis-backed token storage."""

    def __init__(self, secret_key: str = None, token_expiry: int = 3600):
        self.secret_key = (
            secret_key or os.getenv("CSRF_SECRET_KEY") or secrets.token_urlsafe(32)
        )
        self.token_expiry = token_expiry  # seconds
        # SECURITY: Use Redis-backed store (fails hard in production if unavailable)
        self.token_store = CSRFTokenStore()

        if not secret_key and not os.getenv("CSRF_SECRET_KEY"):
            logger.warning(
                "Using generated CSRF secret key - set CSRF_SECRET_KEY environment variable in production"
            )

    def generate_token(self, session_id: str = None) -> str:
        """Generate CSRF token"""

        # Create unique session ID if not provided
        if not session_id:
            session_id = secrets.token_urlsafe(16)

        # Create timestamp
        timestamp = int(time.time())

        # Create token data
        token_data = f"{session_id}:{timestamp}"

        # Create HMAC signature
        signature = hmac.new(
            self.secret_key.encode(), token_data.encode(), hashlib.sha256
        ).hexdigest()

        # Combine data and signature
        token = f"{token_data}:{signature}"

        # Store token with expiry (Redis-backed in production)
        token_info = {
            "session_id": session_id,
            "created_at": timestamp,
            "expires_at": timestamp + self.token_expiry,
        }
        self.token_store.store(token, token_info, ttl=self.token_expiry)

        # Clean up expired tokens (only affects in-memory fallback)
        self._cleanup_expired_tokens()

        return token

    def validate_token(self, token: str, session_id: str = None) -> bool:
        """Validate CSRF token"""

        try:
            if not token:
                return False

            # Check if token exists in store (Redis-backed in production)
            token_info = self.token_store.get(token)
            if not token_info:
                logger.warning("CSRF token not found in store")
                return False

            # Check expiry
            current_time = int(time.time())
            if current_time > token_info["expires_at"]:
                logger.warning("CSRF token expired")
                self._remove_token(token)
                return False

            # Parse token
            parts = token.split(":")
            if len(parts) != 3:
                logger.warning("Invalid CSRF token format")
                return False

            stored_session_id, timestamp_str, signature = parts

            # Verify session ID if provided
            if session_id and stored_session_id != session_id:
                logger.warning("CSRF token session ID mismatch")
                return False

            # Verify signature
            token_data = f"{stored_session_id}:{timestamp_str}"
            expected_signature = hmac.new(
                self.secret_key.encode(), token_data.encode(), hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("CSRF token signature invalid")
                return False

            return True

        except Exception as e:
            logger.error(f"CSRF token validation error: {e}")
            return False

    def _remove_token(self, token: str):
        """Remove token from store (Redis-backed in production)"""
        self.token_store.delete(token)

    def _cleanup_expired_tokens(self):
        """Clean up expired tokens (delegated to store)"""
        self.token_store.cleanup_expired()

    def get_token_from_request(self, request: Request) -> Optional[str]:
        """Extract CSRF token from request"""

        # Check header first
        token = request.headers.get("X-CSRF-Token")
        if token:
            return token

        # Check form data
        if hasattr(request, "form"):
            try:
                form_data = request.form()
                token = form_data.get("csrf_token")
                if token:
                    return token
            except Exception:
                pass

        return None

    def require_csrf_token(self, request: Request, session_id: str = None):
        """Require valid CSRF token for request"""

        # Skip CSRF for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return

        # Get token from request
        token = self.get_token_from_request(request)

        if not token:
            logger.warning(
                f"Missing CSRF token for {request.method} {request.url.path}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token required"
            )

        # Validate token
        if not self.validate_token(token, session_id):
            logger.warning(
                f"Invalid CSRF token for {request.method} {request.url.path}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token"
            )

        logger.debug(f"CSRF token validated for {request.method} {request.url.path}")


# Global CSRF protection instance
csrf_protection = CSRFProtection()


# FastAPI middleware
async def csrf_middleware(request: Request, call_next):
    """CSRF protection middleware"""

    # Skip CSRF for certain paths
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
        "/api/v1/auth/refresh",  # Protected by refresh token cookie, access token may be expired
        "/api/v1/webhooks/",  # Webhooks typically don't use CSRF
        "/api/v1/live/",  # Live capture API uses API key authentication
        "/live/",  # Live capture API uses API key authentication (actual path)
        "/capsules",  # Uses Bearer Auth (no cookies)
        "/chain",  # Uses Bearer Auth (no cookies)
    ]

    # Check if path should be skipped
    path = request.url.path
    should_skip = any(path.startswith(skip_path) for skip_path in skip_paths)

    if not should_skip and request.method not in ["GET", "HEAD", "OPTIONS"]:
        try:
            # Extract session ID from JWT token or session
            session_id = None
            if hasattr(request.state, "user"):
                session_id = request.state.user.get("user_id")

            # Require CSRF token
            csrf_protection.require_csrf_token(request, session_id)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"CSRF middleware error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="CSRF validation error",
            ) from e

    response = await call_next(request)
    return response


# Helper functions for FastAPI dependencies
def get_csrf_token(session_id: str = None) -> str:
    """Generate CSRF token"""
    return csrf_protection.generate_token(session_id)


def validate_csrf_token(token: str, session_id: str = None) -> bool:
    """Validate CSRF token"""
    return csrf_protection.validate_token(token, session_id)


def require_csrf(request: Request):
    """FastAPI dependency to require CSRF token"""
    csrf_protection.require_csrf_token(request)


# Double Submit Cookie Pattern
class DoubleSubmitCSRF:
    """Double submit cookie CSRF protection"""

    def __init__(
        self,
        cookie_name: str = "csrf_token",
        cookie_secure: bool = True,
        cookie_httponly: bool = True,
    ):
        self.cookie_name = cookie_name
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly

    def generate_token(self) -> str:
        """Generate random token"""
        return secrets.token_urlsafe(32)

    def set_csrf_cookie(self, response, token: str):
        """Set CSRF cookie in response"""
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite="strict",
            max_age=3600,  # 1 hour
        )

    def validate_double_submit(self, request: Request) -> bool:
        """Validate double submit pattern"""

        # Get token from cookie
        cookie_token = request.cookies.get(self.cookie_name)
        if not cookie_token:
            return False

        # Get token from header or form
        header_token = request.headers.get("X-CSRF-Token")
        if not header_token:
            # Try form data
            try:
                if hasattr(request, "form"):
                    form_data = request.form()
                    header_token = form_data.get("csrf_token")
            except Exception:
                pass

        if not header_token:
            return False

        # Compare tokens
        return hmac.compare_digest(cookie_token, header_token)


# SameSite cookie protection
def set_secure_cookie(
    response, name: str, value: str, max_age: int = 3600, httponly: bool = True
):
    """Set secure cookie with proper attributes"""
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age,
        httponly=httponly,
        secure=True,  # HTTPS only
        samesite="strict",  # CSRF protection
    )


# Origin checking
def validate_origin(request: Request, allowed_origins: list) -> bool:
    """Validate request origin"""

    origin = request.headers.get("Origin")
    referer = request.headers.get("Referer")

    # Check Origin header
    if origin:
        return origin in allowed_origins

    # Fallback to Referer header
    if referer:
        from urllib.parse import urlparse

        referer_origin = f"{urlparse(referer).scheme}://{urlparse(referer).netloc}"
        return referer_origin in allowed_origins

    return False


# Custom CSRF token for API endpoints
class APICSRFProtection:
    """CSRF protection for API endpoints"""

    def __init__(self, header_name: str = "X-API-CSRF-Token"):
        self.header_name = header_name
        self.tokens = {}  # In production, use Redis

    def generate_api_token(self, api_key: str) -> str:
        """Generate CSRF token for API key"""

        token = secrets.token_urlsafe(32)
        timestamp = int(time.time())

        self.tokens[token] = {
            "api_key": api_key,
            "created_at": timestamp,
            "expires_at": timestamp + 3600,  # 1 hour
        }

        return token

    def validate_api_token(self, token: str, api_key: str) -> bool:
        """Validate API CSRF token"""

        token_info = self.tokens.get(token)
        if not token_info:
            return False

        # Check expiry
        if int(time.time()) > token_info["expires_at"]:
            self.tokens.pop(token, None)
            return False

        # Check API key
        return token_info["api_key"] == api_key


# Example usage and testing
if __name__ == "__main__":
    print(" Testing CSRF Protection...")

    # Test token generation and validation
    token = csrf_protection.generate_token("test_session")
    print(f"Generated token: {token[:20]}...")

    # Test validation
    is_valid = csrf_protection.validate_token(token, "test_session")
    print(f"Token validation: {is_valid}")

    # Test invalid token
    is_valid = csrf_protection.validate_token("invalid_token", "test_session")
    print(f"Invalid token validation: {is_valid}")

    # Test double submit
    double_submit = DoubleSubmitCSRF()
    ds_token = double_submit.generate_token()
    print(f"Double submit token: {ds_token[:20]}...")

    print("[OK] CSRF Protection tests completed")
