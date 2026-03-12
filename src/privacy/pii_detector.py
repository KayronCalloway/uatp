"""
PII Detector - Pattern-based detection and redaction of sensitive data.

MAIF-inspired feature for automatically detecting and redacting PII during capture.
Supports: emails, API keys, AWS keys, phone numbers, credit cards, SSNs, IP addresses.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class PIIType(str, Enum):
    """Types of PII that can be detected."""

    EMAIL = "email"
    API_KEY = "api_key"
    AWS_KEY = "aws_key"
    AWS_SECRET = "aws_secret"
    PHONE = "phone"
    CREDIT_CARD = "credit_card"
    SSN = "ssn"
    IP_ADDRESS = "ip_address"
    JWT_TOKEN = "jwt_token"
    GITHUB_TOKEN = "github_token"
    OPENAI_KEY = "openai_key"
    ANTHROPIC_KEY = "anthropic_key"
    PASSWORD = "password"


@dataclass
class PIIMatch:
    """Represents a detected PII match."""

    pii_type: PIIType
    original: str
    redacted: str
    start: int
    end: int
    confidence: float = 1.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "type": self.pii_type.value,
            "start": self.start,
            "end": self.end,
            "length": len(self.original),
            "confidence": self.confidence,
        }


@dataclass
class RedactionResult:
    """Result of PII detection and redaction."""

    redacted_text: str
    matches: List[PIIMatch] = field(default_factory=list)
    pii_count: int = 0
    types_found: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "pii_redacted": self.pii_count > 0,
            "pii_count": self.pii_count,
            "types_found": self.types_found,
            "matches": [m.to_dict() for m in self.matches],
        }


class PIIDetector:
    """
    Detects and redacts PII from text using pattern matching.

    Thread-safe and stateless - can be used as a singleton.
    """

    # Patterns for PII detection
    # Order matters - more specific patterns should come first
    PATTERNS: Dict[PIIType, Tuple[str, float]] = {
        # API Keys - specific patterns first
        PIIType.OPENAI_KEY: (r"sk-[a-zA-Z0-9]{20,}", 0.99),
        PIIType.ANTHROPIC_KEY: (r"sk-ant-[a-zA-Z0-9\-]{20,}", 0.99),
        PIIType.GITHUB_TOKEN: (r"gh[pousr]_[A-Za-z0-9_]{36,}", 0.99),
        PIIType.AWS_KEY: (r"AKIA[A-Z0-9]{16}", 0.99),
        PIIType.AWS_SECRET: (r"(?<=['\"])[A-Za-z0-9/+=]{40}(?=['\"])", 0.7),
        # JWT tokens (header.payload.signature format)
        PIIType.JWT_TOKEN: (
            r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]+",
            0.95,
        ),
        # Generic API key pattern (lower confidence)
        PIIType.API_KEY: (
            r"(?:api[_-]?key|apikey|api_secret|secret_key)[=:]\s*['\"]?([a-zA-Z0-9_\-]{16,})['\"]?",
            0.8,
        ),
        # Password in common formats
        PIIType.PASSWORD: (
            r"(?:password|passwd|pwd)[=:]\s*['\"]?([^\s'\"]{8,})['\"]?",
            0.85,
        ),
        # Personal identifiers
        PIIType.SSN: (r"\b\d{3}-\d{2}-\d{4}\b", 0.95),
        PIIType.CREDIT_CARD: (r"\b(?:\d{4}[- ]?){3}\d{4}\b", 0.9),
        PIIType.PHONE: (r"\b(?:\+1[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b", 0.85),
        # Email - broad pattern
        PIIType.EMAIL: (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", 0.95),
        # IP addresses (avoid false positives with version numbers)
        PIIType.IP_ADDRESS: (
            r"\b(?<!\.)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?!\.)\b",
            0.8,
        ),
    }

    # Redaction format by type
    REDACTION_FORMATS: Dict[PIIType, str] = {
        PIIType.EMAIL: "[EMAIL_REDACTED]",
        PIIType.API_KEY: "[API_KEY_REDACTED]",
        PIIType.OPENAI_KEY: "[OPENAI_KEY_REDACTED]",
        PIIType.ANTHROPIC_KEY: "[ANTHROPIC_KEY_REDACTED]",
        PIIType.GITHUB_TOKEN: "[GITHUB_TOKEN_REDACTED]",
        PIIType.AWS_KEY: "[AWS_KEY_REDACTED]",
        PIIType.AWS_SECRET: "[AWS_SECRET_REDACTED]",
        PIIType.JWT_TOKEN: "[JWT_TOKEN_REDACTED]",
        PIIType.PHONE: "[PHONE_REDACTED]",
        PIIType.CREDIT_CARD: "[CREDIT_CARD_REDACTED]",
        PIIType.SSN: "[SSN_REDACTED]",
        PIIType.IP_ADDRESS: "[IP_REDACTED]",
        PIIType.PASSWORD: "[PASSWORD_REDACTED]",
    }

    # Compiled patterns for performance
    _compiled_patterns: Dict[PIIType, re.Pattern] = {}

    def __init__(self, custom_patterns: Optional[Dict[PIIType, str]] = None):
        """
        Initialize the PII detector.

        Args:
            custom_patterns: Optional dict of custom patterns to add/override
        """
        self._compile_patterns()
        if custom_patterns:
            for pii_type, pattern in custom_patterns.items():
                self._compiled_patterns[pii_type] = re.compile(pattern, re.IGNORECASE)

    def _compile_patterns(self) -> None:
        """Compile regex patterns for better performance."""
        for pii_type, (pattern, _) in self.PATTERNS.items():
            try:
                self._compiled_patterns[pii_type] = re.compile(pattern, re.IGNORECASE)
            except re.error:
                # Skip invalid patterns
                pass

    def detect(self, text: str) -> List[PIIMatch]:
        """
        Detect all PII in the given text.

        Args:
            text: Text to scan for PII

        Returns:
            List of PIIMatch objects for each detected PII
        """
        if not text:
            return []

        matches = []
        seen_ranges = set()  # Avoid overlapping matches

        for pii_type, pattern in self._compiled_patterns.items():
            _, confidence = self.PATTERNS.get(pii_type, ("", 1.0))

            for match in pattern.finditer(text):
                start, end = match.start(), match.end()

                # Skip if this range overlaps with a previous match
                range_key = (start, end)
                if range_key in seen_ranges:
                    continue

                # Check for overlap with existing matches
                overlaps = False
                for s, e in seen_ranges:
                    if not (end <= s or start >= e):
                        overlaps = True
                        break

                if overlaps:
                    continue

                seen_ranges.add(range_key)
                original = match.group(0)
                redacted = self.REDACTION_FORMATS.get(
                    pii_type, f"[{pii_type.value.upper()}_REDACTED]"
                )

                matches.append(
                    PIIMatch(
                        pii_type=pii_type,
                        original=original,
                        redacted=redacted,
                        start=start,
                        end=end,
                        confidence=confidence,
                    )
                )

        # Sort by position for consistent replacement
        matches.sort(key=lambda m: m.start)
        return matches

    def redact(self, text: str) -> RedactionResult:
        """
        Detect and redact all PII in the given text.

        Args:
            text: Text to redact PII from

        Returns:
            RedactionResult with redacted text and metadata
        """
        if not text:
            return RedactionResult(redacted_text="")

        matches = self.detect(text)

        if not matches:
            return RedactionResult(redacted_text=text)

        # Build redacted text by replacing matches from end to start
        # (to preserve positions during replacement)
        redacted_text = text
        for match in reversed(matches):
            redacted_text = (
                redacted_text[: match.start]
                + match.redacted
                + redacted_text[match.end :]
            )

        types_found = list({m.pii_type.value for m in matches})

        return RedactionResult(
            redacted_text=redacted_text,
            matches=matches,
            pii_count=len(matches),
            types_found=types_found,
        )

    def detect_and_redact(self, text: str) -> Tuple[str, List[PIIMatch]]:
        """
        Convenience method matching the plan's interface.

        Args:
            text: Text to process

        Returns:
            Tuple of (redacted_text, list_of_matches)
        """
        result = self.redact(text)
        return result.redacted_text, result.matches

    def has_pii(self, text: str) -> bool:
        """
        Quick check if text contains any PII.

        Args:
            text: Text to check

        Returns:
            True if any PII detected
        """
        return len(self.detect(text)) > 0


# Global singleton for convenience
_default_detector: Optional[PIIDetector] = None


def get_pii_detector() -> PIIDetector:
    """Get the default PII detector instance."""
    global _default_detector
    if _default_detector is None:
        _default_detector = PIIDetector()
    return _default_detector


def redact_pii(text: str) -> RedactionResult:
    """Convenience function to redact PII using the default detector."""
    return get_pii_detector().redact(text)
