"""
Unit tests for Calibration.
"""

import pytest

from src.analysis.calibration import (
    CalibrationMetrics,
    CalibrationRecommendation,
    ConfidenceCalibrator,
)


class TestCalibrationMetrics:
    """Tests for CalibrationMetrics dataclass."""

    def test_create_metrics(self):
        """Test creating calibration metrics."""
        metrics = CalibrationMetrics(
            expected_calibration_error=0.05,
            max_calibration_error=0.1,
            brier_score=0.08,
            reliability_by_bucket={0.5: {"accuracy": 0.48, "calibration_error": 0.02}},
            sample_size=100,
        )

        assert metrics.expected_calibration_error == 0.05
        assert metrics.max_calibration_error == 0.1
        assert metrics.sample_size == 100


class TestCalibrationRecommendation:
    """Tests for CalibrationRecommendation dataclass."""

    def test_create_recommendation(self):
        """Test creating a calibration recommendation."""
        rec = CalibrationRecommendation(
            domain="general",
            confidence_bucket=0.8,
            current_error=0.1,
            recommended_adjustment=-0.05,
            confidence_level="high",
            sample_size=50,
        )

        assert rec.domain == "general"
        assert rec.confidence_bucket == 0.8
        assert rec.confidence_level == "high"


class TestConfidenceCalibratorConstants:
    """Tests for ConfidenceCalibrator constants."""

    def test_sample_thresholds_defined(self):
        """Test sample size thresholds are defined."""
        assert ConfidenceCalibrator.MIN_SAMPLES_HIGH_CONFIDENCE == 30
        assert ConfidenceCalibrator.MIN_SAMPLES_MEDIUM_CONFIDENCE == 10
        assert ConfidenceCalibrator.MIN_SAMPLES_LOW_CONFIDENCE == 3


class TestConfidenceCalibratorCalculateCalibrationMetrics:
    """Tests for ConfidenceCalibrator.calculate_calibration_metrics."""

    def test_empty_inputs(self):
        """Test with empty inputs."""
        metrics = ConfidenceCalibrator.calculate_calibration_metrics([], [])

        assert metrics.expected_calibration_error == 0.0
        assert metrics.sample_size == 0

    def test_mismatched_lengths(self):
        """Test with mismatched prediction and outcome lengths."""
        with pytest.raises(ValueError, match="same length"):
            ConfidenceCalibrator.calculate_calibration_metrics([0.8, 0.9], [True])

    def test_perfect_calibration(self):
        """Test perfectly calibrated predictions."""
        # 10 predictions at 0.8, 8 succeed = perfect calibration
        predictions = [0.8] * 10
        outcomes = [True] * 8 + [False] * 2

        metrics = ConfidenceCalibrator.calculate_calibration_metrics(
            predictions, outcomes
        )

        assert metrics.expected_calibration_error < 0.01
        assert metrics.sample_size == 10

    def test_overconfident_predictions(self):
        """Test overconfident predictions."""
        # Predict 0.9 but only 50% succeed
        predictions = [0.9] * 10
        outcomes = [True] * 5 + [False] * 5

        metrics = ConfidenceCalibrator.calculate_calibration_metrics(
            predictions, outcomes
        )

        # Should have high calibration error
        assert metrics.expected_calibration_error > 0.3

    def test_underconfident_predictions(self):
        """Test underconfident predictions."""
        # Predict 0.5 but 90% succeed
        predictions = [0.5] * 10
        outcomes = [True] * 9 + [False] * 1

        metrics = ConfidenceCalibrator.calculate_calibration_metrics(
            predictions, outcomes
        )

        # Should have high calibration error
        assert metrics.expected_calibration_error > 0.3

    def test_brier_score_calculated(self):
        """Test Brier score is calculated."""
        predictions = [0.8, 0.6, 0.9]
        outcomes = [True, False, True]

        metrics = ConfidenceCalibrator.calculate_calibration_metrics(
            predictions, outcomes
        )

        assert 0.0 <= metrics.brier_score <= 1.0

    def test_reliability_by_bucket(self):
        """Test reliability by bucket is computed."""
        predictions = [0.1, 0.2, 0.8, 0.9]
        outcomes = [False, False, True, True]

        metrics = ConfidenceCalibrator.calculate_calibration_metrics(
            predictions, outcomes, num_buckets=10
        )

        assert len(metrics.reliability_by_bucket) > 0
        for bucket_data in metrics.reliability_by_bucket.values():
            assert "avg_confidence" in bucket_data
            assert "accuracy" in bucket_data
            assert "calibration_error" in bucket_data
            assert "sample_size" in bucket_data

    def test_mce_is_max_error(self):
        """Test MCE is maximum bucket error."""
        # Create predictions with different bucket errors
        predictions = [0.1] * 5 + [0.9] * 5
        outcomes = [False] * 5 + [False] * 5  # 0.9 bucket is very wrong

        metrics = ConfidenceCalibrator.calculate_calibration_metrics(
            predictions, outcomes
        )

        # MCE should be high due to 0.9 bucket
        assert metrics.max_calibration_error > 0.5

    def test_custom_bucket_count(self):
        """Test with custom bucket count."""
        predictions = [0.5] * 10
        outcomes = [True] * 5 + [False] * 5

        metrics = ConfidenceCalibrator.calculate_calibration_metrics(
            predictions, outcomes, num_buckets=5
        )

        assert metrics.sample_size == 10


class TestConfidenceCalibratorGenerateCalibrationRecommendations:
    """Tests for ConfidenceCalibrator.generate_calibration_recommendations."""

    def test_no_recommendations_below_threshold(self):
        """Test no recommendations for errors below threshold."""
        calibration_data = {
            ("general", 0.8): {
                "predicted_count": 100,
                "actual_success_count": 78,  # 0.78 vs 0.8 = 0.02 error
            }
        }

        recs = ConfidenceCalibrator.generate_calibration_recommendations(
            calibration_data, min_adjustment_threshold=0.05
        )

        assert len(recs) == 0

    def test_recommendations_for_large_errors(self):
        """Test recommendations generated for large errors."""
        calibration_data = {
            ("general", 0.8): {
                "predicted_count": 100,
                "actual_success_count": 60,  # 0.6 vs 0.8 = 0.2 error
            }
        }

        recs = ConfidenceCalibrator.generate_calibration_recommendations(
            calibration_data, min_adjustment_threshold=0.05
        )

        assert len(recs) == 1
        assert recs[0].current_error == pytest.approx(0.2, abs=0.01)

    def test_adjustment_is_conservative(self):
        """Test adjustment is conservative (50% of error)."""
        calibration_data = {
            ("general", 0.8): {
                "predicted_count": 100,
                "actual_success_count": 60,  # 0.2 error
            }
        }

        recs = ConfidenceCalibrator.generate_calibration_recommendations(
            calibration_data
        )

        # Should recommend -0.1 (50% of 0.2 error)
        assert recs[0].recommended_adjustment == pytest.approx(-0.1, abs=0.01)

    def test_confidence_level_high(self):
        """Test high confidence level for large samples."""
        calibration_data = {
            ("general", 0.8): {
                "predicted_count": 50,
                "actual_success_count": 30,
            }
        }

        recs = ConfidenceCalibrator.generate_calibration_recommendations(
            calibration_data
        )

        assert recs[0].confidence_level == "high"

    def test_confidence_level_medium(self):
        """Test medium confidence level."""
        calibration_data = {
            ("general", 0.8): {
                "predicted_count": 15,
                "actual_success_count": 10,
            }
        }

        recs = ConfidenceCalibrator.generate_calibration_recommendations(
            calibration_data
        )

        assert recs[0].confidence_level == "medium"

    def test_confidence_level_low(self):
        """Test low confidence level for small samples."""
        calibration_data = {
            ("general", 0.8): {
                "predicted_count": 5,
                "actual_success_count": 2,
            }
        }

        recs = ConfidenceCalibrator.generate_calibration_recommendations(
            calibration_data
        )

        assert recs[0].confidence_level == "low"

    def test_sorted_by_sample_size(self):
        """Test recommendations sorted by sample size."""
        calibration_data = {
            ("domain1", 0.8): {
                "predicted_count": 10,
                "actual_success_count": 5,
            },
            ("domain2", 0.7): {
                "predicted_count": 100,
                "actual_success_count": 50,
            },
            ("domain3", 0.9): {
                "predicted_count": 50,
                "actual_success_count": 40,
            },
        }

        recs = ConfidenceCalibrator.generate_calibration_recommendations(
            calibration_data
        )

        # Should be sorted by sample size (largest first)
        for i in range(len(recs) - 1):
            assert recs[i].sample_size >= recs[i + 1].sample_size

    def test_skips_zero_predicted_count(self):
        """Test skips entries with zero predicted count."""
        calibration_data = {
            ("general", 0.8): {
                "predicted_count": 0,
                "actual_success_count": 0,
            }
        }

        recs = ConfidenceCalibrator.generate_calibration_recommendations(
            calibration_data
        )

        assert len(recs) == 0

    def test_multiple_domains(self):
        """Test handles multiple domains."""
        calibration_data = {
            ("domain1", 0.8): {
                "predicted_count": 50,
                "actual_success_count": 30,
            },
            ("domain2", 0.8): {
                "predicted_count": 50,
                "actual_success_count": 35,
            },
        }

        recs = ConfidenceCalibrator.generate_calibration_recommendations(
            calibration_data
        )

        # Both have errors > 0.05 threshold, so should get recommendations
        domains = {r.domain for r in recs}
        assert len(recs) == 2
        assert "domain1" in domains or "domain2" in domains


class TestConfidenceCalibratorApplyCalibrationAdjustment:
    """Tests for ConfidenceCalibrator.apply_calibration_adjustment."""

    def test_no_adjustment(self):
        """Test no adjustment when not in map."""
        result = ConfidenceCalibrator.apply_calibration_adjustment(
            raw_confidence=0.8,
            domain="general",
            calibration_map={},
        )

        assert result == 0.8

    def test_apply_adjustment(self):
        """Test applies adjustment from map."""
        calibration_map = {("general", 0.8): -0.1}

        result = ConfidenceCalibrator.apply_calibration_adjustment(
            raw_confidence=0.8,
            domain="general",
            calibration_map=calibration_map,
        )

        assert result == pytest.approx(0.7, abs=0.001)

    def test_clamps_to_zero(self):
        """Test clamps result to minimum 0.0."""
        calibration_map = {("general", 0.1): -0.5}

        result = ConfidenceCalibrator.apply_calibration_adjustment(
            raw_confidence=0.1,
            domain="general",
            calibration_map=calibration_map,
        )

        assert result == 0.0

    def test_clamps_to_one(self):
        """Test clamps result to maximum 1.0."""
        calibration_map = {("general", 0.9): 0.5}

        result = ConfidenceCalibrator.apply_calibration_adjustment(
            raw_confidence=0.9,
            domain="general",
            calibration_map=calibration_map,
        )

        assert result == 1.0

    def test_rounds_to_bucket(self):
        """Test rounds confidence to bucket."""
        calibration_map = {("general", 0.8): -0.1}

        # 0.82 should round to 0.8 bucket
        result = ConfidenceCalibrator.apply_calibration_adjustment(
            raw_confidence=0.82,
            domain="general",
            calibration_map=calibration_map,
        )

        assert result == 0.72

    def test_domain_specific(self):
        """Test domain-specific adjustments."""
        calibration_map = {
            ("domain1", 0.8): -0.1,
            ("domain2", 0.8): 0.05,
        }

        result1 = ConfidenceCalibrator.apply_calibration_adjustment(
            raw_confidence=0.8,
            domain="domain1",
            calibration_map=calibration_map,
        )

        result2 = ConfidenceCalibrator.apply_calibration_adjustment(
            raw_confidence=0.8,
            domain="domain2",
            calibration_map=calibration_map,
        )

        assert result1 == pytest.approx(0.7, abs=0.001)
        assert result2 == pytest.approx(0.85, abs=0.001)


class TestConfidenceCalibratorGenerateReliabilityDiagramData:
    """Tests for ConfidenceCalibrator.generate_reliability_diagram_data."""

    def test_empty_inputs(self):
        """Test with empty inputs."""
        result = ConfidenceCalibrator.generate_reliability_diagram_data([], [])

        assert result["confidence"] == []
        assert result["accuracy"] == []
        assert result["sample_size"] == []

    def test_generates_plot_data(self):
        """Test generates data for plotting."""
        predictions = [0.1, 0.2, 0.8, 0.9]
        outcomes = [False, False, True, True]

        result = ConfidenceCalibrator.generate_reliability_diagram_data(
            predictions, outcomes
        )

        assert "confidence" in result
        assert "accuracy" in result
        assert "sample_size" in result
        assert len(result["confidence"]) == len(result["accuracy"])
        assert len(result["confidence"]) == len(result["sample_size"])

    def test_sorted_by_confidence(self):
        """Test data is sorted by confidence."""
        predictions = [0.9, 0.1, 0.5, 0.3]
        outcomes = [True, False, True, False]

        result = ConfidenceCalibrator.generate_reliability_diagram_data(
            predictions, outcomes
        )

        # Confidence levels should be in ascending order
        for i in range(len(result["confidence"]) - 1):
            assert result["confidence"][i] <= result["confidence"][i + 1]

    def test_accuracy_in_range(self):
        """Test accuracy values are in valid range."""
        predictions = [0.5] * 10
        outcomes = [True] * 5 + [False] * 5

        result = ConfidenceCalibrator.generate_reliability_diagram_data(
            predictions, outcomes
        )

        for acc in result["accuracy"]:
            assert 0.0 <= acc <= 1.0

    def test_sample_sizes_correct(self):
        """Test sample sizes are correct."""
        predictions = [0.1] * 5 + [0.9] * 3
        outcomes = [False] * 5 + [True] * 3

        result = ConfidenceCalibrator.generate_reliability_diagram_data(
            predictions, outcomes
        )

        # Should have 2 buckets with sizes 5 and 3
        assert sum(result["sample_size"]) == 8


class TestConfidenceCalibratorCalculateDomainSpecificCalibration:
    """Tests for ConfidenceCalibrator.calculate_domain_specific_calibration."""

    def test_empty_capsules(self):
        """Test with empty capsule list."""
        result = ConfidenceCalibrator.calculate_domain_specific_calibration([])

        assert result == {}

    def test_groups_by_domain(self):
        """Test groups capsules by domain."""
        capsules = [
            {
                "domain": "domain1",
                "confidence": 0.8,
                "outcome_success": True,
            },
            {
                "domain": "domain2",
                "confidence": 0.9,
                "outcome_success": True,
            },
            {
                "domain": "domain1",
                "confidence": 0.7,
                "outcome_success": False,
            },
        ]

        result = ConfidenceCalibrator.calculate_domain_specific_calibration(capsules)

        assert "domain1" in result
        assert "domain2" in result

    def test_calculates_metrics_per_domain(self):
        """Test calculates metrics for each domain."""
        capsules = [
            {
                "domain": "test",
                "confidence": 0.8,
                "outcome_success": True,
            }
        ] * 10

        result = ConfidenceCalibrator.calculate_domain_specific_calibration(capsules)

        assert "test" in result
        assert isinstance(result["test"], CalibrationMetrics)

    def test_filters_by_domain_list(self):
        """Test filters by provided domain list."""
        capsules = [
            {"domain": "domain1", "confidence": 0.8, "outcome_success": True},
            {"domain": "domain2", "confidence": 0.9, "outcome_success": True},
        ]

        result = ConfidenceCalibrator.calculate_domain_specific_calibration(
            capsules, domains=["domain1"]
        )

        assert "domain1" in result
        assert "domain2" not in result

    def test_handles_missing_fields(self):
        """Test handles capsules with missing fields."""
        capsules = [
            {"domain": "test"},  # Missing confidence and outcome
            {
                "domain": "test",
                "confidence": 0.8,
                "outcome_success": True,
            },
        ]

        result = ConfidenceCalibrator.calculate_domain_specific_calibration(capsules)

        # Should still process valid capsule
        assert "test" in result

    def test_default_domain(self):
        """Test uses default domain when not specified."""
        capsules = [
            {"confidence": 0.8, "outcome_success": True}  # No domain
        ]

        result = ConfidenceCalibrator.calculate_domain_specific_calibration(capsules)

        assert "general" in result


class TestConfidenceCalibratorCompareCalibrationOverTime:
    """Tests for ConfidenceCalibrator.compare_calibration_over_time."""

    def test_insufficient_data(self):
        """Test with insufficient data."""
        history = [
            {
                "timestamp": "2024-01-01",
                "metrics": CalibrationMetrics(
                    expected_calibration_error=0.1,
                    max_calibration_error=0.2,
                    brier_score=0.15,
                    reliability_by_bucket={},
                    sample_size=100,
                ),
            }
        ]

        result = ConfidenceCalibrator.compare_calibration_over_time(history)

        assert result["trend"] == "insufficient_data"

    def test_improving_trend(self):
        """Test detects improving trend."""
        history = [
            {
                "timestamp": "2024-01-01",
                "metrics": CalibrationMetrics(
                    expected_calibration_error=0.15,
                    max_calibration_error=0.2,
                    brier_score=0.15,
                    reliability_by_bucket={},
                    sample_size=100,
                ),
            },
            {
                "timestamp": "2024-02-01",
                "metrics": CalibrationMetrics(
                    expected_calibration_error=0.08,
                    max_calibration_error=0.15,
                    brier_score=0.1,
                    reliability_by_bucket={},
                    sample_size=100,
                ),
            },
        ]

        result = ConfidenceCalibrator.compare_calibration_over_time(history)

        assert result["trend"] == "improving"
        assert result["improvement"] > 0

    def test_degrading_trend(self):
        """Test detects degrading trend."""
        history = [
            {
                "timestamp": "2024-01-01",
                "metrics": CalibrationMetrics(
                    expected_calibration_error=0.05,
                    max_calibration_error=0.1,
                    brier_score=0.08,
                    reliability_by_bucket={},
                    sample_size=100,
                ),
            },
            {
                "timestamp": "2024-02-01",
                "metrics": CalibrationMetrics(
                    expected_calibration_error=0.15,
                    max_calibration_error=0.2,
                    brier_score=0.18,
                    reliability_by_bucket={},
                    sample_size=100,
                ),
            },
        ]

        result = ConfidenceCalibrator.compare_calibration_over_time(history)

        assert result["trend"] == "degrading"
        assert result["improvement"] < 0

    def test_stable_trend(self):
        """Test detects stable trend."""
        history = [
            {
                "timestamp": "2024-01-01",
                "metrics": CalibrationMetrics(
                    expected_calibration_error=0.1,
                    max_calibration_error=0.15,
                    brier_score=0.12,
                    reliability_by_bucket={},
                    sample_size=100,
                ),
            },
            {
                "timestamp": "2024-02-01",
                "metrics": CalibrationMetrics(
                    expected_calibration_error=0.105,
                    max_calibration_error=0.16,
                    brier_score=0.13,
                    reliability_by_bucket={},
                    sample_size=100,
                ),
            },
        ]

        result = ConfidenceCalibrator.compare_calibration_over_time(history)

        assert result["trend"] == "stable"

    def test_improvement_percentage(self):
        """Test calculates improvement percentage."""
        history = [
            {
                "timestamp": "2024-01-01",
                "metrics": CalibrationMetrics(
                    expected_calibration_error=0.2,
                    max_calibration_error=0.3,
                    brier_score=0.25,
                    reliability_by_bucket={},
                    sample_size=100,
                ),
            },
            {
                "timestamp": "2024-02-01",
                "metrics": CalibrationMetrics(
                    expected_calibration_error=0.1,
                    max_calibration_error=0.15,
                    brier_score=0.12,
                    reliability_by_bucket={},
                    sample_size=100,
                ),
            },
        ]

        result = ConfidenceCalibrator.compare_calibration_over_time(history)

        # 0.2 to 0.1 = 50% improvement
        assert result["improvement_percentage"] == pytest.approx(50.0, abs=1.0)

    def test_includes_measurement_count(self):
        """Test includes measurement count."""
        history = [
            {
                "timestamp": f"2024-{i:02d}-01",
                "metrics": CalibrationMetrics(
                    expected_calibration_error=0.1,
                    max_calibration_error=0.15,
                    brier_score=0.12,
                    reliability_by_bucket={},
                    sample_size=100,
                ),
            }
            for i in range(1, 6)
        ]

        result = ConfidenceCalibrator.compare_calibration_over_time(history)

        assert result["measurement_count"] == 5


class TestCalibrationIntegration:
    """Integration tests for calibration."""

    def test_full_calibration_workflow(self):
        """Test complete calibration workflow."""
        # 1. Calculate metrics
        predictions = [0.8] * 10 + [0.5] * 10
        outcomes = [True] * 6 + [False] * 4 + [True] * 5 + [False] * 5

        metrics = ConfidenceCalibrator.calculate_calibration_metrics(
            predictions, outcomes
        )

        assert metrics.sample_size == 20

        # 2. Generate recommendations
        calibration_data = {
            ("general", 0.8): {"predicted_count": 10, "actual_success_count": 6},
            ("general", 0.5): {"predicted_count": 10, "actual_success_count": 5},
        }

        recs = ConfidenceCalibrator.generate_calibration_recommendations(
            calibration_data
        )

        # 0.8 bucket: 0.6 actual vs 0.8 predicted = 0.2 error
        assert len(recs) > 0

        # 3. Apply adjustment
        calibration_map = {
            (rec.domain, rec.confidence_bucket): rec.recommended_adjustment
            for rec in recs
        }

        adjusted = ConfidenceCalibrator.apply_calibration_adjustment(
            raw_confidence=0.8,
            domain="general",
            calibration_map=calibration_map,
        )

        assert adjusted < 0.8  # Should be adjusted down

    def test_perfect_calibration_no_adjustments(self):
        """Test perfect calibration needs no adjustments."""
        # 80% confidence, 80% success
        predictions = [0.8] * 10
        outcomes = [True] * 8 + [False] * 2

        metrics = ConfidenceCalibrator.calculate_calibration_metrics(
            predictions, outcomes
        )

        assert metrics.expected_calibration_error < 0.05

        calibration_data = {
            ("general", 0.8): {"predicted_count": 10, "actual_success_count": 8}
        }

        recs = ConfidenceCalibrator.generate_calibration_recommendations(
            calibration_data
        )

        # Should not recommend adjustment for well-calibrated predictions
        assert len(recs) == 0
