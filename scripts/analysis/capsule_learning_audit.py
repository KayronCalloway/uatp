#!/usr/bin/env python3
"""Read-only capsule learning audit for UATP/Hermes.

This script intentionally does not write to the database. It summarizes whether
existing capsule data is clean enough to promote into learning rules, skills,
preference data, or model-routing evals.
"""

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from scripts.analysis.hermes_signal_filters import is_hermes_meta_message

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "uatp_dev.db"
NEGATIVE_SIGNALS = {"correction", "requery", "abandonment", "soft_rejection"}


def step_text(step: dict[str, Any]) -> str:
    return str(step.get("reasoning") or step.get("content") or "")


def step_signal(step: dict[str, Any]) -> str:
    measurements = step.get("measurements") or {}
    return str(step.get("signal_type") or measurements.get("signal_type") or "neutral")


def is_meta_message(text: str) -> bool:
    return is_hermes_meta_message(text)


def extract_model(payload: dict[str, Any]) -> str:
    session_metadata = payload.get("session_metadata") or {}
    metadata = payload.get("metadata") or {}
    return str(
        payload.get("model_used")
        or payload.get("model")
        or session_metadata.get("hermes_model")
        or metadata.get("model")
        or "unknown"
    )


def audit(db_path: Path = DB_PATH) -> dict[str, Any]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT capsule_id, capsule_type, payload, timestamp FROM capsules ORDER BY timestamp DESC"
        ).fetchall()
    except sqlite3.OperationalError as exc:
        if "no such table: capsules" not in str(exc).lower():
            raise
        rows = []
    finally:
        conn.close()

    capsule_types = Counter(row[1] for row in rows)
    signal_counts = Counter()
    user_signal_counts = Counter()
    meta_signal_counts = Counter()
    role_counts = Counter()
    model_counts = Counter()
    text_fields = Counter()
    steps_per_hermes: list[int] = []
    approx_negative_chains = 0
    noisy_examples: dict[str, list[str]] = defaultdict(list)

    for _capsule_id, capsule_type, payload_str, _timestamp in rows:
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            continue

        if capsule_type == "hermes-capture":
            model_counts[extract_model(payload)] += 1
            steps = payload.get("reasoning_steps") or []
            steps_per_hermes.append(len(steps))
            previous_assistant_has_text = False

            for step in steps:
                role = step.get("role", "unknown")
                role_counts[role] += 1
                signal = step_signal(step)
                signal_counts[signal] += 1
                text = step_text(step)

                if step.get("reasoning"):
                    text_fields["reasoning"] += 1
                if step.get("content"):
                    text_fields["content"] += 1
                if not text:
                    text_fields["missing"] += 1

                if role == "user":
                    user_signal_counts[signal] += 1
                    if is_meta_message(text):
                        meta_signal_counts[signal] += 1
                        if signal != "neutral" and len(noisy_examples[signal]) < 3:
                            noisy_examples[signal].append(text[:180])
                    if signal in NEGATIVE_SIGNALS and previous_assistant_has_text:
                        approx_negative_chains += 1

                previous_assistant_has_text = role == "assistant" and bool(text.strip())

    hermes_count = capsule_types.get("hermes-capture", 0)
    user_steps = sum(user_signal_counts.values())
    non_neutral_user = user_steps - user_signal_counts.get("neutral", 0)

    return {
        "db_path": str(db_path),
        "capsules_total": len(rows),
        "capsule_types": dict(capsule_types.most_common()),
        "hermes": {
            "capsules": hermes_count,
            "steps_total": sum(steps_per_hermes),
            "steps_per_capsule": {
                "min": min(steps_per_hermes) if steps_per_hermes else 0,
                "median": sorted(steps_per_hermes)[len(steps_per_hermes) // 2]
                if steps_per_hermes
                else 0,
                "max": max(steps_per_hermes) if steps_per_hermes else 0,
            },
            "role_counts": dict(role_counts),
            "all_signal_counts": dict(signal_counts),
            "user_signal_counts": dict(user_signal_counts),
            "user_non_neutral_rate": round(non_neutral_user / user_steps, 4)
            if user_steps
            else 0.0,
            "meta_signal_counts": dict(meta_signal_counts),
            "noisy_meta_examples": dict(noisy_examples),
            "approx_negative_chains": approx_negative_chains,
            "text_fields": dict(text_fields),
            "models_top": dict(model_counts.most_common(15)),
        },
        "recommendation": {
            "safe_to_finetune_raw": False,
            "safe_to_use_for_behavioral_rules": True,
            "next_gate": "Use cleaned correction chains and held-out evals before promotion.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="SQLite DB path")
    args = parser.parse_args()

    report = audit(args.db)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    hermes = report["hermes"]
    print(f"DB: {report['db_path']}")
    print(f"Capsules total: {report['capsules_total']}")
    print(f"Capsule types: {report['capsule_types']}")
    print(f"Hermes capsules: {hermes['capsules']}")
    print(f"Hermes user signals: {hermes['user_signal_counts']}")
    print(f"Noisy meta signals: {hermes['meta_signal_counts']}")
    print(f"Approx negative chains: {hermes['approx_negative_chains']}")
    print(f"Text fields: {hermes['text_fields']}")
    print(f"Recommendation: {report['recommendation']['next_gate']}")


if __name__ == "__main__":
    main()
