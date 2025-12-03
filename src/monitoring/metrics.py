#!/usr/bin/env python3
"""
Metrics Collection System for UATP Capsule Engine
================================================

This module provides comprehensive metrics collection for performance monitoring,
including system metrics, application metrics, and custom business metrics.
"""

import asyncio
import json
import logging
import os
import sys
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric type enumeration."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricPoint:
    """Single metric data point."""

    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = None
    metric_type: MetricType = MetricType.GAUGE

    def __post_init__(self):
        if self.labels is None:
            self.labels = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
            "type": self.metric_type.value,
        }


class MetricsCollector:
    """Metrics collector for UATP system."""

    def __init__(self, max_points: int = 10000):
        self.metrics = defaultdict(lambda: deque(maxlen=max_points))
        self.counters = defaultdict(float)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self.max_points = max_points
        self.lock = threading.Lock()

        logger.info("📊 Metrics Collector initialized")

    def record_counter(
        self, name: str, value: float = 1.0, labels: Dict[str, str] = None
    ):
        """Record a counter metric."""

        with self.lock:
            key = self._get_metric_key(name, labels)
            self.counters[key] += value

            point = MetricPoint(
                name=name,
                value=self.counters[key],
                timestamp=datetime.now(),
                labels=labels or {},
                metric_type=MetricType.COUNTER,
            )

            self.metrics[key].append(point)

    def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a gauge metric."""

        with self.lock:
            key = self._get_metric_key(name, labels)
            self.gauges[key] = value

            point = MetricPoint(
                name=name,
                value=value,
                timestamp=datetime.now(),
                labels=labels or {},
                metric_type=MetricType.GAUGE,
            )

            self.metrics[key].append(point)

    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram metric."""

        with self.lock:
            key = self._get_metric_key(name, labels)
            self.histograms[key].append(value)

            # Keep only recent values (last 1000)
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-1000:]

            point = MetricPoint(
                name=name,
                value=value,
                timestamp=datetime.now(),
                labels=labels or {},
                metric_type=MetricType.HISTOGRAM,
            )

            self.metrics[key].append(point)

    def record_timing(self, name: str, duration: float, labels: Dict[str, str] = None):
        """Record a timing metric (in seconds)."""

        self.record_histogram(f"{name}_duration", duration, labels)
        self.record_counter(f"{name}_total", 1.0, labels)

    def get_metric(self, name: str, labels: Dict[str, str] = None) -> List[MetricPoint]:
        """Get metric points by name and labels."""

        key = self._get_metric_key(name, labels)

        with self.lock:
            return list(self.metrics[key])

    def get_all_metrics(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all metrics."""

        with self.lock:
            result = {}
            for key, points in self.metrics.items():
                result[key] = [point.to_dict() for point in points]
            return result

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""

        with self.lock:
            return {
                "total_metrics": len(self.metrics),
                "total_points": sum(len(points) for points in self.metrics.values()),
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histogram_summaries": self._get_histogram_summaries(),
            }

    def get_histogram_summary(
        self, name: str, labels: Dict[str, str] = None
    ) -> Dict[str, float]:
        """Get histogram summary statistics."""

        key = self._get_metric_key(name, labels)

        with self.lock:
            values = self.histograms.get(key, [])

            if not values:
                return {}

            sorted_values = sorted(values)
            count = len(sorted_values)

            return {
                "count": count,
                "sum": sum(sorted_values),
                "min": sorted_values[0],
                "max": sorted_values[-1],
                "mean": sum(sorted_values) / count,
                "p50": sorted_values[int(count * 0.5)],
                "p90": sorted_values[int(count * 0.9)],
                "p95": sorted_values[int(count * 0.95)],
                "p99": sorted_values[int(count * 0.99)],
            }

    def _get_metric_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Generate metric key from name and labels."""

        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _get_histogram_summaries(self) -> Dict[str, Dict[str, float]]:
        """Get all histogram summaries."""

        summaries = {}
        for key, values in self.histograms.items():
            if values:
                sorted_values = sorted(values)
                count = len(sorted_values)
                summaries[key] = {
                    "count": count,
                    "sum": sum(sorted_values),
                    "min": sorted_values[0],
                    "max": sorted_values[-1],
                    "mean": sum(sorted_values) / count,
                    "p95": sorted_values[int(count * 0.95)] if count > 0 else 0,
                }

        return summaries

    def clear_old_metrics(self, hours: int = 24):
        """Clear metrics older than specified hours."""

        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self.lock:
            for key in list(self.metrics.keys()):
                points = self.metrics[key]
                # Filter out old points
                recent_points = deque(
                    [p for p in points if p.timestamp > cutoff_time],
                    maxlen=self.max_points,
                )
                self.metrics[key] = recent_points

                # Remove empty metrics
                if not self.metrics[key]:
                    del self.metrics[key]


class PerformanceMonitor:
    """Performance monitor with timing context managers."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector

    def timer(self, name: str, labels: Dict[str, str] = None):
        """Context manager for timing operations."""

        class TimerContext:
            def __init__(self, monitor, metric_name, metric_labels):
                self.monitor = monitor
                self.name = metric_name
                self.labels = metric_labels
                self.start_time = None

            def __enter__(self):
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.start_time:
                    duration = time.time() - self.start_time
                    self.monitor.metrics.record_timing(self.name, duration, self.labels)

        return TimerContext(self, name, labels)

    def count(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Record a counter metric."""
        self.metrics.record_counter(name, value, labels)

    def gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a gauge metric."""
        self.metrics.record_gauge(name, value, labels)


class SystemMetricsCollector:
    """System metrics collector."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.running = False
        self.collection_interval = 30  # seconds
        self.task = None

    async def start(self):
        """Start collecting system metrics."""

        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._collection_loop())
        logger.info("📊 System metrics collection started")

    async def stop(self):
        """Stop collecting system metrics."""

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("📊 System metrics collection stopped")

    async def _collection_loop(self):
        """Main collection loop."""

        while self.running:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error collecting system metrics: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_system_metrics(self):
        """Collect system metrics."""

        try:
            # CPU usage
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.record_gauge("system_cpu_percent", cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics.record_gauge("system_memory_percent", memory.percent)
            self.metrics.record_gauge("system_memory_used_bytes", memory.used)
            self.metrics.record_gauge("system_memory_free_bytes", memory.free)

            # Disk usage
            disk = psutil.disk_usage(".")
            disk_percent = (disk.used / disk.total) * 100
            self.metrics.record_gauge("system_disk_percent", disk_percent)
            self.metrics.record_gauge("system_disk_used_bytes", disk.used)
            self.metrics.record_gauge("system_disk_free_bytes", disk.free)

            # Network I/O
            net_io = psutil.net_io_counters()
            self.metrics.record_counter("system_network_bytes_sent", net_io.bytes_sent)
            self.metrics.record_counter("system_network_bytes_recv", net_io.bytes_recv)

        except ImportError:
            logger.warning("psutil not available, skipping system metrics")
        except Exception as e:
            logger.error(f"❌ Error collecting system metrics: {e}")


class ApplicationMetricsCollector:
    """Application-specific metrics collector."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.running = False
        self.collection_interval = 60  # seconds
        self.task = None

    async def start(self):
        """Start collecting application metrics."""

        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._collection_loop())
        logger.info("📊 Application metrics collection started")

    async def stop(self):
        """Stop collecting application metrics."""

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("📊 Application metrics collection stopped")

    async def _collection_loop(self):
        """Main collection loop."""

        while self.running:
            try:
                await self._collect_application_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error collecting application metrics: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_application_metrics(self):
        """Collect application metrics."""

        try:
            # Database metrics
            await self._collect_database_metrics()

            # Capsule engine metrics
            await self._collect_capsule_metrics()

            # Authentication metrics
            await self._collect_auth_metrics()

        except Exception as e:
            logger.error(f"❌ Error collecting application metrics: {e}")

    async def _collect_database_metrics(self):
        """Collect database metrics."""

        try:
            from config.database_config import get_database_adapter

            adapter = get_database_adapter()
            if adapter:
                # Get capsule statistics
                stats = await adapter.get_capsule_stats()

                self.metrics.record_gauge(
                    "uatp_capsules_total", stats.get("total_capsules", 0)
                )
                self.metrics.record_gauge(
                    "uatp_capsules_active", stats.get("active_capsules", 0)
                )
                self.metrics.record_gauge(
                    "uatp_capsules_avg_significance", stats.get("avg_significance", 0)
                )

                # Platform metrics
                platforms = stats.get("platforms", {})
                for platform, count in platforms.items():
                    self.metrics.record_gauge(
                        "uatp_capsules_by_platform", count, {"platform": platform}
                    )

                # Type metrics
                types = stats.get("types", {})
                for capsule_type, count in types.items():
                    self.metrics.record_gauge(
                        "uatp_capsules_by_type", count, {"type": capsule_type}
                    )

        except Exception as e:
            logger.error(f"❌ Error collecting database metrics: {e}")

    async def _collect_capsule_metrics(self):
        """Collect capsule engine metrics."""

        try:
            from live_capture.real_time_capsule_generator import (
                RealTimeCapsuleGenerator,
            )

            generator = RealTimeCapsuleGenerator()

            # Session metrics
            if hasattr(generator, "session_manager"):
                sessions = getattr(generator.session_manager, "sessions", {})
                self.metrics.record_gauge("uatp_active_sessions", len(sessions))

                # Session by platform
                platform_counts = {}
                for session in sessions.values():
                    platform = session.get("platform", "unknown")
                    platform_counts[platform] = platform_counts.get(platform, 0) + 1

                for platform, count in platform_counts.items():
                    self.metrics.record_gauge(
                        "uatp_sessions_by_platform", count, {"platform": platform}
                    )

        except Exception as e:
            logger.error(f"❌ Error collecting capsule metrics: {e}")

    async def _collect_auth_metrics(self):
        """Collect authentication metrics."""

        try:
            from auth.jwt_auth import get_authenticator

            authenticator = get_authenticator()
            stats = authenticator.get_user_stats()

            self.metrics.record_gauge("uatp_users_total", stats.get("total_users", 0))
            self.metrics.record_gauge("uatp_users_active", stats.get("active_users", 0))
            self.metrics.record_gauge(
                "uatp_refresh_tokens_active", stats.get("active_refresh_tokens", 0)
            )

            # Role distribution
            roles = stats.get("role_distribution", {})
            for role, count in roles.items():
                self.metrics.record_gauge("uatp_users_by_role", count, {"role": role})

        except Exception as e:
            logger.error(f"❌ Error collecting auth metrics: {e}")


# Global metrics instances
_metrics_collector = None
_performance_monitor = None
_system_collector = None
_app_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(get_metrics_collector())
    return _performance_monitor


def get_system_collector() -> SystemMetricsCollector:
    """Get the global system metrics collector."""
    global _system_collector
    if _system_collector is None:
        _system_collector = SystemMetricsCollector(get_metrics_collector())
    return _system_collector


def get_app_collector() -> ApplicationMetricsCollector:
    """Get the global application metrics collector."""
    global _app_collector
    if _app_collector is None:
        _app_collector = ApplicationMetricsCollector(get_metrics_collector())
    return _app_collector


async def main():
    """Test metrics collection system."""

    print("📊 Testing Metrics Collection System")
    print("=" * 40)

    # Get collectors
    metrics = get_metrics_collector()
    monitor = get_performance_monitor()
    system_collector = get_system_collector()
    app_collector = get_app_collector()

    # Test basic metrics
    print("\n📈 Testing basic metrics...")

    # Record some test metrics
    metrics.record_counter("test_counter", 1.0, {"service": "test"})
    metrics.record_gauge("test_gauge", 42.0, {"service": "test"})
    metrics.record_histogram("test_histogram", 1.5, {"service": "test"})

    # Test performance monitoring
    print("\n⏱️ Testing performance monitoring...")

    with monitor.timer("test_operation", {"operation": "test"}):
        await asyncio.sleep(0.1)  # Simulate work

    monitor.count("test_events", 1.0, {"event_type": "test"})
    monitor.gauge("test_value", 100.0, {"metric": "test"})

    # Test system metrics collection
    print("\n🖥️ Testing system metrics collection...")

    await system_collector.start()
    await asyncio.sleep(2)  # Let it collect some metrics
    await system_collector.stop()

    # Test application metrics collection
    print("\n🏗️ Testing application metrics collection...")

    await app_collector.start()
    await asyncio.sleep(2)  # Let it collect some metrics
    await app_collector.stop()

    # Show metrics summary
    print("\n📊 Metrics Summary:")
    summary = metrics.get_summary()

    print(f"Total metrics: {summary['total_metrics']}")
    print(f"Total points: {summary['total_points']}")
    print(f"Counters: {len(summary['counters'])}")
    print(f"Gauges: {len(summary['gauges'])}")
    print(f"Histograms: {len(summary['histogram_summaries'])}")

    # Show histogram summary
    if summary["histogram_summaries"]:
        print("\nHistogram summaries:")
        for name, stats in summary["histogram_summaries"].items():
            print(f"  {name}:")
            print(f"    Count: {stats['count']}")
            print(f"    Mean: {stats['mean']:.3f}")
            print(f"    P95: {stats['p95']:.3f}")

    print("\n✅ Metrics collection system test completed!")


if __name__ == "__main__":
    asyncio.run(main())
