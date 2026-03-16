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

# Performance and Security Monitoring
from .performance_monitor import PerformanceMonitor, get_monitor, track_query
from .security_monitor import SecurityEventType, SecurityMonitor, get_security_monitor

# Sentry integration is optional (requires sentry-sdk)
try:
    from .sentry_integration import (
        AgentErrorTracking,
        CapsuleErrorTracking,
        SafetyErrorTracking,
        add_agent_breadcrumb,
        add_capsule_breadcrumb,
        add_security_breadcrumb,
        capture_exception,
        capture_message,
        clear_user,
        flush_sentry,
        identify_user,
        monitored,
        sentry_context,
        sentry_transaction,
        setup_sentry,
    )

    _SENTRY_AVAILABLE = True
except ImportError:
    _SENTRY_AVAILABLE = False

    # Stub implementations for when sentry is not available
    def setup_sentry(*args, **kwargs):
        pass

    def capture_exception(*args, **kwargs):
        pass

    def capture_message(*args, **kwargs):
        pass

    def sentry_context(*args, **kwargs):
        from contextlib import contextmanager

        @contextmanager
        def _noop():
            yield

        return _noop()

    def sentry_transaction(*args, **kwargs):
        from contextlib import contextmanager

        @contextmanager
        def _noop():
            yield

        return _noop()

    def monitored(func):
        return func

    class CapsuleErrorTracking:
        pass

    class SafetyErrorTracking:
        pass

    class AgentErrorTracking:
        pass

    def add_capsule_breadcrumb(*args, **kwargs):
        pass

    def add_security_breadcrumb(*args, **kwargs):
        pass

    def add_agent_breadcrumb(*args, **kwargs):
        pass

    def identify_user(*args, **kwargs):
        pass

    def clear_user(*args, **kwargs):
        pass

    def flush_sentry(*args, **kwargs):
        pass


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
