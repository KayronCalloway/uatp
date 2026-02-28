"""
OpenTelemetry Metrics Implementation for UATP
Migrates from legacy Prometheus metrics to modern OpenTelemetry metrics
"""

import os
import time
import logging
from typing import Dict, Any, Optional, Union, List
from contextvars import ContextVar
from functools import wraps

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.metrics import (
    Counter,
    Histogram,
    UpDownCounter,
    Gauge,
    ObservableCounter,
    ObservableGauge,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    ConsoleMetricExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.semantic_conventions.resource import ResourceAttributes

logger = logging.getLogger(__name__)

# Context variables for metric labeling
current_capsule_type: ContextVar[Optional[str]] = ContextVar(
    "current_capsule_type", default=None
)
current_attribution_chain: ContextVar[Optional[str]] = ContextVar(
    "current_attribution_chain", default=None
)


class UATPMetrics:
    """
    UATP-specific OpenTelemetry metrics implementation
    Provides business-specific metrics for capsule operations, attribution tracking, and economics
    """

    def __init__(self):
        self.meter_provider = None
        self.meter = None
        self.initialized = False

        # Core application metrics
        self.request_counter = None
        self.request_duration = None
        self.active_requests = None
        self.error_counter = None

        # UATP-specific metrics
        self.capsule_operations_counter = None
        self.capsule_creation_duration = None
        self.attribution_tracking_counter = None
        self.economic_calculations_counter = None
        self.verification_counter = None
        self.chain_operations_counter = None

        # Business metrics
        self.active_capsules_gauge = None
        self.dividend_calculations_counter = None
        self.governance_votes_counter = None
        self.trust_score_histogram = None

        # Performance metrics
        self.database_operations_counter = None
        self.database_connection_pool = None
        self.cache_operations_counter = None
        self.memory_usage_gauge = None

    def initialize(
        self,
        service_name: str = "uatp-capsule-engine",
        service_version: str = "7.1.0",
        deployment_environment: str = "production",
        otlp_endpoint: str = "http://uatp-otel-collector:4317",
        prometheus_port: int = 8889,
        enable_console_export: bool = False,
    ) -> None:
        """
        Initialize OpenTelemetry metrics with UATP-specific configuration
        """
        if self.initialized:
            logger.warning("Metrics already initialized")
            return

        try:
            # Resource configuration
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
                }
            )

            # Metric readers
            readers = []

            # OTLP Metric Reader for primary backend
            if otlp_endpoint:
                otlp_exporter = OTLPMetricExporter(
                    endpoint=otlp_endpoint, headers=self._get_otlp_headers(), timeout=30
                )
                otlp_reader = PeriodicExportingMetricReader(
                    exporter=otlp_exporter,
                    export_interval_millis=15000,  # 15 seconds
                    export_timeout_millis=30000,  # 30 seconds
                )
                readers.append(otlp_reader)

            # Prometheus Metric Reader for compatibility
            if prometheus_port:
                prometheus_reader = PrometheusMetricReader(port=prometheus_port)
                readers.append(prometheus_reader)

            # Console exporter for development
            if enable_console_export:
                console_reader = PeriodicExportingMetricReader(
                    exporter=ConsoleMetricExporter(), export_interval_millis=30000
                )
                readers.append(console_reader)

            # Initialize MeterProvider
            self.meter_provider = MeterProvider(
                resource=resource, metric_readers=readers
            )
            metrics.set_meter_provider(self.meter_provider)

            # Get meter instance
            self.meter = metrics.get_meter(__name__)

            # Initialize all metrics
            self._initialize_core_metrics()
            self._initialize_uatp_metrics()
            self._initialize_business_metrics()
            self._initialize_performance_metrics()

            self.initialized = True
            logger.info(f"OpenTelemetry metrics initialized for {service_name}")

        except Exception as e:
            logger.error(f"Failed to initialize metrics: {e}")
            raise

    def _get_otlp_headers(self) -> Dict[str, str]:
        """Get headers for OTLP metric exporter"""
        headers = {}

        api_key = os.getenv("OTEL_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        headers.update({"uatp-service": "capsule-engine", "uatp-version": "7.1.0"})

        return headers

    def _initialize_core_metrics(self) -> None:
        """Initialize core application metrics (migrated from Prometheus)"""
        # HTTP request metrics
        self.request_counter = self.meter.create_counter(
            name="uatp_http_requests_total",
            description="Total number of HTTP requests",
            unit="1",
        )

        self.request_duration = self.meter.create_histogram(
            name="uatp_http_request_duration_seconds",
            description="HTTP request duration in seconds",
            unit="s",
        )

        self.active_requests = self.meter.create_up_down_counter(
            name="uatp_http_requests_active",
            description="Number of active HTTP requests",
            unit="1",
        )

        self.error_counter = self.meter.create_counter(
            name="uatp_http_errors_total",
            description="Total number of HTTP errors",
            unit="1",
        )

    def _initialize_uatp_metrics(self) -> None:
        """Initialize UATP-specific capsule and attribution metrics"""
        # Capsule operation metrics
        self.capsule_operations_counter = self.meter.create_counter(
            name="uatp_capsule_operations_total",
            description="Total number of capsule operations",
            unit="1",
        )

        self.capsule_creation_duration = self.meter.create_histogram(
            name="uatp_capsule_creation_duration_seconds",
            description="Time taken to create capsules",
            unit="s",
        )

        # Attribution tracking metrics
        self.attribution_tracking_counter = self.meter.create_counter(
            name="uatp_attribution_tracks_total",
            description="Total number of attribution tracking operations",
            unit="1",
        )

        # Economic calculation metrics
        self.economic_calculations_counter = self.meter.create_counter(
            name="uatp_economic_calculations_total",
            description="Total number of economic calculations",
            unit="1",
        )

        # Verification metrics
        self.verification_counter = self.meter.create_counter(
            name="uatp_verifications_total",
            description="Total number of verification operations",
            unit="1",
        )

        # Chain operation metrics
        self.chain_operations_counter = self.meter.create_counter(
            name="uatp_chain_operations_total",
            description="Total number of chain operations",
            unit="1",
        )

    def _initialize_business_metrics(self) -> None:
        """Initialize business-specific metrics"""
        # Active capsules gauge
        self.active_capsules_gauge = self.meter.create_observable_gauge(
            name="uatp_active_capsules",
            description="Number of active capsules in the system",
            unit="1",
            callbacks=[self._get_active_capsules_count],
        )

        # Dividend calculation metrics
        self.dividend_calculations_counter = self.meter.create_counter(
            name="uatp_dividend_calculations_total",
            description="Total number of dividend calculations",
            unit="1",
        )

        # Governance metrics
        self.governance_votes_counter = self.meter.create_counter(
            name="uatp_governance_votes_total",
            description="Total number of governance votes",
            unit="1",
        )

        # Trust score metrics
        self.trust_score_histogram = self.meter.create_histogram(
            name="uatp_trust_scores",
            description="Distribution of trust scores",
            unit="1",
        )

    def _initialize_performance_metrics(self) -> None:
        """Initialize performance and infrastructure metrics"""
        # Database metrics
        self.database_operations_counter = self.meter.create_counter(
            name="uatp_database_operations_total",
            description="Total number of database operations",
            unit="1",
        )

        self.database_connection_pool = self.meter.create_observable_gauge(
            name="uatp_database_connections_active",
            description="Number of active database connections",
            unit="1",
            callbacks=[self._get_database_connections],
        )

        # Cache metrics
        self.cache_operations_counter = self.meter.create_counter(
            name="uatp_cache_operations_total",
            description="Total number of cache operations",
            unit="1",
        )

        # Memory usage gauge
        self.memory_usage_gauge = self.meter.create_observable_gauge(
            name="uatp_memory_usage_bytes",
            description="Current memory usage in bytes",
            unit="By",
            callbacks=[self._get_memory_usage],
        )

    def _get_active_capsules_count(self, options) -> int:
        """Callback to get active capsules count"""
        try:
            # This would integrate with your actual capsule counting logic
            from src.database.models import Capsule
            from src.database.connection import get_session

            with get_session() as session:
                count = session.query(Capsule).filter(Capsule.active == True).count()
                return count
        except Exception as e:
            logger.warning(f"Failed to get active capsules count: {e}")
            return 0

    def _get_database_connections(self, options) -> int:
        """Callback to get database connection count"""
        try:
            # This would integrate with your database connection pool
            from src.database.connection import get_connection_pool_info

            info = get_connection_pool_info()
            return info.get("active_connections", 0)
        except Exception as e:
            logger.warning(f"Failed to get database connections: {e}")
            return 0

    def _get_memory_usage(self, options) -> int:
        """Callback to get current memory usage"""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return 0

    # Convenience methods for recording metrics
    def record_http_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ) -> None:
        """Record HTTP request metrics"""
        labels = {
            "method": method,
            "endpoint": endpoint,
            "status_code": str(status_code),
        }

        self.request_counter.add(1, labels)
        self.request_duration.record(duration, labels)

        if status_code >= 400:
            self.error_counter.add(1, labels)

    def record_capsule_operation(
        self,
        operation_type: str,
        capsule_type: str,
        success: bool,
        duration: Optional[float] = None,
    ) -> None:
        """Record capsule operation metrics"""
        labels = {
            "operation_type": operation_type,
            "capsule_type": capsule_type,
            "success": str(success).lower(),
        }

        self.capsule_operations_counter.add(1, labels)

        if duration is not None and operation_type == "create":
            self.capsule_creation_duration.record(duration, labels)

    def record_attribution_tracking(self, chain_id: str, success: bool) -> None:
        """Record attribution tracking metrics"""
        labels = {"chain_id": chain_id, "success": str(success).lower()}

        self.attribution_tracking_counter.add(1, labels)

    def record_economic_calculation(self, calculation_type: str, success: bool) -> None:
        """Record economic calculation metrics"""
        labels = {"calculation_type": calculation_type, "success": str(success).lower()}

        self.economic_calculations_counter.add(1, labels)

    def record_verification(self, verification_type: str, result: str) -> None:
        """Record verification metrics"""
        labels = {"verification_type": verification_type, "result": result}

        self.verification_counter.add(1, labels)

    def record_trust_score(self, score: float, entity_type: str) -> None:
        """Record trust score distribution"""
        labels = {"entity_type": entity_type}

        self.trust_score_histogram.record(score, labels)

    def record_database_operation(
        self, operation_type: str, table: str, success: bool
    ) -> None:
        """Record database operation metrics"""
        labels = {
            "operation_type": operation_type,
            "table": table,
            "success": str(success).lower(),
        }

        self.database_operations_counter.add(1, labels)

    def record_cache_operation(
        self, operation_type: str, cache_type: str, hit: bool
    ) -> None:
        """Record cache operation metrics"""
        labels = {
            "operation_type": operation_type,
            "cache_type": cache_type,
            "hit": str(hit).lower(),
        }

        self.cache_operations_counter.add(1, labels)

    def increment_active_requests(
        self, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment active requests counter"""
        self.active_requests.add(1, labels or {})

    def decrement_active_requests(
        self, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Decrement active requests counter"""
        self.active_requests.add(-1, labels or {})

    def shutdown(self) -> None:
        """Shutdown metrics and flush remaining data"""
        if self.meter_provider:
            self.meter_provider.shutdown()
            logger.info("Metrics shutdown completed")


# Global metrics instance
uatp_metrics = UATPMetrics()


def track_operation_metrics(
    operation_type: str, include_duration: bool = True, track_success: bool = True
):
    """
    Decorator for tracking operation metrics
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = False

            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                success = False
                raise
            finally:
                if include_duration:
                    duration = time.time() - start_time
                else:
                    duration = None

                # Extract capsule type from context or arguments
                capsule_type = current_capsule_type.get() or "unknown"

                if operation_type.startswith("capsule"):
                    uatp_metrics.record_capsule_operation(
                        operation_type, capsule_type, success, duration
                    )
                elif operation_type.startswith("attribution"):
                    chain_id = current_attribution_chain.get() or "unknown"
                    uatp_metrics.record_attribution_tracking(chain_id, success)
                elif operation_type.startswith("economic"):
                    uatp_metrics.record_economic_calculation(operation_type, success)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = False

            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                success = False
                raise
            finally:
                if include_duration:
                    duration = time.time() - start_time
                else:
                    duration = None

                capsule_type = current_capsule_type.get() or "unknown"

                if operation_type.startswith("capsule"):
                    uatp_metrics.record_capsule_operation(
                        operation_type, capsule_type, success, duration
                    )
                elif operation_type.startswith("attribution"):
                    chain_id = current_attribution_chain.get() or "unknown"
                    uatp_metrics.record_attribution_tracking(chain_id, success)
                elif operation_type.startswith("economic"):
                    uatp_metrics.record_economic_calculation(operation_type, success)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Convenience decorators for common operations
track_capsule_metrics = track_operation_metrics("capsule_operation")
track_attribution_metrics = track_operation_metrics("attribution_operation")
track_economic_metrics = track_operation_metrics("economic_calculation")
