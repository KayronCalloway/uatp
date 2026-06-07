from __future__ import annotations

import hashlib
import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path

from nacl.encoding import HexEncoder
from nacl.signing import SigningKey

from src.crypto import local_signer
from src.crypto.local_signer import verify_capsule_standalone
from src.security.rfc3161_timestamps import TimestampToken


def _load_sdk_local_signer():
    sdk_root = Path(__file__).resolve().parents[2] / "sdk" / "python"
    sys.path.insert(0, str(sdk_root))
    try:
        for module_name in list(sys.modules):
            if module_name == "uatp" or module_name.startswith("uatp."):
                sys.modules.pop(module_name)
        return importlib.import_module("uatp.crypto.local_signer")
    finally:
        sys.path.remove(str(sdk_root))


def _signed_capsule_with_timestamp() -> tuple[dict, bytes, str]:
    content = {"claim": "standalone TSA parity", "value": 7}
    canonical = local_signer.json.dumps(
        content,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    content_hash = hashlib.sha256(canonical).hexdigest()
    signing_key = SigningKey.generate()
    signature = signing_key.sign(content_hash.encode("utf-8")).signature.hex()
    public_key = signing_key.verify_key.encode(encoder=HexEncoder).decode("ascii")
    token = TimestampToken(
        token_bytes=b"standalone-rfc3161-response",
        timestamp=datetime(2026, 6, 7, 16, 0, tzinfo=timezone.utc),
        tsa_name="test-tsa",
        hash_algorithm="sha256",
        message_imprint=hashlib.sha256(content_hash.encode("utf-8")).hexdigest(),
    )
    capsule = {
        "capsule_id": "caps_2026_06_07_deadbeef",
        "content": content,
        "verification": {
            "hash": content_hash,
            "signature": f"ed25519:{signature}",
            "verify_key": public_key,
            "signer": "user",
            "rfc3161": token.to_dict(),
        },
    }
    return capsule, b"trusted-tsa-anchor", content_hash


def test_standalone_capsule_verifies_rfc3161_timestamp_with_trusted_tsa_anchor(
    monkeypatch,
) -> None:
    capsule, anchor, content_hash = _signed_capsule_with_timestamp()
    captured = {}

    def fake_verify_timestamp(
        self, token, original_data, trusted_tsa_certificates=None
    ):
        captured["token"] = token
        captured["original_data"] = original_data
        captured["trusted_tsa_certificates"] = trusted_tsa_certificates
        return True, "RFC 3161 timestamp verified against TSA trust anchor"

    monkeypatch.setattr(
        local_signer.RFC3161Timestamper,
        "verify_timestamp",
        fake_verify_timestamp,
    )

    result = verify_capsule_standalone(
        capsule,
        trusted_tsa_certificates=(anchor,),
    )

    assert result["signature_valid"] is True
    assert result["content_hash_match"] is True
    assert result["timestamp_present"] is True
    assert result["timestamp_verified"] is True
    assert result["timestamp_status"] == "cryptographically_verified"
    assert result["assurance_level"] == "full"
    assert result["timestamp_verification_reason"] == (
        "RFC 3161 timestamp verified against TSA trust anchor"
    )
    assert captured["original_data"] == content_hash.encode("utf-8")
    assert captured["trusted_tsa_certificates"] == (anchor,)


def test_standalone_capsule_keeps_timestamp_unverified_without_tsa_anchor(
    monkeypatch,
) -> None:
    capsule, _anchor, _content_hash = _signed_capsule_with_timestamp()

    def fail_if_called(*args, **kwargs):
        raise AssertionError("timestamp verifier must not run without explicit anchors")

    monkeypatch.setattr(
        local_signer.RFC3161Timestamper,
        "verify_timestamp",
        fail_if_called,
    )

    result = verify_capsule_standalone(capsule)

    assert result["signature_valid"] is True
    assert result["content_hash_match"] is True
    assert result["timestamp_present"] is True
    assert result["timestamp_verified"] is False
    assert result["timestamp_status"] == "present_unverified"
    assert result["assurance_level"] == "signature_and_hash"


def test_standalone_capsule_sanitizes_tsa_verification_failure(
    monkeypatch,
) -> None:
    capsule, anchor, _content_hash = _signed_capsule_with_timestamp()

    def fake_verify_timestamp(
        self, token, original_data, trusted_tsa_certificates=None
    ):
        return False, "OpenSSL RFC 3161 verification failed: verification rejected"

    monkeypatch.setattr(
        local_signer.RFC3161Timestamper,
        "verify_timestamp",
        fake_verify_timestamp,
    )

    result = verify_capsule_standalone(
        capsule,
        trusted_tsa_certificates=(anchor,),
    )

    assert result["timestamp_verified"] is False
    assert result["timestamp_status"] == "present_unverified"
    assert result["assurance_level"] == "signature_and_hash"
    warnings = "\n".join(result["warnings"])
    assert "verification rejected" in warnings
    assert "trusted-tsa-anchor" not in warnings


def test_sdk_standalone_capsule_verifies_rfc3161_timestamp_with_tsa_anchor(
    monkeypatch,
) -> None:
    sdk_local_signer = _load_sdk_local_signer()
    capsule, anchor, content_hash = _signed_capsule_with_timestamp()
    captured = {}

    def fake_verify_with_openssl(rfc3161, original_data, trusted_tsa_certificates):
        captured["rfc3161"] = rfc3161
        captured["original_data"] = original_data
        captured["trusted_tsa_certificates"] = trusted_tsa_certificates
        return True, "RFC 3161 timestamp verified against TSA trust anchor"

    monkeypatch.setattr(
        sdk_local_signer,
        "_verify_rfc3161_timestamp_with_openssl",
        fake_verify_with_openssl,
    )

    result = sdk_local_signer.verify_capsule_standalone(
        capsule,
        trusted_tsa_certificates=(anchor,),
    )

    assert result["timestamp_verified"] is True
    assert result["timestamp_status"] == "cryptographically_verified"
    assert result["assurance_level"] == "full"
    assert captured["original_data"] == content_hash.encode("utf-8")
    assert captured["trusted_tsa_certificates"] == (anchor,)


def test_sdk_standalone_capsule_keeps_timestamp_unverified_without_tsa_anchor(
    monkeypatch,
) -> None:
    sdk_local_signer = _load_sdk_local_signer()
    capsule, _anchor, _content_hash = _signed_capsule_with_timestamp()

    def fail_if_called(*args, **kwargs):
        raise AssertionError("timestamp verifier must not run without explicit anchors")

    monkeypatch.setattr(
        sdk_local_signer,
        "_verify_rfc3161_timestamp_with_openssl",
        fail_if_called,
    )

    result = sdk_local_signer.verify_capsule_standalone(capsule)

    assert result["timestamp_verified"] is False
    assert result["timestamp_status"] == "present_unverified"
    assert result["assurance_level"] == "signature_and_hash"
