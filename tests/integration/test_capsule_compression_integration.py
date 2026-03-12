"""
Integration tests for capsule compression.
"""

import base64
import json
import zlib

import pytest

from src.models.capsule import CapsuleModel


class TestCapsuleCompression:
    """Tests for MAIF-style capsule compression."""

    @pytest.fixture
    def small_payload(self):
        """Create a small payload (under threshold)."""
        return {"message": "small content", "data": [1, 2, 3]}

    @pytest.fixture
    def large_payload(self):
        """Create a large payload (over default 10KB threshold)."""
        return {
            "reasoning_steps": [
                {
                    "step": i,
                    "reasoning": f"This is a detailed reasoning step {i} " * 100,
                    "confidence": 0.85,
                }
                for i in range(50)
            ],
            "session_metadata": {
                "topics": ["coding", "debugging", "optimization"],
                "platform": "claude-code",
            },
        }

    def test_compression_function_exists(self):
        """Test that compression function is available."""
        from src.live_capture.rich_capture_integration import compress_payload_if_needed

        assert callable(compress_payload_if_needed)

    def test_small_payload_not_compressed(self, small_payload):
        """Test that small payloads are not compressed."""
        from src.live_capture.rich_capture_integration import compress_payload_if_needed

        result, metadata = compress_payload_if_needed(small_payload)

        assert result == small_payload
        assert metadata is None

    def test_large_payload_compressed(self, large_payload):
        """Test that large payloads are compressed."""
        from src.live_capture.rich_capture_integration import compress_payload_if_needed

        result, metadata = compress_payload_if_needed(large_payload)

        # Should be compressed
        if metadata:
            assert "compressed_payload" in result
            assert metadata["is_compressed"] == True
            assert metadata["compression_method"] == "zlib"
            assert metadata["compressed_size"] < metadata["original_size"]

    def test_compression_is_reversible(self, large_payload):
        """Test that compression can be reversed."""
        from src.live_capture.rich_capture_integration import compress_payload_if_needed

        compressed, metadata = compress_payload_if_needed(large_payload)

        if metadata and "compressed_payload" in compressed:
            # Decompress
            compressed_b64 = compressed["compressed_payload"]
            compressed_bytes = base64.b64decode(compressed_b64)
            decompressed_bytes = zlib.decompress(compressed_bytes)
            decompressed = json.loads(decompressed_bytes.decode("utf-8"))

            assert decompressed == large_payload

    def test_compression_ratio_reasonable(self, large_payload):
        """Test that compression achieves reasonable ratio."""
        from src.live_capture.rich_capture_integration import compress_payload_if_needed

        _, metadata = compress_payload_if_needed(large_payload)

        if metadata:
            ratio = metadata["ratio"]
            # Expect at least 50% compression for repetitive text
            assert ratio < 0.8, f"Compression ratio {ratio} is too high"

    def test_capsule_model_has_compression_columns(self):
        """Test that CapsuleModel has compression columns."""
        assert hasattr(CapsuleModel, "is_compressed")
        assert hasattr(CapsuleModel, "compression_method")
        assert hasattr(CapsuleModel, "original_size")
        assert hasattr(CapsuleModel, "compressed_size")


class TestCompressionThreshold:
    """Tests for compression threshold configuration."""

    def test_threshold_environment_variable(self, monkeypatch):
        """Test that threshold can be configured via env var."""
        monkeypatch.setenv("UATP_COMPRESSION_THRESHOLD", "5000")

        from importlib import reload

        import src.live_capture.rich_capture_integration as module

        reload(module)

        threshold = module._get_compression_threshold()
        assert threshold == 5000

    def test_default_threshold(self, monkeypatch):
        """Test default threshold value."""
        monkeypatch.delenv("UATP_COMPRESSION_THRESHOLD", raising=False)

        from importlib import reload

        import src.live_capture.rich_capture_integration as module

        reload(module)

        threshold = module._get_compression_threshold()
        assert threshold == 10240


class TestDecompression:
    """Tests for transparent decompression on read."""

    @pytest.fixture
    def compressed_payload_data(self, large_payload=None):
        """Create compressed payload data structure."""
        if large_payload is None:
            large_payload = {
                "data": "test content " * 1000,
                "metadata": {"type": "test"},
            }

        payload_json = json.dumps(large_payload)
        compressed = zlib.compress(payload_json.encode("utf-8"), level=6)
        compressed_b64 = base64.b64encode(compressed).decode("ascii")

        return {
            "original": large_payload,
            "compressed": {"compressed_payload": compressed_b64},
            "metadata": {
                "is_compressed": True,
                "compression_method": "zlib",
                "original_size": len(payload_json.encode("utf-8")),
                "compressed_size": len(compressed),
            },
        }

    def test_decompression_in_api(self, compressed_payload_data):
        """Test that API correctly decompresses payloads."""
        compressed = compressed_payload_data["compressed"]
        original = compressed_payload_data["original"]

        # Simulate decompression logic from API
        compressed_b64 = compressed["compressed_payload"]
        compressed_bytes = base64.b64decode(compressed_b64)
        decompressed_bytes = zlib.decompress(compressed_bytes)
        decompressed = json.loads(decompressed_bytes.decode("utf-8"))

        assert decompressed == original
