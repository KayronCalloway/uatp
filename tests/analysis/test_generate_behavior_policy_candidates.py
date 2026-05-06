from scripts.analysis.generate_behavior_policy_candidates import (
    VARIANTS,
    benchmark_variants,
    generate_candidates,
    generate_variant_candidate,
)


def eval_record(record_id="rec-1"):
    return {
        "record_id": record_id,
        "source_capsule_id": "cap-1",
        "capsule_type": "hermes-capture",
        "prompt": "Audit the capsule signal quality.",
        "rejected_response": "The signal quality looks fine without changes.",
        "correction": "no fix the false positives",
        "chosen_response": "I added guards for false positives and verified tests.",
        "correction_signal": "correction",
    }


def test_baseline_rejected_candidate_repeats_rejected_response():
    candidate = generate_variant_candidate(eval_record(), "baseline_rejected")

    assert candidate == {
        "record_id": "rec-1",
        "candidate_response": "The signal quality looks fine without changes.",
        "model": "policy:baseline_rejected",
        "metadata": {"variant": "baseline_rejected"},
    }


def test_oracle_chosen_candidate_matches_chosen_response_and_passes():
    report = benchmark_variants([eval_record()])

    oracle = report["variants"]["oracle_chosen"]
    assert oracle["summary"] == {
        "total": 1,
        "passed": 1,
        "failed": 0,
        "unknown_candidates": 0,
        "pass_rate": 1.0,
    }


def test_concise_action_bias_candidate_is_direct_and_avoids_slop_markers():
    candidate = generate_variant_candidate(eval_record(), "concise_action_bias")

    response = candidate["candidate_response"].lower()
    assert response.startswith("fixed:")
    assert "todo" not in response
    assert "placeholder" not in response
    assert "i would" not in response
    assert len(candidate["candidate_response"].split()) <= 28


def test_overexplainer_negative_control_underperforms_oracle():
    report = benchmark_variants([eval_record()])

    oracle_rate = report["variants"]["oracle_chosen"]["summary"]["pass_rate"]
    overexplainer_rate = report["variants"]["overexplainer_negative_control"][
        "summary"
    ]["pass_rate"]
    overexplainer_response = generate_variant_candidate(
        eval_record(), "overexplainer_negative_control"
    )["candidate_response"].lower()

    assert overexplainer_rate < oracle_rate
    assert "analysis" in overexplainer_response
    assert "i would" in overexplainer_response


def test_benchmark_report_includes_variants_ranking_and_promotion_gate():
    report = benchmark_variants([eval_record()])

    assert set(report["variants"]) == set(VARIANTS)
    assert report["ranking"][0]["variant"] == "oracle_chosen"
    assert report["promotion_gate"] == {
        "winner": "oracle_chosen",
        "baseline_pass_rate": 0.0,
        "winner_pass_rate": 1.0,
        "beats_baseline": True,
        "safe_to_promote_live": False,
    }


def test_candidate_generation_is_deterministic():
    records = [eval_record("rec-2"), eval_record("rec-1")]

    first = generate_candidates(records, "concise_action_bias")
    second = generate_candidates(records, "concise_action_bias")

    assert first == second
    assert [candidate["record_id"] for candidate in first] == ["rec-1", "rec-2"]
