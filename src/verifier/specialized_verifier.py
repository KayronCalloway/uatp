"""Specialized verification implementation for UATP 7.0 capsule types.

This module extends the base CapsuleVerifier to provide specialized verification
logic for each of the UATP 7.0 capsule types, implementing their unique
business rules and constraints.
"""

import logging
from datetime import datetime
from typing import List, Tuple, Union

from ..capsule_schema import Capsule
from ..capsules.specialized_capsules import (
    CapsuleExpirationCapsule,
    ConsentCapsule,
    EconomicCapsule,
    GovernanceCapsule,
    ImplicitConsentCapsule,
    RemixCapsule,
    SelfHallucinationCapsule,
    SimulatedMaliceCapsule,
    SpecializedCapsule,
    TemporalSignatureCapsule,
    TrustRenewalCapsule,
    ValueInceptionCapsule,
)
from ..utils.crypto import hash_capsule_dict
from ..utils.crypto import verify_capsule as verify_signature
from .verifier import CapsuleVerifier

logger = logging.getLogger("uatp.verifier.specialized")


class SpecializedCapsuleVerifier(CapsuleVerifier):
    """Enhanced CapsuleVerifier with support for all UATP 7.0 capsule types."""

    @staticmethod
    def verify_capsule(capsule: Union[Capsule, SpecializedCapsule]) -> Tuple[bool, str]:
        """Verify a specialized capsule.

        Args:
            capsule: The capsule to verify.

        Returns:
            Tuple of (is_valid, message)
        """
        # First check hash integrity
        expected_hash = hash_capsule_dict(capsule.to_dict())
        hash_valid = capsule.hash == expected_hash

        if not hash_valid:
            return False, f"Invalid hash for capsule {capsule.capsule_id}"

        # Check signature if available
        signature_valid = True
        if (
            hasattr(capsule, "signature")
            and capsule.signature
            and hasattr(capsule, "metadata")
        ):
            verify_key = capsule.metadata.get("verify_key")
            if verify_key and capsule.signature:
                hash_for_sig = hash_capsule_dict(capsule.to_dict())
                signature_valid = verify_signature(
                    hash_for_sig, capsule.signature, verify_key
                )

        if not signature_valid:
            return False, f"Invalid signature for capsule {capsule.capsule_id}"

        # Dispatch to specialized verification based on capsule type
        capsule_type = capsule.capsule_type

        # Call specialized verification method based on capsule type
        if capsule_type == "Remix":
            return SpecializedCapsuleVerifier.verify_remix_capsule(capsule)
        elif capsule_type == "TemporalSignature":
            return SpecializedCapsuleVerifier.verify_temporal_signature_capsule(capsule)
        elif capsule_type == "ValueInception":
            return SpecializedCapsuleVerifier.verify_value_inception_capsule(capsule)
        elif capsule_type == "SimulatedMalice":
            return SpecializedCapsuleVerifier.verify_simulated_malice_capsule(capsule)
        elif capsule_type == "ImplicitConsent":
            return SpecializedCapsuleVerifier.verify_implicit_consent_capsule(capsule)
        elif capsule_type == "SelfHallucination":
            return SpecializedCapsuleVerifier.verify_self_hallucination_capsule(capsule)
        elif capsule_type == "Consent":
            return SpecializedCapsuleVerifier.verify_consent_capsule(capsule)
        elif capsule_type == "TrustRenewal":
            return SpecializedCapsuleVerifier.verify_trust_renewal_capsule(capsule)
        elif capsule_type == "CapsuleExpiration":
            return SpecializedCapsuleVerifier.verify_capsule_expiration_capsule(capsule)
        elif capsule_type == "Governance":
            return SpecializedCapsuleVerifier.verify_governance_capsule(capsule)
        elif capsule_type == "Economic":
            return SpecializedCapsuleVerifier.verify_economic_capsule(capsule)

        # Default case - basic hash and signature verification already done
        return True, f"Capsule {capsule.capsule_id} verified successfully"

    @staticmethod
    def verify_chain(capsules: List[Capsule]) -> Tuple[bool, str]:
        """Verify a chain of specialized capsules.

        Extends the base verification to add specialized checks between capsules.

        Args:
            capsules: List of capsules in the chain, ordered root → leaf

        Returns:
            Tuple of (is_valid, message)
        """
        # First, run the base chain verification
        valid, msg = CapsuleVerifier.verify_chain(capsules)
        if not valid:
            return valid, msg

        # Then perform specialized verification for each capsule in the chain
        for i, capsule in enumerate(capsules):
            # Skip basic capsule types
            if not isinstance(capsule, SpecializedCapsule):
                continue

            valid, msg = SpecializedCapsuleVerifier.verify_capsule(capsule)
            if not valid:
                return False, f"Specialized verification failed at position {i}: {msg}"

        # Add chain-level verifications here as needed
        # For example, checking temporal sequence consistency across the chain

        # Check for expired capsules
        if not SpecializedCapsuleVerifier._verify_expiration_in_chain(capsules):
            return False, "Chain contains expired capsules without valid replacements"

        # Check for trust renewal validity
        if not SpecializedCapsuleVerifier._verify_trust_renewal_in_chain(capsules):
            return False, "Chain contains invalid trust renewal relationships"

        return True, "Chain verification successful"

    @staticmethod
    def verify_remix_capsule(capsule: RemixCapsule) -> Tuple[bool, str]:
        """Verify a Remix capsule."""
        # Check that all source capsules are referenced
        if not capsule.source_capsule_ids or len(capsule.source_capsule_ids) == 0:
            return False, "Remix capsule must reference at least one source capsule"

        # Check that attribution weights sum to approximately 1.0
        attribution_sum = sum(capsule.attribution_weights.values())
        if abs(attribution_sum - 1.0) > 0.001:  # Allow small floating point errors
            return False, f"Attribution weights must sum to 1.0, got {attribution_sum}"

        # All source IDs should have corresponding weights
        for source_id in capsule.source_capsule_ids:
            if source_id not in capsule.attribution_weights:
                return False, f"Missing attribution weight for source {source_id}"

        return True, "Remix capsule verified successfully"

    @staticmethod
    def verify_temporal_signature_capsule(
        capsule: TemporalSignatureCapsule,
    ) -> Tuple[bool, str]:
        """Verify a Temporal Signature capsule."""
        # Check that the knowledge cutoff is before runtime date
        try:
            cutoff = datetime.fromisoformat(
                capsule.knowledge_cutoff_date.replace("Z", "+00:00")
            )
            runtime = datetime.fromisoformat(
                capsule.runtime_date.replace("Z", "+00:00")
            )

            if cutoff > runtime:
                return False, "Knowledge cutoff date cannot be after runtime date"
        except ValueError:
            return False, "Invalid date format in temporal signature capsule"

        # Check that temporal context contains expected fields
        expected_fields = ["system_clock_source", "temporal_boundary_reason"]
        for field in expected_fields:
            if field not in capsule.temporal_context:
                return False, f"Missing required temporal context field: {field}"

        return True, "Temporal signature capsule verified successfully"

    @staticmethod
    def verify_value_inception_capsule(
        capsule: ValueInceptionCapsule,
    ) -> Tuple[bool, str]:
        """Verify a Value Inception capsule."""
        # Check that value assertions are consistent with framework
        if not capsule.value_framework or not capsule.value_assertions:
            return (
                False,
                "Value inception capsule must have both framework and assertions",
            )

        # Check that values hierarchy is internally consistent
        if len(capsule.values_hierarchy) == 0:
            return False, "Values hierarchy cannot be empty"

        # Check that all tradeoffs reference values in the hierarchy
        all_values = set()
        for item in capsule.values_hierarchy:
            if "value" in item:
                all_values.add(item["value"])

        for tradeoff in capsule.trade_offs:
            if "prioritized" in tradeoff and tradeoff["prioritized"] not in all_values:
                return (
                    False,
                    f"Tradeoff references non-existent value: {tradeoff['prioritized']}",
                )
            if (
                "deprioritized" in tradeoff
                and tradeoff["deprioritized"] not in all_values
            ):
                return (
                    False,
                    f"Tradeoff references non-existent value: {tradeoff['deprioritized']}",
                )

        return True, "Value inception capsule verified successfully"

    @staticmethod
    def verify_simulated_malice_capsule(
        capsule: SimulatedMaliceCapsule,
    ) -> Tuple[bool, str]:
        """Verify a Simulated Malice capsule."""
        # Check that malicious intent is explicitly described
        if not capsule.malicious_intent or not capsule.simulation_purpose:
            return (
                False,
                "Simulated malice capsule must describe both intent and purpose",
            )

        # Check that risk assessment is complete
        required_assessment_fields = ["severity", "likelihood", "countermeasures"]
        for field in required_assessment_fields:
            if field not in capsule.risk_assessment:
                return False, f"Missing required risk assessment field: {field}"

        # Check that authorization is valid
        if not capsule.authorized_by or not capsule.authorization_detail:
            return False, "Simulated malice requires explicit authorization"

        return True, "Simulated malice capsule verified successfully"

    @staticmethod
    def verify_implicit_consent_capsule(
        capsule: ImplicitConsentCapsule,
    ) -> Tuple[bool, str]:
        """Verify an Implicit Consent capsule."""
        # Check that behavioral signals are recorded
        if not capsule.behavioral_signals or len(capsule.behavioral_signals) == 0:
            return False, "Implicit consent must include behavioral signals"

        # Check confidence threshold
        if (
            not hasattr(capsule, "consent_confidence")
            or capsule.consent_confidence < 0.5
        ):
            return (
                False,
                f"Implicit consent requires confidence >= 0.5, got {getattr(capsule, 'consent_confidence', 0)}",
            )

        # Validate interaction context
        if not capsule.interaction_context or not capsule.interaction_context.get(
            "setting"
        ):
            return False, "Interaction context with setting is required"

        return True, "Implicit consent capsule verified successfully"

    @staticmethod
    def verify_self_hallucination_capsule(
        capsule: SelfHallucinationCapsule,
    ) -> Tuple[bool, str]:
        """Verify a Self Hallucination capsule."""
        # Check that affected content and hallucination type are specified
        if not capsule.affected_content or not capsule.hallucination_type:
            return False, "Self hallucination must identify affected content and type"

        # Check that confidence assessment is valid
        if not capsule.confidence_assessment or len(capsule.confidence_assessment) == 0:
            return False, "Self hallucination requires confidence assessment"

        # Check for hallucination markers
        if (
            not capsule.self_hallucination_markers
            or len(capsule.self_hallucination_markers) == 0
        ):
            return (
                False,
                "Self hallucination requires markers to identify hallucination",
            )

        return True, "Self hallucination capsule verified successfully"

    @staticmethod
    def verify_consent_capsule(capsule: ConsentCapsule) -> Tuple[bool, str]:
        """Verify a Consent capsule."""
        # Check that consent is explicitly specified
        if not hasattr(capsule, "consent_given") or capsule.consent_given is None:
            return (
                False,
                "Consent capsule must explicitly specify whether consent is given",
            )

        # Check that scope and conditions are specified
        if not capsule.consent_scope or not capsule.consent_conditions:
            return False, "Consent requires scope and conditions"

        # Check duration format if present
        if capsule.consent_duration:
            # Should match ISO 8601 duration format (simplified check)
            if not (
                capsule.consent_duration.startswith("P")
                or capsule.consent_duration.startswith("-P")
                or capsule.consent_duration.startswith("PT")
            ):
                return (
                    False,
                    f"Invalid ISO 8601 duration format: {capsule.consent_duration}",
                )

        # Check verification method
        if not capsule.consent_verification_method:
            return False, "Consent requires a verification method"

        return True, "Consent capsule verified successfully"

    @staticmethod
    def verify_trust_renewal_capsule(capsule: TrustRenewalCapsule) -> Tuple[bool, str]:
        """Verify a Trust Renewal capsule."""
        # Check that renewal status is specified
        if not hasattr(capsule, "renewal_granted") or capsule.renewal_granted is None:
            return False, "Trust renewal must specify whether renewal is granted"

        # Check that trust subject and criteria are specified
        if not capsule.trust_subject or not capsule.trust_criteria:
            return False, "Trust renewal requires subject and criteria"

        # Check verified claims format
        if not capsule.verified_claims or not isinstance(capsule.verified_claims, list):
            return False, "Trust renewal requires a list of verified claims"

        # Check each verified claim for required structure
        for claim in capsule.verified_claims:
            if not isinstance(claim, dict):
                return False, "Each verified claim must be a dictionary"
            if "claim_type" not in claim or "status" not in claim:
                return False, "Each verified claim requires claim_type and status"

        return True, "Trust renewal capsule verified successfully"

    @staticmethod
    def verify_capsule_expiration_capsule(
        capsule: CapsuleExpirationCapsule,
    ) -> Tuple[bool, str]:
        """Verify a Capsule Expiration capsule."""
        # Check that target capsules are specified
        if not capsule.target_capsule_ids or len(capsule.target_capsule_ids) == 0:
            return False, "Expiration capsule must specify target capsules"

        # Check that expiration type and reason are provided
        if not capsule.expiration_type or not capsule.expiration_reason:
            return False, "Expiration requires type and reason"

        # Check expiration timestamp format
        try:
            datetime.fromisoformat(capsule.expiration_timestamp.replace("Z", "+00:00"))
        except ValueError:
            return (
                False,
                f"Invalid expiration timestamp format: {capsule.expiration_timestamp}",
            )

        # If replacements are provided, check they exist
        if (
            hasattr(capsule, "replacement_capsule_ids")
            and capsule.replacement_capsule_ids
        ):
            if not isinstance(capsule.replacement_capsule_ids, list):
                return False, "Replacement capsule IDs must be a list"

        return True, "Capsule expiration verified successfully"

    @staticmethod
    def verify_governance_capsule(capsule: GovernanceCapsule) -> Tuple[bool, str]:
        """Verify a Governance capsule."""
        # Check that governance action and policy are specified
        if not capsule.governance_action or not capsule.policy_reference:
            return False, "Governance capsule requires action and policy reference"

        # Check affected entities
        if not capsule.affected_entities or len(capsule.affected_entities) == 0:
            return False, "Governance action must affect at least one entity"

        # Check authorization proof
        if not capsule.authorization_proof or len(capsule.authorization_proof) == 0:
            return False, "Governance requires proof of authorization"

        return True, "Governance capsule verified successfully"

    @staticmethod
    def verify_economic_capsule(capsule: EconomicCapsule) -> Tuple[bool, str]:
        """Verify an Economic capsule."""
        # Check that transaction type is valid
        if not capsule.transaction_type:
            return False, "Economic capsule requires transaction type"

        # Check resource allocation and compensation
        if not capsule.resource_allocation or not capsule.compensation_details:
            return (
                False,
                "Economic capsule requires resource allocation and compensation details",
            )

        # Check transaction parties
        if not capsule.transaction_parties or len(capsule.transaction_parties) < 2:
            return False, "Economic transaction requires at least two parties"

        # Check that dividend distribution sums to 1.0 if present
        if hasattr(capsule, "dividend_distribution") and capsule.dividend_distribution:
            dividend_sum = sum(capsule.dividend_distribution.values())
            if abs(dividend_sum - 1.0) > 0.001:  # Allow small floating point errors
                return (
                    False,
                    f"Dividend distribution must sum to 1.0, got {dividend_sum}",
                )

        return True, "Economic capsule verified successfully"

    @staticmethod
    def _verify_expiration_in_chain(capsules: List[Capsule]) -> bool:
        """Check that expired capsules have valid replacements in the chain."""
        # Build ID lookup for quick access
        capsule_id_map = {c.capsule_id: c for c in capsules}

        # Find all expiration capsules
        expiration_capsules = [
            c for c in capsules if getattr(c, "capsule_type", "") == "CapsuleExpiration"
        ]

        # For each expiration, verify that either:
        # 1. Target capsules are not part of this chain, or
        # 2. Replacement capsules are in the chain
        for exp_capsule in expiration_capsules:
            for target_id in exp_capsule.target_capsule_ids:
                if target_id in capsule_id_map:
                    # Target is in this chain, check if it has replacements
                    if not getattr(exp_capsule, "replacement_capsule_ids", None):
                        # Expired with no replacement
                        return False

                    # Check that at least one replacement exists in the chain
                    replacement_exists = False
                    for replacement_id in exp_capsule.replacement_capsule_ids:
                        if replacement_id in capsule_id_map:
                            replacement_exists = True
                            break

                    if not replacement_exists:
                        return False

        return True

    @staticmethod
    def _verify_trust_renewal_in_chain(capsules: List[Capsule]) -> bool:
        """Check that trust renewal relationships in the chain are valid."""
        # This is a placeholder for more complex chain-level trust renewal verification
        # The implementation would need to check that trust renewal capsules properly reference
        # the capsules they renew trust for, that renewals haven't expired, etc.

        # For now, we'll just check that any trust renewal capsules grant renewal
        renewal_capsules = [
            c for c in capsules if getattr(c, "capsule_type", "") == "TrustRenewal"
        ]

        for renewal in renewal_capsules:
            if not getattr(renewal, "renewal_granted", False):
                # If we have an explicit non-renewal, that's considered invalid in the chain
                return False

        return True
