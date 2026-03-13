"""
Unit tests for Signal Detector - Capture Enhancement.

Tests signal detection for implicit feedback from conversations:
- Correction signals (negative)
- Acceptance signals (positive)
- Refinement signals (positive)
- Abandonment signals (negative)
- Re-query detection via similarity
- Sentiment shift calculation
- Session signal aggregation
"""

import pytest

from src.live_capture.signal_detector import (
    SessionSignals,
    Signal,
    SignalDetector,
    aggregate_signals,
    detect_signal,
)


class TestSignal:
    """Tests for Signal dataclass."""

    def test_create_signal(self):
        """Test creating an signal."""
        signal = Signal(
            signal_type="correction",
            confidence=0.85,
            references_previous=True,
            sentiment_delta=-0.5,
            matched_phrases=["that's wrong"],
        )

        assert signal.signal_type == "correction"
        assert signal.confidence == 0.85
        assert signal.references_previous is True
        assert signal.sentiment_delta == -0.5
        assert "that's wrong" in signal.matched_phrases

    def test_to_dict(self):
        """Test converting signal to dict."""
        signal = Signal(
            signal_type="acceptance",
            confidence=0.9,
            references_previous=True,
            sentiment_delta=0.6,
            matched_phrases=["thanks", "perfect"],
            similarity_score=0.75,
        )

        result = signal.to_dict()

        assert result["signal_type"] == "acceptance"
        assert result["confidence"] == 0.9
        assert result["references_previous"] is True
        assert result["sentiment_delta"] == 0.6
        assert len(result["matched_phrases"]) == 2
        assert result["similarity_score"] == 0.75


class TestSignalDetectorCorrection:
    """Tests for correction signal detection."""

    def test_detects_no_thats_wrong(self):
        """Test detecting 'no, that's wrong' correction."""
        detector = SignalDetector()
        signal = detector.detect_signal("No, that's wrong. I meant X.", [], "user")

        assert signal.signal_type == "correction"
        assert signal.confidence > 0.5
        assert signal.sentiment_delta < 0

    def test_detects_actually_correction(self):
        """Test detecting 'actually' correction."""
        detector = SignalDetector()
        signal = detector.detect_signal(
            "Actually, I need something different.", [], "user"
        )

        assert signal.signal_type == "correction"
        assert signal.references_previous is True

    def test_detects_not_what_i_meant(self):
        """Test detecting 'not what I meant'."""
        detector = SignalDetector()
        signal = detector.detect_signal("That's not what I meant at all.", [], "user")

        assert signal.signal_type == "correction"

    def test_detects_that_didnt_work(self):
        """Test detecting 'that didn't work'."""
        detector = SignalDetector()
        signal = detector.detect_signal(
            "That didn't work, I still get the error.", [], "user"
        )

        assert signal.signal_type == "correction"

    def test_detects_incorrect(self):
        """Test detecting 'incorrect'."""
        detector = SignalDetector()
        signal = detector.detect_signal(
            "Incorrect, the API returns JSON not XML.", [], "user"
        )

        assert signal.signal_type == "correction"


class TestSignalDetectorAcceptance:
    """Tests for acceptance signal detection."""

    def test_detects_perfect(self):
        """Test detecting 'perfect'."""
        detector = SignalDetector()
        signal = detector.detect_signal(
            "Perfect, that's exactly what I needed!", [], "user"
        )

        assert signal.signal_type == "acceptance"
        assert signal.sentiment_delta > 0

    def test_detects_thanks(self):
        """Test detecting 'thanks'."""
        detector = SignalDetector()
        signal = detector.detect_signal("Thanks, this works great!", [], "user")

        assert signal.signal_type == "acceptance"

    def test_detects_that_works(self):
        """Test detecting 'that works'."""
        detector = SignalDetector()
        signal = detector.detect_signal(
            "That works! I can see the output now.", [], "user"
        )

        assert signal.signal_type == "acceptance"

    def test_detects_exactly(self):
        """Test detecting 'exactly'."""
        detector = SignalDetector()
        signal = detector.detect_signal("Exactly what I was looking for.", [], "user")

        assert signal.signal_type == "acceptance"

    def test_detects_looks_good(self):
        """Test detecting 'looks good'."""
        detector = SignalDetector()
        signal = detector.detect_signal("Looks good to me!", [], "user")

        assert signal.signal_type == "acceptance"


class TestSignalDetectorRefinement:
    """Tests for refinement signal detection."""

    def test_detects_can_you_also(self):
        """Test detecting 'can you also'."""
        detector = SignalDetector()
        signal = detector.detect_signal("Can you also add error handling?", [], "user")

        assert signal.signal_type == "refinement"
        assert signal.sentiment_delta > 0  # Positive - response was good

    def test_detects_what_about(self):
        """Test detecting 'what about'."""
        detector = SignalDetector()
        signal = detector.detect_signal("What about the edge cases?", [], "user")

        assert signal.signal_type == "refinement"

    def test_detects_additionally(self):
        """Test detecting 'additionally'."""
        detector = SignalDetector()
        signal = detector.detect_signal(
            "Additionally, can we optimize the loop?", [], "user"
        )

        assert signal.signal_type == "refinement"

    def test_detects_now_lets(self):
        """Test detecting 'now let's'."""
        detector = SignalDetector()
        signal = detector.detect_signal("Now let's add the tests.", [], "user")

        assert signal.signal_type == "refinement"


class TestSignalDetectorAbandonment:
    """Tests for abandonment signal detection."""

    def test_detects_never_mind(self):
        """Test detecting 'never mind'."""
        detector = SignalDetector()
        signal = detector.detect_signal(
            "Never mind, I'll figure it out myself.", [], "user"
        )

        assert signal.signal_type == "abandonment"
        assert signal.sentiment_delta < 0

    def test_detects_forget_it(self):
        """Test detecting 'forget it'."""
        detector = SignalDetector()
        signal = detector.detect_signal(
            "Forget it, this is too complicated.", [], "user"
        )

        assert signal.signal_type == "abandonment"

    def test_detects_skip_this(self):
        """Test detecting 'skip this'."""
        detector = SignalDetector()
        signal = detector.detect_signal("Let's skip this for now.", [], "user")

        assert signal.signal_type == "abandonment"


class TestSignalDetectorCodeExecution:
    """Tests for code execution signal detection."""

    def test_detects_i_ran_the_code(self):
        """Test detecting 'I ran the code'."""
        detector = SignalDetector()
        signal = detector.detect_signal(
            "I ran the code and got this output:", [], "user"
        )

        assert signal.signal_type == "code_execution"
        assert signal.sentiment_delta > 0  # Positive - user trusted the code

    def test_detects_when_i_run(self):
        """Test detecting 'when I run'."""
        detector = SignalDetector()
        signal = detector.detect_signal("When I run the script, it prints:", [], "user")

        assert signal.signal_type == "code_execution"

    def test_code_execution_with_error_still_positive(self):
        """Test code execution with error still shows positive (user trusted it)."""
        detector = SignalDetector()
        signal = detector.detect_signal(
            "I ran it and I get this error: TypeError", [], "user"
        )

        assert signal.signal_type == "code_execution"
        # Still positive sentiment (user trusted code enough to try)
        assert signal.sentiment_delta > 0


class TestSignalDetectorRequery:
    """Tests for re-query detection via similarity."""

    def test_detects_similar_question(self):
        """Test detecting a re-query (similar question repeated)."""
        detector = SignalDetector()
        # Use messages that are clearly similar but not identical
        prev_msgs = ["How do I implement a binary search tree in Python?"]
        current = "How do I create a binary search tree in Python please?"

        signal = detector.detect_signal(current, prev_msgs, "user")

        assert signal.signal_type == "requery"
        assert signal.similarity_score is not None
        assert signal.similarity_score >= 0.5

    def test_different_question_not_requery(self):
        """Test that different questions are not marked as re-query."""
        detector = SignalDetector()
        prev_msgs = ["How do I implement a binary search tree?"]
        current = "What is the best database for this project?"

        signal = detector.detect_signal(current, prev_msgs, "user")

        assert signal.signal_type != "requery"

    def test_requery_negative_sentiment(self):
        """Test that re-query has negative sentiment (response didn't help)."""
        detector = SignalDetector()
        prev_msgs = ["How do I fix the error?"]
        current = "How can I fix this error?"

        signal = detector.detect_signal(current, prev_msgs, "user")

        if signal.signal_type == "requery":
            assert signal.sentiment_delta < 0


class TestSignalDetectorNeutral:
    """Tests for neutral signal detection."""

    def test_neutral_question(self):
        """Test that a neutral question returns neutral signal."""
        detector = SignalDetector()
        signal = detector.detect_signal("How do I implement this feature?", [], "user")

        assert signal.signal_type == "neutral"

    def test_assistant_messages_neutral(self):
        """Test that assistant messages always return neutral."""
        detector = SignalDetector()
        signal = detector.detect_signal(
            "Perfect! Here's the solution...", [], "assistant"
        )

        assert signal.signal_type == "neutral"


class TestSignalDetectorSimilarity:
    """Tests for similarity calculation."""

    def test_identical_messages_high_similarity(self):
        """Test that identical messages have high similarity."""
        detector = SignalDetector()
        similarity = detector.calculate_similarity(
            "How do I implement a function?", "How do I implement a function?"
        )

        assert similarity > 0.9

    def test_different_messages_low_similarity(self):
        """Test that different messages have low similarity."""
        detector = SignalDetector()
        similarity = detector.calculate_similarity(
            "How do I implement a function?", "What's the weather like today?"
        )

        assert similarity < 0.3

    def test_similar_messages_moderate_similarity(self):
        """Test that similar messages have moderate similarity."""
        detector = SignalDetector()
        similarity = detector.calculate_similarity(
            "How do I implement a function in Python?",
            "How do I create a function in Python?",
        )

        assert 0.4 < similarity < 0.9


class TestSignalDetectorSentiment:
    """Tests for sentiment calculation."""

    def test_positive_sentiment(self):
        """Test detecting positive sentiment."""
        detector = SignalDetector()
        sentiment = detector._calculate_sentiment("This is great, thanks for the help!")

        assert sentiment > 0

    def test_negative_sentiment(self):
        """Test detecting negative sentiment."""
        detector = SignalDetector()
        sentiment = detector._calculate_sentiment(
            "This is broken and doesn't work at all"
        )

        assert sentiment < 0

    def test_neutral_sentiment(self):
        """Test detecting neutral sentiment."""
        detector = SignalDetector()
        sentiment = detector._calculate_sentiment("Please implement a function")

        # Should be close to 0
        assert -0.3 < sentiment < 0.3


class TestSessionSignalsAggregation:
    """Tests for session-level signal aggregation."""

    def test_aggregate_empty_signals(self):
        """Test aggregating empty signal list."""
        session = aggregate_signals([])

        assert session.correction_count == 0
        assert session.acceptance_count == 0
        assert session.inferred_reward == 0.5  # Default neutral

    def test_aggregate_positive_signals(self):
        """Test aggregating positive signals."""
        signals = [
            Signal("acceptance", 0.9, True, 0.6, ["thanks"]),
            Signal("refinement", 0.8, True, 0.3, ["can you also"]),
            Signal("acceptance", 0.85, True, 0.5, ["perfect"]),
        ]

        session = aggregate_signals(signals)

        assert session.acceptance_count == 2
        assert session.refinement_count == 1
        assert session.inferred_reward > 0.8  # High reward for positive signals

    def test_aggregate_negative_signals(self):
        """Test aggregating negative signals."""
        signals = [
            Signal("correction", 0.85, True, -0.5, ["wrong"]),
            Signal("correction", 0.9, True, -0.6, ["incorrect"]),
            Signal("requery", 0.8, True, -0.3, [], 0.7),
        ]

        session = aggregate_signals(signals)

        assert session.correction_count == 2
        assert session.requery_count == 1
        assert session.inferred_reward < 0.3  # Low reward for negative signals

    def test_aggregate_mixed_signals(self):
        """Test aggregating mixed signals."""
        signals = [
            Signal("acceptance", 0.9, True, 0.6, ["thanks"]),
            Signal("correction", 0.85, True, -0.5, ["wrong"]),
            Signal("refinement", 0.8, True, 0.3, ["also"]),
        ]

        session = aggregate_signals(signals)

        assert session.acceptance_count == 1
        assert session.correction_count == 1
        assert session.refinement_count == 1
        # Mixed signals should result in moderate reward
        assert 0.3 < session.inferred_reward < 0.7

    def test_correction_rate_calculation(self):
        """Test correction rate calculation."""
        signals = [
            Signal("neutral", 0.5, False, 0.0, []),
            Signal("correction", 0.85, True, -0.5, ["wrong"]),
            Signal("neutral", 0.5, False, 0.0, []),
            Signal("neutral", 0.5, False, 0.0, []),
        ]

        session = aggregate_signals(signals)

        # 1 correction out of 4 messages
        assert session.correction_rate == 0.25

    def test_abandonment_detected(self):
        """Test abandonment detection in session."""
        signals = [
            Signal("neutral", 0.5, False, 0.0, []),
            Signal("abandonment", 0.8, True, -0.7, ["never mind"]),
        ]

        session = aggregate_signals(signals)

        assert session.abandonment_detected is True

    def test_session_signals_to_dict(self):
        """Test converting session signals to dict."""
        session = SessionSignals(
            correction_count=2,
            acceptance_count=3,
            refinement_count=1,
            net_sentiment=0.45,
            inferred_reward=0.72,
        )

        result = session.to_dict()

        assert result["correction_count"] == 2
        assert result["acceptance_count"] == 3
        assert result["net_sentiment"] == 0.45
        assert result["inferred_reward"] == 0.72


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_detect_signal_function(self):
        """Test the detect_signal convenience function."""
        signal = detect_signal("Thanks, that works!", [], "user")

        assert signal.signal_type == "acceptance"

    def test_aggregate_signals_function(self):
        """Test the aggregate_signals convenience function."""
        signals = [
            Signal("acceptance", 0.9, True, 0.6, ["thanks"]),
        ]

        session = aggregate_signals(signals)

        assert session.acceptance_count == 1


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_message(self):
        """Test handling empty message."""
        detector = SignalDetector()
        signal = detector.detect_signal("", [], "user")

        assert signal.signal_type == "neutral"

    def test_very_long_message(self):
        """Test handling very long message."""
        detector = SignalDetector()
        long_msg = "word " * 1000 + "thanks"
        signal = detector.detect_signal(long_msg, [], "user")

        assert signal.signal_type == "acceptance"

    def test_case_insensitive_detection(self):
        """Test that detection is case insensitive."""
        detector = SignalDetector()

        signal_lower = detector.detect_signal("thanks!", [], "user")
        signal_upper = detector.detect_signal("THANKS!", [], "user")

        assert signal_lower.signal_type == signal_upper.signal_type

    def test_multiple_signals_priority(self):
        """Test that correction takes priority over acceptance."""
        detector = SignalDetector()
        # Message with both correction and acceptance phrases
        signal = detector.detect_signal(
            "No, that's wrong. Actually, thanks anyway.", [], "user"
        )

        # Correction should take priority
        assert signal.signal_type == "correction"
