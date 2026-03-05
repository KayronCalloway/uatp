"""
UATP 7.2 Edge-Native Capsules Module

Provides compact binary capsule format for edge devices:
- Compact capsule format (<1KB)
- CBOR encoding
- Offline signing
- Edge-cloud sync protocol
"""

from .compact_capsule import (
    CompactCapsule,
    CompactCapsuleEncoder,
    CompactCapsuleDecoder,
    CompactCapsuleFlags,
    COMPACT_CAPSULE_MAGIC,
    COMPACT_CAPSULE_VERSION,
    FIXED_OVERHEAD,
    estimate_capsule_size,
)
from .sync_protocol import (
    EdgeSyncService,
    SyncDirection,
    SyncStatus,
    SyncCheckpoint,
    SyncBatch,
    SyncResult,
    ConflictResolution,
    edge_sync_service,
)
from .offline_signer import (
    OfflineSigner,
    OfflineSignerRegistry,
    OfflineSignature,
    SignatureStatus,
    SigningResult,
    VerificationResult,
    offline_signer_registry,
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
