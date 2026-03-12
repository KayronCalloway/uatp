"""
Unit tests for DSSE export.

Tests PAE encoding, DSSE envelopes, and bundle verification.
"""

import base64
import json
from datetime import datetime, timezone

import pytest

from src.export import (
    PAYLOAD_TYPE_CAPSULE,
    DSSEEnvelope,
    DSSESignature,
    TimestampEvidence,
    UATPBundle,
    VerificationMaterial,
    create_capsule_envelope,
    create_workflow_envelope,
    pae_decode,
    pae_encode,
    sign_pae,
    verify_pae,
)


class TestPAE:
    """Tests for Pre-Auth Encoding."""

    def test_pae_encode_basic(self):
        payload_type = "application/json"
        payload = b'{"key": "value"}'

        encoded = pae_encode(payload_type, payload)

        assert encoded.startswith(b"DSSEv1 ")
        assert b"application/json" in encoded
        assert payload in encoded

    def test_pae_roundtrip(self):
        payload_type = "application/vnd.uatp.capsule.v1+json"
        payload = b'{"capsule_id": "caps_123"}'

        encoded = pae_encode(payload_type, payload)
        decoded_type, decoded_payload = pae_decode(encoded)

        assert decoded_type == payload_type
        assert decoded_payload == payload

    def test_pae_invalid_format(self):
        with pytest.raises(ValueError):
            pae_decode(b"invalid format")

    def test_pae_deterministic(self):
        payload_type = "text/plain"
        payload = b"test content"

        enc1 = pae_encode(payload_type, payload)
        enc2 = pae_encode(payload_type, payload)

        assert enc1 == enc2

    def test_pae_empty_payload(self):
        """Test PAE with empty payload."""
        encoded = pae_encode("text/plain", b"")
        decoded_type, decoded_payload = pae_decode(encoded)

        assert decoded_type == "text/plain"
        assert decoded_payload == b""

    def test_pae_unicode_payload_type(self):
        """Test PAE with unicode in payload type."""
        payload_type = "application/json; charset=utf-8"
        payload = b'{"emoji": "test"}'

        encoded = pae_encode(payload_type, payload)
        decoded_type, decoded_payload = pae_decode(encoded)

        assert decoded_type == payload_type
        assert decoded_payload == payload

    def test_pae_large_payload(self):
        """Test PAE with larger payload (10KB)."""
        payload_type = "application/octet-stream"
        payload = b"x" * 10240

        encoded = pae_encode(payload_type, payload)
        decoded_type, decoded_payload = pae_decode(encoded)

        assert decoded_type == payload_type
        assert decoded_payload == payload
        assert len(decoded_payload) == 10240

    def test_pae_binary_payload(self):
        """Test PAE with binary data containing null bytes."""
        payload_type = "application/octet-stream"
        payload = bytes(range(256))  # All byte values 0-255

        encoded = pae_encode(payload_type, payload)
        decoded_type, decoded_payload = pae_decode(encoded)

        assert decoded_type == payload_type
        assert decoded_payload == payload


class TestDSSEEnvelope:
    """Tests for DSSE envelope."""

    def test_create_envelope(self):
        content = b'{"test": "data"}'
        envelope = DSSEEnvelope.create(content, PAYLOAD_TYPE_CAPSULE)

        assert envelope.payload_type == PAYLOAD_TYPE_CAPSULE
        assert envelope.payload_bytes() == content
        assert envelope.is_signed == False

    def test_envelope_payload_json(self):
        data = {"capsule_id": "caps_123", "type": "reasoning_trace"}
        content = json.dumps(data).encode("utf-8")

        envelope = DSSEEnvelope.create(content)
        parsed = envelope.payload_json()

        assert parsed == data

    def test_envelope_sign_mock(self):
        """Test signing with mock function."""
        content = b'{"test": "data"}'
        envelope = DSSEEnvelope.create(content)

        def mock_sign(data: bytes) -> bytes:
            return b"mock_signature_for_" + data[:20]

        envelope.sign(keyid="mock-key-123", sign_func=mock_sign)

        assert envelope.is_signed == True
        assert len(envelope.signatures) == 1
        assert envelope.signatures[0].keyid == "mock-key-123"

    def test_envelope_verify_mock(self):
        """Test verification with mock function."""
        content = b'{"test": "data"}'
        envelope = DSSEEnvelope.create(content)

        # Sign
        expected_pae = envelope.pae_bytes()

        def mock_sign(data: bytes) -> bytes:
            return b"valid_sig"

        envelope.sign(keyid="key-1", sign_func=mock_sign)

        # Verify
        def mock_verify(message: bytes, sig: bytes) -> bool:
            return sig == b"valid_sig"

        assert envelope.verify("key-1", mock_verify) == True
        assert envelope.verify("wrong-key", mock_verify) == False

    def test_envelope_to_dict_from_dict(self):
        content = b'{"id": "test"}'
        original = DSSEEnvelope.create(content)
        original.signatures.append(DSSESignature(keyid="k1", sig="c2ln"))

        d = original.to_dict()
        restored = DSSEEnvelope.from_dict(d)

        assert restored.payload == original.payload
        assert restored.payload_type == original.payload_type
        assert len(restored.signatures) == 1
        assert restored.signatures[0].keyid == "k1"

    def test_envelope_to_json(self):
        content = b'{"test": true}'
        envelope = DSSEEnvelope.create(content)

        json_str = envelope.to_json()
        parsed = json.loads(json_str)

        assert "payload" in parsed
        assert "payloadType" in parsed
        assert "signatures" in parsed

    def test_create_capsule_envelope(self):
        capsule = {
            "capsule_id": "caps_123",
            "type": "reasoning_trace",
            "timestamp": "2026-03-11T10:00:00Z",
        }

        envelope = create_capsule_envelope(capsule)

        assert envelope.payload_type == PAYLOAD_TYPE_CAPSULE
        payload = envelope.payload_json()
        assert payload["capsule_id"] == "caps_123"

    def test_create_workflow_envelope(self):
        workflow = {
            "workflowId": "wf_123",
            "name": "Test Workflow",
            "steps": [],
        }

        envelope = create_workflow_envelope(workflow)

        assert "workflow" in envelope.payload_type.lower()
        payload = envelope.payload_json()
        assert payload["workflowId"] == "wf_123"

    def test_envelope_multiple_signatures(self):
        """Test envelope with multiple signatures."""
        envelope = DSSEEnvelope.create(b'{"test": true}')

        def sign1(data: bytes) -> bytes:
            return b"sig1"

        def sign2(data: bytes) -> bytes:
            return b"sig2"

        envelope.sign(keyid="key1", sign_func=sign1)
        envelope.sign(keyid="key2", sign_func=sign2)

        assert envelope.is_signed == True
        assert len(envelope.signatures) == 2
        assert envelope.signatures[0].keyid == "key1"
        assert envelope.signatures[1].keyid == "key2"

    def test_dsse_signature_bytes(self):
        """Test DSSESignature.signature_bytes()."""
        sig = DSSESignature(keyid="test", sig=base64.b64encode(b"hello").decode())
        assert sig.signature_bytes() == b"hello"


class TestVerificationMaterial:
    """Tests for verification material."""

    def test_basic_material(self):
        material = VerificationMaterial(
            public_key=base64.b64encode(b"test_key").decode(),
            key_algorithm="ed25519",
            key_id="ed25519-abc123",
        )

        assert material.public_key_bytes() == b"test_key"
        assert material.is_hybrid == False

    def test_hybrid_material(self):
        material = VerificationMaterial(
            public_key=base64.b64encode(b"ed25519_key").decode(),
            pq_public_key=base64.b64encode(b"ml-dsa_key").decode(),
            pq_algorithm="ml-dsa-65",
        )

        assert material.is_hybrid == True

    def test_timestamp_evidence(self):
        ts = TimestampEvidence(
            rfc3161_token="base64token",
            authority="https://freetsa.org",
            timestamp=datetime.now(timezone.utc),
        )

        assert ts.has_token == True

        d = ts.to_dict()
        restored = TimestampEvidence.from_dict(d)

        assert restored.rfc3161_token == ts.rfc3161_token
        assert restored.authority == ts.authority

    def test_material_to_dict_from_dict(self):
        original = VerificationMaterial(
            public_key="cHVia2V5",
            key_algorithm="ed25519",
            key_id="key-123",
            timestamp=TimestampEvidence(
                rfc3161_token="token123",
                authority="https://tsa.example.com",
            ),
        )

        d = original.to_dict()
        restored = VerificationMaterial.from_dict(d)

        assert restored.public_key == original.public_key
        assert restored.key_id == original.key_id
        assert restored.timestamp.rfc3161_token == "token123"


class TestUATPBundle:
    """Tests for UATP bundle."""

    def test_create_bundle(self):
        content = b'{"capsule_id": "test"}'
        envelope = DSSEEnvelope.create(content)

        # Add mock signature
        envelope.signatures.append(DSSESignature(keyid="k1", sig="c2ln"))

        bundle = UATPBundle.create(
            envelope=envelope,
            public_key=b"fake_public_key_32bytes_long!!",
            key_id="k1",
            timestamp_token="rfc3161_token_base64",
            timestamp_authority="https://freetsa.org",
        )

        assert bundle.dsse == envelope
        assert bundle.verification is not None
        assert bundle.verification.timestamp.rfc3161_token == "rfc3161_token_base64"

    def test_bundle_to_json_from_json(self):
        content = b'{"test": "data"}'
        envelope = DSSEEnvelope.create(content)
        envelope.signatures.append(DSSESignature(keyid="k1", sig="c2ln"))

        original = UATPBundle.create(
            envelope=envelope,
            public_key=b"key_bytes_here_32_chars_long!!!",
            key_id="k1",
        )
        original.capsule_id = "caps_test"

        json_str = original.to_json()
        restored = UATPBundle.from_json(json_str)

        assert restored.capsule_id == "caps_test"
        assert restored.dsse.payload == original.dsse.payload
        assert restored.verification.key_id == "k1"

    def test_bundle_get_payload(self):
        data = {"capsule_id": "caps_123", "value": 42}
        content = json.dumps(data).encode()
        envelope = DSSEEnvelope.create(content)

        bundle = UATPBundle(dsse=envelope)
        payload = bundle.get_payload()

        assert payload == data

    def test_bundle_verify_without_material(self):
        envelope = DSSEEnvelope.create(b'{"test": true}')
        bundle = UATPBundle(dsse=envelope)

        result = bundle.verify()

        assert result.is_valid == False
        assert any("no signatures" in e for e in result.errors)

    def test_bundle_structure(self):
        """Verify bundle matches expected structure."""
        content = b'{"capsule_id": "caps_123"}'
        envelope = DSSEEnvelope.create(content, PAYLOAD_TYPE_CAPSULE)
        envelope.signatures.append(
            DSSESignature(keyid="ed25519-abcd1234", sig="dGVzdHNpZw==")
        )

        bundle = UATPBundle.create(
            envelope=envelope,
            public_key=b"x" * 32,
            key_id="ed25519-abcd1234",
            timestamp_token="dGltZXN0YW1w",
            timestamp_authority="https://freetsa.org",
        )

        d = bundle.to_dict()

        # Check structure
        assert d["mediaType"] == "application/vnd.uatp.bundle.v1+json"
        assert "dsse" in d
        assert "verification" in d

        # Check DSSE structure
        dsse = d["dsse"]
        assert "payload" in dsse
        assert "payloadType" in dsse
        assert "signatures" in dsse

        # Check verification structure
        v = d["verification"]
        assert "publicKey" in v
        assert "keyAlgorithm" in v
        assert "timestamp" in v
        assert v["timestamp"]["authority"] == "https://freetsa.org"


class TestBundleWithRealCrypto:
    """Tests using real Ed25519 crypto (if available)."""

    @pytest.fixture
    def ed25519_keys(self):
        """Generate Ed25519 key pair."""
        try:
            from nacl.signing import SigningKey

            signing_key = SigningKey.generate()
            return signing_key, signing_key.verify_key
        except ImportError:
            pytest.skip("nacl not available")

    def test_sign_and_verify_bundle(self, ed25519_keys):
        """Full sign and verify cycle with real keys."""
        signing_key, verify_key = ed25519_keys

        # Create envelope
        capsule_data = {
            "capsule_id": "caps_2026_03_11_test",
            "type": "reasoning_trace",
            "confidence": 0.95,
        }
        envelope = create_capsule_envelope(capsule_data)

        # Sign
        key_id = f"ed25519-{verify_key.encode().hex()[:16]}"

        def sign_func(data: bytes) -> bytes:
            return signing_key.sign(data).signature

        envelope.sign(keyid=key_id, sign_func=sign_func)

        # Create bundle
        bundle = UATPBundle.create(
            envelope=envelope,
            public_key=bytes(verify_key),
            key_id=key_id,
        )

        # Verify
        result = bundle.verify()

        assert result.is_valid == True
        assert result.signature_valid == True
        assert len(result.errors) == 0

    def test_tampered_payload_fails_verification(self, ed25519_keys):
        """Verify that tampering is detected."""
        signing_key, verify_key = ed25519_keys

        # Create and sign
        envelope = create_capsule_envelope({"original": "data"})
        key_id = "test-key"

        def sign_func(data: bytes) -> bytes:
            return signing_key.sign(data).signature

        envelope.sign(keyid=key_id, sign_func=sign_func)

        # Create bundle
        bundle = UATPBundle.create(
            envelope=envelope,
            public_key=bytes(verify_key),
            key_id=key_id,
        )

        # Tamper with payload
        tampered_content = b'{"tampered": true}'
        bundle.dsse.payload = base64.b64encode(tampered_content).decode()

        # Verify should fail
        result = bundle.verify()

        assert result.is_valid == False
        assert result.signature_valid == False


class TestIntegration:
    """Integration tests for export workflow."""

    def test_full_export_workflow(self):
        """Test complete export from capsule to bundle JSON."""
        # 1. Start with capsule data
        capsule = {
            "capsule_id": "caps_2026_03_11_abc123",
            "type": "reasoning_trace",
            "payload": {
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                ],
            },
            "measurements": {
                "confidence": 0.92,
            },
        }

        # 2. Create envelope
        envelope = create_capsule_envelope(capsule)
        assert envelope.payload_type == PAYLOAD_TYPE_CAPSULE

        # 3. Mock signing
        def mock_sign(data: bytes) -> bytes:
            return b"mock_sig_" + data[:8]

        envelope.sign(keyid="mock-key", sign_func=mock_sign)

        # 4. Create bundle
        bundle = UATPBundle.create(
            envelope=envelope,
            public_key=b"mock_public_key_32_bytes_!!!!",
            key_id="mock-key",
        )
        bundle.capsule_id = capsule["capsule_id"]

        # 5. Export to JSON
        json_str = bundle.to_json()
        assert isinstance(json_str, str)

        # 6. Parse and verify structure
        parsed = json.loads(json_str)
        assert parsed["mediaType"] == "application/vnd.uatp.bundle.v1+json"
        assert parsed["capsuleId"] == "caps_2026_03_11_abc123"

        # 7. Restore bundle
        restored = UATPBundle.from_json(json_str)
        restored_payload = restored.get_payload()

        assert restored_payload["capsule_id"] == capsule["capsule_id"]
        assert restored_payload["type"] == "reasoning_trace"


class TestVerificationResult:
    """Tests for VerificationResult."""

    def test_to_dict_basic(self):
        """Test basic to_dict output."""
        from src.export.bundle import VerificationResult

        result = VerificationResult(is_valid=True)
        d = result.to_dict()

        assert d["isValid"] == True
        assert d["errors"] == []
        assert d["warnings"] == []
        assert "verifiedAt" in d
        assert "signatureValid" not in d  # None values omitted

    def test_to_dict_with_signature_status(self):
        """Test to_dict with signature validation info."""
        from src.export.bundle import VerificationResult

        result = VerificationResult(
            is_valid=True,
            signature_valid=True,
            timestamp_valid=False,
        )
        d = result.to_dict()

        assert d["signatureValid"] == True
        assert d["timestampValid"] == False

    def test_to_dict_with_hybrid_signature(self):
        """Test to_dict with PQ signature validation."""
        from src.export.bundle import VerificationResult

        result = VerificationResult(
            is_valid=True,
            signature_valid=True,
            pq_signature_valid=True,
        )
        d = result.to_dict()

        assert d["pqSignatureValid"] == True

    def test_to_dict_with_errors(self):
        """Test to_dict with errors and warnings."""
        from src.export.bundle import VerificationResult

        result = VerificationResult(
            is_valid=False,
            errors=["Signature mismatch", "Key not found"],
            warnings=["Timestamp near expiry"],
        )
        d = result.to_dict()

        assert d["isValid"] == False
        assert len(d["errors"]) == 2
        assert len(d["warnings"]) == 1


class TestBundleIsHybrid:
    """Tests for UATPBundle.is_hybrid property."""

    def test_bundle_is_hybrid_true(self):
        """Test is_hybrid returns True for hybrid bundle."""
        envelope = DSSEEnvelope.create(b'{"test": true}')
        bundle = UATPBundle.create(
            envelope=envelope,
            public_key=b"x" * 32,
            key_id="test",
            pq_public_key=b"y" * 64,
            pq_algorithm="ml-dsa-65",
        )

        assert bundle.is_hybrid == True

    def test_bundle_is_hybrid_false(self):
        """Test is_hybrid returns False for non-hybrid bundle."""
        envelope = DSSEEnvelope.create(b'{"test": true}')
        bundle = UATPBundle.create(
            envelope=envelope,
            public_key=b"x" * 32,
            key_id="test",
        )

        assert bundle.is_hybrid == False

    def test_bundle_is_hybrid_no_verification(self):
        """Test is_hybrid returns False when no verification material."""
        bundle = UATPBundle(dsse=DSSEEnvelope.create(b'{"test": true}'))

        assert bundle.is_hybrid == False


class TestTimestampEvidenceToDict:
    """Tests for TimestampEvidence.to_dict()."""

    def test_to_dict_with_all_fields(self):
        """Test to_dict includes all fields when set."""
        now = datetime.now(timezone.utc)
        ts = TimestampEvidence(
            rfc3161_token="base64token",
            authority="https://freetsa.org",
            timestamp=now,
        )
        d = ts.to_dict()

        assert d["rfc3161Token"] == "base64token"
        assert d["authority"] == "https://freetsa.org"
        assert "timestamp" in d

    def test_to_dict_empty(self):
        """Test to_dict with no fields set."""
        ts = TimestampEvidence()
        d = ts.to_dict()

        assert d == {}


class TestBundleVerifyCustomFunc:
    """Tests for UATPBundle.verify with custom function."""

    def test_verify_with_custom_func_success(self):
        """Test verify with custom verification function that succeeds."""
        envelope = DSSEEnvelope.create(b'{"test": true}')
        envelope.sign(keyid="test-key", sign_func=lambda d: b"valid_sig")

        bundle = UATPBundle.create(
            envelope=envelope,
            public_key=b"x" * 32,
            key_id="test-key",
        )

        # Custom verify function that always returns True for our signature
        def custom_verify(message: bytes, sig: bytes) -> bool:
            return sig == b"valid_sig"

        result = bundle.verify(verify_func=custom_verify)

        assert result.is_valid == True
        assert result.signature_valid == True

    def test_verify_with_custom_func_failure(self):
        """Test verify with custom verification function that fails."""
        envelope = DSSEEnvelope.create(b'{"test": true}')
        envelope.sign(keyid="test-key", sign_func=lambda d: b"some_sig")

        bundle = UATPBundle.create(
            envelope=envelope,
            public_key=b"x" * 32,
            key_id="test-key",
        )

        # Custom verify function that always returns False
        def custom_verify(message: bytes, sig: bytes) -> bool:
            return False

        result = bundle.verify(verify_func=custom_verify)

        assert result.is_valid == False
        assert result.signature_valid == False
