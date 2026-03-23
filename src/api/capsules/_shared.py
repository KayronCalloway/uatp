"""
Capsules Router - Shared Utilities
==================================

Common imports, dependencies, and utilities used across all capsule router modules.
"""

import json
import logging
import os
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth.auth_middleware import (
    get_current_user,
    get_current_user_optional,
    is_admin_user,
    require_admin,
)
from ...core.config import DATABASE_URL
from ...core.database import db
from ...models.capsule import CapsuleModel
from ...services.capsule_lifecycle_service import capsule_lifecycle_service
from ...services.capsule_search_service import get_search_service
from ...services.workflow_chain_service import is_placeholder_signature
from ...utils.timezone_utils import utc_now
from ...utils.uatp_envelope import is_envelope_format, wrap_in_uatp_envelope

# Check if using SQLite (JSONB syntax not supported)
IS_SQLITE = "sqlite" in DATABASE_URL.lower()

# Set up logging
logger = logging.getLogger(__name__)


def to_uuid(user_id: str) -> uuid.UUID:
    """
    Convert a user_id string to a UUID object for database queries.

    The owner_id column in the database is of type UUID(as_uuid=True),
    so we need to convert the string user_id from JWT tokens to UUID.
    """
    try:
        return uuid.UUID(user_id)
    except (ValueError, TypeError):
        logger.warning(f"Invalid user_id format (not a UUID): {user_id[:8]}...")
        raise HTTPException(status_code=400, detail="Invalid user ID format")


def get_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing"""
    return str(uuid.uuid4())[:8]


async def get_db_session():
    """Dependency to get database session"""
    async with db.get_session() as session:
        yield session


class VerificationRateLimiter:
    """
    Per-IP rate limiter for the verification endpoint to prevent brute-force enumeration.

    SECURITY: This limits verification requests to prevent attackers from:
    - Enumerating valid capsule IDs
    - DoS attacks on cryptographic verification (expensive operation)
    - Automated scraping of capsule data

    Limit: 10 requests per minute per IP address
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
        self._last_cleanup = time.time()

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP securely.

        SECURITY: Only trust forwarded headers from explicitly configured proxy IPs.
        Without this check, attackers can spoof X-Forwarded-For to bypass rate limiting.
        """
        direct_ip = request.client.host if request.client else "unknown"

        # SECURITY: Only trust forwarded headers from configured trusted proxies
        # Set TRUSTED_PROXY_IPS env var to comma-separated list of proxy IPs
        trusted_proxies_env = os.getenv("TRUSTED_PROXY_IPS", "")
        trusted_proxies = {
            ip.strip() for ip in trusted_proxies_env.split(",") if ip.strip()
        }

        # Always trust loopback for local development
        trusted_proxies.update({"127.0.0.1", "::1"})

        if direct_ip not in trusted_proxies:
            # Direct connection from untrusted source - use connection IP
            return direct_ip

        # Request is from trusted proxy - check forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return direct_ip

    def is_allowed(self, request: Request) -> tuple[bool, int]:
        """
        Check if request is allowed.

        Returns:
            (allowed: bool, retry_after: int) - retry_after is seconds until next allowed request
        """
        now = time.time()
        client_ip = self._get_client_ip(request)
        key = f"verify:{client_ip}"

        # Periodic cleanup (every 5 minutes)
        if now - self._last_cleanup > 300:
            self._cleanup_expired(now)
            self._last_cleanup = now

        # Initialize or clean expired requests for this key
        cutoff = now - self.window_seconds
        if key not in self.requests:
            self.requests[key] = []
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]

        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            # Calculate retry_after (time until oldest request expires)
            oldest = min(self.requests[key])
            retry_after = int(oldest + self.window_seconds - now) + 1
            return False, max(1, retry_after)

        # Record this request
        self.requests[key].append(now)
        return True, 0

    def _cleanup_expired(self, now: float):
        """Remove expired entries from all keys."""
        cutoff = now - self.window_seconds
        expired_keys = []
        for key in self.requests:
            self.requests[key] = [t for t in self.requests[key] if t > cutoff]
            if not self.requests[key]:
                expired_keys.append(key)
        for key in expired_keys:
            del self.requests[key]


# SECURITY: Singleton rate limiter for verification endpoint
verification_rate_limiter = VerificationRateLimiter(max_requests=10, window_seconds=60)


# Re-export commonly used items for convenience
__all__ = [
    # Functions
    "to_uuid",
    "get_correlation_id",
    "get_db_session",
    # Classes
    "VerificationRateLimiter",
    "verification_rate_limiter",
    # Constants
    "IS_SQLITE",
    "logger",
    # Auth dependencies
    "get_current_user",
    "get_current_user_optional",
    "is_admin_user",
    "require_admin",
    # Models and services
    "CapsuleModel",
    "capsule_lifecycle_service",
    "get_search_service",
    "is_placeholder_signature",
    # Utilities
    "utc_now",
    "is_envelope_format",
    "wrap_in_uatp_envelope",
    # FastAPI
    "Depends",
    "HTTPException",
    "Query",
    "Request",
    "AsyncSession",
    # SQLAlchemy
    "func",
    "select",
    "text",
    # Standard library
    "json",
    "uuid",
    "Dict",
    "Any",
    "Optional",
]
