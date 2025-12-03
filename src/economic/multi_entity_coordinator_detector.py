"""
Multi-Entity Coordination Detection System for UATP Economic Security.

This system detects sophisticated coordination attacks involving multiple entities
working together to manipulate attribution, dividends, governance, or other 
economic aspects of the UATP system.

Advanced detection techniques include:
- Graph analysis of entity relationships
- Temporal correlation analysis
- Behavioral similarity detection
- Cross-platform coordination tracking
- Machine learning anomaly detection
"""

import asyncio
import hashlib
import json
import logging
import numpy as np
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set, Tuple, Any, Optional
from enum import Enum, auto
from itertools import combinations

logger = logging.getLogger(__name__)


class CoordinationType(Enum):
    """Types of multi-entity coordination attacks."""

    ATTRIBUTION_RING = "attribution_ring"
    DIVIDEND_POOLING = "dividend_pooling"
    GOVERNANCE_CARTEL = "governance_cartel"
    SYBIL_NETWORK = "sybil_network"
    WASH_TRADING_RING = "wash_trading_ring"
    COLLUSIVE_BIDDING = "collusive_bidding"
    CROSS_PLATFORM_COORDINATION = "cross_platform_coordination"


@dataclass
class EntityProfile:
    """Profile of an entity's behavior patterns."""

    entity_id: str
    first_seen: datetime
    last_activity: datetime

    # Behavioral patterns
    activity_timestamps: deque = field(default_factory=lambda: deque(maxlen=1000))
    attribution_patterns: Dict[str, float] = field(default_factory=dict)
    voting_patterns: Dict[str, str] = field(default_factory=dict)
    transaction_patterns: Dict[str, float] = field(default_factory=dict)

    # Relationship tracking
    direct_connections: Set[str] = field(default_factory=set)
    indirect_connections: Set[str] = field(default_factory=set)
    interaction_frequency: Dict[str, int] = field(default_factory=dict)

    # Coordination indicators
    coordination_score: float = 0.0
    suspicious_behaviors: List[str] = field(default_factory=list)
    coordination_events: List[datetime] = field(default_factory=list)


@dataclass
class CoordinationCluster:
    """Cluster of entities showing coordination patterns."""

    cluster_id: str
    entities: Set[str]
    coordination_type: CoordinationType
    confidence_score: float
    first_detected: datetime
    last_activity: datetime

    # Evidence and patterns
    behavioral_evidence: Dict[str, Any] = field(default_factory=dict)
    temporal_evidence: Dict[str, Any] = field(default_factory=dict)
    network_evidence: Dict[str, Any] = field(default_factory=dict)

    # Impact assessment
    estimated_impact: Dict[str, float] = field(default_factory=dict)
    affected_systems: List[str] = field(default_factory=list)


class MultiEntityCoordinationDetector:
    """
    Advanced detector for multi-entity coordination attacks.

    Uses graph analysis, temporal correlation, and behavioral similarity
    to identify sophisticated coordination patterns.
    """

    def __init__(self):
        self.entity_profiles: Dict[str, EntityProfile] = {}
        self.coordination_clusters: Dict[str, CoordinationCluster] = {}
        self.activity_events = deque(maxlen=10000)

        # Detection thresholds
        self.thresholds = {
            "behavioral_similarity_threshold": 0.85,
            "temporal_correlation_threshold": 0.80,
            "network_density_threshold": 0.70,
            "coordination_confidence_threshold": 0.75,
            "cluster_size_min": 3,
            "cluster_size_max": 50,
            "activity_window_minutes": 30,
            "analysis_window_hours": 24,
        }

        # Feature extractors for behavioral analysis - implemented inline for now
        self.feature_extractors = {}

        # Graph analysis structures
        self.entity_graph = {}  # Adjacency list representation
        self.interaction_weights = defaultdict(float)

        self.monitoring_active = False

    async def start_monitoring(self):
        """Start the multi-entity coordination monitoring system."""
        if self.monitoring_active:
            logger.warning("Multi-entity coordination monitoring already active")
            return

        self.monitoring_active = True
        logger.info("Starting multi-entity coordination detection")

        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._continuous_cluster_analysis()),
            asyncio.create_task(self._update_entity_profiles()),
            asyncio.create_task(self._detect_real_time_coordination()),
            asyncio.create_task(self._graph_analysis_cycle()),
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Multi-entity coordination monitoring error: {e}")
            self.monitoring_active = False

    async def stop_monitoring(self):
        """Stop the monitoring system."""
        self.monitoring_active = False
        logger.info("Stopped multi-entity coordination detection")

    async def record_entity_activity(
        self, entity_id: str, activity_data: Dict[str, Any]
    ):
        """Record activity from an entity for analysis."""
        timestamp = datetime.now(timezone.utc)

        # Create or update entity profile
        if entity_id not in self.entity_profiles:
            self.entity_profiles[entity_id] = EntityProfile(
                entity_id=entity_id, first_seen=timestamp, last_activity=timestamp
            )

        profile = self.entity_profiles[entity_id]
        profile.last_activity = timestamp
        profile.activity_timestamps.append(timestamp)

        # Record activity event
        activity_event = {
            "entity_id": entity_id,
            "timestamp": timestamp,
            "activity_type": activity_data.get("activity_type"),
            "data": activity_data,
        }
        self.activity_events.append(activity_event)

        # Update behavioral patterns
        await self._update_behavioral_patterns(entity_id, activity_data)

        # Update entity relationships
        await self._update_entity_relationships(entity_id, activity_data)

        # Check for immediate coordination patterns
        await self._check_immediate_coordination(entity_id, activity_data)

    async def _update_behavioral_patterns(
        self, entity_id: str, activity_data: Dict[str, Any]
    ):
        """Update behavioral patterns for an entity."""
        profile = self.entity_profiles[entity_id]
        activity_type = activity_data.get("activity_type")

        if activity_type == "attribution":
            # Track attribution patterns
            content_hash = activity_data.get("content_hash")
            similarity_score = activity_data.get("similarity_score", 0.0)
            if content_hash:
                profile.attribution_patterns[content_hash] = similarity_score

        elif activity_type == "governance":
            # Track voting patterns
            proposal_id = activity_data.get("proposal_id")
            vote = activity_data.get("vote")
            if proposal_id and vote:
                profile.voting_patterns[proposal_id] = vote

        elif activity_type == "transaction":
            # Track transaction patterns
            transaction_type = activity_data.get("transaction_type")
            amount = activity_data.get("amount", 0.0)
            if transaction_type:
                if transaction_type not in profile.transaction_patterns:
                    profile.transaction_patterns[transaction_type] = 0.0
                profile.transaction_patterns[transaction_type] += float(amount)

    async def _update_entity_relationships(
        self, entity_id: str, activity_data: Dict[str, Any]
    ):
        """Update relationships between entities based on activity."""
        profile = self.entity_profiles[entity_id]

        # Look for related entities in the activity
        related_entities = []

        if "related_entity_ids" in activity_data:
            related_entities.extend(activity_data["related_entity_ids"])

        if "recipient_id" in activity_data:
            related_entities.append(activity_data["recipient_id"])

        if "sender_id" in activity_data:
            related_entities.append(activity_data["sender_id"])

        # Update direct connections
        for related_entity in related_entities:
            if related_entity != entity_id:
                profile.direct_connections.add(related_entity)
                profile.interaction_frequency[related_entity] = (
                    profile.interaction_frequency.get(related_entity, 0) + 1
                )

                # Update graph structure
                if entity_id not in self.entity_graph:
                    self.entity_graph[entity_id] = set()
                if related_entity not in self.entity_graph:
                    self.entity_graph[related_entity] = set()

                self.entity_graph[entity_id].add(related_entity)
                self.entity_graph[related_entity].add(entity_id)

                # Update interaction weights
                edge_key = tuple(sorted([entity_id, related_entity]))
                self.interaction_weights[edge_key] += 1.0

    async def _check_immediate_coordination(
        self, entity_id: str, activity_data: Dict[str, Any]
    ):
        """Check for immediate coordination patterns in real-time."""
        current_time = datetime.now(timezone.utc)
        window_start = current_time - timedelta(
            minutes=self.thresholds["activity_window_minutes"]
        )

        # Get recent activities
        recent_activities = [
            event
            for event in self.activity_events
            if event["timestamp"] >= window_start
        ]

        if len(recent_activities) < 3:
            return

        # Check for temporal coordination
        temporal_clusters = await self._detect_temporal_clusters(recent_activities)
        if temporal_clusters:
            for cluster in temporal_clusters:
                await self._investigate_potential_cluster(cluster)

    async def _detect_temporal_clusters(
        self, activities: List[Dict[str, Any]]
    ) -> List[Set[str]]:
        """Detect clusters of entities with synchronized activity timing."""
        clusters = []

        # Group activities by time buckets (30-second windows)
        time_buckets = defaultdict(list)
        for activity in activities:
            timestamp = activity["timestamp"]
            bucket = timestamp.replace(
                second=timestamp.second // 30 * 30, microsecond=0
            )
            time_buckets[bucket].append(activity)

        # Find buckets with multiple entities
        for bucket_time, bucket_activities in time_buckets.items():
            if len(bucket_activities) >= self.thresholds["cluster_size_min"]:
                entity_set = set(
                    activity["entity_id"] for activity in bucket_activities
                )
                if len(entity_set) >= self.thresholds["cluster_size_min"]:
                    # Check if these entities have similar behavioral patterns
                    if await self._check_behavioral_similarity(entity_set):
                        clusters.append(entity_set)

        return clusters

    async def _check_behavioral_similarity(self, entities: Set[str]) -> bool:
        """Check if a set of entities have similar behavioral patterns."""
        if len(entities) < 2:
            return False

        similarity_scores = []

        # Compare all pairs of entities
        for entity1, entity2 in combinations(entities, 2):
            if entity1 in self.entity_profiles and entity2 in self.entity_profiles:
                similarity = await self._calculate_behavioral_similarity(
                    entity1, entity2
                )
                similarity_scores.append(similarity)

        if not similarity_scores:
            return False

        # Check if average similarity exceeds threshold
        avg_similarity = sum(similarity_scores) / len(similarity_scores)
        return avg_similarity >= self.thresholds["behavioral_similarity_threshold"]

    async def _calculate_behavioral_similarity(
        self, entity1: str, entity2: str
    ) -> float:
        """Calculate behavioral similarity between two entities."""
        profile1 = self.entity_profiles[entity1]
        profile2 = self.entity_profiles[entity2]

        similarity_scores = []

        # Compare temporal patterns
        temporal_sim = await self._calculate_temporal_similarity(profile1, profile2)
        similarity_scores.append(temporal_sim)

        # Compare attribution patterns
        attribution_sim = await self._calculate_attribution_similarity(
            profile1, profile2
        )
        similarity_scores.append(attribution_sim)

        # Compare voting patterns
        voting_sim = await self._calculate_voting_similarity(profile1, profile2)
        similarity_scores.append(voting_sim)

        # Compare transaction patterns
        transaction_sim = await self._calculate_transaction_similarity(
            profile1, profile2
        )
        similarity_scores.append(transaction_sim)

        # Return weighted average
        weights = [0.3, 0.25, 0.25, 0.2]  # Temporal, attribution, voting, transaction
        return sum(score * weight for score, weight in zip(similarity_scores, weights))

    async def _calculate_temporal_similarity(
        self, profile1: EntityProfile, profile2: EntityProfile
    ) -> float:
        """Calculate temporal pattern similarity between two entities."""
        if not profile1.activity_timestamps or not profile2.activity_timestamps:
            return 0.0

        # Convert timestamps to hour-of-day patterns
        hours1 = [ts.hour for ts in profile1.activity_timestamps]
        hours2 = [ts.hour for ts in profile2.activity_timestamps]

        # Create hourly activity histograms
        hist1 = np.histogram(hours1, bins=24, range=(0, 24), density=True)[0]
        hist2 = np.histogram(hours2, bins=24, range=(0, 24), density=True)[0]

        # Calculate cosine similarity
        dot_product = np.dot(hist1, hist2)
        norm1 = np.linalg.norm(hist1)
        norm2 = np.linalg.norm(hist2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def _calculate_attribution_similarity(
        self, profile1: EntityProfile, profile2: EntityProfile
    ) -> float:
        """Calculate attribution pattern similarity."""
        if not profile1.attribution_patterns or not profile2.attribution_patterns:
            return 0.0

        # Find common content hashes
        common_hashes = set(profile1.attribution_patterns.keys()) & set(
            profile2.attribution_patterns.keys()
        )
        if not common_hashes:
            return 0.0

        # Calculate similarity of similarity scores for common content
        similarities = []
        for content_hash in common_hashes:
            score1 = profile1.attribution_patterns[content_hash]
            score2 = profile2.attribution_patterns[content_hash]
            # Both entities having high similarity to the same content is suspicious
            if score1 > 0.8 and score2 > 0.8:
                similarities.append(1.0 - abs(score1 - score2))
            else:
                similarities.append(0.0)

        return sum(similarities) / len(similarities) if similarities else 0.0

    async def _calculate_voting_similarity(
        self, profile1: EntityProfile, profile2: EntityProfile
    ) -> float:
        """Calculate voting pattern similarity."""
        if not profile1.voting_patterns or not profile2.voting_patterns:
            return 0.0

        # Find common proposals
        common_proposals = set(profile1.voting_patterns.keys()) & set(
            profile2.voting_patterns.keys()
        )
        if not common_proposals:
            return 0.0

        # Calculate agreement rate
        agreements = 0
        for proposal_id in common_proposals:
            if (
                profile1.voting_patterns[proposal_id]
                == profile2.voting_patterns[proposal_id]
            ):
                agreements += 1

        return agreements / len(common_proposals)

    async def _calculate_transaction_similarity(
        self, profile1: EntityProfile, profile2: EntityProfile
    ) -> float:
        """Calculate transaction pattern similarity."""
        if not profile1.transaction_patterns or not profile2.transaction_patterns:
            return 0.0

        # Get all transaction types
        all_types = set(profile1.transaction_patterns.keys()) | set(
            profile2.transaction_patterns.keys()
        )
        if not all_types:
            return 0.0

        # Create feature vectors
        vector1 = np.array(
            [profile1.transaction_patterns.get(t, 0.0) for t in all_types]
        )
        vector2 = np.array(
            [profile2.transaction_patterns.get(t, 0.0) for t in all_types]
        )

        # Normalize vectors
        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        vector1 = vector1 / norm1
        vector2 = vector2 / norm2

        # Calculate cosine similarity
        return np.dot(vector1, vector2)

    async def _investigate_potential_cluster(self, entities: Set[str]):
        """Investigate a potential coordination cluster."""
        cluster_id = hashlib.sha256("|".join(sorted(entities)).encode()).hexdigest()[
            :16
        ]

        if cluster_id in self.coordination_clusters:
            # Update existing cluster
            cluster = self.coordination_clusters[cluster_id]
            cluster.last_activity = datetime.now(timezone.utc)
            cluster.entities.update(entities)
        else:
            # Create new cluster
            cluster = CoordinationCluster(
                cluster_id=cluster_id,
                entities=entities,
                coordination_type=CoordinationType.ATTRIBUTION_RING,  # Default, will be refined
                confidence_score=0.0,
                first_detected=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
            )

            self.coordination_clusters[cluster_id] = cluster

        # Perform detailed analysis
        await self._analyze_cluster(cluster)

    async def _analyze_cluster(self, cluster: CoordinationCluster):
        """Perform detailed analysis of a coordination cluster."""

        # Calculate confidence score
        behavioral_score = await self._calculate_cluster_behavioral_score(
            cluster.entities
        )
        temporal_score = await self._calculate_cluster_temporal_score(cluster.entities)
        network_score = await self._calculate_cluster_network_score(cluster.entities)

        cluster.confidence_score = (
            behavioral_score + temporal_score + network_score
        ) / 3

        # Determine coordination type
        cluster.coordination_type = await self._determine_coordination_type(
            cluster.entities
        )

        # Collect evidence
        cluster.behavioral_evidence = await self._collect_behavioral_evidence(
            cluster.entities
        )
        cluster.temporal_evidence = await self._collect_temporal_evidence(
            cluster.entities
        )
        cluster.network_evidence = await self._collect_network_evidence(
            cluster.entities
        )

        # Assess impact
        cluster.estimated_impact = await self._assess_cluster_impact(cluster.entities)

        # If confidence is high enough, trigger alert
        if (
            cluster.confidence_score
            >= self.thresholds["coordination_confidence_threshold"]
        ):
            await self._trigger_coordination_alert(cluster)

    async def _calculate_cluster_behavioral_score(self, entities: Set[str]) -> float:
        """Calculate behavioral coordination score for a cluster."""
        if len(entities) < 2:
            return 0.0

        similarity_scores = []
        for entity1, entity2 in combinations(entities, 2):
            if entity1 in self.entity_profiles and entity2 in self.entity_profiles:
                similarity = await self._calculate_behavioral_similarity(
                    entity1, entity2
                )
                similarity_scores.append(similarity)

        return (
            sum(similarity_scores) / len(similarity_scores)
            if similarity_scores
            else 0.0
        )

    async def _calculate_cluster_temporal_score(self, entities: Set[str]) -> float:
        """Calculate temporal coordination score for a cluster."""
        current_time = datetime.now(timezone.utc)
        window_start = current_time - timedelta(
            hours=self.thresholds["analysis_window_hours"]
        )

        # Get recent activities for all entities
        entity_activities = defaultdict(list)
        for event in self.activity_events:
            if event["entity_id"] in entities and event["timestamp"] >= window_start:
                entity_activities[event["entity_id"]].append(event["timestamp"])

        if len(entity_activities) < 2:
            return 0.0

        # Calculate temporal correlation
        correlations = []
        entity_list = list(entity_activities.keys())

        for i in range(len(entity_list)):
            for j in range(i + 1, len(entity_list)):
                entity1_times = entity_activities[entity_list[i]]
                entity2_times = entity_activities[entity_list[j]]

                correlation = await self._calculate_temporal_correlation(
                    entity1_times, entity2_times
                )
                correlations.append(correlation)

        return sum(correlations) / len(correlations) if correlations else 0.0

    async def _calculate_temporal_correlation(
        self, times1: List[datetime], times2: List[datetime]
    ) -> float:
        """Calculate temporal correlation between two sets of timestamps."""
        if not times1 or not times2:
            return 0.0

        # Convert to time buckets (10-minute intervals)
        def to_buckets(times):
            buckets = set()
            for t in times:
                bucket = t.replace(minute=t.minute // 10 * 10, second=0, microsecond=0)
                buckets.add(bucket)
            return buckets

        buckets1 = to_buckets(times1)
        buckets2 = to_buckets(times2)

        # Calculate Jaccard similarity
        intersection = len(buckets1 & buckets2)
        union = len(buckets1 | buckets2)

        return intersection / union if union > 0 else 0.0

    async def _calculate_cluster_network_score(self, entities: Set[str]) -> float:
        """Calculate network connectivity score for a cluster."""
        if len(entities) < 2:
            return 0.0

        # Count connections within the cluster
        internal_connections = 0
        total_possible = len(entities) * (len(entities) - 1) // 2

        for entity1, entity2 in combinations(entities, 2):
            if (
                entity1 in self.entity_profiles
                and entity2 in self.entity_profiles[entity1].direct_connections
            ):
                internal_connections += 1

        # Calculate network density
        density = internal_connections / total_possible if total_possible > 0 else 0.0

        return min(density / self.thresholds["network_density_threshold"], 1.0)

    async def _determine_coordination_type(
        self, entities: Set[str]
    ) -> CoordinationType:
        """Determine the type of coordination based on behavioral patterns."""

        # Analyze predominant activity types
        activity_counts = defaultdict(int)
        for entity_id in entities:
            if entity_id in self.entity_profiles:
                profile = self.entity_profiles[entity_id]
                if profile.attribution_patterns:
                    activity_counts["attribution"] += len(profile.attribution_patterns)
                if profile.voting_patterns:
                    activity_counts["governance"] += len(profile.voting_patterns)
                if profile.transaction_patterns:
                    activity_counts["transaction"] += len(profile.transaction_patterns)

        # Determine primary coordination type
        if not activity_counts:
            return CoordinationType.SYBIL_NETWORK

        primary_activity = max(activity_counts.keys(), key=lambda k: activity_counts[k])

        if primary_activity == "attribution":
            return CoordinationType.ATTRIBUTION_RING
        elif primary_activity == "governance":
            return CoordinationType.GOVERNANCE_CARTEL
        elif primary_activity == "transaction":
            return CoordinationType.WASH_TRADING_RING
        else:
            return CoordinationType.SYBIL_NETWORK

    async def _collect_behavioral_evidence(self, entities: Set[str]) -> Dict[str, Any]:
        """Collect behavioral evidence for a coordination cluster."""
        evidence = {
            "entity_count": len(entities),
            "similarity_scores": {},
            "common_patterns": {},
        }

        # Calculate pairwise similarities
        for entity1, entity2 in combinations(entities, 2):
            if entity1 in self.entity_profiles and entity2 in self.entity_profiles:
                similarity = await self._calculate_behavioral_similarity(
                    entity1, entity2
                )
                evidence["similarity_scores"][f"{entity1}_{entity2}"] = similarity

        return evidence

    async def _collect_temporal_evidence(self, entities: Set[str]) -> Dict[str, Any]:
        """Collect temporal evidence for coordination."""
        evidence = {
            "synchronized_activities": [],
            "activity_correlation": {},
        }

        current_time = datetime.now(timezone.utc)
        window_start = current_time - timedelta(hours=1)

        # Find synchronized activities
        time_buckets = defaultdict(list)
        for event in self.activity_events:
            if event["entity_id"] in entities and event["timestamp"] >= window_start:
                bucket = event["timestamp"].replace(second=0, microsecond=0)
                time_buckets[bucket].append(event)

        # Collect buckets with multiple entities
        for bucket_time, bucket_events in time_buckets.items():
            entity_ids = set(event["entity_id"] for event in bucket_events)
            if len(entity_ids) >= 2:
                evidence["synchronized_activities"].append(
                    {
                        "timestamp": bucket_time.isoformat(),
                        "entities": list(entity_ids),
                        "activity_count": len(bucket_events),
                    }
                )

        return evidence

    async def _collect_network_evidence(self, entities: Set[str]) -> Dict[str, Any]:
        """Collect network structure evidence."""
        evidence = {
            "internal_connections": 0,
            "connection_density": 0.0,
            "hub_entities": [],
        }

        # Count internal connections
        internal_connections = 0
        connection_counts = defaultdict(int)

        for entity_id in entities:
            if entity_id in self.entity_profiles:
                profile = self.entity_profiles[entity_id]
                for connected_entity in profile.direct_connections:
                    if connected_entity in entities:
                        internal_connections += 1
                        connection_counts[entity_id] += 1

        evidence["internal_connections"] = (
            internal_connections // 2
        )  # Avoid double counting

        total_possible = len(entities) * (len(entities) - 1) // 2
        evidence["connection_density"] = (
            internal_connections / 2 / total_possible if total_possible > 0 else 0.0
        )

        # Identify hub entities (highly connected within cluster)
        avg_connections = (
            sum(connection_counts.values()) / len(entities) if entities else 0
        )
        evidence["hub_entities"] = [
            entity_id
            for entity_id, count in connection_counts.items()
            if count > avg_connections * 1.5
        ]

        return evidence

    async def _assess_cluster_impact(self, entities: Set[str]) -> Dict[str, float]:
        """Assess the potential impact of a coordination cluster."""
        impact = {
            "attribution_impact": 0.0,
            "economic_impact": 0.0,
            "governance_impact": 0.0,
        }

        for entity_id in entities:
            if entity_id in self.entity_profiles:
                profile = self.entity_profiles[entity_id]

                # Attribution impact based on content similarity scores
                if profile.attribution_patterns:
                    high_similarity_count = sum(
                        1
                        for score in profile.attribution_patterns.values()
                        if score > 0.9
                    )
                    impact["attribution_impact"] += high_similarity_count * 0.1

                # Economic impact based on transaction volumes
                if profile.transaction_patterns:
                    total_value = sum(profile.transaction_patterns.values())
                    impact["economic_impact"] += float(total_value) * 0.001

                # Governance impact based on voting activity
                if profile.voting_patterns:
                    impact["governance_impact"] += len(profile.voting_patterns) * 0.05

        return impact

    async def _trigger_coordination_alert(self, cluster: CoordinationCluster):
        """Trigger an alert for detected coordination."""
        logger.warning(
            f"COORDINATION DETECTED: {cluster.coordination_type.value} cluster "
            f"with {len(cluster.entities)} entities (confidence: {cluster.confidence_score:.2f})"
        )

        # Integration with the main security monitor
        try:
            from src.economic.security_monitor import security_monitor

            alert_data = {
                "attack_type": "multi_entity_coordination",
                "threat_level": "high" if cluster.confidence_score > 0.85 else "medium",
                "cluster_id": cluster.cluster_id,
                "coordination_type": cluster.coordination_type.value,
                "entities": list(cluster.entities),
                "confidence_score": cluster.confidence_score,
                "evidence": {
                    "behavioral": cluster.behavioral_evidence,
                    "temporal": cluster.temporal_evidence,
                    "network": cluster.network_evidence,
                },
                "estimated_impact": cluster.estimated_impact,
            }

            await security_monitor.record_attribution_event(alert_data)

        except ImportError:
            logger.error("Could not integrate with security monitor")

    async def _continuous_cluster_analysis(self):
        """Continuously analyze all entities for coordination patterns."""
        while self.monitoring_active:
            try:
                await self._perform_full_cluster_analysis()
                await asyncio.sleep(300)  # Full analysis every 5 minutes
            except Exception as e:
                logger.error(f"Continuous cluster analysis error: {e}")
                await asyncio.sleep(600)

    async def _perform_full_cluster_analysis(self):
        """Perform comprehensive cluster analysis on all entities."""
        if len(self.entity_profiles) < self.thresholds["cluster_size_min"]:
            return

        # Get all entities with recent activity
        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time - timedelta(
            hours=self.thresholds["analysis_window_hours"]
        )

        active_entities = set()
        for entity_id, profile in self.entity_profiles.items():
            if profile.last_activity >= cutoff_time:
                active_entities.add(entity_id)

        if len(active_entities) < self.thresholds["cluster_size_min"]:
            return

        # Use graph clustering to find potential coordination groups
        clusters = await self._graph_clustering(active_entities)

        # Analyze each cluster
        for cluster_entities in clusters:
            if len(cluster_entities) >= self.thresholds["cluster_size_min"]:
                await self._investigate_potential_cluster(cluster_entities)

    async def _graph_clustering(self, entities: Set[str]) -> List[Set[str]]:
        """Perform graph clustering to identify coordination groups."""
        clusters = []
        visited = set()

        # Use connected components analysis
        for entity_id in entities:
            if entity_id not in visited:
                cluster = await self._find_connected_component(
                    entity_id, entities, visited
                )
                if len(cluster) >= self.thresholds["cluster_size_min"]:
                    clusters.append(cluster)

        return clusters

    async def _find_connected_component(
        self, start_entity: str, all_entities: Set[str], visited: Set[str]
    ) -> Set[str]:
        """Find connected component starting from an entity."""
        component = set()
        stack = [start_entity]

        while stack:
            entity_id = stack.pop()
            if entity_id in visited:
                continue

            visited.add(entity_id)
            component.add(entity_id)

            # Add connected entities to stack
            if entity_id in self.entity_profiles:
                profile = self.entity_profiles[entity_id]
                for connected_entity in profile.direct_connections:
                    if (
                        connected_entity in all_entities
                        and connected_entity not in visited
                    ):
                        # Check if connection strength is significant
                        interaction_count = profile.interaction_frequency.get(
                            connected_entity, 0
                        )
                        if interaction_count >= 3:  # Minimum interaction threshold
                            stack.append(connected_entity)

        return component

    async def _update_entity_profiles(self):
        """Periodically update entity profiles and coordination scores."""
        while self.monitoring_active:
            try:
                await self._update_all_coordination_scores()
                await asyncio.sleep(180)  # Update every 3 minutes
            except Exception as e:
                logger.error(f"Entity profile update error: {e}")
                await asyncio.sleep(360)

    async def _update_all_coordination_scores(self):
        """Update coordination scores for all entities."""
        for entity_id, profile in self.entity_profiles.items():
            coordination_score = await self._calculate_entity_coordination_score(
                entity_id
            )
            profile.coordination_score = coordination_score

            # Update suspicious behaviors
            if coordination_score > 0.7:
                behavior = f"High coordination score: {coordination_score:.3f}"
                if behavior not in profile.suspicious_behaviors:
                    profile.suspicious_behaviors.append(behavior)
                    profile.coordination_events.append(datetime.now(timezone.utc))

    async def _calculate_entity_coordination_score(self, entity_id: str) -> float:
        """Calculate coordination score for a single entity."""
        profile = self.entity_profiles[entity_id]

        scores = []

        # Connection density score
        if profile.direct_connections:
            connection_score = min(len(profile.direct_connections) / 10, 1.0)
            scores.append(connection_score)

        # Activity pattern regularity score (high regularity can indicate automation)
        if len(profile.activity_timestamps) > 10:
            timestamps = list(profile.activity_timestamps)
            intervals = [
                (timestamps[i + 1] - timestamps[i]).total_seconds()
                for i in range(len(timestamps) - 1)
            ]

            if intervals:
                # Calculate coefficient of variation (lower = more regular)
                mean_interval = sum(intervals) / len(intervals)
                variance = sum(
                    (interval - mean_interval) ** 2 for interval in intervals
                ) / len(intervals)
                std_dev = variance**0.5
                cv = std_dev / mean_interval if mean_interval > 0 else 0

                # Convert to coordination score (lower CV = higher coordination)
                regularity_score = max(0, 1 - cv / 100)
                scores.append(regularity_score)

        # Attribution similarity concentration score
        if profile.attribution_patterns:
            high_similarity_ratio = sum(
                1 for score in profile.attribution_patterns.values() if score > 0.85
            ) / len(profile.attribution_patterns)
            scores.append(high_similarity_ratio)

        # Return average score
        return sum(scores) / len(scores) if scores else 0.0

    async def _detect_real_time_coordination(self):
        """Detect coordination patterns in real-time activity stream."""
        while self.monitoring_active:
            try:
                await self._analyze_recent_activity_patterns()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Real-time coordination detection error: {e}")
                await asyncio.sleep(60)

    async def _analyze_recent_activity_patterns(self):
        """Analyze recent activity for coordination patterns."""
        current_time = datetime.now(timezone.utc)
        window_start = current_time - timedelta(minutes=5)

        # Get very recent activities
        recent_activities = [
            event
            for event in self.activity_events
            if event["timestamp"] >= window_start
        ]

        if len(recent_activities) < 3:
            return

        # Check for burst patterns
        await self._check_activity_bursts(recent_activities)

        # Check for identical patterns
        await self._check_identical_patterns(recent_activities)

    async def _check_activity_bursts(self, activities: List[Dict[str, Any]]):
        """Check for suspicious activity bursts."""
        # Group by entity
        entity_activities = defaultdict(list)
        for activity in activities:
            entity_activities[activity["entity_id"]].append(activity)

        # Check for entities with unusual burst activity
        suspicious_entities = []
        for entity_id, entity_activities_list in entity_activities.items():
            if len(entity_activities_list) > 3:  # More than 3 activities in 5 minutes
                suspicious_entities.append(entity_id)

        # If multiple entities show burst patterns, investigate coordination
        if len(suspicious_entities) >= 2:
            await self._investigate_potential_cluster(set(suspicious_entities))

    async def _check_identical_patterns(self, activities: List[Dict[str, Any]]):
        """Check for identical activity patterns across entities."""
        # Group by activity signature
        pattern_groups = defaultdict(list)

        for activity in activities:
            # Create activity signature (excluding entity_id and timestamp)
            signature_data = {
                k: v
                for k, v in activity["data"].items()
                if k not in ["entity_id", "timestamp"]
            }
            signature = json.dumps(signature_data, sort_keys=True)
            pattern_groups[signature].append(activity["entity_id"])

        # Check for patterns shared by multiple entities
        for signature, entities in pattern_groups.items():
            unique_entities = set(entities)
            if len(unique_entities) >= 2:  # Same pattern used by multiple entities
                await self._investigate_potential_cluster(unique_entities)

    async def _graph_analysis_cycle(self):
        """Perform periodic graph analysis for coordination detection."""
        while self.monitoring_active:
            try:
                await self._analyze_entity_graph()
                await asyncio.sleep(600)  # Full graph analysis every 10 minutes
            except Exception as e:
                logger.error(f"Graph analysis cycle error: {e}")
                await asyncio.sleep(1200)

    async def _analyze_entity_graph(self):
        """Analyze the entity relationship graph for coordination patterns."""
        if len(self.entity_graph) < 3:
            return

        # Find dense subgraphs (potential coordination clusters)
        dense_subgraphs = await self._find_dense_subgraphs()

        for subgraph in dense_subgraphs:
            if len(subgraph) >= self.thresholds["cluster_size_min"]:
                await self._investigate_potential_cluster(subgraph)

    async def _find_dense_subgraphs(self) -> List[Set[str]]:
        """Find dense subgraphs in the entity relationship graph."""
        dense_subgraphs = []

        # Use a simple greedy approach to find dense subgraphs
        for entity_id in self.entity_graph:
            if entity_id not in self.entity_profiles:
                continue

            # Start with entity and its neighbors
            candidates = {entity_id} | self.entity_graph.get(entity_id, set())

            # Iteratively add entities that increase density
            best_subgraph = {entity_id}
            best_density = 0.0

            while candidates:
                best_addition = None
                best_new_density = best_density

                for candidate in candidates:
                    test_subgraph = best_subgraph | {candidate}
                    density = await self._calculate_subgraph_density(test_subgraph)

                    if density > best_new_density:
                        best_addition = candidate
                        best_new_density = density

                if best_addition:
                    best_subgraph.add(best_addition)
                    candidates.remove(best_addition)
                    best_density = best_new_density
                else:
                    break

            # Only keep subgraphs with high density
            if (
                len(best_subgraph) >= 3
                and best_density >= self.thresholds["network_density_threshold"]
            ):
                dense_subgraphs.append(best_subgraph)

        # Remove duplicate subgraphs
        unique_subgraphs = []
        for subgraph in dense_subgraphs:
            is_duplicate = False
            for existing in unique_subgraphs:
                if len(subgraph & existing) / len(subgraph | existing) > 0.8:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_subgraphs.append(subgraph)

        return unique_subgraphs

    async def _calculate_subgraph_density(self, entities: Set[str]) -> float:
        """Calculate the density of a subgraph."""
        if len(entities) < 2:
            return 0.0

        # Count edges within the subgraph
        edges = 0
        for entity1 in entities:
            for entity2 in self.entity_graph.get(entity1, set()):
                if entity2 in entities and entity1 < entity2:  # Avoid double counting
                    edges += 1

        # Calculate density
        max_edges = len(entities) * (len(entities) - 1) // 2
        return edges / max_edges if max_edges > 0 else 0.0

    def get_coordination_summary(self) -> Dict[str, Any]:
        """Get a summary of detected coordination patterns."""
        return {
            "total_entities": len(self.entity_profiles),
            "coordination_clusters": len(self.coordination_clusters),
            "high_risk_entities": len(
                [
                    entity_id
                    for entity_id, profile in self.entity_profiles.items()
                    if profile.coordination_score > 0.7
                ]
            ),
            "cluster_types": {
                coord_type.value: len(
                    [
                        cluster
                        for cluster in self.coordination_clusters.values()
                        if cluster.coordination_type == coord_type
                    ]
                )
                for coord_type in CoordinationType
            },
            "monitoring_active": self.monitoring_active,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def get_entity_risk_profile(self, entity_id: str) -> Dict[str, Any]:
        """Get risk profile for a specific entity."""
        if entity_id not in self.entity_profiles:
            return {"error": "Entity not found"}

        profile = self.entity_profiles[entity_id]

        return {
            "entity_id": entity_id,
            "coordination_score": profile.coordination_score,
            "first_seen": profile.first_seen.isoformat(),
            "last_activity": profile.last_activity.isoformat(),
            "direct_connections": len(profile.direct_connections),
            "suspicious_behaviors": profile.suspicious_behaviors,
            "coordination_events": len(profile.coordination_events),
            "risk_level": (
                "high"
                if profile.coordination_score > 0.7
                else "medium"
                if profile.coordination_score > 0.4
                else "low"
            ),
        }


# Global detector instance
multi_entity_detector = MultiEntityCoordinationDetector()


# Convenience functions
async def start_coordination_detection():
    """Start the multi-entity coordination detection system."""
    await multi_entity_detector.start_monitoring()


async def stop_coordination_detection():
    """Stop the multi-entity coordination detection system."""
    await multi_entity_detector.stop_monitoring()


async def record_entity_activity(entity_id: str, **activity_data):
    """Record entity activity for coordination detection."""
    await multi_entity_detector.record_entity_activity(entity_id, activity_data)
