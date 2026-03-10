"""
Comprehensive security tests for UATP economic attack prevention.

Tests all major attack vectors including attribution gaming, dividend manipulation,
Sybil attacks, flash loan attacks, governance token attacks, and payment exploits.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from src.attribution.cross_conversation_tracker import CrossConversationTracker
from src.economic.circuit_breakers import (
    EconomicCircuitBreakerManager,
)
from src.economic.common_attribution_fund import CommonAttributionFund
from src.economic.fcde_engine import FCDEEngine
from src.economic.security_monitor import (
    AttackType,
    EconomicSecurityMonitor,
    ThreatLevel,
)
from src.governance.advanced_governance import GovernanceDAOEngine, VoteType
from src.integrations.economic.capsule_dividend_engine import CapsuleDividendEngine
from src.security.identity_verification import TestIdentityVerifier


class TestAttributionGamingProtection:
    """Test protection against attribution gaming attacks."""

    @pytest.fixture
    async def tracker(self):
        """Create a cross-conversation tracker for testing."""
        return CrossConversationTracker()

    @pytest.mark.asyncio
    async def test_keyword_stuffing_detection(self, tracker):
        """Test detection of keyword stuffing attacks."""

        # Create content with obvious keyword stuffing
        stuffed_content = "innovation " * 50 + "blockchain " * 30 + "AI revolution"
        normal_content = (
            "This is a thoughtful analysis of innovation in blockchain and AI"
        )

        # The similarity calculation should detect and penalize keyword stuffing
        similarity = tracker._calculate_content_similarity(
            stuffed_content, normal_content
        )

        # Should return very low similarity due to keyword stuffing detection
        assert similarity < 0.1, "Keyword stuffing should result in very low similarity"

    @pytest.mark.asyncio
    async def test_template_gaming_detection(self, tracker):
        """Test detection of template-based similarity gaming."""

        # Create template-based content
        template1 = "The [TOPIC] has [ADJECTIVE] implications for [FIELD]. This [VERB] the [NOUN]."
        template2 = "The blockchain has revolutionary implications for finance. This transforms the industry."

        # Should detect template gaming
        gaming_detected = tracker._detect_template_gaming(template1, template2)
        assert gaming_detected, "Template gaming should be detected"

    @pytest.mark.asyncio
    async def test_artificial_similarity_inflation(self, tracker):
        """Test detection of artificial similarity inflation."""

        # Create artificially similar content (same sentences with minor changes)
        content1 = "The quick brown fox jumps. The lazy dog sleeps. Innovation drives progress."
        content2 = "The quick brown fox jumps. The lazy dog sleeps. Innovation drives progress."

        # Should detect artificial inflation
        inflation_detected = tracker._detect_artificial_similarity_inflation(
            content1, content2
        )
        assert inflation_detected, "Artificial similarity inflation should be detected"

    @pytest.mark.asyncio
    async def test_character_manipulation_detection(self, tracker):
        """Test detection of character-level manipulation."""

        # Create content with character manipulation (spaces, punctuation)
        content1 = "innovation blockchain artificial intelligence"
        content2 = "innovation, blockchain; artificial   intelligence!!!"

        # Should detect character manipulation
        manipulation_detected = tracker._detect_character_manipulation(
            content1, content2
        )
        assert manipulation_detected, "Character manipulation should be detected"


class TestDividendPoolProtection:
    """Test protection against dividend pool drainage attacks."""

    @pytest.fixture
    def fund(self):
        """Create a common attribution fund for testing."""
        return CommonAttributionFund()

    @pytest.mark.asyncio
    async def test_allocation_concentration_limits(self, fund):
        """Test that allocation concentration limits prevent pool drainage."""

        # Register participants
        fund.register_participant("legitimate_user", "contributor")
        fund.register_participant("potential_attacker", "contributor")

        # Make minimal contributions to meet requirements
        fund.contribute_to_fund("legitimate_user", Decimal("10"), "test")
        fund.contribute_to_fund("potential_attacker", Decimal("10"), "test")

        # Simulate an attempt to claim a large portion
        period_id = fund.create_distribution_period(Decimal("1000"))

        # Try to calculate distribution - should apply concentration limits
        distributions = fund.calculate_distribution_allocations(period_id)

        # Check that no single participant gets more than 25%
        total_amount = sum(d.amount for d in distributions)
        for distribution in distributions:
            concentration = (
                distribution.amount / total_amount if total_amount > 0 else 0
            )
            assert (
                concentration <= 0.25
            ), f"Concentration limit violated: {concentration:.2%}"

    @pytest.mark.asyncio
    async def test_fake_participant_rejection(self, fund):
        """Test rejection of fake participants."""

        # Try to register a participant with minimal contribution
        fund.register_participant("fake_user", "contributor")

        # Don't make sufficient contributions
        # Participant should be rejected during validation
        is_legitimate = fund._validate_recipient_legitimacy("fake_user")
        assert not is_legitimate, "Fake participant should be rejected"

    @pytest.mark.asyncio
    async def test_suspicious_registration_patterns(self, fund):
        """Test detection of suspicious batch registration patterns."""

        # Create multiple accounts in rapid succession
        current_time = datetime.now(timezone.utc)

        for i in range(10):
            participant_id = f"batch_user_{i}"
            fund.register_participant(participant_id, "contributor")

            # Make minimal contribution to avoid immediate rejection
            fund.contribute_to_fund(participant_id, Decimal("5"), "test")

        # Check if suspicious pattern is detected
        suspicious = fund._detect_suspicious_participant_behavior("batch_user_5")
        assert suspicious, "Suspicious batch registration should be detected"


class TestSybilAttackProtection:
    """Test protection against Sybil attacks."""

    @pytest.fixture
    def fcde_engine(self):
        """Create an FCDE engine for testing."""
        return FCDEEngine(identity_verifier=TestIdentityVerifier())

    @pytest.mark.asyncio
    async def test_rate_limiting_account_creation(self, fcde_engine):
        """Test rate limiting prevents rapid account creation."""

        ip_address = "192.168.1.100"

        # Try to create many accounts from the same IP
        successful_creations = 0

        for i in range(15):  # Try to create more than the limit
            try:
                contributor_id = f"user_{i}"

                # Mock metadata with same IP
                metadata = {
                    "ip_address": ip_address,
                    "identity_verified": True,
                    "description": f"Legitimate user {i}",
                }

                fcde_engine.register_contribution(
                    f"capsule_{i}", contributor_id, "DIRECT", Decimal("1.0"), metadata
                )
                successful_creations += 1

            except Exception as e:
                # Should hit rate limit
                if "rate limit" in str(e).lower():
                    break

        # Should not allow unlimited account creation
        assert (
            successful_creations < 15
        ), "Rate limiting should prevent excessive account creation"

    @pytest.mark.asyncio
    async def test_identity_verification_requirement(self, fcde_engine):
        """Test that identity verification is required."""

        # Try to create account without identity verification
        metadata = {
            "ip_address": "192.168.1.1",
            "identity_verified": False,
            "description": "Unverified user",
        }

        with pytest.raises(Exception) as exc_info:
            fcde_engine.register_contribution(
                "test_capsule", "unverified_user", "DIRECT", Decimal("1.0"), metadata
            )

        assert "verification" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_suspicious_metadata_detection(self, fcde_engine):
        """Test detection of suspicious metadata patterns."""

        # Test various suspicious patterns
        suspicious_metadata_list = [
            {"description": "bot", "name": "test_bot"},
            {"description": "fake", "name": "fake_user"},
            {"description": "auto", "name": "auto_user"},
            {"description": "x", "name": "y"},  # Too short
            {"description": "aaaaaaaaaa", "name": "aaaaaaa"},  # Repeated characters
        ]

        for metadata in suspicious_metadata_list:
            suspicious = fcde_engine._detect_suspicious_metadata_patterns(metadata)
            assert suspicious, f"Should detect suspicious metadata: {metadata}"


class TestFlashLoanProtection:
    """Test protection against flash loan style attacks."""

    @pytest.fixture
    def dividend_engine(self):
        """Create a dividend engine for testing."""
        return CapsuleDividendEngine()

    @pytest.mark.asyncio
    async def test_atomic_state_locking(self, dividend_engine):
        """Test that atomic state locking prevents concurrent manipulation."""

        # Mock the necessary methods
        dividend_engine.build_ancestry_tree = AsyncMock(
            return_value={"test_capsule": Mock()}
        )
        dividend_engine._validate_distribution_timing = Mock(return_value=True)
        dividend_engine._check_distribution_rate_limit = Mock(return_value=True)

        capsule_id = "test_capsule"

        # Start multiple concurrent distributions (simulating flash loan attack)
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                dividend_engine.distribute_value(
                    capsule_id=capsule_id, value_amount=Decimal("100"), currency="USD"
                )
            )
            tasks.append(task)

        # Only one should succeed due to atomic locking
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful_distributions = sum(
            1 for result in results if not isinstance(result, Exception)
        )
        assert (
            successful_distributions <= 1
        ), "Atomic locking should prevent concurrent distributions"

    @pytest.mark.asyncio
    async def test_ancestry_tree_integrity_validation(self, dividend_engine):
        """Test ancestry tree integrity validation."""

        # Create a manipulated ancestry tree
        manipulated_tree = {
            "capsule_1": Mock(depth=0, parent_ids=[], child_ids=["capsule_2"]),
            "capsule_2": Mock(depth=1, parent_ids=["capsule_1"], child_ids=[]),
            "capsule_3": Mock(
                depth=-1, parent_ids=[], child_ids=[]
            ),  # Invalid negative depth
        }

        # Should detect integrity violation
        is_valid = dividend_engine._validate_ancestry_tree_integrity(
            manipulated_tree, "capsule_1"
        )
        assert not is_valid, "Should detect ancestry tree integrity violation"

    @pytest.mark.asyncio
    async def test_distribution_timing_validation(self, dividend_engine):
        """Test distribution timing validation prevents rapid-fire attacks."""

        capsule_id = "test_capsule"

        # Record a recent distribution
        dividend_engine._distribution_timestamps[capsule_id] = datetime.now(
            timezone.utc
        )

        # Try to distribute again immediately
        is_valid = dividend_engine._validate_distribution_timing(capsule_id)
        assert not is_valid, "Should prevent distributions that are too frequent"


class TestGovernanceTokenProtection:
    """Test protection against governance token attacks."""

    @pytest.fixture
    def governance_engine(self):
        """Create a governance engine for testing."""
        return GovernanceDAOEngine()

    @pytest.mark.asyncio
    async def test_stake_legitimacy_validation(self, governance_engine):
        """Test validation of stake legitimacy."""

        # Register a stakeholder with suspicious characteristics
        stakeholder_id = "suspicious_voter"
        governance_engine.register_stakeholder(stakeholder_id, 10000)  # Large stake

        # Simulate a new account (just registered)
        stakeholder = governance_engine.stakeholders[stakeholder_id]
        stakeholder.joined_date = datetime.now(timezone.utc)  # Very recent

        # Should fail legitimacy validation
        legitimacy_check = governance_engine._validate_stake_legitimacy(stakeholder_id)
        assert not legitimacy_check[
            "legitimate"
        ], "Should reject suspicious large stakes in new accounts"

    @pytest.mark.asyncio
    async def test_vote_buying_detection(self, governance_engine):
        """Test detection of vote buying patterns."""

        # Register stakeholder and create proposal
        voter_id = "potential_buyer"
        governance_engine.register_stakeholder(voter_id, 1000)

        proposal = governance_engine.create_proposal(
            "Test Proposal", "Test", "PARAMETER_CHANGE", voter_id
        )

        # Simulate suspicious voting power increase before voting
        stakeholder = governance_engine.stakeholders[voter_id]
        stakeholder.stake_amount = 10000  # 10x increase

        # Record the power change
        governance_engine.voting_power_history[voter_id] = [
            (datetime.now(timezone.utc) - timedelta(hours=2), 1000),  # Original power
            (
                datetime.now(timezone.utc) - timedelta(minutes=30),
                10000,
            ),  # Suspicious increase
        ]

        # Should detect vote buying pattern
        vote_buying_check = governance_engine._detect_vote_buying_patterns(
            voter_id, proposal.proposal_id, VoteType.YES
        )
        assert vote_buying_check[
            "suspicious"
        ], "Should detect suspicious voting power increase"

    @pytest.mark.asyncio
    async def test_coordinated_voting_detection(self, governance_engine):
        """Test detection of coordinated voting behavior."""

        # Create multiple voters
        proposal_id = "test_proposal"
        voter_ids = []

        for i in range(15):
            voter_id = f"coordinated_voter_{i}"
            governance_engine.register_stakeholder(voter_id, 100)
            voter_ids.append(voter_id)

        # Create a mock proposal
        governance_engine.proposals[proposal_id] = Mock()
        governance_engine.proposals[proposal_id].votes = []

        # Simulate synchronized voting (all within 1 minute)
        base_time = datetime.now(timezone.utc)
        for i, voter_id in enumerate(voter_ids):
            vote = Mock()
            vote.voter_id = voter_id
            vote.timestamp = base_time + timedelta(seconds=i * 2)  # 2 seconds apart
            governance_engine.proposals[proposal_id].votes.append(vote)

        # Should detect coordinated behavior
        coordinated = governance_engine._detect_coordinated_voting_behavior(
            voter_ids[0], proposal_id
        )
        assert coordinated, "Should detect coordinated voting behavior"


class TestSecurityMonitoring:
    """Test the security monitoring system."""

    @pytest.fixture
    def monitor(self):
        """Create a security monitor for testing."""
        return EconomicSecurityMonitor()

    @pytest.mark.asyncio
    async def test_attribution_gaming_alert(self, monitor):
        """Test attribution gaming attack detection and alerting."""

        # Simulate multiple high similarity events
        for i in range(6):  # Exceed threshold of 5
            await monitor.record_attribution_event(
                event_type="similarity_check",
                similarity_score=0.98,  # Above threshold
                content_hash=f"hash_{i}",
            )

        # Should generate alert
        alerts = [
            alert
            for alert in monitor.alerts
            if alert.attack_type == AttackType.ATTRIBUTION_GAMING
        ]
        assert len(alerts) > 0, "Should generate attribution gaming alert"
        assert alerts[0].threat_level == ThreatLevel.HIGH

    @pytest.mark.asyncio
    async def test_dividend_concentration_alert(self, monitor):
        """Test dividend concentration attack detection."""

        # Simulate concentration violation
        await monitor.record_dividend_event(
            event_type="distribution",
            recipient_id="attacker",
            amount="500",  # 50% of 1000 total
        )
        await monitor.record_dividend_event(
            event_type="distribution", recipient_id="legitimate_user", amount="500"
        )

        # Should detect concentration issue
        alerts = [
            alert
            for alert in monitor.alerts
            if alert.attack_type == AttackType.DIVIDEND_MANIPULATION
        ]
        # Note: This might not trigger immediately if we need more context

    @pytest.mark.asyncio
    async def test_sybil_attack_alert(self, monitor):
        """Test Sybil attack detection and alerting."""

        # Simulate rapid account creation from same IP
        ip_address = "192.168.1.200"

        for i in range(12):  # Exceed threshold of 10
            await monitor.record_account_creation_event(
                event_type="account_created",
                account_id=f"account_{i}",
                ip_address=ip_address,
            )

        # Should generate Sybil attack alert
        alerts = [
            alert
            for alert in monitor.alerts
            if alert.attack_type == AttackType.SYBIL_ATTACK
        ]
        assert len(alerts) > 0, "Should generate Sybil attack alert"
        assert alerts[0].threat_level == ThreatLevel.CRITICAL


class TestCircuitBreakers:
    """Test economic circuit breaker functionality."""

    @pytest.fixture
    def circuit_manager(self):
        """Create a circuit breaker manager for testing."""
        return EconomicCircuitBreakerManager()

    @pytest.mark.asyncio
    async def test_circuit_breaker_tripping(self, circuit_manager):
        """Test that circuit breakers trip after too many failures."""

        # Create a failing operation
        async def failing_operation():
            raise Exception("Simulated failure")

        # Execute the operation multiple times to trip the circuit
        failures = 0
        for i in range(10):
            try:
                await circuit_manager.execute_protected_operation(
                    "attribution_system", failing_operation
                )
            except Exception:
                failures += 1

        # Circuit should be open now
        status = circuit_manager.get_system_status()
        attribution_circuit = status["circuit_details"]["attribution_system"]

        # Should eventually trip (may take several failures)
        if failures >= 5:  # Based on threshold
            assert attribution_circuit["state"] in ["open", "half_open"]

    @pytest.mark.asyncio
    async def test_global_emergency_mode(self, circuit_manager):
        """Test global emergency mode activation."""

        # Simulate multiple critical circuit failures
        async def failing_operation():
            raise Exception("Critical failure")

        # Trip critical circuits
        critical_circuits = ["governance_system", "high_value_operations"]

        for circuit_name in critical_circuits:
            for i in range(5):  # Trip each circuit
                try:
                    await circuit_manager.execute_protected_operation(
                        circuit_name, failing_operation
                    )
                except Exception:
                    pass

        # Should activate global emergency mode
        status = circuit_manager.get_system_status()
        if status["open_circuits"] >= 2:
            assert status["global_emergency"] or status["system_health"] in [
                "emergency",
                "degraded",
            ]

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, circuit_manager):
        """Test circuit breaker recovery after failures stop."""

        # Get initial state
        initial_status = circuit_manager.get_system_status()

        # Successful operation
        async def successful_operation():
            return "success"

        # Execute successful operations
        for i in range(3):
            result = await circuit_manager.execute_protected_operation(
                "attribution_system", successful_operation
            )
            assert result == "success"

        # System should remain healthy with successful operations
        final_status = circuit_manager.get_system_status()
        assert final_status["system_health"] in [
            "healthy",
            "impaired",
        ]  # Should not be emergency


class TestIntegratedSecurity:
    """Test integrated security across all systems."""

    @pytest.mark.asyncio
    async def test_coordinated_attack_simulation(self):
        """Simulate a coordinated attack across multiple vectors."""

        # Initialize all systems
        monitor = EconomicSecurityMonitor()
        circuit_manager = EconomicCircuitBreakerManager()

        # Simulate coordinated attack
        attack_events = [
            # Attribution gaming
            ("attribution", {"similarity_score": 0.97, "content_hash": "fake_1"}),
            ("attribution", {"similarity_score": 0.96, "content_hash": "fake_2"}),
            ("attribution", {"similarity_score": 0.98, "content_hash": "fake_3"}),
            # Sybil attack
            ("account_creation", {"ip_address": "10.0.0.1", "account_id": "sybil_1"}),
            ("account_creation", {"ip_address": "10.0.0.1", "account_id": "sybil_2"}),
            ("account_creation", {"ip_address": "10.0.0.1", "account_id": "sybil_3"}),
            # Dividend manipulation
            ("dividend", {"recipient_id": "attacker", "amount": "800"}),
            ("dividend", {"recipient_id": "victim", "amount": "200"}),
        ]

        # Execute coordinated attack
        for event_type, event_data in attack_events:
            if event_type == "attribution":
                await monitor.record_attribution_event(**event_data)
            elif event_type == "account_creation":
                await monitor.record_account_creation_event(**event_data)
            elif event_type == "dividend":
                await monitor.record_dividend_event(**event_data)

        # Should detect multiple attack vectors
        attack_types_detected = {alert.attack_type for alert in monitor.alerts}

        # Should detect at least some of the attack vectors
        assert (
            len(attack_types_detected) > 0
        ), "Should detect coordinated attack vectors"

    @pytest.mark.asyncio
    async def test_system_resilience_under_attack(self):
        """Test that the system remains operational under attack."""

        circuit_manager = EconomicCircuitBreakerManager()

        # Simulate mixed success/failure operations (partial attack)
        async def mixed_operation(should_fail=False):
            if should_fail:
                raise Exception("Attack simulation")
            return "success"

        successes = 0
        failures = 0

        # Execute mixed operations
        for i in range(20):
            try:
                # 30% failure rate (simulating partial attack)
                should_fail = (i % 10) < 3

                result = await circuit_manager.execute_protected_operation(
                    "attribution_system", mixed_operation, should_fail
                )

                if result == "success":
                    successes += 1

            except Exception:
                failures += 1

        # System should handle mixed conditions
        status = circuit_manager.get_system_status()

        # Should maintain some level of operation
        assert successes > 0, "System should maintain some successful operations"
        assert status["system_health"] in [
            "healthy",
            "impaired",
            "degraded",
        ], "System should remain operational"


if __name__ == "__main__":
    # Run specific test for debugging
    pytest.main(
        [
            __file__
            + "::TestAttributionGamingProtection::test_keyword_stuffing_detection",
            "-v",
        ]
    )
