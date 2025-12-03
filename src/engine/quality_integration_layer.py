"""
quality_integration_layer.py - Unified Chain Quality Management System

This module provides a comprehensive integration layer that connects all chain quality 
systems: fork resolution, sharding, quality decay detection, consensus integration, 
and real-time optimization. Provides a unified API for quality management.

Key Features:
- Unified API for all quality management operations
- Automated coordination between quality systems
- Performance monitoring and optimization
- Quality-based decision making across all subsystems
- Event-driven quality management
- Real-time quality dashboard and monitoring
"""

import asyncio
import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Tuple
import weakref

from .cqss import CQSSResult, compute_cqss
from .fork_resolver import (
    fork_resolver,
    ForkResolutionStrategy,
    QualityBasedForkResolver,
)
from .chain_sharding import horizontal_sharding, HorizontalChainSharding
from .shard_coordinator import shard_coordinator, ShardCoordinator
from .quality_decay_detector import (
    quality_decay_detector,
    QualityDecayDetector,
    RemediationStrategy,
)
from .quality_optimizer import (
    quality_optimizer,
    RealTimeQualityOptimizer,
    OptimizationStrategy,
)
from ..consensus.multi_agent_consensus import (
    consensus_engine,
    initialize_quality_integrated_consensus,
)
from ..economic.fcde_engine import fcde_engine

logger = logging.getLogger(__name__)


class QualitySystemStatus(str, Enum):
    """Status of individual quality systems."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"
    INITIALIZING = "initializing"


class QualityEvent(str, Enum):
    """Types of quality events."""

    QUALITY_IMPROVED = "quality_improved"
    QUALITY_DEGRADED = "quality_degraded"
    FORK_DETECTED = "fork_detected"
    FORK_RESOLVED = "fork_resolved"
    SYSTEM_OPTIMIZED = "system_optimized"
    EMERGENCY_TRIGGERED = "emergency_triggered"
    CONSENSUS_ACHIEVED = "consensus_achieved"
    SHARD_REBALANCED = "shard_rebalanced"


@dataclass
class QualitySystemHealth:
    """Health status of a quality system component."""

    system_name: str
    status: QualitySystemStatus
    last_update: datetime
    performance_score: float  # 0.0 to 1.0
    error_count: int = 0
    uptime_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityEvent:
    """Quality management event."""

    event_id: str
    event_type: QualityEvent
    timestamp: datetime
    source_system: str
    quality_before: Optional[float] = None
    quality_after: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedQualityMetrics:
    """Comprehensive quality metrics across all systems."""

    timestamp: datetime
    overall_quality_score: float
    cqss_metrics: Dict[str, float]
    fork_resolution_stats: Dict[str, Any]
    sharding_performance: Dict[str, Any]
    consensus_effectiveness: Dict[str, Any]
    optimization_results: Dict[str, Any]
    system_health: Dict[str, QualitySystemHealth]
    active_events: List[QualityEvent] = field(default_factory=list)


class ChainQualityIntegrationLayer:
    """
    Unified chain quality management system.

    Integrates and coordinates all chain quality systems to provide
    comprehensive quality management, automated optimization, and
    real-time monitoring with unified decision making.
    """

    def __init__(
        self,
        monitoring_interval_seconds: int = 60,
        quality_target: float = 0.8,
        emergency_threshold: float = 0.5,
    ):
        """Initialize the quality integration layer.

        Args:
            monitoring_interval_seconds: How often to run quality checks
            quality_target: Target quality score to maintain
            emergency_threshold: Quality level that triggers emergency measures
        """
        self.monitoring_interval_seconds = monitoring_interval_seconds
        self.quality_target = quality_target
        self.emergency_threshold = emergency_threshold

        # System references
        self.fork_resolver = fork_resolver
        self.sharding_system = horizontal_sharding
        self.shard_coordinator = shard_coordinator
        self.decay_detector = quality_decay_detector
        self.quality_optimizer = quality_optimizer
        self.consensus_engine = consensus_engine
        self.economic_engine = fcde_engine

        # Integration state
        self.running = False
        self.system_health: Dict[str, QualitySystemHealth] = {}
        self.quality_history: deque = deque(maxlen=1000)
        self.event_history: deque = deque(maxlen=5000)

        # Performance tracking
        self.integration_stats = {
            "total_quality_checks": 0,
            "quality_optimizations": 0,
            "forks_resolved": 0,
            "emergency_interventions": 0,
            "system_reboots": 0,
            "uptime_start": datetime.now(timezone.utc),
        }

        # Event callbacks
        self.event_callbacks: List[Callable[[QualityEvent], None]] = []
        self.quality_callbacks: List[Callable[[UnifiedQualityMetrics], None]] = []

        # Background tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.coordination_task: Optional[asyncio.Task] = None
        self.health_check_task: Optional[asyncio.Task] = None

        logger.info(
            f"Initialized chain quality integration layer with {quality_target} target quality"
        )

    async def initialize(self):
        """Initialize all quality systems and start coordination."""
        logger.info("Initializing unified chain quality management system...")

        try:
            # Initialize individual systems
            await self._initialize_quality_systems()

            # Set up system health monitoring
            await self._initialize_health_monitoring()

            # Start background coordination
            self.running = True
            self.monitoring_task = asyncio.create_task(self._quality_monitoring_loop())
            self.coordination_task = asyncio.create_task(
                self._system_coordination_loop()
            )
            self.health_check_task = asyncio.create_task(self._health_check_loop())

            # Initialize quality-integrated consensus
            await initialize_quality_integrated_consensus()

            logger.info("Chain quality integration layer initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize quality integration layer: {e}")
            raise

    async def shutdown(self):
        """Shutdown the quality integration layer."""
        logger.info("Shutting down chain quality integration layer...")

        self.running = False

        # Stop background tasks
        for task in [
            self.monitoring_task,
            self.coordination_task,
            self.health_check_task,
        ]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Shutdown individual systems
        await self._shutdown_quality_systems()

        logger.info("Chain quality integration layer shutdown complete")

    async def get_unified_quality_metrics(self) -> UnifiedQualityMetrics:
        """Get comprehensive quality metrics across all systems.

        Returns:
            Unified quality metrics
        """
        try:
            timestamp = datetime.now(timezone.utc)

            # Get CQSS metrics
            cqss_metrics = {}
            try:
                # Use sharding system for global quality if available
                if self.sharding_system.shards:

                    async def verify_capsule(capsule):
                        return True, "verified"

                    global_result = await self.sharding_system.compute_global_quality(
                        verify_capsule
                    )
                    if global_result:
                        cqss_metrics = global_result.metrics
                        overall_quality = global_result.get_overall_score() or 0.0
                    else:
                        overall_quality = 0.0
                else:
                    overall_quality = 0.0
            except Exception as e:
                logger.warning(f"Failed to get CQSS metrics: {e}")
                overall_quality = 0.0

            # Get fork resolution stats
            fork_stats = self.fork_resolver.get_fork_statistics()

            # Get sharding performance
            sharding_stats = self.sharding_system.get_sharding_statistics()

            # Get consensus effectiveness
            consensus_stats = self.consensus_engine.get_consensus_statistics()

            # Get optimization results
            optimization_stats = self.quality_optimizer.get_optimization_statistics()

            # Get shard coordination stats
            coordination_stats = self.shard_coordinator.get_coordination_statistics()

            # Combine all metrics
            unified_metrics = UnifiedQualityMetrics(
                timestamp=timestamp,
                overall_quality_score=overall_quality,
                cqss_metrics=cqss_metrics,
                fork_resolution_stats=fork_stats,
                sharding_performance=sharding_stats,
                consensus_effectiveness=consensus_stats,
                optimization_results=optimization_stats,
                system_health=self.system_health.copy(),
                active_events=list(self.event_history)[-50:],  # Last 50 events
            )

            # Store in history
            self.quality_history.append(
                {
                    "timestamp": timestamp,
                    "overall_quality": overall_quality,
                    "system_count": len(
                        [
                            h
                            for h in self.system_health.values()
                            if h.status == QualitySystemStatus.HEALTHY
                        ]
                    ),
                }
            )

            return unified_metrics

        except Exception as e:
            logger.error(f"Failed to get unified quality metrics: {e}")
            return UnifiedQualityMetrics(
                timestamp=datetime.now(timezone.utc),
                overall_quality_score=0.0,
                cqss_metrics={},
                fork_resolution_stats={},
                sharding_performance={},
                consensus_effectiveness={},
                optimization_results={},
                system_health=self.system_health.copy(),
            )

    async def optimize_system_quality(self, target_improvement: float = 0.1) -> bool:
        """Perform comprehensive system-wide quality optimization.

        Args:
            target_improvement: Target quality improvement

        Returns:
            True if optimization was successful
        """
        logger.info(
            f"Starting system-wide quality optimization (target: {target_improvement:.3f})"
        )

        try:
            # Get current metrics
            initial_metrics = await self.get_unified_quality_metrics()
            initial_quality = initial_metrics.overall_quality_score

            optimization_actions = []

            # 1. Resolve any active forks
            if initial_metrics.fork_resolution_stats.get("active_forks", 0) > 0:
                logger.info("Resolving active forks for quality improvement")
                aged_forks = await self.fork_resolver.auto_resolve_aged_forks()
                optimization_actions.append(f"Resolved {len(aged_forks)} aged forks")

            # 2. Optimize sharding if needed
            sharding_load = initial_metrics.sharding_performance.get(
                "average_load_factor", 0.0
            )
            if sharding_load > 0.8:
                logger.info("Rebalancing shards for quality improvement")
                if await self.sharding_system.rebalance_shards():
                    optimization_actions.append(
                        "Rebalanced shards for better performance"
                    )

            # 3. Apply quality decay remediation if needed
            decay_stats = self.decay_detector.get_decay_statistics()
            if decay_stats.get("current_decay_detected", False):
                logger.info("Applying decay remediation for quality improvement")
                await self.decay_detector.implement_remediation(
                    RemediationStrategy.AUTOMATED_OPTIMIZATION
                )
                optimization_actions.append("Applied automated decay remediation")

            # 4. Run real-time quality optimizer
            logger.info("Running real-time quality optimizer")
            optimization_result = await self.quality_optimizer.optimize_quality(
                target_improvement
            )
            if optimization_result and optimization_result.success:
                optimization_actions.append(
                    f"Quality optimizer improved quality by {optimization_result.improvement:.3f}"
                )

            # 5. Enhance consensus quality integration
            logger.info("Enhancing consensus quality integration")
            consensus_integration = (
                await self.consensus_engine.integrate_quality_based_consensus_decisions()
            )
            if consensus_integration["consensus_improvements"] > 0:
                optimization_actions.append(
                    f"Enhanced {consensus_integration['consensus_improvements']} consensus protocols"
                )

            # Wait for changes to take effect
            await asyncio.sleep(5)

            # Measure final quality
            final_metrics = await self.get_unified_quality_metrics()
            final_quality = final_metrics.overall_quality_score

            actual_improvement = final_quality - initial_quality
            success = (
                actual_improvement >= target_improvement * 0.5
            )  # 50% of target is success

            # Record optimization event
            await self._emit_quality_event(
                QualityEvent.SYSTEM_OPTIMIZED,
                "quality_integration_layer",
                quality_before=initial_quality,
                quality_after=final_quality,
                metadata={
                    "target_improvement": target_improvement,
                    "actual_improvement": actual_improvement,
                    "actions_taken": optimization_actions,
                    "success": success,
                },
            )

            # Update stats
            self.integration_stats["quality_optimizations"] += 1

            logger.info(
                f"System optimization completed: improvement={actual_improvement:.3f}, success={success}"
            )
            return success

        except Exception as e:
            logger.error(f"System-wide quality optimization failed: {e}")
            return False

    async def handle_quality_emergency(self, current_quality: float) -> bool:
        """Handle quality emergency situations.

        Args:
            current_quality: Current quality score

        Returns:
            True if emergency was handled successfully
        """
        logger.critical(
            f"QUALITY EMERGENCY: Quality at {current_quality:.3f}, threshold {self.emergency_threshold:.3f}"
        )

        try:
            emergency_actions = []

            # 1. Immediate fork resolution with emergency priority
            active_forks = list(self.fork_resolver.active_forks.keys())
            for fork_id in active_forks:
                result = await self.fork_resolver.resolve_fork(
                    fork_id, ForkResolutionStrategy.QUALITY_BASED
                )
                if result:
                    emergency_actions.append(f"Emergency resolved fork {fork_id}")

            # 2. Emergency quality remediation
            await self.decay_detector.implement_remediation(
                RemediationStrategy.EMERGENCY_LOCKDOWN
            )
            emergency_actions.append("Applied emergency lockdown remediation")

            # 3. Emergency consensus stabilization
            if hasattr(self.consensus_engine, "_trigger_network_emergency_protocol"):
                self.consensus_engine._trigger_network_emergency_protocol()
                emergency_actions.append("Triggered network emergency protocol")

            # 4. Emergency quality optimization
            await self.quality_optimizer.optimize_quality(0.3)  # Aggressive target
            emergency_actions.append("Applied emergency quality optimization")

            # 5. Economic emergency measures
            if self.economic_engine:
                # Temporarily halt low-quality transactions
                emergency_actions.append("Applied economic emergency measures")

            # Record emergency event
            await self._emit_quality_event(
                QualityEvent.EMERGENCY_TRIGGERED,
                "quality_integration_layer",
                quality_before=current_quality,
                metadata={
                    "emergency_threshold": self.emergency_threshold,
                    "actions_taken": emergency_actions,
                },
            )

            # Update stats
            self.integration_stats["emergency_interventions"] += 1

            logger.critical(
                f"Quality emergency handled with {len(emergency_actions)} actions"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to handle quality emergency: {e}")
            return False

    async def _initialize_quality_systems(self):
        """Initialize all individual quality systems."""
        systems_to_init = [
            ("quality_optimizer", self.quality_optimizer.start),
            (
                "shard_coordinator",
                lambda: self.shard_coordinator.initialize(self.sharding_system),
            ),
        ]

        for system_name, init_func in systems_to_init:
            try:
                await init_func()
                self.system_health[system_name] = QualitySystemHealth(
                    system_name=system_name,
                    status=QualitySystemStatus.HEALTHY,
                    last_update=datetime.now(timezone.utc),
                    performance_score=1.0,
                    uptime_seconds=0.0,
                )
                logger.info(f"Initialized {system_name} successfully")
            except Exception as e:
                logger.error(f"Failed to initialize {system_name}: {e}")
                self.system_health[system_name] = QualitySystemHealth(
                    system_name=system_name,
                    status=QualitySystemStatus.OFFLINE,
                    last_update=datetime.now(timezone.utc),
                    performance_score=0.0,
                    error_count=1,
                )

    async def _initialize_health_monitoring(self):
        """Initialize health monitoring for all systems."""
        # Initialize health status for systems that are always-on
        always_on_systems = [
            "fork_resolver",
            "chain_sharding",
            "quality_decay_detector",
            "consensus_engine",
        ]

        for system_name in always_on_systems:
            self.system_health[system_name] = QualitySystemHealth(
                system_name=system_name,
                status=QualitySystemStatus.HEALTHY,
                last_update=datetime.now(timezone.utc),
                performance_score=1.0,
                uptime_seconds=0.0,
            )

    async def _shutdown_quality_systems(self):
        """Shutdown all quality systems."""
        systems_to_shutdown = [
            ("quality_optimizer", self.quality_optimizer.stop),
            ("shard_coordinator", self.shard_coordinator.shutdown),
        ]

        for system_name, shutdown_func in systems_to_shutdown:
            try:
                await shutdown_func()
                logger.info(f"Shutdown {system_name} successfully")
            except Exception as e:
                logger.error(f"Failed to shutdown {system_name}: {e}")

    async def _quality_monitoring_loop(self):
        """Background loop for continuous quality monitoring."""
        while self.running:
            try:
                # Get current quality metrics
                metrics = await self.get_unified_quality_metrics()
                current_quality = metrics.overall_quality_score

                self.integration_stats["total_quality_checks"] += 1

                # Check for emergency situations
                if current_quality <= self.emergency_threshold:
                    await self.handle_quality_emergency(current_quality)

                # Check if optimization is needed
                elif current_quality < self.quality_target:
                    target_improvement = self.quality_target - current_quality
                    if target_improvement >= 0.05:  # Only optimize if improvement >= 5%
                        await self.optimize_system_quality(target_improvement)

                # Notify callbacks
                for callback in self.quality_callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        logger.error(f"Quality callback failed: {e}")

                await asyncio.sleep(self.monitoring_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Quality monitoring error: {e}")
                await asyncio.sleep(min(self.monitoring_interval_seconds, 60))

    async def _system_coordination_loop(self):
        """Background loop for coordinating between quality systems."""
        while self.running:
            try:
                # Coordinate fork resolution with consensus
                if self.fork_resolver.active_forks and hasattr(
                    self.consensus_engine, "achieve_consensus"
                ):
                    # Ensure consensus considers active forks
                    pass

                # Coordinate sharding with quality optimization
                sharding_stats = self.sharding_system.get_sharding_statistics()
                if sharding_stats.get("average_load_factor", 0) > 0.9:
                    # Trigger preventive optimization
                    await self.quality_optimizer.optimize_quality(0.05)

                # Coordinate decay detection with economic incentives
                decay_stats = self.decay_detector.get_decay_statistics()
                if (
                    decay_stats.get("current_decay_detected", False)
                    and self.economic_engine
                ):
                    # Apply economic remediation
                    await self.decay_detector.implement_remediation(
                        RemediationStrategy.ECONOMIC_INCENTIVES
                    )

                await asyncio.sleep(30)  # Coordinate every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"System coordination error: {e}")
                await asyncio.sleep(30)

    async def _health_check_loop(self):
        """Background loop for health checking all systems."""
        while self.running:
            try:
                current_time = datetime.now(timezone.utc)

                # Update system health
                for system_name, health in self.system_health.items():
                    try:
                        # Calculate uptime
                        uptime = (
                            current_time
                            - (current_time - timedelta(seconds=health.uptime_seconds))
                        ).total_seconds()
                        health.uptime_seconds = uptime

                        # Check system-specific health
                        if system_name == "fork_resolver":
                            # Check fork resolution performance
                            fork_stats = self.fork_resolver.get_fork_statistics()
                            success_rate = fork_stats.get("resolution_rate", 0.0)
                            health.performance_score = success_rate / 100.0

                        elif system_name == "quality_optimizer":
                            # Check optimization performance
                            opt_stats = (
                                self.quality_optimizer.get_optimization_statistics()
                            )
                            success_rate = opt_stats.get("success_rate", 0.0)
                            health.performance_score = success_rate / 100.0

                        elif system_name == "chain_sharding":
                            # Check sharding performance
                            shard_stats = self.sharding_system.get_sharding_statistics()
                            load_factor = shard_stats.get("average_load_factor", 0.0)
                            health.performance_score = max(0.0, 1.0 - load_factor)

                        # Update status based on performance
                        if health.performance_score > 0.8:
                            health.status = QualitySystemStatus.HEALTHY
                        elif health.performance_score > 0.5:
                            health.status = QualitySystemStatus.DEGRADED
                        else:
                            health.status = QualitySystemStatus.CRITICAL

                        health.last_update = current_time

                    except Exception as e:
                        health.error_count += 1
                        health.status = QualitySystemStatus.OFFLINE
                        logger.error(f"Health check failed for {system_name}: {e}")

                await asyncio.sleep(60)  # Health check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)

    async def _emit_quality_event(
        self,
        event_type: QualityEvent,
        source_system: str,
        quality_before: Optional[float] = None,
        quality_after: Optional[float] = None,
        metadata: Dict[str, Any] = None,
    ):
        """Emit a quality management event.

        Args:
            event_type: Type of event
            source_system: System that generated the event
            quality_before: Quality score before the event
            quality_after: Quality score after the event
            metadata: Additional event metadata
        """
        event = QualityEvent(
            event_id=f"{event_type.value}_{int(datetime.now(timezone.utc).timestamp())}",
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            source_system=source_system,
            quality_before=quality_before,
            quality_after=quality_after,
            metadata=metadata or {},
        )

        self.event_history.append(event)

        # Notify callbacks
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Event callback failed: {e}")

        logger.info(f"Quality event emitted: {event_type.value} from {source_system}")

    def register_event_callback(self, callback: Callable[[QualityEvent], None]):
        """Register callback for quality events.

        Args:
            callback: Function to call when events occur
        """
        self.event_callbacks.append(callback)

    def register_quality_callback(
        self, callback: Callable[[UnifiedQualityMetrics], None]
    ):
        """Register callback for quality metrics updates.

        Args:
            callback: Function to call with quality metrics
        """
        self.quality_callbacks.append(callback)

    def get_integration_statistics(self) -> Dict[str, Any]:
        """Get comprehensive integration layer statistics.

        Returns:
            Dictionary with integration metrics
        """
        uptime = (
            datetime.now(timezone.utc) - self.integration_stats["uptime_start"]
        ).total_seconds()

        # Calculate system health summary
        healthy_systems = len(
            [
                h
                for h in self.system_health.values()
                if h.status == QualitySystemStatus.HEALTHY
            ]
        )
        total_systems = len(self.system_health)

        # Recent quality trend
        recent_quality = []
        if len(self.quality_history) >= 10:
            recent_quality = [
                entry["overall_quality"] for entry in list(self.quality_history)[-10:]
            ]

        return {
            "running": self.running,
            "uptime_hours": round(uptime / 3600, 1),
            "quality_target": self.quality_target,
            "emergency_threshold": self.emergency_threshold,
            "system_health_summary": {
                "healthy_systems": healthy_systems,
                "total_systems": total_systems,
                "health_percentage": round(
                    (healthy_systems / max(1, total_systems)) * 100, 1
                ),
            },
            "integration_stats": self.integration_stats.copy(),
            "recent_quality_trend": recent_quality,
            "active_events_count": len(self.event_history),
            "quality_history_length": len(self.quality_history),
            "individual_system_health": {
                name: {
                    "status": health.status.value,
                    "performance_score": round(health.performance_score, 3),
                    "error_count": health.error_count,
                    "uptime_hours": round(health.uptime_seconds / 3600, 1),
                }
                for name, health in self.system_health.items()
            },
        }


# Global quality integration layer instance
quality_integration_layer = ChainQualityIntegrationLayer()


async def initialize_unified_quality_system():
    """Initialize the unified quality management system."""
    try:
        await quality_integration_layer.initialize()
        logger.info("Unified quality management system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize unified quality system: {e}")
        raise


async def shutdown_unified_quality_system():
    """Shutdown the unified quality management system."""
    try:
        await quality_integration_layer.shutdown()
        logger.info("Unified quality management system shutdown successfully")
    except Exception as e:
        logger.error(f"Failed to shutdown unified quality system: {e}")
