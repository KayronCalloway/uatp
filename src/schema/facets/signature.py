"""
Signature Facet - Cryptographic signature metadata.

Captures:
- Algorithm used (Ed25519, ML-DSA-65)
- Signature value
- Signing timestamp
- RFC 3161 timestamp token (if available)
- Public key for verification
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.schema.base import RunFacet, utc_now


@dataclass
class UATPSignatureRunFacet(RunFacet):
    """
    Cryptographic signature attached to a capsule run.

    This is the primary trust anchor - proves WHO signed WHAT and WHEN.
    """

    # Core signature data
    algorithm: str = "ed25519"  # ed25519, ml-dsa-65, ed25519+ml-dsa-65
    signature: str = ""  # Hex or base64 encoded signature
    signed_at: datetime = field(default_factory=utc_now)

    # Key identification
    key_id: Optional[str] = None  # Key identifier for lookup
    public_key: Optional[str] = (
        None  # Base64 public key (for self-contained verification)
    )
    signer_identity: Optional[str] = None  # URI or name of signer

    # Content hash (what was signed)
    content_hash: str = ""  # SHA-256 of signed content
    hash_algorithm: str = "sha256"

    # RFC 3161 timestamp (external trust anchor)
    timestamp_token: Optional[str] = None  # Base64 RFC 3161 token
    timestamp_authority: Optional[str] = None  # TSA URL

    # Post-quantum signature (if hybrid)
    pq_algorithm: Optional[str] = None  # ml-dsa-65
    pq_signature: Optional[str] = None  # Post-quantum signature

    def is_hybrid(self) -> bool:
        """Check if this is a hybrid classical+PQ signature."""
        return self.pq_signature is not None

    def has_trusted_timestamp(self) -> bool:
        """Check if RFC 3161 timestamp is present."""
        return self.timestamp_token is not None
