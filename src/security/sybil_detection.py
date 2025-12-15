"""
Sybil Detection Interfaces and Implementations
Provides pluggable Sybil resistance for Governance Engine
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class SybilDetector(ABC):
    """Abstract interface for Sybil attack detection."""

    @abstractmethod
    def check(
        self, stakeholder_id: str, identity_proof: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Check if a stakeholder passes Sybil resistance checks.

        Args:
            stakeholder_id: Unique identifier for the stakeholder
            identity_proof: Optional proof of unique identity

        Returns:
            Tuple of (is_valid, reason_message)
        """
        pass


class RealSybilDetector(SybilDetector):
    """Production Sybil detection with full security checks."""

    def __init__(self):
        self.verified_stakeholders: Dict[str, Dict[str, Any]] = {}
        self.suspicious_patterns: Dict[str, list] = {}

    def check(
        self, stakeholder_id: str, identity_proof: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Perform real Sybil resistance checks."""
        # Require identity proof for governance participation
        if not identity_proof:
            logger.warning(
                f"Sybil resistance check failed for {stakeholder_id}: No identity proof"
            )
            return (False, "Identity proof required for governance participation")

        # Verify proof structure
        required_fields = ["method", "identifiers"]
        if not all(field in identity_proof for field in required_fields):
            logger.warning(
                f"Sybil resistance check failed for {stakeholder_id}: Invalid proof structure"
            )
            return (False, "Identity proof missing required fields")

        # Check for duplicate identifiers
        identifiers = identity_proof.get("identifiers", [])
        for existing_id, existing_data in self.verified_stakeholders.items():
            if existing_id == stakeholder_id:
                continue  # Skip self

            existing_identifiers = existing_data.get("identifiers", [])
            # Check for overlapping identifiers
            overlap = set(identifiers) & set(existing_identifiers)
            if overlap:
                logger.warning(
                    f"Sybil resistance check failed for {stakeholder_id}: "
                    f"Duplicate identifiers detected: {overlap}"
                )
                return (False, "Identity already registered under different account")

        # Record successful verification
        self.verified_stakeholders[stakeholder_id] = {
            "verified_at": datetime.now(timezone.utc),
            "method": identity_proof.get("method"),
            "identifiers": identifiers,
            "verification_score": identity_proof.get("score", 1.0),
        }

        logger.info(f"Sybil resistance check passed for stakeholder {stakeholder_id}")
        return (True, "Sybil resistance check passed")


class TestSybilDetector(SybilDetector):
    """Test-only Sybil detector that always succeeds."""

    def check(
        self, stakeholder_id: str, identity_proof: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Always return valid for testing purposes."""
        logger.debug(f"Test mode: Auto-passing Sybil check for {stakeholder_id}")
        return (True, "Test mode - Sybil resistance bypassed")


class MockSybilDetector(SybilDetector):
    """Mock Sybil detector for testing specific scenarios."""

    def __init__(
        self, should_pass: bool = True, failure_reason: str = "Mock Sybil check failed"
    ):
        self.should_pass = should_pass
        self.failure_reason = failure_reason
        self.check_calls: list = []

    def check(
        self, stakeholder_id: str, identity_proof: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Return predetermined result and track calls."""
        self.check_calls.append(
            {
                "stakeholder_id": stakeholder_id,
                "identity_proof": identity_proof,
                "timestamp": datetime.now(timezone.utc),
            }
        )

        if self.should_pass:
            return (True, "Mock Sybil check passed")
        else:
            return (False, self.failure_reason)
