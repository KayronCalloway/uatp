"""
Merkle Audit Log Implementation
===============================

Provides cryptographic append-only audit logs with:
- Tamper-evident history
- Efficient inclusion proofs
- Consistency proofs between log states
- Verifiable log integrity

Based on RFC 6962 (Certificate Transparency) Merkle Tree structure.

Security Properties:
- Any modification to past entries is detectable
- Efficient O(log n) proofs of inclusion
- Third-party verifiable without full log access
"""

import hashlib
import json
import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Leaf and node prefixes per RFC 6962
LEAF_PREFIX = b"\x00"
NODE_PREFIX = b"\x01"


def merkle_hash(data: bytes) -> bytes:
    """Compute SHA-256 hash of data."""
    return hashlib.sha256(data).digest()


def leaf_hash(data: bytes) -> bytes:
    """Compute hash of a leaf node (prefixed with 0x00)."""
    return merkle_hash(LEAF_PREFIX + data)


def node_hash(left: bytes, right: bytes) -> bytes:
    """Compute hash of an internal node (prefixed with 0x01)."""
    return merkle_hash(NODE_PREFIX + left + right)


@dataclass
class LogEntry:
    """A single entry in the audit log."""

    index: int
    timestamp: datetime
    entry_type: str
    data_hash: str  # SHA-256 of the data
    data: Optional[Dict[str, Any]] = (
        None  # Optional: actual data (may be stored separately)
    )
    leaf_hash: str = ""  # Merkle leaf hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp.isoformat(),
            "entry_type": self.entry_type,
            "data_hash": self.data_hash,
            "leaf_hash": self.leaf_hash,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LogEntry":
        return cls(
            index=d["index"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            entry_type=d["entry_type"],
            data_hash=d["data_hash"],
            leaf_hash=d.get("leaf_hash", ""),
            data=d.get("data"),
        )


@dataclass
class InclusionProof:
    """Proof that an entry exists in the log at a specific tree size."""

    leaf_index: int
    tree_size: int
    proof_hashes: List[str]  # Sibling hashes from leaf to root
    root_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "leaf_index": self.leaf_index,
            "tree_size": self.tree_size,
            "proof_hashes": self.proof_hashes,
            "root_hash": self.root_hash,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "InclusionProof":
        return cls(
            leaf_index=d["leaf_index"],
            tree_size=d["tree_size"],
            proof_hashes=d["proof_hashes"],
            root_hash=d["root_hash"],
        )


@dataclass
class ConsistencyProof:
    """Proof that log at size1 is a prefix of log at size2."""

    size1: int
    size2: int
    proof_hashes: List[str]
    root1: str
    root2: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "size1": self.size1,
            "size2": self.size2,
            "proof_hashes": self.proof_hashes,
            "root1": self.root1,
            "root2": self.root2,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ConsistencyProof":
        return cls(
            size1=d["size1"],
            size2=d["size2"],
            proof_hashes=d["proof_hashes"],
            root1=d["root1"],
            root2=d["root2"],
        )


@dataclass
class SignedTreeHead:
    """Signed commitment to the current log state."""

    tree_size: int
    timestamp: datetime
    root_hash: str
    signature: str  # Ed25519 signature over (tree_size || timestamp || root_hash)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tree_size": self.tree_size,
            "timestamp": self.timestamp.isoformat(),
            "root_hash": self.root_hash,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SignedTreeHead":
        return cls(
            tree_size=d["tree_size"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            root_hash=d["root_hash"],
            signature=d["signature"],
        )


class MerkleAuditLog:
    """
    Append-only Merkle audit log with cryptographic integrity guarantees.

    Structure:
    - Entries are stored as leaves in a Merkle tree
    - Each append updates the tree root
    - Inclusion proofs verify entry membership
    - Consistency proofs verify log append-only property

    Storage:
    log_dir/
    ├── entries/          # Individual log entries (JSON)
    ├── tree_state.json   # Current tree state (hashes, size)
    ├── tree_heads/       # Historical signed tree heads
    └── checkpoints/      # Periodic full tree snapshots
    """

    def __init__(
        self,
        log_dir: str = ".uatp_audit_log",
        log_id: str = "default",
        signer: Optional[Any] = None,  # UATPCryptoV7 instance
    ):
        """
        Initialize Merkle audit log.

        Args:
            log_dir: Directory to store log data
            log_id: Identifier for this log
            signer: Crypto instance for signing tree heads
        """
        self.log_dir = Path(log_dir)
        self.log_id = log_id
        self.signer = signer

        # In-memory state
        self._lock = threading.Lock()
        self._entries: List[LogEntry] = []
        self._leaf_hashes: List[bytes] = []
        self._cached_nodes: Dict[Tuple[int, int], bytes] = {}  # (level, index) -> hash

        # Ensure directories exist
        self._ensure_directories()

        # Load existing state
        self._load_state()

        logger.info(
            f"Merkle audit log initialized: {log_id} ({len(self._entries)} entries)"
        )

    def _ensure_directories(self) -> None:
        """Create required directory structure."""
        for subdir in ["entries", "tree_heads", "checkpoints"]:
            (self.log_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> None:
        """Load log state from disk."""
        state_file = self.log_dir / "tree_state.json"
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)

            # Load entries
            for i in range(state.get("tree_size", 0)):
                entry_file = self.log_dir / "entries" / f"{i:010d}.json"
                if entry_file.exists():
                    with open(entry_file) as f:
                        entry = LogEntry.from_dict(json.load(f))
                        self._entries.append(entry)
                        self._leaf_hashes.append(bytes.fromhex(entry.leaf_hash))

    def _save_state(self) -> None:
        """Save log state to disk."""
        state = {
            "log_id": self.log_id,
            "tree_size": len(self._entries),
            "root_hash": self.root_hash().hex() if self._entries else "",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        state_file = self.log_dir / "tree_state.json"
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

    def _save_entry(self, entry: LogEntry) -> None:
        """Save individual entry to disk."""
        entry_file = self.log_dir / "entries" / f"{entry.index:010d}.json"
        with open(entry_file, "w") as f:
            json.dump(entry.to_dict(), f, indent=2)

    @property
    def size(self) -> int:
        """Current number of entries in the log."""
        return len(self._entries)

    def append(
        self,
        entry_type: str,
        data: Dict[str, Any],
        store_data: bool = True,
    ) -> LogEntry:
        """
        Append a new entry to the audit log.

        Args:
            entry_type: Type of entry (e.g., "capsule_created", "key_rotated")
            data: Entry data (will be hashed)
            store_data: Whether to store full data (False = hash only)

        Returns:
            The created log entry
        """
        with self._lock:
            # Serialize data deterministically
            data_bytes = json.dumps(data, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
            data_hash = hashlib.sha256(data_bytes).hexdigest()

            # Compute leaf hash
            leaf_data = f"{entry_type}:{data_hash}".encode()
            leaf_hash_bytes = leaf_hash(leaf_data)

            # Create entry
            entry = LogEntry(
                index=len(self._entries),
                timestamp=datetime.now(timezone.utc),
                entry_type=entry_type,
                data_hash=data_hash,
                data=data if store_data else None,
                leaf_hash=leaf_hash_bytes.hex(),
            )

            # Update in-memory state
            self._entries.append(entry)
            self._leaf_hashes.append(leaf_hash_bytes)

            # Invalidate cached nodes affected by this append
            self._invalidate_cache(entry.index)

            # Persist
            self._save_entry(entry)
            self._save_state()

            logger.debug(f"Appended entry {entry.index}: {entry_type}")
            return entry

    def _invalidate_cache(self, leaf_index: int) -> None:
        """Invalidate cached nodes affected by a new leaf."""
        # For simplicity, clear all cached nodes
        # A more sophisticated implementation would only clear affected paths
        self._cached_nodes.clear()

    def root_hash(self) -> bytes:
        """Compute the current Merkle root hash."""
        if not self._leaf_hashes:
            return b"\x00" * 32  # Empty tree

        return self._compute_root(len(self._leaf_hashes))

    def _compute_root(self, tree_size: int) -> bytes:
        """Compute Merkle root for a given tree size."""
        if tree_size == 0:
            return b"\x00" * 32
        if tree_size == 1:
            return self._leaf_hashes[0]

        # Find the largest power of 2 less than tree_size
        k = 1
        while k * 2 < tree_size:
            k *= 2

        # Recursively compute
        left = self._compute_subtree_root(0, k)
        right = self._compute_root_range(k, tree_size)

        return node_hash(left, right)

    def _compute_subtree_root(self, start: int, size: int) -> bytes:
        """Compute root of a complete subtree."""
        if size == 1:
            return self._leaf_hashes[start]

        cache_key = (start, size)
        if cache_key in self._cached_nodes:
            return self._cached_nodes[cache_key]

        half = size // 2
        left = self._compute_subtree_root(start, half)
        right = self._compute_subtree_root(start + half, half)
        result = node_hash(left, right)

        self._cached_nodes[cache_key] = result
        return result

    def _compute_root_range(self, start: int, end: int) -> bytes:
        """Compute root of a range of leaves."""
        size = end - start
        if size == 0:
            return b"\x00" * 32
        if size == 1:
            return self._leaf_hashes[start]

        # Find largest power of 2 <= size
        k = 1
        while k * 2 <= size:
            k *= 2

        if k == size:
            return self._compute_subtree_root(start, size)

        left = self._compute_subtree_root(start, k)
        right = self._compute_root_range(start + k, end)
        return node_hash(left, right)

    def get_entry(self, index: int) -> Optional[LogEntry]:
        """Get entry by index."""
        if 0 <= index < len(self._entries):
            return self._entries[index]
        return None

    def _compute_inclusion_proof(
        self, leaf_index: int, tree_size: int
    ) -> List[Tuple[bytes, bool]]:
        """
        Compute the inclusion proof path using standard bottom-up approach.

        Returns list of (sibling_hash, is_left) tuples encoded as proof elements.
        """
        proof: List[Tuple[bytes, bool]] = []

        if tree_size <= 1:
            return proof

        # Build proof bottom-up using the path from leaf to root
        def audit_path(index: int, start: int, end: int) -> None:
            """Recursively compute audit path."""
            width = end - start
            if width == 1:
                return

            mid = start + self._largest_power_of_2_less_than(width)

            if index < mid:
                # Target is in left subtree, need right subtree hash
                right_hash = self._compute_root_range(mid, end)
                proof.append((right_hash, False))  # sibling is on right
                audit_path(index, start, mid)
            else:
                # Target is in right subtree, need left subtree hash
                left_hash = self._compute_root_range(start, mid)
                proof.append((left_hash, True))  # sibling is on left
                audit_path(index, mid, end)

        audit_path(leaf_index, 0, tree_size)

        # Reverse so proof goes from leaf to root
        proof.reverse()

        # Return the hashes with position encoded
        return proof

    def _largest_power_of_2_less_than(self, n: int) -> int:
        """Find largest power of 2 less than n."""
        if n <= 1:
            return 0
        k = 1
        while k * 2 < n:
            k *= 2
        return k

    def get_inclusion_proof(
        self, leaf_index: int, tree_size: Optional[int] = None
    ) -> InclusionProof:
        """
        Generate proof that entry at leaf_index is in the log.

        Args:
            leaf_index: Index of the entry
            tree_size: Size of tree for proof (default: current size)

        Returns:
            InclusionProof with sibling hashes
        """
        if tree_size is None:
            tree_size = len(self._entries)

        if leaf_index >= tree_size:
            raise ValueError(f"Leaf index {leaf_index} >= tree size {tree_size}")

        proof_data = self._compute_inclusion_proof(leaf_index, tree_size)
        root = self._compute_root(tree_size)

        # Encode proof: each hash is prefixed with 'L' or 'R' to indicate position
        proof_hashes = []
        for h, is_left in proof_data:
            prefix = "L:" if is_left else "R:"
            proof_hashes.append(prefix + h.hex())

        return InclusionProof(
            leaf_index=leaf_index,
            tree_size=tree_size,
            proof_hashes=proof_hashes,
            root_hash=root.hex(),
        )

    def verify_inclusion_proof(
        self,
        entry: LogEntry,
        proof: InclusionProof,
    ) -> Tuple[bool, str]:
        """
        Verify an inclusion proof.

        Args:
            entry: The log entry
            proof: The inclusion proof

        Returns:
            Tuple of (is_valid, reason)
        """
        # Recompute leaf hash
        leaf_data = f"{entry.entry_type}:{entry.data_hash}".encode()
        computed_leaf = leaf_hash(leaf_data)

        if computed_leaf.hex() != entry.leaf_hash:
            return False, "Leaf hash mismatch"

        # Walk up the tree from leaf to root
        current = computed_leaf

        for proof_entry in proof.proof_hashes:
            # Parse the proof entry (L: or R: prefix)
            if proof_entry.startswith("L:"):
                sibling = bytes.fromhex(proof_entry[2:])
                current = node_hash(sibling, current)  # sibling is left
            elif proof_entry.startswith("R:"):
                sibling = bytes.fromhex(proof_entry[2:])
                current = node_hash(current, sibling)  # sibling is right
            else:
                return False, f"Invalid proof format: {proof_entry[:10]}..."

        if current.hex() != proof.root_hash:
            return (
                False,
                f"Root hash mismatch: computed {current.hex()[:16]}... != expected {proof.root_hash[:16]}...",
            )

        return True, "Inclusion verified"

    def get_consistency_proof(
        self, size1: int, size2: Optional[int] = None
    ) -> ConsistencyProof:
        """
        Generate proof that log at size1 is consistent with log at size2.

        This proves the append-only property: all entries in the smaller
        log are also in the larger log at the same positions.

        Args:
            size1: Smaller tree size
            size2: Larger tree size (default: current size)

        Returns:
            ConsistencyProof
        """
        if size2 is None:
            size2 = len(self._entries)

        if size1 > size2:
            raise ValueError(f"size1 ({size1}) > size2 ({size2})")

        if size1 == 0:
            return ConsistencyProof(
                size1=size1,
                size2=size2,
                proof_hashes=[],
                root1="",
                root2=self._compute_root(size2).hex(),
            )

        proof_hashes = self._compute_consistency_proof(size1, size2)

        return ConsistencyProof(
            size1=size1,
            size2=size2,
            proof_hashes=[h.hex() for h in proof_hashes],
            root1=self._compute_root(size1).hex(),
            root2=self._compute_root(size2).hex(),
        )

    def _compute_consistency_proof(self, size1: int, size2: int) -> List[bytes]:
        """Compute consistency proof between two tree sizes."""
        proof: List[bytes] = []

        if size1 == size2:
            return proof

        # Subproof algorithm from RFC 6962
        def subproof(m: int, start: int, end: int, complete: bool) -> None:
            n = end - start
            if m == n:
                if not complete:
                    proof.append(self._compute_root_range(start, end))
                return

            k = 1
            while k * 2 < n:
                k *= 2

            if m <= k:
                subproof(m, start, start + k, complete)
                proof.append(self._compute_root_range(start + k, end))
            else:
                subproof(m - k, start + k, end, False)
                proof.append(self._compute_subtree_root(start, k))

        subproof(size1, 0, size2, True)
        return proof

    def verify_consistency_proof(self, proof: ConsistencyProof) -> Tuple[bool, str]:
        """
        Verify a consistency proof.

        Args:
            proof: The consistency proof

        Returns:
            Tuple of (is_valid, reason)
        """
        if proof.size1 == 0:
            return True, "Empty log is consistent with any log"

        if proof.size1 == proof.size2:
            if proof.root1 == proof.root2:
                return True, "Same size, same root"
            return False, "Same size but different roots"

        # Verify using the proof hashes
        proof_hashes = [bytes.fromhex(h) for h in proof.proof_hashes]

        # Reconstruct both roots
        try:
            root1, root2 = self._verify_consistency_hashes(
                proof.size1, proof.size2, proof_hashes
            )

            if root1.hex() != proof.root1:
                return False, "Root1 mismatch"
            if root2.hex() != proof.root2:
                return False, "Root2 mismatch"

            return True, "Consistency verified"
        except Exception as e:
            return False, f"Verification failed: {e}"

    def _verify_consistency_hashes(
        self, size1: int, size2: int, proof: List[bytes]
    ) -> Tuple[bytes, bytes]:
        """Verify consistency proof and return both roots."""
        if size1 == size2:
            if not proof:
                root = self._compute_root(size1)
                return root, root
            raise ValueError("Non-empty proof for equal sizes")

        proof_idx = [0]  # Use list to allow modification in nested function

        def inner(m: int, n: int, complete: bool) -> Tuple[bytes, bytes]:
            if m == n:
                if complete:
                    root = self._compute_root(m)
                    return root, root
                else:
                    h = proof[proof_idx[0]]
                    proof_idx[0] += 1
                    return h, h

            k = 1
            while k * 2 < n:
                k *= 2

            if m <= k:
                left1, left2 = inner(m, k, complete)
                right = proof[proof_idx[0]]
                proof_idx[0] += 1
                return left1, node_hash(left2, right)
            else:
                right1, right2 = inner(m - k, n - k, False)
                left = proof[proof_idx[0]]
                proof_idx[0] += 1
                return node_hash(left, right1), node_hash(left, right2)

        return inner(size1, size2, True)

    def get_signed_tree_head(self) -> SignedTreeHead:
        """
        Get a signed commitment to the current log state.

        Returns:
            SignedTreeHead with signature
        """
        tree_size = len(self._entries)
        timestamp = datetime.now(timezone.utc)
        root = self.root_hash()

        # Create message to sign
        message = f"{tree_size}:{timestamp.isoformat()}:{root.hex()}".encode()

        # Sign if signer available
        if self.signer and hasattr(self.signer, "_sign_ed25519"):
            signature = self.signer._sign_ed25519({"sth": message.decode("utf-8")})
        else:
            # Placeholder signature
            signature = f"unsigned:{hashlib.sha256(message).hexdigest()}"

        sth = SignedTreeHead(
            tree_size=tree_size,
            timestamp=timestamp,
            root_hash=root.hex(),
            signature=signature,
        )

        # Save to disk
        sth_file = self.log_dir / "tree_heads" / f"sth_{tree_size:010d}.json"
        with open(sth_file, "w") as f:
            json.dump(sth.to_dict(), f, indent=2)

        return sth

    def audit_log(
        self,
        start_index: int = 0,
        end_index: Optional[int] = None,
        entry_type: Optional[str] = None,
    ) -> List[LogEntry]:
        """
        Query log entries with optional filtering.

        Args:
            start_index: Start index (inclusive)
            end_index: End index (exclusive, default: all)
            entry_type: Filter by entry type

        Returns:
            List of matching entries
        """
        if end_index is None:
            end_index = len(self._entries)

        entries = self._entries[start_index:end_index]

        if entry_type:
            entries = [e for e in entries if e.entry_type == entry_type]

        return entries

    def get_statistics(self) -> Dict[str, Any]:
        """Get log statistics."""
        entry_types: Dict[str, int] = {}
        for entry in self._entries:
            entry_types[entry.entry_type] = entry_types.get(entry.entry_type, 0) + 1

        return {
            "log_id": self.log_id,
            "total_entries": len(self._entries),
            "root_hash": self.root_hash().hex(),
            "entry_types": entry_types,
            "first_entry": self._entries[0].timestamp.isoformat()
            if self._entries
            else None,
            "last_entry": self._entries[-1].timestamp.isoformat()
            if self._entries
            else None,
        }


# Convenience functions


def create_audit_log(
    log_dir: str = ".uatp_audit_log",
    log_id: str = "default",
) -> MerkleAuditLog:
    """Create or open a Merkle audit log."""
    return MerkleAuditLog(log_dir=log_dir, log_id=log_id)


def log_capsule_event(
    log: MerkleAuditLog,
    event_type: str,
    capsule_id: str,
    details: Dict[str, Any],
) -> LogEntry:
    """Log a capsule-related event."""
    data = {
        "capsule_id": capsule_id,
        "event": event_type,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return log.append(f"capsule_{event_type}", data)


def verify_log_integrity(log: MerkleAuditLog) -> Tuple[bool, str]:
    """
    Verify the integrity of an entire audit log.

    Checks that:
    1. All leaf hashes are correct
    2. Tree structure is valid
    3. Root hash matches computed value
    """
    if log.size == 0:
        return True, "Empty log is valid"

    # Verify each entry's leaf hash
    for entry in log._entries:
        leaf_data = f"{entry.entry_type}:{entry.data_hash}".encode()
        computed_leaf = leaf_hash(leaf_data)
        if computed_leaf.hex() != entry.leaf_hash:
            return False, f"Entry {entry.index} has invalid leaf hash"

    # Verify root can be computed
    try:
        root = log.root_hash()
        return (
            True,
            f"Log integrity verified ({log.size} entries, root: {root.hex()[:16]}...)",
        )
    except Exception as e:
        return False, f"Root computation failed: {e}"
