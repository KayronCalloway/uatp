"""
UATP MCP Sessions Router
========================

Read-only API for inspecting MCP-certified agent session graphs.

This router provides the bridge between the MCP certifying gateway's
local SQLite store and the UATP web frontend. It is intentionally
read-only: the gateway writes, this router reads.

Design:
- Reads from the default MCP store path (configurable via env)
- Returns capsule graphs with evidence class + source layer annotations
- No auth required for MVP (sessions are audit trails, not secrets)
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/mcp", tags=["MCP Sessions"])


def _get_store_path() -> Path:
    """Resolve the MCP capsule store database path."""
    env_path = os.getenv("UATP_MCP_STORE_PATH")
    if env_path:
        return Path(env_path)
    # Default: look in cwd (where gateway is typically started)
    return Path("uatp_mcp_store.db")


def _connect() -> sqlite3.Connection:
    """Open a read-only connection to the MCP store."""
    db_path = _get_store_path()
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="MCP store not found")
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


@router.get("/sessions", summary="List MCP session IDs")
async def list_sessions() -> dict[str, Any]:
    """List all session IDs in the MCP store, newest first."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT session_id, MAX(timestamp) as latest
            FROM capsules
            GROUP BY session_id
            ORDER BY latest DESC
            """
        ).fetchall()

    return {
        "sessions": [
            {"session_id": row[0], "latest_timestamp": row[1]} for row in rows
        ],
        "total": len(rows),
    }


@router.get("/sessions/{session_id}", summary="Get session graph")
async def get_session(session_id: str) -> dict[str, Any]:
    """Retrieve the full capsule graph for a session."""
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                capsule_id,
                capsule_type,
                parent_id,
                payload_json,
                signature,
                timestamp,
                upstream_server_id
            FROM capsules
            WHERE session_id = ?
            ORDER BY timestamp ASC
            """,
            (session_id,),
        ).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="Session not found")

    capsules = []
    for r in rows:
        payload = json.loads(r["payload_json"])
        capsules.append(
            {
                "capsule_id": r["capsule_id"],
                "type": r["capsule_type"],
                "parent_id": r["parent_id"],
                "timestamp": r["timestamp"],
                "upstream_server_id": r["upstream_server_id"],
                "signature_preview": (
                    r["signature"][:40] + "..." if r["signature"] else None
                ),
                "payload": payload,
            }
        )

    # Build evidence class summary
    evidence_classes: set[str] = set()
    source_layers: set[str] = set()
    for cap in capsules:
        payload = cap["payload"]
        for key, val in payload.items():
            if isinstance(val, dict):
                if "evidence_class" in val:
                    evidence_classes.add(val["evidence_class"])
                if "source_layer" in val:
                    source_layers.add(val["source_layer"])

    return {
        "session_id": session_id,
        "capsule_count": len(capsules),
        "evidence_classes": sorted(evidence_classes),
        "source_layers": sorted(source_layers),
        "capsules": capsules,
    }


@router.get("/sessions/{session_id}/graph", summary="Get ASCII graph")
async def get_session_graph(session_id: str) -> dict[str, str]:
    """Return a rendered ASCII graph of the session."""
    # Import graph viewer for rendering
    from src.integrations.mcp.graph_viewer import get_session_graph, render_graph

    db_path = _get_store_path()
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="MCP store not found")

    capsules = get_session_graph(str(db_path), session_id)
    if not capsules:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "graph": render_graph(capsules),
    }
