import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List

from src.agent_receipts.artifacts import ArtifactStore, verify_artifact_ref
from src.agent_receipts.events import ArtifactRef
from src.agent_receipts.signing import Ed25519ReceiptSigner, verify_signed_receipt_chain
from src.integrations.hermes import hermes_capture


@dataclass
class MockSignal:
    signal_type: str = "neutral"
    references_previous: bool = False
    sentiment_delta: float = 0.0
    matched_phrases: List[str] = None

    def __post_init__(self):
        if self.matched_phrases is None:
            self.matched_phrases = []


class MockDetector:
    def detect_signal(self, *_args, **_kwargs):
        return MockSignal()


@dataclass
class MockConversationMessage:
    role: str
    content: str
    timestamp: datetime
    message_id: str
    session_id: str
    token_count: int | None = None
    model_info: str | None = None
    signal_type: str = "neutral"
    references_previous: bool = False
    sentiment_delta: float = 0.0


@dataclass
class MockConversationSession:
    session_id: str
    user_id: str
    start_time: datetime
    platform: str
    end_time: datetime
    messages: List[Any]
    significance_score: float
    total_tokens: int
    topics: List[str]


def _receipt_event(bundle: dict[str, Any], event_type: str) -> dict[str, Any]:
    return next(
        receipt["event"]
        for receipt in bundle["signed_receipts"]
        if receipt["event"]["event_type"] == event_type
    )


def _capsule_draft(bundle: dict[str, Any], capsule_type: str) -> dict[str, Any]:
    return next(
        draft
        for draft in bundle["capsule_drafts"]
        if draft["capsule_type"] == capsule_type
    )


def patch_capture_dependencies(monkeypatch):
    monkeypatch.setattr(
        hermes_capture,
        "_get_capture_classes",
        lambda: (MockConversationMessage, MockConversationSession),
    )
    monkeypatch.setattr(hermes_capture, "_get_signal_detector", lambda: MockDetector())


def test_assistant_thinking_is_preserved_for_enhancer(monkeypatch):
    patch_capture_dependencies(monkeypatch)

    conv = hermes_capture._convert_to_uatp_objects(
        "sess_1",
        {"started_at": 1, "model": "test-model"},
        [
            {"role": "user", "content": "do work", "timestamp": 2},
            {
                "role": "assistant",
                "content": "Visible answer.",
                "reasoning": "private reasoning trace",
                "timestamp": 3,
            },
        ],
    )

    assistant = conv.messages[1]
    assert assistant.content.startswith(
        "[THINKING]\nprivate reasoning trace\n[/THINKING]"
    )
    assert assistant.content.endswith("Visible answer.")
    assert assistant._hermes_thinking == "private reasoning trace"


def test_reasoning_only_assistant_turn_is_not_dropped(monkeypatch):
    patch_capture_dependencies(monkeypatch)

    conv = hermes_capture._convert_to_uatp_objects(
        "sess_2",
        {"started_at": 1, "model": "test-model"},
        [
            {"role": "user", "content": "inspect", "timestamp": 2},
            {
                "role": "assistant",
                "content": "",
                "reasoning": "deciding which tool to call",
                "timestamp": 3,
                "tool_calls": "[]",
            },
        ],
    )

    assert len(conv.messages) == 2
    assistant = conv.messages[1]
    assert assistant.content == "[THINKING]\ndeciding which tool to call\n[/THINKING]"
    assert assistant._hermes_thinking == "deciding which tool to call"


def test_event_native_receipt_bundle_maps_hermes_session_and_tool_invocations() -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_receipts",
        {
            "started_at": 1,
            "ended_at": 3,
            "model": "claude-sonnet-4",
            "title": "Receipt wiring",
            "source": "hermes-cli",
        },
        [
            {"role": "user", "content": "run tests", "timestamp": 1},
            {"role": "assistant", "content": "running", "timestamp": 2},
            {"role": "tool", "content": "84 passed", "timestamp": 3},
        ],
        [
            {
                "tool": "terminal",
                "call_id": "call_1",
                "arguments": '{"command":"pytest tests/agent_receipts -q"}',
                "result_preview": "84 passed",
                "result_length": 9,
                "timestamp": "1970-01-01T00:00:02+00:00",
            }
        ],
        model="claude-sonnet-4",
        platform="hermes-cli",
        signer=signer,
    )

    assert bundle["schema_version"] == "agent_receipts.v1"
    assert bundle["chain_report"]["valid"] is True
    assert bundle["chain_report"]["event_count"] == 6
    assert len(bundle["signed_receipts"]) == 6
    assert [draft["capsule_type"] for draft in bundle["capsule_drafts"]] == [
        "agent_session",
        "environment_snapshot",
        "decision_point",
        "tool_call",
        "action_trace",
    ]
    agent_session = bundle["capsule_drafts"][0]["agent_session"]
    decision_point = _capsule_draft(bundle, "decision_point")["decision_point"]
    environment_snapshot = _capsule_draft(bundle, "environment_snapshot")[
        "environment_snapshot"
    ]
    assert agent_session["goals"]
    assert agent_session["decision_count"] == 1
    assert decision_point["selected_action"] == "tool_call:terminal"
    assert decision_point["reasoning"].startswith("Selected tool `terminal`")
    assert environment_snapshot["env_vars_hash"].startswith("sha256:")
    assert _capsule_draft(bundle, "environment_snapshot")["receipt_metadata"][
        "enabled_tools"
    ] == ["terminal"]
    event_types = [
        receipt["event"]["event_type"] for receipt in bundle["signed_receipts"]
    ]
    assert event_types == [
        "session.started",
        "environment.snapshot",
        "decision.point",
        "tool_call.completed",
        "action.trace",
        "session.ended",
    ]
    assert verify_signed_receipt_chain(bundle["_signed_receipt_objects"]).valid is True


def test_event_native_receipts_environment_snapshot_is_public_safe(tmp_path) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_env_safe",
        {
            "started_at": 1,
            "model": "claude-sonnet-4",
            "working_directory": "/Users/kay/private-client/secret-project",
            "open_files": ["/Users/kay/private-client/secret-project/token_plan.md"],
            "loaded_skills": [
                "uatp-secret-workflow",
                {"name": "unsafe-skill", "content_hash": "raw/private/skill/path"},
            ],
            "terminal_backend": "local-private-backend",
            "gateway_source": "kay-private-cli",
        },
        [{"role": "user", "content": "inspect", "timestamp": 1}],
        [],
        signer=signer,
        artifact_store=artifact_store,
    )

    public_json = json.dumps(bundle["public"])
    for raw_value in (
        "/Users/kay",
        "private-client",
        "secret-project",
        "token_plan.md",
        "uatp-secret-workflow",
        "local-private-backend",
        "kay-private-cli",
        "raw/private/skill/path",
        "unsafe-skill",
    ):
        assert raw_value not in public_json

    env_draft = _capsule_draft(bundle, "environment_snapshot")
    env_payload = env_draft["environment_snapshot"]
    assert env_payload["working_directory"].startswith("[omitted:sha256:")
    assert env_payload["open_files"][0].startswith("[omitted:sha256:")
    assert env_draft["receipt_metadata"]["loaded_skills"][0]["content_hash"].startswith(
        "sha256:"
    )


def test_event_native_receipts_normalize_tool_status_and_counts(tmp_path) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_failed_tool",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "run failing command", "timestamp": 1}],
        [
            {
                "tool": "terminal",
                "call_id": "call_failed",
                "status": "completed",
                "arguments": {"command": "pytest -q"},
                "timestamp": "1970-01-01T00:00:02+00:00",
                "completed_timestamp": "1970-01-01T00:00:05+00:00",
                "result_preview": {
                    "exit_code": "1",
                    "stdout": "",
                    "stderr": "1 failed",
                },
            }
        ],
        signer=signer,
        artifact_store=artifact_store,
    )

    tool_call = _capsule_draft(bundle, "tool_call")["tool_call"]
    session = _capsule_draft(bundle, "agent_session")["agent_session"]
    assert tool_call["status"] == "error"
    assert tool_call["duration_ms"] == 3000
    assert session["tool_call_count"] == 1
    assert session["action_count"] == 1
    assert session["decision_count"] == 1


def test_build_capsule_orphan_tool_result_preserves_tool_timestamp(monkeypatch) -> None:
    patch_capture_dependencies(monkeypatch)
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    monkeypatch.setattr(hermes_capture, "_get_agent_receipt_signer", lambda: signer)

    class MockEnhancer:
        @staticmethod
        def create_capsule_from_session_with_rich_metadata(_session, user_id):
            return {
                "capsule_id": "cap_orphan",
                "type": "conversation",
                "version": "7.4",
                "timestamp": "1970-01-01T00:00:09+00:00",
                "status": "active",
                "payload": {"reasoning_steps": [], "session_metadata": {}},
            }

    monkeypatch.setattr(hermes_capture, "_get_rich_enhancer", lambda: MockEnhancer)

    capsule = hermes_capture.build_capsule(
        "sess_orphan_tool",
        {"started_at": 1, "model": "claude-sonnet-4", "source": "hermes-cli"},
        [
            {"role": "user", "content": "inspect", "timestamp": 1},
            {
                "role": "tool",
                "tool_name": "terminal",
                "tool_call_id": "orphan_call",
                "content": "late output",
                "timestamp": 9,
            },
        ],
        model="claude-sonnet-4",
        platform="hermes-cli",
    )

    tool_event = _receipt_event(
        capsule["payload"]["agent_receipts"], "tool_call.completed"
    )
    assert tool_event["timestamp"] == "1970-01-01T00:00:09+00:00"


def test_event_native_receipt_bundle_public_payload_has_no_private_objects() -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_public",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "hello", "timestamp": 1}],
        [],
        model="claude-sonnet-4",
        platform="hermes-cli",
        signer=signer,
    )

    assert "_signed_receipt_objects" in bundle
    assert "_signed_receipt_objects" not in bundle["public"]
    assert bundle["public"]["chain_report"]["valid"] is True


def test_build_capsule_attaches_public_event_native_receipts(monkeypatch) -> None:
    patch_capture_dependencies(monkeypatch)
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    monkeypatch.setattr(hermes_capture, "_get_agent_receipt_signer", lambda: signer)

    class MockEnhancer:
        @staticmethod
        def create_capsule_from_session_with_rich_metadata(_session, user_id):
            return {
                "capsule_id": "cap_1",
                "type": "conversation",
                "version": "7.4",
                "timestamp": "1970-01-01T00:00:03+00:00",
                "status": "active",
                "payload": {"reasoning_steps": [], "session_metadata": {}},
            }

    monkeypatch.setattr(hermes_capture, "_get_rich_enhancer", lambda: MockEnhancer)

    capsule = hermes_capture.build_capsule(
        "sess_capsule_receipts",
        {"started_at": 1, "model": "claude-sonnet-4", "source": "hermes-cli"},
        [
            {"role": "user", "content": "run tests", "timestamp": 1},
            {
                "role": "assistant",
                "content": "running",
                "timestamp": 2,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {
                            "name": "terminal",
                            "arguments": '{"command":"pytest tests/agent_receipts -q"}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "content": "84 passed",
                "timestamp": 3,
            },
            {"role": "assistant", "content": "done", "timestamp": 4},
        ],
        model="claude-sonnet-4",
        platform="hermes-cli",
    )

    receipts = capsule["payload"]["agent_receipts"]
    assert receipts["schema_version"] == "agent_receipts.v1"
    assert receipts["chain_report"]["valid"] is True
    assert receipts["chain_report"]["event_count"] == 6
    assert [draft["capsule_type"] for draft in receipts["capsule_drafts"]] == [
        "agent_session",
        "environment_snapshot",
        "decision_point",
        "tool_call",
        "action_trace",
    ]
    assert "_signed_receipt_objects" not in receipts


def test_event_native_receipts_store_command_output_as_content_addressed_artifact(
    tmp_path,
) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_command_artifact",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "run command", "timestamp": 1}],
        [
            {
                "tool": "terminal",
                "call_id": "call_1",
                "arguments": {"command": "printenv API_KEY"},
                "result_preview": "api_key=sk-secret-value\n",
                "result_length": len("api_key=sk-secret-value\n"),
                "timestamp": "1970-01-01T00:00:02+00:00",
            }
        ],
        signer=signer,
        artifact_store=artifact_store,
    )

    tool_event = _receipt_event(bundle, "tool_call.completed")
    stdout_ref = tool_event["payload"]["artifact_refs"]["stdout"]
    ref = ArtifactRef(**stdout_ref)

    assert stdout_ref["digest"].startswith("sha256:")
    assert stdout_ref["media_type"] == "text/plain"
    assert stdout_ref["redaction"] == {"status": "redacted", "redactions": 1}
    assert verify_artifact_ref(tmp_path, ref) is True
    assert b"sk-secret-value" not in (tmp_path / stdout_ref["path"]).read_bytes()
    assert b"[REDACTED]" in (tmp_path / stdout_ref["path"]).read_bytes()


def test_event_native_receipts_store_write_file_content_as_artifact(tmp_path) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_file_artifact",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "write file", "timestamp": 1}],
        [
            {
                "tool": "write_file",
                "call_id": "call_1",
                "arguments": {"path": "src/a.py", "content": "print('safe')\n"},
                "timestamp": "1970-01-01T00:00:02+00:00",
            }
        ],
        signer=signer,
        artifact_store=artifact_store,
    )

    tool_event = _receipt_event(bundle, "tool_call.completed")
    content_ref = tool_event["payload"]["artifact_refs"]["content_after"]
    ref = ArtifactRef(**content_ref)

    assert content_ref["media_type"] == "text/plain"
    assert verify_artifact_ref(tmp_path, ref) is True
    assert (tmp_path / content_ref["path"]).read_text() == "print('safe')\n"


def test_event_native_receipts_store_patch_strings_as_artifacts(tmp_path) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_patch_artifact",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "patch file", "timestamp": 1}],
        [
            {
                "tool": "patch",
                "call_id": "call_1",
                "arguments": {
                    "path": "src/a.py",
                    "old_string": "api_key=old-secret\n",
                    "new_string": "api_key=new-secret\n",
                },
                "timestamp": "1970-01-01T00:00:02+00:00",
            }
        ],
        signer=signer,
        artifact_store=artifact_store,
    )

    tool_event = _receipt_event(bundle, "tool_call.completed")
    refs = tool_event["payload"]["artifact_refs"]
    old_ref = ArtifactRef(**refs["old_string"])
    new_ref = ArtifactRef(**refs["new_string"])

    assert verify_artifact_ref(tmp_path, old_ref) is True
    assert verify_artifact_ref(tmp_path, new_ref) is True
    assert (tmp_path / refs["old_string"]["path"]).read_text() == "api_key=[REDACTED]\n"
    assert (tmp_path / refs["new_string"]["path"]).read_text() == "api_key=[REDACTED]\n"
    assert refs["old_string"]["redaction"] == {"status": "redacted", "redactions": 1}
    assert refs["new_string"]["redaction"] == {"status": "redacted", "redactions": 1}


def test_event_native_receipts_store_read_file_output_as_artifact(tmp_path) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)
    read_output = "1|token=secret-value\n2|safe line\n"

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_read_artifact",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "read file", "timestamp": 1}],
        [
            {
                "tool": "read_file",
                "call_id": "call_1",
                "arguments": {"path": "src/a.py", "offset": 1, "limit": 20},
                "result_preview": {"content": read_output, "total_lines": 2},
                "result_length": len(read_output),
                "timestamp": "1970-01-01T00:00:02+00:00",
            }
        ],
        signer=signer,
        artifact_store=artifact_store,
    )

    tool_event = _receipt_event(bundle, "tool_call.completed")
    content_ref = tool_event["payload"]["artifact_refs"]["content_read"]
    ref = ArtifactRef(**content_ref)

    assert content_ref["media_type"] == "text/plain"
    assert content_ref["redaction"] == {"status": "redacted", "redactions": 1}
    assert verify_artifact_ref(tmp_path, ref) is True
    assert (
        tmp_path / content_ref["path"]
    ).read_text() == "1|token=[REDACTED]\n2|safe line\n"


def test_store_redacted_text_artifact_centralizes_redaction_and_storage(
    tmp_path,
) -> None:
    artifact_store = ArtifactStore(tmp_path)

    ref = hermes_capture._store_redacted_text_artifact(
        artifact_store,
        "api_key=secret-value\nvisible\n",
    )

    assert ref["media_type"] == "text/plain"
    assert ref["redaction"] == {"status": "redacted", "redactions": 1}
    assert verify_artifact_ref(tmp_path, ArtifactRef(**ref)) is True
    assert (tmp_path / ref["path"]).read_text() == "api_key=[REDACTED]\nvisible\n"


def test_build_capsule_stores_signed_receipt_bundle_as_artifact_ref(
    monkeypatch, tmp_path
) -> None:
    patch_capture_dependencies(monkeypatch)
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)
    monkeypatch.setattr(hermes_capture, "_get_agent_receipt_signer", lambda: signer)
    monkeypatch.setattr(
        hermes_capture,
        "_get_agent_receipt_artifact_store",
        lambda: artifact_store,
    )

    class MockEnhancer:
        @staticmethod
        def create_capsule_from_session_with_rich_metadata(_session, user_id):
            return {
                "capsule_id": "cap_bundle_ref",
                "type": "conversation",
                "version": "7.4",
                "timestamp": "1970-01-01T00:00:03+00:00",
                "status": "active",
                "payload": {"reasoning_steps": [], "session_metadata": {}},
            }

    monkeypatch.setattr(hermes_capture, "_get_rich_enhancer", lambda: MockEnhancer)

    capsule = hermes_capture.build_capsule(
        "sess_bundle_ref",
        {"started_at": 1, "model": "claude-sonnet-4", "source": "hermes-cli"},
        [
            {"role": "user", "content": "run tests", "timestamp": 1},
            {
                "role": "assistant",
                "content": "running",
                "timestamp": 2,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {
                            "name": "terminal",
                            "arguments": '{"command":"pytest tests/agent_receipts -q"}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "content": "84 passed",
                "timestamp": 3,
            },
        ],
        model="claude-sonnet-4",
        platform="hermes-cli",
    )

    status = capsule["payload"]["agent_receipts_status"]
    bundle_ref = status["bundle_artifact_ref"]

    assert status["status"] == "attached"
    assert bundle_ref["media_type"] == "application/vnd.uatp.agent-receipts.bundle+json"
    assert bundle_ref["redaction"] == {"status": "none", "redactions": 0}
    assert verify_artifact_ref(tmp_path, ArtifactRef(**bundle_ref)) is True
    assert "agent_receipts_bundle_ref" in capsule["payload"]
    assert capsule["payload"]["agent_receipts_bundle_ref"] == bundle_ref


def test_build_capsule_records_agent_receipt_failure_status(
    monkeypatch, caplog
) -> None:
    patch_capture_dependencies(monkeypatch)

    class MockEnhancer:
        @staticmethod
        def create_capsule_from_session_with_rich_metadata(_session, user_id):
            return {
                "capsule_id": "cap_failure",
                "type": "conversation",
                "version": "7.4",
                "timestamp": "1970-01-01T00:00:03+00:00",
                "status": "active",
                "payload": {"reasoning_steps": [], "session_metadata": {}},
            }

    def raise_receipt_error(*_args, **_kwargs):
        raise RuntimeError("artifact store unavailable: /private/path/token-secret")

    monkeypatch.setattr(hermes_capture, "_get_rich_enhancer", lambda: MockEnhancer)
    monkeypatch.setattr(
        hermes_capture,
        "_build_event_native_receipt_bundle",
        raise_receipt_error,
    )

    caplog.set_level(logging.WARNING, logger=hermes_capture.__name__)
    capsule = hermes_capture.build_capsule(
        "sess_receipt_failure",
        {"started_at": 1, "model": "claude-sonnet-4", "source": "hermes-cli"},
        [
            {"role": "user", "content": "run tests", "timestamp": 1},
            {"role": "assistant", "content": "done", "timestamp": 2},
        ],
        model="claude-sonnet-4",
        platform="hermes-cli",
    )

    status = capsule["payload"]["agent_receipts_status"]
    assert "agent_receipts" not in capsule["payload"]
    assert status == {
        "status": "failed",
        "error_type": "RuntimeError",
        "message": "artifact store unavailable: /private/path/[REDACTED]",
    }
    assert "token-secret" not in caplog.text
    assert "/private/path/[REDACTED]" in caplog.text


def test_write_capsule_persists_agent_receipt_capsule_drafts_as_rows(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "uatp_dev.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE capsules (
            id INTEGER PRIMARY KEY,
            capsule_id VARCHAR NOT NULL UNIQUE,
            capsule_type VARCHAR NOT NULL,
            version VARCHAR NOT NULL,
            timestamp DATETIME NOT NULL,
            status VARCHAR NOT NULL,
            verification JSON NOT NULL,
            parent_capsule_id VARCHAR,
            payload JSON NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(hermes_capture, "UATP_DB", db_path)

    capsule = {
        "capsule_id": "cap_parent",
        "type": "hermes-capture",
        "version": "7.4",
        "timestamp": "1970-01-01T00:00:03+00:00",
        "status": "active",
        "verification": {"hash": "sha256:parent", "signature": "sig"},
        "payload": {
            "session_metadata": {"hermes_session_id": "sess_db_drafts"},
            "agent_receipts_bundle_ref": {"digest": "sha256:bundle"},
            "agent_receipts": {
                "schema_version": "agent_receipts.v1",
                "chain_report": {"chain_tip_hash": "sha256:tip"},
                "capsule_drafts": [
                    {
                        "capsule_type": "agent_session",
                        "payload_key": "agent_session",
                        "agent_session": {"session_id": "sess_db_drafts"},
                        "receipt_metadata": {"start_event_hash": "sha256:start"},
                    },
                    {
                        "capsule_type": "tool_call",
                        "payload_key": "tool_call",
                        "tool_call": {
                            "call_id": "call_1",
                            "session_id": "sess_db_drafts",
                        },
                        "receipt_metadata": {"event_hash": "sha256:tool"},
                    },
                ],
            },
        },
    }

    assert hermes_capture.write_capsule(capsule) is True

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        """
        SELECT capsule_id, capsule_type, parent_capsule_id, verification, payload
        FROM capsules
        ORDER BY id
        """
    ).fetchall()
    conn.close()

    assert [row[1] for row in rows] == ["hermes-capture", "agent_session", "tool_call"]
    assert rows[1][0] == "cap_parent:agent_receipt:0:agent_session"
    assert rows[2][0] == "cap_parent:agent_receipt:1:tool_call"
    assert rows[1][2] == "cap_parent"
    assert rows[2][2] == "cap_parent"
    draft_verification = json.loads(rows[1][3])
    assert draft_verification["method"] == "agent_receipt_draft"
    assert draft_verification["parent_capsule_id"] == "cap_parent"
    draft_payload = json.loads(rows[2][4])
    assert draft_payload["tool_call"]["call_id"] == "call_1"
    assert draft_payload["receipt_metadata"]["bundle_artifact_ref"] == {
        "digest": "sha256:bundle"
    }


def test_write_capsule_fans_agent_receipt_drafts_into_typed_tables(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "uatp_dev.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE capsules (
            id INTEGER PRIMARY KEY,
            capsule_id VARCHAR NOT NULL UNIQUE,
            capsule_type VARCHAR NOT NULL,
            version VARCHAR NOT NULL,
            timestamp DATETIME NOT NULL,
            status VARCHAR NOT NULL,
            verification JSON NOT NULL,
            parent_capsule_id VARCHAR,
            payload JSON NOT NULL
        );
        CREATE TABLE agent_sessions (
            id INTEGER PRIMARY KEY,
            session_id VARCHAR(64) NOT NULL,
            agent_type VARCHAR(50) NOT NULL,
            agent_version VARCHAR(50),
            scheduler_type VARCHAR(50),
            trigger_message TEXT,
            trigger_source VARCHAR(50),
            user_id_hash VARCHAR(64),
            goals JSON,
            status VARCHAR(50) NOT NULL,
            tool_call_count INTEGER,
            action_count INTEGER,
            decision_count INTEGER,
            started_at DATETIME NOT NULL,
            completed_at DATETIME,
            total_duration_ms INTEGER,
            outcome_summary TEXT,
            error_message TEXT,
            verification JSON,
            capsule_id VARCHAR(64),
            created_at DATETIME NOT NULL
        );
        CREATE TABLE tool_calls (
            id INTEGER PRIMARY KEY,
            call_id VARCHAR(64) NOT NULL,
            session_id VARCHAR(64) NOT NULL,
            tool_name VARCHAR(100) NOT NULL,
            tool_category VARCHAR(50) NOT NULL,
            tool_inputs JSON,
            tool_outputs JSON,
            started_at DATETIME NOT NULL,
            completed_at DATETIME,
            duration_ms INTEGER,
            status VARCHAR(50) NOT NULL,
            error_message TEXT,
            step_index INTEGER NOT NULL,
            parent_call_id VARCHAR(64),
            verification JSON,
            capsule_id VARCHAR(64),
            created_at DATETIME NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(hermes_capture, "UATP_DB", db_path)

    capsule = {
        "capsule_id": "cap_typed_parent",
        "type": "hermes-capture",
        "version": "7.4",
        "timestamp": "1970-01-01T00:00:03+00:00",
        "status": "active",
        "verification": {"hash": "sha256:parent", "signature": "sig"},
        "payload": {
            "session_metadata": {"hermes_session_id": "sess_typed"},
            "agent_receipts_bundle_ref": {"digest": "sha256:bundle"},
            "agent_receipts": {
                "schema_version": "agent_receipts.v1",
                "chain_report": {"chain_tip_hash": "sha256:tip"},
                "capsule_drafts": [
                    {
                        "capsule_type": "agent_session",
                        "payload_key": "agent_session",
                        "agent_session": {
                            "session_id": "sess_typed",
                            "agent_type": "hermes",
                            "agent_version": "1.0",
                            "scheduler_type": None,
                            "trigger_message": "run tests",
                            "trigger_source": "hermes_state_db",
                            "user_id_hash": None,
                            "goals": ["tests"],
                            "status": "completed",
                            "tool_call_count": 1,
                            "action_count": 1,
                            "decision_count": 0,
                            "started_at": "1970-01-01T00:00:01+00:00",
                            "completed_at": "1970-01-01T00:00:03+00:00",
                            "total_duration_ms": 2000,
                            "outcome_summary": "done",
                            "error_message": None,
                        },
                        "receipt_metadata": {"start_event_hash": "sha256:start"},
                    },
                    {
                        "capsule_type": "tool_call",
                        "payload_key": "tool_call",
                        "tool_call": {
                            "call_id": "call_1",
                            "session_id": "sess_typed",
                            "tool_name": "terminal",
                            "tool_category": "command",
                            "tool_inputs": {"command": "pytest -q"},
                            "tool_outputs": {"preview": "1 passed"},
                            "started_at": "1970-01-01T00:00:02+00:00",
                            "completed_at": "1970-01-01T00:00:03+00:00",
                            "duration_ms": 1000,
                            "status": "success",
                            "error_message": None,
                            "step_index": 0,
                            "parent_call_id": None,
                        },
                        "receipt_metadata": {"event_hash": "sha256:tool"},
                    },
                ],
            },
        },
    }

    assert hermes_capture.write_capsule(capsule) is True

    conn = sqlite3.connect(db_path)
    agent_row = conn.execute(
        "SELECT session_id, agent_type, goals, verification, capsule_id FROM agent_sessions"
    ).fetchone()
    tool_row = conn.execute(
        "SELECT call_id, session_id, tool_name, tool_inputs, verification, capsule_id FROM tool_calls"
    ).fetchone()
    conn.close()

    assert agent_row[0] == "sess_typed"
    assert agent_row[1] == "hermes"
    assert json.loads(agent_row[2]) == ["tests"]
    assert json.loads(agent_row[3])["bundle_artifact_ref"] == {
        "digest": "sha256:bundle"
    }
    assert agent_row[4] == "cap_typed_parent:agent_receipt:0:agent_session"
    assert tool_row[0] == "call_1"
    assert tool_row[1] == "sess_typed"
    assert tool_row[2] == "terminal"
    assert json.loads(tool_row[3]) == {"command": "pytest -q"}
    assert json.loads(tool_row[4])["bundle_artifact_ref"] == {"digest": "sha256:bundle"}
    assert tool_row[5] == "cap_typed_parent:agent_receipt:1:tool_call"


def test_event_native_receipts_emit_terminal_action_trace_from_tool_invocation(
    tmp_path,
) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_action_emit",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "run tests", "timestamp": 1}],
        [
            {
                "tool": "terminal",
                "call_id": "call_terminal_1",
                "arguments": {
                    "command": "pytest tests/integration/test_hermes_capture.py -q"
                },
                "timestamp": "1970-01-01T00:00:02+00:00",
                "result_length": 8,
                "result_preview": json.dumps(
                    {"exit_code": 0, "stdout": "1 passed", "stderr": ""}
                ),
            }
        ],
        signer=signer,
        artifact_store=artifact_store,
    )

    draft_types = [draft["capsule_type"] for draft in bundle["capsule_drafts"]]
    assert draft_types == [
        "agent_session",
        "environment_snapshot",
        "decision_point",
        "tool_call",
        "action_trace",
    ]
    action_trace = _capsule_draft(bundle, "action_trace")["action_trace"]
    assert action_trace["session_id"] == "sess_action_emit"
    assert action_trace["tool_call_id"] == "call_terminal_1"
    assert action_trace["action_type"] == "terminal.command"
    assert (
        action_trace["command"] == "pytest tests/integration/test_hermes_capture.py -q"
    )
    assert action_trace["exit_code"] == 0
    assert action_trace["executed_at"] == "1970-01-01T00:00:02+00:00"
    assert (
        _capsule_draft(bundle, "action_trace")["receipt_metadata"][
            "verification_classification"
        ]
        == "pytest"
    )


def test_event_native_receipts_emit_write_file_action_trace_from_tool_invocation(
    tmp_path,
) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_file_write_action",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "write the file", "timestamp": 1}],
        [
            {
                "tool": "write_file",
                "call_id": "call_write_1",
                "arguments": {"path": "src/a.py", "content": "value = 1\n"},
                "timestamp": "1970-01-01T00:00:02+00:00",
            }
        ],
        signer=signer,
        artifact_store=artifact_store,
    )

    draft_types = [draft["capsule_type"] for draft in bundle["capsule_drafts"]]
    assert draft_types == [
        "agent_session",
        "environment_snapshot",
        "decision_point",
        "tool_call",
        "action_trace",
    ]
    action_trace = _capsule_draft(bundle, "action_trace")["action_trace"]
    assert action_trace["tool_call_id"] == "call_write_1"
    assert action_trace["action_type"] == "file.write"
    assert action_trace["file_path"] == "src/a.py"
    assert action_trace["file_operation"] == "write"
    assert action_trace["bytes_affected"] == len("value = 1\n")
    assert action_trace["executed_at"] == "1970-01-01T00:00:02+00:00"


def test_event_native_receipts_emit_patch_action_trace_from_tool_invocation(
    tmp_path,
) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_file_patch_action",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "patch the file", "timestamp": 1}],
        [
            {
                "tool": "patch",
                "call_id": "call_patch_1",
                "arguments": {
                    "path": "src/a.py",
                    "old_string": "value = 1\n",
                    "new_string": "value = 2\n",
                },
                "timestamp": "1970-01-01T00:00:02+00:00",
            }
        ],
        signer=signer,
        artifact_store=artifact_store,
    )

    action_trace = _capsule_draft(bundle, "action_trace")["action_trace"]
    metadata = _capsule_draft(bundle, "action_trace")["receipt_metadata"]
    assert action_trace["tool_call_id"] == "call_patch_1"
    assert action_trace["action_type"] == "file.edit"
    assert action_trace["file_path"] == "src/a.py"
    assert action_trace["file_operation"] == "edit"
    assert action_trace["bytes_affected"] == len("value = 2\n")
    assert metadata["before_hash"] is not None
    assert metadata["after_hash"] is not None


def test_event_native_receipts_emit_read_file_action_trace_from_tool_invocation(
    tmp_path,
) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_file_read_action",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "read the file", "timestamp": 1}],
        [
            {
                "tool": "read_file",
                "call_id": "call_read_1",
                "arguments": {"path": "src/a.py", "offset": 1, "limit": 20},
                "result_preview": {"content": "1|value = 2\n", "total_lines": 1},
                "result_length": len("1|value = 2\n"),
                "timestamp": "1970-01-01T00:00:02+00:00",
            }
        ],
        signer=signer,
        artifact_store=artifact_store,
    )

    action_trace = _capsule_draft(bundle, "action_trace")["action_trace"]
    assert action_trace["tool_call_id"] == "call_read_1"
    assert action_trace["action_type"] == "file.read"
    assert action_trace["file_path"] == "src/a.py"
    assert action_trace["file_operation"] == "read"
    assert action_trace["bytes_affected"] == len("1|value = 2\n")


def test_write_capsule_fans_action_trace_drafts_into_typed_table(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "uatp_dev.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE capsules (
            id INTEGER PRIMARY KEY,
            capsule_id VARCHAR NOT NULL UNIQUE,
            capsule_type VARCHAR NOT NULL,
            version VARCHAR NOT NULL,
            timestamp DATETIME NOT NULL,
            status VARCHAR NOT NULL,
            verification JSON NOT NULL,
            parent_capsule_id VARCHAR,
            payload JSON NOT NULL
        );
        CREATE TABLE action_traces (
            id INTEGER PRIMARY KEY,
            action_id VARCHAR(64) NOT NULL,
            session_id VARCHAR(64) NOT NULL,
            tool_call_id VARCHAR(64),
            action_type VARCHAR(50) NOT NULL,
            command TEXT,
            exit_code INTEGER,
            stdout_hash VARCHAR(71),
            stderr_hash VARCHAR(71),
            url VARCHAR(2000),
            selector VARCHAR(500),
            browser_action VARCHAR(50),
            file_path VARCHAR(1000),
            file_operation VARCHAR(50),
            bytes_affected INTEGER,
            executed_at DATETIME NOT NULL,
            duration_ms INTEGER NOT NULL,
            verification JSON,
            capsule_id VARCHAR(64),
            created_at DATETIME NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(hermes_capture, "UATP_DB", db_path)

    capsule = {
        "capsule_id": "cap_action_parent",
        "type": "hermes-capture",
        "version": "7.4",
        "timestamp": "1970-01-01T00:00:03+00:00",
        "status": "active",
        "verification": {"hash": "sha256:parent", "signature": "sig"},
        "payload": {
            "session_metadata": {"hermes_session_id": "sess_action"},
            "agent_receipts_bundle_ref": {"digest": "sha256:bundle"},
            "agent_receipts": {
                "schema_version": "agent_receipts.v1",
                "chain_report": {"chain_tip_hash": "sha256:tip"},
                "capsule_drafts": [
                    {
                        "capsule_type": "action_trace",
                        "payload_key": "action_trace",
                        "action_trace": {
                            "action_id": "act_call_1",
                            "session_id": "sess_action",
                            "tool_call_id": "call_1",
                            "action_type": "terminal.command",
                            "command": "pytest -q",
                            "exit_code": 0,
                            "stdout_hash": "sha256:stdout",
                            "stderr_hash": "sha256:stderr",
                            "url": None,
                            "selector": None,
                            "browser_action": None,
                            "file_path": None,
                            "file_operation": None,
                            "bytes_affected": None,
                            "executed_at": "1970-01-01T00:00:02+00:00",
                            "duration_ms": 1000,
                        },
                        "receipt_metadata": {"event_hash": "sha256:action"},
                    }
                ],
            },
        },
    }

    assert hermes_capture.write_capsule(capsule) is True

    conn = sqlite3.connect(db_path)
    action_row = conn.execute(
        """
        SELECT action_id, session_id, tool_call_id, action_type, command,
               exit_code, stdout_hash, verification, capsule_id
        FROM action_traces
        """
    ).fetchone()
    conn.close()

    assert action_row[0] == "act_call_1"
    assert action_row[1] == "sess_action"
    assert action_row[2] == "call_1"
    assert action_row[3] == "terminal.command"
    assert action_row[4] == "pytest -q"
    assert action_row[5] == 0
    assert action_row[6] == "sha256:stdout"
    assert json.loads(action_row[7])["bundle_artifact_ref"] == {
        "digest": "sha256:bundle"
    }
    assert action_row[8] == "cap_action_parent:agent_receipt:0:action_trace"


def test_event_native_receipts_public_bundle_does_not_leak_raw_tool_secrets(
    tmp_path,
) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_no_secret_leak",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "API_KEY=trigger-secret-value", "timestamp": 1}],
        [
            {
                "tool": "MultiEdit",
                "arguments": {
                    "file_path": "src/a.py",
                    "edits": [
                        {
                            "old_string": "api_key=old-secret-value\nplain-old-hunter2\n",
                            "new_string": "api_key=new-secret-value\nplain-new-hunter2\n",
                        }
                    ],
                },
                "result_preview": {
                    "content": "token=result-secret-value\nplain-result-hunter2\n"
                },
                "timestamp": "1970-01-01T00:00:02+00:00",
            },
            {
                "tool": "terminal",
                "arguments": {"command": "echo password hunter2"},
                "result_preview": {
                    "stdout": "password hunter2\n",
                    "stderr": "plain-stderr-hunter2\n",
                },
                "timestamp": "1970-01-01T00:00:03+00:00",
            },
        ],
        signer=signer,
        artifact_store=artifact_store,
    )

    public_json = json.dumps(bundle["public"])
    leaked_values = [
        "trigger-secret-value",
        "old-secret-value",
        "new-secret-value",
        "result-secret-value",
        "plain-old-hunter2",
        "plain-new-hunter2",
        "plain-result-hunter2",
        "password hunter2",
        "plain-stderr-hunter2",
    ]
    for leaked_value in leaked_values:
        assert leaked_value not in public_json
    assert "omitted" in public_json


def test_event_native_receipts_public_bundle_keeps_verification_command_classification(
    tmp_path,
) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_verification_command",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "run tests", "timestamp": 1}],
        [
            {
                "tool": "terminal",
                "call_id": "call_pytest",
                "arguments": {"command": "pytest tests/agent_receipts -q"},
                "result_preview": {"stdout": "1 passed\n", "stderr": ""},
                "timestamp": "1970-01-01T00:00:02+00:00",
            }
        ],
        signer=signer,
        artifact_store=artifact_store,
    )

    action_draft = _capsule_draft(bundle, "action_trace")
    assert action_draft["action_trace"]["command"] == "pytest tests/agent_receipts -q"
    assert action_draft["receipt_metadata"]["verification_classification"] == "pytest"


def test_event_native_receipts_fallback_call_id_is_session_scoped(tmp_path) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)

    bundle_a = hermes_capture._build_event_native_receipt_bundle(
        "sess_missing_call_a",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "run", "timestamp": 1}],
        [
            {
                "tool": "terminal",
                "arguments": {"command": "true"},
                "timestamp": "1970-01-01T00:00:02+00:00",
            }
        ],
        signer=signer,
        artifact_store=artifact_store,
    )
    bundle_b = hermes_capture._build_event_native_receipt_bundle(
        "sess_missing_call_b",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "run", "timestamp": 1}],
        [
            {
                "tool": "terminal",
                "arguments": {"command": "true"},
                "timestamp": "1970-01-01T00:00:02+00:00",
            }
        ],
        signer=signer,
        artifact_store=artifact_store,
    )

    call_a = _capsule_draft(bundle_a, "tool_call")["tool_call"]["call_id"]
    call_b = _capsule_draft(bundle_b, "tool_call")["tool_call"]["call_id"]
    assert call_a != call_b
    assert call_a.startswith("sess_missing_call_a:")
    assert call_b.startswith("sess_missing_call_b:")


def test_typed_action_trace_hashes_strip_sha256_prefix_for_legacy_columns(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "uatp_dev.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE capsules (
            id INTEGER PRIMARY KEY,
            capsule_id VARCHAR NOT NULL UNIQUE,
            capsule_type VARCHAR NOT NULL,
            version VARCHAR NOT NULL,
            timestamp DATETIME NOT NULL,
            status VARCHAR NOT NULL,
            verification JSON NOT NULL,
            parent_capsule_id VARCHAR,
            payload JSON NOT NULL
        );
        CREATE TABLE action_traces (
            id INTEGER PRIMARY KEY,
            action_id VARCHAR(64) NOT NULL,
            session_id VARCHAR(64) NOT NULL,
            tool_call_id VARCHAR(64),
            action_type VARCHAR(50) NOT NULL,
            command TEXT,
            exit_code INTEGER,
            stdout_hash VARCHAR(64),
            stderr_hash VARCHAR(64),
            url VARCHAR(2000),
            selector VARCHAR(500),
            browser_action VARCHAR(50),
            file_path VARCHAR(1000),
            file_operation VARCHAR(50),
            bytes_affected INTEGER,
            executed_at DATETIME NOT NULL,
            duration_ms INTEGER NOT NULL,
            verification JSON,
            capsule_id VARCHAR(64),
            created_at DATETIME NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(hermes_capture, "UATP_DB", db_path)

    stdout_hash = "sha256:" + "a" * 64
    stderr_hash = "sha256:" + "b" * 64
    capsule = {
        "capsule_id": "cap_action_hash_parent",
        "type": "hermes-capture",
        "version": "7.4",
        "timestamp": "1970-01-01T00:00:03+00:00",
        "status": "active",
        "verification": {"hash": "sha256:parent", "signature": "sig"},
        "payload": {
            "session_metadata": {"hermes_session_id": "sess_action_hash"},
            "agent_receipts": {
                "schema_version": "agent_receipts.v1",
                "chain_report": {"chain_tip_hash": "sha256:tip"},
                "capsule_drafts": [
                    {
                        "capsule_type": "action_trace",
                        "payload_key": "action_trace",
                        "action_trace": {
                            "action_id": "act_call_hash",
                            "session_id": "sess_action_hash",
                            "tool_call_id": "call_hash",
                            "action_type": "terminal.command",
                            "command": "pytest -q",
                            "exit_code": 0,
                            "stdout_hash": stdout_hash,
                            "stderr_hash": stderr_hash,
                            "url": None,
                            "selector": None,
                            "browser_action": None,
                            "file_path": None,
                            "file_operation": None,
                            "bytes_affected": None,
                            "executed_at": "1970-01-01T00:00:02+00:00",
                            "duration_ms": 1000,
                        },
                        "receipt_metadata": {"event_hash": "sha256:action"},
                    }
                ],
            },
        },
    }

    assert hermes_capture.write_capsule(capsule) is True

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT stdout_hash, stderr_hash FROM action_traces").fetchone()
    conn.close()

    assert row == ("a" * 64, "b" * 64)


def test_event_native_receipts_store_multiedit_strings_as_artifacts(tmp_path) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_multiedit_artifact",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "edit file twice", "timestamp": 1}],
        [
            {
                "tool": "MultiEdit",
                "call_id": "call_1",
                "arguments": {
                    "file_path": "src/a.py",
                    "edits": [
                        {
                            "old_string": "token=old-secret\n",
                            "new_string": "token=new-secret\n",
                        },
                        {
                            "old_string": "password=old-password\n",
                            "new_string": "password=new-password\n",
                        },
                    ],
                },
                "timestamp": "1970-01-01T00:00:02+00:00",
            }
        ],
        signer=signer,
        artifact_store=artifact_store,
    )

    tool_event = _receipt_event(bundle, "tool_call.completed")
    edit_refs = tool_event["payload"]["artifact_refs"]["edits"]

    assert len(edit_refs) == 2
    assert set(edit_refs[0]) == {"old_string", "new_string"}
    assert set(edit_refs[1]) == {"old_string", "new_string"}
    assert (
        tmp_path / edit_refs[0]["old_string"]["path"]
    ).read_text() == "token=[REDACTED]\n"
    assert (
        tmp_path / edit_refs[0]["new_string"]["path"]
    ).read_text() == "token=[REDACTED]\n"
    assert (
        tmp_path / edit_refs[1]["old_string"]["path"]
    ).read_text() == "password=[REDACTED]\n"
    assert (
        tmp_path / edit_refs[1]["new_string"]["path"]
    ).read_text() == "password=[REDACTED]\n"
    for edit_ref in edit_refs:
        for ref_dict in edit_ref.values():
            assert verify_artifact_ref(tmp_path, ArtifactRef(**ref_dict)) is True
            assert ref_dict["redaction"] == {"status": "redacted", "redactions": 1}


def test_event_native_receipts_store_v4a_patch_content_as_artifact(tmp_path) -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="hermes_test")
    artifact_store = ArtifactStore(tmp_path)
    patch_content = """*** Begin Patch
*** Update File: src/a.py
@@
-token=old-secret
+token=new-secret
*** End Patch
"""

    bundle = hermes_capture._build_event_native_receipt_bundle(
        "sess_v4a_patch_artifact",
        {"started_at": 1, "model": "claude-sonnet-4"},
        [{"role": "user", "content": "apply patch", "timestamp": 1}],
        [
            {
                "tool": "patch",
                "call_id": "call_1",
                "arguments": {"mode": "patch", "patch": patch_content},
                "timestamp": "1970-01-01T00:00:02+00:00",
            }
        ],
        signer=signer,
        artifact_store=artifact_store,
    )

    tool_event = _receipt_event(bundle, "tool_call.completed")
    patch_ref = tool_event["payload"]["artifact_refs"]["patch"]

    assert patch_ref["media_type"] == "text/plain"
    assert patch_ref["redaction"] == {"status": "redacted", "redactions": 2}
    assert verify_artifact_ref(tmp_path, ArtifactRef(**patch_ref)) is True
    stored = (tmp_path / patch_ref["path"]).read_text()
    assert "old-secret" not in stored
    assert "new-secret" not in stored
    assert "token=[REDACTED]" in stored
