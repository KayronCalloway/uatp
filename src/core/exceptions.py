"""
Structured Exception Handling System

Provides comprehensive exception handling with correlation IDs, structured logging,
error classification, and integration with monitoring systems. Designed for
production environments with proper error tracking and user-friendly responses.

Key Features:
- Structured exception hierarchy
- Correlation ID tracking
- Automatic error logging and metrics
- User-friendly error responses
- Integration with monitoring systems
- Error context preservation
- Retry mechanism support
- Security-conscious error disclosure
"""

import traceback
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import dataclass, field

import structlog
from fastapi import HTTPException, Request, Response
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

logger = structlog.get_logger(__name__)

# Metrics for error tracking
error_metrics = {
    "exceptions_total": Counter(
        "application_exceptions_total",
        "Total application exceptions",
        ["exception_type", "severity", "component"],
    ),
    "http_errors_total": Counter(
        "http_errors_total", "Total HTTP errors", ["status_code", "method", "endpoint"]
    ),
    "error_handling_duration": Histogram(
        "error_handling_duration_seconds",
        "Time spent handling errors",
        ["exception_type"],
    ),
}


class ErrorSeverity(str, Enum):
    """Error severity levels"""

    LOW = "low"  # Minor issues, system continues normally
    MEDIUM = "medium"  # Notable issues, system degraded
    HIGH = "high"  # Serious issues, system impacted
    CRITICAL = "critical"  # System failure, immediate attention required


class ErrorCategory(str, Enum):
    """Error category classification"""

    VALIDATION = "validation"  # Input validation errors
    AUTHENTICATION = "authentication"  # Auth/authz errors
    BUSINESS_LOGIC = "business_logic"  # Business rule violations
    EXTERNAL_SERVICE = "external_service"  # External API failures
    DATABASE = "database"  # Database-related errors
    CONFIGURATION = "configuration"  # Configuration issues
    SYSTEM = "system"  # System-level errors
    NETWORK = "network"  # Network connectivity issues
    PERMISSION = "permission"  # Permission/access errors
    RATE_LIMIT = "rate_limit"  # Rate limiting errors


@dataclass
class ErrorContext:
    """Context information for errors"""

    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "request_id": self.request_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "additional_data": self.additional_data,
        }


class BaseUATPException(Exception):
    """
    Base exception class for all UATP-specific exceptions
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        retry_after: Optional[int] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)

        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.category = category
        self.severity = severity
        self.context = context or ErrorContext()
        self.details = details or {}
        self.user_message = user_message or self._get_default_user_message()
        self.retry_after = retry_after
        self.cause = cause

        # Record the exception
        self._record_exception()

    def _get_default_user_message(self) -> str:
        """Get default user-friendly message"""
        return (
            "An error occurred while processing your request. Please try again later."
        )

    def _record_exception(self):
        """Record exception metrics and logging"""
        error_metrics["exceptions_total"].labels(
            exception_type=self.__class__.__name__,
            severity=self.severity.value,
            component=self.category.value,
        ).inc()

        # Log the exception with context
        logger.error(
            "Exception occurred",
            exception_type=self.__class__.__name__,
            error_code=self.error_code,
            message=self.message,
            category=self.category.value,
            severity=self.severity.value,
            context=self.context.to_dict(),
            details=self.details,
            stack_trace=traceback.format_exc()
            if self.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
            else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "error_code": self.error_code,
            "message": self.user_message,
            "category": self.category.value,
            "severity": self.severity.value,
            "correlation_id": self.context.correlation_id,
            "timestamp": self.context.timestamp.isoformat(),
            "details": self.details,
            "retry_after": self.retry_after,
        }


class ValidationError(BaseUATPException):
    """Raised when input validation fails"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs,
    ):
        self.field = field
        self.value = value

        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["invalid_value"] = str(value)[:100]  # Limit size

        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            details=details,
            user_message="The provided input is invalid. Please check your data and try again.",
            **kwargs,
        )


class AuthenticationError(BaseUATPException):
    """Raised when authentication fails"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            user_message="Authentication failed. Please check your credentials.",
            **kwargs,
        )


class AuthorizationError(BaseUATPException):
    """Raised when authorization fails"""

    def __init__(
        self, message: str, required_permission: Optional[str] = None, **kwargs
    ):
        details = kwargs.get("details", {})
        if required_permission:
            details["required_permission"] = required_permission

        super().__init__(
            message,
            category=ErrorCategory.PERMISSION,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            user_message="You don't have permission to perform this action.",
            **kwargs,
        )


class BusinessLogicError(BaseUATPException):
    """Raised when business logic validation fails"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            user_message="The operation cannot be completed due to business rules.",
            **kwargs,
        )


class ExternalServiceError(BaseUATPException):
    """Raised when external service calls fail"""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if service_name:
            details["service_name"] = service_name
        if status_code:
            details["status_code"] = status_code

        # Determine severity based on status code
        severity = ErrorSeverity.HIGH
        if status_code and 400 <= status_code < 500:
            severity = ErrorSeverity.MEDIUM

        super().__init__(
            message,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=severity,
            details=details,
            user_message="An external service is currently unavailable. Please try again later.",
            retry_after=60,  # Suggest retry after 60 seconds
            **kwargs,
        )


class DatabaseError(BaseUATPException):
    """Raised when database operations fail"""

    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if operation:
            details["operation"] = operation

        super().__init__(
            message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            details=details,
            user_message="A database error occurred. Please try again later.",
            **kwargs,
        )


class ConfigurationError(BaseUATPException):
    """Raised when configuration is invalid or missing"""

    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key

        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.CRITICAL,
            details=details,
            user_message="A system configuration error occurred. Please contact support.",
            **kwargs,
        )


class RateLimitError(BaseUATPException):
    """Raised when rate limits are exceeded"""

    def __init__(
        self,
        message: str,
        limit: Optional[int] = None,
        window: Optional[int] = None,
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if limit:
            details["limit"] = limit
        if window:
            details["window_seconds"] = window

        super().__init__(
            message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.LOW,
            details=details,
            user_message="Rate limit exceeded. Please wait before making more requests.",
            retry_after=retry_after or 60,
            **kwargs,
        )


class NetworkError(BaseUATPException):
    """Raised when network operations fail"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            user_message="A network error occurred. Please check your connection and try again.",
            retry_after=30,
            **kwargs,
        )


class CapsuleError(BaseUATPException):
    """Base class for capsule-related errors"""

    def __init__(self, message: str, capsule_id: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if capsule_id:
            details["capsule_id"] = capsule_id

        super().__init__(
            message, category=ErrorCategory.BUSINESS_LOGIC, details=details, **kwargs
        )


class CapsuleNotFoundError(CapsuleError):
    """Raised when a capsule cannot be found"""

    def __init__(self, capsule_id: str, **kwargs):
        super().__init__(
            f"Capsule not found: {capsule_id}",
            capsule_id=capsule_id,
            severity=ErrorSeverity.LOW,
            user_message="The requested capsule could not be found.",
            **kwargs,
        )


class CapsuleValidationError(CapsuleError):
    """Raised when capsule validation fails"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            user_message="The capsule data is invalid.",
            **kwargs,
        )


class ErrorHandler:
    """
    Centralized error handling system
    """

    def __init__(self, include_debug_info: bool = False):
        self.include_debug_info = include_debug_info

    def create_error_context(self, request: Optional[Request] = None) -> ErrorContext:
        """Create error context from request"""
        context = ErrorContext()

        if request:
            context.endpoint = str(request.url.path) if request.url else None
            context.method = request.method
            context.ip_address = request.client.host if request.client else None
            context.user_agent = request.headers.get("user-agent")

            # Extract correlation ID from headers or state
            context.correlation_id = request.headers.get("x-correlation-id") or getattr(
                request.state, "correlation_id", context.correlation_id
            )

            # Extract user info if available
            if hasattr(request.state, "user"):
                user = request.state.user
                context.user_id = getattr(user, "user_id", None)
                context.session_id = getattr(user, "session_id", None)

        return context

    def handle_exception(
        self, exc: Exception, request: Optional[Request] = None
    ) -> JSONResponse:
        """Handle exception and return appropriate response"""

        # Create error context
        context = self.create_error_context(request)

        # Handle UATP exceptions
        if isinstance(exc, BaseUATPException):
            # Update context if not already set
            if not exc.context.request_id:
                exc.context = context

            return self._create_error_response(exc)

        # Handle HTTP exceptions
        elif isinstance(exc, HTTPException):
            return self._handle_http_exception(exc, context)

        # Handle unexpected exceptions
        else:
            return self._handle_unexpected_exception(exc, context)

    def _create_error_response(self, exc: BaseUATPException) -> JSONResponse:
        """Create JSON response from UATP exception"""

        # Determine HTTP status code
        status_code = self._get_http_status_code(exc)

        # Create response data
        response_data = exc.to_dict()

        # Add debug information if enabled
        if self.include_debug_info:
            response_data["debug"] = {
                "exception_type": exc.__class__.__name__,
                "internal_message": exc.message,
                "stack_trace": traceback.format_exc(),
            }

        # Create headers
        headers = {
            "X-Correlation-ID": exc.context.correlation_id,
            "X-Error-Code": exc.error_code,
        }

        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)

        return JSONResponse(
            status_code=status_code, content=response_data, headers=headers
        )

    def _handle_http_exception(
        self, exc: HTTPException, context: ErrorContext
    ) -> JSONResponse:
        """Handle FastAPI HTTP exceptions"""

        error_metrics["http_errors_total"].labels(
            status_code=exc.status_code,
            method=context.method or "unknown",
            endpoint=context.endpoint or "unknown",
        ).inc()

        response_data = {
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "correlation_id": context.correlation_id,
            "timestamp": context.timestamp.isoformat(),
        }

        if self.include_debug_info:
            response_data["debug"] = {
                "exception_type": "HTTPException",
                "status_code": exc.status_code,
            }

        headers = {"X-Correlation-ID": context.correlation_id}

        return JSONResponse(
            status_code=exc.status_code, content=response_data, headers=headers
        )

    def _handle_unexpected_exception(
        self, exc: Exception, context: ErrorContext
    ) -> JSONResponse:
        """Handle unexpected exceptions"""

        # Log the unexpected exception
        logger.error(
            "Unexpected exception occurred",
            exception_type=exc.__class__.__name__,
            message=str(exc),
            context=context.to_dict(),
            stack_trace=traceback.format_exc(),
        )

        error_metrics["exceptions_total"].labels(
            exception_type=exc.__class__.__name__,
            severity=ErrorSeverity.CRITICAL.value,
            component="system",
        ).inc()

        # Create generic error response
        response_data = {
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "correlation_id": context.correlation_id,
            "timestamp": context.timestamp.isoformat(),
        }

        if self.include_debug_info:
            response_data["debug"] = {
                "exception_type": exc.__class__.__name__,
                "message": str(exc),
                "stack_trace": traceback.format_exc(),
            }

        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_data,
            headers={"X-Correlation-ID": context.correlation_id},
        )

    def _get_http_status_code(self, exc: BaseUATPException) -> int:
        """Get appropriate HTTP status code for exception"""

        if isinstance(exc, ValidationError):
            return 400  # Bad Request
        elif isinstance(exc, AuthenticationError):
            return 401  # Unauthorized
        elif isinstance(exc, AuthorizationError):
            return 403  # Forbidden
        elif isinstance(exc, CapsuleNotFoundError):
            return 404  # Not Found
        elif isinstance(exc, RateLimitError):
            return 429  # Too Many Requests
        elif isinstance(exc, (ExternalServiceError, NetworkError)):
            return 502  # Bad Gateway
        elif isinstance(exc, DatabaseError):
            return 503  # Service Unavailable
        elif exc.severity == ErrorSeverity.CRITICAL:
            return 500  # Internal Server Error
        else:
            return 400  # Default to Bad Request


# Global error handler instance
error_handler = ErrorHandler()


def setup_error_handlers(app, include_debug_info: bool = False):
    """Setup error handlers for FastAPI application"""

    global error_handler
    error_handler = ErrorHandler(include_debug_info=include_debug_info)

    @app.exception_handler(BaseUATPException)
    async def uatp_exception_handler(request: Request, exc: BaseUATPException):
        """Handle UATP-specific exceptions"""
        return error_handler.handle_exception(exc, request)

    @app.exception_handler(HTTPException)
    async def http_exception_handler_override(request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        return error_handler.handle_exception(exc, request)

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions"""
        return error_handler.handle_exception(exc, request)


# Utility functions for error handling
def create_error_context_from_request(request: Request) -> ErrorContext:
    """Create error context from FastAPI request"""
    return error_handler.create_error_context(request)


def log_error(
    exc: Exception,
    context: Optional[ErrorContext] = None,
    additional_data: Optional[Dict[str, Any]] = None,
):
    """Log error with context"""

    ctx = context or ErrorContext()
    if additional_data:
        ctx.additional_data.update(additional_data)

    logger.error(
        "Error logged",
        exception_type=exc.__class__.__name__,
        message=str(exc),
        context=ctx.to_dict(),
        stack_trace=traceback.format_exc(),
    )


# Decorator for automatic error handling
def handle_errors(
    reraise: bool = False, log_errors: bool = True, default_return: Any = None
):
    """Decorator for automatic error handling"""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BaseUATPException:
                if reraise:
                    raise
                if log_errors:
                    logger.error(f"Error in {func.__name__}", exc_info=True)
                return default_return
            except Exception as e:
                if log_errors:
                    log_error(e)
                if reraise:
                    raise
                return default_return

        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseUATPException:
                if reraise:
                    raise
                if log_errors:
                    logger.error(f"Error in {func.__name__}", exc_info=True)
                return default_return
            except Exception as e:
                if log_errors:
                    log_error(e)
                if reraise:
                    raise
                return default_return

        # Return appropriate wrapper based on function type
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
