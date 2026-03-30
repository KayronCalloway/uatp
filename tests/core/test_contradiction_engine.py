"""
Tests for the Contradiction Engine.

A protocol that can accuse itself is closer to truth.

Tests the self-inspection capabilities:
- Semantic drift detection
- Quality consistency checking
- Confidence-evidence alignment
- Legal label gate verification
"""

import pytest

from src.core.contradiction_engine import (
    Contradiction,
    ContradictionEngine,
    format_contradictions,
)


class TestSemanticDriftDetection:
    """Test semantic drift detection between user request and summary."""

    def test_detects_complete_topic_mismatch(self):
        """Should detect when summary doesn't address user question at all."""
        contradictions = ContradictionEngine.check_semantic_drift(
            last_user_message="How do I fix the authentication bug in login.py?",
            summary="The database uses PostgreSQL with connection pooling.",
        )
        assert len(contradictions) == 1
        assert contradictions[0].category == "semantic_drift"
        assert contradictions[0].severity == "critical"

    def test_no_drift_when_topics_match(self):
        """Should not flag drift when summary addresses the question."""
        contradictions = ContradictionEngine.check_semantic_drift(
            last_user_message="How do I fix the authentication bug?",
            summary="Fixed the authentication bug by updating the password validation logic.",
        )
        assert len(contradictions) == 0

    def test_handles_empty_inputs(self):
        """Should handle empty inputs gracefully."""
        contradictions = ContradictionEngine.check_semantic_drift(
            last_user_message="",
            summary="Some summary",
        )
        assert len(contradictions) == 0

        contradictions = ContradictionEngine.check_semantic_drift(
            last_user_message="Some question",
            summary="",
        )
        assert len(contradictions) == 0

    def test_partial_overlap_not_flagged(self):
        """Should not flag when there's reasonable topic overlap."""
        contradictions = ContradictionEngine.check_semantic_drift(
            last_user_message="Can you help me optimize the database queries?",
            summary="Optimized the database queries by adding indexes and caching.",
        )
        assert len(contradictions) == 0


class TestQualityConsistency:
    """Test quality score consistency checking."""

    def test_detects_high_score_no_evidence(self):
        """Should flag high evidence quality when no evidence provided."""
        contradictions = ContradictionEngine.check_quality_consistency(
            evidence_quality=0.9,
            logical_validity=0.8,
            overall_grade="B",
            has_evidence=False,
        )
        assert len(contradictions) == 1
        assert contradictions[0].category == "quality_mismatch"
        assert contradictions[0].severity == "warning"

    def test_detects_perfect_scores_poor_grade(self):
        """Should flag perfect scores with failing grade."""
        contradictions = ContradictionEngine.check_quality_consistency(
            evidence_quality=1.0,
            logical_validity=1.0,
            overall_grade="F",
            has_evidence=True,
        )
        assert len(contradictions) == 1
        assert contradictions[0].category == "quality_mismatch"
        assert contradictions[0].severity == "critical"

    def test_consistent_scores_not_flagged(self):
        """Should not flag consistent quality scores."""
        contradictions = ContradictionEngine.check_quality_consistency(
            evidence_quality=0.8,
            logical_validity=0.7,
            overall_grade="B",
            has_evidence=True,
        )
        assert len(contradictions) == 0

    def test_handles_none_values(self):
        """Should handle None quality values gracefully."""
        contradictions = ContradictionEngine.check_quality_consistency(
            evidence_quality=None,
            logical_validity=None,
            overall_grade=None,
            has_evidence=False,
        )
        assert len(contradictions) == 0


class TestConfidenceEvidenceAlignment:
    """Test confidence vs evidence alignment checking."""

    def test_detects_high_confidence_no_evidence(self):
        """Should flag high confidence with zero evidence."""
        contradictions = ContradictionEngine.check_confidence_evidence_alignment(
            confidence=0.95,
            confidence_interval=None,
            evidence_count=0,
            tool_verified_count=0,
        )
        assert len(contradictions) == 1
        assert contradictions[0].category == "evidence_gap"
        assert contradictions[0].severity == "warning"

    def test_detects_wide_confidence_interval(self):
        """Should flag very wide confidence intervals."""
        contradictions = ContradictionEngine.check_confidence_evidence_alignment(
            confidence=0.7,
            confidence_interval=(0.1, 0.95),  # Width > 0.8
            evidence_count=5,
            tool_verified_count=3,
        )
        assert len(contradictions) == 1
        assert contradictions[0].category == "confidence_inflation"
        assert contradictions[0].severity == "info"

    def test_reasonable_confidence_with_evidence(self):
        """Should not flag reasonable confidence with supporting evidence."""
        contradictions = ContradictionEngine.check_confidence_evidence_alignment(
            confidence=0.85,
            confidence_interval=(0.75, 0.92),
            evidence_count=5,
            tool_verified_count=3,
        )
        assert len(contradictions) == 0

    def test_low_confidence_no_evidence_ok(self):
        """Low confidence with no evidence should not be flagged."""
        contradictions = ContradictionEngine.check_confidence_evidence_alignment(
            confidence=0.3,
            confidence_interval=None,
            evidence_count=0,
            tool_verified_count=0,
        )
        assert len(contradictions) == 0


class TestOutcomeClaims:
    """Test outcome claim verification."""

    def test_detects_untested_claims(self):
        """Should flag claims that weren't tested."""
        contradictions = ContradictionEngine.check_outcome_claims(
            claimed_outcomes=["feature_works", "tests_pass", "deployed"],
            tested_outcomes=["feature_works", "tests_pass"],
            verified_outcomes=["feature_works"],
        )
        # Should flag "deployed" as untested
        untested = [c for c in contradictions if c.category == "untested_claims"]
        assert len(untested) == 1
        assert "deployed" in untested[0].description

    def test_detects_unverified_tests(self):
        """Should flag tested but unverified outcomes."""
        contradictions = ContradictionEngine.check_outcome_claims(
            claimed_outcomes=["feature_works"],
            tested_outcomes=["feature_works"],
            verified_outcomes=[],
        )
        unverified = [c for c in contradictions if c.category == "unverified_tests"]
        assert len(unverified) == 1

    def test_all_verified_not_flagged(self):
        """Should not flag when all claims are verified."""
        contradictions = ContradictionEngine.check_outcome_claims(
            claimed_outcomes=["feature_works"],
            tested_outcomes=["feature_works"],
            verified_outcomes=["feature_works"],
        )
        assert len(contradictions) == 0


class TestLegalLabelReadiness:
    """Test legal label gate verification."""

    def test_detects_unearned_court_admissible(self):
        """Should flag court_admissible claim without required gates."""
        contradictions = ContradictionEngine.check_legal_label_readiness(
            claims_court_admissible=True,
            has_signature=False,
            has_timestamp=False,
            has_semantic_drift=True,
            interpretation_separated=False,
        )
        assert len(contradictions) == 1
        assert contradictions[0].category == "unearned_label"
        assert contradictions[0].severity == "critical"
        # Should list all missing items
        desc = contradictions[0].description
        assert "signature" in desc
        assert "timestamp" in desc
        assert "drift" in desc
        assert "separation" in desc

    def test_earned_label_not_flagged(self):
        """Should not flag when all gates pass."""
        contradictions = ContradictionEngine.check_legal_label_readiness(
            claims_court_admissible=True,
            has_signature=True,
            has_timestamp=True,
            has_semantic_drift=False,
            interpretation_separated=True,
        )
        assert len(contradictions) == 0

    def test_no_claim_not_flagged(self):
        """Should not flag when not claiming court admissibility."""
        contradictions = ContradictionEngine.check_legal_label_readiness(
            claims_court_admissible=False,
            has_signature=False,
            has_timestamp=False,
            has_semantic_drift=True,
            interpretation_separated=False,
        )
        assert len(contradictions) == 0


class TestCapsuleAnalysis:
    """Test full capsule analysis."""

    def test_analyze_clean_capsule(self):
        """Should return no contradictions for clean capsule."""
        capsule = {
            "payload": {
                "messages": [
                    {"role": "user", "content": "Fix the login bug"},
                    {"role": "assistant", "content": "Fixed the login bug"},
                ],
                "plain_language_summary": {"what_happened": "Fixed the login bug"},
                "quality_assessment": {
                    "evidence_quality": 0.8,
                    "logical_validity": 0.8,
                    "grade": "B",
                },
                "evidence": [{"type": "test_result"}],
                "confidence": {"probability_correct": 0.8},
            },
            "metadata": {"data_richness": "standard"},
            "verification": {"signature": "abc123", "timestamp": "2026-01-01"},
        }
        contradictions = ContradictionEngine.analyze_capsule(capsule)
        critical = [c for c in contradictions if c.severity == "critical"]
        assert len(critical) == 0

    def test_analyze_problematic_capsule(self):
        """Should detect multiple issues in problematic capsule."""
        capsule = {
            "payload": {
                "messages": [
                    {"role": "user", "content": "How do I fix the database error?"},
                ],
                "plain_language_summary": {
                    "what_happened": "Discussed the weather forecast"
                },
                "quality_assessment": {
                    "evidence_quality": 1.0,
                    "logical_validity": 1.0,
                    "grade": "F",
                },
                "confidence": {"probability_correct": 0.99},
            },
            "metadata": {"data_richness": "court_admissible"},
            "verification": {},
        }
        contradictions = ContradictionEngine.analyze_capsule(capsule)
        # Should detect: semantic drift, quality mismatch, high confidence no evidence
        assert len(contradictions) >= 2
        categories = {c.category for c in contradictions}
        assert "semantic_drift" in categories or "quality_mismatch" in categories


class TestFormatContradictions:
    """Test contradiction formatting for display."""

    def test_format_empty_list(self):
        """Should handle empty contradiction list."""
        result = format_contradictions([])
        assert "No contradictions" in result

    def test_format_with_contradictions(self):
        """Should format contradictions readably."""
        contradictions = [
            Contradiction(
                category="semantic_drift",
                severity="critical",
                description="Summary doesn't address question",
                field_a="summary",
                field_b="user_message",
                recommendation="Regenerate summary",
            ),
            Contradiction(
                category="evidence_gap",
                severity="warning",
                description="High confidence without evidence",
                field_a="confidence",
                field_b="evidence_count",
                recommendation="Add supporting evidence",
            ),
        ]
        result = format_contradictions(contradictions)
        assert "SEMANTIC_DRIFT" in result
        assert "EVIDENCE_GAP" in result
        assert "[!]" in result  # Critical marker
        assert "[?]" in result  # Warning marker
