"""
OpenTelemetry Distributed Tracing Implementation for UATP
Provides comprehensive tracing across all services with correlation
"""

import logging
import os
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Dict, Optional

from opentelemetry import baggage, context, trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
from opentelemetry.propagate import extract, inject
from opentelemetry.sdk.trace import Resource, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.semantic_conventions.resource import ResourceAttributes
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)

# Context variables for distributed tracing
current_capsule_id: ContextVar[Optional[str]] = ContextVar(
    "current_capsule_id", default=None
)
current_chain_id: ContextVar[Optional[str]] = ContextVar(
    "current_chain_id", default=None
)
current_operation_type: ContextVar[Optional[str]] = ContextVar(
    "current_operation_type", default=None
)


class UATPTracing:
    """
    UATP-specific OpenTelemetry tracing implementation with custom business logic
    """

    def __init__(self):
        self.tracer_provider = None
        self.tracer = None
        self.initialized = False

    def initialize(
        self,
        service_name: str = "uatp-capsule-engine",
        service_version: str = "7.1.0",
        deployment_environment: str = "production",
        otlp_endpoint: str = "http://uatp-otel-collector:4317",
        jaeger_endpoint: str = "http://jaeger-collector:14268/api/traces",
        enable_console_export: bool = False,
    ) -> None:
        """
        Initialize OpenTelemetry tracing with UATP-specific configuration
        """
        if self.initialized:
            logger.warning("Tracing already initialized")
            return

        try:
            # Resource configuration with UATP-specific attributes
            resource = Resource.create(
                {
                    ResourceAttributes.SERVICE_NAME: service_name,
                    ResourceAttributes.SERVICE_VERSION: service_version,
                    ResourceAttributes.DEPLOYMENT_ENVIRONMENT: deployment_environment,
                    "uatp.system.type": "capsule-engine",
                    "uatp.attribution.enabled": "true",
                    "k8s.cluster.name": os.getenv(
                        "K8S_CLUSTER_NAME", "uatp-production"
                    ),
                    "k8s.namespace.name": os.getenv("K8S_NAMESPACE", "uatp-prod"),
                    "k8s.pod.name": os.getenv("K8S_POD_NAME", "unknown"),
                    "k8s.node.name": os.getenv("K8S_NODE_NAME", "unknown"),
                }
            )

            # Initialize TracerProvider
            self.tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(self.tracer_provider)

            # OTLP Exporter for primary telemetry backend
            if otlp_endpoint:
                otlp_exporter = OTLPSpanExporter(
                    endpoint=otlp_endpoint, headers=self._get_otlp_headers(), timeout=30
                )
                otlp_processor = BatchSpanProcessor(
                    otlp_exporter,
                    max_queue_size=2048,
                    max_export_batch_size=512,
                    export_timeout_millis=30000,
                    schedule_delay_millis=1000,
                )
                self.tracer_provider.add_span_processor(otlp_processor)

            # Jaeger Exporter for compatibility
            if jaeger_endpoint:
                jaeger_exporter = JaegerExporter(
                    agent_host_name="jaeger-agent",
                    agent_port=6831,
                    collector_endpoint=jaeger_endpoint,
                )
                jaeger_processor = BatchSpanProcessor(jaeger_exporter)
                self.tracer_provider.add_span_processor(jaeger_processor)

            # Console exporter for development
            if enable_console_export:
                console_processor = BatchSpanProcessor(ConsoleSpanExporter())
                self.tracer_provider.add_span_processor(console_processor)

            # Get tracer instance
            self.tracer = trace.get_tracer(__name__)

            # Initialize auto-instrumentation
            self._setup_auto_instrumentation()

            self.initialized = True
            logger.info(f"OpenTelemetry tracing initialized for {service_name}")

        except Exception as e:
            logger.error(f"Failed to initialize tracing: {e}")
            raise

    def _get_otlp_headers(self) -> Dict[str, str]:
        """Get headers for OTLP exporter"""
        headers = {}

        # Add authentication headers if available
        api_key = os.getenv("OTEL_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Add custom headers
        headers.update({"uatp-service": "capsule-engine", "uatp-version": "7.1.0"})

        return headers

    def _setup_auto_instrumentation(self) -> None:
        """Setup automatic instrumentation for common libraries"""
        try:
            # HTTP instrumentation
            RequestsInstrumentor().instrument()
            URLLib3Instrumentor().instrument()

            # Database instrumentation
            SQLAlchemyInstrumentor().instrument()

            # Cache instrumentation
            RedisInstrumentor().instrument()

            # Web framework instrumentation
            FlaskInstrumentor().instrument()

            # Logging instrumentation
            LoggingInstrumentor().instrument(
                set_logging_format=True, log_hook=self._log_hook
            )

            logger.info("Auto-instrumentation setup completed")

        except Exception as e:
            logger.warning(f"Some auto-instrumentation failed: {e}")

    def _log_hook(self, span, record):
        """Custom log hook to add trace context to logs"""
        if span and span.is_recording():
            record.trace_id = format(span.get_span_context().trace_id, "032x")
            record.span_id = format(span.get_span_context().span_id, "016x")

            # Add UATP-specific context
            record.capsule_id = current_capsule_id.get()
            record.chain_id = current_chain_id.get()
            record.operation_type = current_operation_type.get()

    def get_tracer(self) -> trace.Tracer:
        """Get the configured tracer instance"""
        if not self.initialized:
            raise RuntimeError("Tracing not initialized. Call initialize() first.")
        return self.tracer

    def shutdown(self) -> None:
        """Shutdown tracing and flush remaining spans"""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
            logger.info("Tracing shutdown completed")


# Global tracing instance
uatp_tracing = UATPTracing()


def trace_capsule_operation(
    operation_type: str, include_payload: bool = False, include_result: bool = False
):
    """
    Decorator for tracing UATP capsule operations with business context
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = uatp_tracing.get_tracer()

            with tracer.start_as_current_span(
                f"uatp.capsule.{operation_type}", kind=trace.SpanKind.INTERNAL
            ) as span:
                try:
                    # Set operation context
                    current_operation_type.set(operation_type)

                    # Add business-specific attributes
                    span.set_attribute("uatp.operation.type", operation_type)
                    span.set_attribute("uatp.function.name", func.__name__)

                    # Extract capsule and chain context from arguments
                    capsule_id = _extract_capsule_id(args, kwargs)
                    if capsule_id:
                        span.set_attribute("uatp.capsule.id", capsule_id)
                        current_capsule_id.set(capsule_id)

                    chain_id = _extract_chain_id(args, kwargs)
                    if chain_id:
                        span.set_attribute("uatp.chain.id", chain_id)
                        current_chain_id.set(chain_id)

                    # Add payload information if requested
                    if include_payload and args:
                        span.set_attribute("uatp.payload.size", len(str(args[0])))
                        span.set_attribute("uatp.payload.type", type(args[0]).__name__)

                    # Add baggage for downstream services
                    baggage.set_baggage("uatp.operation.type", operation_type)
                    if capsule_id:
                        baggage.set_baggage("uatp.capsule.id", capsule_id)

                    # Execute the function
                    result = await func(*args, **kwargs)

                    # Add result information if requested
                    if include_result and result:
                        span.set_attribute("uatp.result.type", type(result).__name__)
                        if hasattr(result, "id"):
                            span.set_attribute("uatp.result.id", str(result.id))

                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = uatp_tracing.get_tracer()

            with tracer.start_as_current_span(
                f"uatp.capsule.{operation_type}", kind=trace.SpanKind.INTERNAL
            ) as span:
                try:
                    # Same logic as async wrapper but for sync functions
                    current_operation_type.set(operation_type)

                    span.set_attribute("uatp.operation.type", operation_type)
                    span.set_attribute("uatp.function.name", func.__name__)

                    # Extract business context
                    capsule_id = _extract_capsule_id(args, kwargs)
                    if capsule_id:
                        span.set_attribute("uatp.capsule.id", capsule_id)
                        current_capsule_id.set(capsule_id)

                    chain_id = _extract_chain_id(args, kwargs)
                    if chain_id:
                        span.set_attribute("uatp.chain.id", chain_id)
                        current_chain_id.set(chain_id)

                    if include_payload and args:
                        span.set_attribute("uatp.payload.size", len(str(args[0])))

                    baggage.set_baggage("uatp.operation.type", operation_type)
                    if capsule_id:
                        baggage.set_baggage("uatp.capsule.id", capsule_id)

                    result = func(*args, **kwargs)

                    if include_result and result:
                        span.set_attribute("uatp.result.type", type(result).__name__)
                        if hasattr(result, "id"):
                            span.set_attribute("uatp.result.id", str(result.id))

                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def _extract_capsule_id(args: tuple, kwargs: dict) -> Optional[str]:
    """Extract capsule ID from function arguments"""
    # Check kwargs first
    if "capsule_id" in kwargs:
        return str(kwargs["capsule_id"])
    if "capsule" in kwargs and hasattr(kwargs["capsule"], "id"):
        return str(kwargs["capsule"].id)

    # Check positional arguments
    for arg in args:
        if hasattr(arg, "id") and hasattr(arg, "capsule_type"):
            return str(arg.id)
        if isinstance(arg, dict) and "capsule_id" in arg:
            return str(arg["capsule_id"])

    return None


def _extract_chain_id(args: tuple, kwargs: dict) -> Optional[str]:
    """Extract chain ID from function arguments"""
    # Check kwargs first
    if "chain_id" in kwargs:
        return str(kwargs["chain_id"])
    if "chain" in kwargs and hasattr(kwargs["chain"], "id"):
        return str(kwargs["chain"].id)

    # Check positional arguments
    for arg in args:
        if hasattr(arg, "chain_id"):
            return str(arg.chain_id)
        if isinstance(arg, dict) and "chain_id" in arg:
            return str(arg["chain_id"])

    return None


def add_span_attributes(**attributes: Any) -> None:
    """Add custom attributes to the current span"""
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, str(value))


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """Add an event to the current span"""
    span = trace.get_current_span()
    if span and span.is_recording():
        span.add_event(name, attributes or {})


def get_trace_context() -> Dict[str, str]:
    """Get the current trace context for propagation"""
    carrier = {}
    inject(carrier)
    return carrier


def set_trace_context(carrier: Dict[str, str]) -> None:
    """Set trace context from propagated headers"""
    ctx = extract(carrier)
    context.attach(ctx)


# Convenience functions for common UATP operations
trace_capsule_create = trace_capsule_operation(
    "create", include_payload=True, include_result=True
)
trace_capsule_merge = trace_capsule_operation(
    "merge", include_payload=True, include_result=True
)
trace_attribution_track = trace_capsule_operation(
    "attribution_track", include_payload=True
)
trace_economics_calculate = trace_capsule_operation(
    "economics_calculate", include_result=True
)
trace_verification_check = trace_capsule_operation(
    "verification_check", include_result=True
)
