"""
Centralized Redis Connection Manager
====================================

Single source of truth for Redis connections with:
- Connection pooling
- Automatic retry with cooldown
- Graceful fallback in development
"""

import logging
import os
import time
from typing import Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Module-level singleton state
_redis_client: Optional[redis.Redis] = None
_redis_unavailable = False
_redis_retry_after = 0.0
_RETRY_COOLDOWN = 60  # seconds


async def get_redis() -> Optional[redis.Redis]:
    """
    Get Redis client with automatic retry cooldown.

    Returns None if Redis is unavailable (with 60s retry cooldown).
    Logs warning once per cooldown period, not on every call.
    """
    global _redis_client, _redis_unavailable, _redis_retry_after

    # Already connected
    if _redis_client is not None:
        return _redis_client

    # In cooldown period - skip silently
    if _redis_unavailable and time.time() < _redis_retry_after:
        return None

    # Try to connect
    try:
        client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True,
            socket_connect_timeout=2,  # Fast fail
        )
        await client.ping()
        _redis_client = client
        _redis_unavailable = False
        logger.info("Redis connection established")
        return _redis_client
    except Exception as e:
        if not _redis_unavailable:
            logger.warning(f"Redis unavailable: {e}. Using in-memory fallback.")
        _redis_unavailable = True
        _redis_retry_after = time.time() + _RETRY_COOLDOWN
        return None


def is_redis_available() -> bool:
    """Check if Redis is available without blocking."""
    return _redis_client is not None


def get_environment() -> str:
    """Get current environment."""
    return os.getenv("ENVIRONMENT", os.getenv("UATP_ENV", "development")).lower()


def is_production() -> bool:
    """Check if running in production."""
    return get_environment() in ("production", "prod", "staging")
