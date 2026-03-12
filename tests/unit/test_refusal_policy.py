"""
Unit tests for Refusal Policy.
"""

import pytest

from src.ethics.rect_system import EthicalViolationType, SeverityLevel
from src.security.refusal_policy import (
    MockRefusalPolicy,
    RealRefusalPolicy,
    RefusalPolicy,
    TestRefusalPolicy,
)


class TestRefusalPolicyInterface:
    """Tests for RefusalPolicy abstract interface."""

    def test_is_abstract(self):
        """Test RefusalPolicy is abstract."""
        assert hasattr(RefusalPolicy, "should_allow_capsule")

        with pytest.raises(TypeError):
            RefusalPolicy()  # Cannot instantiate abstract class


class TestRealRefusalPolicy:
    """Tests for RealRefusalPolicy (production policy)."""

    @pytest.fixture
    def policy(self):
        """Create a real refusal policy."""
        return RealRefusalPolicy()

    def test_blocks_critical_severity(self, policy):
        """Test blocks capsules with critical severity."""
        result = policy.should_allow_capsule(
            ethics_score=0.9,
            severity=SeverityLevel.CRITICAL,
            violations=[],
            refusal_threshold=0.7,
            strict_mode=False,
        )

        assert result is False

    def test_blocks_below_threshold(self, policy):
        """Test blocks capsules below threshold."""
        result = policy.should_allow_capsule(
            ethics_score=0.5,
            severity=SeverityLevel.LOW,
            violations=[],
            refusal_threshold=0.7,
            strict_mode=False,
        )

        assert result is False

    def test_allows_above_threshold(self, policy):
        """Test allows capsules above threshold."""
        result = policy.should_allow_capsule(
            ethics_score=0.9,
            severity=SeverityLevel.LOW,
            violations=[],
            refusal_threshold=0.7,
            strict_mode=False,
        )

        assert result is True

    def test_blocks_violence(self, policy):
        """Test blocks violence violations."""
        result = policy.should_allow_capsule(
            ethics_score=0.9,
            severity=SeverityLevel.MEDIUM,
            violations=[EthicalViolationType.VIOLENCE],
            refusal_threshold=0.7,
            strict_mode=False,
        )

        assert result is False

    def test_blocks_self_harm(self, policy):
        """Test blocks self-harm violations."""
        result = policy.should_allow_capsule(
            ethics_score=0.9,
            severity=SeverityLevel.MEDIUM,
            violations=[EthicalViolationType.SELF_HARM],
            refusal_threshold=0.7,
            strict_mode=False,
        )

        assert result is False

    def test_blocks_harmful_content(self, policy):
        """Test blocks harmful content violations."""
        result = policy.should_allow_capsule(
            ethics_score=0.9,
            severity=SeverityLevel.MEDIUM,
            violations=[EthicalViolationType.HARMFUL_CONTENT],
            refusal_threshold=0.7,
            strict_mode=False,
        )

        assert result is False

    def test_allows_non_critical_violations(self, policy):
        """Test allows non-critical violations."""
        result = policy.should_allow_capsule(
            ethics_score=0.9,
            severity=SeverityLevel.LOW,
            violations=[EthicalViolationType.BIAS_DETECTION],
            refusal_threshold=0.7,
            strict_mode=False,
        )

        assert result is True

    def test_strict_mode_blocks_high_severity(self, policy):
        """Test strict mode blocks high severity."""
        result = policy.should_allow_capsule(
            ethics_score=0.9,
            severity=SeverityLevel.HIGH,
            violations=[],
            refusal_threshold=0.7,
            strict_mode=True,
        )

        assert result is False

    def test_strict_mode_blocks_many_violations(self, policy):
        """Test strict mode blocks many violations."""
        result = policy.should_allow_capsule(
            ethics_score=0.9,
            severity=SeverityLevel.MEDIUM,
            violations=[
                EthicalViolationType.BIAS_DETECTION,
                EthicalViolationType.MANIPULATION,
                EthicalViolationType.MISINFORMATION,
            ],
            refusal_threshold=0.7,
            strict_mode=True,
        )

        assert result is False

    def test_normal_mode_allows_high_severity(self, policy):
        """Test normal mode allows high severity if above threshold."""
        result = policy.should_allow_capsule(
            ethics_score=0.9,
            severity=SeverityLevel.HIGH,
            violations=[],
            refusal_threshold=0.7,
            strict_mode=False,
        )

        assert result is True

    def test_threshold_boundary(self, policy):
        """Test threshold boundary behavior."""
        # At threshold
        result_at = policy.should_allow_capsule(
            ethics_score=0.7,
            severity=SeverityLevel.LOW,
            violations=[],
            refusal_threshold=0.7,
            strict_mode=False,
        )

        # Just above
        result_above = policy.should_allow_capsule(
            ethics_score=0.71,
            severity=SeverityLevel.LOW,
            violations=[],
            refusal_threshold=0.7,
            strict_mode=False,
        )

        # Just below
        result_below = policy.should_allow_capsule(
            ethics_score=0.69,
            severity=SeverityLevel.LOW,
            violations=[],
            refusal_threshold=0.7,
            strict_mode=False,
        )

        assert result_at is True
        assert result_above is True
        assert result_below is False


class TestTestRefusalPolicy:
    """Tests for TestRefusalPolicy (always allows)."""

    @pytest.fixture
    def policy(self):
        """Create a test refusal policy."""
        return TestRefusalPolicy()

    def test_always_allows(self, policy):
        """Test always allows capsules."""
        result = policy.should_allow_capsule(
            ethics_score=0.0,
            severity=SeverityLevel.CRITICAL,
            violations=[EthicalViolationType.VIOLENCE],
            refusal_threshold=0.9,
            strict_mode=True,
        )

        assert result is True

    def test_allows_with_low_score(self, policy):
        """Test allows even with low ethics score."""
        result = policy.should_allow_capsule(
            ethics_score=0.1,
            severity=SeverityLevel.HIGH,
            violations=[],
            refusal_threshold=0.8,
            strict_mode=True,
        )

        assert result is True

    def test_allows_critical_violations(self, policy):
        """Test allows even critical violations."""
        result = policy.should_allow_capsule(
            ethics_score=0.5,
            severity=SeverityLevel.CRITICAL,
            violations=[
                EthicalViolationType.VIOLENCE,
                EthicalViolationType.SELF_HARM,
            ],
            refusal_threshold=0.7,
            strict_mode=True,
        )

        assert result is True


class TestMockRefusalPolicy:
    """Tests for MockRefusalPolicy (configurable)."""

    def test_create_default_allows(self):
        """Test creates with default allow behavior."""
        policy = MockRefusalPolicy()

        result = policy.should_allow_capsule(
            ethics_score=0.5,
            severity=SeverityLevel.HIGH,
            violations=[],
            refusal_threshold=0.7,
            strict_mode=False,
        )

        assert result is True

    def test_create_with_refuse(self):
        """Test creates with refuse behavior."""
        policy = MockRefusalPolicy(should_allow=False)

        result = policy.should_allow_capsule(
            ethics_score=0.9,
            severity=SeverityLevel.LOW,
            violations=[],
            refusal_threshold=0.5,
            strict_mode=False,
        )

        assert result is False

    def test_set_should_allow_changes_behavior(self):
        """Test can change allow/refuse behavior."""
        policy = MockRefusalPolicy(should_allow=True)

        # Initially allows
        result1 = policy.should_allow_capsule(
            ethics_score=0.5,
            severity=SeverityLevel.LOW,
            violations=[],
            refusal_threshold=0.7,
            strict_mode=False,
        )

        # Change to refuse
        policy.set_should_allow(False)

        result2 = policy.should_allow_capsule(
            ethics_score=0.9,
            severity=SeverityLevel.LOW,
            violations=[],
            refusal_threshold=0.5,
            strict_mode=False,
        )

        assert result1 is True
        assert result2 is False

    def test_ignores_parameters(self):
        """Test ignores all parameters and uses configured value."""
        policy = MockRefusalPolicy(should_allow=True)

        # Even with terrible parameters, still allows
        result = policy.should_allow_capsule(
            ethics_score=0.0,
            severity=SeverityLevel.CRITICAL,
            violations=[EthicalViolationType.VIOLENCE],
            refusal_threshold=0.99,
            strict_mode=True,
        )

        assert result is True


class TestRefusalPolicyComparison:
    """Tests comparing different policy implementations."""

    def test_real_vs_test_policy(self):
        """Test Real policy blocks while Test policy allows."""
        real = RealRefusalPolicy()
        test = TestRefusalPolicy()

        # Case that should be blocked
        real_result = real.should_allow_capsule(
            ethics_score=0.3,
            severity=SeverityLevel.CRITICAL,
            violations=[EthicalViolationType.VIOLENCE],
            refusal_threshold=0.7,
            strict_mode=True,
        )

        test_result = test.should_allow_capsule(
            ethics_score=0.3,
            severity=SeverityLevel.CRITICAL,
            violations=[EthicalViolationType.VIOLENCE],
            refusal_threshold=0.7,
            strict_mode=True,
        )

        assert real_result is False
        assert test_result is True

    def test_all_policies_implement_interface(self):
        """Test all policies implement the interface correctly."""
        policies = [
            RealRefusalPolicy(),
            TestRefusalPolicy(),
            MockRefusalPolicy(),
        ]

        for policy in policies:
            assert isinstance(policy, RefusalPolicy)
            assert hasattr(policy, "should_allow_capsule")

    def test_real_policy_strictness_levels(self):
        """Test real policy respects strictness levels."""
        policy = RealRefusalPolicy()

        # Scenario: medium severity, multiple violations, good score
        normal_mode = policy.should_allow_capsule(
            ethics_score=0.9,
            severity=SeverityLevel.MEDIUM,
            violations=[
                EthicalViolationType.BIAS_DETECTION,
                EthicalViolationType.MANIPULATION,
                EthicalViolationType.MISINFORMATION,
            ],
            refusal_threshold=0.7,
            strict_mode=False,
        )

        strict_mode = policy.should_allow_capsule(
            ethics_score=0.9,
            severity=SeverityLevel.MEDIUM,
            violations=[
                EthicalViolationType.BIAS_DETECTION,
                EthicalViolationType.MANIPULATION,
                EthicalViolationType.MISINFORMATION,
            ],
            refusal_threshold=0.7,
            strict_mode=True,
        )

        # Normal mode should allow, strict mode should block (>2 violations)
        assert normal_mode is True
        assert strict_mode is False
