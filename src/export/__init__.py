"""
UATP Export - Sigstore-style DSSE bundle export.

This module provides portability for UATP capsules:
- DSSE envelopes for standardized signed payloads
- Bundles with verification material for offline verification
- PAE (Pre-Auth-Encoding) for secure signing

Usage:
    from src.export import (
        DSSEEnvelope,
        UATPBundle,
        create_capsule_envelope,
    )

    # Create envelope from capsule data
    envelope = create_capsule_envelope(capsule_dict)

    # Sign it
    def sign_func(data: bytes) -> bytes:
        # Your signing logic
        return signature_bytes

    envelope.sign(keyid="ed25519-abc", sign_func=sign_func)

    # Create bundle with verification material
    bundle = UATPBundle.create(
        envelope=envelope,
        public_key=public_key_bytes,
        key_id="ed25519-abc",
        timestamp_token=rfc3161_token,
    )

    # Export to JSON
    bundle_json = bundle.to_json()

    # Verify bundle
    result = bundle.verify()
    print(f"Valid: {result.is_valid}")
"""

# PAE encoding
# Bundle
from src.export.bundle import (
    BUNDLE_MEDIA_TYPE,
    TimestampEvidence,
    UATPBundle,
    VerificationMaterial,
    VerificationResult,
)

# DSSE envelope
from src.export.dsse import (
    PAYLOAD_TYPE_ATTESTATION,
    PAYLOAD_TYPE_CAPSULE,
    PAYLOAD_TYPE_WORKFLOW,
    DSSEEnvelope,
    DSSESignature,
    create_capsule_envelope,
    create_workflow_envelope,
)
from src.export.pae import (
    pae_decode,
    pae_encode,
    sign_pae,
    verify_pae,
)

__all__ = [
    # PAE
    "pae_encode",
    "pae_decode",
    "sign_pae",
    "verify_pae",
    # DSSE
    "DSSEEnvelope",
    "DSSESignature",
    "PAYLOAD_TYPE_CAPSULE",
    "PAYLOAD_TYPE_WORKFLOW",
    "PAYLOAD_TYPE_ATTESTATION",
    "create_capsule_envelope",
    "create_workflow_envelope",
    # Bundle
    "UATPBundle",
    "VerificationMaterial",
    "TimestampEvidence",
    "VerificationResult",
    "BUNDLE_MEDIA_TYPE",
]
