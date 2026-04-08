#!/usr/bin/env python3
"""Analyze tool call sequences from UATP capsules with tool_call_graph data."""

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "uatp_dev.db"


def load_capsules(db_path):
    """Load capsules that have tool_call_graph in payload."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        """SELECT capsule_id, capsule_type,
                  json_extract(payload, '$.tool_call_graph') as tcg,
                  json_extract(payload, '$.quality_assessment.overall_quality') as quality
           FROM capsules
           WHERE json_extract(payload, '$.tool_call_graph') IS NOT NULL"""
    ).fetchall()
    conn.close()

    capsules = []
    for cid, ctype, tcg_raw, quality in rows:
        tcg = json.loads(tcg_raw)
        tools = [inv["tool"] for inv in tcg.get("invocations", []) if "tool" in inv]
        capsules.append(
            {
                "capsule_id": cid,
                "capsule_type": ctype,
                "tools": tools,
                "stored_frequency": tcg.get("tool_frequency", {}),
                "total_calls": tcg.get("total_tool_calls", len(tools)),
                "quality": quality,
            }
        )
    return capsules


def compute_ngrams(tools, n):
    return [tuple(tools[i : i + n]) for i in range(len(tools) - n + 1)]


def find_common_subsequences(tools_list, min_len=3, max_len=5):
    """Find frequent contiguous subsequences across all tool sequences."""
    subseq_counts = Counter()
    for tools in tools_list:
        seen = set()
        for length in range(min_len, max_len + 1):
            for i in range(len(tools) - length + 1):
                seq = tuple(tools[i : i + length])
                if seq not in seen:
                    seen.add(seq)
                    subseq_counts[seq] += 1
    # Also count raw occurrences (not deduplicated per capsule)
    raw_counts = Counter()
    for tools in tools_list:
        for length in range(min_len, max_len + 1):
            for i in range(len(tools) - length + 1):
                raw_counts[tuple(tools[i : i + length])] += 1
    return raw_counts.most_common(15)


def analyze(capsules):
    """Run all analyses, return results dict."""
    all_tools = [c["tools"] for c in capsules]

    # (a) Tool frequency: computed vs stored
    computed_freq = Counter()
    for tools in all_tools:
        computed_freq.update(tools)

    stored_freq = Counter()
    for c in capsules:
        for tool, count in c["stored_frequency"].items():
            stored_freq[tool] += count

    freq_match = computed_freq == stored_freq

    # (b) Bigrams
    bigrams = Counter()
    for tools in all_tools:
        bigrams.update(compute_ngrams(tools, 2))

    # (c) Trigrams
    trigrams = Counter()
    for tools in all_tools:
        trigrams.update(compute_ngrams(tools, 3))

    # (d) Common subsequences
    common_seqs = find_common_subsequences(all_tools)

    # (e) Quality correlation
    quality_corr = []
    for c in capsules:
        if c["quality"] is not None:
            top_tools = Counter(c["tools"]).most_common(3)
            quality_corr.append(
                {
                    "capsule_id": c["capsule_id"],
                    "quality": c["quality"],
                    "total_calls": c["total_calls"],
                    "top_tools": [(t, n) for t, n in top_tools],
                    "unique_tools": len(set(c["tools"])),
                }
            )

    return {
        "capsule_count": len(capsules),
        "total_tool_calls": sum(c["total_calls"] for c in capsules),
        "tool_frequency": dict(computed_freq.most_common()),
        "frequency_matches_stored": freq_match,
        "stored_frequency": dict(stored_freq.most_common()),
        "bigrams": [{"pair": list(k), "count": v} for k, v in bigrams.most_common(20)],
        "trigrams": [
            {"triple": list(k), "count": v} for k, v in trigrams.most_common(15)
        ],
        "common_sequences": [{"seq": list(k), "count": v} for k, v in common_seqs],
        "quality_correlation": sorted(
            quality_corr, key=lambda x: x["quality"], reverse=True
        ),
    }


def print_report(results):
    """Print plain text report."""
    print("=" * 60)
    print("UATP Tool Pattern Analysis")
    print("=" * 60)
    print(f"Capsules with tool_call_graph: {results['capsule_count']}")
    print(f"Total tool calls: {results['total_tool_calls']}")
    print()

    print("--- Tool Frequency (computed) ---")
    for tool, count in results["tool_frequency"].items():
        print(f"  {tool:25s} {count:4d}")
    match = "YES" if results["frequency_matches_stored"] else "NO (mismatch)"
    print(f"\n  Matches stored tool_frequency? {match}")
    if not results["frequency_matches_stored"]:
        print("  Stored frequency:")
        for tool, count in results["stored_frequency"].items():
            print(f"    {tool:25s} {count:4d}")
    print()

    print("--- Bigrams (consecutive pairs) ---")
    for b in results["bigrams"][:15]:
        a, z = b["pair"]
        print(f"  {a:20s} -> {z:20s}  {b['count']:3d}")
    print()

    print("--- Trigrams (consecutive triples) ---")
    for t in results["trigrams"][:10]:
        seq = " -> ".join(t["triple"])
        print(f"  {seq:50s}  {t['count']:3d}")
    print()

    print("--- Common Sequences (len 3-5) ---")
    for s in results["common_sequences"][:10]:
        seq = " -> ".join(s["seq"])
        print(f"  [{len(s['seq'])}] {seq:60s} {s['count']:3d}")
    print()

    print("--- Quality Correlation ---")
    if not results["quality_correlation"]:
        print("  No capsules have both tool_call_graph and quality_assessment.")
    for qc in results["quality_correlation"]:
        print(
            f"  {qc['capsule_id'][:40]:40s}  quality={qc['quality']:.3f}  "
            f"calls={qc['total_calls']}  unique={qc['unique_tools']}"
        )
        for tool, n in qc["top_tools"]:
            print(f"    {tool}: {n}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze tool call patterns from UATP capsules"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write JSON to scripts/analysis/tool_patterns.json",
    )
    parser.add_argument(
        "--db", type=str, default=str(DB_PATH), help="Path to SQLite database"
    )
    args = parser.parse_args()

    db = Path(args.db)
    if not db.exists():
        print(f"Database not found: {db}", file=sys.stderr)
        sys.exit(1)

    capsules = load_capsules(db)
    if not capsules:
        print("No capsules with tool_call_graph found.", file=sys.stderr)
        sys.exit(0)

    results = analyze(capsules)
    print_report(results)

    if args.json:
        out = Path(__file__).parent / "tool_patterns.json"
        out.write_text(json.dumps(results, indent=2))
        print(f"JSON written to {out}")


if __name__ == "__main__":
    main()
