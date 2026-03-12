"""
Unit tests for Critical Path Analysis.
"""

import pytest

from src.analysis.critical_path import CriticalPathAnalysis, CriticalPathAnalyzer
from src.utils.rich_capsule_creator import RichReasoningStep


class TestCriticalPathAnalysis:
    """Tests for CriticalPathAnalysis dataclass."""

    def test_create_analysis(self):
        """Test creating a critical path analysis."""
        analysis = CriticalPathAnalysis(
            critical_steps=[1, 2, 3],
            bottleneck_steps=[2],
            key_decision_points=[3],
            confidence_chain=[0.9, 0.7, 0.85],
            weakest_link={"step_id": 2, "confidence": 0.7},
            critical_path_strength=0.82,
            peripheral_steps=[4, 5],
            dependency_depth=3,
        )

        assert analysis.critical_steps == [1, 2, 3]
        assert analysis.bottleneck_steps == [2]
        assert analysis.dependency_depth == 3

    def test_empty_analysis(self):
        """Test creating an empty analysis."""
        analysis = CriticalPathAnalysis(
            critical_steps=[],
            bottleneck_steps=[],
            key_decision_points=[],
            confidence_chain=[],
            weakest_link={},
            critical_path_strength=1.0,
            peripheral_steps=[],
            dependency_depth=0,
        )

        assert len(analysis.critical_steps) == 0
        assert analysis.critical_path_strength == 1.0


class TestCriticalPathAnalyzerAnalyze:
    """Tests for CriticalPathAnalyzer.analyze."""

    def test_analyze_empty(self):
        """Test analyzing empty steps."""
        result = CriticalPathAnalyzer.analyze([])

        assert result.critical_steps == []
        assert result.bottleneck_steps == []
        assert result.dependency_depth == 0
        assert result.critical_path_strength == 1.0

    def test_analyze_single_step(self):
        """Test analyzing single step."""
        step = RichReasoningStep(
            step=1,
            reasoning="Single step",
            confidence=0.9,
        )

        result = CriticalPathAnalyzer.analyze([step])

        assert 1 in result.critical_steps
        assert result.dependency_depth >= 0

    def test_analyze_linear_chain(self):
        """Test analyzing linear dependency chain."""
        steps = [
            RichReasoningStep(
                step=1,
                reasoning="First",
                confidence=0.9,
            ),
            RichReasoningStep(
                step=2,
                reasoning="Second",
                confidence=0.8,
                depends_on_steps=[1],
            ),
            RichReasoningStep(
                step=3,
                reasoning="Third",
                confidence=0.85,
                depends_on_steps=[2],
            ),
        ]

        result = CriticalPathAnalyzer.analyze(steps)

        # All steps should be critical in a linear chain
        assert 1 in result.critical_steps
        assert 2 in result.critical_steps
        assert 3 in result.critical_steps

    def test_analyze_with_peripheral_steps(self):
        """Test analyzing with peripheral (non-critical) steps."""
        steps = [
            RichReasoningStep(
                step=1,
                reasoning="Main step",
                confidence=0.9,
            ),
            RichReasoningStep(
                step=2,
                reasoning="Peripheral observation",
                confidence=0.85,
                # Not depended upon
            ),
            RichReasoningStep(
                step=3,
                reasoning="Conclusion",
                confidence=0.8,
                depends_on_steps=[1],
            ),
        ]

        result = CriticalPathAnalyzer.analyze(steps)

        # Step 2 should be peripheral
        assert 2 in result.peripheral_steps
        assert 2 not in result.critical_steps

    def test_confidence_chain(self):
        """Test confidence chain extraction."""
        steps = [
            RichReasoningStep(step=1, reasoning="A", confidence=0.9),
            RichReasoningStep(
                step=2,
                reasoning="B",
                confidence=0.7,
                depends_on_steps=[1],
            ),
            RichReasoningStep(
                step=3,
                reasoning="C",
                confidence=0.85,
                depends_on_steps=[2],
            ),
        ]

        result = CriticalPathAnalyzer.analyze(steps)

        assert len(result.confidence_chain) > 0
        assert all(0 <= c <= 1 for c in result.confidence_chain)

    def test_critical_path_strength(self):
        """Test critical path strength calculation."""
        steps = [
            RichReasoningStep(step=1, reasoning="A", confidence=0.8),
            RichReasoningStep(step=2, reasoning="B", confidence=0.6),
            RichReasoningStep(step=3, reasoning="C", confidence=0.9),
        ]

        result = CriticalPathAnalyzer.analyze(steps)

        # Strength should be average of confidence
        assert 0 < result.critical_path_strength <= 1.0

    def test_weakest_link_identified(self):
        """Test weakest link identification."""
        steps = [
            RichReasoningStep(
                step=1,
                reasoning="Strong step",
                confidence=0.95,
            ),
            RichReasoningStep(
                step=2,
                reasoning="Weak step",
                confidence=0.5,
                depends_on_steps=[1],
            ),
            RichReasoningStep(
                step=3,
                reasoning="Medium step",
                confidence=0.8,
                depends_on_steps=[2],
            ),
        ]

        result = CriticalPathAnalyzer.analyze(steps)

        # Weakest link should be step 2
        if result.weakest_link:
            assert result.weakest_link["confidence"] <= 0.5


class TestCriticalPathAnalyzerIdentifyCriticalSteps:
    """Tests for CriticalPathAnalyzer._identify_critical_steps."""

    def test_empty_steps(self):
        """Test with empty steps."""
        result = CriticalPathAnalyzer._identify_critical_steps([])

        assert result == []

    def test_single_step_is_critical(self):
        """Test single step is critical."""
        steps = [RichReasoningStep(step=1, reasoning="Only step", confidence=0.9)]

        result = CriticalPathAnalyzer._identify_critical_steps(steps)

        assert 1 in result

    def test_depended_upon_steps(self):
        """Test steps that are depended upon are critical."""
        steps = [
            RichReasoningStep(step=1, reasoning="Base", confidence=0.9),
            RichReasoningStep(
                step=2,
                reasoning="Depends on 1",
                confidence=0.8,
                depends_on_steps=[1],
            ),
        ]

        result = CriticalPathAnalyzer._identify_critical_steps(steps)

        assert 1 in result  # Depended upon
        assert 2 in result  # Last step

    def test_last_step_always_critical(self):
        """Test last step is always critical."""
        steps = [
            RichReasoningStep(step=1, reasoning="A", confidence=0.9),
            RichReasoningStep(step=2, reasoning="B", confidence=0.8),
            RichReasoningStep(step=3, reasoning="C", confidence=0.85),
        ]

        result = CriticalPathAnalyzer._identify_critical_steps(steps)

        assert 3 in result  # Last step should be critical


class TestCriticalPathAnalyzerIdentifyBottlenecks:
    """Tests for CriticalPathAnalyzer._identify_bottlenecks."""

    def test_empty_steps(self):
        """Test with empty steps."""
        result = CriticalPathAnalyzer._identify_bottlenecks([])

        assert result == []

    def test_single_step(self):
        """Test with single step."""
        steps = [RichReasoningStep(step=1, reasoning="Only", confidence=0.9)]

        result = CriticalPathAnalyzer._identify_bottlenecks(steps)

        assert len(result) == 1

    def test_identifies_lowest_confidence(self):
        """Test identifies lowest confidence steps."""
        steps = [
            RichReasoningStep(step=1, reasoning="High", confidence=0.95),
            RichReasoningStep(step=2, reasoning="Low", confidence=0.5),
            RichReasoningStep(step=3, reasoning="Medium", confidence=0.75),
            RichReasoningStep(step=4, reasoning="Lower", confidence=0.6),
        ]

        result = CriticalPathAnalyzer._identify_bottlenecks(steps)

        # Should include lowest confidence steps
        assert 2 in result  # Lowest at 0.5

    def test_bottleneck_count(self):
        """Test bottleneck count is bottom quartile."""
        steps = [
            RichReasoningStep(step=i, reasoning=f"Step {i}", confidence=0.5 + i * 0.1)
            for i in range(8)
        ]

        result = CriticalPathAnalyzer._identify_bottlenecks(steps)

        # 8 steps -> bottom 2 (quartile)
        assert len(result) == 2


class TestCriticalPathAnalyzerIdentifyDecisionPoints:
    """Tests for CriticalPathAnalyzer._identify_decision_points."""

    def test_no_decision_points(self):
        """Test when no steps have alternatives."""
        steps = [
            RichReasoningStep(step=1, reasoning="A", confidence=0.9),
            RichReasoningStep(step=2, reasoning="B", confidence=0.8),
        ]

        result = CriticalPathAnalyzer._identify_decision_points(steps)

        assert result == []

    def test_identifies_alternatives(self):
        """Test identifies steps with alternatives."""
        steps = [
            RichReasoningStep(step=1, reasoning="A", confidence=0.9),
            RichReasoningStep(
                step=2,
                reasoning="Decision",
                confidence=0.8,
                alternatives_considered=["option1", "option2"],
            ),
            RichReasoningStep(step=3, reasoning="C", confidence=0.85),
        ]

        result = CriticalPathAnalyzer._identify_decision_points(steps)

        assert 2 in result

    def test_empty_alternatives_not_included(self):
        """Test empty alternatives list not counted."""
        steps = [
            RichReasoningStep(
                step=1,
                reasoning="Not a decision",
                confidence=0.9,
                alternatives_considered=[],
            ),
        ]

        result = CriticalPathAnalyzer._identify_decision_points(steps)

        assert result == []


class TestCriticalPathAnalyzerFindWeakestLink:
    """Tests for CriticalPathAnalyzer._find_weakest_link."""

    def test_empty_inputs(self):
        """Test with empty inputs."""
        result = CriticalPathAnalyzer._find_weakest_link([], {}, [])

        assert result == {}

    def test_identifies_weakest(self):
        """Test identifies weakest confidence."""
        steps = [
            RichReasoningStep(step=1, reasoning="A", confidence=0.9),
            RichReasoningStep(step=2, reasoning="B", confidence=0.5),
            RichReasoningStep(step=3, reasoning="C", confidence=0.8),
        ]
        step_map = {s.step: s for s in steps}
        critical_steps = [1, 2, 3]
        confidence_chain = [0.9, 0.5, 0.8]

        result = CriticalPathAnalyzer._find_weakest_link(
            critical_steps, step_map, confidence_chain
        )

        assert result["step_id"] == 2
        assert result["confidence"] == 0.5

    def test_includes_metadata(self):
        """Test includes step metadata."""
        steps = [
            RichReasoningStep(
                step=1,
                reasoning="Weak reasoning here",
                confidence=0.6,
                operation="analysis",
                uncertainty_sources=["source1", "source2"],
            )
        ]
        step_map = {s.step: s for s in steps}
        critical_steps = [1]
        confidence_chain = [0.6]

        result = CriticalPathAnalyzer._find_weakest_link(
            critical_steps, step_map, confidence_chain
        )

        assert "operation" in result
        assert "uncertainty_sources" in result
        assert "reasoning" in result

    def test_truncates_long_reasoning(self):
        """Test truncates long reasoning text."""
        long_text = "x" * 200
        steps = [
            RichReasoningStep(
                step=1,
                reasoning=long_text,
                confidence=0.7,
            )
        ]
        step_map = {s.step: s for s in steps}

        result = CriticalPathAnalyzer._find_weakest_link([1], step_map, [0.7])

        assert len(result["reasoning"]) <= 104  # 100 + "..."


class TestCriticalPathAnalyzerCalculateDependencyDepth:
    """Tests for CriticalPathAnalyzer._calculate_dependency_depth."""

    def test_empty_steps(self):
        """Test with empty steps."""
        result = CriticalPathAnalyzer._calculate_dependency_depth([])

        assert result == 0

    def test_no_dependencies(self):
        """Test with no dependencies."""
        steps = [
            RichReasoningStep(step=1, reasoning="A", confidence=0.9),
            RichReasoningStep(step=2, reasoning="B", confidence=0.8),
        ]

        result = CriticalPathAnalyzer._calculate_dependency_depth(steps)

        assert result == 1  # Each step has depth 1

    def test_linear_chain(self):
        """Test with linear dependency chain."""
        steps = [
            RichReasoningStep(step=1, reasoning="A", confidence=0.9),
            RichReasoningStep(
                step=2,
                reasoning="B",
                confidence=0.8,
                depends_on_steps=[1],
            ),
            RichReasoningStep(
                step=3,
                reasoning="C",
                confidence=0.85,
                depends_on_steps=[2],
            ),
        ]

        result = CriticalPathAnalyzer._calculate_dependency_depth(steps)

        assert result == 3  # Depth of 3 for chain of 3

    def test_branching_dependencies(self):
        """Test with branching dependencies."""
        steps = [
            RichReasoningStep(step=1, reasoning="Root", confidence=0.9),
            RichReasoningStep(
                step=2,
                reasoning="Branch A",
                confidence=0.8,
                depends_on_steps=[1],
            ),
            RichReasoningStep(
                step=3,
                reasoning="Branch B",
                confidence=0.85,
                depends_on_steps=[1],
            ),
            RichReasoningStep(
                step=4,
                reasoning="Merge",
                confidence=0.75,
                depends_on_steps=[2, 3],
            ),
        ]

        result = CriticalPathAnalyzer._calculate_dependency_depth(steps)

        assert result == 3  # Max depth path

    def test_cycle_detection(self):
        """Test handles cycles gracefully."""
        steps = [
            RichReasoningStep(
                step=1,
                reasoning="A",
                confidence=0.9,
                depends_on_steps=[2],  # Cycle
            ),
            RichReasoningStep(
                step=2,
                reasoning="B",
                confidence=0.8,
                depends_on_steps=[1],  # Cycle
            ),
        ]

        # Should not crash
        result = CriticalPathAnalyzer._calculate_dependency_depth(steps)

        assert result >= 0


class TestCriticalPathAnalyzerGenerateImprovementRecommendations:
    """Tests for CriticalPathAnalyzer.generate_improvement_recommendations."""

    def test_no_recommendations_for_perfect(self):
        """Test no recommendations for perfect analysis."""
        analysis = CriticalPathAnalysis(
            critical_steps=[1, 2, 3],
            bottleneck_steps=[],
            key_decision_points=[],
            confidence_chain=[0.95, 0.9, 0.92],
            weakest_link={"step_id": 2, "confidence": 0.9},
            critical_path_strength=0.92,
            peripheral_steps=[],
            dependency_depth=5,
        )
        step_map = {
            1: RichReasoningStep(step=1, reasoning="A", confidence=0.95),
            2: RichReasoningStep(step=2, reasoning="B", confidence=0.9),
            3: RichReasoningStep(step=3, reasoning="C", confidence=0.92),
        }

        recs = CriticalPathAnalyzer.generate_improvement_recommendations(
            analysis, step_map
        )

        # Should have minimal recommendations
        assert len(recs) <= 5

    def test_recommends_strengthening_bottleneck(self):
        """Test recommends strengthening bottleneck."""
        analysis = CriticalPathAnalysis(
            critical_steps=[1, 2],
            bottleneck_steps=[2],
            key_decision_points=[],
            confidence_chain=[0.9, 0.5],
            weakest_link={"step_id": 2, "confidence": 0.5},
            critical_path_strength=0.7,
            peripheral_steps=[],
            dependency_depth=2,
        )
        step_map = {
            1: RichReasoningStep(step=1, reasoning="A", confidence=0.9),
            2: RichReasoningStep(step=2, reasoning="B", confidence=0.5),
        }

        recs = CriticalPathAnalyzer.generate_improvement_recommendations(
            analysis, step_map
        )

        # Should recommend strengthening bottleneck
        assert any("bottleneck" in r.lower() for r in recs)

    def test_recommends_addressing_low_confidence(self):
        """Test recommends addressing low confidence on critical path."""
        analysis = CriticalPathAnalysis(
            critical_steps=[1],
            bottleneck_steps=[],
            key_decision_points=[],
            confidence_chain=[0.6],
            weakest_link={"step_id": 1, "confidence": 0.6},
            critical_path_strength=0.6,
            peripheral_steps=[],
            dependency_depth=1,
        )
        step_map = {
            1: RichReasoningStep(step=1, reasoning="A", confidence=0.6),
        }

        recs = CriticalPathAnalyzer.generate_improvement_recommendations(
            analysis, step_map
        )

        # Should recommend addressing low confidence
        assert any("low confidence" in r.lower() for r in recs)

    def test_recommends_for_uncertainty_sources(self):
        """Test recommends addressing uncertainty sources."""
        analysis = CriticalPathAnalysis(
            critical_steps=[1],
            bottleneck_steps=[],
            key_decision_points=[],
            confidence_chain=[0.8],
            weakest_link={},
            critical_path_strength=0.8,
            peripheral_steps=[],
            dependency_depth=2,
        )
        step_map = {
            1: RichReasoningStep(
                step=1,
                reasoning="A",
                confidence=0.8,
                uncertainty_sources=["s1", "s2", "s3"],
            ),
        }

        recs = CriticalPathAnalyzer.generate_improvement_recommendations(
            analysis, step_map
        )

        # Should recommend addressing uncertainty
        assert any("uncertainty" in r.lower() for r in recs)

    def test_recommends_expanding_shallow_reasoning(self):
        """Test recommends expanding shallow reasoning."""
        analysis = CriticalPathAnalysis(
            critical_steps=[1, 2, 3, 4],
            bottleneck_steps=[],
            key_decision_points=[],
            confidence_chain=[0.9, 0.85, 0.8, 0.87],
            weakest_link={},
            critical_path_strength=0.85,
            peripheral_steps=[],
            dependency_depth=2,  # Shallow for 4 steps
        )
        step_map = {
            i: RichReasoningStep(step=i, reasoning=f"Step {i}", confidence=0.85)
            for i in range(1, 5)
        }

        recs = CriticalPathAnalyzer.generate_improvement_recommendations(
            analysis, step_map
        )

        # Should recommend expanding reasoning
        assert any("shallow" in r.lower() for r in recs)

    def test_limits_recommendations(self):
        """Test limits recommendations to 5."""
        # Create problematic analysis
        analysis = CriticalPathAnalysis(
            critical_steps=list(range(1, 11)),
            bottleneck_steps=list(range(1, 6)),
            key_decision_points=list(range(1, 11)),
            confidence_chain=[0.5] * 10,
            weakest_link={"step_id": 1, "confidence": 0.5},
            critical_path_strength=0.5,
            peripheral_steps=[],
            dependency_depth=1,
        )
        step_map = {
            i: RichReasoningStep(
                step=i,
                reasoning=f"Step {i}",
                confidence=0.5,
                uncertainty_sources=["s1", "s2", "s3"],
            )
            for i in range(1, 11)
        }

        recs = CriticalPathAnalyzer.generate_improvement_recommendations(
            analysis, step_map
        )

        # Should be limited to 5
        assert len(recs) <= 5


class TestCriticalPathAnalyzerToDict:
    """Tests for CriticalPathAnalyzer.to_dict."""

    def test_converts_to_dict(self):
        """Test converts analysis to dictionary."""
        analysis = CriticalPathAnalysis(
            critical_steps=[1, 2, 3],
            bottleneck_steps=[2],
            key_decision_points=[3],
            confidence_chain=[0.9, 0.7, 0.85],
            weakest_link={"step_id": 2, "confidence": 0.7},
            critical_path_strength=0.82,
            peripheral_steps=[4],
            dependency_depth=3,
        )

        result = CriticalPathAnalyzer.to_dict(analysis)

        assert isinstance(result, dict)
        assert "critical_steps" in result
        assert "bottleneck_steps" in result
        assert "dependency_depth" in result

    def test_rounds_confidence_values(self):
        """Test rounds confidence values."""
        analysis = CriticalPathAnalysis(
            critical_steps=[1],
            bottleneck_steps=[],
            key_decision_points=[],
            confidence_chain=[0.123456789],
            weakest_link={},
            critical_path_strength=0.987654321,
            peripheral_steps=[],
            dependency_depth=1,
        )

        result = CriticalPathAnalyzer.to_dict(analysis)

        # Should round to 3 decimals
        assert result["confidence_chain"][0] == 0.123
        assert result["critical_path_strength"] == 0.988

    def test_preserves_all_fields(self):
        """Test preserves all analysis fields."""
        analysis = CriticalPathAnalysis(
            critical_steps=[1, 2],
            bottleneck_steps=[1],
            key_decision_points=[2],
            confidence_chain=[0.8, 0.9],
            weakest_link={"step_id": 1, "confidence": 0.8},
            critical_path_strength=0.85,
            peripheral_steps=[3, 4],
            dependency_depth=2,
        )

        result = CriticalPathAnalyzer.to_dict(analysis)

        assert result["critical_steps"] == [1, 2]
        assert result["bottleneck_steps"] == [1]
        assert result["key_decision_points"] == [2]
        assert result["peripheral_steps"] == [3, 4]
        assert result["dependency_depth"] == 2
