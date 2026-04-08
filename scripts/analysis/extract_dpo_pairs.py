#!/usr/bin/env python3
"""
Extract DPO (Direct Preference Optimization) training pairs from UATP capsules.

Walks reasoning_steps in capsules, detects implicit user feedback signals on
assistant responses, and labels each as 'chosen' or 'rejected' for DPO training.

Output: scripts/analysis/dpo_pairs.jsonl + summary stats to stdout.
"""

import importlib.util
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

# --- Paths ---
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DB_PATH = PROJECT_ROOT / "uatp_dev.db"
OUTPUT_PATH = SCRIPT_DIR / "dpo_pairs.jsonl"


# --- Import SignalDetector without heavy __init__.py chain ---
def _load_signal_detector():
    sd_path = PROJECT_ROOT / "src" / "live_capture" / "signal_detector.py"
    spec = importlib.util.spec_from_file_location("signal_detector", str(sd_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SignalDetector


SignalDetector = _load_signal_detector()

# --- Signal classification ---
POSITIVE_SIGNALS = {"acceptance", "refinement", "code_execution"}
NEGATIVE_SIGNALS = {"correction", "requery", "abandonment", "soft_rejection"}
# 'neutral' is ambiguous — skip


def extract_thinking(text: str) -> tuple:
    """Extract [THINKING]...[/THINKING] block from response text.
    Returns (thinking_block, cleaned_text)."""
    match = re.search(r"\[THINKING\](.*?)\[/THINKING\]", text, re.DOTALL)
    if match:
        thinking = match.group(1).strip()
        cleaned = text[: match.start()] + text[match.end() :]
        return thinking, cleaned.strip()
    return None, text


def get_step_text(step: dict) -> str:
    """Get the text content from a reasoning step."""
    return step.get("reasoning") or step.get("content") or ""


def get_model(capsule_row: dict) -> str:
    """Best-effort model extraction from capsule data."""
    payload = capsule_row.get("payload", {})
    meta = payload.get("session_metadata", {})
    # Try several locations
    for candidate in [
        meta.get("model"),
        payload.get("model"),
        payload.get("model_id"),
        meta.get("platform"),
        capsule_row.get("capsule_type"),
    ]:
        if candidate:
            return candidate
    return "unknown"


def query_capsules(db_path: str) -> list:
    """Query capsules with >5 reasoning steps of target types."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute("""
        SELECT capsule_id, capsule_type, payload
        FROM capsules
        WHERE capsule_type IN ('reasoning_trace', 'hermes-capture', 'claude-code-capture')
          AND json_array_length(json_extract(payload, '$.reasoning_steps')) > 5
    """)
    rows = []
    for row in cur:
        rows.append(
            {
                "capsule_id": row["capsule_id"],
                "capsule_type": row["capsule_type"],
                "payload": json.loads(row["payload"])
                if isinstance(row["payload"], str)
                else row["payload"],
            }
        )
    conn.close()
    return rows


def extract_pairs_from_capsule(capsule: dict, detector: SignalDetector) -> list:
    """Walk reasoning steps and extract labeled DPO pairs."""
    steps = capsule["payload"].get("reasoning_steps", [])
    model = get_model(capsule)
    capsule_id = capsule["capsule_id"]
    pairs = []

    for i, step in enumerate(steps):
        role = step.get("role", "")
        if role != "assistant":
            continue

        # Find the user prompt BEFORE this assistant response
        prompt_text = None
        for j in range(i - 1, -1, -1):
            if steps[j].get("role") == "user":
                prompt_text = get_step_text(steps[j])
                break
        if not prompt_text:
            continue

        # Find the NEXT user message after this assistant response
        next_user_msg = None
        for j in range(i + 1, len(steps)):
            if steps[j].get("role") == "user":
                next_user_msg = get_step_text(steps[j])
                break
        if not next_user_msg:
            continue  # no follow-up to judge

        # Detect signal from the next user message
        signal = detector.detect_signal(next_user_msg, [prompt_text])

        signal_type = signal.signal_type
        # Also check pre-computed signal in step measurements if available
        if signal_type == "neutral":
            meas = steps[min(i + 1, len(steps) - 1)].get("measurements", {})
            pre_signal = meas.get("signal_type", "neutral")
            if pre_signal in POSITIVE_SIGNALS or pre_signal in NEGATIVE_SIGNALS:
                signal_type = pre_signal

        # Classify
        if signal_type in POSITIVE_SIGNALS:
            label = "chosen"
        elif signal_type in NEGATIVE_SIGNALS:
            label = "rejected"
        else:
            continue  # ambiguous, skip

        response_text = get_step_text(step)
        thinking, cleaned_response = extract_thinking(response_text)

        pairs.append(
            {
                "prompt": prompt_text,
                "response": cleaned_response,
                "label": label,
                "thinking": thinking,
                "signal_type": signal_type,
                "signal_confidence": round(signal.confidence, 3),
                "model": model,
                "capsule_id": capsule_id,
            }
        )

    return pairs


def main():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Querying capsules from {DB_PATH} ...")
    capsules = query_capsules(str(DB_PATH))
    print(f"[*] Found {len(capsules)} capsules with >5 reasoning steps")

    detector = SignalDetector()
    all_pairs = []

    for capsule in capsules:
        pairs = extract_pairs_from_capsule(capsule, detector)
        all_pairs.extend(pairs)

    # Write JSONL
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        for pair in all_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    print(f"[*] Wrote {len(all_pairs)} DPO pairs to {OUTPUT_PATH}")

    # --- Stats ---
    chosen = [p for p in all_pairs if p["label"] == "chosen"]
    rejected = [p for p in all_pairs if p["label"] == "rejected"]
    by_model = defaultdict(lambda: {"chosen": 0, "rejected": 0})
    by_signal = defaultdict(int)

    for p in all_pairs:
        by_model[p["model"]][p["label"]] += 1
        by_signal[p["signal_type"]] += 1

    print("\n=== DPO Extraction Stats ===")
    print(f"  Total pairs:    {len(all_pairs)}")
    print(f"  Chosen:         {len(chosen)}")
    print(f"  Rejected:       {len(rejected)}")
    print(f"  Capsules used:  {len(capsules)}")

    if by_signal:
        print("\n  By signal type:")
        for sig, count in sorted(by_signal.items(), key=lambda x: -x[1]):
            print(f"    {sig:20s} {count}")

    if by_model:
        print("\n  By model:")
        for model, counts in sorted(by_model.items()):
            print(
                f"    {model:30s}  chosen={counts['chosen']}  rejected={counts['rejected']}"
            )

    print()


if __name__ == "__main__":
    main()
