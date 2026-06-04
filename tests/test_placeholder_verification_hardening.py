"""Fail-closed tests for placeholder verification artifacts."""

from __future__ import annotations

from datetime import datetime, timezone

import src.security.merkle_tree as merkle_tree
from src.security.uatp_crypto_v7 import UATPCryptoV7

_PLACEHOLDER_SIGNATURE = "ed25519:" + "0" * 128
_PLACEHOLDER_ROOT = "sha256:" + "0" * 64


def _capsule_data() -> dict:
    return {
        "capsule_id": "caps_2026_05_21_0123456789abcdef",
        "capsule_type": "TOOL_CALL",
        "timestamp": datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc).isoformat(),
        "status": "sealed",
        "version": "7.4",
        "payload": {"tool_name": "pytest", "result": "passed"},
    }


def test_verify_capsule_rejects_placeholder_merkle_root_even_with_valid_signature(
    tmp_path,
) -> None:
    crypto = UATPCryptoV7(key_dir=str(tmp_path / "keys"), enable_pq=False)
    capsule = _capsule_data()
    verification = crypto.sign_capsule(capsule, timestamp_mode="none")
    verification["merkle_root"] = _PLACEHOLDER_ROOT

    valid, reason = crypto.verify_capsule(capsule, verification)

    assert valid is False
    assert "placeholder merkle_root" in reason


def test_verify_capsule_rejects_wrong_merkle_root_even_with_valid_signature(
    tmp_path,
) -> None:
    crypto = UATPCryptoV7(key_dir=str(tmp_path / "keys"), enable_pq=False)
    capsule = _capsule_data()
    verification = crypto.sign_capsule(capsule, timestamp_mode="none")
    verification["merkle_root"] = "sha256:" + "f" * 64

    valid, reason = crypto.verify_capsule(capsule, verification)

    assert valid is False
    assert "Merkle root mismatch" in reason


def test_verify_capsule_allows_offline_verification_after_merkle_manager_reset(
    tmp_path,
) -> None:
    crypto = UATPCryptoV7(key_dir=str(tmp_path / "keys"), enable_pq=False)
    capsule = _capsule_data()
    verification = crypto.sign_capsule(capsule, timestamp_mode="none")
    merkle_tree._chain_manager = None

    valid, reason = crypto.verify_capsule(capsule, verification)

    assert valid is True, reason


def test_verify_capsule_allows_historical_verification_after_chain_advances(
    tmp_path,
) -> None:
    crypto = UATPCryptoV7(key_dir=str(tmp_path / "keys"), enable_pq=False)
    capsule = _capsule_data()
    verification = crypto.sign_capsule(capsule, timestamp_mode="none")
    later_capsule = {
        **_capsule_data(),
        "capsule_id": "caps_2026_05_21_fedcba9876543210",
    }
    crypto.sign_capsule(later_capsule, timestamp_mode="none")

    valid, reason = crypto.verify_capsule(capsule, verification)

    assert valid is True, reason


def test_verify_capsule_rejects_placeholder_signature_for_sealed_status(
    tmp_path,
) -> None:
    crypto = UATPCryptoV7(key_dir=str(tmp_path / "keys"), enable_pq=False)
    capsule = _capsule_data()
    verification = crypto.sign_capsule(capsule, timestamp_mode="none")
    verification["signature"] = _PLACEHOLDER_SIGNATURE

    valid, reason = crypto.verify_capsule(capsule, verification)

    assert valid is False
    assert "placeholder signature" in reason


def test_verify_capsule_rejects_placeholder_hash_for_verified_status(tmp_path) -> None:
    crypto = UATPCryptoV7(key_dir=str(tmp_path / "keys"), enable_pq=False)
    capsule = {**_capsule_data(), "status": "verified"}
    verification = crypto.sign_capsule(capsule, timestamp_mode="none")
    verification["hash"] = None

    valid, reason = crypto.verify_capsule(capsule, verification)

    assert valid is False
    assert "verified capsules require real verification artifacts" in reason


def test_verify_capsule_rejects_untrusted_self_signed_key_when_policy_supplied(
    tmp_path,
) -> None:
    trusted = UATPCryptoV7(
        key_dir=str(tmp_path / "trusted_keys"), signer_id="gateway", enable_pq=False
    )
    attacker = UATPCryptoV7(
        key_dir=str(tmp_path / "attacker_keys"), signer_id="gateway", enable_pq=False
    )
    capsule = _capsule_data()
    verification = attacker.sign_capsule(capsule, timestamp_mode="none")
    trust_policy = {"gateway": trusted._get_public_key_hex()}

    valid, reason = trusted.verify_capsule(
        capsule, verification, trusted_public_keys_by_signer=trust_policy
    )

    assert valid is False
    assert "public key is not trusted" in reason


def test_verify_capsule_accepts_trusted_signer_policy(tmp_path) -> None:
    trusted = UATPCryptoV7(
        key_dir=str(tmp_path / "trusted_keys"), signer_id="gateway", enable_pq=False
    )
    capsule = _capsule_data()
    verification = trusted.sign_capsule(capsule, timestamp_mode="none")
    trust_policy = {"gateway": trusted._get_public_key_hex()}

    valid, reason = trusted.verify_capsule(
        capsule, verification, trusted_public_keys_by_signer=trust_policy
    )

    assert valid is True, reason
