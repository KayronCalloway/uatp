#!/usr/bin/env python3
"""Build a held-out Hermes capsule learning eval set.

This script is read-only unless --output is provided. It extracts ordered
correction chains that can be used to evaluate future behavior-policy changes
before any learning signal is promoted.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.analysis.hermes_signal_filters import is_hermes_meta_message

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "uatp_dev.db"
NEGATIVE_SIGNALS = {"correction", "requery", "abandonment", "soft_rejection"}


CapsuleRow = dict[str, Any]
EvalRecord = dict[str, Any]


def step_text(step: dict[str, Any]) -> str:
    return str(step.get("reasoning") or step.get("content") or "").strip()


def step_signal(step: dict[str, Any]) -> str:
    signal = step.get("signal_type")
    if signal:
        return str(signal)
    measurements = step.get("measurements") or {}
    return str(measurements.get("signal_type") or "neutral")


def signal_path(step: dict[str, Any]) -> str:
    if step.get("signal_type"):
        return "signal_type"
    measurements = step.get("measurements") or {}
    if measurements.get("signal_type"):
        return "measurements.signal_type"
    return "missing"


def is_meta_text(text: str) -> bool:
    return is_hermes_meta_message(text)


def extract_model(
    payload: dict[str, Any], chosen_step: dict[str, Any] | None = None
) -> str:
    session_metadata = payload.get("session_metadata") or {}
    metadata = payload.get("metadata") or {}
    step_model = chosen_step.get("model") if chosen_step else None
    return str(
        step_model
        or payload.get("model_used")
        or payload.get("model")
        or session_metadata.get("hermes_model")
        or metadata.get("model")
        or "unknown"
    )


def validate_record(record: EvalRecord) -> list[str]:
    errors = []
    required_text_fields = (
        "prompt",
        "rejected_response",
        "correction",
        "chosen_response",
    )
    for field in required_text_fields:
        value = str(record.get(field) or "").strip()
        if not value:
            errors.append(f"missing {field}")
        if is_meta_text(value):
            errors.append(f"meta text in {field}")

    if record.get("capsule_type") != "hermes-capture":
        errors.append("capsule_type must be hermes-capture")
    if not record.get("source_capsule_id"):
        errors.append("missing source_capsule_id")
    if record.get("correction_signal") not in NEGATIVE_SIGNALS:
        errors.append("correction_signal must be negative")
    if (
        str(record.get("chosen_response") or "").strip()
        == str(record.get("rejected_response") or "").strip()
    ):
        errors.append("chosen_response equals rejected_response")

    step_indices = record.get("step_indices") or {}
    expected_keys = {"prompt", "rejected_response", "correction", "chosen_response"}
    if set(step_indices) != expected_keys:
        errors.append("step_indices missing required keys")
    else:
        indices = [step_indices[key] for key in expected_keys]
        if not all(isinstance(index, int) for index in indices):
            errors.append("step_indices must be integers")
        ordered = [
            step_indices["prompt"],
            step_indices["rejected_response"],
            step_indices["correction"],
            step_indices["chosen_response"],
        ]
        if ordered != sorted(ordered) or len(set(ordered)) != len(ordered):
            errors.append("step_indices must be strictly ordered")

    return errors


def _find_next_role(steps: list[dict[str, Any]], start: int, role: str) -> int | None:
    for index in range(start, len(steps)):
        if steps[index].get("role") == role:
            return index
    return None


def _build_record(
    capsule_id: str,
    capsule_type: str,
    payload: dict[str, Any],
    steps: list[dict[str, Any]],
    indices: tuple[int, int, int, int],
) -> EvalRecord:
    prompt_idx, rejected_idx, correction_idx, chosen_idx = indices
    correction_step = steps[correction_idx]
    return {
        "record_id": f"{capsule_id}:{prompt_idx}-{rejected_idx}-{correction_idx}-{chosen_idx}",
        "source_capsule_id": capsule_id,
        "capsule_type": capsule_type,
        "model": extract_model(payload, steps[chosen_idx]),
        "prompt": step_text(steps[prompt_idx]),
        "rejected_response": step_text(steps[rejected_idx]),
        "correction": step_text(correction_step),
        "chosen_response": step_text(steps[chosen_idx]),
        "correction_signal": step_signal(correction_step),
        "step_indices": {
            "prompt": prompt_idx,
            "rejected_response": rejected_idx,
            "correction": correction_idx,
            "chosen_response": chosen_idx,
        },
        "evidence": {
            "text_field_priority": "reasoning,content",
            "signal_path": signal_path(correction_step),
        },
    }


def extract_eval_records(capsules: list[CapsuleRow]) -> list[EvalRecord]:
    records = []
    ordered_capsules = sorted(
        capsules,
        key=lambda row: str(row.get("capsule_id") or ""),
    )

    for capsule in ordered_capsules:
        capsule_id = str(capsule.get("capsule_id") or "")
        capsule_type = str(capsule.get("capsule_type") or "")
        if capsule_type != "hermes-capture":
            continue

        payload = capsule.get("payload") or {}
        steps = payload.get("reasoning_steps") or []
        if not isinstance(steps, list):
            continue

        for prompt_idx, prompt_step in enumerate(steps):
            if prompt_step.get("role") != "user":
                continue
            rejected_idx = _find_next_role(steps, prompt_idx + 1, "assistant")
            if rejected_idx is None:
                continue
            correction_idx = _find_next_role(steps, rejected_idx + 1, "user")
            if correction_idx is None:
                continue
            if step_signal(steps[correction_idx]) not in NEGATIVE_SIGNALS:
                continue
            chosen_idx = _find_next_role(steps, correction_idx + 1, "assistant")
            if chosen_idx is None:
                continue

            record = _build_record(
                capsule_id,
                capsule_type,
                payload,
                steps,
                (prompt_idx, rejected_idx, correction_idx, chosen_idx),
            )
            if not validate_record(record):
                records.append(record)

    return records


def load_capsules(
    db_path: Path = DB_PATH, limit: int | None = None
) -> list[CapsuleRow]:
    conn = sqlite3.connect(str(db_path))
    query = """
        SELECT capsule_id, capsule_type, payload
        FROM capsules
        WHERE capsule_type = 'hermes-capture'
        ORDER BY capsule_id ASC
    """
    params: tuple[int, ...] = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    try:
        rows = conn.execute(query, params).fetchall()
    except sqlite3.OperationalError as exc:
        if "no such table: capsules" not in str(exc).lower():
            raise
        rows = []
    finally:
        conn.close()

    capsules = []
    for capsule_id, capsule_type, payload_text in rows:
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError:
            continue
        capsules.append(
            {
                "capsule_id": capsule_id,
                "capsule_type": capsule_type,
                "payload": payload,
            }
        )
    return capsules


def write_jsonl(records: list[EvalRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def summarize(records: list[EvalRecord]) -> dict[str, Any]:
    signals = Counter(record["correction_signal"] for record in records)
    models = Counter(record["model"] for record in records)
    return {
        "records": len(records),
        "signals": dict(signals.most_common()),
        "models": dict(models.most_common(15)),
        "safe_for_behavior_eval": True,
        "safe_to_finetune_raw": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH, help="SQLite DB path")
    parser.add_argument("--output", type=Path, help="optional JSONL output path")
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    parser.add_argument("--limit", type=int, help="limit capsules read")
    args = parser.parse_args()

    records = extract_eval_records(load_capsules(args.db, args.limit))
    if args.output:
        write_jsonl(records, args.output)
    summary = summarize(records)
    if args.output:
        summary["output"] = str(args.output)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    print(f"Eval records: {summary['records']}")
    print(f"Signals: {summary['signals']}")
    print(f"Models: {summary['models']}")
    print("Safe for behavior eval: True")
    print("Safe to fine-tune raw: False")
    if args.output:
        print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
