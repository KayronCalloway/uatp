"""
Unit tests for Telemetry.
"""

from datetime import datetime, timezone

import pytest

from src.observability.telemetry import (
    FallbackMetric,
    LabeledFallbackMetric,
    MetricDefinition,
    MetricType,
    TelemetryCollector,
    TelemetryMiddleware,
    TraceEvent,
)


class TestMetricType:
    """Tests for MetricType enum."""

    def test_metric_type_values(self):
        """Test metric type values."""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.SUMMARY.value == "summary"


class TestFallbackMetric:
    """Tests for FallbackMetric class."""

    def test_create_fallback_metric(self):
        """Test creating a fallback metric."""
        metric = FallbackMetric("test_metric", MetricType.COUNTER)

        assert metric.name == "test_metric"
        assert metric.metric_type == MetricType.COUNTER
        assert metric.value == 0.0
        assert metric.observations == []
        assert metric.labels_values == {}

    def test_increment(self):
        """Test incrementing a counter."""
        metric = FallbackMetric("test_counter", MetricType.COUNTER)

        metric.inc()
        assert metric.value == 1.0

        metric.inc(5.0)
        assert metric.value == 6.0

    def test_observe(self):
        """Test observing histogram values."""
        metric = FallbackMetric("test_histogram", MetricType.HISTOGRAM)

        metric.observe(1.5)
        metric.observe(2.0)
        metric.observe(3.5)

        assert len(metric.observations) == 3
        assert metric.observations == [1.5, 2.0, 3.5]

    def test_observe_truncates(self):
        """Test observations truncate at 1000."""
        metric = FallbackMetric("test_histogram", MetricType.HISTOGRAM)

        # Add more than 1000 observations
        for i in range(1050):
            metric.observe(float(i))

        assert len(metric.observations) == 1000

    def test_set_gauge(self):
        """Test setting a gauge value."""
        metric = FallbackMetric("test_gauge", MetricType.GAUGE)

        metric.set(42.0)
        assert metric.value == 42.0

        metric.set(100.0)
        assert metric.value == 100.0

    def test_labels(self):
        """Test creating labeled metric."""
        metric = FallbackMetric("test_metric", MetricType.COUNTER)

        labeled = metric.labels(method="POST", status="200")

        assert isinstance(labeled, LabeledFallbackMetric)
        assert labeled.labels == {"method": "POST", "status": "200"}


class TestLabeledFallbackMetric:
    """Tests for LabeledFallbackMetric class."""

    def test_create_labeled_metric(self):
        """Test creating a labeled metric."""
        parent = FallbackMetric("test_metric", MetricType.COUNTER)
        labeled = LabeledFallbackMetric(parent, {"label": "value"})

        assert labeled.metric is parent
        assert labeled.labels == {"label": "value"}

    def test_labeled_increment(self):
        """Test incrementing labeled counter."""
        parent = FallbackMetric("test_metric", MetricType.COUNTER)
        labeled = parent.labels(key="val")

        labeled.inc()
        labeled.inc(2.0)

        assert parent.labels_values[labeled.label_key]["value"] == 3.0

    def test_labeled_observe(self):
        """Test observing labeled histogram."""
        parent = FallbackMetric("test_metric", MetricType.HISTOGRAM)
        labeled = parent.labels(key="val")

        labeled.observe(1.0)
        labeled.observe(2.0)

        obs = parent.labels_values[labeled.label_key]["observations"]
        assert len(obs) == 2

    def test_labeled_set(self):
        """Test setting labeled gauge."""
        parent = FallbackMetric("test_metric", MetricType.GAUGE)
        labeled = parent.labels(key="val")

        labeled.set(50.0)

        assert parent.labels_values[labeled.label_key]["value"] == 50.0

    def test_different_labels_separate(self):
        """Test different labels are stored separately."""
        parent = FallbackMetric("test_metric", MetricType.COUNTER)

        labeled1 = parent.labels(key="val1")
        labeled2 = parent.labels(key="val2")

        labeled1.inc(1.0)
        labeled2.inc(5.0)

        assert parent.labels_values[labeled1.label_key]["value"] == 1.0
        assert parent.labels_values[labeled2.label_key]["value"] == 5.0


class TestMetricDefinition:
    """Tests for MetricDefinition dataclass."""

    def test_create_metric_definition(self):
        """Test creating a metric definition."""
        definition = MetricDefinition(
            name="test_metric",
            description="Test metric description",
            metric_type=MetricType.COUNTER,
        )

        assert definition.name == "test_metric"
        assert definition.description == "Test metric description"
        assert definition.metric_type == MetricType.COUNTER
        assert definition.labels == []
        assert definition.buckets is None

    def test_metric_definition_with_labels(self):
        """Test metric definition with labels."""
        definition = MetricDefinition(
            name="test_metric",
            description="Test",
            metric_type=MetricType.COUNTER,
            labels=["method", "status"],
        )

        assert definition.labels == ["method", "status"]

    def test_histogram_definition_with_buckets(self):
        """Test histogram definition with buckets."""
        definition = MetricDefinition(
            name="test_histogram",
            description="Test histogram",
            metric_type=MetricType.HISTOGRAM,
            buckets=[0.1, 0.5, 1.0, 5.0],
        )

        assert definition.buckets == [0.1, 0.5, 1.0, 5.0]


class TestTraceEvent:
    """Tests for TraceEvent dataclass."""

    def test_create_trace_event(self):
        """Test creating a trace event."""
        now = datetime.now(timezone.utc)
        event = TraceEvent(
            name="test_operation",
            timestamp=now,
            duration_ms=150.5,
        )

        assert event.name == "test_operation"
        assert event.timestamp == now
        assert event.duration_ms == 150.5
        assert event.attributes == {}
        assert event.span_id == ""
        assert event.trace_id == ""

    def test_trace_event_with_attributes(self):
        """Test trace event with attributes."""
        event = TraceEvent(
            name="test_op",
            timestamp=datetime.now(timezone.utc),
            duration_ms=100.0,
            attributes={"key": "value", "count": 42},
            span_id="span_123",
            trace_id="trace_456",
        )

        assert event.attributes["key"] == "value"
        assert event.attributes["count"] == 42
        assert event.span_id == "span_123"
        assert event.trace_id == "trace_456"


class TestTelemetryCollector:
    """Tests for TelemetryCollector class (fallback mode)."""

    @pytest.fixture
    def collector(self):
        """Create a telemetry collector."""
        return TelemetryCollector(service_name="test-service")

    def test_create_collector(self, collector):
        """Test creating a telemetry collector."""
        assert collector.service_name == "test-service"
        assert collector.metrics is not None
        assert collector.traces == []

    def test_standard_metrics_defined(self, collector):
        """Test that standard metrics are defined."""
        assert "uatp_capsules_created_total" in collector.metrics
        assert "uatp_api_requests_total" in collector.metrics
        assert "uatp_system_health" in collector.metrics

    def test_increment_counter(self, collector):
        """Test incrementing a counter."""
        collector.increment_counter(
            "uatp_capsules_created_total",
            {"capsule_type": "test", "status": "success"},
        )

        # Should not raise
        assert True

    def test_increment_counter_not_found(self, collector):
        """Test incrementing non-existent counter."""
        # Should not raise, just log warning
        collector.increment_counter("nonexistent_metric")
        assert True

    def test_observe_histogram(self, collector):
        """Test observing a histogram."""
        collector.observe_histogram(
            "uatp_capsule_creation_duration_seconds",
            1.5,
            {"capsule_type": "test"},
        )

        # Should not raise
        assert True

    def test_set_gauge(self, collector):
        """Test setting a gauge."""
        collector.set_gauge(
            "uatp_system_health",
            1.0,
            {"component": "api"},
        )

        # Should not raise
        assert True

    def test_trace_operation(self, collector):
        """Test tracing an operation."""
        with collector.trace_operation("test_op", {"attr": "value"}):
            pass  # Do something

        assert len(collector.traces) == 1
        assert collector.traces[0].name == "test_op"

    def test_trace_truncation(self, collector):
        """Test that traces are truncated at 1000."""
        for i in range(1050):
            with collector.trace_operation(f"op_{i}"):
                pass

        assert len(collector.traces) == 1000

    def test_record_capsule_creation(self, collector):
        """Test recording capsule creation."""
        collector.record_capsule_creation("inference", "success", 1.5)

        # Should not raise
        assert True

    def test_record_api_request(self, collector):
        """Test recording API request."""
        collector.record_api_request("POST", "/api/test", 200, 0.5)

        # Should not raise
        assert True

    def test_record_ethics_evaluation(self, collector):
        """Test recording ethics evaluation."""
        collector.record_ethics_evaluation("allowed", "low")

        # Should not raise
        assert True

    def test_record_ethics_refusal(self, collector):
        """Test recording ethics refusal."""
        collector.record_ethics_evaluation("refused", "high")

        # Should not raise
        assert True

    def test_record_llm_request(self, collector):
        """Test recording LLM request."""
        collector.record_llm_request(
            provider="openai",
            model="gpt-4",
            status="success",
            duration_seconds=2.0,
            tokens_used=150,
            cost_usd=0.003,
        )

        # Should not raise
        assert True

    def test_set_system_health(self, collector):
        """Test setting system health."""
        collector.set_system_health("database", True)
        collector.set_system_health("api", False)

        # Should not raise
        assert True

    def test_set_active_connections(self, collector):
        """Test setting active connections."""
        collector.set_active_connections("http", 5)

        # Should not raise
        assert True

    def test_get_recent_traces(self, collector):
        """Test getting recent traces."""
        for i in range(10):
            with collector.trace_operation(f"op_{i}"):
                pass

        recent = collector.get_recent_traces(5)

        assert len(recent) == 5
        # Should be the last 5
        assert recent[0].name == "op_5"

    def test_get_metrics_summary(self, collector):
        """Test getting metrics summary."""
        summary = collector.get_metrics_summary()

        assert "total_metrics" in summary
        assert "total_traces" in summary
        assert "service_name" in summary
        assert summary["service_name"] == "test-service"

    def test_get_metric_data(self, collector):
        """Test getting metric data."""
        data = collector.get_metric_data("uatp_capsules_created_total")

        assert data is not None
        assert "name" in data

    def test_get_metric_data_not_found(self, collector):
        """Test getting non-existent metric data."""
        data = collector.get_metric_data("nonexistent")

        assert data is None


class TestTelemetryMiddleware:
    """Tests for TelemetryMiddleware class."""

    def test_middleware_as_decorator(self):
        """Test using middleware as decorator."""
        collector = TelemetryCollector("test")
        middleware = TelemetryMiddleware(collector)

        @middleware
        def test_function():
            return 42

        result = test_function()

        assert result == 42
        assert len(collector.traces) == 1

    def test_middleware_records_operation_name(self):
        """Test middleware records correct operation name."""
        collector = TelemetryCollector("test")
        middleware = TelemetryMiddleware(collector)

        @middleware
        def my_operation():
            pass

        my_operation()

        assert len(collector.traces) == 1
        assert "my_operation" in collector.traces[0].name
