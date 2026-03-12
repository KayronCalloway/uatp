"""
Unit tests for Attribution Aggregator.
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.utils.attribution_aggregator import (
    MAX_CONTRIBUTOR_WEIGHT,
    MAX_CONTRIBUTORS,
    MIN_CONTRIBUTOR_WEIGHT,
    aggregate_attributions,
    calculate_step_contribution,
    merge_dag_definitions,
)


class TestConstants:
    """Tests for module constants."""

    def test_max_contributor_weight(self):
        """Test max contributor weight is defined."""
        assert MAX_CONTRIBUTOR_WEIGHT == 0.50

    def test_min_contributor_weight(self):
        """Test min contributor weight is defined."""
        assert MIN_CONTRIBUTOR_WEIGHT == 0.01

    def test_max_contributors(self):
        """Test max contributors is defined."""
        assert MAX_CONTRIBUTORS == 100


class TestAggregateAttributions:
    """Tests for aggregate_attributions function."""

    def test_empty_attributions(self):
        """Test with empty attribution list."""
        result = aggregate_attributions([])

        assert result["contributors"] == []
        assert result["weights"] == {}
        assert result["step_count"] == 0

    def test_single_contributor(self):
        """Test with single contributor."""
        step_attributions = [
            {
                "contributors": [
                    {
                        "agent_id": "agent_1",
                        "weight": 1.0,
                        "role": "developer",
                        "timestamp": "2024-01-01T10:00:00Z",
                    }
                ]
            }
        ]

        result = aggregate_attributions(step_attributions)

        assert len(result["contributors"]) == 1
        assert result["contributors"][0]["agent_id"] == "agent_1"
        assert result["weights"]["agent_1"] == 1.0

    def test_multiple_contributors(self):
        """Test with multiple contributors."""
        step_attributions = [
            {
                "contributors": [
                    {"agent_id": "agent_1", "weight": 1.0, "role": "developer"},
                    {"agent_id": "agent_2", "weight": 0.5, "role": "reviewer"},
                ]
            }
        ]

        result = aggregate_attributions(step_attributions)

        assert len(result["contributors"]) == 2
        assert "agent_1" in result["weights"]
        assert "agent_2" in result["weights"]

    def test_weighted_sum_aggregation(self):
        """Test weighted sum aggregation method."""
        step_attributions = [
            {
                "contributors": [
                    {"agent_id": "agent_1", "weight": 2.0},
                ]
            },
            {
                "contributors": [
                    {"agent_id": "agent_1", "weight": 3.0},
                ]
            },
        ]

        result = aggregate_attributions(
            step_attributions, aggregation_method="weighted_sum"
        )

        # agent_1 appears in 2 steps with total weight 5.0
        # After normalization should be 1.0
        assert result["weights"]["agent_1"] == 1.0

    def test_equal_aggregation(self):
        """Test equal weight aggregation."""
        step_attributions = [
            {
                "contributors": [
                    {"agent_id": "agent_1", "weight": 10.0},  # Large weight ignored
                ]
            },
            {
                "contributors": [
                    {"agent_id": "agent_2", "weight": 0.1},  # Small weight ignored
                ]
            },
        ]

        result = aggregate_attributions(step_attributions, aggregation_method="equal")

        # Should have equal weights after normalization
        assert result["weights"]["agent_1"] == pytest.approx(0.5, abs=0.01)
        assert result["weights"]["agent_2"] == pytest.approx(0.5, abs=0.01)

    def test_time_decay_aggregation(self):
        """Test time decay aggregation."""
        now = datetime.now(timezone.utc)
        old = (now - timedelta(days=10)).isoformat()
        recent = now.isoformat()

        step_attributions = [
            {
                "contributors": [
                    {"agent_id": "agent_old", "weight": 1.0, "timestamp": old},
                ]
            },
            {
                "contributors": [
                    {"agent_id": "agent_recent", "weight": 1.0, "timestamp": recent},
                ]
            },
        ]

        result = aggregate_attributions(
            step_attributions, aggregation_method="time_decay"
        )

        # Recent contribution should have higher or equal weight (within floating-point tolerance)
        # Use small epsilon for floating-point comparison
        assert (
            result["weights"]["agent_recent"] >= result["weights"]["agent_old"] - 1e-9
        )

    def test_caps_contributor_weight(self):
        """Test caps individual contributor weight."""
        step_attributions = [
            {
                "contributors": [
                    {"agent_id": "agent_dominant", "weight": 10.0},
                    {"agent_id": "agent_minor", "weight": 0.5},
                ]
            }
        ]

        result = aggregate_attributions(step_attributions)

        # agent_dominant should be capped at MAX_CONTRIBUTOR_WEIGHT
        assert result["weights"]["agent_dominant"] <= 0.50

    def test_redistributes_excess_weight(self):
        """Test redistributes excess weight to other contributors."""
        step_attributions = [
            {
                "contributors": [
                    {"agent_id": "agent_1", "weight": 10.0},  # Will be capped
                    {"agent_id": "agent_2", "weight": 1.0},
                    {"agent_id": "agent_3", "weight": 1.0},
                ]
            }
        ]

        result = aggregate_attributions(step_attributions)

        # agent_1 capped at 0.5, excess redistributed to agent_2 and agent_3
        assert result["weights"]["agent_1"] == 0.5
        # agent_2 and agent_3 should have equal shares of the remaining 0.5
        assert result["weights"]["agent_2"] == pytest.approx(0.25, abs=0.01)
        assert result["weights"]["agent_3"] == pytest.approx(0.25, abs=0.01)

    def test_limits_contributor_count(self):
        """Test limits number of contributors."""
        # Create 150 contributors (exceeds MAX_CONTRIBUTORS=100)
        step_attributions = [
            {
                "contributors": [
                    {"agent_id": f"agent_{i}", "weight": 1.0} for i in range(150)
                ]
            }
        ]

        result = aggregate_attributions(step_attributions)

        # Should limit to MAX_CONTRIBUTORS
        assert len(result["contributors"]) == 100

    def test_keeps_top_contributors(self):
        """Test keeps top contributors when limiting."""
        step_attributions = [
            {
                "contributors": [
                    {"agent_id": f"agent_{i}", "weight": float(i)} for i in range(150)
                ]
            }
        ]

        result = aggregate_attributions(step_attributions)

        # Should keep highest weight contributors
        top_agent = result["contributors"][0]["agent_id"]
        assert "149" in top_agent  # agent_149 has highest weight

    def test_tracks_upstream_capsules(self):
        """Test tracks upstream capsules."""
        step_attributions = [
            {"upstream_capsules": ["cap_1", "cap_2"]},
            {"upstream_capsules": ["cap_2", "cap_3"]},
        ]

        result = aggregate_attributions(step_attributions)

        assert set(result["upstream_capsules"]) == {"cap_1", "cap_2", "cap_3"}

    def test_contributor_roles(self):
        """Test tracks contributor roles."""
        step_attributions = [
            {
                "contributors": [
                    {"agent_id": "agent_1", "weight": 1.0, "role": "developer"},
                    {"agent_id": "agent_1", "weight": 0.5, "role": "reviewer"},
                ]
            }
        ]

        result = aggregate_attributions(step_attributions)

        # agent_1 has multiple roles
        assert result["contributors"][0]["role"] == "multi_role"
        assert "developer" in result["contributors"][0]["roles"]
        assert "reviewer" in result["contributors"][0]["roles"]

    def test_contribution_count(self):
        """Test tracks contribution count."""
        step_attributions = [
            {
                "contributors": [
                    {
                        "agent_id": "agent_1",
                        "weight": 1.0,
                        "timestamp": "2024-01-01T10:00:00Z",
                    },
                ]
            },
            {
                "contributors": [
                    {
                        "agent_id": "agent_1",
                        "weight": 1.0,
                        "timestamp": "2024-01-01T11:00:00Z",
                    },
                ]
            },
        ]

        result = aggregate_attributions(step_attributions)

        assert result["contributors"][0]["contribution_count"] == 2

    def test_latest_timestamp(self):
        """Test tracks latest timestamp."""
        step_attributions = [
            {
                "contributors": [
                    {
                        "agent_id": "agent_1",
                        "weight": 1.0,
                        "timestamp": "2024-01-01T10:00:00Z",
                    },
                    {
                        "agent_id": "agent_1",
                        "weight": 1.0,
                        "timestamp": "2024-01-01T12:00:00Z",
                    },
                ]
            }
        ]

        result = aggregate_attributions(step_attributions)

        # Should use latest timestamp
        assert "12:00:00" in result["contributors"][0]["latest_timestamp"]

    def test_sorts_by_weight_descending(self):
        """Test sorts contributors by weight."""
        step_attributions = [
            {
                "contributors": [
                    {"agent_id": "agent_minor", "weight": 0.5},
                    {"agent_id": "agent_major", "weight": 2.0},
                    {"agent_id": "agent_medium", "weight": 1.0},
                ]
            }
        ]

        result = aggregate_attributions(step_attributions)

        # Should be sorted by weight descending
        assert result["contributors"][0]["agent_id"] == "agent_major"
        assert result["contributors"][1]["agent_id"] == "agent_medium"
        assert result["contributors"][2]["agent_id"] == "agent_minor"

    def test_handles_missing_contributors(self):
        """Test handles steps without contributors."""
        step_attributions = [
            {},  # No contributors key
            {"contributors": []},  # Empty contributors
            {
                "contributors": [
                    {"agent_id": "agent_1", "weight": 1.0},
                ]
            },
        ]

        result = aggregate_attributions(step_attributions)

        # Should only process valid contributor
        assert len(result["contributors"]) == 1

    def test_includes_aggregation_metadata(self):
        """Test includes aggregation metadata."""
        step_attributions = [{"contributors": [{"agent_id": "agent_1", "weight": 1.0}]}]

        result = aggregate_attributions(
            step_attributions, aggregation_method="weighted_sum"
        )

        assert result["aggregation_method"] == "weighted_sum"
        assert result["step_count"] == 1
        assert "aggregated_at" in result


class TestMergeDagDefinitions:
    """Tests for merge_dag_definitions function."""

    def test_empty_steps(self):
        """Test with empty step list."""
        result = merge_dag_definitions([])

        assert result["nodes"] == []
        assert result["edges"] == []
        assert result["entry_points"] == []
        assert result["exit_points"] == []

    def test_single_step(self):
        """Test with single step."""
        steps = [
            {
                "step_index": 1,
                "step_type": "inference",
                "capsule_id": "cap_1",
            }
        ]

        result = merge_dag_definitions(steps)

        assert len(result["nodes"]) == 1
        assert result["nodes"][0]["step_index"] == 1
        assert len(result["edges"]) == 0
        assert result["entry_points"] == [1]
        assert result["exit_points"] == [1]

    def test_linear_chain(self):
        """Test with linear dependency chain."""
        steps = [
            {
                "step_index": 1,
                "step_type": "plan",
                "capsule_id": "cap_1",
            },
            {
                "step_index": 2,
                "step_type": "tool_call",
                "capsule_id": "cap_2",
                "depends_on_steps": [1],
            },
            {
                "step_index": 3,
                "step_type": "output",
                "capsule_id": "cap_3",
                "depends_on_steps": [2],
            },
        ]

        result = merge_dag_definitions(steps)

        assert len(result["nodes"]) == 3
        assert len(result["edges"]) == 2
        assert result["entry_points"] == [1]
        assert result["exit_points"] == [3]

    def test_branching_dag(self):
        """Test with branching DAG."""
        steps = [
            {
                "step_index": 1,
                "step_type": "plan",
                "capsule_id": "cap_1",
            },
            {
                "step_index": 2,
                "step_type": "branch_a",
                "capsule_id": "cap_2",
                "depends_on_steps": [1],
            },
            {
                "step_index": 3,
                "step_type": "branch_b",
                "capsule_id": "cap_3",
                "depends_on_steps": [1],
            },
            {
                "step_index": 4,
                "step_type": "merge",
                "capsule_id": "cap_4",
                "depends_on_steps": [2, 3],
            },
        ]

        result = merge_dag_definitions(steps)

        assert len(result["nodes"]) == 4
        assert len(result["edges"]) == 4  # 1->2, 1->3, 2->4, 3->4
        assert result["entry_points"] == [1]
        assert result["exit_points"] == [4]

    def test_multiple_entry_points(self):
        """Test DAG with multiple entry points."""
        steps = [
            {
                "step_index": 1,
                "step_type": "plan_a",
                "capsule_id": "cap_1",
            },
            {
                "step_index": 2,
                "step_type": "plan_b",
                "capsule_id": "cap_2",
            },
            {
                "step_index": 3,
                "step_type": "merge",
                "capsule_id": "cap_3",
                "depends_on_steps": [1, 2],
            },
        ]

        result = merge_dag_definitions(steps)

        assert set(result["entry_points"]) == {1, 2}
        assert result["exit_points"] == [3]

    def test_multiple_exit_points(self):
        """Test DAG with multiple exit points."""
        steps = [
            {
                "step_index": 1,
                "step_type": "plan",
                "capsule_id": "cap_1",
            },
            {
                "step_index": 2,
                "step_type": "output_a",
                "capsule_id": "cap_2",
                "depends_on_steps": [1],
            },
            {
                "step_index": 3,
                "step_type": "output_b",
                "capsule_id": "cap_3",
                "depends_on_steps": [1],
            },
        ]

        result = merge_dag_definitions(steps)

        assert result["entry_points"] == [1]
        assert set(result["exit_points"]) == {2, 3}

    def test_includes_total_steps(self):
        """Test includes total step count."""
        steps = [
            {"step_index": i, "step_type": "test", "capsule_id": f"cap_{i}"}
            for i in range(5)
        ]

        result = merge_dag_definitions(steps)

        assert result["total_steps"] == 5

    def test_handles_missing_depends_on(self):
        """Test handles missing depends_on_steps field."""
        steps = [
            {
                "step_index": 1,
                "step_type": "test",
                "capsule_id": "cap_1",
                # No depends_on_steps
            }
        ]

        result = merge_dag_definitions(steps)

        assert len(result["nodes"]) == 1
        assert len(result["edges"]) == 0

    def test_handles_none_depends_on(self):
        """Test handles None depends_on_steps."""
        steps = [
            {
                "step_index": 1,
                "step_type": "test",
                "capsule_id": "cap_1",
                "depends_on_steps": None,
            }
        ]

        result = merge_dag_definitions(steps)

        assert len(result["edges"]) == 0


class TestCalculateStepContribution:
    """Tests for calculate_step_contribution function."""

    def test_default_contribution(self):
        """Test default contribution weight."""
        result = calculate_step_contribution({})

        assert result > 0.0
        assert result <= 2.0

    def test_step_type_weights(self):
        """Test different step types have different weights."""
        plan_weight = calculate_step_contribution({"step_type": "plan"})
        tool_weight = calculate_step_contribution({"step_type": "tool_call"})
        human_weight = calculate_step_contribution({"step_type": "human_input"})

        # human_input should be weighted higher
        assert human_weight > tool_weight

    def test_execution_time_bonus(self):
        """Test longer execution time increases weight."""
        short = calculate_step_contribution({"execution_time_ms": 100})
        long = calculate_step_contribution({"execution_time_ms": 5000})

        assert long > short

    def test_execution_time_capped(self):
        """Test execution time bonus is capped."""
        result = calculate_step_contribution({"execution_time_ms": 1000000})

        # Should be capped at 2.0
        assert result <= 2.0

    def test_confidence_affects_weight(self):
        """Test confidence affects contribution weight."""
        low_conf = calculate_step_contribution({"confidence": 0.5})
        high_conf = calculate_step_contribution({"confidence": 0.95})

        assert high_conf > low_conf

    def test_combined_factors(self):
        """Test combined factors."""
        result = calculate_step_contribution(
            {
                "step_type": "inference",
                "execution_time_ms": 1000,
                "confidence": 0.9,
            }
        )

        # Should combine all factors
        assert result > 1.0

    def test_caps_at_two(self):
        """Test contribution is capped at 2.0."""
        result = calculate_step_contribution(
            {
                "step_type": "human_input",  # 1.5 base
                "execution_time_ms": 50000,  # Would add more
                "confidence": 1.0,  # Max confidence
            }
        )

        assert result <= 2.0

    def test_all_step_types(self):
        """Test all step types have weights."""
        types = [
            "plan",
            "tool_call",
            "inference",
            "output",
            "human_input",
            "verification",
            "decision",
            "aggregation",
        ]

        for step_type in types:
            result = calculate_step_contribution({"step_type": step_type})
            assert result > 0.0

    def test_unknown_step_type_default(self):
        """Test unknown step type uses default weight."""
        result = calculate_step_contribution({"step_type": "unknown_type"})

        assert result > 0.0


class TestAttributionAggregatorIntegration:
    """Integration tests for attribution aggregator."""

    def test_full_workflow_attribution(self):
        """Test aggregating full workflow attribution."""
        step_attributions = [
            {
                "contributors": [
                    {
                        "agent_id": "planner_agent",
                        "weight": 0.8,
                        "role": "planner",
                        "timestamp": "2024-01-01T10:00:00Z",
                    }
                ],
                "upstream_capsules": [],
            },
            {
                "contributors": [
                    {
                        "agent_id": "executor_agent",
                        "weight": 1.0,
                        "role": "executor",
                        "timestamp": "2024-01-01T10:05:00Z",
                    },
                    {
                        "agent_id": "planner_agent",
                        "weight": 0.2,
                        "role": "supervisor",
                        "timestamp": "2024-01-01T10:05:00Z",
                    },
                ],
                "upstream_capsules": ["cap_1"],
            },
            {
                "contributors": [
                    {
                        "agent_id": "verifier_agent",
                        "weight": 0.5,
                        "role": "verifier",
                        "timestamp": "2024-01-01T10:10:00Z",
                    }
                ],
                "upstream_capsules": ["cap_1", "cap_2"],
            },
        ]

        result = aggregate_attributions(step_attributions)

        assert len(result["contributors"]) == 3
        assert result["step_count"] == 3
        assert len(result["upstream_capsules"]) == 2

        # Verify weights sum to 1.0
        total_weight = sum(result["weights"].values())
        assert total_weight == pytest.approx(1.0, abs=0.01)

    def test_gaming_prevention(self):
        """Test prevents gaming by capping contribution."""
        # Attacker tries to claim 99% of attribution
        step_attributions = [
            {
                "contributors": [
                    {"agent_id": "attacker", "weight": 99.0},
                    {"agent_id": "legitimate", "weight": 1.0},
                ]
            }
        ]

        result = aggregate_attributions(step_attributions)

        # Attacker should be capped at 50%
        assert result["weights"]["attacker"] == 0.50
        assert result["weights"]["legitimate"] == 0.50
