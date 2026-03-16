"""
Merkle Tree Implementation for Audit Log Verification

Provides efficient batch verification of audit logs using Merkle trees.
Instead of verifying each entry individually, a Merkle tree allows verification
of large batches with a single root hash.

Key Features:
- O(log n) verification time for individual entries
- Compact proof-of-inclusion
- Efficient batch verification
- Tamper-evident structure

Usage:
    from src.audit.merkle_tree import MerkleTree

    # Build tree from audit entries
    tree = MerkleTree(audit_entry_hashes)

    # Get root hash for verification
    root = tree.get_root()

    # Generate proof for specific entry
    proof = tree.generate_proof(entry_index)

    # Verify entry with proof
    is_valid = MerkleTree.verify_proof(entry_hash, proof, root)
"""

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class MerkleProof:
    """Proof of inclusion for a specific entry in Merkle tree"""

    leaf_index: int
    leaf_hash: str
    sibling_hashes: List[Tuple[str, str]]  # (hash, position: 'left' or 'right')
    root_hash: str


class MerkleNode:
    """Node in Merkle tree"""

    def __init__(
        self,
        hash_value: str,
        left: Optional["MerkleNode"] = None,
        right: Optional["MerkleNode"] = None,
    ):
        self.hash_value = hash_value
        self.left = left
        self.right = right

    def is_leaf(self) -> bool:
        """Check if this node is a leaf"""
        return self.left is None and self.right is None


class MerkleTree:
    """
    Merkle Tree for efficient audit log verification.

    A Merkle tree is a binary tree where:
    - Leaf nodes contain hashes of audit entries
    - Internal nodes contain hashes of their children
    - Root node contains hash of entire tree

    Benefits:
    - Verify single entry with O(log n) proof size
    - Detect tampering in any entry
    - Efficient for large audit logs
    """

    def __init__(self, leaf_hashes: List[str]):
        """
        Build Merkle tree from list of leaf hashes.

        Args:
            leaf_hashes: List of hex-encoded hashes (audit entry hashes)
        """
        if not leaf_hashes:
            raise ValueError("Cannot build Merkle tree from empty list")

        self.leaf_hashes = leaf_hashes.copy()
        self.root = self._build_tree(leaf_hashes)

    @staticmethod
    def _hash_pair(left: str, right: str) -> str:
        """
        Hash two child hashes to create parent hash.

        Args:
            left: Left child hash (hex-encoded)
            right: Right child hash (hex-encoded)

        Returns:
            Parent hash (hex-encoded)
        """
        # Concatenate and hash
        combined = left + right
        hash_obj = hashlib.sha256()
        hash_obj.update(combined.encode("utf-8"))
        return hash_obj.hexdigest()

    def _build_tree(self, hashes: List[str]) -> MerkleNode:
        """
        Recursively build Merkle tree from list of hashes.

        Args:
            hashes: List of hex-encoded hashes

        Returns:
            Root node of tree
        """
        # Base case: single hash becomes leaf node
        if len(hashes) == 1:
            return MerkleNode(hashes[0])

        # If odd number of hashes, duplicate last hash
        if len(hashes) % 2 != 0:
            hashes = hashes + [hashes[-1]]

        # Build parent level
        parent_hashes = []
        for i in range(0, len(hashes), 2):
            left_hash = hashes[i]
            right_hash = hashes[i + 1]
            parent_hash = self._hash_pair(left_hash, right_hash)
            parent_hashes.append(parent_hash)

        # Recursively build tree
        return self._build_tree_with_children(hashes, parent_hashes)

    def _build_tree_with_children(
        self, leaf_hashes: List[str], parent_hashes: List[str]
    ) -> MerkleNode:
        """
        Build tree level by level, maintaining parent-child relationships.

        Args:
            leaf_hashes: Current level hashes
            parent_hashes: Parent level hashes

        Returns:
            Root node of tree
        """
        # Base case: single parent hash becomes root
        if len(parent_hashes) == 1:
            # Build leaf nodes
            nodes = [MerkleNode(h) for h in leaf_hashes]

            # Build parent node
            if len(nodes) % 2 != 0:
                nodes.append(nodes[-1])  # Duplicate if odd

            root = MerkleNode(
                parent_hashes[0],
                left=nodes[0] if len(nodes) > 0 else None,
                right=nodes[1] if len(nodes) > 1 else None,
            )
            return root

        # Build nodes for current level
        nodes = []
        for i in range(0, len(leaf_hashes), 2):
            left_hash = leaf_hashes[i]
            right_hash = leaf_hashes[i + 1] if i + 1 < len(leaf_hashes) else left_hash

            left_node = MerkleNode(left_hash)
            right_node = MerkleNode(right_hash)
            parent_hash = parent_hashes[i // 2]

            parent_node = MerkleNode(parent_hash, left=left_node, right=right_node)
            nodes.append(parent_node)

        # If odd number of parents, build next level
        if len(parent_hashes) % 2 != 0:
            parent_hashes = parent_hashes + [parent_hashes[-1]]

        # Build next level
        next_parent_hashes = []
        for i in range(0, len(parent_hashes), 2):
            left_hash = parent_hashes[i]
            right_hash = parent_hashes[i + 1]
            next_parent_hash = self._hash_pair(left_hash, right_hash)
            next_parent_hashes.append(next_parent_hash)

        # Recursively build higher levels
        if len(next_parent_hashes) == 1:
            # Final root level
            if len(nodes) % 2 != 0:
                nodes.append(nodes[-1])

            return MerkleNode(
                next_parent_hashes[0],
                left=nodes[0],
                right=nodes[1] if len(nodes) > 1 else nodes[0],
            )
        else:
            return self._build_tree_with_children(parent_hashes, next_parent_hashes)

    def get_root(self) -> str:
        """Get root hash of Merkle tree"""
        return self.root.hash_value

    def generate_proof(self, leaf_index: int) -> MerkleProof:
        """
        Generate proof of inclusion for specific leaf.

        Args:
            leaf_index: Index of leaf in original list

        Returns:
            Merkle proof containing sibling hashes needed for verification

        Raises:
            ValueError: If leaf_index is out of range
        """
        if leaf_index < 0 or leaf_index >= len(self.leaf_hashes):
            raise ValueError(f"Leaf index {leaf_index} out of range")

        leaf_hash = self.leaf_hashes[leaf_index]

        # Generate sibling hashes by traversing tree
        sibling_hashes = self._collect_sibling_hashes(leaf_index)

        return MerkleProof(
            leaf_index=leaf_index,
            leaf_hash=leaf_hash,
            sibling_hashes=sibling_hashes,
            root_hash=self.root.hash_value,
        )

    def _collect_sibling_hashes(self, leaf_index: int) -> List[Tuple[str, str]]:
        """
        Collect sibling hashes needed to verify a specific leaf.

        Args:
            leaf_index: Index of leaf

        Returns:
            List of (sibling_hash, position) tuples
        """
        siblings = []
        current_level = self.leaf_hashes.copy()

        # Add duplicates if odd length
        if len(current_level) % 2 != 0:
            current_level.append(current_level[-1])

        current_index = leaf_index

        while len(current_level) > 1:
            # Get sibling index
            if current_index % 2 == 0:
                # Current is left child, sibling is right
                sibling_index = current_index + 1
                position = "right"
            else:
                # Current is right child, sibling is left
                sibling_index = current_index - 1
                position = "left"

            sibling_hash = current_level[sibling_index]
            siblings.append((sibling_hash, position))

            # Move to parent level
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1]
                parent = self._hash_pair(left, right)
                next_level.append(parent)

            current_level = next_level
            current_index = current_index // 2

        return siblings

    @staticmethod
    def verify_proof(leaf_hash: str, proof: MerkleProof) -> bool:
        """
        Verify that a leaf is included in the Merkle tree.

        Args:
            leaf_hash: Hash of the leaf to verify
            proof: Merkle proof from generate_proof()

        Returns:
            True if proof is valid, False otherwise
        """
        # Start with leaf hash
        current_hash = leaf_hash

        # Traverse up the tree using sibling hashes
        for sibling_hash, position in proof.sibling_hashes:
            if position == "left":
                # Sibling is on the left
                current_hash = MerkleTree._hash_pair(sibling_hash, current_hash)
            else:
                # Sibling is on the right
                current_hash = MerkleTree._hash_pair(current_hash, sibling_hash)

        # Final hash should match root
        return current_hash == proof.root_hash

    def get_proof_size(self, num_entries: int) -> int:
        """
        Calculate proof size for a tree with num_entries.

        Args:
            num_entries: Number of entries in tree

        Returns:
            Number of hashes needed in proof (O(log n))
        """
        import math

        return math.ceil(math.log2(num_entries))


class AuditLogMerkleTree:
    """
    Specialized Merkle tree for audit log verification.

    Extends basic Merkle tree with audit-specific features:
    - Batch verification of multiple entries
    - Incremental tree updates
    - Efficient range proofs
    """

    def __init__(self, audit_entry_hashes: List[str]):
        """
        Create Merkle tree from audit entry hashes.

        Args:
            audit_entry_hashes: List of audit entry hashes (in sequence order)
        """
        self.tree = MerkleTree(audit_entry_hashes)
        self.entry_count = len(audit_entry_hashes)

    def verify_entry(self, entry_index: int, entry_hash: str) -> bool:
        """
        Verify a single audit entry is in the tree.

        Args:
            entry_index: Sequence number of entry
            entry_hash: Hash of the entry

        Returns:
            True if entry is valid and in tree
        """
        proof = self.tree.generate_proof(entry_index)
        return MerkleTree.verify_proof(entry_hash, proof)

    def verify_batch(self, entries: List[Tuple[int, str]]) -> List[bool]:
        """
        Verify multiple audit entries efficiently.

        Args:
            entries: List of (entry_index, entry_hash) tuples

        Returns:
            List of verification results (True/False for each entry)
        """
        results = []
        for entry_index, entry_hash in entries:
            is_valid = self.verify_entry(entry_index, entry_hash)
            results.append(is_valid)

        return results

    def get_root_hash(self) -> str:
        """Get root hash for this audit log batch"""
        return self.tree.get_root()

    def generate_compact_proof(self, entry_indices: List[int]) -> Dict:
        """
        Generate compact proof for multiple entries.

        Instead of generating separate proofs for each entry (redundant),
        generate a single compact proof containing shared sibling hashes.

        Args:
            entry_indices: List of entry indices to prove

        Returns:
            Compact proof dictionary
        """
        # Generate individual proofs
        proofs = [self.tree.generate_proof(idx) for idx in entry_indices]

        # Combine and deduplicate sibling hashes
        all_siblings = {}
        for proof in proofs:
            for sibling_hash, position in proof.sibling_hashes:
                all_siblings[sibling_hash] = position

        return {
            "root_hash": self.tree.get_root(),
            "entry_indices": entry_indices,
            "shared_siblings": list(all_siblings.items()),
            "entry_hashes": [self.tree.leaf_hashes[idx] for idx in entry_indices],
        }
