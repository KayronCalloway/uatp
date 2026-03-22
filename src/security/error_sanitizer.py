"""
Error Sanitization for Production Security

Prevents information leakage through error messages by:
- Removing file paths
- Removing SQL queries
- Removing stack traces
- Removing internal implementation details
- Mapping common errors to user-friendly messages
"""

import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Patterns that indicate sensitive information in error messages
SENSITIVE_PATTERNS = [
    # File paths (Unix and Windows)
    (re.compile(r"(/[\w\-./]+\.py)", re.IGNORECASE), "[path]"),
    (re.compile(r"([A-Za-z]:\\[\w\\\-. ]+)", re.IGNORECASE), "[path]"),
    # SQL queries (common keywords)
    (
        re.compile(
            r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|FROM|WHERE|JOIN)\b.*?(?=\s*$|\s*;)",
            re.IGNORECASE | re.DOTALL,
        ),
        "[query]",
    ),
    # Stack trace indicators
    (re.compile(r'File ".*?", line \d+'), "[trace]"),
    (re.compile(r"Traceback \(most recent call last\)"), "[trace]"),
    # Internal module paths
    (re.compile(r"src\.[a-zA-Z0-9_.]+"), "[module]"),
    # Database connection strings
    (
        re.compile(r"(postgres|mysql|sqlite|redis)://[^\s]+", re.IGNORECASE),
        "[connection]",
    ),
    # API keys and tokens (generic patterns)
    (
        re.compile(
            r'(api[_-]?key|token|secret|password|credential)[=:]\s*[\'"]?[\w\-]+[\'"]?',
            re.IGNORECASE,
        ),
        "[redacted]",
    ),
    # IP addresses
    (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "[ip]"),
    # Email addresses in error context
    (re.compile(r"[\w\-_.]+@[\w\-_.]+\.[a-zA-Z]{2,}"), "[email]"),
    # UUIDs (often internal identifiers)
    (
        re.compile(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            re.IGNORECASE,
        ),
        "[id]",
    ),
]

# Map of common error types to user-friendly messages
ERROR_TYPE_MESSAGES = {
    "ConnectionError": "Service temporarily unavailable. Please try again later.",
    "TimeoutError": "Request timed out. Please try again.",
    "DatabaseError": "Database operation failed. Please try again later.",
    "IntegrityError": "Data validation failed. Please check your input.",
    "ValidationError": "Invalid input data. Please check your request.",
    "AuthenticationError": "Authentication failed. Please check your credentials.",
    "AuthorizationError": "You don't have permission to perform this action.",
    "NotFoundError": "The requested resource was not found.",
    "RateLimitError": "Too many requests. Please wait before trying again.",
    "ValueError": "Invalid input provided.",
    "TypeError": "Invalid data type in request.",
    "KeyError": "Required field missing.",
    "AttributeError": "Invalid request structure.",
    "JSONDecodeError": "Invalid JSON in request body.",
    "OperationalError": "Service temporarily unavailable.",
    "ProgrammingError": "Request cannot be processed.",
}

# Generic fallback message
GENERIC_ERROR_MESSAGE = "An unexpected error occurred. Please try again later."


def is_production() -> bool:
    """Check if running in production environment."""
    return os.getenv("ENVIRONMENT", "development").lower() in ("production", "prod")


def sanitize_error_message(
    message: str, error_type: Optional[str] = None, allow_original_in_dev: bool = True
) -> str:
    """
    Sanitize an error message to prevent information leakage.

    In production: Always returns sanitized/generic message
    In development: Returns original message with sensitive data redacted

    Args:
        message: The original error message
        error_type: The type/class name of the exception (optional)
        allow_original_in_dev: Whether to show original in development

    Returns:
        Sanitized error message safe for client consumption
    """
    if not message:
        return GENERIC_ERROR_MESSAGE

    # In production, prefer type-based generic messages
    if is_production():
        if error_type and error_type in ERROR_TYPE_MESSAGES:
            return ERROR_TYPE_MESSAGES[error_type]

        # Check if message matches any error type pattern
        message_lower = message.lower()
        for error_key, friendly_message in ERROR_TYPE_MESSAGES.items():
            if error_key.lower() in message_lower:
                return friendly_message

        # Fall back to generic message in production
        return GENERIC_ERROR_MESSAGE

    # In development, redact sensitive patterns but keep structure
    if allow_original_in_dev:
        sanitized = message
        for pattern, replacement in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized

    return GENERIC_ERROR_MESSAGE


def sanitize_exception(exc: Exception, include_type: bool = False) -> dict:
    """
    Create a sanitized error response from an exception.

    Args:
        exc: The exception to sanitize
        include_type: Whether to include error type in response (dev only)

    Returns:
        Dict with sanitized error information
    """
    error_type = type(exc).__name__
    original_message = str(exc)

    response = {
        "error": sanitize_error_message(original_message, error_type),
    }

    # Add error type in non-production for debugging
    if not is_production() and include_type:
        response["error_type"] = error_type
        response["original_message"] = sanitize_error_message(
            original_message, error_type, allow_original_in_dev=True
        )

    return response


def log_and_sanitize(
    exc: Exception, context: Optional[dict] = None, log_level: str = "error"
) -> str:
    """
    Log the full exception details and return a sanitized message.

    This ensures we capture full details in logs while returning
    safe messages to clients.

    Args:
        exc: The exception to handle
        context: Additional context for logging
        log_level: Logging level to use

    Returns:
        Sanitized error message for client
    """
    error_type = type(exc).__name__

    # Build log context
    log_context = {
        "error_type": error_type,
        "error_message": str(exc),
        "is_production": is_production(),
    }
    if context:
        log_context.update(context)

    # Log full details
    log_func = getattr(logger, log_level, logger.error)
    log_func(f"Exception caught: {error_type}", extra=log_context, exc_info=True)

    # Return sanitized message
    return sanitize_error_message(str(exc), error_type)


# FastAPI exception handler factory
def create_sanitized_exception_handler(app):
    """
    Create FastAPI exception handlers that sanitize error responses.

    Usage:
        app = FastAPI()
        create_sanitized_exception_handler(app)
    """
    import uuid

    from fastapi import Request
    from fastapi.responses import JSONResponse

    from src.utils.timezone_utils import utc_now

    @app.exception_handler(Exception)
    async def sanitized_exception_handler(request: Request, exc: Exception):
        """Handle all exceptions with sanitization."""
        correlation_id = str(uuid.uuid4())

        # Log full details
        logger.error(
            "Unhandled exception",
            extra={
                "correlation_id": correlation_id,
                "path": str(request.url.path),
                "method": request.method,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
            exc_info=True,
        )

        # Build sanitized response
        sanitized = sanitize_exception(exc, include_type=not is_production())
        sanitized["correlation_id"] = correlation_id
        sanitized["timestamp"] = utc_now().isoformat()

        return JSONResponse(
            status_code=500,
            content=sanitized,
            headers={"X-Correlation-ID": correlation_id},
        )

    return app
