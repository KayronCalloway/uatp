"""
Provenance System - Truth Layers for UATP Capsules
===================================================

Implements the gold standard approach to separating:
1. Event layer - what literally happened (tool_verified)
2. Evidence layer - what can be verified from artifacts (artifact_verified)
3. Interpretation layer - what the model thinks (derived/heuristic/speculative)
4. Judgment layer - gated recommendations (must be earned)

Every claim carries a proof tag. No masquerading.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ProofLevel(str, Enum):
    """How a claim can be proven."""

    # Verified by tool execution or cryptographic proof
    TOOL_VERIFIED = "tool_verified"

    # Verified by artifact (file hash, git commit, timestamp)
    ARTIFACT_VERIFIED = "artifact_verified"

    # Cryptographically verified (signature, hash chain)
    CRYPTO_VERIFIED = "crypto_verified"

    # Derived from verified facts through logical inference
    DERIVED = "derived"

    # Based on heuristics or patterns
    HEURISTIC = "heuristic"

    # Model-generated interpretation
    MODEL_GENERATED = "model_generated"

    # Speculative or uncertain
    SPECULATIVE = "speculative"

    # Asserted by user without verification
    USER_ASSERTED = "user_asserted"

    # Not yet tested or verified
    UNTESTED = "untested"


@dataclass
class Claim:
    """A single claim with its proof status."""

    value: Any
    proof: ProofLevel
    source: Optional[str] = None  # Where this came from
    timestamp: Optional[datetime] = None
    confidence: Optional[float] = None  # Only meaningful for verified claims

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "value": self.value,
            "proof": self.proof.value,
        }
        if self.source:
            result["source"] = self.source
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        if self.confidence is not None:
            result["confidence"] = self.confidence
        return result


@dataclass
class Event:
    """Something that literally happened."""

    event_type: str  # "user_message", "tool_call", "file_change", etc.
    timestamp: datetime
    data: Dict[str, Any]
    proof: ProofLevel = ProofLevel.TOOL_VERIFIED
    source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "proof": self.proof.value,
            "source": self.source,
        }


@dataclass
class Evidence:
    """Something that can be verified from artifacts."""

    claim: str
    verified: bool
    proof: ProofLevel
    artifact: Optional[str] = None  # File path, commit hash, etc.
    verification_method: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "verified": self.verified,
            "proof": self.proof.value,
            "artifact": self.artifact,
            "verification_method": self.verification_method,
        }


class InterpretationStatus(str, Enum):
    """Status of an interpretation."""

    UNVERIFIED = "unverified"
    PARTIALLY_VERIFIED = "partially_verified"
    CONTRADICTED = "contradicted"
    STALE = "stale"


@dataclass
class Interpretation:
    """What the model thinks - always marked as interpretive."""

    summary: str
    claims: List[Claim]
    status: InterpretationStatus = InterpretationStatus.UNVERIFIED
    semantic_drift_detected: bool = False
    drift_description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "claims": [c.to_dict() for c in self.claims],
            "status": self.status.value,
            "semantic_drift_detected": self.semantic_drift_detected,
            "drift_description": self.drift_description,
        }


class JudgmentGate(str, Enum):
    """Gates that must pass for judgment labels."""

    PROVENANCE_COMPLETE = "provenance_complete"
    SIGNATURE_VERIFIED = "signature_verified"
    TIMESTAMP_VERIFIED = "timestamp_verified"
    NO_SEMANTIC_DRIFT = "no_semantic_drift"
    EVIDENCE_CHAIN_COMPLETE = "evidence_chain_complete"
    INTERPRETATION_SEPARATED = "interpretation_separated"
    CONFIDENCE_CALIBRATED = "confidence_calibrated"


@dataclass
class Judgment:
    """Gated recommendations - must be earned, not claimed."""

    # Gates that have passed
    gates_passed: List[JudgmentGate] = field(default_factory=list)

    # Explicit flags for legal/insurance readiness
    court_admissible: bool = False
    insurance_ready: bool = False
    legal_reliance_ready: bool = False

    # Why not ready (if not ready)
    blockers: List[str] = field(default_factory=list)

    def check_court_admissible(self) -> bool:
        """Check if capsule can claim court admissibility."""
        required = {
            JudgmentGate.PROVENANCE_COMPLETE,
            JudgmentGate.SIGNATURE_VERIFIED,
            JudgmentGate.TIMESTAMP_VERIFIED,
            JudgmentGate.NO_SEMANTIC_DRIFT,
            JudgmentGate.EVIDENCE_CHAIN_COMPLETE,
            JudgmentGate.INTERPRETATION_SEPARATED,
        }
        passed = set(self.gates_passed)
        missing = required - passed
        if missing:
            self.blockers = [f"Missing gate: {g.value}" for g in missing]
            self.court_admissible = False
        else:
            self.court_admissible = True
        return self.court_admissible

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gates_passed": [g.value for g in self.gates_passed],
            "court_admissible": self.court_admissible,
            "insurance_ready": self.insurance_ready,
            "legal_reliance_ready": self.legal_reliance_ready,
            "blockers": self.blockers,
        }


@dataclass
class TrustPosture:
    """Multi-dimensional trust assessment instead of single score."""

    provenance_integrity: str  # "high", "medium", "low"
    artifact_verifiability: str
    semantic_alignment: str
    decision_completeness: str
    risk_calibration: str
    legal_reliance_readiness: str
    operational_utility: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provenance_integrity": self.provenance_integrity,
            "artifact_verifiability": self.artifact_verifiability,
            "semantic_alignment": self.semantic_alignment,
            "decision_completeness": self.decision_completeness,
            "risk_calibration": self.risk_calibration,
            "legal_reliance_readiness": self.legal_reliance_readiness,
            "operational_utility": self.operational_utility,
        }


@dataclass
class LayeredCapsule:
    """
    A capsule with properly separated layers.

    This is the gold standard structure:
    - events: What literally happened (verified)
    - evidence: What artifacts prove (verified)
    - interpretation: What the model thinks (unverified by default)
    - judgment: Gated recommendations (must be earned)
    - trust_posture: Multi-dimensional assessment
    """

    capsule_id: str
    timestamp: datetime
    events: List[Event]
    evidence: List[Evidence]
    interpretation: Interpretation
    judgment: Judgment
    trust_posture: TrustPosture

    # Cryptographic verification (the strong part)
    signature: Optional[str] = None
    signature_verified: bool = False
    timestamp_authority: Optional[str] = None
    timestamp_verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capsule_id": self.capsule_id,
            "timestamp": self.timestamp.isoformat(),
            "layers": {
                "events": [e.to_dict() for e in self.events],
                "evidence": [e.to_dict() for e in self.evidence],
                "interpretation": self.interpretation.to_dict(),
                "judgment": self.judgment.to_dict(),
            },
            "trust_posture": self.trust_posture.to_dict(),
            "verification": {
                "signature": self.signature,
                "signature_verified": self.signature_verified,
                "timestamp_authority": self.timestamp_authority,
                "timestamp_verified": self.timestamp_verified,
            },
        }


def detect_semantic_drift(
    last_user_message: str,
    summary: str,
    decision: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """
    Detect if summary/decision drifted from the last user request.

    Returns (drift_detected, description).
    """
    if not last_user_message or not summary:
        return False, None

    # Normalize for comparison
    user_lower = last_user_message.lower().strip()
    summary_lower = summary.lower()

    # Extract key topics from user message
    # Simple heuristic: look for question words and key nouns
    question_indicators = ["how", "what", "why", "where", "when", "can", "does", "is"]

    user_is_question = any(user_lower.startswith(q) for q in question_indicators)

    if user_is_question:
        # Extract key terms from the question (words > 3 chars, not stop words)
        stop_words = {
            "the",
            "and",
            "for",
            "that",
            "this",
            "with",
            "from",
            "have",
            "what",
            "how",
            "why",
            "where",
            "when",
            "can",
            "does",
            "are",
            "you",
            "your",
            "would",
            "could",
            "should",
            "will",
            "just",
        }
        user_terms = {
            w for w in user_lower.split() if len(w) > 3 and w not in stop_words
        }

        # Check if summary addresses these terms
        summary_terms = set(summary_lower.split())
        overlap = user_terms & summary_terms

        if len(user_terms) > 0 and len(overlap) / len(user_terms) < 0.3:
            return True, (
                f"Summary may not address user question. "
                f"User asked about: {', '.join(list(user_terms)[:5])}. "
                f"Summary mentions: {', '.join(list(overlap)[:5]) or 'none of these'}"
            )

    return False, None


def build_trust_posture(
    events: List[Event],
    evidence: List[Evidence],
    interpretation: Interpretation,
    judgment: Judgment,
    signature_verified: bool,
    timestamp_verified: bool,
) -> TrustPosture:
    """Build multi-dimensional trust assessment."""

    # Provenance: based on signature and timestamp
    if signature_verified and timestamp_verified:
        provenance = "high"
    elif signature_verified or timestamp_verified:
        provenance = "medium"
    else:
        provenance = "low"

    # Artifact verifiability: based on evidence
    verified_evidence = [e for e in evidence if e.verified]
    if len(evidence) > 0:
        ratio = len(verified_evidence) / len(evidence)
        artifact = "high" if ratio > 0.8 else "medium" if ratio > 0.5 else "low"
    else:
        artifact = "low"

    # Semantic alignment: based on drift detection
    if interpretation.semantic_drift_detected:
        semantic = "low"
    elif interpretation.status == InterpretationStatus.UNVERIFIED:
        semantic = "medium"
    else:
        semantic = "high"

    # Decision completeness: based on untested claims
    untested = [c for c in interpretation.claims if c.proof == ProofLevel.UNTESTED]
    if len(untested) == 0:
        completeness = "high"
    elif len(untested) < len(interpretation.claims) * 0.3:
        completeness = "medium"
    else:
        completeness = "low"

    # Risk calibration: always low unless we have real calibration
    risk_cal = "low"  # Honest default

    # Legal readiness: based on judgment gates
    legal = "ready" if judgment.court_admissible else "not_ready"

    # Operational utility: high if we have events and evidence
    if len(events) > 0 and len(evidence) > 0:
        operational = "high"
    elif len(events) > 0:
        operational = "medium"
    else:
        operational = "low"

    return TrustPosture(
        provenance_integrity=provenance,
        artifact_verifiability=artifact,
        semantic_alignment=semantic,
        decision_completeness=completeness,
        risk_calibration=risk_cal,
        legal_reliance_readiness=legal,
        operational_utility=operational,
    )
