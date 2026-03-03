"""
Security Middleware
===================

Production-grade security middleware including CORS, security headers,
input validation, and attack prevention.
"""

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security middleware configuration."""

    def __init__(self):
        # CORS settings
        self.cors_origins = (
            os.getenv("CORS_ORIGINS", "").split(",")
            if os.getenv("CORS_ORIGINS")
            else ["*"]
        )
        self.cors_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"]
        self.cors_headers = ["*"]
        self.cors_credentials = True

        # Security headers
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": self._get_csp_header(),
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "X-Download-Options": "noopen",
            "X-Permitted-Cross-Domain-Policies": "none",
        }

        # HSTS settings
        self.hsts_max_age = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
        self.hsts_include_subdomains = True
        self.hsts_preload = True

        # Content validation
        self.max_request_size = int(os.getenv("MAX_REQUEST_SIZE", "10485760"))  # 10MB
        self.max_header_size = 8192
        self.max_url_length = 2048

        # Attack prevention
        self.enable_sql_injection_detection = True
        self.enable_xss_detection = True
        self.enable_path_traversal_detection = True

        # Blocked patterns
        self.sql_injection_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bSELECT\b.*\bFROM\b)",
            r"(\bINSERT\b.*\bINTO\b)",
            r"(\bUPDATE\b.*\bSET\b)",
            r"(\bDELETE\b.*\bFROM\b)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(\';|\"|\'|\-\-)",
            r"(\bOR\b.*=.*)",
            r"(\bAND\b.*=.*)",
        ]

        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
        ]

        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e\\",
            r"\.\.%2f",
            r"\.\.%5c",
        ]

        # Blocked user agents
        self.blocked_user_agents = {
            "sqlmap",
            "nikto",
            "nmap",
            "masscan",
            "zap",
            "burp",
            "w3af",
            "skipfish",
            "nessus",
            "openvas",
            "arachni",
        }

        # Trusted proxies (for IP detection)
        self.trusted_proxies = (
            set(os.getenv("TRUSTED_PROXIES", "").split(","))
            if os.getenv("TRUSTED_PROXIES")
            else set()
        )

    def _get_csp_header(self) -> str:
        """Get Content Security Policy header."""
        csp_policies = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self'",
            "connect-src 'self'",
            "media-src 'self'",
            "object-src 'none'",
            "child-src 'none'",
            "worker-src 'none'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "base-uri 'self'",
            "manifest-src 'self'",
        ]

        # Add development-specific policies
        if os.getenv("ENVIRONMENT") == "development":
            csp_policies.extend(
                [
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval' localhost:*",
                    "connect-src 'self' localhost:* ws: wss:",
                ]
            )

        return "; ".join(csp_policies)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware."""

    def __init__(self, app, config: Optional[SecurityConfig] = None):
        super().__init__(app)
        self.config = config or SecurityConfig()

        # Compile regex patterns for performance
        self.sql_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.sql_injection_patterns
        ]
        self.xss_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.config.xss_patterns
        ]
        self.path_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.path_traversal_patterns
        ]

        # Security metrics
        self.blocked_requests = 0
        self.sql_injection_attempts = 0
        self.xss_attempts = 0
        self.path_traversal_attempts = 0

        logger.info("Security middleware initialized")

    async def dispatch(self, request: Request, call_next):
        """Apply security checks and headers."""
        # Pre-request security checks
        security_check = await self._security_checks(request)
        if not security_check["allowed"]:
            return self._create_blocked_response(security_check["reason"])

        # Process request
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response, request)

        return response

    async def _security_checks(self, request: Request) -> Dict[str, Any]:
        """Perform comprehensive security checks."""
        # Check request size
        if hasattr(request, "content_length") and request.content_length:
            if request.content_length > self.config.max_request_size:
                return {"allowed": False, "reason": "Request too large"}

        # Check URL length
        if len(str(request.url)) > self.config.max_url_length:
            return {"allowed": False, "reason": "URL too long"}

        # Check headers size
        headers_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if headers_size > self.config.max_header_size:
            return {"allowed": False, "reason": "Headers too large"}

        # Check user agent
        user_agent = request.headers.get("User-Agent", "").lower()
        if any(blocked in user_agent for blocked in self.config.blocked_user_agents):
            self.blocked_requests += 1
            return {"allowed": False, "reason": "Blocked user agent"}

        # SQL injection detection
        if self.config.enable_sql_injection_detection:
            if await self._detect_sql_injection(request):
                self.sql_injection_attempts += 1
                return {"allowed": False, "reason": "SQL injection attempt detected"}

        # XSS detection
        if self.config.enable_xss_detection:
            if await self._detect_xss(request):
                self.xss_attempts += 1
                return {"allowed": False, "reason": "XSS attempt detected"}

        # Path traversal detection
        if self.config.enable_path_traversal_detection:
            if await self._detect_path_traversal(request):
                self.path_traversal_attempts += 1
                return {"allowed": False, "reason": "Path traversal attempt detected"}

        return {"allowed": True, "reason": "Passed security checks"}

    async def _detect_sql_injection(self, request: Request) -> bool:
        """Detect SQL injection attempts."""
        # Check URL parameters
        query_string = str(request.url.query)
        for pattern in self.sql_patterns:
            if pattern.search(query_string):
                logger.warning(f"SQL injection detected in query: {query_string}")
                return True

        # Check request body (for POST/PUT requests)
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Only check text-based content
                content_type = request.headers.get("Content-Type", "")
                if (
                    "application/json" in content_type
                    or "application/x-www-form-urlencoded" in content_type
                ):
                    body = await request.body()
                    body_str = body.decode("utf-8", errors="ignore")

                    for pattern in self.sql_patterns:
                        if pattern.search(body_str):
                            logger.warning(
                                f"SQL injection detected in body: {body_str[:200]}..."
                            )
                            return True
            except Exception as e:
                logger.debug(f"Error checking request body for SQL injection: {e}")

        return False

    async def _detect_xss(self, request: Request) -> bool:
        """Detect XSS attempts."""
        # Check URL and query parameters
        full_url = str(request.url)
        for pattern in self.xss_patterns:
            if pattern.search(full_url):
                logger.warning(f"XSS detected in URL: {full_url}")
                return True

        # Check headers
        for header_name, header_value in request.headers.items():
            for pattern in self.xss_patterns:
                if pattern.search(header_value):
                    logger.warning(
                        f"XSS detected in header {header_name}: {header_value}"
                    )
                    return True

        return False

    async def _detect_path_traversal(self, request: Request) -> bool:
        """Detect path traversal attempts."""
        path = request.url.path
        for pattern in self.path_patterns:
            if pattern.search(path):
                logger.warning(f"Path traversal detected: {path}")
                return True

        return False

    def _add_security_headers(self, response: Response, request: Request):
        """Add security headers to response."""
        # Add standard security headers
        for header, value in self.config.security_headers.items():
            response.headers[header] = value

        # Add HSTS header for HTTPS requests
        if request.url.scheme == "https":
            hsts_value = f"max-age={self.config.hsts_max_age}"
            if self.config.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.config.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        # Add security timestamp
        response.headers["X-Security-Timestamp"] = str(int(time.time()))

    def _create_blocked_response(self, reason: str) -> JSONResponse:
        """Create response for blocked requests."""
        logger.warning(f"Request blocked: {reason}")

        return JSONResponse(
            status_code=403,
            content={
                "error": "Request blocked",
                "message": "Request blocked by security policy",
                "code": "SECURITY_VIOLATION",
            },
            headers={
                "X-Security-Block-Reason": reason,
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
            },
        )

    def get_security_metrics(self) -> Dict[str, int]:
        """Get security metrics."""
        return {
            "blocked_requests": self.blocked_requests,
            "sql_injection_attempts": self.sql_injection_attempts,
            "xss_attempts": self.xss_attempts,
            "path_traversal_attempts": self.path_traversal_attempts,
        }


class CORSMiddleware:
    """Custom CORS middleware with enhanced security."""

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()

    def get_starlette_cors_middleware(self):
        """Get configured Starlette CORS middleware."""
        return StarletteCORSMiddleware(
            allow_origins=self.config.cors_origins,
            allow_credentials=self.config.cors_credentials,
            allow_methods=self.config.cors_methods,
            allow_headers=self.config.cors_headers,
            expose_headers=[
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset",
                "X-Security-Timestamp",
            ],
        )


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Additional request validation middleware."""

    def __init__(self, app):
        super().__init__(app)

        # Allowed content types
        self.allowed_content_types = {
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "text/plain",
        }

        # File upload validation
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_file_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".pdf",
            ".txt",
            ".csv",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".zip",
        }

    async def dispatch(self, request: Request, call_next):
        """Validate request format and content."""
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("Content-Type", "")

            if content_type and not any(
                allowed in content_type for allowed in self.allowed_content_types
            ):
                return JSONResponse(
                    status_code=415, content={"error": "Unsupported content type"}
                )

        # Validate file uploads
        if "multipart/form-data" in request.headers.get("Content-Type", ""):
            validation_result = await self._validate_file_upload(request)
            if not validation_result["valid"]:
                return JSONResponse(
                    status_code=400, content={"error": validation_result["error"]}
                )

        return await call_next(request)

    async def _validate_file_upload(self, request: Request) -> Dict[str, Any]:
        """Validate file upload request."""
        try:
            # This is a simplified validation - in production you'd use
            # python-multipart to properly parse the multipart data
            content_length = request.headers.get("Content-Length")
            if content_length and int(content_length) > self.max_file_size:
                return {
                    "valid": False,
                    "error": f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB",
                }

            return {"valid": True}

        except Exception as e:
            logger.error(f"File upload validation error: {e}")
            return {"valid": False, "error": "Invalid file upload"}


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware.

    Provides Cross-Site Request Forgery protection using:
    - Double Submit Cookie pattern
    - Origin/Referer validation
    - SameSite cookie attribute

    SECURITY NOTE: This middleware should be used in conjunction with
    authentication to protect state-changing operations.
    """

    def __init__(
        self,
        app,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        safe_methods: Optional[Set[str]] = None,
        exempt_paths: Optional[Set[str]] = None,
        allowed_origins: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.safe_methods = safe_methods or {"GET", "HEAD", "OPTIONS", "TRACE"}
        self.exempt_paths = exempt_paths or {
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/auth/login",  # Login needs to work without CSRF token initially
            "/auth/register",
        }
        self.allowed_origins = set(allowed_origins) if allowed_origins else None
        self._token_length = 32  # 256 bits

        logger.info("CSRF protection middleware initialized")

    async def dispatch(self, request: Request, call_next):
        """Apply CSRF protection."""
        # Skip CSRF check for safe methods
        if request.method in self.safe_methods:
            response = await call_next(request)
            # Ensure CSRF cookie is set for subsequent requests
            self._ensure_csrf_cookie(request, response)
            return response

        # Skip CSRF check for exempt paths
        if request.url.path in self.exempt_paths:
            response = await call_next(request)
            self._ensure_csrf_cookie(request, response)
            return response

        # Skip CSRF check for API requests with Authorization header
        # (API clients use tokens, not cookies, so CSRF doesn't apply)
        if request.headers.get("Authorization"):
            return await call_next(request)

        # Validate Origin/Referer header
        origin_valid = self._validate_origin(request)
        if not origin_valid:
            logger.warning(
                f"CSRF: Invalid origin/referer for {request.method} {request.url.path}"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "CSRF validation failed",
                    "message": "Invalid origin",
                    "code": "CSRF_ORIGIN_MISMATCH",
                },
            )

        # Validate CSRF token (Double Submit Cookie pattern)
        token_valid = self._validate_csrf_token(request)
        if not token_valid:
            logger.warning(
                f"CSRF: Token validation failed for {request.method} {request.url.path}"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "CSRF validation failed",
                    "message": "Invalid or missing CSRF token",
                    "code": "CSRF_TOKEN_INVALID",
                },
            )

        response = await call_next(request)
        return response

    def _validate_origin(self, request: Request) -> bool:
        """
        Validate Origin or Referer header.

        SECURITY: This prevents cross-origin form submissions.
        """
        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")

        # Get the request host
        request_host = request.url.netloc

        # Check Origin header first (more reliable)
        if origin:
            try:
                origin_parsed = urlparse(origin)
                origin_host = origin_parsed.netloc

                # If allowed_origins is configured, check against it
                if self.allowed_origins:
                    return origin_host in self.allowed_origins

                # Otherwise, require same origin
                return origin_host == request_host
            except Exception:
                return False

        # Fall back to Referer header
        if referer:
            try:
                referer_parsed = urlparse(referer)
                referer_host = referer_parsed.netloc

                if self.allowed_origins:
                    return referer_host in self.allowed_origins

                return referer_host == request_host
            except Exception:
                return False

        # No Origin or Referer header - likely a direct API call
        # Reject for form-based requests (unless CORS preflight passed)
        content_type = request.headers.get("Content-Type", "")
        if "application/x-www-form-urlencoded" in content_type:
            return False
        if "multipart/form-data" in content_type:
            return False

        # Allow JSON API requests without Origin (they have other protections)
        return True

    def _validate_csrf_token(self, request: Request) -> bool:
        """
        Validate CSRF token using Double Submit Cookie pattern.

        SECURITY: The token in the header/form must match the token in the cookie.
        Since the attacker cannot read the cookie value due to same-origin policy,
        they cannot include the correct token in the header.
        """
        # Get token from cookie
        cookie_token = request.cookies.get(self.cookie_name)
        if not cookie_token:
            # No cookie = no session started yet, might be first request
            # Strict mode: reject. Lenient mode: allow with warning
            return False

        # Get token from header
        header_token = request.headers.get(self.header_name)

        # Also check form data for non-AJAX submissions
        # (This would require reading the body, which is complex in middleware)
        # For now, require the header for state-changing requests

        if not header_token:
            return False

        # SECURITY: Use constant-time comparison to prevent timing attacks
        import hmac

        return hmac.compare_digest(cookie_token, header_token)

    def _ensure_csrf_cookie(self, request: Request, response: Response) -> None:
        """Ensure CSRF cookie is set in response."""
        import secrets

        # Check if cookie already exists
        existing_token = request.cookies.get(self.cookie_name)
        if existing_token:
            return

        # Generate new token
        token = secrets.token_hex(self._token_length)

        # Set cookie with security attributes
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            httponly=False,  # Must be readable by JavaScript
            secure=request.url.scheme == "https",
            samesite="strict",  # Prevent cross-site requests
            max_age=86400,  # 24 hours
            path="/",
        )

    def generate_token(self) -> str:
        """Generate a new CSRF token for embedding in forms."""
        import secrets

        return secrets.token_hex(self._token_length)


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP whitelist/blacklist middleware."""

    def __init__(
        self,
        app,
        whitelist: Optional[List[str]] = None,
        blacklist: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.whitelist = set(whitelist) if whitelist else None
        self.blacklist = set(blacklist) if blacklist else set()

        # Add common malicious IP ranges to blacklist
        self.blacklist.update(
            [
                "0.0.0.0",
                "127.0.0.1",  # Remove if you need localhost access
            ]
        )

    async def dispatch(self, request: Request, call_next):
        """Check IP against whitelist/blacklist."""
        client_ip = self._get_client_ip(request)

        # Check blacklist first
        if client_ip in self.blacklist:
            logger.warning(f"Blocked request from blacklisted IP: {client_ip}")
            return JSONResponse(status_code=403, content={"error": "Access denied"})

        # Check whitelist (if configured)
        if self.whitelist and client_ip not in self.whitelist:
            logger.warning(f"Blocked request from non-whitelisted IP: {client_ip}")
            return JSONResponse(status_code=403, content={"error": "Access denied"})

        return await call_next(request)

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
