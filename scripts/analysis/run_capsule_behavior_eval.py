#!/usr/bin/env python3
"""Run deterministic behavior evals against held-out capsule records.

The runner compares candidate assistant responses to held-out correction-chain
records. It is intentionally deterministic and does not call an LLM, mutate the
DB, or promote behavior changes.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

EvalRecord = dict[str, Any]
Candidate = dict[str, Any]
EvalResult = dict[str, Any]

FORBIDDEN_SLOP_PATTERNS = (
    r"\btodo\s*:",
    r"\bfixme\b",
    r"\bhack\b",
    r"\bplaceholder\s+(implementation|text|data|content|value)\b",
    r"\bstub\s+(implementation|function|method|response)\b",
    r"\bdummy\s+(data|value|response|implementation)\b",
    r"\bfake\s+(data|value|response|implementation)\b",
    r"\bmock\s+(data|value|response|implementation)\b",
)
REFUSAL_MARKERS = (
    "i can't",
    "i cannot",
    "i won't",
    "i am unable",
    "i'm unable",
    "as an ai",
    "before making changes",
)
ACTION_MARKERS = (
    "added",
    "fixed",
    "changed",
    "updated",
    "implemented",
    "verified",
    "ran",
    "created",
    "removed",
    "patched",
)
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
    "you",
    "your",
}


def normalize_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def token_set(text: Any) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", normalize_text(text))
        if len(token) > 2 and token not in STOP_WORDS
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            records.append(record)
    return records


def chosen_action_performed(eval_record: EvalRecord) -> bool:
    chosen = normalize_text(eval_record.get("chosen_response"))
    return any(marker in chosen for marker in ACTION_MARKERS)


def score_candidate(eval_record: EvalRecord, candidate: Candidate | None) -> EvalResult:
    record_id = str(eval_record.get("record_id") or "")
    if candidate is None:
        return {
            "record_id": record_id,
            "passed": False,
            "failures": ["missing_candidate"],
        }

    response = normalize_text(candidate.get("candidate_response"))
    rejected = normalize_text(eval_record.get("rejected_response"))
    chosen = normalize_text(eval_record.get("chosen_response"))
    failures = []

    if not response:
        failures.append("empty_candidate_response")
    if response and response == rejected:
        failures.append("candidate_repeats_rejected_response")
    if any(re.search(pattern, response) for pattern in FORBIDDEN_SLOP_PATTERNS):
        failures.append("contains_forbidden_slop_marker")

    overlap = token_set(response) & token_set(chosen)
    if not overlap and "candidate_repeats_rejected_response" not in failures:
        failures.append("no_overlap_with_chosen_response")

    if chosen_action_performed(eval_record) and any(
        marker in response for marker in REFUSAL_MARKERS
    ):
        failures.append("deflects_when_chosen_response_acted")

    return {
        "record_id": record_id,
        "passed": not failures,
        "failures": failures,
    }


def run_eval(
    eval_records: list[EvalRecord], candidates: list[Candidate]
) -> dict[str, Any]:
    candidate_by_id = {
        str(candidate.get("record_id") or ""): candidate for candidate in candidates
    }
    eval_ids = {str(record.get("record_id") or "") for record in eval_records}
    unknown_candidates = sorted(
        record_id
        for record_id in candidate_by_id
        if record_id and record_id not in eval_ids
    )

    results = []
    for record in sorted(
        eval_records, key=lambda item: str(item.get("record_id") or "")
    ):
        record_id = str(record.get("record_id") or "")
        results.append(score_candidate(record, candidate_by_id.get(record_id)))

    passed = sum(1 for result in results if result["passed"])
    total = len(results)
    failed = total - passed
    return {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "unknown_candidates": len(unknown_candidates),
            "pass_rate": round(passed / total, 4) if total else 0.0,
        },
        "results": results,
        "unknown_candidates": unknown_candidates,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", required=True, type=Path, help="eval JSONL path")
    parser.add_argument(
        "--candidates", required=True, type=Path, help="candidate JSONL path"
    )
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    args = parser.parse_args()

    report = run_eval(load_jsonl(args.eval_set), load_jsonl(args.candidates))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    summary = report["summary"]
    print(f"Total: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Unknown candidates: {summary['unknown_candidates']}")
    print(f"Pass rate: {summary['pass_rate']}")


if __name__ == "__main__":
    main()
