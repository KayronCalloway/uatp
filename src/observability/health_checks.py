"""
Health Check Cascade System
===========================

Production-grade health check system with:
- Cascading dependency checks
- Granular status reporting (healthy, degraded, unhealthy)
- Response time tracking
- Configurable thresholds

Usage:
    from src.observability.health_checks import HealthCheckService

    health_service = HealthCheckService()
    result = await health_service.check_all()
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    NOT_CONFIGURED = "not_configured"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""

    name: str
    status: HealthStatus
    response_time_ms: float
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "status": self.status.value,
            "response_time_ms": round(self.response_time_ms, 2),
            "message": self.message,
            "details": self.details,
            "dependencies": self.dependencies,
        }


@dataclass
class SystemHealthResult:
    """Aggregated system health result."""

    overall_status: HealthStatus
    checks: List[HealthCheckResult]
    timestamp: str
    total_response_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.overall_status.value,
            "checks": {check.name: check.to_dict() for check in self.checks},
            "timestamp": self.timestamp,
            "total_response_time_ms": round(self.total_response_time_ms, 2),
            "summary": {
                "healthy": sum(
                    1 for c in self.checks if c.status == HealthStatus.HEALTHY
                ),
                "degraded": sum(
                    1 for c in self.checks if c.status == HealthStatus.DEGRADED
                ),
                "unhealthy": sum(
                    1 for c in self.checks if c.status == HealthStatus.UNHEALTHY
                ),
                "not_configured": sum(
                    1 for c in self.checks if c.status == HealthStatus.NOT_CONFIGURED
                ),
            },
        }


class HealthCheckService:
    """
    Production health check service with cascading dependencies.

    Features:
    - Register custom health checks
    - Define check dependencies
    - Configure response time thresholds
    - Parallel execution with timeout
    """

    def __init__(
        self,
        check_timeout_seconds: float = 5.0,
        degraded_threshold_ms: float = 1000.0,
    ):
        self.check_timeout = check_timeout_seconds
        self.degraded_threshold_ms = degraded_threshold_ms
        self._checks: Dict[
            str, Callable[[], Coroutine[Any, Any, HealthCheckResult]]
        ] = {}
        self._dependencies: Dict[str, List[str]] = {}

    def register_check(
        self,
        name: str,
        check_fn: Callable[[], Coroutine[Any, Any, HealthCheckResult]],
        dependencies: Optional[List[str]] = None,
    ):
        """Register a health check function."""
        self._checks[name] = check_fn
        self._dependencies[name] = dependencies or []

    async def check_one(self, name: str) -> HealthCheckResult:
        """Run a single health check by name."""
        if name not in self._checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.NOT_CONFIGURED,
                response_time_ms=0,
                message=f"Check '{name}' not registered",
            )

        start_time = time.perf_counter()
        try:
            result = await asyncio.wait_for(
                self._checks[name](), timeout=self.check_timeout
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # Upgrade status to degraded if response time is high
            if (
                result.status == HealthStatus.HEALTHY
                and elapsed_ms > self.degraded_threshold_ms
            ):
                result.status = HealthStatus.DEGRADED
                result.message = (
                    f"{result.message or 'Check passed'} (slow: {elapsed_ms:.0f}ms)"
                )

            result.response_time_ms = elapsed_ms
            result.dependencies = self._dependencies.get(name, [])
            return result

        except asyncio.TimeoutError:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=elapsed_ms,
                message=f"Check timed out after {self.check_timeout}s",
                dependencies=self._dependencies.get(name, []),
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Health check '{name}' failed: {e}")
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=elapsed_ms,
                message=str(e),
                dependencies=self._dependencies.get(name, []),
            )

    async def check_all(self) -> SystemHealthResult:
        """Run all registered health checks in parallel."""
        from datetime import datetime, timezone

        start_time = time.perf_counter()

        # Run all checks concurrently
        tasks = [self.check_one(name) for name in self._checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        check_results = []
        for result in results:
            if isinstance(result, Exception):
                check_results.append(
                    HealthCheckResult(
                        name="unknown",
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=0,
                        message=str(result),
                    )
                )
            else:
                check_results.append(result)

        # Determine overall status
        overall_status = self._calculate_overall_status(check_results)

        total_time = (time.perf_counter() - start_time) * 1000

        return SystemHealthResult(
            overall_status=overall_status,
            checks=check_results,
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_response_time_ms=total_time,
        )

    def _calculate_overall_status(
        self, results: List[HealthCheckResult]
    ) -> HealthStatus:
        """Calculate overall system status from individual check results."""
        if not results:
            return HealthStatus.HEALTHY

        statuses = [r.status for r in results]

        # Any unhealthy check makes the system unhealthy
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY

        # Any degraded check makes the system degraded
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY


# =============================================================================
# Pre-built health check functions
# =============================================================================


async def check_sqlalchemy() -> HealthCheckResult:
    """Check SQLAlchemy database connection."""
    from src.core.database import db

    try:
        start = time.perf_counter()
        async with db.get_session() as session:
            from sqlalchemy import text

            result = await session.execute(text("SELECT 1"))
            result.fetchone()

        elapsed_ms = (time.perf_counter() - start) * 1000

        return HealthCheckResult(
            name="sqlalchemy",
            status=HealthStatus.HEALTHY,
            response_time_ms=elapsed_ms,
            message="Database connection healthy",
            details={"backend": "SQLAlchemy"},
        )
    except Exception as e:
        return HealthCheckResult(
            name="sqlalchemy",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message=f"Database connection failed: {e}",
        )


async def check_asyncpg() -> HealthCheckResult:
    """Check asyncpg database connection pool."""
    try:
        from src.database.connection import get_database_manager

        db_manager = get_database_manager()

        if not db_manager.pool:
            return HealthCheckResult(
                name="asyncpg",
                status=HealthStatus.NOT_CONFIGURED,
                response_time_ms=0,
                message="asyncpg pool not initialized (may be using SQLite)",
            )

        start = time.perf_counter()
        health = await db_manager.health_check()
        elapsed_ms = (time.perf_counter() - start) * 1000

        if health.get("status") == "healthy":
            return HealthCheckResult(
                name="asyncpg",
                status=HealthStatus.HEALTHY,
                response_time_ms=elapsed_ms,
                message="Connection pool healthy",
                details={
                    "pool_size": health.get("pool", {}).get("size", 0),
                    "idle_size": health.get("pool", {}).get("idle_size", 0),
                    "version": health.get("version", "unknown"),
                },
            )
        else:
            return HealthCheckResult(
                name="asyncpg",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=elapsed_ms,
                message=health.get("error", "Unknown error"),
            )
    except Exception as e:
        return HealthCheckResult(
            name="asyncpg",
            status=HealthStatus.NOT_CONFIGURED,
            response_time_ms=0,
            message=f"asyncpg not available: {e}",
        )


async def check_redis() -> HealthCheckResult:
    """Check Redis connection."""
    try:
        import redis.asyncio as redis

        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD")

        start = time.perf_counter()

        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
            socket_connect_timeout=2.0,
        )

        await client.ping()
        info = await client.info("server")
        await client.aclose()

        elapsed_ms = (time.perf_counter() - start) * 1000

        return HealthCheckResult(
            name="redis",
            status=HealthStatus.HEALTHY,
            response_time_ms=elapsed_ms,
            message="Redis connection healthy",
            details={
                "version": info.get("redis_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            },
        )
    except Exception as e:
        return HealthCheckResult(
            name="redis",
            status=HealthStatus.NOT_CONFIGURED
            if "Connection refused" in str(e)
            else HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message=f"Redis connection failed: {e}",
        )


async def check_crypto() -> HealthCheckResult:
    """Check cryptographic subsystem."""
    try:
        start = time.perf_counter()

        from src.security.uatp_crypto_v7 import ED25519_AVAILABLE, PQ_AVAILABLE

        elapsed_ms = (time.perf_counter() - start) * 1000

        if not ED25519_AVAILABLE:
            return HealthCheckResult(
                name="crypto",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=elapsed_ms,
                message="Ed25519 cryptography not available",
            )

        return HealthCheckResult(
            name="crypto",
            status=HealthStatus.HEALTHY,
            response_time_ms=elapsed_ms,
            message="Cryptographic subsystem healthy",
            details={
                "ed25519_available": ED25519_AVAILABLE,
                "pq_available": PQ_AVAILABLE,
            },
        )
    except Exception as e:
        return HealthCheckResult(
            name="crypto",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            message=f"Crypto subsystem check failed: {e}",
        )


def create_default_health_service() -> HealthCheckService:
    """Create health check service with default checks registered."""
    service = HealthCheckService()

    # Register checks with dependencies
    service.register_check("sqlalchemy", check_sqlalchemy)
    service.register_check("asyncpg", check_asyncpg, dependencies=["sqlalchemy"])
    service.register_check("redis", check_redis)
    service.register_check("crypto", check_crypto)

    return service


# Global instance
_health_service: Optional[HealthCheckService] = None


def get_health_service() -> HealthCheckService:
    """Get or create the global health service instance."""
    global _health_service
    if _health_service is None:
        _health_service = create_default_health_service()
    return _health_service
