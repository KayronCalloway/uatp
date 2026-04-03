"""
Confidence Calibration Module
=============================

Bayesian confidence calibration using Platt scaling and online updates.

Key concepts:
- Platt scaling: Logistic regression to map raw scores to calibrated probabilities
- Online updates: Incrementally update calibration with new data
- Calibration drift detection: Alert when calibration degrades
- Per-domain calibration: Different calibrators for different contexts

World-class engineering principles:
- Proper scoring rules (Brier score, log loss)
- Calibration plots and reliability diagrams
- Uncertainty over the calibration itself (meta-uncertainty)
"""

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Optional: scipy for optimization
try:
    from scipy.optimize import minimize
    from scipy.special import expit  # sigmoid

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

    def expit(x):
        """Fallback sigmoid function."""
        return 1 / (1 + math.exp(-x))


@dataclass
class CalibrationPoint:
    """A single calibration data point."""

    predicted_confidence: float
    actual_outcome: float  # 1.0 = success, 0.5 = partial, 0.0 = failure
    timestamp: datetime
    domain: str = "general"
    weight: float = 1.0  # For exponential decay


@dataclass
class CalibrationMetrics:
    """Calibration quality metrics."""

    brier_score: float  # Lower is better (0 = perfect)
    log_loss: float  # Lower is better
    calibration_error: float  # Expected Calibration Error
    sample_size: int
    reliability_diagram: Dict[str, float]  # bucket -> actual_rate


class PlattScaler:
    """
    Platt scaling for confidence calibration.

    Maps raw confidence scores to calibrated probabilities using
    logistic regression: P(correct) = 1 / (1 + exp(A*score + B))

    Supports:
    - Batch fitting from historical data
    - Online updates with exponential decay
    - Per-domain calibration
    """

    def __init__(
        self,
        decay_rate: float = 0.995,  # How much to weight old vs new data
        min_samples: int = 20,  # Minimum samples before calibrating
    ):
        """
        Initialize Platt scaler.

        Args:
            decay_rate: Exponential decay for old samples (0.995 = ~1% decay per sample)
            min_samples: Minimum samples needed before applying calibration
        """
        self.decay_rate = decay_rate
        self.min_samples = min_samples

        # Calibration parameters: P(correct) = sigmoid(A * score + B)
        # Default: identity transform (A=1, B=0 means no adjustment)
        self.A = 1.0
        self.B = 0.0

        # Training data (for online updates)
        self.data_points: List[CalibrationPoint] = []

        # Metadata
        self.last_fit_time: Optional[datetime] = None
        self.fit_count = 0

    def calibrate(self, raw_confidence: float) -> float:
        """
        Apply calibration to a raw confidence score.

        Args:
            raw_confidence: Original confidence (0-1)

        Returns:
            Calibrated confidence (0-1)
        """
        if len(self.data_points) < self.min_samples:
            return raw_confidence  # Not enough data to calibrate

        # Platt scaling: sigmoid(A * score + B)
        logit = self.A * raw_confidence + self.B
        calibrated = expit(logit)

        # Clamp to valid range
        return max(0.01, min(0.99, calibrated))

    def add_observation(
        self,
        predicted: float,
        actual: float,
        domain: str = "general",
        refit: bool = True,
    ):
        """
        Add a new calibration observation.

        Args:
            predicted: The predicted confidence (0-1)
            actual: The actual outcome (1.0 = success, 0.5 = partial, 0.0 = failure)
            domain: Domain/context for this observation
            refit: Whether to refit the model after adding
        """
        # Apply exponential decay to existing points
        for point in self.data_points:
            point.weight *= self.decay_rate

        # Add new point
        self.data_points.append(
            CalibrationPoint(
                predicted_confidence=predicted,
                actual_outcome=actual,
                timestamp=datetime.now(timezone.utc),
                domain=domain,
                weight=1.0,
            )
        )

        # Remove very low weight points (effectively forgotten)
        self.data_points = [p for p in self.data_points if p.weight > 0.01]

        # Refit if we have enough data
        if refit and len(self.data_points) >= self.min_samples:
            self._fit()

    def _fit(self):
        """Fit Platt scaling parameters using weighted log loss."""
        if not SCIPY_AVAILABLE:
            # Fallback: simple bucket-based adjustment
            self._fit_simple()
            return

        if len(self.data_points) < self.min_samples:
            return

        # Extract weighted data
        X = [p.predicted_confidence for p in self.data_points]
        y = [p.actual_outcome for p in self.data_points]
        weights = [p.weight for p in self.data_points]

        def weighted_log_loss(params):
            """Weighted negative log likelihood."""
            A, B = params
            total_loss = 0.0
            total_weight = 0.0

            for xi, yi, wi in zip(X, y, weights, strict=False):
                p = expit(A * xi + B)
                # Avoid log(0)
                p = max(1e-10, min(1 - 1e-10, p))
                loss = -(yi * math.log(p) + (1 - yi) * math.log(1 - p))
                total_loss += wi * loss
                total_weight += wi

            return total_loss / total_weight if total_weight > 0 else 0

        # Optimize
        result = minimize(
            weighted_log_loss,
            x0=[self.A, self.B],
            method="L-BFGS-B",
            bounds=[(-10, 10), (-10, 10)],
        )

        if result.success:
            self.A, self.B = result.x
            self.last_fit_time = datetime.now(timezone.utc)
            self.fit_count += 1

    def _fit_simple(self):
        """Simple bucket-based calibration (fallback without scipy)."""
        if len(self.data_points) < self.min_samples:
            return

        # Group into buckets and compute adjustment
        buckets = {}
        for point in self.data_points:
            bucket = round(point.predicted_confidence, 1)
            if bucket not in buckets:
                buckets[bucket] = {"weighted_actual": 0, "total_weight": 0}
            buckets[bucket]["weighted_actual"] += point.weight * point.actual_outcome
            buckets[bucket]["total_weight"] += point.weight

        # Compute average adjustment
        adjustments = []
        for predicted, data in buckets.items():
            if data["total_weight"] > 0.5:  # Enough weight
                actual_rate = data["weighted_actual"] / data["total_weight"]
                adjustments.append(actual_rate - predicted)

        if adjustments:
            # Simple linear adjustment
            avg_adjustment = sum(adjustments) / len(adjustments)
            self.B = avg_adjustment
            self.last_fit_time = datetime.now(timezone.utc)
            self.fit_count += 1

    def get_metrics(self) -> CalibrationMetrics:
        """Calculate calibration quality metrics."""
        if not self.data_points:
            return CalibrationMetrics(
                brier_score=1.0,
                log_loss=float("inf"),
                calibration_error=1.0,
                sample_size=0,
                reliability_diagram={},
            )

        # Calculate metrics
        brier_sum = 0.0
        log_loss_sum = 0.0
        total_weight = 0.0

        # For reliability diagram
        buckets = {}

        for point in self.data_points:
            calibrated = self.calibrate(point.predicted_confidence)

            # Brier score: (predicted - actual)^2
            brier_sum += point.weight * (calibrated - point.actual_outcome) ** 2

            # Log loss
            p = max(1e-10, min(1 - 1e-10, calibrated))
            y = point.actual_outcome
            log_loss_sum += point.weight * -(
                y * math.log(p) + (1 - y) * math.log(1 - p)
            )

            total_weight += point.weight

            # Reliability diagram
            bucket = f"{round(calibrated, 1):.1f}"
            if bucket not in buckets:
                buckets[bucket] = {"weighted_actual": 0, "total_weight": 0}
            buckets[bucket]["weighted_actual"] += point.weight * point.actual_outcome
            buckets[bucket]["total_weight"] += point.weight

        brier_score = brier_sum / total_weight if total_weight > 0 else 1.0
        log_loss = log_loss_sum / total_weight if total_weight > 0 else float("inf")

        # Reliability diagram
        reliability = {}
        calibration_errors = []
        for bucket, data in buckets.items():
            if data["total_weight"] > 0:
                actual_rate = data["weighted_actual"] / data["total_weight"]
                reliability[bucket] = actual_rate
                predicted = float(bucket)
                calibration_errors.append(
                    abs(predicted - actual_rate) * data["total_weight"]
                )

        ece = sum(calibration_errors) / total_weight if total_weight > 0 else 1.0

        return CalibrationMetrics(
            brier_score=brier_score,
            log_loss=log_loss,
            calibration_error=ece,
            sample_size=len(self.data_points),
            reliability_diagram=reliability,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize calibrator state."""
        return {
            "A": self.A,
            "B": self.B,
            "decay_rate": self.decay_rate,
            "min_samples": self.min_samples,
            "last_fit_time": self.last_fit_time.isoformat()
            if self.last_fit_time
            else None,
            "fit_count": self.fit_count,
            "data_points": [
                {
                    "predicted": p.predicted_confidence,
                    "actual": p.actual_outcome,
                    "timestamp": p.timestamp.isoformat(),
                    "domain": p.domain,
                    "weight": p.weight,
                }
                for p in self.data_points
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlattScaler":
        """Deserialize calibrator state."""
        scaler = cls(
            decay_rate=data.get("decay_rate", 0.995),
            min_samples=data.get("min_samples", 20),
        )
        scaler.A = data.get("A", 1.0)
        scaler.B = data.get("B", 0.0)
        scaler.fit_count = data.get("fit_count", 0)

        if data.get("last_fit_time"):
            scaler.last_fit_time = datetime.fromisoformat(data["last_fit_time"])

        for p in data.get("data_points", []):
            scaler.data_points.append(
                CalibrationPoint(
                    predicted_confidence=p["predicted"],
                    actual_outcome=p["actual"],
                    timestamp=datetime.fromisoformat(p["timestamp"]),
                    domain=p.get("domain", "general"),
                    weight=p.get("weight", 1.0),
                )
            )

        return scaler


class CalibrationManager:
    """
    Manages multiple calibrators for different domains/contexts.

    Features:
    - Per-domain calibration (code vs prose vs math)
    - Global fallback calibrator
    - Persistence to disk
    - Drift detection and alerts
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize calibration manager.

        Args:
            storage_path: Path to store calibration state (optional)
        """
        self.storage_path = storage_path
        self.calibrators: Dict[str, PlattScaler] = {
            "global": PlattScaler(),
        }

        # Load saved state if available
        if storage_path and storage_path.exists():
            self.load()

    def get_calibrator(self, domain: str = "global") -> PlattScaler:
        """Get calibrator for a domain, creating if needed."""
        if domain not in self.calibrators:
            self.calibrators[domain] = PlattScaler()
        return self.calibrators[domain]

    def calibrate(
        self,
        raw_confidence: float,
        domain: str = "global",
        fallback_to_global: bool = True,
    ) -> float:
        """
        Calibrate a confidence score.

        Args:
            raw_confidence: Original confidence (0-1)
            domain: Domain/context
            fallback_to_global: Use global calibrator if domain has insufficient data

        Returns:
            Calibrated confidence
        """
        calibrator = self.get_calibrator(domain)

        # Check if domain has enough data
        if len(calibrator.data_points) < calibrator.min_samples and fallback_to_global:
            calibrator = self.calibrators.get("global", calibrator)

        return calibrator.calibrate(raw_confidence)

    def record_outcome(
        self,
        predicted_confidence: float,
        actual_outcome: float,
        domain: str = "global",
    ):
        """
        Record an outcome for calibration.

        Updates both domain-specific and global calibrators.

        Args:
            predicted_confidence: What the system predicted
            actual_outcome: What actually happened (1.0/0.5/0.0)
            domain: Domain/context
        """
        # Update domain-specific calibrator
        domain_calibrator = self.get_calibrator(domain)
        domain_calibrator.add_observation(predicted_confidence, actual_outcome, domain)

        # Also update global calibrator
        if domain != "global":
            global_calibrator = self.calibrators["global"]
            global_calibrator.add_observation(
                predicted_confidence, actual_outcome, domain
            )

        # Auto-save
        if self.storage_path:
            self.save()

    def get_all_metrics(self) -> Dict[str, CalibrationMetrics]:
        """Get metrics for all calibrators."""
        return {
            domain: calibrator.get_metrics()
            for domain, calibrator in self.calibrators.items()
        }

    def check_drift(self, threshold: float = 0.15) -> List[str]:
        """
        Check for calibration drift.

        Returns list of domains with concerning drift.
        """
        alerts = []

        for domain, calibrator in self.calibrators.items():
            metrics = calibrator.get_metrics()

            if metrics.sample_size >= 20:
                if metrics.calibration_error > threshold:
                    alerts.append(
                        f"Domain '{domain}' has high calibration error: "
                        f"{metrics.calibration_error:.3f} (threshold: {threshold})"
                    )

                if metrics.brier_score > 0.25:
                    alerts.append(
                        f"Domain '{domain}' has poor Brier score: "
                        f"{metrics.brier_score:.3f}"
                    )

        return alerts

    def save(self):
        """Save calibration state to disk."""
        if not self.storage_path:
            return

        data = {
            domain: calibrator.to_dict()
            for domain, calibrator in self.calibrators.items()
        }

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        """Load calibration state from disk."""
        if not self.storage_path or not self.storage_path.exists():
            return

        with open(self.storage_path) as f:
            data = json.load(f)

        self.calibrators = {
            domain: PlattScaler.from_dict(state) for domain, state in data.items()
        }

        # Ensure global exists
        if "global" not in self.calibrators:
            self.calibrators["global"] = PlattScaler()


# Default manager instance
_default_manager: Optional[CalibrationManager] = None


def get_calibration_manager(
    storage_path: Optional[Path] = None,
) -> CalibrationManager:
    """Get or create the default calibration manager."""
    global _default_manager
    if _default_manager is None:
        default_path = Path("data/calibration_state.json")
        _default_manager = CalibrationManager(storage_path or default_path)
    return _default_manager


def calibrate_confidence(
    raw_confidence: float,
    domain: str = "global",
) -> float:
    """Convenience function to calibrate a confidence score."""
    manager = get_calibration_manager()
    return manager.calibrate(raw_confidence, domain)
