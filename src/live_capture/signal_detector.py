#!/usr/bin/env python3
"""
Signal Detector - Capture Enhancement
======================================

Detects "next-state signals" from conversations - implicit feedback that reveals
whether AI responses were helpful.

Signal Types:
- Correction: "no", "that's wrong", "actually" - Negative signal
- Re-query: Similar question repeated - Negative signal
- Refinement: "can you also", "what about" - Positive signal (response was good)
- Acceptance: Topic change, "thanks", "perfect" - Positive signal (task completed)
- Abandonment: Abrupt topic switch, session end - Negative signal
- Code execution: User runs suggested code - Positive signal
- Soft rejection: User ignores assistant response entirely - Negative signal
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Represents a detected signal from a message."""

    signal_type: str  # correction|requery|refinement|acceptance|abandonment|soft_rejection|neutral
    confidence: float  # 0.0 to 1.0
    references_previous: bool  # Whether message references previous context
    sentiment_delta: float  # -1.0 to 1.0 change from previous
    matched_phrases: List[str]  # Phrases that triggered detection
    similarity_score: Optional[float] = None  # For re-query detection

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "signal_type": self.signal_type,
            "confidence": round(self.confidence, 3),
            "references_previous": self.references_previous,
            "sentiment_delta": round(self.sentiment_delta, 3),
            "matched_phrases": self.matched_phrases,
            "similarity_score": (
                round(self.similarity_score, 3) if self.similarity_score else None
            ),
        }


@dataclass
class SessionSignals:
    """Aggregated signals for a session."""

    correction_count: int = 0
    requery_count: int = 0
    refinement_count: int = 0
    acceptance_count: int = 0
    abandonment_detected: bool = False
    soft_rejection_count: int = 0
    total_signals: int = 0
    correction_rate: float = 0.0
    acceptance_rate: float = 0.0
    net_sentiment: float = 0.0
    inferred_reward: float = 0.5  # 0.0 (bad) to 1.0 (good)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for capsule payload."""
        return {
            "correction_count": self.correction_count,
            "requery_count": self.requery_count,
            "refinement_count": self.refinement_count,
            "acceptance_count": self.acceptance_count,
            "abandonment_detected": self.abandonment_detected,
            "soft_rejection_count": self.soft_rejection_count,
            "correction_rate": round(self.correction_rate, 3),
            "acceptance_rate": round(self.acceptance_rate, 3),
            "net_sentiment": round(self.net_sentiment, 3),
            "inferred_reward": round(self.inferred_reward, 3),
        }


class SignalDetector:
    """
    Detects implicit feedback signals from conversation messages.

    These signals provide implicit feedback about AI response quality
    without requiring explicit user ratings.
    """

    # Correction phrases indicate the previous response was wrong
    CORRECTION_PHRASES = [
        "no,",
        "no that's",
        "that's wrong",
        "that's not right",
        "that's incorrect",
        "actually,",
        "actually no",
        "not what i meant",
        "not what i asked",
        "incorrect",
        "you're wrong",
        "that's not correct",
        "i said",
        "i meant",
        "i asked",
        "i was asking",
        "you misunderstood",
        "that doesn't work",
        "that didn't work",
        "still not working",
        "still broken",
        "nope",
        "wrong",
        "not that",
        "no i",
        "thats not",
        "that's not",
        "fix that",
        "fix this",
        "fix it",
        "change that",
        "redo that",
        "try again",
        "do it again",
        "not quite",
        "almost but",
        "close but",
    ]

    # Regex patterns for corrections that can't be caught by substring matching.
    # These detect structural signals: leading negation, restating intent, etc.
    CORRECTION_PATTERNS = [
        # Starts with bare "n" or "no" as first word (shorthand negation)
        r"^n\s",
        r"^no\s",
        r"^no$",
        # "i asked about X" / "i said X" / "i meant X" pattern
        r"^i\s+(asked|said|meant|was\s+asking|was\s+talking)\b",
        # "its X" / "it's X" as a flat correction (supplying the right answer)
        r"^it(?:'?s|s)\s+(?:a|an|the|not)\b",
        # Starts with "not" as a correction
        r"^not\s+(?:that|what|the|this)\b",
        # "X, not Y" correction pattern
        r"\bnot\s+(?:that|what|the)\b.*\bi\b",
        # Very short message after context (< 6 words, contains a noun) — likely terse correction
        # Handled separately in _detect_terse_correction
    ]

    # Acceptance phrases indicate the response was helpful
    ACCEPTANCE_PHRASES = [
        "perfect",
        "thanks",
        "thank you",
        "that works",
        "that worked",
        "great",
        "exactly",
        "yes, that's",
        "yes that's",
        "awesome",
        "excellent",
        "nice",
        "cool",
        "looks good",
        "this works",
        "working now",
        "it works",
        "fixed",
        "solved",
        "got it",
        "makes sense",
        "do it",
        "go ahead",
        "sounds good",
        "lets go",
        "let's go",
        "go for it",
        "ship it",
        "lgtm",
    ]

    # Acceptance patterns that need word-boundary matching (short words that
    # would false-positive as substrings — "yes" in "yesterday", etc.)
    ACCEPTANCE_PATTERNS = [
        r"^yes\b",
        r"^yep\b",
        r"^yeah\b",
        r"^yea\b",
        r"^sure\b",
        r"^ok\b",
        r"^okay\b",
        r"^right\b",
        r"^done\b",
    ]

    # Refinement phrases indicate the response was good but user wants more
    REFINEMENT_PHRASES = [
        "can you also",
        "what about",
        "how about",
        "additionally",
        "and also",
        "one more thing",
        "another thing",
        "also,",
        "now can you",
        "next,",
        "now let's",
        "now I want",
        "can we also",
        "what if we",
        "let's also",
        "building on that",
    ]

    # Abandonment indicators - suggest user gave up
    ABANDONMENT_PHRASES = [
        "never mind",
        "nevermind",
        "forget it",
        "i'll figure it out",
        "i'll do it myself",
        "let me try something else",
        "this isn't working",
        "let's move on",
        "skip this",
        "forget about",
    ]

    # Code execution indicators - user trusted and ran the code
    CODE_EXECUTION_PHRASES = [
        "i ran",
        "i tried",
        "when i run",
        "output is",
        "the output",
        "it prints",
        "it shows",
        "i get this error",
        "i see this",
        "after running",
        "executed",
    ]

    # Positive sentiment words
    POSITIVE_WORDS = {
        "good",
        "great",
        "excellent",
        "perfect",
        "awesome",
        "nice",
        "thanks",
        "helpful",
        "clear",
        "understand",
        "works",
        "working",
        "fixed",
        "solved",
        "love",
        "appreciate",
    }

    # Negative sentiment words
    NEGATIVE_WORDS = {
        "bad",
        "wrong",
        "incorrect",
        "error",
        "broken",
        "fail",
        "failed",
        "doesn't",
        "didn't",
        "can't",
        "won't",
        "confused",
        "unclear",
        "confusing",
        "frustrated",
        "annoying",
    }

    def __init__(self, similarity_threshold: float = 0.5):
        """
        Initialize the signal detector.

        Args:
            similarity_threshold: Threshold for re-query detection (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold

    def detect_signal(
        self,
        current_msg: str,
        previous_msgs: List[str] = None,
        role: str = "user",
        previous_assistant_response: Optional[str] = None,
    ) -> Signal:
        """
        Detect the signal from a message.

        Args:
            current_msg: The current message to analyze
            previous_msgs: Previous messages for context and similarity
            role: 'user' or 'assistant'

        Returns:
            Signal with detected signal type and metadata
        """
        # Only analyze user messages for signals (they respond to assistant)
        if role != "user":
            return Signal(
                signal_type="neutral",
                confidence=0.0,
                references_previous=False,
                sentiment_delta=0.0,
                matched_phrases=[],
            )

        msg_lower = current_msg.lower().strip()
        matched_phrases = []

        # Check for correction (phrases)
        correction_match, correction_phrases = self._check_phrases(
            msg_lower, self.CORRECTION_PHRASES
        )
        if correction_match:
            matched_phrases.extend(correction_phrases)
            return Signal(
                signal_type="correction",
                confidence=min(0.9, 0.6 + len(correction_phrases) * 0.15),
                references_previous=True,
                sentiment_delta=-0.5,
                matched_phrases=correction_phrases,
            )

        # Check for correction (regex patterns)
        pattern_match = self._check_correction_patterns(msg_lower)
        if pattern_match:
            return Signal(
                signal_type="correction",
                confidence=0.7,
                references_previous=True,
                sentiment_delta=-0.4,
                matched_phrases=[pattern_match],
            )

        # Check for terse correction (very short message that restates/redirects)
        terse = self._detect_terse_correction(msg_lower, previous_msgs or [])
        if terse:
            return Signal(
                signal_type="correction",
                confidence=0.6,
                references_previous=True,
                sentiment_delta=-0.3,
                matched_phrases=[terse],
            )

        # Check for abandonment
        abandonment_match, abandonment_phrases = self._check_phrases(
            msg_lower, self.ABANDONMENT_PHRASES
        )
        if abandonment_match:
            matched_phrases.extend(abandonment_phrases)
            return Signal(
                signal_type="abandonment",
                confidence=0.8,
                references_previous=True,
                sentiment_delta=-0.7,
                matched_phrases=abandonment_phrases,
            )

        # Check for acceptance (phrases)
        acceptance_match, acceptance_phrases = self._check_phrases(
            msg_lower, self.ACCEPTANCE_PHRASES
        )
        if acceptance_match:
            matched_phrases.extend(acceptance_phrases)
            return Signal(
                signal_type="acceptance",
                confidence=min(0.95, 0.7 + len(acceptance_phrases) * 0.1),
                references_previous=True,
                sentiment_delta=0.6,
                matched_phrases=acceptance_phrases,
            )

        # Check for acceptance (regex patterns — short affirmative words)
        acceptance_pattern = self._check_acceptance_patterns(msg_lower)
        if acceptance_pattern:
            return Signal(
                signal_type="acceptance",
                confidence=0.75,
                references_previous=True,
                sentiment_delta=0.5,
                matched_phrases=[acceptance_pattern],
            )

        # Check for refinement
        refinement_match, refinement_phrases = self._check_phrases(
            msg_lower, self.REFINEMENT_PHRASES
        )
        if refinement_match:
            matched_phrases.extend(refinement_phrases)
            return Signal(
                signal_type="refinement",
                confidence=0.85,
                references_previous=True,
                sentiment_delta=0.3,
                matched_phrases=refinement_phrases,
            )

        # Check for code execution (positive - user trusted the code)
        code_exec_match, code_exec_phrases = self._check_phrases(
            msg_lower, self.CODE_EXECUTION_PHRASES
        )
        if code_exec_match:
            # Code execution is positive even if user reports an error
            # (they trusted the code enough to try it)
            sentiment = 0.2 if "error" in msg_lower else 0.4
            return Signal(
                signal_type="code_execution",
                confidence=0.75,
                references_previous=True,
                sentiment_delta=sentiment,
                matched_phrases=code_exec_phrases,
            )

        # Check for re-query (similar question repeated)
        if previous_msgs:
            similarity, similar_msg = self._find_similar_message(
                msg_lower, previous_msgs
            )
            if similarity >= self.similarity_threshold:
                return Signal(
                    signal_type="requery",
                    confidence=min(0.9, similarity),
                    references_previous=True,
                    sentiment_delta=-0.3,
                    matched_phrases=["similar to previous query"],
                    similarity_score=similarity,
                )
        # Check for soft rejection (user ignores assistant response entirely)
        soft_rejection = self._detect_soft_rejection(
            msg_lower, previous_assistant_response
        )
        if soft_rejection:
            return soft_rejection

        # Calculate general sentiment
        sentiment = self._calculate_sentiment(msg_lower)
        references_previous = self._check_references_previous(msg_lower)

        return Signal(
            signal_type="neutral",
            confidence=0.5,
            references_previous=references_previous,
            sentiment_delta=sentiment,
            matched_phrases=matched_phrases,
        )

    def _detect_soft_rejection(
        self, msg: str, previous_assistant_response: Optional[str]
    ) -> Optional[Signal]:
        """Detect when user ignores the assistant's response entirely."""
        if not previous_assistant_response or len(previous_assistant_response) <= 200:
            return None

        # Must not contain acceptance phrases or patterns
        acceptance_match, _ = self._check_phrases(msg, self.ACCEPTANCE_PHRASES)
        if acceptance_match:
            return None
        if self._check_acceptance_patterns(msg):
            return None

        # Must not reference the assistant's response (0 shared content words)
        stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "need",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "i",
            "me",
            "my",
            "we",
            "our",
            "you",
            "your",
            "it",
            "its",
            "they",
            "them",
            "their",
            "this",
            "that",
            "these",
            "those",
            "and",
            "but",
            "or",
            "so",
            "if",
            "then",
            "than",
            "when",
            "what",
            "which",
            "who",
            "how",
            "why",
            "where",
            "not",
            "no",
            "yes",
            "just",
            "also",
            "very",
            "too",
            "any",
            "all",
        }
        msg_words = set(re.findall(r"\b\w{3,}\b", msg)) - stopwords
        resp_words = (
            set(re.findall(r"\b\w{3,}\b", previous_assistant_response.lower()))
            - stopwords
        )

        if msg_words & resp_words:
            return None

        # Must look like a new directive/question (not a follow-up)
        follow_up_patterns = [
            r"^(also|additionally|and\b|furthermore|moreover)",
            r"^(building on|following up|regarding|about that)",
        ]
        for pattern in follow_up_patterns:
            if re.search(pattern, msg, re.IGNORECASE):
                return None

        return Signal(
            signal_type="soft_rejection",
            confidence=0.55,
            references_previous=False,
            sentiment_delta=-0.2,
            matched_phrases=["no_reference_to_assistant_response"],
        )

    def _check_phrases(self, msg: str, phrases: List[str]) -> Tuple[bool, List[str]]:
        """Check if message contains any of the given phrases."""
        matched = []
        for phrase in phrases:
            if phrase in msg:
                matched.append(phrase)
        return len(matched) > 0, matched

    def _check_correction_patterns(self, msg: str) -> Optional[str]:
        """Check regex-based correction patterns. Returns matched pattern or None."""
        for pattern in self.CORRECTION_PATTERNS:
            if re.search(pattern, msg, re.IGNORECASE):
                return f"pattern:{pattern}"
        return None

    def _check_acceptance_patterns(self, msg: str) -> Optional[str]:
        """Check regex-based acceptance patterns. Returns matched pattern or None."""
        for pattern in self.ACCEPTANCE_PATTERNS:
            if re.search(pattern, msg, re.IGNORECASE):
                return f"pattern:{pattern}"
        return None

    def _detect_terse_correction(
        self, msg: str, previous_msgs: List[str]
    ) -> Optional[str]:
        """Detect terse corrections: very short messages that supply missing context.

        When a user sends a short factual statement (< 8 words) right after the
        assistant gave a long response, it's often a correction or clarification
        rather than a new topic. Examples:
            "its a file locally"
            "the port is 3000"
            "i mean the other one"
            "python not javascript"
        """
        if not previous_msgs:
            return None

        words = msg.split()
        word_count = len(words)

        # Only applies to short messages (2-7 words)
        if word_count < 2 or word_count > 7:
            return None

        # Must not match acceptance or refinement patterns (those take priority later)
        acceptance_check, _ = self._check_phrases(msg, self.ACCEPTANCE_PHRASES)
        if acceptance_check:
            return None
        refinement_check, _ = self._check_phrases(msg, self.REFINEMENT_PHRASES)
        if refinement_check:
            return None

        # Check if the short message shares content words with the previous user
        # message — if so, the user is restating/correcting, not starting fresh.
        filler = {
            "the",
            "and",
            "but",
            "for",
            "are",
            "was",
            "not",
            "you",
            "all",
            "can",
            "had",
            "her",
            "his",
            "him",
            "how",
            "its",
            "let",
            "may",
            "our",
            "out",
            "own",
            "say",
            "she",
            "too",
            "use",
            "has",
            "any",
            "who",
            "did",
            "get",
            "got",
            "now",
            "old",
            "see",
            "way",
            "day",
            "hot",
            "oil",
            "sit",
            "top",
            "ask",
            "big",
            "bit",
            "end",
            "far",
            "few",
            "put",
            "run",
            "set",
            "try",
            "why",
            "off",
            "yet",
            "also",
            "back",
            "been",
            "call",
            "came",
            "each",
            "even",
            "from",
            "give",
            "goes",
            "gone",
            "good",
            "have",
            "here",
            "high",
            "into",
            "just",
            "keep",
            "know",
            "last",
            "long",
            "look",
            "made",
            "make",
            "many",
            "more",
            "most",
            "much",
            "must",
            "name",
            "need",
            "only",
            "over",
            "part",
            "said",
            "same",
            "show",
            "some",
            "such",
            "take",
            "tell",
            "than",
            "that",
            "them",
            "then",
            "they",
            "this",
            "time",
            "turn",
            "upon",
            "very",
            "want",
            "well",
            "went",
            "what",
            "when",
            "will",
            "with",
            "word",
            "work",
            "year",
            "your",
            "does",
            "like",
            "about",
            "which",
            "would",
            "could",
            "should",
            "there",
            "their",
            "these",
            "those",
            "where",
            "being",
            "other",
            "after",
            "still",
            "think",
        }
        last_user = previous_msgs[-1].lower() if previous_msgs else ""
        msg_words = set(re.findall(r"\b\w{3,}\b", msg)) - filler
        prev_words = set(re.findall(r"\b\w{3,}\b", last_user)) - filler

        shared = msg_words & prev_words
        if shared and len(shared) >= 1:
            return f"terse_restatement:{','.join(sorted(shared))}"

        return None

    def _calculate_sentiment(self, msg: str) -> float:
        """
        Calculate sentiment score from -1.0 to 1.0.

        Uses simple word-based sentiment analysis.
        """
        words = set(re.findall(r"\b\w+\b", msg.lower()))

        positive_count = len(words & self.POSITIVE_WORDS)
        negative_count = len(words & self.NEGATIVE_WORDS)

        total = positive_count + negative_count
        if total == 0:
            return 0.0

        # Normalize to -1.0 to 1.0 range
        sentiment = (positive_count - negative_count) / total
        return max(-1.0, min(1.0, sentiment))

    def _check_references_previous(self, msg: str) -> bool:
        """Check if message references previous context."""
        reference_patterns = [
            r"\bthat\b",
            r"\bthis\b",
            r"\bit\b",
            r"\bthe\s+(code|solution|approach|method|function)\b",
            r"\byour\s+(suggestion|answer|response|code)\b",
            r"\babove\b",
            r"\bprevious\b",
            r"\bearlier\b",
        ]

        for pattern in reference_patterns:
            if re.search(pattern, msg, re.IGNORECASE):
                return True
        return False

    def calculate_similarity(self, msg1: str, msg2: str) -> float:
        """
        Calculate cosine similarity between two messages using word overlap.

        This is a simple TF-based approach without external dependencies.
        """
        # Tokenize
        words1 = set(re.findall(r"\b\w+\b", msg1.lower()))
        words2 = set(re.findall(r"\b\w+\b", msg2.lower()))

        # Remove common stopwords
        stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "need",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "i",
            "me",
            "my",
            "we",
            "our",
            "you",
            "your",
            "it",
            "its",
            "they",
            "them",
            "their",
            "this",
            "that",
            "these",
            "those",
            "and",
            "but",
            "or",
            "so",
            "if",
            "then",
            "than",
            "when",
            "what",
            "which",
            "who",
            "how",
            "why",
            "where",
        }

        words1 = words1 - stopwords
        words2 = words2 - stopwords

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity (intersection over union)
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _find_similar_message(
        self, current_msg: str, previous_msgs: List[str]
    ) -> Tuple[float, Optional[str]]:
        """Find the most similar previous message."""
        max_similarity = 0.0
        most_similar = None

        for prev_msg in previous_msgs:
            similarity = self.calculate_similarity(current_msg, prev_msg)
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar = prev_msg

        return max_similarity, most_similar

    def detect_sentiment_shift(
        self, messages: List[str], window_size: int = 3
    ) -> float:
        """
        Detect sentiment shift across a sequence of messages.

        Returns the change in sentiment from the start to end of the window.
        Positive values indicate improving sentiment, negative indicates declining.
        """
        if len(messages) < 2:
            return 0.0

        # Calculate sentiment for each message
        sentiments = [self._calculate_sentiment(msg) for msg in messages]

        # Compare recent window to earlier window
        recent_msgs = (
            sentiments[-window_size:] if len(sentiments) >= window_size else sentiments
        )
        earlier_msgs = (
            sentiments[:window_size] if len(sentiments) >= window_size else sentiments
        )

        recent_avg = sum(recent_msgs) / len(recent_msgs) if recent_msgs else 0.0
        earlier_avg = sum(earlier_msgs) / len(earlier_msgs) if earlier_msgs else 0.0

        return recent_avg - earlier_avg

    def aggregate_session_signals(self, signals: List[Signal]) -> SessionSignals:
        """
        Aggregate individual signals into session-level metrics.

        Args:
            signals: List of Signal objects from the session

        Returns:
            SessionSignals with aggregated metrics
        """
        session = SessionSignals()

        if not signals:
            return session

        for signal in signals:
            session.total_signals += 1 if signal.signal_type != "neutral" else 0

            if signal.signal_type == "correction":
                session.correction_count += 1
            elif signal.signal_type == "requery":
                session.requery_count += 1
            elif signal.signal_type == "refinement":
                session.refinement_count += 1
            elif signal.signal_type == "acceptance":
                session.acceptance_count += 1
            elif signal.signal_type == "abandonment":
                session.abandonment_detected = True
            elif signal.signal_type == "soft_rejection":
                session.soft_rejection_count += 1

        # Calculate rates
        total_user_msgs = len(signals)
        if total_user_msgs > 0:
            session.correction_rate = (
                session.correction_count + session.requery_count
            ) / total_user_msgs
            session.acceptance_rate = (
                session.acceptance_count + session.refinement_count
            ) / total_user_msgs

        # Calculate net sentiment
        sentiment_sum = sum(s.sentiment_delta for s in signals)
        session.net_sentiment = sentiment_sum / len(signals) if signals else 0.0

        # Calculate inferred reward
        # Higher acceptance/refinement = higher reward
        # Higher correction/requery/abandonment = lower reward
        positive_signals = session.acceptance_count + session.refinement_count
        negative_signals = (
            session.correction_count
            + session.requery_count
            + (1 if session.abandonment_detected else 0)
            + session.soft_rejection_count
        )

        if positive_signals + negative_signals > 0:
            session.inferred_reward = positive_signals / (
                positive_signals + negative_signals
            )
        else:
            # No strong signals - use sentiment as fallback
            session.inferred_reward = (session.net_sentiment + 1.0) / 2.0

        return session


# Global detector instance
_detector = SignalDetector()


def detect_signal(
    current_msg: str,
    previous_msgs: List[str] = None,
    role: str = "user",
    previous_assistant_response: str = None,
) -> Signal:
    """Convenience function to detect signal using global detector."""
    return _detector.detect_signal(
        current_msg, previous_msgs, role, previous_assistant_response
    )


def aggregate_signals(signals: List[Signal]) -> SessionSignals:
    """Convenience function to aggregate signals using global detector."""
    return _detector.aggregate_session_signals(signals)


if __name__ == "__main__":
    # Test the detector
    print("Signal Detector - Test Suite\n")

    detector = SignalDetector()

    # Test cases
    test_cases = [
        ("No, that's wrong. I meant something else.", "correction"),
        ("Perfect, thanks! That works great.", "acceptance"),
        ("Can you also add error handling?", "refinement"),
        ("Never mind, I'll figure it out myself.", "abandonment"),
        ("I ran the code and it shows this output:", "code_execution"),
        ("Help me implement a function", "neutral"),
        ("This is terrible, nothing works", "neutral"),  # negative but not correction
    ]

    for msg, expected in test_cases:
        signal = detector.detect_signal(msg, [], "user")
        status = "[OK]" if signal.signal_type == expected else "[FAIL]"
        print(f"{status} '{msg[:50]}...'")
        print(f"    Expected: {expected}, Got: {signal.signal_type}")
        print(
            f"    Confidence: {signal.confidence:.2f}, Sentiment: {signal.sentiment_delta:.2f}"
        )
        print()

    # Test similarity detection
    print("\n--- Re-query Detection Test ---")
    prev = ["How do I implement a binary search tree?"]
    current = "How do I create a binary search tree in Python?"
    signal = detector.detect_signal(current, prev, "user")
    print(f"Previous: {prev[0]}")
    print(f"Current: {current}")
    print(f"Signal: {signal.signal_type}, Similarity: {signal.similarity_score}")
