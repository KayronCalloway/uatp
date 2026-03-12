"""
Unit tests for CSRF Protection.
"""

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.security.csrf_protection import (
    APICSRFProtection,
    CSRFProtection,
    DoubleSubmitCSRF,
    get_csrf_token,
    validate_csrf_token,
    validate_origin,
)


class TestCSRFProtection:
    """Tests for CSRFProtection class."""

    def test_init_generates_secret(self):
        """Test that init generates secret key if not provided."""
        csrf = CSRFProtection()
        assert csrf.secret_key is not None
        assert len(csrf.secret_key) > 20

    def test_init_uses_provided_secret(self):
        """Test that init uses provided secret key."""
        csrf = CSRFProtection(secret_key="my-secret-key")
        assert csrf.secret_key == "my-secret-key"

    def test_generate_token(self):
        """Test token generation."""
        csrf = CSRFProtection(secret_key="test-secret")
        token = csrf.generate_token("session123")

        assert token is not None
        assert ":" in token
        # Token format: session_id:timestamp:signature
        parts = token.split(":")
        assert len(parts) == 3

    def test_generate_token_no_session(self):
        """Test token generation without session ID."""
        csrf = CSRFProtection(secret_key="test-secret")
        token = csrf.generate_token()

        assert token is not None
        parts = token.split(":")
        assert len(parts) == 3

    def test_validate_token_valid(self):
        """Test valid token validation."""
        csrf = CSRFProtection(secret_key="test-secret")
        token = csrf.generate_token("session123")

        is_valid = csrf.validate_token(token, "session123")
        assert is_valid is True

    def test_validate_token_without_session(self):
        """Test validation without session ID."""
        csrf = CSRFProtection(secret_key="test-secret")
        token = csrf.generate_token()

        is_valid = csrf.validate_token(token)
        assert is_valid is True

    def test_validate_token_wrong_session(self):
        """Test validation with wrong session ID."""
        csrf = CSRFProtection(secret_key="test-secret")
        token = csrf.generate_token("session123")

        is_valid = csrf.validate_token(token, "wrong_session")
        assert is_valid is False

    def test_validate_token_invalid_format(self):
        """Test validation with invalid token format."""
        csrf = CSRFProtection(secret_key="test-secret")

        is_valid = csrf.validate_token("invalid-token-format")
        assert is_valid is False

    def test_validate_token_not_in_store(self):
        """Test validation for token not in store."""
        csrf = CSRFProtection(secret_key="test-secret")

        # Token with correct format but not in store
        is_valid = csrf.validate_token("session:123456:abc123")
        assert is_valid is False

    def test_validate_token_empty(self):
        """Test validation with empty token."""
        csrf = CSRFProtection(secret_key="test-secret")

        is_valid = csrf.validate_token("")
        assert is_valid is False

        is_valid = csrf.validate_token(None)
        assert is_valid is False

    def test_token_expiry(self):
        """Test token expiration mechanism."""
        csrf = CSRFProtection(secret_key="test-secret", token_expiry=3600)
        token = csrf.generate_token()

        # Valid immediately
        assert csrf.validate_token(token) is True

        # Manually expire the token by modifying store
        token_info = csrf.token_store[token]
        token_info["expires_at"] = int(time.time()) - 1

        # Now invalid
        assert csrf.validate_token(token) is False

    def test_cleanup_expired_tokens(self):
        """Test expired token cleanup."""
        csrf = CSRFProtection(secret_key="test-secret", token_expiry=3600)
        token1 = csrf.generate_token()

        assert len(csrf.token_store) == 1

        # Manually expire the token
        csrf.token_store[token1]["expires_at"] = int(time.time()) - 1

        # Generate new token (triggers cleanup)
        csrf.generate_token()

        # Old token should be cleaned up
        assert token1 not in csrf.token_store


class TestCSRFProtectionRequest:
    """Tests for CSRF request handling."""

    def test_require_csrf_token_missing(self):
        """Test missing CSRF token raises exception."""
        csrf = CSRFProtection(secret_key="test-secret")

        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/test"
        request.headers.get.return_value = None
        request.query_params.get.return_value = None
        # Ensure form check doesn't return a token
        delattr(request, "form")

        with pytest.raises(HTTPException) as exc_info:
            csrf.require_csrf_token(request)

        assert exc_info.value.status_code == 403
        assert "required" in exc_info.value.detail

    def test_require_csrf_token_invalid(self):
        """Test invalid CSRF token raises exception."""
        csrf = CSRFProtection(secret_key="test-secret")

        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/test"
        request.headers.get.return_value = "invalid-token"

        with pytest.raises(HTTPException) as exc_info:
            csrf.require_csrf_token(request)

        assert exc_info.value.status_code == 403
        assert "Invalid" in exc_info.value.detail

    def test_require_csrf_skips_safe_methods(self):
        """Test CSRF skipped for safe methods."""
        csrf = CSRFProtection(secret_key="test-secret")

        for method in ["GET", "HEAD", "OPTIONS"]:
            request = MagicMock()
            request.method = method

            # Should not raise
            csrf.require_csrf_token(request)

    def test_get_token_from_header(self):
        """Test extracting token from header."""
        csrf = CSRFProtection(secret_key="test-secret")

        request = MagicMock()
        request.headers.get.return_value = "token-from-header"

        token = csrf.get_token_from_request(request)
        assert token == "token-from-header"

    def test_get_token_from_query_params(self):
        """Test extracting token from query params."""
        csrf = CSRFProtection(secret_key="test-secret")

        request = MagicMock()
        request.headers.get.return_value = None
        request.query_params.get.return_value = "token-from-query"
        # Ensure form check doesn't match
        delattr(request, "form")

        token = csrf.get_token_from_request(request)
        assert token == "token-from-query"


class TestDoubleSubmitCSRF:
    """Tests for DoubleSubmitCSRF class."""

    def test_generate_token(self):
        """Test token generation."""
        ds = DoubleSubmitCSRF()
        token = ds.generate_token()

        assert token is not None
        assert len(token) > 20

    def test_init_defaults(self):
        """Test default values."""
        ds = DoubleSubmitCSRF()

        assert ds.cookie_name == "csrf_token"
        assert ds.cookie_secure is True
        assert ds.cookie_httponly is True

    def test_init_custom(self):
        """Test custom values."""
        ds = DoubleSubmitCSRF(
            cookie_name="my_csrf",
            cookie_secure=False,
            cookie_httponly=False,
        )

        assert ds.cookie_name == "my_csrf"
        assert ds.cookie_secure is False
        assert ds.cookie_httponly is False

    def test_validate_double_submit_valid(self):
        """Test valid double submit."""
        ds = DoubleSubmitCSRF()
        token = ds.generate_token()

        request = MagicMock()
        request.cookies.get.return_value = token
        request.headers.get.return_value = token

        is_valid = ds.validate_double_submit(request)
        assert is_valid is True

    def test_validate_double_submit_missing_cookie(self):
        """Test missing cookie."""
        ds = DoubleSubmitCSRF()

        request = MagicMock()
        request.cookies.get.return_value = None

        is_valid = ds.validate_double_submit(request)
        assert is_valid is False

    def test_validate_double_submit_mismatch(self):
        """Test token mismatch."""
        ds = DoubleSubmitCSRF()

        request = MagicMock()
        request.cookies.get.return_value = "cookie-token"
        request.headers.get.return_value = "header-token"

        is_valid = ds.validate_double_submit(request)
        assert is_valid is False


class TestAPICSRFProtection:
    """Tests for APICSRFProtection class."""

    def test_generate_api_token(self):
        """Test API token generation."""
        api_csrf = APICSRFProtection()
        token = api_csrf.generate_api_token("api_key_123")

        assert token is not None
        assert len(token) > 20
        assert token in api_csrf.tokens

    def test_validate_api_token_valid(self):
        """Test valid API token."""
        api_csrf = APICSRFProtection()
        token = api_csrf.generate_api_token("api_key_123")

        is_valid = api_csrf.validate_api_token(token, "api_key_123")
        assert is_valid is True

    def test_validate_api_token_wrong_key(self):
        """Test API token with wrong key."""
        api_csrf = APICSRFProtection()
        token = api_csrf.generate_api_token("api_key_123")

        is_valid = api_csrf.validate_api_token(token, "wrong_key")
        assert is_valid is False

    def test_validate_api_token_not_found(self):
        """Test API token not found."""
        api_csrf = APICSRFProtection()

        is_valid = api_csrf.validate_api_token("nonexistent", "api_key")
        assert is_valid is False


class TestValidateOrigin:
    """Tests for validate_origin function."""

    def test_validate_origin_match(self):
        """Test origin validation with match."""
        request = MagicMock()
        request.headers.get.side_effect = lambda h: (
            "https://example.com" if h == "Origin" else None
        )

        result = validate_origin(request, ["https://example.com"])
        assert result is True

    def test_validate_origin_no_match(self):
        """Test origin validation with no match."""
        request = MagicMock()
        request.headers.get.side_effect = lambda h: (
            "https://evil.com" if h == "Origin" else None
        )

        result = validate_origin(request, ["https://example.com"])
        assert result is False

    def test_validate_origin_uses_referer(self):
        """Test origin validation falls back to Referer."""
        request = MagicMock()
        request.headers.get.side_effect = lambda h: (
            "https://example.com/page" if h == "Referer" else None
        )

        result = validate_origin(request, ["https://example.com"])
        assert result is True


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_csrf_token(self):
        """Test get_csrf_token function."""
        token = get_csrf_token("session123")

        assert token is not None
        assert ":" in token

    def test_validate_csrf_token(self):
        """Test validate_csrf_token function."""
        token = get_csrf_token("session123")

        is_valid = validate_csrf_token(token, "session123")
        assert is_valid is True
