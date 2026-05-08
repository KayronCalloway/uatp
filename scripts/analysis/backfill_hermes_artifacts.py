#!/usr/bin/env python3
"""Safely backfill Hermes artifact manifests onto existing capsules.

Phase H4.1 from docs/plans/2026-05-06-uatp-artifact-proof-plan.md.

Default mode is read-only. Pass --apply to update rows. The script only writes
payload.artifacts when that field is missing or empty; repeated --apply runs are
idempotent no-ops.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from src.integrations.hermes import hermes_capture

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "uatp_dev.db"


def _load_json(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return None
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _artifacts_missing_or_empty(payload: dict[str, Any]) -> bool:
    if "artifacts" not in payload:
        return True
    artifacts = payload.get("artifacts")
    if artifacts is None or artifacts == "":
        return True
    if isinstance(artifacts, (dict, list)) and not artifacts:
        return True
    return False


def build_artifacts_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Build artifact summary from an existing Hermes payload's tool_call_graph."""
    tool_graph = payload.get("tool_call_graph")
    if not isinstance(tool_graph, dict):
        return {}

    invocations = tool_graph.get("invocations")
    if not isinstance(invocations, list):
        return {}

    normalized_invocations = [inv for inv in invocations if isinstance(inv, dict)]
    file_artifacts = hermes_capture._extract_file_artifacts(normalized_invocations)
    command_artifacts = hermes_capture._extract_command_artifacts(
        normalized_invocations
    )

    artifacts: dict[str, Any] = {}
    if file_artifacts:
        artifacts["files"] = file_artifacts
        artifacts["files_total"] = len(file_artifacts)
        artifacts["files_by_operation"] = dict(
            Counter(f["operation"] for f in file_artifacts).most_common()
        )
    if command_artifacts:
        artifacts["commands"] = command_artifacts
        artifacts["commands_total"] = len(command_artifacts)
        artifacts.update(
            hermes_capture._summarize_command_verifications(command_artifacts)
        )
    return artifacts


def _iter_candidate_rows(
    conn: sqlite3.Connection,
    limit: int | None = None,
) -> list[sqlite3.Row]:
    sql = (
        "SELECT capsule_id, payload FROM capsules "
        "WHERE json_extract(payload, '$.tool_call_graph.invocations') IS NOT NULL "
        "ORDER BY rowid DESC"
    )
    params: tuple[Any, ...] = ()
    if limit is not None:
        sql += " LIMIT ?"
        params = (limit,)
    return list(conn.execute(sql, params).fetchall())


def backfill_database(
    db_path: str | Path = DEFAULT_DB_PATH,
    *,
    apply: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    """Backfill payload.artifacts for eligible Hermes capsules.

    Returns a deterministic report with per-capsule actions. No writes occur
    unless apply=True.
    """
    db_path = Path(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    report: dict[str, Any] = {
        "db_path": str(db_path),
        "dry_run": not apply,
        "scanned": 0,
        "would_update": 0,
        "updated": 0,
        "skipped_existing_artifacts": 0,
        "skipped_invalid_payload": 0,
        "skipped_no_artifacts": 0,
        "capsules": [],
    }

    try:
        for row in _iter_candidate_rows(conn, limit=limit):
            report["scanned"] += 1
            capsule_id = row["capsule_id"]
            payload = _load_json(row["payload"])
            if payload is None:
                report["skipped_invalid_payload"] += 1
                report["capsules"].append(
                    {"capsule_id": capsule_id, "action": "skipped_invalid_payload"}
                )
                continue

            if not _artifacts_missing_or_empty(payload):
                report["skipped_existing_artifacts"] += 1
                report["capsules"].append(
                    {"capsule_id": capsule_id, "action": "skipped_existing_artifacts"}
                )
                continue

            artifacts = build_artifacts_from_payload(payload)
            if not artifacts:
                report["skipped_no_artifacts"] += 1
                report["capsules"].append(
                    {"capsule_id": capsule_id, "action": "skipped_no_artifacts"}
                )
                continue

            capsule_report = {
                "capsule_id": capsule_id,
                "action": "updated" if apply else "would_update",
                "changed_fields": ["payload.artifacts"],
                "files_total": artifacts.get("files_total", 0),
                "commands_total": artifacts.get("commands_total", 0),
                "verification_commands_total": artifacts.get(
                    "verification_commands_total", 0
                ),
            }

            if apply:
                updated_payload = dict(payload)
                updated_payload["artifacts"] = artifacts
                conn.execute(
                    "UPDATE capsules SET payload = ? WHERE capsule_id = ?",
                    (
                        json.dumps(
                            updated_payload, sort_keys=True, separators=(",", ":")
                        ),
                        capsule_id,
                    ),
                )
                report["updated"] += 1
            else:
                report["would_update"] += 1

            report["capsules"].append(capsule_report)

        if apply:
            conn.commit()
    finally:
        conn.close()

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill payload.artifacts for existing Hermes capsules."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--apply", action="store_true", help="Write eligible updates")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    report = backfill_database(args.db, apply=args.apply, limit=args.limit)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
