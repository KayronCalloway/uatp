"""
UATP MCP Graph Viewer
=====================

CLI tool to inspect certified session graphs from the MCP gateway store.

This is what turns the demo from "we signed a thing" into
"we reconstructed governed behavior."

Usage:
    python -m src.integrations.mcp.graph_viewer --session sess_abc123
    python -m src.integrations.mcp.graph_viewer --latest
    python -m src.integrations.mcp.graph_viewer --store uatp_mcp_store.db --list
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List


def list_sessions(db_path: str) -> list[str]:
    """List all session ids in the store."""
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT DISTINCT session_id FROM capsules ORDER BY timestamp DESC"
        ).fetchall()
        return [r[0] for r in rows]


def get_session_graph(db_path: str, session_id: str) -> list[dict[str, Any]]:
    """Retrieve all capsules for a session, ordered by time."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT capsule_id, capsule_type, parent_id, payload_json,
                   signature, timestamp
            FROM capsules
            WHERE session_id = ?
            ORDER BY timestamp ASC
            """,
            (session_id,),
        ).fetchall()
        return [
            {
                "capsule_id": r["capsule_id"],
                "type": r["capsule_type"],
                "parent": r["parent_id"],
                "timestamp": r["timestamp"],
                "payload": json.loads(r["payload_json"]),
                "signature": r["signature"][:40] + "..." if r["signature"] else "none",
            }
            for r in rows
        ]


def render_graph(capsules: list[dict[str, Any]]) -> str:
    """Render a session graph as an ASCII tree."""
    if not capsules:
        return "(no capsules)"

    lines = []
    indent = "    "

    for cap in capsules:
        ctype = cap["type"]
        cid = cap["capsule_id"]
        parent = cap["parent"]
        payload = cap["payload"]

        if ctype == "DECISION_POINT":
            selected = (
                payload.get("decision", {}).get("selected_action", {}).get("value", "?")
            )
            lines.append(f"├─ DECISION_POINT: {selected}")

        elif ctype == "TOOL_CALL":
            tool = payload.get("tool", {}).get("name", {}).get("value", "?")
            status = payload.get("execution", {}).get("status", {}).get("value", "?")
            latency = (
                payload.get("execution", {}).get("latency_ms", {}).get("value", "?")
            )
            lines.append(f"{indent}└─ TOOL_CALL: {tool} ({status}, {latency}ms)")
            lines.append(f"{indent}   └─ proof: {cid}")

        elif ctype == "REFUSAL":
            attempted = payload.get("attempted_tool", {}).get("value", "?")
            reason = payload.get("reason", {}).get("value", "?")
            lines.append(f"{indent}└─ REFUSAL: {attempted}")
            lines.append(f"{indent}   └─ reason: {reason}")
            lines.append(f"{indent}   └─ proof: {cid}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="UATP MCP Graph Viewer")
    parser.add_argument("--store", default="uatp_mcp_store.db", help="Capsule store DB")
    parser.add_argument("--session", help="Session id to inspect")
    parser.add_argument(
        "--latest", action="store_true", help="Show most recent session"
    )
    parser.add_argument("--list", action="store_true", help="List all sessions")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    db_path = args.store
    if not Path(db_path).exists():
        print(f"Store not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    if args.list:
        sessions = list_sessions(db_path)
        print(f"Sessions in {db_path}:")
        for sid in sessions:
            print(f"  {sid}")
        return

    session_id = args.session
    if args.latest:
        sessions = list_sessions(db_path)
        if not sessions:
            print("No sessions found.", file=sys.stderr)
            sys.exit(1)
        session_id = sessions[0]
        print(f"Latest session: {session_id}\n")

    if not session_id:
        print("Provide --session or --latest", file=sys.stderr)
        sys.exit(1)

    capsules = get_session_graph(db_path, session_id)

    if args.raw:
        print(json.dumps(capsules, indent=2))
    else:
        print(f"Session: {session_id}")
        print(f"Capsules: {len(capsules)}")
        print("-" * 50)
        print(render_graph(capsules))


if __name__ == "__main__":
    main()
