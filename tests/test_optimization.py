"""
Tests for the capsule optimization system.
"""

from datetime import datetime, timezone

from src.capsule_schema import (
    CapsuleStatus,
    ReasoningStep,
    ReasoningTraceCapsule,
    ReasoningTracePayload,
    Verification,
)
from src.optimization.capsule_compression import (
    CapsuleCompressor,
    CapsuleDeduplicator,
    CapsulePruner,
    CompressionMethod,
    PruningStrategy,
    optimization_engine,
)


def test_capsule_compression():
    """Test capsule compression functionality."""

    # Create a test capsule
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(
            steps=[
                ReasoningStep(
                    content="This is a test step with some content that should compress well",
                    step_type="observation",
                    metadata={"test": "data"},
                ),
                ReasoningStep(
                    content="Another test step with similar content that should compress well",
                    step_type="conclusion",
                    metadata={"test": "data"},
                ),
            ]
        ),
    )

    compressor = CapsuleCompressor()

    # Test compression
    result = compressor.compress_capsule(capsule, CompressionMethod.ZLIB)

    assert result.original_size > 0
    assert result.compressed_size > 0
    assert result.compression_ratio <= 1.0
    assert result.method == CompressionMethod.ZLIB

    # Test decompression
    decompressed = compressor.decompress_capsule(capsule.capsule_id)
    assert decompressed is not None
    assert decompressed["capsule_id"] == capsule.capsule_id
    assert decompressed["capsule_type"] == "reasoning_trace"


def test_capsule_deduplication():
    """Test capsule deduplication functionality."""

    # Create similar capsules
    capsule1 = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(
            steps=[
                ReasoningStep(
                    content="This is identical content",
                    step_type="observation",
                    metadata={},
                )
            ]
        ),
    )

    capsule2 = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(
            steps=[
                ReasoningStep(
                    content="This is identical content",
                    step_type="observation",
                    metadata={},
                )
            ]
        ),
    )

    deduplicator = CapsuleDeduplicator()

    # Analyze first capsule
    analysis1 = deduplicator.analyze_duplicates(capsule1)
    assert analysis1.capsule_id == capsule1.capsule_id
    assert not analysis1.has_duplicates()  # No duplicates yet

    # Analyze second capsule (should find duplicate)
    analysis2 = deduplicator.analyze_duplicates(capsule2)
    assert analysis2.capsule_id == capsule2.capsule_id
    assert analysis2.has_duplicates()  # Should find duplicate


def test_capsule_pruning():
    """Test capsule pruning functionality."""

    # Create an old capsule
    old_capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc) - timedelta(days=500),  # Very old
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(steps=[]),
    )

    pruner = CapsulePruner()

    # Test age-based pruning
    decision = pruner.should_prune_capsule(
        old_capsule, strategy=PruningStrategy.AGE_BASED
    )
    assert decision.capsule_id == old_capsule.capsule_id
    assert decision.strategy == PruningStrategy.AGE_BASED
    assert decision.should_prune  # Should prune old capsule

    # Test usage-based pruning
    usage_stats = {
        "usage_count": 2,
        "last_accessed": datetime.now(timezone.utc) - timedelta(days=200),
    }
    decision = pruner.should_prune_capsule(
        old_capsule, usage_stats, PruningStrategy.USAGE_BASED
    )
    assert decision.strategy == PruningStrategy.USAGE_BASED
    assert decision.should_prune  # Low usage, old access


def test_optimization_engine():
    """Test the complete optimization engine."""

    # Create test capsule
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(
            steps=[
                ReasoningStep(
                    content="Test content for optimization",
                    step_type="observation",
                    metadata={},
                )
            ]
        ),
    )

    # Optimize capsule
    result = optimization_engine.optimize_capsule(capsule)

    assert result["capsule_id"] == capsule.capsule_id
    assert "optimization_timestamp" in result
    assert "actions_taken" in result
    assert isinstance(result["actions_taken"], list)

    # Check statistics
    stats = optimization_engine.get_optimization_statistics()
    assert "processing_stats" in stats
    assert "compression_stats" in stats
    assert "efficiency_metrics" in stats


def test_batch_optimization():
    """Test batch optimization of multiple capsules."""

    capsules = []
    for i in range(3):
        capsule = ReasoningTraceCapsule(
            capsule_id=f"batch_test_{i}",
            version="7.0",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.ACTIVE,
            verification=Verification(),
            reasoning_trace=ReasoningTracePayload(
                steps=[
                    ReasoningStep(
                        content=f"Batch test content {i}",
                        step_type="observation",
                        metadata={},
                    )
                ]
            ),
        )
        capsules.append(capsule)

    # Batch optimize
    batch_result = optimization_engine.batch_optimize(capsules)

    assert batch_result["total_capsules"] == 3
    assert len(batch_result["optimization_results"]) == 3
    assert "processing_time" in batch_result
    assert "batch_statistics" in batch_result


if __name__ == "__main__":
    test_capsule_compression()
    test_capsule_deduplication()
    test_capsule_pruning()
    test_optimization_engine()
    test_batch_optimization()
    print("[OK] All optimization tests passed!")
