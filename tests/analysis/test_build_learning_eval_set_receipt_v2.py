"""Tests for learning receipt v2 evidence in Hermes eval records."""

from scripts.analysis.build_learning_eval_set import extract_eval_records


def test_eval_record_includes_learning_receipt_v2_evidence():
    capsule = {
        "capsule_id": "caps_test",
        "capsule_type": "hermes-capture",
        "payload": {
            "model_used": "assistant:test",
            "learning_receipt_v2": {
                "schema_version": "2026-06-04.artifact-verification.v1",
                "verification_evidence": {"verification_commands_total": 1},
                "learning_flags": {"verification_after_change": True},
            },
            "reasoning_steps": [
                {"role": "user", "reasoning": "fix it"},
                {"role": "assistant", "reasoning": "I can explain."},
                {
                    "role": "user",
                    "reasoning": "ok fix it",
                    "measurements": {"signal_type": "correction"},
                },
                {"role": "assistant", "reasoning": "Fixed and tested."},
            ],
        },
    }

    records = extract_eval_records([capsule])

    assert len(records) == 1
    assert (
        records[0]["evidence"]["learning_receipt_v2_schema"]
        == "2026-06-04.artifact-verification.v1"
    )
    assert records[0]["evidence"]["verification_commands_total"] == 1
    assert records[0]["evidence"]["verification_after_change"] is True


def test_eval_record_without_learning_receipt_v2_keeps_existing_evidence_shape():
    capsule = {
        "capsule_id": "caps_test_no_receipt",
        "capsule_type": "hermes-capture",
        "payload": {
            "model_used": "assistant:test",
            "reasoning_steps": [
                {"role": "user", "reasoning": "fix it"},
                {"role": "assistant", "reasoning": "I can explain."},
                {
                    "role": "user",
                    "reasoning": "ok fix it",
                    "measurements": {"signal_type": "correction"},
                },
                {"role": "assistant", "reasoning": "Fixed."},
            ],
        },
    }

    record = extract_eval_records([capsule])[0]

    assert record["evidence"] == {
        "text_field_priority": "reasoning,content",
        "signal_path": "measurements.signal_type",
    }
