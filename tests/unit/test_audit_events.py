"""
Unit tests for Audit Events.
"""

import json
import tempfile
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.audit.events import (
    AuditEvent,
    AuditEventEmitter,
    AuditEventType,
    FileAuditHandler,
    LoggingAuditHandler,
    audit_emitter,
)


class TestAuditEventType:
    """Tests for AuditEventType enum."""

    def test_event_types_exist(self):
        """Test that expected event types exist."""
        assert AuditEventType.CAPSULE_CREATED == "capsule_created"
        assert AuditEventType.CAPSULE_VERIFIED == "capsule_verified"
        assert AuditEventType.SIGNATURE_VERIFIED == "signature_verified"
        assert AuditEventType.SECURITY_EVENT == "security_event"

    def test_event_type_values(self):
        """Test event type string values."""
        assert AuditEventType.API_KEY_USED.value == "api_key_used"
        assert AuditEventType.TRUST_VIOLATION.value == "trust_violation"


class TestAuditEvent:
    """Tests for AuditEvent class."""

    def test_create_event(self):
        """Test creating an audit event."""
        event = AuditEvent(
            event_type=AuditEventType.CAPSULE_CREATED,
            capsule_id="caps_123",
            agent_id="agent_456",
        )

        assert event.event_type == AuditEventType.CAPSULE_CREATED
        assert event.capsule_id == "caps_123"
        assert event.agent_id == "agent_456"

    def test_event_with_metadata(self):
        """Test event with metadata."""
        event = AuditEvent(
            event_type=AuditEventType.SECURITY_EVENT,
            metadata={"threat_level": "high", "source": "api"},
        )

        assert event.metadata["threat_level"] == "high"
        assert event.metadata["source"] == "api"

    def test_event_default_timestamp(self):
        """Test event gets default timestamp."""
        event = AuditEvent(event_type=AuditEventType.CAPSULE_ACCESSED)

        assert event.timestamp is not None
        assert event.timestamp.tzinfo == timezone.utc

    def test_event_custom_timestamp(self):
        """Test event with custom timestamp."""
        custom_time = datetime(2026, 3, 12, 10, 0, 0, tzinfo=timezone.utc)
        event = AuditEvent(
            event_type=AuditEventType.CAPSULE_VERIFIED,
            timestamp=custom_time,
        )

        assert event.timestamp == custom_time

    def test_event_id_generated(self):
        """Test event ID is generated."""
        event = AuditEvent(event_type=AuditEventType.CAPSULE_CREATED)

        assert event.event_id is not None
        assert "audit_" in event.event_id

    def test_to_dict(self):
        """Test converting event to dictionary."""
        event = AuditEvent(
            event_type=AuditEventType.CAPSULE_CREATED,
            capsule_id="caps_123",
            agent_id="agent_456",
            metadata={"action": "create"},
        )

        d = event.to_dict()

        assert d["event_type"] == "capsule_created"
        assert d["capsule_id"] == "caps_123"
        assert d["agent_id"] == "agent_456"
        assert d["metadata"]["action"] == "create"

    def test_to_json(self):
        """Test converting event to JSON."""
        event = AuditEvent(
            event_type=AuditEventType.CAPSULE_CREATED,
            capsule_id="caps_123",
        )

        json_str = event.to_json()
        parsed = json.loads(json_str)

        assert parsed["capsule_id"] == "caps_123"
        assert parsed["event_type"] == "capsule_created"


class TestAuditEventEmitter:
    """Tests for AuditEventEmitter class."""

    def test_create_emitter(self):
        """Test creating an emitter."""
        emitter = AuditEventEmitter()

        assert emitter.enabled is True
        assert emitter.handlers == []

    def test_add_handler(self):
        """Test adding a handler."""
        emitter = AuditEventEmitter()
        handler = MagicMock()

        emitter.add_handler(handler)

        assert handler in emitter.handlers

    def test_emit_calls_handlers(self):
        """Test emit calls all handlers."""
        emitter = AuditEventEmitter()
        handler1 = MagicMock()
        handler2 = MagicMock()
        emitter.add_handler(handler1)
        emitter.add_handler(handler2)

        event = AuditEvent(event_type=AuditEventType.CAPSULE_CREATED)
        emitter.emit(event)

        handler1.handle.assert_called_once_with(event)
        handler2.handle.assert_called_once_with(event)

    def test_emit_disabled(self):
        """Test emit does nothing when disabled."""
        emitter = AuditEventEmitter()
        emitter.enabled = False
        handler = MagicMock()
        emitter.add_handler(handler)

        event = AuditEvent(event_type=AuditEventType.CAPSULE_CREATED)
        emitter.emit(event)

        handler.handle.assert_not_called()

    def test_emit_capsule_created(self):
        """Test emit_capsule_created helper."""
        emitter = AuditEventEmitter()
        handler = MagicMock()
        emitter.add_handler(handler)

        emitter.emit_capsule_created("caps_123", "agent_456", "reasoning")

        handler.handle.assert_called_once()
        event = handler.handle.call_args[0][0]
        assert event.event_type == AuditEventType.CAPSULE_CREATED
        assert event.capsule_id == "caps_123"

    def test_emit_capsule_verified(self):
        """Test emit_capsule_verified helper."""
        emitter = AuditEventEmitter()
        handler = MagicMock()
        emitter.add_handler(handler)

        emitter.emit_capsule_verified("caps_123", "agent_456", True, "Valid signature")

        handler.handle.assert_called_once()
        event = handler.handle.call_args[0][0]
        assert event.event_type == AuditEventType.CAPSULE_VERIFIED
        assert event.metadata["verified"] is True

    def test_emit_api_key_used(self):
        """Test emit_api_key_used helper."""
        emitter = AuditEventEmitter()
        handler = MagicMock()
        emitter.add_handler(handler)

        emitter.emit_api_key_used("key_123", "agent_456", "/api/capsules", True)

        handler.handle.assert_called_once()
        event = handler.handle.call_args[0][0]
        assert event.event_type == AuditEventType.API_KEY_USED
        assert event.metadata["endpoint"] == "/api/capsules"

    def test_emit_security_event(self):
        """Test emit_security_event helper."""
        emitter = AuditEventEmitter()
        handler = MagicMock()
        emitter.add_handler(handler)

        emitter.emit_security_event("login_attempt", {"ip": "1.2.3.4"})

        handler.handle.assert_called_once()
        event = handler.handle.call_args[0][0]
        assert event.event_type == AuditEventType.SECURITY_EVENT
        assert event.metadata["event_name"] == "login_attempt"

    def test_emit_capsule_status_change(self):
        """Test emit_capsule_status_change helper."""
        emitter = AuditEventEmitter()
        handler = MagicMock()
        emitter.add_handler(handler)

        emitter.emit_capsule_status_change(
            "caps_123", "pending", "active", "Verification passed"
        )

        handler.handle.assert_called_once()
        event = handler.handle.call_args[0][0]
        assert event.event_type == AuditEventType.CAPSULE_STATUS_CHANGE
        assert event.metadata["old_status"] == "pending"
        assert event.metadata["new_status"] == "active"

    def test_safe_enum_value_with_enum(self):
        """Test _safe_enum_value with enum object."""
        emitter = AuditEventEmitter()

        result = emitter._safe_enum_value(AuditEventType.CAPSULE_CREATED)
        assert result == "capsule_created"

    def test_safe_enum_value_with_string(self):
        """Test _safe_enum_value with string."""
        emitter = AuditEventEmitter()

        result = emitter._safe_enum_value("test_string")
        assert result == "test_string"


class TestLoggingAuditHandler:
    """Tests for LoggingAuditHandler."""

    def test_handle_logs_event(self):
        """Test handler logs event."""
        handler = LoggingAuditHandler()
        event = AuditEvent(
            event_type=AuditEventType.CAPSULE_CREATED,
            capsule_id="caps_123",
        )

        with patch.object(handler.logger, "info") as mock_log:
            handler.handle(event)

            mock_log.assert_called_once()
            logged_msg = mock_log.call_args[0][0]
            assert "AUDIT:" in logged_msg
            assert "caps_123" in logged_msg


class TestFileAuditHandler:
    """Tests for FileAuditHandler."""

    def test_handle_writes_to_file(self):
        """Test handler writes event to file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            filename = f.name

        handler = FileAuditHandler(filename=filename)
        event = AuditEvent(
            event_type=AuditEventType.CAPSULE_CREATED,
            capsule_id="caps_123",
        )

        handler.handle(event)

        with open(filename) as f:
            content = f.read()
            assert "caps_123" in content
            assert "capsule_created" in content

    def test_handle_appends_multiple(self):
        """Test handler appends multiple events."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            filename = f.name

        handler = FileAuditHandler(filename=filename)

        for i in range(3):
            event = AuditEvent(
                event_type=AuditEventType.CAPSULE_CREATED,
                capsule_id=f"caps_{i}",
            )
            handler.handle(event)

        with open(filename) as f:
            lines = f.readlines()
            assert len(lines) == 3


class TestGlobalEmitter:
    """Tests for global audit_emitter."""

    def test_global_emitter_exists(self):
        """Test global emitter exists."""
        assert audit_emitter is not None
        assert isinstance(audit_emitter, AuditEventEmitter)

    def test_global_emitter_has_default_handler(self):
        """Test global emitter has default logging handler."""
        assert len(audit_emitter.handlers) >= 1
        assert any(isinstance(h, LoggingAuditHandler) for h in audit_emitter.handlers)
