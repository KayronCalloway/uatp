"""
Attribution Confidence Validation Framework for UATP Security.

This module implements cross-validation frameworks for attribution confidence
scores to prevent manipulation and ensure reliable attribution decisions.

SECURITY FEATURES:
- Multi-algorithm cross-validation
- Confidence score manipulation detection
- Statistical outlier analysis
- Gaming attack prevention
- Temporal consistency validation
"""

import logging
import statistics
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceValidationResult:
    """Result of confidence validation analysis."""

    validation_id: str
    original_confidence: float
    validated_confidence: float
    adjustment_factor: float

    # Validation metrics
    cross_validation_scores: Dict[str, float] = field(default_factory=dict)
    consensus_reached: bool = False
    statistical_outlier: bool = False

    # Security flags
    manipulation_detected: bool = False
    gaming_indicators: List[str] = field(default_factory=list)
    security_flags: List[str] = field(default_factory=list)

    # Evidence and reasoning
    validation_evidence: Dict[str, Any] = field(default_factory=dict)
    validation_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "validation_id": self.validation_id,
            "original_confidence": self.original_confidence,
            "validated_confidence": self.validated_confidence,
            "adjustment_factor": self.adjustment_factor,
            "cross_validation_scores": self.cross_validation_scores,
            "consensus_reached": self.consensus_reached,
            "statistical_outlier": self.statistical_outlier,
            "manipulation_detected": self.manipulation_detected,
            "gaming_indicators": self.gaming_indicators,
            "security_flags": self.security_flags,
            "validation_evidence": self.validation_evidence,
            "validation_timestamp": self.validation_timestamp.isoformat(),
        }


@dataclass
class ValidationMethod:
    """Configuration for a validation method."""

    method_name: str
    weight: float
    threshold: float
    enabled: bool = True

    # Method-specific parameters
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Performance tracking
    total_validations: int = 0
    successful_validations: int = 0
    manipulation_detections: int = 0


class ConfidenceValidator:
    """Advanced confidence validation with cross-validation framework."""

    def __init__(self):
        # Validation methods registry
        self.validation_methods = {
            "temporal_consistency": ValidationMethod(
                method_name="temporal_consistency",
                weight=0.25,
                threshold=0.7,
                parameters={"max_deviation": 0.3, "window_hours": 24},
            ),
            "peer_comparison": ValidationMethod(
                method_name="peer_comparison",
                weight=0.20,
                threshold=0.65,
                parameters={"min_peers": 3, "max_deviation": 0.25},
            ),
            "statistical_analysis": ValidationMethod(
                method_name="statistical_analysis",
                weight=0.20,
                threshold=0.6,
                parameters={"outlier_threshold": 2.5, "distribution_test": True},
            ),
            "similarity_coherence": ValidationMethod(
                method_name="similarity_coherence",
                weight=0.15,
                threshold=0.65,
                parameters={"min_coherence": 0.7, "max_variance": 0.2},
            ),
            "contextual_validation": ValidationMethod(
                method_name="contextual_validation",
                weight=0.10,
                threshold=0.6,
                parameters={"domain_consistency": True, "user_pattern": True},
            ),
            "gaming_detection": ValidationMethod(
                method_name="gaming_detection",
                weight=0.10,
                threshold=0.8,
                parameters={"gaming_sensitivity": 0.75, "pattern_analysis": True},
            ),
        }

        # Historical data for validation
        self.confidence_history = defaultdict(
            list
        )  # content_hash -> [confidence_scores]
        self.temporal_patterns = defaultdict(list)  # time_window -> confidence_scores
        self.peer_comparisons = defaultdict(
            list
        )  # similar_content -> confidence_scores

        # Security configuration
        self.security_config = {
            "min_consensus_threshold": 0.7,
            "max_confidence_deviation": 0.3,
            "outlier_detection_sensitivity": 2.0,
            "gaming_detection_threshold": 0.8,
            "temporal_window_hours": 48,
            "min_validation_methods": 4,
            "confidence_manipulation_threshold": 0.4,
        }

        # Performance metrics
        self.metrics = {
            "total_validations": 0,
            "manipulations_detected": 0,
            "outliers_detected": 0,
            "consensus_failures": 0,
            "confidence_adjustments": 0,
            "gaming_attempts_blocked": 0,
        }

        logger.info("Confidence Validator initialized with cross-validation framework")

    def validate_confidence(
        self,
        confidence_score: float,
        similarity_data: Dict[str, Any],
        content_hash: str,
        context: Dict[str, Any] = None,
    ) -> ConfidenceValidationResult:
        """
        Validate confidence score using cross-validation framework.
        """
        self.metrics["total_validations"] += 1
        validation_id = f"conf_val_{uuid.uuid4()}"

        context = context or {}

        # Input validation
        if not 0.0 <= confidence_score <= 1.0:
            return ConfidenceValidationResult(
                validation_id=validation_id,
                original_confidence=confidence_score,
                validated_confidence=0.0,
                adjustment_factor=0.0,
                manipulation_detected=True,
                gaming_indicators=["invalid_confidence_range"],
                security_flags=["input_validation_failed"],
            )

        # Run all validation methods
        validation_scores = {}
        gaming_indicators = []
        security_flags = []

        # Temporal consistency validation
        if self.validation_methods["temporal_consistency"].enabled:
            temporal_result = self._validate_temporal_consistency(
                confidence_score, content_hash, context
            )
            validation_scores["temporal_consistency"] = temporal_result["score"]
            if temporal_result["gaming_detected"]:
                gaming_indicators.extend(temporal_result["indicators"])

        # Peer comparison validation
        if self.validation_methods["peer_comparison"].enabled:
            peer_result = self._validate_peer_comparison(
                confidence_score, similarity_data, context
            )
            validation_scores["peer_comparison"] = peer_result["score"]
            if peer_result["gaming_detected"]:
                gaming_indicators.extend(peer_result["indicators"])

        # Statistical analysis validation
        if self.validation_methods["statistical_analysis"].enabled:
            statistical_result = self._validate_statistical_consistency(
                confidence_score, content_hash, similarity_data
            )
            validation_scores["statistical_analysis"] = statistical_result["score"]
            if statistical_result["outlier_detected"]:
                security_flags.append("statistical_outlier")

        # Similarity coherence validation
        if self.validation_methods["similarity_coherence"].enabled:
            coherence_result = self._validate_similarity_coherence(
                confidence_score, similarity_data
            )
            validation_scores["similarity_coherence"] = coherence_result["score"]
            if coherence_result["gaming_detected"]:
                gaming_indicators.extend(coherence_result["indicators"])

        # Contextual validation
        if self.validation_methods["contextual_validation"].enabled:
            contextual_result = self._validate_contextual_consistency(
                confidence_score, context
            )
            validation_scores["contextual_validation"] = contextual_result["score"]

        # Gaming detection validation
        if self.validation_methods["gaming_detection"].enabled:
            gaming_result = self._validate_gaming_patterns(
                confidence_score, similarity_data, context
            )
            validation_scores["gaming_detection"] = gaming_result["score"]
            if gaming_result["gaming_detected"]:
                gaming_indicators.extend(gaming_result["indicators"])
                self.metrics["gaming_attempts_blocked"] += 1

        # Build consensus from validation results
        consensus_result = self._build_validation_consensus(validation_scores)

        # Determine final validated confidence
        validated_confidence = self._calculate_validated_confidence(
            confidence_score, consensus_result, gaming_indicators
        )

        # Check for manipulation
        manipulation_detected = len(gaming_indicators) > 0
        if manipulation_detected:
            self.metrics["manipulations_detected"] += 1

        # Track confidence adjustment
        adjustment_factor = (
            validated_confidence / confidence_score if confidence_score > 0 else 1.0
        )
        if abs(adjustment_factor - 1.0) > 0.1:
            self.metrics["confidence_adjustments"] += 1

        # Store historical data
        self._store_validation_data(
            content_hash, confidence_score, validated_confidence, context
        )

        # Create validation result
        result = ConfidenceValidationResult(
            validation_id=validation_id,
            original_confidence=confidence_score,
            validated_confidence=validated_confidence,
            adjustment_factor=adjustment_factor,
            cross_validation_scores=validation_scores,
            consensus_reached=consensus_result["consensus_reached"],
            statistical_outlier="statistical_outlier" in security_flags,
            manipulation_detected=manipulation_detected,
            gaming_indicators=gaming_indicators,
            security_flags=security_flags,
            validation_evidence={
                "consensus_result": consensus_result,
                "similarity_data": similarity_data,
                "context": context,
            },
        )

        # Emit security events if needed
        if manipulation_detected:
            audit_emitter.emit_security_event(
                "confidence_manipulation_detected",
                {
                    "validation_id": validation_id,
                    "original_confidence": confidence_score,
                    "gaming_indicators": gaming_indicators,
                    "adjustment_factor": adjustment_factor,
                },
            )

        return result

    def _validate_temporal_consistency(
        self, confidence: float, content_hash: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate temporal consistency of confidence scores."""

        method = self.validation_methods["temporal_consistency"]
        window_hours = method.parameters["max_deviation"]
        max_deviation = method.parameters["max_deviation"]

        # Get recent confidence scores for similar content
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        recent_scores = [
            score
            for score, timestamp in self.confidence_history[content_hash]
            if timestamp > cutoff_time
        ]

        gaming_detected = False
        indicators = []

        if len(recent_scores) >= 3:
            mean_score = statistics.mean(recent_scores)
            deviation = abs(confidence - mean_score)

            # Check for suspicious deviation
            if deviation > max_deviation:
                gaming_detected = True
                indicators.append("temporal_confidence_spike")

            # Check for artificial clustering at thresholds
            threshold_clustering = self._detect_threshold_clustering(
                recent_scores + [confidence]
            )
            if threshold_clustering:
                gaming_detected = True
                indicators.append("threshold_clustering")

            # Calculate temporal consistency score
            consistency_score = max(0.0, 1.0 - (deviation / max_deviation))
        else:
            # Not enough historical data
            consistency_score = 0.5

        method.total_validations += 1
        if not gaming_detected:
            method.successful_validations += 1
        else:
            method.manipulation_detections += 1

        return {
            "score": consistency_score,
            "gaming_detected": gaming_detected,
            "indicators": indicators,
            "evidence": {
                "recent_scores": recent_scores,
                "mean_score": statistics.mean(recent_scores) if recent_scores else None,
                "deviation": deviation if recent_scores else None,
            },
        }

    def _validate_peer_comparison(
        self,
        confidence: float,
        similarity_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate confidence against peer similarities."""

        method = self.validation_methods["peer_comparison"]
        min_peers = method.parameters["min_peers"]
        max_deviation = method.parameters["max_deviation"]

        # Get similarity scores from multiple methods
        method_scores = similarity_data.get("method_scores", {})

        gaming_detected = False
        indicators = []

        if len(method_scores) >= min_peers:
            similarities = list(method_scores.values())
            mean_similarity = statistics.mean(similarities)
            similarity_std = (
                statistics.stdev(similarities) if len(similarities) > 1 else 0.0
            )

            # Expected confidence based on similarity
            expected_confidence = self._calculate_expected_confidence(
                mean_similarity, similarity_std
            )

            deviation = abs(confidence - expected_confidence)

            # Check for manipulation
            if deviation > max_deviation:
                gaming_detected = True
                indicators.append("peer_comparison_deviation")

            # Check for gaming patterns in similarity scores
            if self._detect_similarity_gaming(similarities):
                gaming_detected = True
                indicators.append("similarity_score_gaming")

            peer_score = max(0.0, 1.0 - (deviation / max_deviation))
        else:
            peer_score = 0.5  # Insufficient peer data

        method.total_validations += 1
        if not gaming_detected:
            method.successful_validations += 1
        else:
            method.manipulation_detections += 1

        return {
            "score": peer_score,
            "gaming_detected": gaming_detected,
            "indicators": indicators,
            "evidence": {
                "method_scores": method_scores,
                "expected_confidence": expected_confidence
                if len(method_scores) >= min_peers
                else None,
                "deviation": deviation if len(method_scores) >= min_peers else None,
            },
        }

    def _validate_statistical_consistency(
        self, confidence: float, content_hash: str, similarity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate statistical consistency of confidence score."""

        method = self.validation_methods["statistical_analysis"]
        outlier_threshold = method.parameters["outlier_threshold"]

        # Get historical confidence scores
        historical_scores = [
            score for score, _ in self.confidence_history[content_hash]
        ]

        outlier_detected = False
        statistical_score = 0.5

        if len(historical_scores) >= 5:
            # Add current score
            all_scores = historical_scores + [confidence]

            # Calculate z-score
            mean_score = statistics.mean(historical_scores)
            std_score = statistics.stdev(historical_scores)

            if std_score > 0:
                z_score = abs(confidence - mean_score) / std_score

                if z_score > outlier_threshold:
                    outlier_detected = True

                # Normalize z-score to 0-1 range
                statistical_score = max(0.0, 1.0 - (z_score / outlier_threshold))

            # Additional distribution tests
            if method.parameters.get("distribution_test", False):
                # Shapiro-Wilk test for normality
                try:
                    _, p_value = stats.shapiro(all_scores)
                    if p_value < 0.05:  # Non-normal distribution
                        statistical_score *= 0.8  # Reduce confidence
                except:
                    pass

        method.total_validations += 1
        if not outlier_detected:
            method.successful_validations += 1

        if outlier_detected:
            self.metrics["outliers_detected"] += 1

        return {
            "score": statistical_score,
            "outlier_detected": outlier_detected,
            "evidence": {
                "historical_scores": historical_scores,
                "z_score": z_score
                if len(historical_scores) >= 5 and std_score > 0
                else None,
                "mean_score": statistics.mean(historical_scores)
                if historical_scores
                else None,
                "std_score": statistics.stdev(historical_scores)
                if len(historical_scores) > 1
                else None,
            },
        }

    def _validate_similarity_coherence(
        self, confidence: float, similarity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate coherence between confidence and similarity scores."""

        method = self.validation_methods["similarity_coherence"]
        min_coherence = method.parameters["min_coherence"]
        max_variance = method.parameters["max_variance"]

        method_scores = similarity_data.get("method_scores", {})
        ensemble_stats = similarity_data.get("ensemble_stats", {})

        gaming_detected = False
        indicators = []
        coherence_score = 0.5

        if method_scores and ensemble_stats:
            similarities = list(method_scores.values())
            mean_similarity = ensemble_stats.get("mean", statistics.mean(similarities))
            std_similarity = ensemble_stats.get(
                "std", statistics.stdev(similarities) if len(similarities) > 1 else 0.0
            )

            # Check coherence between confidence and similarity
            expected_confidence_from_similarity = min(
                1.0, mean_similarity * 1.2
            )  # Slight boost
            coherence = 1.0 - abs(confidence - expected_confidence_from_similarity)

            if coherence < min_coherence:
                gaming_detected = True
                indicators.append("confidence_similarity_incoherence")

            # Check for excessive similarity variance (gaming indicator)
            if std_similarity > max_variance:
                gaming_detected = True
                indicators.append("excessive_similarity_variance")

            coherence_score = max(0.0, coherence)

        method.total_validations += 1
        if not gaming_detected:
            method.successful_validations += 1
        else:
            method.manipulation_detections += 1

        return {
            "score": coherence_score,
            "gaming_detected": gaming_detected,
            "indicators": indicators,
            "evidence": {
                "similarities": list(method_scores.values()) if method_scores else [],
                "coherence": coherence if method_scores and ensemble_stats else None,
                "similarity_variance": std_similarity if method_scores else None,
            },
        }

    def _validate_contextual_consistency(
        self, confidence: float, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate contextual consistency of confidence score."""

        method = self.validation_methods["contextual_validation"]

        contextual_score = 0.5

        # Domain consistency check
        if method.parameters.get("domain_consistency", False):
            domain = context.get("domain", "general")

            # Check if confidence is consistent with domain expectations
            domain_expectations = {
                "technical": 0.7,  # Technical content should have higher confidence
                "creative": 0.6,  # Creative content more subjective
                "factual": 0.8,  # Factual content should be highly confident
                "general": 0.6,  # General content baseline
            }

            expected_confidence = domain_expectations.get(domain, 0.6)
            domain_consistency = 1.0 - min(0.5, abs(confidence - expected_confidence))
            contextual_score = domain_consistency

        # User pattern consistency
        if method.parameters.get("user_pattern", False):
            user_id = context.get("user_id")
            if user_id:
                # Check against user's typical confidence patterns
                # This would be implemented with user behavior analysis
                contextual_score = min(1.0, contextual_score * 1.1)

        method.total_validations += 1
        method.successful_validations += 1

        return {
            "score": contextual_score,
            "gaming_detected": False,
            "indicators": [],
            "evidence": {
                "domain": context.get("domain"),
                "user_id": context.get("user_id"),
            },
        }

    def _validate_gaming_patterns(
        self,
        confidence: float,
        similarity_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate for specific gaming patterns."""

        method = self.validation_methods["gaming_detection"]
        gaming_sensitivity = method.parameters["gaming_sensitivity"]

        gaming_detected = False
        indicators = []
        gaming_score = 1.0

        # Pattern 1: Confidence clustering at economic thresholds
        economic_thresholds = [0.2, 0.5, 0.8]  # Common attribution thresholds
        for threshold in economic_thresholds:
            if abs(confidence - threshold) < 0.05:  # Very close to threshold
                gaming_detected = True
                indicators.append("threshold_targeting")
                gaming_score *= 0.7

        # Pattern 2: Repeated identical confidence scores
        content_hash = context.get("content_hash", "")
        if content_hash:
            recent_scores = [
                score for score, _ in self.confidence_history[content_hash][-10:]
            ]
            identical_scores = recent_scores.count(confidence)
            if identical_scores > 3:  # Same confidence appears too often
                gaming_detected = True
                indicators.append("identical_confidence_repetition")
                gaming_score *= 0.6

        # Pattern 3: Artificial confidence inflation
        method_scores = similarity_data.get("method_scores", {})
        if method_scores:
            max_similarity = max(method_scores.values())
            if (
                confidence > max_similarity + 0.2
            ):  # Confidence much higher than any similarity
                gaming_detected = True
                indicators.append("artificial_confidence_inflation")
                gaming_score *= 0.5

        # Pattern 4: Temporal gaming patterns
        if self._detect_temporal_gaming_pattern(confidence, context):
            gaming_detected = True
            indicators.append("temporal_gaming_pattern")
            gaming_score *= 0.6

        if gaming_detected and gaming_score < gaming_sensitivity:
            method.manipulation_detections += 1

        method.total_validations += 1

        return {
            "score": gaming_score,
            "gaming_detected": gaming_detected and gaming_score < gaming_sensitivity,
            "indicators": indicators,
            "evidence": {
                "gaming_score": gaming_score,
                "threshold_analysis": [
                    {"threshold": t, "distance": abs(confidence - t)}
                    for t in economic_thresholds
                ],
            },
        }

    def _build_validation_consensus(
        self, validation_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Build consensus from validation method scores."""

        if not validation_scores:
            return {
                "consensus_score": 0.0,
                "consensus_reached": False,
                "method_weights": {},
                "weighted_average": 0.0,
            }

        # Calculate weighted average
        total_weight = 0.0
        weighted_sum = 0.0
        method_weights = {}

        for method_name, score in validation_scores.items():
            if method_name in self.validation_methods:
                method = self.validation_methods[method_name]
                weight = method.weight
                method_weights[method_name] = weight
                weighted_sum += score * weight
                total_weight += weight

        weighted_average = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Check for consensus
        scores = list(validation_scores.values())
        consensus_reached = True

        if len(scores) > 1:
            score_std = statistics.stdev(scores)
            consensus_reached = score_std < (
                1.0 - self.security_config["min_consensus_threshold"]
            )

        if not consensus_reached:
            self.metrics["consensus_failures"] += 1

        return {
            "consensus_score": weighted_average,
            "consensus_reached": consensus_reached,
            "method_weights": method_weights,
            "weighted_average": weighted_average,
            "score_variance": statistics.variance(scores) if len(scores) > 1 else 0.0,
            "methods_used": list(validation_scores.keys()),
        }

    def _calculate_validated_confidence(
        self,
        original_confidence: float,
        consensus_result: Dict[str, Any],
        gaming_indicators: List[str],
    ) -> float:
        """Calculate final validated confidence score."""

        # Start with consensus score
        validated_confidence = consensus_result["consensus_score"]

        # Apply gaming penalties
        gaming_penalty = 1.0
        if gaming_indicators:
            penalty_per_indicator = 0.15
            gaming_penalty = max(
                0.1, 1.0 - (len(gaming_indicators) * penalty_per_indicator)
            )

        # Apply consensus penalty if no consensus reached
        consensus_penalty = 1.0
        if not consensus_result["consensus_reached"]:
            consensus_penalty = 0.8

        # Calculate final confidence
        final_confidence = validated_confidence * gaming_penalty * consensus_penalty

        # Ensure reasonable bounds
        final_confidence = max(0.0, min(1.0, final_confidence))

        # Additional security check: prevent extreme adjustments unless strong evidence
        adjustment_ratio = (
            final_confidence / original_confidence if original_confidence > 0 else 1.0
        )
        max_adjustment = self.security_config["max_confidence_deviation"]

        if abs(adjustment_ratio - 1.0) > max_adjustment:
            # Limit extreme adjustments
            if adjustment_ratio > 1.0:
                final_confidence = original_confidence * (1.0 + max_adjustment)
            else:
                final_confidence = original_confidence * (1.0 - max_adjustment)

        return final_confidence

    def _store_validation_data(
        self,
        content_hash: str,
        original_confidence: float,
        validated_confidence: float,
        context: Dict[str, Any],
    ):
        """Store validation data for historical analysis."""

        timestamp = datetime.now(timezone.utc)

        # Store confidence history
        self.confidence_history[content_hash].append((validated_confidence, timestamp))

        # Limit history size
        if len(self.confidence_history[content_hash]) > 100:
            self.confidence_history[content_hash] = self.confidence_history[
                content_hash
            ][-50:]

        # Store temporal patterns
        time_key = timestamp.strftime("%Y-%m-%d-%H")  # Hourly buckets
        self.temporal_patterns[time_key].append(validated_confidence)

    def _detect_threshold_clustering(self, scores: List[float]) -> bool:
        """Detect artificial clustering around attribution thresholds."""

        thresholds = [0.2, 0.5, 0.8]  # Common UATP thresholds

        for threshold in thresholds:
            near_threshold = [s for s in scores if abs(s - threshold) < 0.05]
            if len(near_threshold) / len(scores) > 0.4:  # More than 40% near threshold
                return True

        return False

    def _detect_similarity_gaming(self, similarities: List[float]) -> bool:
        """Detect gaming in similarity scores."""

        if len(similarities) < 3:
            return False

        # Check for artificial uniformity
        similarity_std = statistics.stdev(similarities)
        if similarity_std < 0.01:  # Suspiciously uniform
            return True

        # Check for outliers that might indicate gaming
        mean_similarity = statistics.mean(similarities)
        outliers = [s for s in similarities if abs(s - mean_similarity) > 0.3]
        if len(outliers) / len(similarities) > 0.3:  # Too many outliers
            return True

        return False

    def _calculate_expected_confidence(
        self, similarity: float, similarity_std: float
    ) -> float:
        """Calculate expected confidence based on similarity scores."""

        # Base confidence from similarity
        base_confidence = similarity * 0.9  # Slight reduction for conservatism

        # Adjust for variance (high variance reduces confidence)
        variance_adjustment = max(0.8, 1.0 - similarity_std)

        return base_confidence * variance_adjustment

    def _detect_temporal_gaming_pattern(
        self, confidence: float, context: Dict[str, Any]
    ) -> bool:
        """Detect temporal gaming patterns."""

        # Check for rapid-fire confidence submissions
        current_time = datetime.now(timezone.utc)
        recent_window = current_time - timedelta(minutes=10)

        # Count recent validations (would need to track this)
        # For now, use a simple heuristic
        user_id = context.get("user_id")
        if user_id:
            # Check if this user has submitted many confidences recently
            # This would require additional tracking infrastructure
            pass

        return False

    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics."""

        method_stats = {}
        for method_name, method in self.validation_methods.items():
            success_rate = method.successful_validations / max(
                1, method.total_validations
            )
            detection_rate = method.manipulation_detections / max(
                1, method.total_validations
            )

            method_stats[method_name] = {
                "enabled": method.enabled,
                "weight": method.weight,
                "threshold": method.threshold,
                "total_validations": method.total_validations,
                "successful_validations": method.successful_validations,
                "manipulation_detections": method.manipulation_detections,
                "success_rate": success_rate,
                "detection_rate": detection_rate,
            }

        return {
            "system_metrics": self.metrics.copy(),
            "security_config": self.security_config.copy(),
            "validation_methods": method_stats,
            "data_sizes": {
                "confidence_history_entries": sum(
                    len(scores) for scores in self.confidence_history.values()
                ),
                "temporal_patterns": len(self.temporal_patterns),
                "peer_comparisons": len(self.peer_comparisons),
            },
        }

    def update_method_configuration(
        self, method_name: str, config_updates: Dict[str, Any]
    ):
        """Update configuration for a validation method."""

        if method_name not in self.validation_methods:
            raise ValueError(f"Unknown validation method: {method_name}")

        method = self.validation_methods[method_name]

        if "weight" in config_updates:
            method.weight = config_updates["weight"]
        if "threshold" in config_updates:
            method.threshold = config_updates["threshold"]
        if "enabled" in config_updates:
            method.enabled = config_updates["enabled"]
        if "parameters" in config_updates:
            method.parameters.update(config_updates["parameters"])

        logger.info(f"Updated configuration for validation method: {method_name}")


# Global confidence validator instance
confidence_validator = ConfidenceValidator()
