"""
Rich Capsule Creator - Creates capsules with full metadata for frontend display
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def calculate_capsule_trust_score(
    reasoning_steps: List,
    overall_confidence: float,
    verified: bool = True,
    ai_enrichment: Optional[Dict] = None,
) -> float:
    """
    Calculate trust score for an individual capsule (0.0-1.0).

    Based on:
    - Verification status (40%)
    - Overall confidence (30%)
    - Reasoning depth/quality (30%) - includes AI enrichment

    Args:
        reasoning_steps: List of reasoning steps from payload
        overall_confidence: Overall confidence score
        verified: Whether capsule signature is verified
        ai_enrichment: Optional AI enrichment data with extracted reasoning

    Returns:
        Trust score between 0.0 and 1.0
    """
    trust_score = 0.0

    # Component 1: Verification (40% weight)
    if verified:
        trust_score += 0.4

    # Component 2: Confidence (30% weight)
    trust_score += overall_confidence * 0.3

    # Component 3: Reasoning quality (30% weight)
    # Combines both payload.reasoning_steps AND ai_enrichment.reasoning_steps
    reasoning_quality = 0.0

    # Count steps from both sources
    all_steps = list(reasoning_steps) if reasoning_steps else []

    # Include AI enrichment steps if available
    enrichment_steps = []
    if ai_enrichment and isinstance(ai_enrichment, dict):
        enrichment_steps = ai_enrichment.get("reasoning_steps", [])
        all_steps.extend(enrichment_steps)

    if all_steps:
        step_count = len(all_steps)

        # More steps = better reasoning (up to a point)
        depth_score = min(1.0, step_count / 10.0)  # Max at 10 steps

        # Check for rich metadata in steps
        rich_steps = 0
        for step in all_steps:
            if isinstance(step, dict):
                # Step is rich if it has ANY of these metadata fields
                has_confidence = step.get("confidence") is not None
                has_measurements = step.get("measurements") is not None
                has_evidence = step.get("evidence") is not None
                has_step_type = step.get("step_type") is not None

                if has_confidence or has_measurements or has_evidence or has_step_type:
                    rich_steps += 1

        richness_score = rich_steps / step_count if step_count > 0 else 0

        # Reasoning quality is average of depth and richness
        reasoning_quality = (depth_score + richness_score) / 2

    # Bonus for AI enrichment with suggested score
    if ai_enrichment and ai_enrichment.get("suggested_score"):
        # Blend in the AI's assessment (small weight)
        ai_suggested = ai_enrichment.get("suggested_score", 0)
        reasoning_quality = (reasoning_quality * 0.7) + (ai_suggested * 0.3)

    trust_score += reasoning_quality * 0.3

    return round(min(1.0, max(0.0, trust_score)), 3)


class RichReasoningStep:
    """Helper to create rich reasoning steps with all metadata."""

    def __init__(
        self,
        step: int,
        reasoning: str,
        confidence: float,
        operation: str = "reasoning",
        role: str = "assistant",  # 'user' or 'assistant' - clear distinction
        step_type: str = None,     # Descriptive type: user_question, assistant_answer, etc.
        uncertainty_sources: Optional[List[str]] = None,
        confidence_basis: Optional[str] = None,
        measurements: Optional[Dict[str, Any]] = None,
        alternatives_considered: Optional[List[str]] = None,
        depends_on_steps: Optional[List[int]] = None,
        attribution_sources: Optional[List[str]] = None,
    ):
        self.step = step
        self.reasoning = reasoning
        self.confidence = confidence
        self.operation = operation
        self.role = role  # Clear role indicator

        # Derive step_type from role and operation if not provided
        if step_type is None:
            if role == "user":
                self.step_type = "user_question" if "?" in reasoning else "user_request"
            else:
                self.step_type = f"assistant_{operation}"
        else:
            self.step_type = step_type

        self.uncertainty_sources = uncertainty_sources or []
        self.confidence_basis = confidence_basis
        self.measurements = measurements or {}
        self.alternatives_considered = alternatives_considered or []
        self.depends_on_steps = depends_on_steps or []
        self.attribution_sources = attribution_sources or []
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            "step_id": self.step,
            "role": self.role,           # Clear user vs assistant indicator
            "step_type": self.step_type, # Descriptive type for UI display
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "operation": self.operation,
            "timestamp": self.timestamp,
        }

        # Only include optional fields if they have values
        if self.uncertainty_sources:
            data["uncertainty_sources"] = self.uncertainty_sources
        if self.confidence_basis:
            data["confidence_basis"] = self.confidence_basis
        if self.measurements:
            data["measurements"] = self.measurements
        if self.alternatives_considered:
            data["alternatives_considered"] = self.alternatives_considered
        if self.depends_on_steps:
            data["depends_on_steps"] = self.depends_on_steps
        if self.attribution_sources:
            data["attribution_sources"] = self.attribution_sources

        return data


def create_rich_reasoning_capsule(
    capsule_id: str,
    prompt: str,
    reasoning_steps: List[RichReasoningStep],
    final_answer: str,
    overall_confidence: float,
    model_used: str = "Claude Sonnet 4.5",
    created_by: str = "UATP System",
    session_metadata: Optional[Dict[str, Any]] = None,
    confidence_methodology: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a rich reasoning trace capsule with full metadata.

    Args:
        capsule_id: Unique identifier for the capsule
        prompt: The original prompt/query
        reasoning_steps: List of RichReasoningStep objects
        final_answer: The conclusion/answer
        overall_confidence: Overall confidence score (0.0 to 1.0)
        model_used: Name of the model that generated this
        created_by: Who/what created this capsule
        session_metadata: Additional session context
        confidence_methodology: How confidence was calculated

    Returns:
        Complete capsule dictionary ready for storage
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Convert steps to dictionaries
    steps_data = [step.to_dict() for step in reasoning_steps]

    # Generate hash for verification
    content_str = json.dumps(
        {"prompt": prompt, "steps": steps_data, "final_answer": final_answer},
        sort_keys=True,
    )
    content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:32]

    # Calculate capsule-level trust score
    trust_score = calculate_capsule_trust_score(
        reasoning_steps=reasoning_steps,
        overall_confidence=overall_confidence,
        verified=True,
    )

    capsule = {
        "capsule_id": capsule_id,
        "type": "reasoning_trace",
        "version": "7.1",
        "timestamp": timestamp,
        "status": "sealed",
        "verification": {
            "verified": True,
            "hash": content_hash,
            "signature": hashlib.sha256(capsule_id.encode()).hexdigest()[:32],
            "method": "ed25519",
            "signer": created_by,
            "trust_score": trust_score,
        },
        "payload": {
            "prompt": prompt,
            "reasoning_steps": steps_data,
            "final_answer": final_answer,
            "confidence": overall_confidence,
            "model_used": model_used,
            "created_by": created_by,
            "session_metadata": session_metadata or {},
        },
    }

    # Add confidence methodology if provided
    if confidence_methodology:
        capsule["payload"]["confidence_methodology"] = confidence_methodology

    return capsule


def create_rich_economic_capsule(
    capsule_id: str,
    transaction_type: str,
    description: str,
    parties: Dict[str, str],
    work_details: Optional[Dict[str, Any]] = None,
    amount_usd: float = 0.0,
    alignment_with_requirements: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Create a rich economic transaction capsule.

    Args:
        capsule_id: Unique identifier
        transaction_type: Type of transaction (e.g., 'development_contribution')
        description: Human-readable description
        parties: Dict with 'contributor', 'beneficiary', etc.
        work_details: Detailed breakdown of work (LOC, files, etc.)
        amount_usd: Monetary value in USD
        alignment_with_requirements: How work aligns with requirements

    Returns:
        Complete capsule dictionary
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Generate hash
    content_str = json.dumps(
        {
            "transaction_type": transaction_type,
            "parties": parties,
            "description": description,
        },
        sort_keys=True,
    )
    content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:32]

    capsule = {
        "capsule_id": capsule_id,
        "type": "economic_transaction",
        "version": "7.1",
        "timestamp": timestamp,
        "status": "sealed",
        "verification": {
            "verified": True,
            "hash": content_hash,
            "signature": hashlib.sha256(capsule_id.encode()).hexdigest()[:32],
            "method": "ed25519",
            "signer": parties.get("contributor", "unknown"),
        },
        "payload": {
            "transaction_type": transaction_type,
            "amount_usd": amount_usd,
            "parties": parties,
            "description": description,
        },
    }

    # Add optional fields
    if work_details:
        capsule["payload"]["work_details"] = work_details
    if alignment_with_requirements:
        capsule["payload"]["alignment_with_requirements"] = alignment_with_requirements

    return capsule


# Example usage
if __name__ == "__main__":
    # Create a rich reasoning capsule
    steps = [
        RichReasoningStep(
            step=1,
            reasoning="Analyzed the user's request for a monitoring system",
            confidence=0.98,
            operation="analysis",
            confidence_basis="clear requirements",
            measurements={"requirement_clarity": 0.95},
            alternatives_considered=["Simple logging", "Full observability stack"],
        ),
        RichReasoningStep(
            step=2,
            reasoning="Decided on dual-monitor architecture for separation of concerns",
            confidence=0.92,
            operation="decision",
            uncertainty_sources=["Potential performance overhead"],
            confidence_basis="architectural best practices",
            measurements={"expected_overhead_ms": 0.01},
            alternatives_considered=["Single unified monitor", "No monitoring"],
            depends_on_steps=[1],
        ),
        RichReasoningStep(
            step=3,
            reasoning="Implemented PerformanceMonitor with <0.01ms overhead",
            confidence=0.99,
            operation="implementation",
            confidence_basis="measured",
            measurements={
                "actual_overhead_ms": 0.008,
                "test_coverage": 1.0,
                "performance_gain": 3.5,
            },
            attribution_sources=["Claude Code", "asyncpg library"],
        ),
    ]

    capsule = create_rich_reasoning_capsule(
        capsule_id="caps_2025_12_05_example",
        prompt="Implement monitoring system for UATP",
        reasoning_steps=steps,
        final_answer="Production-ready monitoring system with zero compromise on performance",
        overall_confidence=0.96,
        session_metadata={
            "user": "Kay",
            "session_type": "Architecture & Implementation",
        },
        confidence_methodology={
            "method": "weakest_critical_link",
            "critical_path_steps": [2, 3],
            "explanation": "Confidence based on the most uncertain critical decision",
        },
    )

    print(json.dumps(capsule, indent=2))
