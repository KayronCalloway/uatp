"""Shared redaction helpers for framework-neutral agent receipts."""

from src.agent_receipts.redaction import (
    REDACTED,
    is_sensitive_key,
    redact_error_message,
    redact_value,
)


def test_redact_value_recursively_masks_sensitive_keys_without_mutating_input() -> None:
    original = {
        "api_token": "sk-live-abc123",
        "nested": {
            "Authorization": "Bearer secret-token",
            "safe": "visible",
            "items": [{"password": "p@ss", "name": "worker"}],
        },
    }

    redacted = redact_value(original)

    assert redacted == {
        "api_token": REDACTED,
        "nested": {
            "Authorization": REDACTED,
            "safe": "visible",
            "items": [{"password": REDACTED, "name": "worker"}],
        },
    }
    assert original["api_token"] == "sk-live-abc123"
    assert original["nested"]["items"][0]["password"] == "p@ss"


def test_redact_value_masks_embedded_bearer_tokens_urls_and_key_assignments() -> None:
    value = {
        "command": "curl -H 'Authorization: Bearer abc.def.ghi' https://api.example.test?token=plain-secret&safe=1",
        "env": "OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz1234567890",
    }

    redacted = redact_value(value)

    assert "abc.def.ghi" not in redacted["command"]
    assert "plain-secret" not in redacted["command"]
    assert "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890" not in redacted["env"]
    assert "Authorization: Bearer [REDACTED]" in redacted["command"]
    assert "token=[REDACTED]" in redacted["command"]
    assert "OPENAI_API_KEY=[REDACTED]" == redacted["env"]


def test_redact_error_message_uses_arguments_and_embedded_secret_patterns() -> None:
    message = "request failed for token abc123 with Authorization: Bearer xyz.secret"
    arguments = {"token": "abc123", "path": "/tmp/file"}

    redacted = redact_error_message(message, arguments)

    assert (
        redacted
        == "request failed for token [REDACTED] with Authorization: Bearer [REDACTED]"
    )


def test_sensitive_key_matching_covers_common_spellings() -> None:
    assert is_sensitive_key("api-token")
    assert is_sensitive_key("OPENAI_API_KEY")
    assert is_sensitive_key("Authorization")
    assert not is_sensitive_key("tool_name")
