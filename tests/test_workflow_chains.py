"""
Unit tests for UATP 7.2 Agentic Workflow Chains

Tests:
- Workflow creation
- Step management
- DAG construction
- Attribution aggregation
- Workflow completion
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

import pytest

from src.capsule_schema import (
    CapsuleStatus,
    CapsuleType,
    Verification,
    WorkflowCompleteCapsule,
    WorkflowCompletePayload,
    WorkflowStepCapsule,
    WorkflowStepPayload,
)
from src.services.workflow_chain_service import WorkflowChainService
from src.utils.attribution_aggregator import (
    aggregate_attributions,
    calculate_step_contribution,
    merge_dag_definitions,
)
from src.utils.uatp_envelope import (
    create_workflow_context,
    detect_capsule_version,
    wrap_in_uatp_envelope,
)


class TestWorkflowStepPayload:
    """Test WorkflowStepPayload validation."""

    def test_valid_workflow_step(self):
        """Test creating a valid workflow step payload."""
        payload = WorkflowStepPayload(
            workflow_capsule_id="wf_20260302_abc123def456789a",
            step_index=0,
            step_type="plan",
            step_name="Initial Planning",
        )
        assert payload.step_index == 0
        assert payload.step_type == "plan"

    def test_workflow_step_with_dependencies(self):
        """Test workflow step with dependencies."""
        payload = WorkflowStepPayload(
            workflow_capsule_id="wf_20260302_abc123def456789a",
            step_index=3,
            step_type="tool_call",
            step_name="Execute Tool",
            depends_on_steps=[0, 1, 2],
            tool_name="file_editor",
            execution_time_ms=1500,
            confidence=0.95,
        )
        assert payload.depends_on_steps == [0, 1, 2]
        assert payload.tool_name == "file_editor"
        assert payload.execution_time_ms == 1500

    def test_workflow_step_inference(self):
        """Test inference step type."""
        payload = WorkflowStepPayload(
            workflow_capsule_id="wf_20260302_abc123def456789a",
            step_index=2,
            step_type="inference",
            model_id="claude-3-opus",
            input_data={"prompt": "Test prompt"},
            output_data={"response": "Test response"},
            confidence=0.88,
        )
        assert payload.step_type == "inference"
        assert payload.model_id == "claude-3-opus"


class TestWorkflowCompletePayload:
    """Test WorkflowCompletePayload validation."""

    def test_valid_workflow_complete(self):
        """Test creating a valid workflow completion payload."""
        now = datetime.now(timezone.utc)
        payload = WorkflowCompletePayload(
            workflow_capsule_id="wf_20260302_abc123def456789a",
            workflow_name="Code Review Workflow",
            workflow_type="linear",
            total_steps=5,
            step_capsule_ids=[
                "caps_2026_03_02_a1b2c3d4e5f6a7b8",
                "caps_2026_03_02_b1c2d3e4f5a6b7c8",
                "caps_2026_03_02_c1d2e3f4a5b6c7d8",
                "caps_2026_03_02_d1e2f3a4b5c6d7e8",
                "caps_2026_03_02_e1f2a3b4c5d6e7f8",
            ],
            started_at=now,
            completed_at=now,
            status="completed",
        )
        assert payload.total_steps == 5
        assert len(payload.step_capsule_ids) == 5

    def test_workflow_complete_with_attribution(self):
        """Test workflow completion with aggregated attribution."""
        now = datetime.now(timezone.utc)
        payload = WorkflowCompletePayload(
            workflow_capsule_id="wf_20260302_abc123def456789a",
            workflow_name="Multi-Agent Workflow",
            workflow_type="parallel",
            total_steps=3,
            step_capsule_ids=["caps_1", "caps_2", "caps_3"],
            aggregated_attribution={
                "contributors": [
                    {"agent_id": "agent_1", "weight": 0.5},
                    {"agent_id": "agent_2", "weight": 0.3},
                    {"agent_id": "agent_3", "weight": 0.2},
                ],
            },
            dag_definition={
                "nodes": [0, 1, 2],
                "edges": [],
                "entry_points": [0, 1, 2],
                "exit_points": [0, 1, 2],
            },
            started_at=now,
            completed_at=now,
        )
        assert payload.aggregated_attribution is not None
        assert payload.dag_definition is not None


class TestWorkflowCapsules:
    """Test workflow capsule creation."""

    def test_create_workflow_step_capsule(self):
        """Test creating a workflow step capsule."""
        capsule = WorkflowStepCapsule(
            capsule_id="caps_2026_03_02_a1b2c3d4e5f6a7b8",
            version="7.2",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.SEALED,
            verification=Verification(
                signature="ed25519:" + "0" * 128,
                merkle_root="sha256:" + "0" * 64,
            ),
            workflow_step=WorkflowStepPayload(
                workflow_capsule_id="wf_test",
                step_index=0,
                step_type="plan",
            ),
        )
        assert capsule.capsule_type == CapsuleType.WORKFLOW_STEP
        assert capsule.version == "7.2"

    def test_create_workflow_complete_capsule(self):
        """Test creating a workflow complete capsule."""
        now = datetime.now(timezone.utc)
        capsule = WorkflowCompleteCapsule(
            capsule_id="caps_2026_03_02_b1c2d3e4f5a6b7c8",
            version="7.2",
            timestamp=now,
            status=CapsuleStatus.SEALED,
            verification=Verification(
                signature="ed25519:" + "0" * 128,
                merkle_root="sha256:" + "0" * 64,
            ),
            workflow_complete=WorkflowCompletePayload(
                workflow_capsule_id="wf_test",
                workflow_name="Test Workflow",
                workflow_type="linear",
                total_steps=2,
                step_capsule_ids=["caps_1", "caps_2"],
                started_at=now,
                completed_at=now,
            ),
        )
        assert capsule.capsule_type == CapsuleType.WORKFLOW_COMPLETE


class TestAttributionAggregator:
    """Test attribution aggregation functionality."""

    def test_aggregate_empty_attributions(self):
        """Test aggregating empty attribution list."""
        result = aggregate_attributions([])
        assert result["step_count"] == 0
        assert result["contributors"] == []

    def test_aggregate_single_attribution(self):
        """Test aggregating single attribution."""
        attributions = [
            {
                "contributors": [
                    {"agent_id": "agent_1", "role": "creator", "weight": 1.0}
                ],
                "upstream_capsules": [],
            }
        ]
        result = aggregate_attributions(attributions)
        assert result["step_count"] == 1
        assert len(result["contributors"]) == 1
        assert result["contributors"][0]["agent_id"] == "agent_1"
        assert result["contributors"][0]["weight"] == 1.0

    def test_aggregate_multiple_attributions(self):
        """Test aggregating multiple attributions."""
        attributions = [
            {
                "contributors": [
                    {"agent_id": "agent_1", "role": "creator", "weight": 1.0}
                ],
            },
            {
                "contributors": [
                    {"agent_id": "agent_1", "role": "modifier", "weight": 0.5},
                    {"agent_id": "agent_2", "role": "reviewer", "weight": 0.5},
                ],
            },
            {
                "contributors": [
                    {"agent_id": "agent_2", "role": "creator", "weight": 1.0}
                ],
            },
        ]
        result = aggregate_attributions(attributions)
        assert result["step_count"] == 3
        assert len(result["contributors"]) == 2

        # agent_1: 1.0 + 0.5 = 1.5
        # agent_2: 0.5 + 1.0 = 1.5
        # Both should have equal normalized weight
        weights = {c["agent_id"]: c["weight"] for c in result["contributors"]}
        assert abs(weights["agent_1"] - weights["agent_2"]) < 0.01


class TestDAGMerging:
    """Test DAG construction from step capsules."""

    def test_merge_linear_dag(self):
        """Test merging linear workflow steps."""
        steps = [
            {
                "step_index": 0,
                "step_type": "plan",
                "capsule_id": "c0",
                "depends_on_steps": [],
            },
            {
                "step_index": 1,
                "step_type": "tool_call",
                "capsule_id": "c1",
                "depends_on_steps": [0],
            },
            {
                "step_index": 2,
                "step_type": "output",
                "capsule_id": "c2",
                "depends_on_steps": [1],
            },
        ]
        dag = merge_dag_definitions(steps)
        assert dag["total_steps"] == 3
        assert len(dag["edges"]) == 2
        assert dag["entry_points"] == [0]
        assert dag["exit_points"] == [2]

    def test_merge_parallel_dag(self):
        """Test merging parallel workflow steps."""
        steps = [
            {
                "step_index": 0,
                "step_type": "plan",
                "capsule_id": "c0",
                "depends_on_steps": [],
            },
            {
                "step_index": 1,
                "step_type": "tool_call",
                "capsule_id": "c1",
                "depends_on_steps": [],
            },
            {
                "step_index": 2,
                "step_type": "tool_call",
                "capsule_id": "c2",
                "depends_on_steps": [],
            },
            {
                "step_index": 3,
                "step_type": "aggregation",
                "capsule_id": "c3",
                "depends_on_steps": [0, 1, 2],
            },
        ]
        dag = merge_dag_definitions(steps)
        assert dag["total_steps"] == 4
        assert len(dag["edges"]) == 3
        assert set(dag["entry_points"]) == {0, 1, 2}
        assert dag["exit_points"] == [3]

    def test_merge_empty_dag(self):
        """Test merging empty step list."""
        dag = merge_dag_definitions([])
        assert dag["nodes"] == []
        assert dag["edges"] == []
        assert dag["entry_points"] == []
        assert dag["exit_points"] == []


class TestStepContribution:
    """Test step contribution calculation."""

    def test_plan_step_contribution(self):
        """Test contribution for plan step."""
        step = {"step_type": "plan"}
        weight = calculate_step_contribution(step)
        assert weight == 0.8

    def test_tool_call_step_contribution(self):
        """Test contribution for tool_call step."""
        step = {"step_type": "tool_call"}
        weight = calculate_step_contribution(step)
        assert weight == 1.0

    def test_inference_step_contribution(self):
        """Test contribution for inference step."""
        step = {"step_type": "inference"}
        weight = calculate_step_contribution(step)
        assert weight == 1.2

    def test_human_input_step_contribution(self):
        """Test contribution for human_input step."""
        step = {"step_type": "human_input"}
        weight = calculate_step_contribution(step)
        assert weight == 1.5

    def test_step_with_confidence(self):
        """Test contribution with confidence factor."""
        step = {"step_type": "tool_call", "confidence": 1.0}
        weight = calculate_step_contribution(step)
        assert weight == 1.0  # Full confidence

        step = {"step_type": "tool_call", "confidence": 0.5}
        weight = calculate_step_contribution(step)
        assert weight < 1.0  # Reduced by low confidence


class TestWorkflowContext:
    """Test workflow context creation."""

    def test_create_workflow_context(self):
        """Test creating workflow context."""
        ctx = create_workflow_context(
            workflow_id="wf_test",
            workflow_name="Test Workflow",
            step_index=0,
            step_type="plan",
        )
        assert ctx["workflow_id"] == "wf_test"
        assert ctx["workflow_name"] == "Test Workflow"
        assert ctx["step_index"] == 0
        assert "timestamp" in ctx

    def test_workflow_context_in_envelope(self):
        """Test workflow context in UATP envelope."""
        ctx = create_workflow_context(
            workflow_id="wf_test",
            workflow_name="Test",
        )
        envelope = wrap_in_uatp_envelope(
            payload_data={"test": "data"},
            capsule_id="caps_test",
            capsule_type="workflow_step",
            workflow_context=ctx,
        )
        assert "workflow_context" in envelope
        assert envelope["_envelope"]["version"] == "7.2"
        assert detect_capsule_version(envelope) == "7.2"


class TestWorkflowChainService:
    """Test WorkflowChainService capsule creation methods."""

    def test_create_workflow_step_capsule(self):
        """Test service method for creating workflow step capsule."""
        service = WorkflowChainService()
        capsule = service.create_workflow_step_capsule(
            workflow_capsule_id="wf_test",
            step_index=0,
            step_type="plan",
            step_name="Initial Plan",
            input_data={"task": "test"},
            output_data={"plan": ["step1", "step2"]},
            execution_time_ms=100,
            confidence=0.9,
        )

        assert capsule.capsule_type == CapsuleType.WORKFLOW_STEP
        assert capsule.version == "7.2"
        assert capsule.workflow_step.step_type == "plan"
        assert capsule.workflow_step.step_index == 0

    def test_create_workflow_complete_capsule(self):
        """Test service method for creating workflow complete capsule."""
        service = WorkflowChainService()
        now = datetime.now(timezone.utc)
        capsule = service.create_workflow_complete_capsule(
            workflow_capsule_id="wf_test",
            workflow_name="Test Workflow",
            workflow_type="linear",
            step_capsule_ids=["caps_1", "caps_2", "caps_3"],
            started_at=now,
            completed_at=now,
            aggregated_attribution={"contributors": []},
            dag_definition={"nodes": [], "edges": []},
            final_output={"result": "success"},
            status="completed",
        )

        assert capsule.capsule_type == CapsuleType.WORKFLOW_COMPLETE
        assert capsule.version == "7.2"
        assert capsule.workflow_complete.total_steps == 3
        assert capsule.workflow_complete.status == "completed"
