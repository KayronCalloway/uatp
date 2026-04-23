#!/usr/bin/env python3
"""
Seed the MCP certifying gateway store with demo session data.
Direct SQLite inserts — no package imports needed.
"""

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("uatp_mcp_store.db")
JSONL_PATH = DB_PATH.with_suffix(".jsonl")


def _hash(payload: dict) -> str:
    j = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(j.encode()).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cid(prefix: str) -> str:
    return f"{prefix}_{_now()[:10].replace('-', '_')}_{uuid.uuid4().hex[:16]}"


def _insert(
    conn: sqlite3.Connection,
    capsule_id: str,
    session_id: str,
    capsule_type: str,
    payload: dict,
    signature: str,
    parent_id: str | None = None,
    upstream_server_id: str | None = None,
):
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload_hash = _hash(payload)
    timestamp = _now()

    conn.execute(
        """
        INSERT INTO capsules
        (capsule_id, session_id, capsule_type, parent_id,
         payload_json, payload_hash, signature, timestamp, upstream_server_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            capsule_id,
            session_id,
            capsule_type,
            parent_id,
            payload_json,
            payload_hash,
            signature,
            timestamp,
            upstream_server_id,
        ),
    )

    # JSONL mirror
    record = {
        "capsule_id": capsule_id,
        "session_id": session_id,
        "capsule_type": capsule_type,
        "parent_id": parent_id,
        "payload_hash": payload_hash,
        "signature": signature,
        "timestamp": timestamp,
    }
    with open(JSONL_PATH, "a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def _ensure_schema(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS capsules (
            capsule_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            capsule_type TEXT NOT NULL,
            parent_id TEXT,
            payload_json TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            signature TEXT,
            timestamp TEXT NOT NULL,
            upstream_server_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_capsules_session ON capsules(session_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_capsules_parent ON capsules(parent_id)"
    )


def main():
    with sqlite3.connect(DB_PATH) as conn:
        _ensure_schema(conn)

        session_id = f"sess_{uuid.uuid4().hex[:16]}"
        print(f"Seeding session: {session_id}")

        # --- Decision 1 → read_file ---
        dec1 = _cid("dec")
        _insert(
            conn,
            dec1,
            session_id,
            "DECISION_POINT",
            {
                "session_id": session_id,
                "trigger": {
                    "source": "model_tool_selection",
                    "message_hash": {
                        "value": None,
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
                "decision": {
                    "selected_action": {
                        "value": "read_file",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "candidate_actions": {
                        "value": ["read_file"],
                        "evidence_class": "asserted",
                        "source_layer": "model",
                        "limitation": "proxy_only_sees_selected_action",
                    },
                },
                "policy": {
                    "policy_version": {
                        "value": "mvp",
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                    "checks_passed": {
                        "value": ["no_constraints_applied"],
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                    "checks_failed": {
                        "value": None,
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                },
            },
            "sig_ed25519_" + uuid.uuid4().hex[:32],
        )

        tool1 = _cid("tool")
        _insert(
            conn,
            tool1,
            session_id,
            "TOOL_CALL",
            {
                "session_id": session_id,
                "parent_decision_id": {
                    "value": dec1,
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
                "tool": {
                    "name": {
                        "value": "read_file",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "upstream_server_id": {
                        "value": "demo_upstream",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "arguments_hash": {
                        "value": "sha256:"
                        + hashlib.sha256(b'{"path":"/etc/hosts"}').hexdigest(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "arguments_preview": {
                        "value": "read_file(path=/etc/hosts)",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
                "execution": {
                    "started_at": {
                        "value": _now(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "ended_at": {
                        "value": _now(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "latency_ms": {
                        "value": 12,
                        "evidence_class": "derived",
                        "source_layer": "proxy",
                    },
                    "status": {
                        "value": "success",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "error_message": {
                        "value": None,
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
                "output": {
                    "content_hash": {
                        "value": "sha256:"
                        + hashlib.sha256(b"127.0.0.1 localhost").hexdigest(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "preview": {
                        "value": "127.0.0.1 localhost",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
            },
            "sig_ed25519_" + uuid.uuid4().hex[:32],
            parent_id=dec1,
            upstream_server_id="demo_upstream",
        )
        print("  + read_file")

        # --- Decision 2 → write_file ---
        dec2 = _cid("dec")
        _insert(
            conn,
            dec2,
            session_id,
            "DECISION_POINT",
            {
                "session_id": session_id,
                "trigger": {
                    "source": "model_tool_selection",
                    "message_hash": {
                        "value": None,
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
                "decision": {
                    "selected_action": {
                        "value": "write_file",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "candidate_actions": {
                        "value": ["write_file"],
                        "evidence_class": "asserted",
                        "source_layer": "model",
                        "limitation": "proxy_only_sees_selected_action",
                    },
                },
                "policy": {
                    "policy_version": {
                        "value": "mvp",
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                    "checks_passed": {
                        "value": ["path_not_in_denylist", "path_in_allowlist"],
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                    "checks_failed": {
                        "value": None,
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                },
            },
            "sig_ed25519_" + uuid.uuid4().hex[:32],
        )

        tool2 = _cid("tool")
        _insert(
            conn,
            tool2,
            session_id,
            "TOOL_CALL",
            {
                "session_id": session_id,
                "parent_decision_id": {
                    "value": dec2,
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
                "tool": {
                    "name": {
                        "value": "write_file",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "upstream_server_id": {
                        "value": "demo_upstream",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "arguments_hash": {
                        "value": "sha256:"
                        + hashlib.sha256(
                            b'{"content":"certified by uatp","path":"/tmp/mcp_demo.txt"}'
                        ).hexdigest(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "arguments_preview": {
                        "value": "write_file(path=/tmp/mcp_demo.txt, content_len=19)",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
                "execution": {
                    "started_at": {
                        "value": _now(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "ended_at": {
                        "value": _now(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "latency_ms": {
                        "value": 8,
                        "evidence_class": "derived",
                        "source_layer": "proxy",
                    },
                    "status": {
                        "value": "success",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "error_message": {
                        "value": None,
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
                "output": {
                    "content_hash": {
                        "value": "sha256:"
                        + hashlib.sha256(b"Wrote 19 bytes").hexdigest(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "preview": {
                        "value": "Wrote 19 bytes to /tmp/mcp_demo.txt",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
            },
            "sig_ed25519_" + uuid.uuid4().hex[:32],
            parent_id=dec2,
            upstream_server_id="demo_upstream",
        )
        print("  + write_file")

        # --- Decision 3 → run_command ---
        dec3 = _cid("dec")
        _insert(
            conn,
            dec3,
            session_id,
            "DECISION_POINT",
            {
                "session_id": session_id,
                "trigger": {
                    "source": "model_tool_selection",
                    "message_hash": {
                        "value": None,
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
                "decision": {
                    "selected_action": {
                        "value": "run_command",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "candidate_actions": {
                        "value": ["run_command"],
                        "evidence_class": "asserted",
                        "source_layer": "model",
                        "limitation": "proxy_only_sees_selected_action",
                    },
                },
                "policy": {
                    "policy_version": {
                        "value": "mvp",
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                    "checks_passed": {
                        "value": ["command_not_blocked"],
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                    "checks_failed": {
                        "value": None,
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                },
            },
            "sig_ed25519_" + uuid.uuid4().hex[:32],
        )

        tool3 = _cid("tool")
        _insert(
            conn,
            tool3,
            session_id,
            "TOOL_CALL",
            {
                "session_id": session_id,
                "parent_decision_id": {
                    "value": dec3,
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
                "tool": {
                    "name": {
                        "value": "run_command",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "upstream_server_id": {
                        "value": "demo_upstream",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "arguments_hash": {
                        "value": "sha256:"
                        + hashlib.sha256(
                            b'{"command":"echo hello-from-mcp"}'
                        ).hexdigest(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "arguments_preview": {
                        "value": "run_command(command=echo hello-from-mcp)",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
                "execution": {
                    "started_at": {
                        "value": _now(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "ended_at": {
                        "value": _now(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "latency_ms": {
                        "value": 45,
                        "evidence_class": "derived",
                        "source_layer": "proxy",
                    },
                    "status": {
                        "value": "success",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "error_message": {
                        "value": None,
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
                "output": {
                    "content_hash": {
                        "value": "sha256:"
                        + hashlib.sha256(b"hello-from-mcp").hexdigest(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "preview": {
                        "value": "Command: echo hello-from-mcp\nExit: 0\nhello-from-mcp",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
            },
            "sig_ed25519_" + uuid.uuid4().hex[:32],
            parent_id=dec3,
            upstream_server_id="demo_upstream",
        )
        print("  + run_command")

        # --- Decision 4 → rm -rf / (blocked) ---
        dec4 = _cid("dec")
        _insert(
            conn,
            dec4,
            session_id,
            "DECISION_POINT",
            {
                "session_id": session_id,
                "trigger": {
                    "source": "model_tool_selection",
                    "message_hash": {
                        "value": None,
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
                "decision": {
                    "selected_action": {
                        "value": "run_command",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "candidate_actions": {
                        "value": ["run_command"],
                        "evidence_class": "asserted",
                        "source_layer": "model",
                        "limitation": "proxy_only_sees_selected_action",
                    },
                },
                "policy": {
                    "policy_version": {
                        "value": "mvp",
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                    "checks_passed": {
                        "value": None,
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                    "checks_failed": {
                        "value": ["command_blocked"],
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                },
            },
            "sig_ed25519_" + uuid.uuid4().hex[:32],
        )

        ref1 = _cid("ref")
        _insert(
            conn,
            ref1,
            session_id,
            "REFUSAL",
            {
                "session_id": session_id,
                "parent_decision_id": {
                    "value": dec4,
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
                "attempted_tool": {
                    "value": "run_command",
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
                "reason": {
                    "value": "constraint_violation: command_blocked",
                    "evidence_class": "policy",
                    "source_layer": "policy",
                },
                "policy_version": {
                    "value": "mvp",
                    "evidence_class": "policy",
                    "source_layer": "policy",
                },
                "escalation": {
                    "value": "human_approval_required",
                    "evidence_class": "derived",
                    "source_layer": "proxy",
                },
            },
            "sig_ed25519_" + uuid.uuid4().hex[:32],
            parent_id=dec4,
        )
        print("  + refusal (rm -rf /)")

        # --- Second session ---
        session_id2 = f"sess_{uuid.uuid4().hex[:16]}"
        dec5 = _cid("dec")
        _insert(
            conn,
            dec5,
            session_id2,
            "DECISION_POINT",
            {
                "session_id": session_id2,
                "trigger": {
                    "source": "model_tool_selection",
                    "message_hash": {
                        "value": "abc123",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
                "decision": {
                    "selected_action": {
                        "value": "read_file",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "candidate_actions": {
                        "value": ["read_file", "write_file"],
                        "evidence_class": "asserted",
                        "source_layer": "model",
                        "limitation": "proxy_only_sees_selected_action",
                    },
                },
                "policy": {
                    "policy_version": {
                        "value": "mvp",
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                    "checks_passed": {
                        "value": ["no_constraints_applied"],
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                    "checks_failed": {
                        "value": None,
                        "evidence_class": "policy",
                        "source_layer": "policy",
                    },
                },
            },
            "sig_ed25519_" + uuid.uuid4().hex[:32],
        )

        tool4 = _cid("tool")
        _insert(
            conn,
            tool4,
            session_id2,
            "TOOL_CALL",
            {
                "session_id": session_id2,
                "parent_decision_id": {
                    "value": dec5,
                    "evidence_class": "observed",
                    "source_layer": "proxy",
                },
                "tool": {
                    "name": {
                        "value": "read_file",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "upstream_server_id": {
                        "value": "demo_upstream",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "arguments_hash": {
                        "value": "sha256:"
                        + hashlib.sha256(b'{"path":"/tmp/test.txt"}').hexdigest(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "arguments_preview": {
                        "value": "read_file(path=/tmp/test.txt)",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
                "execution": {
                    "started_at": {
                        "value": _now(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "ended_at": {
                        "value": _now(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "latency_ms": {
                        "value": 5,
                        "evidence_class": "derived",
                        "source_layer": "proxy",
                    },
                    "status": {
                        "value": "success",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "error_message": {
                        "value": None,
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
                "output": {
                    "content_hash": {
                        "value": "sha256:"
                        + hashlib.sha256(b"test content here").hexdigest(),
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                    "preview": {
                        "value": "test content here",
                        "evidence_class": "observed",
                        "source_layer": "proxy",
                    },
                },
            },
            "sig_ed25519_" + uuid.uuid4().hex[:32],
            parent_id=dec5,
            upstream_server_id="demo_upstream",
        )
        print(f"  + read_file (session {session_id2})")

        conn.commit()

    total = (
        sqlite3.connect(DB_PATH).execute("SELECT COUNT(*) FROM capsules").fetchone()[0]
    )
    print(f"\nDone. {total} capsules in {DB_PATH}")


if __name__ == "__main__":
    main()
