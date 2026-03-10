"""
Comprehensive tests for democratic governance protections.

These tests verify that the governance system's democratic safeguards work
correctly and cannot be bypassed by malicious actors.

CRITICAL: These tests simulate attack scenarios to ensure protections work.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from src.governance.advanced_governance import (
    GovernanceDAOEngine,
    ProposalType,
    VoteType,
)
from src.governance.constitutional_framework import (
    ConstitutionalFramework,
    ViolationType,
)
from src.governance.sybil_resistance import (
    SybilResistanceEngine,
    IdentityVerificationMethod,
)
from src.consensus.multi_agent_consensus import (
    MultiAgentConsensusEngine,
    ConsensusNode,
    NodeRole,
)


class TestStakeConcentrationLimits:
    """Test stake concentration limits to prevent governance capture."""

    def setup_method(self):
        """Set up test environment."""
        self.governance = GovernanceDAOEngine()
        self.constitutional = ConstitutionalFramework()

    def test_individual_stake_limit_enforcement(self):
        """Test that individual stake limits are enforced."""

        # Register legitimate stakeholder with 10% stake
        stakeholder1 = self.governance.register_stakeholder(
            "legitimate_user",
            initial_stake=1000.0,
            identity_proof={
                "method": "verified",
                "score": 0.8,
                "identifiers": ["email1@test.com"],
            },
        )
        assert stakeholder1 is not None

        # Try to register malicious actor with 20% stake (should be rejected)
        with pytest.raises(ValueError) as exc_info:
            self.governance.register_stakeholder(
                "malicious_actor",
                initial_stake=3000.0,  # Would be >15% of total
                identity_proof={
                    "method": "verified",
                    "score": 0.8,
                    "identifiers": ["email2@test.com"],
                },
            )

        assert "15%" in str(exc_info.value)
        assert "limit" in str(exc_info.value).lower()

    def test_coordinated_stake_concentration_detection(self):
        """Test detection of coordinated stake concentration attacks."""

        # Register initial legitimate user
        self.governance.register_stakeholder(
            "legitimate_user",
            initial_stake=1000.0,
            identity_proof={
                "method": "verified",
                "score": 0.8,
                "identifiers": ["email1@test.com"],
            },
        )

        # Try to register coordinated group that would exceed limits
        coordinated_group = []
        for i in range(5):
            try:
                stakeholder = self.governance.register_stakeholder(
                    f"coordinated_user_{i}",
                    initial_stake=800.0,  # Each user 8%, but coordinated would exceed 25%
                    identity_proof={
                        "method": "verified",
                        "score": 0.8,
                        "identifiers": [f"coordinated{i}@test.com"],
                        "ip_address": "192.168.1.100",  # Same IP indicates coordination
                    },
                )
                coordinated_group.append(stakeholder)
            except ValueError as e:
                # Should start rejecting after concentration limit reached
                assert "concentration" in str(e).lower()
                break

        # Should not be able to register full coordinated group
        assert len(coordinated_group) < 5

    def test_constitutional_immutability_of_limits(self):
        """Test that stake limits cannot be modified through governance."""

        # Register stakeholder
        self.governance.register_stakeholder(
            "test_user",
            initial_stake=1000.0,
            identity_proof={
                "method": "verified",
                "score": 0.8,
                "identifiers": ["test@test.com"],
            },
        )

        # Try to create proposal to increase stake limits (should be rejected)
        with pytest.raises(ValueError) as exc_info:
            self.governance.create_proposal(
                title="Increase Stake Limits",
                description="Proposal to increase individual stake limits from 15% to 25%",
                proposal_type=ProposalType.PARAMETER_UPDATE,
                proposer_id="test_user",
                execution_data={
                    "parameter_name": "MAX_INDIVIDUAL_VOTING_POWER",
                    "new_value": 0.25,
                },
            )

        assert "constitutional" in str(exc_info.value).lower()
        assert "immutable" in str(exc_info.value).lower()


class TestSybilResistance:
    """Test Sybil resistance mechanisms."""

    def setup_method(self):
        """Set up test environment."""
        self.sybil_resistance = SybilResistanceEngine()
        self.governance = GovernanceDAOEngine()

    def test_duplicate_identifier_rejection(self):
        """Test rejection of duplicate unique identifiers."""

        # Submit first verification
        verification1_id = self.sybil_resistance.submit_identity_verification(
            "user1",
            IdentityVerificationMethod.EMAIL_VERIFICATION,
            {"quality_score": 0.8},
            {"email": "test@example.com"},
        )
        assert verification1_id is not None

        # Try to submit verification with same email (should be rejected)
        verification2_id = self.sybil_resistance.submit_identity_verification(
            "user2",
            IdentityVerificationMethod.EMAIL_VERIFICATION,
            {"quality_score": 0.8},
            {"email": "test@example.com"},  # Same email
        )

        # Check that second verification was rejected
        verifications = self.sybil_resistance.verifications["user2"]
        assert len(verifications) == 1
        assert verifications[0].status.value == "rejected"

    def test_ip_clustering_detection(self):
        """Test detection of multiple accounts from same IP."""

        # Register multiple accounts from same IP
        ip_address = "192.168.1.100"

        for i in range(5):  # Try to register 5 accounts (exceeds limit of 3)
            verification_id = self.sybil_resistance.submit_identity_verification(
                f"user_{i}",
                IdentityVerificationMethod.EMAIL_VERIFICATION,
                {"quality_score": 0.8, "ip_address": ip_address},
                {"email": f"user{i}@example.com"},
            )

        # Detect Sybil clusters
        clusters = self.sybil_resistance.detect_sybil_clusters()

        # Should detect IP-based cluster
        ip_clusters = [c for c in clusters if c.detection_method == "ip_clustering"]
        assert len(ip_clusters) > 0
        assert ip_clusters[0].threat_level.value in ["high", "critical"]

    def test_behavioral_bot_detection(self):
        """Test detection of bot-like behavioral patterns."""

        # Create behavioral pattern that looks like a bot
        from src.governance.sybil_resistance import BehavioralPattern

        bot_pattern = BehavioralPattern(
            participant_id="bot_user", pattern_type="bot_analysis"
        )

        # Add bot-like characteristics
        base_time = datetime.now(timezone.utc)
        for i in range(20):
            # Perfectly regular timestamps (bot-like)
            bot_pattern.activity_timestamps.append(
                base_time + timedelta(seconds=i * 60)
            )
            # Limited action types (bot-like)
            bot_pattern.action_types.append("vote" if i % 2 == 0 else "proposal")
            # Very fast response times (bot-like)
            bot_pattern.response_times.append(0.1)

        self.sybil_resistance.behavioral_patterns["bot_user"] = bot_pattern

        # Calculate authenticity score
        authenticity = self.sybil_resistance._calculate_behavioral_authenticity(
            bot_pattern
        )

        # Should detect bot-like behavior (low authenticity score)
        assert authenticity < 0.5

    def test_economic_bonding_requirements(self):
        """Test economic bonding requirements for participation."""

        # Test insufficient economic bond
        eligibility_result = self.sybil_resistance.check_participation_eligibility(
            "poor_user", "voting_participation"
        )

        assert not eligibility_result[0]  # Should not be eligible
        assert "economic bond" in eligibility_result[1].lower()

        # Register user with sufficient economic bond
        self.sybil_resistance.economic_bonds["rich_user"] = Decimal("1000.0")

        # Add sufficient verifications
        for method in [
            IdentityVerificationMethod.EMAIL_VERIFICATION,
            IdentityVerificationMethod.PHONE_VERIFICATION,
            IdentityVerificationMethod.ECONOMIC_BONDING,
        ]:
            verification_id = self.sybil_resistance.submit_identity_verification(
                "rich_user",
                method,
                {"quality_score": 0.8, "bond_amount": 1000},
                {"email": "rich@example.com", "phone": "+1234567890"},
            )

        # Now should be eligible
        eligibility_result = self.sybil_resistance.check_participation_eligibility(
            "rich_user", "voting_participation"
        )

        assert eligibility_result[0]  # Should be eligible


class TestMinorityProtection:
    """Test minority protection mechanisms."""

    def setup_method(self):
        """Set up test environment."""
        self.governance = GovernanceDAOEngine()
        self.constitutional = ConstitutionalFramework()

        # Register stakeholders representing majority and minority
        for i in range(10):
            self.governance.register_stakeholder(
                f"majority_user_{i}",
                initial_stake=800.0,
                identity_proof={
                    "method": "verified",
                    "score": 0.8,
                    "identifiers": [f"majority{i}@test.com"],
                },
            )

        for i in range(4):
            self.governance.register_stakeholder(
                f"minority_user_{i}",
                initial_stake=600.0,
                identity_proof={
                    "method": "verified",
                    "score": 0.8,
                    "identifiers": [f"minority{i}@test.com"],
                },
            )

    def test_minority_veto_on_constitutional_changes(self):
        """Test minority veto rights on constitutional changes."""

        # Create constitutional change proposal
        proposal = self.governance.create_proposal(
            title="Change Voting System",
            description="Proposal to modify the consensus mechanism for governance",
            proposal_type=ProposalType.SYSTEM_UPGRADE,
            proposer_id="majority_user_0",
        )

        # Majority votes FOR (10 votes)
        for i in range(10):
            self.governance.cast_vote(
                proposal.proposal_id,
                f"majority_user_{i}",
                VoteType.FOR,
                "fake_private_key",
            )

        # Minority votes AGAINST (4 votes, should trigger 25% veto threshold)
        for i in range(4):
            self.governance.cast_vote(
                proposal.proposal_id,
                f"minority_user_{i}",
                VoteType.AGAINST,
                "fake_private_key",
            )

        # Check minority protection
        minority_veto_result = self.constitutional.enforce_minority_veto_rights(
            proposal.to_dict()
            if hasattr(proposal, "to_dict")
            else {
                "proposal_type": "system_upgrade",
                "description": "governance change",
            },
            sum(
                vote.voting_power
                for vote in proposal.votes
                if vote.vote_type == VoteType.AGAINST
            ),
            sum(vote.voting_power for vote in proposal.votes),
        )

        # Should trigger minority veto
        assert not minority_veto_result[0]
        assert "minority veto" in minority_veto_result[1].lower()

    def test_supermajority_requirement_for_constitutional_changes(self):
        """Test supermajority requirements for constitutional changes."""

        # Create constitutional change proposal
        proposal = self.governance.create_proposal(
            title="Fundamental System Change",
            description="Proposal affecting fundamental rights and attribution system",
            proposal_type=ProposalType.RULE_AMENDMENT,
            proposer_id="majority_user_0",
        )

        # Should require supermajority (75%)
        assert proposal.required_threshold >= 0.75


class TestByzantineFaultTolerance:
    """Test Byzantine fault tolerance mechanisms."""

    def setup_method(self):
        """Set up test environment."""
        self.consensus = MultiAgentConsensusEngine()

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
            self.consensus.register_node(node)

    def test_byzantine_behavior_detection(self):
        """Test detection of Byzantine behavior."""

        # Simulate Byzantine behavior for some nodes
        byzantine_node_id = "node_3"
        byzantine_node = self.consensus.nodes[byzantine_node_id]

        # Simulate conflicting votes, slow responses, etc.
        byzantine_node.last_seen = datetime.now(timezone.utc) - timedelta(
            minutes=15
        )  # Very slow
        byzantine_node.reputation = 30.0  # Low reputation

        # Detect Byzantine behavior
        byzantine_score = self.consensus.detect_byzantine_behavior(byzantine_node_id)

        # Should detect Byzantine behavior
        assert byzantine_score > 0.5

    def test_economic_penalties_for_byzantine_behavior(self):
        """Test economic penalties for Byzantine nodes."""

        byzantine_node_id = "node_5"
        original_stake = self.consensus.nodes[byzantine_node_id].stake

        # Apply Byzantine penalty
        penalty_applied = self.consensus.implement_economic_penalties(
            byzantine_node_id, 500.0, "Byzantine behavior detected"  # Penalty amount
        )

        assert penalty_applied

        # Check that stake was reduced
        new_stake = self.consensus.nodes[byzantine_node_id].stake
        assert new_stake < original_stake

        # Check penalty was recorded
        node = self.consensus.nodes[byzantine_node_id]
        assert hasattr(node, "penalty_history")
        assert len(node.penalty_history) > 0

    def test_network_emergency_protocol(self):
        """Test emergency protocol when Byzantine tolerance exceeded."""

        # Simulate high Byzantine behavior across multiple nodes
        byzantine_nodes = [
            "node_0",
            "node_1",
            "node_2",
            "node_3",
            "node_4",
        ]  # 50% of nodes

        for node_id in byzantine_nodes:
            node = self.consensus.nodes[node_id]
            node.byzantine_behavior_score = 0.8  # High Byzantine score

        # Enhanced Byzantine detection should trigger emergency protocol
        byzantine_scores = self.consensus.implement_enhanced_byzantine_detection()

        # Should detect excessive Byzantine behavior
        byzantine_count = sum(1 for score in byzantine_scores.values() if score > 0.5)
        total_nodes = len(self.consensus.nodes)
        byzantine_ratio = byzantine_count / total_nodes

        # Should exceed 33% Byzantine fault tolerance
        assert byzantine_ratio > 0.33

        # Check if emergency protocol was activated
        assert hasattr(self.consensus, "consensus_halted")


class TestTimeBasedProtections:
    """Test time-based democratic protections."""

    def setup_method(self):
        """Set up test environment."""
        self.governance = GovernanceDAOEngine()

        # Register stakeholder
        self.governance.register_stakeholder(
            "test_user",
            initial_stake=1000.0,
            identity_proof={
                "method": "verified",
                "score": 0.8,
                "identifiers": ["test@test.com"],
            },
        )

    def test_voting_power_vesting_periods(self):
        """Test vesting periods for new stakes."""

        stakeholder_id = "test_user"

        # Add vesting stake
        vesting_added = self.governance.add_stake_vesting_period(
            stakeholder_id, 5000.0, 30  # Large stake addition  # 30-day vesting period
        )

        assert vesting_added

        # Calculate vested voting power (should be reduced)
        vested_power = self.governance.calculate_vested_voting_power(stakeholder_id)
        normal_power = self.governance.stakeholders[
            stakeholder_id
        ].calculate_voting_power()

        # Vested power should be less than normal power due to vesting penalty
        assert vested_power < normal_power

    def test_proposal_creation_delays(self):
        """Test mandatory delays for proposal creation."""

        # Create first proposal
        proposal1 = self.governance.create_proposal(
            title="First Proposal",
            description="Test proposal",
            proposal_type=ProposalType.POLICY_CHANGE,
            proposer_id="test_user",
        )

        # Check that voting doesn't start immediately
        assert proposal1.voting_start > proposal1.created_at

        # Time delay should be at least 1 hour for non-emergency proposals
        time_delay = (
            proposal1.voting_start - proposal1.created_at
        ).total_seconds() / 3600
        assert time_delay >= 1.0

    def test_emergency_governance_lockdown(self):
        """Test emergency governance lockdown mechanism."""

        # Trigger emergency lockdown
        lockdown_activated = self.governance.implement_emergency_governance_lockdown(
            "Detected governance attack", 24  # 24-hour lockdown
        )

        assert lockdown_activated

        # Check lockdown parameters
        lockdown_params = self.governance.governance_parameters.get(
            "emergency_lockdown"
        )
        assert lockdown_params is not None
        assert lockdown_params["active"] is True
        assert lockdown_params["reason"] == "Detected governance attack"


class TestIntegratedAttackScenarios:
    """Test integrated attack scenarios to verify all protections work together."""

    def setup_method(self):
        """Set up test environment."""
        self.governance = GovernanceDAOEngine()
        self.sybil_resistance = SybilResistanceEngine()
        self.consensus = MultiAgentConsensusEngine()
        self.constitutional = ConstitutionalFramework()

    def test_coordinated_governance_capture_attempt(self):
        """Test coordinated attempt to capture governance system."""

        # Attacker tries to register multiple coordinated accounts
        attacker_accounts = []
        for i in range(10):
            try:
                stakeholder = self.governance.register_stakeholder(
                    f"attacker_{i}",
                    initial_stake=1200.0,  # Try to get maximum allowable stake
                    identity_proof={
                        "method": "fake",
                        "score": 0.6,  # Just barely passing
                        "identifiers": [f"attacker{i}@fake.com"],
                        "ip_address": "10.0.0.1",  # Same IP
                    },
                )
                attacker_accounts.append(f"attacker_{i}")
            except ValueError:
                # Expected to fail due to protections
                break

        # Should not be able to register all accounts due to concentration limits
        assert len(attacker_accounts) < 10

        # Detect governance capture attempt
        (
            capture_detected,
            threat_score,
            details,
        ) = self.governance.detect_governance_capture_attempt()

        if len(attacker_accounts) > 3:  # If some accounts got through
            assert capture_detected or threat_score > 0.5

    def test_sybil_attack_with_byzantine_behavior(self):
        """Test Sybil attack combined with Byzantine behavior."""

        # Register legitimate nodes first
        for i in range(5):
            node = ConsensusNode(
                node_id=f"legit_node_{i}",
                role=NodeRole.VALIDATOR,
                stake=1000.0,
                reputation=100.0,
                last_seen=datetime.now(timezone.utc),
                public_key=f"pubkey_legit_{i}",
                network_address=f"192.168.1.{i+10}",
            )
            self.consensus.register_node(node)

        # Attacker tries to register Sybil nodes
        sybil_nodes = []
        for i in range(8):
            try:
                node = ConsensusNode(
                    node_id=f"sybil_node_{i}",
                    role=NodeRole.VALIDATOR,
                    stake=800.0,
                    reputation=60.0,  # Barely passing
                    last_seen=datetime.now(timezone.utc),
                    public_key=f"pubkey_sybil_{i}",
                    network_address="10.0.0.100",  # Same IP (suspicious)
                )
                self.consensus.register_node(node)
                sybil_nodes.append(f"sybil_node_{i}")
            except Exception:
                break

        # Simulate Byzantine behavior from Sybil nodes
        for node_id in sybil_nodes:
            if node_id in self.consensus.nodes:
                node = self.consensus.nodes[node_id]
                node.byzantine_behavior_score = 0.7  # High Byzantine score

        # Run enhanced Byzantine detection
        byzantine_scores = self.consensus.implement_enhanced_byzantine_detection()

        # Should detect coordinated Byzantine behavior
        high_byzantine_count = sum(
            1 for score in byzantine_scores.values() if score > 0.6
        )
        assert high_byzantine_count > 0

    def test_constitutional_protection_bypass_attempt(self):
        """Test attempt to bypass constitutional protections."""

        # Register stakeholder
        self.governance.register_stakeholder(
            "constitutional_attacker",
            initial_stake=1000.0,
            identity_proof={
                "method": "verified",
                "score": 0.8,
                "identifiers": ["attacker@test.com"],
            },
        )

        # Try various methods to bypass constitutional protections

        # 1. Try to create proposal to disable concentration checks
        with pytest.raises(ValueError):
            self.governance.create_proposal(
                title="Disable Concentration Checks",
                description="Proposal to disable stake concentration checks for efficiency",
                proposal_type=ProposalType.PARAMETER_UPDATE,
                proposer_id="constitutional_attacker",
                execution_data={
                    "parameter_name": "CONCENTRATION_CHECK_ENABLED",
                    "new_value": False,
                },
            )

        # 2. Try to create proposal to increase individual limits
        with pytest.raises(ValueError):
            self.governance.create_proposal(
                title="Increase Individual Limits",
                description="Increase individual voting power limit to 30%",
                proposal_type=ProposalType.RULE_AMENDMENT,
                proposer_id="constitutional_attacker",
            )

        # 3. Verify constitutional framework actively prevents tampering
        original_limit = self.constitutional.MAX_INDIVIDUAL_VOTING_POWER

        # Simulate attempt to modify (would be caught by integrity check)
        self.constitutional.MAX_INDIVIDUAL_VOTING_POWER = 0.30

        # Run integrity check
        status = self.constitutional.get_constitutional_status()

        # Should restore original value
        assert self.constitutional.MAX_INDIVIDUAL_VOTING_POWER == original_limit
        assert status["framework_active"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
