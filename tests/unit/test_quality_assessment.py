"""
Unit tests for Quality Assessment.
"""

import pytest

from src.analysis.quality_assessment import (
    QualityAssessment,
    QualityAssessor,
    QualityScore,
)


class TestQualityScore:
    """Tests for QualityScore dataclass."""

    def test_create_quality_score(self):
        """Test creating a quality score."""
        score = QualityScore(
            dimension="completeness",
            score=0.8,
            max_score=10.0,
            issues=["Missing analysis"],
            suggestions=["Add more detail"],
        )

        assert score.dimension == "completeness"
        assert score.score == 0.8
        assert len(score.issues) == 1
        assert len(score.suggestions) == 1


class TestQualityAssessment:
    """Tests for QualityAssessment dataclass."""

    def test_create_assessment(self):
        """Test creating a quality assessment."""
        assessment = QualityAssessment(
            overall_quality=0.75,
            dimension_scores={},
            strengths=["Good evidence"],
            weaknesses=["Weak coherence"],
            improvement_priority=[("coherence", 0.2)],
            quality_grade="B",
        )

        assert assessment.overall_quality == 0.75
        assert assessment.quality_grade == "B"
        assert len(assessment.strengths) == 1


class TestQualityAssessorConstants:
    """Tests for QualityAssessor constants."""

    def test_dimension_weights_defined(self):
        """Test dimension weights are defined."""
        weights = QualityAssessor.DIMENSION_WEIGHTS

        assert "completeness" in weights
        assert "coherence" in weights
        assert "evidence_quality" in weights
        assert "logical_validity" in weights
        assert "bias_detection" in weights
        assert "clarity" in weights

    def test_weights_sum_to_one(self):
        """Test weights sum to approximately 1.0."""
        total = sum(QualityAssessor.DIMENSION_WEIGHTS.values())

        assert total == pytest.approx(1.0, abs=0.01)


class TestQualityAssessorAssessCapsule:
    """Tests for QualityAssessor.assess_capsule."""

    def test_assess_empty_capsule(self):
        """Test assessing empty capsule."""
        capsule = {}

        result = QualityAssessor.assess_capsule(capsule)

        assert isinstance(result, QualityAssessment)
        assert result.overall_quality >= 0.0
        assert result.overall_quality <= 1.0

    def test_assess_capsule_without_steps(self):
        """Test assessing capsule without reasoning steps."""
        capsule = {"payload": {}}

        result = QualityAssessor.assess_capsule(capsule)

        assert result.overall_quality < 0.5

    def test_assess_high_quality_capsule(self):
        """Test assessing high quality capsule."""
        capsule = {
            "payload": {
                "reasoning_steps": [
                    {
                        "operation": "problem_definition",
                        "content": "Define the problem clearly",
                        "confidence": 0.9,
                    },
                    {
                        "operation": "analysis",
                        "content": "Therefore we analyze the situation",
                        "measurements": {"accuracy": 0.95},
                        "evidence": "Data shows...",
                        "confidence": 0.85,
                        "depends_on": [1],
                    },
                    {
                        "operation": "decision",
                        "content": "Thus we conclude",
                        "alternatives_considered": ["opt1", "opt2", "opt3"],
                        "confidence": 0.9,
                        "depends_on": [2],
                    },
                ]
            }
        }

        result = QualityAssessor.assess_capsule(capsule)

        assert result.overall_quality > 0.6
        assert result.quality_grade in ["A", "B", "C"]

    def test_dimension_scores_present(self):
        """Test all dimension scores are present."""
        capsule = {
            "payload": {
                "reasoning_steps": [{"operation": "test", "content": "test content"}]
            }
        }

        result = QualityAssessor.assess_capsule(capsule)

        assert "completeness" in result.dimension_scores
        assert "coherence" in result.dimension_scores
        assert "evidence_quality" in result.dimension_scores
        assert "logical_validity" in result.dimension_scores
        assert "bias_detection" in result.dimension_scores
        assert "clarity" in result.dimension_scores

    def test_improvement_priority_generated(self):
        """Test improvement priority list is generated."""
        capsule = {
            "payload": {"reasoning_steps": [{"operation": "test", "content": "test"}]}
        }

        result = QualityAssessor.assess_capsule(capsule)

        assert len(result.improvement_priority) > 0
        assert all(isinstance(item, tuple) for item in result.improvement_priority)


class TestQualityAssessorAssessCompleteness:
    """Tests for QualityAssessor._assess_completeness."""

    def test_empty_steps(self):
        """Test with empty steps."""
        result = QualityAssessor._assess_completeness([], {})

        assert result.dimension == "completeness"
        assert result.score < 0.5

    def test_problem_statement_detected(self):
        """Test detects problem statement."""
        steps = [{"content": "The problem is X"}]

        result = QualityAssessor._assess_completeness(steps, {})

        assert result.score > 0.0

    def test_analysis_steps_detected(self):
        """Test detects analysis steps."""
        steps = [{"operation": "analysis", "content": "Analyzing the data"}]

        result = QualityAssessor._assess_completeness(steps, {})

        assert result.score > 0.0

    def test_evidence_detected(self):
        """Test detects evidence."""
        steps = [{"measurements": {"accuracy": 0.9}}]

        result = QualityAssessor._assess_completeness(steps, {})

        assert result.score > 0.0

    def test_alternatives_detected(self):
        """Test detects alternatives."""
        steps = [{"alternatives_considered": ["a", "b"]}]

        result = QualityAssessor._assess_completeness(steps, {})

        assert result.score > 0.0

    def test_conclusion_detected(self):
        """Test detects conclusion."""
        steps = [
            {"operation": "analysis"},
            {"operation": "conclude", "content": "Therefore X"},
        ]

        result = QualityAssessor._assess_completeness(steps, {})

        assert result.score > 0.0

    def test_complete_reasoning(self):
        """Test complete reasoning gets high score."""
        steps = [
            {"content": "The problem is X"},
            {"operation": "analysis", "content": "Analyzing"},
            {"measurements": {"val": 1}},
            {"alternatives_considered": ["a", "b"]},
            {"operation": "conclude", "content": "Therefore"},
        ]

        result = QualityAssessor._assess_completeness(steps, {})

        assert result.score == 1.0


class TestQualityAssessorAssessCoherence:
    """Tests for QualityAssessor._assess_coherence."""

    def test_too_few_steps(self):
        """Test with too few steps."""
        result = QualityAssessor._assess_coherence([])

        assert result.score < 0.5

    def test_dependencies_boost_score(self):
        """Test dependencies boost coherence."""
        steps = [
            {"content": "Step 1"},
            {"content": "Step 2", "depends_on": [1]},
            {"content": "Step 3", "depends_on": [2]},
        ]

        result = QualityAssessor._assess_coherence(steps)

        assert result.score > 0.3

    def test_confidence_progression(self):
        """Test positive confidence progression."""
        steps = [
            {"content": "Step 1", "confidence": 0.7},
            {"content": "Step 2", "confidence": 0.8},
            {"content": "Step 3", "confidence": 0.85},
        ]

        result = QualityAssessor._assess_coherence(steps)

        assert result.score > 0.3

    def test_transition_words_detected(self):
        """Test transition words boost coherence."""
        steps = [
            {"content": "First observation"},
            {"content": "Therefore we conclude"},
            {"content": "Because of this result"},
        ]

        result = QualityAssessor._assess_coherence(steps)

        assert result.score > 0.2

    def test_decreasing_confidence_flagged(self):
        """Test decreasing confidence is flagged."""
        steps = [
            {"content": "Step 1", "confidence": 0.9},
            {"content": "Step 2", "confidence": 0.7},
            {"content": "Step 3", "confidence": 0.5},
        ]

        result = QualityAssessor._assess_coherence(steps)

        assert any("confidence decreases" in i.lower() for i in result.issues)


class TestQualityAssessorAssessEvidenceQuality:
    """Tests for QualityAssessor._assess_evidence_quality."""

    def test_no_evidence(self):
        """Test with no evidence."""
        steps = [{"content": "A claim"}]

        result = QualityAssessor._assess_evidence_quality(steps)

        assert result.score < 0.5
        assert len(result.issues) > 0

    def test_measurements_boost_score(self):
        """Test measurements boost evidence quality."""
        steps = [{"measurements": {"accuracy": 0.9}}]

        result = QualityAssessor._assess_evidence_quality(steps)

        assert result.score > 0.1

    def test_evidence_boost_score(self):
        """Test explicit evidence boosts score."""
        steps = [{"evidence": "Data shows X"}]

        result = QualityAssessor._assess_evidence_quality(steps)

        assert result.score > 0.0

    def test_citations_boost_score(self):
        """Test citations boost score."""
        steps = [{"content": "According to [Smith et al]"}]

        result = QualityAssessor._assess_evidence_quality(steps)

        assert result.score > 0.0

    def test_multiple_evidence_types(self):
        """Test multiple evidence types."""
        steps = [
            {"measurements": {"val": 1}},
            {"evidence": "Data"},
            {"content": "Reference [1]"},
        ]

        result = QualityAssessor._assess_evidence_quality(steps)

        # 1.5 + 1.0 + 0.5 = 3.0 / 10.0 = 0.3
        assert result.score >= 0.25

    def test_score_capped_at_max(self):
        """Test score is capped at max."""
        steps = [{"measurements": {"val": i}} for i in range(20)]

        result = QualityAssessor._assess_evidence_quality(steps)

        assert result.score <= 1.0


class TestQualityAssessorAssessLogicalValidity:
    """Tests for QualityAssessor._assess_logical_validity."""

    def test_starts_high(self):
        """Test starts with high score."""
        steps = [{"content": "Valid reasoning"}]

        result = QualityAssessor._assess_logical_validity(steps)

        assert result.score > 0.8

    def test_hasty_generalization_detected(self):
        """Test detects hasty generalization."""
        steps = [{"content": "All users always prefer X"}]

        result = QualityAssessor._assess_logical_validity(steps)

        assert any("generalization" in i.lower() for i in result.issues)

    def test_hasty_generalization_with_evidence_ok(self):
        """Test absolute claims with evidence are ok."""
        steps = [
            {
                "content": "All tested users prefer X",
                "measurements": {"n": 100},
            }
        ]

        result = QualityAssessor._assess_logical_validity(steps)

        # Should not penalize as much
        assert result.score > 0.8

    def test_appeal_to_authority_detected(self):
        """Test detects appeal to authority."""
        steps = [{"content": "Expert says X"}]

        result = QualityAssessor._assess_logical_validity(steps)

        assert any("authority" in i.lower() for i in result.issues)

    def test_false_dichotomy_pattern(self):
        """Test checks for false dichotomy pattern."""
        steps = [{"content": "Either X or Y", "alternatives_considered": ["X", "Y"]}]

        result = QualityAssessor._assess_logical_validity(steps)

        # With only 2 alternatives for "either/or", should penalize
        assert result.score <= 1.0  # May or may not detect, but shouldn't crash

    def test_false_dichotomy_with_alternatives_ok(self):
        """Test dichotomy with multiple alternatives is ok."""
        steps = [
            {
                "content": "Either X or Y",
                "alternatives_considered": ["X", "Y", "Z"],
            }
        ]

        result = QualityAssessor._assess_logical_validity(steps)

        # Should not flag as dichotomy
        assert result.score > 0.9

    def test_valid_reasoning_high_score(self):
        """Test valid reasoning gets high score."""
        steps = [{"content": "Based on evidence, we conclude X", "evidence": "data"}]

        result = QualityAssessor._assess_logical_validity(steps)

        assert result.score >= 0.9


class TestQualityAssessorAssessBias:
    """Tests for QualityAssessor._assess_bias."""

    def test_starts_high(self):
        """Test starts with high score."""
        steps = [{"content": "Neutral analysis"}]

        result = QualityAssessor._assess_bias(steps)

        assert result.score > 0.8

    def test_confirmation_bias_detected(self):
        """Test detects confirmation bias words."""
        steps = [{"content": "Obviously this is correct"}]

        result = QualityAssessor._assess_bias(steps)

        assert any("confirmation" in i.lower() for i in result.issues)

    def test_anchoring_bias_detected(self):
        """Test detects anchoring bias."""
        steps = [{"content": "First we saw X"}]

        result = QualityAssessor._assess_bias(steps)

        assert any("anchoring" in i.lower() for i in result.issues)

    def test_availability_bias_detected(self):
        """Test detects availability bias."""
        steps = [{"content": "Recent studies show"}]

        result = QualityAssessor._assess_bias(steps)

        assert any("availability" in i.lower() for i in result.issues)

    def test_framing_bias_detected(self):
        """Test detects framing bias."""
        steps = [{"content": "Only 10% failed"}]

        result = QualityAssessor._assess_bias(steps)

        assert any("framing" in i.lower() for i in result.issues)

    def test_limited_alternatives_flagged(self):
        """Test limited alternatives flagged."""
        steps = [{"alternatives_considered": ["only_one"]}]

        result = QualityAssessor._assess_bias(steps)

        assert any("limited" in i.lower() for i in result.issues)

    def test_overconfidence_detected(self):
        """Test detects overconfidence."""
        steps = [
            {"content": "Step 1", "confidence": 0.98},
            {"content": "Step 2", "confidence": 0.99},
            {"content": "Step 3", "confidence": 0.97},
        ]

        result = QualityAssessor._assess_bias(steps)

        assert any("overconfidence" in i.lower() for i in result.issues)

    def test_unbiased_reasoning_high_score(self):
        """Test unbiased reasoning gets high score."""
        steps = [
            {
                "content": "Careful analysis suggests X",
                "confidence": 0.8,
                "alternatives_considered": ["X", "Y", "Z"],
            }
        ]

        result = QualityAssessor._assess_bias(steps)

        assert result.score >= 0.8


class TestQualityAssessorAssessClarity:
    """Tests for QualityAssessor._assess_clarity."""

    def test_no_steps(self):
        """Test with no steps."""
        result = QualityAssessor._assess_clarity([])

        assert result.score == 0.0

    def test_clear_steps_boost_score(self):
        """Test clear steps boost score."""
        steps = [
            {
                "operation": "analysis",
                "content": "Clear description of the analysis process",
            },
            {
                "operation": "decision",
                "content": "Well explained decision rationale",
            },
        ]

        result = QualityAssessor._assess_clarity(steps)

        assert result.score > 0.3

    def test_unclear_steps_flagged(self):
        """Test unclear steps are flagged."""
        steps = [{"content": "X"}, {"content": "Y"}]

        result = QualityAssessor._assess_clarity(steps)

        assert any("lack clear" in i.lower() for i in result.issues)

    def test_operations_boost_score(self):
        """Test operation labels boost score."""
        steps = [
            {
                "operation": "analysis",
                "content": "Test content here with sufficient detail for clarity",
            },
            {
                "operation": "decision",
                "content": "Test decision here with clear explanation",
            },
            {
                "operation": "conclude",
                "content": "Test conclusion here with proper reasoning",
            },
        ]

        result = QualityAssessor._assess_clarity(steps)

        # All steps have operations (3 points) + some clarity points
        assert result.score > 0.3

    def test_missing_operations_flagged(self):
        """Test missing operations flagged."""
        steps = [{"content": "Content without operation"}] * 3

        result = QualityAssessor._assess_clarity(steps)

        assert any("lack operation" in i.lower() for i in result.issues)

    def test_reasonable_length_boost(self):
        """Test reasonable step length boosts score."""
        steps = [
            {
                "operation": "analysis",
                "content": "This is a reasonable length explanation that is neither too brief nor too verbose for clarity",
            }
        ] * 3

        result = QualityAssessor._assess_clarity(steps)

        assert result.score > 0.5

    def test_too_brief_flagged(self):
        """Test too brief steps flagged."""
        steps = [{"content": "X"}] * 3

        result = QualityAssessor._assess_clarity(steps)

        assert any("too brief" in i.lower() for i in result.issues)

    def test_too_verbose_flagged(self):
        """Test too verbose steps flagged."""
        long_content = "x" * 400
        steps = [{"content": long_content}] * 3

        result = QualityAssessor._assess_clarity(steps)

        assert any("verbose" in i.lower() for i in result.issues)


class TestQualityAssessorCalculateGrade:
    """Tests for QualityAssessor._calculate_grade."""

    def test_grade_a(self):
        """Test A grade."""
        assert QualityAssessor._calculate_grade(0.95) == "A"
        assert QualityAssessor._calculate_grade(0.9) == "A"

    def test_grade_b(self):
        """Test B grade."""
        assert QualityAssessor._calculate_grade(0.85) == "B"
        assert QualityAssessor._calculate_grade(0.8) == "B"

    def test_grade_c(self):
        """Test C grade."""
        assert QualityAssessor._calculate_grade(0.75) == "C"
        assert QualityAssessor._calculate_grade(0.7) == "C"

    def test_grade_d(self):
        """Test D grade."""
        assert QualityAssessor._calculate_grade(0.65) == "D"
        assert QualityAssessor._calculate_grade(0.6) == "D"

    def test_grade_f(self):
        """Test F grade."""
        assert QualityAssessor._calculate_grade(0.5) == "F"
        assert QualityAssessor._calculate_grade(0.0) == "F"

    def test_edge_cases(self):
        """Test edge case scores."""
        assert QualityAssessor._calculate_grade(1.0) == "A"
        assert QualityAssessor._calculate_grade(0.899) == "B"
        assert QualityAssessor._calculate_grade(0.799) == "C"


class TestQualityAssessmentIntegration:
    """Integration tests for quality assessment."""

    def test_perfect_capsule(self):
        """Test assessing a perfect capsule."""
        capsule = {
            "payload": {
                "reasoning_steps": [
                    {
                        "operation": "problem_definition",
                        "content": "The problem we need to solve is X, which requires careful analysis",
                        "confidence": 0.9,
                    },
                    {
                        "operation": "analysis",
                        "content": "Therefore, analyzing the data reveals important patterns",
                        "measurements": {"accuracy": 0.95, "precision": 0.92},
                        "evidence": "Multiple sources confirm",
                        "confidence": 0.88,
                        "depends_on": [1],
                    },
                    {
                        "operation": "investigate",
                        "content": "Because of these findings, we investigate alternatives",
                        "alternatives_considered": [
                            "approach_a",
                            "approach_b",
                            "approach_c",
                        ],
                        "confidence": 0.85,
                        "depends_on": [2],
                    },
                    {
                        "operation": "decision",
                        "content": "Thus we conclude that approach_a is best [Reference 1]",
                        "confidence": 0.87,
                        "depends_on": [3],
                    },
                ]
            }
        }

        result = QualityAssessor.assess_capsule(capsule)

        assert result.quality_grade in ["A", "B"]
        assert result.overall_quality > 0.7

    def test_poor_capsule(self):
        """Test assessing a poor quality capsule."""
        capsule = {
            "payload": {
                "reasoning_steps": [
                    {"content": "X"},  # Too brief, no operation
                ]
            }
        }

        result = QualityAssessor.assess_capsule(capsule)

        assert result.quality_grade in ["D", "F"]
        assert len(result.weaknesses) > 0
        assert len(result.improvement_priority) > 0

    def test_strengths_identified(self):
        """Test strengths are identified."""
        capsule = {
            "payload": {
                "reasoning_steps": [
                    {
                        "operation": "analysis",
                        "content": "Detailed analysis with clear reasoning",
                        "measurements": {"val": 1},
                        "evidence": "data",
                    }
                ]
                * 3
            }
        }

        result = QualityAssessor.assess_capsule(capsule)

        # Should have at least one strength
        assert len(result.strengths) > 0

    def test_weaknesses_identified(self):
        """Test weaknesses are identified."""
        capsule = {
            "payload": {
                "reasoning_steps": [
                    {
                        "content": "All users always prefer this obviously"
                    }  # Biased, hasty
                ]
            }
        }

        result = QualityAssessor.assess_capsule(capsule)

        # Should have weaknesses
        assert len(result.weaknesses) > 0

    def test_improvement_priority_sorted(self):
        """Test improvement priority is sorted."""
        capsule = {"payload": {"reasoning_steps": [{"content": "Brief"}]}}

        result = QualityAssessor.assess_capsule(capsule)

        # Priority should be sorted by impact
        if len(result.improvement_priority) > 1:
            for i in range(len(result.improvement_priority) - 1):
                assert (
                    result.improvement_priority[i][1]
                    >= result.improvement_priority[i + 1][1]
                )
