"""
Confidence Calibration Engine
Validates and improves confidence predictions based on actual outcomes
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np


@dataclass
class CalibrationMetrics:
    """Metrics for confidence calibration quality."""

    expected_calibration_error: float  # ECE - overall calibration quality
    max_calibration_error: float  # MCE - worst bucket error
    brier_score: float  # Overall prediction accuracy
    reliability_by_bucket: Dict[float, Dict[str, float]]  # Per-bucket metrics
    sample_size: int


@dataclass
class CalibrationRecommendation:
    """Recommendations for improving calibration."""

    domain: str
    confidence_bucket: float
    current_error: float
    recommended_adjustment: float
    confidence_level: str  # 'high', 'medium', 'low' based on sample size
    sample_size: int


class ConfidenceCalibrator:
    """Analyzes and improves confidence calibration."""

    # Minimum samples needed for reliable calibration
    MIN_SAMPLES_HIGH_CONFIDENCE = 30
    MIN_SAMPLES_MEDIUM_CONFIDENCE = 10
    MIN_SAMPLES_LOW_CONFIDENCE = 3

    @staticmethod
    def calculate_calibration_metrics(
        predictions: List[float], outcomes: List[bool], num_buckets: int = 10
    ) -> CalibrationMetrics:
        """
        Calculate comprehensive calibration metrics.

        Args:
            predictions: List of confidence predictions (0.0-1.0)
            outcomes: List of actual outcomes (True/False for success/failure)
            num_buckets: Number of confidence buckets

        Returns:
            CalibrationMetrics with ECE, MCE, Brier score, and per-bucket data
        """
        if len(predictions) != len(outcomes):
            raise ValueError("Predictions and outcomes must have same length")

        if not predictions:
            return CalibrationMetrics(
                expected_calibration_error=0.0,
                max_calibration_error=0.0,
                brier_score=0.0,
                reliability_by_bucket={},
                sample_size=0,
            )

        # Create confidence buckets
        bucket_size = 1.0 / num_buckets
        buckets = defaultdict(lambda: {"predictions": [], "outcomes": []})

        for pred, outcome in zip(predictions, outcomes):
            bucket_idx = min(int(pred / bucket_size), num_buckets - 1)
            bucket_center = (bucket_idx + 0.5) * bucket_size
            buckets[bucket_center]["predictions"].append(pred)
            buckets[bucket_center]["outcomes"].append(outcome)

        # Calculate per-bucket metrics
        reliability_by_bucket = {}
        calibration_errors = []

        for bucket_center, data in buckets.items():
            preds = data["predictions"]
            outc = data["outcomes"]

            avg_confidence = np.mean(preds)
            accuracy = np.mean(outc)
            calibration_error = abs(avg_confidence - accuracy)

            reliability_by_bucket[bucket_center] = {
                "avg_confidence": avg_confidence,
                "accuracy": accuracy,
                "calibration_error": calibration_error,
                "sample_size": len(preds),
            }

            calibration_errors.append(calibration_error * len(preds))

        # Expected Calibration Error (ECE) - weighted by bucket size
        total_samples = len(predictions)
        ece = sum(calibration_errors) / total_samples if total_samples > 0 else 0.0

        # Maximum Calibration Error (MCE) - worst bucket
        mce = max(
            (data["calibration_error"] for data in reliability_by_bucket.values()),
            default=0.0,
        )

        # Brier Score - overall prediction accuracy
        brier_score = np.mean(
            [(pred - outcome) ** 2 for pred, outcome in zip(predictions, outcomes)]
        )

        return CalibrationMetrics(
            expected_calibration_error=ece,
            max_calibration_error=mce,
            brier_score=brier_score,
            reliability_by_bucket=reliability_by_bucket,
            sample_size=total_samples,
        )

    @staticmethod
    def generate_calibration_recommendations(
        calibration_data: Dict[Tuple[str, float], Dict[str, int]],
        min_adjustment_threshold: float = 0.05,
    ) -> List[CalibrationRecommendation]:
        """
        Generate calibration adjustment recommendations.

        Args:
            calibration_data: Dict mapping (domain, confidence_bucket) to counts
            min_adjustment_threshold: Minimum error to recommend adjustment

        Returns:
            List of calibration recommendations
        """
        recommendations = []

        for (domain, confidence_bucket), data in calibration_data.items():
            predicted_count = data["predicted_count"]
            actual_success_count = data["actual_success_count"]

            if predicted_count == 0:
                continue

            # Calculate actual success rate
            actual_rate = actual_success_count / predicted_count

            # Calculate calibration error
            calibration_error = confidence_bucket - actual_rate

            # Only recommend adjustment if error exceeds threshold
            if abs(calibration_error) < min_adjustment_threshold:
                continue

            # Calculate recommended adjustment (conservative: 50% of error)
            recommended_adjustment = -calibration_error * 0.5

            # Determine confidence level based on sample size
            if predicted_count >= ConfidenceCalibrator.MIN_SAMPLES_HIGH_CONFIDENCE:
                confidence_level = "high"
            elif predicted_count >= ConfidenceCalibrator.MIN_SAMPLES_MEDIUM_CONFIDENCE:
                confidence_level = "medium"
            else:
                confidence_level = "low"

            recommendations.append(
                CalibrationRecommendation(
                    domain=domain,
                    confidence_bucket=confidence_bucket,
                    current_error=calibration_error,
                    recommended_adjustment=recommended_adjustment,
                    confidence_level=confidence_level,
                    sample_size=predicted_count,
                )
            )

        # Sort by sample size (most reliable first)
        recommendations.sort(key=lambda r: r.sample_size, reverse=True)

        return recommendations

    @staticmethod
    def apply_calibration_adjustment(
        raw_confidence: float,
        domain: str,
        calibration_map: Dict[Tuple[str, float], float],
    ) -> float:
        """
        Apply calibration adjustment to a raw confidence score.

        Args:
            raw_confidence: Original confidence (0.0-1.0)
            domain: Problem domain
            calibration_map: Map of (domain, bucket) -> adjustment

        Returns:
            Calibrated confidence score
        """
        # Round to nearest 0.1 for bucket lookup
        confidence_bucket = round(raw_confidence * 10) / 10

        # Look up adjustment for this domain and bucket
        adjustment = calibration_map.get((domain, confidence_bucket), 0.0)

        # Apply adjustment and clamp to valid range
        calibrated = raw_confidence + adjustment
        return max(0.0, min(1.0, calibrated))

    @staticmethod
    def generate_reliability_diagram_data(
        predictions: List[float], outcomes: List[bool], num_buckets: int = 10
    ) -> Dict[str, List]:
        """
        Generate data for plotting a reliability diagram.

        Args:
            predictions: Confidence predictions
            outcomes: Actual outcomes
            num_buckets: Number of buckets

        Returns:
            Dict with 'confidence', 'accuracy', 'sample_size' lists for plotting
        """
        bucket_size = 1.0 / num_buckets
        buckets = defaultdict(lambda: {"predictions": [], "outcomes": []})

        for pred, outcome in zip(predictions, outcomes):
            bucket_idx = min(int(pred / bucket_size), num_buckets - 1)
            bucket_center = (bucket_idx + 0.5) * bucket_size
            buckets[bucket_center]["predictions"].append(pred)
            buckets[bucket_center]["outcomes"].append(outcome)

        # Sort by confidence for plotting
        sorted_buckets = sorted(buckets.items())

        confidence_levels = []
        accuracies = []
        sample_sizes = []

        for bucket_center, data in sorted_buckets:
            avg_confidence = np.mean(data["predictions"])
            accuracy = np.mean(data["outcomes"])
            sample_size = len(data["predictions"])

            confidence_levels.append(avg_confidence)
            accuracies.append(accuracy)
            sample_sizes.append(sample_size)

        return {
            "confidence": confidence_levels,
            "accuracy": accuracies,
            "sample_size": sample_sizes,
        }

    @staticmethod
    def calculate_domain_specific_calibration(
        capsules_with_outcomes: List[Dict], domains: Optional[List[str]] = None
    ) -> Dict[str, CalibrationMetrics]:
        """
        Calculate calibration metrics per domain.

        Args:
            capsules_with_outcomes: List of capsules with outcome data
            domains: List of domains to analyze (None = all)

        Returns:
            Dict mapping domain -> CalibrationMetrics
        """
        # Group by domain
        domain_data = defaultdict(lambda: {"predictions": [], "outcomes": []})

        for capsule_data in capsules_with_outcomes:
            domain = capsule_data.get("domain", "general")

            if domains and domain not in domains:
                continue

            confidence = capsule_data.get("confidence")
            outcome_success = capsule_data.get("outcome_success")

            if confidence is not None and outcome_success is not None:
                domain_data[domain]["predictions"].append(confidence)
                domain_data[domain]["outcomes"].append(outcome_success)

        # Calculate metrics per domain
        domain_metrics = {}

        for domain, data in domain_data.items():
            if data["predictions"]:
                metrics = ConfidenceCalibrator.calculate_calibration_metrics(
                    predictions=data["predictions"], outcomes=data["outcomes"]
                )
                domain_metrics[domain] = metrics

        return domain_metrics

    @staticmethod
    def compare_calibration_over_time(
        calibration_history: List[Dict],
    ) -> Dict[str, any]:
        """
        Analyze how calibration has improved over time.

        Args:
            calibration_history: List of {timestamp, metrics} dicts

        Returns:
            Dict with trend analysis
        """
        if len(calibration_history) < 2:
            return {
                "trend": "insufficient_data",
                "improvement": None,
                "message": "Need at least 2 calibration measurements",
            }

        # Extract ECE values over time
        ece_values = [
            h["metrics"].expected_calibration_error for h in calibration_history
        ]

        # Calculate improvement
        first_ece = ece_values[0]
        last_ece = ece_values[-1]
        improvement = first_ece - last_ece
        improvement_pct = (improvement / first_ece * 100) if first_ece > 0 else 0

        # Determine trend
        if improvement > 0.01:
            trend = "improving"
        elif improvement < -0.01:
            trend = "degrading"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "improvement": improvement,
            "improvement_percentage": improvement_pct,
            "first_ece": first_ece,
            "last_ece": last_ece,
            "measurement_count": len(calibration_history),
        }


# Example usage
if __name__ == "__main__":
    print("[OK] Confidence Calibration Engine Ready")
    print("\nCapabilities:")
    print("  - Calculate Expected Calibration Error (ECE)")
    print("  - Calculate Maximum Calibration Error (MCE)")
    print("  - Compute Brier Score for accuracy")
    print("  - Generate calibration adjustments")
    print("  - Create reliability diagrams")
    print("  - Track calibration improvement over time")
    print("  - Domain-specific calibration")
