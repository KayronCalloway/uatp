#!/usr/bin/env python3
"""Cross-model analysis of UATP capsules."""

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "uatp_dev.db"
CAPSULE_TYPES = (
    "reasoning_trace",
    "hermes-capture",
    "claude-code-capture",
    "ollama_proxy_capture",
    "ollama_conversation",
)


def get_conn():
    if not DB_PATH.exists():
        print(f"ERROR: database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def extract_model(p):
    return (
        p.get("model_used")
        or p.get("model")
        or (p.get("session_metadata") or {}).get("hermes_model")
        or (p.get("metadata") or {}).get("model")
        or "unknown"
    )


def count_steps(p):
    steps = (
        p.get("reasoning_steps")
        or (p.get("reasoning_trace") or {}).get("reasoning_steps")
        or []
    )
    return len(steps), steps


def extract_confidence(steps):
    vals = [s["confidence"] for s in steps if s.get("confidence") is not None]
    return sum(vals) / len(vals) if vals else None


def extract_signals(p):
    fs = (p.get("session_metadata") or {}).get("feedback_signals")
    return (
        (fs.get("correction_rate"), fs.get("acceptance_rate")) if fs else (None, None)
    )


def extract_economics(p):
    econ = p.get("economics")
    if econ:
        return econ
    meta = p.get("metadata") or {}
    if meta.get("eval_count"):
        return {"total_tokens": meta["eval_count"], "cache_hit_rate": None}
    return None


def extract_thinking(p):
    et = p.get("extended_thinking")
    return et.get("thinking_to_response_ratio") if et else None


def run_signal_detection_lazy(steps):
    """Fallback: run signal detector on steps without pre-computed signals."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
        from live_capture.signal_detector import aggregate_signals, detect_signal
    except ImportError:
        return None, None

    signals = []
    prev_msgs = []
    for s in steps:
        if s.get("role") == "user":
            text = s.get("content") or s.get("reasoning") or ""
            sig = detect_signal(text, prev_msgs, "user")
            signals.append(sig)
        prev_msgs.append(s.get("content") or s.get("reasoning") or "")

    if not signals:
        return None, None
    agg = aggregate_signals(signals)
    return agg.correction_rate, agg.acceptance_rate


def build_report():
    conn = get_conn()
    placeholders = ",".join("?" for _ in CAPSULE_TYPES)
    rows = conn.execute(
        f"SELECT capsule_id, capsule_type, payload FROM capsules WHERE capsule_type IN ({placeholders})",
        CAPSULE_TYPES,
    ).fetchall()
    conn.close()

    models = defaultdict(
        lambda: {
            "capsules": 0,
            "total_steps": 0,
            "confidences": [],
            "correction_rates": [],
            "acceptance_rates": [],
            "total_tokens": 0,
            "token_capsules": 0,
            "cache_hits": [],
            "thinking_ratios": [],
            "types": defaultdict(int),
        }
    )

    for row in rows:
        p = json.loads(row["payload"])
        model = extract_model(p)
        if model.startswith(("assistant:", "user:")):
            model = model.split(":", 1)[1]
        m = models[model]
        m["capsules"] += 1
        m["types"][row["capsule_type"]] += 1

        n_steps, steps = count_steps(p)
        m["total_steps"] += n_steps

        conf = extract_confidence(steps)
        if conf is not None:
            m["confidences"].append(conf)

        cr, ar = extract_signals(p)
        if cr is None and steps:
            cr, ar = run_signal_detection_lazy(steps)
        if cr is not None:
            m["correction_rates"].append(cr)
        if ar is not None:
            m["acceptance_rates"].append(ar)

        econ = extract_economics(p)
        if econ:
            m["total_tokens"] += econ.get("total_tokens") or 0
            m["token_capsules"] += 1
            ch = econ.get("cache_hit_rate")
            if ch is not None:
                m["cache_hits"].append(ch)

        tr = extract_thinking(p)
        if tr is not None:
            m["thinking_ratios"].append(tr)

    # build summary dicts
    summary = {}
    for model, m in sorted(models.items(), key=lambda x: -x[1]["capsules"]):

        def avg(lst):
            return sum(lst) / len(lst) if lst else None

        summary[model] = {
            "total_capsules": m["capsules"],
            "total_steps": m["total_steps"],
            "avg_confidence": round(avg(m["confidences"]), 4)
            if m["confidences"]
            else None,
            "correction_rate": round(avg(m["correction_rates"]), 4)
            if m["correction_rates"]
            else None,
            "acceptance_rate": round(avg(m["acceptance_rates"]), 4)
            if m["acceptance_rates"]
            else None,
            "total_tokens": m["total_tokens"],
            "avg_tokens_per_capsule": round(m["total_tokens"] / m["token_capsules"])
            if m["token_capsules"]
            else None,
            "cache_hit_rate": round(avg(m["cache_hits"]), 4)
            if m["cache_hits"]
            else None,
            "avg_thinking_ratio": round(avg(m["thinking_ratios"]), 2)
            if m["thinking_ratios"]
            else None,
            "capsule_types": dict(m["types"]),
        }
    return summary


def print_report(summary):
    total_caps = sum(v["total_capsules"] for v in summary.values())
    print(
        f"=== UATP Cross-Model Report ({total_caps} capsules, {len(summary)} models) ===\n"
    )

    for model, s in summary.items():
        print(f"--- {model} ---")
        print(f"  Capsules:       {s['total_capsules']}")
        print(f"  Conv turns:     {s['total_steps']}")
        print(f"  Avg confidence: {s['avg_confidence'] or 'n/a'}")
        print(
            f"  Correction rate:{' ' + str(s['correction_rate']) if s['correction_rate'] is not None else ' n/a'}"
        )
        print(
            f"  Acceptance rate:{' ' + str(s['acceptance_rate']) if s['acceptance_rate'] is not None else ' n/a'}"
        )
        print(
            f"  Total tokens:   {s['total_tokens']:,}"
            if s["total_tokens"]
            else "  Total tokens:   n/a"
        )
        print(
            f"  Avg tok/capsule:{' ' + str(s['avg_tokens_per_capsule']) if s['avg_tokens_per_capsule'] else ' n/a'}"
        )
        print(f"  Cache hit rate: {s['cache_hit_rate'] or 'n/a'}")
        print(f"  Think ratio:    {s['avg_thinking_ratio'] or 'n/a'}")
        types_str = ", ".join(f"{k}={v}" for k, v in s["capsule_types"].items())
        print(f"  Types:          {types_str}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Cross-model UATP capsule analysis")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write JSON to scripts/analysis/model_comparison.json",
    )
    parser.add_argument("--db", type=str, help="Override database path")
    args = parser.parse_args()

    if args.db:
        global DB_PATH
        DB_PATH = Path(args.db)

    summary = build_report()
    print_report(summary)

    if args.json:
        out = Path(__file__).parent / "model_comparison.json"
        out.write_text(json.dumps(summary, indent=2))
        print(f"JSON written to {out}")


if __name__ == "__main__":
    main()
