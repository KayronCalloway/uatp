"""
Advanced Attribution Gaming Detection System for UATP Security.

This module implements sophisticated detection algorithms for various types
of attribution gaming attacks, including coordinated manipulation, Sybil
attacks, and systematic attribution fraud.

SECURITY FEATURES:
- Multi-vector attack detection
- Behavioral pattern analysis
- Network topology analysis
- Statistical anomaly detection
- Machine learning-based classification
"""

import hashlib
import logging
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Set

import numpy as np

try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class GamingAttackType(str, Enum):
    """Types of attribution gaming attacks."""

    SYBIL_ATTACK = "sybil_attack"
    COORDINATED_GAMING = "coordinated_gaming"
    ATTRIBUTION_FARMING = "attribution_farming"
    CIRCULAR_ATTRIBUTION = "circular_attribution"
    SIMILARITY_MANIPULATION = "similarity_manipulation"
    CONFIDENCE_INFLATION = "confidence_inflation"
    TEMPORAL_GAMING = "temporal_gaming"
    CROSS_PLATFORM_GAMING = "cross_platform_gaming"
    IDENTITY_SPOOFING = "identity_spoofing"
    QUALITY_GAMING = "quality_gaming"


class AttackSeverity(str, Enum):
    """Severity levels for gaming attacks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GamingDetectionResult:
    """Result of gaming detection analysis."""

    detection_id: str
    attack_detected: bool
    attack_types: List[GamingAttackType] = field(default_factory=list)
    severity: AttackSeverity = AttackSeverity.LOW
    confidence: float = 0.0

    # Evidence and indicators
    evidence: Dict[str, Any] = field(default_factory=dict)
    indicators: List[str] = field(default_factory=list)
    suspicious_entities: List[str] = field(default_factory=list)

    # Recommended actions
    recommended_actions: List[str] = field(default_factory=list)
    block_entities: List[str] = field(default_factory=list)
    flag_attributions: List[str] = field(default_factory=list)

    # Metadata
    detection_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    detection_method: str = "multi_vector_analysis"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "detection_id": self.detection_id,
            "attack_detected": self.attack_detected,
            "attack_types": [t.value for t in self.attack_types],
            "severity": self.severity.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "indicators": self.indicators,
            "suspicious_entities": self.suspicious_entities,
            "recommended_actions": self.recommended_actions,
            "block_entities": self.block_entities,
            "flag_attributions": self.flag_attributions,
            "detection_timestamp": self.detection_timestamp.isoformat(),
            "detection_method": self.detection_method,
        }


@dataclass
class EntityProfile:
    """Profile of an entity for gaming detection."""

    entity_id: str
    entity_type: str  # user, ai_model, organization

    # Behavioral metrics
    attribution_frequency: float = 0.0
    average_similarity_scores: float = 0.0
    confidence_score_patterns: List[float] = field(default_factory=list)
    temporal_patterns: Dict[str, int] = field(default_factory=dict)

    # Network metrics
    connected_entities: Set[str] = field(default_factory=set)
    clustering_coefficient: float = 0.0
    betweenness_centrality: float = 0.0

    # Anomaly indicators
    anomaly_score: float = 0.0
    suspicious_behaviors: List[str] = field(default_factory=list)

    # Metadata
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_attributions: int = 0

    def calculate_risk_score(self) -> float:
        """Calculate overall risk score for this entity."""

        risk_factors = []

        # High attribution frequency risk
        if self.attribution_frequency > 100:  # More than 100 attributions per day
            risk_factors.append(0.3)

        # Suspicious confidence patterns
        if self.confidence_score_patterns:
            conf_std = np.std(self.confidence_score_patterns)
            if conf_std < 0.05:  # Very uniform confidence scores
                risk_factors.append(0.25)

        # Network centrality risk
        if self.betweenness_centrality > 0.8:  # Highly central node
            risk_factors.append(0.2)

        # Anomaly score
        risk_factors.append(self.anomaly_score * 0.3)

        # Temporal clustering
        if self.temporal_patterns:
            max_hourly_activity = max(self.temporal_patterns.values())
            if max_hourly_activity > 50:  # Burst activity
                risk_factors.append(0.2)

        return min(1.0, sum(risk_factors))


class AttributionGamingDetector:
    """Advanced attribution gaming detection system."""

    def __init__(self):
        # Entity tracking
        self.entity_profiles: Dict[str, EntityProfile] = {}
        self.attribution_graph = nx.DiGraph() if NETWORKX_AVAILABLE else None

        # Attack pattern database
        self.known_attack_patterns = {
            GamingAttackType.SYBIL_ATTACK: {
                "indicators": [
                    "multiple_similar_entities",
                    "rapid_account_creation",
                    "coordinated_behavior",
                ],
                "threshold": 0.7,
                "detection_methods": [
                    "entity_similarity_analysis",
                    "temporal_correlation",
                    "network_topology",
                ],
            },
            GamingAttackType.COORDINATED_GAMING: {
                "indicators": [
                    "synchronized_timing",
                    "similar_content_patterns",
                    "cross_entity_correlation",
                ],
                "threshold": 0.75,
                "detection_methods": [
                    "temporal_analysis",
                    "content_similarity",
                    "behavioral_clustering",
                ],
            },
            GamingAttackType.ATTRIBUTION_FARMING: {
                "indicators": [
                    "high_volume_low_quality",
                    "threshold_targeting",
                    "artificial_attribution",
                ],
                "threshold": 0.6,
                "detection_methods": [
                    "volume_analysis",
                    "quality_assessment",
                    "economic_pattern_analysis",
                ],
            },
            GamingAttackType.CIRCULAR_ATTRIBUTION: {
                "indicators": [
                    "reciprocal_attributions",
                    "closed_loops",
                    "mutual_boosting",
                ],
                "threshold": 0.8,
                "detection_methods": [
                    "graph_cycle_detection",
                    "reciprocity_analysis",
                    "community_detection",
                ],
            },
        }

        # Detection configuration
        self.detection_config = {
            "min_detection_confidence": 0.7,
            "entity_similarity_threshold": 0.85,
            "temporal_correlation_threshold": 0.8,
            "attribution_volume_threshold": 50,  # per day
            "network_density_threshold": 0.9,
            "anomaly_detection_sensitivity": 2.5,
            "behavioral_clustering_eps": 0.3,
            "min_samples_for_cluster": 3,
        }

        # Historical data for pattern learning
        self.attribution_history = deque(maxlen=10000)
        self.temporal_windows = defaultdict(list)  # hour -> attributions
        self.known_gaming_signatures = set()

        # Performance metrics
        self.metrics = {
            "total_detections": 0,
            "attacks_detected": 0,
            "false_positives": 0,
            "entities_flagged": 0,
            "attributions_blocked": 0,
            "gaming_rings_discovered": 0,
        }

        # Machine learning models (placeholder for future ML integration)
        self.ml_models = {}

        logger.info("Attribution Gaming Detector initialized")

    def analyze_attribution_for_gaming(
        self, attribution_data: Dict[str, Any], context: Dict[str, Any] = None
    ) -> GamingDetectionResult:
        """
        Comprehensive analysis of attribution for gaming patterns.
        """
        self.metrics["total_detections"] += 1
        detection_id = f"gaming_det_{uuid.uuid4()}"

        context = context or {}

        # Extract entities involved
        entities = self._extract_entities(attribution_data, context)

        # Update entity profiles
        for entity_id, entity_type in entities.items():
            self._update_entity_profile(
                entity_id, entity_type, attribution_data, context
            )

        # Run multiple detection methods
        detection_results = []

        # 1. Sybil attack detection
        sybil_result = self._detect_sybil_attack(entities, attribution_data, context)
        if sybil_result["detected"]:
            detection_results.append(sybil_result)

        # 2. Coordinated gaming detection
        coordinated_result = self._detect_coordinated_gaming(
            entities, attribution_data, context
        )
        if coordinated_result["detected"]:
            detection_results.append(coordinated_result)

        # 3. Attribution farming detection
        farming_result = self._detect_attribution_farming(
            entities, attribution_data, context
        )
        if farming_result["detected"]:
            detection_results.append(farming_result)

        # 4. Circular attribution detection
        circular_result = self._detect_circular_attribution(
            entities, attribution_data, context
        )
        if circular_result["detected"]:
            detection_results.append(circular_result)

        # 5. Similarity manipulation detection
        similarity_result = self._detect_similarity_manipulation(
            attribution_data, context
        )
        if similarity_result["detected"]:
            detection_results.append(similarity_result)

        # 6. Confidence inflation detection
        confidence_result = self._detect_confidence_inflation(attribution_data, context)
        if confidence_result["detected"]:
            detection_results.append(confidence_result)

        # 7. Temporal gaming detection
        temporal_result = self._detect_temporal_gaming(
            entities, attribution_data, context
        )
        if temporal_result["detected"]:
            detection_results.append(temporal_result)

        # Aggregate results
        aggregated_result = self._aggregate_detection_results(
            detection_id, detection_results, entities, attribution_data
        )

        # Store attribution history
        self._store_attribution_history(attribution_data, context, aggregated_result)

        # Emit security events if attacks detected
        if aggregated_result.attack_detected:
            self.metrics["attacks_detected"] += 1
            audit_emitter.emit_security_event(
                "attribution_gaming_attack_detected",
                {
                    "detection_id": detection_id,
                    "attack_types": [t.value for t in aggregated_result.attack_types],
                    "severity": aggregated_result.severity.value,
                    "entities_involved": list(entities.keys()),
                    "confidence": aggregated_result.confidence,
                },
            )

        return aggregated_result

    def _extract_entities(
        self, attribution_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Extract entities involved in attribution."""

        entities = {}

        # Extract from attribution data
        if "source_ai_id" in attribution_data:
            entities[attribution_data["source_ai_id"]] = "ai_model"
        if "target_ai_id" in attribution_data:
            entities[attribution_data["target_ai_id"]] = "ai_model"
        if "user_id" in attribution_data:
            entities[attribution_data["user_id"]] = "user"

        # Extract from context
        if "source_conversation_id" in attribution_data:
            entities[attribution_data["source_conversation_id"]] = "conversation"
        if "target_conversation_id" in attribution_data:
            entities[attribution_data["target_conversation_id"]] = "conversation"

        return entities

    def _update_entity_profile(
        self,
        entity_id: str,
        entity_type: str,
        attribution_data: Dict[str, Any],
        context: Dict[str, Any],
    ):
        """Update entity profile with new attribution data."""

        if entity_id not in self.entity_profiles:
            self.entity_profiles[entity_id] = EntityProfile(
                entity_id=entity_id, entity_type=entity_type
            )

        profile = self.entity_profiles[entity_id]
        profile.last_activity = datetime.now(timezone.utc)
        profile.total_attributions += 1

        # Update confidence patterns
        if "confidence_score" in attribution_data:
            profile.confidence_score_patterns.append(
                attribution_data["confidence_score"]
            )
            # Keep only recent patterns
            if len(profile.confidence_score_patterns) > 100:
                profile.confidence_score_patterns = profile.confidence_score_patterns[
                    -50:
                ]

        # Update similarity scores
        if "similarity_score" in attribution_data:
            current_avg = profile.average_similarity_scores
            profile.average_similarity_scores = (
                current_avg * (profile.total_attributions - 1)
                + attribution_data["similarity_score"]
            ) / profile.total_attributions

        # Update temporal patterns
        current_hour = datetime.now(timezone.utc).hour
        profile.temporal_patterns[str(current_hour)] = (
            profile.temporal_patterns.get(str(current_hour), 0) + 1
        )

        # Update network connections
        for other_entity in self._extract_entities(attribution_data, context):
            if other_entity != entity_id:
                profile.connected_entities.add(other_entity)

        # Calculate attribution frequency (attributions per day)
        days_active = max(1, (profile.last_activity - profile.first_seen).days)
        profile.attribution_frequency = profile.total_attributions / days_active

        # Update network graph
        if NETWORKX_AVAILABLE and self.attribution_graph is not None:
            self.attribution_graph.add_node(entity_id, entity_type=entity_type)

            # Add edges to other entities
            for other_entity in self._extract_entities(attribution_data, context):
                if other_entity != entity_id:
                    self.attribution_graph.add_edge(entity_id, other_entity)

    def _detect_sybil_attack(
        self,
        entities: Dict[str, str],
        attribution_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Detect Sybil attack patterns."""

        detected = False
        confidence = 0.0
        indicators = []
        evidence = {}

        # Check for similar entity creation patterns
        user_entities = [eid for eid, etype in entities.items() if etype == "user"]

        if len(user_entities) >= 2:
            # Check creation time proximity
            creation_times = []
            for user_id in user_entities:
                if user_id in self.entity_profiles:
                    creation_times.append(self.entity_profiles[user_id].first_seen)

            if len(creation_times) >= 2:
                time_diffs = []
                for i in range(len(creation_times)):
                    for j in range(i + 1, len(creation_times)):
                        diff = abs(
                            (creation_times[i] - creation_times[j]).total_seconds()
                        )
                        time_diffs.append(diff)

                min_time_diff = min(time_diffs) if time_diffs else float("inf")
                if min_time_diff < 3600:  # Created within 1 hour
                    indicators.append("rapid_account_creation")
                    confidence += 0.3

            # Check for behavioral similarity
            if self._check_behavioral_similarity(user_entities):
                indicators.append("similar_behavioral_patterns")
                confidence += 0.4

        # Check for coordinated attribution patterns
        if self._check_coordinated_patterns(entities, attribution_data):
            indicators.append("coordinated_attribution_patterns")
            confidence += 0.3

        detected = (
            confidence
            >= self.known_attack_patterns[GamingAttackType.SYBIL_ATTACK]["threshold"]
        )

        return {
            "attack_type": GamingAttackType.SYBIL_ATTACK,
            "detected": detected,
            "confidence": confidence,
            "indicators": indicators,
            "evidence": evidence,
        }

    def _detect_coordinated_gaming(
        self,
        entities: Dict[str, str],
        attribution_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Detect coordinated gaming patterns."""

        detected = False
        confidence = 0.0
        indicators = []
        evidence = {}

        # Check temporal synchronization
        if self._check_temporal_synchronization(entities):
            indicators.append("synchronized_timing")
            confidence += 0.4

        # Check content similarity patterns
        if self._check_suspicious_content_similarity(attribution_data, context):
            indicators.append("suspicious_content_patterns")
            confidence += 0.3

        # Check attribution reciprocity
        if self._check_attribution_reciprocity(entities):
            indicators.append("attribution_reciprocity")
            confidence += 0.3

        detected = (
            confidence
            >= self.known_attack_patterns[GamingAttackType.COORDINATED_GAMING][
                "threshold"
            ]
        )

        return {
            "attack_type": GamingAttackType.COORDINATED_GAMING,
            "detected": detected,
            "confidence": confidence,
            "indicators": indicators,
            "evidence": evidence,
        }

    def _detect_attribution_farming(
        self,
        entities: Dict[str, str],
        attribution_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Detect attribution farming patterns."""

        detected = False
        confidence = 0.0
        indicators = []
        evidence = {}

        # Check for high volume, low quality attributions
        for entity_id in entities:
            if entity_id in self.entity_profiles:
                profile = self.entity_profiles[entity_id]

                # High attribution frequency
                if (
                    profile.attribution_frequency
                    > self.detection_config["attribution_volume_threshold"]
                ):
                    indicators.append("high_attribution_volume")
                    confidence += 0.3

                # Low average similarity scores (poor quality)
                if profile.average_similarity_scores < 0.3:
                    indicators.append("low_quality_attributions")
                    confidence += 0.2

                # Threshold targeting behavior
                if self._check_threshold_targeting(profile.confidence_score_patterns):
                    indicators.append("threshold_targeting")
                    confidence += 0.3

        detected = (
            confidence
            >= self.known_attack_patterns[GamingAttackType.ATTRIBUTION_FARMING][
                "threshold"
            ]
        )

        return {
            "attack_type": GamingAttackType.ATTRIBUTION_FARMING,
            "detected": detected,
            "confidence": confidence,
            "indicators": indicators,
            "evidence": evidence,
        }

    def _detect_circular_attribution(
        self,
        entities: Dict[str, str],
        attribution_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Detect circular attribution patterns."""

        detected = False
        confidence = 0.0
        indicators = []
        evidence = {}

        if NETWORKX_AVAILABLE and self.attribution_graph is not None:
            # Detect cycles in attribution graph
            try:
                cycles = list(nx.simple_cycles(self.attribution_graph))
                if cycles:
                    # Check if current entities are part of any cycle
                    entity_set = set(entities.keys())
                    for cycle in cycles:
                        cycle_set = set(cycle)
                        if entity_set.intersection(cycle_set):
                            indicators.append("attribution_cycle_detected")
                            confidence += 0.5
                            evidence["cycles"] = cycles[:5]  # Store first 5 cycles
                            break
            except Exception:
                pass  # Graph analysis failed

            # Check reciprocal attributions
            reciprocal_pairs = 0
            for entity1 in entities:
                for entity2 in entities:
                    if (
                        entity1 != entity2
                        and self.attribution_graph.has_edge(entity1, entity2)
                        and self.attribution_graph.has_edge(entity2, entity1)
                    ):
                        reciprocal_pairs += 1

            if reciprocal_pairs > 0:
                indicators.append("reciprocal_attributions")
                confidence += 0.3
                evidence["reciprocal_pairs"] = reciprocal_pairs

        detected = (
            confidence
            >= self.known_attack_patterns[GamingAttackType.CIRCULAR_ATTRIBUTION][
                "threshold"
            ]
        )

        return {
            "attack_type": GamingAttackType.CIRCULAR_ATTRIBUTION,
            "detected": detected,
            "confidence": confidence,
            "indicators": indicators,
            "evidence": evidence,
        }

    def _detect_similarity_manipulation(
        self, attribution_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect similarity score manipulation."""

        detected = False
        confidence = 0.0
        indicators = []
        evidence = {}

        # Check method score consistency
        method_scores = attribution_data.get("method_scores", {})
        if len(method_scores) >= 3:
            scores = list(method_scores.values())
            score_std = np.std(scores)

            # Suspicious uniformity
            if score_std < 0.01:
                indicators.append("artificial_score_uniformity")
                confidence += 0.3

            # Suspicious outliers
            mean_score = np.mean(scores)
            outliers = [s for s in scores if abs(s - mean_score) > 0.4]
            if len(outliers) > len(scores) * 0.3:
                indicators.append("similarity_score_outliers")
                confidence += 0.25

            evidence["method_scores"] = method_scores
            evidence["score_statistics"] = {
                "mean": float(mean_score),
                "std": float(score_std),
                "outliers": len(outliers),
            }

        # Check for gaming signatures in similarity calculation
        if self._check_similarity_gaming_signatures(attribution_data, context):
            indicators.append("known_gaming_signature")
            confidence += 0.4

        detected = confidence >= 0.6  # Custom threshold for similarity manipulation

        return {
            "attack_type": GamingAttackType.SIMILARITY_MANIPULATION,
            "detected": detected,
            "confidence": confidence,
            "indicators": indicators,
            "evidence": evidence,
        }

    def _detect_confidence_inflation(
        self, attribution_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect confidence score inflation."""

        detected = False
        confidence = 0.0
        indicators = []
        evidence = {}

        confidence_score = attribution_data.get("confidence_score", 0.0)
        similarity_score = attribution_data.get("similarity_score", 0.0)

        # Check if confidence is artificially higher than similarity
        if confidence_score > similarity_score + 0.3:
            indicators.append("confidence_exceeds_similarity")
            confidence += 0.4

        # Check for perfect confidence scores (suspicious)
        if confidence_score >= 0.99:
            indicators.append("perfect_confidence_suspicious")
            confidence += 0.3

        # Check historical confidence patterns
        content_hash = context.get("content_hash", "")
        if content_hash:
            historical_confidences = self._get_historical_confidences(content_hash)
            if len(historical_confidences) >= 3:
                mean_historical = np.mean(historical_confidences)
                if confidence_score > mean_historical + 0.4:
                    indicators.append("confidence_spike")
                    confidence += 0.3

        detected = confidence >= 0.6  # Custom threshold for confidence inflation

        return {
            "attack_type": GamingAttackType.CONFIDENCE_INFLATION,
            "detected": detected,
            "confidence": confidence,
            "indicators": indicators,
            "evidence": evidence,
        }

    def _detect_temporal_gaming(
        self,
        entities: Dict[str, str],
        attribution_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Detect temporal gaming patterns."""

        detected = False
        confidence = 0.0
        indicators = []
        evidence = {}

        current_time = datetime.now(timezone.utc)
        current_hour = current_time.hour

        # Check for burst activity
        recent_attributions = 0
        for entity_id in entities:
            if entity_id in self.entity_profiles:
                profile = self.entity_profiles[entity_id]
                recent_attributions += profile.temporal_patterns.get(
                    str(current_hour), 0
                )

        if recent_attributions > 20:  # More than 20 attributions this hour
            indicators.append("burst_activity")
            confidence += 0.3

        # Check for off-hours activity (potential bot behavior)
        if current_time.hour < 6 or current_time.hour > 23:  # Late night/early morning
            total_recent_activity = sum(
                self.entity_profiles[eid].temporal_patterns.get(str(current_hour), 0)
                for eid in entities
                if eid in self.entity_profiles
            )
            if total_recent_activity > 10:
                indicators.append("off_hours_activity")
                confidence += 0.25

        # Check for synchronized timestamps
        if self._check_timestamp_synchronization(entities):
            indicators.append("synchronized_timestamps")
            confidence += 0.4

        detected = confidence >= 0.6  # Custom threshold for temporal gaming

        return {
            "attack_type": GamingAttackType.TEMPORAL_GAMING,
            "detected": detected,
            "confidence": confidence,
            "indicators": indicators,
            "evidence": evidence,
        }

    def _aggregate_detection_results(
        self,
        detection_id: str,
        detection_results: List[Dict[str, Any]],
        entities: Dict[str, str],
        attribution_data: Dict[str, Any],
    ) -> GamingDetectionResult:
        """Aggregate multiple detection results into final result."""

        if not detection_results:
            return GamingDetectionResult(
                detection_id=detection_id, attack_detected=False
            )

        # Collect attack types and indicators
        attack_types = []
        all_indicators = []
        max_confidence = 0.0
        all_evidence = {}

        for result in detection_results:
            attack_types.append(result["attack_type"])
            all_indicators.extend(result["indicators"])
            max_confidence = max(max_confidence, result["confidence"])
            all_evidence[result["attack_type"].value] = result["evidence"]

        # Determine severity
        severity = AttackSeverity.LOW
        if max_confidence >= 0.9:
            severity = AttackSeverity.CRITICAL
        elif max_confidence >= 0.8:
            severity = AttackSeverity.HIGH
        elif max_confidence >= 0.7:
            severity = AttackSeverity.MEDIUM

        # Generate recommendations
        recommended_actions = []
        block_entities = []
        flag_attributions = []

        if severity in [AttackSeverity.HIGH, AttackSeverity.CRITICAL]:
            recommended_actions.append("block_entities")
            recommended_actions.append("investigate_network")
            block_entities.extend(list(entities.keys()))
        elif severity == AttackSeverity.MEDIUM:
            recommended_actions.append("flag_for_review")
            recommended_actions.append("increase_monitoring")
            flag_attributions.append(attribution_data.get("attribution_id", "unknown"))

        # Identify suspicious entities
        suspicious_entities = []
        for entity_id in entities:
            if entity_id in self.entity_profiles:
                risk_score = self.entity_profiles[entity_id].calculate_risk_score()
                if risk_score > 0.7:
                    suspicious_entities.append(entity_id)

        return GamingDetectionResult(
            detection_id=detection_id,
            attack_detected=True,
            attack_types=attack_types,
            severity=severity,
            confidence=max_confidence,
            evidence=all_evidence,
            indicators=list(set(all_indicators)),  # Remove duplicates
            suspicious_entities=suspicious_entities,
            recommended_actions=recommended_actions,
            block_entities=block_entities,
            flag_attributions=flag_attributions,
        )

    def _store_attribution_history(
        self,
        attribution_data: Dict[str, Any],
        context: Dict[str, Any],
        detection_result: GamingDetectionResult,
    ):
        """Store attribution history for pattern learning."""

        history_entry = {
            "timestamp": datetime.now(timezone.utc),
            "attribution_data": attribution_data,
            "context": context,
            "gaming_detected": detection_result.attack_detected,
            "attack_types": [t.value for t in detection_result.attack_types],
            "confidence": detection_result.confidence,
        }

        self.attribution_history.append(history_entry)

        # Update temporal windows
        hour_key = history_entry["timestamp"].strftime("%Y-%m-%d-%H")
        self.temporal_windows[hour_key].append(history_entry)

    # Helper methods for specific detection logic

    def _check_behavioral_similarity(self, user_entities: List[str]) -> bool:
        """Check if entities have suspiciously similar behavior."""

        if len(user_entities) < 2:
            return False

        # Compare behavioral patterns
        behavioral_vectors = []
        for user_id in user_entities:
            if user_id in self.entity_profiles:
                profile = self.entity_profiles[user_id]
                vector = [
                    profile.attribution_frequency,
                    profile.average_similarity_scores,
                    len(profile.confidence_score_patterns),
                    len(profile.connected_entities),
                ]
                behavioral_vectors.append(vector)

        if len(behavioral_vectors) < 2:
            return False

        # Calculate similarity between behavioral vectors
        similarities = []
        for i in range(len(behavioral_vectors)):
            for j in range(i + 1, len(behavioral_vectors)):
                vec1, vec2 = behavioral_vectors[i], behavioral_vectors[j]

                # Cosine similarity
                dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=False))
                magnitude1 = sum(a * a for a in vec1) ** 0.5
                magnitude2 = sum(b * b for b in vec2) ** 0.5

                if magnitude1 > 0 and magnitude2 > 0:
                    similarity = dot_product / (magnitude1 * magnitude2)
                    similarities.append(similarity)

        # Check if any pair is too similar
        return any(
            sim > self.detection_config["entity_similarity_threshold"]
            for sim in similarities
        )

    def _check_coordinated_patterns(
        self, entities: Dict[str, str], attribution_data: Dict[str, Any]
    ) -> bool:
        """Check for coordinated attribution patterns."""

        # Check if entities frequently attribute to each other
        entity_list = list(entities.keys())
        coordinated_count = 0

        for i in range(len(entity_list)):
            for j in range(i + 1, len(entity_list)):
                entity1, entity2 = entity_list[i], entity_list[j]

                if entity1 in self.entity_profiles and entity2 in self.entity_profiles:
                    profile1 = self.entity_profiles[entity1]
                    profile2 = self.entity_profiles[entity2]

                    # Check mutual connections
                    if (
                        entity2 in profile1.connected_entities
                        and entity1 in profile2.connected_entities
                    ):
                        coordinated_count += 1

        # If more than half of entity pairs are mutually connected
        total_pairs = len(entity_list) * (len(entity_list) - 1) // 2
        return total_pairs > 0 and coordinated_count / total_pairs > 0.6

    def _check_temporal_synchronization(self, entities: Dict[str, str]) -> bool:
        """Check for temporal synchronization between entities."""

        current_hour = datetime.now(timezone.utc).hour
        synchronized_entities = 0

        for entity_id in entities:
            if entity_id in self.entity_profiles:
                profile = self.entity_profiles[entity_id]
                current_hour_activity = profile.temporal_patterns.get(
                    str(current_hour), 0
                )

                # Check if this entity is unusually active right now
                avg_hourly_activity = sum(profile.temporal_patterns.values()) / max(
                    1, len(profile.temporal_patterns)
                )
                if current_hour_activity > avg_hourly_activity * 2:
                    synchronized_entities += 1

        # If most entities are synchronized
        return synchronized_entities >= len(entities) * 0.7

    def _check_suspicious_content_similarity(
        self, attribution_data: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """Check for suspicious content similarity patterns."""

        similarity_score = attribution_data.get("similarity_score", 0.0)

        # Very high similarity might indicate content manipulation
        if similarity_score > 0.95:
            return True

        # Check method score consistency
        method_scores = attribution_data.get("method_scores", {})
        if len(method_scores) >= 3:
            scores = list(method_scores.values())
            # All methods giving very similar scores might indicate gaming
            if max(scores) - min(scores) < 0.05 and np.mean(scores) > 0.8:
                return True

        return False

    def _check_attribution_reciprocity(self, entities: Dict[str, str]) -> bool:
        """Check for suspicious attribution reciprocity."""

        if not NETWORKX_AVAILABLE or self.attribution_graph is None:
            return False

        reciprocal_edges = 0
        total_possible_edges = 0

        entity_list = list(entities.keys())
        for i in range(len(entity_list)):
            for j in range(i + 1, len(entity_list)):
                entity1, entity2 = entity_list[i], entity_list[j]
                total_possible_edges += 1

                if self.attribution_graph.has_edge(
                    entity1, entity2
                ) and self.attribution_graph.has_edge(entity2, entity1):
                    reciprocal_edges += 1

        # High reciprocity rate is suspicious
        if total_possible_edges > 0:
            reciprocity_rate = reciprocal_edges / total_possible_edges
            return reciprocity_rate > 0.8

        return False

    def _check_threshold_targeting(self, confidence_scores: List[float]) -> bool:
        """Check if confidence scores target specific thresholds."""

        if len(confidence_scores) < 5:
            return False

        # Common UATP attribution thresholds
        thresholds = [0.2, 0.5, 0.8]

        for threshold in thresholds:
            near_threshold = [s for s in confidence_scores if abs(s - threshold) < 0.05]
            if len(near_threshold) / len(confidence_scores) > 0.4:
                return True

        return False

    def _check_similarity_gaming_signatures(
        self, attribution_data: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """Check for known similarity gaming signatures."""

        # Create signature from attribution data
        signature_components = [
            str(attribution_data.get("similarity_score", 0.0)),
            str(attribution_data.get("confidence_score", 0.0)),
            str(len(attribution_data.get("method_scores", {}))),
            context.get("domain", "unknown"),
        ]

        signature = hashlib.sha256("|".join(signature_components).encode()).hexdigest()

        # Check against known gaming signatures
        return signature in self.known_gaming_signatures

    def _check_timestamp_synchronization(self, entities: Dict[str, str]) -> bool:
        """Check for synchronized timestamp patterns."""

        current_minute = datetime.now(timezone.utc).minute

        # Check if entities are all active in the same minute (bot-like)
        synchronized_count = 0
        for entity_id in entities:
            if entity_id in self.entity_profiles:
                profile = self.entity_profiles[entity_id]
                # Check if last activity was in current minute
                if profile.last_activity.minute == current_minute:
                    synchronized_count += 1

        return synchronized_count >= len(entities) * 0.8

    def _get_historical_confidences(self, content_hash: str) -> List[float]:
        """Get historical confidence scores for content."""

        confidences = []
        for entry in self.attribution_history:
            if entry["context"].get("content_hash") == content_hash:
                if "confidence_score" in entry["attribution_data"]:
                    confidences.append(entry["attribution_data"]["confidence_score"])

        return confidences

    def get_detector_statistics(self) -> Dict[str, Any]:
        """Get comprehensive detector statistics."""

        # Entity statistics
        entity_stats = {
            "total_entities": len(self.entity_profiles),
            "high_risk_entities": len(
                [
                    profile
                    for profile in self.entity_profiles.values()
                    if profile.calculate_risk_score() > 0.7
                ]
            ),
            "entity_types": defaultdict(int),
        }

        for profile in self.entity_profiles.values():
            entity_stats["entity_types"][profile.entity_type] += 1

        # Network statistics
        network_stats = {}
        if NETWORKX_AVAILABLE and self.attribution_graph is not None:
            network_stats = {
                "nodes": self.attribution_graph.number_of_nodes(),
                "edges": self.attribution_graph.number_of_edges(),
                "density": nx.density(self.attribution_graph),
                "connected_components": nx.number_weakly_connected_components(
                    self.attribution_graph
                ),
            }

        return {
            "performance_metrics": self.metrics.copy(),
            "detection_config": self.detection_config.copy(),
            "entity_statistics": dict(entity_stats),
            "network_statistics": network_stats,
            "history_size": len(self.attribution_history),
            "temporal_windows": len(self.temporal_windows),
            "known_signatures": len(self.known_gaming_signatures),
        }

    def add_gaming_signature(self, signature: str, description: str = ""):
        """Add a known gaming signature to the database."""

        self.known_gaming_signatures.add(signature)
        logger.info(f"Added gaming signature: {signature[:16]}... - {description}")

    def update_detection_config(self, config_updates: Dict[str, Any]):
        """Update detection configuration."""

        self.detection_config.update(config_updates)
        logger.info(f"Updated detection configuration: {config_updates}")


# Global gaming detector instance
gaming_detector = AttributionGamingDetector()
