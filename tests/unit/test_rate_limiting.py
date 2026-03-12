"""
Unit tests for Rate Limiting.
"""

import time

import pytest

from src.api.rate_limiting import RateLimiter, TokenBucket, get_rate_limiter


class TestTokenBucket:
    """Tests for TokenBucket class."""

    def test_initial_tokens(self):
        """Test bucket starts with full capacity."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.tokens == 10

    def test_consume_success(self):
        """Test consuming tokens successfully."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)

        result = bucket.consume(1)
        assert result is True
        assert bucket.tokens == 9

    def test_consume_multiple(self):
        """Test consuming multiple tokens."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)

        result = bucket.consume(5)
        assert result is True
        assert bucket.tokens == 5

    def test_consume_fails_when_empty(self):
        """Test consumption fails when insufficient tokens."""
        bucket = TokenBucket(capacity=2, refill_rate=1.0)

        # Consume all tokens
        bucket.consume(2)

        # Should fail
        result = bucket.consume(1)
        assert result is False

    def test_tokens_refill(self):
        """Test tokens refill over time."""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10 tokens/sec

        # Consume all tokens
        bucket.consume(10)
        assert bucket.tokens == 0

        # Wait a bit
        time.sleep(0.2)  # 0.2 seconds = ~2 tokens

        # Try to consume - should refill first
        result = bucket.consume(1)
        assert result is True

    def test_tokens_dont_exceed_capacity(self):
        """Test tokens don't refill beyond capacity."""
        bucket = TokenBucket(capacity=10, refill_rate=100.0)

        # Wait for refill (would be 10+ tokens if uncapped)
        time.sleep(0.2)

        # Consume to trigger refill calculation
        bucket.consume(0)

        assert bucket.tokens <= 10

    def test_get_wait_time_when_available(self):
        """Test wait time is 0 when tokens available."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)

        wait = bucket.get_wait_time()
        assert wait == 0.0

    def test_get_wait_time_when_empty(self):
        """Test wait time calculation when empty."""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10/sec

        # Consume all tokens
        bucket.consume(10)

        wait = bucket.get_wait_time()
        # Need ~1 token at 10/sec = 0.1 seconds
        assert wait > 0
        assert wait <= 0.2


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_init_defaults(self):
        """Test default initialization."""
        limiter = RateLimiter()

        assert limiter.requests_per_minute == 60
        assert limiter.burst_size == 100

    def test_init_custom(self):
        """Test custom initialization."""
        limiter = RateLimiter(requests_per_minute=30, burst_size=50)

        assert limiter.requests_per_minute == 30
        assert limiter.burst_size == 50

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self):
        """Test rate limit allows request."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=100)

        allowed, info = await limiter.check_rate_limit(user_id="user_123")

        assert allowed is True
        assert info == {}

    @pytest.mark.asyncio
    async def test_check_rate_limit_by_user(self):
        """Test rate limiting by user."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)

        # Consume all tokens
        for _ in range(5):
            await limiter.check_rate_limit(user_id="user_123")

        # Next request should be blocked
        allowed, info = await limiter.check_rate_limit(user_id="user_123")

        assert allowed is False
        assert info["limit_type"] == "user"
        assert info["user_id"] == "user_123"
        assert "retry_after" in info

    @pytest.mark.asyncio
    async def test_check_rate_limit_by_ip(self):
        """Test rate limiting by IP."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)

        # Consume all IP tokens
        for _ in range(10):  # IP limit is 2x more lenient
            await limiter.check_rate_limit(ip="192.168.1.1")

        # Next request should be blocked
        allowed, info = await limiter.check_rate_limit(ip="192.168.1.1")

        assert allowed is False
        assert info["limit_type"] == "ip"

    @pytest.mark.asyncio
    async def test_separate_user_buckets(self):
        """Test different users have separate limits."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=3)

        # User 1 hits limit
        for _ in range(3):
            await limiter.check_rate_limit(user_id="user_1")

        allowed1, _ = await limiter.check_rate_limit(user_id="user_1")
        assert allowed1 is False

        # User 2 should still be allowed
        allowed2, _ = await limiter.check_rate_limit(user_id="user_2")
        assert allowed2 is True

    @pytest.mark.asyncio
    async def test_no_user_or_ip(self):
        """Test rate limit without user or IP."""
        limiter = RateLimiter()

        # Should allow without any identification
        allowed, info = await limiter.check_rate_limit()
        assert allowed is True

    def test_get_bucket_creates_new(self):
        """Test _get_bucket creates new bucket if not exists."""
        limiter = RateLimiter()

        bucket = limiter._get_bucket("new_key", limiter.user_buckets)

        assert bucket is not None
        assert bucket.capacity == limiter.burst_size

    def test_get_bucket_returns_existing(self):
        """Test _get_bucket returns existing bucket."""
        limiter = RateLimiter()

        bucket1 = limiter._get_bucket("key", limiter.user_buckets)
        bucket1.consume(5)

        bucket2 = limiter._get_bucket("key", limiter.user_buckets)

        assert bucket1 is bucket2
        assert bucket2.tokens < bucket2.capacity


class TestGetRateLimiter:
    """Tests for get_rate_limiter function."""

    def test_returns_instance(self):
        """Test get_rate_limiter returns a RateLimiter."""
        limiter = get_rate_limiter()

        assert isinstance(limiter, RateLimiter)

    def test_returns_singleton(self):
        """Test get_rate_limiter returns same instance."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2


class TestRefillRate:
    """Tests for refill rate calculations."""

    def test_refill_rate_calculation(self):
        """Test refill rate is calculated correctly."""
        limiter = RateLimiter(requests_per_minute=120, burst_size=100)

        # 120 requests/minute = 2 tokens/second
        assert limiter.refill_rate == 2.0

    def test_refill_rate_fraction(self):
        """Test fractional refill rate."""
        limiter = RateLimiter(requests_per_minute=30, burst_size=100)

        # 30 requests/minute = 0.5 tokens/second
        assert limiter.refill_rate == 0.5
