"""
Machine Learning Analytics Engine for UATP Capsule Engine.
Provides intelligent insights, predictions, and automated analysis.
"""

import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.audit.events import audit_emitter
from src.capsule_schema import AnyCapsule
from src.economic.fcde_engine import fcde_engine
from src.graph.capsule_relationships import relationship_graph

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Types of ML models."""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    RECOMMENDATION = "recommendation"
    NATURAL_LANGUAGE = "natural_language"
    TIME_SERIES = "time_series"


class AnalyticsCategory(str, Enum):
    """Categories of analytics."""

    CONTENT_ANALYSIS = "content_analysis"
    USAGE_PREDICTION = "usage_prediction"
    QUALITY_ASSESSMENT = "quality_assessment"
    RELATIONSHIP_ANALYSIS = "relationship_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    PERFORMANCE_PREDICTION = "performance_prediction"
    RECOMMENDATION = "recommendation"


@dataclass
class AnalyticsResult:
    """Result of ML analytics."""

    result_id: str
    category: AnalyticsCategory
    model_type: ModelType
    prediction: Any
    confidence: float
    features: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result_id": self.result_id,
            "category": self.category.value,
            "model_type": self.model_type.value,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "features": self.features,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MLModel:
    """ML model configuration."""

    model_id: str
    model_type: ModelType
    category: AnalyticsCategory
    algorithm: str
    features: List[str]
    hyperparameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    last_trained: Optional[datetime] = None
    version: str = "1.0"
    enabled: bool = True


class FeatureExtractor:
    """Extracts features from capsules for ML analysis."""

    def __init__(self):
        self.feature_cache: Dict[str, Dict[str, Any]] = {}
        self.vocabulary: Dict[str, int] = {}
        self.max_vocab_size = 10000

    def extract_features(self, capsule: AnyCapsule) -> Dict[str, Any]:
        """Extract comprehensive features from a capsule."""

        if capsule.capsule_id in self.feature_cache:
            return self.feature_cache[capsule.capsule_id]

        features = {}

        # Basic features
        features.update(self._extract_basic_features(capsule))

        # Content features
        features.update(self._extract_content_features(capsule))

        # Temporal features
        features.update(self._extract_temporal_features(capsule))

        # Graph features
        features.update(self._extract_graph_features(capsule))

        # Economic features
        features.update(self._extract_economic_features(capsule))

        # Cache results
        self.feature_cache[capsule.capsule_id] = features

        return features

    def _extract_basic_features(self, capsule: AnyCapsule) -> Dict[str, Any]:
        """Extract basic capsule features."""
        return {
            "capsule_type": capsule.capsule_type.value,
            "version": capsule.version,
            "status": capsule.status.value,
            "has_signer": bool(capsule.verification.signer),
            "has_signature": bool(capsule.verification.signature),
            "capsule_id_length": len(capsule.capsule_id),
        }

    def _extract_content_features(self, capsule: AnyCapsule) -> Dict[str, Any]:
        """Extract content-based features."""
        content = self._extract_text_content(capsule)

        features = {
            "content_length": len(content),
            "word_count": len(content.split()),
            "sentence_count": len(content.split(".")),
            "unique_words": len(set(content.lower().split())),
            "avg_word_length": np.mean([len(word) for word in content.split()])
            if content
            else 0,
            "punctuation_count": len(re.findall(r"[^\w\s]", content)),
            "uppercase_ratio": sum(1 for c in content if c.isupper())
            / max(len(content), 1),
            "digit_ratio": sum(1 for c in content if c.isdigit())
            / max(len(content), 1),
        }

        # Content complexity features
        features.update(self._extract_complexity_features(content))

        # Sentiment features (simplified)
        features.update(self._extract_sentiment_features(content))

        # Topic features
        features.update(self._extract_topic_features(content))

        return features

    def _extract_temporal_features(self, capsule: AnyCapsule) -> Dict[str, Any]:
        """Extract temporal features."""
        now = datetime.now(timezone.utc)
        age = (now - capsule.timestamp).total_seconds()

        return {
            "age_seconds": age,
            "age_hours": age / 3600,
            "age_days": age / 86400,
            "created_hour": capsule.timestamp.hour,
            "created_day_of_week": capsule.timestamp.weekday(),
            "created_month": capsule.timestamp.month,
            "is_weekend": capsule.timestamp.weekday() >= 5,
            "is_business_hours": 9 <= capsule.timestamp.hour <= 17,
        }

    def _extract_graph_features(self, capsule: AnyCapsule) -> Dict[str, Any]:
        """Extract graph-based features."""
        features = {
            "in_degree": 0,
            "out_degree": 0,
            "betweenness_centrality": 0.0,
            "closeness_centrality": 0.0,
            "pagerank": 0.0,
            "clustering_coefficient": 0.0,
        }

        if capsule.capsule_id in relationship_graph.nodes:
            # Get centrality measures
            centrality = relationship_graph.get_capsule_centrality(capsule.capsule_id)
            features.update(
                {
                    "degree_centrality": centrality.get("degree", 0.0),
                    "betweenness_centrality": centrality.get("betweenness", 0.0),
                    "closeness_centrality": centrality.get("closeness", 0.0),
                    "pagerank": centrality.get("pagerank", 0.0),
                }
            )

            # Get graph structure features
            if capsule.capsule_id in relationship_graph.graph:
                features["in_degree"] = relationship_graph.graph.in_degree(
                    capsule.capsule_id
                )
                features["out_degree"] = relationship_graph.graph.out_degree(
                    capsule.capsule_id
                )

        return features

    def _extract_economic_features(self, capsule: AnyCapsule) -> Dict[str, Any]:
        """Extract economic features."""
        features = {
            "has_economic_value": False,
            "contribution_count": 0,
            "total_value_generated": 0.0,
            "creator_reputation": 0.0,
        }

        # Check if capsule has economic attribution
        creator_id = capsule.verification.signer or "unknown"

        if creator_id in fcde_engine.creator_accounts:
            account = fcde_engine.creator_accounts[creator_id]
            features.update(
                {
                    "has_economic_value": True,
                    "creator_reputation": float(account.reputation_score),
                    "creator_total_contributions": float(account.total_contributions),
                    "creator_dividends_earned": float(account.total_dividends_earned),
                }
            )

        return features

    def _extract_complexity_features(self, text: str) -> Dict[str, Any]:
        """Extract text complexity features."""
        if not text:
            return {"complexity_score": 0.0, "readability_score": 0.0}

        # Simple complexity metrics
        words = text.split()
        sentences = text.split(".")

        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = np.mean([len(word) for word in words])

        # Simplified readability score
        readability_score = (
            206.835 - 1.015 * avg_sentence_length - 84.6 * avg_word_length
        )

        return {
            "avg_sentence_length": avg_sentence_length,
            "avg_word_length": avg_word_length,
            "readability_score": max(0, min(100, readability_score)),
            "complexity_score": min(1.0, (avg_sentence_length + avg_word_length) / 20),
        }

    def _extract_sentiment_features(self, text: str) -> Dict[str, Any]:
        """Extract sentiment features (simplified)."""
        if not text:
            return {"sentiment_score": 0.0, "sentiment_polarity": "neutral"}

        # Simple sentiment analysis using word lists
        positive_words = {
            "good",
            "great",
            "excellent",
            "amazing",
            "wonderful",
            "fantastic",
            "positive",
            "successful",
            "effective",
            "beneficial",
            "helpful",
        }

        negative_words = {
            "bad",
            "terrible",
            "awful",
            "horrible",
            "negative",
            "failed",
            "unsuccessful",
            "ineffective",
            "harmful",
            "problematic",
            "wrong",
        }

        words = set(text.lower().split())
        positive_count = len(words.intersection(positive_words))
        negative_count = len(words.intersection(negative_words))

        total_sentiment_words = positive_count + negative_count

        if total_sentiment_words == 0:
            sentiment_score = 0.0
            polarity = "neutral"
        else:
            sentiment_score = (positive_count - negative_count) / total_sentiment_words
            if sentiment_score > 0.1:
                polarity = "positive"
            elif sentiment_score < -0.1:
                polarity = "negative"
            else:
                polarity = "neutral"

        return {
            "sentiment_score": sentiment_score,
            "sentiment_polarity": polarity,
            "positive_word_count": positive_count,
            "negative_word_count": negative_count,
        }

    def _extract_topic_features(self, text: str) -> Dict[str, Any]:
        """Extract topic features (simplified)."""
        if not text:
            return {"primary_topic": "unknown", "topic_confidence": 0.0}

        # Simple topic classification using keyword matching
        topics = {
            "technology": [
                "technology",
                "software",
                "computer",
                "system",
                "algorithm",
                "data",
            ],
            "science": [
                "research",
                "study",
                "experiment",
                "analysis",
                "hypothesis",
                "theory",
            ],
            "business": [
                "business",
                "company",
                "market",
                "customer",
                "revenue",
                "profit",
            ],
            "education": [
                "education",
                "learning",
                "student",
                "teacher",
                "knowledge",
                "skill",
            ],
            "health": [
                "health",
                "medical",
                "patient",
                "treatment",
                "diagnosis",
                "therapy",
            ],
            "general": [
                "general",
                "information",
                "content",
                "text",
                "message",
                "communication",
            ],
        }

        text_lower = text.lower()
        topic_scores = {}

        for topic, keywords in topics.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            topic_scores[topic] = score

        if not topic_scores or max(topic_scores.values()) == 0:
            return {"primary_topic": "general", "topic_confidence": 0.0}

        primary_topic = max(topic_scores, key=topic_scores.get)
        confidence = topic_scores[primary_topic] / sum(topic_scores.values())

        return {
            "primary_topic": primary_topic,
            "topic_confidence": confidence,
            "topic_scores": topic_scores,
        }

    def _extract_text_content(self, capsule: AnyCapsule) -> str:
        """Extract text content from capsule."""
        content_parts = []

        if hasattr(capsule, "reasoning_trace") and capsule.reasoning_trace:
            for step in capsule.reasoning_trace.steps:
                content_parts.append(step.content)

        if hasattr(capsule, "uncertainty") and capsule.uncertainty:
            content_parts.extend(capsule.uncertainty.missing_facts)
            content_parts.append(capsule.uncertainty.recommendation)

        return " ".join(content_parts)


class PredictiveAnalyzer:
    """Performs predictive analytics on capsule data."""

    def __init__(self):
        self.models: Dict[str, MLModel] = {}
        self.feature_extractor = FeatureExtractor()
        self.prediction_cache: Dict[str, Any] = {}

    def predict_capsule_usage(self, capsule: AnyCapsule) -> AnalyticsResult:
        """Predict future usage patterns for a capsule."""

        features = self.feature_extractor.extract_features(capsule)

        # Simple usage prediction model
        usage_score = self._calculate_usage_score(features)

        # Predict usage category
        if usage_score > 0.7:
            usage_prediction = "high"
        elif usage_score > 0.4:
            usage_prediction = "medium"
        else:
            usage_prediction = "low"

        return AnalyticsResult(
            result_id=self._generate_result_id(),
            category=AnalyticsCategory.USAGE_PREDICTION,
            model_type=ModelType.CLASSIFICATION,
            prediction=usage_prediction,
            confidence=min(0.95, usage_score + 0.1),
            features=features,
            metadata={"usage_score": usage_score},
            timestamp=datetime.now(timezone.utc),
        )

    def predict_capsule_quality(self, capsule: AnyCapsule) -> AnalyticsResult:
        """Predict quality score for a capsule."""

        features = self.feature_extractor.extract_features(capsule)

        # Quality prediction based on multiple factors
        quality_score = self._calculate_quality_score(features)

        return AnalyticsResult(
            result_id=self._generate_result_id(),
            category=AnalyticsCategory.QUALITY_ASSESSMENT,
            model_type=ModelType.REGRESSION,
            prediction=quality_score,
            confidence=0.8,
            features=features,
            metadata={"quality_factors": self._get_quality_factors(features)},
            timestamp=datetime.now(timezone.utc),
        )

    def predict_capsule_relationships(self, capsule: AnyCapsule) -> AnalyticsResult:
        """Predict potential relationships for a capsule."""

        features = self.feature_extractor.extract_features(capsule)

        # Find similar capsules
        similar_capsules = self._find_similar_capsules(capsule, features)

        # Predict relationship types
        relationship_predictions = []
        for similar_id, similarity_score in similar_capsules:
            if similarity_score > 0.6:
                relationship_predictions.append(
                    {
                        "target_capsule": similar_id,
                        "relationship_type": "supports",
                        "confidence": similarity_score,
                    }
                )

        return AnalyticsResult(
            result_id=self._generate_result_id(),
            category=AnalyticsCategory.RELATIONSHIP_ANALYSIS,
            model_type=ModelType.RECOMMENDATION,
            prediction=relationship_predictions,
            confidence=0.7,
            features=features,
            metadata={"similar_capsules_found": len(similar_capsules)},
            timestamp=datetime.now(timezone.utc),
        )

    def detect_anomalies(self, capsule: AnyCapsule) -> AnalyticsResult:
        """Detect anomalies in capsule data."""

        features = self.feature_extractor.extract_features(capsule)

        # Simple anomaly detection
        anomaly_score = self._calculate_anomaly_score(features)

        is_anomaly = anomaly_score > 0.7

        return AnalyticsResult(
            result_id=self._generate_result_id(),
            category=AnalyticsCategory.ANOMALY_DETECTION,
            model_type=ModelType.ANOMALY_DETECTION,
            prediction=is_anomaly,
            confidence=anomaly_score,
            features=features,
            metadata={
                "anomaly_score": anomaly_score,
                "anomaly_factors": self._get_anomaly_factors(features),
            },
            timestamp=datetime.now(timezone.utc),
        )

    def _calculate_usage_score(self, features: Dict[str, Any]) -> float:
        """Calculate usage prediction score."""
        score = 0.0

        # Content quality factors
        if features.get("readability_score", 0) > 50:
            score += 0.2

        if features.get("content_length", 0) > 100:
            score += 0.1

        # Graph centrality factors
        score += min(0.3, features.get("pagerank", 0) * 10)
        score += min(0.2, features.get("degree_centrality", 0) * 5)

        # Economic factors
        if features.get("has_economic_value", False):
            score += 0.2

        # Temporal factors
        age_days = features.get("age_days", 0)
        if age_days < 7:  # Recent capsules might get more usage
            score += 0.1

        return min(1.0, score)

    def _calculate_quality_score(self, features: Dict[str, Any]) -> float:
        """Calculate quality prediction score."""
        score = 0.5  # Base score

        # Content quality
        readability = features.get("readability_score", 0)
        if readability > 60:
            score += 0.2
        elif readability < 30:
            score -= 0.2

        # Complexity
        complexity = features.get("complexity_score", 0)
        if 0.3 < complexity < 0.7:  # Optimal complexity
            score += 0.1

        # Sentiment
        sentiment = features.get("sentiment_score", 0)
        if sentiment > 0:
            score += 0.1

        # Economic validation
        if features.get("creator_reputation", 0) > 80:
            score += 0.15

        # Graph metrics
        if features.get("pagerank", 0) > 0.001:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _find_similar_capsules(
        self, capsule: AnyCapsule, features: Dict[str, Any]
    ) -> List[Tuple[str, float]]:
        """Find similar capsules using feature similarity."""
        similar_capsules = []

        # Compare with cached features
        for cached_id, cached_features in self.feature_extractor.feature_cache.items():
            if cached_id != capsule.capsule_id:
                similarity = self._calculate_feature_similarity(
                    features, cached_features
                )
                if similarity > 0.5:
                    similar_capsules.append((cached_id, similarity))

        # Sort by similarity
        similar_capsules.sort(key=lambda x: x[1], reverse=True)

        return similar_capsules[:10]  # Top 10 similar capsules

    def _calculate_feature_similarity(
        self, features1: Dict[str, Any], features2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two feature sets."""

        # Numerical features
        numerical_features = [
            "content_length",
            "word_count",
            "readability_score",
            "sentiment_score",
            "pagerank",
            "degree_centrality",
            "age_days",
        ]

        similarities = []

        for feature in numerical_features:
            val1 = features1.get(feature, 0)
            val2 = features2.get(feature, 0)

            if val1 == 0 and val2 == 0:
                similarities.append(1.0)
            elif val1 == 0 or val2 == 0:
                similarities.append(0.0)
            else:
                # Normalized similarity
                similarity = 1.0 - abs(val1 - val2) / max(val1, val2)
                similarities.append(similarity)

        # Categorical features
        categorical_features = ["capsule_type", "primary_topic", "sentiment_polarity"]

        for feature in categorical_features:
            val1 = features1.get(feature, "")
            val2 = features2.get(feature, "")

            if val1 == val2:
                similarities.append(1.0)
            else:
                similarities.append(0.0)

        return np.mean(similarities) if similarities else 0.0

    def _calculate_anomaly_score(self, features: Dict[str, Any]) -> float:
        """Calculate anomaly detection score."""
        anomaly_score = 0.0

        # Check for unusual content length
        content_length = features.get("content_length", 0)
        if content_length > 10000 or content_length < 10:
            anomaly_score += 0.3

        # Check for unusual readability
        readability = features.get("readability_score", 50)
        if readability < 10 or readability > 90:
            anomaly_score += 0.2

        # Check for unusual creation time
        if (
            features.get("created_hour", 12) < 6
            or features.get("created_hour", 12) > 23
        ):
            anomaly_score += 0.1

        # Check for unusual graph metrics
        if features.get("pagerank", 0) > 0.01:  # Very high PageRank
            anomaly_score += 0.2

        # Check for sentiment extremes
        sentiment = features.get("sentiment_score", 0)
        if abs(sentiment) > 0.8:
            anomaly_score += 0.2

        return min(1.0, anomaly_score)

    def _get_quality_factors(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Get factors contributing to quality score."""
        return {
            "readability": features.get("readability_score", 0),
            "complexity": features.get("complexity_score", 0),
            "sentiment": features.get("sentiment_score", 0),
            "creator_reputation": features.get("creator_reputation", 0),
            "graph_centrality": features.get("pagerank", 0),
        }

    def _get_anomaly_factors(self, features: Dict[str, Any]) -> List[str]:
        """Get factors contributing to anomaly detection."""
        factors = []

        content_length = features.get("content_length", 0)
        if content_length > 10000:
            factors.append("unusually_long_content")
        elif content_length < 10:
            factors.append("unusually_short_content")

        readability = features.get("readability_score", 50)
        if readability < 10:
            factors.append("very_low_readability")
        elif readability > 90:
            factors.append("very_high_readability")

        if features.get("created_hour", 12) < 6:
            factors.append("created_very_early")
        elif features.get("created_hour", 12) > 23:
            factors.append("created_very_late")

        if features.get("pagerank", 0) > 0.01:
            factors.append("unusually_high_influence")

        sentiment = features.get("sentiment_score", 0)
        if sentiment > 0.8:
            factors.append("extremely_positive_sentiment")
        elif sentiment < -0.8:
            factors.append("extremely_negative_sentiment")

        return factors

    def _generate_result_id(self) -> str:
        """Generate unique result ID."""
        import uuid

        return str(uuid.uuid4())[:12]


class MLAnalyticsEngine:
    """Main ML analytics engine."""

    def __init__(self):
        self.predictive_analyzer = PredictiveAnalyzer()
        self.analytics_results: Dict[str, AnalyticsResult] = {}
        self.insights_cache: Dict[str, Any] = {}
        self.model_performance: Dict[str, Dict[str, float]] = {}

    def analyze_capsule(self, capsule: AnyCapsule) -> Dict[str, AnalyticsResult]:
        """Perform comprehensive ML analysis on a capsule."""

        results = {}

        # Usage prediction
        usage_result = self.predictive_analyzer.predict_capsule_usage(capsule)
        results["usage_prediction"] = usage_result
        self.analytics_results[usage_result.result_id] = usage_result

        # Quality assessment
        quality_result = self.predictive_analyzer.predict_capsule_quality(capsule)
        results["quality_assessment"] = quality_result
        self.analytics_results[quality_result.result_id] = quality_result

        # Relationship prediction
        relationship_result = self.predictive_analyzer.predict_capsule_relationships(
            capsule
        )
        results["relationship_prediction"] = relationship_result
        self.analytics_results[relationship_result.result_id] = relationship_result

        # Anomaly detection
        anomaly_result = self.predictive_analyzer.detect_anomalies(capsule)
        results["anomaly_detection"] = anomaly_result
        self.analytics_results[anomaly_result.result_id] = anomaly_result

        # Generate insights
        insights = self._generate_insights(capsule, results)
        self.insights_cache[capsule.capsule_id] = insights

        # Emit audit event
        audit_emitter.emit_capsule_created(
            capsule_id=f"ml_analysis_{capsule.capsule_id}",
            agent_id="ml_analytics_engine",
            capsule_type="ml_analysis",
        )

        logger.info(f"Completed ML analysis for capsule {capsule.capsule_id}")

        return results

    def get_system_insights(self) -> Dict[str, Any]:
        """Get system-wide ML insights."""

        insights = {
            "total_analyses": len(self.analytics_results),
            "analysis_categories": self._get_analysis_distribution(),
            "quality_trends": self._get_quality_trends(),
            "usage_patterns": self._get_usage_patterns(),
            "anomaly_summary": self._get_anomaly_summary(),
            "relationship_insights": self._get_relationship_insights(),
            "top_insights": self._get_top_insights(),
        }

        return insights

    def _generate_insights(
        self, capsule: AnyCapsule, results: Dict[str, AnalyticsResult]
    ) -> Dict[str, Any]:
        """Generate insights from analysis results."""

        insights = []

        # Usage insights
        usage_result = results.get("usage_prediction")
        if usage_result and usage_result.prediction == "high":
            insights.append("This capsule is predicted to have high usage")

        # Quality insights
        quality_result = results.get("quality_assessment")
        if quality_result and quality_result.prediction > 0.8:
            insights.append("This capsule demonstrates high quality content")
        elif quality_result and quality_result.prediction < 0.4:
            insights.append("This capsule may need quality improvements")

        # Relationship insights
        relationship_result = results.get("relationship_prediction")
        if relationship_result and len(relationship_result.prediction) > 3:
            insights.append("This capsule has strong connections to other content")

        # Anomaly insights
        anomaly_result = results.get("anomaly_detection")
        if anomaly_result and anomaly_result.prediction:
            insights.append(
                "This capsule shows unusual patterns that may need attention"
            )

        return {
            "capsule_id": capsule.capsule_id,
            "insights": insights,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "confidence": np.mean([r.confidence for r in results.values()]),
        }

    def _get_analysis_distribution(self) -> Dict[str, int]:
        """Get distribution of analysis categories."""
        distribution = defaultdict(int)

        for result in self.analytics_results.values():
            distribution[result.category.value] += 1

        return dict(distribution)

    def _get_quality_trends(self) -> Dict[str, Any]:
        """Get quality trends from analyses."""
        quality_results = [
            r
            for r in self.analytics_results.values()
            if r.category == AnalyticsCategory.QUALITY_ASSESSMENT
        ]

        if not quality_results:
            return {"trend": "no_data"}

        quality_scores = [r.prediction for r in quality_results]

        return {
            "average_quality": np.mean(quality_scores),
            "quality_std": np.std(quality_scores),
            "high_quality_percentage": sum(1 for s in quality_scores if s > 0.7)
            / len(quality_scores)
            * 100,
            "total_assessments": len(quality_results),
        }

    def _get_usage_patterns(self) -> Dict[str, Any]:
        """Get usage patterns from predictions."""
        usage_results = [
            r
            for r in self.analytics_results.values()
            if r.category == AnalyticsCategory.USAGE_PREDICTION
        ]

        if not usage_results:
            return {"pattern": "no_data"}

        usage_distribution = Counter(r.prediction for r in usage_results)

        return {
            "usage_distribution": dict(usage_distribution),
            "most_common_usage": usage_distribution.most_common(1)[0][0]
            if usage_distribution
            else "unknown",
            "total_predictions": len(usage_results),
        }

    def _get_anomaly_summary(self) -> Dict[str, Any]:
        """Get anomaly detection summary."""
        anomaly_results = [
            r
            for r in self.analytics_results.values()
            if r.category == AnalyticsCategory.ANOMALY_DETECTION
        ]

        if not anomaly_results:
            return {"anomalies": "no_data"}

        anomaly_count = sum(1 for r in anomaly_results if r.prediction)

        return {
            "total_checks": len(anomaly_results),
            "anomalies_detected": anomaly_count,
            "anomaly_rate": anomaly_count / len(anomaly_results) * 100,
            "average_anomaly_score": np.mean(
                [r.confidence for r in anomaly_results if r.prediction]
            ),
        }

    def _get_relationship_insights(self) -> Dict[str, Any]:
        """Get relationship analysis insights."""
        relationship_results = [
            r
            for r in self.analytics_results.values()
            if r.category == AnalyticsCategory.RELATIONSHIP_ANALYSIS
        ]

        if not relationship_results:
            return {"relationships": "no_data"}

        total_relationships = sum(len(r.prediction) for r in relationship_results)

        return {
            "total_relationship_predictions": total_relationships,
            "average_relationships_per_capsule": total_relationships
            / len(relationship_results),
            "capsules_with_relationships": sum(
                1 for r in relationship_results if len(r.prediction) > 0
            ),
            "relationship_density": total_relationships / len(relationship_results)
            if relationship_results
            else 0,
        }

    def _get_top_insights(self) -> List[Dict[str, Any]]:
        """Get top insights across all analyses."""

        # Get recent high-confidence insights
        recent_insights = []

        for capsule_id, insight_data in self.insights_cache.items():
            if insight_data.get("confidence", 0) > 0.8:
                recent_insights.append(
                    {
                        "capsule_id": capsule_id,
                        "insights": insight_data["insights"],
                        "confidence": insight_data["confidence"],
                    }
                )

        # Sort by confidence
        recent_insights.sort(key=lambda x: x["confidence"], reverse=True)

        return recent_insights[:10]  # Top 10 insights


# Global ML analytics engine instance
ml_analytics = MLAnalyticsEngine()
