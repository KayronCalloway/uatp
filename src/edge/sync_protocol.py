"""
Edge-Cloud Sync Protocol for UATP 7.2 Edge-Native Capsules

Provides synchronization between edge devices and cloud infrastructure:
- Offline capsule queue management
- Batch sync with conflict resolution
- Incremental sync with checkpoints
- Bandwidth-efficient delta sync
- Device authentication and authorization
"""

import hashlib
import hmac
import logging
import secrets
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .compact_capsule import (
    CompactCapsule,
    CompactCapsuleDecoder,
    CompactCapsuleEncoder,
    CompactCapsuleFlags,
)

logger = logging.getLogger(__name__)


class SyncDirection(str, Enum):
    """Direction of sync operation."""

    EDGE_TO_CLOUD = "edge_to_cloud"
    CLOUD_TO_EDGE = "cloud_to_edge"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(str, Enum):
    """Status of sync operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CONFLICT = "conflict"


class ConflictResolution(str, Enum):
    """Conflict resolution strategy."""

    CLOUD_WINS = "cloud_wins"
    EDGE_WINS = "edge_wins"
    NEWEST_WINS = "newest_wins"
    MANUAL = "manual"


class DeviceStatus(str, Enum):
    """Device registration status."""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass
class RegisteredDevice:
    """Registered edge device with authentication credentials."""

    device_id: str
    device_secret_hash: str  # Hashed device secret for verification
    owner_id: str
    device_name: Optional[str] = None
    status: DeviceStatus = DeviceStatus.ACTIVE
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excludes secret hash)."""
        return {
            "device_id": self.device_id,
            "owner_id": self.owner_id,
            "device_name": self.device_name,
            "status": self.status.value,
            "registered_at": self.registered_at.isoformat(),
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "metadata": self.metadata,
        }


class SyncStateStore(ABC):
    """Abstract interface for sync state storage."""

    @abstractmethod
    def get_device(self, device_id: str) -> Optional[RegisteredDevice]:
        """Get registered device by ID."""
        pass

    @abstractmethod
    def register_device(self, device: RegisteredDevice) -> None:
        """Register a new device."""
        pass

    @abstractmethod
    def update_device_last_seen(self, device_id: str) -> None:
        """Update device last seen timestamp."""
        pass

    @abstractmethod
    def get_checkpoint(self, device_id: str) -> Optional["SyncCheckpoint"]:
        """Get checkpoint for device."""
        pass

    @abstractmethod
    def save_checkpoint(self, checkpoint: "SyncCheckpoint") -> None:
        """Save checkpoint for device."""
        pass

    @abstractmethod
    def queue_capsule(self, device_id: str, capsule_data: bytes) -> None:
        """Add capsule to device sync queue."""
        pass

    @abstractmethod
    def get_pending_capsules(self, device_id: str, limit: int = 100) -> List[bytes]:
        """Get pending capsules for device."""
        pass

    @abstractmethod
    def remove_synced_capsules(self, device_id: str, count: int) -> None:
        """Remove successfully synced capsules from queue."""
        pass


class InMemorySyncStateStore(SyncStateStore):
    """In-memory sync state store for development/testing."""

    def __init__(self):
        self._devices: Dict[str, RegisteredDevice] = {}
        self._checkpoints: Dict[str, "SyncCheckpoint"] = {}
        self._queues: Dict[str, List[bytes]] = {}
        logger.warning(
            "Using in-memory sync state store - data will be lost on restart. "
            "Use RedisSyncStateStore or DatabaseSyncStateStore in production."
        )

    def get_device(self, device_id: str) -> Optional[RegisteredDevice]:
        return self._devices.get(device_id)

    def register_device(self, device: RegisteredDevice) -> None:
        self._devices[device.device_id] = device

    def update_device_last_seen(self, device_id: str) -> None:
        if device_id in self._devices:
            self._devices[device_id].last_seen_at = datetime.now(timezone.utc)

    def get_checkpoint(self, device_id: str) -> Optional["SyncCheckpoint"]:
        return self._checkpoints.get(device_id)

    def save_checkpoint(self, checkpoint: "SyncCheckpoint") -> None:
        self._checkpoints[checkpoint.device_id] = checkpoint

    def queue_capsule(self, device_id: str, capsule_data: bytes) -> None:
        if device_id not in self._queues:
            self._queues[device_id] = []
        self._queues[device_id].append(capsule_data)

    def get_pending_capsules(self, device_id: str, limit: int = 100) -> List[bytes]:
        return self._queues.get(device_id, [])[:limit]

    def remove_synced_capsules(self, device_id: str, count: int) -> None:
        if device_id in self._queues:
            self._queues[device_id] = self._queues[device_id][count:]


@dataclass
class SyncCheckpoint:
    """Checkpoint for incremental sync."""

    checkpoint_id: str
    device_id: str
    last_sync_timestamp: int  # Unix ms
    last_capsule_id: Optional[str]
    sync_sequence: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "device_id": self.device_id,
            "last_sync_timestamp": self.last_sync_timestamp,
            "last_capsule_id": self.last_capsule_id,
            "sync_sequence": self.sync_sequence,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class SyncBatch:
    """Batch of capsules for sync."""

    batch_id: str
    device_id: str
    direction: SyncDirection
    capsules: List[bytes]  # Encoded compact capsules
    checkpoint: Optional[SyncCheckpoint]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def size_bytes(self) -> int:
        """Total size of batch in bytes."""
        return sum(len(c) for c in self.capsules)

    @property
    def count(self) -> int:
        """Number of capsules in batch."""
        return len(self.capsules)


@dataclass
class SyncResult:
    """Result of sync operation."""

    batch_id: str
    status: SyncStatus
    synced_count: int
    failed_count: int
    conflict_count: int
    checkpoint: Optional[SyncCheckpoint]
    errors: List[str] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "batch_id": self.batch_id,
            "status": self.status.value,
            "synced_count": self.synced_count,
            "failed_count": self.failed_count,
            "conflict_count": self.conflict_count,
            "checkpoint": self.checkpoint.to_dict() if self.checkpoint else None,
            "errors": self.errors,
            "conflicts": self.conflicts,
            "duration_ms": self.duration_ms,
        }


class EdgeSyncService:
    """
    Service for syncing capsules between edge devices and cloud.

    Features:
    - Offline queue management
    - Batch sync with configurable batch sizes
    - Checkpoint-based incremental sync
    - Conflict detection and resolution
    - Device authentication and authorization
    """

    def __init__(
        self,
        max_batch_size: int = 100,
        max_batch_bytes: int = 100 * 1024,  # 100KB default
        conflict_resolution: ConflictResolution = ConflictResolution.NEWEST_WINS,
        state_store: Optional[SyncStateStore] = None,
    ):
        """
        Initialize the sync service.

        Args:
            max_batch_size: Maximum capsules per batch
            max_batch_bytes: Maximum batch size in bytes
            conflict_resolution: Default conflict resolution strategy
            state_store: Persistent state storage backend
        """
        self.max_batch_size = max_batch_size
        self.max_batch_bytes = max_batch_bytes
        self.conflict_resolution = conflict_resolution
        self._state_store = state_store or InMemorySyncStateStore()

        # Legacy in-memory stores (deprecated - use state_store)
        self._pending_queue: Dict[str, List[bytes]] = {}  # device_id -> capsules
        self._checkpoints: Dict[str, SyncCheckpoint] = {}  # device_id -> checkpoint
        self._sync_history: List[SyncResult] = []

        self._encoder = CompactCapsuleEncoder()
        self._decoder = CompactCapsuleDecoder()

    def register_device(
        self,
        device_id: str,
        owner_id: str,
        device_name: Optional[str] = None,
    ) -> Tuple[RegisteredDevice, str]:
        """
        Register a new edge device for sync.

        Args:
            device_id: Unique device identifier
            owner_id: Owner user ID
            device_name: Optional human-readable device name

        Returns:
            Tuple of (RegisteredDevice, device_secret)
            The device_secret must be stored securely on the device.
        """
        # Generate a secure device secret
        device_secret = secrets.token_hex(32)
        secret_hash = hashlib.sha256(device_secret.encode()).hexdigest()

        device = RegisteredDevice(
            device_id=device_id,
            device_secret_hash=secret_hash,
            owner_id=owner_id,
            device_name=device_name,
            status=DeviceStatus.ACTIVE,
        )

        self._state_store.register_device(device)
        logger.info(f"Registered device {device_id} for owner {owner_id}")

        return device, device_secret

    def authenticate_device(
        self,
        device_id: str,
        device_secret: str,
    ) -> Optional[RegisteredDevice]:
        """
        Authenticate a device using its secret.

        Args:
            device_id: Device identifier
            device_secret: Device secret to verify

        Returns:
            RegisteredDevice if authenticated, None otherwise
        """
        device = self._state_store.get_device(device_id)
        if not device:
            logger.warning(f"Authentication failed: device {device_id} not found")
            return None

        # Verify device is active
        if device.status != DeviceStatus.ACTIVE:
            logger.warning(f"Authentication failed: device {device_id} is {device.status}")
            return None

        # Verify secret using constant-time comparison
        secret_hash = hashlib.sha256(device_secret.encode()).hexdigest()
        if not hmac.compare_digest(secret_hash, device.device_secret_hash):
            logger.warning(f"Authentication failed: invalid secret for device {device_id}")
            return None

        # Update last seen
        self._state_store.update_device_last_seen(device_id)

        return device

    def verify_device_ownership(
        self,
        device_id: str,
        owner_id: str,
    ) -> bool:
        """
        Verify that a device belongs to the specified owner.

        Args:
            device_id: Device identifier
            owner_id: Expected owner ID

        Returns:
            True if device belongs to owner
        """
        device = self._state_store.get_device(device_id)
        if not device:
            return False
        return device.owner_id == owner_id

    def queue_capsule(
        self,
        device_id: str,
        capsule_data: bytes,
        device_secret: Optional[str] = None,
        skip_auth: bool = False,
    ) -> bool:
        """
        Add a capsule to the sync queue for a device.

        Args:
            device_id: Device identifier
            capsule_data: Encoded compact capsule
            device_secret: Device secret for authentication (required unless skip_auth)
            skip_auth: Skip authentication (for internal use only)

        Returns:
            True if queued successfully
        """
        # SECURITY: Require authentication unless explicitly skipped (for testing)
        if not skip_auth:
            if not device_secret:
                logger.warning(f"Queue rejected: no device secret provided for {device_id}")
                return False

            device = self.authenticate_device(device_id, device_secret)
            if not device:
                logger.warning(f"Queue rejected: authentication failed for {device_id}")
                return False

        # Use state store if available, fall back to in-memory
        try:
            self._state_store.queue_capsule(device_id, capsule_data)
        except Exception:
            # Fallback to legacy in-memory queue
            if device_id not in self._pending_queue:
                self._pending_queue[device_id] = []
            self._pending_queue[device_id].append(capsule_data)

        logger.debug(f"Queued capsule for device {device_id}")
        return True

    def get_pending_count(self, device_id: str) -> int:
        """Get number of pending capsules for a device."""
        # Try state store first, fall back to in-memory
        try:
            capsules = self._state_store.get_pending_capsules(device_id, limit=10000)
            return len(capsules)
        except Exception:
            return len(self._pending_queue.get(device_id, []))

    def get_pending_capsules(self, device_id: str) -> List[bytes]:
        """Get pending capsules for a device without removing them."""
        try:
            return self._state_store.get_pending_capsules(device_id)
        except Exception:
            return self._pending_queue.get(device_id, []).copy()

    def create_sync_batch(
        self,
        device_id: str,
        direction: SyncDirection = SyncDirection.EDGE_TO_CLOUD,
        max_capsules: Optional[int] = None,
    ) -> Optional[SyncBatch]:
        """
        Create a batch of capsules for sync.

        Args:
            device_id: Device identifier
            direction: Sync direction
            max_capsules: Override max batch size

        Returns:
            SyncBatch or None if no capsules pending
        """
        # Get pending capsules from state store
        pending = self.get_pending_capsules(device_id)
        if not pending:
            return None

        max_count = min(max_capsules or self.max_batch_size, len(pending))
        batch_capsules = []
        batch_size = 0

        for capsule in pending[:max_count]:
            if batch_size + len(capsule) > self.max_batch_bytes:
                break
            batch_capsules.append(capsule)
            batch_size += len(capsule)

        if not batch_capsules:
            return None

        batch_id = self._generate_batch_id(device_id, batch_capsules)

        # Get checkpoint from state store
        try:
            checkpoint = self._state_store.get_checkpoint(device_id)
        except Exception:
            checkpoint = self._checkpoints.get(device_id)

        return SyncBatch(
            batch_id=batch_id,
            device_id=device_id,
            direction=direction,
            capsules=batch_capsules,
            checkpoint=checkpoint,
        )

    def process_sync_batch(
        self,
        batch: SyncBatch,
        cloud_capsule_ids: Optional[List[str]] = None,
    ) -> SyncResult:
        """
        Process a sync batch (simulated cloud sync).

        Args:
            batch: Batch to sync
            cloud_capsule_ids: Existing capsule IDs in cloud (for conflict detection)

        Returns:
            SyncResult with sync status
        """
        start_time = time.time()
        synced = 0
        failed = 0
        conflicts = []
        errors = []

        cloud_ids = set(cloud_capsule_ids or [])

        for capsule_data in batch.capsules:
            try:
                # Decode to validate and extract ID
                capsule = self._decoder.decode(capsule_data)
                capsule_id = capsule.capsule_id_hex

                # Check for conflict
                if capsule_id in cloud_ids:
                    conflict = self._handle_conflict(capsule, capsule_id)
                    if conflict:
                        conflicts.append(conflict)
                    else:
                        synced += 1
                else:
                    # No conflict, would upload to cloud
                    synced += 1

            except Exception as e:
                failed += 1
                errors.append(str(e))
                logger.error(f"Failed to process capsule: {e}")

        # Update checkpoint
        new_checkpoint = self._create_checkpoint(batch.device_id, batch)

        # Remove synced capsules from queue
        if synced > 0:
            try:
                self._state_store.remove_synced_capsules(batch.device_id, synced)
            except Exception:
                # Fallback to in-memory queue
                pending = self._pending_queue.get(batch.device_id, [])
                self._pending_queue[batch.device_id] = pending[synced:]

        duration_ms = int((time.time() - start_time) * 1000)

        # Determine status
        if failed == 0 and len(conflicts) == 0:
            status = SyncStatus.COMPLETED
        elif synced > 0:
            status = SyncStatus.PARTIAL
        elif len(conflicts) > 0:
            status = SyncStatus.CONFLICT
        else:
            status = SyncStatus.FAILED

        result = SyncResult(
            batch_id=batch.batch_id,
            status=status,
            synced_count=synced,
            failed_count=failed,
            conflict_count=len(conflicts),
            checkpoint=new_checkpoint,
            errors=errors,
            conflicts=conflicts,
            duration_ms=duration_ms,
        )

        self._sync_history.append(result)
        return result

    def sync_device(
        self,
        device_id: str,
        cloud_capsule_ids: Optional[List[str]] = None,
    ) -> SyncResult:
        """
        Sync all pending capsules for a device.

        Args:
            device_id: Device identifier
            cloud_capsule_ids: Existing capsule IDs in cloud

        Returns:
            Combined SyncResult
        """
        total_synced = 0
        total_failed = 0
        total_conflicts = 0
        all_errors = []
        all_conflict_details = []
        final_checkpoint = None
        batch_ids = []

        start_time = time.time()

        while self.get_pending_count(device_id) > 0:
            batch = self.create_sync_batch(device_id)
            if not batch:
                break

            result = self.process_sync_batch(batch, cloud_capsule_ids)
            batch_ids.append(result.batch_id)

            total_synced += result.synced_count
            total_failed += result.failed_count
            total_conflicts += result.conflict_count
            all_errors.extend(result.errors)
            all_conflict_details.extend(result.conflicts)
            final_checkpoint = result.checkpoint

            # Stop if batch failed completely
            if result.status == SyncStatus.FAILED:
                break

        duration_ms = int((time.time() - start_time) * 1000)

        if total_failed == 0 and total_conflicts == 0:
            status = SyncStatus.COMPLETED
        elif total_synced > 0:
            status = SyncStatus.PARTIAL
        else:
            status = SyncStatus.FAILED

        return SyncResult(
            batch_id=",".join(batch_ids) if batch_ids else "empty",
            status=status,
            synced_count=total_synced,
            failed_count=total_failed,
            conflict_count=total_conflicts,
            checkpoint=final_checkpoint,
            errors=all_errors,
            conflicts=all_conflict_details,
            duration_ms=duration_ms,
        )

    def get_checkpoint(self, device_id: str) -> Optional[SyncCheckpoint]:
        """Get current checkpoint for a device."""
        return self._checkpoints.get(device_id)

    def set_checkpoint(self, checkpoint: SyncCheckpoint) -> None:
        """Set checkpoint for a device."""
        self._checkpoints[checkpoint.device_id] = checkpoint

    def get_sync_history(
        self,
        device_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[SyncResult]:
        """Get sync history, optionally filtered by device."""
        history = self._sync_history[-limit:]
        # Note: In production, would filter by device_id from batch
        return history

    def _generate_batch_id(self, device_id: str, capsules: List[bytes]) -> str:
        """Generate unique batch ID."""
        content = device_id.encode() + b"".join(capsules[:3])  # Use first 3 for ID
        timestamp = str(int(time.time() * 1000)).encode()
        return hashlib.sha256(content + timestamp).hexdigest()[:32]

    def _create_checkpoint(
        self,
        device_id: str,
        batch: SyncBatch,
    ) -> SyncCheckpoint:
        """Create new checkpoint after sync."""
        existing = self._checkpoints.get(device_id)
        sequence = (existing.sync_sequence + 1) if existing else 1

        last_capsule_id = None
        if batch.capsules:
            try:
                last_capsule = self._decoder.decode(batch.capsules[-1])
                last_capsule_id = last_capsule.capsule_id_hex
            except Exception:
                pass

        checkpoint = SyncCheckpoint(
            checkpoint_id=f"ckpt_{device_id}_{sequence}",
            device_id=device_id,
            last_sync_timestamp=int(time.time() * 1000),
            last_capsule_id=last_capsule_id,
            sync_sequence=sequence,
        )

        self._checkpoints[device_id] = checkpoint
        return checkpoint

    def _handle_conflict(
        self,
        edge_capsule: CompactCapsule,
        cloud_capsule_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Handle conflict between edge and cloud capsule.

        Returns conflict details if unresolved, None if resolved.
        """
        if self.conflict_resolution == ConflictResolution.EDGE_WINS:
            # Edge capsule replaces cloud
            return None
        elif self.conflict_resolution == ConflictResolution.CLOUD_WINS:
            # Discard edge capsule
            return None
        elif self.conflict_resolution == ConflictResolution.NEWEST_WINS:
            # Would compare timestamps in production
            # For now, assume edge is newer
            return None
        else:
            # Manual resolution required
            return {
                "capsule_id": cloud_capsule_id,
                "edge_timestamp": edge_capsule.timestamp_ms,
                "resolution": "manual_required",
            }


# Singleton instance
edge_sync_service = EdgeSyncService()
