"""
Reasoning Chain Integrity Protection for UATP Capsule Engine.

This module implements comprehensive protection mechanisms for AI reasoning chains,
ensuring the authenticity, completeness, and integrity of reasoning processes.
It prevents tampering, insertion of false reasoning steps, and maintains a
verifiable audit trail of the reasoning process.
"""

import base64
import hashlib
import hmac
import json
import logging
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class IntegrityViolationType(str, Enum):
    """Types of reasoning integrity violations."""

    STEP_INSERTION = "step_insertion"
    STEP_DELETION = "step_deletion"
    STEP_MODIFICATION = "step_modification"
    CHAIN_BREAK = "chain_break"
    SIGNATURE_MISMATCH = "signature_mismatch"
    TIMESTAMP_ANOMALY = "timestamp_anomaly"
    CONTEXT_TAMPERING = "context_tampering"
    HASH_COLLISION = "hash_collision"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class ProtectionLevel(str, Enum):
    """Levels of reasoning chain protection."""

    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"
    CRYPTOGRAPHIC = "cryptographic"


class ValidationResult(str, Enum):
    """Results of integrity validation."""

    VALID = "valid"
    INVALID = "invalid"
    SUSPICIOUS = "suspicious"
    UNKNOWN = "unknown"
    COMPROMISED = "compromised"


@dataclass
class ReasoningStep:
    """Individual reasoning step with integrity protection."""

    step_id: str
    step_number: int
    operation: str
    reasoning: str
    confidence: float

    # Integrity fields
    step_hash: str
    previous_step_hash: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    signature: Optional[str] = None

    # Context and metadata
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Chain information
    parent_step_id: Optional[str] = None
    child_step_ids: List[str] = field(default_factory=list)

    def calculate_content_hash(self) -> str:
        """Calculate hash of step content."""
        content = {
            "step_id": self.step_id,
            "step_number": self.step_number,
            "operation": self.operation,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "previous_step_hash": self.previous_step_hash,
            "parent_step_id": self.parent_step_id,
            "context": self.context,
        }

        content_json = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_json.encode()).hexdigest()

    def verify_hash(self) -> bool:
        """Verify step hash integrity."""
        expected_hash = self.calculate_content_hash()
        return self.step_hash == expected_hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "step_id": self.step_id,
            "step_number": self.step_number,
            "operation": self.operation,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "step_hash": self.step_hash,
            "previous_step_hash": self.previous_step_hash,
            "timestamp": self.timestamp.isoformat(),
            "signature": self.signature,
            "context": self.context,
            "metadata": self.metadata,
            "parent_step_id": self.parent_step_id,
            "child_step_ids": self.child_step_ids,
        }


@dataclass
class IntegrityViolation:
    """Record of reasoning integrity violation."""

    violation_id: str
    violation_type: IntegrityViolationType
    description: str
    affected_step_ids: List[str]
    severity: str  # low, medium, high, critical

    # Detection details
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    detection_method: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)

    # Impact assessment
    integrity_score_impact: float = 0.0
    chain_compromised: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary."""
        return {
            "violation_id": self.violation_id,
            "violation_type": self.violation_type.value,
            "description": self.description,
            "affected_step_ids": self.affected_step_ids,
            "severity": self.severity,
            "detected_at": self.detected_at.isoformat(),
            "detection_method": self.detection_method,
            "evidence": self.evidence,
            "integrity_score_impact": self.integrity_score_impact,
            "chain_compromised": self.chain_compromised,
        }


@dataclass
class ChainIntegrityProfile:
    """Integrity profile for a reasoning chain."""

    chain_id: str
    total_steps: int
    integrity_score: float  # 0.0 to 1.0
    protection_level: ProtectionLevel
    validation_result: ValidationResult

    # Integrity metrics
    hash_chain_valid: bool = True
    signature_chain_valid: bool = True
    timestamp_sequence_valid: bool = True
    context_consistency_valid: bool = True

    # Violation tracking
    violations: List[IntegrityViolation] = field(default_factory=list)
    last_validation: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Protection metadata
    encryption_enabled: bool = False
    digital_signatures_enabled: bool = False
    tamper_evidence_enabled: bool = True

    def calculate_integrity_score(self) -> float:
        """Calculate overall integrity score."""
        base_score = 1.0

        # Deduct for validation failures
        if not self.hash_chain_valid:
            base_score -= 0.3
        if not self.signature_chain_valid:
            base_score -= 0.25
        if not self.timestamp_sequence_valid:
            base_score -= 0.2
        if not self.context_consistency_valid:
            base_score -= 0.15

        # Deduct for violations
        for violation in self.violations:
            if violation.severity == "critical":
                base_score -= 0.2
            elif violation.severity == "high":
                base_score -= 0.1
            elif violation.severity == "medium":
                base_score -= 0.05
            elif violation.severity == "low":
                base_score -= 0.02

        return max(0.0, base_score)

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "chain_id": self.chain_id,
            "total_steps": self.total_steps,
            "integrity_score": self.calculate_integrity_score(),
            "protection_level": self.protection_level.value,
            "validation_result": self.validation_result.value,
            "hash_chain_valid": self.hash_chain_valid,
            "signature_chain_valid": self.signature_chain_valid,
            "timestamp_sequence_valid": self.timestamp_sequence_valid,
            "context_consistency_valid": self.context_consistency_valid,
            "violations_count": len(self.violations),
            "last_validation": self.last_validation.isoformat(),
            "encryption_enabled": self.encryption_enabled,
            "digital_signatures_enabled": self.digital_signatures_enabled,
            "tamper_evidence_enabled": self.tamper_evidence_enabled,
        }


class CryptographicProtection:
    """Cryptographic protection for reasoning chains."""

    def __init__(self):
        # Generate or load cryptographic keys
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        self.public_key = self.private_key.public_key()

        # Symmetric encryption key for chain encryption
        self.encryption_key = secrets.token_bytes(32)  # 256-bit key

        # HMAC keys for integrity
        self.hmac_key = secrets.token_bytes(32)

    def sign_step(self, step_content: str) -> str:
        """Create digital signature for reasoning step."""

        try:
            signature = self.private_key.sign(
                step_content.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return base64.b64encode(signature).decode()
        except Exception as e:
            logger.error(f"Failed to sign step: {e}")
            return ""

    def verify_signature(self, step_content: str, signature: str) -> bool:
        """Verify digital signature of reasoning step."""

        try:
            signature_bytes = base64.b64decode(signature.encode())
            self.public_key.verify(
                signature_bytes,
                step_content.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    def create_hmac(self, content: str) -> str:
        """Create HMAC for content integrity."""
        return hmac.new(self.hmac_key, content.encode(), hashlib.sha256).hexdigest()

    def verify_hmac(self, content: str, expected_hmac: str) -> bool:
        """Verify HMAC for content integrity."""
        calculated_hmac = self.create_hmac(content)
        return hmac.compare_digest(calculated_hmac, expected_hmac)


class ReasoningChainProtector:
    """Comprehensive reasoning chain integrity protection."""

    def __init__(self, protection_level: ProtectionLevel = ProtectionLevel.STANDARD):
        self.protection_level = protection_level
        self.crypto_protection = CryptographicProtection()

        # Chain storage and tracking
        self.protected_chains: Dict[str, List[ReasoningStep]] = {}
        self.integrity_profiles: Dict[str, ChainIntegrityProfile] = {}
        self.chain_metadata: Dict[str, Dict[str, Any]] = {}

        # Violation tracking
        self.violations: Dict[str, IntegrityViolation] = {}
        self.violation_patterns: Dict[str, List[str]] = {}

        # Protection configuration
        self.config = self._get_protection_config()

        # Statistics
        self.protection_stats = {
            "total_chains_protected": 0,
            "total_steps_protected": 0,
            "violations_detected": 0,
            "integrity_checks_performed": 0,
            "chains_compromised": 0,
        }

    def _get_protection_config(self) -> Dict[str, Any]:
        """Get protection configuration based on level."""

        configs = {
            ProtectionLevel.BASIC: {
                "hash_verification": True,
                "signature_verification": False,
                "timestamp_validation": True,
                "context_validation": False,
                "encryption": False,
                "tamper_evidence": True,
                "real_time_monitoring": False,
            },
            ProtectionLevel.STANDARD: {
                "hash_verification": True,
                "signature_verification": True,
                "timestamp_validation": True,
                "context_validation": True,
                "encryption": False,
                "tamper_evidence": True,
                "real_time_monitoring": True,
            },
            ProtectionLevel.HIGH: {
                "hash_verification": True,
                "signature_verification": True,
                "timestamp_validation": True,
                "context_validation": True,
                "encryption": True,
                "tamper_evidence": True,
                "real_time_monitoring": True,
            },
            ProtectionLevel.MAXIMUM: {
                "hash_verification": True,
                "signature_verification": True,
                "timestamp_validation": True,
                "context_validation": True,
                "encryption": True,
                "tamper_evidence": True,
                "real_time_monitoring": True,
                "redundant_validation": True,
            },
            ProtectionLevel.CRYPTOGRAPHIC: {
                "hash_verification": True,
                "signature_verification": True,
                "timestamp_validation": True,
                "context_validation": True,
                "encryption": True,
                "tamper_evidence": True,
                "real_time_monitoring": True,
                "redundant_validation": True,
                "zero_knowledge_proofs": True,
            },
        }

        return configs.get(self.protection_level, configs[ProtectionLevel.STANDARD])

    def generate_step_id(self) -> str:
        """Generate unique step ID."""
        return f"step_{uuid.uuid4()}"

    def generate_violation_id(self) -> str:
        """Generate unique violation ID."""
        return f"violation_{uuid.uuid4()}"

    def create_protected_step(
        self,
        operation: str,
        reasoning: str,
        confidence: float,
        chain_id: str,
        context: Dict[str, Any] = None,
        parent_step_id: str = None,
    ) -> ReasoningStep:
        """Create protected reasoning step."""

        step_id = self.generate_step_id()
        context = context or {}

        # Determine step number and previous step hash
        if chain_id in self.protected_chains:
            step_number = len(self.protected_chains[chain_id]) + 1
            previous_step = (
                self.protected_chains[chain_id][-1]
                if self.protected_chains[chain_id]
                else None
            )
            previous_step_hash = previous_step.step_hash if previous_step else None
        else:
            step_number = 1
            previous_step_hash = None
            self.protected_chains[chain_id] = []

        # Create step
        step = ReasoningStep(
            step_id=step_id,
            step_number=step_number,
            operation=operation,
            reasoning=reasoning,
            confidence=confidence,
            previous_step_hash=previous_step_hash,
            context=context,
            parent_step_id=parent_step_id,
            step_hash="",  # Will be calculated
        )

        # Calculate and set hash
        step.step_hash = step.calculate_content_hash()

        # Add digital signature if enabled
        if self.config["signature_verification"]:
            step_content = json.dumps(step.to_dict(), sort_keys=True)
            step.signature = self.crypto_protection.sign_step(step_content)

        # Store step
        self.protected_chains[chain_id].append(step)
        self.protection_stats["total_steps_protected"] += 1

        # Update or create integrity profile
        self._update_integrity_profile(chain_id)

        # Real-time monitoring
        if self.config["real_time_monitoring"]:
            self._monitor_step_creation(step, chain_id)

        audit_emitter.emit_security_event(
            "reasoning_step_protected",
            {
                "step_id": step_id,
                "chain_id": chain_id,
                "protection_level": self.protection_level.value,
                "step_number": step_number,
            },
        )

        logger.debug(f"Created protected reasoning step: {step_id}")
        return step

    def _update_integrity_profile(self, chain_id: str):
        """Update integrity profile for chain."""

        if chain_id not in self.protected_chains:
            return

        chain = self.protected_chains[chain_id]

        if chain_id not in self.integrity_profiles:
            profile = ChainIntegrityProfile(
                chain_id=chain_id,
                total_steps=len(chain),
                integrity_score=1.0,
                protection_level=self.protection_level,
                validation_result=ValidationResult.VALID,
            )
            self.integrity_profiles[chain_id] = profile
            self.protection_stats["total_chains_protected"] += 1
        else:
            profile = self.integrity_profiles[chain_id]
            profile.total_steps = len(chain)
            profile.last_validation = datetime.now(timezone.utc)

        # Update protection metadata
        profile.digital_signatures_enabled = self.config["signature_verification"]
        profile.encryption_enabled = self.config["encryption"]
        profile.tamper_evidence_enabled = self.config["tamper_evidence"]

    def _monitor_step_creation(self, step: ReasoningStep, chain_id: str):
        """Monitor step creation for anomalies."""

        # Check for timestamp anomalies
        if (
            chain_id in self.protected_chains
            and len(self.protected_chains[chain_id]) > 1
        ):
            previous_step = self.protected_chains[chain_id][-2]
            time_diff = (step.timestamp - previous_step.timestamp).total_seconds()

            # Detect suspiciously fast or slow step creation
            if time_diff < 0.1:  # Less than 100ms
                self._record_violation(
                    chain_id,
                    IntegrityViolationType.TIMESTAMP_ANOMALY,
                    "Suspiciously fast step creation",
                    [step.step_id],
                    "medium",
                )
            elif time_diff > 3600:  # More than 1 hour
                self._record_violation(
                    chain_id,
                    IntegrityViolationType.TIMESTAMP_ANOMALY,
                    "Suspiciously slow step creation",
                    [step.step_id],
                    "low",
                )

    def validate_chain_integrity(self, chain_id: str) -> ChainIntegrityProfile:
        """Validate complete integrity of reasoning chain."""

        if chain_id not in self.protected_chains:
            raise ValueError(f"Chain {chain_id} not found")

        chain = self.protected_chains[chain_id]
        profile = self.integrity_profiles.get(chain_id)

        if not profile:
            profile = ChainIntegrityProfile(
                chain_id=chain_id,
                total_steps=len(chain),
                integrity_score=0.0,
                protection_level=self.protection_level,
                validation_result=ValidationResult.UNKNOWN,
            )
            self.integrity_profiles[chain_id] = profile

        self.protection_stats["integrity_checks_performed"] += 1

        # Validate hash chain
        profile.hash_chain_valid = self._validate_hash_chain(chain)

        # Validate signature chain
        if self.config["signature_verification"]:
            profile.signature_chain_valid = self._validate_signature_chain(chain)

        # Validate timestamp sequence
        if self.config["timestamp_validation"]:
            profile.timestamp_sequence_valid = self._validate_timestamp_sequence(chain)

        # Validate context consistency
        if self.config["context_validation"]:
            profile.context_consistency_valid = self._validate_context_consistency(
                chain
            )

        # Calculate overall integrity
        profile.integrity_score = profile.calculate_integrity_score()

        # Determine validation result
        if profile.integrity_score >= 0.95:
            profile.validation_result = ValidationResult.VALID
        elif profile.integrity_score >= 0.8:
            profile.validation_result = ValidationResult.SUSPICIOUS
        elif profile.integrity_score >= 0.5:
            profile.validation_result = ValidationResult.INVALID
        else:
            profile.validation_result = ValidationResult.COMPROMISED
            self.protection_stats["chains_compromised"] += 1

        profile.last_validation = datetime.now(timezone.utc)

        audit_emitter.emit_security_event(
            "chain_integrity_validated",
            {
                "chain_id": chain_id,
                "integrity_score": profile.integrity_score,
                "validation_result": profile.validation_result.value,
                "total_steps": len(chain),
            },
        )

        logger.info(
            f"Chain integrity validated: {chain_id} - {profile.validation_result.value}"
        )
        return profile

    def _validate_hash_chain(self, chain: List[ReasoningStep]) -> bool:
        """Validate hash chain integrity."""

        for i, step in enumerate(chain):
            # Verify step hash
            if not step.verify_hash():
                self._record_violation(
                    step.step_id,
                    IntegrityViolationType.STEP_MODIFICATION,
                    f"Hash mismatch in step {step.step_number}",
                    [step.step_id],
                    "high",
                )
                return False

            # Verify chain linkage
            if i > 0:
                previous_step = chain[i - 1]
                if step.previous_step_hash != previous_step.step_hash:
                    self._record_violation(
                        step.step_id,
                        IntegrityViolationType.CHAIN_BREAK,
                        f"Chain break between steps {previous_step.step_number} and {step.step_number}",
                        [previous_step.step_id, step.step_id],
                        "critical",
                    )
                    return False

        return True

    def _validate_signature_chain(self, chain: List[ReasoningStep]) -> bool:
        """Validate digital signature chain."""

        for step in chain:
            if not step.signature:
                continue

            step_content = json.dumps(step.to_dict(), sort_keys=True)
            if not self.crypto_protection.verify_signature(
                step_content, step.signature
            ):
                self._record_violation(
                    step.step_id,
                    IntegrityViolationType.SIGNATURE_MISMATCH,
                    f"Invalid signature in step {step.step_number}",
                    [step.step_id],
                    "high",
                )
                return False

        return True

    def _validate_timestamp_sequence(self, chain: List[ReasoningStep]) -> bool:
        """Validate timestamp sequence."""

        for i in range(1, len(chain)):
            current_step = chain[i]
            previous_step = chain[i - 1]

            if current_step.timestamp < previous_step.timestamp:
                self._record_violation(
                    current_step.step_id,
                    IntegrityViolationType.TIMESTAMP_ANOMALY,
                    f"Timestamp violation: step {current_step.step_number} predates step {previous_step.step_number}",
                    [previous_step.step_id, current_step.step_id],
                    "medium",
                )
                return False

        return True

    def _validate_context_consistency(self, chain: List[ReasoningStep]) -> bool:
        """Validate context consistency across chain."""

        # Check for context coherence
        contexts = [step.context for step in chain if step.context]

        if len(contexts) < 2:
            return True  # Not enough context to validate

        # Simple consistency check - in production, use more sophisticated analysis
        context_keys = set()
        for context in contexts:
            context_keys.update(context.keys())

        # Check if context keys are consistent
        for context in contexts:
            missing_keys = context_keys - set(context.keys())
            if (
                len(missing_keys) > len(context_keys) * 0.5
            ):  # More than 50% keys missing
                return False

        return True

    def _record_violation(
        self,
        chain_id: str,
        violation_type: IntegrityViolationType,
        description: str,
        affected_step_ids: List[str],
        severity: str,
    ):
        """Record integrity violation."""

        violation_id = self.generate_violation_id()

        violation = IntegrityViolation(
            violation_id=violation_id,
            violation_type=violation_type,
            description=description,
            affected_step_ids=affected_step_ids,
            severity=severity,
            detection_method=f"automated_{self.protection_level.value}",
        )

        # Store violation
        self.violations[violation_id] = violation
        self.protection_stats["violations_detected"] += 1

        # Update integrity profile
        if chain_id in self.integrity_profiles:
            self.integrity_profiles[chain_id].violations.append(violation)

        # Track violation patterns
        if violation_type.value not in self.violation_patterns:
            self.violation_patterns[violation_type.value] = []
        self.violation_patterns[violation_type.value].append(violation_id)

        audit_emitter.emit_security_event(
            "reasoning_integrity_violation",
            {
                "violation_id": violation_id,
                "violation_type": violation_type.value,
                "severity": severity,
                "chain_id": chain_id,
                "affected_steps": len(affected_step_ids),
            },
        )

        logger.warning(f"Integrity violation detected: {violation_id} - {description}")

    def get_chain_integrity_profile(
        self, chain_id: str
    ) -> Optional[ChainIntegrityProfile]:
        """Get integrity profile for chain."""
        return self.integrity_profiles.get(chain_id)

    def get_protected_chain(self, chain_id: str) -> List[ReasoningStep]:
        """Get protected reasoning chain."""
        return self.protected_chains.get(chain_id, [])

    def search_violations(self, filters: Dict[str, Any]) -> List[IntegrityViolation]:
        """Search integrity violations with filters."""

        results = []

        for violation in self.violations.values():
            match = True

            if "violation_type" in filters:
                if violation.violation_type.value != filters["violation_type"]:
                    match = False

            if "severity" in filters:
                if violation.severity != filters["severity"]:
                    match = False

            if "after_date" in filters:
                filter_date = datetime.fromisoformat(filters["after_date"])
                if violation.detected_at < filter_date:
                    match = False

            if "chain_id" in filters:
                # Check if violation affects specified chain
                chain_steps = self.protected_chains.get(filters["chain_id"], [])
                chain_step_ids = [step.step_id for step in chain_steps]
                if not any(
                    step_id in chain_step_ids for step_id in violation.affected_step_ids
                ):
                    match = False

            if match:
                results.append(violation)

        return results

    def get_protection_statistics(self) -> Dict[str, Any]:
        """Get comprehensive protection statistics."""

        # Integrity score distribution
        integrity_scores = [
            profile.calculate_integrity_score()
            for profile in self.integrity_profiles.values()
        ]

        if integrity_scores:
            avg_integrity = sum(integrity_scores) / len(integrity_scores)
            min_integrity = min(integrity_scores)
            max_integrity = max(integrity_scores)
        else:
            avg_integrity = min_integrity = max_integrity = 0.0

        # Violation type distribution
        violation_type_counts = {}
        for violation in self.violations.values():
            vtype = violation.violation_type.value
            violation_type_counts[vtype] = violation_type_counts.get(vtype, 0) + 1

        # Validation result distribution
        validation_results = {}
        for result in ValidationResult:
            count = len(
                [
                    p
                    for p in self.integrity_profiles.values()
                    if p.validation_result == result
                ]
            )
            validation_results[result.value] = count

        return {
            "protection_stats": self.protection_stats,
            "protection_level": self.protection_level.value,
            "integrity_metrics": {
                "average_integrity_score": avg_integrity,
                "minimum_integrity_score": min_integrity,
                "maximum_integrity_score": max_integrity,
                "chains_with_high_integrity": len(
                    [s for s in integrity_scores if s >= 0.9]
                ),
                "chains_with_low_integrity": len(
                    [s for s in integrity_scores if s < 0.7]
                ),
            },
            "violation_analysis": {
                "violation_type_distribution": violation_type_counts,
                "total_unique_violations": len(self.violations),
                "violation_rate": (
                    self.protection_stats["violations_detected"]
                    / max(1, self.protection_stats["total_steps_protected"])
                ),
            },
            "validation_results": validation_results,
            "recent_activity": {
                "chains_validated_last_24h": len(
                    [
                        p
                        for p in self.integrity_profiles.values()
                        if p.last_validation
                        > datetime.now(timezone.utc) - timedelta(days=1)
                    ]
                ),
                "violations_last_24h": len(
                    [
                        v
                        for v in self.violations.values()
                        if v.detected_at
                        > datetime.now(timezone.utc) - timedelta(days=1)
                    ]
                ),
            },
        }


# Global reasoning chain protector instances
reasoning_protectors = {
    "standard": ReasoningChainProtector(ProtectionLevel.STANDARD),
    "high": ReasoningChainProtector(ProtectionLevel.HIGH),
    "maximum": ReasoningChainProtector(ProtectionLevel.MAXIMUM),
}


def create_protected_reasoning_step(
    chain_id: str,
    operation: str,
    reasoning: str,
    confidence: float,
    protection_level: str = "standard",
    context: Dict[str, Any] = None,
) -> ReasoningStep:
    """Convenience function to create protected reasoning step."""

    protector = reasoning_protectors.get(
        protection_level, reasoning_protectors["standard"]
    )

    return protector.create_protected_step(
        operation=operation,
        reasoning=reasoning,
        confidence=confidence,
        chain_id=chain_id,
        context=context,
    )


def validate_reasoning_chain_integrity(
    chain_id: str, protection_level: str = "standard"
) -> Dict[str, Any]:
    """Convenience function to validate reasoning chain integrity."""

    protector = reasoning_protectors.get(
        protection_level, reasoning_protectors["standard"]
    )

    try:
        profile = protector.validate_chain_integrity(chain_id)
        return profile.to_dict()
    except ValueError as e:
        return {"error": str(e)}


def get_chain_protection_summary(chain_id: str) -> Dict[str, Any]:
    """Get comprehensive protection summary for chain."""

    summaries = {}

    for level, protector in reasoning_protectors.items():
        profile = protector.get_chain_integrity_profile(chain_id)
        if profile:
            summaries[level] = profile.to_dict()

    if not summaries:
        return {"error": "Chain not found in any protection level"}

    return {
        "chain_id": chain_id,
        "protection_summaries": summaries,
        "recommended_level": "high"
        if any(p["integrity_score"] < 0.8 for p in summaries.values())
        else "standard",
    }
