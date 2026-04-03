#!/usr/bin/env python3
"""
UATP Outcome Recorder
=====================

Records actual outcomes for capsules to enable calibration measurement.

When you know whether a model's response was correct/helpful/accurate,
use this tool to record that outcome. This creates evidence that can be
compared against the model's self-assessment.

Usage:
    # Record a successful outcome
    python -m src.integrations.outcome_recorder CAPSULE_ID --worked "Tests passed"

    # Record a failure
    python -m src.integrations.outcome_recorder CAPSULE_ID --failed "Code had bugs"

    # Record partial success
    python -m src.integrations.outcome_recorder CAPSULE_ID --partial "Some parts worked"

    # List capsules awaiting outcomes
    python -m src.integrations.outcome_recorder --list-pending

    # View calibration summary
    python -m src.integrations.outcome_recorder --calibration-summary
"""

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# UATP imports
try:
    from src.core.provenance import EpistemicClass, ProofLevel
    from src.security.uatp_crypto_v7 import UATPCryptoV7

    _UATP_AVAILABLE = True
except ImportError:
    _UATP_AVAILABLE = False
    EpistemicClass = None


class OutcomeType(str, Enum):
    """Types of outcomes that can be recorded."""

    # Direct outcomes - we know what happened
    WORKED = "worked"  # The suggestion/code/answer was correct
    FAILED = "failed"  # It was wrong or didn't work
    PARTIAL = "partial"  # Some parts worked, others didn't

    # Inferred outcomes - we infer from user behavior
    ACCEPTED = "accepted"  # User used/accepted the response
    REJECTED = "rejected"  # User explicitly rejected
    REFINED = "refined"  # User asked for modifications
    ABANDONED = "abandoned"  # User moved on without using

    # Unknown
    UNKNOWN = "unknown"  # We don't know what happened


class OutcomeRecorder:
    """Records outcomes for UATP capsules."""

    def __init__(self, db_path: str = "uatp_dev.db"):
        self.db_path = db_path

        # Initialize crypto for signing
        self._crypto = None
        if _UATP_AVAILABLE:
            try:
                self._crypto = UATPCryptoV7(
                    key_dir=".uatp_keys",
                    signer_id="outcome_recorder",
                    enable_pq=True,
                )
            except Exception as e:
                logger.warning(f"Crypto not available: {e}")

    def get_capsule(self, capsule_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a capsule from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT capsule_id, capsule_type, payload, verification,
                       outcome_status, parent_capsule_id
                FROM capsules WHERE capsule_id = ?
                """,
                (capsule_id,),
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return {
                "capsule_id": row[0],
                "capsule_type": row[1],
                "payload": json.loads(row[2]) if row[2] else {},
                "verification": json.loads(row[3]) if row[3] else {},
                "outcome_status": row[4],
                "parent_capsule_id": row[5],
            }
        except Exception as e:
            logger.error(f"Failed to fetch capsule: {e}")
            return None

    def get_self_assessment(self, parent_capsule_id: str) -> Optional[Dict[str, Any]]:
        """Get the self-assessment capsule for a parent capsule."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT capsule_id, payload
                FROM capsules
                WHERE parent_capsule_id = ?
                AND capsule_type = 'model_self_assessment'
                """,
                (parent_capsule_id,),
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return {
                "capsule_id": row[0],
                "payload": json.loads(row[1]) if row[1] else {},
            }
        except Exception as e:
            logger.error(f"Failed to fetch self-assessment: {e}")
            return None

    def record_outcome(
        self,
        capsule_id: str,
        outcome_type: OutcomeType,
        notes: str = None,
        confidence: float = 1.0,
        recorded_by: str = "human",
    ) -> Optional[str]:
        """
        Record an outcome for a capsule.

        This updates the original capsule's outcome fields AND creates
        a new outcome capsule linked to both the original and self-assessment.

        Args:
            capsule_id: The capsule to record outcome for
            outcome_type: What happened (worked, failed, partial, etc.)
            notes: Optional notes about the outcome
            confidence: How confident we are in this outcome (default 1.0 for human)
            recorded_by: Who recorded this (human, system, test_suite, etc.)

        Returns:
            The outcome capsule ID, or None if failed
        """
        # Verify the capsule exists
        capsule = self.get_capsule(capsule_id)
        if not capsule:
            logger.error(f"Capsule {capsule_id} not found")
            return None

        # Check if outcome already recorded
        if capsule.get("outcome_status"):
            logger.warning(
                f"Capsule {capsule_id} already has outcome: {capsule['outcome_status']}"
            )
            # Still allow overwriting

        # Get self-assessment if exists
        self_assessment = self.get_self_assessment(capsule_id)
        predicted_confidence = None
        if self_assessment:
            assessment = self_assessment["payload"].get("assessment", {})
            predicted_confidence = assessment.get("confidence_estimate")

        now = datetime.now(timezone.utc)
        outcome_capsule_id = f"{capsule_id}_outcome"

        # Determine epistemic class based on who recorded
        ec_value = "measured_outcome"
        if recorded_by == "human":
            ec_value = "human_verified"
        elif recorded_by in ("test_suite", "ci", "system"):
            ec_value = "system_verified"

        # Calculate deviation if we have self-assessment
        deviation_score = None
        if predicted_confidence is not None:
            # Map outcome to binary success
            outcome_success = (
                1.0
                if outcome_type == OutcomeType.WORKED
                else (0.5 if outcome_type == OutcomeType.PARTIAL else 0.0)
            )
            # Deviation = how wrong the confidence was
            # Positive = overconfident, Negative = underconfident
            deviation_score = predicted_confidence - outcome_success

        # Create outcome capsule
        outcome_capsule = {
            "capsule_id": outcome_capsule_id,
            "capsule_type": "measured_outcome",
            "parent_capsule_id": capsule_id,
            "timestamp": now.isoformat(),
            "version": "1.1",
            "status": "verified",
            "payload": {
                "schema_version": "2.0_layered",
                "epistemic_class": ec_value,
                "outcome": {
                    "type": outcome_type.value,
                    "confidence": confidence,
                    "notes": notes,
                    "recorded_by": recorded_by,
                    "recorded_at": now.isoformat(),
                },
                "linked_capsules": {
                    "original_response": capsule_id,
                    "self_assessment": self_assessment["capsule_id"]
                    if self_assessment
                    else None,
                },
                "calibration": {
                    "predicted_confidence": predicted_confidence,
                    "actual_outcome": outcome_type.value,
                    "deviation_score": deviation_score,
                },
                "layers": {
                    "events": [
                        {
                            "event_type": "outcome_recorded",
                            "timestamp": now.isoformat(),
                            "data": {
                                "outcome_type": outcome_type.value,
                                "recorded_by": recorded_by,
                            },
                            "proof": "tool_verified",
                            "epistemic_class": "tool_observed",
                            "source": "outcome_recorder",
                        }
                    ],
                    "evidence": [
                        {
                            "claim": f"Outcome '{outcome_type.value}' was recorded",
                            "verified": True,
                            "proof": "human_verified"
                            if recorded_by == "human"
                            else "tool_verified",
                            "epistemic_class": ec_value,
                            "verification_method": recorded_by,
                        }
                    ],
                    "interpretation": {
                        "summary": f"Outcome: {outcome_type.value}",
                        "status": "verified",  # Outcomes are evidence, not interpretation
                        "epistemic_class": ec_value,
                    },
                    "judgment": {
                        "gates_passed": ["outcome_verified"],
                        "court_admissible": recorded_by == "human",
                        "blockers": []
                        if recorded_by == "human"
                        else ["System-recorded outcome"],
                    },
                },
                "trust_posture": {
                    "provenance_integrity": "high",
                    "artifact_verifiability": "high"
                    if recorded_by == "human"
                    else "medium",
                    "semantic_alignment": "verified",
                    "decision_completeness": "complete",
                    "risk_calibration": "measured",
                    "legal_reliance_readiness": "ready"
                    if recorded_by == "human"
                    else "partial",
                    "operational_utility": "high",
                },
            },
            "verification": {},
        }

        # Sign if crypto available
        if self._crypto and self._crypto.enabled:
            try:
                verification = self._crypto.sign_capsule(
                    outcome_capsule, timestamp_mode="local"
                )
                outcome_capsule["verification"] = verification
            except Exception as e:
                logger.warning(f"Signing failed: {e}")

        # Save to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Update original capsule's outcome fields
            cursor.execute(
                """
                UPDATE capsules SET
                    outcome_status = ?,
                    outcome_timestamp = ?,
                    outcome_notes = ?,
                    outcome_metrics = ?
                WHERE capsule_id = ?
                """,
                (
                    outcome_type.value,
                    now.isoformat(),
                    notes,
                    json.dumps(
                        {
                            "confidence": confidence,
                            "recorded_by": recorded_by,
                            "deviation_score": deviation_score,
                        }
                    ),
                    capsule_id,
                ),
            )

            # Also update self-assessment's calibration if exists
            if self_assessment:
                cursor.execute(
                    """
                    UPDATE capsules SET
                        payload = json_set(
                            payload,
                            '$.calibration.outcome_recorded', true,
                            '$.calibration.outcome_capsule_id', ?,
                            '$.calibration.deviation_score', ?
                        )
                    WHERE capsule_id = ?
                    """,
                    (
                        outcome_capsule_id,
                        deviation_score,
                        self_assessment["capsule_id"],
                    ),
                )

            # Insert outcome capsule
            cursor.execute(
                """
                INSERT INTO capsules (
                    capsule_id, capsule_type, version, timestamp, status,
                    verification, payload, parent_capsule_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    outcome_capsule["capsule_id"],
                    outcome_capsule["capsule_type"],
                    outcome_capsule["version"],
                    outcome_capsule["timestamp"],
                    outcome_capsule["status"],
                    json.dumps(outcome_capsule["verification"]),
                    json.dumps(outcome_capsule["payload"]),
                    outcome_capsule["parent_capsule_id"],
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"Outcome recorded for {capsule_id}: {outcome_type.value}")
            if deviation_score is not None:
                logger.info(f"Calibration deviation: {deviation_score:+.2f}")

            return outcome_capsule_id

        except Exception as e:
            logger.error(f"Failed to save outcome: {e}")
            return None

    def list_pending_outcomes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List capsules that have self-assessments but no outcomes yet."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    c.capsule_id,
                    c.timestamp,
                    c.capsule_type,
                    json_extract(c.payload, '$.prompt') as prompt,
                    json_extract(sa.payload, '$.assessment.confidence_estimate') as confidence
                FROM capsules c
                JOIN capsules sa ON sa.parent_capsule_id = c.capsule_id
                WHERE sa.capsule_type = 'model_self_assessment'
                AND c.outcome_status IS NULL
                ORDER BY c.timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "capsule_id": row[0],
                    "timestamp": row[1],
                    "type": row[2],
                    "prompt": row[3][:100] if row[3] else None,
                    "predicted_confidence": row[4],
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Failed to list pending: {e}")
            return []

    def get_calibration_summary(self) -> Dict[str, Any]:
        """Get a summary of calibration across all capsules with outcomes."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all capsules with both self-assessment and outcomes
            cursor.execute(
                """
                SELECT
                    json_extract(sa.payload, '$.assessment.confidence_estimate') as predicted,
                    c.outcome_status,
                    json_extract(c.outcome_metrics, '$.deviation_score') as deviation
                FROM capsules c
                JOIN capsules sa ON sa.parent_capsule_id = c.capsule_id
                WHERE sa.capsule_type = 'model_self_assessment'
                AND c.outcome_status IS NOT NULL
                """
            )
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return {
                    "total_with_outcomes": 0,
                    "message": "No capsules with both self-assessment and outcomes yet",
                }

            # Calculate calibration metrics
            total = len(rows)
            deviations = [r[2] for r in rows if r[2] is not None]
            predictions = [r[0] for r in rows if r[0] is not None]
            outcomes = [r[1] for r in rows]

            # Outcome distribution
            outcome_counts = {}
            for o in outcomes:
                outcome_counts[o] = outcome_counts.get(o, 0) + 1

            # Average deviation (positive = overconfident)
            avg_deviation = sum(deviations) / len(deviations) if deviations else None

            # Confidence buckets
            confidence_buckets = {
                "0.0-0.3": [],
                "0.3-0.6": [],
                "0.6-0.8": [],
                "0.8-1.0": [],
            }
            for pred, outcome in zip(predictions, outcomes, strict=True):
                if pred is not None:
                    success = (
                        1.0
                        if outcome == "worked"
                        else (0.5 if outcome == "partial" else 0.0)
                    )
                    if pred < 0.3:
                        confidence_buckets["0.0-0.3"].append(success)
                    elif pred < 0.6:
                        confidence_buckets["0.3-0.6"].append(success)
                    elif pred < 0.8:
                        confidence_buckets["0.6-0.8"].append(success)
                    else:
                        confidence_buckets["0.8-1.0"].append(success)

            # Calculate accuracy per bucket
            bucket_accuracy = {}
            for bucket, successes in confidence_buckets.items():
                if successes:
                    bucket_accuracy[bucket] = {
                        "count": len(successes),
                        "actual_accuracy": sum(successes) / len(successes),
                    }

            return {
                "total_with_outcomes": total,
                "outcome_distribution": outcome_counts,
                "average_deviation": avg_deviation,
                "overconfident": avg_deviation > 0.1 if avg_deviation else None,
                "underconfident": avg_deviation < -0.1 if avg_deviation else None,
                "confidence_buckets": bucket_accuracy,
                "interpretation": self._interpret_calibration(
                    avg_deviation, bucket_accuracy
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get calibration summary: {e}")
            return {"error": str(e)}

    def _interpret_calibration(
        self, avg_deviation: Optional[float], bucket_accuracy: Dict[str, Any]
    ) -> str:
        """Generate human-readable interpretation of calibration."""
        if avg_deviation is None:
            return "Insufficient data for calibration analysis."

        parts = []

        if avg_deviation > 0.2:
            parts.append(
                "Model is significantly OVERCONFIDENT (claims higher confidence than actual accuracy)."
            )
        elif avg_deviation > 0.1:
            parts.append("Model is moderately overconfident.")
        elif avg_deviation < -0.2:
            parts.append(
                "Model is significantly UNDERCONFIDENT (more accurate than it claims)."
            )
        elif avg_deviation < -0.1:
            parts.append("Model is moderately underconfident.")
        else:
            parts.append("Model is reasonably well-calibrated.")

        # Check specific buckets
        high_conf = bucket_accuracy.get("0.8-1.0", {})
        if high_conf.get("count", 0) >= 3:
            actual = high_conf.get("actual_accuracy", 0)
            if actual < 0.6:
                parts.append(
                    f"WARNING: High-confidence predictions (0.8-1.0) only {actual:.0%} accurate."
                )

        return " ".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="UATP Outcome Recorder - Record actual outcomes to measure calibration"
    )
    parser.add_argument(
        "capsule_id",
        nargs="?",
        help="The capsule ID to record outcome for",
    )
    parser.add_argument(
        "--worked",
        "-w",
        metavar="NOTES",
        help="Record success outcome with optional notes",
    )
    parser.add_argument(
        "--failed",
        "-f",
        metavar="NOTES",
        help="Record failure outcome with optional notes",
    )
    parser.add_argument(
        "--partial",
        "-p",
        metavar="NOTES",
        help="Record partial success with optional notes",
    )
    parser.add_argument(
        "--list-pending",
        "-l",
        action="store_true",
        help="List capsules awaiting outcomes",
    )
    parser.add_argument(
        "--calibration-summary",
        "-c",
        action="store_true",
        help="Show calibration summary across all outcomes",
    )
    parser.add_argument(
        "--db",
        default="uatp_dev.db",
        help="Database path (default: uatp_dev.db)",
    )

    args = parser.parse_args()
    recorder = OutcomeRecorder(db_path=args.db)

    if args.list_pending:
        pending = recorder.list_pending_outcomes()
        if not pending:
            print("No capsules awaiting outcomes.")
        else:
            print(f"\nCapsules awaiting outcomes ({len(pending)}):\n")
            print(f"{'Capsule ID':<45} {'Confidence':<12} {'Prompt'}")
            print("-" * 80)
            for p in pending:
                conf = (
                    f"{p['predicted_confidence']:.2f}"
                    if p["predicted_confidence"]
                    else "N/A"
                )
                prompt = (p["prompt"][:30] + "...") if p["prompt"] else "N/A"
                print(f"{p['capsule_id']:<45} {conf:<12} {prompt}")
        return

    if args.calibration_summary:
        summary = recorder.get_calibration_summary()
        print("\n" + "=" * 60)
        print("CALIBRATION SUMMARY")
        print("=" * 60)
        print(f"Total capsules with outcomes: {summary.get('total_with_outcomes', 0)}")
        if summary.get("outcome_distribution"):
            print("\nOutcome distribution:")
            for outcome, count in summary["outcome_distribution"].items():
                print(f"  {outcome}: {count}")
        if summary.get("average_deviation") is not None:
            print(f"\nAverage deviation: {summary['average_deviation']:+.3f}")
            print("  (positive = overconfident, negative = underconfident)")
        if summary.get("confidence_buckets"):
            print("\nCalibration by confidence bucket:")
            for bucket, data in summary["confidence_buckets"].items():
                print(
                    f"  {bucket}: {data['actual_accuracy']:.0%} accurate (n={data['count']})"
                )
        if summary.get("interpretation"):
            print(f"\nInterpretation: {summary['interpretation']}")
        print("=" * 60)
        return

    # Record outcome
    if not args.capsule_id:
        parser.print_help()
        sys.exit(1)

    if args.worked is not None:
        outcome_id = recorder.record_outcome(
            args.capsule_id, OutcomeType.WORKED, notes=args.worked
        )
    elif args.failed is not None:
        outcome_id = recorder.record_outcome(
            args.capsule_id, OutcomeType.FAILED, notes=args.failed
        )
    elif args.partial is not None:
        outcome_id = recorder.record_outcome(
            args.capsule_id, OutcomeType.PARTIAL, notes=args.partial
        )
    else:
        print("Error: Must specify --worked, --failed, or --partial")
        sys.exit(1)

    if outcome_id:
        print(f"\nOutcome recorded: {outcome_id}")
        print("Run --calibration-summary to see updated calibration metrics.")
    else:
        print("Failed to record outcome.")
        sys.exit(1)


if __name__ == "__main__":
    main()
