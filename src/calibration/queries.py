"""
Calibration Queries - SQL queries for extracting calibration data.

These queries join original capsules with their self-assessments and outcomes
to enable comparison between predicted confidence and actual results.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CalibrationDataPoint:
    """A single data point for calibration analysis."""

    capsule_id: str
    timestamp: datetime

    # From self-assessment (model claim - hypothesis to test)
    claimed_confidence: float
    uncertainty_areas: List[str]
    assumptions_made: List[str]
    potential_errors: List[str]

    # From outcome (measured - ground truth)
    outcome_type: str  # worked, failed, partial
    outcome_confidence: float
    outcome_evidence: Optional[str]

    # Calculated
    deviation: float  # outcome_success - claimed_confidence

    # Context
    prompt_preview: str
    model: str


class CalibrationQueries:
    """SQL queries for calibration data extraction."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Use default database path
            db_path = str(Path(__file__).parent.parent.parent / "uatp_dev.db")
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_calibration_data(
        self,
        model: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[CalibrationDataPoint]:
        """
        Get calibration data points for analysis.

        Joins original capsules with their self-assessments and outcomes.
        """
        query = """
        SELECT
            original.capsule_id,
            original.timestamp,
            original.payload as original_payload,
            self_assess.payload as assessment_payload,
            outcome.payload as outcome_payload
        FROM capsules original
        JOIN capsules self_assess
            ON self_assess.parent_capsule_id = original.capsule_id
            AND self_assess.capsule_type = 'model_self_assessment'
        JOIN capsules outcome
            ON outcome.parent_capsule_id = original.capsule_id
            AND outcome.capsule_type = 'measured_outcome'
        WHERE 1=1
        """
        params: List[Any] = []

        if model:
            query += " AND original.capsule_id LIKE ?"
            params.append(f"%{model}%")

        if since:
            query += " AND original.timestamp >= ?"
            params.append(since.isoformat())

        query += " ORDER BY original.timestamp DESC LIMIT ?"
        params.append(limit)

        conn = self._get_connection()
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        data_points = []
        for row in rows:
            try:
                original_payload = (
                    json.loads(row["original_payload"])
                    if row["original_payload"]
                    else {}
                )
                assessment_payload = (
                    json.loads(row["assessment_payload"])
                    if row["assessment_payload"]
                    else {}
                )
                outcome_payload = (
                    json.loads(row["outcome_payload"]) if row["outcome_payload"] else {}
                )

                # Extract self-assessment data
                assessment = assessment_payload.get("assessment", {})
                claimed_confidence = assessment.get("confidence_estimate", 0.5)

                # Extract outcome data
                outcome = outcome_payload.get("outcome", {})
                outcome_type = outcome.get("type", "unknown")
                outcome_confidence = outcome.get("confidence", 0.5)

                # Calculate success value for deviation
                success_value = {
                    "worked": 1.0,
                    "partial": 0.5,
                    "accepted": 0.8,
                    "refined": 0.6,
                    "failed": 0.0,
                    "rejected": 0.0,
                    "abandoned": 0.0,
                }.get(outcome_type, 0.5)

                deviation = success_value - claimed_confidence

                # Extract prompt preview from original
                prompt = original_payload.get("prompt", "")
                if isinstance(prompt, dict):
                    prompt = prompt.get("content", str(prompt))
                prompt_preview = (
                    str(prompt)[:100] + "..." if len(str(prompt)) > 100 else str(prompt)
                )

                # Extract model from capsule_id
                model_name = "unknown"
                if "gemma" in row["capsule_id"].lower():
                    model_name = "gemma"
                elif "claude" in row["capsule_id"].lower():
                    model_name = "claude"

                data_points.append(
                    CalibrationDataPoint(
                        capsule_id=row["capsule_id"],
                        timestamp=datetime.fromisoformat(row["timestamp"])
                        if row["timestamp"]
                        else datetime.now(),
                        claimed_confidence=claimed_confidence,
                        uncertainty_areas=assessment.get("uncertainty_areas", []),
                        assumptions_made=assessment.get("assumptions_made", []),
                        potential_errors=assessment.get("potential_errors", []),
                        outcome_type=outcome_type,
                        outcome_confidence=outcome_confidence,
                        outcome_evidence=outcome.get("evidence"),
                        deviation=deviation,
                        prompt_preview=prompt_preview,
                        model=model_name,
                    )
                )
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                # Skip malformed records
                continue

        return data_points

    def get_confidence_buckets(self) -> Dict[str, Tuple[int, int]]:
        """
        Get accuracy by confidence bucket.

        Returns dict: {"0.0-0.3": (correct_count, total_count), ...}
        """
        data_points = self.get_calibration_data()

        buckets = {
            "0.0-0.3": [0, 0],  # [correct, total]
            "0.3-0.5": [0, 0],
            "0.5-0.7": [0, 0],
            "0.7-0.9": [0, 0],
            "0.9-1.0": [0, 0],
        }

        for dp in data_points:
            # Determine bucket
            conf = dp.claimed_confidence
            if conf < 0.3:
                bucket = "0.0-0.3"
            elif conf < 0.5:
                bucket = "0.3-0.5"
            elif conf < 0.7:
                bucket = "0.5-0.7"
            elif conf < 0.9:
                bucket = "0.7-0.9"
            else:
                bucket = "0.9-1.0"

            # Count
            buckets[bucket][1] += 1
            if dp.outcome_type in ("worked", "accepted"):
                buckets[bucket][0] += 1
            elif dp.outcome_type == "partial":
                buckets[bucket][0] += 0.5

        return {k: tuple(v) for k, v in buckets.items()}

    def get_uncertainty_hit_rate(self) -> Tuple[float, int]:
        """
        Calculate how often flagged uncertainties were actual error sources.

        Returns (hit_rate, sample_size).
        """
        data_points = self.get_calibration_data()

        hits = 0
        total_with_uncertainties = 0

        for dp in data_points:
            if dp.uncertainty_areas and dp.outcome_type in (
                "failed",
                "partial",
                "rejected",
            ):
                total_with_uncertainties += 1
                # Check if any flagged uncertainty appears in outcome evidence
                if dp.outcome_evidence:
                    evidence_lower = dp.outcome_evidence.lower()
                    for uncertainty in dp.uncertainty_areas:
                        if any(
                            word in evidence_lower
                            for word in uncertainty.lower().split()
                        ):
                            hits += 1
                            break

        if total_with_uncertainties == 0:
            return 0.0, 0

        return hits / total_with_uncertainties, total_with_uncertainties

    def get_missed_error_rate(self) -> Tuple[float, int]:
        """
        Calculate how often errors occurred in areas the model claimed certainty.

        Returns (miss_rate, sample_size).
        """
        data_points = self.get_calibration_data()

        misses = 0
        high_confidence_failures = 0

        for dp in data_points:
            # High confidence (>0.7) but failed
            if dp.claimed_confidence > 0.7 and dp.outcome_type in (
                "failed",
                "rejected",
            ):
                high_confidence_failures += 1
                # Check if error was NOT in flagged uncertainties
                if not dp.uncertainty_areas:
                    misses += 1
                elif dp.outcome_evidence:
                    evidence_lower = dp.outcome_evidence.lower()
                    uncertainty_words = set()
                    for u in dp.uncertainty_areas:
                        uncertainty_words.update(u.lower().split())
                    if not any(word in evidence_lower for word in uncertainty_words):
                        misses += 1

        if high_confidence_failures == 0:
            return 0.0, 0

        return misses / high_confidence_failures, high_confidence_failures

    def get_by_model(self) -> Dict[str, List[CalibrationDataPoint]]:
        """Group calibration data by model."""
        data_points = self.get_calibration_data()

        by_model: Dict[str, List[CalibrationDataPoint]] = {}
        for dp in data_points:
            if dp.model not in by_model:
                by_model[dp.model] = []
            by_model[dp.model].append(dp)

        return by_model

    def get_capsules_pending_outcomes(self) -> List[Dict[str, Any]]:
        """
        Get capsules that have self-assessments but no outcomes yet.

        These are candidates for outcome recording.
        """
        query = """
        SELECT
            original.capsule_id,
            original.timestamp,
            original.payload as original_payload,
            self_assess.payload as assessment_payload
        FROM capsules original
        JOIN capsules self_assess
            ON self_assess.parent_capsule_id = original.capsule_id
            AND self_assess.capsule_type = 'model_self_assessment'
        LEFT JOIN capsules outcome
            ON outcome.parent_capsule_id = original.capsule_id
            AND outcome.capsule_type = 'measured_outcome'
        WHERE outcome.capsule_id IS NULL
        ORDER BY original.timestamp DESC
        """

        conn = self._get_connection()
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            try:
                original_payload = (
                    json.loads(row["original_payload"])
                    if row["original_payload"]
                    else {}
                )
                assessment_payload = (
                    json.loads(row["assessment_payload"])
                    if row["assessment_payload"]
                    else {}
                )

                assessment = assessment_payload.get("assessment", {})
                prompt = original_payload.get("prompt", "")
                if isinstance(prompt, dict):
                    prompt = prompt.get("content", str(prompt))

                results.append(
                    {
                        "capsule_id": row["capsule_id"],
                        "timestamp": row["timestamp"],
                        "claimed_confidence": assessment.get(
                            "confidence_estimate", "N/A"
                        ),
                        "prompt_preview": str(prompt)[:80] + "..."
                        if len(str(prompt)) > 80
                        else str(prompt),
                    }
                )
            except (json.JSONDecodeError, KeyError):
                continue

        return results


if __name__ == "__main__":
    # Test queries
    queries = CalibrationQueries()

    print("=== Calibration Data ===")
    data = queries.get_calibration_data()
    for dp in data[:5]:
        print(
            f"  {dp.capsule_id}: claimed={dp.claimed_confidence:.2f}, "
            f"outcome={dp.outcome_type}, deviation={dp.deviation:+.2f}"
        )

    print("\n=== Confidence Buckets ===")
    buckets = queries.get_confidence_buckets()
    for bucket, (correct, total) in buckets.items():
        if total > 0:
            print(f"  {bucket}: {correct}/{total} ({100 * correct / total:.0f}%)")

    print("\n=== Pending Outcomes ===")
    pending = queries.get_capsules_pending_outcomes()
    print(f"  {len(pending)} capsules awaiting outcomes")
