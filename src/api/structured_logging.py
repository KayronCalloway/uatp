"""
Structured Logging for Insurance API
====================================

Provides consistent, structured logging with context tracking.
"""

import functools
import logging
import time
import uuid
from typing import Callable, Optional, Dict, Any

from quart import request, g

logger = logging.getLogger(__name__)


class StructuredLogger:
    """Wrapper for structured logging with request context"""

    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)

    def _add_context(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        """Add request context to log extra data"""
        context = extra.copy() if extra else {}

        # Add request ID if available
        if hasattr(g, "request_id"):
            context["request_id"] = g.request_id

        # Add user ID if available
        if hasattr(request, "user"):
            context["user_id"] = request.user.get("user_id")

        # Add client IP
        if request:
            context["client_ip"] = request.headers.get(
                "X-Forwarded-For", request.remote_addr
            )

        return context

    def info(self, message: str, **extra):
        """Log info with structured context"""
        context = self._add_context(extra)
        self.logger.info(message, extra=context)

    def warning(self, message: str, **extra):
        """Log warning with structured context"""
        context = self._add_context(extra)
        self.logger.warning(message, extra=context)

    def error(self, message: str, **extra):
        """Log error with structured context"""
        context = self._add_context(extra)
        self.logger.error(message, extra=context)

    def debug(self, message: str, **extra):
        """Log debug with structured context"""
        context = self._add_context(extra)
        self.logger.debug(message, extra=context)


# Global structured logger
structured_logger = StructuredLogger("insurance_api")


def log_request(f: Callable) -> Callable:
    """
    Decorator to log API requests and responses with timing.

    Usage:
        @insurance_bp.route("/policies", methods=["POST"])
        @require_auth
        @log_request
        async def create_policy():
            ...
    """

    @functools.wraps(f)
    async def decorated_function(*args, **kwargs):
        # Generate request ID if not present
        if not hasattr(g, "request_id"):
            g.request_id = str(uuid.uuid4())

        # Get request details
        method = request.method
        path = request.path
        user_id = None
        if hasattr(request, "user"):
            user_id = request.user.get("user_id")

        # Log request start
        start_time = time.time()
        structured_logger.info(
            f"Request started: {method} {path}",
            method=method,
            path=path,
            user_id=user_id,
            request_id=g.request_id,
        )

        try:
            # Execute route handler
            response = await f(*args, **kwargs)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Extract status code
            if isinstance(response, tuple):
                status_code = response[1] if len(response) > 1 else 200
            else:
                status_code = 200

            # Log successful response
            structured_logger.info(
                f"Request completed: {method} {path} - {status_code}",
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
                user_id=user_id,
                request_id=g.request_id,
            )

            return response

        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            structured_logger.error(
                f"Request failed: {method} {path} - {type(e).__name__}: {str(e)}",
                method=method,
                path=path,
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=duration_ms,
                user_id=user_id,
                request_id=g.request_id,
            )

            # Re-raise the exception
            raise

    return decorated_function


def log_operation(operation_name: str, **context):
    """
    Decorator to log business operations with timing.

    Usage:
        @log_operation("claim_submission", claim_type="ai_error")
        async def submit_claim(...):
            ...
    """

    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        async def decorated_function(*args, **kwargs):
            start_time = time.time()

            # Log operation start
            structured_logger.info(
                f"Operation started: {operation_name}",
                operation=operation_name,
                **context,
            )

            try:
                # Execute function
                result = await f(*args, **kwargs)

                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000

                # Log success
                structured_logger.info(
                    f"Operation completed: {operation_name}",
                    operation=operation_name,
                    duration_ms=duration_ms,
                    success=True,
                    **context,
                )

                return result

            except Exception as e:
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000

                # Log failure
                structured_logger.error(
                    f"Operation failed: {operation_name} - {type(e).__name__}: {str(e)}",
                    operation=operation_name,
                    duration_ms=duration_ms,
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    **context,
                )

                # Re-raise
                raise

        return decorated_function

    return decorator


class AuditLogger:
    """Specialized logger for audit events"""

    def __init__(self):
        self.logger = logging.getLogger("insurance_audit")

    def log_policy_created(self, policy_id: str, user_id: str, coverage_amount: int):
        """Log policy creation"""
        self.logger.info(
            f"Policy created: {policy_id}",
            extra={
                "event_type": "policy_created",
                "policy_id": policy_id,
                "user_id": user_id,
                "coverage_amount": coverage_amount,
            },
        )

    def log_claim_submitted(self, claim_id: str, policy_id: str, claimed_amount: int):
        """Log claim submission"""
        self.logger.info(
            f"Claim submitted: {claim_id}",
            extra={
                "event_type": "claim_submitted",
                "claim_id": claim_id,
                "policy_id": policy_id,
                "claimed_amount": claimed_amount,
            },
        )

    def log_claim_approved(
        self, claim_id: str, approved_amount: int, reviewer_id: str = None
    ):
        """Log claim approval"""
        self.logger.info(
            f"Claim approved: {claim_id}",
            extra={
                "event_type": "claim_approved",
                "claim_id": claim_id,
                "approved_amount": approved_amount,
                "reviewer_id": reviewer_id,
            },
        )

    def log_claim_denied(self, claim_id: str, reason: str, reviewer_id: str = None):
        """Log claim denial"""
        self.logger.info(
            f"Claim denied: {claim_id}",
            extra={
                "event_type": "claim_denied",
                "claim_id": claim_id,
                "reason": reason,
                "reviewer_id": reviewer_id,
            },
        )

    def log_policy_cancelled(self, policy_id: str, reason: str):
        """Log policy cancellation"""
        self.logger.info(
            f"Policy cancelled: {policy_id}",
            extra={
                "event_type": "policy_cancelled",
                "policy_id": policy_id,
                "reason": reason,
            },
        )

    def log_auth_failure(self, user_id: str = None, reason: str = None):
        """Log authentication/authorization failure"""
        self.logger.warning(
            f"Authentication failed: {reason}",
            extra={
                "event_type": "auth_failure",
                "user_id": user_id,
                "reason": reason,
            },
        )


# Global audit logger
audit_logger = AuditLogger()
