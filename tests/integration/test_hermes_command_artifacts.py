"""Tests for Hermes command proof extraction (Phase H2.1)."""

import hashlib

from src.integrations.hermes import hermes_capture


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_terminal_invocation_emits_command_proof_with_exit_code_and_output_hash():
    invocations = [
        {
            "tool": "terminal",
            "call_id": "cmd_1",
            "arguments": {"command": "ls -la", "workdir": "/repo"},
            "result_preview": '{"output": "total 8\\nfile.py\\n", "exit_code": 0}',
            "result_length": 42,
            "timestamp": "2026-05-07T12:00:00+00:00",
        }
    ]

    commands = hermes_capture._extract_command_artifacts(invocations)

    assert len(commands) == 1
    entry = commands[0]
    assert entry["tool"] == "terminal"
    assert entry["call_id"] == "cmd_1"
    assert entry["command"] == "ls -la"
    assert entry["workdir"] == "/repo"
    assert entry["exit_code"] == 0
    assert entry["stdout_hash"] == _sha256_hex("total 8\nfile.py\n")
    assert entry["stdout_size"] == len("total 8\nfile.py\n")
    assert entry["stdout_preview"] == "total 8\nfile.py\n"
    assert entry["stdout_preview_truncated"] is False
    assert entry["stdout_preview_original_length"] == len("total 8\nfile.py\n")
    assert entry["redactions"] == 0


def test_bash_invocation_is_supported_and_redacts_secret_output():
    secret_value = "sk-synthetic1234567890"
    invocations = [
        {
            "tool": "Bash",
            "call_id": "cmd_2",
            "arguments": {"command": "printenv API_KEY"},
            "result_preview": f"api_key={secret_value}\n",
            "result_length": 32,
        }
    ]

    commands = hermes_capture._extract_command_artifacts(invocations)

    assert len(commands) == 1
    entry = commands[0]
    assert entry["command"] == "printenv API_KEY"
    assert entry["stdout_hash"] == _sha256_hex("api_key=[REDACTED]\n")
    assert secret_value not in entry["stdout_preview"]
    assert "[REDACTED]" in entry["stdout_preview"]
    assert entry["redactions"] >= 1


def test_long_terminal_output_is_truncated_with_metadata():
    output = "x" * 5000
    invocations = [
        {
            "tool": "terminal",
            "call_id": "cmd_3",
            "arguments": {"command": "python big_output.py"},
            "result_preview": {"output": output, "exit_code": 0},
            "result_length": len(output),
        }
    ]

    entry = hermes_capture._extract_command_artifacts(invocations)[0]

    assert entry["stdout_hash"] == _sha256_hex(output)
    assert entry["stdout_size"] == len(output)
    assert entry["stdout_preview_truncated"] is True
    assert entry["stdout_preview_original_length"] == len(output)
    assert len(entry["stdout_preview"]) <= hermes_capture._ARTIFACT_PREVIEW_CHARS


def test_non_command_invocations_are_skipped():
    invocations = [
        {"tool": "write_file", "arguments": {"path": "a.py", "content": "x"}},
        {"tool": "web_search", "arguments": {"query": "x"}},
    ]

    assert hermes_capture._extract_command_artifacts(invocations) == []


def test_malformed_command_result_does_not_raise_and_uses_raw_preview_as_stdout():
    invocations = [
        {
            "tool": "terminal",
            "call_id": "cmd_4",
            "arguments": {"command": "echo ok"},
            "result_preview": "ok\n",
        }
    ]

    entry = hermes_capture._extract_command_artifacts(invocations)[0]

    assert entry["exit_code"] is None
    assert entry["stdout_hash"] == _sha256_hex("ok\n")
    assert entry["stdout_preview"] == "ok\n"
