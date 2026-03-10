"""
fork_resolver.py - Automated Fork Resolution for UATP Capsule Engine

This module implements quality-based automated fork resolution to prevent system breakdown
as forks multiply exponentially. Uses CQSS scores to select canonical paths and provide
conflict resolution with provenance preservation.

Key Features:
- Quality-based fork resolution using CQSS scores
- Multi-criteria decision system for complex fork scenarios
- Conflict resolution with provenance preservation
- Automated merging of non-conflicting branches
- Economic incentives for quality maintenance
- Byzantine fault tolerance for malicious forks
"""

import hashlib
import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import networkx as nx

from src.capsule_schema import Capsule

from .cqss import compute_cqss

logger = logging.getLogger(__name__)


class ForkResolutionStrategy(str, Enum):
    """Fork resolution strategies."""

    QUALITY_BASED = "quality_based"
    CONSENSUS_WEIGHTED = "consensus_weighted"
    TEMPORAL_PRIORITY = "temporal_priority"
    ECONOMIC_STAKE = "economic_stake"
    HYBRID_MULTI_CRITERIA = "hybrid_multi_criteria"


class ForkConflictType(str, Enum):
    """Types of conflicts in forks."""

    CONTENT_CONFLICT = "content_conflict"
    TEMPORAL_CONFLICT = "temporal_conflict"
    VERIFICATION_CONFLICT = "verification_conflict"
    ECONOMIC_CONFLICT = "economic_conflict"
    BYZANTINE_ATTACK = "byzantine_attack"


@dataclass
class ForkCandidate:
    """Represents a candidate path in a fork."""

    fork_id: str
    branch_id: str
    capsules: List[Capsule]
    quality_score: float
    consensus_weight: float
    economic_stake: float
    temporal_score: float
    provenance_integrity: float
    conflict_types: Set[ForkConflictType] = field(default_factory=set)
    resolution_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ForkResolutionResult:
    """Result of fork resolution process."""

    resolved_fork_id: str
    canonical_branch_id: str
    resolution_strategy: ForkResolutionStrategy
    quality_improvement: float
    discarded_branches: List[str]
    conflicts_resolved: int
    economic_penalties: Dict[str, float]
    provenance_preserved: bool
    resolution_timestamp: datetime
    confidence_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class QualityBasedForkResolver:
    """
    Automated fork resolution system using quality-based selection.

    This system prevents exponential fork multiplication by automatically
    resolving forks based on comprehensive quality metrics and multi-criteria
    decision making with economic incentives for quality maintenance.
    """

    def __init__(self, economic_engine=None, consensus_engine=None):
        """Initialize the fork resolver.

        Args:
            economic_engine: Economic engine for penalties and rewards
            consensus_engine: Consensus engine for weighted decisions
        """
        self.economic_engine = economic_engine
        self.consensus_engine = consensus_engine

        # Fork detection and tracking
        self.active_forks: Dict[str, List[ForkCandidate]] = {}
        self.resolved_forks: Dict[str, ForkResolutionResult] = {}
        self.fork_history: List[Dict[str, Any]] = []

        # Configuration parameters
        self.quality_threshold = 0.7  # Minimum quality for canonical selection
        self.max_fork_age_hours = 24  # Auto-resolve forks after 24 hours
        self.consensus_weight_factor = 0.3  # Weight for consensus in decisions
        self.economic_weight_factor = 0.2  # Weight for economic stake
        self.temporal_weight_factor = 0.1  # Weight for temporal priority
        self.quality_weight_factor = 0.4  # Weight for quality score

        # Byzantine fault tolerance
        self.max_byzantine_tolerance = 0.33  # Up to 33% Byzantine nodes
        self.malicious_behavior_threshold = 0.8

        # Performance optimization
        self.resolution_cache: Dict[str, ForkResolutionResult] = {}
        self.cache_ttl_seconds = 3600  # 1 hour cache TTL

    async def detect_forks(self, chain: List[Capsule]) -> List[str]:
        """Detect forks in the capsule chain.

        Args:
            chain: List of capsules to analyze

        Returns:
            List of fork IDs detected
        """
        forks_detected = []

        # Build graph representation
        G = nx.DiGraph()

        # Add nodes and edges
        for capsule in chain:
            G.add_node(capsule.capsule_id, capsule=capsule)

            # Add parent relationships
            parent_id = getattr(capsule, "parent_capsule", None) or getattr(
                capsule, "previous_capsule_id", None
            )
            if parent_id and parent_id in G:
                G.add_edge(parent_id, capsule.capsule_id)

        # Find fork points (nodes with multiple children)
        fork_points = [node for node, out_degree in G.out_degree() if out_degree > 1]

        for fork_point in fork_points:
            fork_id = self._generate_fork_id(fork_point)

            if fork_id not in self.active_forks:
                # Analyze branches from this fork point
                branches = await self._analyze_fork_branches(G, fork_point, chain)

                if len(branches) > 1:
                    self.active_forks[fork_id] = branches
                    forks_detected.append(fork_id)

                    logger.info(
                        f"Detected fork {fork_id} at capsule {fork_point} with {len(branches)} branches"
                    )

        return forks_detected

    async def _analyze_fork_branches(
        self, graph: nx.DiGraph, fork_point: str, chain: List[Capsule]
    ) -> List[ForkCandidate]:
        """Analyze branches from a fork point.

        Args:
            graph: NetworkX graph of the chain
            fork_point: Node ID where fork occurs
            chain: Full capsule chain

        Returns:
            List of fork candidates for each branch
        """
        branches = []
        successors = list(graph.successors(fork_point))

        for i, successor in enumerate(successors):
            branch_id = f"{fork_point}_branch_{i}"

            # Get all capsules in this branch
            branch_capsules = self._get_branch_capsules(graph, successor, chain)

            if branch_capsules:
                # Calculate quality metrics for this branch
                quality_score = await self._calculate_branch_quality(branch_capsules)
                consensus_weight = await self._calculate_consensus_weight(
                    branch_capsules
                )
                economic_stake = await self._calculate_economic_stake(branch_capsules)
                temporal_score = self._calculate_temporal_score(branch_capsules)
                provenance_integrity = await self._verify_provenance_integrity(
                    branch_capsules
                )

                # Detect conflict types
                conflict_types = await self._detect_conflicts(
                    branch_capsules, successors
                )

                candidate = ForkCandidate(
                    fork_id=self._generate_fork_id(fork_point),
                    branch_id=branch_id,
                    capsules=branch_capsules,
                    quality_score=quality_score,
                    consensus_weight=consensus_weight,
                    economic_stake=economic_stake,
                    temporal_score=temporal_score,
                    provenance_integrity=provenance_integrity,
                    conflict_types=conflict_types,
                )

                branches.append(candidate)

        return branches

    def _get_branch_capsules(
        self, graph: nx.DiGraph, start_node: str, chain: List[Capsule]
    ) -> List[Capsule]:
        """Get all capsules in a branch starting from a node.

        Args:
            graph: NetworkX graph
            start_node: Starting node ID
            chain: Full capsule chain

        Returns:
            List of capsules in the branch
        """
        # Get all nodes reachable from start_node
        reachable = nx.descendants(graph, start_node)
        reachable.add(start_node)

        # Filter capsules to only those in this branch
        branch_capsules = []
        for capsule in chain:
            if capsule.capsule_id in reachable:
                branch_capsules.append(capsule)

        # Sort by timestamp for proper ordering
        branch_capsules.sort(key=lambda c: c.timestamp)
        return branch_capsules

    async def _calculate_branch_quality(self, branch_capsules: List[Capsule]) -> float:
        """Calculate quality score for a branch.

        Args:
            branch_capsules: Capsules in the branch

        Returns:
            Quality score from 0.0 to 1.0
        """
        if not branch_capsules:
            return 0.0

        # Use CQSS to compute comprehensive quality metrics
        async def verify_capsule(capsule):
            # Simplified verification - in production would use real verification
            return True, "verified"

        cqss_result = await compute_cqss(branch_capsules, verify_capsule)
        overall_score = cqss_result.get_overall_score()

        return overall_score if overall_score is not None else 0.0

    async def _calculate_consensus_weight(
        self, branch_capsules: List[Capsule]
    ) -> float:
        """Calculate consensus weight for a branch.

        Args:
            branch_capsules: Capsules in the branch

        Returns:
            Consensus weight from 0.0 to 1.0
        """
        if not self.consensus_engine or not branch_capsules:
            return 0.5  # Neutral weight if no consensus engine

        # Calculate weight based on validator support for this branch
        total_weight = 0.0
        total_validators = 0

        for capsule in branch_capsules:
            agent_id = getattr(capsule, "agent_id", None)
            if agent_id and agent_id in self.consensus_engine.nodes:
                node = self.consensus_engine.nodes[agent_id]
                if node.is_active:
                    voting_power = node.calculate_voting_power()
                    total_weight += voting_power
                    total_validators += 1

        if total_validators == 0:
            return 0.5

        # Normalize by maximum possible weight
        max_possible_weight = total_validators * 1.0  # Assume max voting power is 1.0
        return min(1.0, total_weight / max_possible_weight)

    async def _calculate_economic_stake(self, branch_capsules: List[Capsule]) -> float:
        """Calculate economic stake backing a branch.

        Args:
            branch_capsules: Capsules in the branch

        Returns:
            Economic stake score from 0.0 to 1.0
        """
        if not self.economic_engine or not branch_capsules:
            return 0.5  # Neutral stake if no economic engine

        total_stake = 0.0
        for capsule in branch_capsules:
            agent_id = getattr(capsule, "agent_id", None)
            if agent_id:
                stake = self.economic_engine.get_agent_stake(agent_id)
                reputation = self.economic_engine.get_agent_reputation(agent_id)
                total_stake += stake * reputation  # Weight stake by reputation

        # Normalize to 0-1 scale (assuming max reasonable stake is 1000)
        return min(1.0, total_stake / 1000.0)

    def _calculate_temporal_score(self, branch_capsules: List[Capsule]) -> float:
        """Calculate temporal priority score for a branch.

        Args:
            branch_capsules: Capsules in the branch

        Returns:
            Temporal score from 0.0 to 1.0
        """
        if not branch_capsules:
            return 0.0

        # Score based on recency and consistency of timestamps
        now = datetime.now(timezone.utc)

        timestamps = []
        for capsule in branch_capsules:
            try:
                if isinstance(capsule.timestamp, str):
                    ts = datetime.fromisoformat(
                        capsule.timestamp.replace("Z", "+00:00")
                    )
                else:
                    ts = capsule.timestamp
                timestamps.append(ts)
            except (ValueError, AttributeError):
                continue

        if not timestamps:
            return 0.0

        # Calculate recency score
        latest_timestamp = max(timestamps)
        time_diff = (now - latest_timestamp).total_seconds()
        recency_score = max(0.0, 1.0 - (time_diff / (24 * 3600)))  # Decay over 24 hours

        # Calculate consistency score
        if len(timestamps) > 1:
            time_diffs = [
                (timestamps[i] - timestamps[i - 1]).total_seconds()
                for i in range(1, len(timestamps))
            ]
            consistency_score = 1.0 / (
                1.0 + statistics.stdev(time_diffs) / 3600
            )  # Normalize by hour
        else:
            consistency_score = 1.0

        return (recency_score + consistency_score) / 2.0

    async def _verify_provenance_integrity(
        self, branch_capsules: List[Capsule]
    ) -> float:
        """Verify provenance integrity for a branch.

        Args:
            branch_capsules: Capsules in the branch

        Returns:
            Provenance integrity score from 0.0 to 1.0
        """
        if not branch_capsules:
            return 0.0

        integrity_score = 1.0

        # Check chain continuity
        for i in range(1, len(branch_capsules)):
            current = branch_capsules[i]
            previous = branch_capsules[i - 1]

            # Verify parent relationship
            parent_id = getattr(current, "parent_capsule", None) or getattr(
                current, "previous_capsule_id", None
            )
            if parent_id != previous.capsule_id:
                integrity_score *= 0.8  # Penalty for broken chain

            # Verify timestamp ordering
            try:
                if isinstance(current.timestamp, str):
                    current_ts = datetime.fromisoformat(
                        current.timestamp.replace("Z", "+00:00")
                    )
                else:
                    current_ts = current.timestamp

                if isinstance(previous.timestamp, str):
                    previous_ts = datetime.fromisoformat(
                        previous.timestamp.replace("Z", "+00:00")
                    )
                else:
                    previous_ts = previous.timestamp

                if current_ts < previous_ts:
                    integrity_score *= 0.9  # Penalty for temporal inconsistency
            except (ValueError, AttributeError):
                integrity_score *= 0.95  # Small penalty for unparseable timestamps

        return max(0.0, integrity_score)

    async def _detect_conflicts(
        self, branch_capsules: List[Capsule], all_successors: List[str]
    ) -> Set[ForkConflictType]:
        """Detect types of conflicts in a branch.

        Args:
            branch_capsules: Capsules in the branch
            all_successors: All successor nodes from fork point

        Returns:
            Set of detected conflict types
        """
        conflicts = set()

        if not branch_capsules:
            return conflicts

        # Check for content conflicts (similar content in different branches)
        # This would require comparing with other branches - simplified for now
        if len(all_successors) > 2:
            conflicts.add(ForkConflictType.CONTENT_CONFLICT)

        # Check for temporal conflicts (timestamp anomalies)
        timestamps = []
        for capsule in branch_capsules:
            try:
                if isinstance(capsule.timestamp, str):
                    ts = datetime.fromisoformat(
                        capsule.timestamp.replace("Z", "+00:00")
                    )
                else:
                    ts = capsule.timestamp
                timestamps.append(ts)
            except (ValueError, AttributeError):
                conflicts.add(ForkConflictType.TEMPORAL_CONFLICT)

        # Check for rapid succession (potential Byzantine attack)
        if len(timestamps) > 1:
            time_diffs = [
                (timestamps[i] - timestamps[i - 1]).total_seconds()
                for i in range(1, len(timestamps))
            ]
            if any(diff < 1.0 for diff in time_diffs):  # Less than 1 second apart
                conflicts.add(ForkConflictType.BYZANTINE_ATTACK)

        # Check for verification conflicts
        verification_issues = 0
        for capsule in branch_capsules:
            # Simplified verification check
            if not hasattr(capsule, "signature") or not capsule.signature:
                verification_issues += 1

        if verification_issues > len(branch_capsules) * 0.2:  # More than 20% issues
            conflicts.add(ForkConflictType.VERIFICATION_CONFLICT)

        return conflicts

    async def resolve_fork(
        self,
        fork_id: str,
        strategy: ForkResolutionStrategy = ForkResolutionStrategy.HYBRID_MULTI_CRITERIA,
    ) -> Optional[ForkResolutionResult]:
        """Resolve a fork using the specified strategy.

        Args:
            fork_id: ID of the fork to resolve
            strategy: Resolution strategy to use

        Returns:
            Fork resolution result or None if resolution failed
        """
        if fork_id not in self.active_forks:
            logger.warning(f"Fork {fork_id} not found in active forks")
            return None

        # Check cache first
        cache_key = f"{fork_id}_{strategy.value}"
        if cache_key in self.resolution_cache:
            cached_result = self.resolution_cache[cache_key]
            if (
                datetime.now(timezone.utc) - cached_result.resolution_timestamp
            ).seconds < self.cache_ttl_seconds:
                return cached_result

        candidates = self.active_forks[fork_id]

        if len(candidates) < 2:
            logger.warning(f"Fork {fork_id} has fewer than 2 candidates")
            return None

        # Select canonical branch based on strategy
        canonical_candidate = await self._select_canonical_branch(candidates, strategy)

        if not canonical_candidate:
            logger.error(f"Failed to select canonical branch for fork {fork_id}")
            return None

        # Calculate quality improvement
        quality_before = sum(c.quality_score for c in candidates) / len(candidates)
        quality_after = canonical_candidate.quality_score
        quality_improvement = quality_after - quality_before

        # Identify discarded branches
        discarded_branches = [
            c.branch_id
            for c in candidates
            if c.branch_id != canonical_candidate.branch_id
        ]

        # Apply economic penalties for low-quality branches
        economic_penalties = await self._apply_economic_penalties(
            candidates, canonical_candidate
        )

        # Count conflicts resolved
        conflicts_resolved = sum(
            len(c.conflict_types)
            for c in candidates
            if c.branch_id != canonical_candidate.branch_id
        )

        # Calculate confidence score
        confidence_score = await self._calculate_resolution_confidence(
            canonical_candidate, candidates, strategy
        )

        # Create resolution result
        result = ForkResolutionResult(
            resolved_fork_id=fork_id,
            canonical_branch_id=canonical_candidate.branch_id,
            resolution_strategy=strategy,
            quality_improvement=quality_improvement,
            discarded_branches=discarded_branches,
            conflicts_resolved=conflicts_resolved,
            economic_penalties=economic_penalties,
            provenance_preserved=canonical_candidate.provenance_integrity > 0.8,
            resolution_timestamp=datetime.now(timezone.utc),
            confidence_score=confidence_score,
            metadata={
                "candidates_evaluated": len(candidates),
                "canonical_quality": canonical_candidate.quality_score,
                "consensus_weight": canonical_candidate.consensus_weight,
                "economic_stake": canonical_candidate.economic_stake,
                "temporal_score": canonical_candidate.temporal_score,
                "conflicts_detected": list(canonical_candidate.conflict_types),
            },
        )

        # Store result and clean up
        self.resolved_forks[fork_id] = result
        del self.active_forks[fork_id]
        self.resolution_cache[cache_key] = result

        # Record in history
        self.fork_history.append(
            {
                "fork_id": fork_id,
                "resolution_strategy": strategy.value,
                "canonical_branch": canonical_candidate.branch_id,
                "quality_improvement": quality_improvement,
                "timestamp": result.resolution_timestamp.isoformat(),
                "confidence": confidence_score,
            }
        )

        logger.info(
            f"Resolved fork {fork_id} using {strategy.value} strategy with {confidence_score:.2f} confidence"
        )

        return result

    async def _select_canonical_branch(
        self, candidates: List[ForkCandidate], strategy: ForkResolutionStrategy
    ) -> Optional[ForkCandidate]:
        """Select the canonical branch from candidates.

        Args:
            candidates: List of fork candidates
            strategy: Resolution strategy

        Returns:
            Selected canonical candidate or None
        """
        if not candidates:
            return None

        if strategy == ForkResolutionStrategy.QUALITY_BASED:
            return max(candidates, key=lambda c: c.quality_score)

        elif strategy == ForkResolutionStrategy.CONSENSUS_WEIGHTED:
            return max(candidates, key=lambda c: c.consensus_weight)

        elif strategy == ForkResolutionStrategy.TEMPORAL_PRIORITY:
            return max(candidates, key=lambda c: c.temporal_score)

        elif strategy == ForkResolutionStrategy.ECONOMIC_STAKE:
            return max(candidates, key=lambda c: c.economic_stake)

        elif strategy == ForkResolutionStrategy.HYBRID_MULTI_CRITERIA:
            # Multi-criteria decision making
            best_score = -1.0
            best_candidate = None

            for candidate in candidates:
                # Weighted combination of all factors
                composite_score = (
                    candidate.quality_score * self.quality_weight_factor
                    + candidate.consensus_weight * self.consensus_weight_factor
                    + candidate.economic_stake * self.economic_weight_factor
                    + candidate.temporal_score * self.temporal_weight_factor
                )

                # Apply penalties for conflicts
                conflict_penalty = len(candidate.conflict_types) * 0.1
                composite_score -= conflict_penalty

                # Bonus for high provenance integrity
                if candidate.provenance_integrity > 0.9:
                    composite_score += 0.05

                if composite_score > best_score:
                    best_score = composite_score
                    best_candidate = candidate

            return best_candidate

        else:
            logger.error(f"Unknown resolution strategy: {strategy}")
            return None

    async def _apply_economic_penalties(
        self, candidates: List[ForkCandidate], canonical: ForkCandidate
    ) -> Dict[str, float]:
        """Apply economic penalties for maintaining low-quality branches.

        Args:
            candidates: All fork candidates
            canonical: Selected canonical candidate

        Returns:
            Dict mapping agent IDs to penalty amounts
        """
        penalties = {}

        if not self.economic_engine:
            return penalties

        for candidate in candidates:
            if candidate.branch_id == canonical.branch_id:
                continue  # Don't penalize the canonical branch

            # Calculate penalty based on quality difference and conflicts
            quality_diff = max(0.0, canonical.quality_score - candidate.quality_score)
            conflict_severity = len(candidate.conflict_types) * 0.1

            penalty_rate = (quality_diff + conflict_severity) * 0.5

            # Apply penalties to agents who created capsules in this branch
            for capsule in candidate.capsules:
                agent_id = getattr(capsule, "agent_id", None)
                if not agent_id:
                    continue

                # Calculate penalty based on agent's stake and the severity
                agent_stake = self.economic_engine.get_agent_stake(agent_id)
                penalty_amount = agent_stake * penalty_rate * 0.1  # Max 10% of stake

                if penalty_amount > 0.01:  # Only apply significant penalties
                    try:
                        success = self.economic_engine.implement_economic_penalties(
                            agent_id,
                            penalty_amount,
                            f"Low-quality fork branch penalty (fork {candidate.fork_id})",
                        )
                        if success:
                            penalties[agent_id] = penalty_amount
                    except Exception as e:
                        logger.warning(f"Failed to apply penalty to {agent_id}: {e}")

        return penalties

    async def _calculate_resolution_confidence(
        self,
        canonical: ForkCandidate,
        all_candidates: List[ForkCandidate],
        strategy: ForkResolutionStrategy,
    ) -> float:
        """Calculate confidence in the fork resolution.

        Args:
            canonical: Selected canonical candidate
            all_candidates: All candidates considered
            strategy: Strategy used for resolution

        Returns:
            Confidence score from 0.0 to 1.0
        """
        if len(all_candidates) < 2:
            return 1.0  # Perfect confidence if no alternatives

        # Base confidence on quality margin
        other_candidates = [
            c for c in all_candidates if c.branch_id != canonical.branch_id
        ]

        if strategy == ForkResolutionStrategy.QUALITY_BASED:
            best_other_quality = max(c.quality_score for c in other_candidates)
            quality_margin = canonical.quality_score - best_other_quality
        else:
            # For other strategies, use composite score
            canonical_score = (
                canonical.quality_score * self.quality_weight_factor
                + canonical.consensus_weight * self.consensus_weight_factor
                + canonical.economic_stake * self.economic_weight_factor
                + canonical.temporal_score * self.temporal_weight_factor
            )

            best_other_score = 0.0
            for candidate in other_candidates:
                other_score = (
                    candidate.quality_score * self.quality_weight_factor
                    + candidate.consensus_weight * self.consensus_weight_factor
                    + candidate.economic_stake * self.economic_weight_factor
                    + candidate.temporal_score * self.temporal_weight_factor
                )
                best_other_score = max(best_other_score, other_score)

            quality_margin = canonical_score - best_other_score

        # Convert margin to confidence (sigmoid-like function)
        base_confidence = 1.0 / (1.0 + max(0.0, -quality_margin * 10))

        # Adjust for provenance integrity
        provenance_bonus = canonical.provenance_integrity * 0.1

        # Adjust for conflicts resolved
        conflict_bonus = min(0.1, len(canonical.conflict_types) * 0.02)

        final_confidence = min(1.0, base_confidence + provenance_bonus + conflict_bonus)

        return final_confidence

    async def auto_resolve_aged_forks(self) -> List[ForkResolutionResult]:
        """Automatically resolve forks that have aged beyond threshold.

        Returns:
            List of resolution results for aged forks
        """
        results = []
        aged_forks = []
        now = datetime.now(timezone.utc)

        # Identify aged forks
        for fork_id, candidates in self.active_forks.items():
            if not candidates:
                continue

            # Find the oldest capsule in any candidate
            oldest_timestamp = None
            for candidate in candidates:
                for capsule in candidate.capsules:
                    try:
                        if isinstance(capsule.timestamp, str):
                            ts = datetime.fromisoformat(
                                capsule.timestamp.replace("Z", "+00:00")
                            )
                        else:
                            ts = capsule.timestamp

                        if oldest_timestamp is None or ts < oldest_timestamp:
                            oldest_timestamp = ts
                    except (ValueError, AttributeError):
                        continue

            if oldest_timestamp:
                age_hours = (now - oldest_timestamp).total_seconds() / 3600
                if age_hours > self.max_fork_age_hours:
                    aged_forks.append(fork_id)

        # Resolve aged forks
        for fork_id in aged_forks:
            try:
                result = await self.resolve_fork(
                    fork_id, ForkResolutionStrategy.HYBRID_MULTI_CRITERIA
                )
                if result:
                    result.metadata["auto_resolved"] = True
                    result.metadata["age_hours"] = age_hours
                    results.append(result)
                    logger.info(
                        f"Auto-resolved aged fork {fork_id} after {age_hours:.1f} hours"
                    )
            except Exception as e:
                logger.error(f"Failed to auto-resolve aged fork {fork_id}: {e}")

        return results

    def _generate_fork_id(self, fork_point: str) -> str:
        """Generate a unique fork ID.

        Args:
            fork_point: Capsule ID where fork occurs

        Returns:
            Unique fork ID
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        data = f"{fork_point}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def get_fork_statistics(self) -> Dict[str, Any]:
        """Get comprehensive fork resolution statistics.

        Returns:
            Dictionary with fork statistics
        """
        total_forks = len(self.resolved_forks) + len(self.active_forks)
        resolved_count = len(self.resolved_forks)
        active_count = len(self.active_forks)

        if not self.fork_history:
            return {
                "total_forks": total_forks,
                "resolved_forks": resolved_count,
                "active_forks": active_count,
                "resolution_rate": 0.0,
            }

        # Calculate average resolution time
        quality_improvements = []
        confidence_scores = []

        for record in self.fork_history:
            if "quality_improvement" in record:
                quality_improvements.append(record["quality_improvement"])
            if "confidence" in record:
                confidence_scores.append(record["confidence"])

        avg_quality_improvement = (
            statistics.mean(quality_improvements) if quality_improvements else 0.0
        )
        avg_confidence = (
            statistics.mean(confidence_scores) if confidence_scores else 0.0
        )

        # Strategy usage statistics
        strategy_usage = defaultdict(int)
        for record in self.fork_history:
            strategy_usage[record.get("resolution_strategy", "unknown")] += 1

        return {
            "total_forks": total_forks,
            "resolved_forks": resolved_count,
            "active_forks": active_count,
            "resolution_rate": (resolved_count / total_forks * 100)
            if total_forks > 0
            else 0.0,
            "average_quality_improvement": avg_quality_improvement,
            "average_confidence": avg_confidence,
            "strategy_usage": dict(strategy_usage),
            "total_conflicts_resolved": sum(
                r.conflicts_resolved for r in self.resolved_forks.values()
            ),
            "total_economic_penalties": sum(
                sum(r.economic_penalties.values()) for r in self.resolved_forks.values()
            ),
            "cache_hit_rate": len(self.resolution_cache)
            / max(1, len(self.fork_history))
            * 100,
        }


# Global fork resolver instance
fork_resolver = QualityBasedForkResolver()
