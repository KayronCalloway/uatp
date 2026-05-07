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


def test_pytest_command_is_tagged_as_verification_test():
    invocations = [
        {
            "tool": "terminal",
            "call_id": "cmd_5",
            "arguments": {
                "command": "PYTHONPATH=. .venv/bin/python -m pytest tests -q",
            },
            "result_preview": "1664 passed, 11 skipped\n",
        }
    ]

    entry = hermes_capture._extract_command_artifacts(invocations)[0]

    assert entry["is_verification"] is True
    assert entry["verification_type"] == "test"
    assert entry["verification_status"] == "passed"


def test_ruff_py_compile_and_git_diff_check_are_tagged_by_type():
    invocations = [
        {
            "tool": "terminal",
            "arguments": {
                "command": ".venv/bin/python -m ruff check src scripts tests"
            },
            "result_preview": {"output": "All checks passed!", "exit_code": 0},
        },
        {
            "tool": "terminal",
            "arguments": {
                "command": "PYTHONPATH=. .venv/bin/python -m py_compile src/foo.py"
            },
            "result_preview": {"output": "", "exit_code": 0},
        },
        {
            "tool": "terminal",
            "arguments": {"command": "git diff --check"},
            "result_preview": {"output": "", "exit_code": 0},
        },
    ]

    commands = hermes_capture._extract_command_artifacts(invocations)

    assert [c["verification_type"] for c in commands] == [
        "lint",
        "compile",
        "diff_check",
    ]
    assert all(c["is_verification"] is True for c in commands)
    assert all(c["verification_status"] == "passed" for c in commands)


def test_non_verification_command_gets_explicit_non_verification_metadata():
    invocations = [
        {
            "tool": "terminal",
            "arguments": {"command": "git status --short"},
            "result_preview": {"output": "", "exit_code": 0},
        }
    ]

    entry = hermes_capture._extract_command_artifacts(invocations)[0]

    assert entry["is_verification"] is False
    assert entry["verification_type"] is None
    assert entry["verification_status"] is None


def test_failed_verification_command_is_tagged_failed():
    invocations = [
        {
            "tool": "terminal",
            "arguments": {"command": ".venv/bin/python -m ruff check src"},
            "result_preview": {"output": "E501 line too long", "exit_code": 1},
        }
    ]

    entry = hermes_capture._extract_command_artifacts(invocations)[0]

    assert entry["is_verification"] is True
    assert entry["verification_type"] == "lint"
    assert entry["verification_status"] == "failed"


def test_command_verification_summary_counts_passed_and_failed_by_type():
    commands = [
        {
            "is_verification": True,
            "verification_type": "test",
            "verification_status": "passed",
        },
        {
            "is_verification": True,
            "verification_type": "lint",
            "verification_status": "passed",
        },
        {
            "is_verification": True,
            "verification_type": "lint",
            "verification_status": "failed",
        },
        {
            "is_verification": False,
            "verification_type": None,
            "verification_status": None,
        },
    ]

    summary = hermes_capture._summarize_command_verifications(commands)

    assert summary == {
        "verification_commands_total": 3,
        "verification_commands_passed": 2,
        "verification_commands_failed": 1,
        "verification_commands_by_type": {"lint": 2, "test": 1},
        "verification_commands_by_status": {"failed": 1, "passed": 2},
    }


def test_pytest_raw_output_with_failures_is_tagged_failed_even_if_passed_appears():
    invocations = [
        {
            "tool": "terminal",
            "arguments": {"command": ".venv/bin/python -m pytest tests -q"},
            "result_preview": "1 failed, 3 passed in 0.12s\n",
        }
    ]

    entry = hermes_capture._extract_command_artifacts(invocations)[0]

    assert entry["is_verification"] is True
    assert entry["verification_type"] == "test"
    assert entry["verification_status"] == "failed"


def test_setup_and_echo_commands_are_not_tagged_as_verification():
    invocations = [
        {
            "tool": "terminal",
            "arguments": {"command": "pip install pytest"},
            "result_preview": {"output": "installed", "exit_code": 0},
        },
        {
            "tool": "terminal",
            "arguments": {"command": "python -c \"print('pytest installed')\""},
            "result_preview": {"output": "pytest installed", "exit_code": 0},
        },
        {
            "tool": "terminal",
            "arguments": {"command": "echo ruff check"},
            "result_preview": {"output": "ruff check", "exit_code": 0},
        },
    ]

    commands = hermes_capture._extract_command_artifacts(invocations)

    assert all(c["is_verification"] is False for c in commands)
    assert all(c["verification_type"] is None for c in commands)
    assert all(c["verification_status"] is None for c in commands)
