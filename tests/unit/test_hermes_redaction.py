"""Tests for the redaction filter (Phase H1.2)."""

from src.integrations.hermes import hermes_capture


def test_redact_secrets_strips_api_key_assignment():
    text = 'config = {"api_key": "sk-abc123def456ghi789"}'
    redacted, count = hermes_capture._redact_secrets(text)

    assert "sk-abc123def456ghi789" not in redacted
    assert "[REDACTED]" in redacted
    assert count == 1


def test_redact_secrets_strips_password_assignment():
    text = "password = 'hunter2hunter2'"
    redacted, count = hermes_capture._redact_secrets(text)

    assert "hunter2hunter2" not in redacted
    assert count >= 1


def test_redact_secrets_strips_aws_access_key():
    text = "AWS_KEY=AKIAIOSFODNN7EXAMPLE more text"
    redacted, count = hermes_capture._redact_secrets(text)

    assert "AKIAIOSFODNN7EXAMPLE" not in redacted
    assert count >= 1


def test_redact_secrets_strips_google_api_key():
    text = "key=AIzaSyA-aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456"
    redacted, count = hermes_capture._redact_secrets(text)

    assert "AIzaSyA-aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456" not in redacted
    assert count >= 1


def test_redact_secrets_strips_jwt_token():
    text = (
        "Authorization: Bearer "
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0."
        "abc-def_GHI-jklMNopqr"
    )
    redacted, count = hermes_capture._redact_secrets(text)

    assert "eyJhbGciOiJIUzI1NiJ9" not in redacted
    assert count >= 1


def test_redact_secrets_strips_bearer_token_assignment():
    text = "token: 'gho_aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uV1wX2'"
    redacted, count = hermes_capture._redact_secrets(text)

    assert "gho_aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uV1wX2" not in redacted
    assert count >= 1


def test_redact_secrets_strips_signing_key_hex_blob():
    # 64 hex chars assigned to a key-like field
    text = (
        "signing_key=00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"
    )
    redacted, count = hermes_capture._redact_secrets(text)

    assert "00112233445566778899aabbccddeeff" not in redacted
    assert count >= 1


def test_redact_secrets_leaves_benign_text_unchanged():
    benign = "The build passed: 1648 passed, 11 skipped in 71.10s"
    redacted, count = hermes_capture._redact_secrets(benign)

    assert redacted == benign
    assert count == 0


def test_redact_secrets_returns_input_for_non_string():
    redacted, count = hermes_capture._redact_secrets(None)
    assert redacted == ""
    assert count == 0
