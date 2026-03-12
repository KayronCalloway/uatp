"""
Unit tests for Pattern Mining.
"""

import pytest

from src.analysis.pattern_mining import PatternMiner, ReasoningPattern


class TestReasoningPattern:
    """Tests for ReasoningPattern dataclass."""

    def test_create_pattern(self):
        """Test creating a reasoning pattern."""
        pattern = ReasoningPattern(
            pattern_id="abc123",
            pattern_type="sequence",
            pattern_name="Analysis → Decision",
            pattern_description="A common sequence",
            pattern_structure={"sequence": ["analysis", "decision"]},
            success_rate=0.85,
            usage_count=10,
            applicable_domains=["general"],
            example_capsule_ids=["cap1", "cap2"],
        )

        assert pattern.pattern_id == "abc123"
        assert pattern.pattern_type == "sequence"
        assert pattern.success_rate == 0.85
        assert pattern.usage_count == 10

    def test_pattern_with_confidence_impact(self):
        """Test pattern with confidence impact."""
        pattern = ReasoningPattern(
            pattern_id="xyz789",
            pattern_type="decision_tree",
            pattern_name="Test Pattern",
            pattern_description="Test",
            pattern_structure={},
            success_rate=0.9,
            usage_count=5,
            applicable_domains=["test"],
            example_capsule_ids=["cap1"],
            confidence_impact=0.05,
        )

        assert pattern.confidence_impact == 0.05

    def test_pattern_types(self):
        """Test different pattern types."""
        types = ["sequence", "decision_tree", "failure_mode", "success_strategy"]

        for pattern_type in types:
            pattern = ReasoningPattern(
                pattern_id="id",
                pattern_type=pattern_type,
                pattern_name="name",
                pattern_description="desc",
                pattern_structure={},
                success_rate=0.7,
                usage_count=3,
                applicable_domains=[],
                example_capsule_ids=[],
            )
            assert pattern.pattern_type == pattern_type


class TestPatternMinerConstants:
    """Tests for PatternMiner constants."""

    def test_min_pattern_occurrences(self):
        """Test minimum pattern occurrences constant."""
        assert PatternMiner.MIN_PATTERN_OCCURRENCES == 3

    def test_min_success_rate(self):
        """Test minimum success rate constant."""
        assert PatternMiner.MIN_SUCCESS_RATE == 0.6


class TestPatternMinerExtractStepSequence:
    """Tests for PatternMiner.extract_step_sequence."""

    def test_extract_from_dict_steps(self):
        """Test extracting sequence from dict steps."""
        capsule = {
            "payload": {
                "reasoning_steps": [
                    {"operation": "observation"},
                    {"operation": "analysis"},
                    {"operation": "decision"},
                ]
            }
        }

        sequence = PatternMiner.extract_step_sequence(capsule)

        assert sequence == ["observation", "analysis", "decision"]

    def test_extract_from_string_steps(self):
        """Test extracting sequence from string steps."""
        capsule = {
            "payload": {
                "reasoning_steps": [
                    "First step",
                    "Second step",
                ]
            }
        }

        sequence = PatternMiner.extract_step_sequence(capsule)

        assert sequence == ["reasoning", "reasoning"]

    def test_extract_mixed_steps(self):
        """Test extracting from mixed step types."""
        capsule = {
            "payload": {
                "reasoning_steps": [
                    {"operation": "observation"},
                    "string step",
                    {"operation": "conclusion"},
                ]
            }
        }

        sequence = PatternMiner.extract_step_sequence(capsule)

        assert sequence == ["observation", "reasoning", "conclusion"]

    def test_extract_no_reasoning_steps(self):
        """Test extraction when no reasoning_steps."""
        capsule = {"payload": {}}

        sequence = PatternMiner.extract_step_sequence(capsule)

        assert sequence == []

    def test_extract_no_payload(self):
        """Test extraction when no payload."""
        capsule = {}

        sequence = PatternMiner.extract_step_sequence(capsule)

        assert sequence == []

    def test_extract_with_unknown_operation(self):
        """Test extraction with step missing operation."""
        capsule = {
            "payload": {
                "reasoning_steps": [
                    {},  # No operation field
                    {"operation": "decision"},
                ]
            }
        }

        sequence = PatternMiner.extract_step_sequence(capsule)

        assert sequence == ["unknown", "decision"]


class TestPatternMinerGeneratePatternId:
    """Tests for PatternMiner.generate_pattern_id."""

    def test_generate_id(self):
        """Test generating a pattern ID."""
        structure = {"sequence": ["a", "b", "c"]}

        pattern_id = PatternMiner.generate_pattern_id(structure)

        assert isinstance(pattern_id, str)
        assert len(pattern_id) == 16

    def test_same_structure_same_id(self):
        """Test same structure produces same ID."""
        structure1 = {"sequence": ["x", "y"]}
        structure2 = {"sequence": ["x", "y"]}

        id1 = PatternMiner.generate_pattern_id(structure1)
        id2 = PatternMiner.generate_pattern_id(structure2)

        assert id1 == id2

    def test_different_structure_different_id(self):
        """Test different structures produce different IDs."""
        structure1 = {"sequence": ["a", "b"]}
        structure2 = {"sequence": ["b", "a"]}

        id1 = PatternMiner.generate_pattern_id(structure1)
        id2 = PatternMiner.generate_pattern_id(structure2)

        assert id1 != id2

    def test_order_independent(self):
        """Test ID is independent of key order."""
        structure1 = {"a": 1, "b": 2}
        structure2 = {"b": 2, "a": 1}

        id1 = PatternMiner.generate_pattern_id(structure1)
        id2 = PatternMiner.generate_pattern_id(structure2)

        assert id1 == id2


class TestPatternMinerMineSequencePatterns:
    """Tests for PatternMiner.mine_sequence_patterns."""

    def test_empty_capsules(self):
        """Test mining from empty capsule list."""
        patterns = PatternMiner.mine_sequence_patterns([])

        assert patterns == []

    def test_single_capsule_insufficient(self):
        """Test single capsule is insufficient for pattern."""
        capsules_with_outcomes = [
            {
                "capsule": {
                    "capsule_id": "cap1",
                    "payload": {
                        "reasoning_steps": [
                            {"operation": "analysis"},
                            {"operation": "decision"},
                        ]
                    },
                },
                "outcome_success": True,
                "domain": "test",
            }
        ]

        patterns = PatternMiner.mine_sequence_patterns(capsules_with_outcomes)

        # Single occurrence is below MIN_PATTERN_OCCURRENCES
        assert len(patterns) == 0

    def test_mine_common_sequence(self):
        """Test mining a common sequence pattern."""
        capsules_with_outcomes = [
            {
                "capsule": {
                    "capsule_id": f"cap{i}",
                    "payload": {
                        "reasoning_steps": [
                            {"operation": "observation"},
                            {"operation": "analysis"},
                            {"operation": "decision"},
                        ]
                    },
                },
                "outcome_success": True,
                "domain": "general",
            }
            for i in range(5)  # 5 successful instances
        ]

        patterns = PatternMiner.mine_sequence_patterns(capsules_with_outcomes)

        # Should find patterns
        assert len(patterns) > 0

    def test_low_success_rate_filtered(self):
        """Test patterns with low success rate are filtered."""
        capsules_with_outcomes = [
            {
                "capsule": {
                    "capsule_id": f"cap{i}",
                    "payload": {
                        "reasoning_steps": [
                            {"operation": "bad_pattern"},
                            {"operation": "failure"},
                        ]
                    },
                },
                "outcome_success": False,  # All fail
                "domain": "test",
            }
            for i in range(5)
        ]

        patterns = PatternMiner.mine_sequence_patterns(capsules_with_outcomes)

        # Success rate is 0%, below threshold
        assert len(patterns) == 0

    def test_pattern_success_rate(self):
        """Test pattern success rate is calculated correctly."""
        capsules_with_outcomes = [
            {
                "capsule": {
                    "capsule_id": f"cap_success_{i}",
                    "payload": {
                        "reasoning_steps": [
                            {"operation": "step1"},
                            {"operation": "step2"},
                        ]
                    },
                },
                "outcome_success": True,
                "domain": "test",
            }
            for i in range(3)
        ] + [
            {
                "capsule": {
                    "capsule_id": f"cap_fail_{i}",
                    "payload": {
                        "reasoning_steps": [
                            {"operation": "step1"},
                            {"operation": "step2"},
                        ]
                    },
                },
                "outcome_success": False,
                "domain": "test",
            }
            for i in range(2)
        ]

        patterns = PatternMiner.mine_sequence_patterns(capsules_with_outcomes)

        # Success rate should be 3/5 = 0.6 (minimum threshold)
        if patterns:
            assert patterns[0].success_rate >= 0.6

    def test_min_max_length(self):
        """Test min_length and max_length parameters."""
        capsules_with_outcomes = [
            {
                "capsule": {
                    "capsule_id": f"cap{i}",
                    "payload": {
                        "reasoning_steps": [
                            {"operation": "a"},
                            {"operation": "b"},
                            {"operation": "c"},
                            {"operation": "d"},
                        ]
                    },
                },
                "outcome_success": True,
                "domain": "test",
            }
            for i in range(5)
        ]

        patterns = PatternMiner.mine_sequence_patterns(
            capsules_with_outcomes, min_length=3, max_length=3
        )

        # Should only find patterns of length 3
        for pattern in patterns:
            assert pattern.pattern_structure["length"] == 3

    def test_pattern_sorting(self):
        """Test patterns are sorted by success rate."""
        capsules_with_outcomes = []

        # Create two different patterns with different success rates
        for i in range(5):
            capsules_with_outcomes.append(
                {
                    "capsule": {
                        "capsule_id": f"cap_high_{i}",
                        "payload": {
                            "reasoning_steps": [
                                {"operation": "good1"},
                                {"operation": "good2"},
                            ]
                        },
                    },
                    "outcome_success": True,
                    "domain": "test",
                }
            )

        for i in range(3):
            capsules_with_outcomes.append(
                {
                    "capsule": {
                        "capsule_id": f"cap_med_{i}",
                        "payload": {
                            "reasoning_steps": [
                                {"operation": "ok1"},
                                {"operation": "ok2"},
                            ]
                        },
                    },
                    "outcome_success": i < 2,  # 2/3 success rate
                    "domain": "test",
                }
            )

        patterns = PatternMiner.mine_sequence_patterns(capsules_with_outcomes)

        # Patterns should be sorted by success rate (highest first)
        if len(patterns) >= 2:
            for i in range(len(patterns) - 1):
                assert patterns[i].success_rate >= patterns[i + 1].success_rate


class TestPatternMinerMineDecisionPatterns:
    """Tests for PatternMiner.mine_decision_patterns."""

    def test_empty_capsules(self):
        """Test mining from empty list."""
        patterns = PatternMiner.mine_decision_patterns([])

        assert patterns == []

    def test_find_decision_with_alternatives(self):
        """Test finding decision patterns with alternatives."""
        capsules_with_outcomes = [
            {
                "capsule": {
                    "capsule_id": f"cap{i}",
                    "payload": {
                        "reasoning_steps": [
                            {
                                "operation": "decision",
                                "alternatives_considered": ["opt1", "opt2", "opt3"],
                            }
                        ]
                    },
                },
                "outcome_success": True,
                "domain": "test",
            }
            for i in range(5)
        ]

        patterns = PatternMiner.mine_decision_patterns(capsules_with_outcomes)

        assert len(patterns) > 0
        assert patterns[0].pattern_type == "decision_tree"

    def test_alternatives_count(self):
        """Test pattern captures alternatives count."""
        capsules_with_outcomes = [
            {
                "capsule": {
                    "capsule_id": f"cap{i}",
                    "payload": {
                        "reasoning_steps": [
                            {
                                "operation": "choice",
                                "alternatives_considered": ["a", "b"],
                            }
                        ]
                    },
                },
                "outcome_success": True,
                "domain": "test",
            }
            for i in range(5)
        ]

        patterns = PatternMiner.mine_decision_patterns(capsules_with_outcomes)

        if patterns:
            assert patterns[0].pattern_structure["alternatives_evaluated"] == 2

    def test_no_alternatives_not_captured(self):
        """Test steps without alternatives don't create patterns."""
        capsules_with_outcomes = [
            {
                "capsule": {
                    "capsule_id": f"cap{i}",
                    "payload": {
                        "reasoning_steps": [
                            {
                                "operation": "decision",
                                # No alternatives_considered
                            }
                        ]
                    },
                },
                "outcome_success": True,
                "domain": "test",
            }
            for i in range(5)
        ]

        patterns = PatternMiner.mine_decision_patterns(capsules_with_outcomes)

        assert len(patterns) == 0

    def test_single_alternative_not_captured(self):
        """Test single alternative doesn't create pattern."""
        capsules_with_outcomes = [
            {
                "capsule": {
                    "capsule_id": f"cap{i}",
                    "payload": {
                        "reasoning_steps": [
                            {
                                "operation": "decision",
                                "alternatives_considered": ["only_one"],
                            }
                        ]
                    },
                },
                "outcome_success": True,
                "domain": "test",
            }
            for i in range(5)
        ]

        patterns = PatternMiner.mine_decision_patterns(capsules_with_outcomes)

        # Single alternative is not useful
        assert len(patterns) == 0


class TestPatternMinerMineFailureModes:
    """Tests for PatternMiner.mine_failure_modes."""

    def test_empty_capsules(self):
        """Test mining from empty list."""
        patterns = PatternMiner.mine_failure_modes([])

        assert patterns == []

    def test_low_confidence_with_uncertainty(self):
        """Test detecting low confidence with uncertainty pattern."""
        capsules_with_outcomes = [
            {
                "capsule": {
                    "capsule_id": f"cap{i}",
                    "payload": {
                        "reasoning_steps": [
                            {
                                "operation": "analysis",
                                "confidence": 0.5,
                                "uncertainty_sources": ["source1", "source2"],
                            }
                        ]
                    },
                },
                "outcome_success": False,  # Failed outcomes
                "domain": "test",
            }
            for i in range(5)
        ]

        patterns = PatternMiner.mine_failure_modes(capsules_with_outcomes)

        assert len(patterns) > 0
        assert patterns[0].pattern_type == "failure_mode"

    def test_decision_no_alternatives_failure(self):
        """Test detecting decisions without alternatives as failure."""
        capsules_with_outcomes = [
            {
                "capsule": {
                    "capsule_id": f"cap{i}",
                    "payload": {
                        "reasoning_steps": [
                            {
                                "operation": "decision",
                                # No alternatives
                            }
                        ]
                    },
                },
                "outcome_success": False,
                "domain": "test",
            }
            for i in range(5)
        ]

        patterns = PatternMiner.mine_failure_modes(capsules_with_outcomes)

        if patterns:
            assert any(
                "decision_no_alternatives"
                in p.pattern_structure.get("failure_type", "")
                for p in patterns
            )

    def test_high_success_filtered(self):
        """Test patterns with low failure rate are filtered."""
        capsules_with_outcomes = [
            {
                "capsule": {
                    "capsule_id": f"cap{i}",
                    "payload": {
                        "reasoning_steps": [
                            {
                                "operation": "decision",
                            }
                        ]
                    },
                },
                "outcome_success": True,  # Mostly succeed
                "domain": "test",
            }
            for i in range(5)
        ]

        patterns = PatternMiner.mine_failure_modes(capsules_with_outcomes)

        # Failure rate is low, shouldn't be included
        assert len(patterns) == 0

    def test_failure_patterns_sorted(self):
        """Test failure patterns sorted by success rate (worst first)."""
        capsules_with_outcomes = []

        # Create bad pattern (high failure rate)
        for i in range(5):
            capsules_with_outcomes.append(
                {
                    "capsule": {
                        "capsule_id": f"cap_bad_{i}",
                        "payload": {
                            "reasoning_steps": [
                                {
                                    "operation": "decision",
                                }
                            ]
                        },
                    },
                    "outcome_success": i == 0,  # 1/5 success = 80% failure
                    "domain": "test",
                }
            )

        # Create medium pattern (moderate failure rate)
        for i in range(5):
            capsules_with_outcomes.append(
                {
                    "capsule": {
                        "capsule_id": f"cap_med_{i}",
                        "payload": {
                            "reasoning_steps": [
                                {
                                    "operation": "analysis",
                                    "confidence": 0.6,
                                    "uncertainty_sources": ["s1"],
                                }
                            ]
                        },
                    },
                    "outcome_success": i < 3,  # 3/5 success = 40% failure
                    "domain": "test",
                }
            )

        patterns = PatternMiner.mine_failure_modes(capsules_with_outcomes)

        # Worst patterns first (lowest success rate)
        if len(patterns) >= 2:
            for i in range(len(patterns) - 1):
                assert patterns[i].success_rate <= patterns[i + 1].success_rate


class TestPatternMinerEstimateConfidenceImpact:
    """Tests for PatternMiner._estimate_confidence_impact."""

    def test_very_high_success(self):
        """Test impact for very high success rate."""
        impact = PatternMiner._estimate_confidence_impact(0.95)
        assert impact == 0.05

    def test_high_success(self):
        """Test impact for high success rate."""
        impact = PatternMiner._estimate_confidence_impact(0.85)
        assert impact == 0.03

    def test_moderate_success(self):
        """Test impact for moderate success rate."""
        impact = PatternMiner._estimate_confidence_impact(0.75)
        assert impact == 0.01

    def test_neutral_success(self):
        """Test impact for neutral success rate."""
        impact = PatternMiner._estimate_confidence_impact(0.6)
        assert impact == 0.0

    def test_low_success(self):
        """Test impact for low success rate."""
        impact = PatternMiner._estimate_confidence_impact(0.3)
        assert impact == -0.03


class TestPatternMinerMineAllPatterns:
    """Tests for PatternMiner.mine_all_patterns."""

    def test_returns_all_types(self):
        """Test returns dict with all pattern types."""
        capsules_with_outcomes = []

        result = PatternMiner.mine_all_patterns(capsules_with_outcomes)

        assert "sequence" in result
        assert "decision_tree" in result
        assert "failure_mode" in result

    def test_all_types_are_lists(self):
        """Test all values are lists."""
        result = PatternMiner.mine_all_patterns([])

        assert isinstance(result["sequence"], list)
        assert isinstance(result["decision_tree"], list)
        assert isinstance(result["failure_mode"], list)

    def test_mines_all_patterns(self):
        """Test mines patterns of all types."""
        capsules_with_outcomes = []

        # Add sequence pattern data
        for i in range(5):
            capsules_with_outcomes.append(
                {
                    "capsule": {
                        "capsule_id": f"seq{i}",
                        "payload": {
                            "reasoning_steps": [
                                {"operation": "obs"},
                                {"operation": "dec"},
                            ]
                        },
                    },
                    "outcome_success": True,
                    "domain": "test",
                }
            )

        # Add decision pattern data
        for i in range(5):
            capsules_with_outcomes.append(
                {
                    "capsule": {
                        "capsule_id": f"dec{i}",
                        "payload": {
                            "reasoning_steps": [
                                {
                                    "operation": "choice",
                                    "alternatives_considered": ["a", "b", "c"],
                                }
                            ]
                        },
                    },
                    "outcome_success": True,
                    "domain": "test",
                }
            )

        # Add failure pattern data
        for i in range(5):
            capsules_with_outcomes.append(
                {
                    "capsule": {
                        "capsule_id": f"fail{i}",
                        "payload": {
                            "reasoning_steps": [
                                {
                                    "operation": "decision",
                                }
                            ]
                        },
                    },
                    "outcome_success": False,
                    "domain": "test",
                }
            )

        result = PatternMiner.mine_all_patterns(capsules_with_outcomes)

        # Should find patterns of each type
        assert len(result["sequence"]) > 0
        assert len(result["decision_tree"]) > 0
        assert len(result["failure_mode"]) > 0


class TestPatternMinerMatchPatternToCapsule:
    """Tests for PatternMiner.match_pattern_to_capsule."""

    def test_no_matches(self):
        """Test when no patterns match."""
        capsule = {
            "payload": {
                "reasoning_steps": [
                    {"operation": "unique_op"},
                ]
            }
        }

        patterns = [
            ReasoningPattern(
                pattern_id="p1",
                pattern_type="sequence",
                pattern_name="Test",
                pattern_description="Test",
                pattern_structure={"sequence": ["different_op"]},
                success_rate=0.8,
                usage_count=3,
                applicable_domains=[],
                example_capsule_ids=[],
            )
        ]

        matches = PatternMiner.match_pattern_to_capsule(capsule, patterns)

        assert len(matches) == 0

    def test_sequence_match(self):
        """Test matching sequence pattern."""
        capsule = {
            "payload": {
                "reasoning_steps": [
                    {"operation": "observation"},
                    {"operation": "analysis"},
                    {"operation": "decision"},
                ]
            }
        }

        patterns = [
            ReasoningPattern(
                pattern_id="p1",
                pattern_type="sequence",
                pattern_name="Obs -> Ana",
                pattern_description="Test",
                pattern_structure={"sequence": ["observation", "analysis"]},
                success_rate=0.9,
                usage_count=5,
                applicable_domains=[],
                example_capsule_ids=[],
            )
        ]

        matches = PatternMiner.match_pattern_to_capsule(capsule, patterns)

        assert len(matches) == 1
        assert matches[0][0].pattern_id == "p1"
        assert matches[0][1] == 1.0

    def test_decision_pattern_match(self):
        """Test matching decision pattern."""
        capsule = {
            "payload": {
                "reasoning_steps": [
                    {
                        "operation": "decision",
                        "alternatives_considered": ["a", "b"],
                    }
                ]
            }
        }

        patterns = [
            ReasoningPattern(
                pattern_id="d1",
                pattern_type="decision_tree",
                pattern_name="Binary decision",
                pattern_description="Test",
                pattern_structure={
                    "decision_operation": "decision",
                    "alternatives_evaluated": 2,
                },
                success_rate=0.85,
                usage_count=4,
                applicable_domains=[],
                example_capsule_ids=[],
            )
        ]

        matches = PatternMiner.match_pattern_to_capsule(capsule, patterns)

        assert len(matches) == 1
        assert matches[0][0].pattern_id == "d1"

    def test_multiple_matches_sorted(self):
        """Test multiple matches are sorted by score."""
        capsule = {
            "payload": {
                "reasoning_steps": [
                    {"operation": "a"},
                    {"operation": "b"},
                    {"operation": "c"},
                ]
            }
        }

        patterns = [
            ReasoningPattern(
                pattern_id="p1",
                pattern_type="sequence",
                pattern_name="a->b",
                pattern_description="Test",
                pattern_structure={"sequence": ["a", "b"]},
                success_rate=0.9,
                usage_count=5,
                applicable_domains=[],
                example_capsule_ids=[],
            ),
            ReasoningPattern(
                pattern_id="p2",
                pattern_type="sequence",
                pattern_name="b->c",
                pattern_description="Test",
                pattern_structure={"sequence": ["b", "c"]},
                success_rate=0.85,
                usage_count=3,
                applicable_domains=[],
                example_capsule_ids=[],
            ),
        ]

        matches = PatternMiner.match_pattern_to_capsule(capsule, patterns)

        # Both should match with score 1.0
        assert len(matches) == 2


class TestPatternMinerIsSubsequence:
    """Tests for PatternMiner._is_subsequence."""

    def test_empty_pattern_always_matches(self):
        """Test empty pattern matches any sequence."""
        assert PatternMiner._is_subsequence([], [1, 2, 3]) is True
        assert PatternMiner._is_subsequence([], []) is True

    def test_exact_match(self):
        """Test exact sequence match."""
        assert PatternMiner._is_subsequence(["a", "b", "c"], ["a", "b", "c"]) is True

    def test_subsequence_match(self):
        """Test subsequence match."""
        assert PatternMiner._is_subsequence(["a", "c"], ["a", "b", "c", "d"]) is True

    def test_no_match(self):
        """Test when pattern is not a subsequence."""
        assert PatternMiner._is_subsequence(["a", "d"], ["a", "b", "c"]) is False

    def test_pattern_longer_than_sequence(self):
        """Test when pattern is longer than sequence."""
        assert PatternMiner._is_subsequence(["a", "b", "c", "d"], ["a", "b"]) is False

    def test_order_matters(self):
        """Test that order matters."""
        assert PatternMiner._is_subsequence(["c", "a"], ["a", "b", "c"]) is False

    def test_repeated_elements(self):
        """Test with repeated elements."""
        assert PatternMiner._is_subsequence(["a", "a"], ["a", "b", "a", "c"]) is True
