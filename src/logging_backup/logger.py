"""
Core Logging System
===================

Production-grade logging system with structured logging, audit trails,
and compliance features for the UATP Capsule Engine.
"""

import logging
import logging.config
import os
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import structlog

from .formatters import JSONFormatter, ComplianceFormatter
from .handlers import DatabaseHandler, SecurityHandler
from .filters import SensitiveDataFilter, ComplianceFilter


class LoggingConfig:
    """Centralized logging configuration."""

    def __init__(self):
        # Basic settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_format = os.getenv("LOG_FORMAT", "json")  # json or text
        self.environment = os.getenv("ENVIRONMENT", "development")

        # File logging
        self.log_dir = Path(os.getenv("LOG_DIR", "/app/logs"))
        self.log_file = self.log_dir / os.getenv("LOG_FILE", "uatp.log")
        self.access_log_file = self.log_dir / os.getenv("ACCESS_LOG", "access.log")
        self.error_log_file = self.log_dir / os.getenv("ERROR_LOG", "error.log")
        self.audit_log_file = self.log_dir / os.getenv("AUDIT_LOG", "audit.log")
        self.security_log_file = self.log_dir / os.getenv(
            "SECURITY_LOG", "security.log"
        )

        # Log rotation
        self.max_bytes = int(os.getenv("LOG_MAX_BYTES", "100000000"))  # 100MB
        self.backup_count = int(os.getenv("LOG_BACKUP_COUNT", "10"))

        # Features
        self.enable_console_logging = (
            os.getenv("ENABLE_CONSOLE_LOGGING", "true").lower() == "true"
        )
        self.enable_file_logging = (
            os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"
        )
        self.enable_audit_logging = (
            os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
        )
        self.enable_security_logging = (
            os.getenv("ENABLE_SECURITY_LOGGING", "true").lower() == "true"
        )
        self.enable_database_logging = (
            os.getenv("ENABLE_DATABASE_LOGGING", "false").lower() == "true"
        )

        # Compliance
        self.enable_compliance_logging = (
            os.getenv("ENABLE_COMPLIANCE_LOGGING", "true").lower() == "true"
        )
        self.retention_days = int(
            os.getenv("LOG_RETENTION_DAYS", "2555")
        )  # 7 years for compliance

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)


def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """Setup comprehensive logging system."""
    config = config or LoggingConfig()

    # Configure structlog
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
            structlog.processors.JSONRenderer()
            if config.log_format == "json"
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "src.logging.formatters.JSONFormatter",
            },
            "compliance": {
                "()": "src.logging.formatters.ComplianceFormatter",
            },
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        },
        "filters": {
            "sensitive_data": {
                "()": "src.logging.filters.SensitiveDataFilter",
            },
            "compliance": {
                "()": "src.logging.filters.ComplianceFilter",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": config.log_level,
                "formatter": "json" if config.log_format == "json" else "standard",
                "filters": ["sensitive_data"],
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": config.log_level,
                "formatter": "json",
                "filters": ["sensitive_data"],
                "filename": str(config.log_file),
                "maxBytes": config.max_bytes,
                "backupCount": config.backup_count,
                "encoding": "utf8",
            },
            "access": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(config.access_log_file),
                "maxBytes": config.max_bytes,
                "backupCount": config.backup_count,
                "encoding": "utf8",
            },
            "error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": str(config.error_log_file),
                "maxBytes": config.max_bytes,
                "backupCount": config.backup_count,
                "encoding": "utf8",
            },
            "audit": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "compliance",
                "filters": ["compliance"],
                "filename": str(config.audit_log_file),
                "maxBytes": config.max_bytes,
                "backupCount": config.backup_count,
                "encoding": "utf8",
            },
            "security": {
                "()": "src.logging.handlers.SecurityHandler",
                "level": "WARNING",
                "formatter": "json",
                "filename": str(config.security_log_file),
                "maxBytes": config.max_bytes,
                "backupCount": config.backup_count,
            },
        },
        "loggers": {
            "": {"level": config.log_level, "handlers": []},  # Root logger
            "uatp": {"level": config.log_level, "handlers": [], "propagate": False},
            "uatp.access": {
                "level": "INFO",
                "handlers": ["access"],
                "propagate": False,
            },
            "uatp.audit": {"level": "INFO", "handlers": ["audit"], "propagate": False},
            "uatp.security": {
                "level": "WARNING",
                "handlers": ["security"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["access"],
                "propagate": False,
            },
            "fastapi": {"level": "INFO", "handlers": [], "propagate": True},
        },
    }

    # Add handlers based on configuration
    root_handlers = []
    uatp_handlers = []

    if config.enable_console_logging:
        root_handlers.append("console")
        uatp_handlers.append("console")

    if config.enable_file_logging:
        root_handlers.append("file")
        uatp_handlers.append("file")
        uatp_handlers.append("error")

    # Add database handler if enabled
    if config.enable_database_logging:
        logging_config["handlers"]["database"] = {
            "()": "src.logging.handlers.DatabaseHandler",
            "level": "INFO",
            "formatter": "json",
        }
        uatp_handlers.append("database")

    # Update handlers in config
    logging_config["loggers"][""]["handlers"] = root_handlers
    logging_config["loggers"]["uatp"]["handlers"] = uatp_handlers

    # Apply configuration
    logging.config.dictConfig(logging_config)

    # Log initialization
    logger = logging.getLogger("uatp.logging")
    logger.info(
        "Logging system initialized",
        level=config.log_level,
        format=config.log_format,
        environment=config.environment,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the UATP prefix."""
    return logging.getLogger(f"uatp.{name}")


class AuditLogger:
    """Specialized logger for audit trails and compliance."""

    def __init__(self):
        self.logger = logging.getLogger("uatp.audit")
        self.security_logger = logging.getLogger("uatp.security")

    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        result: str,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """Log user action for audit trail."""
        audit_entry = {
            "event_type": "user_action",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "result": result,
            "session_id": additional_data.get("session_id")
            if additional_data
            else None,
            "ip_address": additional_data.get("ip_address")
            if additional_data
            else None,
            "user_agent": additional_data.get("user_agent")
            if additional_data
            else None,
        }

        if additional_data:
            audit_entry.update(additional_data)

        self.logger.info("User action audit", extra=audit_entry)

    def log_system_event(
        self,
        event_type: str,
        description: str,
        severity: str = "info",
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """Log system event."""
        system_entry = {
            "event_type": "system_event",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_event_type": event_type,
            "description": description,
            "severity": severity,
        }

        if additional_data:
            system_entry.update(additional_data)

        log_method = getattr(self.logger, severity.lower(), self.logger.info)
        log_method("System event", extra=system_entry)

    def log_data_access(
        self,
        user_id: str,
        data_type: str,
        data_id: str,
        access_type: str,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """Log data access for compliance."""
        data_entry = {
            "event_type": "data_access",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "data_type": data_type,
            "data_id": data_id,
            "access_type": access_type,  # read, write, delete, export
        }

        if additional_data:
            data_entry.update(additional_data)

        self.logger.info("Data access audit", extra=data_entry)

    def log_financial_transaction(
        self,
        user_id: str,
        transaction_type: str,
        amount: float,
        currency: str,
        transaction_id: str,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """Log financial transaction for compliance."""
        financial_entry = {
            "event_type": "financial_transaction",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "transaction_type": transaction_type,
            "amount": amount,
            "currency": currency,
            "transaction_id": transaction_id,
        }

        if additional_data:
            financial_entry.update(additional_data)

        self.logger.info("Financial transaction audit", extra=financial_entry)

    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """Log security event."""
        security_entry = {
            "event_type": "security_event",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "security_event_type": event_type,
            "severity": severity,
            "description": description,
            "user_id": user_id,
            "ip_address": ip_address,
        }

        if additional_data:
            security_entry.update(additional_data)

        log_method = getattr(
            self.security_logger, severity.lower(), self.security_logger.warning
        )
        log_method("Security event", extra=security_entry)

    def log_compliance_event(
        self,
        regulation: str,
        event_type: str,
        status: str,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """Log compliance-related event."""
        compliance_entry = {
            "event_type": "compliance_event",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "regulation": regulation,  # GDPR, SOX, PCI-DSS, etc.
            "compliance_event_type": event_type,
            "status": status,
        }

        if additional_data:
            compliance_entry.update(additional_data)

        self.logger.info("Compliance event", extra=compliance_entry)


class PerformanceLogger:
    """Logger for performance monitoring."""

    def __init__(self):
        self.logger = get_logger("performance")

    def log_request_performance(
        self,
        method: str,
        endpoint: str,
        response_time: float,
        status_code: int,
        user_id: Optional[str] = None,
    ):
        """Log request performance metrics."""
        perf_entry = {
            "event_type": "request_performance",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": method,
            "endpoint": endpoint,
            "response_time": response_time,
            "status_code": status_code,
            "user_id": user_id,
        }

        # Log as warning if response time is slow
        if response_time > 2.0:
            self.logger.warning("Slow request detected", extra=perf_entry)
        else:
            self.logger.info("Request performance", extra=perf_entry)

    def log_database_performance(
        self,
        query_type: str,
        execution_time: float,
        affected_rows: Optional[int] = None,
    ):
        """Log database performance metrics."""
        db_entry = {
            "event_type": "database_performance",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query_type": query_type,
            "execution_time": execution_time,
            "affected_rows": affected_rows,
        }

        # Log as warning if query is slow
        if execution_time > 1.0:
            self.logger.warning("Slow database query", extra=db_entry)
        else:
            self.logger.debug("Database query performance", extra=db_entry)

    def log_external_api_performance(
        self, service: str, endpoint: str, response_time: float, status_code: int
    ):
        """Log external API performance."""
        api_entry = {
            "event_type": "external_api_performance",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": service,
            "endpoint": endpoint,
            "response_time": response_time,
            "status_code": status_code,
        }

        if response_time > 5.0 or status_code >= 400:
            self.logger.warning("External API issue", extra=api_entry)
        else:
            self.logger.info("External API call", extra=api_entry)


class BusinessLogger:
    """Logger for business events and metrics."""

    def __init__(self):
        self.logger = get_logger("business")

    def log_user_registration(
        self, user_id: str, user_type: str, referral_source: Optional[str] = None
    ):
        """Log user registration event."""
        registration_entry = {
            "event_type": "user_registration",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "user_type": user_type,
            "referral_source": referral_source,
        }

        self.logger.info("User registration", extra=registration_entry)

    def log_agent_creation(self, user_id: str, agent_id: str, agent_type: str):
        """Log agent creation event."""
        agent_entry = {
            "event_type": "agent_creation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "agent_id": agent_id,
            "agent_type": agent_type,
        }

        self.logger.info("Agent creation", extra=agent_entry)

    def log_citizenship_application(
        self, user_id: str, agent_id: str, jurisdiction: str, status: str
    ):
        """Log citizenship application event."""
        citizenship_entry = {
            "event_type": "citizenship_application",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "agent_id": agent_id,
            "jurisdiction": jurisdiction,
            "status": status,
        }

        self.logger.info("Citizenship application", extra=citizenship_entry)

    def log_bond_creation(
        self, user_id: str, bond_id: str, bond_type: str, face_value: float
    ):
        """Log bond creation event."""
        bond_entry = {
            "event_type": "bond_creation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "bond_id": bond_id,
            "bond_type": bond_type,
            "face_value": face_value,
        }

        self.logger.info("Bond creation", extra=bond_entry)

    def log_payment_transaction(
        self,
        user_id: str,
        transaction_id: str,
        amount: float,
        currency: str,
        transaction_type: str,
        status: str,
    ):
        """Log payment transaction event."""
        payment_entry = {
            "event_type": "payment_transaction",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "transaction_type": transaction_type,
            "status": status,
        }

        self.logger.info("Payment transaction", extra=payment_entry)


# Global logger instances
audit_logger = AuditLogger()
performance_logger = PerformanceLogger()
business_logger = BusinessLogger()
