from scripts.analysis.hermes_report_redaction import (
    redact_report_payload,
    redact_report_text,
)


def test_redacts_api_keys_and_bearer_tokens():
    text = "api_key=fixture-value bearer token Bearer secret-token-value token=plain-secret"

    redacted = redact_report_text(text)

    assert "fixture-value" not in redacted
    assert "secret-token-value" not in redacted
    assert "plain-secret" not in redacted
    assert "[REDACTED]" in redacted


def test_does_not_redact_normal_token_waste_heading():
    assert (
        redact_report_text("## Token Waste / Repetition")
        == "## Token Waste / Repetition"
    )


def test_redacts_connection_strings():
    text = "postgresql://user:synthetic@localhost:5432/db"

    redacted = redact_report_text(text)

    assert "synthetic" not in redacted
    assert "postgresql://" in redacted
    assert "[REDACTED]" in redacted


def test_redacts_absolute_kay_paths_but_keeps_relative_paths():
    text = (
        "/Users/kay/uatp-capsule-engine/scripts/analysis/file.py and "
        "scripts/analysis/file.py and /Users/kay/.hermes/config.yaml"
    )

    redacted = redact_report_text(text)

    assert "/Users/kay" not in redacted
    assert "scripts/analysis/file.py" in redacted
    assert ".hermes/config.yaml" in redacted


def test_recursively_redacts_json_payloads():
    payload = {
        "output_path": "/Users/kay/uatp-capsule-engine/docs/reports/report.md",
        "nested": ["/Users/kay/.hermes/config.yaml", "token=plain-secret"],
    }

    redacted = redact_report_payload(payload)

    assert isinstance(redacted, dict)
    rendered = str(redacted)
    assert "/Users/kay" not in rendered
    assert "plain-secret" not in rendered
    assert "docs/reports/report.md" in rendered
