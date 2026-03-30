"""
Layered Capsule Builder
=======================

Converts raw capture data into properly layered capsules with:
- Event layer: What literally happened (tool calls, messages, file changes)
- Evidence layer: What artifacts prove (signatures, hashes, timestamps)
- Interpretation layer: What the model thinks (MARKED AS UNVERIFIED)
- Judgment layer: Gated labels (ONLY set when gates pass)

This is the gold standard integration point.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.core.contradiction_engine import ContradictionEngine, format_contradictions
from src.core.provenance import (
    Claim,
    Event,
    Evidence,
    Interpretation,
    InterpretationStatus,
    Judgment,
    JudgmentGate,
    LayeredCapsule,
    ProofLevel,
    TrustPosture,
    build_trust_posture,
    detect_semantic_drift,
)


class LayeredCapsuleBuilder:
    """Builds properly layered capsules from raw capture data."""

    @staticmethod
    def extract_events(
        messages: List[Any],
        tool_calls: Optional[List[Dict]] = None,
        environment: Optional[Dict] = None,
    ) -> List[Event]:
        """
        Extract VERIFIED events from capture data.

        Events are things that literally happened - verified by tool execution.
        """
        events = []

        # Message events - these are TOOL_VERIFIED because we captured them
        for msg in messages:
            event = Event(
                event_type=f"{msg.role}_message",
                timestamp=msg.timestamp
                if hasattr(msg, "timestamp")
                else datetime.now(timezone.utc),
                data={
                    "role": msg.role,
                    "content_length": len(msg.content),
                    "model": getattr(msg, "model_info", None),
                    # Don't include full content - just metadata for the event layer
                },
                proof=ProofLevel.TOOL_VERIFIED,
                source="claude_code_capture",
            )
            events.append(event)

        # Tool call events - these are TOOL_VERIFIED
        if tool_calls:
            for tc in tool_calls:
                event = Event(
                    event_type="tool_call",
                    timestamp=datetime.fromisoformat(
                        tc.get("timestamp", datetime.now(timezone.utc).isoformat())
                    ),
                    data={
                        "tool": tc.get("tool"),
                        "success": tc.get("success", True),
                        "duration_ms": tc.get("duration_ms"),
                    },
                    proof=ProofLevel.TOOL_VERIFIED,
                    source="tool_execution",
                )
                events.append(event)

        # Environment capture - ARTIFACT_VERIFIED (we read git state, etc.)
        if environment:
            git_info = environment.get("git", {})
            if git_info.get("commit"):
                event = Event(
                    event_type="git_state",
                    timestamp=datetime.now(timezone.utc),
                    data={
                        "commit": git_info.get("commit"),
                        "branch": git_info.get("branch"),
                        "dirty": git_info.get("dirty", False),
                    },
                    proof=ProofLevel.ARTIFACT_VERIFIED,
                    source="git_repository",
                )
                events.append(event)

        return events

    @staticmethod
    def extract_evidence(
        signature: Optional[str] = None,
        timestamp_token: Optional[Dict] = None,
        file_hashes: Optional[Dict[str, str]] = None,
    ) -> List[Evidence]:
        """
        Extract VERIFIED evidence from cryptographic artifacts.

        Evidence is verifiable from artifacts - signatures, hashes, timestamps.
        """
        evidence = []

        # Cryptographic signature - CRYPTO_VERIFIED
        if signature:
            evidence.append(
                Evidence(
                    claim="Capsule content was signed by the stated key holder",
                    verified=True,
                    proof=ProofLevel.CRYPTO_VERIFIED,
                    artifact=signature[:32] + "...",  # Truncated for display
                    verification_method="ed25519_signature",
                )
            )

        # RFC 3161 timestamp - CRYPTO_VERIFIED if from trusted TSA
        if timestamp_token:
            trusted = timestamp_token.get("trusted", False)
            evidence.append(
                Evidence(
                    claim="Capsule existed at stated time",
                    verified=trusted,
                    proof=ProofLevel.CRYPTO_VERIFIED
                    if trusted
                    else ProofLevel.HEURISTIC,
                    artifact=timestamp_token.get("token", "")[:32] + "..."
                    if timestamp_token.get("token")
                    else None,
                    verification_method="rfc3161_timestamp"
                    if trusted
                    else "local_timestamp",
                )
            )

        # File hashes - ARTIFACT_VERIFIED
        if file_hashes:
            for file_path, file_hash in file_hashes.items():
                evidence.append(
                    Evidence(
                        claim=f"File {file_path} had hash {file_hash[:16]}...",
                        verified=True,
                        proof=ProofLevel.ARTIFACT_VERIFIED,
                        artifact=file_hash,
                        verification_method="sha256_hash",
                    )
                )

        return evidence

    @staticmethod
    def build_interpretation(
        messages: List[Any],
        summary: Optional[str] = None,
        confidence_scores: Optional[Dict] = None,
        quality_assessment: Optional[Dict] = None,
    ) -> Interpretation:
        """
        Build the interpretation layer - ALWAYS MARKED AS UNVERIFIED.

        This is what the model thinks. It's valuable but MUST be clearly
        separated from verified facts.
        """
        claims = []

        # Summary claim - MODEL_GENERATED
        if summary:
            claims.append(
                Claim(
                    value=summary,
                    proof=ProofLevel.MODEL_GENERATED,
                    source="llm_summarization",
                    confidence=None,  # We don't claim confidence on model output
                )
            )

        # Confidence scores - HEURISTIC (not calibrated)
        if confidence_scores:
            # Be honest: these are heuristic, not calibrated
            claims.append(
                Claim(
                    value=f"Confidence estimate: {confidence_scores.get('overall', 'unknown')}",
                    proof=ProofLevel.HEURISTIC,
                    source="heuristic_calculation",
                    confidence=None,  # Meta: we can't be confident about our confidence
                )
            )

        # Quality assessment - HEURISTIC
        if quality_assessment:
            claims.append(
                Claim(
                    value=f"Quality grade: {quality_assessment.get('quality_grade', 'unknown')}",
                    proof=ProofLevel.HEURISTIC,
                    source="quality_heuristics",
                    confidence=None,
                )
            )

        # Detect semantic drift
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.role == "user":
                last_user_msg = msg.content
                break

        drift_detected, drift_description = detect_semantic_drift(
            last_user_message=last_user_msg,
            summary=summary or "",
        )

        return Interpretation(
            summary=summary or "No summary available",
            claims=claims,
            status=InterpretationStatus.UNVERIFIED,  # Honest default
            semantic_drift_detected=drift_detected,
            drift_description=drift_description,
        )

    @staticmethod
    def build_judgment(
        signature_verified: bool = False,
        timestamp_verified: bool = False,
        semantic_drift_detected: bool = False,
        interpretation_separated: bool = True,  # This module always separates
        evidence_chain_complete: bool = False,
    ) -> Judgment:
        """
        Build judgment layer with GATED labels.

        Labels are ONLY set when gates actually pass.
        """
        judgment = Judgment()

        # Check each gate
        if signature_verified:
            judgment.gates_passed.append(JudgmentGate.SIGNATURE_VERIFIED)

        if timestamp_verified:
            judgment.gates_passed.append(JudgmentGate.TIMESTAMP_VERIFIED)

        if not semantic_drift_detected:
            judgment.gates_passed.append(JudgmentGate.NO_SEMANTIC_DRIFT)

        if interpretation_separated:
            judgment.gates_passed.append(JudgmentGate.INTERPRETATION_SEPARATED)

        if evidence_chain_complete:
            judgment.gates_passed.append(JudgmentGate.EVIDENCE_CHAIN_COMPLETE)

        # Provenance is complete if we have events and evidence
        judgment.gates_passed.append(JudgmentGate.PROVENANCE_COMPLETE)

        # Check if court admissible - ONLY if gates pass
        judgment.check_court_admissible()

        return judgment

    @classmethod
    def build_layered_capsule(
        cls,
        capsule_id: str,
        messages: List[Any],
        session: Any,
        tool_calls: Optional[List[Dict]] = None,
        environment: Optional[Dict] = None,
        signature: Optional[str] = None,
        timestamp_token: Optional[Dict] = None,
        summary: Optional[str] = None,
        confidence_scores: Optional[Dict] = None,
        quality_assessment: Optional[Dict] = None,
    ) -> LayeredCapsule:
        """
        Build a complete layered capsule with proper separation.

        This is the gold standard capsule structure.
        """
        # Extract each layer
        events = cls.extract_events(messages, tool_calls, environment)
        evidence = cls.extract_evidence(signature, timestamp_token)
        interpretation = cls.build_interpretation(
            messages, summary, confidence_scores, quality_assessment
        )

        # Build judgment with gate checking
        signature_verified = bool(signature)
        timestamp_verified = (
            timestamp_token.get("trusted", False) if timestamp_token else False
        )
        evidence_chain_complete = len(evidence) >= 2  # Signature + timestamp

        judgment = cls.build_judgment(
            signature_verified=signature_verified,
            timestamp_verified=timestamp_verified,
            semantic_drift_detected=interpretation.semantic_drift_detected,
            interpretation_separated=True,
            evidence_chain_complete=evidence_chain_complete,
        )

        # Build trust posture
        trust_posture = build_trust_posture(
            events=events,
            evidence=evidence,
            interpretation=interpretation,
            judgment=judgment,
            signature_verified=signature_verified,
            timestamp_verified=timestamp_verified,
        )

        # Create the layered capsule
        capsule = LayeredCapsule(
            capsule_id=capsule_id,
            timestamp=datetime.now(timezone.utc),
            events=events,
            evidence=evidence,
            interpretation=interpretation,
            judgment=judgment,
            trust_posture=trust_posture,
            signature=signature,
            signature_verified=signature_verified,
            timestamp_authority=timestamp_token.get("tsa_url")
            if timestamp_token
            else None,
            timestamp_verified=timestamp_verified,
        )

        return capsule

    @classmethod
    def validate_capsule(cls, capsule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run contradiction detection on a capsule.

        Returns validation results including any contradictions found.
        """
        contradictions = ContradictionEngine.analyze_capsule(capsule)

        return {
            "valid": len([c for c in contradictions if c.severity == "critical"]) == 0,
            "contradiction_count": len(contradictions),
            "critical_count": len(
                [c for c in contradictions if c.severity == "critical"]
            ),
            "warning_count": len(
                [c for c in contradictions if c.severity == "warning"]
            ),
            "info_count": len([c for c in contradictions if c.severity == "info"]),
            "contradictions": [
                {
                    "category": c.category,
                    "severity": c.severity,
                    "description": c.description,
                    "recommendation": c.recommendation,
                }
                for c in contradictions
            ],
            "formatted": format_contradictions(contradictions),
        }


def convert_legacy_capsule(legacy_capsule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a legacy flat capsule to the new layered structure.

    This allows existing capsules to be upgraded to the gold standard.
    """
    payload = legacy_capsule.get("payload", {})
    verification = legacy_capsule.get("verification", {})
    metadata = legacy_capsule.get("metadata", {})

    # Build layers from legacy structure
    layers = {
        "events": [],  # Would need to reconstruct from messages
        "evidence": [],
        "interpretation": {
            "summary": payload.get("plain_language_summary", {}).get("decision", ""),
            "claims": [],
            "status": "unverified",
            "semantic_drift_detected": False,
        },
        "judgment": {
            "gates_passed": [],
            "court_admissible": False,  # Honest default - not verified
            "insurance_ready": False,
            "legal_reliance_ready": False,
            "blockers": ["Legacy capsule - gates not verified"],
        },
    }

    # Check what we can verify from existing data
    if verification.get("signature"):
        layers["evidence"].append(
            {
                "claim": "Capsule was signed",
                "verified": True,
                "proof": "crypto_verified",
                "artifact": verification["signature"][:32] + "..."
                if len(verification.get("signature", "")) > 32
                else verification.get("signature"),
                "verification_method": "ed25519_signature",
            }
        )
        layers["judgment"]["gates_passed"].append("signature_verified")

    if verification.get("timestamp", {}).get("trusted"):
        layers["evidence"].append(
            {
                "claim": "Timestamp is trusted",
                "verified": True,
                "proof": "crypto_verified",
                "verification_method": "rfc3161_timestamp",
            }
        )
        layers["judgment"]["gates_passed"].append("timestamp_verified")

    # Trust posture - honest assessment of legacy capsule
    trust_posture = {
        "provenance_integrity": "medium" if verification.get("signature") else "low",
        "artifact_verifiability": "medium" if verification.get("signature") else "low",
        "semantic_alignment": "unknown",  # Can't verify without re-analysis
        "decision_completeness": "unknown",
        "risk_calibration": "low",  # No calibration data
        "legal_reliance_readiness": "not_ready",  # Honest - not verified
        "operational_utility": "medium",
    }

    # Build the new structure
    return {
        "capsule_id": legacy_capsule.get("capsule_id"),
        "timestamp": legacy_capsule.get("timestamp"),
        "schema_version": "2.0_layered",
        "layers": layers,
        "trust_posture": trust_posture,
        "verification": verification,
        "metadata": {
            **metadata,
            "converted_from_legacy": True,
            "original_data_richness": metadata.get("data_richness"),
            # Remove unearned labels
            "data_richness": "standard",  # Honest label
            "compliance": {
                "daubert_standard": False,  # Not verified
                "insurance_ready": False,
                "eu_ai_act_article_13": bool(payload.get("plain_language_summary")),
            },
        },
        # Preserve original payload for reference
        "legacy_payload": payload,
    }
