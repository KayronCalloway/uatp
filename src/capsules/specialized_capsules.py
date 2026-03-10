"""
Stub classes for backward compatibility with the visualizer.

These are placeholder classes to maintain compatibility with older visualizer code
that expects these specialized capsule types. In the new UATP 7.0 schema,
all capsules are based on the polymorphic AnyCapsule type.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SpecializedCapsule(BaseModel):
    """Base stub class for specialized capsules."""

    id: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[dict] = None


class RefusalCapsule(SpecializedCapsule):
    """Stub for refusal capsules - now handled by ethics circuit breaker."""

    reason: Optional[str] = None
    explanation: Optional[str] = None


class IntrospectiveCapsule(SpecializedCapsule):
    """Stub for introspective capsules."""

    reflection: Optional[str] = None


class JointCapsule(SpecializedCapsule):
    """Stub for joint capsules."""

    participants: Optional[list] = None


class MetaCapsule(SpecializedCapsule):
    """Stub for meta capsules."""

    about_capsule: Optional[str] = None


class InfluenceCapsule(SpecializedCapsule):
    """Stub for influence capsules."""

    influence_type: Optional[str] = None


class PerspectiveCapsule(SpecializedCapsule):
    """Stub for perspective capsules."""

    perspective: Optional[str] = None


class LifecycleCapsule(SpecializedCapsule):
    """Stub for lifecycle capsules."""

    stage: Optional[str] = None


class EmbodiedCapsule(SpecializedCapsule):
    """Stub for embodied capsules."""

    embodiment_data: Optional[dict] = None


class AncestralKnowledgeCapsule(SpecializedCapsule):
    """Stub for ancestral knowledge capsules."""

    knowledge_lineage: Optional[list] = None


class CapsuleExpirationCapsule(SpecializedCapsule):
    """Stub for capsule expiration capsules."""

    expiry_date: Optional[str] = None


class ConsentCapsule(SpecializedCapsule):
    """Stub for consent capsules."""

    consent_given: Optional[bool] = None


class EconomicCapsule(SpecializedCapsule):
    """Stub for economic capsules."""

    transaction_data: Optional[dict] = None


class GovernanceCapsule(SpecializedCapsule):
    """Stub for governance capsules."""

    governance_action: Optional[str] = None


class ImplicitConsentCapsule(SpecializedCapsule):
    """Stub for implicit consent capsules."""

    consent_implied: Optional[bool] = None


class ReferenceCapsule(SpecializedCapsule):
    """Stub for reference capsules."""

    reference_id: Optional[str] = None


class RemixCapsule(SpecializedCapsule):
    """Stub for remix capsules."""

    original_capsule: Optional[str] = None


class SelfHallucinationCapsule(SpecializedCapsule):
    """Stub for self hallucination capsules."""

    hallucination_data: Optional[dict] = None


class SimulatedMaliceCapsule(SpecializedCapsule):
    """Stub for simulated malice capsules."""

    malice_simulation: Optional[dict] = None


class TemporalSignatureCapsule(SpecializedCapsule):
    """Stub for temporal signature capsules."""

    temporal_data: Optional[dict] = None


class TrustRenewalCapsule(SpecializedCapsule):
    """Stub for trust renewal capsules."""

    trust_level: Optional[str] = None


class ValueInceptionCapsule(SpecializedCapsule):
    """Stub for value inception capsules."""

    value_data: Optional[dict] = None


class AttributionCapsule(SpecializedCapsule):
    """Stub for attribution capsules."""

    attribution_scores: Optional[dict] = None
    value_distribution: Optional[dict] = None
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None


# For compatibility - these classes are no longer used in the main engine
# but the visualizer may still reference them
__all__ = [
    "SpecializedCapsule",
    "RefusalCapsule",
    "IntrospectiveCapsule",
    "JointCapsule",
    "MetaCapsule",
    "InfluenceCapsule",
    "PerspectiveCapsule",
    "LifecycleCapsule",
    "EmbodiedCapsule",
    "AncestralKnowledgeCapsule",
    "CapsuleExpirationCapsule",
    "ConsentCapsule",
    "EconomicCapsule",
    "GovernanceCapsule",
    "ImplicitConsentCapsule",
    "ReferenceCapsule",
    "RemixCapsule",
    "SelfHallucinationCapsule",
    "SimulatedMaliceCapsule",
    "TemporalSignatureCapsule",
    "TrustRenewalCapsule",
    "ValueInceptionCapsule",
    "AttributionCapsule",
    "create_specialized_capsule",
]


def create_specialized_capsule(
    capsule_type: str, data: dict, metadata: dict = None
) -> SpecializedCapsule:
    """
    Create a specialized capsule instance.

    Args:
        capsule_type: Type of capsule to create
        data: Capsule data
        metadata: Additional metadata

    Returns:
        SpecializedCapsule instance
    """
    capsule_id = str(uuid.uuid4())

    # Map capsule types to classes
    capsule_classes = {
        "authentication_event": SpecializedCapsule,
        "compliance_validation": SpecializedCapsule,
        "custom_model_interaction": SpecializedCapsule,
        "edge_optimization": SpecializedCapsule,
        "multimodal_interaction": SpecializedCapsule,
        "reasoning_chain": SpecializedCapsule,
        "refusal": RefusalCapsule,
        "consent": ConsentCapsule,
        "economic": EconomicCapsule,
        "governance": GovernanceCapsule,
        "attribution": AttributionCapsule,
    }

    capsule_class = capsule_classes.get(capsule_type, SpecializedCapsule)

    # Create capsule with standardized fields
    capsule_data = {
        "id": capsule_id,
        "content": str(data),
        "metadata": {
            "type": capsule_type,
            "created_at": datetime.now().isoformat(),
            "data": data,
            **(metadata or {}),
        },
    }

    return capsule_class(**capsule_data)
