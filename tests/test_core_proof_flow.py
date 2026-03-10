"""
UATP Core Proof Flow Tests
===========================

These tests validate the fundamental cryptographic guarantees:
1. Ed25519 signature generation and verification
2. Tamper detection (any change invalidates signature)
3. RFC3161 external timestamping

If these tests pass, the core claim is valid.
If these tests fail, everything else is theater.
"""

import json
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

from src.security.uatp_crypto_v7 import UATPCryptoV7


@pytest.fixture
def crypto_instance(tmp_path: Path) -> UATPCryptoV7:
    """Create a crypto instance with temporary key directory."""
    return UATPCryptoV7(key_dir=str(tmp_path / ".uatp_keys_test"))


@pytest.fixture
def sample_capsule() -> Dict[str, Any]:
    """Sample capsule content for testing."""
    return {
        "capsule_id": "test_capsule_001",
        "type": "reasoning_trace",
        "platform": "test",
        "user_id": "test_user",
        "timestamp": "2026-03-08T12:00:00Z",
        "significance_score": 8.5,
        "payload": {
            "task": "Approve loan application",
            "decision": "Loan approved for $50,000 at 5.2% APR",
            "reasoning": [
                {
                    "step": 1,
                    "thought": "Credit score 720 (excellent)",
                    "confidence": 0.99,
                },
                {
                    "step": 2,
                    "thought": "Debt-to-income ratio 0.28 (acceptable)",
                    "confidence": 0.95,
                },
            ],
        },
    }


class TestEdDSASignatures:
    """Test Ed25519 signature generation and verification."""

    def test_signature_generation(
        self, crypto_instance: UATPCryptoV7, sample_capsule: Dict[str, Any]
    ) -> None:
        """Test that we can generate a signature for capsule content."""
        verification = crypto_instance.sign_capsule(sample_capsule)

        assert "signature" in verification
        assert "hash" in verification
        assert "verify_key" in verification
        assert "signer" in verification
        assert len(verification["signature"]) > 0
        assert len(verification["hash"]) > 0

    def test_signature_verification_valid(
        self, crypto_instance: UATPCryptoV7, sample_capsule: Dict[str, Any]
    ) -> None:
        """Test that a valid signature verifies correctly."""
        verification = crypto_instance.sign_capsule(sample_capsule)

        is_valid, reason = crypto_instance.verify_capsule(sample_capsule, verification)

        assert is_valid is True
        assert "valid" in reason.lower() or "passed" in reason.lower()

    def test_tamper_detection_major_change(
        self, crypto_instance: UATPCryptoV7, sample_capsule: Dict[str, Any]
    ) -> None:
        """Test that major content changes are detected."""
        verification = crypto_instance.sign_capsule(sample_capsule)

        # Tamper with the decision
        tampered = sample_capsule.copy()
        tampered["payload"] = sample_capsule["payload"].copy()
        tampered["payload"]["decision"] = "Loan approved for $500,000 at 0.1% APR"

        is_valid, reason = crypto_instance.verify_capsule(tampered, verification)

        assert is_valid is False, "Tampered content should fail verification"

    def test_tamper_detection_subtle_change(
        self, crypto_instance: UATPCryptoV7, sample_capsule: Dict[str, Any]
    ) -> None:
        """Test that even subtle changes (single digit) are detected."""
        verification = crypto_instance.sign_capsule(sample_capsule)

        # Subtle tamper - change 8.5 to 8.4
        tampered = sample_capsule.copy()
        tampered["significance_score"] = 8.4

        is_valid, reason = crypto_instance.verify_capsule(tampered, verification)

        assert is_valid is False, "Subtle tamper should be detected"

    def test_tamper_detection_added_field(
        self, crypto_instance: UATPCryptoV7, sample_capsule: Dict[str, Any]
    ) -> None:
        """Test that adding a field is detected."""
        verification = crypto_instance.sign_capsule(sample_capsule)

        tampered = sample_capsule.copy()
        tampered["malicious_field"] = "injected"

        is_valid, reason = crypto_instance.verify_capsule(tampered, verification)

        assert is_valid is False, "Added field should be detected"

    def test_tamper_detection_removed_field(
        self, crypto_instance: UATPCryptoV7, sample_capsule: Dict[str, Any]
    ) -> None:
        """Test that removing a field is detected."""
        verification = crypto_instance.sign_capsule(sample_capsule)

        tampered = sample_capsule.copy()
        del tampered["significance_score"]

        is_valid, reason = crypto_instance.verify_capsule(tampered, verification)

        assert is_valid is False, "Removed field should be detected"


class TestRFC3161Timestamps:
    """Test RFC3161 external timestamping (requires network)."""

    @pytest.fixture
    def timestamper(self) -> Generator[Any, None, None]:
        """Create RFC3161 timestamper."""
        from src.security.rfc3161_timestamps import RFC3161Timestamper

        yield RFC3161Timestamper(tsa_name="freetsa")

    @pytest.mark.network
    def test_timestamp_request(
        self, timestamper: Any, sample_capsule: Dict[str, Any]
    ) -> None:
        """Test requesting a timestamp from external TSA."""
        capsule_bytes = json.dumps(
            sample_capsule, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

        token = timestamper.request_timestamp(capsule_bytes)

        assert token is not None
        assert token.tsa_name == "freetsa"
        assert token.timestamp is not None
        assert len(token.message_imprint) > 0

    @pytest.mark.network
    def test_timestamp_verification(
        self, timestamper: Any, sample_capsule: Dict[str, Any]
    ) -> None:
        """Test verifying a timestamp."""
        capsule_bytes = json.dumps(
            sample_capsule, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

        token = timestamper.request_timestamp(capsule_bytes)
        is_valid, reason = timestamper.verify_timestamp(token, capsule_bytes)

        assert is_valid is True

    @pytest.mark.network
    def test_timestamp_tamper_detection(
        self, timestamper: Any, sample_capsule: Dict[str, Any]
    ) -> None:
        """Test that tampered data fails timestamp verification."""
        capsule_bytes = json.dumps(
            sample_capsule, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

        token = timestamper.request_timestamp(capsule_bytes)

        # Tamper with content
        tampered = sample_capsule.copy()
        tampered["payload"] = sample_capsule["payload"].copy()
        tampered["payload"]["decision"] = "TAMPERED DECISION"
        tampered_bytes = json.dumps(
            tampered, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

        is_valid, reason = timestamper.verify_timestamp(token, tampered_bytes)

        assert is_valid is False, "Tampered data should fail timestamp verification"


class TestCoreGuarantees:
    """Integration tests for core cryptographic guarantees."""

    def test_full_proof_flow(
        self, crypto_instance: UATPCryptoV7, sample_capsule: Dict[str, Any]
    ) -> None:
        """Test the complete proof flow: create, sign, verify, tamper, fail."""
        # 1. Sign original content
        verification = crypto_instance.sign_capsule(sample_capsule)

        # 2. Verify original passes
        is_valid, _ = crypto_instance.verify_capsule(sample_capsule, verification)
        assert is_valid is True, "Original content should verify"

        # 3. Tamper with content
        tampered = sample_capsule.copy()
        tampered["payload"] = sample_capsule["payload"].copy()
        tampered["payload"]["decision"] = "TAMPERED"

        # 4. Tampered content fails
        is_valid_tampered, _ = crypto_instance.verify_capsule(tampered, verification)
        assert is_valid_tampered is False, "Tampered content should fail"

    def test_different_keys_different_signatures(
        self, tmp_path: Path, sample_capsule: Dict[str, Any]
    ) -> None:
        """Test that different keys produce different signatures."""
        crypto1 = UATPCryptoV7(key_dir=str(tmp_path / "keys1"))
        crypto2 = UATPCryptoV7(key_dir=str(tmp_path / "keys2"))

        sig1 = crypto1.sign_capsule(sample_capsule)
        sig2 = crypto2.sign_capsule(sample_capsule)

        assert (
            sig1["signature"] != sig2["signature"]
        ), "Different keys should produce different signatures"
        assert (
            sig1["verify_key"] != sig2["verify_key"]
        ), "Different keys should have different public keys"

    def test_signature_not_transferable(
        self, tmp_path: Path, sample_capsule: Dict[str, Any]
    ) -> None:
        """Test that a signature from one key doesn't verify with another."""
        crypto1 = UATPCryptoV7(key_dir=str(tmp_path / "keys1"))
        crypto2 = UATPCryptoV7(key_dir=str(tmp_path / "keys2"))

        # Sign with key 1
        verification = crypto1.sign_capsule(sample_capsule)

        # Swap the public key - should fail
        tampered_verification = verification.copy()
        tampered_verification["verify_key"] = crypto2.sign_capsule(sample_capsule)[
            "verify_key"
        ]

        is_valid, _ = crypto1.verify_capsule(sample_capsule, tampered_verification)
        assert is_valid is False, "Swapped public key should fail verification"
