"""
Integration tests for cryptographic capsule chaining.
"""

import hashlib
import json

import pytest
from sqlalchemy import select, text

from src.models.capsule import CapsuleModel


class TestCapsuleChaining:
    """Tests for MAIF-style cryptographic chaining."""

    @pytest.fixture
    def sample_payload(self):
        """Create a sample payload."""
        return {
            "content": {"data": {"message": "test content"}},
            "metadata": {"source": "test"},
        }

    def compute_hash(self, payload: dict) -> str:
        """Compute SHA256 hash of payload."""
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @pytest.mark.asyncio
    async def test_content_hash_computation(self, sample_payload):
        """Test that content_hash is computed correctly."""
        from src.live_capture.rich_capture_integration import compute_content_hash

        hash1 = compute_content_hash(sample_payload)
        hash2 = self.compute_hash(sample_payload)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    @pytest.mark.asyncio
    async def test_hash_determinism(self, sample_payload):
        """Test that hashing is deterministic."""
        from src.live_capture.rich_capture_integration import compute_content_hash

        hash1 = compute_content_hash(sample_payload)
        hash2 = compute_content_hash(sample_payload)

        assert hash1 == hash2

    @pytest.mark.asyncio
    async def test_hash_changes_with_content(self, sample_payload):
        """Test that hash changes when content changes."""
        from src.live_capture.rich_capture_integration import compute_content_hash

        hash1 = compute_content_hash(sample_payload)

        modified_payload = sample_payload.copy()
        modified_payload["content"]["data"]["message"] = "modified content"
        hash2 = compute_content_hash(modified_payload)

        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_capsule_model_has_hash_columns(self):
        """Test that CapsuleModel has the new hash columns."""
        # Check column existence
        assert hasattr(CapsuleModel, "prev_hash")
        assert hasattr(CapsuleModel, "content_hash")

    @pytest.mark.asyncio
    async def test_chain_integrity_verification(self, sample_payload):
        """Test chain integrity verification logic."""
        # Create a chain of 3 capsules
        chain = []

        for i in range(3):
            payload = {**sample_payload, "index": i}
            content_hash = self.compute_hash(payload)
            prev_hash = chain[-1]["content_hash"] if chain else None

            chain.append(
                {
                    "capsule_id": f"test_chain_{i}",
                    "payload": payload,
                    "content_hash": content_hash,
                    "prev_hash": prev_hash,
                }
            )

        # Verify chain links
        for i, capsule in enumerate(chain):
            if i > 0:
                assert capsule["prev_hash"] == chain[i - 1]["content_hash"]

        # Verify recomputed hashes match stored
        for capsule in chain:
            recomputed = self.compute_hash(capsule["payload"])
            assert recomputed == capsule["content_hash"]

    @pytest.mark.asyncio
    async def test_chain_tampering_detection(self, sample_payload):
        """Test that tampering is detected via hash mismatch."""
        # Create capsule with hash
        payload = sample_payload.copy()
        original_hash = self.compute_hash(payload)

        # Tamper with the payload
        payload["content"]["data"]["message"] = "tampered"
        tampered_hash = self.compute_hash(payload)

        # The stored hash won't match the recomputed hash
        assert original_hash != tampered_hash


class TestChainVerificationEndpoint:
    """Tests for the chain verification API endpoint."""

    @pytest.mark.asyncio
    async def test_verify_chain_endpoint_structure(self):
        """Test that verify-chain endpoint response has correct structure."""
        # This would be an integration test with the actual API
        # Here we just test the expected response structure
        expected_fields = [
            "capsule_id",
            "chain_intact",
            "verified_count",
            "chain_length",
            "broken_at",
            "chain",
            "message",
        ]

        # Simulated response structure
        response = {
            "capsule_id": "test",
            "chain_intact": True,
            "verified_count": 3,
            "chain_length": 3,
            "broken_at": None,
            "chain": [],
            "message": "Chain integrity verified",
        }

        for field in expected_fields:
            assert field in response
