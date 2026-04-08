#!/usr/bin/env python3
"""Re-score all capsules with the improved signal detector.

Usage:  python scripts/analysis/rescore_capsules.py [--dry-run]
"""

import argparse
import importlib.util
import json
import os
import sqlite3
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location(
    "signal_detector", os.path.join(REPO, "src", "live_capture", "signal_detector.py")
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
SignalDetector, aggregate_signals = mod.SignalDetector, mod.aggregate_signals
DB_PATH = os.path.join(REPO, "uatp_dev.db")
SIGNAL_KEYS = ["correction", "requery", "refinement", "acceptance", "soft_rejection"]


def extract_steps(payload):
    for root in [payload, payload.get("legacy_payload", {})]:
        steps = root.get("reasoning_steps", [])
        if steps and isinstance(steps, list):
            return steps
    return []


def get_text(step):
    return step.get("content") or step.get("reasoning") or ""


def set_feedback(payload, agg_dict):
    for root in [payload, payload.get("legacy_payload", {})]:
        sm = root.get("session_metadata")
        if isinstance(sm, dict):
            sm["feedback_signals"] = agg_dict
            return
    payload.setdefault("session_metadata", {})["feedback_signals"] = agg_dict


def get_old_signals(payload):
    for root in [payload, payload.get("legacy_payload", {})]:
        sm = root.get("session_metadata")
        if isinstance(sm, dict) and "feedback_signals" in sm:
            return sm["feedback_signals"]
    return {}


def main():
    ap = argparse.ArgumentParser(description="Re-score capsules with improved detector")
    ap.add_argument("--dry-run", action="store_true", help="Preview only")
    args = ap.parse_args()

    detector = SignalDetector()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, capsule_id, payload FROM capsules "
        'WHERE payload LIKE \'%"role": "user"%\' OR payload LIKE \'%"role":"user"%\''
    ).fetchall()

    print(f"Found {len(rows)} capsules with user messages")
    if args.dry_run:
        print("[DRY RUN] No database writes will occur\n")

    before, after = Counter(), Counter()
    updated = skipped = 0

    for i, row in enumerate(rows):
        payload = json.loads(row["payload"])
        steps = extract_steps(payload)
        if not any(s.get("role") == "user" for s in steps):
            skipped += 1
            continue

        old = get_old_signals(payload)
        for k in SIGNAL_KEYS:
            before[k] += old.get(f"{k}_count", 0)

        prev_msgs, signals = [], []
        for step in steps:
            if step.get("role") != "user":
                continue
            text = get_text(step)
            if not text.strip():
                continue
            sig = detector.detect_signal(text, prev_msgs, "user")
            signals.append(sig)
            prev_msgs.append(text)
            # Update per-step measurement fields
            meas = step.get("measurements")
            if isinstance(meas, dict):
                meas["signal_type"] = sig.signal_type
                meas["sentiment_delta"] = sig.sentiment_delta
                meas["references_previous"] = sig.references_previous
            for fld in ("signal_type", "sentiment_delta", "references_previous"):
                if fld in step:
                    step[fld] = getattr(sig, fld)

        if not signals:
            skipped += 1
            continue

        agg = aggregate_signals(signals).to_dict()
        set_feedback(payload, agg)
        for k in SIGNAL_KEYS:
            after[k] += agg.get(f"{k}_count", 0)

        if not args.dry_run:
            conn.execute(
                "UPDATE capsules SET payload = ? WHERE id = ?",
                (json.dumps(payload), row["id"]),
            )
        updated += 1
        if (i + 1) % 50 == 0 or (i + 1) == len(rows):
            print(f"  Progress: {i + 1}/{len(rows)} processed, {updated} updated")

    if not args.dry_run:
        conn.commit()
    conn.close()

    tag = " (DRY RUN)" if args.dry_run else ""
    print(f"\n{'=' * 55}\nRescore complete{tag}")
    print(f"  Scanned: {len(rows)}  Updated: {updated}  Skipped: {skipped}")
    print("\nSignal counts  BEFORE -> AFTER:")
    for k in sorted(set(list(before) + list(after))):
        b, a = before.get(k, 0), after.get(k, 0)
        d = a - b
        print(f"  {k:20s}  {b:5d} -> {a:5d}  ({'+' if d >= 0 else ''}{d})")
    print("=" * 55)


if __name__ == "__main__":
    main()
