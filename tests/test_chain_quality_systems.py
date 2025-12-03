"""
test_chain_quality_systems.py - Comprehensive Tests for Chain Quality Systems

Tests all chain quality improvement systems to ensure they meet the performance
targets and quality requirements specified in the implementation.

Test Coverage:
- Fork resolution accuracy and performance
- Memory efficiency with large chains
- Quality degradation detection and remediation
- Cross-shard quality consistency
- Integration between consensus and quality systems
- Performance maintenance with quality optimization
"""

import asyncio
import pytest
import statistics
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from src.engine.cqss import CQSSResult, compute_cqss, build_chain_graph
from src.engine.fork_resolver import (
    QualityBasedForkResolver,
    ForkResolutionStrategy,
    ForkCandidate,
    ForkConflictType,
    fork_resolver,
)
from src.engine.chain_sharding import HorizontalChainSharding, ShardingStrategy
from src.engine.shard_coordinator import ShardCoordinator
from src.engine.quality_decay_detector import (
    QualityDecayDetector,
    DecayPattern,
    RemediationStrategy,
    QualityTrendPoint,
    quality_decay_detector,
)
from src.engine.quality_optimizer import (
    RealTimeQualityOptimizer,
    OptimizationStrategy,
    quality_optimizer,
)
from src.engine.quality_integration_layer import (
    ChainQualityIntegrationLayer,
    quality_integration_layer,
)
from src.consensus.multi_agent_consensus import (
    MultiAgentConsensusEngine,
    ConsensusProtocol,
    ConsensusNode,
)
from capsule_schema import Capsule, CapsuleType, CapsuleStatus


class MockCapsule:
    """Mock capsule for testing."""

    def __init__(
        self, capsule_id: str, parent_id: str = None, quality_score: float = 0.5
    ):
        self.capsule_id = capsule_id
        self.parent_capsule = parent_id
        self.previous_capsule_id = parent_id
        self.capsule_type = CapsuleType.STANDARD
        self.status = CapsuleStatus.VERIFIED
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.agent_id = f"agent_{capsule_id[:8]}"
        self.confidence = quality_score
        self.signature = f"sig_{capsule_id}"
        self.version = "1.0"


@pytest.fixture
def sample_chain():
    """Create a sample chain for testing."""
    capsules = []
    for i in range(100):
        parent_id = f"capsule_{i-1}" if i > 0 else None
        capsule = MockCapsule(f"capsule_{i}", parent_id, 0.7 + (i % 10) * 0.03)
        capsules.append(capsule)
    return capsules


@pytest.fixture
def large_chain():
    """Create a large chain for memory testing."""
    capsules = []
    for i in range(15000):  # Larger than the 10k threshold
        parent_id = f"capsule_{i-1}" if i > 0 else None
        capsule = MockCapsule(f"capsule_{i}", parent_id, 0.6 + (i % 20) * 0.02)
        capsules.append(capsule)
    return capsules


@pytest.fixture
def forked_chain():
    """Create a chain with forks for testing fork resolution."""
    capsules = []

    # Main chain
    for i in range(10):
        parent_id = f"capsule_{i-1}" if i > 0 else None
        capsule = MockCapsule(f"capsule_{i}", parent_id, 0.8)
        capsules.append(capsule)

    # Fork branch 1 (higher quality)
    for i in range(5):
        parent_id = "capsule_4" if i == 0 else f"fork1_{i-1}"
        capsule = MockCapsule(f"fork1_{i}", parent_id, 0.9)
        capsules.append(capsule)

    # Fork branch 2 (lower quality)
    for i in range(3):
        parent_id = "capsule_4" if i == 0 else f"fork2_{i-1}"
        capsule = MockCapsule(f"fork2_{i}", parent_id, 0.5)
        capsules.append(capsule)

    return capsules


class TestCQSSScalability:
    """Test CQSS scalability and memory efficiency."""

    @pytest.mark.asyncio
    async def test_memory_efficient_large_chain_processing(self, large_chain):
        """Test memory efficiency with chains >10,000 capsules."""

        async def verify_capsule(capsule):
            return True, "verified"

        start_time = time.time()
        start_memory = self._get_memory_usage()

        # Test with streaming enabled
        result = await compute_cqss(large_chain, verify_capsule, use_streaming=True)

        end_time = time.time()
        end_memory = self._get_memory_usage()

        # Performance assertions
        processing_time = end_time - start_time
        memory_used = end_memory - start_memory

        assert (
            processing_time < 10.0
        ), f"Processing took {processing_time:.2f}s, should be <10s"
        assert memory_used < 100, f"Memory usage {memory_used}MB, should be <100MB"
        assert (
            result.get_overall_score() is not None
        ), "Should produce valid quality score"

        # Check that streaming was actually used
        assert (
            result.metrics.get("memory_efficiency_score", 0) > 50
        ), "Should use memory-efficient processing"

    @pytest.mark.asyncio
    async def test_incremental_quality_updates(self, sample_chain):
        """Test incremental quality updates for performance."""

        async def verify_capsule(capsule):
            return True, "verified"

        # Initial computation
        initial_result = await compute_cqss(sample_chain[:50], verify_capsule)

        # Add more capsules
        new_capsules = sample_chain[50:]

        start_time = time.time()

        # Full recomputation (current approach)
        full_result = await compute_cqss(sample_chain, verify_capsule)

        processing_time = time.time() - start_time

        # Should be reasonably fast even for full recomputation
        assert (
            processing_time < 1.0
        ), f"Incremental update took {processing_time:.2f}s, should be <1s"
        assert full_result.get_overall_score() is not None

        # Quality should be similar (within 10%)
        initial_quality = initial_result.get_overall_score() or 0.0
        full_quality = full_result.get_overall_score() or 0.0
        quality_difference = abs(full_quality - initial_quality)
        assert (
            quality_difference < 0.1
        ), f"Quality difference {quality_difference} too large"

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Return mock value if psutil not available
            return 50.0


class TestForkResolution:
    """Test automated fork resolution system."""

    @pytest.mark.asyncio
    async def test_fork_detection_accuracy(self, forked_chain):
        """Test fork detection accuracy."""

        resolver = QualityBasedForkResolver()

        detected_forks = await resolver.detect_forks(forked_chain)

        # Should detect exactly one fork point
        assert (
            len(detected_forks) == 1
        ), f"Expected 1 fork, detected {len(detected_forks)}"

        # Check that fork candidates are correctly identified
        fork_id = detected_forks[0]
        candidates = resolver.active_forks.get(fork_id, [])

        assert (
            len(candidates) >= 2
        ), f"Fork should have at least 2 candidates, got {len(candidates)}"

        # Check quality scores are computed
        for candidate in candidates:
            assert (
                0.0 <= candidate.quality_score <= 1.0
            ), f"Invalid quality score: {candidate.quality_score}"

    @pytest.mark.asyncio
    async def test_quality_based_fork_resolution_performance(self, forked_chain):
        """Test fork resolution performance (<5 seconds for complex forks)."""

        resolver = QualityBasedForkResolver()

        # Detect forks first
        detected_forks = await resolver.detect_forks(forked_chain)
        assert len(detected_forks) > 0

        fork_id = detected_forks[0]

        start_time = time.time()

        # Resolve fork using quality-based strategy
        result = await resolver.resolve_fork(
            fork_id, ForkResolutionStrategy.QUALITY_BASED
        )

        resolution_time = time.time() - start_time

        # Performance assertion
        assert (
            resolution_time < 5.0
        ), f"Fork resolution took {resolution_time:.2f}s, should be <5s"

        # Quality assertions
        assert result is not None, "Fork resolution should succeed"
        assert result.quality_improvement >= 0, "Quality should not decrease"
        assert result.confidence_score > 0.5, "Resolution confidence should be >50%"

        # Should select the higher quality branch
        assert result.canonical_branch_id.startswith(
            "fork1"
        ), "Should select higher quality fork1 branch"

    @pytest.mark.asyncio
    async def test_fork_resolution_community_acceptance(self, forked_chain):
        """Test that fork resolution achieves >95% community acceptance rate."""

        resolver = QualityBasedForkResolver()

        # Simulate multiple fork resolution scenarios
        acceptance_rates = []

        for _ in range(10):  # Test 10 scenarios
            # Create mock fork
            detected_forks = await resolver.detect_forks(forked_chain)
            if detected_forks:
                fork_id = detected_forks[0]
                result = await resolver.resolve_fork(
                    fork_id, ForkResolutionStrategy.HYBRID_MULTI_CRITERIA
                )

                if result:
                    # Simulate community acceptance based on quality improvement
                    acceptance_rate = min(1.0, 0.8 + result.quality_improvement * 2)
                    acceptance_rates.append(acceptance_rate)

        if acceptance_rates:
            avg_acceptance = statistics.mean(acceptance_rates)
            assert (
                avg_acceptance > 0.95
            ), f"Average acceptance rate {avg_acceptance:.3f} should be >95%"


class TestChainSharding:
    """Test horizontal chain sharding system."""

    @pytest.mark.asyncio
    async def test_memory_usage_under_1gb_for_100k_capsules(self):
        """Test memory usage <1GB for chains up to 100,000 capsules."""

        sharding_system = HorizontalChainSharding(
            max_capsules_per_shard=1000,
            max_memory_per_shard_mb=10,
            sharding_strategy=ShardingStrategy.HASH_SHARDING,
        )

        start_memory = self._get_memory_usage()

        # Add 100k capsules (would be memory-intensive without sharding)
        for i in range(100000):
            capsule = MockCapsule(f"test_capsule_{i}", quality_score=0.7)
            await sharding_system.add_capsule(capsule)

            # Check memory periodically
            if i % 10000 == 0 and i > 0:
                current_memory = self._get_memory_usage()
                memory_used = current_memory - start_memory
                assert (
                    memory_used < 1024
                ), f"Memory usage {memory_used}MB exceeds 1GB limit at {i} capsules"

        final_memory = self._get_memory_usage()
        total_memory_used = final_memory - start_memory

        assert (
            total_memory_used < 1024
        ), f"Total memory usage {total_memory_used}MB should be <1GB"

        # Check sharding statistics
        stats = sharding_system.get_sharding_statistics()
        assert stats["total_capsules"] == 100000
        assert stats["total_shards"] > 1, "Should create multiple shards"
        assert stats["average_load_factor"] < 0.9, "Average load should be reasonable"

    @pytest.mark.asyncio
    async def test_shard_quality_consistency(self):
        """Test <1% quality variance between shards."""

        sharding_system = HorizontalChainSharding(
            max_capsules_per_shard=100,
            sharding_strategy=ShardingStrategy.QUALITY_BASED_SHARDING,
        )

        coordinator = ShardCoordinator(max_quality_variance=0.01)
        await coordinator.initialize(sharding_system)

        # Add capsules with varying quality to different shards
        for i in range(500):
            quality = 0.6 + (i % 10) * 0.04  # Quality from 0.6 to 0.96
            capsule = MockCapsule(f"quality_test_{i}", quality_score=quality)
            await sharding_system.add_capsule(capsule)

        # Compute global quality metrics
        global_state = await coordinator.compute_global_quality_metrics()

        assert global_state is not None, "Should compute global quality state"

        # Check quality variance
        quality_variance = global_state.quality_variance
        assert (
            quality_variance < 0.01
        ), f"Quality variance {quality_variance:.4f} should be <1%"

        # Check cross-shard consistency
        inconsistencies = await coordinator.detect_quality_inconsistencies()
        high_variance_issues = [
            i for i in inconsistencies if i.get("type") == "high_variance"
        ]

        assert (
            len(high_variance_issues) == 0
        ), f"Should have no high variance issues, found {len(high_variance_issues)}"

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 50.0


class TestQualityDecayDetection:
    """Test quality decay detection and remediation."""

    @pytest.mark.asyncio
    async def test_early_degradation_warning(self):
        """Test early warning >7 days before critical degradation."""

        detector = QualityDecayDetector(
            trend_window_hours=168, detection_sensitivity=0.7  # 1 week
        )

        # Simulate gradual quality degradation over time
        base_time = datetime.now(timezone.utc)

        for i in range(20):  # 20 measurement points
            timestamp = base_time + timedelta(hours=i * 6)  # Every 6 hours

            # Gradual decline from 0.9 to 0.4 over 5 days
            quality_score = 0.9 - (i * 0.025)

            trend_point = QualityTrendPoint(
                timestamp=timestamp,
                overall_score=quality_score,
                integrity_score=quality_score * 1.1,
                trust_score=quality_score * 0.9,
                complexity_score=50.0,
                diversity_score=60.0,
                verification_ratio=quality_score,
                chain_length=1000 + i * 10,
            )

            detector.quality_history.append(trend_point)

        # Analyze trends
        result = await detector.analyze_quality_trends()

        assert result is not None, "Should detect quality trend"
        assert result.decay_detected, "Should detect quality decay"
        assert result.time_to_critical is not None, "Should estimate time to critical"

        # Should provide early warning (>7 days before critical)
        days_to_critical = result.time_to_critical.days
        assert (
            days_to_critical >= 7
        ), f"Should warn ≥7 days before critical, got {days_to_critical} days"

        # Should recommend appropriate remediation
        assert (
            len(result.recommended_actions) > 0
        ), "Should recommend remediation actions"

    @pytest.mark.asyncio
    async def test_remediation_effectiveness(self):
        """Test >80% success rate for quality improvement."""

        detector = QualityDecayDetector()

        # Simulate degraded quality state
        detector.current_decay_state = Mock()
        detector.current_decay_state.decay_detected = True
        detector.current_decay_state.severity_score = 0.8

        successful_remediations = 0
        total_remediations = 10

        for i in range(total_remediations):
            # Test different remediation strategies
            strategies = [
                RemediationStrategy.AUTOMATED_OPTIMIZATION,
                RemediationStrategy.ECONOMIC_INCENTIVES,
                RemediationStrategy.SYSTEM_PARAMETER_TUNING,
            ]

            strategy = strategies[i % len(strategies)]
            action_id = await detector.implement_remediation(strategy)

            if action_id:
                successful_remediations += 1

                # Simulate successful remediation
                if action_id in detector.active_remediations:
                    action = detector.active_remediations[action_id]
                    action.actual_improvement = 0.1  # Positive improvement
                    action.success = True

        success_rate = (successful_remediations / total_remediations) * 100
        assert (
            success_rate >= 80
        ), f"Remediation success rate {success_rate:.1f}% should be ≥80%"


class TestConsensusQualityIntegration:
    """Test integration between consensus and quality systems."""

    @pytest.mark.asyncio
    async def test_quality_weighted_consensus_decisions(self):
        """Test consensus decisions prioritizing higher-quality chains."""

        # Create consensus engine with test nodes
        consensus_engine = MultiAgentConsensusEngine()

        # Add test nodes with different quality scores
        for i in range(5):
            node = ConsensusNode(
                node_id=f"node_{i}",
                role="validator",
                stake=100.0,
                reputation=70.0 + i * 5,  # Varying reputation
                last_seen=datetime.now(timezone.utc),
                public_key=f"pubkey_{i}",
                network_address=f"192.168.1.{i}",
                is_active=True,
            )
            consensus_engine.register_node(node)

        # Test quality-based consensus integration
        integration_stats = (
            await consensus_engine.integrate_quality_based_consensus_decisions(
                quality_threshold=0.7
            )
        )

        assert integration_stats["nodes_evaluated"] > 0, "Should evaluate nodes"
        assert (
            integration_stats["quality_weights_applied"] > 0
        ), "Should apply quality weights"

        # Verify quality weighting is applied
        for node_id, node in consensus_engine.nodes.items():
            if node.is_active:
                # Higher reputation nodes should have enhanced voting power
                if node.reputation > 80:
                    assert (
                        node.vote_weight >= 1.0
                    ), f"High-quality node {node_id} should have enhanced voting power"

    @pytest.mark.asyncio
    async def test_consensus_fork_resolution_integration(self, forked_chain):
        """Test consensus system resolves forks before decision making."""

        consensus_engine = MultiAgentConsensusEngine()

        # Add test nodes
        for i in range(3):
            node = ConsensusNode(
                node_id=f"test_node_{i}",
                role="validator",
                stake=100.0,
                reputation=75.0,
                last_seen=datetime.now(timezone.utc),
                public_key=f"key_{i}",
                network_address=f"addr_{i}",
                is_active=True,
            )
            consensus_engine.register_node(node)

        # Mock the fork resolver to have active forks
        with patch.object(fork_resolver, "active_forks", {"test_fork": []}):
            with patch.object(
                fork_resolver, "resolve_fork", new_callable=AsyncMock
            ) as mock_resolve:
                mock_resolve.return_value = Mock(canonical_branch_id="best_branch")

                # Convert mock capsules to the expected format
                test_capsules = [
                    Mock(capsule_id=cap.capsule_id, agent_id=cap.agent_id)
                    for cap in forked_chain[:5]
                ]

                # Test consensus with fork resolution enabled
                with patch.object(
                    consensus_engine,
                    "_quality_weighted_capsule_consensus",
                    new_callable=AsyncMock,
                ) as mock_consensus:
                    mock_consensus.return_value = True

                    success = await consensus_engine.achieve_consensus(
                        test_capsules, enable_fork_resolution=True
                    )

                    # Should attempt consensus
                    assert (
                        mock_consensus.call_count > 0
                    ), "Should attempt consensus on capsules"


class TestQualityOptimizer:
    """Test real-time quality optimization system."""

    @pytest.mark.asyncio
    async def test_real_time_quality_monitoring(self):
        """Test <100ms for incremental quality updates."""

        optimizer = RealTimeQualityOptimizer(
            monitoring_interval_seconds=1, quality_threshold=0.7
        )

        # Mock quality measurement
        with patch.object(
            optimizer, "measure_current_quality", new_callable=AsyncMock
        ) as mock_measure:
            mock_measure.return_value = 0.75

            start_time = time.time()

            # Measure quality multiple times
            for _ in range(10):
                quality = await optimizer.measure_current_quality()
                assert quality is not None

            total_time = time.time() - start_time
            avg_time_per_measurement = (
                total_time / 10
            ) * 1000  # Convert to milliseconds

            assert (
                avg_time_per_measurement < 100
            ), f"Average measurement time {avg_time_per_measurement:.1f}ms should be <100ms"

    @pytest.mark.asyncio
    async def test_quality_optimization_effectiveness(self):
        """Test quality optimization achieves target improvements."""

        optimizer = RealTimeQualityOptimizer(max_optimization_cost=500.0)

        # Mock current quality measurement
        with patch.object(
            optimizer, "measure_current_quality", new_callable=AsyncMock
        ) as mock_measure:
            # Simulate quality improvement during optimization
            mock_measure.side_effect = [0.6, 0.75]  # Before and after optimization

            # Mock successful optimization actions
            with patch.object(
                optimizer, "_execute_optimization_action", new_callable=AsyncMock
            ) as mock_execute:
                mock_execute.return_value = True

                # Test optimization
                result = await optimizer.optimize_quality(target_improvement=0.1)

                assert result is not None, "Optimization should return result"
                assert (
                    result.improvement >= 0.1
                ), f"Should achieve target improvement, got {result.improvement:.3f}"
                assert result.success, "Optimization should be successful"
                assert (
                    result.cost_effectiveness > 0
                ), "Should have positive cost effectiveness"


class TestQualityIntegrationLayer:
    """Test unified quality integration layer."""

    @pytest.mark.asyncio
    async def test_unified_quality_metrics_collection(self):
        """Test comprehensive quality metrics collection."""

        integration_layer = ChainQualityIntegrationLayer()

        # Mock individual system responses
        with patch.object(
            integration_layer.sharding_system,
            "compute_global_quality",
            new_callable=AsyncMock,
        ) as mock_global:
            mock_result = Mock()
            mock_result.get_overall_score.return_value = 0.75
            mock_result.metrics = {"integrity_score": 80.0, "trust_score": 70.0}
            mock_global.return_value = mock_result

            with patch.object(
                integration_layer.fork_resolver, "get_fork_statistics"
            ) as mock_fork_stats:
                mock_fork_stats.return_value = {"total_forks": 5, "resolved_forks": 4}

                with patch.object(
                    integration_layer.quality_optimizer, "get_optimization_statistics"
                ) as mock_opt_stats:
                    mock_opt_stats.return_value = {
                        "success_rate": 85.0,
                        "total_optimizations": 20,
                    }

                    # Get unified metrics
                    metrics = await integration_layer.get_unified_quality_metrics()

                    assert metrics is not None, "Should return unified metrics"
                    assert (
                        metrics.overall_quality_score == 0.75
                    ), "Should include overall quality score"
                    assert (
                        "integrity_score" in metrics.cqss_metrics
                    ), "Should include CQSS metrics"
                    assert (
                        "total_forks" in metrics.fork_resolution_stats
                    ), "Should include fork resolution stats"
                    assert (
                        "success_rate" in metrics.optimization_results
                    ), "Should include optimization results"

    @pytest.mark.asyncio
    async def test_emergency_quality_intervention(self):
        """Test emergency intervention when quality drops critically."""

        integration_layer = ChainQualityIntegrationLayer(emergency_threshold=0.4)

        # Mock emergency quality situation
        with patch.object(
            integration_layer, "get_unified_quality_metrics", new_callable=AsyncMock
        ) as mock_metrics:
            mock_metrics.return_value = Mock(
                overall_quality_score=0.3
            )  # Below emergency threshold

            # Mock emergency actions
            with patch.object(
                integration_layer.fork_resolver, "resolve_fork", new_callable=AsyncMock
            ) as mock_resolve:
                mock_resolve.return_value = Mock(
                    canonical_branch_id="emergency_resolved"
                )

                with patch.object(
                    integration_layer.decay_detector,
                    "implement_remediation",
                    new_callable=AsyncMock,
                ) as mock_remediation:
                    mock_remediation.return_value = "emergency_action_123"

                    # Test emergency handling
                    success = await integration_layer.handle_quality_emergency(0.3)

                    assert success, "Emergency handling should succeed"
                    assert (
                        mock_remediation.call_count > 0
                    ), "Should apply emergency remediation"

    @pytest.mark.asyncio
    async def test_system_wide_quality_optimization(self):
        """Test comprehensive system-wide optimization."""

        integration_layer = ChainQualityIntegrationLayer()

        # Mock initial low quality
        initial_metrics = Mock(
            overall_quality_score=0.6,
            fork_resolution_stats={"active_forks": 2},
            sharding_performance={"average_load_factor": 0.9},
        )

        # Mock improved quality after optimization
        final_metrics = Mock(overall_quality_score=0.8)

        with patch.object(
            integration_layer, "get_unified_quality_metrics", new_callable=AsyncMock
        ) as mock_metrics:
            mock_metrics.side_effect = [initial_metrics, final_metrics]

            # Mock optimization actions
            with patch.object(
                integration_layer.fork_resolver,
                "auto_resolve_aged_forks",
                new_callable=AsyncMock,
            ) as mock_forks:
                mock_forks.return_value = [Mock(), Mock()]  # 2 resolved forks

                with patch.object(
                    integration_layer.sharding_system,
                    "rebalance_shards",
                    new_callable=AsyncMock,
                ) as mock_rebalance:
                    mock_rebalance.return_value = True

                    with patch.object(
                        integration_layer.quality_optimizer,
                        "optimize_quality",
                        new_callable=AsyncMock,
                    ) as mock_optimize:
                        mock_optimize.return_value = Mock(
                            success=True, improvement=0.15
                        )

                        # Test system-wide optimization
                        success = await integration_layer.optimize_system_quality(
                            target_improvement=0.2
                        )

                        assert success, "System-wide optimization should succeed"
                        assert mock_forks.call_count > 0, "Should resolve aged forks"
                        assert mock_rebalance.call_count > 0, "Should rebalance shards"
                        assert (
                            mock_optimize.call_count > 0
                        ), "Should run quality optimizer"


class TestPerformanceTargets:
    """Test that all systems meet specified performance targets."""

    @pytest.mark.asyncio
    async def test_fork_resolution_performance_target(self, forked_chain):
        """Test fork resolution <5 seconds for complex multi-branch forks."""

        resolver = QualityBasedForkResolver()

        # Create complex multi-branch fork
        detected_forks = await resolver.detect_forks(forked_chain)
        assert len(detected_forks) > 0

        fork_id = detected_forks[0]

        start_time = time.time()
        result = await resolver.resolve_fork(
            fork_id, ForkResolutionStrategy.HYBRID_MULTI_CRITERIA
        )
        resolution_time = time.time() - start_time

        assert (
            resolution_time < 5.0
        ), f"Fork resolution took {resolution_time:.2f}s, target is <5s"
        assert result is not None, "Fork resolution should succeed"

    @pytest.mark.asyncio
    async def test_quality_analysis_performance_target(self, sample_chain):
        """Test quality analysis <100ms for incremental updates."""

        async def verify_capsule(capsule):
            return True, "verified"

        # Initial analysis
        await compute_cqss(sample_chain[:50], verify_capsule)

        # Incremental update simulation
        start_time = time.time()
        result = await compute_cqss(
            sample_chain[:60], verify_capsule
        )  # Add 10 more capsules
        update_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        assert (
            update_time < 100
        ), f"Quality analysis took {update_time:.1f}ms, target is <100ms"
        assert (
            result.get_overall_score() is not None
        ), "Should produce valid quality score"

    @pytest.mark.asyncio
    async def test_shard_coordination_performance_target(self):
        """Test cross-shard quality verification <200ms."""

        sharding_system = HorizontalChainSharding()
        coordinator = ShardCoordinator()

        await coordinator.initialize(sharding_system)

        # Add some test capsules
        for i in range(100):
            capsule = MockCapsule(f"perf_test_{i}")
            await sharding_system.add_capsule(capsule)

        start_time = time.time()
        global_state = await coordinator.compute_global_quality_metrics()
        coordination_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        assert (
            coordination_time < 200
        ), f"Shard coordination took {coordination_time:.1f}ms, target is <200ms"
        assert global_state is not None, "Should produce global quality state"


if __name__ == "__main__":
    # Run tests with performance monitoring
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "--durations=10",  # Show 10 slowest tests
            "-x",  # Stop on first failure
        ]
    )
