#!/usr/bin/env python3
"""
Re-score existing hermes-capture capsules with updated signal guards (SAFE MODE).

Unlike a full re-detection, this only applies guard corrections to the EXISTING
signals in the capsule. This preserves real corrections that the detector
originally caught while fixing known false-positive patterns.

Usage:
    PYTHONPATH=. python3 scripts/analysis/rescore_hermes_capsules.py
    PYTHONPATH=. python3 scripts/analysis/rescore_hermes_capsules.py --apply

Default mode is dry-run. Database writes require explicit --apply.
"""

import argparse
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
DB_PATH = project_root / "uatp_dev.db"


def apply_guards_to_existing(old_sig: str, content: str, pa_len: int) -> str:
    """Apply post-processing guards to an existing signal."""
    lower = content.lower().strip()
    words = lower.split()
    word_count = len(words)
    new_sig = old_sig

    system_meta_markers = (
        "[context compaction",
        "[your active task list was preserved",
        "[note: model was just switched",
    )
    if any(lower.startswith(marker) for marker in system_meta_markers):
        return "neutral"

    # ---- Guard A+B: acceptance false positives ----
    if old_sig == "acceptance":
        # "ok"/"okay" directives
        if lower.startswith("ok") or lower.startswith("okay"):
            gratitude = (
                "thanks",
                "thank you",
                "perfect",
                "great",
                "awesome",
                "cool",
                "nice",
                "good",
                "sounds good",
                "makes sense",
                "got it",
                "i see",
                "appreciate",
            )
            has_gratitude = any(g in lower for g in gratitude)
            directive_verbs = (
                "fix",
                "change",
                "push",
                "run",
                "look",
                "check",
                "add",
                "remove",
                "delete",
                "update",
                "create",
                "build",
                "launch",
                "audit",
                "sweep",
                "commit",
                "merge",
                "pull",
                "apply",
                "implement",
                "write",
                "edit",
                "move",
                "replace",
                "restore",
                "reset",
                "kill",
                "stop",
                "start",
                "restart",
                "upload",
                "download",
                "generate",
                "make",
                "set",
                "configure",
                "deploy",
                "verify",
                "test",
                "go",
                "do",
            )
            has_directive = any(w in directive_verbs for w in words)
            if has_directive or (word_count > 5 and not has_gratitude):
                new_sig = "neutral"

        # Substring-only acceptance in long or questioning messages
        if new_sig == "acceptance":
            if word_count > 10:
                if not re.search(
                    r"^(yes|yep|yeah|yea|sure|ok|okay|right|done|perfect|thanks|thank you|great|awesome|excellent|nice|cool|looks good|sounds good|it works|working now|fixed|solved|got it|makes sense|do it|go ahead|ship it|lgtm)\b",
                    lower,
                ):
                    new_sig = "neutral"
            elif "?" in lower:
                new_sig = "neutral"

    # ---- Guard C: soft_rejection false positives ----
    if old_sig == "soft_rejection":
        if "?" in lower:
            new_sig = "neutral"

        bug_phrases = (
            "isn't",
            "isnt",
            "not working",
            "doesn't work",
            "doesnt work",
            "didn't work",
            "didnt work",
            "still broken",
            "still not",
            "is gone",
            "missing",
            "can't find",
            "cant find",
            "error",
            "bug",
            "issue",
            "problem",
            "wrong",
            "broken",
            "fail",
            "failed",
            "doesn't",
            "doesnt",
            "didn't",
            "didnt",
            "can't",
            "cant",
            "won't",
            "wont",
        )
        if any(p in lower for p in bug_phrases):
            new_sig = "neutral"

        directive_starters = (
            "lets ",
            "let's ",
            "please ",
            "can you ",
            "could you ",
            "would you ",
            "will you ",
            "go ahead",
            "do ",
            "make ",
            "run ",
            "check ",
            "verify ",
            "push ",
            "pull ",
            "commit ",
            "merge ",
            "add ",
            "remove ",
            "delete ",
            "update ",
            "create ",
            "build ",
            "launch ",
            "audit ",
            "sweep ",
            "apply ",
            "implement ",
            "write ",
            "edit ",
            "move ",
            "replace ",
            "restore ",
            "reset ",
            "kill ",
            "stop ",
            "start ",
            "restart ",
            "upload ",
            "download ",
            "generate ",
            "set ",
            "configure ",
            "deploy ",
            "test ",
        )
        if any(lower.startswith(w) for w in directive_starters):
            new_sig = "neutral"

        if lower in (
            "whatever you think",
            "whatever you think is best",
            "up to you",
            "you decide",
            "your call",
            "whatever",
        ):
            new_sig = "neutral"

        if any(
            lower.startswith(w)
            for w in (
                "there are ",
                "there is ",
                "i have ",
                "we have ",
                "it has ",
                "this has ",
                "there's ",
            )
        ):
            new_sig = "neutral"

        # Very short messages are almost never real soft rejections
        if word_count <= 3:
            new_sig = "neutral"

        # Requests and wishes are follow-ups, not rejections
        if (
            "i would like" in lower
            or "i want" in lower
            or "can you" in lower
            or "could you" in lower
        ):
            new_sig = "neutral"

    # ---- Guard D: missed short corrections ----
    if old_sig == "neutral" and pa_len > 500 and word_count <= 5:
        correction_imperatives = (
            "fix it",
            "fix that",
            "fix this",
            "change it",
            "change that",
            "change this",
            "do it again",
            "try again",
            "redo it",
            "redo that",
            "not quite",
            "almost but",
            "close but",
            "still wrong",
            "wrong",
            "no",
            "nope",
            "not that",
            "not this",
            "not it",
            "bad",
            "worse",
            "terrible",
            "awful",
        )
        ok_directive_corrections = (
            "ok fix",
            "okay fix",
            "ok change",
            "okay change",
            "ok redo",
            "okay redo",
            "ok try again",
            "okay try again",
        )
        if any(lower.startswith(c) for c in correction_imperatives) or any(
            lower.startswith(c) for c in ok_directive_corrections
        ):
            new_sig = "correction"

    # ---- Guard E: intent restatements ----
    if old_sig == "neutral" and pa_len > 300:
        if re.search(
            r"^(i asked|i meant|i said|i was asking|i was talking|i want|i need|the issue is|what i want|what i need|what i asked)",
            lower,
        ):
            new_sig = "correction"

    return new_sig


def rescore_capsule(payload: dict) -> tuple[dict, bool]:
    """Re-score all reasoning_steps in a capsule payload. Returns (payload, changed)."""
    steps = payload.get("reasoning_steps", [])
    if not steps:
        return payload, False

    changed = False

    for idx, step in enumerate(steps):
        role = step.get("role")
        if role != "user":
            continue

        content = step.get("content") or step.get("reasoning") or ""
        if not content.strip():
            continue

        measurements = step.setdefault("measurements", {})
        old_sig = measurements.get("signal_type", "neutral")

        # Find previous assistant response length
        pa_len = 0
        for x in range(idx - 1, max(idx - 5, -1), -1):
            if steps[x].get("role") == "assistant":
                pa_len = len(steps[x].get("content") or steps[x].get("reasoning") or "")
                break

        new_sig = apply_guards_to_existing(old_sig, content, pa_len)

        if old_sig != new_sig:
            measurements["signal_type"] = new_sig
            changed = True

    if changed:
        # Rebuild feedback_signals summary
        sig_counts = Counter(
            step.get("measurements", {}).get("signal_type", "neutral")
            for step in steps
            if step.get("role") == "user"
            and step.get("measurements", {}).get("signal_type", "neutral") != "neutral"
        )
        total_user = len([s for s in steps if s.get("role") == "user"])
        if sig_counts:
            payload["feedback_signals"] = {
                "correction_count": sig_counts.get("correction", 0),
                "requery_count": sig_counts.get("requery", 0),
                "refinement_count": sig_counts.get("refinement", 0),
                "acceptance_count": sig_counts.get("acceptance", 0),
                "abandonment_count": sig_counts.get("abandonment", 0),
                "soft_rejection_count": sig_counts.get("soft_rejection", 0),
                "code_execution_count": sig_counts.get("code_execution", 0),
                "total_non_neutral": sum(sig_counts.values()),
                "correction_rate": round(
                    sig_counts.get("correction", 0) / total_user, 4
                )
                if total_user
                else 0.0,
                "acceptance_rate": round(
                    sig_counts.get("acceptance", 0) / total_user, 4
                )
                if total_user
                else 0.0,
                "signal_breakdown": dict(sig_counts),
            }
        else:
            payload.pop("feedback_signals", None)

    return payload, changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write rescored payloads to the database; default is dry-run",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="preview changes without writing; retained for explicitness",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    dry_run = not args.apply

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT id, capsule_id, payload FROM capsules WHERE capsule_type = 'hermes-capture'"
    ).fetchall()

    updated = 0
    total = len(rows)
    signal_changes = Counter()

    print(f"Rescoring {total} hermes-capture capsules (safe mode)...")

    for row in rows:
        payload = json.loads(row["payload"])
        new_payload, changed = rescore_capsule(payload)

        if changed:
            old_steps = json.loads(row["payload"]).get("reasoning_steps", [])
            new_steps = new_payload.get("reasoning_steps", [])
            for old, new in zip(old_steps, new_steps, strict=False):
                old_sig = old.get("measurements", {}).get("signal_type", "neutral")
                new_sig = new.get("measurements", {}).get("signal_type", "neutral")
                if old_sig != new_sig:
                    signal_changes[f"{old_sig}->{new_sig}"] += 1

            if not dry_run:
                conn.execute(
                    "UPDATE capsules SET payload = ? WHERE id = ?",
                    (json.dumps(new_payload), row["id"]),
                )
            updated += 1

    if not dry_run:
        conn.commit()
    conn.close()

    print(
        f"\nDone. {'Would update' if dry_run else 'Updated'} {updated}/{total} capsules."
    )
    if signal_changes:
        print("\nSignal transitions:")
        for transition, count in signal_changes.most_common():
            print(f"  {transition}: {count}")
    else:
        print("\nNo signal transitions.")


if __name__ == "__main__":
    main()
