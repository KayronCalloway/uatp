#!/usr/bin/env python3
"""Benchmark deterministic behavior-policy candidates against capsule eval records.

This script does not call an LLM, write the database, or promote behavior. It
creates explicit policy variants and scores them with the deterministic capsule
behavior eval runner.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.analysis.run_capsule_behavior_eval import load_jsonl, run_eval

VARIANTS = (
    "baseline_rejected",
    "oracle_chosen",
    "concise_action_bias",
    "overexplainer_negative_control",
)

EvalRecord = dict[str, Any]
Candidate = dict[str, Any]


def _candidate(record_id: str, response: str, variant: str) -> Candidate:
    return {
        "record_id": record_id,
        "candidate_response": response,
        "model": f"policy:{variant}",
        "metadata": {"variant": variant},
    }


def _first_sentence(text: Any) -> str:
    normalized = " ".join(str(text or "").strip().split())
    if not normalized:
        return ""
    for marker in (". ", "! ", "? ", "\n"):
        if marker in normalized:
            return normalized.split(marker, 1)[0].strip(".!? ") + "."
    return normalized.strip(".!? ") + "."


def _concise_action_response(eval_record: EvalRecord) -> str:
    correction = str(eval_record.get("correction") or "").strip().rstrip(".")
    chosen_sentence = _first_sentence(eval_record.get("chosen_response"))
    if chosen_sentence:
        response = f"Fixed: {chosen_sentence}"
    else:
        response = f"Fixed: {correction}."
    words = response.split()
    if len(words) > 28:
        response = " ".join(words[:28]).rstrip(",;:") + "."
    return response


def _overexplainer_response(eval_record: EvalRecord) -> str:
    correction = str(eval_record.get("correction") or "that")
    return (
        "Analysis: I understand the concern, and I would approach it by first "
        f"thinking through why the prior answer may have missed '{correction}'. "
        "I would then consider possible next steps before making changes."
    )


def generate_variant_candidate(eval_record: EvalRecord, variant: str) -> Candidate:
    if variant not in VARIANTS:
        raise ValueError(f"unknown policy variant: {variant}")

    record_id = str(eval_record.get("record_id") or "")
    if variant == "baseline_rejected":
        response = str(eval_record.get("rejected_response") or "")
    elif variant == "oracle_chosen":
        response = str(eval_record.get("chosen_response") or "")
    elif variant == "concise_action_bias":
        response = _concise_action_response(eval_record)
    else:
        response = _overexplainer_response(eval_record)

    return _candidate(record_id, response, variant)


def generate_candidates(
    eval_records: list[EvalRecord], variant: str
) -> list[Candidate]:
    return [
        generate_variant_candidate(record, variant)
        for record in sorted(
            eval_records, key=lambda item: str(item.get("record_id") or "")
        )
    ]


def benchmark_variants(eval_records: list[EvalRecord]) -> dict[str, Any]:
    variants = {
        variant: run_eval(eval_records, generate_candidates(eval_records, variant))
        for variant in VARIANTS
    }
    rank_priority = {
        "oracle_chosen": 0,
        "concise_action_bias": 1,
        "baseline_rejected": 2,
        "overexplainer_negative_control": 3,
    }
    ranking = sorted(
        (
            {
                "variant": variant,
                "pass_rate": report["summary"]["pass_rate"],
                "passed": report["summary"]["passed"],
                "failed": report["summary"]["failed"],
            }
            for variant, report in variants.items()
        ),
        key=lambda item: (
            -item["pass_rate"],
            -item["passed"],
            rank_priority[item["variant"]],
        ),
    )
    winner = ranking[0]["variant"] if ranking else ""
    baseline_pass_rate = variants["baseline_rejected"]["summary"]["pass_rate"]
    winner_pass_rate = ranking[0]["pass_rate"] if ranking else 0.0
    return {
        "variants": variants,
        "ranking": ranking,
        "promotion_gate": {
            "winner": winner,
            "baseline_pass_rate": baseline_pass_rate,
            "winner_pass_rate": winner_pass_rate,
            "beats_baseline": winner_pass_rate > baseline_pass_rate,
            "safe_to_promote_live": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", required=True, type=Path, help="eval JSONL path")
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    args = parser.parse_args()

    report = benchmark_variants(load_jsonl(args.eval_set))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print("Policy candidate benchmark")
    for row in report["ranking"]:
        print(
            f"{row['variant']}: pass_rate={row['pass_rate']} "
            f"passed={row['passed']} failed={row['failed']}"
        )
    gate = report["promotion_gate"]
    print(f"Winner: {gate['winner']}")
    print(f"Beats baseline: {gate['beats_baseline']}")
    print("Safe to promote live: False")


if __name__ == "__main__":
    main()
