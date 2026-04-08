#!/usr/bin/env python3
"""
Confidence Calibration Autoresearch
====================================

Uses Gemma to iteratively calibrate the confidence heuristic weights
in RichCaptureEnhancer.calculate_message_confidence against actual
outcomes from DPO pairs.

The loop:
  1. Read current weights from config
  2. Evaluate: for each confidence bucket, compute actual acceptance rate
  3. Compute calibration error (mean absolute difference)
  4. Gemma proposes adjusted weights
  5. Evaluate again. Keep if error decreased, revert if not.
  6. Repeat.

Usage:
    python3 scripts/autoresearch/calibrate_confidence.py [--iterations 30]
"""

import json
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

DB_PATH = project_root / "uatp_dev.db"
CONFIG_PATH = Path(__file__).parent / "confidence_weights.json"
RESULTS_PATH = Path(__file__).parent / "calibration_results.json"

# Default weights matching current code in rich_capture_integration.py
DEFAULT_WEIGHTS = {
    "assistant_base": 0.85,
    "user_base": 0.70,
    "long_content_boost": 0.05,  # content_length > 1000
    "short_content_penalty": -0.10,  # content_length < 100
    "code_boost": 0.08,  # has_code
    "question_penalty": -0.05,  # has_questions
    "high_tokens_boost": 0.02,  # token_count > 500
    "long_content_threshold": 1000,
    "short_content_threshold": 100,
    "high_tokens_threshold": 500,
}


def load_weights() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    CONFIG_PATH.write_text(json.dumps(DEFAULT_WEIGHTS, indent=2))
    return DEFAULT_WEIGHTS.copy()


def save_weights(weights: dict):
    CONFIG_PATH.write_text(json.dumps(weights, indent=2))


def predict_confidence(
    weights: dict,
    role: str,
    content_length: int,
    token_count: int,
    has_code: bool,
    has_questions: bool,
) -> float:
    base = weights["assistant_base"] if role == "assistant" else weights["user_base"]
    if content_length > weights["long_content_threshold"]:
        base += weights["long_content_boost"]
    elif content_length < weights["short_content_threshold"]:
        base += weights["short_content_penalty"]
    if has_code:
        base += weights["code_boost"]
    if has_questions:
        base += weights["question_penalty"]
    if token_count and token_count > weights["high_tokens_threshold"]:
        base += weights["high_tokens_boost"]
    return min(0.95, max(0.05, base))


def load_dpo_pairs() -> list:
    """Load DPO pairs from the extracted JSONL."""
    dpo_path = project_root / "scripts" / "analysis" / "dpo_pairs.jsonl"
    if not dpo_path.exists():
        print(f"DPO pairs not found at {dpo_path}")
        print("Run: python3 scripts/analysis/extract_dpo_pairs.py first")
        sys.exit(1)
    pairs = []
    with open(dpo_path) as f:
        for line in f:
            pairs.append(json.loads(line))
    return pairs


def evaluate(weights: dict, pairs: list) -> dict:
    """Compute calibration metrics: predicted confidence vs actual acceptance rate per bucket."""
    buckets = {}  # bucket_label -> [predicted_conf, actual_outcome]

    for pair in pairs:
        response = pair.get("response", "")
        content_length = len(response)
        has_code = "```" in response or "def " in response
        has_questions = "?" in response
        # Rough token estimate
        token_count = len(response.split())

        predicted = predict_confidence(
            weights, "assistant", content_length, token_count, has_code, has_questions
        )

        # Bucket by predicted confidence (0.1 wide buckets)
        bucket = round(predicted, 1)
        bucket_key = f"{bucket:.1f}"

        if bucket_key not in buckets:
            buckets[bucket_key] = {"predictions": [], "outcomes": []}

        buckets[bucket_key]["predictions"].append(predicted)
        # 1.0 = chosen (accepted), 0.0 = rejected (corrected)
        buckets[bucket_key]["outcomes"].append(
            1.0 if pair["label"] == "chosen" else 0.0
        )

    # Compute calibration error per bucket
    calibration = {}
    total_error = 0.0
    n_buckets = 0

    for bucket_key, data in sorted(buckets.items()):
        avg_predicted = sum(data["predictions"]) / len(data["predictions"])
        avg_actual = sum(data["outcomes"]) / len(data["outcomes"])
        error = abs(avg_predicted - avg_actual)
        calibration[bucket_key] = {
            "avg_predicted": round(avg_predicted, 4),
            "avg_actual": round(avg_actual, 4),
            "error": round(error, 4),
            "count": len(data["predictions"]),
        }
        total_error += error
        n_buckets += 1

    mae = total_error / max(1, n_buckets)

    return {
        "mae": round(mae, 4),
        "buckets": calibration,
        "total_pairs": len(pairs),
    }


def call_gemma(prompt: str) -> str:
    import requests

    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma4:latest",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.4, "num_predict": 2000},
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        print(f"  Gemma error: {e}")
        return ""


def extract_json(response: str) -> dict:
    """Extract JSON from Gemma's response."""
    # Try the whole thing
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass
    # Find JSON block
    import re

    match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    # Try to find within markdown
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return {}


def build_prompt(
    weights: dict, eval_result: dict, iteration: int, history: list
) -> str:
    compact_weights = json.dumps(weights, separators=(",", ":"))
    buckets_summary = ""
    for bk, bv in sorted(eval_result["buckets"].items()):
        buckets_summary += f"  {bk}: predicted={bv['avg_predicted']:.3f} actual={bv['avg_actual']:.3f} error={bv['error']:.3f} n={bv['count']}\n"

    recent = ""
    if history:
        for h in history[-3:]:
            recent += f"  iter={h['iteration']} mae={h['mae']:.4f}\n"

    return f"""Calibrate AI confidence weights. Iteration {iteration}. Current MAE: {eval_result["mae"]:.4f}

Current weights: {compact_weights}

Calibration by bucket (predicted vs actual acceptance rate):
{buckets_summary}
Recent history:
{recent}
Goal: minimize MAE (difference between predicted confidence and actual acceptance rate).
If predicted > actual, the model is overconfident at that level.
If predicted < actual, the model is underconfident.

Adjust weights to bring predicted closer to actual. Output ONLY compact JSON with these keys:
{{"assistant_base":N,"user_base":N,"long_content_boost":N,"short_content_penalty":N,"code_boost":N,"question_penalty":N,"high_tokens_boost":N,"long_content_threshold":N,"short_content_threshold":N,"high_tokens_threshold":N}}

Constraints: all confidence values 0.05-0.95, thresholds are integers.
Output JSON only, no explanation."""


def run(iterations: int = 30):
    pairs = load_dpo_pairs()
    print(f"Loaded {len(pairs)} DPO pairs")

    weights = load_weights()
    baseline = evaluate(weights, pairs)
    print(f"Baseline MAE: {baseline['mae']:.4f}")
    print()

    best_mae = baseline["mae"]
    best_weights = weights.copy()
    history = [{"iteration": 0, "mae": baseline["mae"], "weights": weights.copy()}]

    for i in range(1, iterations + 1):
        current_eval = evaluate(weights, pairs)
        prompt = build_prompt(weights, current_eval, i, history)

        print(
            f"Iteration {i}/{iterations} — current MAE: {current_eval['mae']:.4f}",
            end=" ",
        )
        sys.stdout.flush()

        response = call_gemma(prompt)
        if not response:
            print("— no response, skipping")
            continue

        proposed = extract_json(response)
        if not proposed or "assistant_base" not in proposed:
            print("— bad JSON, skipping")
            continue

        # Validate
        valid = True
        for key in DEFAULT_WEIGHTS:
            if key not in proposed:
                valid = False
                break
            if "threshold" in key:
                proposed[key] = int(proposed[key])
            else:
                proposed[key] = float(proposed[key])
                if not (0.0 <= proposed[key] <= 1.0) and "penalty" not in key:
                    valid = False
                    break
        if not valid:
            print("— invalid weights, skipping")
            continue

        # Evaluate proposed
        proposed_eval = evaluate(proposed, pairs)

        if proposed_eval["mae"] < current_eval["mae"]:
            improvement = current_eval["mae"] - proposed_eval["mae"]
            print(
                f"— improved! MAE {proposed_eval['mae']:.4f} (delta: -{improvement:.4f})"
            )
            weights = proposed
            save_weights(weights)

            if proposed_eval["mae"] < best_mae:
                best_mae = proposed_eval["mae"]
                best_weights = proposed.copy()
        else:
            print(f"— no improvement ({proposed_eval['mae']:.4f}), reverting")

        history.append(
            {
                "iteration": i,
                "mae": evaluate(weights, pairs)["mae"],
                "weights": weights.copy(),
            }
        )

        # Early stop if well calibrated
        if best_mae < 0.02:
            print("\nCalibration error below 2%, stopping early.")
            break

    # Final report
    final_eval = evaluate(best_weights, pairs)
    print(f"\n{'=' * 60}")
    print("CALIBRATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Baseline MAE:  {baseline['mae']:.4f}")
    print(f"Final MAE:     {final_eval['mae']:.4f}")
    print(f"Improvement:   {baseline['mae'] - final_eval['mae']:.4f}")
    print()
    print("Final weights:")
    for k, v in best_weights.items():
        default = DEFAULT_WEIGHTS[k]
        changed = " *" if v != default else ""
        print(f"  {k}: {v}{changed}")
    print()
    print("Calibration by bucket:")
    for bk, bv in sorted(final_eval["buckets"].items()):
        direction = (
            "overconfident"
            if bv["avg_predicted"] > bv["avg_actual"]
            else "underconfident"
        )
        print(
            f"  {bk}: predicted={bv['avg_predicted']:.3f} actual={bv['avg_actual']:.3f} ({direction}, n={bv['count']})"
        )

    # Save results
    save_weights(best_weights)
    RESULTS_PATH.write_text(
        json.dumps(
            {
                "timestamp": datetime.now().isoformat(),
                "baseline_mae": baseline["mae"],
                "final_mae": final_eval["mae"],
                "iterations": len(history) - 1,
                "best_weights": best_weights,
                "calibration": final_eval["buckets"],
                "history": history,
            },
            indent=2,
        )
    )
    print(f"\nWeights saved to {CONFIG_PATH}")
    print(f"Full results saved to {RESULTS_PATH}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=30)
    args = parser.parse_args()
    run(args.iterations)
