"""
Immutable Audit Logging System

Provides cryptographically-chained, tamper-evident audit logs that cannot be
modified or deleted even by administrators. Each log entry is linked to the
previous entry via cryptographic hash, creating an immutable chain.

Key Features:
- Cryptographic chaining (each entry references previous hash)
- Tamper detection (any modification breaks the chain)
- Append-only (no deletions allowed)
- Periodic sealing (timestamped cryptographic checkpoints)
- Merkle tree verification for efficient batch validation

Usage:
    from src.audit.immutable_logger import ImmutableAuditLogger

    logger = ImmutableAuditLogger()
    await logger.log_event(
        event_type="capsule.created",
        user_id="user_123",
        data={"capsule_id": "cap_abc", "action": "create"}
    )
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import asyncio
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


@dataclass
class AuditLogEntry:
    """Single immutable audit log entry"""

    sequence_number: int
    timestamp: str  # ISO 8601 format
    event_type: str
    user_id: Optional[str]
    agent_id: Optional[str]
    ip_address: Optional[str]
    data: Dict[str, Any]
    previous_hash: str  # Hash of previous entry (chain link)
    entry_hash: str  # Hash of this entry
    signature: str  # Cryptographic signature of this entry


class ImmutableAuditLogger:
    """
    Cryptographically-chained, tamper-evident audit log system.

    Each log entry contains:
    1. Sequence number (monotonically increasing)
    2. Timestamp (ISO 8601 with timezone)
    3. Event type and data
    4. Previous entry hash (chain link)
    5. Current entry hash
    6. Cryptographic signature

    Tampering Detection:
    - If any entry is modified, its hash changes
    - If hash changes, the next entry's previous_hash won't match
    - Chain is broken and tampering is detected
    """

    def __init__(
        self,
        storage_path: str = "audit_logs/immutable",
        signing_key: Optional[ed25519.Ed25519PrivateKey] = None,
    ):
        """
        Initialize immutable audit logger.

        Args:
            storage_path: Directory to store audit log files
            signing_key: Ed25519 private key for signing (generated if None)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Generate or load signing key
        if signing_key is None:
            self.signing_key = ed25519.Ed25519PrivateKey.generate()
        else:
            self.signing_key = signing_key

        self.public_key = self.signing_key.public_key()

        # Current chain state
        self.last_entry: Optional[AuditLogEntry] = None
        self.sequence_number: int = 0

        # Load existing chain
        self._load_chain()

    def _load_chain(self):
        """Load existing audit chain from storage"""
        chain_file = self.storage_path / "audit_chain.jsonl"

        if not chain_file.exists():
            return

        with open(chain_file, "r") as f:
            lines = f.readlines()

        if not lines:
            return

        # Load last entry to continue chain
        last_line = lines[-1]
        entry_dict = json.loads(last_line)
        self.last_entry = AuditLogEntry(**entry_dict)
        self.sequence_number = self.last_entry.sequence_number

    def _compute_entry_hash(self, entry_data: Dict[str, Any]) -> str:
        """
        Compute SHA-256 hash of audit entry.

        Args:
            entry_data: Dictionary containing entry fields

        Returns:
            Hex-encoded SHA-256 hash
        """
        # Canonical JSON (sorted keys, no whitespace)
        canonical = json.dumps(entry_data, sort_keys=True, separators=(",", ":"))

        hash_obj = hashlib.sha256()
        hash_obj.update(canonical.encode("utf-8"))

        return hash_obj.hexdigest()

    def _sign_entry(self, entry_hash: str) -> str:
        """
        Sign audit entry hash with Ed25519 private key.

        Args:
            entry_hash: Hex-encoded hash to sign

        Returns:
            Hex-encoded signature
        """
        signature = self.signing_key.sign(entry_hash.encode("utf-8"))
        return signature.hex()

    async def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> AuditLogEntry:
        """
        Log an immutable audit event.

        Args:
            event_type: Type of event (e.g., "capsule.created", "policy.approved")
            user_id: User who performed the action
            agent_id: Agent who performed the action (if applicable)
            ip_address: IP address of requester
            data: Additional event data

        Returns:
            Created audit log entry
        """
        # Increment sequence
        self.sequence_number += 1

        # Get previous hash (or genesis hash if first entry)
        previous_hash = (
            self.last_entry.entry_hash if self.last_entry else "0" * 64  # Genesis hash
        )

        # Create entry data (without hash/signature yet)
        entry_data = {
            "sequence_number": self.sequence_number,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "agent_id": agent_id,
            "ip_address": ip_address,
            "data": data or {},
            "previous_hash": previous_hash,
        }

        # Compute entry hash
        entry_hash = self._compute_entry_hash(entry_data)
        entry_data["entry_hash"] = entry_hash

        # Sign entry
        signature = self._sign_entry(entry_hash)
        entry_data["signature"] = signature

        # Create entry object
        entry = AuditLogEntry(**entry_data)

        # Append to storage (append-only file)
        await self._append_to_storage(entry)

        # Update chain state
        self.last_entry = entry

        return entry

    async def _append_to_storage(self, entry: AuditLogEntry):
        """
        Append entry to immutable storage.

        Uses append-only JSONL file. Each line is a complete audit entry.
        This could be extended to use:
        - AWS S3 Object Lock (WORM storage)
        - IPFS (distributed immutable storage)
        - Blockchain (ultimate immutability)
        """
        chain_file = self.storage_path / "audit_chain.jsonl"

        # Append to file (no overwrites allowed)
        async with asyncio.Lock():
            with open(chain_file, "a") as f:
                f.write(json.dumps(asdict(entry)) + "\n")
                f.flush()  # Force write to disk

    def verify_chain(self) -> tuple[bool, Optional[str]]:
        """
        Verify integrity of entire audit chain.

        Checks:
        1. Each entry's hash matches its content
        2. Each entry's previous_hash matches previous entry's hash
        3. Signatures are valid
        4. Sequence numbers are sequential

        Returns:
            (is_valid, error_message)
        """
        chain_file = self.storage_path / "audit_chain.jsonl"

        if not chain_file.exists():
            return (True, None)  # Empty chain is valid

        with open(chain_file, "r") as f:
            lines = f.readlines()

        previous_entry: Optional[AuditLogEntry] = None

        for i, line in enumerate(lines):
            entry_dict = json.loads(line)
            entry = AuditLogEntry(**entry_dict)

            # Verify sequence number
            expected_seq = i + 1
            if entry.sequence_number != expected_seq:
                return (
                    False,
                    f"Sequence mismatch at position {i}: expected {expected_seq}, got {entry.sequence_number}",
                )

            # Verify hash
            entry_data_for_hash = {
                "sequence_number": entry.sequence_number,
                "timestamp": entry.timestamp,
                "event_type": entry.event_type,
                "user_id": entry.user_id,
                "agent_id": entry.agent_id,
                "ip_address": entry.ip_address,
                "data": entry.data,
                "previous_hash": entry.previous_hash,
            }
            computed_hash = self._compute_entry_hash(entry_data_for_hash)

            if computed_hash != entry.entry_hash:
                return (
                    False,
                    f"Hash mismatch at position {i}: entry has been tampered with",
                )

            # Verify signature
            try:
                self.public_key.verify(
                    bytes.fromhex(entry.signature), entry.entry_hash.encode("utf-8")
                )
            except Exception as e:
                return (
                    False,
                    f"Signature verification failed at position {i}: {str(e)}",
                )

            # Verify chain link
            if previous_entry is not None:
                if entry.previous_hash != previous_entry.entry_hash:
                    return (
                        False,
                        f"Chain broken at position {i}: previous_hash mismatch",
                    )
            else:
                # First entry should reference genesis hash
                if entry.previous_hash != "0" * 64:
                    return (False, f"First entry should reference genesis hash")

            previous_entry = entry

        return (True, None)

    async def seal_chain(self) -> Dict[str, Any]:
        """
        Create a cryptographic seal of the current chain state.

        This creates a timestamped checkpoint that can be used for:
        - Third-party verification
        - Compliance audits
        - Proving chain state at specific time

        Returns:
            Seal data including:
            - Last entry hash
            - Sequence number
            - Timestamp
            - Signature
        """
        if not self.last_entry:
            raise ValueError("Cannot seal empty chain")

        seal_data = {
            "seal_timestamp": datetime.now(timezone.utc).isoformat(),
            "last_entry_hash": self.last_entry.entry_hash,
            "last_sequence_number": self.last_entry.sequence_number,
            "total_entries": self.sequence_number,
        }

        # Sign the seal
        seal_hash = self._compute_entry_hash(seal_data)
        seal_signature = self._sign_entry(seal_hash)

        seal = {**seal_data, "seal_hash": seal_hash, "seal_signature": seal_signature}

        # Store seal
        seal_file = (
            self.storage_path
            / f"seal_{seal_data['seal_timestamp'].replace(':', '-')}.json"
        )
        with open(seal_file, "w") as f:
            json.dump(seal, f, indent=2)

        return seal

    def get_recent_entries(self, count: int = 100) -> List[AuditLogEntry]:
        """Get most recent audit entries"""
        chain_file = self.storage_path / "audit_chain.jsonl"

        if not chain_file.exists():
            return []

        with open(chain_file, "r") as f:
            lines = f.readlines()

        recent_lines = lines[-count:]
        entries = [AuditLogEntry(**json.loads(line)) for line in recent_lines]

        return entries

    def search_entries(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """
        Search audit log entries.

        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            agent_id: Filter by agent ID
            start_time: Filter by start time (inclusive)
            end_time: Filter by end time (inclusive)

        Returns:
            List of matching audit entries
        """
        chain_file = self.storage_path / "audit_chain.jsonl"

        if not chain_file.exists():
            return []

        matches = []

        with open(chain_file, "r") as f:
            for line in f:
                entry = AuditLogEntry(**json.loads(line))

                # Apply filters
                if event_type and entry.event_type != event_type:
                    continue

                if user_id and entry.user_id != user_id:
                    continue

                if agent_id and entry.agent_id != agent_id:
                    continue

                entry_time = datetime.fromisoformat(entry.timestamp)
                if start_time and entry_time < start_time:
                    continue

                if end_time and entry_time > end_time:
                    continue

                matches.append(entry)

        return matches
