#!/usr/bin/env python3
"""
UATP Quickstart Example

This is the simplest possible example of creating and verifying a capsule.
Run this after starting the backend: python run.py
"""

from uatp import UATP


def main():
    # Connect to local UATP server
    client = UATP(base_url="http://localhost:8000")

    # Create a capsule with reasoning chain
    print("Creating capsule...")
    result = client.certify(
        task="Recommend a restaurant",
        decision="Suggested 'The Golden Fork' for dinner",
        reasoning=[
            {
                "step": 1,
                "thought": "User requested Italian food near downtown",
                "confidence": 0.95,
            },
            {
                "step": 2,
                "thought": "Found 3 Italian restaurants within 1 mile",
                "confidence": 0.90,
            },
            {
                "step": 3,
                "thought": "The Golden Fork has highest ratings (4.8 stars)",
                "confidence": 0.88,
            },
        ],
    )

    print(f"✓ Capsule created: {result.capsule_id}")

    # Verify the capsule
    print("\nVerifying capsule...")
    proof = client.get_proof(result.capsule_id)

    if proof.verify():
        print("✓ Signature valid - capsule is authentic")
        print(f"  Signed at: {proof.timestamp}")
        print(f"  Algorithm: {proof.algorithm}")
    else:
        print("✗ Verification failed")

    # View the reasoning chain
    print("\nReasoning chain:")
    for step in result.reasoning:
        print(f"  Step {step['step']}: {step['thought']}")
        print(f"           Confidence: {step['confidence']:.0%}")


if __name__ == "__main__":
    main()
