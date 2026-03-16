#!/usr/bin/env python3
"""
Gold Standard Signing Example
==============================

This example demonstrates UATP's zero-trust architecture:
1. User generates keys LOCALLY (never transmitted)
2. User signs capsules LOCALLY (never transmitted)
3. Only HASH goes to UATP for timestamping
4. Timestamp comes from EXTERNAL TSA (DigiCert)
5. Anyone can verify without trusting UATP

Run this example:
    python examples/gold_standard_signing.py
"""

import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.crypto.local_signer import LocalSigner, verify_capsule_standalone
from src.crypto.user_key_manager import UserKeyManager


def main() -> None:
    print("=" * 60)
    print("UATP Gold Standard Signing Demo")
    print("=" * 60)
    print()

    # Use a temporary directory for this demo
    import tempfile

    key_dir = tempfile.mkdtemp(prefix="uatp_demo_")

    print(f"[1] Generating keys LOCALLY (in {key_dir})")
    print("    - Keys are generated on YOUR device")
    print("    - Private key NEVER leaves your device")
    print()

    # Create key manager and generate keys
    key_manager = UserKeyManager(key_dir=key_dir)

    passphrase = "demo-passphrase-change-in-production"
    key_pair = key_manager.generate_key_pair(passphrase=passphrase)

    print(f"    Key ID: {key_pair.key_id}")
    print(f"    Public Key: {key_pair.public_key_hex[:32]}...")
    print(f"    Created: {key_pair.created_at}")
    print()

    # Create and sign a capsule
    print("[2] Signing capsule LOCALLY")
    print("    - Signing happens entirely on YOUR device")
    print("    - Private key decrypted only for signing, then cleared")
    print()

    signer = LocalSigner(passphrase=passphrase, key_manager=key_manager)

    capsule_content = {
        "decision": "Approve loan application",
        "reasoning": [
            {"step": 1, "thought": "Credit score 750 (excellent)", "confidence": 0.95},
            {"step": 2, "thought": "Debt-to-income ratio 0.25", "confidence": 0.92},
            {"step": 3, "thought": "Employment verified, 5+ years", "confidence": 0.98},
        ],
        "model": "claude-sonnet-4",
        "final_confidence": 0.94,
    }

    signed_capsule = signer.sign_capsule(content=capsule_content)

    print(f"    Capsule ID: {signed_capsule.capsule_id}")
    print(f"    Content Hash: {signed_capsule.content_hash[:32]}...")
    print(f"    Signature: {signed_capsule.signature[:32]}...")
    print()

    # Show what UATP would see
    print("[3] What UATP sees (for timestamping)")
    print("    - ONLY the hash (32 bytes)")
    print("    - NO content, NO private key, NO signature")
    print()
    print(f"    Hash to timestamp: {signed_capsule.content_hash}")
    print()

    # Verify locally
    print("[4] Verifying capsule (can be done by ANYONE)")
    print("    - Uses only PUBLIC information")
    print("    - No trust in UATP required")
    print()

    is_valid = signer.verify_capsule(signed_capsule)
    print(f"    Signature Valid: {is_valid}")
    print()

    # Convert to verifiable format
    print("[5] Export to verifiable format")
    verifiable = signer.to_verifiable_capsule(signed_capsule)
    print(f"    Format: UATP v{verifiable['version']}")
    print(f"    Type: {verifiable['type']}")
    print(f"    Signer: {verifiable['verification']['signer']}")
    print()

    # Standalone verification (like a third party would do)
    print("[6] Standalone verification (no UATP infrastructure)")
    result = verify_capsule_standalone(verifiable)
    print(f"    Valid: {result['valid']}")
    print(f"    Signature Valid: {result['signature_valid']}")
    print()

    # Summary
    print("=" * 60)
    print("SUMMARY: Gold Standard Architecture")
    print("=" * 60)
    print()
    print("What happened:")
    print("  1. Keys generated LOCALLY - never transmitted")
    print("  2. Capsule signed LOCALLY - never transmitted")
    print("  3. Only HASH would go to UATP (for timestamping)")
    print("  4. Timestamp would come from EXTERNAL TSA")
    print("  5. Verification works WITHOUT trusting UATP")
    print()
    print("What UATP CANNOT do:")
    print("  - Forge your signature (don't have your key)")
    print("  - Read your content (only see hash)")
    print("  - Backdate capsules (external TSA)")
    print("  - Tamper with sealed capsules (breaks signature)")
    print()
    print("If the President calls UATP:")
    print('  "I literally cannot forge or tamper.')
    print("   Users hold their own keys.")
    print("   The math doesn't allow it.\"")
    print()

    # Cleanup
    import shutil

    shutil.rmtree(key_dir, ignore_errors=True)

    print("Demo complete. Temporary keys cleaned up.")


if __name__ == "__main__":
    main()
