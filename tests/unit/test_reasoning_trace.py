"""
Unit tests for Reasoning Trace.
"""

import pytest

from src.reasoning.trace import ReasoningStep, ReasoningTrace, StepType


class TestStepType:
    """Tests for StepType enum."""

    def test_step_type_values(self):
        """Test step type values."""
        assert StepType.OBSERVATION.value == "observation"
        assert StepType.INFERENCE.value == "inference"
        assert StepType.HYPOTHESIS.value == "hypothesis"
        assert StepType.EVIDENCE.value == "evidence"
        assert StepType.CONCLUSION.value == "conclusion"
        assert StepType.ACTION.value == "action"
        assert StepType.REFLECTION.value == "reflection"
        assert StepType.UNCERTAINTY.value == "uncertainty"

    def test_all_step_types_exist(self):
        """Test all expected step types exist."""
        expected = [
            "OBSERVATION",
            "INFERENCE",
            "HYPOTHESIS",
            "EVIDENCE",
            "CONCLUSION",
            "ACTION",
            "REFLECTION",
            "UNCERTAINTY",
        ]
        for t in expected:
            assert hasattr(StepType, t)


class TestReasoningStep:
    """Tests for ReasoningStep dataclass."""

    def test_create_reasoning_step(self):
        """Test creating a reasoning step."""
        step = ReasoningStep(content="The sky is blue")

        assert step.content == "The sky is blue"
        assert step.step_type == StepType.OBSERVATION
        assert step.confidence == 1.0
        assert step.metadata == {}
        assert step.timestamp is not None

    def test_create_with_type(self):
        """Test creating a reasoning step with specific type."""
        step = ReasoningStep(
            content="Therefore X is true",
            step_type=StepType.CONCLUSION,
        )

        assert step.step_type == StepType.CONCLUSION

    def test_create_with_confidence(self):
        """Test creating a reasoning step with confidence."""
        step = ReasoningStep(
            content="Hypothesis",
            step_type=StepType.HYPOTHESIS,
            confidence=0.75,
        )

        assert step.confidence == 0.75

    def test_create_with_metadata(self):
        """Test creating a reasoning step with metadata."""
        step = ReasoningStep(
            content="Evidence found",
            step_type=StepType.EVIDENCE,
            metadata={"source": "document.pdf", "page": 5},
        )

        assert step.metadata["source"] == "document.pdf"
        assert step.metadata["page"] == 5

    def test_to_dict(self):
        """Test converting step to dictionary."""
        step = ReasoningStep(
            content="Test content",
            step_type=StepType.INFERENCE,
            confidence=0.9,
        )

        d = step.to_dict()

        assert d["content"] == "Test content"
        assert d["step_type"] == "inference"
        assert d["confidence"] == 0.9
        assert "timestamp" in d
        assert "metadata" in d

    def test_from_dict(self):
        """Test creating step from dictionary."""
        data = {
            "content": "Test content",
            "step_type": "inference",
            "confidence": 0.9,
            "metadata": {"key": "value"},
            "timestamp": "2026-03-12T10:00:00+00:00",
        }

        step = ReasoningStep.from_dict(data)

        assert step.content == "Test content"
        assert step.step_type == StepType.INFERENCE
        assert step.confidence == 0.9
        assert step.metadata["key"] == "value"

    def test_from_dict_with_enum(self):
        """Test from_dict handles enum values correctly."""
        data = {
            "content": "Test",
            "step_type": StepType.EVIDENCE,  # Passing enum directly
        }

        step = ReasoningStep.from_dict(data)

        # Should handle enum passed directly
        assert step.step_type == StepType.EVIDENCE

    def test_from_dict_invalid_step_type(self):
        """Test from_dict with invalid step type defaults to OBSERVATION."""
        data = {
            "content": "Test",
            "step_type": "invalid_type",
        }

        step = ReasoningStep.from_dict(data)

        assert step.step_type == StepType.OBSERVATION

    def test_from_dict_missing_fields(self):
        """Test from_dict with missing fields uses defaults."""
        data = {"content": "Test"}

        step = ReasoningStep.from_dict(data)

        assert step.content == "Test"
        assert step.step_type == StepType.OBSERVATION
        assert step.confidence == 1.0
        assert step.metadata == {}

    def test_from_string(self):
        """Test creating step from string."""
        step = ReasoningStep.from_string("Simple observation")

        assert step.content == "Simple observation"
        assert step.step_type == StepType.OBSERVATION

    def test_str_representation(self):
        """Test string representation."""
        step = ReasoningStep(
            content="Test content",
            step_type=StepType.CONCLUSION,
        )

        s = str(step)

        assert "[CONCLUSION]" in s
        assert "Test content" in s


class TestReasoningTrace:
    """Tests for ReasoningTrace class."""

    def test_create_empty_trace(self):
        """Test creating an empty trace."""
        trace = ReasoningTrace()

        assert len(trace) == 0
        assert trace.steps == []

    def test_create_with_steps(self):
        """Test creating trace with steps."""
        steps = [
            ReasoningStep(content="Step 1"),
            ReasoningStep(content="Step 2"),
        ]
        trace = ReasoningTrace(steps=steps)

        assert len(trace) == 2

    def test_create_from_dicts(self):
        """Test creating trace from dictionaries."""
        steps = [
            {"content": "Step 1", "step_type": "observation"},
            {"content": "Step 2", "step_type": "inference"},
        ]
        trace = ReasoningTrace(steps=steps)

        assert len(trace) == 2
        assert trace[0].step_type == StepType.OBSERVATION
        assert trace[1].step_type == StepType.INFERENCE

    def test_create_from_strings(self):
        """Test creating trace from strings."""
        steps = ["First step", "Second step"]
        trace = ReasoningTrace(steps=steps)

        assert len(trace) == 2
        assert trace[0].content == "First step"

    def test_add_step_reasoning_step(self):
        """Test adding a ReasoningStep."""
        trace = ReasoningTrace()
        step = ReasoningStep(content="New step")

        trace.add_step(step)

        assert len(trace) == 1
        assert trace[0].content == "New step"

    def test_add_step_dict(self):
        """Test adding a dictionary."""
        trace = ReasoningTrace()

        trace.add_step({"content": "Dict step", "step_type": "inference"})

        assert len(trace) == 1
        assert trace[0].step_type == StepType.INFERENCE

    def test_add_step_string(self):
        """Test adding a string."""
        trace = ReasoningTrace()

        trace.add_step("String step")

        assert len(trace) == 1
        assert trace[0].content == "String step"

    def test_add_step_invalid_type(self):
        """Test adding invalid type raises error."""
        trace = ReasoningTrace()

        with pytest.raises(TypeError):
            trace.add_step(123)

    def test_to_dict_list(self):
        """Test converting trace to list of dictionaries."""
        trace = ReasoningTrace(steps=["Step 1", "Step 2"])

        result = trace.to_dict_list()

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["content"] == "Step 1"

    def test_to_string_list(self):
        """Test converting trace to list of strings."""
        trace = ReasoningTrace(
            steps=[
                ReasoningStep(content="Step 1", step_type=StepType.OBSERVATION),
                ReasoningStep(content="Step 2", step_type=StepType.CONCLUSION),
            ]
        )

        result = trace.to_string_list()

        assert isinstance(result, list)
        assert len(result) == 2
        assert "[OBSERVATION]" in result[0]
        assert "[CONCLUSION]" in result[1]

    def test_from_dict_list(self):
        """Test creating trace from list of dictionaries."""
        data = [
            {"content": "Step 1", "step_type": "observation"},
            {"content": "Step 2", "step_type": "conclusion"},
        ]

        trace = ReasoningTrace.from_dict_list(data)

        assert len(trace) == 2
        assert trace[1].step_type == StepType.CONCLUSION

    def test_from_string_list(self):
        """Test creating trace from list of strings."""
        data = ["Step 1", "Step 2", "Step 3"]

        trace = ReasoningTrace.from_string_list(data)

        assert len(trace) == 3
        for step in trace:
            assert step.step_type == StepType.OBSERVATION

    def test_len(self):
        """Test __len__ method."""
        trace = ReasoningTrace(steps=["A", "B", "C"])

        assert len(trace) == 3

    def test_getitem(self):
        """Test __getitem__ method."""
        trace = ReasoningTrace(steps=["First", "Second", "Third"])

        assert trace[0].content == "First"
        assert trace[1].content == "Second"
        assert trace[-1].content == "Third"

    def test_iter(self):
        """Test iteration over trace."""
        trace = ReasoningTrace(steps=["A", "B", "C"])

        contents = [step.content for step in trace]

        assert contents == ["A", "B", "C"]

    def test_get_step_types(self):
        """Test getting step type counts."""
        trace = ReasoningTrace(
            steps=[
                ReasoningStep(content="Obs 1", step_type=StepType.OBSERVATION),
                ReasoningStep(content="Obs 2", step_type=StepType.OBSERVATION),
                ReasoningStep(content="Inf 1", step_type=StepType.INFERENCE),
                ReasoningStep(content="Conc 1", step_type=StepType.CONCLUSION),
            ]
        )

        counts = trace.get_step_types()

        assert counts[StepType.OBSERVATION] == 2
        assert counts[StepType.INFERENCE] == 1
        assert counts[StepType.CONCLUSION] == 1

    def test_get_step_types_empty(self):
        """Test getting step type counts for empty trace."""
        trace = ReasoningTrace()

        counts = trace.get_step_types()

        assert all(count == 0 for count in counts.values())

    def test_get_average_confidence(self):
        """Test calculating average confidence."""
        trace = ReasoningTrace(
            steps=[
                ReasoningStep(content="A", confidence=0.8),
                ReasoningStep(content="B", confidence=0.6),
                ReasoningStep(content="C", confidence=1.0),
            ]
        )

        avg = trace.get_average_confidence()

        assert avg == pytest.approx(0.8, rel=0.01)

    def test_get_average_confidence_empty(self):
        """Test average confidence for empty trace."""
        trace = ReasoningTrace()

        avg = trace.get_average_confidence()

        assert avg == 0.0

    def test_has_conclusion_true(self):
        """Test has_conclusion returns True when conclusion exists."""
        trace = ReasoningTrace(
            steps=[
                ReasoningStep(content="Obs", step_type=StepType.OBSERVATION),
                ReasoningStep(content="Conc", step_type=StepType.CONCLUSION),
            ]
        )

        assert trace.has_conclusion() is True

    def test_has_conclusion_false(self):
        """Test has_conclusion returns False when no conclusion."""
        trace = ReasoningTrace(
            steps=[
                ReasoningStep(content="Obs", step_type=StepType.OBSERVATION),
                ReasoningStep(content="Inf", step_type=StepType.INFERENCE),
            ]
        )

        assert trace.has_conclusion() is False

    def test_has_conclusion_empty(self):
        """Test has_conclusion for empty trace."""
        trace = ReasoningTrace()

        assert trace.has_conclusion() is False

    def test_get_conclusion_steps(self):
        """Test getting conclusion steps."""
        trace = ReasoningTrace(
            steps=[
                ReasoningStep(content="Obs", step_type=StepType.OBSERVATION),
                ReasoningStep(content="Conc 1", step_type=StepType.CONCLUSION),
                ReasoningStep(content="Inf", step_type=StepType.INFERENCE),
                ReasoningStep(content="Conc 2", step_type=StepType.CONCLUSION),
            ]
        )

        conclusions = trace.get_conclusion_steps()

        assert len(conclusions) == 2
        assert conclusions[0].content == "Conc 1"
        assert conclusions[1].content == "Conc 2"

    def test_get_conclusion_steps_none(self):
        """Test getting conclusion steps when none exist."""
        trace = ReasoningTrace(steps=["Observation 1", "Observation 2"])

        conclusions = trace.get_conclusion_steps()

        assert conclusions == []


class TestReasoningTracePydantic:
    """Tests for Pydantic integration."""

    def test_pydantic_schema_exists(self):
        """Test that Pydantic schema method exists."""
        assert hasattr(ReasoningTrace, "__get_pydantic_core_schema__")

    def test_from_empty_list(self):
        """Test creating trace from empty list."""
        trace = ReasoningTrace(steps=[])

        assert len(trace) == 0
