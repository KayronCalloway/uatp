#!/usr/bin/env python3
"""
Standalone Verification Example

Demonstrates verifying a capsule without connecting to any server.
This is the "zero-trust" verification - you don't need to trust UATP.
"""

import json

from uatp.verifier import verify_capsule


def main():
    # Example capsule (in production, you'd load this from a file or API)
    capsule = {
        "capsule_id": "cap_example_123",
        "version": "7.2",
        "task": "Loan approval decision",
        "decision": "Approved for $25,000 at 6.5% APR",
        "reasoning": [
            {"step": 1, "thought": "Credit score 710 (good)", "confidence": 0.92},
            {
                "step": 2,
                "thought": "Debt-to-income 0.31 (acceptable)",
                "confidence": 0.88,
            },
            {"step": 3, "thought": "Employment verified (3 years)", "confidence": 0.95},
        ],
        "timestamp": "2026-03-10T15:30:00Z",
        "signature": {
            "algorithm": "Ed25519",
            "public_key": "MCowBQYDK2VwAyEA...",  # Truncated for example
            "value": "base64_signature_here...",
        },
    }

    print("Capsule to verify:")
    print(json.dumps(capsule, indent=2))
    print()

    # Verify without any network connection
    # This checks:
    # 1. Signature matches content (tamper detection)
    # 2. Public key is valid
    # 3. Timestamp is properly formatted
    result = verify_capsule(capsule)

    if result.valid:
        print("✓ Capsule is cryptographically valid")
        print(f"  Signer: {result.signer_id}")
        print(f"  Signed: {result.timestamp}")
        print()
        print("This means:")
        print("  - Content has not been modified since signing")
        print("  - The signature was made with the corresponding private key")
        print("  - You verified this yourself, without trusting any server")
    else:
        print(f"✗ Verification failed: {result.error}")
        print()
        print("Possible reasons:")
        print("  - Capsule was tampered with after signing")
        print("  - Signature is invalid or corrupted")
        print("  - Public key doesn't match the signature")


if __name__ == "__main__":
    main()
