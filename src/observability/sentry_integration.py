"""
Sentry Error Tracking Integration

Implements comprehensive error tracking and monitoring using Sentry, including:
- Automatic exception capture
- Performance monitoring
- Custom error grouping
- User context tracking
- Breadcrumb logging
- Release tracking
- Environment-specific configuration

Key Features:
1. Automatic error capture with stack traces
2. Performance transaction monitoring
3. Custom tags and context
4. User identification
5. Breadcrumb tracking for debugging
6. Release and environment tracking
7. Sample rate configuration
8. Error filtering and scrubbing

Usage:
    from src.observability.sentry_integration import setup_sentry, capture_exception

    # Setup Sentry (in main.py)
    setup_sentry(
        dsn="https://your-dsn@sentry.io/project-id",
        environment="production",
        release="1.0.0"
    )

    # Capture exceptions
    try:
        risky_operation()
    except Exception as e:
        capture_exception(e, extra={"capsule_id": capsule_id})

    # Add context
    from src.observability.sentry_integration import sentry_context
    with sentry_context(user_id="user_123", operation="create_capsule"):
        create_capsule()

    # Performance monitoring
    from src.observability.sentry_integration import sentry_transaction
    with sentry_transaction("capsule_verification", "task"):
        verify_capsule()
"""

import logging
import os
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import sentry_sdk
from sentry_sdk import (
    add_breadcrumb,
    configure_scope,
    push_scope,
    set_user,
)
from sentry_sdk import capture_exception as sentry_capture_exception
from sentry_sdk import capture_message as sentry_capture_message
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

try:
    from sentry_sdk.integrations.quart import QuartIntegration

    QUART_AVAILABLE = True
except ImportError:
    QUART_AVAILABLE = False

logger = logging.getLogger(__name__)


class SentryConfig:
    """Sentry configuration"""

    def __init__(
        self,
        dsn: Optional[str] = None,
        environment: str = "production",
        release: Optional[str] = None,
        traces_sample_rate: float = 0.1,
        profiles_sample_rate: float = 0.1,
        send_default_pii: bool = False,
        attach_stacktrace: bool = True,
        max_breadcrumbs: int = 100,
        debug: bool = False,
    ):
        self.dsn = dsn or os.getenv("SENTRY_DSN")
        self.environment = environment
        self.release = release or os.getenv("RELEASE_VERSION", "unknown")
        self.traces_sample_rate = traces_sample_rate
        self.profiles_sample_rate = profiles_sample_rate
        self.send_default_pii = send_default_pii
        self.attach_stacktrace = attach_stacktrace
        self.max_breadcrumbs = max_breadcrumbs
        self.debug = debug


class SentryManager:
    """
    Manages Sentry error tracking and performance monitoring
    """

    def __init__(self, config: Optional[SentryConfig] = None):
        self.config = config or SentryConfig()
        self._initialized = False

    def setup(self):
        """Initialize Sentry"""

        if self._initialized:
            logger.warning("Sentry already initialized")
            return

        if not self.config.dsn:
            logger.warning("Sentry DSN not configured, error tracking disabled")
            return

        # Prepare integrations
        integrations = self._get_integrations()

        # Initialize Sentry SDK
        sentry_sdk.init(
            dsn=self.config.dsn,
            environment=self.config.environment,
            release=self.config.release,
            traces_sample_rate=self.config.traces_sample_rate,
            profiles_sample_rate=self.config.profiles_sample_rate,
            send_default_pii=self.config.send_default_pii,
            attach_stacktrace=self.config.attach_stacktrace,
            max_breadcrumbs=self.config.max_breadcrumbs,
            debug=self.config.debug,
            integrations=integrations,
            before_send=self._before_send,
            before_breadcrumb=self._before_breadcrumb,
        )

        self._initialized = True

        logger.info(
            "Sentry initialized",
            environment=self.config.environment,
            release=self.config.release,
            traces_sample_rate=self.config.traces_sample_rate,
        )

    def _get_integrations(self) -> List[Any]:
        """Get Sentry integrations"""

        integrations = [
            # Logging integration (capture ERROR and CRITICAL logs)
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            # SQLAlchemy integration
            SqlalchemyIntegration(),
            # Redis integration
            RedisIntegration(),
            # Asyncio integration
            AsyncioIntegration(),
            # HTTPX integration (for async HTTP)
            HttpxIntegration(),
        ]

        # Add Quart integration if available
        if QUART_AVAILABLE:
            integrations.append(QuartIntegration())

        return integrations

    def _before_send(
        self, event: Dict[str, Any], hint: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Filter and modify events before sending to Sentry.

        This is where you can:
        - Filter out specific errors
        - Scrub sensitive data
        - Add additional context
        """

        # Filter out health check errors
        if "request" in event:
            url = event["request"].get("url", "")
            if "/health" in url or "/metrics" in url:
                return None

        # Scrub sensitive data from event
        event = self._scrub_sensitive_data(event)

        return event

    def _before_breadcrumb(
        self, crumb: Dict[str, Any], hint: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Filter and modify breadcrumbs before adding to event.
        """

        # Skip noisy breadcrumbs
        if crumb.get("category") in ["console", "ui.click"]:
            return None

        return crumb

    def _scrub_sensitive_data(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Scrub sensitive data from event"""

        sensitive_keys = [
            "password",
            "secret",
            "token",
            "api_key",
            "auth",
            "credit_card",
            "ssn",
            "private_key",
            "signing_key",
        ]

        def scrub_dict(d: Dict[str, Any]):
            for key, value in list(d.items()):
                # Check if key contains sensitive terms
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    d[key] = "[REDACTED]"
                elif isinstance(value, dict):
                    scrub_dict(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            scrub_dict(item)

        scrub_dict(event)
        return event

    def is_initialized(self) -> bool:
        """Check if Sentry is initialized"""
        return self._initialized


# Global Sentry manager
sentry_manager = SentryManager()


def setup_sentry(
    dsn: Optional[str] = None,
    environment: str = "production",
    release: Optional[str] = None,
    traces_sample_rate: float = 0.1,
):
    """
    Setup Sentry error tracking.

    Args:
        dsn: Sentry DSN (or use SENTRY_DSN env var)
        environment: Environment name (production, staging, development)
        release: Release version
        traces_sample_rate: Percentage of transactions to sample (0.0-1.0)
    """

    config = SentryConfig(
        dsn=dsn,
        environment=environment,
        release=release,
        traces_sample_rate=traces_sample_rate,
        debug=(environment == "development"),
    )

    sentry_manager.config = config
    sentry_manager.setup()


def capture_exception(
    exception: Exception,
    level: str = "error",
    extra: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    user: Optional[Dict[str, Any]] = None,
):
    """
    Capture exception to Sentry with context.

    Args:
        exception: Exception to capture
        level: Severity level (fatal, error, warning, info, debug)
        extra: Additional context data
        tags: Tags for grouping and filtering
        user: User information

    Usage:
        try:
            create_capsule()
        except Exception as e:
            capture_exception(e, extra={"capsule_id": "123"}, tags={"operation": "create"})
    """

    if not sentry_manager.is_initialized():
        logger.error(f"Exception occurred (Sentry not initialized): {exception}")
        return

    with push_scope() as scope:
        # Set level
        scope.level = level

        # Add extra context
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)

        # Add tags
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        # Set user
        if user:
            scope.set_user(user)

        # Capture exception
        sentry_capture_exception(exception)


def capture_message(
    message: str,
    level: str = "info",
    extra: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
):
    """
    Capture message to Sentry.

    Usage:
        capture_message("Capsule verification failed", level="warning", tags={"capsule_id": "123"})
    """

    if not sentry_manager.is_initialized():
        return

    with push_scope() as scope:
        scope.level = level

        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)

        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        sentry_capture_message(message)


@contextmanager
def sentry_context(
    user_id: Optional[str] = None, operation: Optional[str] = None, **extra_context
):
    """
    Context manager for adding Sentry context.

    Usage:
        with sentry_context(user_id="user_123", operation="create_capsule", capsule_type="attribution"):
            result = create_capsule()
    """

    with configure_scope() as scope:
        # Set user
        if user_id:
            scope.set_user({"id": user_id})

        # Set operation tag
        if operation:
            scope.set_tag("operation", operation)

        # Set extra context
        for key, value in extra_context.items():
            scope.set_context(key, value)

        # Add breadcrumb
        add_breadcrumb(
            category="context",
            message=f"Operation: {operation or 'unknown'}",
            level="info",
        )

        try:
            yield scope
        except Exception as e:
            # Automatically capture exceptions within context
            capture_exception(e)
            raise


@contextmanager
def sentry_transaction(name: str, op: str = "task"):
    """
    Context manager for Sentry performance transaction.

    Usage:
        with sentry_transaction("capsule_verification", "task"):
            result = verify_capsule()
    """

    transaction = sentry_sdk.start_transaction(name=name, op=op)
    try:
        with transaction:
            yield transaction
    except Exception:
        transaction.set_status("internal_error")
        raise


def monitored(operation_name: Optional[str] = None, capture_errors: bool = True):
    """
    Decorator to automatically monitor functions with Sentry.

    Usage:
        @monitored("create_capsule")
        def create_capsule(data):
            # function logic
            pass

        @monitored()  # Uses function name
        async def async_operation():
            # async logic
            pass
    """

    def decorator(func: Callable):
        name = operation_name or func.__name__

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with sentry_transaction(name, "function"):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    if capture_errors:
                        capture_exception(e, extra={"function": name})
                    raise

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with sentry_transaction(name, "async_function"):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    if capture_errors:
                        capture_exception(e, extra={"function": name})
                    raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Business-specific error tracking
class CapsuleErrorTracking:
    """Error tracking helpers for capsule operations"""

    @staticmethod
    def track_capsule_error(
        error: Exception,
        capsule_id: str,
        operation: str,
        capsule_type: Optional[str] = None,
    ):
        """Track capsule-related error"""
        capture_exception(
            error,
            tags={"component": "capsule", "operation": operation},
            extra={"capsule_id": capsule_id, "capsule_type": capsule_type},
        )

    @staticmethod
    def track_verification_failure(
        capsule_id: str, reason: str, verification_type: str
    ):
        """Track verification failure"""
        capture_message(
            f"Capsule verification failed: {reason}",
            level="warning",
            tags={"component": "verification", "verification_type": verification_type},
            extra={"capsule_id": capsule_id, "reason": reason},
        )


class SafetyErrorTracking:
    """Error tracking helpers for safety operations"""

    @staticmethod
    def track_safety_violation(
        domain: str, risk_level: str, decision_id: str, violation_type: str
    ):
        """Track safety violation"""
        capture_message(
            f"Safety violation: {violation_type}",
            level="error",
            tags={"component": "safety", "domain": domain, "risk_level": risk_level},
            extra={"decision_id": decision_id, "violation_type": violation_type},
        )


class AgentErrorTracking:
    """Error tracking helpers for agent operations"""

    @staticmethod
    def track_agent_error(error: Exception, agent_id: str, operation: str):
        """Track agent operation error"""
        capture_exception(
            error,
            tags={"component": "agent", "operation": operation},
            extra={"agent_id": agent_id},
        )

    @staticmethod
    def track_spending_violation(
        agent_id: str, attempted_amount: float, budget_limit: float
    ):
        """Track agent spending violation"""
        capture_message(
            "Agent spending violation",
            level="warning",
            tags={"component": "agent", "operation": "spending"},
            extra={
                "agent_id": agent_id,
                "attempted_amount": attempted_amount,
                "budget_limit": budget_limit,
                "overage": attempted_amount - budget_limit,
            },
        )


# Breadcrumb helpers
def add_capsule_breadcrumb(action: str, capsule_id: str, **data):
    """Add capsule-related breadcrumb"""
    add_breadcrumb(
        category="capsule",
        message=f"{action}: {capsule_id}",
        level="info",
        data={"capsule_id": capsule_id, **data},
    )


def add_security_breadcrumb(event: str, **data):
    """Add security-related breadcrumb"""
    add_breadcrumb(category="security", message=event, level="warning", data=data)


def add_agent_breadcrumb(action: str, agent_id: str, **data):
    """Add agent-related breadcrumb"""
    add_breadcrumb(
        category="agent",
        message=f"{action}: {agent_id}",
        level="info",
        data={"agent_id": agent_id, **data},
    )


# User identification
def identify_user(
    user_id: str, email: Optional[str] = None, username: Optional[str] = None
):
    """
    Identify user in Sentry.

    Usage:
        identify_user("user_123", email="user@example.com", username="johndoe")
    """
    set_user({"id": user_id, "email": email, "username": username})


def clear_user():
    """Clear user identification"""
    set_user(None)


# Performance monitoring helpers
def start_transaction(name: str, op: str = "task") -> Any:
    """Start a new transaction"""
    return sentry_sdk.start_transaction(name=name, op=op)


def start_span(operation: str, description: Optional[str] = None) -> Any:
    """Start a new span within current transaction"""
    return sentry_sdk.start_span(op=operation, description=description)


# Shutdown
def flush_sentry(timeout: float = 2.0):
    """
    Flush pending Sentry events.

    Call this before application shutdown.

    Args:
        timeout: Maximum time to wait for flush (seconds)
    """
    sentry_sdk.flush(timeout=timeout)
    logger.info("Sentry events flushed")
