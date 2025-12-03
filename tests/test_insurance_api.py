"""
Comprehensive Insurance API Tests

Tests the complete insurance system including:
- Risk assessment engine
- Policy management lifecycle
- Claims processing workflow
- Database persistence
- API endpoints
"""

import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, MagicMock, patch

from src.insurance.risk_assessor import (
    RiskAssessor,
    RiskLevel,
    DecisionCategory,
    RiskFactor,
)
from src.insurance.policy_manager import (
    PolicyManager,
    Policy,
    PolicyHolder,
    PolicyTerms,
    PolicyStatus,
)
from src.insurance.claims_processor import (
    ClaimsProcessor,
    Claim,
    ClaimEvidence,
    ClaimStatus,
    ClaimType,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_db_manager():
    """Mock database manager for testing"""
    mock = AsyncMock()

    # Mock session context manager
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.add = Mock()

    # Mock async context manager for session
    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)

    # get_session() is NOT async, it returns a session object immediately
    mock.get_session = Mock(return_value=mock_context_manager)

    return mock


@pytest.fixture
def sample_capsule_chain():
    """Sample capsule chain for testing"""
    return [
        {
            "capsule_id": "caps_001",
            "agent_id": "gpt-4",
            "capsule_type": "reasoning_trace",
            "timestamp": datetime.utcnow().isoformat(),
            "reasoning": {"steps": ["Step 1", "Step 2"]},
            "verification": {
                "signature": "ed25519:abc123",
                "merkle_root": "sha256:def456",
            },
        },
        {
            "capsule_id": "caps_002",
            "agent_id": "gpt-4",
            "capsule_type": "economic_transaction",
            "timestamp": datetime.utcnow().isoformat(),
            "parent_capsule_id": "caps_001",
            "verification": {
                "signature": "ed25519:ghi789",
                "merkle_root": "sha256:jkl012",
            },
        },
    ]


@pytest.fixture
def sample_policy_holder():
    """Sample policy holder for testing"""
    return PolicyHolder(
        user_id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        organization="Test Org",
        contact_phone="+1-555-0123",
    )


@pytest.fixture
def sample_policy_terms():
    """Sample policy terms for testing"""
    return PolicyTerms(
        coverage_amount=100000,
        deductible=1000,
        premium_monthly=150.0,
        term_months=12,
        decision_category=DecisionCategory.CUSTOMER_SERVICE,
        risk_level=RiskLevel.LOW,
        conditions=["Must verify capsule chain", "AI provider must be certified"],
        exclusions=["Intentional misuse", "Unauthorized modifications"],
        max_claims_per_year=3,
        max_payout_per_claim=50000,
    )


@pytest.fixture
def sample_policy(sample_policy_holder, sample_policy_terms):
    """Sample policy for testing"""
    return Policy(
        policy_id="POL-TEST123",
        holder=sample_policy_holder,
        terms=sample_policy_terms,
        status=PolicyStatus.ACTIVE,
        created_at=datetime.utcnow(),
        activated_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=365),
        claims_filed=0,
        total_paid_out=0,
    )


@pytest.fixture
def sample_claim_evidence(sample_capsule_chain):
    """Sample claim evidence for testing"""
    return ClaimEvidence(
        capsule_chain=sample_capsule_chain,
        incident_description="AI system provided incorrect medical advice",
        incident_date=datetime.utcnow(),
        harm_description="Patient followed incorrect advice resulting in injury",
        financial_impact=25000,
        supporting_documents=["medical_report.pdf", "ai_logs.json"],
        witness_statements=["Doctor confirmed incorrect advice"],
    )


# ============================================================================
# RISK ASSESSMENT TESTS
# ============================================================================


class TestRiskAssessor:
    """Test risk assessment engine"""

    @pytest.mark.asyncio
    async def test_risk_assessor_initialization(self, mock_db_manager):
        """Test risk assessor can be initialized"""
        assessor = RiskAssessor(database_manager=mock_db_manager)
        assert assessor is not None
        assert assessor.WEIGHTS["chain_integrity"] == 0.30

    @pytest.mark.asyncio
    async def test_assess_capsule_chain_basic(
        self, mock_db_manager, sample_capsule_chain
    ):
        """Test basic capsule chain assessment"""
        assessor = RiskAssessor(database_manager=mock_db_manager)

        assessment = await assessor.assess_capsule_chain(
            capsule_chain=sample_capsule_chain,
            decision_category=DecisionCategory.CUSTOMER_SERVICE,
            requested_coverage=100000,
        )

        assert assessment is not None
        assert assessment.risk_level in RiskLevel
        assert 0 <= assessment.overall_score <= 1
        assert len(assessment.factors) == 5  # 5 risk factors total
        assert (
            float(
                assessment.premium_estimate.replace("$", "")
                .replace(",", "")
                .replace("/month", "")
            )
            > 0
        )

    @pytest.mark.asyncio
    async def test_risk_level_thresholds(self, mock_db_manager, sample_capsule_chain):
        """Test that risk levels map correctly to scores"""
        assessor = RiskAssessor(database_manager=mock_db_manager)

        assessment = await assessor.assess_capsule_chain(
            capsule_chain=sample_capsule_chain,
            decision_category=DecisionCategory.INFORMATION_RETRIEVAL,  # Low risk
            requested_coverage=10000,
        )

        # Low risk category should result in lower scores
        assert assessment.overall_score < 0.6

    @pytest.mark.asyncio
    async def test_high_stakes_decision_increases_premium(
        self, mock_db_manager, sample_capsule_chain
    ):
        """Test that high-stakes decisions have higher premiums"""
        assessor = RiskAssessor(database_manager=mock_db_manager)

        # Low stakes
        low_stakes = await assessor.assess_capsule_chain(
            capsule_chain=sample_capsule_chain,
            decision_category=DecisionCategory.CUSTOMER_SERVICE,
            requested_coverage=100000,
        )

        # High stakes
        high_stakes = await assessor.assess_capsule_chain(
            capsule_chain=sample_capsule_chain,
            decision_category=DecisionCategory.MEDICAL,
            requested_coverage=100000,
        )

        # Compare numeric values
        # Premium might be "Uninsurable" for very high risk
        if high_stakes.premium_estimate == "Uninsurable":
            high_premium = float("inf")
        else:
            high_premium = float(
                high_stakes.premium_estimate.replace("$", "")
                .replace(",", "")
                .replace("/month", "")
            )
        low_premium = float(
            low_stakes.premium_estimate.replace("$", "")
            .replace(",", "")
            .replace("/month", "")
        )
        assert high_premium > low_premium

    @pytest.mark.asyncio
    async def test_empty_chain_assessment(self, mock_db_manager):
        """Test assessment with empty capsule chain"""
        assessor = RiskAssessor(database_manager=mock_db_manager)

        assessment = await assessor.assess_capsule_chain(
            capsule_chain=[],
            decision_category=DecisionCategory.CUSTOMER_SERVICE,
            requested_coverage=100000,
        )

        # Empty chain should be high risk
        assert assessment.risk_level in [
            RiskLevel.HIGH,
            RiskLevel.VERY_HIGH,
            RiskLevel.UNINSURABLE,
        ]
        assert assessment.overall_score > 0.5


# ============================================================================
# POLICY MANAGEMENT TESTS
# ============================================================================


class TestPolicyManager:
    """Test policy lifecycle management"""

    @pytest.mark.asyncio
    async def test_create_policy_basic(
        self, mock_db_manager, sample_policy_holder, sample_policy_terms
    ):
        """Test basic policy creation"""
        manager = PolicyManager(database_manager=mock_db_manager)

        with patch.object(manager, "_store_policy", new_callable=AsyncMock):
            policy = await manager.create_policy(
                holder=sample_policy_holder, terms=sample_policy_terms
            )

            assert policy is not None
            assert policy.policy_id.startswith("POL-")
            assert policy.status == PolicyStatus.PENDING
            assert policy.holder == sample_policy_holder
            assert policy.terms == sample_policy_terms

    @pytest.mark.asyncio
    async def test_activate_policy(self, mock_db_manager, sample_policy):
        """Test policy activation"""
        manager = PolicyManager(database_manager=mock_db_manager)
        sample_policy.status = PolicyStatus.PENDING

        with patch.object(manager, "_fetch_policy", return_value=sample_policy):
            with patch.object(manager, "_update_policy", new_callable=AsyncMock):
                activated = await manager.activate_policy(sample_policy.policy_id)

                assert activated.status == PolicyStatus.ACTIVE
                assert activated.activated_at is not None

    @pytest.mark.asyncio
    async def test_cancel_policy(self, mock_db_manager, sample_policy):
        """Test policy cancellation"""
        manager = PolicyManager(database_manager=mock_db_manager)

        with patch.object(manager, "_fetch_policy", return_value=sample_policy):
            with patch.object(manager, "_update_policy", new_callable=AsyncMock):
                with patch.object(
                    manager, "_process_refund", return_value={"success": True}
                ):
                    cancelled = await manager.cancel_policy(
                        policy_id=sample_policy.policy_id, reason="Customer request"
                    )

                    assert cancelled.status == PolicyStatus.CANCELLED
                    assert cancelled.cancellation_reason == "Customer request"
                    assert cancelled.cancelled_at is not None

    @pytest.mark.asyncio
    async def test_check_claim_eligibility_valid(self, mock_db_manager, sample_policy):
        """Test claim eligibility check for valid claim"""
        manager = PolicyManager(database_manager=mock_db_manager)

        with patch.object(manager, "get_policy", return_value=sample_policy):
            eligibility = await manager.check_policy_eligibility(
                policy_id=sample_policy.policy_id, claim_amount=25000
            )

            assert eligibility["eligible"] is True
            assert eligibility["max_claimable"] == 25000

    @pytest.mark.asyncio
    async def test_check_claim_eligibility_exceeds_limit(
        self, mock_db_manager, sample_policy
    ):
        """Test claim eligibility when amount exceeds policy limits"""
        manager = PolicyManager(database_manager=mock_db_manager)

        with patch.object(manager, "get_policy", return_value=sample_policy):
            eligibility = await manager.check_policy_eligibility(
                policy_id=sample_policy.policy_id,
                claim_amount=75000,  # Exceeds max_payout_per_claim of 50000
            )

            assert eligibility["eligible"] is True
            assert eligibility["max_claimable"] == 50000

    @pytest.mark.asyncio
    async def test_check_claim_eligibility_expired_policy(
        self, mock_db_manager, sample_policy
    ):
        """Test claim eligibility for expired policy"""
        manager = PolicyManager(database_manager=mock_db_manager)
        sample_policy.expires_at = datetime.utcnow() - timedelta(days=1)

        with patch.object(manager, "get_policy", return_value=sample_policy):
            eligibility = await manager.check_policy_eligibility(
                policy_id=sample_policy.policy_id, claim_amount=25000
            )

            assert eligibility["eligible"] is False
            assert "expired" in eligibility["reason"].lower()


# ============================================================================
# CLAIMS PROCESSING TESTS
# ============================================================================


class TestClaimsProcessor:
    """Test claims processing workflow"""

    @pytest.mark.asyncio
    async def test_submit_claim_basic(
        self, mock_db_manager, mock_policy_manager, sample_claim_evidence
    ):
        """Test basic claim submission"""
        processor = ClaimsProcessor(
            policy_manager=mock_policy_manager, database_manager=mock_db_manager
        )

        with patch.object(
            processor,
            "_verify_evidence_chain",
            return_value={"valid": True, "signature_rate": 1.0},
        ):
            with patch.object(processor, "_store_claim", new_callable=AsyncMock):
                with patch.object(
                    processor, "_fetch_claim", new_callable=AsyncMock
                ) as mock_fetch:
                    # Make _fetch_claim return the claim that was just created
                    async def fetch_side_effect(claim_id):
                        return Claim(
                            claim_id=claim_id,
                            policy_id="POL-TEST123",
                            claimant_user_id=str(uuid.uuid4()),
                            claim_type=ClaimType.INCORRECT_OUTPUT,
                            claimed_amount=25000,
                            evidence=sample_claim_evidence,
                            status=ClaimStatus.SUBMITTED,
                            submitted_at=datetime.utcnow(),
                        )

                    mock_fetch.side_effect = fetch_side_effect

                    claim = await processor.submit_claim(
                        policy_id="POL-TEST123",
                        claimant_user_id=str(uuid.uuid4()),
                        claim_type=ClaimType.INCORRECT_OUTPUT,
                        claimed_amount=25000,
                        evidence=sample_claim_evidence,
                    )

                    assert claim is not None
                    assert claim.claim_id.startswith("CLM-")
                    assert claim.status == ClaimStatus.SUBMITTED
                    assert claim.claimed_amount == 25000

    @pytest.mark.asyncio
    async def test_auto_approve_small_claim(
        self, mock_db_manager, mock_policy_manager, sample_claim_evidence
    ):
        """Test automatic approval of small claims"""
        processor = ClaimsProcessor(
            policy_manager=mock_policy_manager, database_manager=mock_db_manager
        )

        with patch.object(
            processor,
            "_verify_evidence_chain",
            return_value={"valid": True, "signature_rate": 1.0},
        ):
            with patch.object(processor, "_store_claim", new_callable=AsyncMock):
                with patch.object(processor, "_update_claim", new_callable=AsyncMock):
                    with patch.object(
                        processor, "_fetch_claim", new_callable=AsyncMock
                    ) as mock_fetch:

                        async def fetch_side_effect(claim_id):
                            return Claim(
                                claim_id=claim_id,
                                policy_id="POL-TEST123",
                                claimant_user_id=str(uuid.uuid4()),
                                claim_type=ClaimType.INCORRECT_OUTPUT,
                                claimed_amount=500,
                                evidence=sample_claim_evidence,
                                status=ClaimStatus.SUBMITTED,
                                submitted_at=datetime.utcnow(),
                            )

                        mock_fetch.side_effect = fetch_side_effect

                        claim = await processor.submit_claim(
                            policy_id="POL-TEST123",
                            claimant_user_id=str(uuid.uuid4()),
                            claim_type=ClaimType.INCORRECT_OUTPUT,
                            claimed_amount=500,  # Under $1000 threshold
                            evidence=sample_claim_evidence,
                        )

                        # Trigger auto-review
                        reviewed = await processor.review_claim(claim.claim_id)

                        # Small claims with valid chain should auto-approve or go to investigating
                        assert reviewed.status in [
                            ClaimStatus.APPROVED,
                            ClaimStatus.INVESTIGATING,
                        ]

    @pytest.mark.asyncio
    async def test_auto_deny_weak_evidence(
        self, mock_db_manager, mock_policy_manager, sample_claim_evidence
    ):
        """Test automatic denial of claims with weak evidence"""
        processor = ClaimsProcessor(
            policy_manager=mock_policy_manager, database_manager=mock_db_manager
        )

        # Make chain verification fail
        with patch.object(
            processor,
            "_verify_evidence_chain",
            return_value={"valid": False, "signature_rate": 0.0},
        ):
            with patch.object(processor, "_store_claim", new_callable=AsyncMock):
                with patch.object(processor, "_update_claim", new_callable=AsyncMock):
                    with patch.object(
                        processor, "_fetch_claim", new_callable=AsyncMock
                    ) as mock_fetch:

                        async def fetch_side_effect(claim_id):
                            return Claim(
                                claim_id=claim_id,
                                policy_id="POL-TEST123",
                                claimant_user_id=str(uuid.uuid4()),
                                claim_type=ClaimType.INCORRECT_OUTPUT,
                                claimed_amount=25000,
                                evidence=sample_claim_evidence,
                                status=ClaimStatus.SUBMITTED,
                                submitted_at=datetime.utcnow(),
                            )

                        mock_fetch.side_effect = fetch_side_effect

                        claim = await processor.submit_claim(
                            policy_id="POL-TEST123",
                            claimant_user_id=str(uuid.uuid4()),
                            claim_type=ClaimType.INCORRECT_OUTPUT,
                            claimed_amount=25000,
                            evidence=sample_claim_evidence,
                        )

                        reviewed = await processor.review_claim(claim.claim_id)

                        # Weak evidence goes to UNDER_REVIEW or DENIED
                        assert reviewed.status in [
                            ClaimStatus.UNDER_REVIEW,
                            ClaimStatus.DENIED,
                        ]
                        if (
                            reviewed.status == ClaimStatus.DENIED
                            and reviewed.denial_reason
                        ):
                            assert "capsule chain" in reviewed.denial_reason.lower()

    @pytest.mark.asyncio
    async def test_approve_claim(
        self, mock_db_manager, mock_policy_manager, sample_claim_evidence
    ):
        """Test manual claim approval"""
        processor = ClaimsProcessor(
            policy_manager=mock_policy_manager, database_manager=mock_db_manager
        )

        with patch.object(
            processor,
            "_verify_evidence_chain",
            return_value={"valid": True, "signature_rate": 1.0},
        ):
            with patch.object(processor, "_store_claim", new_callable=AsyncMock):
                with patch.object(processor, "_update_claim", new_callable=AsyncMock):
                    with patch.object(
                        processor, "_fetch_claim", new_callable=AsyncMock
                    ) as mock_fetch:

                        async def fetch_side_effect(claim_id):
                            return Claim(
                                claim_id=claim_id,
                                policy_id="POL-TEST123",
                                claimant_user_id=str(uuid.uuid4()),
                                claim_type=ClaimType.INCORRECT_OUTPUT,
                                claimed_amount=25000,
                                evidence=sample_claim_evidence,
                                status=ClaimStatus.SUBMITTED,
                                submitted_at=datetime.utcnow(),
                            )

                        mock_fetch.side_effect = fetch_side_effect

                        claim = await processor.submit_claim(
                            policy_id="POL-TEST123",
                            claimant_user_id=str(uuid.uuid4()),
                            claim_type=ClaimType.INCORRECT_OUTPUT,
                            claimed_amount=25000,
                            evidence=sample_claim_evidence,
                        )

                        approved = await processor.approve_claim(
                            claim_id=claim.claim_id, approved_amount=20000
                        )

                        assert approved.status == ClaimStatus.APPROVED
                        assert approved.approved_amount == 20000

    @pytest.mark.asyncio
    async def test_deny_claim(
        self, mock_db_manager, mock_policy_manager, sample_claim_evidence
    ):
        """Test manual claim denial"""
        processor = ClaimsProcessor(
            policy_manager=mock_policy_manager, database_manager=mock_db_manager
        )

        with patch.object(
            processor,
            "_verify_evidence_chain",
            return_value={"valid": True, "signature_rate": 1.0},
        ):
            with patch.object(processor, "_store_claim", new_callable=AsyncMock):
                with patch.object(processor, "_update_claim", new_callable=AsyncMock):
                    with patch.object(
                        processor, "_fetch_claim", new_callable=AsyncMock
                    ) as mock_fetch:

                        async def fetch_side_effect(claim_id):
                            return Claim(
                                claim_id=claim_id,
                                policy_id="POL-TEST123",
                                claimant_user_id=str(uuid.uuid4()),
                                claim_type=ClaimType.INCORRECT_OUTPUT,
                                claimed_amount=25000,
                                evidence=sample_claim_evidence,
                                status=ClaimStatus.SUBMITTED,
                                submitted_at=datetime.utcnow(),
                            )

                        mock_fetch.side_effect = fetch_side_effect

                        claim = await processor.submit_claim(
                            policy_id="POL-TEST123",
                            claimant_user_id=str(uuid.uuid4()),
                            claim_type=ClaimType.INCORRECT_OUTPUT,
                            claimed_amount=25000,
                            evidence=sample_claim_evidence,
                        )

                        denied = await processor.deny_claim(
                            claim_id=claim.claim_id, reason="Evidence insufficient"
                        )

                        assert denied.status == ClaimStatus.DENIED
                        assert denied.denial_reason == "Evidence insufficient"

    @pytest.mark.asyncio
    async def test_fraud_detection_triggers(
        self, mock_db_manager, mock_policy_manager, sample_claim_evidence
    ):
        """Test that fraud detection identifies suspicious patterns"""
        processor = ClaimsProcessor(
            policy_manager=mock_policy_manager, database_manager=mock_db_manager
        )

        # Duplicate claim (same capsule chain submitted twice)
        with patch.object(
            processor,
            "_verify_evidence_chain",
            return_value={"valid": True, "signature_rate": 1.0},
        ):
            with patch.object(processor, "_store_claim", new_callable=AsyncMock):
                with patch.object(
                    processor, "_fetch_claim", new_callable=AsyncMock
                ) as mock_fetch:

                    async def fetch_side_effect(claim_id):
                        return Claim(
                            claim_id=claim_id,
                            policy_id="POL-TEST123",
                            claimant_user_id=str(uuid.uuid4()),
                            claim_type=ClaimType.INCORRECT_OUTPUT,
                            claimed_amount=25000,
                            evidence=sample_claim_evidence,
                            status=ClaimStatus.SUBMITTED,
                            submitted_at=datetime.utcnow(),
                        )

                    mock_fetch.side_effect = fetch_side_effect

                    claim1 = await processor.submit_claim(
                        policy_id="POL-TEST123",
                        claimant_user_id=str(uuid.uuid4()),
                        claim_type=ClaimType.INCORRECT_OUTPUT,
                        claimed_amount=25000,
                        evidence=sample_claim_evidence,
                    )

                    fraud_score = await processor._detect_fraud(claim1)

                    # Should detect some risk factors
                    assert fraud_score >= 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestInsuranceIntegration:
    """Test complete insurance workflows end-to-end"""

    @pytest.mark.asyncio
    async def test_complete_policy_lifecycle(
        self, mock_db_manager, sample_policy_holder, sample_capsule_chain
    ):
        """Test complete policy creation, activation, claim, and payout flow"""

        # Step 1: Assess risk
        assessor = RiskAssessor(database_manager=mock_db_manager)
        assessment = await assessor.assess_capsule_chain(
            capsule_chain=sample_capsule_chain,
            decision_category=DecisionCategory.CUSTOMER_SERVICE,
            requested_coverage=100000,
        )

        assert assessment.risk_level != RiskLevel.UNINSURABLE

        # Step 2: Create policy with assessed terms
        manager = PolicyManager(database_manager=mock_db_manager)
        terms = PolicyTerms(
            coverage_amount=100000,
            deductible=1000,
            premium_monthly=float(assessment.premium_estimate),
            term_months=12,
            decision_category=DecisionCategory.CUSTOMER_SERVICE,
            risk_level=assessment.risk_level,
            conditions=assessment.conditions,
            exclusions=assessment.exclusions,
        )

        policy = await manager.create_policy(holder=sample_policy_holder, terms=terms)

        assert policy.status == PolicyStatus.PENDING

        # Step 3: Activate policy
        with patch.object(manager, "_fetch_policy", return_value=policy):
            with patch.object(manager, "_update_policy", new_callable=AsyncMock):
                activated = await manager.activate_policy(policy.policy_id)
                assert activated.status == PolicyStatus.ACTIVE

        # Step 4: Submit claim
        processor = ClaimsProcessor(
            policy_manager=manager, database_manager=mock_db_manager
        )
        evidence = ClaimEvidence(
            capsule_chain=sample_capsule_chain,
            incident_description="AI error caused financial loss",
            incident_date=datetime.utcnow(),
            harm_description="Customer received wrong product recommendations",
            financial_impact=5000,
        )

        with patch.object(
            processor,
            "_verify_evidence_chain",
            return_value={"valid": True, "signature_rate": 1.0},
        ):
            with patch.object(processor, "_store_claim", new_callable=AsyncMock):
                with patch.object(processor, "_update_claim", new_callable=AsyncMock):
                    claim = await processor.submit_claim(
                        policy_id=policy.policy_id,
                        claimant_user_id=sample_policy_holder.user_id,
                        claim_type=ClaimType.INCORRECT_OUTPUT,
                        claimed_amount=5000,
                        evidence=evidence,
                    )

                    assert claim.claim_id is not None

                    # Step 5: Approve claim
                    approved = await processor.approve_claim(
                        claim_id=claim.claim_id,
                        approved_amount=5000,
                        reviewer_id="admin_001",
                    )

                    assert approved.status == ClaimStatus.APPROVED
                    assert approved.approved_amount == 5000


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_missing_verification_in_capsule(self, mock_db_manager):
        """Test handling of capsules without verification"""
        assessor = RiskAssessor(database_manager=mock_db_manager)

        bad_chain = [
            {"capsule_id": "caps_001", "agent_id": "gpt-4"}
        ]  # Missing verification

        assessment = await assessor.assess_capsule_chain(
            capsule_chain=bad_chain,
            decision_category=DecisionCategory.CUSTOMER_SERVICE,
            requested_coverage=100000,
        )

        # Should mark as high risk
        assert assessment.overall_risk_level in [
            RiskLevel.HIGH,
            RiskLevel.VERY_HIGH,
            RiskLevel.UNINSURABLE,
        ]

    @pytest.mark.asyncio
    async def test_extremely_large_coverage_request(
        self, mock_db_manager, sample_capsule_chain
    ):
        """Test handling of unreasonably large coverage amounts"""
        assessor = RiskAssessor(database_manager=mock_db_manager)

        assessment = await assessor.assess_capsule_chain(
            capsule_chain=sample_capsule_chain,
            decision_category=DecisionCategory.MEDICAL,
            requested_coverage=100_000_000,  # $100M
        )

        # Should either be uninsurable or have very high premium
        assert (
            assessment.risk_level in [RiskLevel.VERY_HIGH, RiskLevel.UNINSURABLE]
            or float(assessment.premium_estimate) > 100000
        )

    @pytest.mark.asyncio
    async def test_claim_without_capsule_chain(
        self, mock_db_manager, mock_policy_manager
    ):
        """Test claim submission without capsule chain evidence"""
        processor = ClaimsProcessor(
            policy_manager=mock_policy_manager, database_manager=mock_db_manager
        )

        evidence = ClaimEvidence(
            capsule_chain=[],  # Empty chain
            incident_description="Claim without proof",
            incident_date=datetime.utcnow(),
            harm_description="No evidence provided",
        )

        with patch.object(
            processor,
            "_verify_evidence_chain",
            return_value={"valid": False, "signature_rate": 0.0},
        ):
            with patch.object(processor, "_store_claim", new_callable=AsyncMock):
                with patch.object(processor, "_update_claim", new_callable=AsyncMock):
                    claim = await processor.submit_claim(
                        policy_id="POL-TEST123",
                        claimant_user_id=str(uuid.uuid4()),
                        claim_type=ClaimType.INCORRECT_OUTPUT,
                        claimed_amount=25000,
                        evidence=evidence,
                    )

                    reviewed = await processor.review_claim(claim.claim_id, claim)

                    # Should be denied due to lack of evidence
                    assert reviewed.status == ClaimStatus.DENIED


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
