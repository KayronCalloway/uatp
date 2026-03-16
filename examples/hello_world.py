#!/usr/bin/env python3
"""
UATP Hello World

Proof in 10 lines. No server needed.
"""

from uatp import UATP

# Create and sign a capsule (keys generated locally, never transmitted)
client = UATP()

result = client.certify(
    task="Hello World",
    decision="Successfully created first cryptographic audit trail",
    reasoning=[
        {"step": 1, "thought": "UATP installed correctly", "confidence": 1.0},
        {"step": 2, "thought": "Ed25519 key pair generated", "confidence": 1.0},
        {"step": 3, "thought": "Capsule signed locally", "confidence": 1.0},
    ],
)

print(f"""
Capsule created and signed.

  ID:        {result.capsule_id}
  Signature: {result.signature[:32]}...
  Public Key: {result.public_key[:32]}...

Your private key never left your device.
Verify anytime with: uatp verify {result.capsule_id}
""")
