"""
trace.py - Structured reasoning trace implementation for UATP Capsule Engine.

This module provides classes for representing reasoning traces in a structured,
analyzable format rather than simple strings.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import GetCoreSchemaHandler

# Import Pydantic core components for schema generation
from pydantic_core import PydanticCustomError, core_schema


class StepType(Enum):
    """Types of reasoning steps for more structured analysis."""

    OBSERVATION = "observation"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    EVIDENCE = "evidence"
    CONCLUSION = "conclusion"
    ACTION = "action"
    REFLECTION = "reflection"
    UNCERTAINTY = "uncertainty"


@dataclass
class ReasoningStep:
    """
    A structured reasoning step with type, content, and metadata.
    More analyzable than a simple string.
    """

    content: str
    step_type: StepType = StepType.OBSERVATION
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "content": self.content,
            "step_type": self.step_type.value,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReasoningStep":
        """Create a ReasoningStep from a dictionary."""
        # Handle both string and enum for step_type
        step_type = data.get("step_type", StepType.OBSERVATION.value)
        if isinstance(step_type, str):
            try:
                step_type = StepType(step_type)
            except ValueError:
                step_type = StepType.OBSERVATION

        return cls(
            content=data.get("content", ""),
            step_type=step_type,
            confidence=data.get("confidence", 1.0),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )

    @classmethod
    def from_string(cls, content: str) -> "ReasoningStep":
        """Create a simple ReasoningStep from a string (for backward compatibility)."""
        return cls(content=content)

    def __str__(self) -> str:
        """String representation of the reasoning step."""
        return f"[{self.step_type.value.upper()}] {self.content}"


class ReasoningTrace:
    """
    A structured collection of reasoning steps with analysis capabilities.
    Compatible with Pydantic models through custom schema generation.
    """

    def __init__(self, steps: Optional[List[Any]] = None):
        """
        Initialize a reasoning trace.

        Args:
            steps: Optional list of ReasoningStep objects or dictionaries or strings
        """
        self.steps: List[ReasoningStep] = []

        if steps:
            for step in steps:
                if isinstance(step, ReasoningStep):
                    self.steps.append(step)
                elif isinstance(step, dict):
                    self.steps.append(ReasoningStep.from_dict(step))
                elif isinstance(step, str):
                    self.steps.append(ReasoningStep.from_string(step))

    def add_step(self, step: Any) -> None:
        """
        Add a step to the reasoning trace.

        Args:
            step: A ReasoningStep, dictionary, or string
        """
        if isinstance(step, ReasoningStep):
            self.steps.append(step)
        elif isinstance(step, dict):
            self.steps.append(ReasoningStep.from_dict(step))
        elif isinstance(step, str):
            self.steps.append(ReasoningStep.from_string(step))
        else:
            raise TypeError("Step must be a ReasoningStep, dictionary, or string")

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert to a list of dictionaries."""
        return [step.to_dict() for step in self.steps]

    def to_string_list(self) -> List[str]:
        """Convert to a list of strings (for backward compatibility)."""
        return [str(step) for step in self.steps]

    @classmethod
    def from_dict_list(cls, data: List[Dict[str, Any]]) -> "ReasoningTrace":
        """Create a ReasoningTrace from a list of dictionaries."""
        return cls(steps=[ReasoningStep.from_dict(item) for item in data])

    @classmethod
    def from_string_list(cls, data: List[str]) -> "ReasoningTrace":
        """Create a ReasoningTrace from a list of strings (for backward compatibility)."""
        return cls(steps=[ReasoningStep.from_string(item) for item in data])

    def __len__(self) -> int:
        """Get the number of steps in the trace."""
        return len(self.steps)

    def __getitem__(self, index: int) -> ReasoningStep:
        """Get a step by index."""
        return self.steps[index]

    def __iter__(self):
        """Iterate over steps."""
        return iter(self.steps)

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, handler: GetCoreSchemaHandler):
        """Generate a Pydantic schema for this custom type using a single validator."""

        def validate(value: Any) -> "ReasoningTrace":
            """Validate input from various formats."""
            if isinstance(value, cls):
                return value
            if isinstance(value, list):
                if not value:  # Handle empty list
                    return cls(steps=[])
                # Check if it's a list of dicts (structured) or strings (legacy)
                if isinstance(value[0], dict):
                    return cls.from_dict_list(value)
                if isinstance(value[0], str):
                    return cls.from_string_list(value)

            # If validation fails, raise a custom error
            raise PydanticCustomError(
                "reasoning_trace_validation",
                "Input must be a ReasoningTrace instance, a list of dicts, or a list of strings",
            )

        # Schema for validating input
        from_input_schema = core_schema.no_info_plain_validator_function(validate)

        # Schema for serializing the object back to a JSON-compatible format
        to_json_schema = core_schema.plain_serializer_function_ser_schema(
            lambda instance: instance.to_dict_list(), info_arg=False, when_used="json"
        )

        # Combine validation and serialization
        return core_schema.json_or_python_schema(
            python_schema=from_input_schema,
            json_schema=from_input_schema,  # Use the same validator for JSON input
            serialization=to_json_schema,
        )

    def get_step_types(self) -> Dict[StepType, int]:
        """Count the occurrences of each step type."""
        counts = {step_type: 0 for step_type in StepType}
        for step in self.steps:
            counts[step.step_type] = counts.get(step.step_type, 0) + 1
        return counts

    def get_average_confidence(self) -> float:
        """Calculate the average confidence across all steps."""
        if not self.steps:
            return 0.0
        return sum(step.confidence for step in self.steps) / len(self.steps)

    def has_conclusion(self) -> bool:
        """Check if the trace has at least one conclusion step."""
        return any(step.step_type == StepType.CONCLUSION for step in self.steps)

    def get_conclusion_steps(self) -> List[ReasoningStep]:
        """Get all conclusion steps."""
        return [step for step in self.steps if step.step_type == StepType.CONCLUSION]
