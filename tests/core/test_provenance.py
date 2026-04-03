"""
Tests for the Gold Standard Provenance System.

Tests the layered capsule architecture:
- ProofLevel enum and proper labeling
- Event, Evidence, Interpretation, Judgment structures
- Trust posture calculation
- Semantic drift detection
"""

from datetime import datetime, timezone

import pytest

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


class TestProofLevel:
    """Test ProofLevel enum values."""

    def test_all_proof_levels_exist(self):
        """Verify all expected proof levels are defined."""
        expected = [
            "tool_verified",
            "artifact_verified",
            "crypto_verified",
            "derived",
            "heuristic",
            "model_generated",
            "speculative",
            "user_asserted",
            "untested",
            "human_verified",
        ]
        actual = [p.value for p in ProofLevel]
        assert set(expected) == set(actual)

    def test_proof_level_is_string_enum(self):
        """ProofLevel should be usable as string."""
        assert ProofLevel.TOOL_VERIFIED.value == "tool_verified"
        assert str(ProofLevel.TOOL_VERIFIED.value) == "tool_verified"


class TestClaim:
    """Test Claim dataclass."""

    def test_claim_with_proof_level(self):
        """Claims should carry proof level."""
        claim = Claim(
            value="The function returns correct output",
            proof=ProofLevel.TOOL_VERIFIED,
            source="unit_test",
        )
        assert claim.proof == ProofLevel.TOOL_VERIFIED
        assert claim.value == "The function returns correct output"

    def test_claim_to_dict(self):
        """Claims should serialize to dict."""
        claim = Claim(
            value="Test passed",
            proof=ProofLevel.TOOL_VERIFIED,
            source="pytest",
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            confidence=0.95,
        )
        d = claim.to_dict()
        assert d["value"] == "Test passed"
        assert d["proof"] == "tool_verified"
        assert d["source"] == "pytest"
        assert d["confidence"] == 0.95

    def test_model_generated_claim(self):
        """Model-generated claims should be clearly marked."""
        claim = Claim(
            value="I think the code is correct",
            proof=ProofLevel.MODEL_GENERATED,
            source="claude",
        )
        assert claim.proof == ProofLevel.MODEL_GENERATED


class TestEvent:
    """Test Event dataclass."""

    def test_event_creation(self):
        """Events should capture what literally happened."""
        event = Event(
            event_type="user_message",
            timestamp=datetime.now(timezone.utc),
            data={"content_length": 100, "role": "user"},
            proof=ProofLevel.TOOL_VERIFIED,
            source="claude_code_capture",
        )
        assert event.event_type == "user_message"
        assert event.proof == ProofLevel.TOOL_VERIFIED

    def test_event_to_dict(self):
        """Events should serialize properly."""
        ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        event = Event(
            event_type="tool_call",
            timestamp=ts,
            data={"tool": "Read", "success": True},
            proof=ProofLevel.TOOL_VERIFIED,
        )
        d = event.to_dict()
        assert d["event_type"] == "tool_call"
        assert d["proof"] == "tool_verified"
        assert "2026-01-01" in d["timestamp"]


class TestEvidence:
    """Test Evidence dataclass."""

    def test_verified_evidence(self):
        """Verified evidence should be marked as such."""
        evidence = Evidence(
            claim="File was signed by key holder",
            verified=True,
            proof=ProofLevel.CRYPTO_VERIFIED,
            artifact="ed25519:abc123...",
            verification_method="ed25519_signature",
        )
        assert evidence.verified is True
        assert evidence.proof == ProofLevel.CRYPTO_VERIFIED

    def test_unverified_evidence(self):
        """Unverified evidence should be honest about it."""
        evidence = Evidence(
            claim="Timestamp is accurate",
            verified=False,
            proof=ProofLevel.HEURISTIC,
            verification_method="local_clock",
        )
        assert evidence.verified is False
        assert evidence.proof == ProofLevel.HEURISTIC


class TestInterpretation:
    """Test Interpretation dataclass."""

    def test_interpretation_defaults_to_unverified(self):
        """Interpretations should be UNVERIFIED by default."""
        interp = Interpretation(
            summary="The code looks good",
            claims=[],
        )
        assert interp.status == InterpretationStatus.UNVERIFIED

    def test_semantic_drift_flag(self):
        """Semantic drift should be detectable."""
        interp = Interpretation(
            summary="Discussed weather patterns",
            claims=[],
            semantic_drift_detected=True,
            drift_description="Summary doesn't address user's code question",
        )
        assert interp.semantic_drift_detected is True
        assert "code question" in interp.drift_description


class TestJudgment:
    """Test Judgment dataclass and gate checking."""

    def test_empty_judgment_not_court_admissible(self):
        """Judgment with no gates passed should not be court admissible."""
        judgment = Judgment()
        result = judgment.check_court_admissible()
        assert result is False
        assert judgment.court_admissible is False
        assert len(judgment.blockers) > 0

    def test_partial_gates_not_court_admissible(self):
        """Partial gate compliance should not grant court admissibility."""
        judgment = Judgment()
        judgment.gates_passed = [
            JudgmentGate.SIGNATURE_VERIFIED,
            JudgmentGate.TIMESTAMP_VERIFIED,
        ]
        result = judgment.check_court_admissible()
        assert result is False
        assert "interpretation_separated" in str(judgment.blockers).lower()

    def test_full_gates_court_admissible(self):
        """All required gates should grant court admissibility."""
        judgment = Judgment()
        judgment.gates_passed = [
            JudgmentGate.PROVENANCE_COMPLETE,
            JudgmentGate.SIGNATURE_VERIFIED,
            JudgmentGate.TIMESTAMP_VERIFIED,
            JudgmentGate.NO_SEMANTIC_DRIFT,
            JudgmentGate.EVIDENCE_CHAIN_COMPLETE,
            JudgmentGate.INTERPRETATION_SEPARATED,
        ]
        result = judgment.check_court_admissible()
        assert result is True
        assert judgment.court_admissible is True
        assert len(judgment.blockers) == 0


class TestSemanticDriftDetection:
    """Test semantic drift detection function."""

    def test_no_drift_when_topics_match(self):
        """No drift when summary addresses user question."""
        drift, desc = detect_semantic_drift(
            last_user_message="How do I fix the login bug?",
            summary="Fixed the login bug by updating the authentication handler.",
        )
        assert drift is False

    def test_drift_when_topics_mismatch(self):
        """Drift detected when summary doesn't address question."""
        drift, desc = detect_semantic_drift(
            last_user_message="How do I fix the login bug?",
            summary="The weather today is sunny with clear skies.",
        )
        assert drift is True
        assert desc is not None

    def test_no_drift_with_empty_inputs(self):
        """Empty inputs should not trigger drift."""
        drift, desc = detect_semantic_drift(
            last_user_message="",
            summary="Some summary",
        )
        assert drift is False

    def test_drift_detection_case_insensitive(self):
        """Drift detection should be case insensitive."""
        drift, desc = detect_semantic_drift(
            last_user_message="How do I fix the LOGIN bug?",
            summary="Fixed the login issue in the authentication system.",
        )
        assert drift is False


class TestTrustPosture:
    """Test trust posture calculation."""

    def test_high_trust_with_verification(self):
        """High trust when signature and timestamp verified."""
        posture = build_trust_posture(
            events=[
                Event(
                    event_type="test",
                    timestamp=datetime.now(timezone.utc),
                    data={},
                    proof=ProofLevel.TOOL_VERIFIED,
                )
            ],
            evidence=[
                Evidence(
                    claim="Signed",
                    verified=True,
                    proof=ProofLevel.CRYPTO_VERIFIED,
                )
            ],
            interpretation=Interpretation(summary="Test", claims=[]),
            judgment=Judgment(),
            signature_verified=True,
            timestamp_verified=True,
        )
        assert posture.provenance_integrity == "high"

    def test_low_trust_without_verification(self):
        """Low trust when nothing is verified."""
        posture = build_trust_posture(
            events=[],
            evidence=[],
            interpretation=Interpretation(
                summary="Test",
                claims=[],
                semantic_drift_detected=True,
            ),
            judgment=Judgment(),
            signature_verified=False,
            timestamp_verified=False,
        )
        assert posture.provenance_integrity == "low"
        assert posture.semantic_alignment == "low"


class TestLayeredCapsule:
    """Test the complete LayeredCapsule structure."""

    def test_layered_capsule_to_dict(self):
        """LayeredCapsule should serialize with all layers."""
        capsule = LayeredCapsule(
            capsule_id="test_123",
            timestamp=datetime.now(timezone.utc),
            events=[],
            evidence=[],
            interpretation=Interpretation(summary="Test", claims=[]),
            judgment=Judgment(),
            trust_posture=TrustPosture(
                provenance_integrity="low",
                artifact_verifiability="low",
                semantic_alignment="medium",
                decision_completeness="low",
                risk_calibration="low",
                legal_reliance_readiness="not_ready",
                operational_utility="low",
            ),
        )
        d = capsule.to_dict()
        assert "capsule_id" in d
        assert "layers" in d
        assert "events" in d["layers"]
        assert "evidence" in d["layers"]
        assert "interpretation" in d["layers"]
        assert "judgment" in d["layers"]
        assert "trust_posture" in d
        assert "verification" in d
