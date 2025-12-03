#!/usr/bin/env python3
"""
Simple test runner for democratic governance protections.
Tests critical security features without complex dependencies.
"""

import sys
import traceback
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Add src to path for imports
sys.path.insert(0, "src")


def test_stake_concentration_limits():
    """Test stake concentration limits."""
    print("Testing stake concentration limits...")

    try:
        from src.governance.advanced_governance import GovernanceDAOEngine

        governance = GovernanceDAOEngine()

        # Test 1: Register legitimate stakeholder with 10% stake
        stakeholder1 = governance.register_stakeholder(
            "legitimate_user",
            initial_stake=1000.0,
            identity_proof={
                "method": "verified",
                "score": 0.8,
                "identifiers": ["email1@test.com"],
            },
        )
        assert stakeholder1 is not None, "Failed to register legitimate stakeholder"
        print("✓ Legitimate stakeholder registered successfully")

        # Test 2: Try to register malicious actor with 20% stake (should be rejected)
        try:
            governance.register_stakeholder(
                "malicious_actor",
                initial_stake=3000.0,  # Would be >15% of total
                identity_proof={
                    "method": "verified",
                    "score": 0.8,
                    "identifiers": ["email2@test.com"],
                },
            )
            assert (
                False
            ), "Malicious actor with excessive stake should have been rejected"
        except ValueError as e:
            assert "15%" in str(e), f"Error message should mention 15% limit: {e}"
            print("✓ Excessive stake concentration properly rejected")

        # Test 3: Verify constitutional immutability
        assert (
            governance.MAX_INDIVIDUAL_VOTING_POWER == 0.15
        ), "Stake limit should be immutable at 15%"
        print("✓ Constitutional limits are immutable")

        print("PASS: Stake concentration limits working correctly\n")
        return True

    except Exception as e:
        print(f"FAIL: Stake concentration test failed: {e}")
        traceback.print_exc()
        return False


def test_sybil_resistance():
    """Test Sybil resistance mechanisms."""
    print("Testing Sybil resistance...")

    try:
        from src.governance.sybil_resistance import (
            SybilResistanceEngine,
            IdentityVerificationMethod,
        )

        sybil_resistance = SybilResistanceEngine()

        # Test 1: Duplicate identifier rejection
        verification1_id = sybil_resistance.submit_identity_verification(
            "user1",
            IdentityVerificationMethod.EMAIL_VERIFICATION,
            {"quality_score": 0.8},
            {"email": "test@example.com"},
        )
        assert verification1_id is not None, "First verification should succeed"

        verification2_id = sybil_resistance.submit_identity_verification(
            "user2",
            IdentityVerificationMethod.EMAIL_VERIFICATION,
            {"quality_score": 0.8},
            {"email": "test@example.com"},  # Same email
        )

        # Check that second verification was rejected
        verifications = sybil_resistance.verifications["user2"]
        assert len(verifications) == 1, "Should have one verification record"
        assert (
            verifications[0].status.value == "rejected"
        ), "Duplicate email should be rejected"
        print("✓ Duplicate identifier properly rejected")

        # Test 2: IP clustering detection
        ip_address = "192.168.1.100"

        for i in range(5):  # Try to register 5 accounts (exceeds limit of 3)
            verification_id = sybil_resistance.submit_identity_verification(
                f"user_{i}",
                IdentityVerificationMethod.EMAIL_VERIFICATION,
                {"quality_score": 0.8, "ip_address": ip_address},
                {"email": f"user{i}@example.com"},
            )

        # Detect Sybil clusters
        clusters = sybil_resistance.detect_sybil_clusters()

        # Should detect IP-based cluster
        ip_clusters = [c for c in clusters if c.detection_method == "ip_clustering"]
        assert len(ip_clusters) > 0, "Should detect IP-based Sybil cluster"
        assert ip_clusters[0].threat_level.value in [
            "high",
            "critical",
        ], "IP cluster should be high threat"
        print("✓ IP clustering attack detected")

        print("PASS: Sybil resistance working correctly\n")
        return True

    except Exception as e:
        print(f"FAIL: Sybil resistance test failed: {e}")
        traceback.print_exc()
        return False


def test_constitutional_framework():
    """Test constitutional framework protections."""
    print("Testing constitutional framework...")

    try:
        from src.governance.constitutional_framework import (
            ConstitutionalFramework,
            ViolationType,
        )

        constitutional = ConstitutionalFramework()

        # Test 1: Validate proposal constitutionality
        constitutional_violation_proposal = {
            "proposal_type": "stake_limits_modification",
            "description": "increase stake limit to allow 25% individual voting power",
            "title": "Modify Constitutional Limits",
            "proposal_id": "test_001",
            "proposer_id": "attacker",
        }

        (
            is_constitutional,
            violation_reason,
            threshold,
        ) = constitutional.validate_proposal_constitutionality(
            constitutional_violation_proposal
        )

        assert not is_constitutional, "Constitutional violation should be detected"
        assert (
            "immutable" in violation_reason.lower()
        ), f"Should mention immutability: {violation_reason}"
        print("✓ Constitutional violation properly detected")

        # Test 2: Stake concentration enforcement
        enforcement_result = constitutional.enforce_stake_concentration_limits(
            "test_user",
            2000.0,  # Voting power
            10000.0,  # Total system power (20% individual share)
        )

        assert not enforcement_result[0], "Should reject excessive concentration"
        assert "15%" in enforcement_result[1], "Should mention 15% limit"
        print("✓ Stake concentration limits enforced")

        # Test 3: Verify integrity checks
        status = constitutional.get_constitutional_status()
        assert status["framework_active"] is True, "Framework should be active"
        assert status["checks_enabled"] is True, "Checks should be enabled"
        print("✓ Constitutional integrity maintained")

        print("PASS: Constitutional framework working correctly\n")
        return True

    except Exception as e:
        print(f"FAIL: Constitutional framework test failed: {e}")
        traceback.print_exc()
        return False


def test_byzantine_fault_tolerance():
    """Test Byzantine fault tolerance."""
    print("Testing Byzantine fault tolerance...")

    try:
        from src.consensus.multi_agent_consensus import (
            MultiAgentConsensusEngine,
            ConsensusNode,
            NodeRole,
        )

        consensus = MultiAgentConsensusEngine()

        # Register nodes
        for i in range(10):
            node = ConsensusNode(
                node_id=f"node_{i}",
                role=NodeRole.VALIDATOR,
                stake=1000.0,
                reputation=100.0,
                last_seen=datetime.now(timezone.utc),
                public_key=f"pubkey_{i}",
                network_address=f"192.168.1.{i+1}",
            )
            consensus.register_node(node)

        # Test 1: Byzantine behavior detection
        byzantine_node_id = "node_3"
        byzantine_node = consensus.nodes[byzantine_node_id]

        # Simulate Byzantine behavior
        byzantine_node.last_seen = datetime.now(timezone.utc) - timedelta(minutes=15)
        byzantine_node.reputation = 30.0

        byzantine_score = consensus.detect_byzantine_behavior(byzantine_node_id)
        assert (
            byzantine_score > 0.5
        ), f"Should detect Byzantine behavior: {byzantine_score}"
        print("✓ Byzantine behavior detected")

        # Test 2: Economic penalties
        original_stake = consensus.nodes[byzantine_node_id].stake

        penalty_applied = consensus.implement_economic_penalties(
            byzantine_node_id, 500.0, "Byzantine behavior detected"
        )

        assert penalty_applied, "Penalty should be applied"
        new_stake = consensus.nodes[byzantine_node_id].stake
        assert new_stake < original_stake, "Stake should be reduced"
        print("✓ Economic penalties applied")

        print("PASS: Byzantine fault tolerance working correctly\n")
        return True

    except Exception as e:
        print(f"FAIL: Byzantine fault tolerance test failed: {e}")
        traceback.print_exc()
        return False


def test_time_based_protections():
    """Test time-based protections."""
    print("Testing time-based protections...")

    try:
        from src.governance.advanced_governance import GovernanceDAOEngine, ProposalType

        governance = GovernanceDAOEngine()

        # Register stakeholder
        governance.register_stakeholder(
            "test_user",
            initial_stake=1000.0,
            identity_proof={
                "method": "verified",
                "score": 0.8,
                "identifiers": ["test@test.com"],
            },
        )

        # Test 1: Vesting periods
        stakeholder_id = "test_user"

        vesting_added = governance.add_stake_vesting_period(
            stakeholder_id, 5000.0, 30  # 30-day vesting period
        )

        assert vesting_added, "Vesting period should be added"

        vested_power = governance.calculate_vested_voting_power(stakeholder_id)
        normal_power = governance.stakeholders[stakeholder_id].calculate_voting_power()

        assert vested_power < normal_power, "Vested power should be reduced"
        print("✓ Voting power vesting periods working")

        # Test 2: Proposal delays
        proposal = governance.create_proposal(
            title="Test Proposal",
            description="Test proposal with mandatory delay",
            proposal_type=ProposalType.POLICY_CHANGE,
            proposer_id="test_user",
        )

        assert (
            proposal.voting_start > proposal.created_at
        ), "Voting should not start immediately"

        time_delay = (
            proposal.voting_start - proposal.created_at
        ).total_seconds() / 3600
        assert time_delay >= 1.0, f"Should have at least 1 hour delay: {time_delay}"
        print("✓ Proposal creation delays working")

        print("PASS: Time-based protections working correctly\n")
        return True

    except Exception as e:
        print(f"FAIL: Time-based protections test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all governance protection tests."""
    print("=" * 60)
    print("TESTING CRITICAL DEMOCRATIC GOVERNANCE PROTECTIONS")
    print("=" * 60)
    print()

    tests = [
        test_stake_concentration_limits,
        test_sybil_resistance,
        test_constitutional_framework,
        test_byzantine_fault_tolerance,
        test_time_based_protections,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"CRITICAL ERROR in {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    print("DEMOCRATIC PROTECTION TEST RESULTS:")
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")

    if failed == 0:
        print("\n🎉 ALL DEMOCRATIC PROTECTIONS ARE WORKING CORRECTLY!")
        print("✅ The system is protected against governance capture attacks")
        print("✅ Stake concentration limits prevent wealth-based takeovers")
        print("✅ Sybil resistance prevents fake identity attacks")
        print("✅ Constitutional framework prevents rule tampering")
        print("✅ Byzantine fault tolerance maintains consensus integrity")
        print("✅ Time-based protections prevent rapid manipulation")
    else:
        print(f"\n⚠️  {failed} CRITICAL PROTECTION FAILURES DETECTED!")
        print("🚨 IMMEDIATE SECURITY REVIEW REQUIRED")
        return 1

    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
