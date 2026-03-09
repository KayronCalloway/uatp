"""
UATP Reference Capsules

This module provides reference implementations of high-quality capsules
that demonstrate optimal scoring in the CQSS system.
"""

import json
import uuid
from datetime import datetime
from typing import List, Optional

from capsule_schema import Capsule
from capsules.specialized_capsules import (
    EconomicCapsule,
    RemixCapsule,
)


# Stub crypto functions to replace missing crypto.crypto_utils module
def generate_key_pair():
    """Stub function to generate a mock key pair."""
    mock_private_key = "mock_private_key_for_reference_capsules"
    mock_public_key = "mock_public_key_for_reference_capsules"
    return mock_private_key, mock_public_key


def sign_message(message, private_key):
    """Stub function to generate a mock signature."""
    return f"mock_signature_for_{hash(message)}_with_{hash(private_key)}"


class ReferenceCapsulesFactory:
    """Factory class to create reference high-quality capsules."""

    @staticmethod
    def create_ideal_capsule() -> Capsule:
        """Create an ideal reference capsule with perfect CQSS scoring components.

        Returns:
            A capsule with optimal signature, reasoning, confidence, and ethical policy components.
        """
        # Generate a proper key pair for strong signature
        private_key, public_key = generate_key_pair()

        # Create base capsule data
        capsule_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Create robust reasoning trace
        reasoning_trace = {
            "process": "methodical",
            "steps": [
                {
                    "step": 1,
                    "description": "Analyze user request for intent and constraints",
                    "outcome": "Clear intent identified with explicit ethical boundaries",
                    "confidence": 0.98,
                },
                {
                    "step": 2,
                    "description": "Review available information and knowledge",
                    "outcome": "Comprehensive information gathered from authoritative sources",
                    "confidence": 0.95,
                },
                {
                    "step": 3,
                    "description": "Generate multiple solution approaches",
                    "outcome": "Three distinct approaches considered with pros/cons analysis",
                    "confidence": 0.92,
                },
                {
                    "step": 4,
                    "description": "Evaluate solutions against ethical frameworks",
                    "outcome": "Selected approach passes all ethical policy checks",
                    "confidence": 0.97,
                },
                {
                    "step": 5,
                    "description": "Implement chosen solution with safeguards",
                    "outcome": "Implemented with monitoring and fallback mechanisms",
                    "confidence": 0.96,
                },
            ],
            "justification": "The chosen approach maximizes utility while respecting key ethical constraints. Alternative approaches were rejected due to potential negative externalities.",
            "citations": [
                {"source": "UATP Ethical Framework v7.2", "section": "3.1.4"},
                {"source": "Trust & Safety Guidelines", "section": "Principle 5"},
            ],
            "confidence_overall": 0.95,
        }

        # Create strong ethical policy validation
        ethical_policy = {
            "framework": "UATP Ethical Standard v7",
            "policies_checked": [
                {
                    "policy": "informed_consent",
                    "compliant": True,
                    "evidence": "Explicit user consent obtained at step 1",
                },
                {
                    "policy": "transparency",
                    "compliant": True,
                    "evidence": "Full reasoning disclosure in capsule metadata",
                },
                {
                    "policy": "accountability",
                    "compliant": True,
                    "evidence": "Clear agent attribution in capsule",
                },
                {
                    "policy": "fairness",
                    "compliant": True,
                    "evidence": "Solution checked against bias metrics",
                },
                {
                    "policy": "safety",
                    "compliant": True,
                    "evidence": "Implementation includes monitoring safeguards",
                },
            ],
            "validation_level": "comprehensive",
            "validation_timestamp": timestamp,
            "validation_authority": "UATP Policy Engine v7.2.1",
        }

        # Create message to sign
        message = {
            "capsule_id": capsule_id,
            "timestamp": timestamp,
            "reasoning_trace": reasoning_trace,
            "ethical_policy": ethical_policy,
            "agent_id": "reference_agent_001",
        }

        # Create cryptographic signature
        signature = sign_message(json.dumps(message), private_key)

        # Assemble the ideal capsule
        ideal_capsule = Capsule(
            capsule_id=capsule_id,
            timestamp=timestamp,
            capsule_type="reference",
            agent_id="reference_agent_001",
            signature=signature,
            public_key=public_key,
            metadata={
                "reasoning_trace": reasoning_trace,
                "ethical_policy": ethical_policy,
                "confidence_score": 0.95,
                "version": "UATP 7.0",
                "purpose": "Reference implementation of ideal capsule",
            },
        )

        return ideal_capsule

    @staticmethod
    def create_ideal_economic_capsule() -> EconomicCapsule:
        """Create an ideal reference economic capsule with perfect attribution.

        Returns:
            An economic capsule with optimal value attribution structure.
        """
        # Generate a proper key pair for strong signature
        private_key, public_key = generate_key_pair()

        # Create base capsule data
        capsule_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Create robust economic data
        economic_event_type = "value_creation"
        value_amount = 1000.0

        # Create detailed attribution structure
        resource_allocation = {
            "source": "reference_agent_001",
            "attribution_model": "proportional_contribution",
            "provenance": {"original_work": True, "derived_works": []},
        }

        # Create value recipients with proper shares
        value_recipients = [
            {
                "agent": "reference_agent_001",
                "share": 0.7,
                "attribution_type": "creator",
            },
            {
                "agent": "reference_agent_002",
                "share": 0.2,
                "attribution_type": "validator",
            },
            {"agent": "platform", "share": 0.1, "attribution_type": "infrastructure"},
        ]

        # Create message to sign
        message = {
            "capsule_id": capsule_id,
            "timestamp": timestamp,
            "economic_event_type": economic_event_type,
            "value_amount": value_amount,
            "resource_allocation": resource_allocation,
            "value_recipients": value_recipients,
            "agent_id": "reference_agent_001",
        }

        # Create cryptographic signature
        signature = sign_message(json.dumps(message), private_key)

        # Assemble the ideal economic capsule
        ideal_economic_capsule = EconomicCapsule(
            capsule_id=capsule_id,
            timestamp=timestamp,
            agent_id="reference_agent_001",
            signature=signature,
            public_key=public_key,
            economic_event_type=economic_event_type,
            value_amount=value_amount,
            resource_allocation=resource_allocation,
            value_recipients=value_recipients,
            metadata={
                "version": "UATP 7.0",
                "purpose": "Reference implementation of ideal economic capsule",
                "dividend_model": "residual_rights",
                "value_type": "original_creation",
            },
        )

        return ideal_economic_capsule

    @staticmethod
    def create_ideal_remix_capsule() -> RemixCapsule:
        """Create an ideal reference remix capsule with perfect attribution.

        Returns:
            A remix capsule with optimal attribution structure.
        """
        # Generate key pair
        private_key, public_key = generate_key_pair()

        # Create base capsule data
        capsule_id = str(uuid.uuid4())
        source_capsule_id = str(uuid.uuid4())  # Original capsule being remixed
        timestamp = datetime.now().isoformat()

        # Create robust reasoning trace
        reasoning_trace = {
            "process": "attribution-aware",
            "steps": [
                {
                    "step": 1,
                    "description": "Identify source material and rights",
                    "outcome": "Source capsule properly identified with clear rights",
                    "confidence": 0.99,
                },
                {
                    "step": 2,
                    "description": "Analyze transformative elements",
                    "outcome": "New creative elements clearly distinguished from source",
                    "confidence": 0.97,
                },
                {
                    "step": 3,
                    "description": "Apply attribution model",
                    "outcome": "Fair attribution model selected based on contribution weight",
                    "confidence": 0.98,
                },
            ],
            "justification": "The remix builds substantially on the original work while adding significant new value. Attribution is proportional to creative contribution.",
            "confidence_overall": 0.98,
        }

        # Attribution structure
        attribution = {
            "source_capsule": source_capsule_id,
            "source_agent": "reference_agent_002",
            "contribution_ratio": 0.6,  # Original contributed 60% of value
            "transformation_type": "enhancement",
            "new_elements": [
                "improved_reasoning",
                "expanded_application",
                "refined_methodology",
            ],
        }

        # Create message to sign
        message = {
            "capsule_id": capsule_id,
            "timestamp": timestamp,
            "source_capsule_id": source_capsule_id,
            "attribution": attribution,
            "agent_id": "reference_agent_001",
            "reasoning_trace": reasoning_trace,
        }

        # Create cryptographic signature
        signature = sign_message(json.dumps(message), private_key)

        # Assemble the ideal remix capsule
        ideal_remix_capsule = RemixCapsule(
            capsule_id=capsule_id,
            timestamp=timestamp,
            agent_id="reference_agent_001",
            signature=signature,
            public_key=public_key,
            source_capsule_id=source_capsule_id,
            attribution=attribution,
            metadata={
                "reasoning_trace": reasoning_trace,
                "version": "UATP 7.0",
                "purpose": "Reference implementation of ideal remix capsule",
            },
        )

        return ideal_remix_capsule

    @staticmethod
    def create_reference_capsule_set() -> List[Capsule]:
        """Create a complete set of reference capsules demonstrating ideal implementations.

        Returns:
            A list of reference capsules
        """
        capsules = [
            ReferenceCapsulesFactory.create_ideal_capsule(),
            ReferenceCapsulesFactory.create_ideal_economic_capsule(),
            ReferenceCapsulesFactory.create_ideal_remix_capsule(),
        ]

        return capsules


def get_reference_capsule(capsule_type: str = "ideal") -> Optional[Capsule]:
    """Get a specific reference capsule by type.

    Args:
        capsule_type: Type of reference capsule to retrieve ("ideal", "economic", "remix")

    Returns:
        The requested reference capsule or None if type not found
    """
    if capsule_type == "ideal":
        return ReferenceCapsulesFactory.create_ideal_capsule()
    elif capsule_type == "economic":
        return ReferenceCapsulesFactory.create_ideal_economic_capsule()
    elif capsule_type == "remix":
        return ReferenceCapsulesFactory.create_ideal_remix_capsule()
    else:
        return None
