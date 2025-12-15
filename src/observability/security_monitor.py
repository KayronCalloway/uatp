"""
Security monitoring for UATP Capsule Engine.
Tracks authentication failures, validation errors, and potential attacks.
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from src.utils.timezone_utils import utc_now


class SecurityEventType(Enum):
    """Types of security events to track."""

    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    INVALID_INPUT = "invalid_input"
    AUTH_FAILURE = "auth_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_QUERY = "suspicious_query"
    VALIDATION_FAILURE = "validation_failure"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


@dataclass
class SecurityEvent:
    """A single security event."""

    event_type: SecurityEventType
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    timestamp: datetime
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SecurityMonitor:
    """
    Monitor security events and detect potential attacks.

    Features:
    - Track failed authentication attempts
    - Detect SQL injection attempts
    - Monitor validation failures
    - Identify suspicious patterns (rate limiting, brute force)
    - Alert on anomalous behavior
    """

    def __init__(self, alert_threshold: int = 5, time_window_minutes: int = 5):
        self.alert_threshold = alert_threshold
        self.time_window = timedelta(minutes=time_window_minutes)

        # Store recent events (last 10,000)
        self.recent_events: deque = deque(maxlen=10000)

        # Track events by IP address
        self.events_by_ip: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Track events by user
        self.events_by_user: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Counters
        self.event_counts: Dict[SecurityEventType, int] = defaultdict(int)

    def record_event(
        self,
        event_type: SecurityEventType,
        severity: str,
        description: str,
        source_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Record a security event."""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            description=description,
            timestamp=utc_now(),
            source_ip=source_ip,
            user_id=user_id,
            details=details or {},
        )

        # Store event
        self.recent_events.append(event)
        self.event_counts[event_type] += 1

        if source_ip:
            self.events_by_ip[source_ip].append(event)

        if user_id:
            self.events_by_user[user_id].append(event)

        # Check for patterns and alert
        self._check_patterns(event)

        # Log based on severity
        self._log_event(event)

    def _log_event(self, event: SecurityEvent):
        """Log security event based on severity."""
        emoji_map = {"low": "ℹ️", "medium": "⚠️", "high": "🚨", "critical": "🔥"}

        emoji = emoji_map.get(event.severity, "❓")
        print(f"{emoji} SECURITY [{event.severity.upper()}]: {event.description}")

        if event.source_ip:
            print(f"   Source IP: {event.source_ip}")

        if event.details:
            for key, value in event.details.items():
                print(f"   {key}: {value}")

    def _check_patterns(self, event: SecurityEvent):
        """Check for suspicious patterns."""
        now = utc_now()

        # Check for repeated events from same IP
        if event.source_ip:
            recent_from_ip = [
                e
                for e in self.events_by_ip[event.source_ip]
                if (now - e.timestamp) < self.time_window
            ]

            if len(recent_from_ip) >= self.alert_threshold:
                self._alert_pattern(
                    f"Multiple security events from IP {event.source_ip}",
                    f"{len(recent_from_ip)} events in {self.time_window.total_seconds() / 60:.1f} minutes",
                )

        # Check for repeated events from same user
        if event.user_id:
            recent_from_user = [
                e
                for e in self.events_by_user[event.user_id]
                if (now - e.timestamp) < self.time_window
            ]

            if len(recent_from_user) >= self.alert_threshold:
                self._alert_pattern(
                    f"Multiple security events from user {event.user_id}",
                    f"{len(recent_from_user)} events in {self.time_window.total_seconds() / 60:.1f} minutes",
                )

    def _alert_pattern(self, title: str, details: str):
        """Alert on detected attack pattern."""
        print(f"🚨 ATTACK PATTERN DETECTED: {title}")
        print(f"   {details}")
        print("   Consider blocking source or enabling additional security measures")

    def record_sql_injection_attempt(
        self, query: str, source_ip: Optional[str] = None, user_id: Optional[str] = None
    ):
        """Record a potential SQL injection attempt."""
        self.record_event(
            event_type=SecurityEventType.SQL_INJECTION_ATTEMPT,
            severity="critical",
            description="SQL injection attempt detected",
            source_ip=source_ip,
            user_id=user_id,
            details={"attempted_query": query[:100]},  # First 100 chars
        )

    def record_validation_failure(
        self, field: str, value: Any, reason: str, source_ip: Optional[str] = None
    ):
        """Record input validation failure."""
        severity = (
            "medium"
            if "sql" in reason.lower() or "injection" in reason.lower()
            else "low"
        )

        self.record_event(
            event_type=SecurityEventType.VALIDATION_FAILURE,
            severity=severity,
            description=f"Validation failed for {field}",
            source_ip=source_ip,
            details={
                "field": field,
                "value": str(value)[:50],  # First 50 chars
                "reason": reason,
            },
        )

    def record_auth_failure(
        self,
        username: str,
        source_ip: Optional[str] = None,
        reason: str = "Invalid credentials",
    ):
        """Record authentication failure."""
        self.record_event(
            event_type=SecurityEventType.AUTH_FAILURE,
            severity="medium",
            description=f"Authentication failed for user: {username}",
            source_ip=source_ip,
            details={"username": username, "reason": reason},
        )

    def record_rate_limit(
        self,
        endpoint: str,
        source_ip: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Record rate limit exceeded."""
        self.record_event(
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            severity="low",
            description=f"Rate limit exceeded for {endpoint}",
            source_ip=source_ip,
            user_id=user_id,
            details={"endpoint": endpoint},
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        now = utc_now()

        # Events in last hour
        recent_hour = [
            e for e in self.recent_events if (now - e.timestamp) < timedelta(hours=1)
        ]

        # Events by severity
        severity_counts = defaultdict(int)
        for event in recent_hour:
            severity_counts[event.severity] += 1

        # Events by type
        type_counts = defaultdict(int)
        for event in recent_hour:
            type_counts[event.event_type.value] += 1

        # Top offending IPs
        ip_counts = defaultdict(int)
        for event in recent_hour:
            if event.source_ip:
                ip_counts[event.source_ip] += 1

        top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_events": len(self.recent_events),
            "events_last_hour": len(recent_hour),
            "by_severity": dict(severity_counts),
            "by_type": dict(type_counts),
            "top_offending_ips": [
                {"ip": ip, "event_count": count} for ip, count in top_ips
            ],
            "all_time_counts": {
                event_type.value: count
                for event_type, count in self.event_counts.items()
            },
        }

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent security events."""
        recent = list(self.recent_events)[-limit:]

        return [
            {
                "type": event.event_type.value,
                "severity": event.severity,
                "description": event.description,
                "timestamp": event.timestamp.isoformat(),
                "source_ip": event.source_ip,
                "user_id": event.user_id,
                "details": event.details,
            }
            for event in reversed(recent)
        ]

    def check_alerts(self) -> List[str]:
        """Check for security issues requiring attention."""
        alerts = []
        now = utc_now()

        # Check for high rate of critical events
        recent_hour = [
            e for e in self.recent_events if (now - e.timestamp) < timedelta(hours=1)
        ]

        critical_events = [e for e in recent_hour if e.severity == "critical"]
        if len(critical_events) > 5:
            alerts.append(
                f"CRITICAL: {len(critical_events)} critical security events in last hour"
            )

        # Check for SQL injection attempts
        sql_injection_attempts = [
            e
            for e in recent_hour
            if e.event_type == SecurityEventType.SQL_INJECTION_ATTEMPT
        ]
        if sql_injection_attempts:
            alerts.append(
                f"CRITICAL: {len(sql_injection_attempts)} SQL injection attempts detected"
            )

        # Check for auth failure patterns
        auth_failures = [
            e for e in recent_hour if e.event_type == SecurityEventType.AUTH_FAILURE
        ]
        if len(auth_failures) > 10:
            alerts.append(
                f"WARNING: {len(auth_failures)} authentication failures in last hour"
            )

        return alerts


# Global security monitor instance
_security_monitor = SecurityMonitor(alert_threshold=5, time_window_minutes=5)


def get_security_monitor() -> SecurityMonitor:
    """Get the global security monitor instance."""
    return _security_monitor
