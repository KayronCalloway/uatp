"""Tests for Hermes learning receipt v2 evidence extraction."""

from src.integrations.hermes import hermes_capture


def test_learning_receipt_v2_extracts_files_commands_and_verification_order():
    invocations = [
        {
            "tool": "write_file",
            "call_id": "call-write",
            "arguments": {"path": "src/example.py", "content": "print('ok')\n"},
            "result_preview": {"output": "wrote", "exit_code": 0},
            "timestamp": "2026-06-04T08:00:00+00:00",
        },
        {
            "tool": "terminal",
            "call_id": "call-test",
            "arguments": {"command": "./.venv/bin/python -m pytest tests/example -q"},
            "result_preview": {"output": "1 passed", "exit_code": 0},
            "timestamp": "2026-06-04T08:01:00+00:00",
        },
    ]
    messages = [
        {"role": "user", "content": "ok fix it to my standard"},
        {"role": "assistant", "content": "Changed src/example.py and ran tests."},
    ]

    receipt = hermes_capture._build_learning_receipt_v2(invocations, messages)

    assert receipt["schema_version"] == "2026-06-04.artifact-verification.v1"
    assert receipt["artifact_manifest"]["tool_call_count"] == 2
    assert receipt["artifact_manifest"]["files"][0]["operation"] == "write"
    assert receipt["artifact_manifest"]["commands"][0]["verification_type"] == "test"
    assert receipt["verification_evidence"]["verification_commands_total"] == 1
    assert receipt["verification_evidence"]["verification_commands_passed"] == 1
    assert receipt["verification_evidence"]["ran_after_last_write"] is True
    assert receipt["verification_evidence"]["last_write_index"] == 0
    assert receipt["verification_evidence"]["last_verification_index"] == 1
    assert receipt["learning_flags"]["modified_artifacts"] is True
    assert receipt["learning_flags"]["verified_changes"] is True
    assert receipt["learning_flags"]["verification_after_change"] is True
    assert "standard" in receipt["task_intent"]["quality_triggers"]
    assert "fix" in receipt["task_intent"]["action_directives"]


def test_learning_receipt_v2_detects_missing_post_change_verification():
    invocations = [
        {
            "tool": "terminal",
            "call_id": "call-test",
            "arguments": {"command": "pytest tests/example -q"},
            "result_preview": {"output": "1 passed", "exit_code": 0},
            "timestamp": "2026-06-04T08:00:00+00:00",
        },
        {
            "tool": "patch",
            "call_id": "call-patch",
            "arguments": {
                "path": "src/example.py",
                "old_string": "old",
                "new_string": "new",
            },
            "result_preview": {"output": "patched", "exit_code": 0},
            "timestamp": "2026-06-04T08:01:00+00:00",
        },
    ]

    receipt = hermes_capture._build_learning_receipt_v2(invocations, [])

    assert receipt["verification_evidence"]["verification_commands_total"] == 1
    assert receipt["verification_evidence"]["ran_after_last_write"] is False
    assert receipt["learning_flags"]["modified_artifacts"] is True
    assert receipt["learning_flags"]["verified_changes"] is True
    assert receipt["learning_flags"]["verification_after_change"] is False


def test_learning_receipt_v2_redacts_command_output_secrets():
    secret_value = "sk-sec...6789"
    invocations = [
        {
            "tool": "terminal",
            "call_id": "call-secret",
            "arguments": {"command": "printenv"},
            "result_preview": {
                "output": f"OPENAI_API_KEY={secret_value}",
                "exit_code": 0,
            },
        }
    ]

    receipt = hermes_capture._build_learning_receipt_v2(invocations, [])
    preview = receipt["artifact_manifest"]["commands"][0]["stdout_preview"]

    assert secret_value not in preview
    assert "[REDACTED]" in preview


def test_learning_receipt_v2_marks_action_directive_without_tools_as_explanation_bias_risk():
    receipt = hermes_capture._build_learning_receipt_v2(
        [], [{"role": "user", "content": "ok continue and fix it"}]
    )

    assert receipt["learning_flags"]["acted_with_tools"] is False
    assert receipt["learning_flags"]["possible_explanation_bias"] is True
    assert "continue" in receipt["task_intent"]["action_directives"]
