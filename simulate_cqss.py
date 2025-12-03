#!/usr/bin/env python3
"""
simulate_cqss.py - Command-line interface for CQSS simulation.

This script provides a simple CLI for simulating how changes to capsules
would affect their CQSS scores.
"""

import argparse
import json
import sys
from typing import Any, Dict

from capsule_schema import Capsule
from cqss.simulator import CQSSSimulator
from tabulate import tabulate


def load_capsule_from_file(file_path: str, capsule_id: str = None) -> Capsule:
    """
    Load a capsule from a file.

    Args:
        file_path: Path to the JSONL file containing capsules
        capsule_id: Optional ID of the specific capsule to load

    Returns:
        Loaded Capsule object
    """
    try:
        with open(file_path) as f:
            for line in f:
                if line.strip():
                    capsule_dict = json.loads(line)
                    if (
                        capsule_id is None
                        or capsule_dict.get("capsule_id") == capsule_id
                    ):
                        return Capsule.from_dict(capsule_dict)

        if capsule_id:
            print(f"Error: Capsule with ID '{capsule_id}' not found in {file_path}")
        else:
            print(f"Error: No capsules found in {file_path}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in '{file_path}'")
        sys.exit(1)


def format_score_report(report: Dict[str, Any]) -> str:
    """Format a simulation report for display."""

    # Format the original and simulated scores
    original = report["original"]
    simulated = report["simulated"]

    # Create a table for the score breakdown
    headers = ["Metric", "Original", "Simulated", "Change"]
    rows = []

    # Add total score row
    rows.append(
        [
            "Total Score",
            f"{original['total_score']:.1f}",
            f"{simulated['total_score']:.1f}",
            f"{report['difference']:.1f}",
        ]
    )

    # Add rows for each component
    for key in original["breakdown"]:
        if key in simulated["breakdown"]:
            orig_val = original["breakdown"][key]
            sim_val = simulated["breakdown"][key]
            diff = sim_val - orig_val
            rows.append(
                [
                    key.replace("_", " ").title(),
                    f"{orig_val:.1f}",
                    f"{sim_val:.1f}",
                    f"{diff:.1f}",
                ]
            )

    return tabulate(rows, headers=headers, tablefmt="grid")


def simulate_confidence(args):
    """Simulate changing the confidence value."""
    capsule = load_capsule_from_file(args.file, args.id)
    report = CQSSSimulator.simulate_confidence_change(capsule, args.value)
    print(format_score_report(report))


def simulate_reasoning(args):
    """Simulate changing the reasoning trace."""
    capsule = load_capsule_from_file(args.file, args.id)

    # Parse the reasoning trace
    if args.trace_file:
        with open(args.trace_file) as f:
            new_trace = [line.strip() for line in f if line.strip()]
    else:
        new_trace = args.steps

    report = CQSSSimulator.simulate_reasoning_trace_change(capsule, new_trace)
    print(format_score_report(report))


def simulate_policy(args):
    """Simulate changing the ethical policy."""
    capsule = load_capsule_from_file(args.file, args.id)
    report = CQSSSimulator.simulate_ethical_policy_change(capsule, args.policy_id)
    print(format_score_report(report))


def simulate_signature(args):
    """Simulate changing the signature validity."""
    capsule = load_capsule_from_file(args.file, args.id)
    report = CQSSSimulator.simulate_signature_change(capsule, args.valid)
    print(format_score_report(report))


def optimize_capsule(args):
    """Optimize a capsule to reach a target score."""
    capsule = load_capsule_from_file(args.file, args.id)

    # Parse fixed attributes
    fixed = []
    if args.fixed:
        fixed = args.fixed.split(",")

    report, optimized = CQSSSimulator.optimize_capsule(capsule, args.target, fixed)

    # Print optimization report
    print("\n=== Capsule Optimization Report ===\n")
    print(f"Original Score: {report['original_score']:.1f}")
    print(f"Optimized Score: {report['optimized_score']:.1f}")
    print(f"Target Score: {report['target_score']:.1f}")
    print(f"Target Achieved: {'Yes' if report['target_achieved'] else 'No'}")

    print("\nChanges Made:")
    if report["changes_made"]:
        for change in report["changes_made"]:
            print(f"- {change}")
    else:
        print("- No changes were necessary")

    # Print optimized capsule
    if args.output:
        with open(args.output, "w") as f:
            json.dump(optimized.to_dict(), f, indent=2)
        print(f"\nOptimized capsule saved to {args.output}")


def main():
    parser = argparse.ArgumentParser(
        description="CQSS Simulator - Predict how changes affect capsule quality scores"
    )
    subparsers = parser.add_subparsers(dest="command", help="Simulation command")

    # Common arguments for all commands
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--file",
        "-f",
        default="capsule_chain.jsonl",
        help="Path to the JSONL file containing capsules",
    )
    parent_parser.add_argument(
        "--id", "-i", help="ID of the specific capsule to simulate"
    )

    # Confidence simulation
    confidence_parser = subparsers.add_parser(
        "confidence", parents=[parent_parser], help="Simulate changing confidence"
    )
    confidence_parser.add_argument(
        "--value",
        "-v",
        type=float,
        required=True,
        help="New confidence value (0.0-1.0)",
    )
    confidence_parser.set_defaults(func=simulate_confidence)

    # Reasoning trace simulation
    reasoning_parser = subparsers.add_parser(
        "reasoning", parents=[parent_parser], help="Simulate changing reasoning trace"
    )
    reasoning_group = reasoning_parser.add_mutually_exclusive_group(required=True)
    reasoning_group.add_argument(
        "--steps",
        "-s",
        nargs="+",
        help="New reasoning trace steps as a list of strings",
    )
    reasoning_group.add_argument(
        "--trace-file",
        "-t",
        help="File containing reasoning trace steps (one per line)",
    )
    reasoning_parser.set_defaults(func=simulate_reasoning)

    # Ethical policy simulation
    policy_parser = subparsers.add_parser(
        "policy", parents=[parent_parser], help="Simulate changing ethical policy"
    )
    policy_parser.add_argument(
        "--policy-id", "-p", required=True, help="New ethical policy ID"
    )
    policy_parser.set_defaults(func=simulate_policy)

    # Signature simulation
    signature_parser = subparsers.add_parser(
        "signature",
        parents=[parent_parser],
        help="Simulate changing signature validity",
    )
    signature_parser.add_argument(
        "--valid",
        "-v",
        action="store_true",
        help="Whether the signature should be considered valid",
    )
    signature_parser.set_defaults(func=simulate_signature)

    # Capsule optimization
    optimize_parser = subparsers.add_parser(
        "optimize",
        parents=[parent_parser],
        help="Optimize a capsule to reach a target score",
    )
    optimize_parser.add_argument(
        "--target", "-t", type=float, default=90.0, help="Target CQSS score to achieve"
    )
    optimize_parser.add_argument(
        "--fixed",
        "-x",
        help="Comma-separated list of attributes that should not be changed",
    )
    optimize_parser.add_argument(
        "--output", "-o", help="Output file for the optimized capsule"
    )
    optimize_parser.set_defaults(func=optimize_capsule)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
