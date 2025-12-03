"""
Performance monitoring for UATP Capsule Engine.
Tracks query latency, connection pool usage, and database performance.
"""

import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import statistics


@dataclass
class QueryMetrics:
    """Metrics for a single query execution."""

    query_name: str
    duration_ms: float
    timestamp: datetime
    success: bool
    error: Optional[str] = None


@dataclass
class PerformanceStats:
    """Aggregated performance statistics."""

    total_queries: int = 0
    failed_queries: int = 0

    # Latency percentiles
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0

    # Connection pool
    pool_size: int = 0
    pool_utilization: float = 0.0

    # Recent query metrics (last 1000 queries)
    recent_queries: deque = field(default_factory=lambda: deque(maxlen=1000))


class PerformanceMonitor:
    """
    Monitor database and query performance in real-time.

    Features:
    - Query latency tracking (p50, p95, p99)
    - Connection pool monitoring
    - Slow query detection
    - Performance degradation alerts
    """

    def __init__(self, slow_query_threshold_ms: float = 100.0):
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.stats = PerformanceStats()
        self._query_times: Dict[str, List[float]] = {}

    async def track_query(self, query_name: str, coro):
        """
        Track execution time of a query coroutine.

        Usage:
            result = await monitor.track_query('load_capsules',
                                               db.fetch(query, params))
        """
        start_time = time.perf_counter()
        error = None
        success = True

        try:
            result = await coro
            return result
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Record metrics
            metric = QueryMetrics(
                query_name=query_name,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                success=success,
                error=error,
            )

            self._record_metric(metric)

            # Alert on slow queries
            if duration_ms > self.slow_query_threshold_ms:
                self._alert_slow_query(metric)

    def _record_metric(self, metric: QueryMetrics):
        """Record a query metric and update statistics."""
        self.stats.total_queries += 1
        if not metric.success:
            self.stats.failed_queries += 1

        # Add to recent queries
        self.stats.recent_queries.append(metric)

        # Track by query name
        if metric.query_name not in self._query_times:
            self._query_times[metric.query_name] = []
        self._query_times[metric.query_name].append(metric.duration_ms)

        # Update percentiles (calculate from recent successful queries)
        recent_durations = [
            q.duration_ms for q in self.stats.recent_queries if q.success
        ]

        if recent_durations:
            sorted_durations = sorted(recent_durations)
            n = len(sorted_durations)

            self.stats.p50_ms = sorted_durations[int(n * 0.50)]
            self.stats.p95_ms = sorted_durations[int(n * 0.95)]
            self.stats.p99_ms = sorted_durations[int(n * 0.99)]

    def _alert_slow_query(self, metric: QueryMetrics):
        """Log alert for slow queries."""
        print(
            f"⚠️  SLOW QUERY: {metric.query_name} took {metric.duration_ms:.2f}ms "
            f"(threshold: {self.slow_query_threshold_ms}ms)"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        success_rate = (
            (self.stats.total_queries - self.stats.failed_queries)
            / max(1, self.stats.total_queries)
        ) * 100

        return {
            "total_queries": self.stats.total_queries,
            "failed_queries": self.stats.failed_queries,
            "success_rate": f"{success_rate:.2f}%",
            "latency": {
                "p50_ms": round(self.stats.p50_ms, 2),
                "p95_ms": round(self.stats.p95_ms, 2),
                "p99_ms": round(self.stats.p99_ms, 2),
            },
            "slow_queries": sum(
                1
                for q in self.stats.recent_queries
                if q.duration_ms > self.slow_query_threshold_ms
            ),
            "recent_errors": [
                {
                    "query": q.query_name,
                    "error": q.error,
                    "timestamp": q.timestamp.isoformat(),
                }
                for q in list(self.stats.recent_queries)[-10:]
                if not q.success
            ],
        }

    def get_query_breakdown(self) -> Dict[str, Dict[str, float]]:
        """Get performance breakdown by query type."""
        breakdown = {}

        for query_name, durations in self._query_times.items():
            if durations:
                breakdown[query_name] = {
                    "count": len(durations),
                    "avg_ms": statistics.mean(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                }

        return breakdown

    def update_pool_metrics(self, pool_size: int, active_connections: int):
        """Update connection pool metrics."""
        self.stats.pool_size = pool_size
        self.stats.pool_utilization = (active_connections / max(1, pool_size)) * 100

        # Alert on high pool utilization
        if self.stats.pool_utilization > 80:
            print(
                f"⚠️  HIGH POOL UTILIZATION: {self.stats.pool_utilization:.1f}% "
                f"({active_connections}/{pool_size} connections)"
            )

    def check_alerts(self) -> List[str]:
        """Check for performance issues and return alerts."""
        alerts = []

        # Check p95 latency
        if self.stats.p95_ms > 500:
            alerts.append(
                f"CRITICAL: p95 latency is {self.stats.p95_ms:.2f}ms (threshold: 500ms)"
            )
        elif self.stats.p95_ms > 200:
            alerts.append(
                f"WARNING: p95 latency is {self.stats.p95_ms:.2f}ms (threshold: 200ms)"
            )

        # Check failure rate
        if self.stats.total_queries > 0:
            failure_rate = (self.stats.failed_queries / self.stats.total_queries) * 100
            if failure_rate > 5:
                alerts.append(
                    f"CRITICAL: Query failure rate is {failure_rate:.2f}% (threshold: 5%)"
                )
            elif failure_rate > 1:
                alerts.append(
                    f"WARNING: Query failure rate is {failure_rate:.2f}% (threshold: 1%)"
                )

        # Check pool utilization
        if self.stats.pool_utilization > 90:
            alerts.append(
                f"CRITICAL: Connection pool {self.stats.pool_utilization:.1f}% utilized (threshold: 90%)"
            )
        elif self.stats.pool_utilization > 70:
            alerts.append(
                f"WARNING: Connection pool {self.stats.pool_utilization:.1f}% utilized (threshold: 70%)"
            )

        return alerts


# Global monitor instance
_monitor = PerformanceMonitor(slow_query_threshold_ms=100.0)


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _monitor


async def track_query(query_name: str, coro):
    """
    Convenience function to track a query.

    Usage:
        from src.observability.performance_monitor import track_query

        result = await track_query('load_capsules', db.fetch(query, params))
    """
    return await _monitor.track_query(query_name, coro)
