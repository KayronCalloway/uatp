"""
Unit tests for Immutable Audit Logger.
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.audit.immutable_logger import AuditLogEntry, ImmutableAuditLogger


class TestAuditLogEntry:
    """Tests for AuditLogEntry dataclass."""

    def test_create_entry(self):
        """Test creating an audit log entry."""
        entry = AuditLogEntry(
            sequence_number=1,
            timestamp="2026-03-12T10:00:00+00:00",
            event_type="test.event",
            user_id="user_123",
            agent_id="agent_456",
            ip_address="192.168.1.1",
            data={"action": "test"},
            previous_hash="0" * 64,
            entry_hash="a" * 64,
            signature="b" * 128,
        )

        assert entry.sequence_number == 1
        assert entry.event_type == "test.event"
        assert entry.user_id == "user_123"
        assert entry.data == {"action": "test"}


class TestImmutableAuditLogger:
    """Tests for ImmutableAuditLogger."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def logger(self, temp_storage):
        """Create a logger instance with temp storage."""
        return ImmutableAuditLogger(storage_path=temp_storage)

    @pytest.mark.asyncio
    async def test_log_event_basic(self, logger):
        """Test logging a basic event."""
        entry = await logger.log_event(
            event_type="capsule.created",
            user_id="user_123",
            data={"capsule_id": "cap_abc"},
        )

        assert entry.sequence_number == 1
        assert entry.event_type == "capsule.created"
        assert entry.user_id == "user_123"
        assert entry.previous_hash == "0" * 64  # Genesis hash
        assert len(entry.entry_hash) == 64
        assert len(entry.signature) > 0

    @pytest.mark.asyncio
    async def test_log_event_chain(self, logger):
        """Test that events are chained correctly."""
        entry1 = await logger.log_event(
            event_type="event.first",
            data={"num": 1},
        )
        entry2 = await logger.log_event(
            event_type="event.second",
            data={"num": 2},
        )

        assert entry2.sequence_number == 2
        assert entry2.previous_hash == entry1.entry_hash

    @pytest.mark.asyncio
    async def test_verify_chain_valid(self, logger):
        """Test chain verification passes for valid chain."""
        await logger.log_event(event_type="test.1")
        await logger.log_event(event_type="test.2")
        await logger.log_event(event_type="test.3")

        is_valid, error = logger.verify_chain()

        assert is_valid is True
        assert error is None

    def test_verify_empty_chain(self, logger):
        """Test verifying empty chain is valid."""
        is_valid, error = logger.verify_chain()

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_verify_chain_detects_tamper(self, logger):
        """Test that tampering is detected."""
        await logger.log_event(event_type="test.1")
        await logger.log_event(event_type="test.2")

        # Tamper with the chain file
        chain_file = Path(logger.storage_path) / "audit_chain.jsonl"
        with open(chain_file) as f:
            lines = f.readlines()

        # Modify the first entry
        entry = json.loads(lines[0])
        entry["event_type"] = "tampered.event"
        lines[0] = json.dumps(entry) + "\n"

        with open(chain_file, "w") as f:
            f.writelines(lines)

        is_valid, error = logger.verify_chain()

        assert is_valid is False
        assert "tampered" in error.lower() or "mismatch" in error.lower()

    @pytest.mark.asyncio
    async def test_get_recent_entries(self, logger):
        """Test getting recent entries."""
        for i in range(5):
            await logger.log_event(event_type=f"test.{i}")

        recent = logger.get_recent_entries(count=3)

        assert len(recent) == 3
        assert recent[-1].event_type == "test.4"

    @pytest.mark.asyncio
    async def test_search_by_event_type(self, logger):
        """Test searching by event type."""
        await logger.log_event(event_type="capsule.created")
        await logger.log_event(event_type="policy.approved")
        await logger.log_event(event_type="capsule.created")

        results = logger.search_entries(event_type="capsule.created")

        assert len(results) == 2
        assert all(e.event_type == "capsule.created" for e in results)

    @pytest.mark.asyncio
    async def test_search_by_user_id(self, logger):
        """Test searching by user ID."""
        await logger.log_event(event_type="test", user_id="alice")
        await logger.log_event(event_type="test", user_id="bob")
        await logger.log_event(event_type="test", user_id="alice")

        results = logger.search_entries(user_id="alice")

        assert len(results) == 2
        assert all(e.user_id == "alice" for e in results)

    @pytest.mark.asyncio
    async def test_seal_chain(self, logger):
        """Test sealing the chain."""
        await logger.log_event(event_type="test.1")
        await logger.log_event(event_type="test.2")

        seal = await logger.seal_chain()

        assert "seal_timestamp" in seal
        assert seal["total_entries"] == 2
        assert "seal_signature" in seal

    @pytest.mark.asyncio
    async def test_seal_empty_chain_raises(self, logger):
        """Test sealing empty chain raises error."""
        with pytest.raises(ValueError, match="Cannot seal empty chain"):
            await logger.seal_chain()


class TestLoggerPersistence:
    """Tests for logger persistence and chain loading."""

    @pytest.mark.asyncio
    async def test_load_existing_chain(self):
        """Test loading existing chain state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create logger and add entries
            logger1 = ImmutableAuditLogger(storage_path=tmpdir)
            await logger1.log_event(event_type="test.1")
            await logger1.log_event(event_type="test.2")
            last_hash = logger1.last_entry.entry_hash

            # Create new logger instance with same storage
            logger2 = ImmutableAuditLogger(storage_path=tmpdir)

            # Should continue from where we left off
            assert logger2.sequence_number == 2
            assert logger2.last_entry.entry_hash == last_hash

            # New entry should chain correctly
            entry3 = await logger2.log_event(event_type="test.3")
            assert entry3.sequence_number == 3
            assert entry3.previous_hash == last_hash


class TestComputeEntryHash:
    """Tests for hash computation."""

    def test_hash_deterministic(self):
        """Test that hash is deterministic for same input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ImmutableAuditLogger(storage_path=tmpdir)

            entry_data = {
                "sequence_number": 1,
                "timestamp": "2026-03-12T10:00:00+00:00",
                "event_type": "test",
                "user_id": None,
                "agent_id": None,
                "ip_address": None,
                "data": {},
                "previous_hash": "0" * 64,
            }

            hash1 = logger._compute_entry_hash(entry_data)
            hash2 = logger._compute_entry_hash(entry_data)

            assert hash1 == hash2
            assert len(hash1) == 64

    def test_hash_changes_with_data(self):
        """Test that hash changes when data changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ImmutableAuditLogger(storage_path=tmpdir)

            data1 = {"sequence_number": 1, "event_type": "a"}
            data2 = {"sequence_number": 1, "event_type": "b"}

            hash1 = logger._compute_entry_hash(data1)
            hash2 = logger._compute_entry_hash(data2)

            assert hash1 != hash2
