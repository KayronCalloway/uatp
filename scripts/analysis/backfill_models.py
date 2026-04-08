#!/usr/bin/env python3
"""Backfill model_used for reasoning_trace capsules with unknown/NULL models.

Matches capsules to Claude Code JSONL transcripts using:
  1. Direct sessionId match (from legacy_payload.environment)
  2. Timestamp-based match (capsule captured_at falls within JSONL session range)
  3. Skips capsules with no matching JSONL

Usage: python3 scripts/analysis/backfill_models.py [--dry-run]
"""

import glob
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path.home() / "uatp-capsule-engine" / "uatp_dev.db"
JSONL_GLOB = str(Path.home() / ".claude/projects/*/*.jsonl")
DRY_RUN = "--dry-run" in sys.argv


def load_jsonl_sessions():
    """Build session map from JSONL files: {sessionId: {model, start, end}}."""
    sessions = {}
    for fpath in sorted(glob.glob(JSONL_GLOB)):
        sid = os.path.basename(fpath).replace(".jsonl", "")
        model = None
        timestamps = []
        try:
            with open(fpath) as f:
                for line in f:
                    entry = json.loads(line)
                    ts = entry.get("timestamp")
                    if ts:
                        timestamps.append(ts)
                    if (
                        not model
                        and entry.get("type") == "assistant"
                        and entry.get("message", {}).get("model")
                    ):
                        m = entry["message"]["model"]
                        if m and not m.startswith("<"):  # skip <synthetic>
                            model = m
        except (json.JSONDecodeError, OSError) as e:
            print(f"  WARN: skipping {fpath}: {e}")
            continue
        if model and timestamps:
            sessions[sid] = {
                "model": model,
                "start": min(timestamps),
                "end": max(timestamps),
            }
    print(f"Loaded {len(sessions)} JSONL sessions with valid models")
    return sessions


def find_model_by_timestamp(sessions, capsule_ts):
    """Find the JSONL session active at capsule_ts."""
    if not capsule_ts:
        return None
    # Normalize timestamp for comparison
    ts = capsule_ts.replace("+00:00", "Z").replace(" ", "T")
    if not ts.endswith("Z"):
        ts += "Z"
    for sid, info in sessions.items():
        if info["start"] <= ts <= info["end"]:
            return info["model"]
    return None


def main():
    if DRY_RUN:
        print("=== DRY RUN MODE (no changes will be made) ===\n")

    sessions = load_jsonl_sessions()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Get capsules needing backfill
    cur.execute("""
        SELECT id, capsule_id, payload FROM capsules
        WHERE capsule_type = 'reasoning_trace'
          AND (json_extract(payload, '$.model_used') IS NULL
               OR json_extract(payload, '$.model_used') = 'unknown')
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} capsules needing model backfill\n")

    updated = 0
    skipped_no_match = 0
    skipped_already = 0
    by_model = {}

    for i, row in enumerate(rows):
        payload = json.loads(row["payload"])
        legacy = payload.get("legacy_payload", {})

        # Skip if already has real model
        existing = payload.get("model_used") or legacy.get("model_used")
        PLACEHOLDER_MODELS = {
            "unknown",
            "assistant:claude-code-model",
            "user:claude-code-model",
            "user:claude_code_test-model",
            "assistant:test-model",
            "user:claude_code_auto-model",
            "assistant:claude-opus-4-5",
        }
        if existing and existing not in PLACEHOLDER_MODELS:
            skipped_already += 1
            continue

        model = None

        # Strategy 1: direct sessionId from environment
        env = legacy.get("environment", {})
        if isinstance(env, dict):
            env_sid = env.get("sessionId")
            if env_sid and env_sid in sessions:
                model = sessions[env_sid]["model"]

        # Strategy 2: timestamp match
        if not model:
            cap_ts = env.get("captured_at") if isinstance(env, dict) else None
            if not cap_ts:
                cap_ts = payload.get("timestamp")
            model = find_model_by_timestamp(sessions, cap_ts)

        if not model:
            skipped_no_match += 1
            continue

        # Update payload
        payload["model_used"] = model
        if "legacy_payload" in payload and "model_used" in payload["legacy_payload"]:
            payload["legacy_payload"]["model_used"] = model

        if not DRY_RUN:
            cur.execute(
                "UPDATE capsules SET payload = ? WHERE id = ?",
                (json.dumps(payload), row["id"]),
            )

        updated += 1
        by_model[model] = by_model.get(model, 0) + 1

        if (i + 1) % 100 == 0:
            print(f"  Progress: {i + 1}/{len(rows)} processed, {updated} updated")

    if not DRY_RUN:
        conn.commit()
    conn.close()

    print(f"\n{'=' * 50}")
    print(f"SUMMARY {'(DRY RUN)' if DRY_RUN else ''}")
    print(f"{'=' * 50}")
    print(f"Total capsules scanned:  {len(rows)}")
    print(f"Updated:                 {updated}")
    print(f"Skipped (no match):      {skipped_no_match}")
    print(f"Skipped (already set):   {skipped_already}")
    print("\nModels assigned:")
    for m, c in sorted(by_model.items(), key=lambda x: -x[1]):
        print(f"  {m}: {c}")


if __name__ == "__main__":
    main()
