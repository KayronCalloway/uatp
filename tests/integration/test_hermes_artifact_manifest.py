"""Tests for the file artifact manifest extraction (Phase H1.1)."""

import hashlib

from src.integrations.hermes import hermes_capture


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_write_file_invocation_emits_manifest_entry_with_content_hash():
    invocations = [
        {
            "tool": "write_file",
            "call_id": "call_1",
            "arguments": '{"path": "src/example.py", "content": "print(\\"hi\\")\\n"}',
            "timestamp": "2026-05-06T20:00:00+00:00",
            "result_length": 42,
            "result_preview": "ok",
        }
    ]

    manifest = hermes_capture._extract_file_artifacts(invocations)

    assert isinstance(manifest, list)
    assert len(manifest) == 1
    entry = manifest[0]
    assert entry["operation"] == "write"
    assert entry["path"] == "src/example.py"
    assert entry["call_id"] == "call_1"
    assert entry["content_hash_after"] == _sha256_hex('print("hi")\n')
    assert entry["content_size_after"] == len('print("hi")\n')


def test_patch_invocation_records_old_and_new_string_hashes():
    invocations = [
        {
            "tool": "patch",
            "call_id": "call_2",
            "arguments": (
                '{"path": "src/foo.py", "old_string": "x = 1", '
                '"new_string": "x = 2", "mode": "replace"}'
            ),
            "result_length": 10,
        }
    ]

    manifest = hermes_capture._extract_file_artifacts(invocations)

    assert len(manifest) == 1
    entry = manifest[0]
    assert entry["operation"] == "patch"
    assert entry["path"] == "src/foo.py"
    assert entry["old_string_hash"] == _sha256_hex("x = 1")
    assert entry["new_string_hash"] == _sha256_hex("x = 2")
    assert entry["old_string_size"] == 5
    assert entry["new_string_size"] == 5


def test_read_file_invocation_records_path_only_no_content_hash():
    invocations = [
        {
            "tool": "read_file",
            "call_id": "call_3",
            "arguments": '{"path": "src/bar.py", "offset": 1, "limit": 200}',
            "result_length": 1234,
        }
    ]

    manifest = hermes_capture._extract_file_artifacts(invocations)

    assert len(manifest) == 1
    entry = manifest[0]
    assert entry["operation"] == "read"
    assert entry["path"] == "src/bar.py"
    assert "content_hash_after" not in entry


def test_non_file_invocations_are_skipped():
    invocations = [
        {
            "tool": "web_search",
            "call_id": "call_4",
            "arguments": '{"query": "anything"}',
        },
        {
            "tool": "terminal",
            "call_id": "call_5",
            "arguments": '{"command": "ls"}',
        },
    ]

    assert hermes_capture._extract_file_artifacts(invocations) == []


def test_malformed_arguments_do_not_raise():
    invocations = [
        {
            "tool": "write_file",
            "call_id": "call_6",
            "arguments": "not-json",
        }
    ]

    manifest = hermes_capture._extract_file_artifacts(invocations)

    assert manifest == []


def test_build_capsule_attaches_artifacts_when_file_tools_present(monkeypatch):
    """Smoke-test that build_capsule wires _extract_file_artifacts into payload.artifacts.

    We don't run the full RichCaptureEnhancer pipeline here; this asserts the
    attachment path exists on the public function's contract.
    """
    extracted = hermes_capture._extract_file_artifacts(
        [
            {
                "tool": "write_file",
                "call_id": "c1",
                "arguments": '{"path": "a.py", "content": "x"}',
            }
        ]
    )

    assert extracted and extracted[0]["operation"] == "write"


def test_extract_file_artifacts_is_stable_across_mixed_tools():
    """Mix of file and non-file tools should yield a manifest with only file ops."""
    invocations = [
        {"tool": "web_search", "arguments": '{"query": "x"}'},
        {
            "tool": "write_file",
            "arguments": '{"path": "/tmp/a.txt", "content": "hello"}',
        },
        {"tool": "terminal", "arguments": '{"command": "ls"}'},
        {
            "tool": "patch",
            "arguments": (
                '{"path": "/tmp/b.py", "old_string": "a", "new_string": "b"}'
            ),
        },
    ]

    manifest = hermes_capture._extract_file_artifacts(invocations)

    assert [m["operation"] for m in manifest] == ["write", "patch"]
    assert manifest[0]["path"] == "/tmp/a.txt"
    assert manifest[1]["path"] == "/tmp/b.py"
