"""
Unit tests for Confidence Explainer.
"""

import pytest

from src.analysis.confidence_explainer import ConfidenceExplainer, ConfidenceExplanation


class TestConfidenceExplanation:
    """Tests for ConfidenceExplanation dataclass."""

    def test_create_explanation(self):
        """Test creating a confidence explanation."""
        exp = ConfidenceExplanation(
            confidence=0.85,
            confidence_factors={"base": 0.8, "bonus": 0.05},
            boosting_factors=["Code examples provided"],
            limiting_factors=["Brief response"],
            improvement_suggestions=["Add more detail"],
        )

        assert exp.confidence == 0.85
        assert len(exp.confidence_factors) == 2
        assert len(exp.boosting_factors) == 1

    def test_to_dict(self):
        """Test converting explanation to dict."""
        exp = ConfidenceExplanation(
            confidence=0.857,
            confidence_factors={"base": 0.85, "adjustment": 0.007},
            boosting_factors=["test"],
            limiting_factors=[],
            improvement_suggestions=["improve"],
        )

        result = exp.to_dict()

        assert result["confidence"] == 0.857
        assert result["confidence_factors"]["base"] == 0.85
        assert result["confidence_factors"]["adjustment"] == 0.007
        assert "boosting_factors" in result

    def test_rounds_values(self):
        """Test rounds confidence values to 3 decimals."""
        exp = ConfidenceExplanation(
            confidence=0.123456789,
            confidence_factors={"test": 0.987654321},
        )

        result = exp.to_dict()

        assert result["confidence"] == 0.123
        assert result["confidence_factors"]["test"] == 0.988


class TestConfidenceExplainerExplainMessageConfidence:
    """Tests for ConfidenceExplainer.explain_message_confidence."""

    def test_assistant_base_confidence(self):
        """Test assistant has higher base confidence."""
        exp = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=500,
            token_count=None,
        )

        assert exp.confidence > 0.7

    def test_user_base_confidence(self):
        """Test user has lower base confidence."""
        exp = ConfidenceExplainer.explain_message_confidence(
            role="user",
            content_length=500,
            token_count=None,
        )

        assert 0.6 < exp.confidence < 0.8

    def test_long_content_boosts_confidence(self):
        """Test long content boosts confidence."""
        short = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=500,
            token_count=None,
        )
        long = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=1500,
            token_count=None,
        )

        assert long.confidence > short.confidence

    def test_very_brief_reduces_confidence(self):
        """Test very brief content reduces confidence."""
        exp = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=50,
            token_count=None,
        )

        assert "brief" in str(exp.limiting_factors).lower()
        assert exp.confidence < 0.85

    def test_code_presence_boosts(self):
        """Test code presence boosts confidence."""
        no_code = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=500,
            token_count=None,
            has_code=False,
        )
        with_code = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=500,
            token_count=None,
            has_code=True,
        )

        assert with_code.confidence > no_code.confidence

    def test_questions_reduce_confidence(self):
        """Test clarifying questions reduce confidence."""
        exp = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=500,
            token_count=None,
            has_questions=True,
        )

        assert any("question" in f.lower() for f in exp.limiting_factors)

    def test_token_count_boosts(self):
        """Test high token count boosts confidence."""
        low_tokens = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=500,
            token_count=100,
        )
        high_tokens = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=500,
            token_count=600,
        )

        assert high_tokens.confidence > low_tokens.confidence

    def test_uncertainty_language_reduces(self):
        """Test uncertainty language reduces confidence."""
        exp = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=500,
            token_count=None,
            uncertainty_language=["maybe", "possibly", "might"],
        )

        assert any("uncertain" in f.lower() for f in exp.limiting_factors)
        assert exp.confidence < 0.85

    def test_uncertainty_capped(self):
        """Test uncertainty reduction is capped."""
        exp = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=500,
            token_count=None,
            uncertainty_language=["maybe"] * 20,  # Many uncertainty words
        )

        # Penalty should be capped at -0.15
        uncertainty_factor = exp.confidence_factors.get("uncertainty_language", 0)
        assert uncertainty_factor >= -0.15

    def test_complete_response_bonus(self):
        """Test complete response (long + code) gets bonus."""
        exp = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=600,
            token_count=None,
            has_code=True,
        )

        assert "complete_response" in exp.confidence_factors

    def test_confidence_clamped(self):
        """Test confidence is clamped to [0, 1]."""
        # Try to create very high confidence
        exp = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=5000,
            token_count=2000,
            has_code=True,
        )

        assert 0.0 <= exp.confidence <= 1.0

    def test_boosting_factors_recorded(self):
        """Test boosting factors are recorded."""
        exp = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=1500,
            token_count=None,
            has_code=True,
        )

        assert len(exp.boosting_factors) > 0

    def test_suggestions_when_limited(self):
        """Test suggestions provided when factors limit confidence."""
        exp = ConfidenceExplainer.explain_message_confidence(
            role="assistant",
            content_length=50,  # Brief
            token_count=None,
        )

        assert len(exp.improvement_suggestions) > 0


class TestConfidenceExplainerExplainStepConfidence:
    """Tests for ConfidenceExplainer.explain_step_confidence."""

    def test_measurements_boost(self):
        """Test measurements boost confidence."""
        exp = ConfidenceExplainer.explain_step_confidence(
            step_confidence=0.8,
            has_measurements=True,
            has_alternatives=False,
            has_dependencies=False,
            uncertainty_count=0,
            operation_type="analysis",
        )

        assert "measurements" in str(exp.boosting_factors).lower()
        assert "measurements_present" in exp.confidence_factors

    def test_alternatives_boost(self):
        """Test alternatives considered boost confidence."""
        exp = ConfidenceExplainer.explain_step_confidence(
            step_confidence=0.8,
            has_measurements=False,
            has_alternatives=True,
            has_dependencies=False,
            uncertainty_count=0,
            operation_type="decision",
        )

        assert "alternatives" in str(exp.boosting_factors).lower()

    def test_decision_without_alternatives_limited(self):
        """Test decision without alternatives is flagged."""
        exp = ConfidenceExplainer.explain_step_confidence(
            step_confidence=0.8,
            has_measurements=False,
            has_alternatives=False,
            has_dependencies=False,
            uncertainty_count=0,
            operation_type="decision",
        )

        assert any("alternative" in f.lower() for f in exp.limiting_factors)

    def test_dependencies_boost(self):
        """Test dependencies boost confidence."""
        exp = ConfidenceExplainer.explain_step_confidence(
            step_confidence=0.8,
            has_measurements=False,
            has_alternatives=False,
            has_dependencies=True,
            uncertainty_count=0,
            operation_type="analysis",
        )

        assert "dependency_chain" in exp.confidence_factors

    def test_uncertainty_reduces(self):
        """Test uncertainty sources reduce confidence."""
        exp = ConfidenceExplainer.explain_step_confidence(
            step_confidence=0.8,
            has_measurements=False,
            has_alternatives=False,
            has_dependencies=False,
            uncertainty_count=3,
            operation_type="analysis",
        )

        assert any("uncertainty" in f.lower() for f in exp.limiting_factors)

    def test_measurement_operation_boost(self):
        """Test measurement operations get boost."""
        exp = ConfidenceExplainer.explain_step_confidence(
            step_confidence=0.8,
            has_measurements=True,
            has_alternatives=False,
            has_dependencies=False,
            uncertainty_count=0,
            operation_type="measurement",
        )

        assert "measurement_operation" in exp.confidence_factors
        assert exp.confidence_factors["measurement_operation"] > 0

    def test_estimation_operation_penalty(self):
        """Test estimation operations get penalty."""
        exp = ConfidenceExplainer.explain_step_confidence(
            step_confidence=0.8,
            has_measurements=False,
            has_alternatives=False,
            has_dependencies=False,
            uncertainty_count=0,
            operation_type="estimation",
        )

        assert "estimation_operation" in exp.confidence_factors
        assert exp.confidence_factors["estimation_operation"] < 0

    def test_suggestions_generated(self):
        """Test improvement suggestions are generated."""
        exp = ConfidenceExplainer.explain_step_confidence(
            step_confidence=0.6,
            has_measurements=False,
            has_alternatives=False,
            has_dependencies=False,
            uncertainty_count=2,
            operation_type="decision",
        )

        assert len(exp.improvement_suggestions) > 0


class TestConfidenceExplainerExplainOverallConfidence:
    """Tests for ConfidenceExplainer.explain_overall_confidence."""

    def test_empty_steps(self):
        """Test with empty step confidences."""
        exp = ConfidenceExplainer.explain_overall_confidence(
            overall_confidence=0.8,
            step_confidences=[],
            methodology="weighted_average",
        )

        assert exp.confidence == 0.8
        assert len(exp.limiting_factors) > 0

    def test_weakest_link_methodology(self):
        """Test weakest link methodology explanation."""
        exp = ConfidenceExplainer.explain_overall_confidence(
            overall_confidence=0.6,
            step_confidences=[0.9, 0.6, 0.85],
            methodology="weakest_critical_link",
        )

        assert "weakest" in exp.confidence_factors["methodology"].lower()

    def test_weighted_average_methodology(self):
        """Test weighted average methodology explanation."""
        exp = ConfidenceExplainer.explain_overall_confidence(
            overall_confidence=0.8,
            step_confidences=[0.8, 0.82, 0.78],
            methodology="weighted_average",
        )

        assert "weighted" in exp.confidence_factors["methodology"].lower()

    def test_low_weakest_link_flagged(self):
        """Test low weakest link is flagged."""
        exp = ConfidenceExplainer.explain_overall_confidence(
            overall_confidence=0.5,
            step_confidences=[0.9, 0.5, 0.85],
            methodology="weakest_critical_link",
        )

        assert any("weakest" in f.lower() for f in exp.limiting_factors)

    def test_high_variance_flagged(self):
        """Test high variance is flagged."""
        exp = ConfidenceExplainer.explain_overall_confidence(
            overall_confidence=0.7,
            step_confidences=[0.3, 0.9, 0.5, 0.95],
            methodology="weighted_average",
        )

        # Variance should be detected
        # variance = mean((0.3-0.6625)^2 + (0.9-0.6625)^2 + ...) = high
        assert (
            "variance" in str(exp.limiting_factors).lower()
            or "low_confidence_steps" in exp.confidence_factors
        )

    def test_low_confidence_steps_counted(self):
        """Test low confidence steps are counted."""
        exp = ConfidenceExplainer.explain_overall_confidence(
            overall_confidence=0.7,
            step_confidences=[0.6, 0.65, 0.9, 0.85],
            methodology="weighted_average",
        )

        assert "low_confidence_steps" in exp.confidence_factors

    def test_high_confidence_steps_boost(self):
        """Test many high confidence steps boost."""
        exp = ConfidenceExplainer.explain_overall_confidence(
            overall_confidence=0.92,
            step_confidences=[0.95, 0.92, 0.91, 0.93],
            methodology="weighted_average",
        )

        assert any("high confidence" in f.lower() for f in exp.boosting_factors)

    def test_consistent_quality_boost(self):
        """Test consistent high quality boosts."""
        exp = ConfidenceExplainer.explain_overall_confidence(
            overall_confidence=0.85,
            step_confidences=[0.85, 0.87, 0.83, 0.88],
            methodology="weighted_average",
        )

        assert "consistent_quality" in exp.confidence_factors

    def test_critical_path_noted(self):
        """Test critical path analysis is noted."""
        exp = ConfidenceExplainer.explain_overall_confidence(
            overall_confidence=0.8,
            step_confidences=[0.8, 0.85, 0.75],
            methodology="weakest_critical_link",
            critical_steps=[1, 3],
        )

        assert "critical_path_focused" in exp.confidence_factors


class TestConfidenceExplainerGenerateFactorBreakdown:
    """Tests for ConfidenceExplainer._generate_factor_breakdown."""

    def test_empty_factors(self):
        """Test with empty factors."""
        result = ConfidenceExplainer._generate_factor_breakdown({})

        assert "No detailed factor" in result

    def test_numeric_factors(self):
        """Test numeric factors formatted."""
        result = ConfidenceExplainer._generate_factor_breakdown(
            {"base": 0.85, "bonus": 0.05, "penalty": -0.1}
        )

        assert "base: +0.850" in result
        assert "bonus: +0.050" in result
        assert "penalty: -0.100" in result

    def test_string_factors(self):
        """Test string factors included."""
        result = ConfidenceExplainer._generate_factor_breakdown(
            {"methodology": "weakest_link"}
        )

        assert "methodology: weakest_link" in result

    def test_multiple_factors_separated(self):
        """Test multiple factors separated by pipe."""
        result = ConfidenceExplainer._generate_factor_breakdown({"a": 0.5, "b": 0.3})

        assert " | " in result


class TestConfidenceExplainerCompareConfidences:
    """Tests for ConfidenceExplainer.compare_confidences."""

    def test_improved_confidence(self):
        """Test detecting improved confidence."""
        exp1 = ConfidenceExplanation(
            confidence=0.7,
            confidence_factors={"base": 0.7},
        )
        exp2 = ConfidenceExplanation(
            confidence=0.85,
            confidence_factors={"base": 0.7, "bonus": 0.15},
        )

        result = ConfidenceExplainer.compare_confidences(0.7, exp1, 0.85, exp2)

        assert result["direction"] == "improved"
        assert result["confidence_difference"] > 0

    def test_decreased_confidence(self):
        """Test detecting decreased confidence."""
        exp1 = ConfidenceExplanation(
            confidence=0.85,
            confidence_factors={"base": 0.85},
        )
        exp2 = ConfidenceExplanation(
            confidence=0.6,
            confidence_factors={"base": 0.85, "penalty": -0.25},
        )

        result = ConfidenceExplainer.compare_confidences(0.85, exp1, 0.6, exp2)

        assert result["direction"] == "decreased"
        assert result["confidence_difference"] < 0

    def test_unchanged_confidence(self):
        """Test detecting unchanged confidence."""
        exp1 = ConfidenceExplanation(
            confidence=0.8,
            confidence_factors={"base": 0.8},
        )
        exp2 = ConfidenceExplanation(
            confidence=0.8,
            confidence_factors={"base": 0.8},
        )

        result = ConfidenceExplainer.compare_confidences(0.8, exp1, 0.8, exp2)

        assert result["direction"] == "unchanged"
        assert result["confidence_difference"] == 0.0

    def test_new_factors_detected(self):
        """Test new factors are detected."""
        exp1 = ConfidenceExplanation(
            confidence=0.7,
            confidence_factors={"base": 0.7},
        )
        exp2 = ConfidenceExplanation(
            confidence=0.85,
            confidence_factors={"base": 0.7, "new_factor": 0.15},
        )

        result = ConfidenceExplainer.compare_confidences(0.7, exp1, 0.85, exp2)

        assert "new_factor" in result["new_factors"]

    def test_removed_factors_detected(self):
        """Test removed factors are detected."""
        exp1 = ConfidenceExplanation(
            confidence=0.85,
            confidence_factors={"base": 0.7, "bonus": 0.15},
        )
        exp2 = ConfidenceExplanation(
            confidence=0.7,
            confidence_factors={"base": 0.7},
        )

        result = ConfidenceExplainer.compare_confidences(0.85, exp1, 0.7, exp2)

        assert "bonus" in result["removed_factors"]

    def test_changed_factors_detected(self):
        """Test changed factors are detected."""
        exp1 = ConfidenceExplanation(
            confidence=0.7,
            confidence_factors={"base": 0.7, "adjustment": 0.0},
        )
        exp2 = ConfidenceExplanation(
            confidence=0.8,
            confidence_factors={"base": 0.7, "adjustment": 0.1},
        )

        result = ConfidenceExplainer.compare_confidences(0.7, exp1, 0.8, exp2)

        assert "adjustment" in result["changed_factors"]
        assert result["changed_factors"]["adjustment"]["change"] == pytest.approx(
            0.1, abs=0.01
        )

    def test_small_changes_ignored(self):
        """Test small changes (< 0.01) are ignored."""
        exp1 = ConfidenceExplanation(
            confidence=0.8,
            confidence_factors={"base": 0.800},
        )
        exp2 = ConfidenceExplanation(
            confidence=0.8,
            confidence_factors={"base": 0.805},  # Only 0.005 change
        )

        result = ConfidenceExplainer.compare_confidences(0.8, exp1, 0.8, exp2)

        assert "base" not in result["changed_factors"]

    def test_percentage_calculation(self):
        """Test percentage difference calculation."""
        exp1 = ConfidenceExplanation(confidence=0.5, confidence_factors={})
        exp2 = ConfidenceExplanation(confidence=0.75, confidence_factors={})

        result = ConfidenceExplainer.compare_confidences(0.5, exp1, 0.75, exp2)

        # 0.25 increase from 0.5 is 50%
        assert result["difference_percentage"] == pytest.approx(50.0, abs=0.1)

    def test_zero_division_handling(self):
        """Test handles zero confidence gracefully."""
        exp1 = ConfidenceExplanation(confidence=0.0, confidence_factors={})
        exp2 = ConfidenceExplanation(confidence=0.5, confidence_factors={})

        result = ConfidenceExplainer.compare_confidences(0.0, exp1, 0.5, exp2)

        # Should not raise, percentage is 0
        assert result["difference_percentage"] == 0.0
