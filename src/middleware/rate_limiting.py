"""
Rate Limiting Middleware
========================

Production-grade rate limiting with Redis backend, sliding window algorithm,
and configurable limits per user, IP, and endpoint.
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

import redis.asyncio as redis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Configuration for rate limiting."""

    def __init__(self):
        # Redis configuration
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_password = os.getenv("REDIS_PASSWORD")
        self.redis_db = int(os.getenv("REDIS_DB", "1"))  # Use DB 1 for rate limiting

        # Default rate limits (requests per minute)
        self.default_rate_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        self.burst_limit = int(os.getenv("RATE_LIMIT_BURST", "10"))

        # Rate limit windows (in seconds)
        self.window_size = int(os.getenv("RATE_LIMIT_WINDOW_SIZE", "60"))
        self.cleanup_interval = int(os.getenv("RATE_LIMIT_CLEANUP_INTERVAL", "300"))

        # Endpoint-specific limits (requests per minute)
        self.endpoint_limits = {
            # Auth endpoints - strict limits to prevent brute force
            "/auth/login": 5,
            "/auth/register": 3,
            "/auth/refresh": 10,
            # Legacy endpoints
            "/api/agents/create": 10,
            "/api/citizenship/apply": 5,
            "/api/bonds/create": 20,
            # UATP 7.2 Workflow Chain endpoints
            "/workflows": 30,  # List/create workflows
            "/workflows/stats": 60,  # Stats can be called frequently
            # UATP 7.2 Model Registry endpoints
            "/models": 30,
            "/models/register": 10,  # Model registration is expensive
            "/models/stats": 60,
            "/models/training-sessions": 20,
            # SECURITY: Strict limits on artifact/license creation to prevent abuse
            "/models/artifacts": 20,  # Artifact upload rate
            "/models/license": 10,  # License attachment rate
            # UATP 7.2 Edge Sync endpoints
            "/edge/sync": 20,  # Sync operations
            "/edge/register": 5,  # Device registration
            # UATP 7.2 Attestation endpoints
            "/attestation/challenge": 10,  # Challenge generation
            "/attestation/verify": 10,  # Attestation verification
            # Capsule endpoints
            "/capsules": 60,  # Read operations
            "/capsules/create": 30,  # Create operations
            "/capsules/verify": 30,  # Verification
        }

        # User type limits
        self.user_type_limits = {
            "admin": 1000,
            "agent_owner": 200,
            "financial_manager": 300,
            "compliance_officer": 150,
            "viewer": 100,
            "api_client": 500,
        }


class SlidingWindowRateLimiter:
    """Redis-based sliding window rate limiter."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self._last_cleanup = time.time()

    async def init_redis(self):
        """Initialize Redis connection."""
        if self.redis_client is None:
            try:
                self.redis_client = redis.Redis(
                    host=self.config.redis_host,
                    port=self.config.redis_port,
                    password=self.config.redis_password,
                    db=self.config.redis_db,
                    decode_responses=True,
                )

                # Test connection
                await self.redis_client.ping()
                logger.info("Rate limiter Redis connection established")
            except Exception as e:
                logger.warning(
                    f"Redis not available for rate limiting (allowing all requests): {e}"
                )
                self.redis_client = None  # Mark as unavailable

    async def is_allowed(
        self, key: str, limit: int, window: int = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed using sliding window algorithm.

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        if window is None:
            window = self.config.window_size

        await self.init_redis()

        # SECURITY: Fail closed in production when Redis unavailable
        if self.redis_client is None:
            env = os.getenv("ENVIRONMENT", os.getenv("UATP_ENV", "development")).lower()
            if env in ("production", "prod", "staging"):
                logger.error(
                    "CRITICAL: Redis unavailable for rate limiting in production - "
                    "blocking request to prevent bypass"
                )
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=503, detail="Service temporarily unavailable"
                )
            # Development only - allow with warning
            logger.warning(
                "Redis unavailable for rate limiting (dev mode) - allowing request"
            )
            return True, {
                "limit": limit,
                "remaining": limit,
                "reset": int(time.time() + window),
                "retry_after": None,
                "redis_unavailable": True,
            }

        now = time.time()
        pipeline = self.redis_client.pipeline()

        try:
            # Remove expired entries
            pipeline.zremrangebyscore(key, 0, now - window)

            # Count current requests
            pipeline.zcard(key)

            # Add current request
            pipeline.zadd(key, {str(now): now})

            # Set expiration
            pipeline.expire(key, window + 1)

            results = await pipeline.execute()
            current_count = results[1] + 1  # +1 for the request we just added

            # Check if limit exceeded
            allowed = current_count <= limit

            if not allowed:
                # Remove the request we just added since it's not allowed
                await self.redis_client.zrem(key, str(now))

            # Calculate reset time
            oldest_request = await self.redis_client.zrange(key, 0, 0, withscores=True)
            reset_time = (
                int(oldest_request[0][1] + window)
                if oldest_request
                else int(now + window)
            )

            rate_limit_info = {
                "limit": limit,
                "remaining": max(0, limit - current_count),
                "reset": reset_time,
                "retry_after": int(reset_time - now) if not allowed else 0,
            }

            return allowed, rate_limit_info

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # SECURITY: Fail closed in production when Redis errors occur
            env = os.getenv("ENVIRONMENT", os.getenv("UATP_ENV", "development")).lower()
            if env in ("production", "prod", "staging"):
                logger.error(
                    "CRITICAL: Redis error in production rate limiting - "
                    "blocking request to prevent bypass"
                )
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=503, detail="Service temporarily unavailable"
                )
            # Development only - fail open with warning
            logger.warning("Rate limiting error (dev mode) - allowing request")
            return True, {
                "limit": limit,
                "remaining": limit,
                "reset": int(now + window),
                "retry_after": 0,
            }

    async def cleanup_expired_keys(self):
        """Cleanup expired rate limiting keys."""
        current_time = time.time()

        # Only cleanup every cleanup_interval seconds
        if current_time - self._last_cleanup < self.config.cleanup_interval:
            return

        try:
            await self.init_redis()

            # Get all rate limiting keys
            keys = await self.redis_client.keys("rate_limit:*")

            if keys:
                # Remove expired entries from all keys
                pipeline = self.redis_client.pipeline()
                cutoff_time = current_time - self.config.window_size

                for key in keys:
                    pipeline.zremrangebyscore(key, 0, cutoff_time)

                await pipeline.execute()
                logger.debug(f"Cleaned up {len(keys)} rate limiting keys")

            self._last_cleanup = current_time

        except Exception as e:
            logger.error(f"Rate limiting cleanup error: {e}")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(self, app, config: Optional[RateLimitConfig] = None):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.limiter = SlidingWindowRateLimiter(self.config)

        # Excluded paths that don't require rate limiting
        self.excluded_paths = {
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
        }

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to requests."""
        # Skip rate limiting for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Get rate limiting parameters
        limit, key = await self._get_rate_limit_params(request)

        # Check rate limit
        allowed, rate_info = await self.limiter.is_allowed(key, limit)

        if not allowed:
            # Return rate limit exceeded response
            response = Response(
                content=json.dumps(
                    {
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {limit} per minute",
                        "retry_after": rate_info["retry_after"],
                    }
                ),
                status_code=429,
                media_type="application/json",
            )
        else:
            # Process request
            response = await call_next(request)

        # Add rate limiting headers
        response.headers.update(
            {
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(rate_info["reset"]),
            }
        )

        if not allowed:
            response.headers["Retry-After"] = str(rate_info["retry_after"])

        # Periodic cleanup
        await self.limiter.cleanup_expired_keys()

        return response

    async def _get_rate_limit_params(self, request: Request) -> Tuple[int, str]:
        """Get rate limit and cache key for request."""
        # Get client identifier
        client_id = self._get_client_identifier(request)

        # Get endpoint-specific limit
        endpoint_limit = self._get_endpoint_limit(request.url.path)

        # Get user-specific limit (if authenticated)
        user_limit = self._get_user_limit(request)

        # Use the most restrictive limit
        limit = min(
            filter(None, [endpoint_limit, user_limit, self.config.default_rate_limit])
        )

        # Create cache key
        key_parts = ["rate_limit", client_id, request.url.path, request.method]
        key = ":".join(key_parts)

        return limit, key

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for the client."""
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fallback to IP address
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address securely.

        SECURITY: Only trust forwarded headers from explicitly configured proxy IPs.
        Without this check, attackers can spoof X-Forwarded-For to bypass rate limiting.
        """
        direct_ip = request.client.host if request.client else "unknown"

        # SECURITY: Only trust forwarded headers from configured trusted proxies
        # Set TRUSTED_PROXY_IPS env var to comma-separated list of proxy IPs
        # Example: TRUSTED_PROXY_IPS=10.0.0.1,10.0.0.2,172.16.0.1
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
            # Take the first (client) IP from the chain
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct connection
        return direct_ip

    def _get_endpoint_limit(self, path: str) -> Optional[int]:
        """Get endpoint-specific rate limit."""
        # Check exact path match
        if path in self.config.endpoint_limits:
            return self.config.endpoint_limits[path]

        # Check pattern matches
        for pattern, limit in self.config.endpoint_limits.items():
            if path.startswith(pattern):
                return limit

        return None

    def _get_user_limit(self, request: Request) -> Optional[int]:
        """Get user type-specific rate limit."""
        user_type = getattr(request.state, "user_type", None)
        if user_type and user_type in self.config.user_type_limits:
            return self.config.user_type_limits[user_type]

        return None


class InMemoryRateLimiter:
    """In-memory rate limiter for development/testing."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests: Dict[str, list] = {}
        self._last_cleanup = time.time()

    async def is_allowed(
        self, key: str, limit: int, window: int = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed."""
        if window is None:
            window = self.config.window_size

        now = time.time()
        cutoff_time = now - window

        # Initialize key if not exists
        if key not in self.requests:
            self.requests[key] = []

        # Remove expired requests
        self.requests[key] = [
            req_time for req_time in self.requests[key] if req_time > cutoff_time
        ]

        # Check if limit exceeded
        current_count = len(self.requests[key])
        allowed = current_count < limit

        if allowed:
            self.requests[key].append(now)
            current_count += 1

        # Calculate reset time
        oldest_request = min(self.requests[key]) if self.requests[key] else now
        reset_time = int(oldest_request + window)

        rate_limit_info = {
            "limit": limit,
            "remaining": max(0, limit - current_count),
            "reset": reset_time,
            "retry_after": int(reset_time - now) if not allowed else 0,
        }

        # Periodic cleanup
        if now - self._last_cleanup > 60:  # Cleanup every minute
            self._cleanup()
            self._last_cleanup = now

        return allowed, rate_limit_info

    def _cleanup(self):
        """Remove old entries."""
        now = time.time()
        cutoff_time = now - self.config.window_size

        for key in list(self.requests.keys()):
            self.requests[key] = [
                req_time for req_time in self.requests[key] if req_time > cutoff_time
            ]
            if not self.requests[key]:
                del self.requests[key]


def create_rate_limiter(
    use_redis: bool = True, config: Optional[RateLimitConfig] = None
) -> SlidingWindowRateLimiter:
    """Factory function to create appropriate rate limiter."""
    config = config or RateLimitConfig()

    if use_redis:
        return SlidingWindowRateLimiter(config)
    else:
        # Return in-memory limiter wrapped to match interface
        in_memory = InMemoryRateLimiter(config)

        class InMemoryWrapper:
            def __init__(self, limiter):
                self.limiter = limiter
                self.config = config

            async def init_redis(self):
                pass

            async def is_allowed(self, key: str, limit: int, window: int = None):
                return await self.limiter.is_allowed(key, limit, window)

            async def cleanup_expired_keys(self):
                pass

        return InMemoryWrapper(in_memory)


# Additional rate limiting utilities


class APIKeyRateLimiter:
    """Specialized rate limiter for API keys."""

    def __init__(self, base_limiter: SlidingWindowRateLimiter):
        self.base_limiter = base_limiter

    async def check_api_key_limit(
        self, api_key_id: str, limit: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit for API key."""
        key = f"api_key:{api_key_id}"
        return await self.base_limiter.is_allowed(key, limit)


class DynamicRateLimiter:
    """Rate limiter with dynamic limits based on system load."""

    def __init__(self, base_limiter: SlidingWindowRateLimiter):
        self.base_limiter = base_limiter
        self.load_factor = 1.0

    def update_load_factor(self, cpu_usage: float, memory_usage: float):
        """Update rate limiting based on system load."""
        # Reduce limits when system is under high load
        if cpu_usage > 80 or memory_usage > 80:
            self.load_factor = 0.5
        elif cpu_usage > 60 or memory_usage > 60:
            self.load_factor = 0.75
        else:
            self.load_factor = 1.0

    async def is_allowed(
        self, key: str, limit: int, window: int = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit with dynamic adjustment."""
        adjusted_limit = int(limit * self.load_factor)
        return await self.base_limiter.is_allowed(key, adjusted_limit, window)
