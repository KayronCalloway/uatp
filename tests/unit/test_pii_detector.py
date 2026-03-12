"""
Unit tests for PII Detector.
"""

import pytest

from src.privacy.pii_detector import PIIDetector, PIIMatch, PIIType, RedactionResult


class TestPIIDetector:
    """Tests for the PIIDetector class."""

    @pytest.fixture
    def detector(self):
        """Create a PII detector instance."""
        return PIIDetector()

    # --- Email Detection Tests ---

    def test_detect_email(self, detector):
        """Test email detection."""
        text = "Contact me at john.doe@example.com for more info."
        matches = detector.detect(text)

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.EMAIL
        assert matches[0].original == "john.doe@example.com"

    def test_detect_multiple_emails(self, detector):
        """Test multiple email detection."""
        text = "Email alice@test.org or bob@company.co.uk"
        matches = detector.detect(text)

        assert len(matches) == 2
        emails = [m.original for m in matches]
        assert "alice@test.org" in emails
        assert "bob@company.co.uk" in emails

    # --- API Key Detection Tests ---

    def test_detect_openai_key(self, detector):
        """Test OpenAI API key detection."""
        text = "My key is sk-1234567890abcdefghij1234567890abcdefghij"
        matches = detector.detect(text)

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.OPENAI_KEY

    def test_detect_anthropic_key(self, detector):
        """Test Anthropic API key detection."""
        text = "Use key sk-ant-api03-abcdefghijklmnopqrstuvwxyz"
        matches = detector.detect(text)

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.ANTHROPIC_KEY

    def test_detect_aws_key(self, detector):
        """Test AWS access key detection."""
        text = "AWS key: AKIAIOSFODNN7EXAMPLE"
        matches = detector.detect(text)

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.AWS_KEY

    def test_detect_github_token(self, detector):
        """Test GitHub token detection."""
        text = "Token: ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        matches = detector.detect(text)

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.GITHUB_TOKEN

    # --- Personal Information Tests ---

    def test_detect_phone_number(self, detector):
        """Test US phone number detection."""
        text = "Call me at 555-123-4567 or (555) 987-6543"
        matches = detector.detect(text)

        assert len(matches) == 2
        assert all(m.pii_type == PIIType.PHONE for m in matches)

    def test_detect_credit_card(self, detector):
        """Test credit card number detection."""
        text = "Card: 4111-1111-1111-1111"
        matches = detector.detect(text)

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.CREDIT_CARD

    def test_detect_ssn(self, detector):
        """Test SSN detection."""
        text = "SSN: 123-45-6789"
        matches = detector.detect(text)

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.SSN

    # --- Redaction Tests ---

    def test_redact_email(self, detector):
        """Test email redaction."""
        text = "Contact john@example.com for help."
        result = detector.redact(text)

        assert isinstance(result, RedactionResult)
        assert "[EMAIL_REDACTED]" in result.redacted_text
        assert "john@example.com" not in result.redacted_text
        assert result.pii_count == 1
        assert "email" in result.types_found

    def test_redact_multiple_types(self, detector):
        """Test redacting multiple PII types."""
        text = "Email: test@example.com, Phone: 555-123-4567"
        result = detector.redact(text)

        assert "[EMAIL_REDACTED]" in result.redacted_text
        assert "[PHONE_REDACTED]" in result.redacted_text
        assert result.pii_count == 2

    def test_redact_preserves_context(self, detector):
        """Test that non-PII text is preserved."""
        text = "Hello, my email is test@example.com. Please reply."
        result = detector.redact(text)

        assert result.redacted_text.startswith("Hello, my email is")
        assert result.redacted_text.endswith(". Please reply.")

    # --- Edge Cases ---

    def test_no_pii_found(self, detector):
        """Test handling text with no PII."""
        text = "This is a normal sentence with no sensitive data."
        result = detector.redact(text)

        assert result.redacted_text == text
        assert result.pii_count == 0
        assert len(result.matches) == 0

    def test_empty_text(self, detector):
        """Test handling empty text."""
        result = detector.redact("")
        assert result.redacted_text == ""
        assert result.pii_count == 0

    def test_detect_and_redact_convenience(self, detector):
        """Test the detect_and_redact convenience method."""
        text = "Email me at test@example.com"
        redacted, matches = detector.detect_and_redact(text)

        assert "[EMAIL_REDACTED]" in redacted
        assert len(matches) == 1

    def test_has_pii(self, detector):
        """Test the has_pii quick check method."""
        assert detector.has_pii("test@example.com")
        assert not detector.has_pii("no sensitive data here")

    # --- Confidence Scores ---

    def test_confidence_scores(self, detector):
        """Test that matches have appropriate confidence scores."""
        text = "sk-1234567890abcdefghij1234567890abcdefghij"
        matches = detector.detect(text)

        assert len(matches) == 1
        assert matches[0].confidence >= 0.9  # High confidence for known patterns

    # --- RedactionResult Tests ---

    def test_redaction_result_to_dict(self, detector):
        """Test RedactionResult serialization."""
        text = "Contact test@example.com"
        result = detector.redact(text)
        d = result.to_dict()

        assert d["pii_redacted"] == True
        assert d["pii_count"] == 1
        assert "email" in d["types_found"]
        assert len(d["matches"]) == 1
        assert d["matches"][0]["type"] == "email"


class TestPIIMatch:
    """Tests for PIIMatch dataclass."""

    def test_to_dict(self):
        """Test PIIMatch serialization."""
        match = PIIMatch(
            pii_type=PIIType.EMAIL,
            original="test@example.com",
            redacted="[EMAIL_REDACTED]",
            start=0,
            end=16,
            confidence=0.95,
        )
        d = match.to_dict()

        assert d["type"] == "email"
        assert d["start"] == 0
        assert d["end"] == 16
        assert d["length"] == 16
        assert d["confidence"] == 0.95


class TestAdditionalPIITypes:
    """Tests for additional PII types."""

    @pytest.fixture
    def detector(self):
        return PIIDetector()

    def test_detect_jwt_token(self, detector):
        """Test JWT token detection."""
        # Example JWT-like token (base64 encoded segments)
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        text = f"Bearer {jwt}"
        matches = detector.detect(text)

        jwt_matches = [m for m in matches if m.pii_type == PIIType.JWT_TOKEN]
        assert len(jwt_matches) == 1

    def test_detect_ip_address(self, detector):
        """Test IP address detection."""
        text = "Server IP: 192.168.1.100"
        matches = detector.detect(text)

        ip_matches = [m for m in matches if m.pii_type == PIIType.IP_ADDRESS]
        assert len(ip_matches) == 1
        assert ip_matches[0].original == "192.168.1.100"

    def test_ip_address_not_version_number(self, detector):
        """Test that version numbers like 1.2.3 are not detected as IPs."""
        text = "Version 1.2.3 released today"
        matches = detector.detect(text)

        ip_matches = [m for m in matches if m.pii_type == PIIType.IP_ADDRESS]
        # Should not detect "1.2.3" as IP (not valid IP format)
        # Valid IPs have 4 octets, not 3
        assert len(ip_matches) == 0


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_pii_detector_singleton(self):
        """Test that get_pii_detector returns same instance."""
        from src.privacy.pii_detector import get_pii_detector

        detector1 = get_pii_detector()
        detector2 = get_pii_detector()

        assert detector1 is detector2

    def test_redact_pii_convenience(self):
        """Test the redact_pii convenience function."""
        from src.privacy.pii_detector import redact_pii

        result = redact_pii("Contact test@example.com please")

        assert "[EMAIL_REDACTED]" in result.redacted_text
        assert result.pii_count == 1


class TestCustomPatterns:
    """Tests for custom pattern support."""

    def test_custom_pattern(self):
        """Test adding custom patterns."""
        # Add custom pattern for internal employee IDs
        custom = {PIIType.API_KEY: r"EMP-\d{6}"}
        detector = PIIDetector(custom_patterns=custom)

        text = "Employee ID: EMP-123456"
        matches = detector.detect(text)

        # Should find the custom pattern
        assert any(m.original == "EMP-123456" for m in matches)
