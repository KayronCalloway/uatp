"""
UATP MCP Capsule Store
======================

Append-only local storage for MCP-certified capsules.

Design:
- SQLite backend for relational queries (parent/child, session graphs)
- JSONL mirror for append-only export and audit simplicity
- Hash chain via merkle_root field (prepared, not yet enforced)
- No updates, no deletes. Only inserts and idempotent reads.

This is MVP storage. Production would add:
- Remote anchoring (RFC 3161 timestamps, blockchain anchors)
- Encrypted payloads with selective disclosure
- Retention policy enforcement
- Replication and backup
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CapsuleStore:
    """
    Append-only store for UATP capsules emitted by the MCP gateway.
    """

    def __init__(self, db_path: str | Path = "uatp_mcp_store.db"):
        self.db_path = Path(db_path)
        self.jsonl_path = self.db_path.with_suffix(".jsonl")
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
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
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_capsules_session
                ON capsules(session_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_capsules_parent
                ON capsules(parent_id)
                """
            )
            conn.commit()

    def insert(
        self,
        capsule_id: str,
        session_id: str,
        capsule_type: str,
        payload: dict[str, Any],
        signature: str | None,
        parent_id: str | None = None,
        upstream_server_id: str | None = None,
    ) -> None:
        """
        Append a capsule to the store.
        """
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload_hash = "sha256:" + hashlib.sha256(payload_json.encode()).hexdigest()
        timestamp = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as conn:
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
            conn.commit()

        # Also append to JSONL for append-only audit simplicity
        record = {
            "capsule_id": capsule_id,
            "session_id": session_id,
            "capsule_type": capsule_type,
            "parent_id": parent_id,
            "payload_hash": payload_hash,
            "signature": signature,
            "timestamp": timestamp,
        }
        with open(self.jsonl_path, "a") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")

        logger.debug(f"Stored capsule {capsule_id} ({capsule_type})")

    def get(self, capsule_id: str) -> dict[str, Any] | None:
        """Retrieve a single capsule by id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM capsules WHERE capsule_id = ?", (capsule_id,)
            ).fetchone()
            if row is None:
                return None
            return {
                **dict(row),
                "payload": json.loads(row["payload_json"]),
            }

    def get_session_graph(self, session_id: str) -> list[dict[str, Any]]:
        """
        Retrieve all capsules for a session, ordered by timestamp.
        This builds the execution graph for inspection and demo.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM capsules
                WHERE session_id = ?
                ORDER BY timestamp ASC
                """,
                (session_id,),
            ).fetchall()
            return [{**dict(r), "payload": json.loads(r["payload_json"])} for r in rows]

    def generate_id(self, prefix: str = "cap") -> str:
        """Generate a UATP-style capsule id."""
        now = datetime.now(timezone.utc)
        date_part = now.strftime("%Y_%m_%d")
        random_part = uuid.uuid4().hex[:16]
        return f"{prefix}_{date_part}_{random_part}"
