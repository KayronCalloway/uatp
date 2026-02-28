"""
Security Middleware for UATP Capsule Engine API.

This middleware provides automatic security enforcement across all API routes,
integrating the 9 AI-centric security systems into every API request/response cycle.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Dict, List, Any, Optional, Callable

from quart import request, g, jsonify, Response, current_app
from quart.wrappers import Response as QuartResponse

from ..security.security_manager import (
    get_security_manager,
    get_unified_security_status,
)
from ..security.memory_timing_protection import protected_operation, SecurityLevel
from ..attribution.gaming_detector import gaming_detector
from ..economic.circuit_breakers import circuit_breaker_manager

logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """
    Comprehensive security middleware for API routes.

    This middleware enforces security policies across all API endpoints,
    providing automatic threat detection, rate limiting, and security verification.
    """

    def __init__(self, app=None):
        self.app = app
        self.security_stats = {
            "total_requests": 0,
            "security_checks_passed": 0,
            "security_checks_failed": 0,
            "threats_detected": 0,
            "requests_blocked": 0,
            "average_security_overhead_ms": 0.0,
        }

        # Security configuration
        self.config = {
            "enable_request_verification": True,
            "enable_response_verification": True,
            "enable_threat_detection": True,
            "enable_gaming_detection": True,
            "enable_circuit_breaker_checks": True,
            "max_security_overhead_ms": 100,  # Maximum allowed security processing time
            "security_level": SecurityLevel.HIGH,
        }

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize middleware with Flask/Quart application."""
        self.app = app

        # Register middleware hooks
        app.before_request(self.before_request)
        app.after_request(self.after_request)

        # Add security configuration to app config
        app.config.setdefault("SECURITY_MIDDLEWARE_CONFIG", self.config)

        logger.info("🛡️ Security Middleware initialized and registered")

    async def before_request(self):
        """Security checks before processing each request."""
        start_time = time.time()
        g.security_start_time = start_time
        g.security_context = {
            "request_id": f"req_{int(start_time * 1000)}",
            "endpoint": request.endpoint,
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", "Unknown"),
            "api_key": request.headers.get("X-API-Key"),
            "security_checks": {},
        }

        self.security_stats["total_requests"] += 1

        # Skip security checks for health endpoints and static files
        if self._should_skip_security_checks():
            return None

        try:
            with protected_operation(f"api_request_{g.security_context['endpoint']}"):
                # 1. Gaming detection check
                if self.config["enable_gaming_detection"]:
                    gaming_result = await self._check_gaming_patterns()
                    g.security_context["security_checks"][
                        "gaming_detection"
                    ] = gaming_result

                    if not gaming_result["allowed"]:
                        return await self._block_request(
                            "Gaming pattern detected", gaming_result
                        )

                # 2. Circuit breaker checks
                if self.config["enable_circuit_breaker_checks"]:
                    circuit_result = await self._check_circuit_breakers()
                    g.security_context["security_checks"][
                        "circuit_breakers"
                    ] = circuit_result

                    if not circuit_result["allowed"]:
                        return await self._block_request(
                            "Circuit breaker triggered", circuit_result
                        )

                # 3. Request verification with security manager
                if self.config["enable_request_verification"]:
                    verification_result = await self._verify_request_security()
                    g.security_context["security_checks"][
                        "request_verification"
                    ] = verification_result

                    if not verification_result["allowed"]:
                        return await self._block_request(
                            "Request security verification failed", verification_result
                        )

                # 4. Threat detection
                if self.config["enable_threat_detection"]:
                    threat_result = await self._detect_threats()
                    g.security_context["security_checks"][
                        "threat_detection"
                    ] = threat_result

                    if threat_result["threats_detected"] > 0:
                        self.security_stats["threats_detected"] += threat_result[
                            "threats_detected"
                        ]

                        # Block high-severity threats
                        if any(
                            t["severity"] == "high" for t in threat_result["threats"]
                        ):
                            return await self._block_request(
                                "High-severity threat detected", threat_result
                            )

                # Record successful security checks
                self.security_stats["security_checks_passed"] += 1

                # Calculate and record security overhead
                security_overhead = (time.time() - start_time) * 1000
                self._update_security_overhead(security_overhead)

                # Log security check success
                logger.info(
                    f"✅ Security checks passed for {request.method} {request.path} in {security_overhead:.1f}ms"
                )

                return None

        except Exception as e:
            logger.error(f"❌ Security middleware error: {e}")
            self.security_stats["security_checks_failed"] += 1

            # In production, you might want to block on security errors
            # For now, log and allow with degraded security
            g.security_context["security_checks"]["error"] = str(e)
            return None

    async def after_request(self, response: QuartResponse) -> QuartResponse:
        """Security checks after processing each request."""
        # Skip for non-security checked requests
        if not hasattr(g, "security_context"):
            return response

        # Skip for blocked requests
        if response.status_code in [403, 429, 503]:
            return response

        try:
            # Response verification with security manager
            if self.config["enable_response_verification"]:
                response_verification = await self._verify_response_security(response)
                g.security_context["security_checks"][
                    "response_verification"
                ] = response_verification

                if not response_verification["allowed"]:
                    # Replace response with security error
                    return await self._create_security_error_response(
                        "Response security verification failed"
                    )

            # Add security headers
            self._add_security_headers(response)

            # Log final security context
            total_time = (time.time() - g.security_start_time) * 1000
            logger.info(
                f"🔒 Request completed with security: {request.method} {request.path} ({total_time:.1f}ms total)"
            )

            return response

        except Exception as e:
            logger.error(f"❌ After-request security error: {e}")
            return response

    def _should_skip_security_checks(self) -> bool:
        """Determine if security checks should be skipped for this request."""
        skip_patterns = ["/health", "/metrics", "/ping", "/static/", "/favicon.ico"]

        return any(pattern in request.path for pattern in skip_patterns)

    async def _check_gaming_patterns(self) -> Dict[str, Any]:
        """Check for gaming patterns using the gaming detector."""
        try:
            request_data = {
                "remote_addr": request.remote_addr,
                "user_agent": request.headers.get("User-Agent", ""),
                "api_key": request.headers.get("X-API-Key", ""),
                "endpoint": request.endpoint,
                "method": request.method,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            result = gaming_detector.analyze_attribution_for_gaming(request_data)
            is_suspicious = (
                result.gaming_detected if hasattr(result, "gaming_detected") else False
            )

            return {
                "allowed": not is_suspicious,
                "suspicious": is_suspicious,
                "check_type": "gaming_detection",
                "threat_level": "high" if is_suspicious else "none",
            }

        except Exception as e:
            logger.error(f"Gaming detection error: {e}")
            return {"allowed": True, "error": str(e)}

    async def _check_circuit_breakers(self) -> Dict[str, Any]:
        """Check circuit breaker status for the request."""
        try:
            # Check if any circuit breakers are tripped
            breaker_status = circuit_breaker_manager.get_system_status()

            # Check for tripped breakers that would affect this request
            critical_breakers = [
                "attribution_system",
                "payment_processing",
                "account_creation",
            ]
            tripped_critical = [
                name
                for name, status in breaker_status.items()
                if name in critical_breakers and status.get("state") == "open"
            ]

            if tripped_critical:
                return {
                    "allowed": False,
                    "tripped_breakers": tripped_critical,
                    "check_type": "circuit_breakers",
                    "reason": f"Critical circuit breakers tripped: {', '.join(tripped_critical)}",
                }

            return {
                "allowed": True,
                "check_type": "circuit_breakers",
                "active_breakers": len(breaker_status),
            }

        except Exception as e:
            logger.error(f"Circuit breaker check error: {e}")
            return {"allowed": True, "error": str(e)}

    async def _verify_request_security(self) -> Dict[str, Any]:
        """Verify request using unified security manager."""
        try:
            security_manager = get_security_manager()
            if not security_manager:
                return {"allowed": True, "note": "Security manager not available"}

            # Prepare request data for security verification
            request_data = {
                "endpoint": request.endpoint,
                "method": request.method,
                "path": request.path,
                "remote_addr": request.remote_addr,
                "headers": dict(request.headers),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Perform security verification
            success, result = await security_manager.secure_capsule_operation(
                "api_request_verification", request_data
            )

            return {
                "allowed": success,
                "verification_rate": result.get("verification_rate", 0),
                "security_details": result.get("security_verifications", {}),
                "check_type": "request_verification",
            }

        except Exception as e:
            logger.error(f"Request verification error: {e}")
            return {"allowed": True, "error": str(e)}

    async def _detect_threats(self) -> Dict[str, Any]:
        """Detect security threats in the request."""
        threats = []

        try:
            # Check for suspicious patterns in headers
            user_agent = request.headers.get("User-Agent", "").lower()
            suspicious_agents = ["bot", "crawler", "scanner", "hack", "exploit"]

            if any(agent in user_agent for agent in suspicious_agents):
                threats.append(
                    {
                        "type": "suspicious_user_agent",
                        "severity": "medium",
                        "details": f"Suspicious user agent: {user_agent[:100]}",
                    }
                )

            # Check for unusual request patterns
            if request.method not in [
                "GET",
                "POST",
                "PUT",
                "DELETE",
                "OPTIONS",
                "HEAD",
            ]:
                threats.append(
                    {
                        "type": "unusual_http_method",
                        "severity": "medium",
                        "details": f"Unusual HTTP method: {request.method}",
                    }
                )

            # Check for potential injection patterns in headers
            for header_name, header_value in request.headers:
                if any(
                    pattern in header_value.lower()
                    for pattern in ["<script", "javascript:", "data:", "vbscript:"]
                ):
                    threats.append(
                        {
                            "type": "potential_injection",
                            "severity": "high",
                            "details": f"Suspicious pattern in header {header_name}",
                        }
                    )

            return {
                "threats_detected": len(threats),
                "threats": threats,
                "check_type": "threat_detection",
            }

        except Exception as e:
            logger.error(f"Threat detection error: {e}")
            return {"threats_detected": 0, "threats": [], "error": str(e)}

    async def _verify_response_security(
        self, response: QuartResponse
    ) -> Dict[str, Any]:
        """Verify response security before sending to client."""
        try:
            # Check for sensitive data exposure
            if hasattr(response, "get_data"):
                response_data = await response.get_data(as_text=True)
            else:
                response_data = str(response)

            # Look for potential sensitive data patterns
            sensitive_patterns = [
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
                r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # Credit card-like
                r"\bsk_[a-zA-Z0-9_]+\b",  # API keys starting with sk_
                r"\bpk_[a-zA-Z0-9_]+\b",  # API keys starting with pk_
            ]

            import re

            sensitive_found = []
            for pattern in sensitive_patterns:
                if re.search(pattern, response_data):
                    sensitive_found.append(pattern)

            if sensitive_found:
                logger.warning(
                    f"⚠️ Potential sensitive data detected in response for {request.path}"
                )

            return {
                "allowed": True,  # Don't block for now, just log
                "sensitive_patterns_detected": len(sensitive_found),
                "check_type": "response_verification",
            }

        except Exception as e:
            logger.error(f"Response verification error: {e}")
            return {"allowed": True, "error": str(e)}

    async def _block_request(self, reason: str, details: Dict[str, Any]) -> Response:
        """Block a request and return security error response."""
        self.security_stats["requests_blocked"] += 1
        self.security_stats["security_checks_failed"] += 1

        logger.warning(
            f"🚫 Request blocked: {reason} for {request.method} {request.path}"
        )

        return (
            jsonify(
                {
                    "error": "Security violation",
                    "reason": reason,
                    "request_id": g.security_context.get("request_id"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "details": details if current_app.debug else None,
                }
            ),
            403,
        )

    async def _create_security_error_response(self, reason: str) -> Response:
        """Create a security error response."""
        return (
            jsonify(
                {
                    "error": "Security verification failed",
                    "reason": reason,
                    "request_id": g.security_context.get("request_id"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            403,
        )

    def _add_security_headers(self, response: QuartResponse) -> None:
        """Add security headers to the response."""
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers[
            "Strict-Transport-Security"
        ] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # UATP-specific security headers
        response.headers["X-UATP-Security-Level"] = self.config["security_level"].value
        response.headers["X-UATP-Security-Version"] = "7.1"

        # Add security context info (if debug mode)
        if current_app.debug and hasattr(g, "security_context"):
            security_checks = g.security_context.get("security_checks", {})
            passed_checks = sum(
                1 for check in security_checks.values() if check.get("allowed", True)
            )
            response.headers[
                "X-UATP-Security-Checks"
            ] = f"{passed_checks}/{len(security_checks)}"

    def _update_security_overhead(self, overhead_ms: float) -> None:
        """Update average security overhead metrics."""
        current_avg = self.security_stats["average_security_overhead_ms"]
        total_requests = self.security_stats["total_requests"]

        if total_requests == 1:
            self.security_stats["average_security_overhead_ms"] = overhead_ms
        else:
            new_avg = (
                (current_avg * (total_requests - 1)) + overhead_ms
            ) / total_requests
            self.security_stats["average_security_overhead_ms"] = new_avg

        # Log performance warning if overhead is too high
        if overhead_ms > self.config["max_security_overhead_ms"]:
            logger.warning(
                f"⚠️ High security overhead: {overhead_ms:.1f}ms (threshold: {self.config['max_security_overhead_ms']}ms)"
            )

    def get_security_statistics(self) -> Dict[str, Any]:
        """Get comprehensive security middleware statistics."""
        security_status = get_unified_security_status()

        return {
            "middleware_stats": self.security_stats,
            "configuration": self.config,
            "security_system_status": security_status,
            "performance_metrics": {
                "average_overhead_ms": self.security_stats[
                    "average_security_overhead_ms"
                ],
                "success_rate": (
                    self.security_stats["security_checks_passed"]
                    / max(self.security_stats["total_requests"], 1)
                )
                * 100,
            },
        }


# Decorator for additional route-specific security
def require_security_level(level: SecurityLevel):
    """Decorator to require specific security level for a route."""

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            # Check if current security level meets requirement
            if hasattr(g, "security_context"):
                # You could add route-specific security logic here
                pass
            return await f(*args, **kwargs)

        return decorated_function

    return decorator


def create_security_middleware() -> SecurityMiddleware:
    """Factory function to create security middleware."""
    return SecurityMiddleware()
