"""
Tests for the advanced governance system.
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.crypto.post_quantum import pq_crypto
from src.governance.advanced_governance import (
    GovernanceDAOEngine,
    ProposalStatus,
    ProposalType,
    VoteType,
    VotingMethod,
)
from src.security.sybil_detection import TestSybilDetector


def test_stakeholder_registration():
    """Test stakeholder registration."""

    engine = GovernanceDAOEngine(sybil_detector=TestSybilDetector())

    # Register stakeholder
    stakeholder = engine.register_stakeholder("test_stakeholder_001", 1000.0)

    assert stakeholder.stakeholder_id == "test_stakeholder_001"
    assert stakeholder.stake_amount == 1000.0
    assert stakeholder.reputation_score == 100.0
    assert "test_stakeholder_001" in engine.stakeholders


def test_proposal_creation():
    """Test proposal creation."""

    engine = GovernanceDAOEngine(sybil_detector=TestSybilDetector())

    # Register proposer
    engine.register_stakeholder("proposer_001", 5000.0)

    # Create proposal
    proposal = engine.create_proposal(
        title="Test Proposal",
        description="A test proposal for governance",
        proposal_type=ProposalType.POLICY_CHANGE,
        proposer_id="proposer_001",
        voting_duration=timedelta(days=3),
    )

    assert proposal.title == "Test Proposal"
    assert proposal.proposal_type == ProposalType.POLICY_CHANGE
    assert proposal.proposer_id == "proposer_001"
    assert proposal.status == ProposalStatus.SUBMITTED
    assert proposal.proposal_id in engine.proposals


def test_voting_process():
    """Test the voting process."""

    engine = GovernanceDAOEngine(sybil_detector=TestSybilDetector())

    # Register stakeholders
    engine.register_stakeholder("voter_001", 2000.0)
    engine.register_stakeholder("voter_002", 3000.0)

    # Create proposal
    proposal = engine.create_proposal(
        title="Voting Test Proposal",
        description="Test proposal for voting",
        proposal_type=ProposalType.PARAMETER_UPDATE,
        proposer_id="voter_001",
        voting_duration=timedelta(hours=1),
    )

    # Generate keypairs for voting
    pq_keypair = pq_crypto.generate_dilithium_keypair()
    private_key_1, public_key_1 = pq_keypair.private_key, pq_keypair.public_key
    pq_keypair = pq_crypto.generate_dilithium_keypair()
    private_key_2, public_key_2 = pq_keypair.private_key, pq_keypair.public_key

    # Set voting period to active (simulate time passing)
    proposal.voting_start = datetime.now(timezone.utc) - timedelta(minutes=5)
    proposal.status = ProposalStatus.VOTING

    # Cast votes
    vote_1 = engine.cast_vote(
        proposal_id=proposal.proposal_id,
        voter_id="voter_001",
        vote_type=VoteType.FOR,
        private_key=private_key_1.private_key.hex(),
    )

    vote_2 = engine.cast_vote(
        proposal_id=proposal.proposal_id,
        voter_id="voter_002",
        vote_type=VoteType.AGAINST,
        private_key=private_key_2.private_key.hex(),
    )

    assert vote_1.vote_type == VoteType.FOR
    assert vote_2.vote_type == VoteType.AGAINST
    assert len(proposal.votes) == 2

    # Check vote tally
    tally = proposal.get_vote_tally()
    assert tally[VoteType.FOR] > 0
    assert tally[VoteType.AGAINST] > 0


def test_proposal_finalization():
    """Test proposal finalization."""

    engine = GovernanceDAOEngine(sybil_detector=TestSybilDetector())

    # Register stakeholders
    engine.register_stakeholder("final_voter_001", 3000.0)
    engine.register_stakeholder("final_voter_002", 2000.0)

    # Create proposal
    proposal = engine.create_proposal(
        title="Finalization Test",
        description="Test proposal finalization",
        proposal_type=ProposalType.POLICY_CHANGE,
        proposer_id="final_voter_001",
        voting_duration=timedelta(seconds=1),  # Very short duration
    )

    # Set up voting period
    proposal.voting_start = datetime.now(timezone.utc) - timedelta(minutes=5)
    proposal.voting_end = datetime.now(timezone.utc) - timedelta(
        seconds=1
    )  # Already ended
    proposal.status = ProposalStatus.VOTING

    # Cast majority vote
    pq_keypair = pq_crypto.generate_dilithium_keypair()
    private_key, _ = pq_keypair.private_key, pq_keypair.public_key
    engine.cast_vote(
        proposal_id=proposal.proposal_id,
        voter_id="final_voter_001",
        vote_type=VoteType.FOR,
        private_key=private_key.private_key.hex(),
    )

    # Finalize proposal
    result = engine.finalize_proposal(proposal.proposal_id)

    assert result is True
    assert proposal.status == ProposalStatus.PASSED


def test_delegation():
    """Test voting power delegation."""

    engine = GovernanceDAOEngine(sybil_detector=TestSybilDetector())

    # Register stakeholders
    engine.register_stakeholder("delegator_001", 1000.0)
    engine.register_stakeholder("delegate_001", 2000.0)

    # Delegate voting power
    result = engine.delegate_voting_power("delegator_001", "delegate_001")

    assert result is True
    assert engine.stakeholders["delegator_001"].delegated_to == "delegate_001"

    # Test revocation
    revoke_result = engine.revoke_delegation("delegator_001")
    assert revoke_result is True
    assert engine.stakeholders["delegator_001"].delegated_to is None


def test_circular_delegation_prevention():
    """Test prevention of circular delegation."""

    engine = GovernanceDAOEngine(sybil_detector=TestSybilDetector())

    # Register stakeholders
    engine.register_stakeholder("circular_001", 1000.0)
    engine.register_stakeholder("circular_002", 1000.0)
    engine.register_stakeholder("circular_003", 1000.0)

    # Create delegation chain
    engine.delegate_voting_power("circular_001", "circular_002")
    engine.delegate_voting_power("circular_002", "circular_003")

    # Attempt to create circular delegation
    with pytest.raises(ValueError, match="Circular delegation detected"):
        engine.delegate_voting_power("circular_003", "circular_001")


def test_proposal_status_tracking():
    """Test proposal status tracking."""

    engine = GovernanceDAOEngine(sybil_detector=TestSybilDetector())

    # Register stakeholder
    engine.register_stakeholder("status_voter_001", 1000.0)

    # Create proposal
    proposal = engine.create_proposal(
        title="Status Test",
        description="Test status tracking",
        proposal_type=ProposalType.SYSTEM_UPGRADE,
        proposer_id="status_voter_001",
    )

    # Get proposal status
    status = engine.get_proposal_status(proposal.proposal_id)

    assert status["proposal_id"] == proposal.proposal_id
    assert status["title"] == "Status Test"
    assert status["status"] == ProposalStatus.SUBMITTED.value
    assert status["proposal_type"] == ProposalType.SYSTEM_UPGRADE.value
    assert "vote_tally" in status
    assert "participation_rate" in status


def test_governance_analytics():
    """Test governance analytics."""

    engine = GovernanceDAOEngine(sybil_detector=TestSybilDetector())

    # Register stakeholders
    engine.register_stakeholder("analytics_001", 1000.0)
    engine.register_stakeholder("analytics_002", 2000.0)

    # Create proposals
    engine.create_proposal(
        title="Analytics Test 1",
        description="First test proposal",
        proposal_type=ProposalType.POLICY_CHANGE,
        proposer_id="analytics_001",
    )

    engine.create_proposal(
        title="Analytics Test 2",
        description="Second test proposal",
        proposal_type=ProposalType.PARAMETER_UPDATE,
        proposer_id="analytics_002",
    )

    # Get analytics
    analytics = engine.get_governance_analytics()

    assert "governance_stats" in analytics
    assert "total_stakeholders" in analytics
    assert "proposal_type_distribution" in analytics
    assert "participation_stats" in analytics
    assert analytics["total_stakeholders"] == 2
    assert analytics["governance_stats"]["total_proposals"] == 2


def test_emergency_proposal():
    """Test emergency proposal handling."""

    engine = GovernanceDAOEngine(sybil_detector=TestSybilDetector())

    # Register stakeholder
    engine.register_stakeholder("emergency_001", 5000.0)

    # Create emergency proposal
    proposal = engine.create_proposal(
        title="Emergency Action",
        description="Emergency proposal test",
        proposal_type=ProposalType.EMERGENCY_ACTION,
        proposer_id="emergency_001",
    )

    # Emergency proposals should have shorter voting duration and higher threshold
    assert proposal.voting_method == VotingMethod.SUPERMAJORITY
    assert proposal.required_threshold == 0.75

    # Voting period should be shorter
    voting_duration = proposal.voting_end - proposal.voting_start
    assert voting_duration <= timedelta(hours=25)  # Should be around 24 hours


def test_voting_power_calculation():
    """Test voting power calculation."""

    engine = GovernanceDAOEngine(sybil_detector=TestSybilDetector())

    # Register stakeholder
    stakeholder = engine.register_stakeholder("power_test_001", 1000.0)

    # Test initial voting power
    initial_power = stakeholder.calculate_voting_power()
    assert initial_power > 0

    # Modify reputation and participation
    stakeholder.reputation_score = 150.0
    stakeholder.participation_rate = 0.8

    # Recalculate voting power
    new_power = stakeholder.calculate_voting_power()
    assert (
        new_power > initial_power
    )  # Should increase with better reputation and participation


def test_proposal_execution():
    """Test proposal execution."""

    engine = GovernanceDAOEngine(sybil_detector=TestSybilDetector())

    # Register stakeholder
    engine.register_stakeholder("executor_001", 1000.0)

    # Create proposal with execution data
    proposal = engine.create_proposal(
        title="Parameter Update Test",
        description="Test parameter update execution",
        proposal_type=ProposalType.PARAMETER_UPDATE,
        proposer_id="executor_001",
        execution_data={"parameter_name": "min_stake_to_propose", "new_value": 2000.0},
    )

    # Simulate passing the proposal
    proposal.status = ProposalStatus.PASSED

    # Execute proposal
    old_value = engine.governance_parameters["min_stake_to_propose"]
    engine._execute_proposal(proposal)

    # Check that parameter was updated
    assert engine.governance_parameters["min_stake_to_propose"] == 2000.0
    assert proposal.status == ProposalStatus.EXECUTED
    assert proposal.proposal_id in engine.executed_actions


if __name__ == "__main__":
    test_stakeholder_registration()
    test_proposal_creation()
    test_voting_process()
    test_proposal_finalization()
    test_delegation()
    test_circular_delegation_prevention()
    test_proposal_status_tracking()
    test_governance_analytics()
    test_emergency_proposal()
    test_voting_power_calculation()
    test_proposal_execution()
    print("✅ All governance tests passed!")
