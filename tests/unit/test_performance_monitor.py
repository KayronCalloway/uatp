"""
Unit tests for Performance Monitor.
"""

import asyncio

import pytest

from src.observability.performance_monitor import (
    PerformanceMonitor,
    PerformanceStats,
    QueryMetrics,
    get_monitor,
    track_query,
)


class TestQueryMetrics:
    """Tests for QueryMetrics dataclass."""

    def test_create_query_metrics(self):
        """Test creating query metrics."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        metrics = QueryMetrics(
            query_name="test_query",
            duration_ms=123.45,
            timestamp=now,
            success=True,
        )

        assert metrics.query_name == "test_query"
        assert metrics.duration_ms == 123.45
        assert metrics.success is True
        assert metrics.error is None

    def test_query_metrics_with_error(self):
        """Test query metrics with error."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        metrics = QueryMetrics(
            query_name="failing_query",
            duration_ms=50.0,
            timestamp=now,
            success=False,
            error="Connection timeout",
        )

        assert metrics.success is False
        assert metrics.error == "Connection timeout"


class TestPerformanceStats:
    """Tests for PerformanceStats dataclass."""

    def test_create_default_stats(self):
        """Test creating default performance stats."""
        stats = PerformanceStats()

        assert stats.total_queries == 0
        assert stats.failed_queries == 0
        assert stats.p50_ms == 0.0
        assert stats.pool_size == 0

    def test_recent_queries_deque(self):
        """Test recent queries uses deque with maxlen."""
        stats = PerformanceStats()

        assert hasattr(stats.recent_queries, "maxlen")
        assert stats.recent_queries.maxlen == 1000


class TestPerformanceMonitorInit:
    """Tests for PerformanceMonitor initialization."""

    def test_create_monitor(self):
        """Test creating a performance monitor."""
        monitor = PerformanceMonitor()

        assert monitor.slow_query_threshold_ms == 100.0
        assert isinstance(monitor.stats, PerformanceStats)

    def test_custom_threshold(self):
        """Test creating monitor with custom threshold."""
        monitor = PerformanceMonitor(slow_query_threshold_ms=250.0)

        assert monitor.slow_query_threshold_ms == 250.0


class TestPerformanceMonitorTrackQuery:
    """Tests for PerformanceMonitor.track_query."""

    @pytest.mark.asyncio
    async def test_track_successful_query(self):
        """Test tracking a successful query."""
        monitor = PerformanceMonitor()

        async def mock_query():
            await asyncio.sleep(0.01)
            return "result"

        result = await monitor.track_query("test_query", mock_query())

        assert result == "result"
        assert monitor.stats.total_queries == 1
        assert monitor.stats.failed_queries == 0

    @pytest.mark.asyncio
    async def test_track_failed_query(self):
        """Test tracking a failed query."""
        monitor = PerformanceMonitor()

        async def failing_query():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await monitor.track_query("failing_query", failing_query())

        assert monitor.stats.total_queries == 1
        assert monitor.stats.failed_queries == 1

    @pytest.mark.asyncio
    async def test_records_duration(self):
        """Test records query duration."""
        monitor = PerformanceMonitor()

        async def slow_query():
            await asyncio.sleep(0.05)
            return "done"

        await monitor.track_query("slow_query", slow_query())

        assert monitor.stats.total_queries == 1
        # Should have recorded duration > 50ms
        assert len(monitor.stats.recent_queries) == 1
        assert monitor.stats.recent_queries[0].duration_ms > 40

    @pytest.mark.asyncio
    async def test_tracks_multiple_queries(self):
        """Test tracking multiple queries."""
        monitor = PerformanceMonitor()

        async def query():
            return "result"

        for i in range(5):
            await monitor.track_query(f"query_{i}", query())

        assert monitor.stats.total_queries == 5

    @pytest.mark.asyncio
    async def test_slow_query_alert(self, capsys):
        """Test alerts on slow queries."""
        monitor = PerformanceMonitor(slow_query_threshold_ms=10.0)

        async def slow_query():
            await asyncio.sleep(0.02)  # 20ms
            return "result"

        await monitor.track_query("slow_test", slow_query())

        captured = capsys.readouterr()
        assert "SLOW QUERY" in captured.out


class TestPerformanceMonitorRecordMetric:
    """Tests for PerformanceMonitor._record_metric."""

    def test_increments_total_queries(self):
        """Test increments total queries."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        metric = QueryMetrics(
            query_name="test",
            duration_ms=50.0,
            timestamp=datetime.now(timezone.utc),
            success=True,
        )

        monitor._record_metric(metric)

        assert monitor.stats.total_queries == 1

    def test_increments_failed_queries(self):
        """Test increments failed queries."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        metric = QueryMetrics(
            query_name="test",
            duration_ms=50.0,
            timestamp=datetime.now(timezone.utc),
            success=False,
            error="Error",
        )

        monitor._record_metric(metric)

        assert monitor.stats.failed_queries == 1

    def test_adds_to_recent_queries(self):
        """Test adds to recent queries."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        metric = QueryMetrics(
            query_name="test",
            duration_ms=50.0,
            timestamp=datetime.now(timezone.utc),
            success=True,
        )

        monitor._record_metric(metric)

        assert len(monitor.stats.recent_queries) == 1

    def test_tracks_by_query_name(self):
        """Test tracks durations by query name."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        for i in range(3):
            metric = QueryMetrics(
                query_name="test_query",
                duration_ms=50.0 + i,
                timestamp=datetime.now(timezone.utc),
                success=True,
            )
            monitor._record_metric(metric)

        assert "test_query" in monitor._query_times
        assert len(monitor._query_times["test_query"]) == 3

    def test_updates_percentiles(self):
        """Test updates latency percentiles."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        # Record 100 queries with increasing duration
        for i in range(100):
            metric = QueryMetrics(
                query_name="test",
                duration_ms=float(i),
                timestamp=datetime.now(timezone.utc),
                success=True,
            )
            monitor._record_metric(metric)

        # Percentiles should be calculated
        assert monitor.stats.p50_ms > 0
        assert monitor.stats.p95_ms > monitor.stats.p50_ms
        assert monitor.stats.p99_ms > monitor.stats.p95_ms

    def test_recent_queries_limited(self):
        """Test recent queries limited to 1000."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        # Add more than 1000 queries
        for i in range(1100):
            metric = QueryMetrics(
                query_name="test",
                duration_ms=50.0,
                timestamp=datetime.now(timezone.utc),
                success=True,
            )
            monitor._record_metric(metric)

        assert len(monitor.stats.recent_queries) == 1000


class TestPerformanceMonitorGetStats:
    """Tests for PerformanceMonitor.get_stats."""

    def test_get_stats_empty(self):
        """Test get stats with no queries."""
        monitor = PerformanceMonitor()

        stats = monitor.get_stats()

        assert stats["total_queries"] == 0
        assert stats["failed_queries"] == 0
        assert "success_rate" in stats

    def test_get_stats_with_queries(self):
        """Test get stats with queries."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        for i in range(10):
            metric = QueryMetrics(
                query_name="test",
                duration_ms=50.0 + i,
                timestamp=datetime.now(timezone.utc),
                success=True,
            )
            monitor._record_metric(metric)

        stats = monitor.get_stats()

        assert stats["total_queries"] == 10
        assert "100.00%" in stats["success_rate"]

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        # 8 successful, 2 failed
        for i in range(10):
            metric = QueryMetrics(
                query_name="test",
                duration_ms=50.0,
                timestamp=datetime.now(timezone.utc),
                success=i < 8,
            )
            monitor._record_metric(metric)

        stats = monitor.get_stats()

        assert "80.00%" in stats["success_rate"]

    def test_includes_latency_metrics(self):
        """Test includes latency metrics."""
        monitor = PerformanceMonitor()

        stats = monitor.get_stats()

        assert "latency" in stats
        assert "p50_ms" in stats["latency"]
        assert "p95_ms" in stats["latency"]
        assert "p99_ms" in stats["latency"]

    def test_counts_slow_queries(self):
        """Test counts slow queries."""
        monitor = PerformanceMonitor(slow_query_threshold_ms=100.0)
        from datetime import datetime, timezone

        # Add fast and slow queries
        for i in range(10):
            metric = QueryMetrics(
                query_name="test",
                duration_ms=50.0 if i < 7 else 150.0,  # 3 slow
                timestamp=datetime.now(timezone.utc),
                success=True,
            )
            monitor._record_metric(metric)

        stats = monitor.get_stats()

        assert stats["slow_queries"] == 3

    def test_includes_recent_errors(self):
        """Test includes recent errors."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        # Add successful and failed queries
        for i in range(5):
            metric = QueryMetrics(
                query_name=f"query_{i}",
                duration_ms=50.0,
                timestamp=datetime.now(timezone.utc),
                success=i > 2,
                error="Error" if i <= 2 else None,
            )
            monitor._record_metric(metric)

        stats = monitor.get_stats()

        assert "recent_errors" in stats
        assert len(stats["recent_errors"]) == 3


class TestPerformanceMonitorGetQueryBreakdown:
    """Tests for PerformanceMonitor.get_query_breakdown."""

    def test_empty_breakdown(self):
        """Test breakdown with no queries."""
        monitor = PerformanceMonitor()

        breakdown = monitor.get_query_breakdown()

        assert breakdown == {}

    def test_breakdown_by_query_type(self):
        """Test breakdown by query type."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        # Record different query types
        for query_name in ["select_capsules", "insert_capsule", "update_capsule"]:
            for i in range(5):
                metric = QueryMetrics(
                    query_name=query_name,
                    duration_ms=50.0 + i,
                    timestamp=datetime.now(timezone.utc),
                    success=True,
                )
                monitor._record_metric(metric)

        breakdown = monitor.get_query_breakdown()

        assert "select_capsules" in breakdown
        assert "insert_capsule" in breakdown
        assert "update_capsule" in breakdown

    def test_breakdown_includes_statistics(self):
        """Test breakdown includes statistics."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        for i in range(10):
            metric = QueryMetrics(
                query_name="test_query",
                duration_ms=float(i * 10),
                timestamp=datetime.now(timezone.utc),
                success=True,
            )
            monitor._record_metric(metric)

        breakdown = monitor.get_query_breakdown()

        assert "count" in breakdown["test_query"]
        assert "avg_ms" in breakdown["test_query"]
        assert "min_ms" in breakdown["test_query"]
        assert "max_ms" in breakdown["test_query"]

        assert breakdown["test_query"]["count"] == 10
        assert breakdown["test_query"]["min_ms"] == 0.0
        assert breakdown["test_query"]["max_ms"] == 90.0


class TestPerformanceMonitorUpdatePoolMetrics:
    """Tests for PerformanceMonitor.update_pool_metrics."""

    def test_updates_pool_size(self):
        """Test updates pool size."""
        monitor = PerformanceMonitor()

        monitor.update_pool_metrics(pool_size=10, active_connections=5)

        assert monitor.stats.pool_size == 10
        assert monitor.stats.pool_utilization == 50.0

    def test_calculates_utilization(self):
        """Test calculates pool utilization."""
        monitor = PerformanceMonitor()

        monitor.update_pool_metrics(pool_size=20, active_connections=15)

        assert monitor.stats.pool_utilization == 75.0

    def test_full_utilization(self):
        """Test 100% pool utilization."""
        monitor = PerformanceMonitor()

        monitor.update_pool_metrics(pool_size=10, active_connections=10)

        assert monitor.stats.pool_utilization == 100.0

    def test_high_utilization_alert(self, capsys):
        """Test alerts on high pool utilization."""
        monitor = PerformanceMonitor()

        monitor.update_pool_metrics(pool_size=10, active_connections=9)

        captured = capsys.readouterr()
        assert "HIGH POOL UTILIZATION" in captured.out

    def test_no_alert_low_utilization(self, capsys):
        """Test no alert for low utilization."""
        monitor = PerformanceMonitor()

        monitor.update_pool_metrics(pool_size=10, active_connections=5)

        captured = capsys.readouterr()
        assert "HIGH POOL UTILIZATION" not in captured.out


class TestPerformanceMonitorCheckAlerts:
    """Tests for PerformanceMonitor.check_alerts."""

    def test_no_alerts_initially(self):
        """Test no alerts initially."""
        monitor = PerformanceMonitor()

        alerts = monitor.check_alerts()

        assert len(alerts) == 0

    def test_alert_high_p95_latency(self):
        """Test alerts on high p95 latency."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        # Add queries to push p95 high
        for i in range(100):
            metric = QueryMetrics(
                query_name="test",
                duration_ms=600.0,  # High latency
                timestamp=datetime.now(timezone.utc),
                success=True,
            )
            monitor._record_metric(metric)

        alerts = monitor.check_alerts()

        # Should have critical alert
        assert any("CRITICAL" in a and "p95" in a for a in alerts)

    def test_alert_warning_p95_latency(self):
        """Test warning alert for moderate p95 latency."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        # Add queries to push p95 to 250ms (warning threshold)
        for i in range(100):
            metric = QueryMetrics(
                query_name="test",
                duration_ms=250.0,
                timestamp=datetime.now(timezone.utc),
                success=True,
            )
            monitor._record_metric(metric)

        alerts = monitor.check_alerts()

        # Should have warning
        assert any("WARNING" in a and "p95" in a for a in alerts)

    def test_alert_high_failure_rate(self):
        """Test alerts on high failure rate."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        # 6 failures out of 10 = 60% failure rate
        for i in range(10):
            metric = QueryMetrics(
                query_name="test",
                duration_ms=50.0,
                timestamp=datetime.now(timezone.utc),
                success=i >= 6,
            )
            monitor._record_metric(metric)

        alerts = monitor.check_alerts()

        # Should have critical alert
        assert any("CRITICAL" in a and "failure rate" in a for a in alerts)

    def test_alert_warning_failure_rate(self):
        """Test warning for moderate failure rate."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        # 2 failures out of 100 = 2% failure rate
        for i in range(100):
            metric = QueryMetrics(
                query_name="test",
                duration_ms=50.0,
                timestamp=datetime.now(timezone.utc),
                success=i >= 2,
            )
            monitor._record_metric(metric)

        alerts = monitor.check_alerts()

        # Should have warning
        assert any("WARNING" in a and "failure rate" in a for a in alerts)

    def test_alert_high_pool_utilization(self):
        """Test alerts on high pool utilization."""
        monitor = PerformanceMonitor()

        monitor.update_pool_metrics(pool_size=10, active_connections=9)

        alerts = monitor.check_alerts()

        # Should have warning
        assert any("WARNING" in a and "pool" in a.lower() for a in alerts)

    def test_alert_critical_pool_utilization(self):
        """Test critical alert for very high pool utilization."""
        monitor = PerformanceMonitor()

        monitor.update_pool_metrics(pool_size=10, active_connections=10)

        alerts = monitor.check_alerts()

        # Should have critical alert
        assert any("CRITICAL" in a and "pool" in a.lower() for a in alerts)

    def test_multiple_alerts(self):
        """Test can have multiple alerts."""
        monitor = PerformanceMonitor()
        from datetime import datetime, timezone

        # Create high latency
        for i in range(100):
            metric = QueryMetrics(
                query_name="test",
                duration_ms=600.0,
                timestamp=datetime.now(timezone.utc),
                success=False,  # Also create failures
            )
            monitor._record_metric(metric)

        # Create high pool utilization
        monitor.update_pool_metrics(pool_size=10, active_connections=10)

        alerts = monitor.check_alerts()

        # Should have multiple alerts
        assert len(alerts) >= 2


class TestPerformanceMonitorGlobalInstance:
    """Tests for global monitor instance."""

    def test_get_monitor_returns_instance(self):
        """Test get_monitor returns monitor instance."""
        monitor = get_monitor()

        assert isinstance(monitor, PerformanceMonitor)

    def test_get_monitor_singleton(self):
        """Test get_monitor returns same instance."""
        monitor1 = get_monitor()
        monitor2 = get_monitor()

        assert monitor1 is monitor2

    @pytest.mark.asyncio
    async def test_track_query_convenience_function(self):
        """Test track_query convenience function."""

        async def test_coro():
            return "result"

        result = await track_query("test", test_coro())

        assert result == "result"


class TestPerformanceMonitorIntegration:
    """Integration tests for performance monitoring."""

    @pytest.mark.asyncio
    async def test_realistic_workload(self):
        """Test with realistic workload."""
        monitor = PerformanceMonitor(slow_query_threshold_ms=100.0)

        # Simulate various queries
        async def fast_query():
            await asyncio.sleep(0.01)
            return "fast"

        async def medium_query():
            await asyncio.sleep(0.05)
            return "medium"

        async def slow_query():
            await asyncio.sleep(0.15)
            return "slow"

        # Execute mix of queries
        await monitor.track_query("fast_1", fast_query())
        await monitor.track_query("medium_1", medium_query())
        await monitor.track_query("slow_1", slow_query())

        # Check statistics
        stats = monitor.get_stats()
        assert stats["total_queries"] == 3
        assert stats["slow_queries"] >= 1

        # Check breakdown
        breakdown = monitor.get_query_breakdown()
        assert len(breakdown) == 3

    @pytest.mark.asyncio
    async def test_handles_errors_gracefully(self):
        """Test handles errors and continues monitoring."""
        monitor = PerformanceMonitor()

        async def good_query():
            return "ok"

        async def bad_query():
            raise RuntimeError("Failed")

        # Mix of good and bad
        await monitor.track_query("good_1", good_query())

        with pytest.raises(RuntimeError):
            await monitor.track_query("bad_1", bad_query())

        await monitor.track_query("good_2", good_query())

        # Should track all attempts
        assert monitor.stats.total_queries == 3
        assert monitor.stats.failed_queries == 1
