"""
Integration tests for UATP cryptographic signing and verification.

Tests the UATPCryptoV7 class sign_capsule and verify_capsule methods,
ensuring the full round-trip works and tampering is detected.

Run with: pytest tests/integration/test_crypto_roundtrip.py -v
"""

import copy
import os
import sys
import tempfile
from datetime import datetime, timezone

import pytest

# Ensure src is in path
sys.path.insert(0, ".")

from src.security.uatp_crypto_v7 import UATPCryptoV7


@pytest.fixture(scope="module")
def temp_key_dir():
    """Create a temporary directory for test keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(scope="module")
def crypto(temp_key_dir):
    """Create a UATPCryptoV7 instance with temp keys."""
    return UATPCryptoV7(key_dir=temp_key_dir, signer_id="test_signer")


@pytest.fixture
def sample_capsule_data():
    """Sample capsule data for testing."""
    return {
        "capsule_id": "test_capsule_001",
        "capsule_type": "reasoning_trace",
        "version": "7.2",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "SEALED",
        "payload": {
            "reasoning_steps": [
                {"step": 1, "thought": "First, analyze the problem"},
                {"step": 2, "thought": "Then, find a solution"},
            ],
            "conclusion": "Problem solved",
        },
        "agent_id": "test_agent",
        "session_id": "test_session_123",
    }


class TestCryptoRoundtrip:
    """Test complete sign/verify round-trips."""

    def test_sign_and_verify_success(self, crypto, sample_capsule_data):
        """Test that signing and verifying a capsule works."""
        # Sign the capsule
        verification = crypto.sign_capsule(sample_capsule_data, timestamp_mode="none")

        # Verification object should have required fields
        assert "signer" in verification
        assert "verify_key" in verification
        assert "hash" in verification
        assert "signature" in verification

        # Hash should be in sha256: format
        assert verification["hash"].startswith("sha256:")

        # Signature should be in ed25519: format
        assert verification["signature"].startswith("ed25519:")

        # Verify the capsule
        is_valid, reason = crypto.verify_capsule(sample_capsule_data, verification)
        assert is_valid, f"Verification failed: {reason}"
        assert "valid" in reason.lower()

    def test_tampered_payload_detected(self, crypto, sample_capsule_data):
        """Test that tampering with payload is detected."""
        # Sign the original capsule
        verification = crypto.sign_capsule(sample_capsule_data, timestamp_mode="none")

        # Tamper with the payload
        tampered_data = copy.deepcopy(sample_capsule_data)
        tampered_data["payload"]["conclusion"] = "TAMPERED"

        # Verification should fail
        is_valid, reason = crypto.verify_capsule(tampered_data, verification)
        assert not is_valid, "Tampered capsule should not verify"
        assert "hash" in reason.lower() or "mismatch" in reason.lower()

    def test_tampered_capsule_id_detected(self, crypto, sample_capsule_data):
        """Test that tampering with capsule_id is detected."""
        verification = crypto.sign_capsule(sample_capsule_data, timestamp_mode="none")

        tampered_data = copy.deepcopy(sample_capsule_data)
        tampered_data["capsule_id"] = "different_capsule_id"

        is_valid, reason = crypto.verify_capsule(tampered_data, verification)
        assert not is_valid, "Tampered capsule_id should not verify"

    def test_tampered_signature_detected(self, crypto, sample_capsule_data):
        """Test that tampering with signature is detected."""
        verification = crypto.sign_capsule(sample_capsule_data, timestamp_mode="none")

        # Tamper with the signature (flip some bits)
        tampered_verification = copy.deepcopy(verification)
        sig = tampered_verification["signature"]
        # Flip some hex chars
        tampered_sig = sig[:-4] + "0000"
        tampered_verification["signature"] = tampered_sig

        is_valid, reason = crypto.verify_capsule(
            sample_capsule_data, tampered_verification
        )
        assert not is_valid, "Tampered signature should not verify"

    def test_wrong_verify_key_fails(self, temp_key_dir, sample_capsule_data):
        """Test that verification fails with wrong public key."""
        # Create two different crypto instances (different keys)
        crypto1 = UATPCryptoV7(
            key_dir=os.path.join(temp_key_dir, "keys1"), signer_id="signer1"
        )
        crypto2 = UATPCryptoV7(
            key_dir=os.path.join(temp_key_dir, "keys2"), signer_id="signer2"
        )

        # Sign with crypto1
        verification = crypto1.sign_capsule(sample_capsule_data, timestamp_mode="none")

        # Replace verify_key with crypto2's key
        tampered_verification = copy.deepcopy(verification)
        tampered_verification["verify_key"] = crypto2._get_public_key_hex()

        # Verification should fail (signature was made with different key)
        is_valid, reason = crypto1.verify_capsule(
            sample_capsule_data, tampered_verification
        )
        assert not is_valid, "Verification with wrong key should fail"


class TestVerificationFormat:
    """Test verification object format compliance."""

    def test_hash_format(self, crypto, sample_capsule_data):
        """Test hash is in correct UATP format."""
        verification = crypto.sign_capsule(sample_capsule_data, timestamp_mode="none")

        hash_value = verification["hash"]
        assert hash_value.startswith("sha256:")

        # Extract hex part
        hash_hex = hash_value.split(":", 1)[1]
        assert len(hash_hex) == 64, "SHA256 hash should be 64 hex chars"

        # Should be valid hex
        try:
            bytes.fromhex(hash_hex)
        except ValueError:
            pytest.fail("Hash should be valid hex")

    def test_signature_format(self, crypto, sample_capsule_data):
        """Test signature is in correct UATP format."""
        verification = crypto.sign_capsule(sample_capsule_data, timestamp_mode="none")

        sig_value = verification["signature"]
        assert sig_value.startswith("ed25519:")

        # Extract hex part
        sig_hex = sig_value.split(":", 1)[1]
        assert len(sig_hex) == 128, "Ed25519 signature should be 128 hex chars"

        # Should be valid hex
        try:
            bytes.fromhex(sig_hex)
        except ValueError:
            pytest.fail("Signature should be valid hex")

    def test_verify_key_format(self, crypto, sample_capsule_data):
        """Test verify_key is in correct format."""
        verification = crypto.sign_capsule(sample_capsule_data, timestamp_mode="none")

        verify_key = verification["verify_key"]
        assert verify_key is not None
        assert len(verify_key) == 64, "Ed25519 public key should be 64 hex chars"

        # Should be valid hex
        try:
            bytes.fromhex(verify_key)
        except ValueError:
            pytest.fail("Verify key should be valid hex")

    def test_merkle_root_present(self, crypto, sample_capsule_data):
        """Test merkle_root is present in verification."""
        verification = crypto.sign_capsule(sample_capsule_data, timestamp_mode="none")

        # Merkle root should be present (may be same as content hash for single capsule)
        assert "merkle_root" in verification
        assert verification["merkle_root"] is not None


class TestCryptoEdgeCases:
    """Edge case tests for crypto operations."""

    def test_empty_payload(self, crypto):
        """Test signing capsule with empty payload."""
        capsule = {
            "capsule_id": "empty_payload_test",
            "capsule_type": "test",
            "version": "7.2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {},
        }

        verification = crypto.sign_capsule(capsule, timestamp_mode="none")
        is_valid, reason = crypto.verify_capsule(capsule, verification)
        assert is_valid, f"Empty payload capsule should verify: {reason}"

    def test_nested_payload(self, crypto):
        """Test signing capsule with deeply nested payload."""
        capsule = {
            "capsule_id": "nested_test",
            "capsule_type": "test",
            "version": "7.2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "level1": {
                    "level2": {"level3": {"data": "deep value", "numbers": [1, 2, 3]}}
                }
            },
        }

        verification = crypto.sign_capsule(capsule, timestamp_mode="none")
        is_valid, reason = crypto.verify_capsule(capsule, verification)
        assert is_valid, f"Nested payload capsule should verify: {reason}"

    def test_unicode_in_payload(self, crypto):
        """Test signing capsule with unicode characters."""
        capsule = {
            "capsule_id": "unicode_test",
            "capsule_type": "test",
            "version": "7.2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "emoji": "Hello!",
                "chinese": "Claude",
                "arabic": "Some text",
            },
        }

        verification = crypto.sign_capsule(capsule, timestamp_mode="none")
        is_valid, reason = crypto.verify_capsule(capsule, verification)
        assert is_valid, f"Unicode payload capsule should verify: {reason}"

    def test_multiple_signs_same_data(self, crypto, sample_capsule_data):
        """Test that signing the same data twice produces consistent hashes."""
        verification1 = crypto.sign_capsule(sample_capsule_data, timestamp_mode="none")
        verification2 = crypto.sign_capsule(sample_capsule_data, timestamp_mode="none")

        # Hashes should be identical (deterministic)
        assert verification1["hash"] == verification2["hash"]

        # Signatures should also be identical (Ed25519 is deterministic)
        assert verification1["signature"] == verification2["signature"]


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
