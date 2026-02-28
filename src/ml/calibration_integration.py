"""
Calibration Integration - Gap 5 Implementation
Integrates confidence calibration into the capsule flow.

When we say "85% confident", are we actually right 85% of the time?
This module:
1. Bootstraps calibration from existing outcomes in the database
2. Applies calibration to new capsule confidence
3. Updates calibration when new outcomes are recorded

The calibration loop:
Capsule Created (raw confidence) -> Apply Calibration -> Calibrated Confidence
                                          ↑
Outcome Recorded -> Update Calibrator ────┘
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Import calibration infrastructure
try:
    from src.feedback.calibration import CalibrationManager, PlattScaler

    CALIBRATION_AVAILABLE = True
except ImportError:
    CALIBRATION_AVAILABLE = False
    logger.warning("Calibration module not available")


# Default storage path
DEFAULT_CALIBRATION_PATH = Path("data/calibration_state.json")


class CapsuleCalibrator:
    """
    Integrates calibration with capsule creation and outcome tracking.

    Usage:
        calibrator = CapsuleCalibrator(db_path)

        # Bootstrap from existing data
        calibrator.bootstrap_from_database()

        # Apply to new capsule
        calibrated = calibrator.calibrate(raw_confidence=0.85, topics=["coding"])

        # Update when outcome recorded
        calibrator.record_outcome(confidence=0.85, outcome="success", topics=["coding"])
    """

    def __init__(
        self,
        db_path: str = None,
        storage_path: Path = None,
        min_samples: int = 10,
    ):
        """
        Initialize capsule calibrator.

        Args:
            db_path: Path to SQLite database
            storage_path: Path to store calibration state
            min_samples: Minimum samples before applying calibration
        """
        self.db_path = db_path or "uatp_dev.db"
        self.storage_path = storage_path or DEFAULT_CALIBRATION_PATH

        if CALIBRATION_AVAILABLE:
            self._manager = CalibrationManager(self.storage_path)
            # Set minimum samples
            for calibrator in self._manager.calibrators.values():
                calibrator.min_samples = min_samples
        else:
            self._manager = None

        self._bootstrapped = False

    def bootstrap_from_database(self) -> Dict[str, Any]:
        """
        Bootstrap calibration from existing capsule outcomes.

        Reads all capsules with outcomes and feeds them to the calibrator.

        Returns:
            Dict with bootstrap statistics
        """
        if not CALIBRATION_AVAILABLE or not self._manager:
            return {"error": "Calibration not available"}

        stats = {
            "processed": 0,
            "skipped": 0,
            "by_outcome": {"success": 0, "partial": 0, "failure": 0},
            "by_domain": {},
        }

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all capsules with outcomes
            cursor.execute(
                """
                SELECT capsule_id, payload, outcome_status
                FROM capsules
                WHERE outcome_status IS NOT NULL
                ORDER BY timestamp ASC
            """
            )

            outcome_values = {
                "success": 1.0,
                "partial": 0.5,
                "failure": 0.0,
            }

            for row in cursor.fetchall():
                capsule_id, payload_data, outcome_status = row

                if outcome_status not in outcome_values:
                    stats["skipped"] += 1
                    continue

                # Parse payload for confidence and topics
                payload = {}
                if isinstance(payload_data, str):
                    try:
                        payload = json.loads(payload_data)
                    except json.JSONDecodeError:
                        stats["skipped"] += 1
                        continue
                elif payload_data:
                    payload = payload_data

                # Get original confidence (before any calibration)
                confidence = payload.get("confidence_original") or payload.get(
                    "confidence", 0.5
                )

                # Get domain from topics
                topics = payload.get("session_metadata", {}).get("topics", [])
                domain = topics[0].lower() if topics else "general"

                # Record for calibration
                actual_outcome = outcome_values[outcome_status]
                self._manager.record_outcome(
                    predicted_confidence=confidence,
                    actual_outcome=actual_outcome,
                    domain=domain,
                )

                stats["processed"] += 1
                stats["by_outcome"][outcome_status] = (
                    stats["by_outcome"].get(outcome_status, 0) + 1
                )
                stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1

            conn.close()

            self._bootstrapped = True
            logger.info(f"Calibration bootstrapped from {stats['processed']} capsules")

            return stats

        except Exception as e:
            logger.error(f"Failed to bootstrap calibration: {e}")
            return {"error": str(e)}

    def calibrate(
        self,
        raw_confidence: float,
        topics: List[str] = None,
        auto_bootstrap: bool = True,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Apply calibration to a confidence score.

        Args:
            raw_confidence: Original confidence (0-1)
            topics: List of topics for domain-specific calibration
            auto_bootstrap: Bootstrap from database if not done yet

        Returns:
            Tuple of (calibrated_confidence, calibration_info)
        """
        if not CALIBRATION_AVAILABLE or not self._manager:
            return raw_confidence, {"calibration": "not_available"}

        # Auto-bootstrap if needed
        if auto_bootstrap and not self._bootstrapped:
            self.bootstrap_from_database()

        # Determine domain
        domain = topics[0].lower() if topics else "general"

        # Get calibrator metrics before applying
        calibrator = self._manager.get_calibrator(domain)
        has_enough_data = len(calibrator.data_points) >= calibrator.min_samples

        if not has_enough_data:
            # Try global calibrator
            calibrator = self._manager.calibrators.get("global")
            has_enough_data = (
                calibrator and len(calibrator.data_points) >= calibrator.min_samples
            )
            domain = "global"

        if not has_enough_data:
            return raw_confidence, {
                "calibration": "insufficient_data",
                "sample_size": len(calibrator.data_points) if calibrator else 0,
                "min_required": calibrator.min_samples if calibrator else 10,
            }

        # Apply calibration
        calibrated = self._manager.calibrate(raw_confidence, domain)

        # Calculate adjustment
        adjustment = calibrated - raw_confidence

        return calibrated, {
            "calibration": "applied",
            "domain": domain,
            "raw_confidence": raw_confidence,
            "calibrated_confidence": calibrated,
            "adjustment": adjustment,
            "sample_size": len(calibrator.data_points),
            "calibrator_params": {
                "A": calibrator.A,
                "B": calibrator.B,
            },
        }

    def record_outcome(
        self,
        confidence: float,
        outcome: str,
        topics: List[str] = None,
    ):
        """
        Record an outcome for calibration update.

        Args:
            confidence: The original predicted confidence
            outcome: 'success', 'partial', or 'failure'
            topics: List of topics for domain
        """
        if not CALIBRATION_AVAILABLE or not self._manager:
            return

        outcome_values = {
            "success": 1.0,
            "partial": 0.5,
            "failure": 0.0,
        }

        if outcome not in outcome_values:
            return

        domain = topics[0].lower() if topics else "general"

        self._manager.record_outcome(
            predicted_confidence=confidence,
            actual_outcome=outcome_values[outcome],
            domain=domain,
        )

        logger.debug(
            f"Recorded outcome for calibration: {outcome} (confidence was {confidence:.0%})"
        )

    def get_calibration_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive calibration report.

        Returns:
            Dict with calibration metrics, reliability diagram, and recommendations
        """
        if not CALIBRATION_AVAILABLE or not self._manager:
            return {"error": "Calibration not available"}

        report = {
            "domains": {},
            "global_metrics": None,
            "drift_alerts": [],
            "recommendations": [],
        }

        # Get metrics for all domains
        all_metrics = self._manager.get_all_metrics()

        for domain, metrics in all_metrics.items():
            report["domains"][domain] = {
                "sample_size": metrics.sample_size,
                "brier_score": round(metrics.brier_score, 4),
                "calibration_error": round(metrics.calibration_error, 4),
                "log_loss": round(metrics.log_loss, 4)
                if metrics.log_loss != float("inf")
                else None,
                "reliability_diagram": metrics.reliability_diagram,
            }

            if domain == "global":
                report["global_metrics"] = report["domains"][domain]

        # Check for drift
        report["drift_alerts"] = self._manager.check_drift()

        # Generate recommendations
        global_metrics = all_metrics.get("global")
        if global_metrics:
            if global_metrics.sample_size < 20:
                report["recommendations"].append(
                    f"Need more data: {global_metrics.sample_size}/20 samples for reliable calibration"
                )
            elif global_metrics.calibration_error > 0.15:
                report["recommendations"].append(
                    f"High calibration error ({global_metrics.calibration_error:.1%}): "
                    "System may be over/under confident"
                )
            elif global_metrics.brier_score < 0.1:
                report["recommendations"].append(
                    "Excellent calibration! Predictions are well-calibrated."
                )

            # Check for over/under confidence
            reliability = global_metrics.reliability_diagram
            if reliability:
                over_confident_buckets = []
                under_confident_buckets = []

                for bucket, actual in reliability.items():
                    predicted = float(bucket)
                    if predicted - actual > 0.15:
                        over_confident_buckets.append(bucket)
                    elif actual - predicted > 0.15:
                        under_confident_buckets.append(bucket)

                if over_confident_buckets:
                    report["recommendations"].append(
                        f"Over-confident in buckets: {', '.join(over_confident_buckets)}"
                    )
                if under_confident_buckets:
                    report["recommendations"].append(
                        f"Under-confident in buckets: {', '.join(under_confident_buckets)}"
                    )

        return report

    def get_reliability_table(self) -> str:
        """
        Get a formatted reliability table for display.

        Returns:
            Formatted string table
        """
        if not CALIBRATION_AVAILABLE or not self._manager:
            return "Calibration not available"

        metrics = self._manager.calibrators.get("global", PlattScaler()).get_metrics()

        if not metrics.reliability_diagram:
            return "Insufficient data for reliability table"

        lines = [
            "Confidence | Actual Rate | Count | Status",
            "-----------|-------------|-------|-------",
        ]

        calibrator = self._manager.calibrators.get("global")

        for bucket in sorted(metrics.reliability_diagram.keys()):
            predicted = float(bucket)
            actual = metrics.reliability_diagram[bucket]

            # Count samples in this bucket
            count = sum(
                1
                for p in calibrator.data_points
                if f"{round(p.predicted_confidence, 1):.1f}" == bucket
            )

            # Determine status
            diff = predicted - actual
            if abs(diff) < 0.1:
                status = "✓ Good"
            elif diff > 0:
                status = f"↓ Over by {diff:.0%}"
            else:
                status = f"↑ Under by {-diff:.0%}"

            lines.append(
                f"   {bucket}    |    {actual:.0%}     |  {count:3}  | {status}"
            )

        return "\n".join(lines)


# Singleton instance
_calibrator: Optional[CapsuleCalibrator] = None


def get_capsule_calibrator(db_path: str = None) -> CapsuleCalibrator:
    """Get or create the capsule calibrator."""
    global _calibrator
    if _calibrator is None:
        _calibrator = CapsuleCalibrator(db_path=db_path)
    return _calibrator


def calibrate_capsule_confidence(
    raw_confidence: float,
    topics: List[str] = None,
) -> Tuple[float, Dict[str, Any]]:
    """
    Convenience function to calibrate a capsule's confidence.

    Returns:
        Tuple of (calibrated_confidence, calibration_info)
    """
    calibrator = get_capsule_calibrator()
    return calibrator.calibrate(raw_confidence, topics)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Calibration Integration")
    parser.add_argument(
        "--bootstrap", action="store_true", help="Bootstrap from database"
    )
    parser.add_argument("--report", action="store_true", help="Show calibration report")
    parser.add_argument("--table", action="store_true", help="Show reliability table")
    parser.add_argument(
        "--test", type=float, help="Test calibration on a confidence value"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    calibrator = CapsuleCalibrator(db_path="/Users/kay/uatp-capsule-engine/uatp_dev.db")

    if args.bootstrap:
        print("Bootstrapping calibration from database...")
        stats = calibrator.bootstrap_from_database()
        print("\nBootstrap Results:")
        print(f"  Processed: {stats.get('processed', 0)}")
        print(f"  By outcome: {stats.get('by_outcome', {})}")
        print(f"  By domain: {stats.get('by_domain', {})}")

    if args.report:
        print("\nCalibration Report:")
        print("=" * 50)
        report = calibrator.get_calibration_report()

        if "global_metrics" in report and report["global_metrics"]:
            gm = report["global_metrics"]
            print("\nGlobal Metrics:")
            print(f"  Sample size: {gm['sample_size']}")
            print(f"  Brier score: {gm['brier_score']:.4f} (lower is better)")
            print(f"  Calibration error: {gm['calibration_error']:.4f}")

        if report.get("recommendations"):
            print("\nRecommendations:")
            for rec in report["recommendations"]:
                print(f"  • {rec}")

        if report.get("drift_alerts"):
            print("\nDrift Alerts:")
            for alert in report["drift_alerts"]:
                print(f"  ⚠ {alert}")

    if args.table:
        print("\nReliability Table:")
        print(calibrator.get_reliability_table())

    if args.test is not None:
        calibrated, info = calibrator.calibrate(args.test)
        print("\nTest Calibration:")
        print(f"  Raw confidence: {args.test:.0%}")
        print(f"  Calibrated: {calibrated:.0%}")
        print(f"  Adjustment: {info.get('adjustment', 0):+.1%}")
        print(f"  Status: {info.get('calibration', 'unknown')}")
