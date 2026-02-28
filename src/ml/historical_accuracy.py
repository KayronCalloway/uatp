"""
Historical Accuracy Learning - Gap 2 Implementation
Uses embeddings to find similar past capsules and learn from their outcomes.

When creating a new capsule:
1. Find similar past capsules by embedding similarity
2. Check if those similar capsules have outcome data
3. Calculate historical accuracy from those outcomes
4. Adjust the current capsule's confidence based on historical accuracy

Example:
    "Similar recommendations in the past were 87% accurate"
    Adjusts confidence: model_confidence=0.85 + historical_accuracy=0.87 -> blended=0.86
"""

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SimilarCapsule:
    """A similar capsule with its outcome data."""

    capsule_id: str
    similarity: float
    timestamp: datetime
    outcome_status: Optional[str]  # 'success', 'partial', 'failure', or None
    original_confidence: float
    topics: List[str]


@dataclass
class HistoricalAccuracyResult:
    """Result of historical accuracy analysis."""

    historical_accuracy: Optional[float]  # None if no data
    sample_size: int
    similar_capsules: List[SimilarCapsule]
    adjusted_confidence: float
    confidence_adjustment: float  # How much was changed
    explanation: str
    outcome_breakdown: Dict[str, int]  # {'success': 5, 'partial': 2, 'failure': 1}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "historical_accuracy": self.historical_accuracy,
            "sample_size": self.sample_size,
            "adjusted_confidence": self.adjusted_confidence,
            "confidence_adjustment": self.confidence_adjustment,
            "explanation": self.explanation,
            "outcome_breakdown": self.outcome_breakdown,
            "similar_capsule_count": len(self.similar_capsules),
            "similar_capsules": [
                {
                    "capsule_id": sc.capsule_id,
                    "similarity": round(sc.similarity, 3),
                    "outcome": sc.outcome_status,
                    "original_confidence": sc.original_confidence,
                }
                for sc in self.similar_capsules[:5]  # Top 5 only
            ],
        }


class HistoricalAccuracyEngine:
    """
    Engine for learning from historical capsule outcomes.

    Uses embedding similarity to find relevant past capsules and
    calculates accuracy from their outcomes to inform new predictions.
    """

    # Minimum similarity to consider a capsule as "similar"
    MIN_SIMILARITY_THRESHOLD = 0.3

    # Maximum similar capsules to consider
    MAX_SIMILAR_CAPSULES = 20

    # Minimum sample size to trust historical accuracy
    MIN_SAMPLE_SIZE = 3

    # Weight given to historical accuracy vs model confidence
    HISTORICAL_WEIGHT = 0.3

    def __init__(self, db_path: str = None):
        """
        Initialize the historical accuracy engine.

        Args:
            db_path: Path to SQLite database (default: uatp_dev.db)
        """
        self.db_path = db_path or "uatp_dev.db"

    def _get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a = np.array(a)
        b = np.array(b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def find_similar_capsules(
        self,
        query_embedding: List[float],
        exclude_capsule_id: str = None,
        min_similarity: float = None,
        limit: int = None,
    ) -> List[SimilarCapsule]:
        """
        Find capsules similar to the query embedding.

        Args:
            query_embedding: The embedding vector to search for
            exclude_capsule_id: Capsule ID to exclude from results
            min_similarity: Minimum similarity threshold
            limit: Maximum results

        Returns:
            List of SimilarCapsule objects sorted by similarity
        """
        min_sim = min_similarity or self.MIN_SIMILARITY_THRESHOLD
        max_results = limit or self.MAX_SIMILAR_CAPSULES

        conn = self._get_connection()
        similar = []

        try:
            cursor = conn.cursor()

            # Get all capsules with embeddings
            cursor.execute(
                """
                SELECT capsule_id, embedding, timestamp, outcome_status, payload
                FROM capsules
                WHERE embedding IS NOT NULL
            """
            )

            for row in cursor.fetchall():
                (
                    capsule_id,
                    embedding_data,
                    timestamp,
                    outcome_status,
                    payload_data,
                ) = row

                # Skip the query capsule itself
                if capsule_id == exclude_capsule_id:
                    continue

                # Parse embedding
                if isinstance(embedding_data, str):
                    try:
                        embedding = json.loads(embedding_data)
                    except json.JSONDecodeError:
                        continue
                else:
                    embedding = embedding_data

                if not embedding:
                    continue

                # Calculate similarity
                similarity = self._cosine_similarity(query_embedding, embedding)

                if similarity >= min_sim:
                    # Parse payload for confidence and topics
                    payload = {}
                    if isinstance(payload_data, str):
                        try:
                            payload = json.loads(payload_data)
                        except json.JSONDecodeError:
                            pass
                    elif payload_data:
                        payload = payload_data

                    original_confidence = payload.get("confidence", 0.5)
                    session_meta = payload.get("session_metadata", {})
                    topics = session_meta.get("topics", [])

                    # Parse timestamp
                    if isinstance(timestamp, str):
                        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    else:
                        ts = timestamp or datetime.now(timezone.utc)

                    similar.append(
                        SimilarCapsule(
                            capsule_id=capsule_id,
                            similarity=similarity,
                            timestamp=ts,
                            outcome_status=outcome_status,
                            original_confidence=original_confidence,
                            topics=topics if isinstance(topics, list) else [],
                        )
                    )

            # Sort by similarity descending
            similar.sort(key=lambda x: x.similarity, reverse=True)

            return similar[:max_results]

        finally:
            conn.close()

    def calculate_historical_accuracy(
        self,
        similar_capsules: List[SimilarCapsule],
        weight_by_similarity: bool = True,
    ) -> Tuple[Optional[float], Dict[str, int]]:
        """
        Calculate historical accuracy from similar capsules.

        Args:
            similar_capsules: List of similar capsules
            weight_by_similarity: Whether to weight by similarity score

        Returns:
            Tuple of (accuracy_score, outcome_breakdown)
        """
        # Filter to capsules with outcome data
        with_outcomes = [sc for sc in similar_capsules if sc.outcome_status]

        if not with_outcomes:
            return None, {}

        # Outcome value mapping
        outcome_values = {
            "success": 1.0,
            "partial": 0.5,
            "failure": 0.0,
        }

        # Count outcomes
        outcome_breakdown = {}
        for sc in with_outcomes:
            status = sc.outcome_status
            outcome_breakdown[status] = outcome_breakdown.get(status, 0) + 1

        if weight_by_similarity:
            # Weighted average by similarity
            total_weight = 0.0
            weighted_sum = 0.0

            for sc in with_outcomes:
                value = outcome_values.get(sc.outcome_status, 0.5)
                weight = sc.similarity  # Use similarity as weight
                weighted_sum += value * weight
                total_weight += weight

            accuracy = weighted_sum / total_weight if total_weight > 0 else None
        else:
            # Simple average
            values = [
                outcome_values.get(sc.outcome_status, 0.5) for sc in with_outcomes
            ]
            accuracy = np.mean(values) if values else None

        return accuracy, outcome_breakdown

    def blend_confidence(
        self,
        model_confidence: float,
        historical_accuracy: Optional[float],
        sample_size: int,
        weight_history: float = None,
    ) -> Tuple[float, float]:
        """
        Blend model confidence with historical accuracy.

        Uses a conservative approach:
        - More data = more trust in historical accuracy
        - Small sample = mostly trust model confidence
        - Historical accuracy adjusts model confidence toward it

        Args:
            model_confidence: The model's original confidence
            historical_accuracy: Historical accuracy (can be None)
            sample_size: Number of similar capsules with outcomes
            weight_history: Weight for historical accuracy (default: 0.3)

        Returns:
            Tuple of (adjusted_confidence, adjustment_amount)
        """
        if historical_accuracy is None or sample_size < self.MIN_SAMPLE_SIZE:
            return model_confidence, 0.0

        base_weight = weight_history or self.HISTORICAL_WEIGHT

        # Scale weight by sample size (more data = more trust)
        # Reaches full weight at ~10 samples
        sample_factor = min(1.0, sample_size / 10.0)
        effective_weight = base_weight * sample_factor

        # Blend: weighted average
        adjusted = (
            model_confidence * (1 - effective_weight)
            + historical_accuracy * effective_weight
        )

        # Cap confidence at 0.95 and floor at 0.05
        adjusted = max(0.05, min(0.95, adjusted))

        adjustment = adjusted - model_confidence

        return adjusted, adjustment

    def analyze_for_capsule(
        self,
        query_embedding: List[float],
        model_confidence: float,
        capsule_id: str = None,
    ) -> HistoricalAccuracyResult:
        """
        Perform full historical accuracy analysis for a capsule.

        Args:
            query_embedding: The new capsule's embedding
            model_confidence: The model's confidence for this capsule
            capsule_id: The new capsule's ID (to exclude from similar search)

        Returns:
            HistoricalAccuracyResult with all analysis data
        """
        # Find similar capsules
        similar = self.find_similar_capsules(
            query_embedding=query_embedding,
            exclude_capsule_id=capsule_id,
        )

        # Calculate historical accuracy
        historical_accuracy, outcome_breakdown = self.calculate_historical_accuracy(
            similar_capsules=similar,
            weight_by_similarity=True,
        )

        # Count capsules with outcomes
        with_outcomes = [sc for sc in similar if sc.outcome_status]
        sample_size = len(with_outcomes)

        # Blend confidence
        adjusted_confidence, confidence_adjustment = self.blend_confidence(
            model_confidence=model_confidence,
            historical_accuracy=historical_accuracy,
            sample_size=sample_size,
        )

        # Generate explanation
        if historical_accuracy is None:
            explanation = f"No historical outcome data available from {len(similar)} similar capsules."
        elif sample_size < self.MIN_SAMPLE_SIZE:
            explanation = (
                f"Found {sample_size} similar capsules with outcomes "
                f"(need {self.MIN_SAMPLE_SIZE}+ for adjustment). "
                f"Historical accuracy: {historical_accuracy:.0%}."
            )
        else:
            direction = "increased" if confidence_adjustment > 0 else "decreased"
            explanation = (
                f"Based on {sample_size} similar past capsules with "
                f"{historical_accuracy:.0%} historical accuracy, "
                f"confidence {direction} by {abs(confidence_adjustment):.1%} "
                f"(from {model_confidence:.0%} to {adjusted_confidence:.0%})."
            )

        return HistoricalAccuracyResult(
            historical_accuracy=historical_accuracy,
            sample_size=sample_size,
            similar_capsules=similar,
            adjusted_confidence=adjusted_confidence,
            confidence_adjustment=confidence_adjustment,
            explanation=explanation,
            outcome_breakdown=outcome_breakdown,
        )

    def get_accuracy_by_topic(
        self,
        topic: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get historical accuracy for a specific topic.

        Args:
            topic: Topic to search for
            limit: Maximum capsules to analyze

        Returns:
            Dict with topic accuracy statistics
        """
        conn = self._get_connection()

        try:
            cursor = conn.cursor()

            # Find capsules with this topic
            cursor.execute(
                """
                SELECT capsule_id, outcome_status, payload
                FROM capsules
                WHERE outcome_status IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (limit * 2,),
            )  # Get more to filter

            matching = []
            for row in cursor.fetchall():
                capsule_id, outcome_status, payload_data = row

                payload = {}
                if isinstance(payload_data, str):
                    try:
                        payload = json.loads(payload_data)
                    except json.JSONDecodeError:
                        continue
                elif payload_data:
                    payload = payload_data

                topics = payload.get("session_metadata", {}).get("topics", [])
                if topic.lower() in [t.lower() for t in topics]:
                    matching.append(
                        {
                            "capsule_id": capsule_id,
                            "outcome": outcome_status,
                            "confidence": payload.get("confidence", 0.5),
                        }
                    )

                if len(matching) >= limit:
                    break

            if not matching:
                return {
                    "topic": topic,
                    "sample_size": 0,
                    "accuracy": None,
                    "message": "No capsules found for this topic",
                }

            # Calculate accuracy
            outcome_values = {"success": 1.0, "partial": 0.5, "failure": 0.0}
            values = [outcome_values.get(m["outcome"], 0.5) for m in matching]

            return {
                "topic": topic,
                "sample_size": len(matching),
                "accuracy": float(np.mean(values)),
                "outcomes": {
                    "success": sum(1 for m in matching if m["outcome"] == "success"),
                    "partial": sum(1 for m in matching if m["outcome"] == "partial"),
                    "failure": sum(1 for m in matching if m["outcome"] == "failure"),
                },
            }

        finally:
            conn.close()


# Singleton instance
_engine: Optional[HistoricalAccuracyEngine] = None


def get_historical_accuracy_engine(db_path: str = None) -> HistoricalAccuracyEngine:
    """Get or create the historical accuracy engine."""
    global _engine
    if _engine is None:
        _engine = HistoricalAccuracyEngine(db_path)
    return _engine


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Historical Accuracy Analysis")
    parser.add_argument("--topic", type=str, help="Get accuracy for a topic")
    parser.add_argument("--test", action="store_true", help="Run test analysis")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    engine = HistoricalAccuracyEngine()

    if args.topic:
        result = engine.get_accuracy_by_topic(args.topic)
        print(f"\nTopic: {result['topic']}")
        print(f"Sample size: {result['sample_size']}")
        if result["accuracy"] is not None:
            print(f"Historical accuracy: {result['accuracy']:.1%}")
            print(f"Outcomes: {result.get('outcomes', {})}")
        else:
            print(result.get("message", "No data"))

    if args.test:
        # Create a dummy embedding for testing
        dummy_embedding = [0.1] * 512  # TF-IDF dimension
        result = engine.analyze_for_capsule(
            query_embedding=dummy_embedding,
            model_confidence=0.85,
        )
        print("\nTest Analysis:")
        print(f"Similar capsules found: {len(result.similar_capsules)}")
        print(f"Sample size (with outcomes): {result.sample_size}")
        print(f"Historical accuracy: {result.historical_accuracy}")
        print(f"Adjusted confidence: {result.adjusted_confidence:.1%}")
        print(f"Explanation: {result.explanation}")
