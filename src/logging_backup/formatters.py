"""
Logging Formatters
==================

Custom formatters for structured logging, compliance, and security.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hostname = self._get_hostname()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "hostname": self.hostname,
            "process_id": record.process,
            "thread_id": record.thread,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add stack info if present
        if record.stack_info:
            log_entry["stack_info"] = record.stack_info

        # Add extra fields from record
        extra_fields = self._extract_extra_fields(record)
        if extra_fields:
            log_entry.update(extra_fields)

        # Add location info for debug level
        if record.levelno <= logging.DEBUG:
            log_entry.update(
                {
                    "filename": record.filename,
                    "function": record.funcName,
                    "line_number": record.lineno,
                }
            )

        return json.dumps(log_entry, ensure_ascii=False, default=str)

    def _extract_extra_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract extra fields from log record."""
        # Standard fields to skip
        skip_fields = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "getMessage",
            "stack_info",
            "exc_info",
            "exc_text",
        }

        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in skip_fields:
                try:
                    # Ensure value is JSON serializable
                    json.dumps(value, default=str)
                    extra_fields[key] = value
                except (TypeError, ValueError):
                    extra_fields[key] = str(value)

        return extra_fields

    def _get_hostname(self) -> str:
        """Get hostname for log entries."""
        import socket

        try:
            return socket.gethostname()
        except Exception:
            return "unknown"


class ComplianceFormatter(JSONFormatter):
    """Specialized formatter for compliance and audit logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with compliance-specific fields."""
        # Get base JSON format
        log_entry_str = super().format(record)
        log_entry = json.loads(log_entry_str)

        # Add compliance-specific fields
        compliance_fields = {
            "compliance_timestamp": datetime.now(timezone.utc).isoformat(),
            "compliance_version": "1.0",
            "data_classification": self._get_data_classification(record),
            "retention_policy": self._get_retention_policy(record),
            "audit_trail_id": self._generate_audit_id(record),
        }

        log_entry.update(compliance_fields)

        # Ensure immutability indicators
        log_entry["hash"] = self._calculate_hash(log_entry)

        return json.dumps(log_entry, ensure_ascii=False, default=str, sort_keys=True)

    def _get_data_classification(self, record: logging.LogRecord) -> str:
        """Determine data classification level."""
        # Check for sensitive data indicators
        message = record.getMessage().lower()
        extra_fields = getattr(record, "__dict__", {})

        # High sensitivity indicators
        high_sensitivity_keywords = [
            "password",
            "ssn",
            "credit_card",
            "bank_account",
            "financial_transaction",
            "payment",
            "personal_data",
        ]

        # Medium sensitivity indicators
        medium_sensitivity_keywords = [
            "user_id",
            "email",
            "phone",
            "address",
            "api_key",
        ]

        # Check message and extra fields
        text_to_check = message + " " + str(extra_fields)

        if any(keyword in text_to_check for keyword in high_sensitivity_keywords):
            return "HIGHLY_SENSITIVE"
        elif any(keyword in text_to_check for keyword in medium_sensitivity_keywords):
            return "SENSITIVE"
        else:
            return "PUBLIC"

    def _get_retention_policy(self, record: logging.LogRecord) -> str:
        """Determine retention policy based on log type."""
        logger_name = record.name.lower()

        if "audit" in logger_name or "compliance" in logger_name:
            return "7_YEARS"  # Compliance requirement
        elif "security" in logger_name:
            return "3_YEARS"  # Security requirement
        elif "financial" in logger_name or "payment" in logger_name:
            return "7_YEARS"  # Financial requirement
        else:
            return "1_YEAR"  # Standard retention

    def _generate_audit_id(self, record: logging.LogRecord) -> str:
        """Generate unique audit trail ID."""
        import uuid

        return str(uuid.uuid4())

    def _calculate_hash(self, log_entry: Dict[str, Any]) -> str:
        """Calculate hash for log entry integrity."""
        import hashlib

        # Remove hash field if present to avoid recursion
        log_copy = {k: v for k, v in log_entry.items() if k != "hash"}

        # Create deterministic string representation
        log_string = json.dumps(log_copy, sort_keys=True, default=str)

        # Calculate SHA-256 hash
        return hashlib.sha256(log_string.encode("utf-8")).hexdigest()


class SecurityFormatter(JSONFormatter):
    """Specialized formatter for security logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with security-specific fields."""
        # Get base JSON format
        log_entry_str = super().format(record)
        log_entry = json.loads(log_entry_str)

        # Add security-specific fields
        security_fields = {
            "security_event_id": self._generate_security_event_id(),
            "threat_level": self._assess_threat_level(record),
            "incident_category": self._categorize_incident(record),
            "source_ip": self._extract_source_ip(record),
            "user_agent": self._extract_user_agent(record),
            "geographic_location": self._get_geographic_info(record),
        }

        log_entry.update(security_fields)

        return json.dumps(log_entry, ensure_ascii=False, default=str)

    def _generate_security_event_id(self) -> str:
        """Generate unique security event ID."""
        import uuid

        return f"SEC-{uuid.uuid4().hex[:8].upper()}"

    def _assess_threat_level(self, record: logging.LogRecord) -> str:
        """Assess threat level based on log content."""
        message = record.getMessage().lower()
        level = record.levelname

        # Critical threats
        critical_indicators = [
            "sql injection",
            "xss attack",
            "authentication bypass",
            "privilege escalation",
            "data breach",
            "unauthorized access",
        ]

        # High threats
        high_indicators = [
            "failed login",
            "suspicious activity",
            "rate limit exceeded",
            "blocked request",
            "invalid token",
            "access denied",
        ]

        # Medium threats
        medium_indicators = ["unusual pattern", "slow request", "validation error"]

        if level == "CRITICAL" or any(
            indicator in message for indicator in critical_indicators
        ):
            return "CRITICAL"
        elif level == "ERROR" or any(
            indicator in message for indicator in high_indicators
        ):
            return "HIGH"
        elif level == "WARNING" or any(
            indicator in message for indicator in medium_indicators
        ):
            return "MEDIUM"
        else:
            return "LOW"

    def _categorize_incident(self, record: logging.LogRecord) -> str:
        """Categorize security incident."""
        message = record.getMessage().lower()

        if "authentication" in message or "login" in message:
            return "AUTHENTICATION"
        elif "authorization" in message or "access" in message:
            return "AUTHORIZATION"
        elif "injection" in message or "xss" in message:
            return "INJECTION_ATTACK"
        elif "rate limit" in message:
            return "RATE_LIMITING"
        elif "validation" in message:
            return "INPUT_VALIDATION"
        else:
            return "GENERAL_SECURITY"

    def _extract_source_ip(self, record: logging.LogRecord) -> Optional[str]:
        """Extract source IP from log record."""
        extra_fields = getattr(record, "__dict__", {})
        return (
            extra_fields.get("ip_address")
            or extra_fields.get("client_ip")
            or extra_fields.get("source_ip")
        )

    def _extract_user_agent(self, record: logging.LogRecord) -> Optional[str]:
        """Extract user agent from log record."""
        extra_fields = getattr(record, "__dict__", {})
        return extra_fields.get("user_agent")

    def _get_geographic_info(
        self, record: logging.LogRecord
    ) -> Optional[Dict[str, str]]:
        """Get geographic information for IP address."""
        # This would integrate with a GeoIP service in production
        # For now, return placeholder
        source_ip = self._extract_source_ip(record)
        if source_ip and not source_ip.startswith(("127.", "10.", "192.168.", "172.")):
            return {"country": "Unknown", "city": "Unknown", "region": "Unknown"}
        return None


class PerformanceFormatter(JSONFormatter):
    """Specialized formatter for performance logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with performance-specific fields."""
        # Get base JSON format
        log_entry_str = super().format(record)
        log_entry = json.loads(log_entry_str)

        # Add performance-specific fields
        performance_fields = {
            "performance_metric_type": self._get_metric_type(record),
            "measurement_unit": self._get_measurement_unit(record),
            "baseline_comparison": self._compare_to_baseline(record),
            "performance_category": self._categorize_performance(record),
        }

        log_entry.update(performance_fields)

        return json.dumps(log_entry, ensure_ascii=False, default=str)

    def _get_metric_type(self, record: logging.LogRecord) -> str:
        """Determine performance metric type."""
        extra_fields = getattr(record, "__dict__", {})

        if "response_time" in extra_fields:
            return "RESPONSE_TIME"
        elif "execution_time" in extra_fields:
            return "EXECUTION_TIME"
        elif "throughput" in extra_fields:
            return "THROUGHPUT"
        elif "memory" in str(extra_fields):
            return "MEMORY_USAGE"
        elif "cpu" in str(extra_fields):
            return "CPU_USAGE"
        else:
            return "GENERAL_PERFORMANCE"

    def _get_measurement_unit(self, record: logging.LogRecord) -> str:
        """Determine measurement unit."""
        metric_type = self._get_metric_type(record)

        unit_mapping = {
            "RESPONSE_TIME": "seconds",
            "EXECUTION_TIME": "seconds",
            "THROUGHPUT": "requests_per_second",
            "MEMORY_USAGE": "bytes",
            "CPU_USAGE": "percentage",
        }

        return unit_mapping.get(metric_type, "unknown")

    def _compare_to_baseline(self, record: logging.LogRecord) -> str:
        """Compare metric to baseline performance."""
        extra_fields = getattr(record, "__dict__", {})

        # This would compare to actual baselines in production
        response_time = extra_fields.get("response_time", 0)

        if response_time > 5.0:
            return "SIGNIFICANTLY_SLOWER"
        elif response_time > 2.0:
            return "SLOWER"
        elif response_time < 0.1:
            return "FASTER"
        else:
            return "NORMAL"

    def _categorize_performance(self, record: logging.LogRecord) -> str:
        """Categorize performance issue."""
        message = record.getMessage().lower()

        if "slow" in message or "timeout" in message:
            return "LATENCY_ISSUE"
        elif "memory" in message:
            return "MEMORY_ISSUE"
        elif "cpu" in message:
            return "CPU_ISSUE"
        elif "database" in message:
            return "DATABASE_PERFORMANCE"
        elif "api" in message:
            return "API_PERFORMANCE"
        else:
            return "GENERAL_PERFORMANCE"
