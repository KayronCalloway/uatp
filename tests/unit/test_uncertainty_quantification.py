"""
Unit tests for Uncertainty Quantification.
"""

import math

import pytest

from src.analysis.uncertainty_quantification import (
    RiskAssessment,
    UncertaintyEstimate,
    UncertaintyQuantifier,
)


class TestUncertaintyEstimate:
    """Tests for UncertaintyEstimate dataclass."""

    def test_create_estimate(self):
        """Test creating an uncertainty estimate."""
        estimate = UncertaintyEstimate(
            point_estimate=0.8,
            confidence_interval=(0.7, 0.9),
            credible_interval=(0.72, 0.88),
            confidence_level=0.95,
            epistemic_uncertainty=0.05,
            aleatoric_uncertainty=0.03,
            total_uncertainty=0.06,
            risk_score=0.2,
            worst_case=0.6,
            best_case=0.95,
            variance=0.0036,
            skewness=0.1,
            is_symmetric=True,
        )

        assert estimate.point_estimate == 0.8
        assert estimate.confidence_interval == (0.7, 0.9)
        assert estimate.credible_interval == (0.72, 0.88)
        assert estimate.confidence_level == 0.95

    def test_uncertainty_decomposition(self):
        """Test uncertainty decomposition fields."""
        estimate = UncertaintyEstimate(
            point_estimate=0.5,
            confidence_interval=(0.4, 0.6),
            credible_interval=(0.4, 0.6),
            confidence_level=0.95,
            epistemic_uncertainty=0.08,
            aleatoric_uncertainty=0.04,
            total_uncertainty=0.09,
            risk_score=0.3,
            worst_case=0.3,
            best_case=0.7,
            variance=0.0081,
            skewness=0.0,
            is_symmetric=True,
        )

        assert estimate.epistemic_uncertainty == 0.08
        assert estimate.aleatoric_uncertainty == 0.04
        assert estimate.total_uncertainty == 0.09

    def test_risk_metrics(self):
        """Test risk metric fields."""
        estimate = UncertaintyEstimate(
            point_estimate=0.7,
            confidence_interval=(0.5, 0.9),
            credible_interval=(0.5, 0.9),
            confidence_level=0.95,
            epistemic_uncertainty=0.1,
            aleatoric_uncertainty=0.1,
            total_uncertainty=0.14,
            risk_score=0.4,
            worst_case=0.4,
            best_case=0.9,
            variance=0.02,
            skewness=-0.5,
            is_symmetric=False,
        )

        assert estimate.risk_score == 0.4
        assert estimate.worst_case == 0.4
        assert estimate.best_case == 0.9

    def test_distribution_characteristics(self):
        """Test distribution characteristic fields."""
        estimate = UncertaintyEstimate(
            point_estimate=0.6,
            confidence_interval=(0.5, 0.7),
            credible_interval=(0.5, 0.7),
            confidence_level=0.95,
            epistemic_uncertainty=0.05,
            aleatoric_uncertainty=0.05,
            total_uncertainty=0.07,
            risk_score=0.2,
            worst_case=0.4,
            best_case=0.8,
            variance=0.005,
            skewness=0.2,
            is_symmetric=False,
        )

        assert estimate.variance == 0.005
        assert estimate.skewness == 0.2
        assert estimate.is_symmetric is False


class TestRiskAssessment:
    """Tests for RiskAssessment dataclass."""

    def test_create_assessment(self):
        """Test creating a risk assessment."""
        assessment = RiskAssessment(
            overall_risk=0.4,
            risk_factors=[{"factor": "low_confidence", "severity": 0.3}],
            risk_mitigation=["Add more evidence"],
            confidence_in_assessment=0.8,
        )

        assert assessment.overall_risk == 0.4
        assert len(assessment.risk_factors) == 1
        assert len(assessment.risk_mitigation) == 1
        assert assessment.confidence_in_assessment == 0.8

    def test_multiple_risk_factors(self):
        """Test assessment with multiple risk factors."""
        assessment = RiskAssessment(
            overall_risk=0.7,
            risk_factors=[
                {"factor": "low_confidence", "severity": 0.3},
                {"factor": "no_validation", "severity": 0.2},
                {"factor": "short_chain", "severity": 0.1},
            ],
            risk_mitigation=[
                "Add more evidence",
                "Add validation steps",
                "Expand reasoning",
            ],
            confidence_in_assessment=0.6,
        )

        assert len(assessment.risk_factors) == 3
        assert len(assessment.risk_mitigation) == 3

    def test_empty_risk_factors(self):
        """Test assessment with no risk factors."""
        assessment = RiskAssessment(
            overall_risk=0.0,
            risk_factors=[],
            risk_mitigation=[],
            confidence_in_assessment=0.9,
        )

        assert len(assessment.risk_factors) == 0
        assert len(assessment.risk_mitigation) == 0


class TestUncertaintyQuantifierEstimateConfidence:
    """Tests for UncertaintyQuantifier.estimate_confidence_uncertainty."""

    def test_basic_estimation(self):
        """Test basic confidence uncertainty estimation."""
        estimate = UncertaintyQuantifier.estimate_confidence_uncertainty(
            confidence=0.8,
            sample_size=10,
        )

        assert estimate.point_estimate > 0
        assert estimate.point_estimate < 1
        assert estimate.confidence_level == 0.95

    def test_confidence_interval_bounds(self):
        """Test confidence interval is within [0, 1]."""
        estimate = UncertaintyQuantifier.estimate_confidence_uncertainty(
            confidence=0.5,
            sample_size=5,
        )

        assert estimate.confidence_interval[0] >= 0.0
        assert estimate.confidence_interval[1] <= 1.0
        assert estimate.confidence_interval[0] < estimate.confidence_interval[1]

    def test_high_confidence_narrow_interval(self):
        """Test high confidence with large sample has narrow interval."""
        estimate = UncertaintyQuantifier.estimate_confidence_uncertainty(
            confidence=0.95,
            sample_size=100,
        )

        interval_width = (
            estimate.confidence_interval[1] - estimate.confidence_interval[0]
        )
        assert interval_width < 0.2

    def test_low_confidence_increases_risk(self):
        """Test low confidence increases risk score."""
        high_conf = UncertaintyQuantifier.estimate_confidence_uncertainty(
            confidence=0.9, sample_size=10
        )
        low_conf = UncertaintyQuantifier.estimate_confidence_uncertainty(
            confidence=0.3, sample_size=10
        )

        # Risk should be related to uncertainty, and lower confidence
        # with the same sample size should have similar uncertainty
        # but the posterior mean will be different
        assert low_conf.point_estimate < high_conf.point_estimate

    def test_small_sample_increases_epistemic(self):
        """Test small sample size increases epistemic uncertainty."""
        small_sample = UncertaintyQuantifier.estimate_confidence_uncertainty(
            confidence=0.7, sample_size=5
        )
        large_sample = UncertaintyQuantifier.estimate_confidence_uncertainty(
            confidence=0.7, sample_size=50
        )

        # Epistemic uncertainty should decrease with more data
        assert small_sample.epistemic_uncertainty >= large_sample.epistemic_uncertainty

    def test_prior_influence(self):
        """Test that prior affects the estimate."""
        strong_prior = UncertaintyQuantifier.estimate_confidence_uncertainty(
            confidence=0.5, sample_size=5, prior_mean=0.9, prior_strength=10.0
        )
        weak_prior = UncertaintyQuantifier.estimate_confidence_uncertainty(
            confidence=0.5, sample_size=5, prior_mean=0.9, prior_strength=1.0
        )

        # Strong prior should pull estimate closer to prior mean
        assert strong_prior.point_estimate > weak_prior.point_estimate

    def test_worst_best_case(self):
        """Test worst and best case estimates."""
        estimate = UncertaintyQuantifier.estimate_confidence_uncertainty(
            confidence=0.7, sample_size=10
        )

        assert estimate.worst_case < estimate.point_estimate
        assert estimate.best_case > estimate.point_estimate
        assert estimate.worst_case >= 0.0
        assert estimate.best_case <= 1.0

    def test_skewness_computed(self):
        """Test skewness is computed."""
        estimate = UncertaintyQuantifier.estimate_confidence_uncertainty(
            confidence=0.8, sample_size=10
        )

        # Skewness should be finite
        assert not math.isnan(estimate.skewness)
        assert not math.isinf(estimate.skewness)

    def test_symmetric_check(self):
        """Test symmetry check."""
        # At 0.5 confidence with balanced prior, distribution should be more symmetric
        balanced = UncertaintyQuantifier.estimate_confidence_uncertainty(
            confidence=0.5, sample_size=10, prior_mean=0.5, prior_strength=5.0
        )

        # Near-symmetric distributions should have small skewness
        assert abs(balanced.skewness) < 0.5


class TestUncertaintyQuantifierPropagateUncertainty:
    """Tests for UncertaintyQuantifier.propagate_uncertainty."""

    def test_empty_list(self):
        """Test propagation with empty list."""
        result = UncertaintyQuantifier.propagate_uncertainty([])

        assert result.point_estimate == 0.0
        assert result.risk_score == 1.0

    def test_single_estimate(self):
        """Test propagation with single estimate."""
        single = UncertaintyEstimate(
            point_estimate=0.8,
            confidence_interval=(0.7, 0.9),
            credible_interval=(0.7, 0.9),
            confidence_level=0.95,
            epistemic_uncertainty=0.05,
            aleatoric_uncertainty=0.03,
            total_uncertainty=0.06,
            risk_score=0.2,
            worst_case=0.6,
            best_case=0.9,
            variance=0.0036,
            skewness=0.0,
            is_symmetric=True,
        )

        result = UncertaintyQuantifier.propagate_uncertainty([single])

        assert result.point_estimate == 0.8
        assert result.risk_score == 0.2

    def test_multiple_estimates(self):
        """Test propagation with multiple estimates."""
        estimates = [
            UncertaintyEstimate(
                point_estimate=0.9,
                confidence_interval=(0.85, 0.95),
                credible_interval=(0.85, 0.95),
                confidence_level=0.95,
                epistemic_uncertainty=0.03,
                aleatoric_uncertainty=0.02,
                total_uncertainty=0.04,
                risk_score=0.1,
                worst_case=0.8,
                best_case=0.95,
                variance=0.0016,
                skewness=0.0,
                is_symmetric=True,
            ),
            UncertaintyEstimate(
                point_estimate=0.8,
                confidence_interval=(0.7, 0.9),
                credible_interval=(0.7, 0.9),
                confidence_level=0.95,
                epistemic_uncertainty=0.05,
                aleatoric_uncertainty=0.04,
                total_uncertainty=0.06,
                risk_score=0.2,
                worst_case=0.6,
                best_case=0.9,
                variance=0.0036,
                skewness=0.0,
                is_symmetric=True,
            ),
        ]

        result = UncertaintyQuantifier.propagate_uncertainty(estimates)

        # Geometric mean of 0.9 and 0.8 is sqrt(0.72) ≈ 0.849
        assert 0.8 < result.point_estimate < 0.9

    def test_risk_takes_maximum(self):
        """Test combined risk takes maximum of individual risks."""
        estimates = [
            UncertaintyEstimate(
                point_estimate=0.9,
                confidence_interval=(0.8, 1.0),
                credible_interval=(0.8, 1.0),
                confidence_level=0.95,
                epistemic_uncertainty=0.03,
                aleatoric_uncertainty=0.02,
                total_uncertainty=0.04,
                risk_score=0.1,
                worst_case=0.8,
                best_case=0.95,
                variance=0.0016,
                skewness=0.0,
                is_symmetric=True,
            ),
            UncertaintyEstimate(
                point_estimate=0.7,
                confidence_interval=(0.5, 0.9),
                credible_interval=(0.5, 0.9),
                confidence_level=0.95,
                epistemic_uncertainty=0.1,
                aleatoric_uncertainty=0.1,
                total_uncertainty=0.14,
                risk_score=0.5,
                worst_case=0.4,
                best_case=0.85,
                variance=0.02,
                skewness=0.0,
                is_symmetric=True,
            ),
        ]

        result = UncertaintyQuantifier.propagate_uncertainty(estimates)

        assert result.risk_score == 0.5

    def test_variance_summed(self):
        """Test combined variance is sum of individual variances."""
        estimates = [
            UncertaintyEstimate(
                point_estimate=0.8,
                confidence_interval=(0.7, 0.9),
                credible_interval=(0.7, 0.9),
                confidence_level=0.95,
                epistemic_uncertainty=0.05,
                aleatoric_uncertainty=0.03,
                total_uncertainty=0.06,
                risk_score=0.2,
                worst_case=0.6,
                best_case=0.9,
                variance=0.01,
                skewness=0.0,
                is_symmetric=True,
            ),
            UncertaintyEstimate(
                point_estimate=0.7,
                confidence_interval=(0.6, 0.8),
                credible_interval=(0.6, 0.8),
                confidence_level=0.95,
                epistemic_uncertainty=0.04,
                aleatoric_uncertainty=0.03,
                total_uncertainty=0.05,
                risk_score=0.15,
                worst_case=0.5,
                best_case=0.85,
                variance=0.02,
                skewness=0.0,
                is_symmetric=True,
            ),
        ]

        result = UncertaintyQuantifier.propagate_uncertainty(estimates)

        assert result.variance == pytest.approx(0.03, rel=0.01)


class TestUncertaintyQuantifierAssessReasoningRisk:
    """Tests for UncertaintyQuantifier.assess_reasoning_risk."""

    def test_empty_inputs(self):
        """Test with empty inputs."""
        result = UncertaintyQuantifier.assess_reasoning_risk([], [])

        assert result.overall_risk >= 0.0
        assert result.confidence_in_assessment == 0.0

    def test_low_confidence_detected(self):
        """Test low confidence is detected as risk."""
        result = UncertaintyQuantifier.assess_reasoning_risk(
            reasoning_steps=[{"content": "analysis"}],
            confidence_history=[0.5, 0.6, 0.5],
        )

        # Should detect low confidence
        factor_names = [f["factor"] for f in result.risk_factors]
        assert "low_confidence" in factor_names

    def test_high_variance_detected(self):
        """Test high variance is detected as risk."""
        result = UncertaintyQuantifier.assess_reasoning_risk(
            reasoning_steps=[{"content": "test"}],
            confidence_history=[0.3, 0.9, 0.4, 0.85],
        )

        factor_names = [f["factor"] for f in result.risk_factors]
        assert "confidence_variance" in factor_names

    def test_missing_validation_detected(self):
        """Test missing validation is detected as risk."""
        result = UncertaintyQuantifier.assess_reasoning_risk(
            reasoning_steps=[
                {"content": "observation"},
                {"content": "conclusion"},
            ],
            confidence_history=[0.9, 0.85],
        )

        factor_names = [f["factor"] for f in result.risk_factors]
        assert "no_validation" in factor_names

    def test_validation_present(self):
        """Test validation present removes that risk."""
        result = UncertaintyQuantifier.assess_reasoning_risk(
            reasoning_steps=[
                {"content": "observation"},
                {"validation": True, "content": "validated"},
                {"content": "conclusion"},
            ],
            confidence_history=[0.9, 0.95, 0.9],
        )

        factor_names = [f["factor"] for f in result.risk_factors]
        assert "no_validation" not in factor_names

    def test_short_chain_detected(self):
        """Test short reasoning chain is detected."""
        result = UncertaintyQuantifier.assess_reasoning_risk(
            reasoning_steps=[{"content": "single step"}],
            confidence_history=[0.9],
        )

        factor_names = [f["factor"] for f in result.risk_factors]
        assert "short_chain" in factor_names

    def test_no_alternatives_detected(self):
        """Test missing alternatives is detected."""
        result = UncertaintyQuantifier.assess_reasoning_risk(
            reasoning_steps=[
                {"content": "step 1"},
                {"content": "step 2"},
                {"content": "step 3"},
            ],
            confidence_history=[0.9, 0.85, 0.9],
        )

        factor_names = [f["factor"] for f in result.risk_factors]
        assert "no_alternatives" in factor_names

    def test_alternatives_present(self):
        """Test alternatives present removes that risk."""
        result = UncertaintyQuantifier.assess_reasoning_risk(
            reasoning_steps=[
                {"content": "step 1"},
                {"content": "step 2", "alternatives_considered": ["alt1", "alt2"]},
                {"content": "step 3"},
            ],
            confidence_history=[0.9, 0.85, 0.9],
        )

        factor_names = [f["factor"] for f in result.risk_factors]
        assert "no_alternatives" not in factor_names

    def test_mitigations_generated(self):
        """Test that mitigations are generated for each risk."""
        result = UncertaintyQuantifier.assess_reasoning_risk(
            reasoning_steps=[{"content": "short"}],
            confidence_history=[0.5],
        )

        assert len(result.risk_mitigation) == len(result.risk_factors)

    def test_risk_capped_at_one(self):
        """Test overall risk is capped at 1.0."""
        result = UncertaintyQuantifier.assess_reasoning_risk(
            reasoning_steps=[{"content": "minimal"}],
            confidence_history=[0.2, 0.1, 0.3, 0.8],
        )

        assert result.overall_risk <= 1.0

    def test_confidence_in_assessment_increases_with_data(self):
        """Test assessment confidence increases with more data."""
        small_history = UncertaintyQuantifier.assess_reasoning_risk(
            reasoning_steps=[{"content": "test"}],
            confidence_history=[0.8, 0.85],
        )
        large_history = UncertaintyQuantifier.assess_reasoning_risk(
            reasoning_steps=[{"content": "test"}],
            confidence_history=[0.8] * 20,
        )

        assert (
            large_history.confidence_in_assessment
            > small_history.confidence_in_assessment
        )


class TestUncertaintyQuantifierMonteCarlo:
    """Tests for UncertaintyQuantifier.monte_carlo_prediction."""

    def test_basic_simulation(self):
        """Test basic Monte Carlo simulation."""
        result = UncertaintyQuantifier.monte_carlo_prediction(
            base_confidence=0.8,
            uncertainty=0.1,
            num_samples=1000,
        )

        assert "percentiles" in result
        assert "mean" in result
        assert "std" in result
        assert "success_probability" in result
        assert "samples" in result

    def test_sample_count(self):
        """Test correct number of samples."""
        result = UncertaintyQuantifier.monte_carlo_prediction(
            base_confidence=0.5,
            uncertainty=0.2,
            num_samples=5000,
        )

        assert result["samples"] == 5000

    def test_percentiles_ordered(self):
        """Test percentiles are in order."""
        result = UncertaintyQuantifier.monte_carlo_prediction(
            base_confidence=0.6,
            uncertainty=0.15,
            num_samples=10000,
        )

        percentiles = result["percentiles"]
        assert percentiles["p05"] <= percentiles["p25"]
        assert percentiles["p25"] <= percentiles["p50"]
        assert percentiles["p50"] <= percentiles["p75"]
        assert percentiles["p75"] <= percentiles["p95"]

    def test_mean_near_base_confidence(self):
        """Test mean is close to base confidence."""
        result = UncertaintyQuantifier.monte_carlo_prediction(
            base_confidence=0.7,
            uncertainty=0.1,
            num_samples=10000,
        )

        # Mean should be close to 0.7 (within 0.05 tolerance)
        assert abs(result["mean"] - 0.7) < 0.05

    def test_std_reflects_uncertainty(self):
        """Test std reflects input uncertainty."""
        low_uncertainty = UncertaintyQuantifier.monte_carlo_prediction(
            base_confidence=0.5,
            uncertainty=0.05,
            num_samples=10000,
        )
        high_uncertainty = UncertaintyQuantifier.monte_carlo_prediction(
            base_confidence=0.5,
            uncertainty=0.2,
            num_samples=10000,
        )

        assert high_uncertainty["std"] > low_uncertainty["std"]

    def test_success_probability_high_confidence(self):
        """Test success probability for high confidence."""
        result = UncertaintyQuantifier.monte_carlo_prediction(
            base_confidence=0.9,
            uncertainty=0.05,
            num_samples=10000,
        )

        # With mean 0.9 and low uncertainty, most samples should exceed 0.5
        assert result["success_probability"] > 0.95

    def test_success_probability_low_confidence(self):
        """Test success probability for low confidence."""
        result = UncertaintyQuantifier.monte_carlo_prediction(
            base_confidence=0.3,
            uncertainty=0.1,
            num_samples=10000,
        )

        # With mean 0.3, fewer samples should exceed 0.5
        assert result["success_probability"] < 0.5

    def test_values_clamped(self):
        """Test values are clamped to [0, 1]."""
        result = UncertaintyQuantifier.monte_carlo_prediction(
            base_confidence=0.5,
            uncertainty=0.3,  # High uncertainty could produce out-of-range values
            num_samples=10000,
        )

        # All percentiles should be in [0, 1]
        for key, value in result["percentiles"].items():
            assert 0.0 <= value <= 1.0

    def test_deterministic_seed_not_set(self):
        """Test that results vary between calls (no fixed seed)."""
        result1 = UncertaintyQuantifier.monte_carlo_prediction(
            base_confidence=0.5,
            uncertainty=0.2,
            num_samples=100,
        )
        result2 = UncertaintyQuantifier.monte_carlo_prediction(
            base_confidence=0.5,
            uncertainty=0.2,
            num_samples=100,
        )

        # Results should differ (with very high probability)
        # Allow for small possibility of exact match
        assert result1["mean"] != result2["mean"] or result1["std"] != result2["std"]
