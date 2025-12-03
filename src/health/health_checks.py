"""
Production-Ready Health Check System for UATP Capsule Engine

Provides comprehensive health monitoring including:
- Database connectivity checks
- External service availability
- Circuit breaker status
- Memory and resource usage
- Dependency health validation
- Kubernetes-compatible health endpoints
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil
import structlog
from fastapi import HTTPException

from ..resilience import circuit_registry
from ..database.connection import get_database_manager

logger = structlog.get_logger(__name__)


class HealthStatus(str, Enum):
    """Health check status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""

    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    duration_ms: float
    timestamp: datetime
    error: Optional[str] = None


class HealthChecker:
    """Base class for health checkers"""

    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout
        self.logger = logger.bind(health_checker=name)

    async def check(self) -> HealthCheckResult:
        """Perform health check with timeout"""
        start_time = time.time()

        try:
            async with asyncio.timeout(self.timeout):
                status, message, details = await self._perform_check()

            duration_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details=details,
                duration_ms=duration_ms,
                timestamp=datetime.now(timezone.utc),
            )

        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Health check timed out after {self.timeout}s"

            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=error_msg,
                details={"timeout": self.timeout},
                duration_ms=duration_ms,
                timestamp=datetime.now(timezone.utc),
                error=error_msg,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Health check failed: {str(e)}"

            self.logger.error("Health check failed", error=str(e))

            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=error_msg,
                details={"error_type": type(e).__name__},
                duration_ms=duration_ms,
                timestamp=datetime.now(timezone.utc),
                error=error_msg,
            )

    async def _perform_check(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Override this method in subclasses"""
        raise NotImplementedError


class DatabaseHealthChecker(HealthChecker):
    """Database connectivity health checker"""

    def __init__(self):
        super().__init__("database", timeout=10.0)
        self.db_manager = get_database_manager()

    async def _perform_check(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Check database connectivity"""
        try:
            # Check if database manager is initialized
            if not hasattr(self.db_manager, "health_check"):
                return (
                    HealthStatus.UNHEALTHY,
                    "Database manager not properly initialized",
                    {"initialized": False},
                )

            # Perform health check
            health_info = self.db_manager.health_check()

            if health_info.get("database", False):
                return (
                    HealthStatus.HEALTHY,
                    "Database connection is healthy",
                    health_info,
                )
            else:
                return (
                    HealthStatus.UNHEALTHY,
                    "Database connection failed",
                    health_info,
                )

        except Exception as e:
            return (
                HealthStatus.UNHEALTHY,
                f"Database health check failed: {str(e)}",
                {"error": str(e)},
            )


class CircuitBreakerHealthChecker(HealthChecker):
    """Circuit breaker status health checker"""

    def __init__(self):
        super().__init__("circuit_breakers", timeout=2.0)

    async def _perform_check(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Check circuit breaker status"""
        try:
            health_summary = circuit_registry.get_health_summary()

            overall_health = health_summary["overall_health"]
            total_circuits = health_summary["total_circuits"]
            unhealthy_count = health_summary["unhealthy"]

            if overall_health == "healthy":
                status = HealthStatus.HEALTHY
                message = f"All {total_circuits} circuit breakers are healthy"
            elif overall_health == "degraded":
                status = HealthStatus.DEGRADED
                message = (
                    f"{unhealthy_count}/{total_circuits} circuit breakers are unhealthy"
                )
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Circuit breaker system is unhealthy ({unhealthy_count}/{total_circuits})"

            return (status, message, health_summary)

        except Exception as e:
            return (
                HealthStatus.UNHEALTHY,
                f"Circuit breaker health check failed: {str(e)}",
                {"error": str(e)},
            )


class SystemResourceHealthChecker(HealthChecker):
    """System resource utilization health checker"""

    def __init__(self, cpu_threshold: float = 80.0, memory_threshold: float = 85.0):
        super().__init__("system_resources", timeout=5.0)
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold

    async def _perform_check(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Check system resource utilization"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            details = {
                "cpu": {"percent": cpu_percent, "threshold": self.cpu_threshold},
                "memory": {
                    "percent": memory.percent,
                    "available_gb": round(memory.available / (1024**3), 2),
                    "total_gb": round(memory.total / (1024**3), 2),
                    "threshold": self.memory_threshold,
                },
                "disk": {
                    "percent": disk.percent,
                    "free_gb": round(disk.free / (1024**3), 2),
                    "total_gb": round(disk.total / (1024**3), 2),
                },
            }

            # Determine health status
            issues = []

            if cpu_percent > self.cpu_threshold:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")

            if memory.percent > self.memory_threshold:
                issues.append(f"High memory usage: {memory.percent:.1f}%")

            if disk.percent > 90:
                issues.append(f"High disk usage: {disk.percent:.1f}%")

            if not issues:
                return (
                    HealthStatus.HEALTHY,
                    "System resources are within normal limits",
                    details,
                )
            elif len(issues) == 1 and (cpu_percent < 90 and memory.percent < 95):
                return (
                    HealthStatus.DEGRADED,
                    f"Resource warning: {'; '.join(issues)}",
                    details,
                )
            else:
                return (
                    HealthStatus.UNHEALTHY,
                    f"Resource critical: {'; '.join(issues)}",
                    details,
                )

        except Exception as e:
            return (
                HealthStatus.UNHEALTHY,
                f"System resource check failed: {str(e)}",
                {"error": str(e)},
            )


class ExternalServiceHealthChecker(HealthChecker):
    """External service availability health checker"""

    def __init__(self, service_name: str, check_func):
        super().__init__(f"external_{service_name}", timeout=10.0)
        self.service_name = service_name
        self.check_func = check_func

    async def _perform_check(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Check external service availability"""
        try:
            # Call the service-specific check function
            is_available, details = await self.check_func()

            if is_available:
                return (
                    HealthStatus.HEALTHY,
                    f"{self.service_name} service is available",
                    details,
                )
            else:
                return (
                    HealthStatus.UNHEALTHY,
                    f"{self.service_name} service is unavailable",
                    details,
                )

        except Exception as e:
            return (
                HealthStatus.UNHEALTHY,
                f"{self.service_name} service check failed: {str(e)}",
                {"error": str(e)},
            )


class HealthCheckManager:
    """Manages all health checks for the application"""

    def __init__(self):
        self.checkers: List[HealthChecker] = []
        self.logger = logger.bind(component="health_manager")

        # Register default health checkers
        self._register_default_checkers()

    def _register_default_checkers(self):
        """Register default health checkers"""
        self.register_checker(DatabaseHealthChecker())
        self.register_checker(CircuitBreakerHealthChecker())
        self.register_checker(SystemResourceHealthChecker())

    def register_checker(self, checker: HealthChecker):
        """Register a health checker"""
        self.checkers.append(checker)
        self.logger.info("Health checker registered", checker=checker.name)

    async def check_health(self, include_details: bool = True) -> Dict[str, Any]:
        """Perform all health checks"""
        start_time = time.time()

        # Run all health checks concurrently
        tasks = [checker.check() for checker in self.checkers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        health_results = {}
        overall_status = HealthStatus.HEALTHY
        failed_checks = []
        degraded_checks = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle unexpected errors
                checker_name = self.checkers[i].name
                health_results[checker_name] = {
                    "status": HealthStatus.UNHEALTHY.value,
                    "message": f"Health check crashed: {str(result)}",
                    "error": str(result),
                }
                failed_checks.append(checker_name)
                overall_status = HealthStatus.UNHEALTHY
            else:
                checker_result = result
                health_results[checker_result.name] = {
                    "status": checker_result.status.value,
                    "message": checker_result.message,
                    "duration_ms": round(checker_result.duration_ms, 2),
                    "timestamp": checker_result.timestamp.isoformat(),
                }

                if include_details:
                    health_results[checker_result.name][
                        "details"
                    ] = checker_result.details

                if checker_result.error:
                    health_results[checker_result.name]["error"] = checker_result.error

                # Update overall status
                if checker_result.status == HealthStatus.UNHEALTHY:
                    failed_checks.append(checker_result.name)
                    overall_status = HealthStatus.UNHEALTHY
                elif checker_result.status == HealthStatus.DEGRADED:
                    degraded_checks.append(checker_result.name)
                    if overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED

        total_duration = (time.time() - start_time) * 1000

        # Create summary
        summary = {
            "status": overall_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": round(total_duration, 2),
            "checks": health_results,
        }

        # Add summary statistics
        total_checks = len(self.checkers)
        healthy_checks = total_checks - len(failed_checks) - len(degraded_checks)

        summary["summary"] = {
            "total_checks": total_checks,
            "healthy": healthy_checks,
            "degraded": len(degraded_checks),
            "unhealthy": len(failed_checks),
        }

        if failed_checks:
            summary["failed_checks"] = failed_checks
        if degraded_checks:
            summary["degraded_checks"] = degraded_checks

        # Log the health check result
        self.logger.info(
            "Health check completed",
            overall_status=overall_status.value,
            duration_ms=round(total_duration, 2),
            healthy=healthy_checks,
            degraded=len(degraded_checks),
            unhealthy=len(failed_checks),
        )

        return summary

    async def check_readiness(self) -> Dict[str, Any]:
        """Check if application is ready to serve traffic"""
        # For readiness, we only check critical dependencies
        critical_checkers = [
            checker
            for checker in self.checkers
            if checker.name in ["database", "circuit_breakers"]
        ]

        if not critical_checkers:
            return {
                "status": HealthStatus.HEALTHY.value,
                "message": "No critical dependencies to check",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Run critical checks
        tasks = [checker.check() for checker in critical_checkers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check if all critical services are healthy
        failed_critical = []
        for i, result in enumerate(results):
            if isinstance(result, Exception) or result.status == HealthStatus.UNHEALTHY:
                failed_critical.append(critical_checkers[i].name)

        if failed_critical:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Critical services unavailable: {', '.join(failed_critical)}",
                "failed_services": failed_critical,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            return {
                "status": HealthStatus.HEALTHY.value,
                "message": "All critical services are ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def check_liveness(self) -> Dict[str, Any]:
        """Check if application is alive (basic functionality)"""
        # Liveness check should be lightweight
        return {
            "status": HealthStatus.HEALTHY.value,
            "message": "Application is alive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": time.time() - getattr(self, "_start_time", time.time()),
        }

    def set_start_time(self):
        """Set application start time for uptime calculation"""
        self._start_time = time.time()


# Global health check manager
health_manager = HealthCheckManager()


async def get_health_status(include_details: bool = True) -> Dict[str, Any]:
    """Get comprehensive health status"""
    return await health_manager.check_health(include_details)


async def get_readiness_status() -> Dict[str, Any]:
    """Get readiness status (for Kubernetes readiness probe)"""
    return await health_manager.check_readiness()


async def get_liveness_status() -> Dict[str, Any]:
    """Get liveness status (for Kubernetes liveness probe)"""
    return await health_manager.check_liveness()


def create_health_check_exception(status: HealthStatus, message: str) -> HTTPException:
    """Create appropriate HTTP exception based on health status"""
    if status == HealthStatus.UNHEALTHY:
        return HTTPException(status_code=503, detail=message)
    elif status == HealthStatus.DEGRADED:
        return HTTPException(status_code=200, detail=message)  # Still serving traffic
    else:
        return HTTPException(status_code=200, detail=message)
