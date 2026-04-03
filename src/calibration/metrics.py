"""
Calibration Metrics - Calculated from historical comparison.

Key principle: These metrics come from comparing model claims to actual outcomes,
NOT from model self-assessment. The self-assessment is what we're evaluating,
not what we're trusting.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from .queries import CalibrationDataPoint, CalibrationQueries


@dataclass
class CalibrationMetrics:
    """
    Calibration metrics calculated from historical comparison.

    These are MEASURED, not model-claimed. That's the whole point.
    """

    # Basic counts
    total_predictions: int = 0
    predictions_with_outcomes: int = 0

    # Confidence calibration
    # Maps bucket (e.g., "0.8-0.9") to actual accuracy in that bucket
    confidence_buckets: Dict[str, float] = field(default_factory=dict)

    # Overconfidence score
    # Positive = overconfident (claims higher confidence than warranted)
    # Negative = underconfident (claims lower confidence than warranted)
    overconfidence_score: float = 0.0

    # Self-assessment accuracy
    # How often flagged uncertainties were actual error sources
    uncertainty_hit_rate: float = 0.0
    uncertainty_sample_size: int = 0

    # How often errors occurred where model claimed certainty
    missed_error_rate: float = 0.0
    missed_error_sample_size: int = 0

    # Outcome breakdown
    outcome_distribution: Dict[str, int] = field(default_factory=dict)

    # Per-model breakdown
    by_model: Dict[str, "CalibrationMetrics"] = field(default_factory=dict)

    # Temporal tracking
    calculated_at: Optional[datetime] = None
    data_range_start: Optional[datetime] = None
    data_range_end: Optional[datetime] = None

    def is_well_calibrated(self) -> bool:
        """
        Is the model well-calibrated?

        Well-calibrated means |overconfidence_score| < 0.1.
        """
        return abs(self.overconfidence_score) < 0.1

    def calibration_quality(self) -> str:
        """Human-readable calibration quality assessment."""
        if self.predictions_with_outcomes < 10:
            return "insufficient_data"

        score = abs(self.overconfidence_score)
        if score < 0.1:
            return "excellent"
        elif score < 0.2:
            return "good"
        elif score < 0.3:
            return "fair"
        else:
            return "poor"

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 60,
            "CALIBRATION METRICS",
            "=" * 60,
            f"Total predictions: {self.total_predictions}",
            f"With outcomes: {self.predictions_with_outcomes}",
            "",
        ]

        if self.predictions_with_outcomes > 0:
            lines.append("Outcome distribution:")
            for outcome, count in sorted(self.outcome_distribution.items()):
                lines.append(f"  {outcome}: {count}")

            lines.append(f"\nOverconfidence score: {self.overconfidence_score:+.3f}")
            lines.append("  (positive = overconfident, negative = underconfident)")
            lines.append(f"\nCalibration quality: {self.calibration_quality()}")

            if self.confidence_buckets:
                lines.append("\nConfidence bucket accuracy:")
                for bucket, accuracy in sorted(self.confidence_buckets.items()):
                    lines.append(f"  {bucket}: {accuracy:.0%}")

            if self.uncertainty_sample_size > 0:
                lines.append(f"\nUncertainty hit rate: {self.uncertainty_hit_rate:.0%}")
                lines.append(f"  (n={self.uncertainty_sample_size})")

            if self.missed_error_sample_size > 0:
                lines.append(f"\nMissed error rate: {self.missed_error_rate:.0%}")
                lines.append(f"  (n={self.missed_error_sample_size})")
        else:
            lines.append(
                "No outcomes recorded yet. Use outcome_recorder to add outcomes."
            )

        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_predictions": self.total_predictions,
            "predictions_with_outcomes": self.predictions_with_outcomes,
            "confidence_buckets": self.confidence_buckets,
            "overconfidence_score": self.overconfidence_score,
            "uncertainty_hit_rate": self.uncertainty_hit_rate,
            "uncertainty_sample_size": self.uncertainty_sample_size,
            "missed_error_rate": self.missed_error_rate,
            "missed_error_sample_size": self.missed_error_sample_size,
            "outcome_distribution": self.outcome_distribution,
            "calibration_quality": self.calibration_quality(),
            "calculated_at": self.calculated_at.isoformat()
            if self.calculated_at
            else None,
            "data_range_start": self.data_range_start.isoformat()
            if self.data_range_start
            else None,
            "data_range_end": self.data_range_end.isoformat()
            if self.data_range_end
            else None,
        }


def calculate_calibration(
    db_path: Optional[str] = None,
    model: Optional[str] = None,
    since: Optional[datetime] = None,
    include_by_model: bool = True,
) -> CalibrationMetrics:
    """
    Calculate calibration metrics from historical data.

    This is the main entry point for calibration analysis.
    """
    queries = CalibrationQueries(db_path)

    # Get all data points
    data_points = queries.get_calibration_data(model=model, since=since)

    if not data_points:
        return CalibrationMetrics(calculated_at=datetime.now())

    # Calculate basic metrics
    metrics = CalibrationMetrics(
        total_predictions=len(data_points),
        predictions_with_outcomes=len(data_points),
        calculated_at=datetime.now(),
    )

    # Data range
    timestamps = [dp.timestamp for dp in data_points]
    metrics.data_range_start = min(timestamps)
    metrics.data_range_end = max(timestamps)

    # Outcome distribution
    for dp in data_points:
        if dp.outcome_type not in metrics.outcome_distribution:
            metrics.outcome_distribution[dp.outcome_type] = 0
        metrics.outcome_distribution[dp.outcome_type] += 1

    # Overconfidence score (average deviation)
    deviations = [dp.deviation for dp in data_points]
    metrics.overconfidence_score = -sum(deviations) / len(
        deviations
    )  # Negate: positive = overconfident

    # Confidence buckets
    bucket_data = queries.get_confidence_buckets()
    for bucket, (correct, total) in bucket_data.items():
        if total > 0:
            metrics.confidence_buckets[bucket] = correct / total

    # Uncertainty hit rate
    hit_rate, sample_size = queries.get_uncertainty_hit_rate()
    metrics.uncertainty_hit_rate = hit_rate
    metrics.uncertainty_sample_size = sample_size

    # Missed error rate
    miss_rate, miss_sample = queries.get_missed_error_rate()
    metrics.missed_error_rate = miss_rate
    metrics.missed_error_sample_size = miss_sample

    # Per-model breakdown
    if include_by_model:
        by_model_data = queries.get_by_model()
        for model_name, model_data in by_model_data.items():
            if len(model_data) < 3:  # Skip models with too few data points
                continue

            model_metrics = CalibrationMetrics(
                total_predictions=len(model_data),
                predictions_with_outcomes=len(model_data),
            )

            # Outcome distribution for this model
            for dp in model_data:
                if dp.outcome_type not in model_metrics.outcome_distribution:
                    model_metrics.outcome_distribution[dp.outcome_type] = 0
                model_metrics.outcome_distribution[dp.outcome_type] += 1

            # Overconfidence for this model
            model_deviations = [dp.deviation for dp in model_data]
            model_metrics.overconfidence_score = -sum(model_deviations) / len(
                model_deviations
            )

            metrics.by_model[model_name] = model_metrics

    return metrics


def build_calibration_context(
    topic: Optional[str] = None,
    model: Optional[str] = None,
    db_path: Optional[str] = None,
    min_samples: int = 10,
) -> str:
    """
    Build context about model's historical reliability for injection into prompts.

    This is Phase 5 of the calibration system - the feedback loop.
    The feedback comes from MEASURED OUTCOMES, not model self-assessment.
    """
    metrics = calculate_calibration(db_path=db_path, model=model)

    if metrics.predictions_with_outcomes < min_samples:
        return f"Insufficient calibration data ({metrics.predictions_with_outcomes}/{min_samples} samples required)."

    # Build context string
    lines = [
        f"CALIBRATION CONTEXT (from {metrics.predictions_with_outcomes} verified outcomes):",
    ]

    # Accuracy summary
    worked = metrics.outcome_distribution.get("worked", 0)
    partial = metrics.outcome_distribution.get("partial", 0)
    failed = metrics.outcome_distribution.get("failed", 0)
    total = worked + partial + failed
    if total > 0:
        accuracy = (worked + 0.5 * partial) / total
        lines.append(f"- Historical accuracy: {accuracy:.0%}")

    # Confidence calibration
    if abs(metrics.overconfidence_score) > 0.1:
        if metrics.overconfidence_score > 0:
            lines.append(
                f"- Your confidence tends to be {metrics.overconfidence_score:+.0%} higher than warranted"
            )
        else:
            lines.append(
                f"- Your confidence tends to be {abs(metrics.overconfidence_score):.0%} lower than warranted"
            )
    else:
        lines.append("- Your confidence is well-calibrated")

    # Missed error patterns
    if metrics.missed_error_rate > 0.2 and metrics.missed_error_sample_size >= 3:
        lines.append(
            f"- WARNING: {metrics.missed_error_rate:.0%} of errors occurred in areas you claimed certainty"
        )

    # Uncertainty hit rate
    if metrics.uncertainty_hit_rate > 0.5 and metrics.uncertainty_sample_size >= 3:
        lines.append(
            f"- Your flagged uncertainties were relevant {metrics.uncertainty_hit_rate:.0%} of the time"
        )

    lines.append("\nAdjust your confidence accordingly.")

    return "\n".join(lines)


if __name__ == "__main__":
    # Calculate and display calibration metrics
    metrics = calculate_calibration()
    print(metrics.summary())

    if metrics.predictions_with_outcomes > 0:
        print("\n" + "=" * 60)
        print("CALIBRATION CONTEXT (for prompt injection):")
        print("=" * 60)
        print(build_calibration_context())
