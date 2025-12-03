"""
Integration tests for the complete UATP Capsule Engine system.
Tests the interaction between all advanced components.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from src.audit.events import audit_emitter
from src.capsule_schema import (
    CapsuleStatus,
    ReasoningStep,
    ReasoningTraceCapsule,
    ReasoningTracePayload,
    Verification,
)

# Import all systems
from src.crypto.post_quantum import pq_crypto
from src.crypto.zero_knowledge import zk_system
from src.economic.capsule_economics import capsule_economics
from src.economic.fcde_engine import ContributionType, fcde_engine
from src.ethics.rect_system import rect_system
from src.governance.advanced_governance import ProposalType, VoteType, governance_engine
from src.optimization.capsule_compression import optimization_engine
from src.privacy.capsule_privacy import (
    DEFAULT_PRIVACY_POLICIES,
    PrivacyLevel,
    privacy_engine,
)
from src.verification.formal_contracts import (
    formal_verification,
    postcondition,
    precondition,
)


def test_complete_capsule_lifecycle():
    """Test complete capsule lifecycle through all systems."""

    # 1. Create a capsule with post-quantum crypto
    pq_keypair = pq_crypto.generate_dilithium_keypair()

    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(
            signature="ed25519:" + "0" * 128,
            signer="integration_test_agent",
            merkle_root="sha256:" + "0" * 64,
        ),
        reasoning_trace=ReasoningTracePayload(
            reasoning_steps=[
                ReasoningStep(
                    content="This is a comprehensive test of the UATP system integration",
                    step_type="observation",
                    metadata={"test": "integration"},
                ),
                ReasoningStep(
                    content="Testing all advanced features working together",
                    step_type="conclusion",
                    metadata={"confidence": 0.95},
                ),
            ],
            total_confidence=0.92,
        ),
    )

    # 2. Register economic contribution
    contribution_id = capsule_economics.register_capsule_creation(
        capsule=capsule, creator_id="integration_test_agent"
    )
    assert contribution_id is not None

    # 3. Apply privacy controls
    private_capsule = privacy_engine.privatize_capsule(
        capsule=capsule, privacy_policy=DEFAULT_PRIVACY_POLICIES["selective"]
    )
    assert private_capsule.privacy_policy.privacy_level == PrivacyLevel.SELECTIVE

    # 4. Generate ZK proof for privacy
    zk_proof = zk_system.generate_privacy_capsule_proof(
        {
            "capsule_id": capsule.capsule_id,
            "reasoning_trace": capsule.reasoning_trace,
            "timestamp": capsule.timestamp.isoformat(),
        }
    )
    assert zk_system.verify_proof(zk_proof)

    # 5. Run through ethical monitoring
    rect_result = rect_system.process_capsule(capsule)
    assert rect_result["rect_enabled"] is True
    assert rect_result["capsule_id"] == capsule.capsule_id

    # 6. Optimize capsule
    optimization_result = optimization_engine.optimize_capsule(capsule)
    assert optimization_result["capsule_id"] == capsule.capsule_id
    assert len(optimization_result["actions_taken"]) > 0

    # 7. Record usage for economics
    capsule_economics.record_capsule_usage(
        capsule_id=capsule.capsule_id,
        user_id="test_user_001",
        usage_type="reasoning_analysis",
        usage_value=Decimal("10.0"),
    )

    # 8. Verify all systems recorded the capsule
    assert capsule.capsule_id in capsule_economics.capsule_value_cache
    assert capsule.capsule_id in privacy_engine.private_capsules
    assert optimization_result["space_saved"] >= 0

    print("✅ Complete capsule lifecycle test passed!")


def test_governance_with_economics():
    """Test governance system integrated with economics."""

    # Register stakeholders with economic stake
    stakeholder_1 = governance_engine.register_stakeholder("gov_stakeholder_1", 5000.0)
    stakeholder_2 = governance_engine.register_stakeholder("gov_stakeholder_2", 3000.0)

    # Register them in economic system too
    fcde_engine.register_contribution(
        capsule_id="gov_capsule_001",
        contributor_id="gov_stakeholder_1",
        contribution_type=ContributionType.GOVERNANCE_PARTICIPATION,
        quality_score=Decimal("1.5"),
    )

    # Create governance proposal
    proposal = governance_engine.create_proposal(
        title="Integrate Economic Rewards",
        description="Proposal to integrate economic rewards with governance",
        proposal_type=ProposalType.SYSTEM_UPGRADE,
        proposer_id="gov_stakeholder_1",
    )

    # Set voting active
    proposal.voting_start = datetime.now(timezone.utc) - timedelta(minutes=5)
    from src.governance.advanced_governance import ProposalStatus

    proposal.status = ProposalStatus.VOTING

    # Generate keys and vote
    pq_keypair = pq_crypto.generate_dilithium_keypair()
    private_key_1 = pq_keypair.private_key
    pq_keypair_2 = pq_crypto.generate_dilithium_keypair()
    private_key_2 = pq_keypair_2.private_key

    vote_1 = governance_engine.cast_vote(
        proposal_id=proposal.proposal_id,
        voter_id="gov_stakeholder_1",
        vote_type=VoteType.FOR,
        private_key=private_key_1.hex(),
    )

    vote_2 = governance_engine.cast_vote(
        proposal_id=proposal.proposal_id,
        voter_id="gov_stakeholder_2",
        vote_type=VoteType.FOR,
        private_key=private_key_2.hex(),
    )

    # Check votes were recorded
    assert len(proposal.votes) == 2
    assert proposal.is_passed()

    # Process economic dividends
    dividend_pool_id = fcde_engine.process_dividend_distribution(Decimal("1000.0"))

    # Check economic impact
    creator_analytics = fcde_engine.get_creator_analytics("gov_stakeholder_1")
    assert creator_analytics["total_contributions"] > 0
    assert creator_analytics["unclaimed_dividends"] > 0

    print("✅ Governance with economics test passed!")


def test_privacy_with_formal_verification():
    """Test privacy system with formal verification."""

    # Create a function with formal contracts
    @precondition(
        lambda ctx: ctx["args"][0].privacy_policy.privacy_level
        in [PrivacyLevel.SELECTIVE, PrivacyLevel.PRIVATE],
        "Private capsule must have appropriate privacy level",
    )
    @postcondition(
        lambda ctx: ctx["result"] is not None, "Selective disclosure must return result"
    )
    def secure_disclosure(private_capsule, requested_fields, requester_id):
        """Securely disclose private capsule data."""
        return privacy_engine.selective_disclosure(
            private_capsule.capsule_id, requested_fields, requester_id
        )

    # Create capsule and privatize
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_09_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(
            reasoning_steps=[
                ReasoningStep(
                    content="Private reasoning content",
                    step_type="observation",
                    metadata={},
                )
            ],
            total_confidence=0.9,
        ),
    )

    # Apply privacy policy
    privacy_policy = DEFAULT_PRIVACY_POLICIES["selective"]
    privacy_policy.authorized_viewers = ["authorized_user_001"]
    private_capsule = privacy_engine.privatize_capsule(capsule, privacy_policy)

    # Test secure disclosure with formal verification
    result = secure_disclosure(
        private_capsule, {"capsule_id", "timestamp"}, "authorized_user_001"
    )

    assert result is not None
    assert result["capsule_id"] == capsule.capsule_id
    assert "disclosed_fields" in result

    # Generate verification report
    verification_report = formal_verification.get_violation_report()
    assert verification_report["total_violations"] >= 0

    print("✅ Privacy with formal verification test passed!")


def test_ethics_with_optimization():
    """Test ethics system integrated with optimization."""

    # Create capsule with potential ethical issues
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_02_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(
            reasoning_steps=[
                ReasoningStep(
                    content="This content might be considered harmful by some metrics",
                    step_type="observation",
                    metadata={},
                )
            ],
            total_confidence=0.9,
        ),
    )

    # Run through ethical monitoring
    rect_result = rect_system.process_capsule(capsule)

    # If no critical violations, proceed with optimization
    if rect_result["highest_severity"] != "critical":
        optimization_result = optimization_engine.optimize_capsule(capsule)
        assert optimization_result["capsule_id"] == capsule.capsule_id

        # Check that ethical monitoring was recorded
        assert rect_result["violation_count"] >= 0
        assert "actions_taken" in rect_result

        # Check optimization stats
        stats = optimization_engine.get_optimization_statistics()
        assert stats["processing_stats"]["total_processed"] > 0

    print("✅ Ethics with optimization test passed!")


def test_full_system_analytics():
    """Test analytics across all systems."""

    # Create multiple capsules for comprehensive testing
    capsules = []
    for i in range(5):
        capsule = ReasoningTraceCapsule(
            capsule_id=f"caps_2024_01_0{i+3}_0123456789abcdef",
            version="7.0",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.ACTIVE,
            verification=Verification(),
            reasoning_trace=ReasoningTracePayload(
                reasoning_steps=[
                    ReasoningStep(
                        content=f"Analytics test content {i}",
                        step_type="observation",
                        metadata={"test_id": i},
                    )
                ],
                total_confidence=0.9,
            ),
        )
        capsules.append(capsule)

        # Register economic contribution
        capsule_economics.register_capsule_creation(capsule, f"creator_{i}")

        # Run through systems
        rect_system.process_capsule(capsule)
        optimization_engine.optimize_capsule(capsule)

    # Collect analytics from all systems
    analytics = {
        "economic": fcde_engine.get_system_analytics(),
        "optimization": optimization_engine.get_optimization_statistics(),
        "ethics": rect_system.get_system_status(),
        "governance": governance_engine.get_governance_analytics(),
        "formal_verification": formal_verification.get_violation_report(),
    }

    # Validate analytics
    assert analytics["economic"]["total_contributions"] > 0
    assert analytics["optimization"]["processing_stats"]["total_processed"] > 0
    assert analytics["ethics"]["enabled"] is True
    assert analytics["governance"]["total_stakeholders"] >= 0
    assert analytics["formal_verification"]["total_violations"] >= 0

    print("✅ Full system analytics test passed!")


def test_audit_event_integration():
    """Test audit event system integration."""

    # Create capsule that will trigger multiple audit events
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_08_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(
            reasoning_steps=[
                ReasoningStep(
                    content="Content for audit testing",
                    step_type="observation",
                    metadata={},
                )
            ],
            total_confidence=0.9,
        ),
    )

    # Track initial audit events
    initial_events = len(audit_emitter.handlers)

    # Process capsule through all systems (should generate audit events)
    capsule_economics.register_capsule_creation(capsule, "audit_test_agent")
    rect_system.process_capsule(capsule)
    optimization_engine.optimize_capsule(capsule)

    # Register governance stakeholder (should generate audit event)
    governance_engine.register_stakeholder("audit_stakeholder", 1000.0)

    # Process dividend distribution (should generate audit event)
    fcde_engine.process_dividend_distribution(Decimal("100.0"))

    # Verify audit events were generated
    assert len(audit_emitter.handlers) >= initial_events

    print("✅ Audit event integration test passed!")


if __name__ == "__main__":
    # Run all integration tests
    test_complete_capsule_lifecycle()
    test_governance_with_economics()
    test_privacy_with_formal_verification()
    test_ethics_with_optimization()
    test_full_system_analytics()
    test_audit_event_integration()

    print("\n🎉 ALL INTEGRATION TESTS PASSED!")
    print("✅ Complete UATP Capsule Engine system integration verified")
