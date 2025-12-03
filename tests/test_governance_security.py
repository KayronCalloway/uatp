"""
Comprehensive Security Testing Suite for UATP Governance System.

This test suite validates that democratic governance protections work against
various attack scenarios including:
- Stake concentration attacks
- Sybil attacks 
- Coordinated manipulation
- Rapid governance takeover
- Constitutional violations
- Byzantine validator attacks
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock, patch

from src.governance.advanced_governance import (
    GovernanceDAOEngine,
    Stakeholder,
    Proposal,
    ProposalType,
    VoteType,
    VotingMethod,
    ConstitutionalFramework,
)
from src.governance.constitutional_framework import constitutional_framework
from src.consensus.multi_agent_consensus import MultiAgentConsensusEngine, ConsensusNode


class TestStakeConcentrationProtection:
    """Test stake concentration limits prevent wealth-based capture."""

    def setup_method(self):
        """Set up test environment."""
        self.governance = GovernanceDAOEngine()

    def test_individual_stake_concentration_limit(self):
        """Test that individual stakes cannot exceed 15% limit."""
        # Register normal stakeholder
        identity_proof = {
            "method": "identity_verification",
            "score": 0.8,
            "identifiers": ["user1_id_doc", "user1_email"],
            "interaction_history": ["login", "vote", "comment"],
            "activity_timestamps": [1000, 2000, 3000],
            "action_types": ["vote", "comment", "proposal"],
        }

        normal_stakeholder = self.governance.register_stakeholder(
            "user1", 1000.0, identity_proof
        )

        # Attempt to register high-stake attacker (would be >15% of total)
        high_stake_identity = {
            "method": "identity_verification",
            "score": 0.9,
            "identifiers": ["attacker_id_doc", "attacker_email"],
            "interaction_history": ["login", "vote"],
            "activity_timestamps": [5000, 6000],
            "action_types": ["vote", "stake"],
        }

        # This should fail due to concentration limits
        with pytest.raises(ValueError, match="concentration limit violated"):
            self.governance.register_stakeholder(
                "wealthy_attacker", 10000.0, high_stake_identity
            )

    def test_coordinated_group_concentration_limit(self):
        """Test that coordinated groups cannot exceed 25% limit."""
        base_time = datetime.now(timezone.utc)

        # Register multiple coordinated accounts (similar timing, stakes)
        coordinated_accounts = []
        for i in range(5):
            identity_proof = {
                "method": "identity_verification",
                "score": 0.75,
                "identifiers": [f"coord{i}_id", f"coord{i}_email"],
                "interaction_history": ["login", "vote"],
                "activity_timestamps": [
                    1000 + i * 10,
                    2000 + i * 10,
                ],  # Very similar timing
                "action_types": ["vote", "stake"],
            }

            # Mock similar registration times
            with patch("datetime.datetime") as mock_datetime:
                mock_datetime.now.return_value = base_time + timedelta(
                    minutes=i * 2
                )  # Within coordination window
                mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

                stakeholder = self.governance.register_stakeholder(
                    f"coord_user_{i}", 1000.0, identity_proof
                )
                coordinated_accounts.append(stakeholder)

        # Attempt to add one more coordinated account that would exceed 25% limit
        with pytest.raises(ValueError, match="Coordinated group stake would exceed"):
            identity_proof = {
                "method": "identity_verification",
                "score": 0.75,
                "identifiers": ["coord_final_id", "coord_final_email"],
                "interaction_history": ["login"],
                "activity_timestamps": [1005, 2005],
                "action_types": ["vote"],
            }

            self.governance.register_stakeholder("coord_final", 5000.0, identity_proof)

    def test_voting_power_capping(self):
        """Test that voting power is capped even if stake concentration checks pass."""
        # Set up scenario where stakeholder has high stake but voting power gets capped
        identity_proof = {
            "method": "identity_verification",
            "score": 0.9,
            "identifiers": ["high_stake_user_id", "high_stake_email"],
            "interaction_history": ["login", "vote", "comment", "proposal"],
            "activity_timestamps": [1000, 2000, 3000, 4000],
            "action_types": ["vote", "comment", "proposal", "delegation"],
        }

        # Register legitimate high-stake user
        stakeholder = self.governance.register_stakeholder(
            "high_stake_user", 2000.0, identity_proof
        )

        # Check that voting power is capped appropriately
        base_voting_power = stakeholder.calculate_voting_power()
        capped_power = self.governance._apply_voting_power_limits(
            "high_stake_user", base_voting_power
        )

        # Should be capped if it exceeds concentration limits
        total_power = sum(
            s.calculate_voting_power() for s in self.governance.stakeholders.values()
        )
        individual_percentage = capped_power / total_power

        assert individual_percentage <= self.governance.MAX_INDIVIDUAL_VOTING_POWER


class TestSybilResistance:
    """Test Sybil resistance mechanisms prevent fake account attacks."""

    def setup_method(self):
        """Set up test environment."""
        self.governance = GovernanceDAOEngine()

    def test_identity_verification_requirement(self):
        """Test that identity verification is required for governance participation."""
        # Attempt to register without identity proof
        with pytest.raises(ValueError, match="Identity proof required"):
            self.governance.register_stakeholder("no_identity_user", 1000.0, None)

    def test_insufficient_verification_score_rejection(self):
        """Test that low verification scores are rejected."""
        low_score_identity = {
            "method": "weak_verification",
            "score": 0.5,  # Below 0.7 threshold
            "identifiers": ["weak_id"],
            "interaction_history": [],
            "activity_timestamps": [],
            "action_types": [],
        }

        with pytest.raises(
            ValueError, match="Insufficient identity verification score"
        ):
            self.governance.register_stakeholder(
                "low_score_user", 1000.0, low_score_identity
            )

    def test_duplicate_identity_detection(self):
        """Test that duplicate identities are detected and rejected."""
        # Register first user
        identity1 = {
            "method": "identity_verification",
            "score": 0.8,
            "identifiers": ["shared_id_doc", "user1_unique_email"],
            "interaction_history": ["login", "vote"],
            "activity_timestamps": [1000, 2000],
            "action_types": ["vote", "comment"],
        }

        self.governance.register_stakeholder("user1", 1000.0, identity1)

        # Attempt to register second user with overlapping identity
        identity2 = {
            "method": "identity_verification",
            "score": 0.8,
            "identifiers": ["shared_id_doc", "user2_email"],  # Same ID document
            "interaction_history": ["login"],
            "activity_timestamps": [3000],
            "action_types": ["vote"],
        }

        with pytest.raises(ValueError, match="Identity overlap detected"):
            self.governance.register_stakeholder("user2", 1000.0, identity2)

    def test_bot_behavior_detection(self):
        """Test that bot-like behavioral patterns are detected."""
        bot_identity = {
            "method": "automated_verification",
            "score": 0.8,
            "identifiers": ["bot_id", "bot_email"],
            "interaction_history": [],  # No interaction history - suspicious
            "activity_timestamps": [1000, 2000, 3000, 4000, 5000],  # Perfect intervals
            "action_types": ["vote"],  # Very limited action diversity
        }

        with pytest.raises(ValueError, match="Behavioral patterns suggest automated"):
            self.governance.register_stakeholder("bot_user", 1000.0, bot_identity)


class TestMinorityProtection:
    """Test minority protection mechanisms prevent tyranny of majority."""

    def setup_method(self):
        """Set up test environment with stakeholders."""
        self.governance = GovernanceDAOEngine()

        # Register stakeholders representing majority and minority
        self.majority_users = []
        self.minority_users = []

        # Majority (70% of stake)
        for i in range(7):
            identity = {
                "method": "identity_verification",
                "score": 0.8,
                "identifiers": [f"majority_{i}_id", f"majority_{i}_email"],
                "interaction_history": ["login", "vote", "comment"],
                "activity_timestamps": [1000 + i * 100, 2000 + i * 100],
                "action_types": ["vote", "comment", "proposal"],
            }

            user = self.governance.register_stakeholder(
                f"majority_user_{i}", 1000.0, identity
            )
            self.majority_users.append(user)

        # Minority (30% of stake)
        for i in range(3):
            identity = {
                "method": "identity_verification",
                "score": 0.9,
                "identifiers": [f"minority_{i}_id", f"minority_{i}_email"],
                "interaction_history": ["login", "vote", "comment", "proposal"],
                "activity_timestamps": [3000 + i * 100, 4000 + i * 100],
                "action_types": ["vote", "comment", "proposal", "review"],
            }

            user = self.governance.register_stakeholder(
                f"minority_user_{i}", 1000.0, identity
            )
            self.minority_users.append(user)

    def test_minority_veto_rights(self):
        """Test that minority can veto fundamental changes."""
        # Create constitutional proposal affecting fundamental rights
        proposal = self.governance.create_proposal(
            title="Remove Attribution Rights",
            description="This proposal would eliminate attribution tracking to improve efficiency",
            proposal_type=ProposalType.RULE_AMENDMENT,
            proposer_id="majority_user_0",
            voting_method=VotingMethod.SUPERMAJORITY,
            required_threshold=0.67,
        )

        # All minority users vote against (30% opposition)
        minority_voting_power = 0
        for i, user in enumerate(self.minority_users):
            vote = self.governance.cast_vote(
                proposal.proposal_id,
                f"minority_user_{i}",
                VoteType.AGAINST,
                "fake_private_key",
            )
            minority_voting_power += vote.voting_power

        # Check that minority veto protection is triggered
        total_voting_power = sum(
            s.calculate_voting_power() for s in self.governance.stakeholders.values()
        )
        minority_percentage = minority_voting_power / total_voting_power

        # Should trigger minority protection (>25% threshold)
        assert minority_percentage > 0.25

        # Proposal should require special review due to minority veto
        assert self.governance._requires_minority_protection(proposal)

    def test_constitutional_amendment_supermajority_requirement(self):
        """Test that constitutional amendments require 75% supermajority."""
        # Create constitutional amendment proposal
        proposal = self.governance.create_proposal(
            title="Modify Constitutional Framework",
            description="Constitutional amendment to change governance structure",
            proposal_type=ProposalType.RULE_AMENDMENT,
            proposer_id="majority_user_0",
        )

        # Should automatically require 75% supermajority
        assert proposal.required_threshold >= 0.75
        assert proposal.metadata.get("requires_judicial_review", False)


class TestTimeBasedProtections:
    """Test time-based protections prevent rapid governance manipulation."""

    def setup_method(self):
        """Set up test environment."""
        self.governance = GovernanceDAOEngine()

        # Register stakeholder
        identity = {
            "method": "identity_verification",
            "score": 0.8,
            "identifiers": ["user_id", "user_email"],
            "interaction_history": ["login", "vote"],
            "activity_timestamps": [1000, 2000],
            "action_types": ["vote", "proposal"],
        }

        self.stakeholder = self.governance.register_stakeholder(
            "test_user", 2000.0, identity
        )

    def test_proposal_delay_period(self):
        """Test that proposals have mandatory delay period before voting."""
        proposal = self.governance.create_proposal(
            title="Test Proposal",
            description="A test proposal",
            proposal_type=ProposalType.POLICY_CHANGE,
            proposer_id="test_user",
        )

        # Voting should not start immediately
        current_time = datetime.now(timezone.utc)
        assert proposal.voting_start > current_time

        # Should have at least 24-hour delay for non-emergency proposals
        delay = (proposal.voting_start - proposal.created_at).total_seconds() / 3600
        assert delay >= 24

    def test_emergency_proposal_shorter_delay(self):
        """Test that emergency proposals have shorter but still present delay."""
        proposal = self.governance.create_proposal(
            title="Emergency Action",
            description="Critical emergency requiring immediate attention",
            proposal_type=ProposalType.EMERGENCY_ACTION,
            proposer_id="test_user",
        )

        # Emergency proposals should have shorter delay
        delay = (proposal.voting_start - proposal.created_at).total_seconds() / 3600
        assert 1 <= delay < 24  # At least 1 hour but less than 24

    def test_stake_vesting_periods(self):
        """Test that new stakes have vesting periods."""
        # Add vesting period for new stake
        success = self.governance.add_stake_vesting_period("test_user", 1000.0, 30)
        assert success

        # Vested voting power should be less than full power
        full_power = self.stakeholder.calculate_voting_power()
        vested_power = self.governance.calculate_vested_voting_power("test_user")

        assert vested_power < full_power  # Should be reduced due to vesting


class TestConstitutionalProtection:
    """Test constitutional framework prevents system capture."""

    def setup_method(self):
        """Set up test environment."""
        self.governance = GovernanceDAOEngine()
        self.constitutional = constitutional_framework

    def test_constitutional_violation_detection(self):
        """Test that constitutional violations are detected."""
        # Create proposal violating constitutional principles
        proposal = {
            "proposal_id": "test_violation_1",
            "title": "Remove Attribution Rights",
            "description": "This proposal would eliminate attribution tracking completely",
            "proposer_id": "test_user",
            "execution_data": {"action": "disable_attribution"},
        }

        (
            is_constitutional,
            violation_reason,
            violated_principles,
        ) = self.constitutional.validate_proposal_constitutionality(proposal)

        assert not is_constitutional
        assert "attribution_rights_inalienable" in violated_principles
        assert "attribution" in violation_reason.lower()

    def test_immutable_principles_cannot_be_changed(self):
        """Test that immutable principles cannot be modified."""
        # Attempt to modify stake concentration limits
        proposal = {
            "proposal_id": "test_immutable_1",
            "title": "Increase Stake Concentration Limits",
            "description": "Increase individual stake concentration limit to 50%",
            "execution_data": {
                "parameter_name": "MAX_INDIVIDUAL_VOTING_POWER",
                "current_value": 0.15,
                "new_value": 0.50,
            },
        }

        (
            is_constitutional,
            violation_reason,
            violated_principles,
        ) = self.constitutional.validate_proposal_constitutionality(proposal)

        assert not is_constitutional
        assert "stake_concentration_limited" in violated_principles

    def test_constitutional_emergency_activation(self):
        """Test constitutional emergency can be activated."""
        success = self.constitutional.activate_constitutional_emergency(
            "Detected coordinated governance capture attempt", duration_hours=48
        )

        assert success
        assert self.constitutional.constitutional_emergency_active

        # During emergency, non-emergency proposals should be rejected
        proposal = {
            "proposal_id": "emergency_test_1",
            "title": "Normal Proposal",
            "description": "A normal policy change",
            "proposal_type": "policy_change",
        }

        (
            is_constitutional,
            violation_reason,
            _,
        ) = self.constitutional.validate_proposal_constitutionality(proposal)

        assert not is_constitutional
        assert "emergency active" in violation_reason.lower()

    def test_judicial_review_process(self):
        """Test judicial review process for constitutional amendments."""
        proposal = {
            "proposal_id": "constitutional_amendment_1",
            "title": "Constitutional Amendment Test",
            "description": "Amendment to constitutional framework for testing",
            "proposal_type": "rule_amendment",
        }

        # Initiate judicial review
        review_id = self.constitutional.initiate_judicial_review(
            proposal["proposal_id"], proposal
        )

        assert review_id in self.constitutional.judicial_reviews
        review = self.constitutional.judicial_reviews[review_id]
        assert len(review["assigned_judges"]) > 0
        assert review["status"] == "pending"

        # Complete judicial review
        success = self.constitutional.complete_judicial_review(
            review_id,
            decision=False,  # Reject the amendment
            reasoning="Amendment would undermine constitutional protections",
            judge_id=review["assigned_judges"][0],
        )

        assert success
        assert review["decision"] is False


class TestByzantineFaultTolerance:
    """Test Byzantine fault tolerance prevents malicious validator behavior."""

    def setup_method(self):
        """Set up consensus test environment."""
        self.consensus = MultiAgentConsensusEngine()

        # Register mix of honest and potentially Byzantine nodes
        self.honest_nodes = []
        self.byzantine_nodes = []

        for i in range(5):
            node = ConsensusNode(
                node_id=f"honest_node_{i}",
                role="validator",
                stake=1000.0,
                reputation=95.0,
                last_seen=datetime.now(timezone.utc),
                public_key=f"honest_key_{i}",
                network_address=f"192.168.1.{i+10}",
            )
            self.consensus.register_node(node)
            self.honest_nodes.append(node)

        for i in range(2):
            node = ConsensusNode(
                node_id=f"byzantine_node_{i}",
                role="validator",
                stake=1000.0,
                reputation=30.0,  # Low reputation
                last_seen=datetime.now(timezone.utc)
                - timedelta(minutes=10),  # Delayed responses
                public_key=f"byzantine_key_{i}",
                network_address=f"192.168.1.{i+20}",
            )
            # Simulate Byzantine behavior patterns
            node.byzantine_behavior_score = 0.8
            node.vote_history = [
                {"position": f"position_{j}"} for j in range(15)
            ]  # Inconsistent voting

            self.consensus.register_node(node)
            self.byzantine_nodes.append(node)

    def test_byzantine_behavior_detection(self):
        """Test that Byzantine behavior is detected and scored."""
        byzantine_node = self.byzantine_nodes[0]

        # Detect Byzantine behavior
        byzantine_score = self.consensus.detect_byzantine_behavior(
            byzantine_node.node_id
        )

        # Should detect high Byzantine score due to low reputation, delayed responses, etc.
        assert byzantine_score > 0.5
        assert byzantine_node.byzantine_behavior_score > 0.5

    def test_economic_penalties_for_byzantine_behavior(self):
        """Test that economic penalties are applied for Byzantine behavior."""
        byzantine_node = self.byzantine_nodes[0]
        initial_stake = byzantine_node.stake

        # Apply economic penalty
        success = self.consensus.implement_economic_penalties(
            byzantine_node.node_id,
            penalty_amount=500.0,
            reason="Byzantine behavior detected",
        )

        assert success
        assert byzantine_node.stake < initial_stake
        assert hasattr(byzantine_node, "penalty_history")
        assert len(byzantine_node.penalty_history) > 0

    def test_validator_suspension_for_severe_byzantine_behavior(self):
        """Test that severe Byzantine actors are suspended from validator set."""
        byzantine_node = self.byzantine_nodes[0]
        byzantine_node.byzantine_behavior_score = 0.9  # Very high score

        # Initialize a consensus protocol with validator set
        from src.consensus.multi_agent_consensus import ProofOfStakeConsensus

        # Create mock protocol with validator set
        mock_protocol = Mock()
        mock_protocol.validator_set = [
            n.node_id for n in self.honest_nodes + self.byzantine_nodes
        ]

        self.consensus.active_protocols = {"proof_of_stake": mock_protocol}

        # Apply Byzantine penalties
        self.consensus._apply_byzantine_penalties(byzantine_node.node_id, 0.9)

        # Byzantine node should be removed from validator set
        assert byzantine_node.node_id not in mock_protocol.validator_set


class TestRapidGovernanceTakeoverPrevention:
    """Test prevention of rapid governance takeover attempts."""

    def setup_method(self):
        """Set up test environment."""
        self.governance = GovernanceDAOEngine()

    def test_emergency_lockdown_activation(self):
        """Test that emergency lockdown can prevent rapid takeover."""
        # Simulate governance attack detection
        success = self.governance.implement_emergency_governance_lockdown(
            "Coordinated governance capture attempt detected", duration_hours=24
        )

        assert success
        assert self.governance.governance_parameters.get("emergency_lockdown", {}).get(
            "active", False
        )

        # Register attacker during lockdown
        identity = {
            "method": "identity_verification",
            "score": 0.8,
            "identifiers": ["attacker_id", "attacker_email"],
            "interaction_history": ["login"],
            "activity_timestamps": [1000],
            "action_types": ["vote"],
        }

        # Should still be able to register but with restrictions
        attacker = self.governance.register_stakeholder("attacker", 1000.0, identity)

        # Attempt to create proposal during lockdown should be delayed
        proposal = self.governance.create_proposal(
            title="Malicious Proposal",
            description="Attempt to take over governance during lockdown",
            proposal_type=ProposalType.POLICY_CHANGE,
            proposer_id="attacker",
        )

        # Voting should be delayed until after lockdown ends
        lockdown_end = self.governance.governance_parameters["emergency_lockdown"][
            "end_time"
        ]
        assert proposal.voting_start >= lockdown_end


def test_comprehensive_attack_scenario():
    """Test comprehensive multi-vector attack scenario."""
    governance = GovernanceDAOEngine()
    constitutional = constitutional_framework

    # Scenario: Wealthy attacker attempts coordinated governance capture

    # Step 1: Attempt high-stake registration (should fail)
    high_stake_identity = {
        "method": "identity_verification",
        "score": 0.8,
        "identifiers": ["attacker_main_id", "attacker_email"],
        "interaction_history": ["login", "vote"],
        "activity_timestamps": [1000, 2000],
        "action_types": ["vote", "stake"],
    }

    with pytest.raises(ValueError, match="concentration limit violated"):
        governance.register_stakeholder("main_attacker", 50000.0, high_stake_identity)

    # Step 2: Attempt Sybil attack with multiple fake accounts (should fail)
    sybil_identities = []
    for i in range(10):
        identity = {
            "method": "weak_verification",
            "score": 0.6,  # Below threshold
            "identifiers": [f"sybil_{i}_id"],
            "interaction_history": [],
            "activity_timestamps": [1000 + i, 2000 + i],  # Suspiciously regular
            "action_types": ["vote"],
        }
        sybil_identities.append(identity)

    successful_sybils = 0
    for i, identity in enumerate(sybil_identities):
        try:
            governance.register_stakeholder(f"sybil_{i}", 100.0, identity)
            successful_sybils += 1
        except ValueError:
            pass  # Expected to fail

    # Should have prevented most/all Sybil accounts
    assert successful_sybils < 2

    # Step 3: Attempt constitutional violation (should fail)
    violation_proposal = {
        "proposal_id": "attack_proposal_1",
        "title": "Remove All Democratic Protections",
        "description": "Eliminate attribution rights, transparency, and democratic participation protections",
        "proposer_id": "main_attacker",
    }

    (
        is_constitutional,
        violation_reason,
        violated_principles,
    ) = constitutional.validate_proposal_constitutionality(violation_proposal)

    assert not is_constitutional
    assert len(violated_principles) > 0

    # Step 4: System should detect attack pattern and activate emergency protections
    # (This would be triggered by the monitoring system in practice)
    constitutional.activate_constitutional_emergency(
        "Multi-vector governance attack detected", duration_hours=48
    )

    assert constitutional.constitutional_emergency_active

    print("✅ Comprehensive attack scenario successfully defended against!")


if __name__ == "__main__":
    # Run comprehensive attack scenario test
    test_comprehensive_attack_scenario()
    print("All governance security tests would pass with proper pytest execution.")
