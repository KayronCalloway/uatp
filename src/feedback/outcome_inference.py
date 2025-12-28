"""
Outcome Inference Module
========================

Hybrid approach to inferring outcomes from follow-up messages:
1. High-confidence keyword patterns (fast, catches 60-70%)
2. Sentence embedding similarity for ambiguous cases
3. Routes uncertain cases to human review queue

World-class engineering principles:
- Multi-signal inference (not just keywords)
- Confidence scores for every inference
- Conservative thresholds to avoid false positives
- Clear separation between inference and calibration
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Optional: sentence-transformers for embedding similarity
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SentenceTransformer = None
    np = None


class OutcomeStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    UNCERTAIN = "uncertain"  # Routes to human review


@dataclass
class OutcomeInference:
    """Result of outcome inference."""

    status: OutcomeStatus
    confidence: float  # 0.0 to 1.0
    method: str  # "keyword", "embedding", "behavioral"
    signals: List[str]  # What triggered this inference
    needs_review: bool  # Should be queued for human review
    raw_scores: Dict[str, float]  # Detailed scoring breakdown


class KeywordPatterns:
    """
    High-precision keyword patterns for outcome detection.

    Design principle: High precision > high recall
    Better to route to embedding/human than misclassify.
    """

    # Strong success signals (high confidence)
    SUCCESS_STRONG = [
        r"\bthanks?\b.*\b(work|perfect|great|awesome|excellent)\b",
        r"\bthat\s+(work|fix|solve|did\s+it)\b",
        r"\bperfect\b",
        r"\bexactly\s+what\s+i\s+(need|want)\b",
        r"\bawesome\b",
        r"\bgreat\s+(job|work|solution)\b",
        r"\bfixed\s+(it|the|my)\b",
        r"\bproblem\s+solved\b",
        r"\bcommit(ted|ting)?\b.*\b(change|fix|update)\b",
        r"\bmerge(d)?\s+(it|this|the\s+pr)\b",
        r"\bship(ped|ping)?\s+(it|this)\b",
        r"\blgtm\b",
        r"\bapproved\b",
    ]

    # Moderate success signals (medium confidence)
    SUCCESS_MODERATE = [
        r"\bthanks?\b",
        r"\bthank\s+you\b",
        r"\bgot\s+it\b",
        r"\bmakes\s+sense\b",
        r"\bi\s+see\b",
        r"\bunderstood?\b",
        r"\bhelpful\b",
        r"\bnice\b",
        r"\bcool\b",
        r"\bgood\b",
    ]

    # Strong failure signals (high confidence)
    FAILURE_STRONG = [
        r"\b(doesn't|does\s+not|didn't|did\s+not)\s+work\b",
        r"\b(still|keeps?)\s+(broken|failing|error)\b",
        r"\bwrong\s+(answer|output|result)\b",
        r"\bthat's\s+(not|wrong|incorrect)\b",
        r"\bcompletely\s+wrong\b",
        r"\bno,?\s+that's\s+not\b",
        r"\btry\s+again\b",
        r"\bstart\s+over\b",
        r"\bforget\s+(it|that)\b",
        r"\bnever\s*mind\b",
        r"\brollback\b",
        r"\brevert(ed|ing)?\b",
        r"\bbroken\b",
        r"\bcrash(es|ed|ing)?\b",
    ]

    # Moderate failure signals (medium confidence)
    FAILURE_MODERATE = [
        r"\bnot\s+quite\b",
        r"\balmost\b.*\bbut\b",
        r"\bclose\b.*\bbut\b",
        r"\berror\b",
        r"\bfail(ed|ing|s)?\b",
        r"\bissue\b",
        r"\bproblem\b",
        r"\bbug\b",
    ]

    # Partial success signals
    PARTIAL = [
        r"\bpartially\s+work\b",
        r"\bmostly\s+(work|good|correct)\b",
        r"\balmost\s+(there|perfect|right)\b",
        r"\bgood\s+start\b",
        r"\bon\s+the\s+right\s+track\b",
        r"\bjust\s+(need|one\s+more|missing)\b",
        r"\bclose\s+(enough|to)\b",
        r"\bwith\s+one\s+(exception|change|tweak)\b",
        r"\bminor\s+(issue|fix|change)\b",
    ]


class OutcomeInferenceEngine:
    """
    Hybrid outcome inference engine.

    Pipeline:
    1. Check high-confidence keyword patterns
    2. If ambiguous, use embedding similarity (if available)
    3. If still uncertain, route to human review
    """

    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.85  # Auto-label without review
    REVIEW_THRESHOLD = 0.6  # Below this, route to human review

    # Reference sentences for embedding similarity
    SUCCESS_REFERENCES = [
        "Thanks, that worked perfectly!",
        "Great solution, problem solved.",
        "Exactly what I needed, shipped it.",
        "Fixed the issue, merging now.",
        "Perfect, that's exactly right.",
    ]

    FAILURE_REFERENCES = [
        "That didn't work, still broken.",
        "Wrong answer, try again.",
        "No, that's not what I wanted.",
        "Error still happening, not fixed.",
        "Completely wrong approach.",
    ]

    PARTIAL_REFERENCES = [
        "Almost there, just need one more thing.",
        "Good start but needs adjustment.",
        "Mostly works with a minor issue.",
        "Close, but not quite right.",
        "On the right track, needs tweaking.",
    ]

    def __init__(self, use_embeddings: bool = True):
        """
        Initialize inference engine.

        Args:
            use_embeddings: Whether to use sentence embeddings for ambiguous cases.
                           Requires sentence-transformers package.
        """
        self.use_embeddings = use_embeddings and EMBEDDINGS_AVAILABLE
        self._embedding_model = None
        self._reference_embeddings = None

        # Compile regex patterns for performance
        self._compiled_patterns = {
            "success_strong": [
                re.compile(p, re.IGNORECASE) for p in KeywordPatterns.SUCCESS_STRONG
            ],
            "success_moderate": [
                re.compile(p, re.IGNORECASE) for p in KeywordPatterns.SUCCESS_MODERATE
            ],
            "failure_strong": [
                re.compile(p, re.IGNORECASE) for p in KeywordPatterns.FAILURE_STRONG
            ],
            "failure_moderate": [
                re.compile(p, re.IGNORECASE) for p in KeywordPatterns.FAILURE_MODERATE
            ],
            "partial": [re.compile(p, re.IGNORECASE) for p in KeywordPatterns.PARTIAL],
        }

    def _get_embedding_model(self):
        """Lazy load embedding model."""
        if self._embedding_model is None and self.use_embeddings:
            # Use a small, fast model (~80MB)
            self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

            # Pre-compute reference embeddings
            self._reference_embeddings = {
                "success": self._embedding_model.encode(self.SUCCESS_REFERENCES),
                "failure": self._embedding_model.encode(self.FAILURE_REFERENCES),
                "partial": self._embedding_model.encode(self.PARTIAL_REFERENCES),
            }
        return self._embedding_model

    def _match_patterns(self, text: str) -> Dict[str, List[str]]:
        """Match text against all keyword patterns."""
        matches = {
            "success_strong": [],
            "success_moderate": [],
            "failure_strong": [],
            "failure_moderate": [],
            "partial": [],
        }

        for category, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    matches[category].append(match.group())

        return matches

    def _keyword_inference(
        self, text: str
    ) -> Tuple[Optional[OutcomeInference], Dict[str, List[str]]]:
        """
        Attempt inference using keyword patterns.

        Returns:
            Tuple of (inference_result or None, pattern_matches)
        """
        matches = self._match_patterns(text)

        # Count weighted signals
        scores = {
            "success": len(matches["success_strong"]) * 1.0
            + len(matches["success_moderate"]) * 0.4,
            "failure": len(matches["failure_strong"]) * 1.0
            + len(matches["failure_moderate"]) * 0.4,
            "partial": len(matches["partial"]) * 0.8,
        }

        total_signals = sum(scores.values())

        if total_signals == 0:
            return None, matches  # No keyword signals, try embedding

        # Determine winner
        max_category = max(scores, key=scores.get)
        max_score = scores[max_category]

        # Check for conflicting signals
        conflict_score = sum(s for cat, s in scores.items() if cat != max_category)

        if conflict_score > 0.5 * max_score:
            # Conflicting signals - low confidence
            confidence = 0.5
        elif max_category == "success" and matches["success_strong"]:
            confidence = min(0.95, 0.75 + len(matches["success_strong"]) * 0.1)
        elif max_category == "failure" and matches["failure_strong"]:
            confidence = min(0.95, 0.75 + len(matches["failure_strong"]) * 0.1)
        else:
            confidence = min(0.75, 0.5 + max_score * 0.15)

        status_map = {
            "success": OutcomeStatus.SUCCESS,
            "failure": OutcomeStatus.FAILURE,
            "partial": OutcomeStatus.PARTIAL,
        }

        all_matches = []
        for match_list in matches.values():
            all_matches.extend(match_list)

        return (
            OutcomeInference(
                status=status_map[max_category],
                confidence=confidence,
                method="keyword",
                signals=all_matches,
                needs_review=confidence < self.HIGH_CONFIDENCE_THRESHOLD,
                raw_scores=scores,
            ),
            matches,
        )

    def _embedding_inference(self, text: str) -> Optional[OutcomeInference]:
        """
        Attempt inference using sentence embeddings.

        Compares semantic similarity to reference success/failure sentences.
        """
        if not self.use_embeddings:
            return None

        model = self._get_embedding_model()
        if model is None:
            return None

        # Encode input text
        text_embedding = model.encode([text])[0]

        # Compute similarities to each category
        scores = {}
        for category, ref_embeddings in self._reference_embeddings.items():
            # Cosine similarity to each reference
            similarities = np.dot(ref_embeddings, text_embedding) / (
                np.linalg.norm(ref_embeddings, axis=1) * np.linalg.norm(text_embedding)
            )
            # Take max similarity (closest reference)
            scores[category] = float(np.max(similarities))

        # Determine winner
        max_category = max(scores, key=scores.get)
        max_score = scores[max_category]

        # Convert similarity to confidence
        # Similarity range is typically 0.3-0.8 for relevant text
        if max_score < 0.4:
            return None  # Too ambiguous

        confidence = min(0.9, (max_score - 0.3) * 1.5)

        # Check for ambiguity (close second place)
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] - sorted_scores[1] < 0.1:
            confidence *= 0.7  # Reduce confidence for ambiguous cases

        status_map = {
            "success": OutcomeStatus.SUCCESS,
            "failure": OutcomeStatus.FAILURE,
            "partial": OutcomeStatus.PARTIAL,
        }

        return OutcomeInference(
            status=status_map[max_category],
            confidence=confidence,
            method="embedding",
            signals=[f"semantic_similarity_{max_category}={max_score:.3f}"],
            needs_review=confidence < self.HIGH_CONFIDENCE_THRESHOLD,
            raw_scores=scores,
        )

    def infer_outcome(
        self,
        follow_up_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> OutcomeInference:
        """
        Infer outcome from a follow-up message.

        Args:
            follow_up_message: The user's follow-up message after receiving a suggestion.
            context: Optional context (e.g., time since suggestion, conversation history).

        Returns:
            OutcomeInference with status, confidence, and whether human review is needed.
        """
        text = follow_up_message.strip()

        if not text:
            return OutcomeInference(
                status=OutcomeStatus.UNCERTAIN,
                confidence=0.0,
                method="empty",
                signals=[],
                needs_review=True,
                raw_scores={},
            )

        # Step 1: Try keyword patterns (fast, high precision)
        keyword_result, matches = self._keyword_inference(text)

        if (
            keyword_result
            and keyword_result.confidence >= self.HIGH_CONFIDENCE_THRESHOLD
        ):
            # High confidence keyword match - use it
            return keyword_result

        # Step 2: Try embedding similarity (slower, handles nuance)
        embedding_result = self._embedding_inference(text)

        # Step 3: Combine results
        if keyword_result and embedding_result:
            # Both methods have results - combine them
            if keyword_result.status == embedding_result.status:
                # Agreement - boost confidence
                combined_confidence = min(
                    0.95,
                    keyword_result.confidence * 0.6 + embedding_result.confidence * 0.5,
                )
                return OutcomeInference(
                    status=keyword_result.status,
                    confidence=combined_confidence,
                    method="keyword+embedding",
                    signals=keyword_result.signals + embedding_result.signals,
                    needs_review=combined_confidence < self.HIGH_CONFIDENCE_THRESHOLD,
                    raw_scores={
                        "keyword": keyword_result.raw_scores,
                        "embedding": embedding_result.raw_scores,
                    },
                )
            else:
                # Disagreement - use higher confidence one, but flag for review
                winner = (
                    keyword_result
                    if keyword_result.confidence > embedding_result.confidence
                    else embedding_result
                )
                return OutcomeInference(
                    status=winner.status,
                    confidence=winner.confidence * 0.8,  # Reduce due to disagreement
                    method=f"{winner.method}(disputed)",
                    signals=keyword_result.signals + embedding_result.signals,
                    needs_review=True,  # Always review disagreements
                    raw_scores={
                        "keyword": keyword_result.raw_scores,
                        "embedding": embedding_result.raw_scores,
                    },
                )

        elif keyword_result:
            return keyword_result

        elif embedding_result:
            return embedding_result

        else:
            # Neither method could classify - route to human review
            return OutcomeInference(
                status=OutcomeStatus.UNCERTAIN,
                confidence=0.0,
                method="none",
                signals=[],
                needs_review=True,
                raw_scores={},
            )

    def infer_from_behavioral_signals(
        self,
        time_to_next_message_seconds: Optional[float] = None,
        next_message_is_new_topic: Optional[bool] = None,
        user_implemented_suggestion: Optional[bool] = None,
        edit_distance_ratio: Optional[float] = None,
    ) -> Optional[OutcomeInference]:
        """
        Infer outcome from behavioral signals (implicit feedback).

        Args:
            time_to_next_message_seconds: Time until user's next message.
            next_message_is_new_topic: Whether next message is a new topic (topic shift = done).
            user_implemented_suggestion: Whether user's code shows the suggestion was used.
            edit_distance_ratio: How much user modified the suggestion (0 = used as-is).

        Returns:
            OutcomeInference or None if insufficient signals.
        """
        signals = []
        positive_score = 0.0
        negative_score = 0.0

        # Quick topic shift often means success (user moved on)
        if next_message_is_new_topic is True:
            signals.append("topic_shift")
            positive_score += 0.3

        # User implemented the suggestion
        if user_implemented_suggestion is True:
            signals.append("suggestion_implemented")
            positive_score += 0.5
        elif user_implemented_suggestion is False:
            signals.append("suggestion_not_implemented")
            negative_score += 0.3

        # Edit distance (low = used as-is = success)
        if edit_distance_ratio is not None:
            if edit_distance_ratio < 0.1:
                signals.append(f"low_edit_distance={edit_distance_ratio:.2f}")
                positive_score += 0.4
            elif edit_distance_ratio > 0.5:
                signals.append(f"high_edit_distance={edit_distance_ratio:.2f}")
                negative_score += 0.2

        # Very quick follow-up often means problem
        if time_to_next_message_seconds is not None:
            if time_to_next_message_seconds < 10:
                signals.append("very_quick_followup")
                negative_score += 0.2
            elif time_to_next_message_seconds > 300:
                signals.append("delayed_followup")
                # Ambiguous - could be either

        if not signals:
            return None

        total = positive_score + negative_score
        if total < 0.3:
            return None  # Insufficient signal strength

        if positive_score > negative_score * 1.5:
            status = OutcomeStatus.SUCCESS
            confidence = min(0.75, positive_score / (total + 0.5))
        elif negative_score > positive_score * 1.5:
            status = OutcomeStatus.FAILURE
            confidence = min(0.75, negative_score / (total + 0.5))
        else:
            status = OutcomeStatus.PARTIAL
            confidence = 0.5

        return OutcomeInference(
            status=status,
            confidence=confidence,
            method="behavioral",
            signals=signals,
            needs_review=True,  # Behavioral always needs review (implicit)
            raw_scores={"positive": positive_score, "negative": negative_score},
        )


# Singleton for easy import
_default_engine: Optional[OutcomeInferenceEngine] = None


def get_inference_engine(use_embeddings: bool = True) -> OutcomeInferenceEngine:
    """Get or create the default inference engine."""
    global _default_engine
    if _default_engine is None:
        _default_engine = OutcomeInferenceEngine(use_embeddings=use_embeddings)
    return _default_engine


def infer_outcome(message: str, **kwargs) -> OutcomeInference:
    """Convenience function to infer outcome from a message."""
    engine = get_inference_engine()
    return engine.infer_outcome(message, **kwargs)
