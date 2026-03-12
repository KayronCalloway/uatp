"""
Unit tests for Merkle Tree implementation.
"""

import pytest

from src.audit.merkle_tree import (
    AuditLogMerkleTree,
    MerkleNode,
    MerkleProof,
    MerkleTree,
)


class TestMerkleNode:
    """Tests for MerkleNode."""

    def test_leaf_node(self):
        """Test leaf node detection."""
        leaf = MerkleNode("abc123")
        assert leaf.is_leaf() is True

    def test_internal_node(self):
        """Test internal node detection."""
        left = MerkleNode("left")
        right = MerkleNode("right")
        parent = MerkleNode("parent", left=left, right=right)

        assert parent.is_leaf() is False
        assert parent.left == left
        assert parent.right == right


class TestMerkleTree:
    """Tests for MerkleTree."""

    def test_create_single_leaf(self):
        """Test tree with single leaf."""
        tree = MerkleTree(["abc123"])

        assert tree.get_root() == "abc123"

    def test_create_two_leaves(self):
        """Test tree with two leaves."""
        leaves = ["hash1", "hash2"]
        tree = MerkleTree(leaves)

        root = tree.get_root()
        expected = MerkleTree._hash_pair("hash1", "hash2")

        assert root == expected

    def test_create_power_of_two_leaves(self):
        """Test tree with 4 leaves (power of 2)."""
        leaves = ["a", "b", "c", "d"]
        tree = MerkleTree(leaves)

        # Build expected tree
        ab = MerkleTree._hash_pair("a", "b")
        cd = MerkleTree._hash_pair("c", "d")
        root = MerkleTree._hash_pair(ab, cd)

        assert tree.get_root() == root

    def test_create_odd_leaves(self):
        """Test tree with odd number of leaves."""
        leaves = ["a", "b", "c"]
        tree = MerkleTree(leaves)

        # With odd leaves, last is duplicated
        ab = MerkleTree._hash_pair("a", "b")
        cc = MerkleTree._hash_pair("c", "c")
        root = MerkleTree._hash_pair(ab, cc)

        assert tree.get_root() == root

    def test_empty_leaves_raises(self):
        """Test that empty list raises error."""
        with pytest.raises(ValueError, match="Cannot build Merkle tree from empty"):
            MerkleTree([])

    def test_generate_proof(self):
        """Test proof generation."""
        leaves = ["a", "b", "c", "d"]
        tree = MerkleTree(leaves)

        proof = tree.generate_proof(0)

        assert proof.leaf_index == 0
        assert proof.leaf_hash == "a"
        assert proof.root_hash == tree.get_root()
        assert len(proof.sibling_hashes) > 0

    def test_generate_proof_invalid_index(self):
        """Test proof generation with invalid index."""
        tree = MerkleTree(["a", "b"])

        with pytest.raises(ValueError, match="out of range"):
            tree.generate_proof(5)

        with pytest.raises(ValueError, match="out of range"):
            tree.generate_proof(-1)

    def test_verify_proof_valid(self):
        """Test proof verification succeeds for valid proof."""
        leaves = ["a", "b", "c", "d"]
        tree = MerkleTree(leaves)

        for i in range(len(leaves)):
            proof = tree.generate_proof(i)
            is_valid = MerkleTree.verify_proof(leaves[i], proof)
            assert is_valid is True

    def test_verify_proof_invalid_hash(self):
        """Test proof verification fails for wrong hash."""
        leaves = ["a", "b", "c", "d"]
        tree = MerkleTree(leaves)

        proof = tree.generate_proof(0)
        is_valid = MerkleTree.verify_proof("wrong_hash", proof)

        assert is_valid is False

    def test_verify_proof_tampered_root(self):
        """Test proof verification fails with tampered root."""
        leaves = ["a", "b", "c", "d"]
        tree = MerkleTree(leaves)

        proof = tree.generate_proof(0)
        # Tamper with root
        tampered_proof = MerkleProof(
            leaf_index=proof.leaf_index,
            leaf_hash=proof.leaf_hash,
            sibling_hashes=proof.sibling_hashes,
            root_hash="tampered_root",
        )

        is_valid = MerkleTree.verify_proof("a", tampered_proof)
        assert is_valid is False

    def test_hash_pair_deterministic(self):
        """Test that hash_pair is deterministic."""
        hash1 = MerkleTree._hash_pair("left", "right")
        hash2 = MerkleTree._hash_pair("left", "right")

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex

    def test_hash_pair_order_matters(self):
        """Test that hash_pair order matters."""
        hash1 = MerkleTree._hash_pair("a", "b")
        hash2 = MerkleTree._hash_pair("b", "a")

        assert hash1 != hash2

    def test_get_proof_size(self):
        """Test proof size calculation."""
        tree = MerkleTree(["a"] * 16)

        # For 16 entries, log2(16) = 4
        assert tree.get_proof_size(16) == 4
        assert tree.get_proof_size(8) == 3
        assert tree.get_proof_size(1000) == 10  # ceil(log2(1000))


class TestAuditLogMerkleTree:
    """Tests for AuditLogMerkleTree."""

    def test_create_audit_tree(self):
        """Test creating audit-specific tree."""
        hashes = ["entry1", "entry2", "entry3"]
        audit_tree = AuditLogMerkleTree(hashes)

        assert audit_tree.entry_count == 3
        assert len(audit_tree.get_root_hash()) == 64

    def test_verify_entry(self):
        """Test single entry verification."""
        hashes = ["entry1", "entry2", "entry3", "entry4"]
        audit_tree = AuditLogMerkleTree(hashes)

        assert audit_tree.verify_entry(0, "entry1") is True
        assert audit_tree.verify_entry(1, "entry2") is True
        assert audit_tree.verify_entry(0, "wrong") is False

    def test_verify_batch(self):
        """Test batch verification."""
        hashes = ["a", "b", "c", "d"]
        audit_tree = AuditLogMerkleTree(hashes)

        entries = [
            (0, "a"),
            (1, "b"),
            (2, "wrong"),
            (3, "d"),
        ]

        results = audit_tree.verify_batch(entries)

        assert results == [True, True, False, True]

    def test_generate_compact_proof(self):
        """Test compact proof generation."""
        hashes = ["a", "b", "c", "d", "e", "f", "g", "h"]
        audit_tree = AuditLogMerkleTree(hashes)

        compact = audit_tree.generate_compact_proof([0, 1, 2])

        assert compact["root_hash"] == audit_tree.get_root_hash()
        assert compact["entry_indices"] == [0, 1, 2]
        assert compact["entry_hashes"] == ["a", "b", "c"]
        assert len(compact["shared_siblings"]) > 0
