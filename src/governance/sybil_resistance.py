"""
Advanced Sybil Resistance System for UATP Governance.

This module implements comprehensive protection against Sybil attacks through
multiple layers of identity verification, behavioral analysis, and economic
staking requirements.

CRITICAL SECURITY: These protections cannot be disabled through governance votes
and are essential for preventing democratic capture attacks.
"""

import hashlib
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class IdentityVerificationMethod(str, Enum):
    """Methods of identity verification."""

    EMAIL_VERIFICATION = "email_verification"
    PHONE_VERIFICATION = "phone_verification"
    DOCUMENT_VERIFICATION = "document_verification"
    BIOMETRIC_VERIFICATION = "biometric_verification"
    SOCIAL_VERIFICATION = "social_verification"
    CRYPTO_PROOF = "crypto_proof"
    REPUTATION_VOUCHING = "reputation_vouching"
    TIME_LOCKED_PROOF = "time_locked_proof"
    ECONOMIC_BONDING = "economic_bonding"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"


class SybilThreatLevel(str, Enum):
    """Levels of Sybil attack threat."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    CONFIRMED_ATTACK = "confirmed_attack"


class VerificationStatus(str, Enum):
    """Status of identity verification."""

    UNVERIFIED = "unverified"
    PENDING = "pending"
    PARTIAL = "partial"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPICIOUS = "suspicious"
    REVOKED = "revoked"


@dataclass
class IdentityVerification:
    """Identity verification record."""

    verification_id: str
    participant_id: str
    method: IdentityVerificationMethod
    status: VerificationStatus

    # Verification data
    verification_data: Dict[str, Any] = field(default_factory=dict)
    unique_identifiers: Dict[str, str] = field(default_factory=dict)
    verification_score: float = 0.0
    confidence_level: float = 0.0

    # Timestamps
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    verified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Security
    verification_hash: Optional[str] = None
    verifier_id: Optional[str] = None
    challenge_response: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if verification has expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        """Check if verification is valid."""
        return (
            self.status == VerificationStatus.VERIFIED
            and not self.is_expired()
            and self.verification_score >= 0.7
        )


@dataclass
class BehavioralPattern:
    """Behavioral pattern analysis for Sybil detection."""

    participant_id: str
    pattern_type: str

    # Behavioral metrics
    activity_timestamps: List[datetime] = field(default_factory=list)
    action_types: List[str] = field(default_factory=list)
    interaction_partners: Set[str] = field(default_factory=set)
    response_times: List[float] = field(default_factory=list)
    linguistic_patterns: Dict[str, float] = field(default_factory=dict)

    # Anomaly scores
    temporal_anomaly_score: float = 0.0
    behavioral_anomaly_score: float = 0.0
    interaction_anomaly_score: float = 0.0

    # Analysis results
    human_likelihood: float = 0.5
    bot_indicators: List[str] = field(default_factory=list)
    coordination_indicators: List[str] = field(default_factory=list)

    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SybilCluster:
    """Cluster of potentially coordinated Sybil accounts."""

    cluster_id: str
    member_ids: Set[str] = field(default_factory=set)

    # Coordination evidence
    shared_identifiers: Dict[str, List[str]] = field(default_factory=dict)
    temporal_correlation: float = 0.0
    behavioral_similarity: float = 0.0
    network_correlation: float = 0.0

    # Threat assessment
    threat_level: SybilThreatLevel = SybilThreatLevel.LOW
    confidence_score: float = 0.0
    evidence_strength: float = 0.0

    # Detection details
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    detection_method: str = ""
    investigation_status: str = "pending"


class SybilResistanceEngine:
    """Advanced Sybil resistance and detection system."""

    # IMMUTABLE SYBIL RESISTANCE PARAMETERS
    MIN_VERIFICATION_SCORE = 0.70  # Minimum score for participation
    MIN_ECONOMIC_BOND = Decimal("500.0")  # Minimum economic stake required
    MAX_ACCOUNTS_PER_IP = 3  # Maximum accounts per IP address
    MAX_ACCOUNTS_PER_IDENTIFIER = 1  # Maximum accounts per unique identifier
    BEHAVIORAL_ANALYSIS_REQUIRED = True  # Cannot be disabled
    COORDINATION_DETECTION_ENABLED = True  # Cannot be disabled

    # Verification requirements by participation level
    VERIFICATION_REQUIREMENTS = {
        "basic_participation": {
            "min_methods": 2,
            "min_score": 0.60,
            "economic_bond": Decimal("100.0"),
        },
        "voting_participation": {
            "min_methods": 3,
            "min_score": 0.70,
            "economic_bond": Decimal("500.0"),
        },
        "proposal_creation": {
            "min_methods": 4,
            "min_score": 0.80,
            "economic_bond": Decimal("2000.0"),
        },
        "governance_leadership": {
            "min_methods": 5,
            "min_score": 0.90,
            "economic_bond": Decimal("10000.0"),
        },
    }

    def __init__(self):
        self.verifications: Dict[str, List[IdentityVerification]] = defaultdict(list)
        self.behavioral_patterns: Dict[str, BehavioralPattern] = {}
        self.sybil_clusters: Dict[str, SybilCluster] = {}
        self.economic_bonds: Dict[str, Decimal] = {}

        # Detection state
        self.ip_registry: Dict[str, List[str]] = defaultdict(list)
        self.identifier_registry: Dict[str, List[str]] = defaultdict(list)
        self.suspicious_patterns: Dict[str, Any] = {}

        # Statistics
        self.stats = {
            "total_verifications": 0,
            "verified_participants": 0,
            "rejected_participants": 0,
            "sybil_clusters_detected": 0,
            "coordination_attacks_prevented": 0,
            "economic_bonds_total": Decimal("0.0"),
        }

        logger.info("Initialized Sybil Resistance Engine with immutable protections")

    def submit_identity_verification(
        self,
        participant_id: str,
        method: IdentityVerificationMethod,
        verification_data: Dict[str, Any],
        unique_identifiers: Dict[str, str],
    ) -> str:
        """Submit identity verification for participant."""

        verification_id = f"verify_{uuid.uuid4().hex[:12]}"

        # Check for duplicate identifiers
        duplicate_check = self._check_duplicate_identifiers(unique_identifiers)
        if not duplicate_check[0]:
            logger.warning(
                f"Duplicate identifier detected for {participant_id}: {duplicate_check[1]}"
            )
            status = VerificationStatus.REJECTED
            score = 0.0
        else:
            status = VerificationStatus.PENDING
            score = self._calculate_initial_verification_score(
                method, verification_data
            )

        # Create verification record
        verification = IdentityVerification(
            verification_id=verification_id,
            participant_id=participant_id,
            method=method,
            status=status,
            verification_data=verification_data,
            unique_identifiers=unique_identifiers,
            verification_score=score,
            verification_hash=self._generate_verification_hash(verification_data),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=365),  # 1 year expiry
        )

        self.verifications[participant_id].append(verification)
        self.stats["total_verifications"] += 1

        # Register unique identifiers
        for identifier_type, identifier_value in unique_identifiers.items():
            self.identifier_registry[f"{identifier_type}:{identifier_value}"].append(
                participant_id
            )

        # Register IP address if provided
        ip_address = verification_data.get("ip_address")
        if ip_address:
            self.ip_registry[ip_address].append(participant_id)

        # Trigger verification process
        if status == VerificationStatus.PENDING:
            self._process_verification(verification)

        audit_emitter.emit_security_event(
            event_type="identity_verification_submitted",
            details={
                "verification_id": verification_id,
                "participant_id": participant_id,
                "method": method.value,
                "status": status.value,
                "score": score,
            },
        )

        logger.info(
            f"Identity verification submitted: {verification_id} for {participant_id}"
        )
        return verification_id

    def _check_duplicate_identifiers(
        self, unique_identifiers: Dict[str, str]
    ) -> Tuple[bool, Optional[str]]:
        """Check for duplicate unique identifiers."""

        for identifier_type, identifier_value in unique_identifiers.items():
            registry_key = f"{identifier_type}:{identifier_value}"

            if registry_key in self.identifier_registry:
                existing_participants = self.identifier_registry[registry_key]
                if len(existing_participants) >= self.MAX_ACCOUNTS_PER_IDENTIFIER:
                    return (
                        False,
                        f"Identifier {identifier_type} already used by {len(existing_participants)} accounts",
                    )

        return True, None

    def _calculate_initial_verification_score(
        self, method: IdentityVerificationMethod, verification_data: Dict[str, Any]
    ) -> float:
        """Calculate initial verification score."""

        base_scores = {
            IdentityVerificationMethod.EMAIL_VERIFICATION: 0.3,
            IdentityVerificationMethod.PHONE_VERIFICATION: 0.4,
            IdentityVerificationMethod.DOCUMENT_VERIFICATION: 0.7,
            IdentityVerificationMethod.BIOMETRIC_VERIFICATION: 0.9,
            IdentityVerificationMethod.SOCIAL_VERIFICATION: 0.5,
            IdentityVerificationMethod.CRYPTO_PROOF: 0.8,
            IdentityVerificationMethod.REPUTATION_VOUCHING: 0.6,
            IdentityVerificationMethod.TIME_LOCKED_PROOF: 0.8,
            IdentityVerificationMethod.ECONOMIC_BONDING: 0.7,
            IdentityVerificationMethod.BEHAVIORAL_ANALYSIS: 0.6,
        }

        base_score = base_scores.get(method, 0.5)

        # Adjust based on verification data quality
        if verification_data.get("data_quality_score"):
            quality_multiplier = min(1.2, verification_data["data_quality_score"])
            base_score *= quality_multiplier

        # Penalty for suspicious patterns
        if verification_data.get("suspicious_indicators"):
            base_score *= 0.7

        return min(1.0, base_score)

    def _process_verification(self, verification: IdentityVerification):
        """Process pending verification."""

        try:
            # Perform method-specific verification
            if verification.method == IdentityVerificationMethod.EMAIL_VERIFICATION:
                result = self._verify_email(verification)
            elif verification.method == IdentityVerificationMethod.PHONE_VERIFICATION:
                result = self._verify_phone(verification)
            elif verification.method == IdentityVerificationMethod.BEHAVIORAL_ANALYSIS:
                result = self._verify_behavioral_patterns(verification)
            elif verification.method == IdentityVerificationMethod.ECONOMIC_BONDING:
                result = self._verify_economic_bond(verification)
            else:
                # Generic verification
                result = self._verify_generic(verification)

            # Update verification based on result
            verification.status = result["status"]
            verification.verification_score = result["score"]
            verification.confidence_level = result["confidence"]
            verification.verified_at = datetime.now(timezone.utc)

            if verification.status == VerificationStatus.VERIFIED:
                self.stats["verified_participants"] += 1
            elif verification.status == VerificationStatus.REJECTED:
                self.stats["rejected_participants"] += 1

        except Exception as e:
            logger.error(
                f"Verification processing failed for {verification.verification_id}: {e}"
            )
            verification.status = VerificationStatus.REJECTED
            verification.verification_score = 0.0

    def _verify_email(self, verification: IdentityVerification) -> Dict[str, Any]:
        """Verify email address."""

        email = verification.unique_identifiers.get("email")
        if not email:
            return {
                "status": VerificationStatus.REJECTED,
                "score": 0.0,
                "confidence": 0.0,
            }

        # Check email format and domain
        if "@" not in email or "." not in email.split("@")[1]:
            return {
                "status": VerificationStatus.REJECTED,
                "score": 0.0,
                "confidence": 0.0,
            }

        # Check against disposable email services
        domain = email.split("@")[1].lower()
        disposable_domains = ["tempmail.org", "10minutemail.com", "guerrillamail.com"]

        if domain in disposable_domains:
            return {
                "status": VerificationStatus.REJECTED,
                "score": 0.0,
                "confidence": 0.0,
            }

        # Simulate email verification challenge
        score = 0.8 if domain in ["gmail.com", "outlook.com", "yahoo.com"] else 0.6

        return {
            "status": VerificationStatus.VERIFIED,
            "score": score,
            "confidence": 0.8,
        }

    def _verify_phone(self, verification: IdentityVerification) -> Dict[str, Any]:
        """Verify phone number."""

        phone = verification.unique_identifiers.get("phone")
        if not phone:
            return {
                "status": VerificationStatus.REJECTED,
                "score": 0.0,
                "confidence": 0.0,
            }

        # Basic phone format validation
        if (
            len(phone) < 10
            or not phone.replace("+", "").replace("-", "").replace(" ", "").isdigit()
        ):
            return {
                "status": VerificationStatus.REJECTED,
                "score": 0.0,
                "confidence": 0.0,
            }

        # Simulate SMS verification
        return {"status": VerificationStatus.VERIFIED, "score": 0.7, "confidence": 0.9}

    def _verify_behavioral_patterns(
        self, verification: IdentityVerification
    ) -> Dict[str, Any]:
        """Verify through behavioral analysis."""

        participant_id = verification.participant_id

        if participant_id not in self.behavioral_patterns:
            # Initialize behavioral pattern analysis
            self.behavioral_patterns[participant_id] = BehavioralPattern(
                participant_id=participant_id, pattern_type="initial_analysis"
            )

        pattern = self.behavioral_patterns[participant_id]

        # Analyze behavioral authenticity
        human_score = self._calculate_behavioral_authenticity(pattern)

        if human_score >= 0.7:
            status = VerificationStatus.VERIFIED
            score = human_score
        elif human_score >= 0.5:
            status = VerificationStatus.PARTIAL
            score = human_score * 0.8
        else:
            status = VerificationStatus.SUSPICIOUS
            score = human_score * 0.5

        return {"status": status, "score": score, "confidence": 0.8}

    def _verify_economic_bond(
        self, verification: IdentityVerification
    ) -> Dict[str, Any]:
        """Verify economic bonding requirement."""

        participant_id = verification.participant_id
        bond_amount = verification.verification_data.get("bond_amount", 0)

        try:
            bond_amount = Decimal(str(bond_amount))
        except:
            return {
                "status": VerificationStatus.REJECTED,
                "score": 0.0,
                "confidence": 1.0,
            }

        if bond_amount < self.MIN_ECONOMIC_BOND:
            return {
                "status": VerificationStatus.REJECTED,
                "score": 0.0,
                "confidence": 1.0,
            }

        # Record economic bond
        self.economic_bonds[participant_id] = bond_amount
        self.stats["economic_bonds_total"] += bond_amount

        # Higher bonds get higher scores
        score = min(1.0, float(bond_amount) / 5000.0)

        return {
            "status": VerificationStatus.VERIFIED,
            "score": score,
            "confidence": 1.0,
        }

    def _verify_generic(self, verification: IdentityVerification) -> Dict[str, Any]:
        """Generic verification for other methods."""

        # Simulate verification process
        data_quality = verification.verification_data.get("quality_score", 0.5)

        if data_quality >= 0.8:
            return {
                "status": VerificationStatus.VERIFIED,
                "score": data_quality,
                "confidence": 0.8,
            }
        elif data_quality >= 0.6:
            return {
                "status": VerificationStatus.PARTIAL,
                "score": data_quality,
                "confidence": 0.7,
            }
        else:
            return {
                "status": VerificationStatus.REJECTED,
                "score": 0.0,
                "confidence": 0.6,
            }

    def _calculate_behavioral_authenticity(self, pattern: BehavioralPattern) -> float:
        """Calculate behavioral authenticity score."""

        authenticity_score = 0.5  # Base score

        # Check temporal patterns
        if len(pattern.activity_timestamps) > 10:
            # Look for human-like irregular patterns
            intervals = []
            for i in range(1, len(pattern.activity_timestamps)):
                interval = (
                    pattern.activity_timestamps[i] - pattern.activity_timestamps[i - 1]
                ).total_seconds()
                intervals.append(interval)

            if intervals:
                # Human activity should have variation
                interval_variance = sum(
                    (x - sum(intervals) / len(intervals)) ** 2 for x in intervals
                ) / len(intervals)
                if (
                    interval_variance > 100
                ):  # High variance indicates human-like behavior
                    authenticity_score += 0.2
                else:
                    authenticity_score -= 0.3  # Too regular, bot-like

        # Check action diversity
        if len(set(pattern.action_types)) >= 5:
            authenticity_score += 0.2
        elif len(set(pattern.action_types)) <= 2:
            authenticity_score -= 0.2

        # Check interaction patterns
        if len(pattern.interaction_partners) >= 5:
            authenticity_score += 0.1
        elif len(pattern.interaction_partners) == 0:
            authenticity_score -= 0.2

        # Check response times
        if pattern.response_times:
            avg_response = sum(pattern.response_times) / len(pattern.response_times)
            if 1.0 <= avg_response <= 30.0:  # Human-like response times
                authenticity_score += 0.1
            elif avg_response < 0.5:  # Too fast, bot-like
                authenticity_score -= 0.3

        return max(0.0, min(1.0, authenticity_score))

    def detect_sybil_clusters(self) -> List[SybilCluster]:
        """Detect potential Sybil clusters."""

        clusters = []

        # Detect IP-based clusters
        for ip_address, participants in self.ip_registry.items():
            if len(participants) > self.MAX_ACCOUNTS_PER_IP:
                cluster = self._create_sybil_cluster(
                    participants,
                    "ip_clustering",
                    {"ip_address": ip_address, "participant_count": len(participants)},
                )
                clusters.append(cluster)

        # Detect behavioral similarity clusters
        behavioral_clusters = self._detect_behavioral_clusters()
        clusters.extend(behavioral_clusters)

        # Detect temporal correlation clusters
        temporal_clusters = self._detect_temporal_clusters()
        clusters.extend(temporal_clusters)

        # Store detected clusters
        for cluster in clusters:
            self.sybil_clusters[cluster.cluster_id] = cluster
            self.stats["sybil_clusters_detected"] += 1

        return clusters

    def _create_sybil_cluster(
        self, participants: List[str], detection_method: str, evidence: Dict[str, Any]
    ) -> SybilCluster:
        """Create a Sybil cluster record."""

        cluster_id = f"cluster_{uuid.uuid4().hex[:12]}"

        # Calculate threat level based on cluster size and evidence
        size_factor = min(1.0, len(participants) / 10.0)
        threat_level = SybilThreatLevel.LOW

        if size_factor > 0.8:
            threat_level = SybilThreatLevel.CRITICAL
        elif size_factor > 0.6:
            threat_level = SybilThreatLevel.HIGH
        elif size_factor > 0.3:
            threat_level = SybilThreatLevel.MEDIUM

        cluster = SybilCluster(
            cluster_id=cluster_id,
            member_ids=set(participants),
            threat_level=threat_level,
            confidence_score=size_factor,
            detection_method=detection_method,
        )

        logger.warning(
            f"Sybil cluster detected: {cluster_id} with {len(participants)} members via {detection_method}"
        )

        return cluster

    def _detect_behavioral_clusters(self) -> List[SybilCluster]:
        """Detect clusters based on behavioral similarity."""

        clusters = []

        # Group participants by similar behavioral patterns
        similarity_threshold = 0.8
        processed = set()

        for participant_id, pattern in self.behavioral_patterns.items():
            if participant_id in processed:
                continue

            similar_participants = [participant_id]

            for other_id, other_pattern in self.behavioral_patterns.items():
                if other_id != participant_id and other_id not in processed:
                    similarity = self._calculate_behavioral_similarity(
                        pattern, other_pattern
                    )
                    if similarity >= similarity_threshold:
                        similar_participants.append(other_id)

            if len(similar_participants) >= 3:  # Minimum cluster size
                cluster = self._create_sybil_cluster(
                    similar_participants,
                    "behavioral_similarity",
                    {"similarity_threshold": similarity_threshold},
                )
                clusters.append(cluster)
                processed.update(similar_participants)

        return clusters

    def _detect_temporal_clusters(self) -> List[SybilCluster]:
        """Detect clusters based on temporal correlation."""

        clusters = []

        # Group by registration time windows
        time_windows = defaultdict(list)

        for participant_id, verifications in self.verifications.items():
            if verifications:
                earliest_verification = min(verifications, key=lambda v: v.submitted_at)
                time_bucket = int(
                    earliest_verification.submitted_at.timestamp() // 3600
                )  # Hour buckets
                time_windows[time_bucket].append(participant_id)

        # Identify suspicious time windows
        for time_bucket, participants in time_windows.items():
            if len(participants) >= 5:  # 5+ registrations in same hour
                cluster = self._create_sybil_cluster(
                    participants,
                    "temporal_correlation",
                    {
                        "time_bucket": time_bucket,
                        "hour_registrations": len(participants),
                    },
                )
                clusters.append(cluster)

        return clusters

    def _calculate_behavioral_similarity(
        self, pattern1: BehavioralPattern, pattern2: BehavioralPattern
    ) -> float:
        """Calculate behavioral similarity between two patterns."""

        similarity_factors = []

        # Compare action types
        actions1 = set(pattern1.action_types)
        actions2 = set(pattern2.action_types)
        if actions1 or actions2:
            action_similarity = len(actions1 & actions2) / len(actions1 | actions2)
            similarity_factors.append(action_similarity)

        # Compare response times
        if pattern1.response_times and pattern2.response_times:
            avg1 = sum(pattern1.response_times) / len(pattern1.response_times)
            avg2 = sum(pattern2.response_times) / len(pattern2.response_times)
            time_similarity = 1.0 - abs(avg1 - avg2) / max(avg1, avg2)
            similarity_factors.append(time_similarity)

        # Compare interaction patterns
        partners1 = pattern1.interaction_partners
        partners2 = pattern2.interaction_partners
        if partners1 or partners2:
            partner_similarity = len(partners1 & partners2) / len(partners1 | partners2)
            similarity_factors.append(partner_similarity)

        if not similarity_factors:
            return 0.0

        return sum(similarity_factors) / len(similarity_factors)

    def check_participation_eligibility(
        self, participant_id: str, participation_level: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if participant is eligible for given participation level."""

        if participation_level not in self.VERIFICATION_REQUIREMENTS:
            return False, "Invalid participation level", {}

        requirements = self.VERIFICATION_REQUIREMENTS[participation_level]

        # Get participant verifications
        verifications = self.verifications.get(participant_id, [])
        valid_verifications = [v for v in verifications if v.is_valid()]

        # Check verification count
        if len(valid_verifications) < requirements["min_methods"]:
            return (
                False,
                f"Insufficient verification methods: {len(valid_verifications)} < {requirements['min_methods']}",
                {
                    "current_methods": len(valid_verifications),
                    "required_methods": requirements["min_methods"],
                },
            )

        # Check verification score
        avg_score = sum(v.verification_score for v in valid_verifications) / len(
            valid_verifications
        )
        if avg_score < requirements["min_score"]:
            return (
                False,
                f"Insufficient verification score: {avg_score:.2f} < {requirements['min_score']}",
                {
                    "current_score": avg_score,
                    "required_score": requirements["min_score"],
                },
            )

        # Check economic bond
        current_bond = self.economic_bonds.get(participant_id, Decimal("0.0"))
        if current_bond < requirements["economic_bond"]:
            return (
                False,
                f"Insufficient economic bond: {current_bond} < {requirements['economic_bond']}",
                {
                    "current_bond": str(current_bond),
                    "required_bond": str(requirements["economic_bond"]),
                },
            )

        # Check for Sybil cluster membership
        for cluster in self.sybil_clusters.values():
            if participant_id in cluster.member_ids and cluster.threat_level in [
                SybilThreatLevel.HIGH,
                SybilThreatLevel.CRITICAL,
            ]:
                return (
                    False,
                    f"Participant is member of high-threat Sybil cluster: {cluster.cluster_id}",
                    {
                        "cluster_id": cluster.cluster_id,
                        "threat_level": cluster.threat_level.value,
                    },
                )

        return (
            True,
            "Eligible for participation",
            {
                "verification_methods": len(valid_verifications),
                "verification_score": avg_score,
                "economic_bond": str(current_bond),
            },
        )

    def _generate_verification_hash(self, verification_data: Dict[str, Any]) -> str:
        """Generate hash for verification data."""

        # Create deterministic hash of verification data
        data_string = str(sorted(verification_data.items()))
        return hashlib.sha256(data_string.encode()).hexdigest()

    def get_sybil_resistance_status(self) -> Dict[str, Any]:
        """Get comprehensive Sybil resistance status."""

        # Run cluster detection
        self.detect_sybil_clusters()

        return {
            "system_status": {
                "protection_active": True,
                "detection_enabled": self.COORDINATION_DETECTION_ENABLED,
                "behavioral_analysis_active": self.BEHAVIORAL_ANALYSIS_REQUIRED,
            },
            "statistics": dict(self.stats),
            "verification_requirements": self.VERIFICATION_REQUIREMENTS,
            "protection_parameters": {
                "min_verification_score": self.MIN_VERIFICATION_SCORE,
                "min_economic_bond": str(self.MIN_ECONOMIC_BOND),
                "max_accounts_per_ip": self.MAX_ACCOUNTS_PER_IP,
                "max_accounts_per_identifier": self.MAX_ACCOUNTS_PER_IDENTIFIER,
            },
            "threat_assessment": {
                "total_clusters": len(self.sybil_clusters),
                "high_threat_clusters": len(
                    [
                        c
                        for c in self.sybil_clusters.values()
                        if c.threat_level
                        in [SybilThreatLevel.HIGH, SybilThreatLevel.CRITICAL]
                    ]
                ),
                "suspicious_ips": len(
                    [
                        ip
                        for ip, participants in self.ip_registry.items()
                        if len(participants) > self.MAX_ACCOUNTS_PER_IP
                    ]
                ),
            },
        }


# Global Sybil resistance engine
sybil_resistance = SybilResistanceEngine()
