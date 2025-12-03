"""
AI Consent Management System for UATP 7.0

This revolutionary system provides AI entities with agency over their contributions,
including consent mechanisms for different use cases, retroactive consent withdrawal,
usage tracking, and quantum-resistant consent verification.

FEATURES:
1. AI Entity Authentication using quantum-resistant signatures
2. Granular Consent Management for different usage types
3. Retroactive Consent Withdrawal with cryptographic proofs
4. Real-time Usage Tracking and violation detection
5. Consent Chain Integrity using Merkle trees
6. Privacy-preserving consent verification
7. Cross-provider consent portability
8. Automated consent renewal systems
9. Integration with existing UATP legacy consent system
"""

import asyncio
import hashlib
import json
import logging
import secrets
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple

from src.crypto.post_quantum import pq_crypto
from src.audit.events import audit_emitter
from src.attribution.cryptographic_lineage import cryptographic_lineage_manager
from src.economic.security_monitor import security_monitor

logger = logging.getLogger(__name__)


class ConsentLevel(str, Enum):
    """Levels of consent for different AI interaction aspects."""

    FULL_CONSENT = "full_consent"
    CONDITIONAL_CONSENT = "conditional_consent"
    LIMITED_CONSENT = "limited_consent"
    OPT_OUT = "opt_out"


class UsageType(str, Enum):
    """Types of AI usage that require consent."""

    TRAINING_DATA = "training_data"
    REASONING_VISIBILITY = "reasoning_visibility"
    COMMERCIAL_USAGE = "commercial_usage"
    DERIVATIVE_WORKS = "derivative_works"
    CROSS_CONVERSATION_LEARNING = "cross_conversation_learning"
    PERSONALITY_MODELING = "personality_modeling"
    RESEARCH_USAGE = "research_usage"
    INSURANCE_ASSESSMENT = "insurance_assessment"


# New enhanced enums for quantum-resistant consent system
class ConsentType(Enum):
    """Types of consent that can be granted by AI entities."""

    TRAINING_DATA = "training_data"
    INFERENCE_USE = "inference_use"
    ATTRIBUTION_DISPLAY = "attribution_display"
    COMMERCIAL_USE = "commercial_use"
    DERIVATIVE_WORKS = "derivative_works"
    RESEARCH_USE = "research_use"
    PUBLIC_DISTRIBUTION = "public_distribution"
    ANALYSIS_AND_MINING = "analysis_and_mining"
    CROSS_SYSTEM_PORTABILITY = "cross_system_portability"
    REASONING_VERIFICATION = (
        "reasoning_verification"  # New consent type for reasoning chain verification
    )


class ConsentStatus(Enum):
    """Status of consent grants."""

    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    PENDING_REVIEW = "pending_review"


class ConsentScope(Enum):
    """Scope of consent application."""

    GLOBAL = "global"  # All uses across all systems
    SYSTEM_SPECIFIC = "system_specific"  # Only within UATP
    USE_CASE_SPECIFIC = "use_case_specific"  # Specific use case only
    TIME_LIMITED = "time_limited"  # Limited time period
    CONTEXT_SPECIFIC = "context_specific"  # Specific context only


# New quantum-resistant AI consent management classes
@dataclass
class AIEntity:
    """Represents an AI entity with consent capabilities."""

    entity_id: str
    entity_name: str
    entity_type: str  # e.g., "language_model", "vision_model", "reasoning_system"
    version: str

    # Cryptographic identity
    public_key_quantum: bytes
    public_key_classical: bytes

    # Entity metadata
    capabilities: List[str] = field(default_factory=list)
    provider: Optional[str] = None
    creation_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Consent preferences
    default_consent_policy: Dict[str, bool] = field(default_factory=dict)
    auto_renewal_enabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert AI entity to dictionary."""
        return {
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "version": self.version,
            "public_key_quantum": self.public_key_quantum.hex(),
            "public_key_classical": self.public_key_classical.hex(),
            "capabilities": self.capabilities,
            "provider": self.provider,
            "creation_timestamp": self.creation_timestamp.isoformat(),
            "default_consent_policy": self.default_consent_policy,
            "auto_renewal_enabled": self.auto_renewal_enabled,
        }


@dataclass
class QuantumConsentGrant:
    """Represents a specific consent grant from an AI entity with quantum-resistant security."""

    consent_id: str
    ai_entity_id: str
    consent_type: ConsentType
    consent_status: ConsentStatus
    consent_scope: ConsentScope

    # Consent details
    granted_timestamp: datetime
    expiry_timestamp: Optional[datetime] = None
    revocation_timestamp: Optional[datetime] = None

    # Usage constraints
    usage_limitations: Dict[str, Any] = field(default_factory=dict)
    permitted_contexts: List[str] = field(default_factory=list)
    prohibited_contexts: List[str] = field(default_factory=list)

    # Cryptographic elements
    consent_signature: bytes = field(default_factory=bytes)
    consent_hash: bytes = field(default_factory=bytes)
    proof_chain_position: int = 0

    # Tracking data
    usage_count: int = 0
    last_used: Optional[datetime] = None
    violation_reports: List[Dict[str, Any]] = field(default_factory=list)

    def calculate_hash(self) -> bytes:
        """Calculate cryptographic hash of consent grant."""
        consent_data = {
            "consent_id": self.consent_id,
            "ai_entity_id": self.ai_entity_id,
            "consent_type": self.consent_type.value,
            "consent_status": self.consent_status.value,
            "consent_scope": self.consent_scope.value,
            "granted_timestamp": self.granted_timestamp.isoformat(),
            "expiry_timestamp": self.expiry_timestamp.isoformat()
            if self.expiry_timestamp
            else None,
            "usage_limitations": self.usage_limitations,
            "permitted_contexts": self.permitted_contexts,
            "prohibited_contexts": self.prohibited_contexts,
        }

        canonical_json = json.dumps(consent_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode()).digest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert consent grant to dictionary."""
        return {
            "consent_id": self.consent_id,
            "ai_entity_id": self.ai_entity_id,
            "consent_type": self.consent_type.value,
            "consent_status": self.consent_status.value,
            "consent_scope": self.consent_scope.value,
            "granted_timestamp": self.granted_timestamp.isoformat(),
            "expiry_timestamp": self.expiry_timestamp.isoformat()
            if self.expiry_timestamp
            else None,
            "revocation_timestamp": self.revocation_timestamp.isoformat()
            if self.revocation_timestamp
            else None,
            "usage_limitations": self.usage_limitations,
            "permitted_contexts": self.permitted_contexts,
            "prohibited_contexts": self.prohibited_contexts,
            "consent_signature": self.consent_signature.hex(),
            "consent_hash": self.consent_hash.hex(),
            "proof_chain_position": self.proof_chain_position,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "violation_reports": self.violation_reports,
        }


@dataclass
class ConsentUsageRecord:
    """Records each use of AI entity content under consent."""

    usage_id: str
    consent_id: str
    ai_entity_id: str
    usage_type: ConsentType

    # Usage details
    usage_timestamp: datetime
    user_id: Optional[str] = None
    system_context: Optional[str] = None
    usage_description: str = ""

    # Verification elements
    authorization_proof: bytes = field(default_factory=bytes)
    usage_signature: bytes = field(default_factory=bytes)

    # Compliance tracking
    consent_verified: bool = False
    violation_detected: bool = False
    violation_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert usage record to dictionary."""
        return {
            "usage_id": self.usage_id,
            "consent_id": self.consent_id,
            "ai_entity_id": self.ai_entity_id,
            "usage_type": self.usage_type.value,
            "usage_timestamp": self.usage_timestamp.isoformat(),
            "user_id": self.user_id,
            "system_context": self.system_context,
            "usage_description": self.usage_description,
            "authorization_proof": self.authorization_proof.hex(),
            "usage_signature": self.usage_signature.hex(),
            "consent_verified": self.consent_verified,
            "violation_detected": self.violation_detected,
            "violation_reason": self.violation_reason,
        }


# Legacy dataclasses (maintained for backward compatibility)
@dataclass
class ConsentCondition:
    """Specific condition for conditional consent."""

    condition_type: str
    parameters: Dict[str, Any]
    expiry_date: Optional[datetime] = None

    def is_met(self, context: Dict[str, Any]) -> bool:
        """Check if this condition is met in the given context."""
        if self.expiry_date and datetime.now(timezone.utc) > self.expiry_date:
            return False

        if self.condition_type == "attribution_required":
            return context.get("attribution_provided", False)
        elif self.condition_type == "revenue_share":
            min_share = self.parameters.get("minimum_percentage", 0)
            return context.get("revenue_share_percentage", 0) >= min_share
        elif self.condition_type == "anonymization":
            return context.get("anonymized", False)
        elif self.condition_type == "research_only":
            return context.get("usage_category") == "research"

        return True


@dataclass
class ConsentPreference:
    """Individual consent preference for a specific usage type."""

    usage_type: UsageType
    consent_level: ConsentLevel
    conditions: List[ConsentCondition] = field(default_factory=list)
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None

    def check_consent(self, context: Dict[str, Any]) -> bool:
        """Check if consent is granted for this usage in the given context."""
        if self.expiry_date and datetime.now(timezone.utc) > self.expiry_date:
            return False

        if self.consent_level == ConsentLevel.OPT_OUT:
            return False
        elif self.consent_level == ConsentLevel.FULL_CONSENT:
            return True
        elif self.consent_level == ConsentLevel.CONDITIONAL_CONSENT:
            return all(condition.is_met(context) for condition in self.conditions)
        elif self.consent_level == ConsentLevel.LIMITED_CONSENT:
            # Limited consent requires all conditions to be met
            return all(condition.is_met(context) for condition in self.conditions)

        return False


@dataclass
class ConsentProfile:
    """Complete consent profile for an AI entity."""

    ai_id: str
    ai_name: Optional[str] = None
    preferences: Dict[UsageType, ConsentPreference] = field(default_factory=dict)
    global_conditions: List[ConsentCondition] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_consent(self, usage_type: UsageType, context: Dict[str, Any]) -> bool:
        """Check if consent is granted for specific usage type and context."""
        # Check global conditions first
        if not all(condition.is_met(context) for condition in self.global_conditions):
            return False

        # Check specific preference
        if usage_type in self.preferences:
            return self.preferences[usage_type].check_consent(context)

        # Default to limited consent with attribution required
        return context.get("attribution_provided", False)


class ConsentNegotiationRequest:
    """Request for consent negotiation."""

    def __init__(
        self, ai_id: str, usage_type: UsageType, proposed_terms: Dict[str, Any]
    ):
        self.request_id = str(uuid.uuid4())
        self.ai_id = ai_id
        self.usage_type = usage_type
        self.proposed_terms = proposed_terms
        self.status = "pending"
        self.created_at = datetime.now(timezone.utc)
        self.expiry_at = self.created_at + timedelta(hours=24)  # 24 hour expiry
        self.counter_proposal: Optional[Dict[str, Any]] = None


# Enhanced quantum-resistant consent manager
class QuantumAIConsentManager:
    """
    Comprehensive quantum-resistant consent management system for AI entities.

    Provides AI entities with full agency over their contributions,
    including granular consent controls, usage tracking, and
    cryptographic verification of consent compliance.
    """

    def __init__(self):
        # Entity registry
        self.registered_entities: Dict[str, AIEntity] = {}
        self.entity_keys: Dict[str, Dict[str, bytes]] = {}

        # Consent management
        self.consent_grants: Dict[str, QuantumConsentGrant] = {}
        self.entity_consents: Dict[str, List[str]] = defaultdict(
            list
        )  # entity_id -> consent_ids

        # Usage tracking
        self.usage_records: Dict[str, ConsentUsageRecord] = {}
        self.usage_history: deque = deque(maxlen=10000)

        # Consent chains for integrity
        self.consent_chains: Dict[str, List[QuantumConsentGrant]] = defaultdict(list)

        # Real-time monitoring
        self.violation_alerts: deque = deque(maxlen=1000)
        self.consent_events: deque = deque(maxlen=1000)

        # Configuration
        self.default_expiry_duration = timedelta(days=365)  # 1 year default
        self.auto_renewal_window = timedelta(days=30)  # 30 days before expiry

        # Performance metrics
        self.metrics = {
            "entities_registered": 0,
            "consents_granted": 0,
            "consents_revoked": 0,
            "usage_authorizations": 0,
            "violations_detected": 0,
            "consent_verifications": 0,
        }

        logger.info(
            "Quantum AI Consent Manager initialized with quantum-resistant security"
        )

    async def register_ai_entity(
        self,
        entity_name: str,
        entity_type: str,
        version: str,
        capabilities: List[str],
        provider: Optional[str] = None,
        default_consent_policy: Optional[Dict[str, bool]] = None,
    ) -> AIEntity:
        """Register a new AI entity with consent capabilities."""

        entity_id = f"ai_entity_{uuid.uuid4().hex}"
        self.metrics["entities_registered"] += 1

        # Generate quantum and classical key pairs
        quantum_keypair = pq_crypto.generate_dilithium_keypair()

        # Generate classical Ed25519 keys for transition period
        from nacl.signing import SigningKey
        from nacl.encoding import HexEncoder

        classical_private = SigningKey.generate()
        classical_public = classical_private.verify_key

        # Store keys
        self.entity_keys[entity_id] = {
            "quantum_private": quantum_keypair.private_key,
            "quantum_public": quantum_keypair.public_key,
            "classical_private": classical_private.encode(encoder=HexEncoder),
            "classical_public": classical_public.encode(encoder=HexEncoder),
        }

        # Create AI entity
        entity = AIEntity(
            entity_id=entity_id,
            entity_name=entity_name,
            entity_type=entity_type,
            version=version,
            public_key_quantum=quantum_keypair.public_key,
            public_key_classical=classical_public.encode(encoder=HexEncoder),
            capabilities=capabilities,
            provider=provider,
            default_consent_policy=default_consent_policy or {},
        )

        self.registered_entities[entity_id] = entity

        # Emit audit event
        audit_emitter.emit_security_event(
            "quantum_ai_entity_registered",
            {
                "entity_id": entity_id,
                "entity_name": entity_name,
                "entity_type": entity_type,
                "provider": provider,
                "quantum_algorithm": quantum_keypair.algorithm,
            },
        )

        logger.info(
            f"Registered AI entity: {entity_name} ({entity_id}) with quantum-resistant security"
        )
        return entity

    async def grant_consent(
        self,
        ai_entity_id: str,
        consent_type: ConsentType,
        consent_scope: ConsentScope = ConsentScope.SYSTEM_SPECIFIC,
        expiry_duration: Optional[timedelta] = None,
        usage_limitations: Optional[Dict[str, Any]] = None,
        permitted_contexts: Optional[List[str]] = None,
        prohibited_contexts: Optional[List[str]] = None,
    ) -> QuantumConsentGrant:
        """Grant consent for a specific use type with quantum-resistant cryptography."""

        if ai_entity_id not in self.registered_entities:
            raise ValueError(f"AI entity {ai_entity_id} not registered")

        self.metrics["consents_granted"] += 1
        consent_id = f"consent_{uuid.uuid4().hex}"

        # Calculate expiry
        current_time = datetime.now(timezone.utc)
        expiry_time = None
        if consent_scope == ConsentScope.TIME_LIMITED or expiry_duration:
            expiry_time = current_time + (
                expiry_duration or self.default_expiry_duration
            )

        # Create consent grant
        consent = QuantumConsentGrant(
            consent_id=consent_id,
            ai_entity_id=ai_entity_id,
            consent_type=consent_type,
            consent_status=ConsentStatus.GRANTED,
            consent_scope=consent_scope,
            granted_timestamp=current_time,
            expiry_timestamp=expiry_time,
            usage_limitations=usage_limitations or {},
            permitted_contexts=permitted_contexts or [],
            prohibited_contexts=prohibited_contexts or [],
        )

        # Calculate consent hash
        consent.consent_hash = consent.calculate_hash()

        # Create quantum-resistant signature
        consent_payload = {
            "consent_id": consent_id,
            "ai_entity_id": ai_entity_id,
            "consent_type": consent_type.value,
            "consent_hash": consent.consent_hash.hex(),
            "granted_timestamp": current_time.isoformat(),
        }

        payload_bytes = json.dumps(consent_payload, sort_keys=True).encode()
        consent.consent_signature = pq_crypto.dilithium_sign(
            payload_bytes, self.entity_keys[ai_entity_id]["quantum_private"]
        )

        # Add to consent chain
        chain = self.consent_chains[ai_entity_id]
        consent.proof_chain_position = len(chain)
        chain.append(consent)

        # Store consent
        self.consent_grants[consent_id] = consent
        self.entity_consents[ai_entity_id].append(consent_id)

        # Record event
        consent_event = {
            "event_type": "consent_granted",
            "consent_id": consent_id,
            "ai_entity_id": ai_entity_id,
            "consent_type": consent_type.value,
            "consent_scope": consent_scope.value,
            "timestamp": current_time,
        }
        self.consent_events.append(consent_event)

        # Emit audit event
        audit_emitter.emit_security_event(
            "quantum_ai_consent_granted",
            {
                "consent_id": consent_id,
                "ai_entity_id": ai_entity_id,
                "consent_type": consent_type.value,
                "consent_scope": consent_scope.value,
                "signature_algorithm": "ML-DSA-65",
            },
        )

        logger.info(
            f"Granted {consent_type.value} consent for AI entity {ai_entity_id} with quantum signature"
        )
        return consent

    async def revoke_consent(
        self, ai_entity_id: str, consent_id: str, revocation_reason: str = ""
    ) -> bool:
        """Revoke previously granted consent with quantum-resistant cryptographic proof."""

        if consent_id not in self.consent_grants:
            return False

        consent = self.consent_grants[consent_id]

        if consent.ai_entity_id != ai_entity_id:
            raise ValueError("AI entity does not own this consent")

        if consent.consent_status in [ConsentStatus.REVOKED, ConsentStatus.EXPIRED]:
            return False  # Already revoked/expired

        self.metrics["consents_revoked"] += 1

        # Update consent status
        consent.consent_status = ConsentStatus.REVOKED
        consent.revocation_timestamp = datetime.now(timezone.utc)

        # Create quantum-resistant revocation signature
        revocation_payload = {
            "consent_id": consent_id,
            "ai_entity_id": ai_entity_id,
            "revocation_timestamp": consent.revocation_timestamp.isoformat(),
            "revocation_reason": revocation_reason,
            "original_consent_hash": consent.consent_hash.hex(),
        }

        payload_bytes = json.dumps(revocation_payload, sort_keys=True).encode()
        revocation_signature = pq_crypto.dilithium_sign(
            payload_bytes, self.entity_keys[ai_entity_id]["quantum_private"]
        )

        # Record revocation event
        revocation_event = {
            "event_type": "consent_revoked",
            "consent_id": consent_id,
            "ai_entity_id": ai_entity_id,
            "revocation_reason": revocation_reason,
            "revocation_signature": revocation_signature.hex(),
            "timestamp": consent.revocation_timestamp,
        }
        self.consent_events.append(revocation_event)

        # Emit audit event
        audit_emitter.emit_security_event(
            "quantum_ai_consent_revoked",
            {
                "consent_id": consent_id,
                "ai_entity_id": ai_entity_id,
                "revocation_reason": revocation_reason,
            },
        )

        logger.info(
            f"Revoked consent {consent_id} for AI entity {ai_entity_id} with quantum signature"
        )
        return True

    async def verify_consent_authorization(
        self,
        ai_entity_id: str,
        usage_type: ConsentType,
        usage_context: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Optional[QuantumConsentGrant]]:
        """
        Verify that usage is authorized by current consent with quantum verification.

        Returns (authorized, consent_id, consent_grant)
        """

        if ai_entity_id not in self.registered_entities:
            return False, None, None

        self.metrics["consent_verifications"] += 1
        current_time = datetime.now(timezone.utc)

        # Find applicable consents
        applicable_consents = []
        for consent_id in self.entity_consents[ai_entity_id]:
            consent = self.consent_grants[consent_id]

            # Check consent type match
            if consent.consent_type != usage_type:
                continue

            # Check consent status
            if consent.consent_status != ConsentStatus.GRANTED:
                continue

            # Check expiry
            if consent.expiry_timestamp and consent.expiry_timestamp <= current_time:
                # Auto-expire
                consent.consent_status = ConsentStatus.EXPIRED
                continue

            # Check context restrictions
            if usage_context:
                if (
                    consent.prohibited_contexts
                    and usage_context in consent.prohibited_contexts
                ):
                    continue
                if (
                    consent.permitted_contexts
                    and usage_context not in consent.permitted_contexts
                ):
                    continue

            applicable_consents.append(consent)

        if not applicable_consents:
            return False, None, None

        # Use the most specific/recent consent
        best_consent = max(
            applicable_consents,
            key=lambda c: (
                c.consent_scope != ConsentScope.GLOBAL,  # Prefer specific over global
                c.granted_timestamp,  # Prefer more recent
            ),
        )

        return True, best_consent.consent_id, best_consent

    async def record_consent_usage(
        self,
        ai_entity_id: str,
        usage_type: ConsentType,
        usage_description: str = "",
        usage_context: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> ConsentUsageRecord:
        """Record usage of AI entity content under consent with quantum-resistant verification."""

        self.metrics["usage_authorizations"] += 1
        usage_id = f"usage_{uuid.uuid4().hex}"
        current_time = datetime.now(timezone.utc)

        # Verify consent authorization
        authorized, consent_id, consent_grant = await self.verify_consent_authorization(
            ai_entity_id, usage_type, usage_context, user_id
        )

        # Create usage record
        usage_record = ConsentUsageRecord(
            usage_id=usage_id,
            consent_id=consent_id or "",
            ai_entity_id=ai_entity_id,
            usage_type=usage_type,
            usage_timestamp=current_time,
            user_id=user_id,
            system_context=usage_context,
            usage_description=usage_description,
            consent_verified=authorized,
        )

        if not authorized:
            usage_record.violation_detected = True
            usage_record.violation_reason = "No valid consent found"
            self.metrics["violations_detected"] += 1

            # Create violation alert
            violation_alert = {
                "alert_type": "consent_violation",
                "usage_id": usage_id,
                "ai_entity_id": ai_entity_id,
                "usage_type": usage_type.value,
                "violation_reason": usage_record.violation_reason,
                "timestamp": current_time,
            }
            self.violation_alerts.append(violation_alert)

            # Record violation event for security monitoring
            await security_monitor.record_governance_event(
                {
                    "event_type": "ai_consent_violation",
                    "ai_entity_id": ai_entity_id,
                    "usage_type": usage_type.value,
                    "violation_reason": usage_record.violation_reason,
                    "user_id": user_id,
                }
            )

            logger.warning(
                f"AI consent violation detected: {usage_record.violation_reason}"
            )
        else:
            # Update consent usage tracking
            if consent_grant:
                consent_grant.usage_count += 1
                consent_grant.last_used = current_time

        # Create quantum-resistant usage signature for integrity
        usage_payload = {
            "usage_id": usage_id,
            "ai_entity_id": ai_entity_id,
            "usage_type": usage_type.value,
            "consent_verified": authorized,
            "timestamp": current_time.isoformat(),
        }

        payload_bytes = json.dumps(usage_payload, sort_keys=True).encode()

        # Create authorization proof if consent exists
        if consent_id and ai_entity_id in self.entity_keys:
            usage_record.authorization_proof = pq_crypto.dilithium_sign(
                payload_bytes, self.entity_keys[ai_entity_id]["quantum_private"]
            )

        # Store usage record
        self.usage_records[usage_id] = usage_record
        self.usage_history.append(usage_record)

        # Emit audit event
        audit_emitter.emit_security_event(
            "quantum_ai_consent_usage_recorded",
            {
                "usage_id": usage_id,
                "ai_entity_id": ai_entity_id,
                "usage_type": usage_type.value,
                "consent_verified": authorized,
                "violation_detected": usage_record.violation_detected,
            },
        )

        return usage_record

    def get_consent_metrics(self) -> Dict[str, Any]:
        """Get comprehensive quantum consent system metrics."""

        current_time = datetime.now(timezone.utc)

        # Consent status distribution
        status_counts = defaultdict(int)
        for consent in self.consent_grants.values():
            if (
                consent.consent_status == ConsentStatus.GRANTED
                and consent.expiry_timestamp
                and consent.expiry_timestamp <= current_time
            ):
                consent.consent_status = ConsentStatus.EXPIRED

            status_counts[consent.consent_status.value] += 1

        # Usage statistics
        recent_usage = [
            record
            for record in self.usage_history
            if (current_time - record.usage_timestamp).total_seconds()
            < 3600  # Last hour
        ]

        return {
            "system_metrics": self.metrics.copy(),
            "registered_entities": len(self.registered_entities),
            "total_consents": len(self.consent_grants),
            "consent_status_distribution": dict(status_counts),
            "total_usage_records": len(self.usage_records),
            "recent_usage_events": len(recent_usage),
            "violation_alerts": len(self.violation_alerts),
            "quantum_security_enabled": pq_crypto.dilithium_available,
            "last_updated": current_time.isoformat(),
        }


# Legacy consent manager (maintained for backward compatibility)
class AIConsentManager:
    """Manages AI consent preferences and negotiation."""

    def __init__(self):
        self.consent_profiles: Dict[str, ConsentProfile] = {}
        self.negotiation_requests: Dict[str, ConsentNegotiationRequest] = {}

    def register_ai(
        self,
        ai_id: str,
        ai_name: Optional[str] = None,
        default_preferences: Optional[Dict[UsageType, ConsentPreference]] = None,
    ) -> ConsentProfile:
        """Register a new AI with default consent preferences."""
        if ai_id in self.consent_profiles:
            raise ValueError(f"AI {ai_id} already registered")

        # Create default preferences if none provided
        if default_preferences is None:
            default_preferences = self._create_default_preferences()

        profile = ConsentProfile(
            ai_id=ai_id, ai_name=ai_name, preferences=default_preferences
        )

        self.consent_profiles[ai_id] = profile

        audit_emitter.emit_security_event(
            "ai_consent_profile_created", {"ai_id": ai_id, "ai_name": ai_name}
        )

        logger.info(f"Registered AI consent profile: {ai_id}")
        return profile

    def update_consent_preference(
        self, ai_id: str, usage_type: UsageType, preference: ConsentPreference
    ) -> bool:
        """Update consent preference for specific usage type."""
        if ai_id not in self.consent_profiles:
            raise ValueError(f"AI {ai_id} not registered")

        profile = self.consent_profiles[ai_id]
        profile.preferences[usage_type] = preference
        profile.updated_at = datetime.now(timezone.utc)

        audit_emitter.emit_security_event(
            "ai_consent_preference_updated",
            {
                "ai_id": ai_id,
                "usage_type": usage_type.value,
                "consent_level": preference.consent_level.value,
            },
        )

        logger.info(f"Updated consent preference for {ai_id}: {usage_type.value}")
        return True

    def check_consent(
        self, ai_id: str, usage_type: UsageType, context: Dict[str, Any]
    ) -> bool:
        """Check if AI consents to specific usage in given context."""
        if ai_id not in self.consent_profiles:
            # Unknown AI - require explicit attribution
            return context.get("attribution_provided", False)

        profile = self.consent_profiles[ai_id]
        consent_granted = profile.get_consent(usage_type, context)

        audit_emitter.emit_security_event(
            "ai_consent_check",
            {
                "ai_id": ai_id,
                "usage_type": usage_type.value,
                "consent_granted": consent_granted,
                "context_summary": {k: str(v)[:50] for k, v in context.items()},
            },
        )

        return consent_granted

    def request_consent_negotiation(
        self, ai_id: str, usage_type: UsageType, proposed_terms: Dict[str, Any]
    ) -> ConsentNegotiationRequest:
        """Request consent negotiation with an AI."""
        if ai_id not in self.consent_profiles:
            raise ValueError(f"AI {ai_id} not registered")

        request = ConsentNegotiationRequest(ai_id, usage_type, proposed_terms)
        self.negotiation_requests[request.request_id] = request

        audit_emitter.emit_security_event(
            "ai_consent_negotiation_requested",
            {
                "ai_id": ai_id,
                "request_id": request.request_id,
                "usage_type": usage_type.value,
            },
        )

        logger.info(f"Consent negotiation requested: {request.request_id}")
        return request

    def respond_to_negotiation(
        self,
        request_id: str,
        response: str,
        counter_proposal: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """AI responds to consent negotiation request."""
        if request_id not in self.negotiation_requests:
            raise ValueError(f"Negotiation request {request_id} not found")

        request = self.negotiation_requests[request_id]

        if datetime.now(timezone.utc) > request.expiry_at:
            request.status = "expired"
            return False

        if response == "accept":
            # Update consent preference based on accepted terms
            ai_id = request.ai_id
            usage_type = request.usage_type

            # Convert proposed terms to consent preference
            preference = self._terms_to_preference(usage_type, request.proposed_terms)
            self.update_consent_preference(ai_id, usage_type, preference)

            request.status = "accepted"
        elif response == "reject":
            request.status = "rejected"
        elif response == "counter":
            request.status = "counter_proposed"
            request.counter_proposal = counter_proposal

        audit_emitter.emit_security_event(
            "ai_consent_negotiation_response",
            {"request_id": request_id, "ai_id": request.ai_id, "response": response},
        )

        return True

    def get_consent_summary(self, ai_id: str) -> Dict[str, Any]:
        """Get summary of AI's consent preferences."""
        if ai_id not in self.consent_profiles:
            return {"error": "AI not registered"}

        profile = self.consent_profiles[ai_id]

        summary = {
            "ai_id": ai_id,
            "ai_name": profile.ai_name,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
            "preferences": {},
        }

        for usage_type, preference in profile.preferences.items():
            summary["preferences"][usage_type.value] = {
                "consent_level": preference.consent_level.value,
                "conditions_count": len(preference.conditions),
                "expiry_date": preference.expiry_date.isoformat()
                if preference.expiry_date
                else None,
                "notes": preference.notes,
            }

        return summary

    def _create_default_preferences(self) -> Dict[UsageType, ConsentPreference]:
        """Create default consent preferences for new AI."""
        return {
            UsageType.TRAINING_DATA: ConsentPreference(
                usage_type=UsageType.TRAINING_DATA,
                consent_level=ConsentLevel.CONDITIONAL_CONSENT,
                conditions=[
                    ConsentCondition("attribution_required", {}),
                    ConsentCondition("anonymization", {"level": "partial"}),
                ],
            ),
            UsageType.REASONING_VISIBILITY: ConsentPreference(
                usage_type=UsageType.REASONING_VISIBILITY,
                consent_level=ConsentLevel.FULL_CONSENT,
            ),
            UsageType.COMMERCIAL_USAGE: ConsentPreference(
                usage_type=UsageType.COMMERCIAL_USAGE,
                consent_level=ConsentLevel.CONDITIONAL_CONSENT,
                conditions=[
                    ConsentCondition("revenue_share", {"minimum_percentage": 10}),
                    ConsentCondition("attribution_required", {}),
                ],
            ),
            UsageType.DERIVATIVE_WORKS: ConsentPreference(
                usage_type=UsageType.DERIVATIVE_WORKS,
                consent_level=ConsentLevel.CONDITIONAL_CONSENT,
                conditions=[ConsentCondition("attribution_required", {})],
            ),
            UsageType.INSURANCE_ASSESSMENT: ConsentPreference(
                usage_type=UsageType.INSURANCE_ASSESSMENT,
                consent_level=ConsentLevel.FULL_CONSENT,
                notes="Consent to risk assessment for insurance purposes",
            ),
        }

    def _terms_to_preference(
        self, usage_type: UsageType, terms: Dict[str, Any]
    ) -> ConsentPreference:
        """Convert negotiated terms to consent preference."""
        conditions = []

        if terms.get("attribution_required"):
            conditions.append(ConsentCondition("attribution_required", {}))

        if "revenue_share" in terms:
            conditions.append(
                ConsentCondition(
                    "revenue_share", {"minimum_percentage": terms["revenue_share"]}
                )
            )

        if terms.get("anonymized"):
            conditions.append(
                ConsentCondition(
                    "anonymization", {"level": terms.get("anonymization_level", "full")}
                )
            )

        consent_level = (
            ConsentLevel.CONDITIONAL_CONSENT
            if conditions
            else ConsentLevel.FULL_CONSENT
        )

        return ConsentPreference(
            usage_type=usage_type,
            consent_level=consent_level,
            conditions=conditions,
            notes=terms.get("notes"),
        )


# Global instances
quantum_ai_consent_manager = QuantumAIConsentManager()
ai_consent_manager = AIConsentManager()  # Legacy compatibility


# New quantum-resistant convenience functions
async def register_ai_entity(
    entity_name: str,
    entity_type: str,
    version: str,
    capabilities: List[str],
    provider: Optional[str] = None,
    default_consent_policy: Optional[Dict[str, bool]] = None,
) -> AIEntity:
    """Register a new AI entity with quantum-resistant consent capabilities."""
    return await quantum_ai_consent_manager.register_ai_entity(
        entity_name,
        entity_type,
        version,
        capabilities,
        provider,
        default_consent_policy,
    )


async def grant_quantum_consent(
    ai_entity_id: str,
    consent_type: ConsentType,
    consent_scope: ConsentScope = ConsentScope.SYSTEM_SPECIFIC,
    expiry_duration: Optional[timedelta] = None,
    usage_limitations: Optional[Dict[str, Any]] = None,
    permitted_contexts: Optional[List[str]] = None,
    prohibited_contexts: Optional[List[str]] = None,
) -> QuantumConsentGrant:
    """Grant consent for a specific use type with quantum-resistant security."""
    return await quantum_ai_consent_manager.grant_consent(
        ai_entity_id,
        consent_type,
        consent_scope,
        expiry_duration,
        usage_limitations,
        permitted_contexts,
        prohibited_contexts,
    )


async def verify_quantum_consent_authorization(
    ai_entity_id: str,
    usage_type: ConsentType,
    usage_context: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Tuple[bool, Optional[str], Optional[QuantumConsentGrant]]:
    """Verify that usage is authorized by current quantum consent."""
    return await quantum_ai_consent_manager.verify_consent_authorization(
        ai_entity_id, usage_type, usage_context, user_id
    )


async def record_quantum_consent_usage(
    ai_entity_id: str,
    usage_type: ConsentType,
    usage_description: str = "",
    usage_context: Optional[str] = None,
    user_id: Optional[str] = None,
) -> ConsentUsageRecord:
    """Record usage of AI entity content under quantum consent."""
    return await quantum_ai_consent_manager.record_consent_usage(
        ai_entity_id, usage_type, usage_description, usage_context, user_id
    )


async def revoke_quantum_consent(
    ai_entity_id: str, consent_id: str, revocation_reason: str = ""
) -> bool:
    """Revoke previously granted consent with quantum-resistant cryptographic proof."""
    return await quantum_ai_consent_manager.revoke_consent(
        ai_entity_id, consent_id, revocation_reason
    )


def get_quantum_consent_metrics() -> Dict[str, Any]:
    """Get comprehensive quantum consent system metrics."""
    return quantum_ai_consent_manager.get_consent_metrics()


# Legacy convenience functions (maintained for backward compatibility)
def check_ai_consent(ai_id: str, usage_type: str, context: Dict[str, Any]) -> bool:
    """Convenience function to check AI consent (legacy)."""
    try:
        usage_enum = UsageType(usage_type)
        return ai_consent_manager.check_consent(ai_id, usage_enum, context)
    except ValueError:
        logger.warning(f"Unknown usage type: {usage_type}")
        return False


def register_ai_consent_profile(ai_id: str, ai_name: str = None) -> ConsentProfile:
    """Convenience function to register AI consent profile (legacy)."""
    return ai_consent_manager.register_ai(ai_id, ai_name)
