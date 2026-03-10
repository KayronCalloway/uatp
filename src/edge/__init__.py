"""
UATP 7.2 Edge-Native Capsules Module

Provides compact binary capsule format for edge devices:
- Compact capsule format (<1KB)
- CBOR encoding
- Offline signing
- Edge-cloud sync protocol
"""

from .compact_capsule import (
    COMPACT_CAPSULE_MAGIC,
    COMPACT_CAPSULE_VERSION,
    FIXED_OVERHEAD,
    CompactCapsule,
    CompactCapsuleDecoder,
    CompactCapsuleEncoder,
    CompactCapsuleFlags,
    estimate_capsule_size,
)
from .offline_signer import (
    OfflineSignature,
    OfflineSigner,
    OfflineSignerRegistry,
    SignatureStatus,
    SigningResult,
    VerificationResult,
    offline_signer_registry,
)
from .sync_protocol import (
    ConflictResolution,
    EdgeSyncService,
    SyncBatch,
    SyncCheckpoint,
    SyncDirection,
    SyncResult,
    SyncStatus,
    edge_sync_service,
)

__all__ = [
    # Compact Capsule
    "CompactCapsule",
    "CompactCapsuleEncoder",
    "CompactCapsuleDecoder",
    "CompactCapsuleFlags",
    "COMPACT_CAPSULE_MAGIC",
    "COMPACT_CAPSULE_VERSION",
    "FIXED_OVERHEAD",
    "estimate_capsule_size",
    # Sync Protocol
    "EdgeSyncService",
    "SyncDirection",
    "SyncStatus",
    "SyncCheckpoint",
    "SyncBatch",
    "SyncResult",
    "ConflictResolution",
    "edge_sync_service",
    # Offline Signer
    "OfflineSigner",
    "OfflineSignerRegistry",
    "OfflineSignature",
    "SignatureStatus",
    "SigningResult",
    "VerificationResult",
    "offline_signer_registry",
]
