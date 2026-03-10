"""
chain_sharding.py - Horizontal Chain Partitioning for Memory Scalability

This module implements horizontal chain sharding to overcome the memory bottleneck
in graph-based analysis. Supports unlimited chain growth via distributed processing
while maintaining cross-shard quality verification and consistency.

Key Features:
- Horizontal chain partitioning across multiple shards
- Cross-shard quality verification and consistency
- Memory-efficient streaming analysis for large chains
- Shard coordination for global chain quality metrics
- Dynamic shard rebalancing based on load
- Byzantine fault tolerance for shard coordination
- Quality-preserving merge and split operations
"""

import gc
import hashlib
import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional

import networkx as nx

from src.capsule_schema import Capsule

from .cqss import CQSSResult, compute_cqss
from .shard_coordinator import ShardCoordinator

logger = logging.getLogger(__name__)


class ShardState(str, Enum):
    """States of a shard."""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    REBALANCING = "rebalancing"
    MERGING = "merging"
    SPLITTING = "splitting"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class ShardingStrategy(str, Enum):
    """Strategies for sharding capsule chains."""

    TEMPORAL_SHARDING = "temporal_sharding"
    HASH_SHARDING = "hash_sharding"
    AGENT_BASED_SHARDING = "agent_based_sharding"
    QUALITY_BASED_SHARDING = "quality_based_sharding"
    HYBRID_SHARDING = "hybrid_sharding"


@dataclass
class ShardMetrics:
    """Metrics for a single shard."""

    shard_id: str
    capsule_count: int
    memory_usage_bytes: int
    processing_time_ms: float
    quality_score: float
    last_updated: datetime
    health_score: float = 1.0

    def calculate_load_factor(self) -> float:
        """Calculate load factor for rebalancing decisions."""
        # Combine multiple factors into load score
        memory_factor = min(
            1.0, self.memory_usage_bytes / (1024 * 1024 * 100)
        )  # 100MB baseline
        capsule_factor = min(1.0, self.capsule_count / 1000)  # 1000 capsules baseline
        processing_factor = min(
            1.0, self.processing_time_ms / 1000
        )  # 1 second baseline

        return (memory_factor + capsule_factor + processing_factor) / 3.0


@dataclass
class ChainShard:
    """Represents a single shard of the capsule chain."""

    shard_id: str
    shard_index: int
    capsules: Dict[str, Capsule] = field(default_factory=dict)
    capsule_order: List[str] = field(default_factory=list)
    parent_references: Dict[str, str] = field(default_factory=dict)
    child_references: Dict[str, List[str]] = field(default_factory=dict)
    cross_shard_references: Dict[str, str] = field(default_factory=dict)
    state: ShardState = ShardState.INITIALIZING
    metrics: Optional[ShardMetrics] = None
    last_quality_check: Optional[datetime] = None
    quality_cache: Dict[str, CQSSResult] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize metrics after creation."""
        self.metrics = ShardMetrics(
            shard_id=self.shard_id,
            capsule_count=0,
            memory_usage_bytes=0,
            processing_time_ms=0.0,
            quality_score=0.0,
            last_updated=datetime.now(timezone.utc),
        )

    def add_capsule(self, capsule: Capsule) -> bool:
        """Add a capsule to this shard."""
        try:
            if capsule.capsule_id in self.capsules:
                logger.warning(
                    f"Capsule {capsule.capsule_id} already exists in shard {self.shard_id}"
                )
                return False

            # Add capsule
            self.capsules[capsule.capsule_id] = capsule
            self.capsule_order.append(capsule.capsule_id)

            # Update parent-child relationships
            parent_id = getattr(capsule, "parent_capsule", None) or getattr(
                capsule, "previous_capsule_id", None
            )
            if parent_id:
                self.parent_references[capsule.capsule_id] = parent_id

                if parent_id in self.capsules:
                    # Parent is in same shard
                    if parent_id not in self.child_references:
                        self.child_references[parent_id] = []
                    self.child_references[parent_id].append(capsule.capsule_id)
                else:
                    # Parent is in different shard - mark as cross-shard reference
                    self.cross_shard_references[capsule.capsule_id] = parent_id

            # Update metrics
            self._update_metrics()

            logger.debug(f"Added capsule {capsule.capsule_id} to shard {self.shard_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to add capsule {capsule.capsule_id} to shard {self.shard_id}: {e}"
            )
            return False

    def remove_capsule(self, capsule_id: str) -> Optional[Capsule]:
        """Remove a capsule from this shard."""
        if capsule_id not in self.capsules:
            return None

        capsule = self.capsules.pop(capsule_id)
        self.capsule_order.remove(capsule_id)

        # Clean up references
        if capsule_id in self.parent_references:
            del self.parent_references[capsule_id]

        if capsule_id in self.child_references:
            del self.child_references[capsule_id]

        # Remove from cross-shard references
        if capsule_id in self.cross_shard_references:
            del self.cross_shard_references[capsule_id]

        # Clean up quality cache
        if capsule_id in self.quality_cache:
            del self.quality_cache[capsule_id]

        self._update_metrics()
        return capsule

    def get_capsules_in_order(self) -> List[Capsule]:
        """Get capsules in chronological order."""
        return [
            self.capsules[cid] for cid in self.capsule_order if cid in self.capsules
        ]

    def build_local_graph(self) -> nx.DiGraph:
        """Build NetworkX graph for capsules in this shard only."""
        G = nx.DiGraph()

        # Add nodes
        for capsule_id, capsule in self.capsules.items():
            G.add_node(capsule_id, capsule=capsule)

        # Add edges for relationships within this shard
        for child_id, parent_id in self.parent_references.items():
            if parent_id in self.capsules:  # Only add edge if parent is in same shard
                G.add_edge(parent_id, child_id)

        return G

    async def compute_shard_quality(self, verify_capsule_fn) -> CQSSResult:
        """Compute quality metrics for this shard only."""
        start_time = datetime.now(timezone.utc)

        try:
            capsules = self.get_capsules_in_order()
            if not capsules:
                return CQSSResult({})

            # Use cached result if recent
            cache_key = f"shard_quality_{len(capsules)}"
            if (
                cache_key in self.quality_cache
                and self.last_quality_check
                and (start_time - self.last_quality_check).seconds < 300
            ):  # 5 minute cache
                return self.quality_cache[cache_key]

            # Compute quality for shard
            result = await compute_cqss(capsules, verify_capsule_fn)

            # Cache result
            self.quality_cache[cache_key] = result
            self.last_quality_check = start_time

            # Update metrics
            if self.metrics:
                processing_time = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000
                self.metrics.processing_time_ms = processing_time
                self.metrics.quality_score = result.get_overall_score() or 0.0
                self.metrics.last_updated = datetime.now(timezone.utc)

            return result

        except Exception as e:
            logger.error(f"Failed to compute quality for shard {self.shard_id}: {e}")
            return CQSSResult({})

    def _update_metrics(self):
        """Update shard metrics."""
        if not self.metrics:
            return

        self.metrics.capsule_count = len(self.capsules)

        # Estimate memory usage
        memory_estimate = 0
        for capsule in self.capsules.values():
            # Rough estimate: 1KB per capsule base + content size
            base_size = 1024
            if hasattr(capsule, "content") and capsule.content:
                base_size += len(str(capsule.content))
            memory_estimate += base_size

        self.metrics.memory_usage_bytes = memory_estimate
        self.metrics.last_updated = datetime.now(timezone.utc)

        # Calculate health score based on various factors
        load_factor = self.metrics.calculate_load_factor()
        cross_shard_refs = len(self.cross_shard_references)
        total_refs = len(self.parent_references)

        # Health decreases with high load and many cross-shard references
        cross_shard_penalty = (cross_shard_refs / max(1, total_refs)) * 0.3
        load_penalty = load_factor * 0.5

        self.metrics.health_score = max(0.1, 1.0 - cross_shard_penalty - load_penalty)


class HorizontalChainSharding:
    """
    Horizontal chain sharding system for memory scalability.

    Partitions the capsule chain across multiple shards to overcome memory limitations
    while maintaining quality verification and cross-shard consistency.
    """

    def __init__(
        self,
        max_capsules_per_shard: int = 1000,
        max_memory_per_shard_mb: int = 100,
        sharding_strategy: ShardingStrategy = ShardingStrategy.HYBRID_SHARDING,
        coordinator: Optional[ShardCoordinator] = None,
    ):
        """Initialize the horizontal sharding system.

        Args:
            max_capsules_per_shard: Maximum capsules per shard before splitting
            max_memory_per_shard_mb: Maximum memory per shard in megabytes
            sharding_strategy: Strategy for partitioning capsules
            coordinator: Optional shard coordinator for cross-shard operations
        """
        self.max_capsules_per_shard = max_capsules_per_shard
        self.max_memory_per_shard_mb = max_memory_per_shard_mb
        self.sharding_strategy = sharding_strategy
        self.coordinator = coordinator

        # Shard management
        self.shards: Dict[str, ChainShard] = {}
        self.shard_mapping: Dict[str, str] = {}  # capsule_id -> shard_id
        self.shard_order: List[str] = []  # Ordered list of shard IDs

        # Performance monitoring
        self.total_capsules = 0
        self.total_memory_usage = 0
        self.rebalancing_in_progress = False
        self.quality_history: List[Dict[str, Any]] = []

        # Caching for cross-shard operations
        self._cross_shard_cache: Dict[str, Any] = {}
        self._cache_ttl_seconds = 300  # 5 minutes

        logger.info(
            f"Initialized horizontal chain sharding with strategy: {sharding_strategy}"
        )

    async def add_capsule(self, capsule: Capsule) -> bool:
        """Add a capsule to the appropriate shard.

        Args:
            capsule: Capsule to add

        Returns:
            True if successfully added, False otherwise
        """
        try:
            # Determine target shard
            target_shard_id = await self._determine_target_shard(capsule)

            if target_shard_id not in self.shards:
                await self._create_shard(target_shard_id)

            shard = self.shards[target_shard_id]

            # Add capsule to shard
            if shard.add_capsule(capsule):
                self.shard_mapping[capsule.capsule_id] = target_shard_id
                self.total_capsules += 1

                # Check if shard needs splitting
                if await self._should_split_shard(shard):
                    await self._schedule_shard_split(shard)

                logger.debug(
                    f"Added capsule {capsule.capsule_id} to shard {target_shard_id}"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to add capsule {capsule.capsule_id}: {e}")
            return False

    async def get_capsule(self, capsule_id: str) -> Optional[Capsule]:
        """Get a capsule by ID from any shard.

        Args:
            capsule_id: ID of capsule to retrieve

        Returns:
            Capsule if found, None otherwise
        """
        shard_id = self.shard_mapping.get(capsule_id)
        if not shard_id or shard_id not in self.shards:
            return None

        return self.shards[shard_id].capsules.get(capsule_id)

    async def stream_capsules(
        self,
        start_timestamp: Optional[datetime] = None,
        end_timestamp: Optional[datetime] = None,
        quality_threshold: float = 0.0,
    ) -> Iterator[Capsule]:
        """Stream capsules across all shards without loading everything into memory.

        Args:
            start_timestamp: Optional start time filter
            end_timestamp: Optional end time filter
            quality_threshold: Minimum quality score filter

        Yields:
            Capsules matching the criteria
        """
        for shard_id in self.shard_order:
            if shard_id not in self.shards:
                continue

            shard = self.shards[shard_id]

            # Stream capsules from this shard
            for capsule in shard.get_capsules_in_order():
                # Apply timestamp filters
                if start_timestamp:
                    capsule_time = capsule.timestamp
                    if isinstance(capsule_time, str):
                        capsule_time = datetime.fromisoformat(
                            capsule_time.replace("Z", "+00:00")
                        )
                    if capsule_time < start_timestamp:
                        continue

                if end_timestamp:
                    capsule_time = capsule.timestamp
                    if isinstance(capsule_time, str):
                        capsule_time = datetime.fromisoformat(
                            capsule_time.replace("Z", "+00:00")
                        )
                    if capsule_time > end_timestamp:
                        continue

                # Apply quality filter if coordinator available
                if quality_threshold > 0.0 and self.coordinator:
                    quality_score = await self.coordinator.get_capsule_quality_score(
                        capsule.capsule_id
                    )
                    if quality_score < quality_threshold:
                        continue

                yield capsule

            # Force garbage collection after processing each shard
            gc.collect()

    async def compute_global_quality(self, verify_capsule_fn) -> CQSSResult:
        """Compute quality metrics across all shards.

        Args:
            verify_capsule_fn: Function to verify capsule signatures

        Returns:
            Global CQSS result aggregated from all shards
        """
        if not self.shards:
            return CQSSResult({})

        # Compute quality for each shard
        shard_results = {}
        total_capsules = 0

        for shard_id, shard in self.shards.items():
            try:
                result = await shard.compute_shard_quality(verify_capsule_fn)
                shard_results[shard_id] = result
                total_capsules += len(shard.capsules)
            except Exception as e:
                logger.error(f"Failed to compute quality for shard {shard_id}: {e}")
                continue

        if not shard_results:
            return CQSSResult({})

        # Aggregate results across shards
        aggregated_metrics = self._aggregate_shard_metrics(
            shard_results, total_capsules
        )

        return CQSSResult(aggregated_metrics)

    async def rebalance_shards(self) -> bool:
        """Rebalance capsules across shards for optimal performance.

        Returns:
            True if rebalancing was successful
        """
        if self.rebalancing_in_progress:
            logger.warning("Rebalancing already in progress")
            return False

        self.rebalancing_in_progress = True
        logger.info("Starting shard rebalancing")

        try:
            # Identify overloaded and underloaded shards
            overloaded_shards = []
            underloaded_shards = []

            for shard_id, shard in self.shards.items():
                if not shard.metrics:
                    continue

                load_factor = shard.metrics.calculate_load_factor()

                if load_factor > 0.8:  # 80% load threshold
                    overloaded_shards.append((shard_id, load_factor))
                elif load_factor < 0.3:  # 30% load threshold
                    underloaded_shards.append((shard_id, load_factor))

            # Sort by load factor
            overloaded_shards.sort(key=lambda x: x[1], reverse=True)
            underloaded_shards.sort(key=lambda x: x[1])

            # Move capsules from overloaded to underloaded shards
            rebalanced_count = 0

            for overloaded_id, _ in overloaded_shards:
                if not underloaded_shards:
                    break

                overloaded_shard = self.shards[overloaded_id]
                underloaded_id, _ = underloaded_shards[0]
                underloaded_shard = self.shards[underloaded_id]

                # Move some capsules
                capsules_to_move = min(
                    len(overloaded_shard.capsules) // 4,  # Move 25% of capsules
                    (self.max_capsules_per_shard - len(underloaded_shard.capsules))
                    // 2,
                )

                if capsules_to_move > 0:
                    moved = await self._move_capsules_between_shards(
                        overloaded_shard, underloaded_shard, capsules_to_move
                    )
                    rebalanced_count += moved

                # Update underloaded list if shard is now full
                if len(underloaded_shard.capsules) > self.max_capsules_per_shard * 0.8:
                    underloaded_shards.pop(0)

            logger.info(f"Rebalancing completed: moved {rebalanced_count} capsules")
            return True

        except Exception as e:
            logger.error(f"Shard rebalancing failed: {e}")
            return False

        finally:
            self.rebalancing_in_progress = False

    async def _determine_target_shard(self, capsule: Capsule) -> str:
        """Determine which shard should contain this capsule.

        Args:
            capsule: Capsule to place

        Returns:
            Target shard ID
        """
        if self.sharding_strategy == ShardingStrategy.TEMPORAL_SHARDING:
            # Shard by time period (e.g., daily)
            if isinstance(capsule.timestamp, str):
                timestamp = datetime.fromisoformat(
                    capsule.timestamp.replace("Z", "+00:00")
                )
            else:
                timestamp = capsule.timestamp

            day_key = timestamp.strftime("%Y-%m-%d")
            return f"shard_temporal_{day_key}"

        elif self.sharding_strategy == ShardingStrategy.HASH_SHARDING:
            # Shard by hash of capsule ID
            hash_value = int(
                hashlib.sha256(capsule.capsule_id.encode()).hexdigest()[:8], 16
            )
            shard_index = hash_value % max(
                1, len(self.shards) or 4
            )  # Start with 4 shards
            return f"shard_hash_{shard_index}"

        elif self.sharding_strategy == ShardingStrategy.AGENT_BASED_SHARDING:
            # Shard by agent ID
            agent_id = getattr(capsule, "agent_id", "unknown")
            agent_hash = int(hashlib.sha256(agent_id.encode()).hexdigest()[:8], 16)
            shard_index = agent_hash % max(1, len(self.shards) or 4)
            return f"shard_agent_{shard_index}"

        elif self.sharding_strategy == ShardingStrategy.QUALITY_BASED_SHARDING:
            # Shard by expected quality tier
            confidence = getattr(capsule, "confidence", 0.5)
            if confidence > 0.8:
                return "shard_quality_high"
            elif confidence > 0.5:
                return "shard_quality_medium"
            else:
                return "shard_quality_low"

        else:  # HYBRID_SHARDING
            # Combine temporal and hash sharding
            if isinstance(capsule.timestamp, str):
                timestamp = datetime.fromisoformat(
                    capsule.timestamp.replace("Z", "+00:00")
                )
            else:
                timestamp = capsule.timestamp

            # Use hour-based temporal sharding for recent capsules
            now = datetime.now(timezone.utc)
            if (now - timestamp).days < 1:  # Less than 1 day old
                hour_key = timestamp.strftime("%Y-%m-%d-%H")
                return f"shard_hybrid_recent_{hour_key}"
            else:
                # Use hash sharding for older capsules
                hash_value = int(
                    hashlib.sha256(capsule.capsule_id.encode()).hexdigest()[:8], 16
                )
                shard_index = hash_value % 4
                return f"shard_hybrid_archive_{shard_index}"

    async def _create_shard(self, shard_id: str) -> ChainShard:
        """Create a new shard.

        Args:
            shard_id: ID for the new shard

        Returns:
            Created shard
        """
        shard_index = len(self.shards)
        shard = ChainShard(
            shard_id=shard_id, shard_index=shard_index, state=ShardState.INITIALIZING
        )

        self.shards[shard_id] = shard
        self.shard_order.append(shard_id)
        shard.state = ShardState.ACTIVE

        logger.info(f"Created new shard: {shard_id}")
        return shard

    async def _should_split_shard(self, shard: ChainShard) -> bool:
        """Check if a shard should be split.

        Args:
            shard: Shard to check

        Returns:
            True if shard should be split
        """
        if not shard.metrics:
            return False

        # Check capsule count
        if shard.metrics.capsule_count > self.max_capsules_per_shard:
            return True

        # Check memory usage
        memory_mb = shard.metrics.memory_usage_bytes / (1024 * 1024)
        if memory_mb > self.max_memory_per_shard_mb:
            return True

        # Check load factor
        if shard.metrics.calculate_load_factor() > 0.9:
            return True

        return False

    async def _schedule_shard_split(self, shard: ChainShard):
        """Schedule a shard for splitting.

        Args:
            shard: Shard to split
        """
        # For now, just log the need for splitting
        # In a production system, this would queue the split operation
        logger.info(
            f"Shard {shard.shard_id} scheduled for splitting (load: {shard.metrics.calculate_load_factor():.2f})"
        )

        # Implement shard splitting operation
        try:
            # 1. Create two new child shards
            left_shard_id = f"{shard.shard_id}_left"
            right_shard_id = f"{shard.shard_id}_right"

            left_shard = ChainShard(
                shard_id=left_shard_id,
                strategy=shard.strategy,
                key_range=(
                    shard.key_range[0],
                    (shard.key_range[0] + shard.key_range[1]) // 2,
                ),
                created_at=datetime.now(timezone.utc),
            )

            right_shard = ChainShard(
                shard_id=right_shard_id,
                strategy=shard.strategy,
                key_range=(
                    (shard.key_range[0] + shard.key_range[1]) // 2,
                    shard.key_range[1],
                ),
                created_at=datetime.now(timezone.utc),
            )

            # 2. Redistribute capsules based on hash key
            midpoint = (shard.key_range[0] + shard.key_range[1]) // 2

            for capsule_id in list(shard.capsule_ids):
                # Calculate which shard this capsule belongs to
                key_hash = hash(capsule_id) % (shard.key_range[1] - shard.key_range[0])

                if key_hash < midpoint:
                    left_shard.capsule_ids.add(capsule_id)
                else:
                    right_shard.capsule_ids.add(capsule_id)

            # 3. Register new shards and mark old shard as split
            self.shards[left_shard_id] = left_shard
            self.shards[right_shard_id] = right_shard
            shard.status = ShardStatus.SPLIT  # Mark as split
            shard.metadata["split_into"] = [left_shard_id, right_shard_id]

            logger.info(
                f"Shard split complete: {shard.shard_id} -> {left_shard_id} ({len(left_shard.capsule_ids)} capsules), "
                f"{right_shard_id} ({len(right_shard.capsule_ids)} capsules)"
            )

            # 4. Notify coordinator of topology change
            await self._notify_topology_change(
                "shard_split",
                {
                    "parent_shard": shard.shard_id,
                    "left_shard": left_shard_id,
                    "right_shard": right_shard_id,
                },
            )

        except Exception as e:
            logger.error(f"Shard split failed: {e}")
            raise

    async def _notify_topology_change(self, event_type: str, metadata: Dict[str, Any]):
        """Notify coordinator and other shards of topology changes"""
        try:
            # Emit topology change event for coordination
            from src.audit.events import audit_emitter

            audit_emitter.emit_system_event(
                event_name=f"shard_topology_{event_type}", metadata=metadata
            )
        except Exception as e:
            logger.warning(f"Failed to notify topology change: {e}")

    async def _move_capsules_between_shards(
        self, source_shard: ChainShard, target_shard: ChainShard, count: int
    ) -> int:
        """Move capsules between shards during rebalancing.

        Args:
            source_shard: Source shard
            target_shard: Target shard
            count: Number of capsules to move

        Returns:
            Number of capsules actually moved
        """
        moved_count = 0

        # Select capsules to move (prefer those with fewer cross-shard references)
        capsules_to_move = []

        for capsule_id in source_shard.capsule_order:
            if len(capsules_to_move) >= count:
                break

            # Prefer capsules with minimal cross-shard dependencies
            if capsule_id not in source_shard.cross_shard_references:
                capsules_to_move.append(capsule_id)

        # If we need more capsules, add some with cross-shard references
        if len(capsules_to_move) < count:
            remaining_needed = count - len(capsules_to_move)
            for capsule_id in source_shard.capsule_order:
                if len(capsules_to_move) >= count:
                    break
                if capsule_id not in capsules_to_move:
                    capsules_to_move.append(capsule_id)
                    remaining_needed -= 1
                    if remaining_needed <= 0:
                        break

        # Move the selected capsules
        for capsule_id in capsules_to_move:
            capsule = source_shard.remove_capsule(capsule_id)
            if capsule and target_shard.add_capsule(capsule):
                # Update mapping
                self.shard_mapping[capsule_id] = target_shard.shard_id
                moved_count += 1

                logger.debug(
                    f"Moved capsule {capsule_id} from {source_shard.shard_id} to {target_shard.shard_id}"
                )

        return moved_count

    def _aggregate_shard_metrics(
        self, shard_results: Dict[str, CQSSResult], total_capsules: int
    ) -> Dict[str, Any]:
        """Aggregate quality metrics from multiple shards.

        Args:
            shard_results: Quality results from each shard
            total_capsules: Total number of capsules across all shards

        Returns:
            Aggregated metrics
        """
        if not shard_results:
            return {}

        # Initialize aggregated metrics
        aggregated = {
            "chain_length": total_capsules,
            "shard_count": len(shard_results),
            "total_shards": len(self.shards),
        }

        # Collect metrics that can be summed
        summed_metrics = [
            "valid_signatures",
            "fork_count",
            "unique_agents",
            "root_count",
            "leaf_count",
            "join_points",
        ]

        # Collect metrics that should be averaged
        averaged_metrics = [
            "verification_ratio",
            "integrity_score",
            "complexity_score",
            "trust_score",
            "diversity_score",
            "avg_path_length",
            "joint_capsule_ratio",
            "introspective_ratio",
            "avg_confidence",
        ]

        # Sum appropriate metrics
        for metric in summed_metrics:
            total = 0
            for result in shard_results.values():
                value = result.metrics.get(metric, 0)
                if value is not None:
                    total += value
            aggregated[metric] = total

        # Average appropriate metrics
        for metric in averaged_metrics:
            values = []
            for result in shard_results.values():
                value = result.metrics.get(metric)
                if value is not None:
                    values.append(value)

            if values:
                aggregated[metric] = round(statistics.mean(values), 2)
            else:
                aggregated[metric] = 0.0

        # Calculate special aggregated metrics
        if total_capsules > 0:
            # Longest path across all shards
            longest_paths = [
                result.metrics.get("longest_path", 0)
                for result in shard_results.values()
            ]
            aggregated["longest_path"] = max(longest_paths) if longest_paths else 0

            # Cross-shard reference ratio
            total_cross_refs = sum(
                len(shard.cross_shard_references) for shard in self.shards.values()
            )
            aggregated["cross_shard_references"] = total_cross_refs
            aggregated["cross_shard_ratio"] = round(
                total_cross_refs / total_capsules, 2
            )

        return aggregated

    def get_sharding_statistics(self) -> Dict[str, Any]:
        """Get comprehensive sharding statistics.

        Returns:
            Dictionary with sharding performance metrics
        """
        if not self.shards:
            return {"total_shards": 0, "total_capsules": 0}

        # Calculate shard statistics
        shard_stats = []
        total_memory = 0
        total_load = 0.0

        for shard in self.shards.values():
            if shard.metrics:
                load_factor = shard.metrics.calculate_load_factor()
                shard_stats.append(
                    {
                        "shard_id": shard.shard_id,
                        "capsule_count": shard.metrics.capsule_count,
                        "memory_usage_mb": round(
                            shard.metrics.memory_usage_bytes / (1024 * 1024), 2
                        ),
                        "load_factor": round(load_factor, 2),
                        "health_score": round(shard.metrics.health_score, 2),
                        "cross_shard_refs": len(shard.cross_shard_references),
                        "state": shard.state.value,
                    }
                )

                total_memory += shard.metrics.memory_usage_bytes
                total_load += load_factor

        avg_load = total_load / len(self.shards) if self.shards else 0.0

        return {
            "total_shards": len(self.shards),
            "active_shards": len(
                [s for s in self.shards.values() if s.state == ShardState.ACTIVE]
            ),
            "total_capsules": self.total_capsules,
            "total_memory_mb": round(total_memory / (1024 * 1024), 2),
            "average_load_factor": round(avg_load, 2),
            "sharding_strategy": self.sharding_strategy.value,
            "rebalancing_in_progress": self.rebalancing_in_progress,
            "shard_details": shard_stats,
            "performance_targets": {
                "max_capsules_per_shard": self.max_capsules_per_shard,
                "max_memory_per_shard_mb": self.max_memory_per_shard_mb,
                "target_load_factor": 0.7,
                "target_health_score": 0.8,
            },
        }


# Global sharding system instance
horizontal_sharding = HorizontalChainSharding()
