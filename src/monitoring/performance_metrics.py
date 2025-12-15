"""
Comprehensive Performance Monitoring System
==========================================

Production-grade performance monitoring with:
- API response time percentiles (P50, P95, P99)
- Database query performance and slow query detection
- Cache hit rates and invalidation patterns
- Connection pool utilization and health
- Memory usage and garbage collection performance
- Error rates and failure patterns
- Real-time metrics collection and alerting
"""

import asyncio
import gc
import logging
import resource
import sys
import time
import weakref
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, DefaultDict, Dict, List, Optional

import prometheus_client
import psutil
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric type enumeration."""

    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"
    SUMMARY = "summary"


@dataclass
class AlertRule:
    """Alert rule configuration."""

    name: str
    metric_name: str
    threshold: float
    operator: str  # 'gt', 'lt', 'eq', 'gte', 'lte'
    window_seconds: int = 300  # 5 minutes default
    cooldown_seconds: int = 900  # 15 minutes cooldown
    severity: str = "warning"  # 'warning', 'critical'
    callback: Optional[Callable] = None
    last_triggered: Optional[datetime] = None
    active: bool = True


@dataclass
class SystemMetrics:
    """System-level performance metrics."""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    load_average_1m: float
    load_average_5m: float
    load_average_15m: float
    open_files: int
    active_threads: int


@dataclass
class ApplicationMetrics:
    """Application-level performance metrics."""

    timestamp: datetime
    active_connections: int
    connection_pool_utilization: float
    request_rate_per_second: float
    error_rate_percent: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    cache_hit_rate_percent: float
    database_query_rate: float
    slow_query_count: int
    gc_collections: int
    gc_time_ms: float
    heap_size_mb: float


class PerformanceMetricsCollector:
    """Comprehensive performance metrics collection system."""

    def __init__(self, collection_interval: int = 30):
        self.collection_interval = collection_interval
        self.enabled = True

        # Prometheus metrics registry
        self.registry = CollectorRegistry()

        # Core metrics
        self.request_duration = Histogram(
            "uatp_request_duration_seconds",
            "Request duration in seconds",
            ["method", "endpoint", "status"],
            registry=self.registry,
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        )

        self.request_count = Counter(
            "uatp_requests_total",
            "Total requests",
            ["method", "endpoint", "status"],
            registry=self.registry,
        )

        self.database_query_duration = Histogram(
            "uatp_database_query_duration_seconds",
            "Database query duration in seconds",
            ["query_type", "table"],
            registry=self.registry,
            buckets=(0.001, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
        )

        self.database_connections_active = Gauge(
            "uatp_database_connections_active",
            "Active database connections",
            registry=self.registry,
        )

        self.cache_operations = Counter(
            "uatp_cache_operations_total",
            "Cache operations",
            ["operation", "layer", "result"],
            registry=self.registry,
        )

        self.cache_hit_rate = Gauge(
            "uatp_cache_hit_rate",
            "Cache hit rate percentage",
            ["layer"],
            registry=self.registry,
        )

        self.memory_usage = Gauge(
            "uatp_memory_usage_bytes",
            "Memory usage in bytes",
            ["type"],
            registry=self.registry,
        )

        self.cpu_usage = Gauge(
            "uatp_cpu_usage_percent", "CPU usage percentage", registry=self.registry
        )

        self.error_count = Counter(
            "uatp_errors_total",
            "Total errors",
            ["error_type", "component"],
            registry=self.registry,
        )

        # Time series data storage (for alerting and analysis)
        self.metrics_history: DefaultDict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.response_times: deque = deque(maxlen=1000)
        self.system_metrics_history: deque = deque(maxlen=100)
        self.app_metrics_history: deque = deque(maxlen=100)

        # Alert system
        self.alert_rules: List[AlertRule] = []
        self.alert_callbacks: List[Callable] = []

        # Background tasks
        self._collection_task: Optional[asyncio.Task] = None
        self._alert_task: Optional[asyncio.Task] = None

        # Component references for metrics collection
        self._database_manager = None
        self._cache_manager = None
        self._query_optimizer = None

        # Process info
        self.process = psutil.Process()
        self.start_time = time.time()

    def register_database_manager(self, db_manager) -> None:
        """Register database manager for metrics collection."""
        self._database_manager = weakref.ref(db_manager)
        logger.info("Database manager registered for metrics collection")

    def register_cache_manager(self, cache_manager) -> None:
        """Register cache manager for metrics collection."""
        self._cache_manager = weakref.ref(cache_manager)
        logger.info("Cache manager registered for metrics collection")

    def register_query_optimizer(self, query_optimizer) -> None:
        """Register query optimizer for metrics collection."""
        self._query_optimizer = weakref.ref(query_optimizer)
        logger.info("Query optimizer registered for metrics collection")

    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")

    def add_alert_callback(self, callback: Callable) -> None:
        """Add an alert callback function."""
        self.alert_callbacks.append(callback)
        logger.info("Added alert callback")

    def record_request(
        self, method: str, endpoint: str, status: int, duration: float
    ) -> None:
        """Record request metrics."""
        if not self.enabled:
            return

        # Prometheus metrics
        self.request_count.labels(
            method=method, endpoint=endpoint, status=str(status)
        ).inc()
        self.request_duration.labels(
            method=method, endpoint=endpoint, status=str(status)
        ).observe(duration)

        # Time series data
        self.response_times.append(duration * 1000)  # Convert to ms
        self.metrics_history["request_rate"].append(
            {"timestamp": time.time(), "value": 1}
        )

        if status >= 400:
            self.error_count.labels(error_type="http_error", component="api").inc()

    def record_database_query(
        self, query_type: str, table: str, duration: float
    ) -> None:
        """Record database query metrics."""
        if not self.enabled:
            return

        self.database_query_duration.labels(query_type=query_type, table=table).observe(
            duration
        )

        self.metrics_history["db_query_time"].append(
            {"timestamp": time.time(), "value": duration * 1000}  # Convert to ms
        )

    def record_cache_operation(self, operation: str, layer: str, result: str) -> None:
        """Record cache operation metrics."""
        if not self.enabled:
            return

        self.cache_operations.labels(
            operation=operation, layer=layer, result=result
        ).inc()

    def record_error(self, error_type: str, component: str) -> None:
        """Record error metrics."""
        if not self.enabled:
            return

        self.error_count.labels(error_type=error_type, component=component).inc()

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level metrics."""
        try:
            # CPU and memory
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            system_memory = psutil.virtual_memory()

            # Disk I/O
            disk_io = psutil.disk_usage("/")
            disk_io_counters = psutil.disk_io_counters()

            # Network I/O
            network_io = psutil.net_io_counters()

            # Load average (Unix-like systems)
            load_avg = [0.0, 0.0, 0.0]
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                # Windows doesn't have load average
                pass

            # File descriptors and threads
            try:
                open_files = len(self.process.open_files())
            except (psutil.AccessDenied, OSError):
                open_files = 0

            active_threads = self.process.num_threads()

            metrics = SystemMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=cpu_percent,
                memory_percent=system_memory.percent,
                memory_used_gb=memory_info.rss / (1024**3),
                memory_available_gb=system_memory.available / (1024**3),
                disk_usage_percent=disk_io.percent,
                disk_io_read_mb=disk_io_counters.read_bytes / (1024**2)
                if disk_io_counters
                else 0,
                disk_io_write_mb=disk_io_counters.write_bytes / (1024**2)
                if disk_io_counters
                else 0,
                network_sent_mb=network_io.bytes_sent / (1024**2),
                network_recv_mb=network_io.bytes_recv / (1024**2),
                load_average_1m=load_avg[0],
                load_average_5m=load_avg[1],
                load_average_15m=load_avg[2],
                open_files=open_files,
                active_threads=active_threads,
            )

            # Update Prometheus gauges
            self.cpu_usage.set(cpu_percent)
            self.memory_usage.labels(type="rss").set(memory_info.rss)
            self.memory_usage.labels(type="vms").set(memory_info.vms)

            return metrics

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None

    def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-level metrics."""
        try:
            now = datetime.now(timezone.utc)

            # Database metrics
            active_connections = 0
            pool_utilization = 0.0

            if self._database_manager and self._database_manager():
                db_manager = self._database_manager()
                db_metrics = db_manager.get_metrics()
                active_connections = db_metrics.get("pool_size", 0)
                max_connections = db_metrics.get("pool_max_size", 1)
                pool_utilization = (active_connections / max_connections) * 100
                self.database_connections_active.set(active_connections)

            # Request rate calculation
            recent_requests = [
                m
                for m in self.metrics_history["request_rate"]
                if time.time() - m["timestamp"] <= 60
            ]  # Last minute
            request_rate = len(recent_requests) / 60.0 if recent_requests else 0.0

            # Response time percentiles
            avg_response_time = 0.0
            p95_response_time = 0.0
            p99_response_time = 0.0

            if self.response_times:
                sorted_times = sorted(self.response_times)
                avg_response_time = sum(sorted_times) / len(sorted_times)

                if len(sorted_times) >= 20:  # Need reasonable sample size
                    p95_idx = int(len(sorted_times) * 0.95)
                    p99_idx = int(len(sorted_times) * 0.99)
                    p95_response_time = sorted_times[p95_idx]
                    p99_response_time = sorted_times[p99_idx]

            # Cache metrics
            cache_hit_rate = 0.0
            if self._cache_manager and self._cache_manager():
                cache_manager = self._cache_manager()
                cache_stats = cache_manager.get_stats()

                if "l1_stats" in cache_stats:
                    l1_stats = cache_stats["l1_stats"]
                    cache_hit_rate = l1_stats.get("hit_rate", 0.0)
                    self.cache_hit_rate.labels(layer="l1").set(cache_hit_rate)

                if "l2_stats" in cache_stats:
                    l2_stats = cache_stats["l2_stats"]
                    l2_hit_rate = l2_stats.get("hit_rate", 0.0)
                    self.cache_hit_rate.labels(layer="l2").set(l2_hit_rate)

            # Database query metrics
            db_query_rate = 0.0
            slow_query_count = 0

            if self._query_optimizer and self._query_optimizer():
                optimizer = self._query_optimizer()
                optimizer_stats = optimizer.get_metrics_summary()
                slow_query_count = optimizer_stats.get("slow_queries", 0)

                recent_queries = [
                    m
                    for m in self.metrics_history["db_query_time"]
                    if time.time() - m["timestamp"] <= 60
                ]
                db_query_rate = len(recent_queries) / 60.0

            # Garbage collection metrics
            gc_stats = gc.get_stats()
            gc_collections = sum(stat["collections"] for stat in gc_stats)

            # Heap size estimation
            heap_size_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
            if sys.platform == "linux":
                heap_size_mb /= 1024.0  # Linux reports in KB, others in bytes

            # Error rate calculation
            total_requests = len(self.response_times)
            error_requests = sum(
                1 for rule in self.alert_rules if "error" in rule.name.lower()
            )
            error_rate = (
                (error_requests / total_requests * 100) if total_requests > 0 else 0.0
            )

            metrics = ApplicationMetrics(
                timestamp=now,
                active_connections=active_connections,
                connection_pool_utilization=pool_utilization,
                request_rate_per_second=request_rate,
                error_rate_percent=error_rate,
                avg_response_time_ms=avg_response_time,
                p95_response_time_ms=p95_response_time,
                p99_response_time_ms=p99_response_time,
                cache_hit_rate_percent=cache_hit_rate,
                database_query_rate=db_query_rate,
                slow_query_count=slow_query_count,
                gc_collections=gc_collections,
                gc_time_ms=0.0,  # Would need more detailed tracking
                heap_size_mb=heap_size_mb,
            )

            return metrics

        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return None

    async def check_alerts(self) -> None:
        """Check alert rules and trigger notifications."""
        if not self.alert_rules:
            return

        now = datetime.now(timezone.utc)

        for rule in self.alert_rules:
            if not rule.active:
                continue

            # Check cooldown period
            if (
                rule.last_triggered
                and (now - rule.last_triggered).total_seconds() < rule.cooldown_seconds
            ):
                continue

            try:
                # Get recent metric values
                metric_data = self.metrics_history.get(rule.metric_name, deque())
                if not metric_data:
                    continue

                # Filter to window
                window_start = time.time() - rule.window_seconds
                recent_values = [
                    m["value"] for m in metric_data if m["timestamp"] >= window_start
                ]

                if not recent_values:
                    continue

                # Calculate metric value (average for window)
                metric_value = sum(recent_values) / len(recent_values)

                # Check threshold
                triggered = False
                if rule.operator == "gt" and metric_value > rule.threshold:
                    triggered = True
                elif rule.operator == "gte" and metric_value >= rule.threshold:
                    triggered = True
                elif rule.operator == "lt" and metric_value < rule.threshold:
                    triggered = True
                elif rule.operator == "lte" and metric_value <= rule.threshold:
                    triggered = True
                elif (
                    rule.operator == "eq" and abs(metric_value - rule.threshold) < 0.001
                ):
                    triggered = True

                if triggered:
                    rule.last_triggered = now
                    await self._trigger_alert(rule, metric_value)

            except Exception as e:
                logger.error(f"Error checking alert rule {rule.name}: {e}")

    async def _trigger_alert(self, rule: AlertRule, value: float) -> None:
        """Trigger an alert."""
        alert_data = {
            "rule": rule.name,
            "metric": rule.metric_name,
            "value": value,
            "threshold": rule.threshold,
            "severity": rule.severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.warning(
            f"ALERT: {rule.name} - {rule.metric_name}={value} {rule.operator} {rule.threshold}"
        )

        # Call rule-specific callback
        if rule.callback:
            try:
                await rule.callback(alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback for {rule.name}: {e}")

        # Call global alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Error in global alert callback: {e}")

    async def start_collection(self) -> None:
        """Start background metrics collection."""
        if self._collection_task:
            return

        self._collection_task = asyncio.create_task(self._collection_loop())
        self._alert_task = asyncio.create_task(self._alert_loop())
        logger.info(
            f"Started performance metrics collection (interval: {self.collection_interval}s)"
        )

    async def stop_collection(self) -> None:
        """Stop background metrics collection."""
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass

        if self._alert_task:
            self._alert_task.cancel()
            try:
                await self._alert_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped performance metrics collection")

    async def _collection_loop(self) -> None:
        """Background metrics collection loop."""
        while True:
            try:
                # Collect system metrics
                system_metrics = self.collect_system_metrics()
                if system_metrics:
                    self.system_metrics_history.append(system_metrics)

                # Collect application metrics
                app_metrics = self.collect_application_metrics()
                if app_metrics:
                    self.app_metrics_history.append(app_metrics)

                await asyncio.sleep(self.collection_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _alert_loop(self) -> None:
        """Background alert checking loop."""
        while True:
            try:
                await self.check_alerts()
                await asyncio.sleep(60)  # Check alerts every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert loop: {e}")
                await asyncio.sleep(60)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        try:
            latest_system = (
                self.system_metrics_history[-1] if self.system_metrics_history else None
            )
            latest_app = (
                self.app_metrics_history[-1] if self.app_metrics_history else None
            )

            summary = {
                "collection_enabled": self.enabled,
                "collection_interval": self.collection_interval,
                "uptime_seconds": int(time.time() - self.start_time),
                "alert_rules_count": len(self.alert_rules),
                "metrics_points_collected": len(self.response_times),
                "system_metrics": asdict(latest_system) if latest_system else None,
                "application_metrics": asdict(latest_app) if latest_app else None,
            }

            return summary

        except Exception as e:
            logger.error(f"Error generating metrics summary: {e}")
            return {"error": str(e)}

    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        try:
            return prometheus_client.generate_latest(self.registry).decode("utf-8")
        except Exception as e:
            logger.error(f"Error exporting Prometheus metrics: {e}")
            return f"# Error exporting metrics: {e}\
"


# Global performance metrics collector
_global_metrics_collector: Optional[PerformanceMetricsCollector] = None


def get_metrics_collector() -> PerformanceMetricsCollector:
    """Get the global metrics collector."""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = PerformanceMetricsCollector()
    return _global_metrics_collector


def initialize_metrics_collector(
    collection_interval: int = 30,
) -> PerformanceMetricsCollector:
    """Initialize the global metrics collector."""
    global _global_metrics_collector
    _global_metrics_collector = PerformanceMetricsCollector(collection_interval)
    logger.info(
        f"Performance metrics collector initialized (interval: {collection_interval}s)"
    )
    return _global_metrics_collector


# Default alert rules for common performance issues
def create_default_alert_rules() -> List[AlertRule]:
    """Create default alert rules for common performance issues."""
    return [
        AlertRule(
            name="high_response_time",
            metric_name="avg_response_time_ms",
            threshold=1000.0,  # 1 second
            operator="gt",
            window_seconds=300,
            severity="warning",
        ),
        AlertRule(
            name="very_high_response_time",
            metric_name="p95_response_time_ms",
            threshold=2000.0,  # 2 seconds
            operator="gt",
            window_seconds=180,
            severity="critical",
        ),
        AlertRule(
            name="high_error_rate",
            metric_name="error_rate_percent",
            threshold=5.0,  # 5%
            operator="gt",
            window_seconds=300,
            severity="warning",
        ),
        AlertRule(
            name="low_cache_hit_rate",
            metric_name="cache_hit_rate_percent",
            threshold=70.0,
            operator="lt",
            window_seconds=600,
            severity="warning",
        ),
        AlertRule(
            name="high_memory_usage",
            metric_name="memory_percent",
            threshold=85.0,
            operator="gt",
            window_seconds=300,
            severity="warning",
        ),
        AlertRule(
            name="high_cpu_usage",
            metric_name="cpu_percent",
            threshold=80.0,
            operator="gt",
            window_seconds=300,
            severity="warning",
        ),
    ]


async def setup_default_monitoring() -> PerformanceMetricsCollector:
    """Set up default performance monitoring with common alert rules."""
    collector = get_metrics_collector()

    # Add default alert rules
    for rule in create_default_alert_rules():
        collector.add_alert_rule(rule)

    # Start collection
    await collector.start_collection()

    logger.info("Default performance monitoring setup complete")
    return collector
