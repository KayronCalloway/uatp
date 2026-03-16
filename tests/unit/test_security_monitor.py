"""
Unit tests for Security Monitor.
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.observability.security_monitor import (
    SecurityEvent,
    SecurityEventType,
    SecurityMonitor,
    get_security_monitor,
)


class TestSecurityEventType:
    """Tests for SecurityEventType enum."""

    def test_event_types_defined(self):
        """Test all security event types are defined."""
        assert SecurityEventType.SQL_INJECTION_ATTEMPT.value == "sql_injection_attempt"
        assert SecurityEventType.INVALID_INPUT.value == "invalid_input"
        assert SecurityEventType.AUTH_FAILURE.value == "auth_failure"
        assert SecurityEventType.RATE_LIMIT_EXCEEDED.value == "rate_limit_exceeded"
        assert SecurityEventType.SUSPICIOUS_QUERY.value == "suspicious_query"
        assert SecurityEventType.VALIDATION_FAILURE.value == "validation_failure"
        assert SecurityEventType.UNAUTHORIZED_ACCESS.value == "unauthorized_access"

    def test_all_types_exist(self):
        """Test all expected types exist."""
        types = [
            "SQL_INJECTION_ATTEMPT",
            "INVALID_INPUT",
            "AUTH_FAILURE",
            "RATE_LIMIT_EXCEEDED",
            "SUSPICIOUS_QUERY",
            "VALIDATION_FAILURE",
            "UNAUTHORIZED_ACCESS",
        ]

        for t in types:
            assert hasattr(SecurityEventType, t)


class TestSecurityEvent:
    """Tests for SecurityEvent dataclass."""

    def test_create_event(self):
        """Test creating a security event."""
        now = datetime.now(timezone.utc)
        event = SecurityEvent(
            event_type=SecurityEventType.AUTH_FAILURE,
            severity="medium",
            description="Login failed",
            timestamp=now,
        )

        assert event.event_type == SecurityEventType.AUTH_FAILURE
        assert event.severity == "medium"
        assert event.source_ip is None
        assert event.user_id is None

    def test_event_with_all_fields(self):
        """Test creating event with all fields."""
        now = datetime.now(timezone.utc)
        event = SecurityEvent(
            event_type=SecurityEventType.VALIDATION_FAILURE,
            severity="low",
            description="Invalid input",
            timestamp=now,
            source_ip="192.168.1.1",
            user_id="user_123",
            details={"field": "email", "value": "invalid"},
        )

        assert event.source_ip == "192.168.1.1"
        assert event.user_id == "user_123"
        assert event.details["field"] == "email"


class TestSecurityMonitorInit:
    """Tests for SecurityMonitor initialization."""

    def test_create_monitor(self):
        """Test creating a security monitor."""
        monitor = SecurityMonitor()

        assert monitor.alert_threshold == 5
        assert monitor.time_window == timedelta(minutes=5)
        assert len(monitor.recent_events) == 0

    def test_custom_parameters(self):
        """Test creating monitor with custom parameters."""
        monitor = SecurityMonitor(alert_threshold=10, time_window_minutes=15)

        assert monitor.alert_threshold == 10
        assert monitor.time_window == timedelta(minutes=15)

    def test_initializes_tracking_structures(self):
        """Test initializes tracking structures."""
        monitor = SecurityMonitor()

        assert hasattr(monitor, "recent_events")
        assert hasattr(monitor, "events_by_ip")
        assert hasattr(monitor, "events_by_user")
        assert hasattr(monitor, "event_counts")


class TestSecurityMonitorRecordEvent:
    """Tests for SecurityMonitor.record_event."""

    def test_record_simple_event(self):
        """Test recording a simple event."""
        monitor = SecurityMonitor()

        monitor.record_event(
            event_type=SecurityEventType.INVALID_INPUT,
            severity="low",
            description="Invalid email format",
        )

        assert len(monitor.recent_events) == 1
        assert monitor.event_counts[SecurityEventType.INVALID_INPUT] == 1

    def test_record_event_with_ip(self):
        """Test recording event with source IP."""
        monitor = SecurityMonitor()

        monitor.record_event(
            event_type=SecurityEventType.AUTH_FAILURE,
            severity="medium",
            description="Login failed",
            source_ip="10.0.0.1",
        )

        assert "10.0.0.1" in monitor.events_by_ip
        assert len(monitor.events_by_ip["10.0.0.1"]) == 1

    def test_record_event_with_user(self):
        """Test recording event with user ID."""
        monitor = SecurityMonitor()

        monitor.record_event(
            event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
            severity="high",
            description="Access denied",
            user_id="user_456",
        )

        assert "user_456" in monitor.events_by_user
        assert len(monitor.events_by_user["user_456"]) == 1

    def test_record_multiple_events(self):
        """Test recording multiple events."""
        monitor = SecurityMonitor()

        for i in range(5):
            monitor.record_event(
                event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                severity="low",
                description=f"Rate limit exceeded {i}",
            )

        assert len(monitor.recent_events) == 5
        assert monitor.event_counts[SecurityEventType.RATE_LIMIT_EXCEEDED] == 5

    def test_recent_events_limited(self):
        """Test recent events limited to 10000."""
        monitor = SecurityMonitor()

        # Add more than 10000 events
        for i in range(10100):
            monitor.record_event(
                event_type=SecurityEventType.INVALID_INPUT,
                severity="low",
                description=f"Event {i}",
            )

        assert len(monitor.recent_events) == 10000


class TestSecurityMonitorRecordSqlInjectionAttempt:
    """Tests for SecurityMonitor.record_sql_injection_attempt."""

    def test_records_sql_injection(self):
        """Test records SQL injection attempt."""
        monitor = SecurityMonitor()

        monitor.record_sql_injection_attempt(
            query="SELECT * FROM users WHERE id = '1 OR 1=1'",
            source_ip="10.0.0.1",
        )

        assert monitor.event_counts[SecurityEventType.SQL_INJECTION_ATTEMPT] == 1

    def test_truncates_query(self):
        """Test truncates long query."""
        monitor = SecurityMonitor()
        long_query = "SELECT * FROM " + "x" * 200

        monitor.record_sql_injection_attempt(query=long_query)

        event = monitor.recent_events[0]
        assert len(event.details["attempted_query"]) <= 100

    def test_severity_is_critical(self):
        """Test SQL injection has critical severity."""
        monitor = SecurityMonitor()

        monitor.record_sql_injection_attempt(query="DROP TABLE users")

        event = monitor.recent_events[0]
        assert event.severity == "critical"


class TestSecurityMonitorRecordValidationFailure:
    """Tests for SecurityMonitor.record_validation_failure."""

    def test_records_validation_failure(self):
        """Test records validation failure."""
        monitor = SecurityMonitor()

        monitor.record_validation_failure(
            field="email",
            value="not-an-email",
            reason="Invalid format",
        )

        assert monitor.event_counts[SecurityEventType.VALIDATION_FAILURE] == 1

    def test_sql_related_gets_medium_severity(self):
        """Test SQL-related validation gets medium severity."""
        monitor = SecurityMonitor()

        monitor.record_validation_failure(
            field="query",
            value="SELECT",
            reason="SQL injection detected",
        )

        event = monitor.recent_events[0]
        assert event.severity == "medium"

    def test_normal_validation_gets_low_severity(self):
        """Test normal validation gets low severity."""
        monitor = SecurityMonitor()

        monitor.record_validation_failure(
            field="age",
            value=-5,
            reason="Must be positive",
        )

        event = monitor.recent_events[0]
        assert event.severity == "low"

    def test_truncates_value(self):
        """Test truncates long value."""
        monitor = SecurityMonitor()
        long_value = "x" * 200

        monitor.record_validation_failure(
            field="text",
            value=long_value,
            reason="Too long",
        )

        event = monitor.recent_events[0]
        assert len(event.details["value"]) <= 50


class TestSecurityMonitorRecordAuthFailure:
    """Tests for SecurityMonitor.record_auth_failure."""

    def test_records_auth_failure(self):
        """Test records authentication failure."""
        monitor = SecurityMonitor()

        monitor.record_auth_failure(username="john_doe", source_ip="10.0.0.1")

        assert monitor.event_counts[SecurityEventType.AUTH_FAILURE] == 1

    def test_auth_failure_severity(self):
        """Test auth failure has medium severity."""
        monitor = SecurityMonitor()

        monitor.record_auth_failure(username="test")

        event = monitor.recent_events[0]
        assert event.severity == "medium"

    def test_includes_reason(self):
        """Test includes failure reason."""
        monitor = SecurityMonitor()

        monitor.record_auth_failure(
            username="test",
            reason="Account locked",
        )

        event = monitor.recent_events[0]
        assert event.details["reason"] == "Account locked"


class TestSecurityMonitorRecordRateLimit:
    """Tests for SecurityMonitor.record_rate_limit."""

    def test_records_rate_limit(self):
        """Test records rate limit event."""
        monitor = SecurityMonitor()

        monitor.record_rate_limit(endpoint="/api/capsules", source_ip="10.0.0.1")

        assert monitor.event_counts[SecurityEventType.RATE_LIMIT_EXCEEDED] == 1

    def test_rate_limit_severity(self):
        """Test rate limit has low severity."""
        monitor = SecurityMonitor()

        monitor.record_rate_limit(endpoint="/api/test")

        event = monitor.recent_events[0]
        assert event.severity == "low"


class TestSecurityMonitorCheckPatterns:
    """Tests for SecurityMonitor._check_patterns."""

    def test_detects_repeated_events_from_ip(self, capsys):
        """Test detects repeated events from same IP."""
        monitor = SecurityMonitor(alert_threshold=3, time_window_minutes=5)

        # Record multiple events from same IP
        for i in range(5):
            monitor.record_event(
                event_type=SecurityEventType.AUTH_FAILURE,
                severity="medium",
                description=f"Attempt {i}",
                source_ip="10.0.0.1",
            )

        captured = capsys.readouterr()
        assert "ATTACK PATTERN DETECTED" in captured.out

    def test_detects_repeated_events_from_user(self, capsys):
        """Test detects repeated events from same user."""
        monitor = SecurityMonitor(alert_threshold=3, time_window_minutes=5)

        # Record multiple events from same user
        for i in range(5):
            monitor.record_event(
                event_type=SecurityEventType.VALIDATION_FAILURE,
                severity="low",
                description=f"Attempt {i}",
                user_id="user_123",
            )

        captured = capsys.readouterr()
        assert "ATTACK PATTERN DETECTED" in captured.out

    def test_no_alert_below_threshold(self, capsys):
        """Test no alert below threshold."""
        monitor = SecurityMonitor(alert_threshold=10, time_window_minutes=5)

        for i in range(5):
            monitor.record_event(
                event_type=SecurityEventType.AUTH_FAILURE,
                severity="medium",
                description=f"Attempt {i}",
                source_ip="10.0.0.1",
            )

        captured = capsys.readouterr()
        assert "ATTACK PATTERN DETECTED" not in captured.out


class TestSecurityMonitorGetStats:
    """Tests for SecurityMonitor.get_stats."""

    def test_get_stats_empty(self):
        """Test get stats with no events."""
        monitor = SecurityMonitor()

        stats = monitor.get_stats()

        assert stats["total_events"] == 0
        assert stats["events_last_hour"] == 0

    def test_get_stats_with_events(self):
        """Test get stats with events."""
        monitor = SecurityMonitor()

        for i in range(10):
            monitor.record_event(
                event_type=SecurityEventType.INVALID_INPUT,
                severity="low",
                description=f"Event {i}",
            )

        stats = monitor.get_stats()

        assert stats["total_events"] == 10
        assert stats["events_last_hour"] == 10

    def test_severity_counts(self):
        """Test counts by severity."""
        monitor = SecurityMonitor()

        monitor.record_event(SecurityEventType.AUTH_FAILURE, "high", "Test 1")
        monitor.record_event(SecurityEventType.INVALID_INPUT, "low", "Test 2")
        monitor.record_event(
            SecurityEventType.SQL_INJECTION_ATTEMPT, "critical", "Test 3"
        )

        stats = monitor.get_stats()

        assert stats["by_severity"]["high"] == 1
        assert stats["by_severity"]["low"] == 1
        assert stats["by_severity"]["critical"] == 1

    def test_type_counts(self):
        """Test counts by event type."""
        monitor = SecurityMonitor()

        for i in range(5):
            monitor.record_event(SecurityEventType.AUTH_FAILURE, "medium", f"Event {i}")

        for i in range(3):
            monitor.record_event(
                SecurityEventType.RATE_LIMIT_EXCEEDED, "low", f"Event {i}"
            )

        stats = monitor.get_stats()

        assert stats["by_type"]["auth_failure"] == 5
        assert stats["by_type"]["rate_limit_exceeded"] == 3

    def test_top_offending_ips(self):
        """Test identifies top offending IPs."""
        monitor = SecurityMonitor()

        # IP 1: 10 events
        for i in range(10):
            monitor.record_event(
                SecurityEventType.AUTH_FAILURE,
                "medium",
                "Test",
                source_ip="192.168.1.1",
            )

        # IP 2: 5 events
        for i in range(5):
            monitor.record_event(
                SecurityEventType.AUTH_FAILURE,
                "medium",
                "Test",
                source_ip="192.168.1.2",
            )

        stats = monitor.get_stats()

        top_ips = stats["top_offending_ips"]
        assert len(top_ips) == 2
        assert top_ips[0]["ip"] == "192.168.1.1"
        assert top_ips[0]["event_count"] == 10

    def test_limits_top_ips_to_five(self):
        """Test limits top IPs to 5."""
        monitor = SecurityMonitor()

        # Create 10 different IPs with events
        for ip_num in range(10):
            for i in range(5):
                monitor.record_event(
                    SecurityEventType.AUTH_FAILURE,
                    "medium",
                    "Test",
                    source_ip=f"192.168.1.{ip_num}",
                )

        stats = monitor.get_stats()

        assert len(stats["top_offending_ips"]) <= 5


class TestSecurityMonitorGetRecentEvents:
    """Tests for SecurityMonitor.get_recent_events."""

    def test_get_recent_events_empty(self):
        """Test get recent events with no events."""
        monitor = SecurityMonitor()

        events = monitor.get_recent_events()

        assert events == []

    def test_get_recent_events_default_limit(self):
        """Test gets last 50 events by default."""
        monitor = SecurityMonitor()

        for i in range(100):
            monitor.record_event(
                SecurityEventType.INVALID_INPUT,
                "low",
                f"Event {i}",
            )

        events = monitor.get_recent_events()

        assert len(events) == 50

    def test_get_recent_events_custom_limit(self):
        """Test gets custom number of events."""
        monitor = SecurityMonitor()

        for i in range(50):
            monitor.record_event(
                SecurityEventType.INVALID_INPUT,
                "low",
                f"Event {i}",
            )

        events = monitor.get_recent_events(limit=10)

        assert len(events) == 10

    def test_events_in_reverse_order(self):
        """Test events returned in reverse order (newest first)."""
        monitor = SecurityMonitor()

        for i in range(5):
            monitor.record_event(
                SecurityEventType.INVALID_INPUT,
                "low",
                f"Event {i}",
            )

        events = monitor.get_recent_events()

        # Most recent should be Event 4
        assert "Event 4" in events[0]["description"]

    def test_event_includes_all_fields(self):
        """Test event dict includes all fields."""
        monitor = SecurityMonitor()

        monitor.record_event(
            event_type=SecurityEventType.AUTH_FAILURE,
            severity="medium",
            description="Test event",
            source_ip="10.0.0.1",
            user_id="user_1",
            details={"key": "value"},
        )

        events = monitor.get_recent_events()

        event = events[0]
        assert "type" in event
        assert "severity" in event
        assert "description" in event
        assert "timestamp" in event
        assert "source_ip" in event
        assert "user_id" in event
        assert "details" in event


class TestSecurityMonitorCheckAlerts:
    """Tests for SecurityMonitor.check_alerts."""

    def test_no_alerts_initially(self):
        """Test no alerts with no events."""
        monitor = SecurityMonitor()

        alerts = monitor.check_alerts()

        assert len(alerts) == 0

    def test_alert_critical_events(self):
        """Test alerts on high rate of critical events."""
        monitor = SecurityMonitor()

        for i in range(10):
            monitor.record_event(
                SecurityEventType.SQL_INJECTION_ATTEMPT,
                "critical",
                f"Attempt {i}",
            )

        alerts = monitor.check_alerts()

        # Should have critical event alert
        assert any("critical security events" in a.lower() for a in alerts)

    def test_alert_sql_injection_attempts(self):
        """Test alerts on SQL injection attempts."""
        monitor = SecurityMonitor()

        monitor.record_sql_injection_attempt(
            query="DROP TABLE users",
            source_ip="10.0.0.1",
        )

        alerts = monitor.check_alerts()

        # Should alert on SQL injection
        assert any("SQL injection" in a for a in alerts)

    def test_alert_many_auth_failures(self):
        """Test alerts on many auth failures."""
        monitor = SecurityMonitor()

        for i in range(15):
            monitor.record_auth_failure(
                username=f"user_{i}",
                source_ip="10.0.0.1",
            )

        alerts = monitor.check_alerts()

        # Should alert on auth failures
        assert any("authentication failures" in a.lower() for a in alerts)

    def test_no_alert_few_auth_failures(self):
        """Test no alert for few auth failures."""
        monitor = SecurityMonitor()

        for i in range(5):
            monitor.record_auth_failure(username=f"user_{i}")

        alerts = monitor.check_alerts()

        # Should not alert on few failures
        assert not any("authentication" in a.lower() for a in alerts)


class TestSecurityMonitorGlobalInstance:
    """Tests for global security monitor instance."""

    def test_get_security_monitor_returns_instance(self):
        """Test get_security_monitor returns instance."""
        monitor = get_security_monitor()

        assert isinstance(monitor, SecurityMonitor)

    def test_get_security_monitor_singleton(self):
        """Test get_security_monitor returns same instance."""
        monitor1 = get_security_monitor()
        monitor2 = get_security_monitor()

        assert monitor1 is monitor2


class TestSecurityMonitorIntegration:
    """Integration tests for security monitoring."""

    def test_realistic_attack_scenario(self, capsys):
        """Test realistic attack scenario detection."""
        monitor = SecurityMonitor(alert_threshold=3, time_window_minutes=5)

        # Simulate brute force attack - need > 10 for check_alerts
        for i in range(15):
            monitor.record_auth_failure(
                username=f"admin_{i}",
                source_ip="10.0.0.1",
            )

        captured = capsys.readouterr()

        # Should detect pattern
        assert "ATTACK PATTERN DETECTED" in captured.out

        # Check alerts - need > 10 auth failures
        alerts = monitor.check_alerts()
        assert len(alerts) > 0

    def test_mixed_severity_tracking(self):
        """Test tracks events of different severities."""
        monitor = SecurityMonitor()

        monitor.record_sql_injection_attempt(query="DROP TABLE")
        monitor.record_auth_failure(username="test")
        monitor.record_validation_failure("email", "bad", "Invalid")
        monitor.record_rate_limit("/api/test")

        stats = monitor.get_stats()

        assert stats["total_events"] == 4
        assert len(stats["by_severity"]) >= 2

    def test_ip_tracking_across_event_types(self):
        """Test tracks IP across different event types."""
        monitor = SecurityMonitor()

        source_ip = "192.168.1.100"

        monitor.record_auth_failure(username="user1", source_ip=source_ip)
        monitor.record_validation_failure("field", "val", "reason", source_ip=source_ip)
        monitor.record_rate_limit("/api/test", source_ip=source_ip)

        assert len(monitor.events_by_ip[source_ip]) == 3
