"""
Capsule Privacy System using Zero-Knowledge Proofs
Provides privacy-preserving capsule verification and selective disclosure.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from src.capsule_schema import AnyCapsule, CapsuleType
from src.crypto.zero_knowledge import ZKProof, zk_system

logger = logging.getLogger(__name__)


class PrivacyLevel(str, Enum):
    """Privacy levels for capsule disclosure."""

    PUBLIC = "public"
    SELECTIVE = "selective"
    PRIVATE = "private"
    CONFIDENTIAL = "confidential"


@dataclass
class PrivacyPolicy:
    """Privacy policy for capsule disclosure."""

    privacy_level: PrivacyLevel
    disclosed_fields: Set[str]
    redacted_fields: Set[str]
    proof_required: bool
    authorized_viewers: List[str]

    def allows_field(self, field_name: str) -> bool:
        """Check if a field is allowed to be disclosed."""
        if self.privacy_level == PrivacyLevel.PUBLIC:
            return True
        elif self.privacy_level == PrivacyLevel.SELECTIVE:
            return field_name in self.disclosed_fields
        else:
            return field_name not in self.redacted_fields


@dataclass
class PrivateCapsule:
    """Privacy-enhanced capsule with ZK proofs."""

    capsule_id: str
    public_metadata: Dict[str, Any]
    privacy_policy: PrivacyPolicy
    integrity_proof: ZKProof
    privacy_proof: Optional[ZKProof]
    original_capsule_hash: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "capsule_id": self.capsule_id,
            "public_metadata": self.public_metadata,
            "privacy_policy": {
                "privacy_level": self.privacy_policy.privacy_level.value,
                "disclosed_fields": list(self.privacy_policy.disclosed_fields),
                "redacted_fields": list(self.privacy_policy.redacted_fields),
                "proof_required": self.privacy_policy.proof_required,
                "authorized_viewers": self.privacy_policy.authorized_viewers,
            },
            "integrity_proof": self.integrity_proof.to_dict(),
            "privacy_proof": self.privacy_proof.to_dict()
            if self.privacy_proof
            else None,
            "original_capsule_hash": self.original_capsule_hash,
        }


class CapsulePrivacyEngine:
    """Engine for managing capsule privacy with zero-knowledge proofs."""

    def __init__(self):
        self.privacy_policies = {}
        self.private_capsules = {}

    def set_privacy_policy(self, capsule_id: str, policy: PrivacyPolicy):
        """Set privacy policy for a capsule."""
        self.privacy_policies[capsule_id] = policy
        logger.info(
            f"Privacy policy set for capsule {capsule_id}: {policy.privacy_level}"
        )

    def privatize_capsule(
        self, capsule: AnyCapsule, privacy_policy: PrivacyPolicy
    ) -> PrivateCapsule:
        """Convert a regular capsule to a private capsule with ZK proofs."""

        # Hash the original capsule
        original_hash = self._hash_capsule(capsule)

        # Generate public metadata (safe to disclose)
        public_metadata = self._extract_public_metadata(capsule, privacy_policy)

        # Generate integrity proof (proves capsule is valid without revealing content)
        integrity_proof = zk_system.prove_capsule_integrity(
            capsule_hash=original_hash,
            signature_valid=True,  # Would check real signature
        )

        # Generate privacy proof if required
        privacy_proof = None
        if privacy_policy.proof_required:
            capsule_data = self._capsule_to_dict(capsule)
            privacy_proof = zk_system.generate_privacy_capsule_proof(capsule_data)

        private_capsule = PrivateCapsule(
            capsule_id=capsule.capsule_id,
            public_metadata=public_metadata,
            privacy_policy=privacy_policy,
            integrity_proof=integrity_proof,
            privacy_proof=privacy_proof,
            original_capsule_hash=original_hash,
        )

        # Store for later retrieval
        self.private_capsules[capsule.capsule_id] = private_capsule

        logger.info(
            f"Privatized capsule {capsule.capsule_id} with level {privacy_policy.privacy_level}"
        )
        return private_capsule

    def verify_private_capsule(self, private_capsule: PrivateCapsule) -> bool:
        """Verify a private capsule using ZK proofs."""
        try:
            # Verify integrity proof
            integrity_valid = zk_system.verify_proof(private_capsule.integrity_proof)
            if not integrity_valid:
                logger.error(
                    f"Integrity proof failed for capsule {private_capsule.capsule_id}"
                )
                return False

            # Verify privacy proof if present
            if private_capsule.privacy_proof:
                privacy_valid = zk_system.verify_proof(private_capsule.privacy_proof)
                if not privacy_valid:
                    logger.error(
                        f"Privacy proof failed for capsule {private_capsule.capsule_id}"
                    )
                    return False

            logger.info(
                f"Private capsule {private_capsule.capsule_id} verified successfully"
            )
            return True

        except Exception as e:
            logger.error(f"Error verifying private capsule: {e}")
            return False

    def selective_disclosure(
        self, capsule_id: str, requested_fields: Set[str], requester_id: str
    ) -> Dict[str, Any]:
        """Perform selective disclosure of capsule fields."""
        if capsule_id not in self.private_capsules:
            raise ValueError(f"Private capsule {capsule_id} not found")

        private_capsule = self.private_capsules[capsule_id]
        policy = private_capsule.privacy_policy

        # Check if requester is authorized
        if (
            requester_id not in policy.authorized_viewers
            and policy.privacy_level != PrivacyLevel.PUBLIC
        ):
            raise PermissionError(
                f"Requester {requester_id} not authorized to view capsule {capsule_id}"
            )

        # Filter fields based on privacy policy
        disclosed_data = {}
        for field in requested_fields:
            if policy.allows_field(field):
                if field in private_capsule.public_metadata:
                    disclosed_data[field] = private_capsule.public_metadata[field]

        # Generate proof of selective disclosure
        disclosure_proof = self._generate_disclosure_proof(
            capsule_id, requested_fields, disclosed_data
        )

        return {
            "capsule_id": capsule_id,
            "disclosed_fields": disclosed_data,
            "disclosure_proof": disclosure_proof.to_dict(),
            "privacy_level": policy.privacy_level.value,
        }

    def prove_capsule_property(
        self, capsule_id: str, property_name: str, property_value: Any
    ) -> ZKProof:
        """Prove a property of a capsule without revealing the capsule content."""
        if capsule_id not in self.private_capsules:
            raise ValueError(f"Private capsule {capsule_id} not found")

        private_capsule = self.private_capsules[capsule_id]

        # Generate proof based on property type
        if property_name == "timestamp_range":
            # Prove timestamp is within a range
            min_time, max_time = property_value
            timestamp = private_capsule.public_metadata.get("timestamp", 0)
            return zk_system.prove_range(timestamp, min_time, max_time)

        elif property_name == "capsule_type":
            # Prove capsule is of a specific type
            return self._prove_capsule_type(private_capsule, property_value)

        elif property_name == "content_length":
            # Prove content length is within bounds
            min_len, max_len = property_value
            content_length = len(str(private_capsule.public_metadata))
            return zk_system.prove_range(content_length, min_len, max_len)

        else:
            raise ValueError(f"Unknown property type: {property_name}")

    def _extract_public_metadata(
        self, capsule: AnyCapsule, policy: PrivacyPolicy
    ) -> Dict[str, Any]:
        """Extract public metadata based on privacy policy."""
        public_data = {}

        # Always include basic identifiers
        public_data["capsule_id"] = capsule.capsule_id
        public_data["capsule_type"] = capsule.capsule_type.value
        public_data["version"] = capsule.version

        # Include timestamp if allowed
        if policy.allows_field("timestamp"):
            public_data["timestamp"] = capsule.timestamp.isoformat()

        # Include status if allowed
        if policy.allows_field("status"):
            public_data["status"] = (
                capsule.status.value
                if hasattr(capsule.status, "value")
                else capsule.status
            )

        # Include signer if allowed
        if policy.allows_field("signer") and capsule.verification.signer:
            public_data["signer"] = capsule.verification.signer

        # Add capsule-specific public fields
        if capsule.capsule_type == CapsuleType.REASONING_TRACE:
            if policy.allows_field("step_count"):
                public_data["step_count"] = len(capsule.reasoning_trace.steps)

        return public_data

    def _hash_capsule(self, capsule: AnyCapsule) -> str:
        """Generate hash of capsule for integrity proof."""
        capsule_dict = self._capsule_to_dict(capsule)
        capsule_json = json.dumps(capsule_dict, sort_keys=True)
        return hashlib.sha256(capsule_json.encode()).hexdigest()

    def _capsule_to_dict(self, capsule: AnyCapsule) -> Dict[str, Any]:
        """Convert capsule to dictionary."""
        return {
            "capsule_id": capsule.capsule_id,
            "capsule_type": capsule.capsule_type.value
            if hasattr(capsule.capsule_type, "value")
            else capsule.capsule_type,
            "version": capsule.version,
            "timestamp": capsule.timestamp.isoformat(),
            "status": capsule.status.value
            if hasattr(capsule.status, "value")
            else capsule.status,
            "verification": {
                "signature": capsule.verification.signature,
                "hash": capsule.verification.hash,
                "signer": capsule.verification.signer,
            },
        }

    def _generate_disclosure_proof(
        self,
        capsule_id: str,
        requested_fields: Set[str],
        disclosed_data: Dict[str, Any],
    ) -> ZKProof:
        """Generate proof of selective disclosure."""
        public_inputs = {
            "capsule_id": capsule_id,
            "requested_fields": sorted(list(requested_fields)),
            "disclosed_hash": hashlib.sha256(
                json.dumps(disclosed_data, sort_keys=True).encode()
            ).hexdigest(),
        }

        private_witness = {
            "full_capsule_data": "redacted_for_privacy",
            "disclosure_policy": "redacted_for_privacy",
        }

        return zk_system.prove_capsule_privacy(public_inputs, private_witness)

    def _prove_capsule_type(
        self, private_capsule: PrivateCapsule, expected_type: str
    ) -> ZKProof:
        """Prove capsule is of a specific type."""
        actual_type = private_capsule.public_metadata.get("capsule_type")

        # This is a simple equality proof
        public_inputs = {
            "capsule_id": private_capsule.capsule_id,
            "expected_type": expected_type,
            "matches": actual_type == expected_type,
        }

        private_witness = {
            "actual_type": actual_type,
            "capsule_metadata": private_capsule.public_metadata,
        }

        return zk_system.prove_capsule_privacy(public_inputs, private_witness)

    def create_privacy_report(self, capsule_id: str) -> Dict[str, Any]:
        """Create a privacy report for a capsule."""
        if capsule_id not in self.private_capsules:
            return {"error": "Capsule not found"}

        private_capsule = self.private_capsules[capsule_id]

        return {
            "capsule_id": capsule_id,
            "privacy_level": private_capsule.privacy_policy.privacy_level.value,
            "proofs_verified": {
                "integrity": zk_system.verify_proof(private_capsule.integrity_proof),
                "privacy": zk_system.verify_proof(private_capsule.privacy_proof)
                if private_capsule.privacy_proof
                else None,
            },
            "disclosed_fields": list(private_capsule.privacy_policy.disclosed_fields),
            "redacted_fields": list(private_capsule.privacy_policy.redacted_fields),
            "authorized_viewers": len(
                private_capsule.privacy_policy.authorized_viewers
            ),
        }


# Global privacy engine instance
privacy_engine = CapsulePrivacyEngine()

# Define default privacy policies
DEFAULT_PRIVACY_POLICIES = {
    "public": PrivacyPolicy(
        privacy_level=PrivacyLevel.PUBLIC,
        disclosed_fields=set(),
        redacted_fields=set(),
        proof_required=False,
        authorized_viewers=["*"],
    ),
    "selective": PrivacyPolicy(
        privacy_level=PrivacyLevel.SELECTIVE,
        disclosed_fields={"capsule_id", "capsule_type", "timestamp", "status"},
        redacted_fields={"reasoning_trace", "verification"},
        proof_required=True,
        authorized_viewers=[],
    ),
    "private": PrivacyPolicy(
        privacy_level=PrivacyLevel.PRIVATE,
        disclosed_fields={"capsule_id", "capsule_type"},
        redacted_fields={"reasoning_trace", "verification", "timestamp", "status"},
        proof_required=True,
        authorized_viewers=[],
    ),
    "confidential": PrivacyPolicy(
        privacy_level=PrivacyLevel.CONFIDENTIAL,
        disclosed_fields={"capsule_id"},
        redacted_fields={
            "capsule_type",
            "reasoning_trace",
            "verification",
            "timestamp",
            "status",
        },
        proof_required=True,
        authorized_viewers=[],
    ),
}
