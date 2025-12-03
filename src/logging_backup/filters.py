"""
Logging Filters
===============

Custom filters for sensitive data protection, compliance, and log processing.
"""

import logging
import re
import json
from typing import Set, Dict, Any, Pattern, List, Optional


class SensitiveDataFilter(logging.Filter):
    """Filter to remove or mask sensitive data from logs."""

    def __init__(self, name=""):
        super().__init__(name)

        # Sensitive field patterns
        self.sensitive_field_patterns = {
            r"\b(password|pwd|secret|token|key|private_key|api_key)\b": "[REDACTED]",
            r"\b(ssn|social_security_number)\b": "[REDACTED_SSN]",
            r"\b(credit_card|cc_number|card_number)\b": "[REDACTED_CC]",
            r"\b(phone|mobile|telephone)\b": "[REDACTED_PHONE]",
            r"\b(email|e_mail)\b": "[REDACTED_EMAIL]",
            r"\b(address|street|location)\b": "[REDACTED_ADDRESS]",
        }

        # Compiled regex patterns for performance
        self.compiled_patterns = {
            re.compile(pattern, re.IGNORECASE): replacement
            for pattern, replacement in self.sensitive_field_patterns.items()
        }

        # Value patterns (actual sensitive data)
        self.value_patterns = [
            # Credit card numbers (basic pattern)
            (
                re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
                "[REDACTED_CC]",
            ),
            # Email addresses
            (
                re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
                "[REDACTED_EMAIL]",
            ),
            # Phone numbers (US format)
            (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[REDACTED_PHONE]"),
            # SSN format
            (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
            # JWT tokens (basic pattern)
            (
                re.compile(r"\beyJ[A-Za-z0-9+/=]+\.[A-Za-z0-9+/=]+\.[A-Za-z0-9+/=]*\b"),
                "[REDACTED_JWT]",
            ),
            # API keys (common formats)
            (re.compile(r"\b[A-Za-z0-9]{32,}\b"), "[REDACTED_KEY]"),
        ]

        # Fields that should always be redacted
        self.always_redact_fields = {
            "password",
            "current_password",
            "new_password",
            "confirm_password",
            "secret",
            "private_key",
            "api_key",
            "access_token",
            "refresh_token",
            "auth_token",
            "session_token",
            "jwt_token",
            "bearer_token",
            "credit_card_number",
            "cc_number",
            "card_number",
            "cvv",
            "cvv2",
            "ssn",
            "social_security_number",
            "tax_id",
            "national_id",
            "bank_account",
            "routing_number",
            "iban",
            "swift_code",
        }

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter sensitive data from log record."""
        try:
            # Filter message
            if record.msg:
                record.msg = self._sanitize_text(str(record.msg))

            # Filter args
            if record.args:
                sanitized_args = []
                for arg in record.args:
                    if isinstance(arg, str):
                        sanitized_args.append(self._sanitize_text(arg))
                    elif isinstance(arg, dict):
                        sanitized_args.append(self._sanitize_dict(arg))
                    else:
                        sanitized_args.append(arg)
                record.args = tuple(sanitized_args)

            # Filter extra fields
            for key, value in list(record.__dict__.items()):
                if key.lower() in self.always_redact_fields:
                    setattr(record, key, "[REDACTED]")
                elif isinstance(value, str):
                    setattr(record, key, self._sanitize_text(value))
                elif isinstance(value, dict):
                    setattr(record, key, self._sanitize_dict(value))
                elif isinstance(value, list):
                    setattr(record, key, self._sanitize_list(value))

            return True

        except Exception as e:
            # Don't let filter errors break logging
            print(f"Error in sensitive data filter: {e}")
            return True

    def _sanitize_text(self, text: str) -> str:
        """Sanitize sensitive data from text."""
        if not text:
            return text

        sanitized = text

        # Apply field name patterns
        for pattern, replacement in self.compiled_patterns.items():
            sanitized = pattern.sub(replacement, sanitized)

        # Apply value patterns
        for pattern, replacement in self.value_patterns:
            sanitized = pattern.sub(replacement, sanitized)

        return sanitized

    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data from dictionary."""
        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, value in data.items():
            # Check if key is sensitive
            if key.lower() in self.always_redact_fields:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_text(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = self._sanitize_list(value)
            else:
                sanitized[key] = value

        return sanitized

    def _sanitize_list(self, data: List[Any]) -> List[Any]:
        """Sanitize sensitive data from list."""
        if not isinstance(data, list):
            return data

        sanitized = []
        for item in data:
            if isinstance(item, str):
                sanitized.append(self._sanitize_text(item))
            elif isinstance(item, dict):
                sanitized.append(self._sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self._sanitize_list(item))
            else:
                sanitized.append(item)

        return sanitized


class ComplianceFilter(logging.Filter):
    """Filter for compliance logging requirements."""

    def __init__(self, name=""):
        super().__init__(name)

        # Compliance requirements
        self.required_fields = {"timestamp", "user_id", "action", "resource", "result"}

        # PII (Personally Identifiable Information) fields
        self.pii_fields = {
            "email",
            "phone",
            "address",
            "name",
            "birth_date",
            "ssn",
            "national_id",
            "passport_number",
        }

        # Regulations that apply
        self.applicable_regulations = {"GDPR", "CCPA", "SOX", "HIPAA", "PCI_DSS"}

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply compliance filtering to log record."""
        try:
            # Add compliance metadata
            self._add_compliance_metadata(record)

            # Ensure required fields for audit logs
            if self._is_audit_log(record):
                return self._validate_audit_fields(record)

            # Handle PII according to regulations
            self._handle_pii_compliance(record)

            return True

        except Exception as e:
            print(f"Error in compliance filter: {e}")
            return True

    def _add_compliance_metadata(self, record: logging.LogRecord):
        """Add compliance metadata to record."""
        record.compliance_timestamp = record.created
        record.compliance_level = self._determine_compliance_level(record)
        record.applicable_regulations = self._get_applicable_regulations(record)
        record.retention_period = self._get_retention_period(record)

    def _is_audit_log(self, record: logging.LogRecord) -> bool:
        """Check if this is an audit log entry."""
        return (
            "audit" in record.name.lower()
            or hasattr(record, "event_type")
            or record.levelname in ["AUDIT", "COMPLIANCE"]
        )

    def _validate_audit_fields(self, record: logging.LogRecord) -> bool:
        """Validate required fields for audit logs."""
        # Check for required audit fields
        record_dict = record.__dict__

        missing_fields = []
        for field in self.required_fields:
            if field not in record_dict or record_dict[field] is None:
                missing_fields.append(field)

        if missing_fields:
            # Add warning about missing fields
            record.compliance_warning = (
                f"Missing required audit fields: {', '.join(missing_fields)}"
            )

        return True  # Don't block the log, just warn

    def _handle_pii_compliance(self, record: logging.LogRecord):
        """Handle PII according to compliance requirements."""
        # Mark PII fields
        pii_present = []
        for key, value in record.__dict__.items():
            if key.lower() in self.pii_fields:
                pii_present.append(key)

        if pii_present:
            record.pii_fields = pii_present
            record.requires_consent = True
            record.subject_rights_applicable = True

    def _determine_compliance_level(self, record: logging.LogRecord) -> str:
        """Determine compliance level based on content."""
        if self._contains_financial_data(record):
            return "HIGH"
        elif self._contains_pii(record):
            return "MEDIUM"
        else:
            return "LOW"

    def _contains_financial_data(self, record: logging.LogRecord) -> bool:
        """Check if record contains financial data."""
        financial_keywords = [
            "payment",
            "transaction",
            "bond",
            "financial",
            "money",
            "credit_card",
        ]

        content = str(record.__dict__).lower()
        return any(keyword in content for keyword in financial_keywords)

    def _contains_pii(self, record: logging.LogRecord) -> bool:
        """Check if record contains PII."""
        content = str(record.__dict__).lower()
        return any(field in content for field in self.pii_fields)

    def _get_applicable_regulations(self, record: logging.LogRecord) -> List[str]:
        """Get applicable regulations for this record."""
        regulations = []

        if self._contains_pii(record):
            regulations.extend(["GDPR", "CCPA"])

        if self._contains_financial_data(record):
            regulations.extend(["SOX", "PCI_DSS"])

        if "health" in str(record.__dict__).lower():
            regulations.append("HIPAA")

        return list(set(regulations))  # Remove duplicates

    def _get_retention_period(self, record: logging.LogRecord) -> str:
        """Determine retention period based on regulations."""
        applicable_regs = self._get_applicable_regulations(record)

        if "SOX" in applicable_regs:
            return "7_YEARS"
        elif "PCI_DSS" in applicable_regs:
            return "1_YEAR"
        elif "GDPR" in applicable_regs or "CCPA" in applicable_regs:
            return "UNTIL_DELETION_REQUEST"
        else:
            return "3_YEARS"


class SecurityFilter(logging.Filter):
    """Filter for security-related log processing."""

    def __init__(self, name=""):
        super().__init__(name)

        # Security event patterns
        self.security_patterns = {
            "authentication_failure": re.compile(
                r"(failed|invalid|incorrect).*(login|auth|password)", re.IGNORECASE
            ),
            "authorization_failure": re.compile(
                r"(access|permission).*(denied|forbidden)", re.IGNORECASE
            ),
            "injection_attack": re.compile(
                r"(sql|script|code).*(injection|attack)", re.IGNORECASE
            ),
            "brute_force": re.compile(
                r"(multiple|repeated|brute).*(attempt|failure)", re.IGNORECASE
            ),
            "suspicious_activity": re.compile(
                r"(suspicious|anomal|unusual).*(activity|behavior)", re.IGNORECASE
            ),
        }

        # Threat levels
        self.threat_levels = {
            "CRITICAL": ["data_breach", "system_compromise", "privilege_escalation"],
            "HIGH": ["injection_attack", "brute_force", "unauthorized_access"],
            "MEDIUM": [
                "authentication_failure",
                "authorization_failure",
                "suspicious_activity",
            ],
            "LOW": ["failed_validation", "rate_limit_exceeded"],
        }

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply security filtering to log record."""
        try:
            # Classify security event
            security_classification = self._classify_security_event(record)
            if security_classification:
                record.security_event_type = security_classification
                record.threat_level = self._get_threat_level(security_classification)
                record.requires_investigation = self._requires_investigation(
                    security_classification
                )
                record.alert_priority = self._get_alert_priority(
                    security_classification
                )

            # Add security context
            self._add_security_context(record)

            return True

        except Exception as e:
            print(f"Error in security filter: {e}")
            return True

    def _classify_security_event(self, record: logging.LogRecord) -> Optional[str]:
        """Classify the type of security event."""
        content = f"{record.getMessage()} {str(record.__dict__)}".lower()

        for event_type, pattern in self.security_patterns.items():
            if pattern.search(content):
                return event_type

        return None

    def _get_threat_level(self, security_event_type: str) -> str:
        """Get threat level for security event type."""
        for level, event_types in self.threat_levels.items():
            if security_event_type in event_types:
                return level
        return "LOW"

    def _requires_investigation(self, security_event_type: str) -> bool:
        """Check if security event requires investigation."""
        high_priority_events = {
            "injection_attack",
            "brute_force",
            "unauthorized_access",
            "data_breach",
            "system_compromise",
            "privilege_escalation",
        }
        return security_event_type in high_priority_events

    def _get_alert_priority(self, security_event_type: str) -> int:
        """Get alert priority (1-5, 1 being highest)."""
        threat_level = self._get_threat_level(security_event_type)

        priority_mapping = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}

        return priority_mapping.get(threat_level, 5)

    def _add_security_context(self, record: logging.LogRecord):
        """Add security context to record."""
        record.security_processed = True
        record.security_filter_version = "1.0"

        # Extract security-relevant fields
        if hasattr(record, "ip_address"):
            record.source_ip = record.ip_address

        if hasattr(record, "user_agent"):
            record.client_info = record.user_agent

        if hasattr(record, "user_id"):
            record.subject_id = record.user_id


class PerformanceFilter(logging.Filter):
    """Filter for performance-related log processing."""

    def __init__(self, name=""):
        super().__init__(name)

        # Performance thresholds
        self.thresholds = {
            "response_time_slow": 2.0,  # seconds
            "response_time_critical": 10.0,  # seconds
            "memory_warning": 80,  # percent
            "memory_critical": 90,  # percent
            "cpu_warning": 80,  # percent
            "cpu_critical": 90,  # percent
        }

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply performance filtering to log record."""
        try:
            # Check performance metrics
            performance_alerts = self._check_performance_thresholds(record)
            if performance_alerts:
                record.performance_alerts = performance_alerts
                record.performance_impact = self._assess_performance_impact(
                    performance_alerts
                )

            # Add performance classification
            record.performance_category = self._classify_performance_event(record)

            return True

        except Exception as e:
            print(f"Error in performance filter: {e}")
            return True

    def _check_performance_thresholds(self, record: logging.LogRecord) -> List[str]:
        """Check if any performance thresholds are exceeded."""
        alerts = []

        # Check response time
        response_time = getattr(record, "response_time", None)
        if response_time:
            if response_time > self.thresholds["response_time_critical"]:
                alerts.append("CRITICAL_RESPONSE_TIME")
            elif response_time > self.thresholds["response_time_slow"]:
                alerts.append("SLOW_RESPONSE_TIME")

        # Check memory usage
        memory_usage = getattr(record, "memory_usage", None)
        if memory_usage:
            if memory_usage > self.thresholds["memory_critical"]:
                alerts.append("CRITICAL_MEMORY_USAGE")
            elif memory_usage > self.thresholds["memory_warning"]:
                alerts.append("HIGH_MEMORY_USAGE")

        # Check CPU usage
        cpu_usage = getattr(record, "cpu_usage", None)
        if cpu_usage:
            if cpu_usage > self.thresholds["cpu_critical"]:
                alerts.append("CRITICAL_CPU_USAGE")
            elif cpu_usage > self.thresholds["cpu_warning"]:
                alerts.append("HIGH_CPU_USAGE")

        return alerts

    def _assess_performance_impact(self, alerts: List[str]) -> str:
        """Assess overall performance impact."""
        if any("CRITICAL" in alert for alert in alerts):
            return "SEVERE"
        elif len(alerts) > 2:
            return "MODERATE"
        elif alerts:
            return "MINOR"
        else:
            return "NONE"

    def _classify_performance_event(self, record: logging.LogRecord) -> str:
        """Classify the type of performance event."""
        message = record.getMessage().lower()

        if "database" in message or "query" in message:
            return "DATABASE_PERFORMANCE"
        elif "api" in message or "http" in message:
            return "API_PERFORMANCE"
        elif "memory" in message:
            return "MEMORY_PERFORMANCE"
        elif "cpu" in message:
            return "CPU_PERFORMANCE"
        elif "network" in message:
            return "NETWORK_PERFORMANCE"
        else:
            return "GENERAL_PERFORMANCE"
