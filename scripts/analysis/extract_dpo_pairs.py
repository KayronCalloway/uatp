#!/usr/bin/env python3
"""
Extract DPO preference pairs from UATP capsules.

Two extraction modes:
1. Labeled singles: assistant response + next user signal (chosen/rejected)
2. Correction chains: prompt → rejected response → correction → chosen response
   These are true preference pairs (same prompt, two responses, clear preference).

Output: JSONL compatible with TRL/Axolotl DPO trainers.
"""

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
DB_PATH = project_root / "uatp_dev.db"
OUTPUT_PATH = Path(__file__).parent / "dpo_pairs.jsonl"

# Import signal detector without heavy __init__.py
spec = importlib.util.spec_from_file_location(
    "signal_detector", project_root / "src" / "live_capture" / "signal_detector.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
SignalDetector = mod.SignalDetector

CHOSEN_SIGNALS = {"acceptance", "refinement", "code_execution"}
REJECTED_SIGNALS = {"correction", "requery", "abandonment", "soft_rejection"}


def get_step_text(step):
    return (step.get("reasoning") or step.get("content") or "").strip()


def get_step_signal(step):
    sig = step.get("signal_type")
    if sig and sig != "neutral":
        return sig
    m = step.get("measurements") or {}
    sig = m.get("signal_type")
    if sig and sig != "neutral":
        return sig
    return None


def extract_thinking(text):
    """Split [THINKING]...[/THINKING] from content."""
    import re

    match = re.search(r"\[THINKING\]\n?(.*?)\n?\[/THINKING\]", text, re.DOTALL)
    if match:
        thinking = match.group(1).strip()
        clean = re.sub(
            r"\[THINKING\].*?\[/THINKING\]\s*", "", text, flags=re.DOTALL
        ).strip()
        return thinking, clean
    # Also check for separate thinking field
    return None, text


def extract_model(payload):
    return (
        payload.get("model_used")
        or payload.get("model")
        or payload.get("session_metadata", {}).get("hermes_model")
        or "unknown"
    )


def run():
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute("""
        SELECT capsule_id, payload FROM capsules
        WHERE json_array_length(json_extract(payload, '$.reasoning_steps')) > 5
        AND capsule_type IN ('reasoning_trace', 'hermes-capture', 'claude-code-capture')
    """).fetchall()
    conn.close()

    detector = SignalDetector()
    labeled_pairs = []
    chain_pairs = []

    for capsule_id, payload_str in rows:
        p = json.loads(payload_str)
        steps = p.get("reasoning_steps", [])
        model = extract_model(p)

        # --- Mode 1: Labeled singles ---
        prev_user_msgs = []
        for i in range(len(steps)):
            if steps[i].get("role") != "user":
                continue
            user_text = get_step_text(steps[i])
            if not user_text:
                continue

            # Find preceding assistant response
            asst_idx = None
            for x in range(i - 1, max(i - 5, -1), -1):
                if steps[x].get("role") == "assistant":
                    asst_idx = x
                    break
            if asst_idx is None:
                prev_user_msgs.append(user_text)
                continue

            asst_text = get_step_text(steps[asst_idx])
            if not asst_text:
                prev_user_msgs.append(user_text)
                continue

            # Get signal from step or run detector
            sig = get_step_signal(steps[i])
            if not sig:
                detected = detector.detect_signal(user_text, prev_user_msgs, "user")
                sig = (
                    detected.signal_type if detected.signal_type != "neutral" else None
                )

            if sig and sig in CHOSEN_SIGNALS | REJECTED_SIGNALS:
                # Find the prompt that triggered this response
                prompt_idx = None
                for x in range(asst_idx - 1, max(asst_idx - 5, -1), -1):
                    if steps[x].get("role") == "user":
                        prompt_idx = x
                        break

                prompt_text = (
                    get_step_text(steps[prompt_idx]) if prompt_idx is not None else ""
                )
                thinking, clean_response = extract_thinking(asst_text)

                labeled_pairs.append(
                    {
                        "prompt": prompt_text,
                        "response": clean_response,
                        "thinking": thinking,
                        "label": "chosen" if sig in CHOSEN_SIGNALS else "rejected",
                        "signal_type": sig,
                        "model": model,
                        "capsule_id": capsule_id,
                        "pair_type": "labeled_single",
                    }
                )

            prev_user_msgs.append(user_text)

        # --- Mode 2: Correction chains ---
        # Pattern: user[i] → asst[j](rejected) → user[k](correction) → asst[m](chosen)
        for i in range(len(steps)):
            if steps[i].get("role") != "user":
                continue
            prompt_text = get_step_text(steps[i])
            if not prompt_text:
                continue

            # Find next assistant
            j = None
            for x in range(i + 1, min(i + 5, len(steps))):
                if steps[x].get("role") == "assistant":
                    j = x
                    break
            if j is None:
                continue

            # Find next user (correction?)
            k = None
            for x in range(j + 1, min(j + 5, len(steps))):
                if steps[x].get("role") == "user":
                    k = x
                    break
            if k is None:
                continue

            correction_text = get_step_text(steps[k])
            sig = get_step_signal(steps[k])
            if sig not in ("correction", "requery"):
                continue

            # Find next assistant after correction
            m = None
            for x in range(k + 1, min(k + 5, len(steps))):
                if steps[x].get("role") == "assistant":
                    m = x
                    break
            if m is None:
                continue

            rejected_text = get_step_text(steps[j])
            chosen_text = get_step_text(steps[m])
            if not rejected_text or not chosen_text:
                continue

            rej_thinking, rej_clean = extract_thinking(rejected_text)
            cho_thinking, cho_clean = extract_thinking(chosen_text)

            # Combined prompt = original prompt + correction context
            combined_prompt = prompt_text
            if correction_text:
                combined_prompt = (
                    f"{prompt_text}\n\n[User correction: {correction_text}]"
                )

            chain_pairs.append(
                {
                    "prompt": prompt_text,
                    "chosen": cho_clean,
                    "rejected": rej_clean,
                    "chosen_thinking": cho_thinking,
                    "rejected_thinking": rej_thinking,
                    "correction": correction_text,
                    "signal_type": sig,
                    "model": model,
                    "capsule_id": capsule_id,
                    "pair_type": "correction_chain",
                }
            )

    # Write output
    with open(OUTPUT_PATH, "w") as f:
        for pair in chain_pairs:
            f.write(json.dumps(pair) + "\n")
        for pair in labeled_pairs:
            f.write(json.dumps(pair) + "\n")

    # Stats
    from collections import Counter

    chain_models = Counter(p["model"] for p in chain_pairs)
    label_models = Counter(p["model"] for p in labeled_pairs)
    label_signals = Counter(p["signal_type"] for p in labeled_pairs)
    chosen_count = sum(1 for p in labeled_pairs if p["label"] == "chosen")
    rejected_count = sum(1 for p in labeled_pairs if p["label"] == "rejected")

    print(f"Written to {OUTPUT_PATH}")
    print(f"\n  Correction chains: {len(chain_pairs)} (true preference pairs)")
    print(
        f"  Labeled singles:   {len(labeled_pairs)} ({chosen_count} chosen, {rejected_count} rejected)"
    )
    print(f"  Total pairs:       {len(chain_pairs) + len(labeled_pairs)}")
    print(f"  Capsules used:     {len(rows)}")
    print("\n  Chain pairs by model:")
    for m, c in chain_models.most_common():
        print(f"    {m:<35} {c}")
    print("\n  Labeled singles by signal:")
    for s, c in label_signals.most_common():
        print(f"    {s:<25} {c}")


if __name__ == "__main__":
    run()
