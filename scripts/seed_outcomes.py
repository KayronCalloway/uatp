#!/usr/bin/env python3
"""
Seed outcomes for capsules to bootstrap ML training.

Uses heuristics based on:
- Confidence scores
- Content analysis (errors, success indicators)
- Random sampling for diversity
"""

import json
import os
import random
import sqlite3
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def extract_signals(payload: dict) -> dict:
    """Extract outcome signals from payload."""
    signals = {
        "confidence": payload.get("confidence", 0.5),
        "has_error_mentions": False,
        "has_success_mentions": False,
        "step_count": 0,
        "has_final_answer": bool(payload.get("final_answer")),
    }

    # Check reasoning steps
    steps = payload.get("reasoning_steps", [])
    signals["step_count"] = len(steps)

    text_content = json.dumps(payload).lower()

    # Error indicators
    error_words = [
        "error",
        "failed",
        "exception",
        "broken",
        "wrong",
        "issue",
        "bug",
        "crash",
    ]
    signals["has_error_mentions"] = any(w in text_content for w in error_words)

    # Success indicators
    success_words = [
        "success",
        "works",
        "fixed",
        "resolved",
        "complete",
        "implemented",
        "done",
    ]
    signals["has_success_mentions"] = any(w in text_content for w in success_words)

    return signals


def infer_outcome(signals: dict) -> tuple:
    """
    Infer outcome status and confidence.
    Returns (status, confidence, notes).
    """
    conf = signals["confidence"]

    # High confidence + success indicators = success
    if (
        conf >= 0.7
        and signals["has_success_mentions"]
        and not signals["has_error_mentions"]
    ):
        return (
            "success",
            0.8 + random.uniform(-0.1, 0.15),
            "High confidence with success indicators",
        )

    # Error mentions = failure
    if signals["has_error_mentions"] and not signals["has_success_mentions"]:
        return ("failure", 0.7 + random.uniform(-0.1, 0.1), "Error indicators detected")

    # Low confidence = partial
    if conf < 0.5:
        return ("partial", 0.6 + random.uniform(-0.1, 0.1), "Low confidence reasoning")

    # Good confidence with final answer = success
    if conf >= 0.6 and signals["has_final_answer"] and signals["step_count"] >= 3:
        return (
            "success",
            0.7 + random.uniform(-0.1, 0.1),
            "Complete reasoning with answer",
        )

    # Mixed signals = partial
    if signals["has_error_mentions"] and signals["has_success_mentions"]:
        return (
            "partial",
            0.65 + random.uniform(-0.05, 0.05),
            "Mixed success/error signals",
        )

    # Default: use confidence as guide
    if conf >= 0.65:
        return (
            "success",
            conf * 0.9 + random.uniform(-0.05, 0.05),
            "Confidence-based inference",
        )
    elif conf >= 0.45:
        return ("partial", conf + random.uniform(-0.05, 0.05), "Medium confidence")
    else:
        return ("failure", 0.6 + random.uniform(-0.1, 0.1), "Low confidence inference")


def seed_outcomes(db_path: str, limit: int = 50):
    """Seed outcomes for capsules."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Get capsules without outcomes
    cur.execute(
        """
        SELECT capsule_id, payload
        FROM capsules
        WHERE outcome_status IS NULL
            AND capsule_id NOT LIKE 'demo-%'
            AND capsule_id NOT LIKE 'test_%'
        ORDER BY timestamp DESC
        LIMIT ?
    """,
        (limit,),
    )

    rows = cur.fetchall()
    if not rows:
        print("No capsules need outcomes")
        return

    print(f"Seeding outcomes for {len(rows)} capsules...")

    outcomes = {"success": 0, "failure": 0, "partial": 0}

    for row in rows:
        payload = row["payload"]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except:
                payload = {}

        signals = extract_signals(payload)
        status, conf, notes = infer_outcome(signals)

        cur.execute(
            """
            UPDATE capsules SET
                outcome_status = ?,
                outcome_timestamp = ?,
                outcome_notes = ?,
                outcome_metrics = ?
            WHERE capsule_id = ?
        """,
            (
                status,
                datetime.now(timezone.utc).isoformat(),
                f"Auto-seeded: {notes}",
                json.dumps(
                    {
                        "inference_confidence": round(conf, 3),
                        "method": "heuristic_seeding",
                    }
                ),
                row["capsule_id"],
            ),
        )
        outcomes[status] += 1

    conn.commit()
    conn.close()

    print(f"Done! Outcomes: {outcomes}")


if __name__ == "__main__":
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uatp_dev.db"
    )
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    seed_outcomes(db_path, limit)
