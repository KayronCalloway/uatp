"""
Rate Limiting for Insurance API
================================

Token bucket algorithm for rate limiting API endpoints.
Prevents abuse while allowing reasonable burst traffic.
"""

import functools
import time
from collections import defaultdict
from typing import Dict, Callable
import logging

from quart import request, jsonify

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket rate limiter implementation"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum number of tokens (requests) in the bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.

        Returns:
            bool: True if tokens were available and consumed, False otherwise
        """
        # Refill tokens based on time passed
        now = time.time()
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + (time_passed * self.refill_rate))
        self.last_refill = now

        # Try to consume
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_wait_time(self) -> float:
        """Get seconds until next token is available"""
        if self.tokens >= 1:
            return 0.0
        tokens_needed = 1 - self.tokens
        return tokens_needed / self.refill_rate


class RateLimiter:
    """Rate limiter with per-user and per-IP tracking"""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 100,
    ):
        """
        Args:
            requests_per_minute: Sustained rate limit
            burst_size: Maximum burst capacity
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.refill_rate = requests_per_minute / 60.0  # tokens per second

        # Separate buckets for users and IPs
        self.user_buckets: Dict[str, TokenBucket] = {}
        self.ip_buckets: Dict[str, TokenBucket] = {}

        # Cleanup old buckets periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def _get_bucket(self, key: str, buckets: Dict[str, TokenBucket]) -> TokenBucket:
        """Get or create a token bucket for a key"""
        if key not in buckets:
            buckets[key] = TokenBucket(self.burst_size, self.refill_rate)
        return buckets[key]

    def _cleanup_old_buckets(self):
        """Remove inactive buckets to prevent memory leak"""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return

        # Remove buckets that haven't been used recently
        max_age = 600  # 10 minutes
        for buckets in [self.user_buckets, self.ip_buckets]:
            keys_to_remove = [
                key
                for key, bucket in buckets.items()
                if now - bucket.last_refill > max_age
            ]
            for key in keys_to_remove:
                del buckets[key]

        self.last_cleanup = now
        logger.debug(f"Cleaned up {len(keys_to_remove)} old rate limit buckets")

    async def check_rate_limit(
        self, user_id: str = None, ip: str = None
    ) -> tuple[bool, dict]:
        """
        Check if request should be allowed.

        Args:
            user_id: Authenticated user ID (optional)
            ip: Client IP address

        Returns:
            tuple: (allowed: bool, info: dict)
        """
        self._cleanup_old_buckets()

        # Check user-based rate limit (stricter)
        if user_id:
            bucket = self._get_bucket(user_id, self.user_buckets)
            if not bucket.consume():
                wait_time = bucket.get_wait_time()
                return False, {
                    "limit_type": "user",
                    "user_id": user_id,
                    "retry_after": wait_time,
                    "requests_per_minute": self.requests_per_minute,
                }

        # Check IP-based rate limit (more lenient)
        if ip:
            ip_bucket = self._get_bucket(ip, self.ip_buckets)
            # IP limit is 2x more lenient
            ip_bucket_copy = TokenBucket(self.burst_size * 2, self.refill_rate * 2)
            ip_bucket_copy.tokens = ip_bucket.tokens
            ip_bucket_copy.last_refill = ip_bucket.last_refill

            if not ip_bucket.consume():
                wait_time = ip_bucket.get_wait_time()
                return False, {
                    "limit_type": "ip",
                    "ip": ip,
                    "retry_after": wait_time,
                    "requests_per_minute": self.requests_per_minute * 2,
                }

        return True, {}


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            requests_per_minute=60,  # 60 requests per minute per user
            burst_size=100,  # Allow bursts up to 100
        )
    return _rate_limiter


def rate_limit(
    requests_per_minute: int = None,
    burst_size: int = None,
):
    """
    Decorator to apply rate limiting to Quart routes.

    Usage:
        @insurance_bp.route("/policies", methods=["POST"])
        @require_auth
        @rate_limit(requests_per_minute=10, burst_size=20)
        async def create_policy():
            ...

    Args:
        requests_per_minute: Override default rate limit
        burst_size: Override default burst size
    """

    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        async def decorated_function(*args, **kwargs):
            # Get rate limiter (with custom settings if provided)
            if requests_per_minute is not None or burst_size is not None:
                limiter = RateLimiter(
                    requests_per_minute=requests_per_minute or 60,
                    burst_size=burst_size or 100,
                )
            else:
                limiter = get_rate_limiter()

            # Extract user ID from request (if authenticated)
            user_id = None
            if hasattr(request, "user"):
                user_id = request.user.get("user_id")

            # Get client IP
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            if "," in ip:
                ip = ip.split(",")[0].strip()

            # Check rate limit
            allowed, info = await limiter.check_rate_limit(user_id=user_id, ip=ip)

            if not allowed:
                logger.warning(
                    f"Rate limit exceeded: {info['limit_type']} "
                    f"({user_id or ip}), retry after {info['retry_after']:.1f}s"
                )
                return (
                    jsonify(
                        {
                            "error": "Rate limit exceeded",
                            "message": f"Too many requests. Please wait {info['retry_after']:.1f} seconds.",
                            "retry_after": info["retry_after"],
                            "limit": info["requests_per_minute"],
                        }
                    ),
                    429,
                )

            # Allow request
            return await f(*args, **kwargs)

        return decorated_function

    return decorator
