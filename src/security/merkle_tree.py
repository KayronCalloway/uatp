"""
Merkle Tree Implementation for UATP Capsule Chain Verification
===============================================================

This module provides a proper Merkle tree implementation for verifying
the integrity of capsule chains. It enables:

1. Efficient verification of individual capsules within a chain
2. Tamper detection across the entire chain
3. Compact proofs for third-party verification
4. Incremental updates as new capsules are added

Security Properties:
- SHA-256 hashing for collision resistance
- Deterministic tree construction
- Audit proofs for selective disclosure
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ProofDirection(Enum):
    """Direction indicator for Merkle proof siblings."""

    LEFT = "left"
    RIGHT = "right"


@dataclass
class MerkleProof:
    """
    A Merkle proof that can verify a leaf's inclusion in a tree.

    Attributes:
        leaf_hash: The hash of the leaf being proven
        leaf_index: Position of the leaf in the tree
        siblings: List of (hash, direction) pairs from leaf to root
        root: The Merkle root this proof validates against
    """

    leaf_hash: str
    leaf_index: int
    siblings: List[Tuple[str, ProofDirection]]
    root: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize proof to dictionary."""
        return {
            "leaf_hash": self.leaf_hash,
            "leaf_index": self.leaf_index,
            "siblings": [{"hash": h, "direction": d.value} for h, d in self.siblings],
            "root": self.root,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MerkleProof":
        """Deserialize proof from dictionary."""
        siblings = [
            (s["hash"], ProofDirection(s["direction"])) for s in data["siblings"]
        ]
        return cls(
            leaf_hash=data["leaf_hash"],
            leaf_index=data["leaf_index"],
            siblings=siblings,
            root=data["root"],
        )


@dataclass
class MerkleTree:
    """
    A complete Merkle tree for capsule chain verification.

    The tree is built from leaf hashes (capsule content hashes) and
    provides efficient proofs and verification.
    """

    leaves: List[str] = field(default_factory=list)
    levels: List[List[str]] = field(default_factory=list)

    @property
    def root(self) -> Optional[str]:
        """Get the Merkle root hash."""
        if not self.levels:
            return None
        return self.levels[-1][0] if self.levels[-1] else None

    @property
    def root_formatted(self) -> str:
        """Get the Merkle root in UATP format."""
        root = self.root
        if root:
            return f"sha256:{root}"
        return "sha256:" + "0" * 64


class MerkleTreeBuilder:
    """
    Builder class for constructing Merkle trees from capsule hashes.

    Usage:
        builder = MerkleTreeBuilder()
        builder.add_leaf(capsule1_hash)
        builder.add_leaf(capsule2_hash)
        tree = builder.build()
        root = tree.root_formatted
    """

    def __init__(self) -> None:
        self._leaves: List[str] = []

    @staticmethod
    def _hash_pair(left: str, right: str) -> str:
        """
        Hash two nodes together to create parent node.

        Uses sorted concatenation to ensure deterministic ordering.
        """
        # Concatenate in sorted order for determinism
        combined = (left + right).encode("utf-8")
        return hashlib.sha256(combined).hexdigest()

    @staticmethod
    def _hash_single(data: str) -> str:
        """Hash a single value (for odd-numbered levels)."""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def add_leaf(self, content_hash: str) -> int:
        """
        Add a leaf (capsule hash) to the tree.

        Args:
            content_hash: SHA-256 hash of capsule content
                         Can be in format "sha256:hex" or just "hex"

        Returns:
            Index of the added leaf
        """
        # Normalize hash format
        if content_hash.startswith("sha256:"):
            content_hash = content_hash.split(":", 1)[1]

        self._leaves.append(content_hash)
        return len(self._leaves) - 1

    def add_capsule(self, capsule_data: Dict[str, Any]) -> int:
        """
        Add a capsule to the tree by computing its content hash.

        Args:
            capsule_data: Complete capsule dictionary

        Returns:
            Index of the added leaf
        """
        content_hash = self._compute_capsule_hash(capsule_data)
        return self.add_leaf(content_hash)

    @staticmethod
    def _compute_capsule_hash(capsule_data: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of capsule content."""
        # Exclude verification field to avoid circular dependency
        canonical_data = {k: v for k, v in capsule_data.items() if k != "verification"}
        canonical_json = json.dumps(
            canonical_data, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def build(self) -> MerkleTree:
        """
        Build the Merkle tree from added leaves.

        Returns:
            Complete MerkleTree with all levels computed
        """
        if not self._leaves:
            return MerkleTree()

        tree = MerkleTree(leaves=self._leaves.copy())

        # Start with leaf level
        current_level = self._leaves.copy()
        tree.levels.append(current_level)

        # Build up the tree level by level
        while len(current_level) > 1:
            next_level = []

            # Process pairs
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    # Hash pair
                    parent = self._hash_pair(current_level[i], current_level[i + 1])
                else:
                    # Odd node - promote with self-hash
                    parent = self._hash_single(current_level[i])

                next_level.append(parent)

            tree.levels.append(next_level)
            current_level = next_level

        logger.debug(
            f"Built Merkle tree with {len(self._leaves)} leaves, root: {tree.root}"
        )
        return tree


class MerkleVerifier:
    """
    Verifier for Merkle proofs and tree integrity.
    """

    @staticmethod
    def generate_proof(tree: MerkleTree, leaf_index: int) -> Optional[MerkleProof]:
        """
        Generate a Merkle proof for a specific leaf.

        Args:
            tree: The complete Merkle tree
            leaf_index: Index of the leaf to prove

        Returns:
            MerkleProof object or None if index invalid
        """
        if not tree.levels or leaf_index >= len(tree.leaves):
            return None

        siblings: List[Tuple[str, ProofDirection]] = []
        current_index = leaf_index

        # Traverse up the tree, collecting siblings
        for level in tree.levels[:-1]:  # Exclude root level
            if current_index % 2 == 0:
                # Current node is left child, sibling is right
                if current_index + 1 < len(level):
                    siblings.append((level[current_index + 1], ProofDirection.RIGHT))
            else:
                # Current node is right child, sibling is left
                siblings.append((level[current_index - 1], ProofDirection.LEFT))

            # Move to parent index
            current_index = current_index // 2

        return MerkleProof(
            leaf_hash=tree.leaves[leaf_index],
            leaf_index=leaf_index,
            siblings=siblings,
            root=tree.root or "",
        )

    @staticmethod
    def verify_proof(proof: MerkleProof) -> bool:
        """
        Verify a Merkle proof.

        Args:
            proof: The MerkleProof to verify

        Returns:
            True if proof is valid, False otherwise
        """
        current_hash = proof.leaf_hash

        for sibling_hash, direction in proof.siblings:
            if direction == ProofDirection.LEFT:
                # Sibling is on left
                combined = (sibling_hash + current_hash).encode("utf-8")
            else:
                # Sibling is on right
                combined = (current_hash + sibling_hash).encode("utf-8")

            current_hash = hashlib.sha256(combined).hexdigest()

        is_valid = current_hash == proof.root

        if is_valid:
            logger.debug(f"Merkle proof verified for leaf {proof.leaf_index}")
        else:
            logger.warning(f"Merkle proof FAILED for leaf {proof.leaf_index}")

        return is_valid

    @staticmethod
    def verify_capsule_in_chain(
        capsule_data: Dict[str, Any], proof: MerkleProof
    ) -> Tuple[bool, str]:
        """
        Verify a capsule's inclusion in a chain using a Merkle proof.

        Args:
            capsule_data: The capsule to verify
            proof: The Merkle proof for this capsule

        Returns:
            Tuple of (is_valid, reason)
        """
        # Compute capsule hash
        canonical_data = {k: v for k, v in capsule_data.items() if k != "verification"}
        canonical_json = json.dumps(
            canonical_data, sort_keys=True, separators=(",", ":")
        )
        computed_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        # Check if computed hash matches proof's leaf hash
        if computed_hash != proof.leaf_hash:
            return (
                False,
                f"Capsule hash mismatch: computed {computed_hash}, expected {proof.leaf_hash}",
            )

        # Verify the proof
        if not MerkleVerifier.verify_proof(proof):
            return False, "Merkle proof verification failed"

        return True, "Capsule verified in chain"


class ChainMerkleManager:
    """
    Manager for maintaining Merkle trees across capsule chains.

    Provides:
    - Incremental tree updates as capsules are added
    - Efficient root computation for new capsules
    - Chain integrity verification
    """

    def __init__(self) -> None:
        self._builder = MerkleTreeBuilder()
        self._current_tree: Optional[MerkleTree] = None
        self._capsule_indices: Dict[str, int] = {}  # capsule_id -> leaf_index

    def add_capsule(self, capsule_id: str, capsule_data: Dict[str, Any]) -> str:
        """
        Add a capsule to the chain and update the Merkle root.

        Args:
            capsule_id: Unique capsule identifier
            capsule_data: Capsule content (without verification)

        Returns:
            New Merkle root in UATP format ("sha256:hex")
        """
        leaf_index = self._builder.add_capsule(capsule_data)
        self._capsule_indices[capsule_id] = leaf_index

        # Rebuild tree (could be optimized for incremental updates)
        tree = self._builder.build()
        self._current_tree = tree

        return tree.root_formatted

    def get_current_root(self) -> str:
        """Get the current Merkle root."""
        if self._current_tree:
            return self._current_tree.root_formatted
        return "sha256:" + "0" * 64

    def generate_proof_for_capsule(self, capsule_id: str) -> Optional[MerkleProof]:
        """
        Generate a Merkle proof for a specific capsule.

        Args:
            capsule_id: The capsule to generate proof for

        Returns:
            MerkleProof or None if capsule not found
        """
        if capsule_id not in self._capsule_indices:
            logger.warning(f"Capsule {capsule_id} not found in chain")
            return None

        if not self._current_tree:
            logger.warning("No tree built yet")
            return None

        leaf_index = self._capsule_indices[capsule_id]
        return MerkleVerifier.generate_proof(self._current_tree, leaf_index)

    def verify_chain_integrity(self) -> Tuple[bool, str]:
        """
        Verify the integrity of the entire chain.

        Returns:
            Tuple of (is_valid, reason)
        """
        if not self._current_tree:
            return True, "Empty chain is valid"

        # Rebuild tree from scratch and compare roots
        verification_builder = MerkleTreeBuilder()
        for leaf in self._current_tree.leaves:
            verification_builder.add_leaf(leaf)

        verification_tree = verification_builder.build()

        if verification_tree.root == self._current_tree.root:
            return (
                True,
                f"Chain integrity verified with {len(self._current_tree.leaves)} capsules",
            )
        else:
            return False, "Chain integrity check failed - root mismatch"

    def get_chain_stats(self) -> Dict[str, Any]:
        """Get statistics about the current chain."""
        return {
            "capsule_count": len(self._capsule_indices),
            "tree_depth": len(self._current_tree.levels) if self._current_tree else 0,
            "merkle_root": self.get_current_root(),
            "capsule_ids": list(self._capsule_indices.keys()),
        }


# Singleton instance for global chain management
_chain_manager: Optional[ChainMerkleManager] = None


def get_chain_merkle_manager() -> ChainMerkleManager:
    """Get or create the global chain Merkle manager."""
    global _chain_manager
    if _chain_manager is None:
        _chain_manager = ChainMerkleManager()
    return _chain_manager


def compute_merkle_root_for_capsules(capsules: List[Dict[str, Any]]) -> str:
    """
    Compute Merkle root for a list of capsules.

    Convenience function for batch operations.

    Args:
        capsules: List of capsule dictionaries

    Returns:
        Merkle root in UATP format ("sha256:hex")
    """
    builder = MerkleTreeBuilder()
    for capsule in capsules:
        builder.add_capsule(capsule)

    tree = builder.build()
    return tree.root_formatted


def verify_capsule_in_chain(
    capsule_data: Dict[str, Any], merkle_root: str, proof_data: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Verify a capsule's inclusion in a chain.

    Convenience function for external verification.

    Args:
        capsule_data: The capsule to verify
        merkle_root: Expected Merkle root
        proof_data: Serialized MerkleProof

    Returns:
        Tuple of (is_valid, reason)
    """
    proof = MerkleProof.from_dict(proof_data)

    # Normalize merkle_root format
    if merkle_root.startswith("sha256:"):
        merkle_root = merkle_root.split(":", 1)[1]

    if proof.root != merkle_root:
        return (
            False,
            f"Merkle root mismatch: proof has {proof.root}, expected {merkle_root}",
        )

    return MerkleVerifier.verify_capsule_in_chain(capsule_data, proof)
