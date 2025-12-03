"""
Comprehensive Performance Monitoring Dashboard
Real-time metrics, alerting, and performance analytics
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

import psutil
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from ..database.connection import db_manager
from ..database.query_optimizer import query_optimizer
from ..economic.fcde_engine import fcde_engine
from ..governance.refusal_mechanisms import refusal_governance
from ..integrations.advanced_llm_registry import LLMRegistry

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric"""

    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None


@dataclass
class SystemAlert:
    """System performance alert"""

    alert_id: str
    metric_name: str
    severity: str  # info, warning, critical
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class PerformanceMonitor:
    """Comprehensive performance monitoring system"""

    def __init__(self):
        # Prometheus metrics
        self.init_prometheus_metrics()

        # Alert management
        self.alerts: Dict[str, SystemAlert] = {}
        self.alert_callbacks: List[Callable[[SystemAlert], None]] = []

        # Performance history
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.system_stats = {
            "cpu_usage": deque(maxlen=100),
            "memory_usage": deque(maxlen=100),
            "disk_usage": deque(maxlen=100),
            "network_io": deque(maxlen=100),
        }

        # Monitoring configuration
        self.monitoring_interval = 10  # seconds
        self.alert_thresholds = self._init_alert_thresholds()
        self.is_monitoring = False
        self.monitor_task = None

        # Performance baselines
        self.baselines = {}

    def init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""

        # System metrics
        self.cpu_usage_gauge = Gauge("system_cpu_usage_percent", "CPU usage percentage")
        self.memory_usage_gauge = Gauge(
            "system_memory_usage_percent", "Memory usage percentage"
        )
        self.disk_usage_gauge = Gauge(
            "system_disk_usage_percent", "Disk usage percentage"
        )

        # Application metrics
        self.request_duration_histogram = Histogram(
            "app_request_duration_seconds", "Request duration", ["endpoint", "method"]
        )
        self.active_connections_gauge = Gauge(
            "app_active_connections", "Active database connections"
        )
        self.cache_hit_rate_gauge = Gauge(
            "app_cache_hit_rate", "Cache hit rate percentage"
        )

        # UATP-specific metrics
        self.capsule_creation_counter = Counter(
            "uatp_capsules_created_total", "Total capsules created", ["type", "status"]
        )
        self.attribution_processing_histogram = Histogram(
            "uatp_attribution_processing_duration_seconds",
            "Attribution processing time",
        )
        self.governance_proposals_gauge = Gauge(
            "uatp_governance_proposals_active", "Active governance proposals"
        )
        self.refusal_rate_gauge = Gauge("uatp_refusal_rate", "Request refusal rate")

        # Economic metrics
        self.economic_value_counter = Counter(
            "uatp_economic_value_total", "Total economic value processed"
        )
        self.fcde_contributions_gauge = Gauge(
            "uatp_fcde_contributions_active", "Active FCDE contributions"
        )

        # LLM Registry metrics
        self.llm_providers_gauge = Gauge(
            "uatp_llm_providers_registered", "Registered LLM providers"
        )
        self.llm_models_gauge = Gauge(
            "uatp_llm_models_available", "Available LLM models"
        )

    def _init_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize alert thresholds"""
        return {
            "cpu_usage": {"warning": 80.0, "critical": 95.0},
            "memory_usage": {"warning": 85.0, "critical": 95.0},
            "disk_usage": {"warning": 90.0, "critical": 98.0},
            "response_time": {"warning": 2.0, "critical": 5.0},
            "error_rate": {"warning": 5.0, "critical": 10.0},
            "database_connections": {"warning": 80.0, "critical": 95.0},
            "cache_hit_rate": {"warning": 70.0, "critical": 50.0},
        }

    async def start_monitoring(self):
        """Start the monitoring system"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Performance monitoring started")

    async def stop_monitoring(self):
        """Stop the monitoring system"""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await self._collect_system_metrics()
                await self._collect_application_metrics()
                await self._collect_uatp_metrics()
                await self._check_alerts()

                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)  # Short delay before retry

    async def _collect_system_metrics(self):
        """Collect system-level performance metrics"""

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_usage_gauge.set(cpu_percent)
        self.system_stats["cpu_usage"].append(cpu_percent)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        self.memory_usage_gauge.set(memory_percent)
        self.system_stats["memory_usage"].append(memory_percent)

        # Disk usage
        disk = psutil.disk_usage("/")
        disk_percent = (disk.used / disk.total) * 100
        self.disk_usage_gauge.set(disk_percent)
        self.system_stats["disk_usage"].append(disk_percent)

        # Network I/O
        network = psutil.net_io_counters()
        network_bytes = network.bytes_sent + network.bytes_recv
        self.system_stats["network_io"].append(network_bytes)

        # Record metrics
        timestamp = datetime.now(timezone.utc)
        metrics = [
            PerformanceMetric("cpu_usage", cpu_percent, "%", timestamp),
            PerformanceMetric("memory_usage", memory_percent, "%", timestamp),
            PerformanceMetric("disk_usage", disk_percent, "%", timestamp),
        ]

        for metric in metrics:
            self.metric_history[metric.name].append(metric)

    async def _collect_application_metrics(self):
        """Collect application-level performance metrics"""

        # Database connection pool metrics
        if db_manager.engine and hasattr(db_manager.engine.pool, "size"):
            pool_size = db_manager.engine.pool.size()
            checked_out = db_manager.engine.pool.checkedout()
            pool_usage = (checked_out / pool_size) * 100 if pool_size > 0 else 0

            self.active_connections_gauge.set(checked_out)

            # Record metric
            timestamp = datetime.now(timezone.utc)
            metric = PerformanceMetric(
                "database_connections", pool_usage, "%", timestamp
            )
            self.metric_history["database_connections"].append(metric)

        # Cache performance
        if query_optimizer.redis_client:
            cache_stats = query_optimizer.get_optimization_stats()
            hit_rate = cache_stats["cache_stats"]["hit_rate_percent"]
            self.cache_hit_rate_gauge.set(hit_rate)

            # Record metric
            timestamp = datetime.now(timezone.utc)
            metric = PerformanceMetric("cache_hit_rate", hit_rate, "%", timestamp)
            self.metric_history["cache_hit_rate"].append(metric)

    async def _collect_uatp_metrics(self):
        """Collect UATP-specific performance metrics"""

        # Governance metrics
        if hasattr(refusal_governance, "refusal_stats"):
            active_proposals = len(
                [
                    p
                    for p in refusal_governance.appeals.values()
                    if p.status.value in ["pending", "under_review"]
                ]
            )
            self.governance_proposals_gauge.set(active_proposals)

            # Refusal rate calculation
            total_requests = 1000  # This would come from request tracking
            total_refusals = refusal_governance.refusal_stats["total_refusals"]
            refusal_rate = (
                (total_refusals / total_requests) * 100 if total_requests > 0 else 0
            )
            self.refusal_rate_gauge.set(refusal_rate)

        # Economic metrics
        if hasattr(fcde_engine, "creator_accounts"):
            total_contributors = len(fcde_engine.creator_accounts)
            self.fcde_contributions_gauge.set(total_contributors)

        # LLM Registry metrics (if available)
        try:
            if "LLMRegistry" in globals():
                registry = LLMRegistry()
                provider_count = len(registry._providers)
                model_count = len(registry._models)

                self.llm_providers_gauge.set(provider_count)
                self.llm_models_gauge.set(model_count)
        except Exception:
            pass  # Registry might not be initialized

    async def _check_alerts(self):
        """Check for alert conditions"""

        current_time = datetime.now(timezone.utc)

        # Check each metric against thresholds
        for metric_name, history in self.metric_history.items():
            if not history:
                continue

            latest_metric = history[-1]

            if metric_name in self.alert_thresholds:
                thresholds = self.alert_thresholds[metric_name]

                # Check critical threshold
                if latest_metric.value >= thresholds.get("critical", float("inf")):
                    await self._trigger_alert(
                        metric_name,
                        "critical",
                        f"{metric_name} is critically high: {latest_metric.value}{latest_metric.unit}",
                        latest_metric.value,
                        thresholds["critical"],
                    )

                # Check warning threshold
                elif latest_metric.value >= thresholds.get("warning", float("inf")):
                    await self._trigger_alert(
                        metric_name,
                        "warning",
                        f"{metric_name} is above warning threshold: {latest_metric.value}{latest_metric.unit}",
                        latest_metric.value,
                        thresholds["warning"],
                    )

                # Check if metric has returned to normal (resolve alerts)
                else:
                    await self._resolve_alerts(metric_name)

    async def _trigger_alert(
        self,
        metric_name: str,
        severity: str,
        message: str,
        value: float,
        threshold: float,
    ):
        """Trigger a performance alert"""

        alert_id = f"{metric_name}_{severity}"

        # Check if alert already exists
        if alert_id in self.alerts and not self.alerts[alert_id].resolved:
            return  # Alert already active

        alert = SystemAlert(
            alert_id=alert_id,
            metric_name=metric_name,
            severity=severity,
            message=message,
            value=value,
            threshold=threshold,
            timestamp=datetime.now(timezone.utc),
        )

        self.alerts[alert_id] = alert

        # Notify alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

        logger.warning(f"Performance alert triggered: {message}")

    async def _resolve_alerts(self, metric_name: str):
        """Resolve alerts for a metric"""

        resolved_alerts = []
        for alert_id, alert in self.alerts.items():
            if alert.metric_name == metric_name and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now(timezone.utc)
                resolved_alerts.append(alert)

        if resolved_alerts:
            logger.info(f"Resolved {len(resolved_alerts)} alerts for {metric_name}")

    def add_alert_callback(self, callback: Callable[[SystemAlert], None]):
        """Add a callback for alert notifications"""
        self.alert_callbacks.append(callback)

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""

        current_time = datetime.now(timezone.utc)

        # System overview
        system_overview = {}
        for metric_name in ["cpu_usage", "memory_usage", "disk_usage"]:
            if metric_name in self.metric_history and self.metric_history[metric_name]:
                latest = self.metric_history[metric_name][-1]
                system_overview[metric_name] = {
                    "current": latest.value,
                    "unit": latest.unit,
                    "status": self._get_metric_status(metric_name, latest.value),
                }

        # Application metrics
        app_metrics = {}
        for metric_name in ["database_connections", "cache_hit_rate"]:
            if metric_name in self.metric_history and self.metric_history[metric_name]:
                latest = self.metric_history[metric_name][-1]
                app_metrics[metric_name] = {
                    "current": latest.value,
                    "unit": latest.unit,
                    "status": self._get_metric_status(metric_name, latest.value),
                }

        # Active alerts
        active_alerts = [
            {
                "alert_id": alert.alert_id,
                "metric": alert.metric_name,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
            }
            for alert in self.alerts.values()
            if not alert.resolved
        ]

        # Alert summary
        alert_summary = {
            "total": len(self.alerts),
            "active": len(active_alerts),
            "resolved": len([a for a in self.alerts.values() if a.resolved]),
            "by_severity": {
                "critical": len(
                    [a for a in active_alerts if a["severity"] == "critical"]
                ),
                "warning": len(
                    [a for a in active_alerts if a["severity"] == "warning"]
                ),
                "info": len([a for a in active_alerts if a["severity"] == "info"]),
            },
        }

        return {
            "timestamp": current_time.isoformat(),
            "monitoring_status": "active" if self.is_monitoring else "inactive",
            "system_overview": system_overview,
            "application_metrics": app_metrics,
            "active_alerts": active_alerts,
            "alert_summary": alert_summary,
            "uptime_seconds": time.time()
            - (self.monitor_task.get_name() if self.monitor_task else time.time()),
            "performance_score": self._calculate_performance_score(),
        }

    def _get_metric_status(self, metric_name: str, value: float) -> str:
        """Get status (good/warning/critical) for a metric value"""

        if metric_name not in self.alert_thresholds:
            return "good"

        thresholds = self.alert_thresholds[metric_name]

        if value >= thresholds.get("critical", float("inf")):
            return "critical"
        elif value >= thresholds.get("warning", float("inf")):
            return "warning"
        else:
            return "good"

    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score (0-100)"""

        scores = []

        # System metrics (weight: 40%)
        for metric_name in ["cpu_usage", "memory_usage", "disk_usage"]:
            if metric_name in self.metric_history and self.metric_history[metric_name]:
                latest = self.metric_history[metric_name][-1]
                status = self._get_metric_status(metric_name, latest.value)

                if status == "good":
                    scores.append(100)
                elif status == "warning":
                    scores.append(70)
                else:  # critical
                    scores.append(30)

        # Application metrics (weight: 40%)
        for metric_name in ["database_connections", "cache_hit_rate"]:
            if metric_name in self.metric_history and self.metric_history[metric_name]:
                latest = self.metric_history[metric_name][-1]
                status = self._get_metric_status(metric_name, latest.value)

                if status == "good":
                    scores.append(100)
                elif status == "warning":
                    scores.append(70)
                else:  # critical
                    scores.append(30)

        # Alert penalty (weight: 20%)
        active_alerts = [a for a in self.alerts.values() if not a.resolved]
        critical_alerts = [a for a in active_alerts if a.severity == "critical"]
        warning_alerts = [a for a in active_alerts if a.severity == "warning"]

        alert_score = 100
        alert_score -= len(critical_alerts) * 30  # -30 per critical alert
        alert_score -= len(warning_alerts) * 10  # -10 per warning alert
        alert_score = max(0, alert_score)
        scores.append(alert_score)

        return sum(scores) / len(scores) if scores else 100

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        return generate_latest()

    def get_metric_history(
        self, metric_name: str, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get historical data for a specific metric"""

        if metric_name not in self.metric_history:
            return []

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        history = []
        for metric in self.metric_history[metric_name]:
            if metric.timestamp >= cutoff_time:
                history.append(
                    {
                        "timestamp": metric.timestamp.isoformat(),
                        "value": metric.value,
                        "unit": metric.unit,
                        "tags": metric.tags,
                    }
                )

        return history


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Alert notification functions
def log_alert_callback(alert: SystemAlert):
    """Log alert to console/file"""
    logger.warning(f"PERFORMANCE ALERT [{alert.severity.upper()}]: {alert.message}")


def email_alert_callback(alert: SystemAlert):
    """Send email alert (placeholder implementation)"""
    if alert.severity == "critical":
        # This would integrate with actual email service
        logger.critical(f"CRITICAL ALERT EMAIL: {alert.message}")


# Register default alert callbacks
performance_monitor.add_alert_callback(log_alert_callback)
performance_monitor.add_alert_callback(email_alert_callback)


@asynccontextmanager
async def performance_monitoring():
    """Context manager for performance monitoring"""
    await performance_monitor.start_monitoring()
    try:
        yield performance_monitor
    finally:
        await performance_monitor.stop_monitoring()
