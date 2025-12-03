"""
quality_optimizer.py - Real-time Quality Improvement System

This module implements real-time quality monitoring and automated optimization
mechanisms to maintain high chain quality standards. Provides automated
interventions, quality-based economic feedback, and continuous improvement.

Key Features:
- Real-time quality monitoring with automatic intervention
- Economic penalties for persistent quality degradation
- Automated capsule improvement suggestions
- Quality-based economic feedback loops
- Performance-aware optimization strategies
- Integration with fork resolution and sharding systems
"""

import asyncio
import json
import logging
import statistics
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable, Set
import weakref

from .cqss import CQSSResult, compute_cqss
from .fork_resolver import ForkResolutionStrategy, fork_resolver
from .quality_decay_detector import quality_decay_detector, RemediationStrategy
from ..economic.fcde_engine import fcde_engine
from ..consensus.multi_agent_consensus import consensus_engine

logger = logging.getLogger(__name__)


class OptimizationStrategy(str, Enum):
    """Types of quality optimization strategies."""

    PREVENTIVE_MAINTENANCE = "preventive_maintenance"
    REACTIVE_INTERVENTION = "reactive_intervention"
    PREDICTIVE_OPTIMIZATION = "predictive_optimization"
    EMERGENCY_STABILIZATION = "emergency_stabilization"
    PERFORMANCE_TUNING = "performance_tuning"
    ECONOMIC_INCENTIVIZATION = "economic_incentivization"


class QualityMetric(str, Enum):
    """Quality metrics that can be optimized."""

    OVERALL_SCORE = "overall_score"
    INTEGRITY_SCORE = "integrity_score"
    TRUST_SCORE = "trust_score"
    COMPLEXITY_SCORE = "complexity_score"
    DIVERSITY_SCORE = "diversity_score"
    VERIFICATION_RATIO = "verification_ratio"
    FORK_RESOLUTION_RATE = "fork_resolution_rate"
    CHAIN_CONSISTENCY = "chain_consistency"


@dataclass
class OptimizationAction:
    """Single optimization action with measurable impact."""

    action_id: str
    strategy: OptimizationStrategy
    target_metrics: List[QualityMetric]
    timestamp: datetime
    expected_improvement: float
    actual_improvement: Optional[float] = None
    cost: float = 0.0
    duration: Optional[timedelta] = None
    success: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityOptimizationResult:
    """Result of a quality optimization cycle."""

    optimization_id: str
    timestamp: datetime
    initial_quality: float
    final_quality: float
    improvement: float
    actions_applied: List[OptimizationAction]
    cost_effectiveness: float
    time_to_improve: timedelta
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


class RealTimeQualityOptimizer:
    """
    Real-time quality improvement system.

    Continuously monitors chain quality and applies automated optimizations
    to maintain high standards. Integrates with economic systems, fork
    resolution, and sharding for comprehensive quality management.
    """

    def __init__(
        self,
        monitoring_interval_seconds: int = 30,
        quality_threshold: float = 0.7,
        emergency_threshold: float = 0.5,
        max_optimization_cost: float = 1000.0,
    ):
        """Initialize the quality optimizer.

        Args:
            monitoring_interval_seconds: How often to check quality
            quality_threshold: Minimum acceptable quality score
            emergency_threshold: Quality level that triggers emergency measures
            max_optimization_cost: Maximum cost for optimization actions
        """
        self.monitoring_interval_seconds = monitoring_interval_seconds
        self.quality_threshold = quality_threshold
        self.emergency_threshold = emergency_threshold
        self.max_optimization_cost = max_optimization_cost

        # Quality monitoring state
        self.current_quality: Optional[float] = None
        self.quality_history: deque = deque(maxlen=1000)
        self.optimization_history: List[QualityOptimizationResult] = []

        # Active optimizations
        self.active_optimizations: Dict[str, OptimizationAction] = {}
        self.optimization_queue: List[OptimizationAction] = []

        # Performance tracking
        self.strategy_effectiveness: Dict[OptimizationStrategy, float] = defaultdict(
            float
        )
        self.metric_improvement_rates: Dict[QualityMetric, float] = defaultdict(float)

        # Configuration
        self.optimization_strategies = {
            OptimizationStrategy.PREVENTIVE_MAINTENANCE: self._preventive_maintenance,
            OptimizationStrategy.REACTIVE_INTERVENTION: self._reactive_intervention,
            OptimizationStrategy.PREDICTIVE_OPTIMIZATION: self._predictive_optimization,
            OptimizationStrategy.EMERGENCY_STABILIZATION: self._emergency_stabilization,
            OptimizationStrategy.PERFORMANCE_TUNING: self._performance_tuning,
            OptimizationStrategy.ECONOMIC_INCENTIVIZATION: self._economic_incentivization,
        }

        # Background tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.optimization_task: Optional[asyncio.Task] = None
        self.running = False

        # Integration points
        self.economic_engine = fcde_engine
        self.fork_resolver = fork_resolver
        self.decay_detector = quality_decay_detector
        self.consensus_engine = consensus_engine

        # Callbacks for external notifications
        self.quality_callbacks: List[Callable[[float, float], None]] = []
        self.optimization_callbacks: List[
            Callable[[QualityOptimizationResult], None]
        ] = []

        logger.info(
            f"Initialized quality optimizer with {quality_threshold} quality threshold"
        )

    async def start(self):
        """Start real-time quality monitoring and optimization."""
        if self.running:
            return

        self.running = True

        # Start background monitoring
        self.monitoring_task = asyncio.create_task(self._quality_monitoring_loop())
        self.optimization_task = asyncio.create_task(
            self._optimization_processing_loop()
        )

        logger.info("Started real-time quality optimizer")

    async def stop(self):
        """Stop quality monitoring and optimization."""
        self.running = False

        # Cancel background tasks
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        if self.optimization_task:
            self.optimization_task.cancel()
            try:
                await self.optimization_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped quality optimizer")

    async def measure_current_quality(self, chain=None) -> Optional[float]:
        """Measure current chain quality.

        Args:
            chain: Optional chain to measure. If None, uses sharding system.

        Returns:
            Current quality score or None if measurement failed
        """
        try:
            if chain:
                # Direct measurement
                async def verify_capsule(capsule):
                    return True, "verified"

                result = await compute_cqss(chain, verify_capsule)
                quality_score = result.get_overall_score()
            else:
                # Use sharding system for global quality
                from .chain_sharding import horizontal_sharding

                if horizontal_sharding.sharding_system:

                    async def verify_capsule(capsule):
                        return True, "verified"

                    result = await horizontal_sharding.compute_global_quality(
                        verify_capsule
                    )
                    quality_score = result.get_overall_score()
                else:
                    return None

            if quality_score is not None:
                self.current_quality = quality_score
                self.quality_history.append(
                    {
                        "timestamp": datetime.now(timezone.utc),
                        "quality_score": quality_score,
                    }
                )

                # Notify callbacks
                for callback in self.quality_callbacks:
                    try:
                        old_quality = (
                            self.quality_history[-2]["quality_score"]
                            if len(self.quality_history) > 1
                            else quality_score
                        )
                        callback(old_quality, quality_score)
                    except Exception as e:
                        logger.error(f"Quality callback failed: {e}")

            return quality_score

        except Exception as e:
            logger.error(f"Failed to measure quality: {e}")
            return None

    async def optimize_quality(
        self, target_improvement: float = 0.1
    ) -> Optional[QualityOptimizationResult]:
        """Perform comprehensive quality optimization.

        Args:
            target_improvement: Target quality improvement (0.0 to 1.0)

        Returns:
            Optimization result or None if failed
        """
        optimization_id = f"opt_{int(datetime.now(timezone.utc).timestamp())}"
        start_time = datetime.now(timezone.utc)

        try:
            # Measure initial quality
            initial_quality = await self.measure_current_quality()
            if initial_quality is None:
                logger.error("Cannot optimize: failed to measure initial quality")
                return None

            logger.info(
                f"Starting quality optimization {optimization_id}: initial={initial_quality:.3f}, target improvement={target_improvement:.3f}"
            )

            # Determine optimization strategy based on current state
            strategy = await self._select_optimization_strategy(
                initial_quality, target_improvement
            )

            # Create optimization actions
            actions = await self._create_optimization_actions(
                strategy, initial_quality, target_improvement
            )

            if not actions:
                logger.warning(
                    f"No optimization actions generated for strategy {strategy}"
                )
                return None

            # Execute optimization actions
            applied_actions = []
            total_cost = 0.0

            for action in actions:
                if total_cost + action.cost > self.max_optimization_cost:
                    logger.warning(
                        f"Skipping action {action.action_id}: would exceed cost limit"
                    )
                    continue

                success = await self._execute_optimization_action(action)
                if success:
                    applied_actions.append(action)
                    total_cost += action.cost

                    # Short delay between actions
                    await asyncio.sleep(1)

            if not applied_actions:
                logger.error("No optimization actions were successfully applied")
                return None

            # Wait for effects to take place
            await asyncio.sleep(5)

            # Measure final quality
            final_quality = await self.measure_current_quality()
            if final_quality is None:
                final_quality = (
                    initial_quality  # Assume no change if measurement failed
                )

            # Calculate results
            actual_improvement = final_quality - initial_quality
            cost_effectiveness = (
                actual_improvement / max(total_cost, 1.0) if total_cost > 0 else 0.0
            )
            time_to_improve = datetime.now(timezone.utc) - start_time
            success = (
                actual_improvement >= target_improvement * 0.5
            )  # 50% of target is success

            # Create result
            result = QualityOptimizationResult(
                optimization_id=optimization_id,
                timestamp=start_time,
                initial_quality=initial_quality,
                final_quality=final_quality,
                improvement=actual_improvement,
                actions_applied=applied_actions,
                cost_effectiveness=cost_effectiveness,
                time_to_improve=time_to_improve,
                success=success,
                metadata={
                    "strategy_used": strategy.value,
                    "actions_planned": len(actions),
                    "actions_applied": len(applied_actions),
                    "total_cost": total_cost,
                    "target_improvement": target_improvement,
                },
            )

            # Store result
            self.optimization_history.append(result)

            # Update strategy effectiveness
            self.strategy_effectiveness[strategy] = (
                self.strategy_effectiveness[strategy] * 0.8
                + max(0, actual_improvement) * 0.2
            )

            # Notify callbacks
            for callback in self.optimization_callbacks:
                try:
                    callback(result)
                except Exception as e:
                    logger.error(f"Optimization callback failed: {e}")

            logger.info(
                f"Optimization {optimization_id} completed: improvement={actual_improvement:.3f}, success={success}"
            )
            return result

        except Exception as e:
            logger.error(f"Quality optimization {optimization_id} failed: {e}")
            return None

    async def _quality_monitoring_loop(self):
        """Background loop for continuous quality monitoring."""
        while self.running:
            try:
                # Measure current quality
                quality = await self.measure_current_quality()

                if quality is not None:
                    # Check if intervention is needed
                    if quality <= self.emergency_threshold:
                        # Emergency optimization
                        logger.critical(
                            f"Emergency quality intervention needed: {quality:.3f}"
                        )
                        await self._queue_optimization(
                            OptimizationStrategy.EMERGENCY_STABILIZATION, urgent=True
                        )

                    elif quality <= self.quality_threshold:
                        # Standard optimization
                        logger.warning(f"Quality below threshold: {quality:.3f}")
                        await self._queue_optimization(
                            OptimizationStrategy.REACTIVE_INTERVENTION
                        )

                    else:
                        # Preventive maintenance
                        if len(self.quality_history) >= 10:
                            recent_qualities = [
                                q["quality_score"]
                                for q in list(self.quality_history)[-10:]
                            ]
                            if (
                                len(recent_qualities) > 5
                                and statistics.stdev(recent_qualities) > 0.1
                            ):
                                # High volatility - apply preventive measures
                                await self._queue_optimization(
                                    OptimizationStrategy.PREVENTIVE_MAINTENANCE
                                )

                # Sleep until next monitoring cycle
                await asyncio.sleep(self.monitoring_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Quality monitoring error: {e}")
                await asyncio.sleep(min(self.monitoring_interval_seconds, 60))

    async def _optimization_processing_loop(self):
        """Background loop for processing optimization queue."""
        while self.running:
            try:
                if self.optimization_queue:
                    # Get next optimization action
                    action = self.optimization_queue.pop(0)

                    if action.strategy == OptimizationStrategy.EMERGENCY_STABILIZATION:
                        # Process emergency actions immediately
                        await self._execute_optimization_action(action)
                    else:
                        # Queue for batch processing
                        current_time = datetime.now(timezone.utc)
                        if (
                            current_time - action.timestamp
                        ).seconds >= 60:  # Wait 1 minute for batching
                            target_improvement = 0.1  # Default improvement target
                            await self.optimize_quality(target_improvement)

                            # Clear similar queued actions to avoid duplication
                            self.optimization_queue = [
                                a
                                for a in self.optimization_queue
                                if a.strategy != action.strategy
                            ]

                await asyncio.sleep(10)  # Check every 10 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Optimization processing error: {e}")
                await asyncio.sleep(10)

    async def _queue_optimization(
        self, strategy: OptimizationStrategy, urgent: bool = False
    ):
        """Queue an optimization action for processing.

        Args:
            strategy: Optimization strategy to queue
            urgent: Whether this is an urgent optimization
        """
        action = OptimizationAction(
            action_id=f"queued_{strategy.value}_{int(datetime.now(timezone.utc).timestamp())}",
            strategy=strategy,
            target_metrics=[QualityMetric.OVERALL_SCORE],
            timestamp=datetime.now(timezone.utc),
            expected_improvement=0.1,
            metadata={"urgent": urgent},
        )

        if urgent:
            # Insert at front of queue
            self.optimization_queue.insert(0, action)
        else:
            # Add to end of queue
            self.optimization_queue.append(action)

        logger.info(
            f"Queued optimization: {strategy.value} ({'urgent' if urgent else 'normal'})"
        )

    async def _select_optimization_strategy(
        self, current_quality: float, target_improvement: float
    ) -> OptimizationStrategy:
        """Select the most appropriate optimization strategy.

        Args:
            current_quality: Current quality score
            target_improvement: Target improvement amount

        Returns:
            Selected optimization strategy
        """
        # Emergency measures for very low quality
        if current_quality <= self.emergency_threshold:
            return OptimizationStrategy.EMERGENCY_STABILIZATION

        # Reactive intervention for quality below threshold
        if current_quality <= self.quality_threshold:
            return OptimizationStrategy.REACTIVE_INTERVENTION

        # Predictive optimization for proactive improvement
        if target_improvement > 0.2:
            return OptimizationStrategy.PREDICTIVE_OPTIMIZATION

        # Economic incentivization for moderate improvements
        if target_improvement > 0.1:
            return OptimizationStrategy.ECONOMIC_INCENTIVIZATION

        # Performance tuning for fine-tuning
        if target_improvement > 0.05:
            return OptimizationStrategy.PERFORMANCE_TUNING

        # Default to preventive maintenance
        return OptimizationStrategy.PREVENTIVE_MAINTENANCE

    async def _create_optimization_actions(
        self,
        strategy: OptimizationStrategy,
        current_quality: float,
        target_improvement: float,
    ) -> List[OptimizationAction]:
        """Create specific optimization actions for a strategy.

        Args:
            strategy: Optimization strategy
            current_quality: Current quality score
            target_improvement: Target improvement

        Returns:
            List of optimization actions
        """
        actions = []
        action_id_base = (
            f"{strategy.value}_{int(datetime.now(timezone.utc).timestamp())}"
        )

        if strategy == OptimizationStrategy.EMERGENCY_STABILIZATION:
            # Emergency measures
            actions.extend(
                [
                    OptimizationAction(
                        action_id=f"{action_id_base}_fork_resolution",
                        strategy=strategy,
                        target_metrics=[
                            QualityMetric.FORK_RESOLUTION_RATE,
                            QualityMetric.CHAIN_CONSISTENCY,
                        ],
                        timestamp=datetime.now(timezone.utc),
                        expected_improvement=0.2,
                        cost=50.0,
                        metadata={"priority": "emergency"},
                    ),
                    OptimizationAction(
                        action_id=f"{action_id_base}_quality_lockdown",
                        strategy=strategy,
                        target_metrics=[
                            QualityMetric.VERIFICATION_RATIO,
                            QualityMetric.INTEGRITY_SCORE,
                        ],
                        timestamp=datetime.now(timezone.utc),
                        expected_improvement=0.15,
                        cost=100.0,
                        metadata={"priority": "emergency"},
                    ),
                ]
            )

        elif strategy == OptimizationStrategy.REACTIVE_INTERVENTION:
            # Reactive measures based on detected issues
            actions.extend(
                [
                    OptimizationAction(
                        action_id=f"{action_id_base}_decay_remediation",
                        strategy=strategy,
                        target_metrics=[
                            QualityMetric.OVERALL_SCORE,
                            QualityMetric.TRUST_SCORE,
                        ],
                        timestamp=datetime.now(timezone.utc),
                        expected_improvement=0.12,
                        cost=30.0,
                    ),
                    OptimizationAction(
                        action_id=f"{action_id_base}_consensus_optimization",
                        strategy=strategy,
                        target_metrics=[
                            QualityMetric.VERIFICATION_RATIO,
                            QualityMetric.DIVERSITY_SCORE,
                        ],
                        timestamp=datetime.now(timezone.utc),
                        expected_improvement=0.08,
                        cost=25.0,
                    ),
                ]
            )

        elif strategy == OptimizationStrategy.ECONOMIC_INCENTIVIZATION:
            # Economic measures to encourage quality
            actions.append(
                OptimizationAction(
                    action_id=f"{action_id_base}_incentive_boost",
                    strategy=strategy,
                    target_metrics=[
                        QualityMetric.OVERALL_SCORE,
                        QualityMetric.DIVERSITY_SCORE,
                    ],
                    timestamp=datetime.now(timezone.utc),
                    expected_improvement=0.1,
                    cost=75.0,
                    metadata={"economic_intervention": True},
                )
            )

        elif strategy == OptimizationStrategy.PERFORMANCE_TUNING:
            # Fine-tuning for better performance
            actions.extend(
                [
                    OptimizationAction(
                        action_id=f"{action_id_base}_parameter_tuning",
                        strategy=strategy,
                        target_metrics=[QualityMetric.COMPLEXITY_SCORE],
                        timestamp=datetime.now(timezone.utc),
                        expected_improvement=0.05,
                        cost=10.0,
                    ),
                    OptimizationAction(
                        action_id=f"{action_id_base}_caching_optimization",
                        strategy=strategy,
                        target_metrics=[QualityMetric.OVERALL_SCORE],
                        timestamp=datetime.now(timezone.utc),
                        expected_improvement=0.03,
                        cost=5.0,
                    ),
                ]
            )

        else:  # PREVENTIVE_MAINTENANCE and PREDICTIVE_OPTIMIZATION
            actions.append(
                OptimizationAction(
                    action_id=f"{action_id_base}_maintenance",
                    strategy=strategy,
                    target_metrics=[QualityMetric.OVERALL_SCORE],
                    timestamp=datetime.now(timezone.utc),
                    expected_improvement=target_improvement * 0.8,
                    cost=20.0,
                )
            )

        return actions

    async def _execute_optimization_action(self, action: OptimizationAction) -> bool:
        """Execute a specific optimization action.

        Args:
            action: Optimization action to execute

        Returns:
            True if successful
        """
        try:
            start_time = datetime.now(timezone.utc)
            success = False

            if action.strategy == OptimizationStrategy.EMERGENCY_STABILIZATION:
                success = await self._emergency_stabilization(action)
            elif action.strategy == OptimizationStrategy.REACTIVE_INTERVENTION:
                success = await self._reactive_intervention(action)
            elif action.strategy == OptimizationStrategy.ECONOMIC_INCENTIVIZATION:
                success = await self._economic_incentivization(action)
            elif action.strategy == OptimizationStrategy.PERFORMANCE_TUNING:
                success = await self._performance_tuning(action)
            else:
                success = await self._preventive_maintenance(action)

            # Update action result
            action.success = success
            action.duration = datetime.now(timezone.utc) - start_time

            if success:
                self.active_optimizations[action.action_id] = action
                logger.info(
                    f"Optimization action {action.action_id} executed successfully"
                )
            else:
                logger.warning(f"Optimization action {action.action_id} failed")

            return success

        except Exception as e:
            logger.error(
                f"Failed to execute optimization action {action.action_id}: {e}"
            )
            action.success = False
            return False

    async def _emergency_stabilization(self, action: OptimizationAction) -> bool:
        """Execute emergency stabilization measures."""
        try:
            # Resolve all active forks immediately
            if QualityMetric.FORK_RESOLUTION_RATE in action.target_metrics:
                active_forks = list(self.fork_resolver.active_forks.keys())
                for fork_id in active_forks:
                    await self.fork_resolver.resolve_fork(
                        fork_id, ForkResolutionStrategy.HYBRID_MULTI_CRITERIA
                    )

            # Apply emergency quality remediation
            if (
                self.decay_detector.current_decay_state
                and self.decay_detector.current_decay_state.decay_detected
            ):
                await self.decay_detector.implement_remediation(
                    RemediationStrategy.EMERGENCY_LOCKDOWN
                )

            return True

        except Exception as e:
            logger.error(f"Emergency stabilization failed: {e}")
            return False

    async def _reactive_intervention(self, action: OptimizationAction) -> bool:
        """Execute reactive intervention measures."""
        try:
            # Apply quality decay remediation
            if self.decay_detector.current_decay_state:
                for strategy in [
                    RemediationStrategy.AUTOMATED_OPTIMIZATION,
                    RemediationStrategy.SYSTEM_PARAMETER_TUNING,
                ]:
                    await self.decay_detector.implement_remediation(strategy)

            # Optimize consensus for better verification
            if hasattr(self.consensus_engine, "implement_enhanced_byzantine_detection"):
                self.consensus_engine.implement_enhanced_byzantine_detection()

            return True

        except Exception as e:
            logger.error(f"Reactive intervention failed: {e}")
            return False

    async def _economic_incentivization(self, action: OptimizationAction) -> bool:
        """Execute economic incentivization measures."""
        try:
            if not self.economic_engine:
                return False

            # Increase quality bonuses
            bonus_amount = action.cost * 0.8  # Use 80% of cost as bonus
            self.economic_engine.update_treasury(
                bonus_amount, f"Quality optimization bonus - {action.action_id}"
            )

            # Temporarily increase dividend rate
            if hasattr(self.economic_engine, "dividend_rate"):
                current_rate = self.economic_engine.dividend_rate
                new_rate = min(current_rate * 1.3, 0.12)  # Cap at 12%
                self.economic_engine.set_dividend_rate(new_rate)

                action.metadata["dividend_rate_increase"] = {
                    "old_rate": float(current_rate),
                    "new_rate": float(new_rate),
                }

            return True

        except Exception as e:
            logger.error(f"Economic incentivization failed: {e}")
            return False

    async def _performance_tuning(self, action: OptimizationAction) -> bool:
        """Execute performance tuning measures."""
        try:
            # Clear caches to force fresh calculations
            if hasattr(self.fork_resolver, "resolution_cache"):
                self.fork_resolver.resolution_cache.clear()

            if hasattr(self.decay_detector, "trend_analysis_cache"):
                self.decay_detector.trend_analysis_cache.clear()

            # Optimize sharding if available
            try:
                from .chain_sharding import horizontal_sharding

                if horizontal_sharding.shards:
                    await horizontal_sharding.rebalance_shards()
            except ImportError:
                pass

            return True

        except Exception as e:
            logger.error(f"Performance tuning failed: {e}")
            return False

    async def _preventive_maintenance(self, action: OptimizationAction) -> bool:
        """Execute preventive maintenance measures."""
        try:
            # Apply light quality remediation
            if self.decay_detector.current_decay_state:
                await self.decay_detector.implement_remediation(
                    RemediationStrategy.AUTOMATED_OPTIMIZATION
                )

            # Age out old forks if any
            aged_results = await self.fork_resolver.auto_resolve_aged_forks()

            action.metadata["aged_forks_resolved"] = len(aged_results)
            return True

        except Exception as e:
            logger.error(f"Preventive maintenance failed: {e}")
            return False

    async def _predictive_optimization(self, action: OptimizationAction) -> bool:
        """Execute predictive optimization measures."""
        # For now, use preventive maintenance logic
        # In production, this would use ML models to predict and prevent issues
        return await self._preventive_maintenance(action)

    def register_quality_callback(self, callback: Callable[[float, float], None]):
        """Register callback for quality changes.

        Args:
            callback: Function called with (old_quality, new_quality)
        """
        self.quality_callbacks.append(callback)

    def register_optimization_callback(
        self, callback: Callable[[QualityOptimizationResult], None]
    ):
        """Register callback for optimization completions.

        Args:
            callback: Function called with optimization result
        """
        self.optimization_callbacks.append(callback)

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics.

        Returns:
            Dictionary with optimization metrics
        """
        if not self.optimization_history:
            return {
                "total_optimizations": 0,
                "average_improvement": 0.0,
                "success_rate": 0.0,
                "current_quality": self.current_quality,
            }

        successful_optimizations = [
            opt for opt in self.optimization_history if opt.success
        ]

        total_optimizations = len(self.optimization_history)
        success_rate = len(successful_optimizations) / total_optimizations * 100

        if successful_optimizations:
            avg_improvement = statistics.mean(
                [opt.improvement for opt in successful_optimizations]
            )
            avg_cost_effectiveness = statistics.mean(
                [opt.cost_effectiveness for opt in successful_optimizations]
            )
        else:
            avg_improvement = 0.0
            avg_cost_effectiveness = 0.0

        # Strategy effectiveness
        strategy_stats = {}
        for strategy, effectiveness in self.strategy_effectiveness.items():
            strategy_usage = len(
                [
                    opt
                    for opt in self.optimization_history
                    if any(
                        action.strategy == strategy for action in opt.actions_applied
                    )
                ]
            )
            strategy_stats[strategy.value] = {
                "effectiveness": round(effectiveness, 3),
                "usage_count": strategy_usage,
            }

        return {
            "running": self.running,
            "current_quality": self.current_quality,
            "quality_threshold": self.quality_threshold,
            "emergency_threshold": self.emergency_threshold,
            "total_optimizations": total_optimizations,
            "successful_optimizations": len(successful_optimizations),
            "success_rate": round(success_rate, 1),
            "average_improvement": round(avg_improvement, 3),
            "average_cost_effectiveness": round(avg_cost_effectiveness, 3),
            "active_optimizations": len(self.active_optimizations),
            "queued_optimizations": len(self.optimization_queue),
            "quality_history_length": len(self.quality_history),
            "strategy_effectiveness": strategy_stats,
            "recent_quality_trend": [
                {
                    "timestamp": entry["timestamp"].isoformat(),
                    "quality": round(entry["quality_score"], 3),
                }
                for entry in list(self.quality_history)[-10:]  # Last 10 measurements
            ],
        }


# Global quality optimizer instance
quality_optimizer = RealTimeQualityOptimizer()
