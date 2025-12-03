"""
cli.py - Command-line interface for UATP Capsule Engine.
Provides commands for capsule creation, chain verification, CQSS analysis, and visualization.
"""

import argparse
import csv
import json
import subprocess
import sys

from engine.capsule_engine import CapsuleEngine
from engine.cqss import compute_cqss


def validate_capsule_type(capsule_type):
    """Validate capsule type is allowed and properly formatted."""
    # List of allowed capsule types
    allowed_types = [
        "Consent",
        "TrustRenewal",
        "Governance",
        "Economic",
        "SimulatedMalice",
        "CapsuleExpiration",
        "SelfHallucination",
        "ValueInception",
        "TemporalSignature",
        "Remix",
    ]

    if not capsule_type or not isinstance(capsule_type, str):
        raise ValueError("Capsule type must be a non-empty string")

    if capsule_type not in allowed_types:
        raise ValueError(
            f"Invalid capsule type. Must be one of: {', '.join(allowed_types)}"
        )

    return capsule_type


def validate_confidence(confidence):
    """Validate confidence is a float between 0 and 1."""
    try:
        confidence_float = float(confidence)
        if not (0 <= confidence_float <= 1):
            raise ValueError("Confidence must be between 0 and 1")
        return confidence_float
    except (TypeError, ValueError):
        raise ValueError("Confidence must be a float between 0 and 1")


def validate_reasoning_trace(reasoning_trace):
    """Validate reasoning trace is properly formatted."""
    if not reasoning_trace:
        raise ValueError("Reasoning trace cannot be empty")

    # Split by comma and validate each step
    steps = reasoning_trace.split(",")
    if not steps:
        raise ValueError("At least one reasoning step is required")

    # Validate step length
    for step in steps:
        if not step.strip():
            raise ValueError("Reasoning steps cannot be empty")
        if len(step) > 1000:  # Reasonable maximum length
            raise ValueError(
                f"Reasoning step too long: {step[:50]}... (max 1000 chars)"
            )

    return steps


def validate_metadata(metadata_str):
    """Validate metadata is valid JSON and not too large."""
    if not metadata_str:
        return {}

    try:
        metadata = json.loads(metadata_str)

        # Validate metadata is a dict
        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a JSON object")

        # Check metadata size (1MB limit)
        metadata_size = len(json.dumps(metadata))
        if metadata_size > 1024 * 1024:  # 1MB
            raise ValueError("Metadata exceeds maximum size of 1MB")

        return metadata
    except json.JSONDecodeError:
        raise ValueError("Metadata must be valid JSON")


def create_capsule(args):
    try:
        # Validate input parameters
        capsule_type = validate_capsule_type(args.type)
        confidence = validate_confidence(args.confidence)
        reasoning_trace = validate_reasoning_trace(args.reasoning_trace)
        metadata = validate_metadata(args.metadata)

        # Create capsule with validated parameters
        engine = CapsuleEngine()
        capsule = engine.create_capsule(
            capsule_type=capsule_type,
            confidence=confidence,
            reasoning_trace=reasoning_trace,
            metadata=metadata,
        )
        engine.log_capsule(capsule)
        print(f"Capsule created and logged: {capsule.capsule_id}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def verify_chain(args):
    engine = CapsuleEngine()
    chain = list(engine.load_chain())
    if not chain:
        print("Chain is empty. Nothing to verify.")
        return
    all_valid = all(engine.verify_capsule(c) for c in chain)
    print(
        f"Chain verification: {'VALID' if all_valid else 'INVALID'} ({len(chain)} capsules)"
    )


def compute_cqss_cmd(args):
    engine = CapsuleEngine()
    chain = list(engine.load_chain())
    if not chain:
        print("Chain is empty. No metrics to compute.")
        return
    result = compute_cqss(chain, engine.verify_capsule)
    print("CQSS Metrics:")
    for k, v in result.as_dict().items():
        print(f"  {k}: {v}")


def export_chain(args):
    engine = CapsuleEngine()
    chain = list(engine.load_chain())
    if not chain:
        print("No capsules found in chain.")
        return
    try:
        if args.format == "json":
            with open(args.output, "w") as f:
                json.dump([c.to_dict() for c in chain], f, indent=2)
            print(f"Exported chain to {args.output} (JSON)")
        elif args.format == "csv":
            with open(args.output, "w", newline="") as f:
                all_keys = set()
                for c in chain:
                    all_keys.update(c.to_dict().keys())

                writer = csv.DictWriter(f, fieldnames=sorted(list(all_keys)))
                writer.writeheader()
                for c in chain:
                    writer.writerow(c.to_dict())
            print(f"Exported chain to {args.output} (CSV)")
        else:
            print("Unknown export format. Use 'json' or 'csv'.")
    except Exception as e:
        print(f"Export failed: {e}")


def visualize(args):
    # Fix command injection vulnerability by using subprocess.run with explicit arguments
    subprocess.run(["streamlit", "run", "visualizer/app.py"], check=True)


def main():
    parser = argparse.ArgumentParser(description="UATP Capsule Engine CLI")
    subparsers = parser.add_subparsers(dest="command", help="sub-command help")

    # create-capsule
    p_create = subparsers.add_parser(
        "create-capsule", help="Create and log a new capsule"
    )
    p_create.add_argument(
        "--type",
        required=True,
        help="Capsule type (e.g. Introspective, Refusal, Joint)",
    )
    p_create.add_argument(
        "--confidence", type=float, required=True, help="Confidence value"
    )
    p_create.add_argument(
        "--reasoning-trace", required=True, help="Comma-separated reasoning trace steps"
    )
    p_create.add_argument("--metadata", help="JSON string for metadata")
    p_create.set_defaults(func=create_capsule)

    # verify-chain
    p_verify = subparsers.add_parser(
        "verify-chain", help="Verify all capsule signatures in the chain"
    )
    p_verify.set_defaults(func=verify_chain)

    # compute-cqss
    p_cqss = subparsers.add_parser(
        "compute-cqss", help="Compute CQSS metrics for the chain"
    )
    p_cqss.set_defaults(func=compute_cqss_cmd)

    # export
    p_export = subparsers.add_parser("export", help="Export chain to JSON or CSV")
    p_export.add_argument(
        "--format", choices=["json", "csv"], required=True, help="Export format"
    )
    p_export.add_argument("--output", required=True, help="Output file path")
    p_export.set_defaults(func=export_chain)

    # visualize
    p_vis = subparsers.add_parser("visualize", help="Launch the Streamlit visualizer")
    p_vis.set_defaults(func=visualize)

    args = parser.parse_args()
    if hasattr(args, "func"):
        try:
            args.func(args)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
