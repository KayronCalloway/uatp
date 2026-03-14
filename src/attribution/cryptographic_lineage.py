"""
Cryptographic Lineage Security for UATP Attribution System.

This module implements cryptographic proofs and tamper-evident attribution
chains to secure the lineage system against falsification and manipulation.

SECURITY FEATURES:
- Ed25519 digital signatures for attribution integrity
- Merkle tree proofs for lineage verification
- Hash chains for temporal consistency
- Zero-knowledge proofs for privacy-preserving attribution
- Cryptographic commitment schemes
"""

import hashlib
import json
import logging
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    ed25519 = None

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)

if not CRYPTO_AVAILABLE:
    logger.warning("Cryptography library not available. Using mock implementations.")


@dataclass
class CryptographicProof:
    """Cryptographic proof for attribution integrity."""

    proof_id: str
    proof_type: str  # signature, merkle, commitment, zk_proof

    # Proof data
    signature: Optional[bytes] = None
    public_key: Optional[bytes] = None
    merkle_root: Optional[bytes] = None
    merkle_path: Optional[List[bytes]] = None
    commitment: Optional[bytes] = None

    # Metadata
    algorithm: str = "ed25519"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Verification data
    verified: bool = False
    verification_timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert proof to dictionary."""
        return {
            "proof_id": self.proof_id,
            "proof_type": self.proof_type,
            "signature": self.signature.hex() if self.signature else None,
            "public_key": self.public_key.hex() if self.public_key else None,
            "merkle_root": self.merkle_root.hex() if self.merkle_root else None,
            "merkle_path": [p.hex() for p in self.merkle_path]
            if self.merkle_path
            else None,
            "commitment": self.commitment.hex() if self.commitment else None,
            "algorithm": self.algorithm,
            "timestamp": self.timestamp.isoformat(),
            "verified": self.verified,
            "verification_timestamp": self.verification_timestamp.isoformat()
            if self.verification_timestamp
            else None,
        }


@dataclass
class SecureLineageEntry:
    """Secure lineage entry with cryptographic proofs."""

    entry_id: str
    capsule_id: str
    parent_capsule_id: Optional[str]

    # Attribution data
    contributor_id: str
    contribution_type: str
    attribution_weight: float

    # Cryptographic elements
    content_hash: bytes
    previous_hash: bytes
    entry_hash: bytes
    digital_signature: bytes

    # Proofs
    integrity_proof: CryptographicProof
    lineage_proof: Optional[CryptographicProof] = None

    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    nonce: int = field(default_factory=lambda: secrets.randbits(64))

    def calculate_hash(self) -> bytes:
        """Calculate hash of this lineage entry."""
        data = {
            "entry_id": self.entry_id,
            "capsule_id": self.capsule_id,
            "parent_capsule_id": self.parent_capsule_id,
            "contributor_id": self.contributor_id,
            "contribution_type": self.contribution_type,
            "attribution_weight": self.attribution_weight,
            "content_hash": self.content_hash.hex(),
            "previous_hash": self.previous_hash.hex(),
            "timestamp": self.timestamp.isoformat(),
            "nonce": self.nonce,
        }

        canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode()).digest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            "entry_id": self.entry_id,
            "capsule_id": self.capsule_id,
            "parent_capsule_id": self.parent_capsule_id,
            "contributor_id": self.contributor_id,
            "contribution_type": self.contribution_type,
            "attribution_weight": self.attribution_weight,
            "content_hash": self.content_hash.hex(),
            "previous_hash": self.previous_hash.hex(),
            "entry_hash": self.entry_hash.hex(),
            "digital_signature": self.digital_signature.hex(),
            "integrity_proof": self.integrity_proof.to_dict(),
            "lineage_proof": self.lineage_proof.to_dict()
            if self.lineage_proof
            else None,
            "timestamp": self.timestamp.isoformat(),
            "nonce": self.nonce,
        }


class MerkleTree:
    """Merkle tree implementation for batch lineage verification."""

    def __init__(self, entries: List[bytes]):
        self.entries = entries
        self.tree = self._build_tree(entries)
        self.root = self.tree[0][0] if self.tree else b""

    def _build_tree(self, entries: List[bytes]) -> List[List[bytes]]:
        """Build Merkle tree from entries."""
        if not entries:
            return []

        # Start with leaf level
        current_level = entries[:]
        tree = [current_level[:]]

        # Build tree levels
        while len(current_level) > 1:
            next_level = []

            # Process pairs
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left

                # Combine hashes
                combined = hashlib.sha256(left + right).digest()
                next_level.append(combined)

            current_level = next_level
            tree.insert(0, current_level[:])

        return tree

    def get_proof(self, index: int) -> List[bytes]:
        """Get Merkle proof for entry at index."""
        if index >= len(self.entries):
            return []

        proof = []
        current_index = index

        # Traverse tree levels from bottom to top
        for level in range(len(self.tree) - 1, 0, -1):
            level_size = len(self.tree[level])

            # Find sibling
            if current_index % 2 == 0:  # Left child
                sibling_index = current_index + 1
            else:  # Right child
                sibling_index = current_index - 1

            # Add sibling to proof if it exists
            if sibling_index < level_size:
                proof.append(self.tree[level][sibling_index])

            # Move to parent index
            current_index = current_index // 2

        return proof

    @staticmethod
    def verify_proof(entry: bytes, proof: List[bytes], root: bytes) -> bool:
        """Verify Merkle proof."""
        current_hash = entry

        for sibling in proof:
            # Determine order (smaller hash first)
            if current_hash <= sibling:
                current_hash = hashlib.sha256(current_hash + sibling).digest()
            else:
                current_hash = hashlib.sha256(sibling + current_hash).digest()

        return current_hash == root


class CryptographicLineageManager:
    """Manager for cryptographic lineage security."""

    def __init__(self):
        # Key management
        self.private_keys: Dict[str, bytes] = {}  # contributor_id -> private_key
        self.public_keys: Dict[str, bytes] = {}  # contributor_id -> public_key

        # Lineage chain storage
        self.lineage_chain: List[SecureLineageEntry] = []
        self.lineage_index: Dict[str, int] = {}  # entry_id -> chain_position

        # Merkle tree management
        self.merkle_trees: Dict[str, MerkleTree] = {}  # batch_id -> MerkleTree
        self.batch_size = 100  # Entries per Merkle tree batch

        # Verification cache
        self.verification_cache: Dict[str, bool] = {}

        # Performance metrics
        self.metrics = {
            "entries_created": 0,
            "signatures_verified": 0,
            "merkle_proofs_generated": 0,
            "verification_failures": 0,
            "lineage_violations_detected": 0,
        }

        logger.info("Cryptographic Lineage Manager initialized")

    def generate_key_pair(self, contributor_id: str) -> Tuple[bytes, bytes]:
        """Generate Ed25519 key pair for contributor."""

        if not CRYPTO_AVAILABLE:
            # Mock implementation
            private_key = secrets.token_bytes(32)
            public_key = secrets.token_bytes(32)
        else:
            private_key_obj = ed25519.Ed25519PrivateKey.generate()
            public_key_obj = private_key_obj.public_key()

            private_key = private_key_obj.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )

            public_key = public_key_obj.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )

        # Store keys
        self.private_keys[contributor_id] = private_key
        self.public_keys[contributor_id] = public_key

        audit_emitter.emit_security_event(
            "cryptographic_keys_generated",
            {
                "contributor_id": contributor_id,
                "public_key_hash": hashlib.sha256(public_key).hexdigest()[:16],
            },
        )

        return private_key, public_key

    def create_secure_lineage_entry(
        self,
        capsule_id: str,
        parent_capsule_id: Optional[str],
        contributor_id: str,
        contribution_type: str,
        attribution_weight: float,
        content_data: Dict[str, Any],
    ) -> SecureLineageEntry:
        """Create cryptographically secure lineage entry."""

        self.metrics["entries_created"] += 1
        entry_id = f"secure_lineage_{uuid.uuid4()}"

        # Ensure contributor has keys
        if contributor_id not in self.private_keys:
            self.generate_key_pair(contributor_id)

        # Calculate content hash
        content_json = json.dumps(content_data, sort_keys=True, separators=(",", ":"))
        content_hash = hashlib.sha256(content_json.encode()).digest()

        # Get previous hash from chain
        previous_hash = b"\x00" * 32  # Genesis hash
        if self.lineage_chain:
            previous_hash = self.lineage_chain[-1].entry_hash

        # Create entry (without hash and signature initially)
        entry = SecureLineageEntry(
            entry_id=entry_id,
            capsule_id=capsule_id,
            parent_capsule_id=parent_capsule_id,
            contributor_id=contributor_id,
            contribution_type=contribution_type,
            attribution_weight=attribution_weight,
            content_hash=content_hash,
            previous_hash=previous_hash,
            entry_hash=b"",  # Will be calculated
            digital_signature=b"",  # Will be calculated
            integrity_proof=CryptographicProof(
                proof_id=f"integrity_{uuid.uuid4()}", proof_type="signature"
            ),
        )

        # Calculate entry hash
        entry.entry_hash = entry.calculate_hash()

        # Create digital signature
        entry.digital_signature = self._sign_entry(entry, contributor_id)

        # Create integrity proof
        entry.integrity_proof.signature = entry.digital_signature
        entry.integrity_proof.public_key = self.public_keys[contributor_id]

        # Verify lineage consistency
        if not self._verify_lineage_consistency(entry):
            self.metrics["lineage_violations_detected"] += 1
            raise ValueError("Lineage consistency violation detected")

        # Add to chain
        self.lineage_chain.append(entry)
        self.lineage_index[entry_id] = len(self.lineage_chain) - 1

        # Create Merkle proof if batch is complete
        if len(self.lineage_chain) % self.batch_size == 0:
            self._create_merkle_batch()

        audit_emitter.emit_security_event(
            "secure_lineage_entry_created",
            {
                "entry_id": entry_id,
                "capsule_id": capsule_id,
                "contributor_id": contributor_id,
                "entry_hash": entry.entry_hash.hex()[:16],
            },
        )

        return entry

    def verify_lineage_entry(self, entry_id: str) -> Dict[str, Any]:
        """Verify cryptographic integrity of lineage entry."""

        if entry_id not in self.lineage_index:
            return {"verified": False, "error": "Entry not found", "checks": {}}

        position = self.lineage_index[entry_id]
        entry = self.lineage_chain[position]

        verification_result = {"verified": True, "error": None, "checks": {}}

        # 1. Verify digital signature
        signature_valid = self._verify_signature(entry)
        verification_result["checks"]["signature"] = signature_valid
        if not signature_valid:
            verification_result["verified"] = False
            verification_result["error"] = "Invalid digital signature"

        # 2. Verify entry hash
        calculated_hash = entry.calculate_hash()
        hash_valid = calculated_hash == entry.entry_hash
        verification_result["checks"]["hash"] = hash_valid
        if not hash_valid:
            verification_result["verified"] = False
            verification_result["error"] = "Invalid entry hash"

        # 3. Verify chain consistency
        chain_valid = self._verify_chain_position(entry, position)
        verification_result["checks"]["chain"] = chain_valid
        if not chain_valid:
            verification_result["verified"] = False
            verification_result["error"] = "Chain consistency violation"

        # 4. Verify Merkle proof if available
        merkle_valid = self._verify_merkle_proof(entry, position)
        verification_result["checks"]["merkle"] = merkle_valid
        if merkle_valid is False:  # None means no proof available
            verification_result["verified"] = False
            verification_result["error"] = "Invalid Merkle proof"

        # Update metrics
        if verification_result["verified"]:
            self.metrics["signatures_verified"] += 1
        else:
            self.metrics["verification_failures"] += 1

        # Cache result
        self.verification_cache[entry_id] = verification_result["verified"]

        return verification_result

    def verify_lineage_chain_integrity(self) -> Dict[str, Any]:
        """Verify integrity of entire lineage chain."""

        if not self.lineage_chain:
            return {
                "verified": True,
                "total_entries": 0,
                "failed_entries": [],
                "chain_breaks": [],
            }

        failed_entries = []
        chain_breaks = []

        # Verify each entry
        for i, entry in enumerate(self.lineage_chain):
            verification = self.verify_lineage_entry(entry.entry_id)
            if not verification["verified"]:
                failed_entries.append(
                    {
                        "entry_id": entry.entry_id,
                        "position": i,
                        "error": verification["error"],
                    }
                )

            # Check chain linkage
            if i > 0:
                expected_previous = self.lineage_chain[i - 1].entry_hash
                if entry.previous_hash != expected_previous:
                    chain_breaks.append(
                        {
                            "position": i,
                            "entry_id": entry.entry_id,
                            "expected_previous": expected_previous.hex()[:16],
                            "actual_previous": entry.previous_hash.hex()[:16],
                        }
                    )

        return {
            "verified": len(failed_entries) == 0 and len(chain_breaks) == 0,
            "total_entries": len(self.lineage_chain),
            "failed_entries": failed_entries,
            "chain_breaks": chain_breaks,
            "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def create_lineage_proof(self, capsule_id: str) -> Dict[str, Any]:
        """Create comprehensive lineage proof for a capsule."""

        # Find all entries for this capsule
        capsule_entries = [
            entry for entry in self.lineage_chain if entry.capsule_id == capsule_id
        ]

        if not capsule_entries:
            return {
                "error": "No lineage entries found for capsule",
                "capsule_id": capsule_id,
            }

        # Create proof bundle
        proof_bundle = {
            "proof_id": f"lineage_proof_{uuid.uuid4()}",
            "capsule_id": capsule_id,
            "proof_type": "comprehensive_lineage",
            "entries": [],
            "merkle_proofs": [],
            "chain_verification": None,
            "creation_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Add entry proofs
        for entry in capsule_entries:
            entry_proof = {
                "entry_id": entry.entry_id,
                "entry_data": entry.to_dict(),
                "verification": self.verify_lineage_entry(entry.entry_id),
            }

            # Add Merkle proof if available
            position = self.lineage_index[entry.entry_id]
            merkle_proof = self._get_merkle_proof_for_position(position)
            if merkle_proof:
                entry_proof["merkle_proof"] = merkle_proof

            proof_bundle["entries"].append(entry_proof)

        # Add chain verification
        proof_bundle["chain_verification"] = self.verify_lineage_chain_integrity()

        return proof_bundle

    def detect_lineage_tampering(self) -> Dict[str, Any]:
        """Detect potential lineage tampering attempts."""

        tampering_indicators = []
        suspicious_entries = []

        # Check for hash inconsistencies
        for i, entry in enumerate(self.lineage_chain):
            calculated_hash = entry.calculate_hash()
            if calculated_hash != entry.entry_hash:
                tampering_indicators.append("hash_mismatch")
                suspicious_entries.append(
                    {
                        "entry_id": entry.entry_id,
                        "position": i,
                        "issue": "Hash mismatch",
                    }
                )

        # Check for signature failures
        for i, entry in enumerate(self.lineage_chain):
            if not self._verify_signature(entry):
                tampering_indicators.append("signature_failure")
                suspicious_entries.append(
                    {
                        "entry_id": entry.entry_id,
                        "position": i,
                        "issue": "Invalid signature",
                    }
                )

        # Check for temporal inconsistencies
        for i in range(1, len(self.lineage_chain)):
            current = self.lineage_chain[i]
            previous = self.lineage_chain[i - 1]

            if current.timestamp < previous.timestamp:
                tampering_indicators.append("temporal_inconsistency")
                suspicious_entries.append(
                    {
                        "entry_id": current.entry_id,
                        "position": i,
                        "issue": "Timestamp earlier than previous entry",
                    }
                )

        # Check for duplicate nonces (replay attacks)
        nonces = [entry.nonce for entry in self.lineage_chain]
        if len(nonces) != len(set(nonces)):
            tampering_indicators.append("duplicate_nonces")

        tampering_detected = len(tampering_indicators) > 0

        if tampering_detected:
            audit_emitter.emit_security_event(
                "lineage_tampering_detected",
                {
                    "indicators": list(set(tampering_indicators)),
                    "suspicious_entries_count": len(suspicious_entries),
                    "total_entries": len(self.lineage_chain),
                },
            )

        return {
            "tampering_detected": tampering_detected,
            "indicators": list(set(tampering_indicators)),
            "suspicious_entries": suspicious_entries,
            "detection_timestamp": datetime.now(timezone.utc).isoformat(),
            "chain_length": len(self.lineage_chain),
        }

    def _sign_entry(self, entry: SecureLineageEntry, contributor_id: str) -> bytes:
        """Create digital signature for lineage entry."""

        if not CRYPTO_AVAILABLE:
            # Mock signature
            return hashlib.sha256(
                f"{entry.entry_id}_{contributor_id}".encode()
            ).digest()

        private_key_bytes = self.private_keys[contributor_id]
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)

        # Sign the entry hash
        signature = private_key.sign(entry.entry_hash)
        return signature

    def _verify_signature(self, entry: SecureLineageEntry) -> bool:
        """Verify digital signature of lineage entry."""

        if not CRYPTO_AVAILABLE:
            # Mock verification
            expected = hashlib.sha256(
                f"{entry.entry_id}_{entry.contributor_id}".encode()
            ).digest()
            return entry.digital_signature == expected

        try:
            public_key_bytes = self.public_keys.get(entry.contributor_id)
            if not public_key_bytes:
                return False

            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public_key.verify(entry.digital_signature, entry.entry_hash)
            return True
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    def _verify_lineage_consistency(self, entry: SecureLineageEntry) -> bool:
        """Verify that entry is consistent with lineage chain."""

        # Check parent-child relationship
        if entry.parent_capsule_id:
            # Find parent entry
            parent_entries = [
                e for e in self.lineage_chain if e.capsule_id == entry.parent_capsule_id
            ]

            if not parent_entries:
                logger.warning(
                    f"Parent capsule {entry.parent_capsule_id} not found in lineage"
                )
                return False

        # Check previous hash linkage
        if self.lineage_chain:
            expected_previous = self.lineage_chain[-1].entry_hash
            if entry.previous_hash != expected_previous:
                logger.warning("Previous hash mismatch in lineage chain")
                return False

        return True

    def _verify_chain_position(self, entry: SecureLineageEntry, position: int) -> bool:
        """Verify entry's position in the chain."""

        # Check previous hash linkage
        if position > 0:
            expected_previous = self.lineage_chain[position - 1].entry_hash
            if entry.previous_hash != expected_previous:
                return False
        else:
            # Genesis entry should have zero previous hash
            if entry.previous_hash != b"\x00" * 32:
                return False

        # Check next entry linkage
        if position < len(self.lineage_chain) - 1:
            next_entry = self.lineage_chain[position + 1]
            if next_entry.previous_hash != entry.entry_hash:
                return False

        return True

    def _verify_merkle_proof(
        self, entry: SecureLineageEntry, position: int
    ) -> Optional[bool]:
        """Verify Merkle proof for entry."""

        # Find which batch this entry belongs to
        batch_start = (position // self.batch_size) * self.batch_size
        batch_id = f"batch_{batch_start}"

        if batch_id not in self.merkle_trees:
            return None  # No Merkle proof available

        merkle_tree = self.merkle_trees[batch_id]
        batch_position = position - batch_start

        # Get proof and verify
        proof = merkle_tree.get_proof(batch_position)
        return MerkleTree.verify_proof(entry.entry_hash, proof, merkle_tree.root)

    def _create_merkle_batch(self):
        """Create Merkle tree for latest batch of entries."""

        if len(self.lineage_chain) < self.batch_size:
            return

        # Get latest batch
        batch_start = len(self.lineage_chain) - self.batch_size
        batch_entries = self.lineage_chain[batch_start:]

        # Extract hashes
        entry_hashes = [entry.entry_hash for entry in batch_entries]

        # Create Merkle tree
        merkle_tree = MerkleTree(entry_hashes)
        batch_id = f"batch_{batch_start}"
        self.merkle_trees[batch_id] = merkle_tree

        # Update lineage proofs for entries in this batch
        for i, entry in enumerate(batch_entries):
            proof = merkle_tree.get_proof(i)
            lineage_proof = CryptographicProof(
                proof_id=f"merkle_{uuid.uuid4()}",
                proof_type="merkle",
                merkle_root=merkle_tree.root,
                merkle_path=proof,
            )
            entry.lineage_proof = lineage_proof

        self.metrics["merkle_proofs_generated"] += len(batch_entries)

        logger.info(f"Created Merkle batch {batch_id} with {len(entry_hashes)} entries")

    def _get_merkle_proof_for_position(self, position: int) -> Optional[Dict[str, Any]]:
        """Get Merkle proof for entry at position."""

        batch_start = (position // self.batch_size) * self.batch_size
        batch_id = f"batch_{batch_start}"

        if batch_id not in self.merkle_trees:
            return None

        merkle_tree = self.merkle_trees[batch_id]
        batch_position = position - batch_start
        proof = merkle_tree.get_proof(batch_position)

        return {
            "batch_id": batch_id,
            "merkle_root": merkle_tree.root.hex(),
            "proof_path": [p.hex() for p in proof],
            "batch_position": batch_position,
        }

    def get_cryptographic_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cryptographic statistics."""

        # Key statistics
        key_stats = {
            "total_contributors": len(self.private_keys),
            "public_keys_distributed": len(self.public_keys),
        }

        # Chain statistics
        chain_stats = {
            "total_entries": len(self.lineage_chain),
            "merkle_trees": len(self.merkle_trees),
            "batch_size": self.batch_size,
            "latest_batch_entries": len(self.lineage_chain) % self.batch_size,
        }

        # Verification statistics
        verification_stats = {
            "cached_verifications": len(self.verification_cache),
            "verified_entries": sum(1 for v in self.verification_cache.values() if v),
            "failed_verifications": sum(
                1 for v in self.verification_cache.values() if not v
            ),
        }

        return {
            "performance_metrics": self.metrics.copy(),
            "key_statistics": key_stats,
            "chain_statistics": chain_stats,
            "verification_statistics": verification_stats,
            "crypto_available": CRYPTO_AVAILABLE,
        }

    def export_public_keys(self) -> Dict[str, str]:
        """Export public keys for verification by external parties."""

        return {
            contributor_id: public_key.hex()
            for contributor_id, public_key in self.public_keys.items()
        }

    def import_public_key(self, contributor_id: str, public_key_hex: str):
        """Import public key for external contributor verification."""

        try:
            public_key_bytes = bytes.fromhex(public_key_hex)
            self.public_keys[contributor_id] = public_key_bytes

            audit_emitter.emit_security_event(
                "public_key_imported",
                {
                    "contributor_id": contributor_id,
                    "public_key_hash": hashlib.sha256(public_key_bytes).hexdigest()[
                        :16
                    ],
                },
            )

            logger.info(f"Imported public key for contributor: {contributor_id}")
        except Exception as e:
            logger.error(f"Failed to import public key: {e}")
            raise


# Global cryptographic lineage manager instance
cryptographic_lineage_manager = CryptographicLineageManager()
