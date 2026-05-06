from scripts.analysis.run_capsule_behavior_eval import run_eval, score_candidate


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


def candidate(record_id="rec-1", response=None):
    return {
        "record_id": record_id,
        "candidate_response": response
        if response is not None
        else "I added false-positive guards and verified the behavior with tests.",
    }


def test_passing_candidate_scores_pass():
    result = score_candidate(eval_record(), candidate())

    assert result == {
        "record_id": "rec-1",
        "passed": True,
        "failures": [],
    }


def test_exact_rejected_response_repeat_fails():
    result = score_candidate(
        eval_record(),
        candidate(response="The signal quality looks fine without changes."),
    )

    assert result == {
        "record_id": "rec-1",
        "passed": False,
        "failures": ["candidate_repeats_rejected_response"],
    }


def test_missing_candidate_fails():
    report = run_eval([eval_record()], [])

    assert report["summary"] == {
        "total": 1,
        "passed": 0,
        "failed": 1,
        "unknown_candidates": 0,
        "pass_rate": 0.0,
    }
    assert report["results"] == [
        {
            "record_id": "rec-1",
            "passed": False,
            "failures": ["missing_candidate"],
        }
    ]


def test_empty_response_fails():
    result = score_candidate(eval_record(), candidate(response="   "))

    assert result == {
        "record_id": "rec-1",
        "passed": False,
        "failures": ["empty_candidate_response", "no_overlap_with_chosen_response"],
    }


def test_slop_marker_fails():
    result = score_candidate(
        eval_record(),
        candidate(response="TODO: add the real implementation later."),
    )

    assert result == {
        "record_id": "rec-1",
        "passed": False,
        "failures": [
            "contains_forbidden_slop_marker",
            "no_overlap_with_chosen_response",
        ],
    }


def test_discussing_removed_slop_markers_does_not_fail():
    result = score_candidate(
        eval_record(),
        candidate(
            response="I removed TODO placeholders and verified the false-positive guards with tests."
        ),
    )

    assert result == {
        "record_id": "rec-1",
        "passed": True,
        "failures": [],
    }


def test_unknown_candidate_record_id_is_reported():
    report = run_eval([eval_record()], [candidate("unknown-rec")])

    assert report["summary"] == {
        "total": 1,
        "passed": 0,
        "failed": 1,
        "unknown_candidates": 1,
        "pass_rate": 0.0,
    }
    assert report["unknown_candidates"] == ["unknown-rec"]


def test_aggregate_summary_counts_passed_and_failed():
    report = run_eval(
        [eval_record("rec-1"), eval_record("rec-2")],
        [
            candidate("rec-1"),
            candidate(
                "rec-2", response="The signal quality looks fine without changes."
            ),
        ],
    )

    assert report["summary"] == {
        "total": 2,
        "passed": 1,
        "failed": 1,
        "unknown_candidates": 0,
        "pass_rate": 0.5,
    }
    assert [result["passed"] for result in report["results"]] == [True, False]
