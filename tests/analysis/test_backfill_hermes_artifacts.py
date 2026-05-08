"""Tests for safe Hermes artifact backfill (Phase H4.1)."""

import json
import sqlite3

from scripts.analysis import backfill_hermes_artifacts


def _make_db(tmp_path):
    db_path = tmp_path / "capsules.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE capsules (
            capsule_id TEXT PRIMARY KEY,
            capsule_type TEXT NOT NULL,
            payload JSON NOT NULL,
            verification JSON NOT NULL,
            content_hash TEXT,
            prev_hash TEXT
        )
        """
    )
    return db_path, conn


def _insert_capsule(conn, capsule_id, payload):
    conn.execute(
        """
        INSERT INTO capsules (capsule_id, capsule_type, payload, verification)
        VALUES (?, ?, ?, ?)
        """,
        (
            capsule_id,
            "reasoning_trace",
            json.dumps(payload),
            json.dumps({"signature": "synthetic-signature"}),
        ),
    )
    conn.commit()


def _payload_with_tool_graph():
    return {
        "prompt": "Hermes session",
        "tool_call_graph": {
            "invocations": [
                {
                    "tool": "write_file",
                    "call_id": "call_1",
                    "arguments": {"path": "src/example.py", "content": "print('hi')\n"},
                },
                {
                    "tool": "terminal",
                    "call_id": "cmd_1",
                    "arguments": {
                        "command": "PYTHONPATH=. .venv/bin/python -m pytest tests -q"
                    },
                    "result_preview": {"output": "1 passed\n", "exit_code": 0},
                },
            ]
        },
    }


def test_dry_run_reports_would_update_without_writing(tmp_path):
    db_path, conn = _make_db(tmp_path)
    _insert_capsule(conn, "capsule-1", _payload_with_tool_graph())

    report = backfill_hermes_artifacts.backfill_database(db_path, apply=False)

    assert report["dry_run"] is True
    assert report["would_update"] == 1
    assert report["updated"] == 0
    assert report["skipped_existing_artifacts"] == 0
    assert report["capsules"][0]["capsule_id"] == "capsule-1"
    assert report["capsules"][0]["action"] == "would_update"
    assert report["capsules"][0]["changed_fields"] == ["payload.artifacts"]

    stored_payload = json.loads(
        conn.execute(
            "SELECT payload FROM capsules WHERE capsule_id = 'capsule-1'"
        ).fetchone()[0]
    )
    assert "artifacts" not in stored_payload


def test_apply_updates_exactly_payload_artifacts_and_preserves_other_fields(tmp_path):
    db_path, conn = _make_db(tmp_path)
    original_payload = _payload_with_tool_graph()
    _insert_capsule(conn, "capsule-1", original_payload)

    report = backfill_hermes_artifacts.backfill_database(db_path, apply=True)

    assert report["dry_run"] is False
    assert report["would_update"] == 0
    assert report["updated"] == 1
    assert report["capsules"][0]["action"] == "updated"
    assert report["capsules"][0]["changed_fields"] == ["payload.artifacts"]

    stored_payload = json.loads(
        conn.execute(
            "SELECT payload FROM capsules WHERE capsule_id = 'capsule-1'"
        ).fetchone()[0]
    )
    assert stored_payload["prompt"] == original_payload["prompt"]
    assert stored_payload["tool_call_graph"] == original_payload["tool_call_graph"]
    assert stored_payload["artifacts"]["files_total"] == 1
    assert stored_payload["artifacts"]["commands_total"] == 1
    assert stored_payload["artifacts"]["verification_commands_total"] == 1


def test_second_apply_is_noop_when_artifacts_already_present(tmp_path):
    db_path, conn = _make_db(tmp_path)
    _insert_capsule(conn, "capsule-1", _payload_with_tool_graph())

    first_report = backfill_hermes_artifacts.backfill_database(db_path, apply=True)
    second_report = backfill_hermes_artifacts.backfill_database(db_path, apply=True)

    assert first_report["updated"] == 1
    assert second_report["updated"] == 0
    assert second_report["skipped_existing_artifacts"] == 1
    assert second_report["capsules"][0]["action"] == "skipped_existing_artifacts"


def test_capsule_with_empty_artifacts_is_eligible_for_apply(tmp_path):
    db_path, conn = _make_db(tmp_path)
    payload = _payload_with_tool_graph()
    payload["artifacts"] = {}
    _insert_capsule(conn, "capsule-1", payload)

    report = backfill_hermes_artifacts.backfill_database(db_path, apply=True)

    assert report["updated"] == 1
    stored_payload = json.loads(
        conn.execute(
            "SELECT payload FROM capsules WHERE capsule_id = 'capsule-1'"
        ).fetchone()[0]
    )
    assert stored_payload["artifacts"]["files_total"] == 1


def test_capsule_with_populated_legacy_artifacts_value_is_not_overwritten(tmp_path):
    db_path, conn = _make_db(tmp_path)
    payload = _payload_with_tool_graph()
    payload["artifacts"] = ["legacy-manifest"]
    _insert_capsule(conn, "capsule-1", payload)

    report = backfill_hermes_artifacts.backfill_database(db_path, apply=True)

    assert report["updated"] == 0
    assert report["skipped_existing_artifacts"] == 1
    assert report["capsules"][0]["action"] == "skipped_existing_artifacts"
    stored_payload = json.loads(
        conn.execute(
            "SELECT payload FROM capsules WHERE capsule_id = 'capsule-1'"
        ).fetchone()[0]
    )
    assert stored_payload["artifacts"] == ["legacy-manifest"]


def test_capsule_without_artifactable_tools_is_skipped(tmp_path):
    db_path, _conn = _make_db(tmp_path)
    payload = {
        "tool_call_graph": {
            "invocations": [{"tool": "web_search", "arguments": {"query": "x"}}]
        }
    }
    _insert_capsule(_conn, "capsule-1", payload)

    report = backfill_hermes_artifacts.backfill_database(db_path, apply=True)

    assert report["updated"] == 0
    assert report["skipped_no_artifacts"] == 1
    assert report["capsules"][0]["action"] == "skipped_no_artifacts"
