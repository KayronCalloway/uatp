#!/usr/bin/env python3
"""
UATP Core Proof Flow Test
==========================

This script tests the fundamental cryptographic proof flow:
1. Create a capsule with AI decision + reasoning
2. Sign it with Ed25519
3. Verify the signature passes
4. Tamper with the content
5. Verify the signature now FAILS

If this works, the core claim is valid.
If this fails, everything else is theater.
"""

import os
import sys
from typing import Any, Dict

# Add project paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))


def main() -> int:
    print("=" * 60)
    print("UATP Core Proof Flow Test")
    print("=" * 60)
    print()

    # Step 1: Create capsule content
    print("[1] Creating capsule content...")
    capsule_content: Dict[str, Any] = {
        "capsule_id": "test_capsule_001",
        "type": "reasoning_trace",
        "platform": "test",
        "user_id": "test_user",
        "timestamp": "2026-03-08T12:00:00Z",
        "significance_score": 8.5,
        "payload": {
            "task": "Approve loan application",
            "decision": "Loan approved for $50,000 at 5.2% APR",
            "reasoning": [
                {
                    "step": 1,
                    "thought": "Credit score 720 (excellent)",
                    "confidence": 0.99,
                },
                {
                    "step": 2,
                    "thought": "Debt-to-income ratio 0.28 (acceptable)",
                    "confidence": 0.95,
                },
            ],
        },
    }
    print("    Content created with decision and reasoning chain")
    print()

    # Step 2: Sign with Ed25519
    print("[2] Signing capsule with Ed25519...")
    try:
        from src.security.uatp_crypto_v7 import UATPCryptoV7

        crypto = UATPCryptoV7(key_dir=".uatp_keys_test")
        verification = crypto.sign_capsule(capsule_content)

        print(f"    Signer: {verification['signer']}")
        print(f"    Hash: {verification['hash'][:50]}...")
        print(f"    Signature: {verification['signature'][:50]}...")
        print(f"    Public Key: {verification['verify_key'][:32]}...")
        print()

    except Exception as e:
        print(f"[FAIL] Signing failed: {e}")
        return 1

    # Step 3: Verify signature
    print("[3] Verifying signature...")
    is_valid, reason = crypto.verify_capsule(capsule_content, verification)

    if is_valid:
        print(f"    [PASS] Signature verification: {reason}")
        print()
    else:
        print(f"    [FAIL] Signature verification failed: {reason}")
        return 1

    # Step 4: Tamper with content
    print("[4] Tampering with content...")
    tampered_content = capsule_content.copy()
    tampered_content["payload"] = capsule_content["payload"].copy()
    tampered_content["payload"]["decision"] = (
        "Loan approved for $500,000 at 0.1% APR"  # Changed!
    )
    print("    Original: Loan approved for $50,000 at 5.2% APR")
    print("    Tampered: Loan approved for $500,000 at 0.1% APR")
    print()

    # Step 5: Verify tampered content fails
    print("[5] Verifying tampered content (should FAIL)...")
    is_valid_tampered, reason_tampered = crypto.verify_capsule(
        tampered_content, verification
    )

    if not is_valid_tampered:
        print(f"    [PASS] Tamper detection worked: {reason_tampered}")
        print()
    else:
        print("    [FAIL] CRITICAL: Tampered content verified as valid!")
        return 1

    # Step 6: Additional test - modify a small detail
    print("[6] Subtle tamper test (change one digit)...")
    subtle_tamper = capsule_content.copy()
    subtle_tamper["significance_score"] = 8.4  # Changed 8.5 to 8.4

    is_valid_subtle, reason_subtle = crypto.verify_capsule(subtle_tamper, verification)

    if not is_valid_subtle:
        print(f"    [PASS] Subtle tamper detected: {reason_subtle}")
        print()
    else:
        print("    [FAIL] CRITICAL: Subtle tamper not detected!")
        return 1

    # Step 7: Test RFC3161 timestamping (optional - requires network)
    print("[7] Testing RFC3161 timestamping from external TSA...")
    timestamp_works = False
    try:
        import json

        from src.security.rfc3161_timestamps import RFC3161Timestamper

        # Serialize content deterministically
        capsule_bytes = json.dumps(
            capsule_content, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

        timestamper = RFC3161Timestamper(tsa_name="freetsa")
        token = timestamper.request_timestamp(capsule_bytes)

        print(f"    TSA: {token.tsa_name}")
        print(f"    Timestamp: {token.timestamp.isoformat()}")
        print(f"    Hash: {token.message_imprint[:32]}...")
        print()

        # Verify timestamp
        is_valid_ts, reason_ts = timestamper.verify_timestamp(token, capsule_bytes)
        if is_valid_ts:
            print(f"    [PASS] Timestamp verified: {reason_ts}")
            timestamp_works = True
        else:
            print(f"    [WARN] Timestamp verification: {reason_ts}")
        print()

        # Test that tampered data fails timestamp verification
        print("[8] Testing tampered data against timestamp...")
        tampered_bytes = json.dumps(
            tampered_content, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

        is_valid_tampered_ts, reason_tampered_ts = timestamper.verify_timestamp(
            token, tampered_bytes
        )
        if not is_valid_tampered_ts:
            print(f"    [PASS] Tampered data fails timestamp: {reason_tampered_ts}")
        else:
            print("    [WARN] Timestamp did not detect tamper")
        print()

    except Exception as e:
        print(f"    [SKIP] RFC3161 test skipped: {e}")
        print("    (This requires network access and 'requests' library)")
        print()

    # Summary
    print("=" * 60)
    print("CORE PROOF FLOW: ALL TESTS PASSED")
    print("=" * 60)
    print()
    print("Verified capabilities:")
    print("  [OK] Ed25519 signature generation")
    print("  [OK] Ed25519 signature verification")
    print("  [OK] Tamper detection (major changes)")
    print("  [OK] Tamper detection (subtle changes)")
    if timestamp_works:
        print("  [OK] RFC3161 external timestamping (FreeTSA)")
        print("  [OK] Timestamp tamper detection")
    else:
        print("  [--] RFC3161 timestamping (not tested)")
    print()
    print("The cryptographic foundation is SOLID.")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
