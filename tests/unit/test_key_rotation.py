"""
Unit tests for Key Rotation Manager.
"""

import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.security.key_rotation import (
    KeyMetadata,
    KeyRotationManager,
    KeyStatus,
    KeyType,
    RotationPolicy,
    check_key_health,
)


class TestKeyStatus:
    """Tests for KeyStatus enum."""

    def test_key_status_values(self):
        """Test key status values."""
        assert KeyStatus.ACTIVE.value == "active"
        assert KeyStatus.PENDING.value == "pending"
        assert KeyStatus.ARCHIVED.value == "archived"
        assert KeyStatus.REVOKED.value == "revoked"
        assert KeyStatus.EXPIRED.value == "expired"


class TestKeyType:
    """Tests for KeyType enum."""

    def test_key_type_values(self):
        """Test key type values."""
        assert KeyType.ED25519.value == "ed25519"
        assert KeyType.ML_DSA_65.value == "ml-dsa-65"
        assert KeyType.HYBRID.value == "hybrid"


class TestKeyMetadata:
    """Tests for KeyMetadata dataclass."""

    def test_create_key_metadata(self):
        """Test creating key metadata."""
        now = datetime.now(timezone.utc)
        metadata = KeyMetadata(
            key_id="key_123",
            key_type=KeyType.ED25519,
            version=1,
            status=KeyStatus.ACTIVE,
            created_at=now,
        )

        assert metadata.key_id == "key_123"
        assert metadata.key_type == KeyType.ED25519
        assert metadata.version == 1
        assert metadata.status == KeyStatus.ACTIVE
        assert metadata.created_at == now

    def test_key_metadata_defaults(self):
        """Test key metadata default values."""
        metadata = KeyMetadata(
            key_id="key_123",
            key_type=KeyType.ED25519,
            version=1,
            status=KeyStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )

        assert metadata.activated_at is None
        assert metadata.expires_at is None
        assert metadata.revoked_at is None
        assert metadata.revocation_reason is None
        assert metadata.public_key_hash == ""
        assert metadata.algorithm_params == {}

    def test_to_dict(self):
        """Test converting metadata to dictionary."""
        now = datetime.now(timezone.utc)
        metadata = KeyMetadata(
            key_id="key_123",
            key_type=KeyType.ED25519,
            version=1,
            status=KeyStatus.ACTIVE,
            created_at=now,
            activated_at=now,
            public_key_hash="abc123",
        )

        d = metadata.to_dict()

        assert d["key_id"] == "key_123"
        assert d["key_type"] == "ed25519"
        assert d["version"] == 1
        assert d["status"] == "active"
        assert d["public_key_hash"] == "abc123"

    def test_from_dict(self):
        """Test creating metadata from dictionary."""
        now = datetime.now(timezone.utc)
        data = {
            "key_id": "key_123",
            "key_type": "ed25519",
            "version": 1,
            "status": "active",
            "created_at": now.isoformat(),
            "activated_at": now.isoformat(),
            "expires_at": None,
            "revoked_at": None,
            "revocation_reason": None,
            "public_key_hash": "abc123",
            "algorithm_params": {},
        }

        metadata = KeyMetadata.from_dict(data)

        assert metadata.key_id == "key_123"
        assert metadata.key_type == KeyType.ED25519
        assert metadata.status == KeyStatus.ACTIVE

    def test_is_valid_for_signing_active(self):
        """Test is_valid_for_signing returns True for active key."""
        metadata = KeyMetadata(
            key_id="key_123",
            key_type=KeyType.ED25519,
            version=1,
            status=KeyStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=90),
        )

        assert metadata.is_valid_for_signing() is True

    def test_is_valid_for_signing_not_active(self):
        """Test is_valid_for_signing returns False for non-active key."""
        metadata = KeyMetadata(
            key_id="key_123",
            key_type=KeyType.ED25519,
            version=1,
            status=KeyStatus.ARCHIVED,
            created_at=datetime.now(timezone.utc),
        )

        assert metadata.is_valid_for_signing() is False

    def test_is_valid_for_signing_expired(self):
        """Test is_valid_for_signing returns False for expired key."""
        metadata = KeyMetadata(
            key_id="key_123",
            key_type=KeyType.ED25519,
            version=1,
            status=KeyStatus.ACTIVE,
            created_at=datetime.now(timezone.utc) - timedelta(days=100),
            expires_at=datetime.now(timezone.utc) - timedelta(days=10),
        )

        assert metadata.is_valid_for_signing() is False

    def test_is_valid_for_verification_active(self):
        """Test is_valid_for_verification for active key."""
        metadata = KeyMetadata(
            key_id="key_123",
            key_type=KeyType.ED25519,
            version=1,
            status=KeyStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )

        assert metadata.is_valid_for_verification() is True

    def test_is_valid_for_verification_archived(self):
        """Test is_valid_for_verification for archived key."""
        metadata = KeyMetadata(
            key_id="key_123",
            key_type=KeyType.ED25519,
            version=1,
            status=KeyStatus.ARCHIVED,
            created_at=datetime.now(timezone.utc),
        )

        assert metadata.is_valid_for_verification() is True

    def test_is_valid_for_verification_revoked(self):
        """Test is_valid_for_verification returns False for revoked key."""
        metadata = KeyMetadata(
            key_id="key_123",
            key_type=KeyType.ED25519,
            version=1,
            status=KeyStatus.REVOKED,
            created_at=datetime.now(timezone.utc),
        )

        assert metadata.is_valid_for_verification() is False


class TestRotationPolicy:
    """Tests for RotationPolicy dataclass."""

    def test_default_policy(self):
        """Test default policy values."""
        policy = RotationPolicy()

        assert policy.rotation_interval_days == 90
        assert policy.overlap_period_days == 7
        assert policy.max_archived_keys == 10
        assert policy.auto_rotate is True
        assert policy.notify_days_before == 14

    def test_custom_policy(self):
        """Test custom policy values."""
        policy = RotationPolicy(
            rotation_interval_days=30,
            overlap_period_days=14,
            max_archived_keys=5,
        )

        assert policy.rotation_interval_days == 30
        assert policy.overlap_period_days == 14
        assert policy.max_archived_keys == 5

    def test_policy_to_dict(self):
        """Test converting policy to dictionary."""
        policy = RotationPolicy(rotation_interval_days=30)

        d = policy.to_dict()

        assert d["rotation_interval_days"] == 30
        assert "overlap_period_days" in d
        assert "auto_rotate" in d

    def test_policy_from_dict(self):
        """Test creating policy from dictionary."""
        data = {
            "rotation_interval_days": 30,
            "overlap_period_days": 14,
            "max_archived_keys": 5,
            "auto_rotate": False,
            "notify_days_before": 7,
        }

        policy = RotationPolicy.from_dict(data)

        assert policy.rotation_interval_days == 30
        assert policy.auto_rotate is False


class TestKeyRotationManager:
    """Tests for KeyRotationManager class."""

    @pytest.fixture
    def temp_key_dir(self):
        """Create temporary directory for keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def manager(self, temp_key_dir):
        """Create a key rotation manager."""
        return KeyRotationManager(key_dir=temp_key_dir)

    def test_create_manager(self, manager):
        """Test creating a key rotation manager."""
        assert manager is not None
        assert manager.policy is not None
        assert manager.keys == {}

    def test_manager_creates_directories(self, temp_key_dir):
        """Test manager creates directory structure."""
        KeyRotationManager(key_dir=temp_key_dir)

        import os

        for subdir in ["active", "archived", "revoked", "pending"]:
            assert os.path.exists(os.path.join(temp_key_dir, subdir))

    def test_manager_custom_policy(self, temp_key_dir):
        """Test manager with custom policy."""
        policy = RotationPolicy(rotation_interval_days=30)
        manager = KeyRotationManager(key_dir=temp_key_dir, policy=policy)

        assert manager.policy.rotation_interval_days == 30

    def test_generate_key_id(self, manager):
        """Test generating key ID."""
        key_id = manager.generate_key_id(KeyType.ED25519)

        assert key_id is not None
        assert "ed25519" in key_id
        assert manager.signer_id in key_id

    def test_generate_key_id_different_types(self, manager):
        """Test key ID contains key type."""
        ed_id = manager.generate_key_id(KeyType.ED25519)
        pq_id = manager.generate_key_id(KeyType.ML_DSA_65)

        assert "ed25519" in ed_id
        assert "ml-dsa-65" in pq_id

    def test_create_key_ed25519(self, manager):
        """Test creating an Ed25519 key."""
        metadata = manager.create_key(KeyType.ED25519, activate_immediately=True)

        assert metadata is not None
        assert metadata.key_type == KeyType.ED25519
        assert metadata.status == KeyStatus.ACTIVE
        assert metadata.version == 1

    def test_create_key_pending(self, manager):
        """Test creating a pending key."""
        metadata = manager.create_key(KeyType.ED25519, activate_immediately=False)

        assert metadata.status == KeyStatus.PENDING
        assert metadata.activated_at is None

    def test_create_key_versioning(self, manager):
        """Test key versioning increments."""
        key1 = manager.create_key(KeyType.ED25519, activate_immediately=True)
        key2 = manager.create_key(KeyType.ED25519, activate_immediately=True)

        assert key1.version == 1
        assert key2.version == 2

    def test_create_key_custom_validity(self, manager):
        """Test creating key with custom validity period."""
        metadata = manager.create_key(
            KeyType.ED25519, activate_immediately=True, validity_days=30
        )

        assert metadata.expires_at is not None
        # Expiration should be approximately 30 days from now
        expected_expiry = datetime.now(timezone.utc) + timedelta(days=30)
        diff = abs((metadata.expires_at - expected_expiry).total_seconds())
        assert diff < 60  # Within 1 minute tolerance

    def test_activate_key(self, manager):
        """Test activating a pending key."""
        # Create pending key
        metadata = manager.create_key(KeyType.ED25519, activate_immediately=False)
        key_id = metadata.key_id

        # Activate it
        result = manager.activate_key(key_id)

        assert result is True
        assert manager.keys[key_id].status == KeyStatus.ACTIVE
        assert manager.keys[key_id].activated_at is not None

    def test_activate_key_not_found(self, manager):
        """Test activating non-existent key."""
        result = manager.activate_key("nonexistent_key")

        assert result is False

    def test_activate_key_not_pending(self, manager):
        """Test activating an already active key."""
        metadata = manager.create_key(KeyType.ED25519, activate_immediately=True)

        result = manager.activate_key(metadata.key_id)

        assert result is False

    def test_archive_key(self, manager):
        """Test archiving an active key."""
        metadata = manager.create_key(KeyType.ED25519, activate_immediately=True)
        key_id = metadata.key_id

        result = manager.archive_key(key_id)

        assert result is True
        assert manager.keys[key_id].status == KeyStatus.ARCHIVED

    def test_archive_key_not_found(self, manager):
        """Test archiving non-existent key."""
        result = manager.archive_key("nonexistent_key")

        assert result is False

    def test_archive_key_not_active(self, manager):
        """Test archiving a non-active key."""
        metadata = manager.create_key(KeyType.ED25519, activate_immediately=False)

        result = manager.archive_key(metadata.key_id)

        assert result is False

    def test_revoke_key(self, manager):
        """Test revoking a key."""
        metadata = manager.create_key(KeyType.ED25519, activate_immediately=True)
        key_id = metadata.key_id

        result = manager.revoke_key(key_id, "Compromised")

        assert result is True
        assert manager.keys[key_id].status == KeyStatus.REVOKED
        assert manager.keys[key_id].revocation_reason == "Compromised"
        assert manager.keys[key_id].revoked_at is not None

    def test_revoke_key_not_found(self, manager):
        """Test revoking non-existent key."""
        result = manager.revoke_key("nonexistent_key", "Testing")

        assert result is False

    def test_get_active_key(self, manager):
        """Test getting active key."""
        manager.create_key(KeyType.ED25519, activate_immediately=True)

        active = manager.get_active_key(KeyType.ED25519)

        assert active is not None
        assert active.key_type == KeyType.ED25519
        assert active.status == KeyStatus.ACTIVE

    def test_get_active_key_not_found(self, manager):
        """Test getting active key when none exists."""
        active = manager.get_active_key(KeyType.ED25519)

        assert active is None

    def test_get_key_for_verification(self, manager):
        """Test getting key for verification."""
        metadata = manager.create_key(KeyType.ED25519, activate_immediately=True)
        key_id = metadata.key_id

        key = manager.get_key_for_verification(key_id)

        assert key is not None
        assert key.key_id == key_id

    def test_get_key_for_verification_revoked(self, manager):
        """Test getting revoked key for verification."""
        metadata = manager.create_key(KeyType.ED25519, activate_immediately=True)
        key_id = metadata.key_id

        # Revoke the key
        manager.revoke_key(key_id, "Testing")

        # Should not be returned for verification
        key = manager.get_key_for_verification(key_id)
        assert key is None

    def test_list_keys(self, manager):
        """Test listing all keys."""
        manager.create_key(KeyType.ED25519, activate_immediately=True)
        manager.create_key(KeyType.ED25519, activate_immediately=False)

        keys = manager.list_keys()

        assert len(keys) == 2

    def test_list_keys_by_type(self, manager):
        """Test listing keys filtered by type."""
        manager.create_key(KeyType.ED25519, activate_immediately=True)

        ed_keys = manager.list_keys(key_type=KeyType.ED25519)

        assert len(ed_keys) == 1
        assert ed_keys[0].key_type == KeyType.ED25519

    def test_list_keys_by_status(self, manager):
        """Test listing keys filtered by status."""
        manager.create_key(KeyType.ED25519, activate_immediately=True)
        manager.create_key(KeyType.ED25519, activate_immediately=False)

        active_keys = manager.list_keys(status=KeyStatus.ACTIVE)
        pending_keys = manager.list_keys(status=KeyStatus.PENDING)

        assert len(active_keys) == 1
        assert len(pending_keys) == 1

    def test_check_rotation_needed_no_keys(self, manager):
        """Test checking rotation needed with no keys."""
        needs = manager.check_rotation_needed()

        assert needs == []

    def test_check_rotation_needed_new_key(self, manager):
        """Test checking rotation needed for new key."""
        manager.create_key(KeyType.ED25519, activate_immediately=True)

        needs = manager.check_rotation_needed()

        # New key should not need rotation
        assert needs == []

    def test_get_rotation_status(self, manager):
        """Test getting rotation status."""
        manager.create_key(KeyType.ED25519, activate_immediately=True)

        status = manager.get_rotation_status()

        assert status["total_keys"] == 1
        assert status["active_keys"] == 1
        assert status["archived_keys"] == 0
        assert status["revoked_keys"] == 0
        assert "policy" in status

    def test_rotate_keys(self, manager):
        """Test rotating keys."""
        # Create initial key
        old_key = manager.create_key(KeyType.ED25519, activate_immediately=True)
        old_id = old_key.key_id

        # Rotate
        new_keys = manager.rotate_keys(KeyType.ED25519)

        assert len(new_keys) == 1
        assert new_keys[0].status == KeyStatus.ACTIVE
        # Old key should be archived
        assert manager.keys[old_id].status == KeyStatus.ARCHIVED


class TestCheckKeyHealth:
    """Tests for check_key_health convenience function."""

    def test_check_key_health(self):
        """Test check_key_health function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manager and add a key
            manager = KeyRotationManager(key_dir=tmpdir)
            manager.create_key(KeyType.ED25519, activate_immediately=True)

            # Check health
            health = check_key_health(key_dir=tmpdir)

            assert health["total_keys"] == 1
            assert health["active_keys"] == 1
