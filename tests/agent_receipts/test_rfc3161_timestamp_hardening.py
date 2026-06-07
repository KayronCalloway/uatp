"""Fail-closed RFC3161 timestamp hardening tests."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from datetime import datetime, timezone

import pytest

from src.security import rfc3161_timestamps
from src.security.rfc3161_timestamps import RFC3161Timestamper, TimestampToken


def test_parse_timestamp_response_does_not_fallback_to_current_time(
    monkeypatch,
) -> None:
    monkeypatch.setattr(rfc3161_timestamps, "RFC3161_AVAILABLE", False)
    timestamper = RFC3161Timestamper.__new__(RFC3161Timestamper)

    with pytest.raises(ValueError, match="could not parse RFC 3161 timestamp response"):
        timestamper._parse_timestamp_response(b"not a timestamp token")


def test_verify_timestamp_rejects_hash_only_verification(monkeypatch) -> None:
    monkeypatch.setattr(rfc3161_timestamps, "RFC3161_AVAILABLE", False)
    data = b"timestamped manifest hash"
    token = TimestampToken(
        token_bytes=b"not independently verified",
        timestamp=datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc),
        tsa_name="freetsa",
        hash_algorithm="sha256",
        message_imprint=hashlib.sha256(data).hexdigest(),
    )
    timestamper = RFC3161Timestamper.__new__(RFC3161Timestamper)

    valid, reason = timestamper.verify_timestamp(token, data)

    assert valid is False
    assert "full RFC 3161 verification unavailable" in reason


def test_verify_timestamp_rejects_rfc3161_without_configured_tsa_trust_anchor(
    monkeypatch,
) -> None:
    class FakeRFC3161:
        @staticmethod
        def verify_timestamp(token_bytes, data):
            return None

    monkeypatch.setattr(rfc3161_timestamps, "RFC3161_AVAILABLE", True)
    monkeypatch.setattr(rfc3161_timestamps, "rfc3161ng", FakeRFC3161)
    data = b"timestamped manifest hash"
    token = TimestampToken(
        token_bytes=b"token with matching imprint",
        timestamp=datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc),
        tsa_name="freetsa",
        hash_algorithm="sha256",
        message_imprint=hashlib.sha256(data).hexdigest(),
    )
    timestamper = RFC3161Timestamper.__new__(RFC3161Timestamper)

    valid, reason = timestamper.verify_timestamp(token, data)

    assert valid is False
    assert "TSA trust anchor verification not configured" in reason


def test_verify_timestamp_rejects_unused_tsa_trust_anchors(monkeypatch) -> None:
    class FakeRFC3161:
        @staticmethod
        def verify_timestamp(token_bytes, data):
            return None

    monkeypatch.setattr(rfc3161_timestamps, "RFC3161_AVAILABLE", True)
    monkeypatch.setattr(rfc3161_timestamps, "rfc3161ng", FakeRFC3161)
    data = b"timestamped manifest hash"
    token = TimestampToken(
        token_bytes=b"token with matching imprint",
        timestamp=datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc),
        tsa_name="freetsa",
        hash_algorithm="sha256",
        message_imprint=hashlib.sha256(data).hexdigest(),
    )
    timestamper = RFC3161Timestamper.__new__(RFC3161Timestamper)

    valid, reason = timestamper.verify_timestamp(
        token,
        data,
        trusted_tsa_certificates=(b"trusted cert not yet wired",),
    )

    assert valid is False
    assert "OpenSSL RFC 3161 verification failed" in reason


def test_verify_timestamp_accepts_openssl_verified_tsa_anchor(monkeypatch) -> None:
    calls = []

    def fake_run(command, *, capture_output, check, text):
        calls.append(command)
        assert capture_output is True
        assert check is False
        assert text is True
        return subprocess.CompletedProcess(
            command, 0, stdout="Verification: OK", stderr=""
        )

    monkeypatch.setattr(rfc3161_timestamps.subprocess, "run", fake_run)
    monkeypatch.setattr(rfc3161_timestamps, "RFC3161_AVAILABLE", False)
    data = b"timestamped manifest hash"
    token = TimestampToken(
        token_bytes=b"trusted timestamp response der",
        timestamp=datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc),
        tsa_name="test-tsa",
        hash_algorithm="sha256",
        message_imprint=hashlib.sha256(data).hexdigest(),
    )
    timestamper = RFC3161Timestamper.__new__(RFC3161Timestamper)

    valid, reason = timestamper.verify_timestamp(
        token,
        data,
        trusted_tsa_certificates=(b"-----BEGIN CERTIFICATE-----\ntrusted\n",),
    )

    assert valid is True
    assert "verified against TSA trust anchor" in reason
    assert calls
    assert calls[0][:3] == ["openssl", "ts", "-verify"]
    assert "-CAfile" in calls[0]


def test_verify_timestamp_rejects_openssl_failure_without_leaking_anchor_bytes(
    monkeypatch,
) -> None:
    def fake_run(command, *, capture_output, check, text):
        return subprocess.CompletedProcess(
            command,
            1,
            stdout="",
            stderr="verification failed near /private/tmp/generated-path",
        )

    monkeypatch.setattr(rfc3161_timestamps.subprocess, "run", fake_run)
    monkeypatch.setattr(rfc3161_timestamps, "RFC3161_AVAILABLE", False)
    data = b"timestamped manifest hash"
    secretish_anchor = b"-----BEGIN CERTIFICATE-----\nDO-NOT-LEAK-ANCHOR\n"
    token = TimestampToken(
        token_bytes=b"DO-NOT-LEAK-TOKEN",
        timestamp=datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc),
        tsa_name="test-tsa",
        hash_algorithm="sha256",
        message_imprint=hashlib.sha256(data).hexdigest(),
    )
    timestamper = RFC3161Timestamper.__new__(RFC3161Timestamper)

    valid, reason = timestamper.verify_timestamp(
        token,
        data,
        trusted_tsa_certificates=(secretish_anchor,),
    )

    assert valid is False
    assert "OpenSSL RFC 3161 verification failed" in reason
    assert "DO-NOT-LEAK" not in reason
    assert "/private/tmp" not in reason


def test_verify_timestamp_with_real_openssl_generated_tsr(tmp_path) -> None:
    if shutil.which("openssl") is None:
        pytest.skip("openssl not installed")

    root_config_path = tmp_path / "root.cnf"
    tsa_request_config_path = tmp_path / "tsa_req.cnf"
    tsa_extension_config_path = tmp_path / "tsa_ext.cnf"
    timestamp_config_path = tmp_path / "timestamp.cnf"
    serial_path = tmp_path / "serial.txt"
    root_key_path = tmp_path / "root.key"
    root_cert_path = tmp_path / "root.crt"
    key_path = tmp_path / "tsa.key"
    csr_path = tmp_path / "tsa.csr"
    cert_path = tmp_path / "tsa.crt"
    data_path = tmp_path / "data.txt"
    query_path = tmp_path / "data.tsq"
    response_path = tmp_path / "data.tsr"
    root_config_path.write_text(
        """
[ req ]
distinguished_name = dn
prompt = no
x509_extensions = ca_ext
[ dn ]
CN = UATP Test Root CA
[ ca_ext ]
basicConstraints = critical,CA:TRUE
keyUsage = critical,keyCertSign,cRLSign
subjectKeyIdentifier = hash
""".strip()
    )
    tsa_request_config_path.write_text(
        """
[ req ]
distinguished_name = dn
prompt = no
[ dn ]
CN = UATP Test TSA
""".strip()
    )
    tsa_extension_config_path.write_text(
        """
[ tsa_ext ]
basicConstraints = critical,CA:FALSE
keyUsage = critical,digitalSignature,nonRepudiation
extendedKeyUsage = critical,timeStamping
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
""".strip()
    )
    timestamp_config_path.write_text(
        """
[ tsa ]
default_tsa = tsa_config
[ tsa_config ]
serial = serial.txt
crypto_device = builtin
signer_cert = tsa.crt
certs = tsa.crt
signer_key = tsa.key
default_policy = 1.2.3.4.1
other_policies = 1.2.3.4.1
signer_digest = sha256
digests = sha256
accuracy = secs:1
ordering = yes
tsa_name = yes
ess_cert_id_chain = no
ess_cert_id_alg = sha256
""".strip()
    )
    serial_path.write_text("01")
    data = b"real openssl timestamped manifest hash"
    data_path.write_bytes(data)

    commands = [
        [
            "openssl",
            "req",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-x509",
            "-days",
            "1",
            "-keyout",
            str(root_key_path),
            "-out",
            str(root_cert_path),
            "-config",
            str(root_config_path),
        ],
        [
            "openssl",
            "req",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(key_path),
            "-out",
            str(csr_path),
            "-config",
            str(tsa_request_config_path),
        ],
        [
            "openssl",
            "x509",
            "-req",
            "-in",
            str(csr_path),
            "-CA",
            str(root_cert_path),
            "-CAkey",
            str(root_key_path),
            "-CAcreateserial",
            "-days",
            "1",
            "-out",
            str(cert_path),
            "-extfile",
            str(tsa_extension_config_path),
            "-extensions",
            "tsa_ext",
        ],
        [
            "openssl",
            "ts",
            "-query",
            "-data",
            str(data_path),
            "-sha256",
            "-cert",
            "-out",
            str(query_path),
        ],
        [
            "openssl",
            "ts",
            "-reply",
            "-queryfile",
            str(query_path),
            "-config",
            str(timestamp_config_path),
            "-out",
            str(response_path),
        ],
    ]
    for command in commands:
        result = subprocess.run(
            command,
            cwd=tmp_path,
            capture_output=True,
            check=False,
            text=True,
        )
        assert result.returncode == 0, result.stderr

    token = TimestampToken(
        token_bytes=response_path.read_bytes(),
        timestamp=datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc),
        tsa_name="openssl-test-tsa",
        hash_algorithm="sha256",
        message_imprint=hashlib.sha256(data).hexdigest(),
    )
    timestamper = RFC3161Timestamper.__new__(RFC3161Timestamper)

    valid, reason = timestamper.verify_timestamp(
        token,
        data,
        trusted_tsa_certificates=(root_cert_path.read_bytes(), cert_path.read_bytes()),
    )

    assert valid is True
    assert "verified against TSA trust anchor" in reason
