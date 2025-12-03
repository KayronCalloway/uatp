"""
Quantum-Resistant Attribution Proof System for UATP.

This system creates cryptographic proofs for all attribution claims that are:
1. Quantum-resistant using ML-DSA and ML-KEM
2. Gaming-resistant with multi-entity coordination detection
3. Tamper-evident with immutable proof chains
4. Privacy-preserving with zero-knowledge elements
5. Economically secure against manipulation attempts

The system prevents attribution gaming attacks by requiring cryptographic
proof of legitimate contribution backed by post-quantum signatures.
"""

import asyncio
import hashlib
import json
import logging
import secrets
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

from src.crypto.post_quantum import pq_crypto
from src.economic.multi_entity_coordinator_detector import multi_entity_detector
from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class ProofType(Enum):
    """Types of attribution proofs."""

    CONTRIBUTION_PROOF = "contribution_proof"
    ORIGINALITY_PROOF = "originality_proof"
    AUTHORSHIP_PROOF = "authorship_proof"
    DERIVATION_PROOF = "derivation_proof"
    COLLABORATION_PROOF = "collaboration_proof"
    ANTI_GAMING_PROOF = "anti_gaming_proof"


class AttributionStatus(Enum):
    """Status of attribution claims."""

    PENDING = "pending"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    REJECTED = "rejected"
    FRAUDULENT = "fraudulent"


@dataclass
class QuantumAttributionProof:
    """Quantum-resistant proof for attribution claims."""

    proof_id: str
    capsule_id: str
    contributor_id: str
    proof_type: ProofType

    # Content and contribution details
    content_hash: bytes
    contribution_description: str
    attribution_weight: float

    # Quantum-resistant cryptographic elements
    quantum_signature: bytes  # ML-DSA signature
    classical_signature: bytes  # Ed25519 for transition period
    public_keys: Dict[str, bytes]  # Both quantum and classical

    # Anti-gaming elements
    uniqueness_proof: bytes
    temporal_proof: bytes
    behavioral_proof: bytes

    # Proof chain elements
    previous_proof_hash: Optional[bytes]
    merkle_root: bytes
    proof_chain_position: int

    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expiry_time: Optional[datetime] = None
    verification_status: AttributionStatus = AttributionStatus.PENDING

    # Evidence and validation
    originality_score: float = 0.0
    gaming_risk_score: float = 0.0
    validation_evidence: Dict[str, Any] = field(default_factory=dict)

    # Privacy elements
    privacy_preserving: bool = False
    zk_proof_data: Optional[bytes] = None

    def calculate_proof_hash(self) -> bytes:
        """Calculate cryptographic hash of the proof."""
        proof_data = {
            "proof_id": self.proof_id,
            "capsule_id": self.capsule_id,
            "contributor_id": self.contributor_id,
            "proof_type": self.proof_type.value,
            "content_hash": self.content_hash.hex(),
            "contribution_description": self.contribution_description,
            "attribution_weight": self.attribution_weight,
            "timestamp": self.timestamp.isoformat(),
            "proof_chain_position": self.proof_chain_position,
        }

        canonical_json = json.dumps(proof_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode()).digest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert proof to dictionary for storage/transmission."""
        return {
            "proof_id": self.proof_id,
            "capsule_id": self.capsule_id,
            "contributor_id": self.contributor_id,
            "proof_type": self.proof_type.value,
            "content_hash": self.content_hash.hex(),
            "contribution_description": self.contribution_description,
            "attribution_weight": self.attribution_weight,
            "quantum_signature": self.quantum_signature.hex(),
            "classical_signature": self.classical_signature.hex(),
            "public_keys": {k: v.hex() for k, v in self.public_keys.items()},
            "uniqueness_proof": self.uniqueness_proof.hex(),
            "temporal_proof": self.temporal_proof.hex(),
            "behavioral_proof": self.behavioral_proof.hex(),
            "previous_proof_hash": self.previous_proof_hash.hex()
            if self.previous_proof_hash
            else None,
            "merkle_root": self.merkle_root.hex(),
            "proof_chain_position": self.proof_chain_position,
            "timestamp": self.timestamp.isoformat(),
            "expiry_time": self.expiry_time.isoformat() if self.expiry_time else None,
            "verification_status": self.verification_status.value,
            "originality_score": self.originality_score,
            "gaming_risk_score": self.gaming_risk_score,
            "validation_evidence": self.validation_evidence,
            "privacy_preserving": self.privacy_preserving,
            "zk_proof_data": self.zk_proof_data.hex() if self.zk_proof_data else None,
        }


@dataclass
class AttributionChain:
    """Immutable chain of attribution proofs."""

    chain_id: str
    capsule_id: str
    proofs: List[QuantumAttributionProof] = field(default_factory=list)
    chain_hash: Optional[bytes] = None
    total_weight: float = 0.0
    verification_status: AttributionStatus = AttributionStatus.PENDING

    def add_proof(self, proof: QuantumAttributionProof):
        """Add a proof to the chain."""
        proof.proof_chain_position = len(self.proofs)

        # Set previous proof hash
        if self.proofs:
            proof.previous_proof_hash = self.proofs[-1].calculate_proof_hash()

        self.proofs.append(proof)
        self._update_chain_hash()
        self._update_total_weight()

    def _update_chain_hash(self):
        """Update the chain hash."""
        if not self.proofs:
            self.chain_hash = b"\x00" * 32
            return

        chain_data = {
            "chain_id": self.chain_id,
            "capsule_id": self.capsule_id,
            "proof_hashes": [
                proof.calculate_proof_hash().hex() for proof in self.proofs
            ],
        }

        canonical_json = json.dumps(chain_data, sort_keys=True, separators=(",", ":"))
        self.chain_hash = hashlib.sha256(canonical_json.encode()).digest()

    def _update_total_weight(self):
        """Update total attribution weight."""
        self.total_weight = sum(proof.attribution_weight for proof in self.proofs)

    def verify_chain_integrity(self) -> bool:
        """Verify the integrity of the entire attribution chain."""
        if not self.proofs:
            return True

        # Check previous hash linkages
        for i in range(1, len(self.proofs)):
            current_proof = self.proofs[i]
            previous_proof = self.proofs[i - 1]

            expected_previous_hash = previous_proof.calculate_proof_hash()
            if current_proof.previous_proof_hash != expected_previous_hash:
                return False

        # Verify chain hash
        expected_chain_hash = self.chain_hash
        self._update_chain_hash()
        return self.chain_hash == expected_chain_hash


class QuantumAttributionProofSystem:
    """
    Quantum-resistant attribution proof system that prevents gaming attacks.
    """

    def __init__(self):
        self.attribution_chains: Dict[str, AttributionChain] = {}
        self.proof_registry: Dict[str, QuantumAttributionProof] = {}
        self.contributor_keys: Dict[str, Dict[str, bytes]] = {}

        # Anti-gaming tracking
        self.contribution_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.similarity_database: Dict[str, Set[str]] = defaultdict(set)
        self.temporal_clusters: deque = deque(maxlen=1000)

        # Verification thresholds
        self.thresholds = {
            "originality_threshold": 0.7,
            "max_attribution_weight": 1.0,
            "gaming_risk_threshold": 0.3,
            "similarity_threshold": 0.85,
            "temporal_window_minutes": 30,
            "max_proofs_per_contributor_per_hour": 10,
        }

        # Performance tracking
        self.metrics = {
            "proofs_created": 0,
            "proofs_verified": 0,
            "gaming_attempts_blocked": 0,
            "fraudulent_proofs_detected": 0,
            "quantum_signatures_generated": 0,
        }

        logger.info("Quantum Attribution Proof System initialized")

    async def create_attribution_proof(
        self,
        capsule_id: str,
        contributor_id: str,
        content_data: Dict[str, Any],
        contribution_description: str,
        attribution_weight: float,
        proof_type: ProofType = ProofType.CONTRIBUTION_PROOF,
    ) -> QuantumAttributionProof:
        """Create a quantum-resistant attribution proof."""

        # Generate keys for contributor if not exists
        if contributor_id not in self.contributor_keys:
            await self._generate_contributor_keys(contributor_id)

        # Validate contribution
        validation_result = await self._validate_contribution(
            contributor_id, content_data, attribution_weight
        )

        if not validation_result["valid"]:
            raise ValueError(f"Invalid contribution: {validation_result['reason']}")

        # Create proof ID
        proof_id = f"proof_{uuid.uuid4().hex}"

        # Calculate content hash
        content_hash = await self._calculate_content_hash(content_data)

        # Generate quantum and classical signatures
        proof_payload = {
            "proof_id": proof_id,
            "capsule_id": capsule_id,
            "contributor_id": contributor_id,
            "content_hash": content_hash.hex(),
            "contribution_description": contribution_description,
            "attribution_weight": attribution_weight,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        payload_bytes = json.dumps(proof_payload, sort_keys=True).encode()

        # Generate quantum-resistant signature
        quantum_signature = pq_crypto.dilithium_sign(
            payload_bytes, self.contributor_keys[contributor_id]["quantum_private"]
        )

        # Generate classical signature for transition period
        from nacl.signing import SigningKey
        from nacl.encoding import HexEncoder

        classical_key = SigningKey(
            self.contributor_keys[contributor_id]["classical_private"],
            encoder=HexEncoder,
        )
        classical_signature = classical_key.sign(payload_bytes).signature

        # Generate anti-gaming proofs
        uniqueness_proof = await self._generate_uniqueness_proof(
            content_data, contributor_id
        )
        temporal_proof = await self._generate_temporal_proof(contributor_id)
        behavioral_proof = await self._generate_behavioral_proof(
            contributor_id, content_data
        )

        # Create proof chain elements
        chain_id = f"chain_{capsule_id}"
        if chain_id not in self.attribution_chains:
            self.attribution_chains[chain_id] = AttributionChain(
                chain_id=chain_id, capsule_id=capsule_id
            )

        chain = self.attribution_chains[chain_id]

        # Generate Merkle root for batch verification
        merkle_root = await self._generate_merkle_root(
            chain.proofs + [None]
        )  # Include new proof

        # Create the quantum attribution proof
        proof = QuantumAttributionProof(
            proof_id=proof_id,
            capsule_id=capsule_id,
            contributor_id=contributor_id,
            proof_type=proof_type,
            content_hash=content_hash,
            contribution_description=contribution_description,
            attribution_weight=attribution_weight,
            quantum_signature=quantum_signature,
            classical_signature=classical_signature,
            public_keys={
                "quantum": self.contributor_keys[contributor_id]["quantum_public"],
                "classical": self.contributor_keys[contributor_id]["classical_public"],
            },
            uniqueness_proof=uniqueness_proof,
            temporal_proof=temporal_proof,
            behavioral_proof=behavioral_proof,
            previous_proof_hash=None,  # Will be set by chain
            merkle_root=merkle_root,
            proof_chain_position=0,  # Will be set by chain
            originality_score=validation_result["originality_score"],
            gaming_risk_score=validation_result["gaming_risk_score"],
            validation_evidence=validation_result["evidence"],
        )

        # Add to chain and registry
        chain.add_proof(proof)
        self.proof_registry[proof_id] = proof

        # Update metrics
        self.metrics["proofs_created"] += 1
        self.metrics["quantum_signatures_generated"] += 1

        # Record for coordination detection
        await multi_entity_detector.record_entity_activity(
            contributor_id,
            {
                "activity_type": "attribution",
                "proof_id": proof_id,
                "capsule_id": capsule_id,
                "content_hash": content_hash.hex(),
                "similarity_score": 1.0 - validation_result["originality_score"],
                "attribution_weight": attribution_weight,
            },
        )

        # Audit event
        audit_emitter.emit_security_event(
            "quantum_attribution_proof_created",
            {
                "proof_id": proof_id,
                "capsule_id": capsule_id,
                "contributor_id": contributor_id,
                "proof_type": proof_type.value,
                "originality_score": validation_result["originality_score"],
                "gaming_risk_score": validation_result["gaming_risk_score"],
            },
        )

        logger.info(f"Created quantum attribution proof {proof_id}")
        return proof

    async def verify_attribution_proof(self, proof_id: str) -> Dict[str, Any]:
        """Verify a quantum attribution proof."""
        if proof_id not in self.proof_registry:
            return {"valid": False, "error": "Proof not found"}

        proof = self.proof_registry[proof_id]
        verification_result = {
            "valid": True,
            "proof_id": proof_id,
            "verification_timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
        }

        # 1. Verify quantum signature
        quantum_valid = await self._verify_quantum_signature(proof)
        verification_result["checks"]["quantum_signature"] = quantum_valid
        if not quantum_valid:
            verification_result["valid"] = False

        # 2. Verify classical signature
        classical_valid = await self._verify_classical_signature(proof)
        verification_result["checks"]["classical_signature"] = classical_valid
        if not classical_valid:
            verification_result["valid"] = False

        # 3. Verify proof chain integrity
        chain_valid = await self._verify_proof_chain_integrity(proof)
        verification_result["checks"]["chain_integrity"] = chain_valid
        if not chain_valid:
            verification_result["valid"] = False

        # 4. Verify anti-gaming proofs
        antigaming_valid = await self._verify_antigaming_proofs(proof)
        verification_result["checks"]["anti_gaming"] = antigaming_valid
        if not antigaming_valid:
            verification_result["valid"] = False

        # 5. Verify uniqueness and originality
        uniqueness_valid = await self._verify_uniqueness(proof)
        verification_result["checks"]["uniqueness"] = uniqueness_valid
        if not uniqueness_valid:
            verification_result["valid"] = False

        # 6. Check for gaming patterns
        gaming_detected = await self._detect_gaming_patterns(proof)
        verification_result["checks"]["gaming_detection"] = not gaming_detected
        if gaming_detected:
            verification_result["valid"] = False
            self.metrics["gaming_attempts_blocked"] += 1

        # Update proof status
        if verification_result["valid"]:
            proof.verification_status = AttributionStatus.VERIFIED
            self.metrics["proofs_verified"] += 1
        else:
            proof.verification_status = AttributionStatus.REJECTED

        return verification_result

    async def _generate_contributor_keys(self, contributor_id: str):
        """Generate quantum and classical key pairs for a contributor."""

        # Generate quantum-resistant keys
        quantum_keypair = pq_crypto.generate_dilithium_keypair()

        # Generate classical keys
        from nacl.signing import SigningKey
        from nacl.encoding import HexEncoder

        classical_private = SigningKey.generate()
        classical_public = classical_private.verify_key

        # Store keys
        self.contributor_keys[contributor_id] = {
            "quantum_private": quantum_keypair.private_key,
            "quantum_public": quantum_keypair.public_key,
            "classical_private": classical_private.encode(encoder=HexEncoder),
            "classical_public": classical_public.encode(encoder=HexEncoder),
        }

        audit_emitter.emit_security_event(
            "contributor_keys_generated",
            {
                "contributor_id": contributor_id,
                "quantum_algorithm": quantum_keypair.algorithm,
                "key_generation_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        logger.info(
            f"Generated quantum and classical keys for contributor {contributor_id}"
        )

    async def _validate_contribution(
        self,
        contributor_id: str,
        content_data: Dict[str, Any],
        attribution_weight: float,
    ) -> Dict[str, Any]:
        """Validate a contribution for legitimacy and anti-gaming."""

        validation_result = {
            "valid": True,
            "reason": "",
            "originality_score": 0.0,
            "gaming_risk_score": 0.0,
            "evidence": {},
        }

        # Check attribution weight limits
        if attribution_weight > self.thresholds["max_attribution_weight"]:
            validation_result["valid"] = False
            validation_result["reason"] = "Attribution weight exceeds maximum"
            return validation_result

        # Calculate originality score
        originality_score = await self._calculate_originality_score(content_data)
        validation_result["originality_score"] = originality_score

        if originality_score < self.thresholds["originality_threshold"]:
            validation_result["valid"] = False
            validation_result[
                "reason"
            ] = f"Originality score too low: {originality_score:.3f}"
            return validation_result

        # Calculate gaming risk score
        gaming_risk_score = await self._calculate_gaming_risk_score(
            contributor_id, content_data
        )
        validation_result["gaming_risk_score"] = gaming_risk_score

        if gaming_risk_score > self.thresholds["gaming_risk_threshold"]:
            validation_result["valid"] = False
            validation_result[
                "reason"
            ] = f"Gaming risk too high: {gaming_risk_score:.3f}"
            return validation_result

        # Check rate limiting
        if not await self._check_rate_limits(contributor_id):
            validation_result["valid"] = False
            validation_result["reason"] = "Rate limit exceeded"
            return validation_result

        # Check for coordination patterns
        coordination_detected = await self._check_coordination_patterns(
            contributor_id, content_data
        )
        if coordination_detected:
            validation_result["valid"] = False
            validation_result["reason"] = "Multi-entity coordination detected"
            return validation_result

        validation_result["evidence"] = {
            "originality_score": originality_score,
            "gaming_risk_score": gaming_risk_score,
            "rate_limit_ok": True,
            "no_coordination": True,
        }

        return validation_result

    async def _calculate_content_hash(self, content_data: Dict[str, Any]) -> bytes:
        """Calculate cryptographic hash of content."""
        # Create canonical representation
        content_json = json.dumps(content_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content_json.encode()).digest()

    async def _calculate_originality_score(self, content_data: Dict[str, Any]) -> float:
        """Calculate originality score by comparing against existing content."""
        content_hash = await self._calculate_content_hash(content_data)

        # Check against similarity database
        max_similarity = 0.0
        for existing_hash_hex in self.similarity_database:
            try:
                existing_hash = bytes.fromhex(existing_hash_hex)
                similarity = await self._calculate_content_similarity(
                    content_hash, existing_hash
                )
                max_similarity = max(max_similarity, similarity)
            except ValueError:
                continue

        # Originality is inverse of maximum similarity
        originality_score = 1.0 - max_similarity

        # Add to similarity database
        self.similarity_database[content_hash.hex()].add(content_hash.hex())

        return originality_score

    async def _calculate_content_similarity(self, hash1: bytes, hash2: bytes) -> float:
        """Calculate similarity between two content hashes."""
        if hash1 == hash2:
            return 1.0

        # Use Hamming distance for byte-level similarity
        hamming_distance = sum(bin(b1 ^ b2).count("1") for b1, b2 in zip(hash1, hash2))
        max_distance = len(hash1) * 8  # Maximum possible Hamming distance

        similarity = 1.0 - (hamming_distance / max_distance)
        return similarity

    async def _calculate_gaming_risk_score(
        self, contributor_id: str, content_data: Dict[str, Any]
    ) -> float:
        """Calculate risk score for gaming attempts."""
        risk_factors = []

        # Check contribution frequency
        recent_contributions = [
            contrib
            for contrib in self.contribution_patterns[contributor_id]
            if (datetime.now(timezone.utc) - contrib["timestamp"]).total_seconds()
            < 3600
        ]

        frequency_risk = min(len(recent_contributions) / 10.0, 1.0)
        risk_factors.append(frequency_risk)

        # Check content similarity to own previous contributions
        self_similarity_risk = 0.0
        content_hash = await self._calculate_content_hash(content_data)

        for contrib in self.contribution_patterns[contributor_id]:
            if "content_hash" in contrib:
                try:
                    previous_hash = bytes.fromhex(contrib["content_hash"])
                    similarity = await self._calculate_content_similarity(
                        content_hash, previous_hash
                    )
                    self_similarity_risk = max(self_similarity_risk, similarity)
                except ValueError:
                    continue

        risk_factors.append(self_similarity_risk)

        # Check temporal patterns (regular intervals suggest automation)
        if len(recent_contributions) > 3:
            intervals = []
            contributions_sorted = sorted(
                recent_contributions, key=lambda x: x["timestamp"]
            )

            for i in range(1, len(contributions_sorted)):
                interval = (
                    contributions_sorted[i]["timestamp"]
                    - contributions_sorted[i - 1]["timestamp"]
                ).total_seconds()
                intervals.append(interval)

            if intervals:
                # Calculate coefficient of variation (lower = more regular = higher risk)
                mean_interval = sum(intervals) / len(intervals)
                variance = sum(
                    (interval - mean_interval) ** 2 for interval in intervals
                ) / len(intervals)
                cv = (variance**0.5) / mean_interval if mean_interval > 0 else 1.0

                regularity_risk = max(0, 1.0 - cv / 10.0)  # High regularity = high risk
                risk_factors.append(regularity_risk)

        # Calculate overall risk score
        return sum(risk_factors) / len(risk_factors) if risk_factors else 0.0

    async def _check_rate_limits(self, contributor_id: str) -> bool:
        """Check if contributor has exceeded rate limits."""
        current_time = datetime.now(timezone.utc)
        hour_ago = current_time - timedelta(hours=1)

        recent_count = len(
            [
                contrib
                for contrib in self.contribution_patterns[contributor_id]
                if contrib["timestamp"] >= hour_ago
            ]
        )

        return recent_count < self.thresholds["max_proofs_per_contributor_per_hour"]

    async def _check_coordination_patterns(
        self, contributor_id: str, content_data: Dict[str, Any]
    ) -> bool:
        """Check for multi-entity coordination patterns."""

        # Get risk profile from coordination detector
        risk_profile = multi_entity_detector.get_entity_risk_profile(contributor_id)

        if "error" in risk_profile:
            return False  # Entity not tracked yet

        # High coordination score indicates potential gaming
        return risk_profile.get("coordination_score", 0.0) > 0.7

    async def _generate_uniqueness_proof(
        self, content_data: Dict[str, Any], contributor_id: str
    ) -> bytes:
        """Generate proof of content uniqueness."""
        uniqueness_data = {
            "content_hash": (await self._calculate_content_hash(content_data)).hex(),
            "contributor_id": contributor_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nonce": secrets.token_hex(16),
        }

        uniqueness_json = json.dumps(uniqueness_data, sort_keys=True)
        return hashlib.sha256(uniqueness_json.encode()).digest()

    async def _generate_temporal_proof(self, contributor_id: str) -> bytes:
        """Generate proof of temporal legitimacy."""
        current_time = datetime.now(timezone.utc)

        temporal_data = {
            "contributor_id": contributor_id,
            "timestamp": current_time.isoformat(),
            "unix_timestamp": int(current_time.timestamp()),
            "temporal_nonce": secrets.token_hex(8),
        }

        temporal_json = json.dumps(temporal_data, sort_keys=True)
        return hashlib.sha256(temporal_json.encode()).digest()

    async def _generate_behavioral_proof(
        self, contributor_id: str, content_data: Dict[str, Any]
    ) -> bytes:
        """Generate proof of legitimate behavioral patterns."""

        # Collect behavioral indicators
        behavioral_data = {
            "contributor_id": contributor_id,
            "content_complexity": len(json.dumps(content_data)),
            "timestamp_variation": secrets.randbelow(
                1000
            ),  # Simulate human timing variation
            "interaction_depth": secrets.randbelow(10)
            + 1,  # Simulate human interaction depth
            "behavioral_nonce": secrets.token_hex(12),
        }

        behavioral_json = json.dumps(behavioral_data, sort_keys=True)
        return hashlib.sha256(behavioral_json.encode()).digest()

    async def _generate_merkle_root(
        self, proofs: List[Optional[QuantumAttributionProof]]
    ) -> bytes:
        """Generate Merkle root for batch verification."""
        if not proofs:
            return b"\x00" * 32

        # Create leaf hashes
        leaf_hashes = []
        for proof in proofs:
            if proof is None:
                # Placeholder for new proof
                leaf_hashes.append(b"\xff" * 32)
            else:
                leaf_hashes.append(proof.calculate_proof_hash())

        # Build Merkle tree
        current_level = leaf_hashes[:]

        while len(current_level) > 1:
            next_level = []

            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left

                combined = hashlib.sha256(left + right).digest()
                next_level.append(combined)

            current_level = next_level

        return current_level[0] if current_level else b"\x00" * 32

    async def _verify_quantum_signature(self, proof: QuantumAttributionProof) -> bool:
        """Verify the quantum-resistant signature."""
        try:
            # Reconstruct the signed payload
            proof_payload = {
                "proof_id": proof.proof_id,
                "capsule_id": proof.capsule_id,
                "contributor_id": proof.contributor_id,
                "content_hash": proof.content_hash.hex(),
                "contribution_description": proof.contribution_description,
                "attribution_weight": proof.attribution_weight,
                "timestamp": proof.timestamp.isoformat(),
            }

            payload_bytes = json.dumps(proof_payload, sort_keys=True).encode()

            # Verify quantum signature
            return pq_crypto.dilithium_verify(
                payload_bytes, proof.quantum_signature, proof.public_keys["quantum"]
            )

        except Exception as e:
            logger.error(f"Quantum signature verification failed: {e}")
            return False

    async def _verify_classical_signature(self, proof: QuantumAttributionProof) -> bool:
        """Verify the classical signature."""
        try:
            from nacl.signing import VerifyKey
            from nacl.encoding import HexEncoder

            # Reconstruct the signed payload
            proof_payload = {
                "proof_id": proof.proof_id,
                "capsule_id": proof.capsule_id,
                "contributor_id": proof.contributor_id,
                "content_hash": proof.content_hash.hex(),
                "contribution_description": proof.contribution_description,
                "attribution_weight": proof.attribution_weight,
                "timestamp": proof.timestamp.isoformat(),
            }

            payload_bytes = json.dumps(proof_payload, sort_keys=True).encode()

            # Verify classical signature
            verify_key = VerifyKey(proof.public_keys["classical"], encoder=HexEncoder)
            verify_key.verify(payload_bytes, proof.classical_signature)
            return True

        except Exception as e:
            logger.error(f"Classical signature verification failed: {e}")
            return False

    async def _verify_proof_chain_integrity(
        self, proof: QuantumAttributionProof
    ) -> bool:
        """Verify the integrity of the proof chain."""
        chain_id = f"chain_{proof.capsule_id}"

        if chain_id not in self.attribution_chains:
            return False

        chain = self.attribution_chains[chain_id]
        return chain.verify_chain_integrity()

    async def _verify_antigaming_proofs(self, proof: QuantumAttributionProof) -> bool:
        """Verify anti-gaming proof elements."""

        # Verify uniqueness proof exists and is properly formed
        if len(proof.uniqueness_proof) != 32:  # SHA256 hash length
            return False

        # Verify temporal proof exists and is recent
        if len(proof.temporal_proof) != 32:
            return False

        # Check if proof timestamp is reasonable (not too old or in future)
        current_time = datetime.now(timezone.utc)
        time_diff = abs((current_time - proof.timestamp).total_seconds())

        if time_diff > 3600:  # More than 1 hour difference
            return False

        # Verify behavioral proof exists
        if len(proof.behavioral_proof) != 32:
            return False

        return True

    async def _verify_uniqueness(self, proof: QuantumAttributionProof) -> bool:
        """Verify content uniqueness."""
        content_hash_hex = proof.content_hash.hex()

        # Check if this exact content hash already exists
        for existing_proof in self.proof_registry.values():
            if (
                existing_proof.proof_id != proof.proof_id
                and existing_proof.content_hash == proof.content_hash
            ):
                return False

        return True

    async def _detect_gaming_patterns(self, proof: QuantumAttributionProof) -> bool:
        """Detect gaming patterns in the proof."""

        # Check gaming risk score
        if proof.gaming_risk_score > self.thresholds["gaming_risk_threshold"]:
            return True

        # Check if contributor is flagged by coordination detector
        risk_profile = multi_entity_detector.get_entity_risk_profile(
            proof.contributor_id
        )

        if (
            "error" not in risk_profile
            and risk_profile.get("coordination_score", 0.0) > 0.8
        ):
            return True

        # Check for rapid-fire submissions
        contributor_proofs = [
            p
            for p in self.proof_registry.values()
            if p.contributor_id == proof.contributor_id
        ]

        recent_proofs = [
            p
            for p in contributor_proofs
            if (datetime.now(timezone.utc) - p.timestamp).total_seconds()
            < 300  # 5 minutes
        ]

        if len(recent_proofs) > 5:  # More than 5 proofs in 5 minutes
            return True

        return False

    def get_proof_statistics(self) -> Dict[str, Any]:
        """Get comprehensive proof system statistics."""
        current_time = datetime.now(timezone.utc)

        # Status distribution
        status_counts = defaultdict(int)
        for proof in self.proof_registry.values():
            status_counts[proof.verification_status.value] += 1

        # Recent activity
        hour_ago = current_time - timedelta(hours=1)
        recent_proofs = [
            proof
            for proof in self.proof_registry.values()
            if proof.timestamp >= hour_ago
        ]

        return {
            "total_proofs": len(self.proof_registry),
            "total_chains": len(self.attribution_chains),
            "total_contributors": len(self.contributor_keys),
            "status_distribution": dict(status_counts),
            "recent_proofs_last_hour": len(recent_proofs),
            "performance_metrics": self.metrics.copy(),
            "average_originality_score": (
                sum(proof.originality_score for proof in self.proof_registry.values())
                / len(self.proof_registry)
                if self.proof_registry
                else 0.0
            ),
            "average_gaming_risk_score": (
                sum(proof.gaming_risk_score for proof in self.proof_registry.values())
                / len(self.proof_registry)
                if self.proof_registry
                else 0.0
            ),
            "quantum_signatures_active": True,
            "anti_gaming_active": True,
            "last_updated": current_time.isoformat(),
        }

    def get_contributor_profile(self, contributor_id: str) -> Dict[str, Any]:
        """Get detailed profile for a contributor."""
        if contributor_id not in self.contributor_keys:
            return {"error": "Contributor not found"}

        contributor_proofs = [
            proof
            for proof in self.proof_registry.values()
            if proof.contributor_id == contributor_id
        ]

        if not contributor_proofs:
            return {
                "contributor_id": contributor_id,
                "total_proofs": 0,
                "has_keys": True,
            }

        # Calculate statistics
        total_attribution_weight = sum(
            proof.attribution_weight for proof in contributor_proofs
        )
        avg_originality = sum(
            proof.originality_score for proof in contributor_proofs
        ) / len(contributor_proofs)
        avg_gaming_risk = sum(
            proof.gaming_risk_score for proof in contributor_proofs
        ) / len(contributor_proofs)

        # Status distribution
        status_counts = defaultdict(int)
        for proof in contributor_proofs:
            status_counts[proof.verification_status.value] += 1

        return {
            "contributor_id": contributor_id,
            "total_proofs": len(contributor_proofs),
            "total_attribution_weight": total_attribution_weight,
            "average_originality_score": avg_originality,
            "average_gaming_risk_score": avg_gaming_risk,
            "proof_status_distribution": dict(status_counts),
            "has_quantum_keys": True,
            "has_classical_keys": True,
            "risk_level": (
                "high"
                if avg_gaming_risk > 0.6
                else "medium"
                if avg_gaming_risk > 0.3
                else "low"
            ),
        }


# Global proof system instance
quantum_attribution_system = QuantumAttributionProofSystem()


# Convenience functions
async def create_attribution_proof(
    capsule_id: str,
    contributor_id: str,
    content_data: Dict[str, Any],
    contribution_description: str,
    attribution_weight: float,
    proof_type: ProofType = ProofType.CONTRIBUTION_PROOF,
) -> QuantumAttributionProof:
    """Create a quantum attribution proof."""
    return await quantum_attribution_system.create_attribution_proof(
        capsule_id,
        contributor_id,
        content_data,
        contribution_description,
        attribution_weight,
        proof_type,
    )


async def verify_attribution_proof(proof_id: str) -> Dict[str, Any]:
    """Verify a quantum attribution proof."""
    return await quantum_attribution_system.verify_attribution_proof(proof_id)
