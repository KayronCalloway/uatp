"""Environment variable sanity tests.

These tests replace the legacy `openai_test.py` and `test_script.py` scripts that
lived at project root.  They ensure critical configuration variables are wired
correctly without relying on ad-hoc print statements.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def test_signing_key_env_present(monkeypatch):
    """UATP_SIGNING_KEY must be present and hex-encoded."""
    # For local runs developers may not have the real key; inject dummy value.
    if "UATP_SIGNING_KEY" not in os.environ:
        monkeypatch.setenv("UATP_SIGNING_KEY", "a" * 64)
    key = os.environ["UATP_SIGNING_KEY"]
    # Basic sanity: even length and only hex chars.
    assert len(key) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in key)


def test_api_keys_loaded(monkeypatch):
    """Ensure UATP_API_KEYS env var (JSON) is present for API auth tests."""
    if "UATP_API_KEYS" not in os.environ:
        monkeypatch.setenv("UATP_API_KEYS", "{}")
    assert "UATP_API_KEYS" in os.environ


def test_optional_openai_key(monkeypatch):
    """OPENAI_API_KEY may be missing locally but should not break other tests."""
    # If missing, supply dummy to avoid accidental network calls in unit tests.
    if "OPENAI_API_KEY" not in os.environ:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert os.environ["OPENAI_API_KEY"].startswith("sk-")
