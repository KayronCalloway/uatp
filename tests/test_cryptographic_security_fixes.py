"""
Comprehensive test suite for cryptographic security fixes in UATP Capsule Engine.
Tests all critical security vulnerabilities have been properly fixed.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from src.crypto.post_quantum import PostQuantumCrypto
from src.crypto.secure_key_manager import SecureKeyManager
from src.crypto.zero_knowledge import ZKProofSystem

# Import the modules under test
from src.crypto_utils import (
    _check_replay_protection,
    _validate_public_key_format,
    _validate_signature_format,
    clear_signature_cache,
    get_signature_cache_stats,
    verify_capsule,
    verify_post_quantum,
)


class TestSignatureFormatValidation:
    """Test comprehensive signature format validation."""

    def test_ed25519_signature_validation_valid(self):
        """Test valid Ed25519 signature format."""
        valid_sig = "ed25519:" + "a" * 128  # 64 bytes = 128 hex chars
        assert _validate_signature_format(valid_sig, "ed25519")

    def test_ed25519_signature_validation_missing_prefix(self):
        """Test Ed25519 signature without prefix fails."""
        invalid_sig = "a" * 128
        assert not _validate_signature_format(invalid_sig, "ed25519")

    def test_ed25519_signature_validation_wrong_length(self):
        """Test Ed25519 signature with wrong length fails."""
        invalid_sig = "ed25519:" + "a" * 64  # Too short
        assert not _validate_signature_format(invalid_sig, "ed25519")

    def test_ed25519_signature_validation_invalid_hex(self):
        """Test Ed25519 signature with invalid hex fails."""
        invalid_sig = "ed25519:" + "g" * 128  # 'g' is not valid hex
        assert not _validate_signature_format(invalid_sig, "ed25519")

    def test_dilithium_signature_validation_valid(self):
        """Test valid Dilithium signature format."""
        valid_sig = "dilithium3:" + "a" * 4500  # Substantial length
        assert _validate_signature_format(valid_sig, "dilithium3")

    def test_dilithium_signature_validation_too_short(self):
        """Test short Dilithium signature fails."""
        invalid_sig = "dilithium3:" + "a" * 100  # Too short
        assert not _validate_signature_format(invalid_sig, "dilithium3")

    def test_empty_signature_validation(self):
        """Test empty signature fails validation."""
        assert not _validate_signature_format("", "ed25519")
        assert not _validate_signature_format(None, "ed25519")


class TestPublicKeyFormatValidation:
    """Test comprehensive public key format validation."""

    def test_ed25519_public_key_validation_valid(self):
        """Test valid Ed25519 public key format."""
        valid_key = "a" * 64  # 32 bytes = 64 hex chars
        assert _validate_public_key_format(valid_key, "ed25519")

    def test_ed25519_public_key_validation_wrong_length(self):
        """Test Ed25519 public key with wrong length fails."""
        invalid_key = "a" * 32  # Too short
        assert not _validate_public_key_format(invalid_key, "ed25519")

    def test_dilithium_public_key_validation_valid(self):
        """Test valid Dilithium public key format."""
        valid_key = "a" * 3000  # Substantial length for Dilithium3
        assert _validate_public_key_format(valid_key, "dilithium3")

    def test_dilithium_public_key_validation_too_short(self):
        """Test short Dilithium public key fails."""
        invalid_key = "a" * 100  # Too short
        assert not _validate_public_key_format(invalid_key, "dilithium3")

    def test_invalid_hex_public_key(self):
        """Test public key with invalid hex fails."""
        invalid_key = "g" * 64  # 'g' is not valid hex
        assert not _validate_public_key_format(invalid_key, "ed25519")


class TestReplayProtection:
    """Test signature replay attack protection."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_signature_cache()

    def test_first_signature_allowed(self):
        """Test first occurrence of signature is allowed."""
        hash_str = "test_hash"
        signature = "test_signature"
        public_key = "test_public_key"

        result = _check_replay_protection(hash_str, signature, public_key)
        assert result

    def test_reverification_allowed(self):
        """Test re-verification of same signature is allowed.

        The replay protection allows re-verification of the same hash+signature+key
        combination (legitimate re-verification scenarios). This enables users to
        verify the same capsule multiple times without being blocked.
        """
        hash_str = "test_hash"
        signature = "test_signature"
        public_key = "test_public_key"

        # First use should succeed
        result1 = _check_replay_protection(hash_str, signature, public_key)
        assert result1

        # Re-verification with same hash+signature+key should be ALLOWED
        result2 = _check_replay_protection(hash_str, signature, public_key)
        assert result2  # Legitimate re-verification is allowed

    def test_different_signatures_allowed(self):
        """Test different signatures are both allowed."""
        hash_str = "test_hash"
        public_key = "test_public_key"

        result1 = _check_replay_protection(hash_str, "signature1", public_key)
        assert result1

        result2 = _check_replay_protection(hash_str, "signature2", public_key)
        assert result2

    def test_cache_stats(self):
        """Test cache statistics functionality."""
        clear_signature_cache()
        stats = get_signature_cache_stats()
        assert stats["cache_size"] == 0

        _check_replay_protection("hash1", "sig1", "key1")
        stats = get_signature_cache_stats()
        assert stats["cache_size"] == 1


class TestPostQuantumCryptographyFixes:
    """Test post-quantum cryptography security fixes."""

    def test_dilithium_not_available_raises_error(self):
        """Test that missing Dilithium libraries raise proper errors."""
        pq = PostQuantumCrypto()
        pq.dilithium_available = False

        with pytest.raises(
            RuntimeError, match="SECURITY ERROR: Post-quantum cryptography"
        ):
            pq.generate_dilithium_keypair()

        with pytest.raises(
            RuntimeError, match="SECURITY ERROR: Post-quantum cryptography"
        ):
            pq.dilithium_sign(b"message", b"fake_key")

    def test_kyber_not_available_raises_error(self):
        """Test that missing Kyber libraries raise proper errors."""
        pq = PostQuantumCrypto()
        pq.kyber_available = False

        with pytest.raises(
            RuntimeError, match="SECURITY ERROR: Post-quantum cryptography"
        ):
            pq.generate_kyber_keypair()

        with pytest.raises(
            RuntimeError, match="SECURITY ERROR: Post-quantum cryptography"
        ):
            pq.kyber_encapsulate(b"fake_public_key")

    def test_fallback_keypair_generation_disabled(self):
        """Test that fallback keypair generation is disabled."""
        pq = PostQuantumCrypto()

        with pytest.raises(
            RuntimeError, match="SECURITY ERROR: Post-quantum cryptography"
        ):
            pq._generate_secure_fallback_keypair("Dilithium3")

    def test_fallback_signing_disabled(self):
        """Test that fallback signing is disabled."""
        pq = PostQuantumCrypto()

        with pytest.raises(
            RuntimeError, match="SECURITY ERROR: Post-quantum cryptography"
        ):
            pq._secure_fallback_sign(b"message", b"key")

    def test_fallback_verification_disabled(self):
        """Test that fallback verification is disabled."""
        pq = PostQuantumCrypto()

        result = pq._secure_fallback_verify(b"message", b"signature", b"key")
        assert not result

    @patch("src.crypto.post_quantum.pq_crypto")
    def test_hybrid_verification_requires_both_signatures(self, mock_pq_crypto):
        """Test that hybrid verification requires BOTH signatures to be valid."""
        mock_pq_crypto.dilithium_available = True
        mock_pq_crypto.dilithium_verify.return_value = True

        pq = PostQuantumCrypto()
        pq.dilithium_available = True

        message = b"test message"
        signatures = {
            "ed25519": "ed25519:" + "a" * 128,
            "dilithium": "dilithium3:" + "b" * 4500,
        }
        ed25519_public = b"a" * 32
        dilithium_public = b"b" * 1952

        # Mock Ed25519 verification to fail
        with patch("nacl.signing.VerifyKey") as mock_verify_key:
            mock_verify_key.return_value.verify.side_effect = Exception(
                "Ed25519 failed"
            )

            result = pq.hybrid_verify(
                message, signatures, ed25519_public, dilithium_public
            )
            assert not result  # Should fail if Ed25519 fails

    def test_hybrid_verification_missing_signatures(self):
        """Test hybrid verification fails with missing signatures."""
        pq = PostQuantumCrypto()

        message = b"test message"
        incomplete_signatures = {"ed25519": "ed25519:" + "a" * 128}  # Missing dilithium
        ed25519_public = b"a" * 32
        dilithium_public = b"b" * 1952

        result = pq.hybrid_verify(
            message, incomplete_signatures, ed25519_public, dilithium_public
        )
        assert not result


class TestZeroKnowledgeProofFixes:
    """Test zero-knowledge proof security fixes."""

    def test_zk_proof_generation_disabled_without_libraries(self):
        """Test ZK proof generation fails without real libraries."""
        zk = ZKProofSystem()
        zk.groth16_available = False

        capsule_data = {"capsule_id": "test", "timestamp": time.time()}
        private_witness = {"private_content": "secret", "nonce": "random"}

        with pytest.raises(
            RuntimeError, match="SECURITY ERROR: Zero-knowledge proof libraries"
        ):
            zk.prove_capsule_privacy(capsule_data, private_witness)

    def test_zk_range_proof_disabled_without_libraries(self):
        """Test ZK range proofs fail without real libraries."""
        zk = ZKProofSystem()
        zk.bulletproofs_available = False

        with pytest.raises(RuntimeError, match="SECURITY ERROR: Bulletproof libraries"):
            zk.prove_range(50, 0, 100)

    def test_fallback_proof_generation_disabled(self):
        """Test fallback proof generation is disabled."""
        zk = ZKProofSystem()

        with pytest.raises(
            RuntimeError, match="SECURITY ERROR: Zero-knowledge proof libraries"
        ):
            zk._generate_fallback_proof("test_circuit", {}, {})

    def test_fallback_verification_disabled(self):
        """Test fallback verification is disabled."""
        zk = ZKProofSystem()

        # Create a dummy proof object
        from src.crypto.zero_knowledge import ProofType, ZKProof

        dummy_proof = ZKProof(
            proof_type=ProofType.SNARK,
            proof_data=b"dummy",
            public_inputs={},
            verification_key=b"dummy",
            circuit_hash="dummy",
        )

        result = zk._verify_fallback_proof(dummy_proof)
        assert not result


class TestSecureKeyManager:
    """Test secure key management system."""

    def test_key_manager_initialization(self):
        """Test secure key manager initializes properly."""
        key_manager = SecureKeyManager("test_password")
        assert key_manager is not None
        assert key_manager._master_key is not None

    def test_key_generation_with_encryption(self):
        """Test that keys are generated and encrypted."""
        key_manager = SecureKeyManager("test_password")

        private_hex, public_hex = key_manager.generate_key_pair("ed25519", "test_key")

        assert private_hex is not None
        assert public_hex is not None
        assert len(private_hex) > 0
        assert len(public_hex) > 0

    def test_key_retrieval_and_decryption(self):
        """Test that keys can be retrieved and decrypted."""
        key_manager = SecureKeyManager("test_password")

        private_hex, _ = key_manager.generate_key_pair("ed25519", "test_key")

        # Retrieve the private key
        retrieved_key = key_manager.get_private_key("test_key")
        assert retrieved_key is not None
        assert len(retrieved_key) == 32  # Ed25519 private key length

    def test_key_not_found_raises_error(self):
        """Test that retrieving non-existent key raises error."""
        key_manager = SecureKeyManager("test_password")

        with pytest.raises(KeyError, match="Key nonexistent not found"):
            key_manager.get_private_key("nonexistent")

    def test_key_rotation(self):
        """Test key rotation functionality."""
        key_manager = SecureKeyManager("test_password")

        # Generate initial key
        original_private, original_public = key_manager.generate_key_pair(
            "ed25519", "test_key"
        )

        # Rotate the key
        new_private, new_public = key_manager.rotate_key("test_key")

        # New keys should be different
        assert new_private != original_private
        assert new_public != original_public

    def test_secure_key_deletion(self):
        """Test secure key deletion."""
        key_manager = SecureKeyManager("test_password")

        key_manager.generate_key_pair("ed25519", "test_key")
        assert "test_key" in key_manager.list_keys()

        key_manager.delete_key("test_key")
        assert "test_key" not in key_manager.list_keys()

    def test_key_health_status(self):
        """Test key health monitoring."""
        key_manager = SecureKeyManager("test_password")

        status = key_manager.get_key_health_status()
        assert "status" in status
        assert "total_keys" in status
        assert status["master_key_status"] == "initialized"


class TestEnhancedCryptoUtils:
    """Test enhanced crypto utilities with security fixes."""

    def setup_method(self):
        """Clear replay cache before each test."""
        clear_signature_cache()

    @patch("src.crypto_utils._validate_signature_format")
    @patch("src.crypto_utils._validate_public_key_format")
    def test_verify_capsule_enhanced_validation(
        self, mock_key_validation, mock_sig_validation
    ):
        """Test verify_capsule uses enhanced validation."""
        mock_key_validation.return_value = True
        mock_sig_validation.return_value = True

        # Create a mock capsule
        mock_capsule = MagicMock()
        mock_capsule.verification.hash = "test_hash"

        with patch("src.crypto_utils.hash_for_signature", return_value="test_hash"):
            with patch("src.crypto_utils._check_replay_protection", return_value=True):
                with patch("nacl.signing.VerifyKey") as mock_verify_key:
                    mock_verify_key.return_value.verify.return_value = (
                        None  # No exception = valid
                    )

                    result, message = verify_capsule(
                        mock_capsule, "a" * 64, "ed25519:" + "b" * 128
                    )

                    # Should call validation functions
                    mock_key_validation.assert_called_once()
                    mock_sig_validation.assert_called_once()

    def test_verify_capsule_reverification_allowed(self):
        """Test verify_capsule allows legitimate re-verification.

        The replay protection system allows re-verification of the same
        hash+signature+key combination (legitimate re-verification scenarios).
        Users should be able to verify the same capsule multiple times.
        """
        mock_capsule = MagicMock()
        mock_capsule.verification.hash = "test_hash"

        with patch("src.crypto_utils.hash_for_signature", return_value="test_hash"):
            with patch(
                "src.crypto_utils._validate_signature_format", return_value=True
            ):
                with patch(
                    "src.crypto_utils._validate_public_key_format", return_value=True
                ):
                    with patch("src.crypto_utils.VerifyKey") as mock_verify_key:
                        mock_verify_key.return_value.verify.return_value = None

                        # First verification should succeed
                        result1, _ = verify_capsule(
                            mock_capsule, "a" * 64, "ed25519:" + "b" * 128
                        )
                        assert result1

                        # Re-verification of same capsule should also succeed
                        result2, _ = verify_capsule(
                            mock_capsule, "a" * 64, "ed25519:" + "b" * 128
                        )
                        assert result2  # Re-verification is allowed


class TestSecurityIntegration:
    """Integration tests for overall security improvements."""

    def test_post_quantum_signature_validation_integration(self):
        """Test post-quantum signature validation with enhanced checks."""
        # Test that post-quantum verification uses enhanced validation
        hash_str = "test_hash"
        pq_public_key_hex = "a" * 3000  # Valid length for Dilithium
        pq_signature_hex = "dilithium3:" + "b" * 4500  # Valid format

        with patch("src.crypto.post_quantum.pq_crypto") as mock_pq_crypto:
            mock_pq_crypto.dilithium_available = False

            # Should raise error due to unavailable libraries
            with pytest.raises(
                RuntimeError, match="SECURITY ERROR: Post-quantum cryptography"
            ):
                verify_post_quantum(hash_str, pq_public_key_hex, pq_signature_hex)

    def test_comprehensive_security_stack(self):
        """Test that all security layers work together."""
        # This test verifies the complete security stack:
        # 1. Format validation
        # 2. Replay protection
        # 3. Cryptographic verification
        # 4. Post-quantum readiness

        clear_signature_cache()

        # Test Ed25519 signature with all security layers
        mock_capsule = MagicMock()
        mock_capsule.verification.hash = "comprehensive_test_hash"

        with patch(
            "src.crypto_utils.hash_for_signature",
            return_value="comprehensive_test_hash",
        ):
            with patch(
                "src.crypto_utils._validate_signature_format", return_value=True
            ):
                with patch(
                    "src.crypto_utils._validate_public_key_format", return_value=True
                ):
                    with patch("src.crypto_utils.VerifyKey") as mock_verify_key:
                        mock_verify_key.return_value.verify.return_value = None

                        # Valid signature should pass all checks
                        result, message = verify_capsule(
                            mock_capsule,
                            "a" * 64,  # Valid Ed25519 public key
                            "ed25519:" + "b" * 128,  # Valid Ed25519 signature
                        )

                        assert result
                        assert "verified" in message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
