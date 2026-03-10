"""
shard_coordinator.py - Cross-Shard Quality Management and Coordination

This module implements coordination between shards to maintain global chain quality
consistency, handle cross-shard references, and ensure quality metrics are properly
aggregated and synchronized across the distributed sharding system.

Key Features:
- Cross-shard quality verification and consistency
- Global quality metric aggregation
- Shard topology management and load balancing
- Cross-shard reference resolution
- Distributed consensus for quality decisions
- Byzantine fault tolerance for shard coordination
- Quality-based shard routing and optimization
"""

import asyncio
import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .cqss import CQSSResult

if TYPE_CHECKING:
    from .chain_sharding import ChainShard, HorizontalChainSharding

logger = logging.getLogger(__name__)


class CoordinationState(str, Enum):
    """States of shard coordination."""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    SYNCHRONIZING = "synchronizing"
    REBALANCING = "rebalancing"
    DEGRADED = "degraded"
    EMERGENCY = "emergency"


class QualityConsistencyLevel(str, Enum):
    """Levels of quality consistency across shards."""

    EVENTUAL = "eventual"  # Eventually consistent quality
    STRONG = "strong"  # Strongly consistent quality
    BOUNDED = "bounded"  # Bounded staleness consistency


@dataclass
class CrossShardReference:
    """Reference between capsules in different shards."""

    source_capsule_id: str
    target_capsule_id: str
    source_shard_id: str
    target_shard_id: str
    reference_type: str  # "parent", "dependency", "citation", etc.
    timestamp: datetime
    verified: bool = False
    quality_impact: float = 0.0  # Impact on quality metrics


@dataclass
class ShardQualitySnapshot:
    """Quality snapshot for a specific shard at a point in time."""

    shard_id: str
    timestamp: datetime
    capsule_count: int
    quality_result: CQSSResult
    cross_shard_refs: List[CrossShardReference]
    health_score: float
    load_factor: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GlobalQualityState:
    """Global quality state across all shards."""

    timestamp: datetime
    total_capsules: int
    total_shards: int
    active_shards: int
    global_quality_score: float
    shard_snapshots: Dict[str, ShardQualitySnapshot]
    cross_shard_references: List[CrossShardReference]
    consistency_level: QualityConsistencyLevel
    quality_variance: float  # Variance in quality across shards
    metadata: Dict[str, Any] = field(default_factory=dict)


class ShardCoordinator:
    """
    Cross-shard quality management and coordination system.

    Manages quality consistency across distributed shards, handles cross-shard
    references, and provides global quality metrics while maintaining performance
    and Byzantine fault tolerance.
    """

    def __init__(
        self,
        consistency_level: QualityConsistencyLevel = QualityConsistencyLevel.BOUNDED,
        max_quality_variance: float = 0.1,
        sync_interval_seconds: int = 300,  # 5 minutes
        byzantine_tolerance: float = 0.33,
    ):
        """Initialize the shard coordinator.

        Args:
            consistency_level: Desired quality consistency level
            max_quality_variance: Maximum allowed quality variance between shards
            sync_interval_seconds: Interval for synchronization operations
            byzantine_tolerance: Maximum fraction of Byzantine shards tolerated
        """
        self.consistency_level = consistency_level
        self.max_quality_variance = max_quality_variance
        self.sync_interval_seconds = sync_interval_seconds
        self.byzantine_tolerance = byzantine_tolerance

        # Coordination state
        self.state = CoordinationState.INITIALIZING
        self.sharding_system: Optional["HorizontalChainSharding"] = None

        # Quality tracking
        self.shard_quality_snapshots: Dict[str, ShardQualitySnapshot] = {}
        self.global_quality_history: List[GlobalQualityState] = []
        self.cross_shard_references: Dict[str, CrossShardReference] = {}

        # Performance monitoring
        self.sync_statistics = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "avg_sync_duration": 0.0,
            "quality_inconsistencies_detected": 0,
            "quality_inconsistencies_resolved": 0,
        }

        # Caching for performance
        self.quality_cache: Dict[str, Any] = {}
        self.cache_ttl_seconds = 60

        # Background tasks
        self.sync_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None

        logger.info(
            f"Initialized shard coordinator with {consistency_level.value} consistency"
        )

    async def initialize(self, sharding_system: "HorizontalChainSharding"):
        """Initialize the coordinator with a sharding system.

        Args:
            sharding_system: The horizontal sharding system to coordinate
        """
        self.sharding_system = sharding_system
        self.state = CoordinationState.ACTIVE

        # Start background tasks
        self.sync_task = asyncio.create_task(self._periodic_sync())
        self.monitoring_task = asyncio.create_task(self._quality_monitoring())

        logger.info("Shard coordinator initialized and active")

    async def shutdown(self):
        """Shutdown the coordinator and cleanup tasks."""
        self.state = CoordinationState.INITIALIZING

        # Cancel background tasks
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Shard coordinator shutdown")

    async def register_cross_shard_reference(
        self,
        source_capsule_id: str,
        target_capsule_id: str,
        reference_type: str = "parent",
    ) -> bool:
        """Register a cross-shard reference between capsules.

        Args:
            source_capsule_id: ID of the source capsule
            target_capsule_id: ID of the target capsule
            reference_type: Type of reference

        Returns:
            True if registered successfully
        """
        if not self.sharding_system:
            return False

        try:
            # Find which shards contain these capsules
            source_shard_id = self.sharding_system.shard_mapping.get(source_capsule_id)
            target_shard_id = self.sharding_system.shard_mapping.get(target_capsule_id)

            if not source_shard_id or not target_shard_id:
                logger.warning(
                    f"Could not find shards for cross-reference: {source_capsule_id} -> {target_capsule_id}"
                )
                return False

            if source_shard_id == target_shard_id:
                # Not actually a cross-shard reference
                return True

            # Create cross-shard reference
            ref_id = f"{source_capsule_id}:{target_capsule_id}"
            cross_ref = CrossShardReference(
                source_capsule_id=source_capsule_id,
                target_capsule_id=target_capsule_id,
                source_shard_id=source_shard_id,
                target_shard_id=target_shard_id,
                reference_type=reference_type,
                timestamp=datetime.now(timezone.utc),
            )

            self.cross_shard_references[ref_id] = cross_ref

            # Verify the reference
            await self._verify_cross_shard_reference(cross_ref)

            logger.debug(
                f"Registered cross-shard reference: {source_shard_id} -> {target_shard_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to register cross-shard reference: {e}")
            return False

    async def get_capsule_quality_score(self, capsule_id: str) -> float:
        """Get quality score for a specific capsule across shards.

        Args:
            capsule_id: ID of the capsule

        Returns:
            Quality score (0.0 to 1.0)
        """
        if not self.sharding_system:
            return 0.0

        # Check cache first
        cache_key = f"quality_{capsule_id}"
        if cache_key in self.quality_cache:
            cached_time, cached_score = self.quality_cache[cache_key]
            if (
                datetime.now(timezone.utc) - cached_time
            ).seconds < self.cache_ttl_seconds:
                return cached_score

        try:
            # Find the shard containing this capsule
            shard_id = self.sharding_system.shard_mapping.get(capsule_id)
            if not shard_id or shard_id not in self.sharding_system.shards:
                return 0.0

            shard = self.sharding_system.shards[shard_id]

            # Get capsule from shard
            capsule = shard.capsules.get(capsule_id)
            if not capsule:
                return 0.0

            # Use shard's quality metrics or compute individual quality
            if shard_id in self.shard_quality_snapshots:
                snapshot = self.shard_quality_snapshots[shard_id]
                # Use shard's overall quality as baseline
                base_score = snapshot.quality_result.get_overall_score() or 0.0

                # Adjust based on capsule-specific factors
                confidence = getattr(capsule, "confidence", 0.5)
                capsule_score = (base_score * 0.7) + (confidence * 0.3)
            else:
                # Fallback to capsule confidence
                capsule_score = getattr(capsule, "confidence", 0.5)

            # Cache the result
            self.quality_cache[cache_key] = (datetime.now(timezone.utc), capsule_score)

            return capsule_score

        except Exception as e:
            logger.error(f"Failed to get quality score for capsule {capsule_id}: {e}")
            return 0.0

    async def compute_global_quality_metrics(self) -> Optional[GlobalQualityState]:
        """Compute global quality metrics across all shards.

        Returns:
            Global quality state or None if computation failed
        """
        if not self.sharding_system or not self.sharding_system.shards:
            return None

        try:
            start_time = datetime.now(timezone.utc)

            # Collect quality snapshots from all shards
            shard_snapshots = {}
            total_capsules = 0
            active_shards = 0
            quality_scores = []

            for shard_id, shard in self.sharding_system.shards.items():
                try:
                    # Create quality snapshot for this shard
                    snapshot = await self._create_shard_quality_snapshot(shard)
                    if snapshot:
                        shard_snapshots[shard_id] = snapshot
                        total_capsules += snapshot.capsule_count

                        if snapshot.health_score > 0.5:  # Consider healthy if > 50%
                            active_shards += 1

                        quality_score = snapshot.quality_result.get_overall_score()
                        if quality_score is not None:
                            quality_scores.append(quality_score)

                except Exception as e:
                    logger.warning(
                        f"Failed to create snapshot for shard {shard_id}: {e}"
                    )
                    continue

            if not quality_scores:
                return None

            # Calculate global quality metrics
            global_quality_score = statistics.mean(quality_scores)
            quality_variance = (
                statistics.variance(quality_scores) if len(quality_scores) > 1 else 0.0
            )

            # Determine consistency level achieved
            if quality_variance <= self.max_quality_variance / 10:
                achieved_consistency = QualityConsistencyLevel.STRONG
            elif quality_variance <= self.max_quality_variance:
                achieved_consistency = QualityConsistencyLevel.BOUNDED
            else:
                achieved_consistency = QualityConsistencyLevel.EVENTUAL

            # Create global state
            global_state = GlobalQualityState(
                timestamp=start_time,
                total_capsules=total_capsules,
                total_shards=len(self.sharding_system.shards),
                active_shards=active_shards,
                global_quality_score=global_quality_score,
                shard_snapshots=shard_snapshots,
                cross_shard_references=list(self.cross_shard_references.values()),
                consistency_level=achieved_consistency,
                quality_variance=quality_variance,
                metadata={
                    "computation_duration_ms": (
                        datetime.now(timezone.utc) - start_time
                    ).total_seconds()
                    * 1000,
                    "quality_score_range": (min(quality_scores), max(quality_scores)),
                    "cross_shard_ref_count": len(self.cross_shard_references),
                },
            )

            # Store in history
            self.global_quality_history.append(global_state)

            # Keep only recent history (last 100 states)
            if len(self.global_quality_history) > 100:
                self.global_quality_history.pop(0)

            # Update shard snapshots
            self.shard_quality_snapshots.update(shard_snapshots)

            logger.debug(
                f"Computed global quality: {global_quality_score:.3f} (variance: {quality_variance:.3f})"
            )
            return global_state

        except Exception as e:
            logger.error(f"Failed to compute global quality metrics: {e}")
            return None

    async def detect_quality_inconsistencies(self) -> List[Dict[str, Any]]:
        """Detect quality inconsistencies across shards.

        Returns:
            List of detected inconsistencies
        """
        inconsistencies = []

        if not self.shard_quality_snapshots:
            return inconsistencies

        try:
            # Get all quality scores
            quality_scores = []
            shard_data = []

            for shard_id, snapshot in self.shard_quality_snapshots.items():
                quality_score = snapshot.quality_result.get_overall_score()
                if quality_score is not None:
                    quality_scores.append(quality_score)
                    shard_data.append((shard_id, quality_score, snapshot))

            if len(quality_scores) < 2:
                return inconsistencies

            # Calculate statistics
            mean_quality = statistics.mean(quality_scores)
            quality_stdev = (
                statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0.0
            )

            # Detect outliers (shards with quality > 2 standard deviations from mean)
            outlier_threshold = 2.0 * quality_stdev

            for shard_id, quality_score, snapshot in shard_data:
                deviation = abs(quality_score - mean_quality)

                if (
                    deviation > outlier_threshold and deviation > 0.1
                ):  # Significant deviation
                    inconsistency = {
                        "type": "quality_outlier",
                        "shard_id": shard_id,
                        "shard_quality": quality_score,
                        "global_mean": mean_quality,
                        "deviation": deviation,
                        "severity": min(1.0, deviation / 0.5),  # Normalize severity
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "metadata": {
                            "capsule_count": snapshot.capsule_count,
                            "health_score": snapshot.health_score,
                            "cross_shard_refs": len(snapshot.cross_shard_refs),
                        },
                    }
                    inconsistencies.append(inconsistency)

            # Detect high variance
            if quality_stdev > self.max_quality_variance:
                inconsistencies.append(
                    {
                        "type": "high_variance",
                        "variance": quality_stdev,
                        "max_allowed": self.max_quality_variance,
                        "severity": min(
                            1.0, quality_stdev / (self.max_quality_variance * 2)
                        ),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "metadata": {
                            "affected_shards": len(shard_data),
                            "quality_range": (min(quality_scores), max(quality_scores)),
                        },
                    }
                )

            # Detect Byzantine behavior patterns
            byzantine_inconsistencies = await self._detect_byzantine_quality_patterns(
                shard_data
            )
            inconsistencies.extend(byzantine_inconsistencies)

            if inconsistencies:
                self.sync_statistics["quality_inconsistencies_detected"] += len(
                    inconsistencies
                )
                logger.warning(
                    f"Detected {len(inconsistencies)} quality inconsistencies"
                )

            return inconsistencies

        except Exception as e:
            logger.error(f"Failed to detect quality inconsistencies: {e}")
            return []

    async def resolve_quality_inconsistencies(
        self, inconsistencies: List[Dict[str, Any]]
    ) -> int:
        """Resolve detected quality inconsistencies.

        Args:
            inconsistencies: List of inconsistencies to resolve

        Returns:
            Number of inconsistencies resolved
        """
        resolved_count = 0

        for inconsistency in inconsistencies:
            try:
                inconsistency_type = inconsistency.get("type")

                if inconsistency_type == "quality_outlier":
                    if await self._resolve_quality_outlier(inconsistency):
                        resolved_count += 1

                elif inconsistency_type == "high_variance":
                    if await self._resolve_high_variance(inconsistency):
                        resolved_count += 1

                elif inconsistency_type == "byzantine_pattern":
                    if await self._resolve_byzantine_pattern(inconsistency):
                        resolved_count += 1

            except Exception as e:
                logger.error(
                    f"Failed to resolve inconsistency {inconsistency.get('type', 'unknown')}: {e}"
                )

        if resolved_count > 0:
            self.sync_statistics["quality_inconsistencies_resolved"] += resolved_count
            logger.info(
                f"Resolved {resolved_count}/{len(inconsistencies)} quality inconsistencies"
            )

        return resolved_count

    async def _periodic_sync(self):
        """Periodic synchronization of shard quality metrics."""
        while self.state == CoordinationState.ACTIVE:
            try:
                sync_start = datetime.now(timezone.utc)

                # Compute global quality metrics
                global_state = await self.compute_global_quality_metrics()

                if global_state:
                    # Detect inconsistencies
                    inconsistencies = await self.detect_quality_inconsistencies()

                    # Resolve inconsistencies
                    if inconsistencies:
                        await self.resolve_quality_inconsistencies(inconsistencies)

                    # Update statistics
                    self.sync_statistics["total_syncs"] += 1
                    self.sync_statistics["successful_syncs"] += 1

                    sync_duration = (
                        datetime.now(timezone.utc) - sync_start
                    ).total_seconds()
                    self.sync_statistics["avg_sync_duration"] = (
                        self.sync_statistics["avg_sync_duration"] * 0.9
                        + sync_duration * 0.1
                    )
                else:
                    self.sync_statistics["failed_syncs"] += 1

                # Wait for next sync interval
                await asyncio.sleep(self.sync_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic sync failed: {e}")
                self.sync_statistics["failed_syncs"] += 1
                await asyncio.sleep(
                    min(self.sync_interval_seconds, 60)
                )  # Backoff on error

    async def _quality_monitoring(self):
        """Background quality monitoring and alerting."""
        while self.state == CoordinationState.ACTIVE:
            try:
                # Monitor global quality trends
                if len(self.global_quality_history) >= 3:
                    recent_states = self.global_quality_history[-3:]

                    # Check for quality degradation
                    quality_trend = [s.global_quality_score for s in recent_states]

                    if all(
                        quality_trend[i] > quality_trend[i + 1]
                        for i in range(len(quality_trend) - 1)
                    ):
                        # Consistent degradation
                        degradation = quality_trend[0] - quality_trend[-1]
                        if degradation > 0.1:  # 10% degradation
                            logger.warning(
                                f"Global quality degradation detected: {degradation:.3f}"
                            )

                            # Switch to emergency mode if severe
                            if degradation > 0.3:
                                self.state = CoordinationState.EMERGENCY

                # Monitor shard health
                unhealthy_shards = 0
                for snapshot in self.shard_quality_snapshots.values():
                    if snapshot.health_score < 0.3:
                        unhealthy_shards += 1

                if (
                    unhealthy_shards
                    > len(self.shard_quality_snapshots) * self.byzantine_tolerance
                ):
                    logger.critical(
                        f"Too many unhealthy shards: {unhealthy_shards}/{len(self.shard_quality_snapshots)}"
                    )
                    self.state = CoordinationState.DEGRADED

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Quality monitoring failed: {e}")
                await asyncio.sleep(60)

    async def _create_shard_quality_snapshot(
        self, shard: "ChainShard"
    ) -> Optional[ShardQualitySnapshot]:
        """Create a quality snapshot for a shard.

        Args:
            shard: Shard to create snapshot for

        Returns:
            Quality snapshot or None if failed
        """
        try:
            # Get shard's quality result
            async def verify_capsule(capsule):
                return True, "verified"  # Simplified verification

            quality_result = await shard.compute_shard_quality(verify_capsule)

            # Get cross-shard references for this shard
            cross_refs = [
                ref
                for ref in self.cross_shard_references.values()
                if ref.source_shard_id == shard.shard_id
                or ref.target_shard_id == shard.shard_id
            ]

            # Calculate health and load
            health_score = shard.metrics.health_score if shard.metrics else 0.5
            load_factor = (
                shard.metrics.calculate_load_factor() if shard.metrics else 0.5
            )

            snapshot = ShardQualitySnapshot(
                shard_id=shard.shard_id,
                timestamp=datetime.now(timezone.utc),
                capsule_count=len(shard.capsules),
                quality_result=quality_result,
                cross_shard_refs=cross_refs,
                health_score=health_score,
                load_factor=load_factor,
                metadata={
                    "state": shard.state.value,
                    "memory_usage_mb": shard.metrics.memory_usage_bytes / (1024 * 1024)
                    if shard.metrics
                    else 0,
                },
            )

            return snapshot

        except Exception as e:
            logger.error(f"Failed to create snapshot for shard {shard.shard_id}: {e}")
            return None

    async def _verify_cross_shard_reference(
        self, cross_ref: CrossShardReference
    ) -> bool:
        """Verify a cross-shard reference.

        Args:
            cross_ref: Cross-shard reference to verify

        Returns:
            True if reference is valid
        """
        if not self.sharding_system:
            return False

        try:
            # Check that both capsules exist in their respective shards
            source_shard = self.sharding_system.shards.get(cross_ref.source_shard_id)
            target_shard = self.sharding_system.shards.get(cross_ref.target_shard_id)

            if not source_shard or not target_shard:
                return False

            source_exists = cross_ref.source_capsule_id in source_shard.capsules
            target_exists = cross_ref.target_capsule_id in target_shard.capsules

            if source_exists and target_exists:
                cross_ref.verified = True
                cross_ref.quality_impact = (
                    0.05  # Small positive impact for valid references
                )
                return True
            else:
                cross_ref.verified = False
                cross_ref.quality_impact = -0.1  # Negative impact for broken references
                return False

        except Exception as e:
            logger.error(f"Failed to verify cross-shard reference: {e}")
            cross_ref.verified = False
            return False

    async def _detect_byzantine_quality_patterns(
        self, shard_data: List[Tuple[str, float, ShardQualitySnapshot]]
    ) -> List[Dict[str, Any]]:
        """Detect Byzantine behavior patterns in shard quality reports.

        Args:
            shard_data: List of (shard_id, quality_score, snapshot) tuples

        Returns:
            List of detected Byzantine patterns
        """
        patterns = []

        try:
            if len(shard_data) < 3:
                return patterns

            # Look for suspiciously consistent quality scores (possible collusion)
            quality_scores = [score for _, score, _ in shard_data]

            # Group shards by similar quality scores
            score_groups = defaultdict(list)
            for shard_id, score, snapshot in shard_data:
                # Round to 2 decimal places for grouping
                rounded_score = round(score, 2)
                score_groups[rounded_score].append((shard_id, score, snapshot))

            # Check for suspiciously large groups with identical scores
            for score, group in score_groups.items():
                if len(group) > len(shard_data) * 0.6:  # More than 60% have same score
                    patterns.append(
                        {
                            "type": "byzantine_pattern",
                            "pattern": "identical_scores",
                            "affected_shards": [shard_id for shard_id, _, _ in group],
                            "suspicious_score": score,
                            "severity": min(1.0, len(group) / len(shard_data)),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

            # Look for implausible quality reports
            statistics.mean(quality_scores)
            for shard_id, score, snapshot in shard_data:
                # Check for impossibly high quality with low health
                if score > 0.95 and snapshot.health_score < 0.3:
                    patterns.append(
                        {
                            "type": "byzantine_pattern",
                            "pattern": "implausible_quality",
                            "affected_shards": [shard_id],
                            "reported_quality": score,
                            "health_score": snapshot.health_score,
                            "severity": 0.8,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

        except Exception as e:
            logger.error(f"Failed to detect Byzantine patterns: {e}")

        return patterns

    async def _resolve_quality_outlier(self, inconsistency: Dict[str, Any]) -> bool:
        """Resolve quality outlier inconsistency.

        Args:
            inconsistency: Quality outlier inconsistency

        Returns:
            True if resolved
        """
        try:
            shard_id = inconsistency.get("shard_id")
            if not shard_id or not self.sharding_system:
                return False

            # Recompute quality for the outlier shard
            shard = self.sharding_system.shards.get(shard_id)
            if shard:
                # Clear quality cache for this shard
                shard.quality_cache.clear()

                # Trigger recomputation
                snapshot = await self._create_shard_quality_snapshot(shard)
                if snapshot:
                    self.shard_quality_snapshots[shard_id] = snapshot
                    logger.info(f"Recomputed quality for outlier shard {shard_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to resolve quality outlier: {e}")
            return False

    async def _resolve_high_variance(self, inconsistency: Dict[str, Any]) -> bool:
        """Resolve high variance inconsistency.

        Args:
            inconsistency: High variance inconsistency

        Returns:
            True if resolved
        """
        try:
            # Trigger rebalancing if sharding system supports it
            if self.sharding_system and hasattr(
                self.sharding_system, "rebalance_shards"
            ):
                success = await self.sharding_system.rebalance_shards()
                if success:
                    logger.info(
                        "Triggered shard rebalancing to reduce quality variance"
                    )
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to resolve high variance: {e}")
            return False

    async def _resolve_byzantine_pattern(self, inconsistency: Dict[str, Any]) -> bool:
        """Resolve Byzantine pattern inconsistency.

        Args:
            inconsistency: Byzantine pattern inconsistency

        Returns:
            True if resolved
        """
        try:
            affected_shards = inconsistency.get("affected_shards", [])
            pattern = inconsistency.get("pattern", "unknown")

            # Apply penalties or corrections based on pattern
            if pattern == "identical_scores":
                # Force recomputation for all affected shards
                for shard_id in affected_shards:
                    if self.sharding_system and shard_id in self.sharding_system.shards:
                        shard = self.sharding_system.shards[shard_id]
                        shard.quality_cache.clear()

                logger.warning(
                    f"Cleared quality cache for {len(affected_shards)} shards with suspicious identical scores"
                )
                return True

            elif pattern == "implausible_quality":
                # Mark affected shards for closer monitoring
                for shard_id in affected_shards:
                    logger.warning(
                        f"Shard {shard_id} marked for monitoring due to implausible quality report"
                    )
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to resolve Byzantine pattern: {e}")
            return False

    def get_coordination_statistics(self) -> Dict[str, Any]:
        """Get comprehensive coordination statistics.

        Returns:
            Dictionary with coordination metrics
        """
        return {
            "coordination_state": self.state.value,
            "consistency_level": self.consistency_level.value,
            "sync_statistics": self.sync_statistics.copy(),
            "active_shards": len(self.shard_quality_snapshots),
            "cross_shard_references": len(self.cross_shard_references),
            "verified_references": len(
                [ref for ref in self.cross_shard_references.values() if ref.verified]
            ),
            "global_quality_history_length": len(self.global_quality_history),
            "current_quality_variance": (
                self.global_quality_history[-1].quality_variance
                if self.global_quality_history
                else 0.0
            ),
            "max_allowed_variance": self.max_quality_variance,
            "byzantine_tolerance": self.byzantine_tolerance,
            "cache_size": len(self.quality_cache),
            "recent_global_quality": (
                self.global_quality_history[-1].global_quality_score
                if self.global_quality_history
                else 0.0
            ),
        }


# Global shard coordinator instance
shard_coordinator = ShardCoordinator()
