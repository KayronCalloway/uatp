"""
UATP Python SDK - Privacy Engine Module

Provides zero-knowledge proof generation and privacy-preserving functionality.
"""

import hashlib
import json
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class ZKProof:
    """A zero-knowledge proof for privacy-preserving attribution."""

    proof_id: str
    proof_type: str  # "attribution", "identity", "ownership", "computation"
    statement: str  # What is being proven
    proof_data: Dict[str, Any]
    verification_key: str
    creator_id: str
    validity_period: int  # seconds
    created_at: datetime

    @property
    def is_valid(self) -> bool:
        """Check if the proof is still valid."""
        now = datetime.now(timezone.utc)
        expiry = self.created_at.timestamp() + self.validity_period
        return now.timestamp() < expiry

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "proof_id": self.proof_id,
            "proof_type": self.proof_type,
            "statement": self.statement,
            "proof_data": self.proof_data,
            "verification_key": self.verification_key,
            "creator_id": self.creator_id,
            "validity_period": self.validity_period,
            "created_at": self.created_at.isoformat(),
            "is_valid": self.is_valid,
        }


@dataclass
class PrivacyPolicy:
    """Privacy policy configuration for UATP interactions."""

    anonymize_user_id: bool = True
    hide_content: bool = False
    encrypt_metadata: bool = True
    zero_knowledge_proofs: bool = True
    retention_period_days: int = 90
    sharing_permissions: List[str] = None

    def __post_init__(self):
        if self.sharing_permissions is None:
            self.sharing_permissions = ["attribution", "governance"]


class PrivacyEngine:
    """Handles privacy-preserving operations for UATP."""

    def __init__(self, client):
        self.client = client
        self.proof_cache = {}
        self.privacy_policies = {}
        logger.info(" Privacy Engine initialized with zero-knowledge capabilities")

    async def create_proof(
        self,
        data: Dict[str, Any],
        proof_type: str = "attribution",
        statement: Optional[str] = None,
        validity_hours: int = 24,
    ) -> ZKProof:
        """
        Create a zero-knowledge proof for privacy-preserving operations.

        Args:
            data: Data to create proof for
            proof_type: Type of proof to create
            statement: What is being proven
            validity_hours: How long the proof should remain valid

        Returns:
            Zero-knowledge proof object
        """

        if statement is None:
            statement = f"Proof of {proof_type} without revealing sensitive data"

        # Generate proof components
        proof_id = f"zkp_{secrets.token_hex(16)}"
        verification_key = self._generate_verification_key(data, proof_type)

        # Create proof request
        proof_request = {
            "proof_type": proof_type,
            "statement": statement,
            "data_hash": hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest(),
            "validity_hours": validity_hours,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            # Submit to UATP privacy service
            response = await self.client.http_client.post(
                "/api/v1/privacy/create-proof", json=proof_request
            )
            response.raise_for_status()

            result = response.json()

            # Create ZK proof object
            zk_proof = ZKProof(
                proof_id=proof_id,
                proof_type=proof_type,
                statement=statement,
                proof_data=result.get("proof_data", {}),
                verification_key=verification_key,
                creator_id=result.get("creator_id", "anonymous"),
                validity_period=validity_hours * 3600,
                created_at=datetime.now(timezone.utc),
            )

            # Cache the proof
            self.proof_cache[proof_id] = zk_proof

            logger.info(f" Created zero-knowledge proof: {proof_id}")
            return zk_proof

        except Exception as e:
            logger.error(f"[ERROR] ZK proof creation failed: {e}")

            # Create fallback proof
            fallback_proof = ZKProof(
                proof_id=proof_id,
                proof_type=proof_type,
                statement=statement,
                proof_data={
                    "method": "local_commitment",
                    "commitment": hashlib.sha256(
                        json.dumps(data, sort_keys=True).encode()
                    ).hexdigest(),
                    "nonce": secrets.token_hex(32),
                },
                verification_key=verification_key,
                creator_id="local_user",
                validity_period=validity_hours * 3600,
                created_at=datetime.now(timezone.utc),
            )

            self.proof_cache[proof_id] = fallback_proof
            return fallback_proof

    def _generate_verification_key(self, data: Dict[str, Any], proof_type: str) -> str:
        """Generate a verification key for the proof."""
        key_material = (
            f"{proof_type}:{json.dumps(data, sort_keys=True)}:{secrets.token_hex(16)}"
        )
        return hashlib.sha256(key_material.encode()).hexdigest()

    async def verify_proof(self, proof: Union[ZKProof, str]) -> Dict[str, Any]:
        """
        Verify a zero-knowledge proof.

        Args:
            proof: ZKProof object or proof ID string

        Returns:
            Verification result with details
        """

        if isinstance(proof, str):
            proof_id = proof
            proof_obj = self.proof_cache.get(proof_id)
            if not proof_obj:
                # Try to fetch from server
                proof_obj = await self.get_proof(proof_id)
                if not proof_obj:
                    return {"verified": False, "error": "Proof not found"}
        else:
            proof_obj = proof
            proof_id = proof.proof_id

        verification_request = {
            "proof_id": proof_id,
            "proof_type": proof_obj.proof_type,
            "verification_key": proof_obj.verification_key,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            response = await self.client.http_client.post(
                "/api/v1/privacy/verify-proof", json=verification_request
            )
            response.raise_for_status()

            result = response.json()

            # Check local validity as well
            is_locally_valid = proof_obj.is_valid

            verification_result = {
                "verified": result.get("verified", False) and is_locally_valid,
                "proof_id": proof_id,
                "proof_type": proof_obj.proof_type,
                "statement": proof_obj.statement,
                "validity_remaining": max(
                    0,
                    proof_obj.validity_period
                    - (
                        datetime.now(timezone.utc) - proof_obj.created_at
                    ).total_seconds(),
                ),
                "verification_timestamp": datetime.utcnow().isoformat(),
                "details": result.get("details", {}),
            }

            logger.info(
                f" Verified proof {proof_id}: {verification_result['verified']}"
            )
            return verification_result

        except Exception as e:
            logger.error(f"[ERROR] Proof verification failed for {proof_id}: {e}")
            return {"verified": False, "error": str(e), "proof_id": proof_id}

    async def get_proof(self, proof_id: str) -> Optional[ZKProof]:
        """Retrieve a proof by ID."""

        # Check cache first
        if proof_id in self.proof_cache:
            return self.proof_cache[proof_id]

        try:
            response = await self.client.http_client.get(
                f"/api/v1/privacy/proofs/{proof_id}"
            )
            response.raise_for_status()

            data = response.json()

            proof = ZKProof(
                proof_id=data["proof_id"],
                proof_type=data["proof_type"],
                statement=data["statement"],
                proof_data=data["proof_data"],
                verification_key=data["verification_key"],
                creator_id=data["creator_id"],
                validity_period=data["validity_period"],
                created_at=datetime.fromisoformat(data["created_at"]),
            )

            # Cache the proof
            self.proof_cache[proof_id] = proof
            return proof

        except Exception as e:
            logger.error(f"[ERROR] Failed to get proof {proof_id}: {e}")
            return None

    async def anonymize_data(
        self, data: Dict[str, Any], anonymization_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Anonymize sensitive data while preserving utility.

        Args:
            data: Data to anonymize
            anonymization_level: "minimal", "standard", "maximum"

        Returns:
            Anonymized data
        """

        anonymization_request = {
            "data": data,
            "level": anonymization_level,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            response = await self.client.http_client.post(
                "/api/v1/privacy/anonymize", json=anonymization_request
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f" Anonymized data with level: {anonymization_level}")
            return result.get("anonymized_data", {})

        except Exception as e:
            logger.error(f"[ERROR] Data anonymization failed: {e}")

            # Fallback local anonymization
            return self._local_anonymize(data, anonymization_level)

    def _local_anonymize(self, data: Dict[str, Any], level: str) -> Dict[str, Any]:
        """Local fallback anonymization."""

        anonymized = data.copy()

        # Fields to anonymize based on level
        sensitive_fields = {
            "minimal": ["user_id", "email"],
            "standard": ["user_id", "email", "username", "full_name", "ip_address"],
            "maximum": [
                "user_id",
                "email",
                "username",
                "full_name",
                "ip_address",
                "location",
                "device_id",
                "session_id",
            ],
        }

        fields_to_anonymize = sensitive_fields.get(level, sensitive_fields["standard"])

        for field in fields_to_anonymize:
            if field in anonymized:
                if field in ["user_id", "email", "username"]:
                    # Hash with salt
                    salt = secrets.token_hex(16)
                    anonymized[field] = hashlib.sha256(
                        f"{anonymized[field]}{salt}".encode()
                    ).hexdigest()[:16]
                else:
                    # Remove completely
                    anonymized[field] = "[REDACTED]"

        return anonymized

    async def create_privacy_policy(self, user_id: str, policy: PrivacyPolicy) -> bool:
        """Create or update privacy policy for a user."""

        policy_request = {
            "user_id": user_id,
            "policy": {
                "anonymize_user_id": policy.anonymize_user_id,
                "hide_content": policy.hide_content,
                "encrypt_metadata": policy.encrypt_metadata,
                "zero_knowledge_proofs": policy.zero_knowledge_proofs,
                "retention_period_days": policy.retention_period_days,
                "sharing_permissions": policy.sharing_permissions,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            response = await self.client.http_client.put(
                f"/api/v1/privacy/policies/{user_id}", json=policy_request
            )
            response.raise_for_status()

            # Cache the policy
            self.privacy_policies[user_id] = policy

            logger.info(f" Updated privacy policy for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Failed to update privacy policy for {user_id}: {e}")
            return False

    async def get_privacy_policy(self, user_id: str) -> Optional[PrivacyPolicy]:
        """Get privacy policy for a user."""

        # Check cache first
        if user_id in self.privacy_policies:
            return self.privacy_policies[user_id]

        try:
            response = await self.client.http_client.get(
                f"/api/v1/privacy/policies/{user_id}"
            )
            response.raise_for_status()

            data = response.json()
            policy_data = data["policy"]

            policy = PrivacyPolicy(
                anonymize_user_id=policy_data["anonymize_user_id"],
                hide_content=policy_data["hide_content"],
                encrypt_metadata=policy_data["encrypt_metadata"],
                zero_knowledge_proofs=policy_data["zero_knowledge_proofs"],
                retention_period_days=policy_data["retention_period_days"],
                sharing_permissions=policy_data["sharing_permissions"],
            )

            # Cache the policy
            self.privacy_policies[user_id] = policy
            return policy

        except Exception as e:
            logger.error(f"[ERROR] Failed to get privacy policy for {user_id}: {e}")
            return None

    async def encrypt_sensitive_data(
        self, data: Dict[str, Any], encryption_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Encrypt sensitive data for secure storage."""

        if encryption_key is None:
            encryption_key = secrets.token_hex(32)

        encryption_request = {
            "data": data,
            "key_hint": hashlib.sha256(encryption_key.encode()).hexdigest()[:16],
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            response = await self.client.http_client.post(
                "/api/v1/privacy/encrypt",
                json=encryption_request,
                headers={"X-Encryption-Key": encryption_key},
            )
            response.raise_for_status()

            result = response.json()
            logger.info(" Data encrypted successfully")
            return result

        except Exception as e:
            logger.error(f"[ERROR] Data encryption failed: {e}")

            # Fallback local encryption (simplified)
            encrypted_data = {}
            for key, value in data.items():
                if isinstance(value, str) and key in ["content", "prompt", "response"]:
                    # Simple XOR encryption (not secure, just for demo)
                    encrypted_value = ""
                    for i, char in enumerate(value):
                        key_char = encryption_key[i % len(encryption_key)]
                        encrypted_value += chr(ord(char) ^ ord(key_char))
                    encrypted_data[key] = encrypted_value.encode(
                        "utf-8", errors="ignore"
                    ).hex()
                else:
                    encrypted_data[key] = value

            return {
                "encrypted_data": encrypted_data,
                "encryption_method": "local_fallback",
                "key_hint": hashlib.sha256(encryption_key.encode()).hexdigest()[:16],
            }

    def clear_cache(self):
        """Clear all cached privacy data."""
        self.proof_cache.clear()
        self.privacy_policies.clear()
        logger.info(" Privacy cache cleared")
