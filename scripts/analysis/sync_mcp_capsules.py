#!/usr/bin/env python3
"""
Sync MCP gateway capsules from uatp_mcp_store.db into uatp_dev.db.

The MCP gateway writes to its own append-only store. This script copies
those capsules into the main UATP database so they appear in the dashboard,
stats, and DPO extraction pipeline.

Usage:
    python3 scripts/analysis/sync_mcp_capsules.py [--dry-run]
"""

import json
import sqlite3
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
MCP_DB = project_root / "uatp_mcp_store.db"
UATP_DB = project_root / "uatp_dev.db"


def main():
    dry_run = "--dry-run" in sys.argv

    if not MCP_DB.exists():
        print(f"MCP store not found at {MCP_DB}")
        return

    if not UATP_DB.exists():
        print(f"UATP DB not found at {UATP_DB}")
        return

    mcp_conn = sqlite3.connect(str(MCP_DB))
    mcp_conn.row_factory = sqlite3.Row

    rows = mcp_conn.execute(
        """
        SELECT capsule_id, session_id, capsule_type, parent_id,
               payload_json, payload_hash, signature, timestamp,
               upstream_server_id
        FROM capsules
        ORDER BY timestamp ASC
        """
    ).fetchall()
    mcp_conn.close()

    uatp_conn = sqlite3.connect(str(UATP_DB))
    uatp_conn.row_factory = sqlite3.Row

    inserted = 0
    skipped = 0

    for row in rows:
        # Check if already exists in uatp_dev.db
        existing = uatp_conn.execute(
            "SELECT 1 FROM capsules WHERE capsule_id = ?", (row["capsule_id"],)
        ).fetchone()
        if existing:
            skipped += 1
            continue

        payload = json.loads(row["payload_json"])
        # Wrap MCP payload in standard UATP capsule structure
        uatp_payload = {
            "capsule_type": "mcp-gateway",
            "mcp_capsule_type": row["capsule_type"],
            "session_id": row["session_id"],
            "parent_id": row["parent_id"],
            "upstream_server_id": row["upstream_server_id"],
            "payload_hash": row["payload_hash"],
            "mcp_payload": payload,
        }

        if not dry_run:
            uatp_conn.execute(
                """
                INSERT INTO capsules (capsule_id, capsule_type, version, timestamp, status, verification, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (capsule_id) DO NOTHING
                """,
                (
                    row["capsule_id"],
                    "mcp-gateway",
                    "1.0",
                    row["timestamp"],
                    "verified" if row["signature"] else "pending",
                    json.dumps(
                        {"signature": row["signature"], "hash": row["payload_hash"]}
                    ),
                    json.dumps(uatp_payload),
                ),
            )
        inserted += 1

    if not dry_run:
        uatp_conn.commit()
    uatp_conn.close()

    print(f"MCP capsules: {len(rows)} total")
    print(f"{'Would insert' if dry_run else 'Inserted'}: {inserted}")
    print(f"Skipped (already present): {skipped}")


if __name__ == "__main__":
    main()
