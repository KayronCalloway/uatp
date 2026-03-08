#!/usr/bin/env python3
"""
Health Check System for UATP Capsule Engine
===========================================

This module provides comprehensive health checks for all system components
including database, external services, and application health.
"""

import asyncio
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Health check result structure."""

    service: str
    status: HealthStatus
    response_time: float
    timestamp: datetime
    details: Dict[str, Any] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["status"] = self.status.value
        result["timestamp"] = self.timestamp.isoformat()
        return result


class HealthCheckManager:
    """Health check manager for UATP system."""

    def __init__(self):
        self.checks = {}
        self.results_history = []
        self.max_history = 1000

        logger.info(" Health Check Manager initialized")

    def register_check(self, name: str, check_func, interval: int = 30):
        """Register a health check."""

        self.checks[name] = {
            "function": check_func,
            "interval": interval,
            "last_run": None,
            "last_result": None,
        }

        logger.info(f" Registered health check: {name} (interval: {interval}s)")

    async def run_check(self, name: str) -> HealthCheckResult:
        """Run a specific health check."""

        if name not in self.checks:
            return HealthCheckResult(
                service=name,
                status=HealthStatus.UNKNOWN,
                response_time=0.0,
                timestamp=datetime.now(),
                error="Health check not registered",
            )

        check = self.checks[name]
        start_time = time.time()

        try:
            result = await check["function"]()
            response_time = time.time() - start_time

            health_result = HealthCheckResult(
                service=name,
                status=result.get("status", HealthStatus.UNKNOWN),
                response_time=response_time,
                timestamp=datetime.now(),
                details=result.get("details", {}),
                error=result.get("error"),
            )

            # Update check info
            check["last_run"] = datetime.now()
            check["last_result"] = health_result

            # Add to history
            self.results_history.append(health_result)
            if len(self.results_history) > self.max_history:
                self.results_history.pop(0)

            return health_result

        except Exception as e:
            response_time = time.time() - start_time

            health_result = HealthCheckResult(
                service=name,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                timestamp=datetime.now(),
                error=str(e),
            )

            check["last_run"] = datetime.now()
            check["last_result"] = health_result
            self.results_history.append(health_result)

            logger.error(f"[ERROR] Health check failed for {name}: {e}")
            return health_result

    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""

        results = {}

        for name in self.checks:
            results[name] = await self.run_check(name)

        return results

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health."""

        results = await self.run_all_checks()

        # Calculate overall status
        statuses = [result.status for result in results.values()]

        if all(status == HealthStatus.HEALTHY for status in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED

        # Calculate stats
        total_checks = len(results)
        healthy_checks = sum(
            1 for result in results.values() if result.status == HealthStatus.HEALTHY
        )
        unhealthy_checks = sum(
            1 for result in results.values() if result.status == HealthStatus.UNHEALTHY
        )
        degraded_checks = total_checks - healthy_checks - unhealthy_checks

        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": total_checks,
                "healthy": healthy_checks,
                "degraded": degraded_checks,
                "unhealthy": unhealthy_checks,
            },
            "checks": {name: result.to_dict() for name, result in results.items()},
        }

    def get_check_history(
        self, service: str = None, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get health check history."""

        cutoff_time = datetime.now() - timedelta(hours=hours)

        history = [
            result.to_dict()
            for result in self.results_history
            if result.timestamp > cutoff_time
            and (service is None or result.service == service)
        ]

        return sorted(history, key=lambda x: x["timestamp"], reverse=True)

    def get_uptime_stats(self, service: str = None) -> Dict[str, Any]:
        """Get uptime statistics."""

        history = self.get_check_history(service, hours=24)

        if not history:
            return {"uptime_percentage": 0.0, "total_checks": 0}

        total_checks = len(history)
        healthy_checks = sum(1 for check in history if check["status"] == "healthy")
        uptime_percentage = (
            (healthy_checks / total_checks) * 100 if total_checks > 0 else 0.0
        )

        return {
            "uptime_percentage": uptime_percentage,
            "total_checks": total_checks,
            "healthy_checks": healthy_checks,
            "period_hours": 24,
        }


# Health check implementations
async def check_database_health():
    """Check database health."""

    try:
        from config.database_config import get_database_adapter, get_database_config

        config = get_database_config()
        adapter = get_database_adapter()

        if not adapter:
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": "Database adapter not available",
            }

        # Test basic operations
        start_time = time.time()

        if config.is_postgresql():
            # PostgreSQL-specific checks
            from database.postgresql_schema import get_postgresql_manager

            pg_manager = get_postgresql_manager()

            if not pg_manager.pool:
                await pg_manager.create_connection_pool()

            health = await pg_manager.health_check()

            if health["status"] == "healthy":
                return {
                    "status": HealthStatus.HEALTHY,
                    "details": {
                        "database_type": "postgresql",
                        "version": health.get("version", "unknown"),
                        "tables": len(health.get("tables", [])),
                        "connectivity": health.get("connectivity", False),
                        "pool_size": health.get("pool_status", {}).get("size", 0),
                    },
                }
            else:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "error": health.get("error", "Unknown database error"),
                }

        else:
            # SQLite checks
            return {
                "status": HealthStatus.HEALTHY,
                "details": {
                    "database_type": "sqlite",
                    "file_path": config.config.get("database_path", "unknown"),
                },
            }

    except Exception as e:
        return {"status": HealthStatus.UNHEALTHY, "error": str(e)}


async def check_capsule_engine_health():
    """Check capsule engine health."""

    try:
        from live_capture.real_time_capsule_generator import RealTimeCapsuleGenerator

        # Test capsule generation
        generator = RealTimeCapsuleGenerator()

        # Check if the generator is properly initialized
        if hasattr(generator, "session_manager"):
            return {
                "status": HealthStatus.HEALTHY,
                "details": {
                    "active_sessions": len(
                        getattr(generator.session_manager, "sessions", {})
                    ),
                    "auto_encapsulation": getattr(
                        generator, "auto_encapsulation", False
                    ),
                },
            }
        else:
            return {
                "status": HealthStatus.DEGRADED,
                "details": {"message": "Capsule engine partially initialized"},
            }

    except Exception as e:
        return {"status": HealthStatus.UNHEALTHY, "error": str(e)}


async def check_api_health():
    """Check API health."""

    try:
        import aiohttp

        # Test API endpoint
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    "http://localhost:8000/health", timeout=5
                ) as response:
                    if response.status == 200:
                        return {
                            "status": HealthStatus.HEALTHY,
                            "details": {
                                "api_status": "running",
                                "response_code": response.status,
                            },
                        }
                    else:
                        return {
                            "status": HealthStatus.DEGRADED,
                            "details": {
                                "api_status": "degraded",
                                "response_code": response.status,
                            },
                        }
            except asyncio.TimeoutError:
                return {"status": HealthStatus.UNHEALTHY, "error": "API timeout"}

    except Exception as e:
        return {"status": HealthStatus.UNHEALTHY, "error": str(e)}


async def check_authentication_health():
    """Check authentication system health."""

    try:
        from auth.jwt_auth import get_authenticator

        authenticator = get_authenticator()

        # Test basic authentication functions
        stats = authenticator.get_user_stats()

        return {
            "status": HealthStatus.HEALTHY,
            "details": {
                "total_users": stats.get("total_users", 0),
                "active_users": stats.get("active_users", 0),
                "active_refresh_tokens": stats.get("active_refresh_tokens", 0),
            },
        }

    except Exception as e:
        return {"status": HealthStatus.UNHEALTHY, "error": str(e)}


async def check_disk_space():
    """Check disk space."""

    try:
        import shutil

        # Check current directory disk usage
        total, used, free = shutil.disk_usage(".")

        # Convert to GB
        total_gb = total / (1024**3)
        used_gb = used / (1024**3)
        free_gb = free / (1024**3)

        used_percentage = (used / total) * 100

        # Determine status based on usage
        if used_percentage > 90:
            status = HealthStatus.UNHEALTHY
        elif used_percentage > 80:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        return {
            "status": status,
            "details": {
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "used_percentage": round(used_percentage, 2),
            },
        }

    except Exception as e:
        return {"status": HealthStatus.UNHEALTHY, "error": str(e)}


async def check_memory_usage():
    """Check memory usage."""

    try:
        import psutil

        # Get memory info
        memory = psutil.virtual_memory()

        used_percentage = memory.percent

        # Determine status based on usage
        if used_percentage > 90:
            status = HealthStatus.UNHEALTHY
        elif used_percentage > 80:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        return {
            "status": status,
            "details": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "free_gb": round(memory.free / (1024**3), 2),
                "used_percentage": used_percentage,
            },
        }

    except ImportError:
        return {"status": HealthStatus.UNKNOWN, "error": "psutil not available"}
    except Exception as e:
        return {"status": HealthStatus.UNHEALTHY, "error": str(e)}


# Global health check manager
_health_manager = None


def get_health_manager() -> HealthCheckManager:
    """Get the global health check manager."""
    global _health_manager
    if _health_manager is None:
        _health_manager = HealthCheckManager()

        # Register default health checks
        _health_manager.register_check("database", check_database_health, 30)
        _health_manager.register_check(
            "capsule_engine", check_capsule_engine_health, 60
        )
        _health_manager.register_check("api", check_api_health, 30)
        _health_manager.register_check(
            "authentication", check_authentication_health, 60
        )
        _health_manager.register_check("disk_space", check_disk_space, 300)  # 5 minutes
        _health_manager.register_check("memory", check_memory_usage, 60)

    return _health_manager


async def main():
    """Test health check system."""

    print(" Testing Health Check System")
    print("=" * 40)

    # Get health manager
    health_manager = get_health_manager()

    # Run individual checks
    print("\n Running individual health checks...")

    for check_name in ["database", "capsule_engine", "disk_space", "memory"]:
        print(f"\n Checking {check_name}...")
        result = await health_manager.run_check(check_name)

        status_emoji = {
            HealthStatus.HEALTHY: "[OK]",
            HealthStatus.DEGRADED: "[WARN]",
            HealthStatus.UNHEALTHY: "[ERROR]",
            HealthStatus.UNKNOWN: "",
        }

        print(f"{status_emoji[result.status]} {check_name}: {result.status.value}")
        print(f"   Response time: {result.response_time:.3f}s")

        if result.details:
            print(f"   Details: {result.details}")

        if result.error:
            print(f"   Error: {result.error}")

    # Get overall system health
    print("\n Overall system health...")
    system_health = await health_manager.get_system_health()

    print(f"Overall Status: {system_health['overall_status']}")
    print(f"Summary: {system_health['summary']}")

    # Show uptime stats
    print("\n Uptime statistics (last 24h)...")
    uptime = health_manager.get_uptime_stats()
    print(f"Uptime: {uptime['uptime_percentage']:.1f}%")
    print(f"Total checks: {uptime['total_checks']}")

    print("\n[OK] Health check system test completed!")


if __name__ == "__main__":
    asyncio.run(main())
