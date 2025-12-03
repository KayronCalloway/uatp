#!/usr/bin/env python3
"""
UATP Observability System
Implements OpenTelemetry metrics, tracing, and Prometheus integration.
"""

import logging
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# OpenTelemetry imports
try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.semantic_conventions.resource import ResourceAttributes
    from opentelemetry.util.http import get_excluded_urls

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

# Prometheus client imports
try:
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        start_http_server,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics we track."""

    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"
    SUMMARY = "summary"


class FallbackMetric:
    """Simple fallback metric for when Prometheus is not available."""

    def __init__(self, name: str, metric_type: MetricType):
        self.name = name
        self.metric_type = metric_type
        self.value = 0.0
        self.observations = []
        self.labels_values = {}

    def inc(self, value: float = 1.0):
        """Increment counter."""
        self.value += value

    def observe(self, value: float):
        """Record histogram observation."""
        self.observations.append(value)
        if len(self.observations) > 1000:  # Keep only last 1000 observations
            self.observations = self.observations[-1000:]

    def set(self, value: float):
        """Set gauge value."""
        self.value = value

    def labels(self, **kwargs):
        """Return labeled version of metric."""
        return LabeledFallbackMetric(self, kwargs)


class LabeledFallbackMetric:
    """Labeled version of fallback metric."""

    def __init__(self, metric: FallbackMetric, labels: Dict[str, str]):
        self.metric = metric
        self.labels = labels
        self.label_key = str(sorted(labels.items()))

        if self.label_key not in metric.labels_values:
            metric.labels_values[self.label_key] = {
                "value": 0.0,
                "observations": [],
                "labels": labels,
            }

    def inc(self, value: float = 1.0):
        """Increment counter."""
        self.metric.labels_values[self.label_key]["value"] += value

    def observe(self, value: float):
        """Record histogram observation."""
        obs = self.metric.labels_values[self.label_key]["observations"]
        obs.append(value)
        if len(obs) > 1000:
            self.metric.labels_values[self.label_key]["observations"] = obs[-1000:]

    def set(self, value: float):
        """Set gauge value."""
        self.metric.labels_values[self.label_key]["value"] = value


@dataclass
class MetricDefinition:
    """Definition of a metric."""

    name: str
    description: str
    metric_type: MetricType
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # For histograms


@dataclass
class TraceEvent:
    """Represents a trace event."""

    name: str
    timestamp: datetime
    duration_ms: float
    attributes: Dict[str, Any] = field(default_factory=dict)
    span_id: str = ""
    trace_id: str = ""


class TelemetryCollector:
    """Collects telemetry data with fallback for missing dependencies."""

    def __init__(self, service_name: str = "uatp-capsule-engine"):
        self.service_name = service_name
        self.enabled = OTEL_AVAILABLE or PROMETHEUS_AVAILABLE

        # Initialize metrics storage
        self.metrics: Dict[str, Any] = {}
        self.traces: List[TraceEvent] = []

        # Initialize OpenTelemetry if available
        if OTEL_AVAILABLE:
            self._setup_opentelemetry()
        else:
            self.tracer = None
            self.meter = None

        # Initialize Prometheus if available
        if PROMETHEUS_AVAILABLE:
            self._setup_prometheus()
        else:
            self.prometheus_registry = None

        # Define standard metrics
        self._define_standard_metrics()

        logger.info(
            f"Telemetry collector initialized (OpenTelemetry: {OTEL_AVAILABLE}, Prometheus: {PROMETHEUS_AVAILABLE})"
        )

    def _setup_opentelemetry(self):
        """Set up OpenTelemetry tracing and metrics."""
        try:
            # Create resource
            resource = Resource.create(
                {
                    ResourceAttributes.SERVICE_NAME: self.service_name,
                    ResourceAttributes.SERVICE_VERSION: "1.0.0",
                    ResourceAttributes.SERVICE_NAMESPACE: "uatp",
                }
            )

            # Set up tracing
            tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(tracer_provider)

            # Add Jaeger exporter if configured
            jaeger_endpoint = os.getenv("JAEGER_ENDPOINT")
            if jaeger_endpoint:
                jaeger_exporter = JaegerExporter(
                    agent_host_name=jaeger_endpoint,
                    agent_port=14268,
                )
                tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

            # Set up metrics
            metric_reader = PrometheusMetricReader()
            meter_provider = MeterProvider(
                resource=resource, metric_readers=[metric_reader]
            )
            metrics.set_meter_provider(meter_provider)

            # Get tracer and meter
            self.tracer = trace.get_tracer(__name__)
            self.meter = metrics.get_meter(__name__)

            # Instrument popular libraries
            RequestsInstrumentor().instrument()
            LoggingInstrumentor().instrument()

        except Exception as e:
            logger.error(f"Failed to setup OpenTelemetry: {e}")
            self.tracer = None
            self.meter = None

    def _setup_prometheus(self):
        """Set up Prometheus metrics."""
        try:
            # Create custom registry
            self.prometheus_registry = CollectorRegistry()

            # Start Prometheus metrics server
            prometheus_port = int(os.getenv("PROMETHEUS_PORT", "8000"))
            start_http_server(prometheus_port, registry=self.prometheus_registry)

            logger.info(f"Prometheus metrics server started on port {prometheus_port}")

        except Exception as e:
            logger.error(f"Failed to setup Prometheus: {e}")
            self.prometheus_registry = None

    def _define_standard_metrics(self):
        """Define standard UATP metrics."""
        standard_metrics = [
            MetricDefinition(
                name="uatp_capsules_created_total",
                description="Total number of capsules created",
                metric_type=MetricType.COUNTER,
                labels=["capsule_type", "status"],
            ),
            MetricDefinition(
                name="uatp_capsule_creation_duration_seconds",
                description="Time taken to create a capsule",
                metric_type=MetricType.HISTOGRAM,
                labels=["capsule_type"],
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            ),
            MetricDefinition(
                name="uatp_api_requests_total",
                description="Total API requests",
                metric_type=MetricType.COUNTER,
                labels=["method", "endpoint", "status_code"],
            ),
            MetricDefinition(
                name="uatp_api_request_duration_seconds",
                description="API request duration",
                metric_type=MetricType.HISTOGRAM,
                labels=["method", "endpoint"],
                buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            ),
            MetricDefinition(
                name="uatp_ethics_evaluations_total",
                description="Total ethics evaluations",
                metric_type=MetricType.COUNTER,
                labels=["result", "severity"],
            ),
            MetricDefinition(
                name="uatp_ethics_refusals_total",
                description="Total ethics refusals",
                metric_type=MetricType.COUNTER,
                labels=["reason", "severity"],
            ),
            MetricDefinition(
                name="uatp_llm_requests_total",
                description="Total LLM requests",
                metric_type=MetricType.COUNTER,
                labels=["provider", "model", "status"],
            ),
            MetricDefinition(
                name="uatp_llm_request_duration_seconds",
                description="LLM request duration",
                metric_type=MetricType.HISTOGRAM,
                labels=["provider", "model"],
                buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0],
            ),
            MetricDefinition(
                name="uatp_llm_tokens_total",
                description="Total LLM tokens used",
                metric_type=MetricType.COUNTER,
                labels=["provider", "model", "type"],
            ),
            MetricDefinition(
                name="uatp_llm_cost_total",
                description="Total LLM cost in USD",
                metric_type=MetricType.COUNTER,
                labels=["provider", "model"],
            ),
            MetricDefinition(
                name="uatp_system_health",
                description="System health status (1=healthy, 0=unhealthy)",
                metric_type=MetricType.GAUGE,
                labels=["component"],
            ),
            MetricDefinition(
                name="uatp_active_connections",
                description="Number of active connections",
                metric_type=MetricType.GAUGE,
                labels=["type"],
            ),
        ]

        # Create metrics
        for metric_def in standard_metrics:
            self._create_metric(metric_def)

    def _create_metric(self, metric_def: MetricDefinition):
        """Create a metric based on definition."""
        try:
            if PROMETHEUS_AVAILABLE:
                if metric_def.metric_type == MetricType.COUNTER:
                    metric = Counter(
                        metric_def.name,
                        metric_def.description,
                        metric_def.labels,
                        registry=self.prometheus_registry,
                    )
                elif metric_def.metric_type == MetricType.HISTOGRAM:
                    metric = Histogram(
                        metric_def.name,
                        metric_def.description,
                        metric_def.labels,
                        buckets=metric_def.buckets,
                        registry=self.prometheus_registry,
                    )
                elif metric_def.metric_type == MetricType.GAUGE:
                    metric = Gauge(
                        metric_def.name,
                        metric_def.description,
                        metric_def.labels,
                        registry=self.prometheus_registry,
                    )

                self.metrics[metric_def.name] = metric
                logger.debug(f"Created metric: {metric_def.name}")
            else:
                # Fallback: Create simple in-memory metric
                metric = FallbackMetric(metric_def.name, metric_def.metric_type)
                self.metrics[metric_def.name] = metric
                logger.debug(f"Created fallback metric: {metric_def.name}")

        except Exception as e:
            logger.error(f"Failed to create metric {metric_def.name}: {e}")

    def increment_counter(
        self,
        metric_name: str,
        labels: Optional[Dict[str, str]] = None,
        value: float = 1.0,
    ):
        """Increment a counter metric."""
        try:
            if metric_name in self.metrics:
                if labels:
                    self.metrics[metric_name].labels(**labels).inc(value)
                else:
                    self.metrics[metric_name].inc(value)
            else:
                logger.warning(f"Metric {metric_name} not found")
        except Exception as e:
            logger.error(f"Failed to increment counter {metric_name}: {e}")

    def observe_histogram(
        self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Record a histogram observation."""
        try:
            if metric_name in self.metrics:
                if labels:
                    self.metrics[metric_name].labels(**labels).observe(value)
                else:
                    self.metrics[metric_name].observe(value)
            else:
                logger.warning(f"Metric {metric_name} not found")
        except Exception as e:
            logger.error(f"Failed to observe histogram {metric_name}: {e}")

    def set_gauge(
        self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Set a gauge metric value."""
        try:
            if metric_name in self.metrics:
                if labels:
                    self.metrics[metric_name].labels(**labels).set(value)
                else:
                    self.metrics[metric_name].set(value)
            else:
                logger.warning(f"Metric {metric_name} not found")
        except Exception as e:
            logger.error(f"Failed to set gauge {metric_name}: {e}")

    @contextmanager
    def trace_operation(
        self, operation_name: str, attributes: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracing operations."""
        start_time = time.time()
        span_id = f"span_{int(time.time() * 1000)}"
        trace_id = f"trace_{int(time.time() * 1000)}"

        try:
            # Start OpenTelemetry span if available
            if self.tracer:
                with self.tracer.start_as_current_span(operation_name) as span:
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)

                    yield span
            else:
                yield None

        except Exception as e:
            logger.error(f"Error in traced operation {operation_name}: {e}")
            raise

        finally:
            # Record trace event
            duration_ms = (time.time() - start_time) * 1000
            trace_event = TraceEvent(
                name=operation_name,
                timestamp=datetime.now(timezone.utc),
                duration_ms=duration_ms,
                attributes=attributes or {},
                span_id=span_id,
                trace_id=trace_id,
            )
            self.traces.append(trace_event)

            # Keep only last 1000 traces
            if len(self.traces) > 1000:
                self.traces = self.traces[-1000:]

    def record_capsule_creation(
        self, capsule_type: str, status: str, duration_seconds: float
    ):
        """Record capsule creation metrics."""
        self.increment_counter(
            "uatp_capsules_created_total",
            {"capsule_type": capsule_type, "status": status},
        )
        self.observe_histogram(
            "uatp_capsule_creation_duration_seconds",
            duration_seconds,
            {"capsule_type": capsule_type},
        )

    def record_api_request(
        self, method: str, endpoint: str, status_code: int, duration_seconds: float
    ):
        """Record API request metrics."""
        self.increment_counter(
            "uatp_api_requests_total",
            {"method": method, "endpoint": endpoint, "status_code": str(status_code)},
        )
        self.observe_histogram(
            "uatp_api_request_duration_seconds",
            duration_seconds,
            {"method": method, "endpoint": endpoint},
        )

    def record_ethics_evaluation(self, result: str, severity: str):
        """Record ethics evaluation metrics."""
        self.increment_counter(
            "uatp_ethics_evaluations_total", {"result": result, "severity": severity}
        )

        if result == "refused":
            self.increment_counter(
                "uatp_ethics_refusals_total",
                {"reason": "ethical_violation", "severity": severity},
            )

    def record_llm_request(
        self,
        provider: str,
        model: str,
        status: str,
        duration_seconds: float,
        tokens_used: int,
        cost_usd: float,
    ):
        """Record LLM request metrics."""
        self.increment_counter(
            "uatp_llm_requests_total",
            {"provider": provider, "model": model, "status": status},
        )
        self.observe_histogram(
            "uatp_llm_request_duration_seconds",
            duration_seconds,
            {"provider": provider, "model": model},
        )
        self.increment_counter(
            "uatp_llm_tokens_total",
            {"provider": provider, "model": model, "type": "total"},
            tokens_used,
        )
        self.increment_counter(
            "uatp_llm_cost_total", {"provider": provider, "model": model}, cost_usd
        )

    def set_system_health(self, component: str, healthy: bool):
        """Set system health status."""
        self.set_gauge(
            "uatp_system_health", 1.0 if healthy else 0.0, {"component": component}
        )

    def set_active_connections(self, connection_type: str, count: int):
        """Set active connection count."""
        self.set_gauge(
            "uatp_active_connections", float(count), {"type": connection_type}
        )

    def get_recent_traces(self, limit: int = 100) -> List[TraceEvent]:
        """Get recent trace events."""
        return self.traces[-limit:]

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of metrics."""
        summary = {
            "total_metrics": len(self.metrics),
            "total_traces": len(self.traces),
            "opentelemetry_enabled": OTEL_AVAILABLE,
            "prometheus_enabled": PROMETHEUS_AVAILABLE,
            "service_name": self.service_name,
            "recent_traces": len(self.traces),
        }

        # Add metrics data if using fallback system
        if not PROMETHEUS_AVAILABLE:
            summary["fallback_metrics"] = {}
            for name, metric in self.metrics.items():
                if isinstance(metric, FallbackMetric):
                    summary["fallback_metrics"][name] = {
                        "type": metric.metric_type.value,
                        "value": metric.value,
                        "observations_count": len(metric.observations),
                        "labels_count": len(metric.labels_values),
                    }

        return summary

    def get_metric_data(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed data for a specific metric."""
        if metric_name not in self.metrics:
            return None

        metric = self.metrics[metric_name]
        if isinstance(metric, FallbackMetric):
            return {
                "name": metric.name,
                "type": metric.metric_type.value,
                "value": metric.value,
                "observations": metric.observations[-10:],  # Last 10 observations
                "labels": {key: data for key, data in metric.labels_values.items()},
            }

        return {"name": metric_name, "type": "prometheus_metric"}


# Global telemetry collector instance
telemetry = TelemetryCollector()


class TelemetryMiddleware:
    """Middleware for automatic telemetry collection."""

    def __init__(self, collector: TelemetryCollector):
        self.collector = collector

    def __call__(self, func):
        """Decorator for automatic telemetry collection."""

        def wrapper(*args, **kwargs):
            operation_name = f"{func.__module__}.{func.__name__}"

            with self.collector.trace_operation(operation_name):
                return func(*args, **kwargs)

        return wrapper


# Convenience decorators
def trace_operation(operation_name: Optional[str] = None):
    """Decorator for tracing operations."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            with telemetry.trace_operation(op_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def time_operation(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator for timing operations."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                telemetry.observe_histogram(metric_name, duration, labels)

        return wrapper

    return decorator


# Example usage and testing
if __name__ == "__main__":

    def test_telemetry():
        """Test the telemetry system."""
        print("📊 UATP Telemetry System Test")
        print("=" * 40)

        # Test basic metrics
        print("Testing basic metrics...")
        telemetry.record_capsule_creation("reasoning", "success", 1.5)
        telemetry.record_api_request("POST", "/api/capsules", 200, 0.1)
        telemetry.record_ethics_evaluation("allowed", "low")
        telemetry.record_llm_request("openai", "gpt-4", "success", 2.0, 150, 0.003)

        # Test tracing
        print("\nTesting tracing...")
        with telemetry.trace_operation("test_operation", {"test": "value"}):
            time.sleep(0.1)

        # Test system health
        print("\nTesting system health...")
        telemetry.set_system_health("database", True)
        telemetry.set_system_health("api", True)
        telemetry.set_active_connections("http", 5)

        # Get metrics summary
        summary = telemetry.get_metrics_summary()
        print("\n📈 Metrics Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")

        # Get recent traces
        traces = telemetry.get_recent_traces(5)
        print(f"\n🔍 Recent Traces ({len(traces)}):")
        for trace in traces:
            print(f"  {trace.name}: {trace.duration_ms:.2f}ms")

        print("\n✅ Telemetry system test complete!")

        if PROMETHEUS_AVAILABLE:
            print("\n🔧 Prometheus metrics available at: http://localhost:8000/metrics")
        else:
            print("\n📈 Sample metric data:")
            metric_data = telemetry.get_metric_data("uatp_capsules_created_total")
            if metric_data:
                print(f"  {metric_data['name']}: {metric_data['value']}")

        if OTEL_AVAILABLE:
            print("📡 OpenTelemetry tracing enabled")
        else:
            print("📡 Using fallback tracing (OpenTelemetry not available)")

    test_telemetry()
