"""
Monitoring Middleware
=====================

Production-grade monitoring middleware with Prometheus metrics,
health checks, and system monitoring.
"""

import time
import psutil
import logging
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse
import os
import asyncio

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

ACTIVE_CONNECTIONS = Gauge(
    "http_active_connections", "Number of active HTTP connections"
)

SYSTEM_CPU_USAGE = Gauge("system_cpu_usage_percent", "System CPU usage percentage")

SYSTEM_MEMORY_USAGE = Gauge(
    "system_memory_usage_percent", "System memory usage percentage"
)

SYSTEM_DISK_USAGE = Gauge("system_disk_usage_percent", "System disk usage percentage")

DATABASE_CONNECTIONS = Gauge(
    "database_connections_active", "Number of active database connections"
)

REDIS_CONNECTIONS = Gauge(
    "redis_connections_active", "Number of active Redis connections"
)

APPLICATION_INFO = Gauge(
    "application_info", "Application information", ["version", "environment"]
)

ERROR_COUNT = Counter(
    "application_errors_total", "Total application errors", ["error_type", "endpoint"]
)

SECURITY_EVENTS = Counter(
    "security_events_total", "Total security events", ["event_type", "severity"]
)


class MonitoringConfig:
    """Configuration for monitoring middleware."""

    def __init__(self):
        # Metrics collection
        self.enable_metrics = (
            os.getenv("PROMETHEUS_METRICS_ENABLED", "true").lower() == "true"
        )
        self.metrics_endpoint = os.getenv("METRICS_ENDPOINT", "/metrics")

        # System monitoring
        self.enable_system_metrics = True
        self.system_metrics_interval = int(
            os.getenv("SYSTEM_METRICS_INTERVAL", "30")
        )  # seconds

        # Health check
        self.health_endpoint = os.getenv("HEALTH_ENDPOINT", "/health")

        # Application info
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.environment = os.getenv("ENVIRONMENT", "development")


class MetricsMiddleware(BaseHTTPMiddleware):
    """Prometheus metrics collection middleware."""

    def __init__(self, app, config: Optional[MonitoringConfig] = None):
        super().__init__(app)
        self.config = config or MonitoringConfig()
        self.active_requests = 0

        # Initialize application info metric
        APPLICATION_INFO.labels(
            version=self.config.app_version, environment=self.config.environment
        ).set(1)

        # Start system metrics collection
        if self.config.enable_system_metrics:
            asyncio.create_task(self._collect_system_metrics())

        logger.info("Metrics middleware initialized")

    async def dispatch(self, request: Request, call_next):
        """Collect request metrics."""
        # Handle metrics endpoint
        if (
            request.url.path == self.config.metrics_endpoint
            and self.config.enable_metrics
        ):
            return await self._handle_metrics_request()

        # Handle health check endpoint
        if request.url.path == self.config.health_endpoint:
            return await self._handle_health_request()

        # Skip metrics collection for internal endpoints
        if request.url.path in [
            self.config.metrics_endpoint,
            self.config.health_endpoint,
            "/favicon.ico",
        ]:
            return await call_next(request)

        # Increment active connections
        self.active_requests += 1
        ACTIVE_CONNECTIONS.set(self.active_requests)

        # Get endpoint for labeling
        endpoint = self._get_endpoint_label(request.url.path)

        # Start request timer
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Record metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
            ).inc()

            REQUEST_DURATION.labels(method=request.method, endpoint=endpoint).observe(
                time.time() - start_time
            )

            return response

        except Exception as e:
            # Record error metrics
            ERROR_COUNT.labels(error_type=type(e).__name__, endpoint=endpoint).inc()

            # Still record request duration
            REQUEST_DURATION.labels(method=request.method, endpoint=endpoint).observe(
                time.time() - start_time
            )

            raise

        finally:
            # Decrement active connections
            self.active_requests -= 1
            ACTIVE_CONNECTIONS.set(self.active_requests)

    async def _handle_metrics_request(self) -> PlainTextResponse:
        """Handle Prometheus metrics endpoint."""
        try:
            metrics_data = generate_latest()
            return PlainTextResponse(
                content=metrics_data, media_type=CONTENT_TYPE_LATEST
            )
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return PlainTextResponse("Error generating metrics", status_code=500)

    async def _handle_health_request(self) -> Response:
        """Handle health check endpoint."""
        health_data = await self._get_health_status()

        status_code = 200 if health_data["status"] == "healthy" else 503

        return Response(
            content=health_data, status_code=status_code, media_type="application/json"
        )

    async def _get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        health_checks = {}
        overall_status = "healthy"

        # System health
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            health_checks["system"] = {
                "status": "healthy",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
            }

            # Check for high resource usage
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 95:
                health_checks["system"]["status"] = "warning"
                if overall_status == "healthy":
                    overall_status = "warning"

        except Exception as e:
            health_checks["system"] = {"status": "error", "error": str(e)}
            overall_status = "unhealthy"

        # Database health (if available)
        try:
            # This would be implemented with actual database check
            health_checks["database"] = {
                "status": "healthy",
                "connections": "available",
            }
        except Exception as e:
            health_checks["database"] = {"status": "error", "error": str(e)}
            overall_status = "unhealthy"

        # Redis health (if available)
        try:
            # This would be implemented with actual Redis check
            health_checks["redis"] = {"status": "healthy", "connections": "available"}
        except Exception as e:
            health_checks["redis"] = {"status": "error", "error": str(e)}
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "version": self.config.app_version,
            "environment": self.config.environment,
            "checks": health_checks,
        }

    def _get_endpoint_label(self, path: str) -> str:
        """Get normalized endpoint label for metrics."""
        # Normalize path parameters
        # e.g., /api/users/123 -> /api/users/{id}

        # Simple normalization - replace numeric IDs
        import re

        # Replace UUIDs
        path = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{uuid}",
            path,
        )

        # Replace numeric IDs
        path = re.sub(r"/\d+", "/{id}", path)

        # Limit label cardinality
        if len(path.split("/")) > 5:
            parts = path.split("/")[:5]
            path = "/".join(parts) + "/..."

        return path

    async def _collect_system_metrics(self):
        """Collect system metrics periodically."""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                SYSTEM_CPU_USAGE.set(cpu_percent)

                # Memory usage
                memory = psutil.virtual_memory()
                SYSTEM_MEMORY_USAGE.set(memory.percent)

                # Disk usage
                disk = psutil.disk_usage("/")
                SYSTEM_DISK_USAGE.set(disk.percent)

                # Wait for next collection
                await asyncio.sleep(self.config.system_metrics_interval)

            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(self.config.system_metrics_interval)


class SecurityMetricsCollector:
    """Collect security-related metrics."""

    @staticmethod
    def record_security_event(event_type: str, severity: str = "info"):
        """Record a security event."""
        SECURITY_EVENTS.labels(event_type=event_type, severity=severity).inc()

    @staticmethod
    def record_failed_login(username: str):
        """Record failed login attempt."""
        SecurityMetricsCollector.record_security_event("failed_login", "warning")

    @staticmethod
    def record_blocked_request(reason: str):
        """Record blocked request."""
        SecurityMetricsCollector.record_security_event(
            f"blocked_request_{reason}", "warning"
        )

    @staticmethod
    def record_rate_limit_exceeded():
        """Record rate limit exceeded."""
        SecurityMetricsCollector.record_security_event("rate_limit_exceeded", "info")


class DatabaseMetricsCollector:
    """Collect database-related metrics."""

    @staticmethod
    def update_connection_count(count: int):
        """Update database connection count."""
        DATABASE_CONNECTIONS.set(count)

    @staticmethod
    def record_query_error(error_type: str):
        """Record database query error."""
        ERROR_COUNT.labels(
            error_type=f"database_{error_type}", endpoint="database"
        ).inc()


class RedisMetricsCollector:
    """Collect Redis-related metrics."""

    @staticmethod
    def update_connection_count(count: int):
        """Update Redis connection count."""
        REDIS_CONNECTIONS.set(count)

    @staticmethod
    def record_cache_hit():
        """Record cache hit."""
        # This would be implemented with actual cache metrics
        pass

    @staticmethod
    def record_cache_miss():
        """Record cache miss."""
        # This would be implemented with actual cache metrics
        pass


class ApplicationMetrics:
    """Application-specific metrics collection."""

    def __init__(self):
        # Business metrics
        self.user_registrations = Counter(
            "user_registrations_total", "Total user registrations"
        )

        self.agent_creations = Counter("agent_creations_total", "Total agent creations")

        self.citizenship_applications = Counter(
            "citizenship_applications_total",
            "Total citizenship applications",
            ["status"],
        )

        self.bond_creations = Counter("bond_creations_total", "Total bond creations")

        self.payment_transactions = Counter(
            "payment_transactions_total", "Total payment transactions", ["status"]
        )

        self.active_users = Gauge("active_users_current", "Currently active users")

        self.active_agents = Gauge("active_agents_current", "Currently active agents")

    def record_user_registration(self):
        """Record user registration."""
        self.user_registrations.inc()

    def record_agent_creation(self):
        """Record agent creation."""
        self.agent_creations.inc()

    def record_citizenship_application(self, status: str):
        """Record citizenship application."""
        self.citizenship_applications.labels(status=status).inc()

    def record_bond_creation(self):
        """Record bond creation."""
        self.bond_creations.inc()

    def record_payment_transaction(self, status: str):
        """Record payment transaction."""
        self.payment_transactions.labels(status=status).inc()

    def update_active_users(self, count: int):
        """Update active users count."""
        self.active_users.set(count)

    def update_active_agents(self, count: int):
        """Update active agents count."""
        self.active_agents.set(count)


# Global instances
security_metrics = SecurityMetricsCollector()
database_metrics = DatabaseMetricsCollector()
redis_metrics = RedisMetricsCollector()
app_metrics = ApplicationMetrics()


class PerformanceMonitor:
    """Monitor application performance and alert on issues."""

    def __init__(self):
        self.response_time_threshold = 2.0  # seconds
        self.error_rate_threshold = 0.05  # 5%
        self.memory_threshold = 85  # percent
        self.cpu_threshold = 85  # percent

        self.alerts_sent = set()
        self.last_alert_check = time.time()

    async def check_performance(self):
        """Check performance metrics and send alerts if needed."""
        current_time = time.time()

        # Only check every 5 minutes
        if current_time - self.last_alert_check < 300:
            return

        try:
            # Check system resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent

            if cpu_percent > self.cpu_threshold:
                await self._send_alert(f"High CPU usage: {cpu_percent}%")

            if memory_percent > self.memory_threshold:
                await self._send_alert(f"High memory usage: {memory_percent}%")

            self.last_alert_check = current_time

        except Exception as e:
            logger.error(f"Error checking performance: {e}")

    async def _send_alert(self, message: str):
        """Send performance alert."""
        # Prevent duplicate alerts
        if message in self.alerts_sent:
            return

        logger.error(f"Performance Alert: {message}")

        # Add to sent alerts (with TTL in production)
        self.alerts_sent.add(message)

        # In production, this would send to alerting system
        # (Slack, PagerDuty, email, etc.)


# Global performance monitor
performance_monitor = PerformanceMonitor()
