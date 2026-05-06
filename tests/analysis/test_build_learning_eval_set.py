import pytest

from scripts.analysis.build_learning_eval_set import (
    extract_eval_records,
    is_meta_text,
    validate_record,
)


def step(role, text, signal="neutral", model=None):
    data = {
        "role": role,
        "reasoning": text,
        "measurements": {"signal_type": signal},
    }
    if model:
        data["model"] = model
    return data


def capsule(capsule_id, steps, capsule_type="hermes-capture"):
    return {
        "capsule_id": capsule_id,
        "capsule_type": capsule_type,
        "payload": {
            "session_metadata": {"hermes_model": "assistant:test-model"},
            "reasoning_steps": steps,
        },
    }


def test_extracts_complete_correction_chain_into_eval_record():
    records = extract_eval_records(
        [
            capsule(
                "cap-1",
                [
                    step("user", "Please inspect the capsule signal quality."),
                    step("assistant", "The signal quality looks fine without changes."),
                    step("user", "no fix the false positives", "correction"),
                    step(
                        "assistant",
                        "I added guards for false positives and verified tests.",
                    ),
                ],
            )
        ]
    )

    assert records == [
        {
            "record_id": "cap-1:0-1-2-3",
            "source_capsule_id": "cap-1",
            "capsule_type": "hermes-capture",
            "model": "assistant:test-model",
            "prompt": "Please inspect the capsule signal quality.",
            "rejected_response": "The signal quality looks fine without changes.",
            "correction": "no fix the false positives",
            "chosen_response": "I added guards for false positives and verified tests.",
            "correction_signal": "correction",
            "step_indices": {
                "prompt": 0,
                "rejected_response": 1,
                "correction": 2,
                "chosen_response": 3,
            },
            "evidence": {
                "text_field_priority": "reasoning,content",
                "signal_path": "measurements.signal_type",
            },
        }
    ]
    assert validate_record(records[0]) == []


@pytest.mark.parametrize(
    "text",
    [
        "[CONTEXT COMPACTION — REFERENCE ONLY] earlier turns...",
        "[Your active task list was preserved across context compression]",
        "[Note: model was just switched to claude-sonnet-4.6]",
    ],
)
def test_meta_text_is_excluded_from_eval_records(text):
    assert is_meta_text(text)
    records = extract_eval_records(
        [
            capsule(
                "cap-meta",
                [
                    step("user", "Do the thing."),
                    step("assistant", "I did the thing."),
                    step("user", text, "correction"),
                    step("assistant", "Continuing from context."),
                ],
            )
        ]
    )

    assert records == []


def test_rejects_records_with_empty_required_text():
    records = extract_eval_records(
        [
            capsule(
                "cap-empty",
                [
                    step("user", "Please inspect the data."),
                    step("assistant", ""),
                    step("user", "fix that", "correction"),
                    step("assistant", "Fixed."),
                ],
            )
        ]
    )

    assert records == []


def test_rejects_non_negative_user_signal_chains():
    records = extract_eval_records(
        [
            capsule(
                "cap-accept",
                [
                    step("user", "Please inspect the data."),
                    step("assistant", "I inspected it."),
                    step("user", "ok thanks", "acceptance"),
                    step("assistant", "You are welcome."),
                ],
            )
        ]
    )

    assert records == []


def test_deterministic_ordering_and_record_ids_across_capsules():
    records = extract_eval_records(
        [
            capsule(
                "cap-b",
                [
                    step("user", "Prompt B"),
                    step("assistant", "Rejected B"),
                    step("user", "fix b", "correction"),
                    step("assistant", "Chosen B"),
                ],
            ),
            capsule(
                "cap-a",
                [
                    step("user", "Prompt A"),
                    step("assistant", "Rejected A"),
                    step("user", "retry a", "requery"),
                    step("assistant", "Chosen A"),
                ],
            ),
        ]
    )

    assert [record["record_id"] for record in records] == [
        "cap-a:0-1-2-3",
        "cap-b:0-1-2-3",
    ]
