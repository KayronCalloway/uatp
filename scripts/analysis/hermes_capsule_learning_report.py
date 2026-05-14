#!/usr/bin/env python3
"""One-command, non-mutating Hermes capsule learning report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.analysis.build_learning_eval_set import (  # noqa: E402
    DB_PATH,
    extract_eval_records,
    load_capsules,
    write_jsonl,
)
from scripts.analysis.build_learning_eval_set import (
    summarize as summarize_eval,
)
from scripts.analysis.capsule_learning_audit import audit  # noqa: E402
from scripts.analysis.generate_behavior_policy_candidates import (
    benchmark_variants,  # noqa: E402
)
from scripts.analysis.hermes_failure_taxonomy import (  # noqa: E402
    CorrectionChain,
    summarize_failure_modes,
)
from scripts.analysis.hermes_learning_proposals import (
    generate_learning_proposals,  # noqa: E402
)
from scripts.analysis.hermes_report_redaction import (  # noqa: E402
    redact_report_payload,
    redact_report_text,
)
from scripts.analysis.hermes_token_waste import summarize_token_waste  # noqa: E402
from scripts.analysis.hermes_tool_decision_analysis import (
    summarize_tool_decisions,  # noqa: E402
)

DEFAULT_EVAL_SET = (
    PROJECT_ROOT / "scripts" / "analysis" / "hermes_learning_eval_set.jsonl"
)
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "reports" / "hermes_capsule_learning_report.md"
MIN_CHAINS_FOR_BEHAVIOR_RULES = 50
MIN_CHAINS_FOR_POLICY_PROMOTION = 200


def _load_or_build_records(
    db_path: Path, eval_set: Path, dry_run: bool
) -> list[dict[str, Any]]:
    records = extract_eval_records(load_capsules(db_path))
    if not dry_run:
        write_jsonl(records, eval_set)
    return records


def _chains_from_records(records: list[dict[str, Any]]) -> list[CorrectionChain]:
    return [CorrectionChain.from_eval_record(record) for record in records]


def build_report_payload(
    db_path: Path = DB_PATH,
    eval_set: Path = DEFAULT_EVAL_SET,
    output_path: Path | None = DEFAULT_OUTPUT,
    dry_run: bool = True,
) -> dict[str, Any]:
    audit_report = audit(db_path)
    records = _load_or_build_records(db_path, eval_set, dry_run=dry_run)
    eval_summary = summarize_eval(records)
    chains = _chains_from_records(records)
    benchmark = (
        benchmark_variants(records)
        if records
        else {
            "ranking": [],
            "variants": {},
            "promotion_gate": {
                "winner": "",
                "baseline_pass_rate": 0.0,
                "winner_pass_rate": 0.0,
                "beats_baseline": False,
                "safe_to_promote_live": False,
            },
        }
    )

    meta_counts = audit_report.get("hermes", {}).get("meta_signal_counts", {})
    meta_contamination_count = sum(int(value) for value in meta_counts.values())
    clean_chains = len(records)
    signal_health = {
        "meta_contamination_count": meta_contamination_count,
        "clean_correction_chains": clean_chains,
        "min_chains_for_behavior_rules": MIN_CHAINS_FOR_BEHAVIOR_RULES,
        "min_chains_for_policy_promotion": MIN_CHAINS_FOR_POLICY_PROMOTION,
        "safe_for_behavior_rules": meta_contamination_count == 0
        and clean_chains >= MIN_CHAINS_FOR_BEHAVIOR_RULES,
        "safe_for_policy_promotion": meta_contamination_count == 0
        and clean_chains >= MIN_CHAINS_FOR_POLICY_PROMOTION,
    }

    safe_to_promote_live = bool(
        signal_health["safe_for_policy_promotion"]
        and benchmark.get("promotion_gate", {}).get("safe_to_promote_live") is True
    )

    payload = {
        "summary": {
            "safe_to_promote_live": safe_to_promote_live,
            "eval_records": clean_chains,
            "meta_contamination_count": meta_contamination_count,
            "output_path": str(output_path) if output_path else None,
            "dry_run": dry_run,
        },
        "audit": audit_report,
        "eval": eval_summary,
        "benchmark": benchmark,
        "signal_health": signal_health,
        "failure_modes": summarize_failure_modes(chains),
        "token_waste": summarize_token_waste(chains),
        "tool_misses": summarize_tool_decisions(chains),
        "proposals": generate_learning_proposals(chains),
    }
    return payload


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _section_failure_modes(failure_modes: dict[str, Any]) -> list[str]:
    lines = ["## Behavioral Failure Modes", ""]
    if not failure_modes:
        return lines + [
            "No repeated behavioral failure modes met the current deterministic rules.",
            "",
        ]
    for mode, data in failure_modes.items():
        lines.append(f"### {mode} — {data['count']} examples")
        lines.append(f"Lesson: {data['lesson']}")
        lines.append("Evidence:")
        for item in data.get("evidence", []):
            lines.append(f"- {item['id']}: `{item['correction']}`")
        lines.append("")
    return lines


def _section_tool_misses(tool_misses: dict[str, Any]) -> list[str]:
    lines = ["## Tool-Use Misses", ""]
    if not tool_misses:
        return lines + [
            "No deterministic tool-use misses found in the clean eval records.",
            "",
        ]
    for label, data in tool_misses.items():
        lines.append(f"### {label} — {data['count']} examples")
        lines.append(f"Lesson: {data['lesson']}")
        for item in data.get("evidence", []):
            lines.append(f"- {item['id']}: `{item['correction']}`")
        lines.append("")
    return lines


def _section_proposals(proposals: list[dict[str, Any]]) -> list[str]:
    lines = ["## Proposed Memory / Skill Diffs", ""]
    if not proposals:
        return lines + [
            "No proposal met the evidence threshold. No memory or skill changes should be applied.",
            "",
        ]
    for proposal in proposals:
        lines.append(f"### {proposal['type']}")
        if proposal["type"] == "memory":
            lines.append(f"Target: `{proposal['target']}`")
            lines.append(f"Content: {proposal['content']}")
        else:
            lines.append(f"Skill: `{proposal['skill']}`")
            lines.append(f"Patch: {proposal['patch_summary']}")
        lines.append(f"safe_to_apply: {_bool_text(bool(proposal['safe_to_apply']))}")
        lines.append(f"Risk: {proposal['risk']}")
        lines.append("Evidence:")
        for evidence in proposal.get("evidence", []):
            lines.append(f"- {evidence}")
        lines.append("")
    return lines


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    audit_report = payload.get("audit", {})
    hermes = audit_report.get("hermes", {})
    signal_health = payload.get("signal_health", {})
    eval_summary = payload.get("eval", {})
    benchmark = payload.get("benchmark", {})
    token_waste = payload.get("token_waste", {})

    lines = [
        "# Hermes Capsule Learning Report",
        "",
        "## Summary Verdict",
        "",
        f"safe_to_promote_live: {_bool_text(bool(summary.get('safe_to_promote_live')))}",
        f"dry_run: {_bool_text(bool(summary.get('dry_run', True)))}",
    ]
    if int(summary.get("eval_records", 0)) < MIN_CHAINS_FOR_BEHAVIOR_RULES:
        lines.append("Insufficient data for live behavior promotion.")
    if int(summary.get("meta_contamination_count", 0)) > 0:
        lines.append("Signal cleanup required.")
    lines.extend(
        [
            "",
            "## Data Inventory",
            "",
            f"Capsules total: {audit_report.get('capsules_total', 0)}",
            f"Hermes capsules: {hermes.get('capsules', 0)}",
            f"Hermes steps: {hermes.get('steps_total', 0)}",
            f"Clean eval records: {eval_summary.get('records', 0)}",
            "",
            "## Signal Health",
            "",
            f"User signals: `{json.dumps(hermes.get('user_signal_counts', {}), sort_keys=True)}`",
            f"Meta contamination count: {signal_health.get('meta_contamination_count', 0)}",
            f"Clean correction chains: {signal_health.get('clean_correction_chains', 0)}",
            f"Minimum chains for behavior rules: {signal_health.get('min_chains_for_behavior_rules', MIN_CHAINS_FOR_BEHAVIOR_RULES)}",
            f"safe_for_behavior_rules: {_bool_text(bool(signal_health.get('safe_for_behavior_rules')))}",
            "",
            "## Clean Correction Chains",
            "",
            f"Records: {eval_summary.get('records', 0)}",
            f"Signals: `{json.dumps(eval_summary.get('signals', {}), sort_keys=True)}`",
            f"safe_to_finetune_raw: {_bool_text(bool(eval_summary.get('safe_to_finetune_raw')))}",
            "",
        ]
    )
    lines.extend(_section_failure_modes(payload.get("failure_modes", {})))
    lines.extend(
        [
            "## Token Waste / Repetition",
            "",
            f"Long answer followed by short correction: {token_waste.get('long_answer_short_correction', 0)}",
            f"Estimated wasted tokens: {token_waste.get('estimated_wasted_tokens', 0)}",
            f"Deflection phrases: `{json.dumps(token_waste.get('phrases', {}), sort_keys=True)}`",
            "Evidence:",
        ]
    )
    for item in token_waste.get("evidence", []):
        lines.append(f"- {item['id']}: {item['flags']}")
    lines.append("")
    lines.extend(_section_tool_misses(payload.get("tool_misses", {})))
    lines.extend(_section_proposals(payload.get("proposals", [])))
    lines.extend(
        [
            "## Eval and Benchmark Results",
            "",
            f"Promotion gate: `{json.dumps(benchmark.get('promotion_gate', {}), sort_keys=True)}`",
            "Ranking:",
        ]
    )
    for row in benchmark.get("ranking", []):
        lines.append(
            f"- {row['variant']}: pass_rate={row['pass_rate']} passed={row['passed']} failed={row['failed']}"
        )
    lines.extend(
        [
            "",
            "## Next Actions",
            "",
            "- Do not promote live behavior until signal contamination is zero and clean correction-chain thresholds pass.",
            "- Review proposed memory/skill diffs manually before applying any durable change.",
            "- Keep raw fine-tuning disabled until a separate data-card gate exists.",
            "",
        ]
    )
    return redact_report_text("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH, help="SQLite DB path")
    parser.add_argument("--eval-set", type=Path, default=DEFAULT_EVAL_SET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json", action="store_true", help="emit JSON payload")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="default mode: do not write eval JSONL; markdown output is still written unless --json is used",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write generated eval JSONL as well as report",
    )
    args = parser.parse_args(argv)

    dry_run = not args.apply
    payload = build_report_payload(args.db, args.eval_set, args.output, dry_run=dry_run)
    if args.json:
        print(json.dumps(redact_report_payload(payload), indent=2, sort_keys=True))
        return 0

    markdown = render_markdown(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
