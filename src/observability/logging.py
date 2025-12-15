"""
Structured Logging with OpenTelemetry Integration for UATP
Provides correlated logs with traces and metrics for comprehensive observability
"""

import json
import logging
import os
import sys
from contextvars import ContextVar
from typing import Any, Dict, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semantic_conventions.resource import ResourceAttributes

from src.utils.timezone_utils import utc_now

# Context variables for structured logging
current_user_id: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)
current_session_id: ContextVar[Optional[str]] = ContextVar(
    "current_session_id", default=None
)
current_request_id: ContextVar[Optional[str]] = ContextVar(
    "current_request_id", default=None
)


class UATPStructuredFormatter(logging.Formatter):
    """
    Custom formatter for UATP structured logging with OpenTelemetry trace correlation
    """

    def __init__(
        self, include_trace_info: bool = True, include_business_context: bool = True
    ):
        super().__init__()
        self.include_trace_info = include_trace_info
        self.include_business_context = include_business_context

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON with trace correlation"""
        # Base log structure
        log_entry = {
            "timestamp": utc_now().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add process information
        log_entry.update(
            {"process": {"pid": os.getpid(), "name": "uatp-capsule-engine"}}
        )

        # Add Kubernetes context if available
        if os.getenv("K8S_POD_NAME"):
            log_entry["kubernetes"] = {
                "pod_name": os.getenv("K8S_POD_NAME"),
                "namespace": os.getenv("K8S_NAMESPACE"),
                "node_name": os.getenv("K8S_NODE_NAME"),
                "cluster_name": os.getenv("K8S_CLUSTER_NAME"),
            }

        # Add OpenTelemetry trace correlation
        if self.include_trace_info:
            span = trace.get_current_span()
            if span and span.is_recording():
                span_context = span.get_span_context()
                log_entry["trace"] = {
                    "trace_id": format(span_context.trace_id, "032x"),
                    "span_id": format(span_context.span_id, "016x"),
                    "trace_flags": span_context.trace_flags,
                }

        # Add business context from context variables
        if self.include_business_context:
            business_context = {}

            # User context
            user_id = current_user_id.get()
            if user_id:
                business_context["user_id"] = user_id

            # Session context
            session_id = current_session_id.get()
            if session_id:
                business_context["session_id"] = session_id

            # Request context
            request_id = current_request_id.get()
            if request_id:
                business_context["request_id"] = request_id

            # UATP-specific context from trace context variables
            from .tracing import (
                current_capsule_id,
                current_chain_id,
                current_operation_type,
            )

            capsule_id = current_capsule_id.get()
            if capsule_id:
                business_context["capsule_id"] = capsule_id

            chain_id = current_chain_id.get()
            if chain_id:
                business_context["chain_id"] = chain_id

            operation_type = current_operation_type.get()
            if operation_type:
                business_context["operation_type"] = operation_type

            if business_context:
                log_entry["business"] = business_context

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
                if record.exc_info
                else None,
            }

        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
            ]:
                extra_fields[key] = value

        if extra_fields:
            log_entry["extra"] = extra_fields

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class UATPLogging:
    """
    UATP-specific structured logging implementation with OpenTelemetry integration
    """

    def __init__(self):
        self.logger_provider = None
        self.initialized = False
        self.root_logger = None

    def initialize(
        self,
        service_name: str = "uatp-capsule-engine",
        service_version: str = "7.0.0",
        deployment_environment: str = "production",
        log_level: str = "INFO",
        otlp_endpoint: Optional[str] = "http://uatp-otel-collector:4318",
        enable_console_output: bool = True,
        enable_file_output: bool = True,
        log_file_path: str = "/var/log/uatp/application.log",
    ) -> None:
        """
        Initialize structured logging with OpenTelemetry integration
        """
        if self.initialized:
            logging.warning("Logging already initialized")
            return

        try:
            # Resource configuration
            resource = Resource.create(
                {
                    ResourceAttributes.SERVICE_NAME: service_name,
                    ResourceAttributes.SERVICE_VERSION: service_version,
                    ResourceAttributes.DEPLOYMENT_ENVIRONMENT: deployment_environment,
                    "uatp.system.type": "capsule-engine",
                    "k8s.cluster.name": os.getenv(
                        "K8S_CLUSTER_NAME", "uatp-production"
                    ),
                    "k8s.namespace.name": os.getenv("K8S_NAMESPACE", "uatp-prod"),
                }
            )

            # Initialize LoggerProvider for OpenTelemetry
            self.logger_provider = LoggerProvider(resource=resource)

            # OTLP Log Exporter
            if otlp_endpoint:
                otlp_exporter = OTLPLogExporter(
                    endpoint=otlp_endpoint, headers=self._get_otlp_headers(), timeout=30
                )
                log_processor = BatchLogRecordProcessor(otlp_exporter)
                self.logger_provider.add_log_record_processor(log_processor)

            # Configure root logger
            self.root_logger = logging.getLogger()
            self.root_logger.setLevel(getattr(logging, log_level.upper()))

            # Clear existing handlers
            self.root_logger.handlers.clear()

            # Console handler with structured formatting
            if enable_console_output:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(UATPStructuredFormatter())
                self.root_logger.addHandler(console_handler)

            # File handler with structured formatting
            if enable_file_output:
                try:
                    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
                    file_handler = logging.FileHandler(log_file_path)
                    file_handler.setFormatter(UATPStructuredFormatter())
                    self.root_logger.addHandler(file_handler)
                except Exception as e:
                    logging.warning(f"Failed to setup file logging: {e}")

            # OpenTelemetry logging handler
            if self.logger_provider:
                otel_handler = LoggingHandler(
                    logger_provider=self.logger_provider,
                    level=getattr(logging, log_level.upper()),
                )
                self.root_logger.addHandler(otel_handler)

            # Configure specific loggers
            self._configure_library_loggers()

            self.initialized = True
            logging.info(f"Structured logging initialized for {service_name}")

        except Exception as e:
            logging.error(f"Failed to initialize logging: {e}")
            raise

    def _get_otlp_headers(self) -> Dict[str, str]:
        """Get headers for OTLP log exporter"""
        headers = {}

        api_key = os.getenv("OTEL_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        headers.update({"uatp-service": "capsule-engine", "uatp-version": "7.0.0"})

        return headers

    def _configure_library_loggers(self) -> None:
        """Configure logging levels for third-party libraries"""
        # Reduce noise from third-party libraries
        library_loggers = {
            "urllib3": logging.WARNING,
            "requests": logging.WARNING,
            "opentelemetry": logging.WARNING,
            "sqlalchemy.engine": logging.WARNING,
            "sqlalchemy.pool": logging.WARNING,
            "aioprometheus": logging.WARNING,
        }

        for logger_name, level in library_loggers.items():
            logging.getLogger(logger_name).setLevel(level)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance with structured formatting"""
        if not self.initialized:
            raise RuntimeError("Logging not initialized. Call initialize() first.")
        return logging.getLogger(name)

    def shutdown(self) -> None:
        """Shutdown logging and flush remaining logs"""
        if self.logger_provider:
            self.logger_provider.shutdown()
            logging.info("Logging shutdown completed")


# Global logging instance
uatp_logging = UATPLogging()


class UATPLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that automatically adds UATP-specific context to log records
    """

    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        super().__init__(logger, extra or {})

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process the logging call to add context information"""
        # Add current context to extra fields
        extra = kwargs.get("extra", {})

        # Add trace context
        span = trace.get_current_span()
        if span and span.is_recording():
            span_context = span.get_span_context()
            extra.update(
                {
                    "trace_id": format(span_context.trace_id, "032x"),
                    "span_id": format(span_context.span_id, "016x"),
                }
            )

        # Add business context
        user_id = current_user_id.get()
        if user_id:
            extra["user_id"] = user_id

        session_id = current_session_id.get()
        if session_id:
            extra["session_id"] = session_id

        request_id = current_request_id.get()
        if request_id:
            extra["request_id"] = request_id

        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(name: str, **context) -> UATPLoggerAdapter:
    """
    Get a UATP logger with automatic context injection

    Args:
        name: Logger name (usually __name__)
        **context: Additional context to include in all log messages

    Returns:
        Logger adapter with UATP-specific enhancements
    """
    base_logger = uatp_logging.get_logger(name)
    return UATPLoggerAdapter(base_logger, context)


def set_user_context(user_id: str) -> None:
    """Set user context for current execution"""
    current_user_id.set(user_id)


def set_session_context(session_id: str) -> None:
    """Set session context for current execution"""
    current_session_id.set(session_id)


def set_request_context(request_id: str) -> None:
    """Set request context for current execution"""
    current_request_id.set(request_id)


def clear_context() -> None:
    """Clear all context variables"""
    current_user_id.set(None)
    current_session_id.set(None)
    current_request_id.set(None)


# Structured logging functions for common UATP operations
def log_capsule_operation(
    logger: logging.Logger, operation: str, capsule_id: str, success: bool, **extra
) -> None:
    """Log capsule operation with structured context"""
    logger.info(
        f"Capsule operation: {operation}",
        extra={
            "operation_type": "capsule_operation",
            "operation": operation,
            "capsule_id": capsule_id,
            "success": success,
            **extra,
        },
    )


def log_attribution_event(
    logger: logging.Logger, event_type: str, chain_id: str, details: Dict[str, Any]
) -> None:
    """Log attribution tracking event with structured context"""
    logger.info(
        f"Attribution event: {event_type}",
        extra={
            "operation_type": "attribution_tracking",
            "event_type": event_type,
            "chain_id": chain_id,
            "details": details,
        },
    )


def log_economic_calculation(
    logger: logging.Logger, calculation_type: str, amount: float, currency: str, **extra
) -> None:
    """Log economic calculation with structured context"""
    logger.info(
        f"Economic calculation: {calculation_type}",
        extra={
            "operation_type": "economic_calculation",
            "calculation_type": calculation_type,
            "amount": amount,
            "currency": currency,
            **extra,
        },
    )


def log_security_event(
    logger: logging.Logger, event_type: str, severity: str, details: Dict[str, Any]
) -> None:
    """Log security event with structured context"""
    level = getattr(logging, severity.upper(), logging.INFO)
    logger.log(
        level,
        f"Security event: {event_type}",
        extra={
            "operation_type": "security_event",
            "event_type": event_type,
            "severity": severity,
            "details": details,
        },
    )


def log_performance_metrics(
    logger: logging.Logger, operation: str, duration: float, success: bool, **metrics
) -> None:
    """Log performance metrics with structured context"""
    logger.info(
        f"Performance metrics for {operation}",
        extra={
            "operation_type": "performance_metrics",
            "operation": operation,
            "duration_seconds": duration,
            "success": success,
            "metrics": metrics,
        },
    )


# Context manager for automatic request logging
class LogRequestContext:
    """Context manager for automatic request logging with correlation"""

    def __init__(
        self,
        logger: logging.Logger,
        request_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        self.logger = logger
        self.request_id = request_id
        self.user_id = user_id
        self.session_id = session_id
        self.start_time = None

    def __enter__(self):
        self.start_time = utc_now()

        # Set context variables
        set_request_context(self.request_id)
        if self.user_id:
            set_user_context(self.user_id)
        if self.session_id:
            set_session_context(self.session_id)

        self.logger.info(
            "Request started",
            extra={
                "operation_type": "request_lifecycle",
                "event": "request_start",
                "request_id": self.request_id,
            },
        )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (utc_now() - self.start_time).total_seconds()
        success = exc_type is None

        self.logger.info(
            "Request completed",
            extra={
                "operation_type": "request_lifecycle",
                "event": "request_end",
                "request_id": self.request_id,
                "duration_seconds": duration,
                "success": success,
                "exception_type": exc_type.__name__ if exc_type else None,
            },
        )

        # Clear context
        clear_context()
