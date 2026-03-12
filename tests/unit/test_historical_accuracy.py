"""
Unit tests for Historical Accuracy Tracking.
"""

import pytest

from src.analysis.historical_accuracy import (
    AccuracyMetrics,
    HistoricalAccuracyTracker,
    HistoricalDataPoint,
)


class TestHistoricalDataPoint:
    """Tests for HistoricalDataPoint dataclass."""

    def test_create_data_point(self):
        """Test creating a historical data point."""
        dp = HistoricalDataPoint(
            capsule_id="cap_123",
            predicted_probability_correct=0.85,
            actual_outcome="correct",
            actual_outcome_binary=1.0,
            prediction_timestamp="2024-01-01T10:00:00Z",
            outcome_timestamp="2024-01-01T12:00:00Z",
        )

        assert dp.capsule_id == "cap_123"
        assert dp.predicted_probability_correct == 0.85
        assert dp.actual_outcome_binary == 1.0

    def test_data_point_with_domain(self):
        """Test data point with domain."""
        dp = HistoricalDataPoint(
            capsule_id="cap_1",
            predicted_probability_correct=0.8,
            actual_outcome="correct",
            actual_outcome_binary=1.0,
            prediction_timestamp="2024-01-01T10:00:00Z",
            outcome_timestamp="2024-01-01T12:00:00Z",
            domain="healthcare",
        )

        assert dp.domain == "healthcare"

    def test_data_point_with_financial_impact(self):
        """Test data point with financial impact."""
        dp = HistoricalDataPoint(
            capsule_id="cap_1",
            predicted_probability_correct=0.8,
            actual_outcome="correct",
            actual_outcome_binary=1.0,
            prediction_timestamp="2024-01-01T10:00:00Z",
            outcome_timestamp="2024-01-01T12:00:00Z",
            financial_impact_predicted=1000.0,
            financial_impact_actual=950.0,
        )

        assert dp.financial_impact_predicted == 1000.0
        assert dp.financial_impact_actual == 950.0

    def test_partial_outcome(self):
        """Test partial outcome representation."""
        dp = HistoricalDataPoint(
            capsule_id="cap_1",
            predicted_probability_correct=0.8,
            actual_outcome="partial",
            actual_outcome_binary=0.5,
            prediction_timestamp="2024-01-01T10:00:00Z",
            outcome_timestamp="2024-01-01T12:00:00Z",
        )

        assert dp.actual_outcome == "partial"
        assert dp.actual_outcome_binary == 0.5


class TestAccuracyMetrics:
    """Tests for AccuracyMetrics dataclass."""

    def test_create_metrics(self):
        """Test creating accuracy metrics."""
        metrics = AccuracyMetrics(
            total_predictions=100,
            total_outcomes_recorded=95,
            coverage_rate=0.95,
            mean_predicted_confidence=0.82,
            mean_actual_accuracy=0.78,
            accuracy_gap=0.04,
            calibration_score=0.88,
            calibration_curve=[(0.8, 0.78), (0.9, 0.85)],
        )

        assert metrics.total_predictions == 100
        assert metrics.coverage_rate == 0.95
        assert metrics.calibration_score == 0.88

    def test_metrics_with_financial_data(self):
        """Test metrics with financial data."""
        metrics = AccuracyMetrics(
            total_predictions=50,
            total_outcomes_recorded=50,
            coverage_rate=1.0,
            mean_predicted_confidence=0.8,
            mean_actual_accuracy=0.75,
            accuracy_gap=0.05,
            calibration_score=0.9,
            calibration_curve=[],
            total_predicted_value=50000.0,
            total_actual_value=48000.0,
            value_prediction_error=2000.0,
        )

        assert metrics.total_predicted_value == 50000.0
        assert metrics.value_prediction_error == 2000.0


class TestHistoricalAccuracyTrackerInit:
    """Tests for HistoricalAccuracyTracker initialization."""

    def test_create_tracker_no_db(self):
        """Test creating tracker without database."""
        tracker = HistoricalAccuracyTracker()

        assert tracker.db is None
        assert tracker.cache == []

    def test_create_tracker_with_db(self):
        """Test creating tracker with database connection."""
        mock_db = object()
        tracker = HistoricalAccuracyTracker(database_connection=mock_db)

        assert tracker.db is mock_db


class TestHistoricalAccuracyTrackerQueryHistoricalData:
    """Tests for HistoricalAccuracyTracker.query_historical_data."""

    @pytest.mark.asyncio
    async def test_query_with_no_db_returns_cache(self):
        """Test query returns cache when no database."""
        tracker = HistoricalAccuracyTracker()
        tracker.cache = [
            HistoricalDataPoint(
                capsule_id="cap_1",
                predicted_probability_correct=0.8,
                actual_outcome="correct",
                actual_outcome_binary=1.0,
                prediction_timestamp="2024-01-01T10:00:00Z",
                outcome_timestamp="2024-01-01T12:00:00Z",
            )
        ]

        result = await tracker.query_historical_data()

        assert len(result) == 1
        assert result[0].capsule_id == "cap_1"

    @pytest.mark.asyncio
    async def test_query_with_filters(self):
        """Test query accepts filter parameters."""
        tracker = HistoricalAccuracyTracker()

        # Should not raise even with filters
        result = await tracker.query_historical_data(
            domain="test",
            min_confidence=0.5,
            max_confidence=0.9,
        )

        assert isinstance(result, list)


class TestHistoricalAccuracyTrackerCalculateAccuracyMetrics:
    """Tests for HistoricalAccuracyTracker.calculate_accuracy_metrics."""

    def test_empty_data(self):
        """Test with empty historical data."""
        tracker = HistoricalAccuracyTracker()

        metrics = tracker.calculate_accuracy_metrics([])

        assert metrics.total_predictions == 0
        assert metrics.total_outcomes_recorded == 0
        assert metrics.coverage_rate == 0.0

    def test_basic_metrics(self):
        """Test basic metric calculation."""
        tracker = HistoricalAccuracyTracker()
        data = [
            HistoricalDataPoint(
                capsule_id=f"cap_{i}",
                predicted_probability_correct=0.8,
                actual_outcome="correct",
                actual_outcome_binary=1.0,
                prediction_timestamp="2024-01-01T10:00:00Z",
                outcome_timestamp="2024-01-01T12:00:00Z",
            )
            for i in range(10)
        ]

        metrics = tracker.calculate_accuracy_metrics(data)

        assert metrics.total_predictions == 10
        assert metrics.total_outcomes_recorded == 10
        assert metrics.coverage_rate == 1.0

    def test_predicted_vs_actual(self):
        """Test predicted vs actual calculation."""
        tracker = HistoricalAccuracyTracker()
        data = [
            HistoricalDataPoint(
                capsule_id="cap_1",
                predicted_probability_correct=0.9,
                actual_outcome="correct",
                actual_outcome_binary=1.0,
                prediction_timestamp="2024-01-01T10:00:00Z",
                outcome_timestamp="2024-01-01T12:00:00Z",
            ),
            HistoricalDataPoint(
                capsule_id="cap_2",
                predicted_probability_correct=0.8,
                actual_outcome="incorrect",
                actual_outcome_binary=0.0,
                prediction_timestamp="2024-01-01T10:00:00Z",
                outcome_timestamp="2024-01-01T12:00:00Z",
            ),
        ]

        metrics = tracker.calculate_accuracy_metrics(data)

        # Mean predicted = (0.9 + 0.8) / 2 = 0.85
        # Mean actual = (1.0 + 0.0) / 2 = 0.5
        assert metrics.mean_predicted_confidence == pytest.approx(0.85, abs=0.01)
        assert metrics.mean_actual_accuracy == pytest.approx(0.5, abs=0.01)
        assert metrics.accuracy_gap == pytest.approx(0.35, abs=0.01)

    def test_calibration_curve(self):
        """Test calibration curve generation."""
        tracker = HistoricalAccuracyTracker()
        data = [
            HistoricalDataPoint(
                capsule_id=f"cap_{i}",
                predicted_probability_correct=0.5,
                actual_outcome="correct" if i % 2 == 0 else "incorrect",
                actual_outcome_binary=1.0 if i % 2 == 0 else 0.0,
                prediction_timestamp="2024-01-01T10:00:00Z",
                outcome_timestamp="2024-01-01T12:00:00Z",
            )
            for i in range(10)
        ]

        metrics = tracker.calculate_accuracy_metrics(data)

        assert len(metrics.calibration_curve) > 0

    def test_financial_metrics(self):
        """Test financial metrics calculation."""
        tracker = HistoricalAccuracyTracker()
        data = [
            HistoricalDataPoint(
                capsule_id=f"cap_{i}",
                predicted_probability_correct=0.8,
                actual_outcome="correct",
                actual_outcome_binary=1.0,
                prediction_timestamp="2024-01-01T10:00:00Z",
                outcome_timestamp="2024-01-01T12:00:00Z",
                financial_impact_predicted=1000.0,
                financial_impact_actual=950.0,
            )
            for i in range(5)
        ]

        metrics = tracker.calculate_accuracy_metrics(data)

        assert metrics.total_predicted_value == 5000.0
        assert metrics.total_actual_value == 4750.0
        assert metrics.value_prediction_error == 250.0

    def test_confidence_bins(self):
        """Test confidence bins are calculated."""
        tracker = HistoricalAccuracyTracker()
        data = [
            HistoricalDataPoint(
                capsule_id="cap_low",
                predicted_probability_correct=0.3,
                actual_outcome="correct",
                actual_outcome_binary=1.0,
                prediction_timestamp="2024-01-01T10:00:00Z",
                outcome_timestamp="2024-01-01T12:00:00Z",
            ),
            HistoricalDataPoint(
                capsule_id="cap_high",
                predicted_probability_correct=0.95,
                actual_outcome="correct",
                actual_outcome_binary=1.0,
                prediction_timestamp="2024-01-01T10:00:00Z",
                outcome_timestamp="2024-01-01T12:00:00Z",
            ),
        ]

        metrics = tracker.calculate_accuracy_metrics(data)

        assert metrics.confidence_bins is not None
        assert "0.0-0.5" in metrics.confidence_bins
        assert "0.9-1.0" in metrics.confidence_bins


class TestHistoricalAccuracyTrackerCalculateCalibrationCurve:
    """Tests for HistoricalAccuracyTracker._calculate_calibration_curve."""

    def test_empty_data(self):
        """Test with empty data."""
        tracker = HistoricalAccuracyTracker()

        result = tracker._calculate_calibration_curve([], [])

        assert result == []

    def test_bins_predictions(self):
        """Test bins predictions."""
        tracker = HistoricalAccuracyTracker()
        predicted = [0.1, 0.2, 0.8, 0.9]
        actual = [0.0, 0.0, 1.0, 1.0]

        result = tracker._calculate_calibration_curve(predicted, actual)

        assert len(result) > 0
        assert all(isinstance(point, tuple) for point in result)
        assert all(len(point) == 2 for point in result)

    def test_perfect_calibration(self):
        """Test perfect calibration curve."""
        tracker = HistoricalAccuracyTracker()
        # Perfectly calibrated: 0.8 confidence, 80% correct
        predicted = [0.8] * 10
        actual = [1.0] * 8 + [0.0] * 2

        result = tracker._calculate_calibration_curve(predicted, actual)

        # Should have points near diagonal
        if result:
            for pred, acc in result:
                assert abs(pred - acc) < 0.1


class TestHistoricalAccuracyTrackerCalculateExpectedCalibrationError:
    """Tests for HistoricalAccuracyTracker._calculate_expected_calibration_error."""

    def test_empty_curve(self):
        """Test with empty calibration curve."""
        tracker = HistoricalAccuracyTracker()

        result = tracker._calculate_expected_calibration_error([])

        assert result == 0.0

    def test_perfect_calibration_zero_error(self):
        """Test perfect calibration has zero error."""
        tracker = HistoricalAccuracyTracker()
        curve = [(0.5, 0.5), (0.8, 0.8), (0.9, 0.9)]

        result = tracker._calculate_expected_calibration_error(curve)

        assert result == 0.0

    def test_calculates_mean_error(self):
        """Test calculates mean absolute error."""
        tracker = HistoricalAccuracyTracker()
        curve = [(0.8, 0.6), (0.9, 0.7)]  # Errors: 0.2, 0.2

        result = tracker._calculate_expected_calibration_error(curve)

        assert result == pytest.approx(0.2, abs=0.01)


class TestHistoricalAccuracyTrackerCalculateConfidenceBins:
    """Tests for HistoricalAccuracyTracker._calculate_confidence_bins."""

    def test_empty_data(self):
        """Test with empty data."""
        tracker = HistoricalAccuracyTracker()

        result = tracker._calculate_confidence_bins([])

        # Should have all bins with count 0
        assert "0.0-0.5" in result
        assert result["0.0-0.5"]["count"] == 0

    def test_assigns_to_correct_bins(self):
        """Test assigns data to correct bins."""
        tracker = HistoricalAccuracyTracker()
        data = [
            HistoricalDataPoint(
                capsule_id="cap_low",
                predicted_probability_correct=0.3,
                actual_outcome="correct",
                actual_outcome_binary=1.0,
                prediction_timestamp="2024-01-01T10:00:00Z",
                outcome_timestamp="2024-01-01T12:00:00Z",
            ),
            HistoricalDataPoint(
                capsule_id="cap_mid",
                predicted_probability_correct=0.6,
                actual_outcome="correct",
                actual_outcome_binary=1.0,
                prediction_timestamp="2024-01-01T10:00:00Z",
                outcome_timestamp="2024-01-01T12:00:00Z",
            ),
            HistoricalDataPoint(
                capsule_id="cap_high",
                predicted_probability_correct=0.95,
                actual_outcome="correct",
                actual_outcome_binary=1.0,
                prediction_timestamp="2024-01-01T10:00:00Z",
                outcome_timestamp="2024-01-01T12:00:00Z",
            ),
        ]

        result = tracker._calculate_confidence_bins(data)

        assert result["0.0-0.5"]["count"] == 1
        assert result["0.5-0.7"]["count"] == 1
        assert result["0.9-1.0"]["count"] == 1

    def test_calculates_bin_statistics(self):
        """Test calculates statistics per bin."""
        tracker = HistoricalAccuracyTracker()
        data = [
            HistoricalDataPoint(
                capsule_id=f"cap_{i}",
                predicted_probability_correct=0.8,
                actual_outcome="correct" if i % 2 == 0 else "incorrect",
                actual_outcome_binary=1.0 if i % 2 == 0 else 0.0,
                prediction_timestamp="2024-01-01T10:00:00Z",
                outcome_timestamp="2024-01-01T12:00:00Z",
            )
            for i in range(10)
        ]

        result = tracker._calculate_confidence_bins(data)

        bin_0_7_0_9 = result["0.7-0.9"]
        assert bin_0_7_0_9["count"] == 10
        assert "mean_predicted" in bin_0_7_0_9
        assert "mean_actual" in bin_0_7_0_9
        assert "accuracy_gap" in bin_0_7_0_9


class TestHistoricalAccuracyTrackerGetCalibratedProbability:
    """Tests for HistoricalAccuracyTracker.get_calibrated_probability."""

    def test_no_historical_data(self):
        """Test with no historical data."""
        tracker = HistoricalAccuracyTracker()

        calibrated, interval = tracker.get_calibrated_probability(0.8)

        # No data, returns uncalibrated with high uncertainty
        assert calibrated == 0.8
        assert interval == 0.2

    def test_calibrates_based_on_similar(self):
        """Test calibrates based on similar predictions."""
        tracker = HistoricalAccuracyTracker()
        # Would need to test with actual database query
        # For now, test the no-data path
        calibrated, interval = tracker.get_calibrated_probability(0.7)

        assert 0.0 <= calibrated <= 1.0
        assert interval > 0


class TestHistoricalAccuracyTrackerGenerateActuarialReport:
    """Tests for HistoricalAccuracyTracker.generate_actuarial_report."""

    def test_insufficient_data(self):
        """Test report with insufficient data."""
        tracker = HistoricalAccuracyTracker()

        report = tracker.generate_actuarial_report()

        assert "error" in report
        assert report["minimum_required"] == 100

    def test_generates_report_structure(self):
        """Test generates report with expected structure."""
        tracker = HistoricalAccuracyTracker()

        report = tracker.generate_actuarial_report()

        # Current implementation always returns insufficient data
        # because it queries empty database
        assert "error" in report or "data_summary" in report

    def test_report_insufficient_data_message(self):
        """Test report returns proper error for insufficient data."""
        tracker = HistoricalAccuracyTracker()

        report = tracker.generate_actuarial_report()

        # Should indicate insufficient data
        assert "error" in report or "minimum_required" in report


class TestHistoricalAccuracyTrackerGenerateUnderwritingRecommendation:
    """Tests for HistoricalAccuracyTracker._generate_underwriting_recommendation."""

    def test_decline_insufficient_data(self):
        """Test declines with insufficient data."""
        tracker = HistoricalAccuracyTracker()
        metrics = AccuracyMetrics(
            total_predictions=50,
            total_outcomes_recorded=50,
            coverage_rate=1.0,
            mean_predicted_confidence=0.8,
            mean_actual_accuracy=0.8,
            accuracy_gap=0.0,
            calibration_score=0.95,
            calibration_curve=[],
        )

        rec = tracker._generate_underwriting_recommendation(metrics)

        assert rec["decision"] == "DECLINE"
        assert "Insufficient" in rec["reason"]

    def test_conditional_poor_calibration(self):
        """Test conditional approval for poor calibration."""
        tracker = HistoricalAccuracyTracker()
        metrics = AccuracyMetrics(
            total_predictions=150,
            total_outcomes_recorded=150,
            coverage_rate=1.0,
            mean_predicted_confidence=0.9,
            mean_actual_accuracy=0.7,
            accuracy_gap=0.2,
            calibration_score=0.75,  # Below 0.8 threshold
            calibration_curve=[],
        )

        rec = tracker._generate_underwriting_recommendation(metrics)

        assert rec["decision"] == "CONDITIONAL"
        assert "calibration" in rec["reason"].lower()

    def test_decline_low_accuracy(self):
        """Test declines for low actual accuracy."""
        tracker = HistoricalAccuracyTracker()
        metrics = AccuracyMetrics(
            total_predictions=150,
            total_outcomes_recorded=150,
            coverage_rate=1.0,
            mean_predicted_confidence=0.8,
            mean_actual_accuracy=0.65,  # Below 0.7 threshold
            accuracy_gap=0.15,
            calibration_score=0.85,
            calibration_curve=[],
        )

        rec = tracker._generate_underwriting_recommendation(metrics)

        assert rec["decision"] == "DECLINE"
        assert "accuracy" in rec["reason"].lower()

    def test_approve_good_metrics(self):
        """Test approves for good metrics."""
        tracker = HistoricalAccuracyTracker()
        metrics = AccuracyMetrics(
            total_predictions=150,
            total_outcomes_recorded=150,
            coverage_rate=1.0,
            mean_predicted_confidence=0.82,
            mean_actual_accuracy=0.80,
            accuracy_gap=0.02,
            calibration_score=0.92,
            calibration_curve=[],
        )

        rec = tracker._generate_underwriting_recommendation(metrics)

        assert rec["decision"] == "APPROVE"
        assert "suggested_premium_multiplier" in rec

    def test_premium_multiplier_for_conditional(self):
        """Test premium multiplier for conditional approval."""
        tracker = HistoricalAccuracyTracker()
        metrics = AccuracyMetrics(
            total_predictions=150,
            total_outcomes_recorded=150,
            coverage_rate=1.0,
            mean_predicted_confidence=0.9,
            mean_actual_accuracy=0.7,
            accuracy_gap=0.2,
            calibration_score=0.7,
            calibration_curve=[],
        )

        rec = tracker._generate_underwriting_recommendation(metrics)

        assert rec["decision"] == "CONDITIONAL"
        assert rec["suggested_premium_multiplier"] == 1.5


class TestHistoricalAccuracyIntegration:
    """Integration tests for historical accuracy tracking."""

    def test_full_workflow(self):
        """Test complete workflow from data to metrics."""
        tracker = HistoricalAccuracyTracker()

        # Populate cache with realistic data
        tracker.cache = [
            HistoricalDataPoint(
                capsule_id=f"cap_{i}",
                predicted_probability_correct=0.85,
                actual_outcome="correct" if i % 10 < 8 else "incorrect",
                actual_outcome_binary=1.0 if i % 10 < 8 else 0.0,
                prediction_timestamp="2024-01-01T10:00:00Z",
                outcome_timestamp="2024-01-01T12:00:00Z",
                domain="general",
                financial_impact_predicted=1000.0,
                financial_impact_actual=950.0 if i % 10 < 8 else -500.0,
            )
            for i in range(150)
        ]

        # Calculate metrics from cache
        metrics = tracker.calculate_accuracy_metrics(tracker.cache)

        assert metrics.total_predictions == 150
        assert metrics.mean_predicted_confidence > 0.8
        assert metrics.total_predicted_value is not None
        assert metrics.total_actual_value is not None

    def test_tracks_partial_outcomes(self):
        """Test handles partial outcomes."""
        tracker = HistoricalAccuracyTracker()
        data = [
            HistoricalDataPoint(
                capsule_id="cap_1",
                predicted_probability_correct=0.8,
                actual_outcome="partial",
                actual_outcome_binary=0.5,
                prediction_timestamp="2024-01-01T10:00:00Z",
                outcome_timestamp="2024-01-01T12:00:00Z",
            )
        ] * 50

        metrics = tracker.calculate_accuracy_metrics(data)

        # Mean actual should be 0.5
        assert metrics.mean_actual_accuracy == pytest.approx(0.5, abs=0.01)
