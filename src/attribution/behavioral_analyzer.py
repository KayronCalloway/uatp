"""
Behavioral Analysis System for Coordinated Account Detection.

This module implements advanced behavioral analysis to detect coordinated
account activity, Sybil attacks, and attribution farming operations through
pattern recognition and machine learning techniques.

SECURITY FEATURES:
- Multi-dimensional behavioral fingerprinting
- Temporal pattern analysis
- Network topology detection
- Machine learning-based clustering
- Anomaly detection algorithms
"""

import logging
import pickle
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from scipy import stats
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


@dataclass
class BehavioralProfile:
    """Comprehensive behavioral profile for an entity."""

    entity_id: str
    entity_type: str  # user, ai_model, organization

    # Temporal behavior patterns
    activity_hours: Dict[int, int] = field(default_factory=dict)  # hour -> count
    activity_days: Dict[int, int] = field(default_factory=dict)  # day_of_week -> count
    session_durations: List[float] = field(default_factory=list)  # minutes
    inter_action_intervals: List[float] = field(default_factory=list)  # seconds

    # Attribution behavior patterns
    attribution_frequencies: List[float] = field(default_factory=list)
    similarity_score_patterns: List[float] = field(default_factory=list)
    confidence_score_patterns: List[float] = field(default_factory=list)
    content_length_patterns: List[int] = field(default_factory=list)

    # Interaction patterns
    interaction_partners: Dict[str, int] = field(
        default_factory=dict
    )  # entity_id -> count
    response_times: List[float] = field(default_factory=list)  # seconds
    conversation_patterns: Dict[str, int] = field(
        default_factory=dict
    )  # pattern -> count

    # Content patterns
    vocabulary_diversity: float = 0.0
    linguistic_features: Dict[str, float] = field(default_factory=dict)
    topic_distributions: Dict[str, float] = field(default_factory=dict)

    # Device/Environment patterns (when available)
    user_agents: Set[str] = field(default_factory=set)
    ip_address_patterns: Set[str] = field(default_factory=set)
    timezone_patterns: Dict[str, int] = field(default_factory=dict)

    # Metadata
    first_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_actions: int = 0
    profile_version: int = 1

    def calculate_behavioral_fingerprint(self) -> np.ndarray:
        """Calculate normalized behavioral fingerprint vector."""

        features = []

        # Temporal features
        if self.activity_hours:
            # Hour distribution entropy
            hour_counts = np.array(list(self.activity_hours.values()))
            hour_probs = hour_counts / hour_counts.sum()
            hour_entropy = -np.sum(hour_probs * np.log2(hour_probs + 1e-10))
            features.append(hour_entropy)

            # Peak activity hour
            peak_hour = max(self.activity_hours, key=self.activity_hours.get)
            features.append(peak_hour / 23.0)  # Normalize to 0-1
        else:
            features.extend([0.0, 0.0])

        # Session behavior
        if self.session_durations:
            features.extend(
                [
                    np.mean(self.session_durations),
                    np.std(self.session_durations),
                    np.median(self.session_durations),
                ]
            )
        else:
            features.extend([0.0, 0.0, 0.0])

        # Attribution patterns
        if self.similarity_score_patterns:
            features.extend(
                [
                    np.mean(self.similarity_score_patterns),
                    np.std(self.similarity_score_patterns),
                    len(np.unique(self.similarity_score_patterns))
                    / len(self.similarity_score_patterns),
                ]
            )
        else:
            features.extend([0.0, 0.0, 0.0])

        # Interaction diversity
        interaction_diversity = len(self.interaction_partners) / max(
            1, self.total_actions
        )
        features.append(interaction_diversity)

        # Response time patterns
        if self.response_times:
            features.extend([np.mean(self.response_times), np.std(self.response_times)])
        else:
            features.extend([0.0, 0.0])

        # Content diversity
        features.append(self.vocabulary_diversity)

        # Device/Environment diversity
        features.extend(
            [
                len(self.user_agents),
                len(self.ip_address_patterns),
                len(self.timezone_patterns),
            ]
        )

        return np.array(features, dtype=np.float32)

    def calculate_similarity_to(self, other_profile: "BehavioralProfile") -> float:
        """Calculate behavioral similarity to another profile."""

        fingerprint1 = self.calculate_behavioral_fingerprint()
        fingerprint2 = other_profile.calculate_behavioral_fingerprint()

        # Ensure same dimensionality
        min_len = min(len(fingerprint1), len(fingerprint2))
        fingerprint1 = fingerprint1[:min_len]
        fingerprint2 = fingerprint2[:min_len]

        # Calculate cosine similarity
        dot_product = np.dot(fingerprint1, fingerprint2)
        norm1 = np.linalg.norm(fingerprint1)
        norm2 = np.linalg.norm(fingerprint2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def detect_anomalies(self) -> List[str]:
        """Detect anomalous patterns in this profile."""

        anomalies = []

        # Temporal anomalies
        if self.activity_hours:
            # Check for 24/7 activity (bot-like)
            active_hours = len(
                [h for h, count in self.activity_hours.items() if count > 0]
            )
            if active_hours > 20:  # Active in more than 20 hours
                anomalies.append("excessive_temporal_coverage")

            # Check for burst activity
            max_hourly_activity = max(self.activity_hours.values())
            avg_hourly_activity = sum(self.activity_hours.values()) / len(
                self.activity_hours
            )
            if max_hourly_activity > avg_hourly_activity * 10:
                anomalies.append("burst_activity_pattern")

        # Attribution anomalies
        if self.confidence_score_patterns:
            # Check for artificial uniformity
            if len(set(self.confidence_score_patterns)) == 1:
                anomalies.append("uniform_confidence_scores")

            # Check for threshold clustering
            thresholds = [0.2, 0.5, 0.8]
            for threshold in thresholds:
                near_threshold = [
                    s
                    for s in self.confidence_score_patterns
                    if abs(s - threshold) < 0.05
                ]
                if len(near_threshold) / len(self.confidence_score_patterns) > 0.4:
                    anomalies.append("threshold_clustering")
                    break

        # Response time anomalies
        if self.response_times:
            response_std = np.std(self.response_times)
            if response_std < 1.0:  # Very consistent response times (bot-like)
                anomalies.append("mechanical_response_timing")

        # Interaction pattern anomalies
        if self.interaction_partners:
            # Check for excessive reciprocity
            total_interactions = sum(self.interaction_partners.values())
            unique_partners = len(self.interaction_partners)
            if unique_partners > 1:
                reciprocity_ratio = total_interactions / unique_partners
                if reciprocity_ratio > 10:  # High repetition with same partners
                    anomalies.append("excessive_partner_reciprocity")

        return anomalies


@dataclass
class CoordinatedBehaviorCluster:
    """Detected cluster of coordinated behavior."""

    cluster_id: str
    entity_ids: List[str]
    cluster_type: str  # sybil, coordinated, farming, etc.

    # Behavioral similarity metrics
    avg_similarity: float = 0.0
    similarity_matrix: Optional[np.ndarray] = None
    behavioral_fingerprint: Optional[np.ndarray] = None

    # Temporal coordination metrics
    temporal_correlation: float = 0.0
    synchronized_activities: List[datetime] = field(default_factory=list)

    # Evidence and indicators
    coordination_indicators: List[str] = field(default_factory=list)
    anomaly_scores: Dict[str, float] = field(default_factory=dict)

    # Metadata
    detection_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert cluster to dictionary."""
        return {
            "cluster_id": self.cluster_id,
            "entity_ids": self.entity_ids,
            "cluster_type": self.cluster_type,
            "avg_similarity": self.avg_similarity,
            "temporal_correlation": self.temporal_correlation,
            "coordination_indicators": self.coordination_indicators,
            "anomaly_scores": self.anomaly_scores,
            "detection_timestamp": self.detection_timestamp.isoformat(),
            "confidence": self.confidence,
            "cluster_size": len(self.entity_ids),
        }


class BehavioralAnalyzer:
    """Advanced behavioral analysis system for coordinated account detection."""

    def __init__(self):
        # Profile storage
        self.behavioral_profiles: Dict[str, BehavioralProfile] = {}

        # Activity tracking
        self.activity_log: deque = deque(maxlen=50000)  # Recent activities
        self.session_tracker: Dict[str, Dict[str, Any]] = {}  # Active sessions

        # Network analysis
        self.interaction_graph = nx.Graph() if NETWORKX_AVAILABLE else None

        # Clustering and ML models
        self.scaler = StandardScaler()
        self.clustering_model = None
        self.pca_model = None

        # Detection configuration
        self.config = {
            "similarity_threshold": 0.85,
            "cluster_min_size": 3,
            "cluster_eps": 0.3,
            "temporal_correlation_threshold": 0.8,
            "anomaly_detection_threshold": 2.5,
            "profile_update_frequency": 100,  # actions
            "clustering_frequency": 1000,  # actions
            "max_profile_age_days": 90,
        }

        # Detected clusters
        self.detected_clusters: Dict[str, CoordinatedBehaviorCluster] = {}

        # Performance metrics
        self.metrics = {
            "profiles_created": 0,
            "activities_processed": 0,
            "clusters_detected": 0,
            "anomalies_detected": 0,
            "coordinated_accounts_flagged": 0,
            "false_positives": 0,
        }

        logger.info("Behavioral Analyzer initialized")

    def update_behavioral_profile(
        self,
        entity_id: str,
        entity_type: str,
        activity_data: Dict[str, Any],
        context: Dict[str, Any] = None,
    ):
        """Update behavioral profile with new activity data."""

        self.metrics["activities_processed"] += 1
        context = context or {}

        # Create profile if doesn't exist
        if entity_id not in self.behavioral_profiles:
            self.behavioral_profiles[entity_id] = BehavioralProfile(
                entity_id=entity_id, entity_type=entity_type
            )
            self.metrics["profiles_created"] += 1

        profile = self.behavioral_profiles[entity_id]
        profile.last_activity = datetime.now(timezone.utc)
        profile.total_actions += 1

        # Update temporal patterns
        current_time = datetime.now(timezone.utc)
        profile.activity_hours[current_time.hour] = (
            profile.activity_hours.get(current_time.hour, 0) + 1
        )
        profile.activity_days[current_time.weekday()] = (
            profile.activity_days.get(current_time.weekday(), 0) + 1
        )

        # Update attribution patterns
        if "similarity_score" in activity_data:
            profile.similarity_score_patterns.append(activity_data["similarity_score"])
            # Keep only recent patterns
            if len(profile.similarity_score_patterns) > 1000:
                profile.similarity_score_patterns = profile.similarity_score_patterns[
                    -500:
                ]

        if "confidence_score" in activity_data:
            profile.confidence_score_patterns.append(activity_data["confidence_score"])
            if len(profile.confidence_score_patterns) > 1000:
                profile.confidence_score_patterns = profile.confidence_score_patterns[
                    -500:
                ]

        # Update interaction patterns
        if "interaction_partner" in activity_data:
            partner_id = activity_data["interaction_partner"]
            profile.interaction_partners[partner_id] = (
                profile.interaction_partners.get(partner_id, 0) + 1
            )

            # Update interaction graph
            if NETWORKX_AVAILABLE and self.interaction_graph is not None:
                self.interaction_graph.add_edge(entity_id, partner_id)

        # Update response time patterns
        if "response_time" in activity_data:
            profile.response_times.append(activity_data["response_time"])
            if len(profile.response_times) > 1000:
                profile.response_times = profile.response_times[-500:]

        # Update content patterns
        if "content_length" in activity_data:
            profile.content_length_patterns.append(activity_data["content_length"])
            if len(profile.content_length_patterns) > 1000:
                profile.content_length_patterns = profile.content_length_patterns[-500:]

        # Update device/environment patterns
        if "user_agent" in context:
            profile.user_agents.add(context["user_agent"])

        if "ip_address" in context:
            # Store IP pattern (first 3 octets for privacy)
            ip_parts = context["ip_address"].split(".")
            if len(ip_parts) >= 3:
                ip_pattern = ".".join(ip_parts[:3]) + ".x"
                profile.ip_address_patterns.add(ip_pattern)

        if "timezone" in context:
            profile.timezone_patterns[context["timezone"]] = (
                profile.timezone_patterns.get(context["timezone"], 0) + 1
            )

        # Store activity in log
        self.activity_log.append(
            {
                "entity_id": entity_id,
                "timestamp": current_time,
                "activity_data": activity_data,
                "context": context,
            }
        )

        # Periodic clustering analysis
        if (
            self.metrics["activities_processed"] % self.config["clustering_frequency"]
            == 0
        ):
            self._perform_clustering_analysis()

        # Profile maintenance
        if profile.total_actions % self.config["profile_update_frequency"] == 0:
            self._update_profile_features(profile)

    def detect_coordinated_behavior(
        self,
        target_entities: Optional[List[str]] = None,
        analysis_window_hours: int = 24,
    ) -> List[CoordinatedBehaviorCluster]:
        """Detect coordinated behavior patterns among entities."""

        # Determine entities to analyze
        if target_entities is None:
            # Analyze all entities with recent activity
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=analysis_window_hours
            )
            target_entities = [
                entity_id
                for entity_id, profile in self.behavioral_profiles.items()
                if profile.last_activity > cutoff_time
            ]

        if len(target_entities) < 2:
            return []

        # Filter entities that exist in profiles
        valid_entities = [
            entity_id
            for entity_id in target_entities
            if entity_id in self.behavioral_profiles
        ]

        if len(valid_entities) < 2:
            return []

        detected_clusters = []

        # 1. Behavioral similarity clustering
        similarity_clusters = self._detect_behavioral_similarity_clusters(
            valid_entities
        )
        detected_clusters.extend(similarity_clusters)

        # 2. Temporal coordination detection
        temporal_clusters = self._detect_temporal_coordination(
            valid_entities, analysis_window_hours
        )
        detected_clusters.extend(temporal_clusters)

        # 3. Network topology analysis
        if NETWORKX_AVAILABLE:
            network_clusters = self._detect_network_coordination(valid_entities)
            detected_clusters.extend(network_clusters)

        # 4. Anomaly-based clustering
        anomaly_clusters = self._detect_anomaly_clusters(valid_entities)
        detected_clusters.extend(anomaly_clusters)

        # Store detected clusters
        for cluster in detected_clusters:
            self.detected_clusters[cluster.cluster_id] = cluster
            self.metrics["clusters_detected"] += 1
            self.metrics["coordinated_accounts_flagged"] += len(cluster.entity_ids)

            # Emit security event
            audit_emitter.emit_security_event(
                "coordinated_behavior_cluster_detected",
                {
                    "cluster_id": cluster.cluster_id,
                    "cluster_type": cluster.cluster_type,
                    "entity_count": len(cluster.entity_ids),
                    "confidence": cluster.confidence,
                    "indicators": cluster.coordination_indicators,
                },
            )

        return detected_clusters

    def _detect_behavioral_similarity_clusters(
        self, entity_ids: List[str]
    ) -> List[CoordinatedBehaviorCluster]:
        """Detect clusters based on behavioral similarity."""

        if len(entity_ids) < self.config["cluster_min_size"]:
            return []

        # Extract behavioral fingerprints
        fingerprints = []
        valid_entities = []

        for entity_id in entity_ids:
            if entity_id in self.behavioral_profiles:
                profile = self.behavioral_profiles[entity_id]
                fingerprint = profile.calculate_behavioral_fingerprint()

                if len(fingerprint) > 0 and not np.all(fingerprint == 0):
                    fingerprints.append(fingerprint)
                    valid_entities.append(entity_id)

        if len(fingerprints) < self.config["cluster_min_size"]:
            return []

        # Normalize fingerprints
        fingerprints_array = np.array(fingerprints)

        try:
            fingerprints_normalized = self.scaler.fit_transform(fingerprints_array)
        except Exception as e:
            logger.error(f"Error normalizing fingerprints: {e}")
            return []

        # Perform DBSCAN clustering
        clustering = DBSCAN(
            eps=self.config["cluster_eps"], min_samples=self.config["cluster_min_size"]
        )
        cluster_labels = clustering.fit_predict(fingerprints_normalized)

        # Extract clusters
        clusters = []
        unique_labels = set(cluster_labels)

        for label in unique_labels:
            if label == -1:  # Noise points
                continue

            cluster_indices = [i for i, l in enumerate(cluster_labels) if l == label]
            cluster_entities = [valid_entities[i] for i in cluster_indices]

            if len(cluster_entities) >= self.config["cluster_min_size"]:
                # Calculate cluster metrics
                cluster_fingerprints = fingerprints_normalized[cluster_indices]
                avg_similarity = self._calculate_cluster_similarity(
                    cluster_fingerprints
                )

                # Calculate coordination indicators
                indicators = self._analyze_cluster_coordination(cluster_entities)

                cluster = CoordinatedBehaviorCluster(
                    cluster_id=f"behavioral_{uuid.uuid4()}",
                    entity_ids=cluster_entities,
                    cluster_type="behavioral_similarity",
                    avg_similarity=avg_similarity,
                    coordination_indicators=indicators,
                    confidence=min(1.0, avg_similarity * 1.2),
                )

                clusters.append(cluster)

        return clusters

    def _detect_temporal_coordination(
        self, entity_ids: List[str], window_hours: int
    ) -> List[CoordinatedBehaviorCluster]:
        """Detect temporal coordination patterns."""

        # Get recent activities for entities
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        entity_activities = {entity_id: [] for entity_id in entity_ids}

        for activity in self.activity_log:
            if activity["timestamp"] > cutoff_time:
                entity_id = activity["entity_id"]
                if entity_id in entity_activities:
                    entity_activities[entity_id].append(activity["timestamp"])

        # Filter entities with sufficient activity
        active_entities = {
            entity_id: activities
            for entity_id, activities in entity_activities.items()
            if len(activities) >= 5
        }

        if len(active_entities) < self.config["cluster_min_size"]:
            return []

        clusters = []

        # Analyze pairwise temporal correlations
        entity_list = list(active_entities.keys())
        correlation_matrix = np.zeros((len(entity_list), len(entity_list)))

        for i, entity1 in enumerate(entity_list):
            for j, entity2 in enumerate(entity_list[i + 1 :], i + 1):
                activities1 = active_entities[entity1]
                activities2 = active_entities[entity2]

                correlation = self._calculate_temporal_correlation(
                    activities1, activities2
                )
                correlation_matrix[i][j] = correlation
                correlation_matrix[j][i] = correlation

        # Find highly correlated groups
        threshold = self.config["temporal_correlation_threshold"]
        for i, entity1 in enumerate(entity_list):
            coordinated_entities = [entity1]

            for j, entity2 in enumerate(entity_list):
                if i != j and correlation_matrix[i][j] > threshold:
                    coordinated_entities.append(entity2)

            if len(coordinated_entities) >= self.config["cluster_min_size"]:
                # Calculate average correlation
                cluster_indices = [entity_list.index(e) for e in coordinated_entities]
                cluster_correlations = []

                for idx1 in cluster_indices:
                    for idx2 in cluster_indices[idx1 + 1 :]:
                        cluster_correlations.append(correlation_matrix[idx1][idx2])

                avg_correlation = (
                    np.mean(cluster_correlations) if cluster_correlations else 0.0
                )

                cluster = CoordinatedBehaviorCluster(
                    cluster_id=f"temporal_{uuid.uuid4()}",
                    entity_ids=coordinated_entities,
                    cluster_type="temporal_coordination",
                    temporal_correlation=avg_correlation,
                    coordination_indicators=["synchronized_activity_timing"],
                    confidence=avg_correlation,
                )

                clusters.append(cluster)
                break  # Avoid overlapping clusters

        return clusters

    def _detect_network_coordination(
        self, entity_ids: List[str]
    ) -> List[CoordinatedBehaviorCluster]:
        """Detect coordination through network topology analysis."""

        if not NETWORKX_AVAILABLE or self.interaction_graph is None:
            return []

        clusters = []

        # Find densely connected subgraphs
        entity_subgraph = self.interaction_graph.subgraph(entity_ids)

        if entity_subgraph.number_of_nodes() < self.config["cluster_min_size"]:
            return []

        # Detect communities using various algorithms
        try:
            # Simple approach: find cliques
            cliques = list(nx.find_cliques(entity_subgraph))

            for clique in cliques:
                if len(clique) >= self.config["cluster_min_size"]:
                    # Calculate network density
                    clique_subgraph = entity_subgraph.subgraph(clique)
                    density = nx.density(clique_subgraph)

                    if density > 0.7:  # High connectivity
                        cluster = CoordinatedBehaviorCluster(
                            cluster_id=f"network_{uuid.uuid4()}",
                            entity_ids=list(clique),
                            cluster_type="network_coordination",
                            coordination_indicators=["dense_interaction_network"],
                            confidence=density,
                        )
                        clusters.append(cluster)

        except Exception as e:
            logger.error(f"Network coordination detection error: {e}")

        return clusters

    def _detect_anomaly_clusters(
        self, entity_ids: List[str]
    ) -> List[CoordinatedBehaviorCluster]:
        """Detect clusters of entities with similar anomalous behavior."""

        anomalous_entities = {}

        # Identify entities with anomalies
        for entity_id in entity_ids:
            if entity_id in self.behavioral_profiles:
                profile = self.behavioral_profiles[entity_id]
                anomalies = profile.detect_anomalies()

                if anomalies:
                    anomalous_entities[entity_id] = set(anomalies)
                    self.metrics["anomalies_detected"] += len(anomalies)

        if len(anomalous_entities) < self.config["cluster_min_size"]:
            return []

        clusters = []

        # Group entities by shared anomalies
        anomaly_groups = defaultdict(list)

        for entity_id, anomalies in anomalous_entities.items():
            # Use frozenset for hashable key
            anomaly_key = frozenset(anomalies)
            anomaly_groups[anomaly_key].append(entity_id)

        # Create clusters for groups with sufficient size
        for anomaly_set, entities in anomaly_groups.items():
            if len(entities) >= self.config["cluster_min_size"]:
                cluster = CoordinatedBehaviorCluster(
                    cluster_id=f"anomaly_{uuid.uuid4()}",
                    entity_ids=entities,
                    cluster_type="anomaly_coordination",
                    coordination_indicators=list(anomaly_set),
                    confidence=min(1.0, len(anomaly_set) * 0.3),
                )
                clusters.append(cluster)

        return clusters

    def _perform_clustering_analysis(self):
        """Perform periodic clustering analysis of all profiles."""

        # Get active entities
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        active_entities = [
            entity_id
            for entity_id, profile in self.behavioral_profiles.items()
            if profile.last_activity > cutoff_time and profile.total_actions >= 10
        ]

        if len(active_entities) >= self.config["cluster_min_size"]:
            clusters = self.detect_coordinated_behavior(active_entities)
            logger.info(
                f"Periodic clustering analysis detected {len(clusters)} clusters"
            )

    def _update_profile_features(self, profile: BehavioralProfile):
        """Update derived features for a behavioral profile."""

        # Calculate vocabulary diversity
        if hasattr(profile, "vocabulary_usage"):
            total_words = sum(profile.vocabulary_usage.values())
            unique_words = len(profile.vocabulary_usage)
            profile.vocabulary_diversity = unique_words / max(1, total_words)

        # Update linguistic features
        if profile.content_length_patterns:
            profile.linguistic_features.update(
                {
                    "avg_content_length": np.mean(profile.content_length_patterns),
                    "content_length_variance": np.var(profile.content_length_patterns),
                }
            )

    def _calculate_cluster_similarity(self, fingerprints: np.ndarray) -> float:
        """Calculate average pairwise similarity within cluster."""

        if len(fingerprints) < 2:
            return 0.0

        similarities = []
        for i in range(len(fingerprints)):
            for j in range(i + 1, len(fingerprints)):
                # Cosine similarity
                dot_product = np.dot(fingerprints[i], fingerprints[j])
                norm1 = np.linalg.norm(fingerprints[i])
                norm2 = np.linalg.norm(fingerprints[j])

                if norm1 > 0 and norm2 > 0:
                    similarity = dot_product / (norm1 * norm2)
                    similarities.append(similarity)

        return np.mean(similarities) if similarities else 0.0

    def _analyze_cluster_coordination(self, entity_ids: List[str]) -> List[str]:
        """Analyze coordination indicators for a cluster."""

        indicators = []
        profiles = [
            self.behavioral_profiles[eid]
            for eid in entity_ids
            if eid in self.behavioral_profiles
        ]

        if len(profiles) < 2:
            return indicators

        # Check temporal alignment
        activity_overlaps = []
        for i, profile1 in enumerate(profiles):
            for j, profile2 in enumerate(profiles[i + 1 :], i + 1):
                overlap = self._calculate_activity_overlap(profile1, profile2)
                activity_overlaps.append(overlap)

        if activity_overlaps and np.mean(activity_overlaps) > 0.8:
            indicators.append("temporal_alignment")

        # Check behavioral similarity
        similarities = []
        for i, profile1 in enumerate(profiles):
            for j, profile2 in enumerate(profiles[i + 1 :], i + 1):
                similarity = profile1.calculate_similarity_to(profile2)
                similarities.append(similarity)

        if similarities and np.mean(similarities) > self.config["similarity_threshold"]:
            indicators.append("high_behavioral_similarity")

        # Check for shared anomalies
        all_anomalies = [profile.detect_anomalies() for profile in profiles]
        common_anomalies = set(all_anomalies[0]) if all_anomalies else set()

        for anomalies in all_anomalies[1:]:
            common_anomalies = common_anomalies.intersection(set(anomalies))

        if common_anomalies:
            indicators.append("shared_anomalous_patterns")

        return indicators

    def _calculate_temporal_correlation(
        self, activities1: List[datetime], activities2: List[datetime]
    ) -> float:
        """Calculate temporal correlation between two activity streams."""

        if len(activities1) < 3 or len(activities2) < 3:
            return 0.0

        # Convert to hourly bins
        def to_hourly_bins(activities: List[datetime]) -> np.ndarray:
            if not activities:
                return np.array([])

            start_time = min(min(activities1), min(activities2))
            end_time = max(max(activities1), max(activities2))

            hours = int((end_time - start_time).total_seconds() // 3600) + 1
            bins = np.zeros(hours)

            for activity in activities:
                hour_index = int((activity - start_time).total_seconds() // 3600)
                if 0 <= hour_index < hours:
                    bins[hour_index] += 1

            return bins

        bins1 = to_hourly_bins(activities1)
        bins2 = to_hourly_bins(activities2)

        if len(bins1) == 0 or len(bins2) == 0 or len(bins1) != len(bins2):
            return 0.0

        # Calculate Pearson correlation
        try:
            correlation, _ = stats.pearsonr(bins1, bins2)
            return max(0.0, correlation)  # Only positive correlations
        except Exception:
            return 0.0

    def _calculate_activity_overlap(
        self, profile1: BehavioralProfile, profile2: BehavioralProfile
    ) -> float:
        """Calculate activity time overlap between two profiles."""

        # Compare hourly activity patterns
        hours1 = set(profile1.activity_hours.keys())
        hours2 = set(profile2.activity_hours.keys())

        if not hours1 or not hours2:
            return 0.0

        overlap = len(hours1.intersection(hours2))
        union = len(hours1.union(hours2))

        return overlap / union if union > 0 else 0.0

    def get_entity_risk_assessment(self, entity_id: str) -> Dict[str, Any]:
        """Get comprehensive risk assessment for an entity."""

        if entity_id not in self.behavioral_profiles:
            return {"error": "Entity not found", "entity_id": entity_id}

        profile = self.behavioral_profiles[entity_id]

        # Calculate risk factors
        risk_factors = {}

        # Anomaly risk
        anomalies = profile.detect_anomalies()
        risk_factors["anomaly_risk"] = len(anomalies) * 0.2

        # Behavioral uniqueness risk (very unique or very common patterns)
        fingerprint = profile.calculate_behavioral_fingerprint()
        if len(fingerprint) > 0:
            # Compare with other profiles
            similarities = []
            for other_id, other_profile in self.behavioral_profiles.items():
                if other_id != entity_id:
                    similarity = profile.calculate_similarity_to(other_profile)
                    similarities.append(similarity)

            if similarities:
                max_similarity = max(similarities)
                if max_similarity > 0.9:  # Very similar to others
                    risk_factors["similarity_risk"] = 0.8
                elif max_similarity < 0.1:  # Very unique
                    risk_factors["uniqueness_risk"] = 0.3

        # Cluster membership risk
        cluster_memberships = [
            cluster
            for cluster in self.detected_clusters.values()
            if entity_id in cluster.entity_ids
        ]
        risk_factors["cluster_risk"] = min(1.0, len(cluster_memberships) * 0.4)

        # Calculate overall risk score
        overall_risk = min(1.0, sum(risk_factors.values()))

        return {
            "entity_id": entity_id,
            "overall_risk_score": overall_risk,
            "risk_factors": risk_factors,
            "anomalies_detected": anomalies,
            "cluster_memberships": len(cluster_memberships),
            "total_activities": profile.total_actions,
            "profile_age_days": (
                datetime.now(timezone.utc) - profile.first_activity
            ).days,
            "last_activity": profile.last_activity.isoformat(),
        }

    def get_analyzer_statistics(self) -> Dict[str, Any]:
        """Get comprehensive analyzer statistics."""

        # Profile statistics
        profile_stats = {
            "total_profiles": len(self.behavioral_profiles),
            "active_profiles_24h": len(
                [
                    p
                    for p in self.behavioral_profiles.values()
                    if p.last_activity
                    > datetime.now(timezone.utc) - timedelta(hours=24)
                ]
            ),
            "profile_types": defaultdict(int),
        }

        for profile in self.behavioral_profiles.values():
            profile_stats["profile_types"][profile.entity_type] += 1

        # Cluster statistics
        cluster_stats = {
            "total_clusters": len(self.detected_clusters),
            "cluster_types": defaultdict(int),
            "avg_cluster_size": 0,
            "largest_cluster": 0,
        }

        if self.detected_clusters:
            cluster_sizes = []
            for cluster in self.detected_clusters.values():
                cluster_stats["cluster_types"][cluster.cluster_type] += 1
                cluster_size = len(cluster.entity_ids)
                cluster_sizes.append(cluster_size)

            cluster_stats["avg_cluster_size"] = np.mean(cluster_sizes)
            cluster_stats["largest_cluster"] = max(cluster_sizes)

        # Network statistics
        network_stats = {}
        if NETWORKX_AVAILABLE and self.interaction_graph is not None:
            network_stats = {
                "nodes": self.interaction_graph.number_of_nodes(),
                "edges": self.interaction_graph.number_of_edges(),
                "density": nx.density(self.interaction_graph),
                "connected_components": nx.number_connected_components(
                    self.interaction_graph
                ),
            }

        return {
            "performance_metrics": self.metrics.copy(),
            "configuration": self.config.copy(),
            "profile_statistics": dict(profile_stats),
            "cluster_statistics": dict(cluster_stats),
            "network_statistics": network_stats,
            "activity_log_size": len(self.activity_log),
        }

    def cleanup_old_data(self, max_age_days: int = None):
        """Clean up old behavioral data."""

        max_age_days = max_age_days or self.config["max_profile_age_days"]
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=max_age_days)

        # Remove old profiles
        old_profiles = [
            entity_id
            for entity_id, profile in self.behavioral_profiles.items()
            if profile.last_activity < cutoff_time
        ]

        for entity_id in old_profiles:
            del self.behavioral_profiles[entity_id]

        # Clean up old clusters
        old_clusters = [
            cluster_id
            for cluster_id, cluster in self.detected_clusters.items()
            if cluster.detection_timestamp < cutoff_time
        ]

        for cluster_id in old_clusters:
            del self.detected_clusters[cluster_id]

        logger.info(
            f"Cleaned up {len(old_profiles)} old profiles and {len(old_clusters)} old clusters"
        )


# Global behavioral analyzer instance
behavioral_analyzer = BehavioralAnalyzer()
