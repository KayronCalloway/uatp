"""
Logging and Audit Middleware
=============================

Production-grade logging middleware with structured logging, audit trails,
and performance monitoring.
"""

import time
import json
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import os

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class LoggingConfig:
    """Configuration for logging middleware."""

    def __init__(self):
        # Logging levels
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.access_log_enabled = (
            os.getenv("ACCESS_LOG_ENABLED", "true").lower() == "true"
        )
        self.audit_log_enabled = (
            os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
        )

        # Log format
        self.log_format = os.getenv("LOG_FORMAT", "json")  # json or text

        # Performance logging
        self.log_slow_requests = True
        self.slow_request_threshold = float(
            os.getenv("SLOW_REQUEST_THRESHOLD", "2.0")
        )  # seconds

        # Request/Response logging
        self.log_request_body = os.getenv("LOG_REQUEST_BODY", "false").lower() == "true"
        self.log_response_body = (
            os.getenv("LOG_RESPONSE_BODY", "false").lower() == "true"
        )
        self.max_body_size = int(os.getenv("MAX_LOG_BODY_SIZE", "1024"))  # bytes

        # Sensitive data filtering
        self.sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "proxy-authorization",
            "x-forwarded-authorization",
        }

        self.sensitive_query_params = {
            "password",
            "token",
            "key",
            "secret",
            "api_key",
            "access_token",
            "refresh_token",
        }

        self.sensitive_body_fields = {
            "password",
            "current_password",
            "new_password",
            "confirm_password",
            "secret",
            "private_key",
            "api_key",
            "token",
            "ssn",
            "credit_card",
        }

        # Paths to exclude from access logging
        self.excluded_paths = {"/health", "/metrics", "/favicon.ico"}


class LoggingMiddleware(BaseHTTPMiddleware):
    """Comprehensive logging middleware."""

    def __init__(self, app, config: Optional[LoggingConfig] = None):
        super().__init__(app)
        self.config = config or LoggingConfig()

        # Request counter
        self.request_count = 0

        logger.info("Logging middleware initialized", config=self.config.__dict__)

    async def dispatch(self, request: Request, call_next):
        """Log request and response details."""
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Add request ID to request state
        request.state.request_id = request_id

        # Increment request counter
        self.request_count += 1

        # Log incoming request
        if (
            self.config.access_log_enabled
            and request.url.path not in self.config.excluded_paths
        ):
            await self._log_request(request, request_id)

        # Process request
        try:
            response = await call_next(request)

            # Calculate response time
            response_time = time.time() - start_time

            # Add response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"

            # Log response
            if (
                self.config.access_log_enabled
                and request.url.path not in self.config.excluded_paths
            ):
                await self._log_response(request, response, response_time, request_id)

            # Log slow requests
            if (
                self.config.log_slow_requests
                and response_time > self.config.slow_request_threshold
            ):
                await self._log_slow_request(request, response_time, request_id)

            return response

        except Exception as e:
            response_time = time.time() - start_time

            # Log error
            logger.error(
                "Request processing error",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                response_time=response_time,
                error=str(e),
                error_type=type(e).__name__,
            )

            raise

    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request details."""
        # Get client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")

        # Get user information (if available)
        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "username", None)

        # Prepare request data
        log_data = {
            "event": "request_started",
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": self._sanitize_query_params(dict(request.query_params)),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "headers": self._sanitize_headers(dict(request.headers)),
            "user_id": user_id,
            "username": username,
            "content_length": request.headers.get("Content-Length"),
            "content_type": request.headers.get("Content-Type"),
        }

        # Add request body if enabled
        if self.config.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if len(body) <= self.config.max_body_size:
                    if "application/json" in request.headers.get("Content-Type", ""):
                        try:
                            body_json = json.loads(body.decode("utf-8"))
                            log_data["request_body"] = self._sanitize_body(body_json)
                        except json.JSONDecodeError:
                            log_data["request_body"] = "[Invalid JSON]"
                    else:
                        log_data["request_body"] = body.decode(
                            "utf-8", errors="ignore"
                        )[: self.config.max_body_size]
                else:
                    log_data["request_body"] = f"[Body too large: {len(body)} bytes]"
            except Exception as e:
                log_data["request_body"] = f"[Error reading body: {str(e)}]"

        logger.info("Incoming request", **log_data)

    async def _log_response(
        self,
        request: Request,
        response: Response,
        response_time: float,
        request_id: str,
    ):
        """Log response details."""
        log_data = {
            "event": "request_completed",
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "response_time": round(response_time, 3),
            "response_headers": dict(response.headers),
        }

        # Add response body if enabled and not too large
        if self.config.log_response_body:
            try:
                # This is tricky with streaming responses, so we'll skip for now
                # In production, you might want to implement response body logging differently
                pass
            except Exception as e:
                log_data["response_body"] = f"[Error reading response: {str(e)}]"

        # Determine log level based on status code
        if response.status_code >= 500:
            logger.error("Request completed with server error", **log_data)
        elif response.status_code >= 400:
            logger.warning("Request completed with client error", **log_data)
        else:
            logger.info("Request completed successfully", **log_data)

    async def _log_slow_request(
        self, request: Request, response_time: float, request_id: str
    ):
        """Log slow request details."""
        logger.warning(
            "Slow request detected",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            response_time=round(response_time, 3),
            threshold=self.config.slow_request_threshold,
            user_id=getattr(request.state, "user_id", None),
        )

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive information from headers."""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.config.sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized

    def _sanitize_query_params(self, params: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive information from query parameters."""
        sanitized = {}
        for key, value in params.items():
            if key.lower() in self.config.sensitive_query_params:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized

    def _sanitize_body(self, body: Any) -> Any:
        """Remove sensitive information from request body."""
        if isinstance(body, dict):
            sanitized = {}
            for key, value in body.items():
                if key.lower() in self.config.sensitive_body_fields:
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, dict):
                    sanitized[key] = self._sanitize_body(value)
                elif isinstance(value, list):
                    sanitized[key] = [self._sanitize_body(item) for item in value]
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(body, list):
            return [self._sanitize_body(item) for item in body]
        else:
            return body


class AuditMiddleware(BaseHTTPMiddleware):
    """Audit trail middleware for security and compliance."""

    def __init__(self, app, config: Optional[LoggingConfig] = None):
        super().__init__(app)
        self.config = config or LoggingConfig()

        # Actions that require auditing
        self.audited_actions = {
            "POST": ["create", "register", "login"],
            "PUT": ["update", "modify"],
            "PATCH": ["update", "modify"],
            "DELETE": ["delete", "remove", "revoke"],
        }

        # Sensitive endpoints that always get audited
        self.sensitive_endpoints = {
            "/auth/login",
            "/auth/register",
            "/auth/logout",
            "/api/users",
            "/api/agents",
            "/api/citizenship",
            "/api/bonds",
            "/api/payments",
        }

    async def dispatch(self, request: Request, call_next):
        """Create audit trail for sensitive operations."""
        should_audit = self._should_audit(request)

        if should_audit:
            # Log pre-request audit entry
            await self._log_audit_entry(request, "ATTEMPT")

        try:
            response = await call_next(request)

            if should_audit:
                # Log post-request audit entry
                await self._log_audit_entry(request, "SUCCESS", response.status_code)

            return response

        except Exception as e:
            if should_audit:
                # Log failed request audit entry
                await self._log_audit_entry(request, "FAILURE", error=str(e))
            raise

    def _should_audit(self, request: Request) -> bool:
        """Determine if request should be audited."""
        # Always audit sensitive endpoints
        if any(
            request.url.path.startswith(endpoint)
            for endpoint in self.sensitive_endpoints
        ):
            return True

        # Audit based on HTTP method
        if request.method in self.audited_actions:
            return True

        return False

    async def _log_audit_entry(
        self,
        request: Request,
        status: str,
        status_code: Optional[int] = None,
        error: Optional[str] = None,
    ):
        """Log audit trail entry."""
        audit_data = {
            "event": "audit_trail",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
            "user_id": getattr(request.state, "user_id", None),
            "username": getattr(request.state, "username", None),
            "action": request.method,
            "resource": request.url.path,
            "status": status,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", ""),
            "session_id": getattr(request.state, "session_id", None),
        }

        if status_code:
            audit_data["status_code"] = status_code

        if error:
            audit_data["error"] = error

        # Add request details for certain operations
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                if "application/json" in request.headers.get("Content-Type", ""):
                    body = await request.body()
                    if body:
                        body_json = json.loads(body.decode("utf-8"))
                        # Only log non-sensitive fields
                        safe_fields = {
                            k: v
                            for k, v in body_json.items()
                            if k.lower() not in self.config.sensitive_body_fields
                        }
                        audit_data["request_data"] = safe_fields
            except Exception:
                pass

        logger.info("Audit trail entry", **audit_data)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """Performance monitoring and logging middleware."""

    def __init__(self, app):
        super().__init__(app)
        self.request_metrics = {
            "total_requests": 0,
            "total_response_time": 0.0,
            "min_response_time": float("inf"),
            "max_response_time": 0.0,
            "status_codes": {},
            "endpoints": {},
        }

    async def dispatch(self, request: Request, call_next):
        """Monitor and log performance metrics."""
        start_time = time.time()

        try:
            response = await call_next(request)
            response_time = time.time() - start_time

            # Update metrics
            self._update_metrics(request, response, response_time)

            # Log performance data
            self._log_performance(request, response, response_time)

            return response

        except Exception as e:
            response_time = time.time() - start_time
            self._log_performance(request, None, response_time, error=str(e))
            raise

    def _update_metrics(
        self, request: Request, response: Response, response_time: float
    ):
        """Update performance metrics."""
        self.request_metrics["total_requests"] += 1
        self.request_metrics["total_response_time"] += response_time

        if response_time < self.request_metrics["min_response_time"]:
            self.request_metrics["min_response_time"] = response_time

        if response_time > self.request_metrics["max_response_time"]:
            self.request_metrics["max_response_time"] = response_time

        # Track status codes
        status_code = response.status_code
        self.request_metrics["status_codes"][status_code] = (
            self.request_metrics["status_codes"].get(status_code, 0) + 1
        )

        # Track endpoints
        endpoint = f"{request.method} {request.url.path}"
        if endpoint not in self.request_metrics["endpoints"]:
            self.request_metrics["endpoints"][endpoint] = {
                "count": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
            }

        endpoint_metrics = self.request_metrics["endpoints"][endpoint]
        endpoint_metrics["count"] += 1
        endpoint_metrics["total_time"] += response_time
        endpoint_metrics["avg_time"] = (
            endpoint_metrics["total_time"] / endpoint_metrics["count"]
        )

    def _log_performance(
        self,
        request: Request,
        response: Optional[Response],
        response_time: float,
        error: Optional[str] = None,
    ):
        """Log performance data."""
        perf_data = {
            "event": "performance_metric",
            "method": request.method,
            "path": request.url.path,
            "response_time": round(response_time, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if response:
            perf_data["status_code"] = response.status_code

        if error:
            perf_data["error"] = error

        logger.info("Performance metric", **perf_data)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        if self.request_metrics["total_requests"] > 0:
            avg_response_time = (
                self.request_metrics["total_response_time"]
                / self.request_metrics["total_requests"]
            )
        else:
            avg_response_time = 0.0

        return {
            "total_requests": self.request_metrics["total_requests"],
            "avg_response_time": round(avg_response_time, 3),
            "min_response_time": round(self.request_metrics["min_response_time"], 3)
            if self.request_metrics["min_response_time"] != float("inf")
            else 0,
            "max_response_time": round(self.request_metrics["max_response_time"], 3),
            "status_codes": self.request_metrics["status_codes"],
            "top_endpoints": sorted(
                self.request_metrics["endpoints"].items(),
                key=lambda x: x[1]["count"],
                reverse=True,
            )[:10],
        }
