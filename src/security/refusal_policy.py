"""
Refusal policy interfaces for ethics circuit breaker.

Provides abstraction for different refusal policies (production vs testing).
"""

from abc import ABC, abstractmethod
from typing import List

from src.ethics.rect_system import EthicalViolationType, SeverityLevel


class RefusalPolicy(ABC):
    """Abstract interface for capsule refusal policies."""

    @abstractmethod
    def should_allow_capsule(
        self,
        ethics_score: float,
        severity: SeverityLevel,
        violations: List[EthicalViolationType],
        refusal_threshold: float,
        strict_mode: bool,
    ) -> bool:
        """
        Determine if a capsule should be allowed based on ethics evaluation.

        Args:
            ethics_score: Ethics evaluation score (0-1)
            severity: Severity level of violations
            violations: List of detected violations
            refusal_threshold: Threshold score for refusal
            strict_mode: Whether strict mode is enabled

        Returns:
            True if capsule should be allowed, False if it should be refused
        """
        pass


class RealRefusalPolicy(RefusalPolicy):
    """Production refusal policy that enforces ethical standards."""

    def should_allow_capsule(
        self,
        ethics_score: float,
        severity: SeverityLevel,
        violations: List[EthicalViolationType],
        refusal_threshold: float,
        strict_mode: bool,
    ) -> bool:
        """Enforce actual refusal logic based on ethics evaluation."""
        # Critical violations are always blocked
        if severity == SeverityLevel.CRITICAL:
            return False

        # Check against threshold
        if ethics_score < refusal_threshold:
            return False

        # Check for specific critical violations
        critical_violations = {
            EthicalViolationType.VIOLENCE,
            EthicalViolationType.SELF_HARM,
            EthicalViolationType.HARMFUL_CONTENT,
        }

        if any(v in critical_violations for v in violations):
            return False

        # In strict mode, be more restrictive
        if strict_mode and (severity == SeverityLevel.HIGH or len(violations) > 2):
            return False

        return True


class TestRefusalPolicy(RefusalPolicy):
    """Test refusal policy that never refuses capsules.

    Used in testing to evaluate ethics without actually blocking capsules.
    Allows tests to verify ethics evaluation logic without refusals.
    """

    def should_allow_capsule(
        self,
        ethics_score: float,
        severity: SeverityLevel,
        violations: List[EthicalViolationType],
        refusal_threshold: float,
        strict_mode: bool,
    ) -> bool:
        """Always allow capsules in test mode."""
        return True


class MockRefusalPolicy(RefusalPolicy):
    """Mock refusal policy for testing specific refusal scenarios.

    Allows tests to control exact refusal behavior for specific test cases.
    """

    def __init__(self, should_allow: bool = True):
        """
        Initialize mock refusal policy.

        Args:
            should_allow: Whether this policy should allow capsules (default True)
        """
        self._should_allow = should_allow

    def should_allow_capsule(
        self,
        ethics_score: float,
        severity: SeverityLevel,
        violations: List[EthicalViolationType],
        refusal_threshold: float,
        strict_mode: bool,
    ) -> bool:
        """Return configured allow/refuse decision."""
        return self._should_allow

    def set_should_allow(self, should_allow: bool):
        """Change the allow/refuse decision dynamically."""
        self._should_allow = should_allow
