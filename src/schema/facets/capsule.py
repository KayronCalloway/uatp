"""
Capsule Facet - Core capsule metadata.

Describes the capsule itself:
- Type
- Status
- Content hash
- Compression info
- Encryption info
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.schema.base import DatasetFacet, utc_now


@dataclass
class UATPCapsuleDatasetFacet(DatasetFacet):
    """
    Core metadata about a capsule (as output dataset).

    This facet describes WHAT the capsule contains.
    """

    # Identity
    capsule_id: str = ""
    capsule_type: str = "reasoning_trace"  # reasoning_trace, agent_execution, etc.
    version: str = "7.2"

    # Status
    status: str = "sealed"  # draft, sealed, verified, archived
    created_at: datetime = field(default_factory=utc_now)

    # Content integrity
    content_hash: str = ""  # SHA-256 of payload
    hash_algorithm: str = "sha256"

    # Chaining
    prev_hash: Optional[str] = None  # Hash of previous capsule
    chain_position: Optional[int] = None  # Position in chain

    # Compression
    is_compressed: bool = False
    compression_method: Optional[str] = None  # zlib, lzma
    original_size: Optional[int] = None
    compressed_size: Optional[int] = None

    # Encryption
    is_encrypted: bool = False
    encryption_method: Optional[str] = None  # AES-256-GCM
    key_id: Optional[str] = None  # Key used for encryption

    # PII handling
    pii_redacted: bool = False
    pii_types_found: list = field(default_factory=list)
    pii_count: int = 0

    def compression_ratio(self) -> Optional[float]:
        """Calculate compression ratio if compressed."""
        if self.is_compressed and self.original_size and self.compressed_size:
            return self.compressed_size / self.original_size
        return None
