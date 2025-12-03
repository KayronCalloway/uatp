"""
Observability Module

Provides comprehensive observability for UATP Capsule Engine including:
- Distributed Tracing (OpenTelemetry)
- Error Tracking (Sentry)
- Performance Monitoring (Real-time query latency, connection pool metrics)
- Security Monitoring (Attack detection, validation tracking)
- Application Performance Monitoring (APM)

Usage:
    from src.observability import setup_sentry
    from src.observability import capture_exception
    from src.observability import get_monitor, get_security_monitor

    # Setup error tracking
    setup_sentry(dsn="https://your-dsn@sentry.io/project")

    # Capture errors
    try:
        risky_operation()
    except Exception as e:
        capture_exception(e)

    # Get performance metrics
    perf_monitor = get_monitor()
    stats = perf_monitor.get_stats()

    # Check security events
    sec_monitor = get_security_monitor()
    events = sec_monitor.get_recent_events()
"""

from .sentry_integration import (
    setup_sentry,
    capture_exception,
    capture_message,
    sentry_context,
    sentry_transaction,
    monitored,
    CapsuleErrorTracking,
    SafetyErrorTracking,
    AgentErrorTracking,
    add_capsule_breadcrumb,
    add_security_breadcrumb,
    add_agent_breadcrumb,
    identify_user,
    clear_user,
    flush_sentry,
)

# Performance and Security Monitoring
from .performance_monitor import PerformanceMonitor, get_monitor, track_query

from .security_monitor import SecurityMonitor, SecurityEventType, get_security_monitor

__all__ = [
    # Error Tracking
    "setup_sentry",
    "capture_exception",
    "capture_message",
    "sentry_context",
    "sentry_transaction",
    "monitored",
    "CapsuleErrorTracking",
    "SafetyErrorTracking",
    "AgentErrorTracking",
    "add_capsule_breadcrumb",
    "add_security_breadcrumb",
    "add_agent_breadcrumb",
    "identify_user",
    "clear_user",
    "flush_sentry",
    # Performance Monitoring
    "PerformanceMonitor",
    "get_monitor",
    "track_query",
    # Security Monitoring
    "SecurityMonitor",
    "SecurityEventType",
    "get_security_monitor",
]
