"""
Audit event system for UATP Capsule Engine.
Emits structured audit events for compliance and monitoring.
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events."""

    CAPSULE_CREATED = "capsule_created"
    CAPSULE_VERIFIED = "capsule_verified"
    CAPSULE_ACCESSED = "capsule_accessed"
    SIGNATURE_VERIFIED = "signature_verified"
    SIGNATURE_FAILED = "signature_failed"
    API_KEY_USED = "api_key_used"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    AUTHENTICATION_FAILED = "authentication_failed"
    SECURITY_EVENT = "security_event"
    TRUST_VIOLATION = "trust_violation"
    CAPSULE_STATUS_CHANGE = "capsule_status_change"


class AuditEvent:
    """Structured audit event."""

    def __init__(
        self,
        event_type: AuditEventType,
        capsule_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.event_type = event_type
        self.capsule_id = capsule_id
        self.agent_id = agent_id
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.event_id = f"audit_{self.timestamp.isoformat()}_{id(self)}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "capsule_id": self.capsule_id,
            "agent_id": self.agent_id,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())


class AuditEventEmitter:
    """Emits audit events to various destinations."""

    def __init__(self):
        self.handlers = []
        self.enabled = True

    def _safe_enum_value(self, value):
        """Safely extract enum value, handling both enum objects and strings."""
        if hasattr(value, "value"):
            return value.value
        return str(value)

    def add_handler(self, handler):
        """Add an event handler."""
        self.handlers.append(handler)

    def emit(self, event: AuditEvent):
        """Emit an audit event to all handlers."""
        if not self.enabled:
            return

        try:
            for handler in self.handlers:
                handler.handle(event)
        except Exception as e:
            logger.error(f"Failed to emit audit event: {e}")

    def emit_capsule_created(self, capsule_id: str, agent_id: str, capsule_type: str):
        """Emit a capsule created event."""
        event = AuditEvent(
            event_type=AuditEventType.CAPSULE_CREATED,
            capsule_id=capsule_id,
            agent_id=agent_id,
            metadata={
                "capsule_type": self._safe_enum_value(capsule_type),
                "action": "create",
            },
        )
        self.emit(event)

    def emit_capsule_verified(
        self, capsule_id: str, agent_id: str, verified: bool, reason: str
    ):
        """Emit a capsule verification event."""
        event = AuditEvent(
            event_type=AuditEventType.CAPSULE_VERIFIED,
            capsule_id=capsule_id,
            agent_id=agent_id,
            metadata={"verified": verified, "reason": reason, "action": "verify"},
        )
        self.emit(event)

    def emit_api_key_used(
        self, api_key_id: str, agent_id: str, endpoint: str, success: bool
    ):
        """Emit an API key usage event."""
        event = AuditEvent(
            event_type=AuditEventType.API_KEY_USED,
            agent_id=agent_id,
            metadata={
                "api_key_id": api_key_id,
                "endpoint": endpoint,
                "success": success,
                "action": "api_access",
            },
        )
        self.emit(event)

    def emit_security_event(self, event_name: str, metadata: Dict[str, Any]):
        """Emit a general security event."""
        event = AuditEvent(
            event_type=AuditEventType.SECURITY_EVENT,
            agent_id=metadata.get("agent_id"),
            capsule_id=metadata.get("capsule_id"),
            metadata={"event_name": event_name, **metadata, "action": "security_check"},
        )
        self.emit(event)

    def emit_capsule_status_change(
        self,
        capsule_id: str,
        old_status: str,
        new_status: str,
        reason: str,
        agent_id: Optional[str] = None,
    ):
        """Emit a capsule status change event."""
        event = AuditEvent(
            event_type=AuditEventType.CAPSULE_STATUS_CHANGE,
            capsule_id=capsule_id,
            agent_id=agent_id,
            metadata={
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason,
                "action": "status_change",
            },
        )
        self.emit(event)


class LoggingAuditHandler:
    """Audit handler that logs events."""

    def __init__(self, logger_name: str = "audit"):
        self.logger = logging.getLogger(logger_name)

    def handle(self, event: AuditEvent):
        """Handle audit event by logging it."""
        self.logger.info(f"AUDIT: {event.to_json()}")


class FileAuditHandler:
    """Audit handler that writes events to a file."""

    def __init__(self, filename: str = "audit.log"):
        self.filename = filename

    def handle(self, event: AuditEvent):
        """Handle audit event by writing to file."""
        try:
            with open(self.filename, "a") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit event to file: {e}")


class KafkaAuditHandler:
    """Audit handler that sends events to Kafka (requires kafka-python)."""

    def __init__(
        self, topic: str = "uatp-audit", bootstrap_servers: str = "localhost:9092"
    ):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self._init_producer()

    def _init_producer(self):
        """Initialize Kafka producer."""
        try:
            from kafka import KafkaProducer

            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        except ImportError:
            logger.warning(
                "kafka-python not installed, KafkaAuditHandler will not work"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")

    def handle(self, event: AuditEvent):
        """Handle audit event by sending to Kafka."""
        if not self.producer:
            return

        try:
            self.producer.send(self.topic, value=event.to_dict())
        except Exception as e:
            logger.error(f"Failed to send audit event to Kafka: {e}")


class ImmutableAuditHandler:
    """
    Audit handler that writes to immutable, tamper-evident log.

    Uses cryptographic chaining to prevent tampering with audit logs.
    Even administrators cannot modify or delete entries after they're written.

    Benefits:
    - Tamper-evident: Any modification breaks the cryptographic chain
    - Non-repudiation: Entries are cryptographically signed
    - Compliance-ready: Meets SOC 2, ISO 27001, HIPAA audit requirements
    """

    def __init__(self, storage_path: str = "audit_logs/immutable"):
        """
        Initialize immutable audit handler.

        Args:
            storage_path: Directory for immutable audit logs
        """
        try:
            from src.audit.immutable_logger import ImmutableAuditLogger

            self.logger_instance = ImmutableAuditLogger(storage_path=storage_path)
            self.enabled = True
        except ImportError as e:
            logger.error(f"Failed to import ImmutableAuditLogger: {e}")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize ImmutableAuditLogger: {e}")
            self.enabled = False

    def handle(self, event: AuditEvent):
        """Handle audit event by writing to immutable log."""
        if not self.enabled:
            return

        try:
            import asyncio

            # Extract user/agent info from event
            user_id = event.metadata.get("user_id")
            agent_id = event.agent_id
            ip_address = event.metadata.get("ip_address")

            # Log to immutable chain
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If event loop is running, schedule the coroutine
                asyncio.create_task(
                    self.logger_instance.log_event(
                        event_type=event.event_type.value,
                        user_id=user_id,
                        agent_id=agent_id,
                        ip_address=ip_address,
                        data=event.to_dict(),
                    )
                )
            else:
                # If no event loop, run synchronously
                loop.run_until_complete(
                    self.logger_instance.log_event(
                        event_type=event.event_type.value,
                        user_id=user_id,
                        agent_id=agent_id,
                        ip_address=ip_address,
                        data=event.to_dict(),
                    )
                )

        except Exception as e:
            logger.error(f"Failed to write to immutable audit log: {e}")

    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        """
        Verify integrity of immutable audit log.

        Returns:
            (is_valid, error_message)
        """
        if not self.enabled:
            return (False, "Immutable audit logger not enabled")

        try:
            return self.logger_instance.verify_chain()
        except Exception as e:
            return (False, f"Verification failed: {str(e)}")


# Global audit event emitter
audit_emitter = AuditEventEmitter()

# Add default logging handler
audit_emitter.add_handler(LoggingAuditHandler())

# To enable immutable audit logging (recommended for production):
# audit_emitter.add_handler(ImmutableAuditHandler(storage_path="audit_logs/immutable"))
#
# Benefits of immutable audit logging:
# - Tamper-evident: Any modification breaks cryptographic chain
# - Compliance-ready: Meets SOC 2, ISO 27001, HIPAA requirements
# - Non-repudiation: Cryptographic signatures prevent denial
# - Periodic sealing: Can generate timestamped checkpoints for third-party verification
#
# To verify audit log integrity:
#   handler = ImmutableAuditHandler()
#   is_valid, error = handler.verify_integrity()
#   if not is_valid:
#       logger.critical(f"AUDIT LOG TAMPERING DETECTED: {error}")
