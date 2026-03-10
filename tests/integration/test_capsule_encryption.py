"""
Integration tests for Capsule Encryption.

Tests verify that:
1. Per-user key derivation works correctly
2. Keys are deterministic (same user_id -> same key)
3. Different users get different keys
4. Key derivation is cryptographically sound

Run with: pytest tests/integration/test_capsule_encryption.py -v
"""

import base64
import os
import sys

import pytest

sys.path.insert(0, ".")

# Set environment for testing
os.environ.setdefault("ENVIRONMENT", "development")


class TestKeyDerivation:
    """Test per-user encryption key derivation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.user_id_a = "550e8400-e29b-41d4-a716-446655440000"
        self.user_id_b = "550e8400-e29b-41d4-a716-446655440001"

    def test_key_manager_imports(self):
        """Test that SecureKeyManager can be imported."""
        from src.security.secure_key_manager import (
            SecureKeyManager,
            create_secure_key_manager,
        )

        assert SecureKeyManager is not None
        assert create_secure_key_manager is not None

    def test_derive_user_encryption_key_exists(self):
        """Test that derive_user_encryption_key method exists."""
        from src.security.secure_key_manager import SecureKeyManager

        assert hasattr(SecureKeyManager, "derive_user_encryption_key")

    def test_derive_user_key_returns_32_bytes(self):
        """Test that derived key is 32 bytes (AES-256)."""
        from src.security.secure_key_manager import create_secure_key_manager

        key_manager = create_secure_key_manager()
        user_key = key_manager.derive_user_encryption_key(self.user_id_a)

        assert user_key is not None
        assert isinstance(user_key, bytes)
        assert len(user_key) == 32, f"Expected 32 bytes, got {len(user_key)}"

    def test_same_user_gets_same_key(self):
        """Test that the same user_id always produces the same key."""
        from src.security.secure_key_manager import create_secure_key_manager

        key_manager = create_secure_key_manager()

        key1 = key_manager.derive_user_encryption_key(self.user_id_a)
        key2 = key_manager.derive_user_encryption_key(self.user_id_a)

        assert key1 == key2, "Same user should get same key"

    def test_different_users_get_different_keys(self):
        """Test that different user_ids produce different keys."""
        from src.security.secure_key_manager import create_secure_key_manager

        key_manager = create_secure_key_manager()

        key_a = key_manager.derive_user_encryption_key(self.user_id_a)
        key_b = key_manager.derive_user_encryption_key(self.user_id_b)

        assert key_a != key_b, "Different users should get different keys"

    def test_key_is_base64_encodable(self):
        """Test that derived key can be base64 encoded for transport."""
        from src.security.secure_key_manager import create_secure_key_manager

        key_manager = create_secure_key_manager()
        user_key = key_manager.derive_user_encryption_key(self.user_id_a)

        # Should be able to encode/decode without error
        encoded = base64.b64encode(user_key).decode("utf-8")
        decoded = base64.b64decode(encoded)

        assert decoded == user_key


class TestEncryptionUtilities:
    """Test encryption utilities (Python-side simulation of frontend encryption)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.user_id = "550e8400-e29b-41d4-a716-446655440000"
        self.test_payload = {
            "reasoning_steps": [{"step": 1, "content": "test"}],
            "conclusion": "done",
        }

    def test_aes_gcm_encryption_roundtrip(self):
        """Test AES-GCM encryption/decryption roundtrip."""
        import json

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        from src.security.secure_key_manager import create_secure_key_manager

        # Get user key
        key_manager = create_secure_key_manager()
        user_key = key_manager.derive_user_encryption_key(self.user_id)

        # Encrypt payload
        aesgcm = AESGCM(user_key)
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        plaintext = json.dumps(self.test_payload).encode("utf-8")
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        # Decrypt payload
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        decrypted_payload = json.loads(decrypted.decode("utf-8"))

        assert decrypted_payload == self.test_payload

    def test_encryption_produces_different_ciphertext_each_time(self):
        """Test that encryption with random nonce produces different ciphertext."""
        import json

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        from src.security.secure_key_manager import create_secure_key_manager

        key_manager = create_secure_key_manager()
        user_key = key_manager.derive_user_encryption_key(self.user_id)

        aesgcm = AESGCM(user_key)
        plaintext = json.dumps(self.test_payload).encode("utf-8")

        # Encrypt twice with different nonces
        nonce1 = os.urandom(12)
        nonce2 = os.urandom(12)

        ciphertext1 = aesgcm.encrypt(nonce1, plaintext, None)
        ciphertext2 = aesgcm.encrypt(nonce2, plaintext, None)

        assert (
            ciphertext1 != ciphertext2
        ), "Different nonces should produce different ciphertext"

    def test_wrong_key_fails_decryption(self):
        """Test that decryption with wrong key fails."""
        import json

        from cryptography.exceptions import InvalidTag
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        from src.security.secure_key_manager import create_secure_key_manager

        key_manager = create_secure_key_manager()
        user_key_a = key_manager.derive_user_encryption_key(self.user_id)
        user_key_b = key_manager.derive_user_encryption_key("different-user-id")

        # Encrypt with user A's key
        aesgcm_a = AESGCM(user_key_a)
        nonce = os.urandom(12)
        plaintext = json.dumps(self.test_payload).encode("utf-8")
        ciphertext = aesgcm_a.encrypt(nonce, plaintext, None)

        # Try to decrypt with user B's key - should fail
        aesgcm_b = AESGCM(user_key_b)
        with pytest.raises(InvalidTag):
            aesgcm_b.decrypt(nonce, ciphertext, None)


class TestKeyRouter:
    """Test the user keys router endpoints."""

    def test_router_imports(self):
        """Test that user keys router can be imported."""
        from src.api.user_keys_router import router

        assert router is not None

    def test_router_has_encryption_key_endpoint(self):
        """Test that router has my-encryption-key endpoint."""
        from src.api.user_keys_router import router

        # Check routes
        routes = [route.path for route in router.routes]
        assert "/my-encryption-key" in routes or any(
            "my-encryption-key" in r for r in routes
        )

    def test_router_has_key_info_endpoint(self):
        """Test that router has key-info endpoint."""
        from src.api.user_keys_router import router

        routes = [route.path for route in router.routes]
        assert "/key-info" in routes or any("key-info" in r for r in routes)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
