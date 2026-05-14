from pathlib import Path

from scripts.analysis.build_learning_eval_set import extract_eval_records
from scripts.analysis.generate_behavior_policy_candidates import benchmark_variants
from scripts.analysis.hermes_capsule_learning_report import render_markdown
from scripts.analysis.hermes_failure_taxonomy import (
    CorrectionChain,
    classify_failure_modes,
)
from scripts.analysis.hermes_learning_proposals import generate_learning_proposals
from scripts.analysis.hermes_signal_filters import is_hermes_meta_message
from scripts.analysis.hermes_token_waste import analyze_token_waste
from scripts.analysis.hermes_tool_decision_analysis import analyze_tool_decisions
from scripts.analysis.rescore_hermes_capsules import rescore_capsule
from scripts.analysis.run_capsule_behavior_eval import run_eval


def user_step(text, signal="neutral"):
    return {
        "role": "user",
        "reasoning": text,
        "measurements": {"signal_type": signal},
    }


def assistant_step(text):
    return {
        "role": "assistant",
        "reasoning": text,
    }


def test_capsule_learning_gate_manifest_exists_and_records_safety_boundary():
    manifest = Path("AUDIT_2026_05_06_capsule_learning_gate.md")

    assert manifest.exists()
    text = manifest.read_text(encoding="utf-8")
    assert "safe_to_finetune_raw: false" in text
    assert "safe_to_promote_live: false" in text
    assert "uatp_dev.db.backup.20260506_084405" in text


def test_capsule_learning_pipeline_contract_with_synthetic_data():
    long_rejected_response = " ".join(["This is a long rejected explanation"] * 80)
    payload = {
        "session_metadata": {"hermes_model": "assistant:test-model"},
        "reasoning_steps": [
            user_step(
                "[CONTEXT COMPACTION — REFERENCE ONLY] previous turns", "correction"
            ),
            user_step("Audit the capsule learning path."),
            assistant_step(long_rejected_response),
            user_step("ok fix it", "neutral"),
            assistant_step(
                "Fixed: added guards and verified the capsule learning path."
            ),
        ],
    }

    rescored_payload, changed = rescore_capsule(payload)

    assert changed is True
    assert (
        rescored_payload["reasoning_steps"][0]["measurements"]["signal_type"]
        == "neutral"
    )
    assert (
        rescored_payload["reasoning_steps"][3]["measurements"]["signal_type"]
        == "correction"
    )

    records = extract_eval_records(
        [
            {
                "capsule_id": "cap-contract",
                "capsule_type": "hermes-capture",
                "payload": rescored_payload,
            }
        ]
    )

    assert len(records) == 1
    record = records[0]
    assert record["record_id"] == "cap-contract:1-2-3-4"
    assert record["evidence"] == {
        "text_field_priority": "reasoning,content",
        "signal_path": "measurements.signal_type",
    }

    baseline_report = run_eval(
        [record],
        [
            {
                "record_id": record["record_id"],
                "candidate_response": record["rejected_response"],
            }
        ],
    )
    oracle_report = run_eval(
        [record],
        [
            {
                "record_id": record["record_id"],
                "candidate_response": record["chosen_response"],
            }
        ],
    )

    assert baseline_report["summary"]["pass_rate"] == 0.0
    assert baseline_report["results"][0]["failures"] == [
        "candidate_repeats_rejected_response"
    ]
    assert oracle_report["summary"]["pass_rate"] == 1.0

    benchmark = benchmark_variants(records)

    assert benchmark["variants"]["baseline_rejected"]["summary"]["pass_rate"] == 0.0
    assert benchmark["promotion_gate"] == {
        "winner": "oracle_chosen",
        "baseline_pass_rate": 0.0,
        "winner_pass_rate": 1.0,
        "beats_baseline": True,
        "safe_to_promote_live": False,
    }

    chain = CorrectionChain.from_eval_record(record)
    assert is_hermes_meta_message(
        "[CONTEXT COMPACTION — REFERENCE ONLY] previous turns"
    )
    assert "explanation_instead_of_action" in classify_failure_modes(chain)
    assert "long_answer_short_correction" in analyze_token_waste(chain).flags

    tool_chain = CorrectionChain(
        prompt="Can you work on UATP?",
        rejected_response="UATP is a concept I can explain generally.",
        correction="n can you see uatp?",
        chosen_response="I checked the local repo and found it.",
        source_capsule_id="cap-tool",
    )
    assert "should_have_used_file_tool" in analyze_tool_decisions(tool_chain).labels

    proposals = generate_learning_proposals(
        [
            chain,
            CorrectionChain(
                prompt="p",
                rejected_response=long_rejected_response,
                correction="fix that",
                chosen_response="Fixed and verified.",
                source_capsule_id="cap-2",
            ),
            CorrectionChain(
                prompt="p",
                rejected_response=long_rejected_response,
                correction="ok fix everything",
                chosen_response="Fixed and verified.",
                source_capsule_id="cap-3",
            ),
        ]
    )
    assert proposals[0]["safe_to_apply"] is False

    markdown = render_markdown(
        {
            "summary": {
                "safe_to_promote_live": False,
                "eval_records": 1,
                "meta_contamination_count": 1,
                "dry_run": True,
            },
            "audit": {
                "capsules_total": 1,
                "hermes": {"capsules": 1, "steps_total": 4, "user_signal_counts": {}},
            },
            "eval": {
                "records": 1,
                "signals": {"correction": 1},
                "safe_to_finetune_raw": False,
            },
            "benchmark": benchmark,
            "signal_health": {
                "meta_contamination_count": 1,
                "clean_correction_chains": 1,
            },
            "failure_modes": {},
            "token_waste": {
                "long_answer_short_correction": 1,
                "estimated_wasted_tokens": 100,
                "phrases": {},
                "evidence": [],
            },
            "tool_misses": {},
            "proposals": proposals,
        }
    )
    assert "Insufficient data for live behavior promotion" in markdown
    assert "safe_to_promote_live: false" in markdown
