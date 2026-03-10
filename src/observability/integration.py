"""
OpenTelemetry Integration Layer for UATP
Provides seamless integration with existing UATP components
"""

import logging
import os
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Dict, Optional

from .logging import (
    get_logger,
    set_request_context,
    set_session_context,
    set_user_context,
    uatp_logging,
)
from .metrics import track_operation_metrics, uatp_metrics
from .tracing import (
    add_span_attributes,
    add_span_event,
    trace_capsule_operation,
    uatp_tracing,
)

logger = logging.getLogger(__name__)


class UATPObservability:
    """
    Main integration class for OpenTelemetry observability in UATP
    Provides a unified interface for all observability features
    """

    def __init__(self):
        self.initialized = False
        self.tracing_enabled = False
        self.metrics_enabled = False
        self.logging_enabled = False

    def initialize(
        self,
        service_name: str = "uatp-capsule-engine",
        service_version: str = "7.1.0",
        deployment_environment: Optional[str] = None,
        enable_tracing: bool = True,
        enable_metrics: bool = True,
        enable_logging: bool = True,
        **kwargs,
    ) -> None:
        """
        Initialize all OpenTelemetry components for UATP
        """
        if self.initialized:
            logger.warning("UATP Observability already initialized")
            return

        # Determine environment
        if deployment_environment is None:
            deployment_environment = os.getenv("DEPLOYMENT_ENVIRONMENT", "development")

        # Get configuration from environment
        config = self._get_configuration()

        try:
            # Initialize logging first (needed for other components)
            if enable_logging:
                uatp_logging.initialize(
                    service_name=service_name,
                    service_version=service_version,
                    deployment_environment=deployment_environment,
                    log_level=config.get("log_level", "INFO"),
                    otlp_endpoint=config.get("otlp_logs_endpoint"),
                    enable_console_output=config.get("enable_console_logging", True),
                    enable_file_output=config.get("enable_file_logging", True),
                    **kwargs.get("logging", {}),
                )
                self.logging_enabled = True
                logger.info("Logging initialized successfully")

            # Initialize tracing
            if enable_tracing:
                uatp_tracing.initialize(
                    service_name=service_name,
                    service_version=service_version,
                    deployment_environment=deployment_environment,
                    otlp_endpoint=config.get("otlp_traces_endpoint"),
                    jaeger_endpoint=config.get("jaeger_endpoint"),
                    enable_console_export=config.get("enable_console_tracing", False),
                    **kwargs.get("tracing", {}),
                )
                self.tracing_enabled = True
                logger.info("Tracing initialized successfully")

            # Initialize metrics
            if enable_metrics:
                uatp_metrics.initialize(
                    service_name=service_name,
                    service_version=service_version,
                    deployment_environment=deployment_environment,
                    otlp_endpoint=config.get("otlp_metrics_endpoint"),
                    prometheus_port=config.get("prometheus_port", 8889),
                    enable_console_export=config.get("enable_console_metrics", False),
                    **kwargs.get("metrics", {}),
                )
                self.metrics_enabled = True
                logger.info("Metrics initialized successfully")

            self.initialized = True
            logger.info(
                f"UATP Observability initialized successfully for {service_name}"
            )

            # Add startup event
            if self.tracing_enabled:
                add_span_event(
                    "uatp.observability.initialized",
                    {
                        "service_name": service_name,
                        "service_version": service_version,
                        "environment": deployment_environment,
                        "tracing_enabled": self.tracing_enabled,
                        "metrics_enabled": self.metrics_enabled,
                        "logging_enabled": self.logging_enabled,
                    },
                )

        except Exception as e:
            logger.error(f"Failed to initialize UATP Observability: {e}")
            raise

    def _get_configuration(self) -> Dict[str, Any]:
        """Get observability configuration from environment variables"""
        return {
            # Endpoints
            "otlp_traces_endpoint": os.getenv(
                "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
                os.getenv(
                    "OTEL_EXPORTER_OTLP_ENDPOINT", "http://uatp-otel-collector:4317"
                ),
            ),
            "otlp_metrics_endpoint": os.getenv(
                "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
                os.getenv(
                    "OTEL_EXPORTER_OTLP_ENDPOINT", "http://uatp-otel-collector:4317"
                ),
            ),
            "otlp_logs_endpoint": os.getenv(
                "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
                os.getenv(
                    "OTEL_EXPORTER_OTLP_ENDPOINT", "http://uatp-otel-collector:4318"
                ),
            ),
            "jaeger_endpoint": os.getenv(
                "JAEGER_ENDPOINT", "http://jaeger-collector:14268/api/traces"
            ),
            # Configuration
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "prometheus_port": int(os.getenv("PROMETHEUS_PORT", "8889")),
            # Feature flags
            "enable_console_logging": os.getenv("OTEL_CONSOLE_LOGGING", "true").lower()
            == "true",
            "enable_file_logging": os.getenv("OTEL_FILE_LOGGING", "true").lower()
            == "true",
            "enable_console_tracing": os.getenv("OTEL_CONSOLE_TRACING", "false").lower()
            == "true",
            "enable_console_metrics": os.getenv("OTEL_CONSOLE_METRICS", "false").lower()
            == "true",
        }

    def shutdown(self) -> None:
        """Shutdown all observability components"""
        if not self.initialized:
            return

        logger.info("Shutting down UATP Observability")

        if self.tracing_enabled:
            uatp_tracing.shutdown()

        if self.metrics_enabled:
            uatp_metrics.shutdown()

        if self.logging_enabled:
            uatp_logging.shutdown()

        self.initialized = False
        logger.info("UATP Observability shutdown completed")

    # Context managers for request/operation tracking
    @asynccontextmanager
    async def trace_request(
        self,
        request_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **attributes,
    ):
        """Context manager for tracing HTTP requests"""
        # Set context
        set_request_context(request_id)
        if user_id:
            set_user_context(user_id)
        if session_id:
            set_session_context(session_id)

        # Add span attributes
        if self.tracing_enabled:
            add_span_attributes(
                request_id=request_id,
                user_id=user_id or "anonymous",
                session_id=session_id or "none",
                **attributes,
            )

        # Track active requests
        if self.metrics_enabled:
            uatp_metrics.increment_active_requests({"request_id": request_id})

        try:
            yield
        finally:
            # Cleanup
            if self.metrics_enabled:
                uatp_metrics.decrement_active_requests({"request_id": request_id})

    @contextmanager
    def trace_operation(self, operation_name: str, **attributes):
        """Context manager for tracing operations"""
        if self.tracing_enabled:
            add_span_event(f"operation.{operation_name}.start", attributes)
            add_span_attributes(operation_name=operation_name, **attributes)

        try:
            yield
            if self.tracing_enabled:
                add_span_event(f"operation.{operation_name}.success")
        except Exception as e:
            if self.tracing_enabled:
                add_span_event(
                    f"operation.{operation_name}.error",
                    {"error_type": type(e).__name__, "error_message": str(e)},
                )
            raise

    # Convenience methods
    def get_logger(self, name: str, **context):
        """Get a logger with observability context"""
        if self.logging_enabled:
            return get_logger(name, **context)
        else:
            return logging.getLogger(name)

    def record_business_event(
        self, event_name: str, event_data: Dict[str, Any]
    ) -> None:
        """Record a business event with full observability"""
        logger = self.get_logger(__name__)

        # Log the event
        logger.info(
            f"Business event: {event_name}",
            extra={
                "event_type": "business_event",
                "event_name": event_name,
                "event_data": event_data,
            },
        )

        # Add trace event
        if self.tracing_enabled:
            add_span_event(f"business.{event_name}", event_data)

        # Record metrics if applicable
        if self.metrics_enabled and "metric_value" in event_data:
            # This is a simplified example - real implementation would be more sophisticated
            pass


# Global observability instance
uatp_observability = UATPObservability()


# Convenience functions for backward compatibility and ease of use
def initialize_uatp_observability(**kwargs) -> None:
    """Initialize UATP observability with default settings"""
    uatp_observability.initialize(**kwargs)


def get_uatp_logger(name: str, **context):
    """Get a UATP logger with observability features"""
    return uatp_observability.get_logger(name, **context)


# Decorators for easy integration
def observe_capsule_operation(operation_type: str):
    """Decorator that combines tracing and metrics for capsule operations"""

    def decorator(func):
        # Apply both tracing and metrics decorators
        traced_func = trace_capsule_operation(
            operation_type, include_payload=True, include_result=True
        )(func)
        monitored_func = track_operation_metrics(f"capsule_{operation_type}")(
            traced_func
        )
        return monitored_func

    return decorator


def observe_attribution_operation(operation_type: str = "attribution_track"):
    """Decorator for attribution operations"""

    def decorator(func):
        traced_func = trace_capsule_operation(operation_type, include_payload=True)(
            func
        )
        monitored_func = track_operation_metrics(operation_type)(traced_func)
        return monitored_func

    return decorator


def observe_economic_operation(operation_type: str = "economic_calculation"):
    """Decorator for economic operations"""

    def decorator(func):
        traced_func = trace_capsule_operation(operation_type, include_result=True)(func)
        monitored_func = track_operation_metrics(operation_type)(traced_func)
        return monitored_func

    return decorator


# Health check integration
def get_observability_health() -> Dict[str, Any]:
    """Get health status of observability components"""
    return {
        "initialized": uatp_observability.initialized,
        "tracing_enabled": uatp_observability.tracing_enabled,
        "metrics_enabled": uatp_observability.metrics_enabled,
        "logging_enabled": uatp_observability.logging_enabled,
        "components": {
            "tracing": uatp_tracing.initialized
            if uatp_observability.tracing_enabled
            else None,
            "metrics": uatp_metrics.initialized
            if uatp_observability.metrics_enabled
            else None,
            "logging": uatp_logging.initialized
            if uatp_observability.logging_enabled
            else None,
        },
    }


# Migration helpers for existing code
class ObservabilityMigrationHelper:
    """Helper class for migrating existing code to use OpenTelemetry"""

    @staticmethod
    def migrate_prometheus_metrics():
        """Helper to identify Prometheus metrics that need migration"""
        # This would scan the codebase and identify Prometheus metrics
        # For now, it's a placeholder for documentation
        pass

    @staticmethod
    def update_logging_calls():
        """Helper to update existing logging calls"""
        # This would help update existing logging calls to use structured logging
        pass

    @staticmethod
    def add_tracing_to_functions():
        """Helper to add tracing to existing functions"""
        # This would help identify functions that should be traced
        pass
