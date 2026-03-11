#!/usr/bin/env python3
"""
Local Signing Example

Demonstrates the zero-trust model: signing happens entirely on your device.
Private keys are never transmitted to any server.
"""

from uatp.signer import LocalSigner


def main():
    # Initialize local signer (generates or loads keys from ~/.uatp/keys/)
    print("Initializing local signer...")
    signer = LocalSigner()

    print(f"✓ Using key: {signer.key_id}")
    print(f"  Key location: {signer.key_path}")
    print(f"  Public key: {signer.public_key[:32]}...")
    print()

    # Create capsule content
    capsule_content = {
        "task": "Code review decision",
        "decision": "Approved PR #142 with minor suggestions",
        "reasoning": [
            {
                "step": 1,
                "thought": "No security vulnerabilities detected",
                "confidence": 0.94,
            },
            {"step": 2, "thought": "Code follows style guidelines", "confidence": 0.91},
            {"step": 3, "thought": "Test coverage adequate (87%)", "confidence": 0.89},
        ],
        "metadata": {
            "repository": "company/backend",
            "pr_number": 142,
            "reviewer": "ai-assistant",
        },
    }

    # Sign locally - private key NEVER leaves this device
    print("Signing capsule locally...")
    signed_capsule = signer.sign(capsule_content)

    print("✓ Capsule signed")
    print(f"  Capsule ID: {signed_capsule.capsule_id}")
    print(f"  Signature: {signed_capsule.signature[:32]}...")
    print(f"  Timestamp: {signed_capsule.timestamp}")
    print()

    # Verify our own signature
    print("Verifying signature...")
    if signer.verify(signed_capsule):
        print("✓ Self-verification passed")
    else:
        print("✗ Self-verification failed (this shouldn't happen)")
    print()

    # Export for storage or transmission
    print("Exporting capsule...")
    exported = signed_capsule.to_json()
    print(f"  Size: {len(exported)} bytes")
    print()

    print("What just happened:")
    print("  1. Private key stayed on your device")
    print("  2. Signing happened locally (no network)")
    print("  3. Anyone can verify using only the public key")
    print("  4. UATP servers never saw your private key")


if __name__ == "__main__":
    main()
