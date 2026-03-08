"""
CSRF Protection
Cross-Site Request Forgery protection for FastAPI applications
"""

import hashlib
import hmac
import logging
import secrets
import time
from typing import Optional

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


class CSRFProtection:
    """CSRF protection implementation"""

    def __init__(self, secret_key: str = None, token_expiry: int = 3600):
        # Load from environment variable if not provided
        import os

        self.secret_key = (
            secret_key or os.getenv("CSRF_SECRET_KEY") or secrets.token_urlsafe(32)
        )
        self.token_expiry = token_expiry  # seconds
        self.token_store = {}  # In production, use Redis

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

        # Store token with expiry
        self.token_store[token] = {
            "session_id": session_id,
            "created_at": timestamp,
            "expires_at": timestamp + self.token_expiry,
        }

        # Clean up expired tokens
        self._cleanup_expired_tokens()

        return token

    def validate_token(self, token: str, session_id: str = None) -> bool:
        """Validate CSRF token"""

        try:
            if not token:
                return False

            # Check if token exists in store
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
        """Remove token from store"""
        self.token_store.pop(token, None)

    def _cleanup_expired_tokens(self):
        """Clean up expired tokens"""
        current_time = int(time.time())
        expired_tokens = [
            token
            for token, info in self.token_store.items()
            if current_time > info["expires_at"]
        ]

        for token in expired_tokens:
            self._remove_token(token)

        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired CSRF tokens")

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

        # Check query parameters
        token = request.query_params.get("csrf_token")
        if token:
            return token

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
        "/api/v1/webhooks/",  # Webhooks typically don't use CSRF
        "/api/v1/live/",  # Live capture API uses API key authentication
        "/live/",  # Live capture API uses API key authentication (actual path)
        "/capsules",  # Capsule API uses API key authentication
        "/chain",  # Chain sealing API uses API key authentication
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
