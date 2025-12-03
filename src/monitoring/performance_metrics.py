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
import psutil
import resource
import sys
import time
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable, DefaultDict
from dataclasses import dataclass, asdict
from enum import Enum
import weakref

import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry

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
    severity: str = 'warning'  # 'warning', 'critical'
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
            'uatp_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint', 'status'],
            registry=self.registry,
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        )
        
        self.request_count = Counter(
            'uatp_requests_total',
            'Total requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.database_query_duration = Histogram(
            'uatp_database_query_duration_seconds',
            'Database query duration in seconds',
            ['query_type', 'table'],
            registry=self.registry,
            buckets=(0.001, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
        )
        
        self.database_connections_active = Gauge(
            'uatp_database_connections_active',
            'Active database connections',
            registry=self.registry
        )
        
        self.cache_operations = Counter(
            'uatp_cache_operations_total',
            'Cache operations',
            ['operation', 'layer', 'result'],
            registry=self.registry
        )
        
        self.cache_hit_rate = Gauge(
            'uatp_cache_hit_rate',
            'Cache hit rate percentage',
            ['layer'],
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'uatp_memory_usage_bytes',
            'Memory usage in bytes',
            ['type'],
            registry=self.registry
        )
        
        self.cpu_usage = Gauge(
            'uatp_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.error_count = Counter(
            'uatp_errors_total',
            'Total errors',
            ['error_type', 'component'],
            registry=self.registry
        )
        
        # Time series data storage (for alerting and analysis)
        self.metrics_history: DefaultDict[str, deque] = defaultdict(lambda: deque(maxlen=1000))\n        self.response_times: deque = deque(maxlen=1000)\n        self.system_metrics_history: deque = deque(maxlen=100)\n        self.app_metrics_history: deque = deque(maxlen=100)\n        \n        # Alert system\n        self.alert_rules: List[AlertRule] = []\n        self.alert_callbacks: List[Callable] = []\n        \n        # Background tasks\n        self._collection_task: Optional[asyncio.Task] = None\n        self._alert_task: Optional[asyncio.Task] = None\n        \n        # Component references for metrics collection\n        self._database_manager = None\n        self._cache_manager = None\n        self._query_optimizer = None\n        \n        # Process info\n        self.process = psutil.Process()\n        self.start_time = time.time()\n    \n    def register_database_manager(self, db_manager) -> None:\n        \"\"\"Register database manager for metrics collection.\"\"\"\n        self._database_manager = weakref.ref(db_manager)\n        logger.info(\"Database manager registered for metrics collection\")\n    \n    def register_cache_manager(self, cache_manager) -> None:\n        \"\"\"Register cache manager for metrics collection.\"\"\"\n        self._cache_manager = weakref.ref(cache_manager)\n        logger.info(\"Cache manager registered for metrics collection\")\n    \n    def register_query_optimizer(self, query_optimizer) -> None:\n        \"\"\"Register query optimizer for metrics collection.\"\"\"\n        self._query_optimizer = weakref.ref(query_optimizer)\n        logger.info(\"Query optimizer registered for metrics collection\")\n    \n    def add_alert_rule(self, rule: AlertRule) -> None:\n        \"\"\"Add an alert rule.\"\"\"\n        self.alert_rules.append(rule)\n        logger.info(f\"Added alert rule: {rule.name}\")\n    \n    def add_alert_callback(self, callback: Callable) -> None:\n        \"\"\"Add an alert callback function.\"\"\"\n        self.alert_callbacks.append(callback)\n        logger.info(\"Added alert callback\")\n    \n    def record_request(self, method: str, endpoint: str, status: int, duration: float) -> None:\n        \"\"\"Record request metrics.\"\"\"\n        if not self.enabled:\n            return\n        \n        # Prometheus metrics\n        self.request_count.labels(method=method, endpoint=endpoint, status=str(status)).inc()\n        self.request_duration.labels(method=method, endpoint=endpoint, status=str(status)).observe(duration)\n        \n        # Time series data\n        self.response_times.append(duration * 1000)  # Convert to ms\n        self.metrics_history['request_rate'].append({\n            'timestamp': time.time(),\n            'value': 1\n        })\n        \n        if status >= 400:\n            self.error_count.labels(error_type='http_error', component='api').inc()\n    \n    def record_database_query(self, query_type: str, table: str, duration: float) -> None:\n        \"\"\"Record database query metrics.\"\"\"\n        if not self.enabled:\n            return\n        \n        self.database_query_duration.labels(query_type=query_type, table=table).observe(duration)\n        \n        self.metrics_history['db_query_time'].append({\n            'timestamp': time.time(),\n            'value': duration * 1000  # Convert to ms\n        })\n    \n    def record_cache_operation(self, operation: str, layer: str, result: str) -> None:\n        \"\"\"Record cache operation metrics.\"\"\"\n        if not self.enabled:\n            return\n        \n        self.cache_operations.labels(operation=operation, layer=layer, result=result).inc()\n    \n    def record_error(self, error_type: str, component: str) -> None:\n        \"\"\"Record error metrics.\"\"\"\n        if not self.enabled:\n            return\n        \n        self.error_count.labels(error_type=error_type, component=component).inc()\n    \n    def collect_system_metrics(self) -> SystemMetrics:\n        \"\"\"Collect system-level metrics.\"\"\"\n        try:\n            # CPU and memory\n            cpu_percent = self.process.cpu_percent()\n            memory_info = self.process.memory_info()\n            system_memory = psutil.virtual_memory()\n            \n            # Disk I/O\n            disk_io = psutil.disk_usage('/')\n            disk_io_counters = psutil.disk_io_counters()\n            \n            # Network I/O\n            network_io = psutil.net_io_counters()\n            \n            # Load average (Unix-like systems)\n            load_avg = [0.0, 0.0, 0.0]\n            try:\n                load_avg = list(psutil.getloadavg())\n            except AttributeError:\n                # Windows doesn't have load average\n                pass\n            \n            # File descriptors and threads\n            try:\n                open_files = len(self.process.open_files())\n            except (psutil.AccessDenied, OSError):\n                open_files = 0\n            \n            active_threads = self.process.num_threads()\n            \n            metrics = SystemMetrics(\n                timestamp=datetime.now(timezone.utc),\n                cpu_percent=cpu_percent,\n                memory_percent=system_memory.percent,\n                memory_used_gb=memory_info.rss / (1024**3),\n                memory_available_gb=system_memory.available / (1024**3),\n                disk_usage_percent=disk_io.percent,\n                disk_io_read_mb=disk_io_counters.read_bytes / (1024**2) if disk_io_counters else 0,\n                disk_io_write_mb=disk_io_counters.write_bytes / (1024**2) if disk_io_counters else 0,\n                network_sent_mb=network_io.bytes_sent / (1024**2),\n                network_recv_mb=network_io.bytes_recv / (1024**2),\n                load_average_1m=load_avg[0],\n                load_average_5m=load_avg[1],\n                load_average_15m=load_avg[2],\n                open_files=open_files,\n                active_threads=active_threads\n            )\n            \n            # Update Prometheus gauges\n            self.cpu_usage.set(cpu_percent)\n            self.memory_usage.labels(type='rss').set(memory_info.rss)\n            self.memory_usage.labels(type='vms').set(memory_info.vms)\n            \n            return metrics\n            \n        except Exception as e:\n            logger.error(f\"Error collecting system metrics: {e}\")\n            return None\n    \n    def collect_application_metrics(self) -> ApplicationMetrics:\n        \"\"\"Collect application-level metrics.\"\"\"\n        try:\n            now = datetime.now(timezone.utc)\n            \n            # Database metrics\n            active_connections = 0\n            pool_utilization = 0.0\n            \n            if self._database_manager and self._database_manager():\n                db_manager = self._database_manager()\n                db_metrics = db_manager.get_metrics()\n                active_connections = db_metrics.get('pool_size', 0)\n                max_connections = db_metrics.get('pool_max_size', 1)\n                pool_utilization = (active_connections / max_connections) * 100\n                self.database_connections_active.set(active_connections)\n            \n            # Request rate calculation\n            recent_requests = [m for m in self.metrics_history['request_rate'] \n                             if time.time() - m['timestamp'] <= 60]  # Last minute\n            request_rate = len(recent_requests) / 60.0 if recent_requests else 0.0\n            \n            # Response time percentiles\n            avg_response_time = 0.0\n            p95_response_time = 0.0\n            p99_response_time = 0.0\n            \n            if self.response_times:\n                sorted_times = sorted(self.response_times)\n                avg_response_time = sum(sorted_times) / len(sorted_times)\n                \n                if len(sorted_times) >= 20:  # Need reasonable sample size\n                    p95_idx = int(len(sorted_times) * 0.95)\n                    p99_idx = int(len(sorted_times) * 0.99)\n                    p95_response_time = sorted_times[p95_idx]\n                    p99_response_time = sorted_times[p99_idx]\n            \n            # Cache metrics\n            cache_hit_rate = 0.0\n            if self._cache_manager and self._cache_manager():\n                cache_manager = self._cache_manager()\n                cache_stats = cache_manager.get_stats()\n                \n                if 'l1_stats' in cache_stats:\n                    l1_stats = cache_stats['l1_stats']\n                    cache_hit_rate = l1_stats.get('hit_rate', 0.0)\n                    self.cache_hit_rate.labels(layer='l1').set(cache_hit_rate)\n                \n                if 'l2_stats' in cache_stats:\n                    l2_stats = cache_stats['l2_stats']\n                    l2_hit_rate = l2_stats.get('hit_rate', 0.0)\n                    self.cache_hit_rate.labels(layer='l2').set(l2_hit_rate)\n            \n            # Database query metrics\n            db_query_rate = 0.0\n            slow_query_count = 0\n            \n            if self._query_optimizer and self._query_optimizer():\n                optimizer = self._query_optimizer()\n                optimizer_stats = optimizer.get_metrics_summary()\n                slow_query_count = optimizer_stats.get('slow_queries', 0)\n                \n                recent_queries = [m for m in self.metrics_history['db_query_time']\n                                if time.time() - m['timestamp'] <= 60]\n                db_query_rate = len(recent_queries) / 60.0\n            \n            # Garbage collection metrics\n            gc_stats = gc.get_stats()\n            gc_collections = sum(stat['collections'] for stat in gc_stats)\n            \n            # Heap size estimation\n            heap_size_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0\n            if sys.platform == 'linux':\n                heap_size_mb /= 1024.0  # Linux reports in KB, others in bytes\n            \n            # Error rate calculation\n            total_requests = len(self.response_times)\n            error_requests = sum(1 for rule in self.alert_rules if 'error' in rule.name.lower())\n            error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0.0\n            \n            metrics = ApplicationMetrics(\n                timestamp=now,\n                active_connections=active_connections,\n                connection_pool_utilization=pool_utilization,\n                request_rate_per_second=request_rate,\n                error_rate_percent=error_rate,\n                avg_response_time_ms=avg_response_time,\n                p95_response_time_ms=p95_response_time,\n                p99_response_time_ms=p99_response_time,\n                cache_hit_rate_percent=cache_hit_rate,\n                database_query_rate=db_query_rate,\n                slow_query_count=slow_query_count,\n                gc_collections=gc_collections,\n                gc_time_ms=0.0,  # Would need more detailed tracking\n                heap_size_mb=heap_size_mb\n            )\n            \n            return metrics\n            \n        except Exception as e:\n            logger.error(f\"Error collecting application metrics: {e}\")\n            return None\n    \n    async def check_alerts(self) -> None:\n        \"\"\"Check alert rules and trigger notifications.\"\"\"\n        if not self.alert_rules:\n            return\n        \n        now = datetime.now(timezone.utc)\n        \n        for rule in self.alert_rules:\n            if not rule.active:\n                continue\n            \n            # Check cooldown period\n            if (rule.last_triggered and \n                (now - rule.last_triggered).total_seconds() < rule.cooldown_seconds):\n                continue\n            \n            try:\n                # Get recent metric values\n                metric_data = self.metrics_history.get(rule.metric_name, deque())\n                if not metric_data:\n                    continue\n                \n                # Filter to window\n                window_start = time.time() - rule.window_seconds\n                recent_values = [m['value'] for m in metric_data \n                               if m['timestamp'] >= window_start]\n                \n                if not recent_values:\n                    continue\n                \n                # Calculate metric value (average for window)\n                metric_value = sum(recent_values) / len(recent_values)\n                \n                # Check threshold\n                triggered = False\n                if rule.operator == 'gt' and metric_value > rule.threshold:\n                    triggered = True\n                elif rule.operator == 'gte' and metric_value >= rule.threshold:\n                    triggered = True\n                elif rule.operator == 'lt' and metric_value < rule.threshold:\n                    triggered = True\n                elif rule.operator == 'lte' and metric_value <= rule.threshold:\n                    triggered = True\n                elif rule.operator == 'eq' and abs(metric_value - rule.threshold) < 0.001:\n                    triggered = True\n                \n                if triggered:\n                    rule.last_triggered = now\n                    await self._trigger_alert(rule, metric_value)\n                    \n            except Exception as e:\n                logger.error(f\"Error checking alert rule {rule.name}: {e}\")\n    \n    async def _trigger_alert(self, rule: AlertRule, value: float) -> None:\n        \"\"\"Trigger an alert.\"\"\"\n        alert_data = {\n            'rule': rule.name,\n            'metric': rule.metric_name,\n            'value': value,\n            'threshold': rule.threshold,\n            'severity': rule.severity,\n            'timestamp': datetime.now(timezone.utc).isoformat()\n        }\n        \n        logger.warning(f\"ALERT: {rule.name} - {rule.metric_name}={value} {rule.operator} {rule.threshold}\")\n        \n        # Call rule-specific callback\n        if rule.callback:\n            try:\n                await rule.callback(alert_data)\n            except Exception as e:\n                logger.error(f\"Error in alert callback for {rule.name}: {e}\")\n        \n        # Call global alert callbacks\n        for callback in self.alert_callbacks:\n            try:\n                await callback(alert_data)\n            except Exception as e:\n                logger.error(f\"Error in global alert callback: {e}\")\n    \n    async def start_collection(self) -> None:\n        \"\"\"Start background metrics collection.\"\"\"\n        if self._collection_task:\n            return\n        \n        self._collection_task = asyncio.create_task(self._collection_loop())\n        self._alert_task = asyncio.create_task(self._alert_loop())\n        logger.info(f\"Started performance metrics collection (interval: {self.collection_interval}s)\")\n    \n    async def stop_collection(self) -> None:\n        \"\"\"Stop background metrics collection.\"\"\"\n        if self._collection_task:\n            self._collection_task.cancel()\n            try:\n                await self._collection_task\n            except asyncio.CancelledError:\n                pass\n        \n        if self._alert_task:\n            self._alert_task.cancel()\n            try:\n                await self._alert_task\n            except asyncio.CancelledError:\n                pass\n        \n        logger.info(\"Stopped performance metrics collection\")\n    \n    async def _collection_loop(self) -> None:\n        \"\"\"Background metrics collection loop.\"\"\"\n        while True:\n            try:\n                # Collect system metrics\n                system_metrics = self.collect_system_metrics()\n                if system_metrics:\n                    self.system_metrics_history.append(system_metrics)\n                \n                # Collect application metrics\n                app_metrics = self.collect_application_metrics()\n                if app_metrics:\n                    self.app_metrics_history.append(app_metrics)\n                \n                await asyncio.sleep(self.collection_interval)\n                \n            except asyncio.CancelledError:\n                break\n            except Exception as e:\n                logger.error(f\"Error in metrics collection loop: {e}\")\n                await asyncio.sleep(self.collection_interval)\n    \n    async def _alert_loop(self) -> None:\n        \"\"\"Background alert checking loop.\"\"\"\n        while True:\n            try:\n                await self.check_alerts()\n                await asyncio.sleep(60)  # Check alerts every minute\n                \n            except asyncio.CancelledError:\n                break\n            except Exception as e:\n                logger.error(f\"Error in alert loop: {e}\")\n                await asyncio.sleep(60)\n    \n    def get_metrics_summary(self) -> Dict[str, Any]:\n        \"\"\"Get current metrics summary.\"\"\"\n        try:\n            latest_system = self.system_metrics_history[-1] if self.system_metrics_history else None\n            latest_app = self.app_metrics_history[-1] if self.app_metrics_history else None\n            \n            summary = {\n                'collection_enabled': self.enabled,\n                'collection_interval': self.collection_interval,\n                'uptime_seconds': int(time.time() - self.start_time),\n                'alert_rules_count': len(self.alert_rules),\n                'metrics_points_collected': len(self.response_times),\n                'system_metrics': asdict(latest_system) if latest_system else None,\n                'application_metrics': asdict(latest_app) if latest_app else None\n            }\n            \n            return summary\n            \n        except Exception as e:\n            logger.error(f\"Error generating metrics summary: {e}\")\n            return {'error': str(e)}\n    \n    def export_prometheus_metrics(self) -> str:\n        \"\"\"Export metrics in Prometheus format.\"\"\"\n        try:\n            return prometheus_client.generate_latest(self.registry).decode('utf-8')\n        except Exception as e:\n            logger.error(f\"Error exporting Prometheus metrics: {e}\")\n            return f\"# Error exporting metrics: {e}\\n\"\n\n\n# Global performance metrics collector\n_global_metrics_collector: Optional[PerformanceMetricsCollector] = None\n\n\ndef get_metrics_collector() -> PerformanceMetricsCollector:\n    \"\"\"Get the global metrics collector.\"\"\"\n    global _global_metrics_collector\n    if _global_metrics_collector is None:\n        _global_metrics_collector = PerformanceMetricsCollector()\n    return _global_metrics_collector\n\n\ndef initialize_metrics_collector(collection_interval: int = 30) -> PerformanceMetricsCollector:\n    \"\"\"Initialize the global metrics collector.\"\"\"\n    global _global_metrics_collector\n    _global_metrics_collector = PerformanceMetricsCollector(collection_interval)\n    logger.info(f\"Performance metrics collector initialized (interval: {collection_interval}s)\")\n    return _global_metrics_collector\n\n\n# Default alert rules for common performance issues\ndef create_default_alert_rules() -> List[AlertRule]:\n    \"\"\"Create default alert rules for common performance issues.\"\"\"\n    return [\n        AlertRule(\n            name=\"high_response_time\",\n            metric_name=\"avg_response_time_ms\",\n            threshold=1000.0,  # 1 second\n            operator=\"gt\",\n            window_seconds=300,\n            severity=\"warning\"\n        ),\n        AlertRule(\n            name=\"very_high_response_time\",\n            metric_name=\"p95_response_time_ms\",\n            threshold=2000.0,  # 2 seconds\n            operator=\"gt\",\n            window_seconds=180,\n            severity=\"critical\"\n        ),\n        AlertRule(\n            name=\"high_error_rate\",\n            metric_name=\"error_rate_percent\",\n            threshold=5.0,  # 5%\n            operator=\"gt\",\n            window_seconds=300,\n            severity=\"warning\"\n        ),\n        AlertRule(\n            name=\"low_cache_hit_rate\",\n            metric_name=\"cache_hit_rate_percent\",\n            threshold=70.0,\n            operator=\"lt\",\n            window_seconds=600,\n            severity=\"warning\"\n        ),\n        AlertRule(\n            name=\"high_memory_usage\",\n            metric_name=\"memory_percent\",\n            threshold=85.0,\n            operator=\"gt\",\n            window_seconds=300,\n            severity=\"warning\"\n        ),\n        AlertRule(\n            name=\"high_cpu_usage\",\n            metric_name=\"cpu_percent\",\n            threshold=80.0,\n            operator=\"gt\",\n            window_seconds=300,\n            severity=\"warning\"\n        )\n    ]\n\n\nasync def setup_default_monitoring() -> PerformanceMetricsCollector:\n    \"\"\"Set up default performance monitoring with common alert rules.\"\"\"\n    collector = get_metrics_collector()\n    \n    # Add default alert rules\n    for rule in create_default_alert_rules():\n        collector.add_alert_rule(rule)\n    \n    # Start collection\n    await collector.start_collection()\n    \n    logger.info(\"Default performance monitoring setup complete\")\n    return collector"