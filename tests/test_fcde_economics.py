"""
Tests for the Fair Creator Dividend Engine (FCDE) economic system.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.capsule_schema import (
    CapsuleStatus,
    ReasoningStep,
    ReasoningTraceCapsule,
    ReasoningTracePayload,
    Verification,
)
from src.economic.capsule_economics import capsule_economics
from src.economic.fcde_engine import (
    AttributionRecord,
    Contribution,
    ContributionType,
    fcde_engine,
)


def test_contribution_registration():
    """Test registering contributions with FCDE."""

    # Register a capsule creation contribution
    contribution_id = fcde_engine.register_contribution(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        contributor_id="creator_001",
        contribution_type=ContributionType.CAPSULE_CREATION,
        quality_score=Decimal("1.5"),
        metadata={"test": "data"},
    )

    assert contribution_id is not None
    assert contribution_id in fcde_engine.contributions

    contribution = fcde_engine.contributions[contribution_id]
    assert contribution.contributor_id == "creator_001"
    assert contribution.contribution_type == ContributionType.CAPSULE_CREATION
    assert contribution.quality_score == Decimal("1.5")
    assert contribution.metadata["test"] == "data"

    # Check that creator account was created
    assert "creator_001" in fcde_engine.creator_accounts
    account = fcde_engine.creator_accounts["creator_001"]
    assert contribution_id in account.contribution_history
    assert account.total_contributions > 0


def test_capsule_usage_recording():
    """Test recording capsule usage for economic tracking."""

    # First register a contribution
    contribution_id = fcde_engine.register_contribution(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        contributor_id="creator_002",
        contribution_type=ContributionType.KNOWLEDGE_PROVISION,
        quality_score=Decimal("2.0"),
    )

    # Record usage
    fcde_engine.record_capsule_usage("test_capsule_002", Decimal("5.0"))

    # Check attribution record was updated
    assert "test_capsule_002" in fcde_engine.attributions
    attribution = fcde_engine.attributions["test_capsule_002"]
    assert attribution.total_value_generated == Decimal("5.0")

    # Check contribution usage count
    contribution = fcde_engine.contributions[contribution_id]
    assert contribution.usage_count == 1


def test_quality_multiplier_calculation():
    """Test quality multiplier calculation."""

    # Create a capsule with some usage
    contribution_id = fcde_engine.register_contribution(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        contributor_id="creator_003",
        contribution_type=ContributionType.REASONING_QUALITY,
        quality_score=Decimal("1.0"),
    )

    # Record significant usage
    fcde_engine.record_capsule_usage("test_capsule_003", Decimal("200.0"))

    # Calculate quality multiplier
    multiplier = fcde_engine.calculate_quality_multiplier("test_capsule_003")

    # Should be higher than 1.0 due to usage
    assert multiplier > Decimal("1.0")
    assert multiplier <= Decimal("5.0")  # Capped at 5x


def test_dividend_distribution():
    """Test dividend distribution process."""

    # Register multiple contributions
    for i in range(3):
        fcde_engine.register_contribution(
            capsule_id=f"test_capsule_{i+10}",
            contributor_id=f"creator_{i+10}",
            contribution_type=ContributionType.CAPSULE_CREATION,
            quality_score=Decimal("1.0"),
        )

    # Set dividend pool
    initial_treasury = fcde_engine.system_treasury
    pool_value = Decimal("1000.0")

    # Process dividend distribution
    pool_id = fcde_engine.process_dividend_distribution(pool_value)

    assert pool_id is not None
    assert pool_id in fcde_engine.dividend_pools

    # Check treasury was reduced
    assert fcde_engine.system_treasury == initial_treasury - pool_value

    # Check dividend pool
    dividend_pool = fcde_engine.dividend_pools[pool_id]
    assert dividend_pool.available_dividends == pool_value
    assert dividend_pool.distributed_dividends > 0

    # Check that creators received dividends
    for i in range(3):
        creator_id = f"creator_{i+10}"
        if creator_id in fcde_engine.creator_accounts:
            account = fcde_engine.creator_accounts[creator_id]
            assert account.unclaimed_dividends > 0


def test_dividend_claiming():
    """Test dividend claiming process."""

    # Register a contribution
    fcde_engine.register_contribution(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        contributor_id="creator_claim",
        contribution_type=ContributionType.KNOWLEDGE_PROVISION,
        quality_score=Decimal("1.0"),
    )

    # Process dividend distribution
    fcde_engine.process_dividend_distribution(Decimal("500.0"))

    # Check creator has unclaimed dividends
    account = fcde_engine.creator_accounts["creator_claim"]
    unclaimed_before = account.unclaimed_dividends

    assert unclaimed_before > 0

    # Claim dividends
    claimed_amount = fcde_engine.claim_dividends("creator_claim")

    # Check dividends were claimed
    assert claimed_amount == unclaimed_before
    assert account.unclaimed_dividends == 0
    assert account.total_dividends_claimed == claimed_amount


def test_creator_analytics():
    """Test creator analytics generation."""

    # Register multiple contributions for a creator
    creator_id = "analytics_creator"

    for i in range(3):
        fcde_engine.register_contribution(
            capsule_id=f"analytics_capsule_{i}",
            contributor_id=creator_id,
            contribution_type=ContributionType.CAPSULE_CREATION,
            quality_score=Decimal("1.0"),
        )

    # Get analytics
    analytics = fcde_engine.get_creator_analytics(creator_id)

    assert analytics["creator_id"] == creator_id
    assert analytics["total_contributions"] > 0
    assert len(analytics["recent_contributions"]) == 3
    assert "contribution_breakdown" in analytics
    assert "capsule_creation" in analytics["contribution_breakdown"]


def test_system_analytics():
    """Test system-wide analytics."""

    analytics = fcde_engine.get_system_analytics()

    assert "total_contributions" in analytics
    assert "total_creators" in analytics
    assert "system_treasury" in analytics
    assert "top_contributors" in analytics
    assert "contribution_type_distribution" in analytics
    assert analytics["total_contributions"] >= 0
    assert analytics["total_creators"] >= 0


def test_capsule_economics_integration():
    """Test integration between capsule system and economics."""

    # Create a test capsule
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2025_07_11_abcdef1234567890",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.SEALED,
        verification=Verification(
            signature="ed25519:0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
            merkle_root="sha256:" + "0" * 64,
        ),
        reasoning_trace=ReasoningTracePayload(
            reasoning_steps=[
                ReasoningStep(
                    step_id=1,
                    operation="observation",
                    reasoning="Step 1",
                    confidence=0.9,
                ),
                ReasoningStep(
                    step_id=2,
                    operation="conclusion",
                    reasoning="Step 2",
                    confidence=0.8,
                ),
            ],
            total_confidence=0.85,
        ),
    )

    # Register capsule creation
    contribution_id = capsule_economics.register_capsule_creation(
        capsule=capsule, creator_id="economics_creator"
    )

    assert contribution_id is not None
    assert capsule.capsule_id in capsule_economics.capsule_value_cache

    # Record usage
    capsule_economics.record_capsule_usage(
        capsule_id=capsule.capsule_id,
        user_id="user_001",
        usage_type="reasoning_access",
        usage_value=Decimal("2.0"),
    )

    # Check usage was recorded
    assert capsule.capsule_id in capsule_economics.usage_tracking
    tracking = capsule_economics.usage_tracking[capsule.capsule_id]
    assert tracking["total_usage"] == 1
    assert "user_001" in tracking["unique_users"]


def test_capsule_roi_calculation():
    """Test ROI calculation for capsules."""

    # Create and register capsule
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2025_07_11_1234567890abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.SEALED,
        verification=Verification(
            signature="ed25519:0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
            merkle_root="sha256:" + "0" * 64,
        ),
        reasoning_trace=ReasoningTracePayload(reasoning_steps=[], total_confidence=1.0),
    )

    capsule_economics.register_capsule_creation(capsule, "roi_creator")

    # Record multiple uses
    for i in range(5):
        capsule_economics.record_capsule_usage(
            capsule_id=capsule.capsule_id,
            user_id=f"user_{i}",
            usage_value=Decimal("1.0"),
        )

    # Calculate ROI
    roi_data = capsule_economics.calculate_capsule_roi(capsule.capsule_id)

    assert "error" not in roi_data
    assert roi_data["capsule_id"] == capsule.capsule_id
    assert roi_data["total_usage"] == 5
    assert roi_data["unique_users"] == 5
    assert roi_data["current_value"] > roi_data["initial_value"]
    assert roi_data["roi_percentage"] > 0


def test_creator_economic_summary():
    """Test creator economic summary."""

    # Create capsule and register
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2025_07_11_fedcba0987654321",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.SEALED,
        verification=Verification(
            signature="ed25519:0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
            merkle_root="sha256:" + "0" * 64,
        ),
        reasoning_trace=ReasoningTracePayload(reasoning_steps=[], total_confidence=1.0),
    )

    creator_id = "summary_creator"
    capsule_economics.register_capsule_creation(capsule, creator_id)

    # Record usage
    capsule_economics.record_capsule_usage(capsule.capsule_id, "user_001")

    # Get economic summary
    summary = capsule_economics.get_creator_economic_summary(creator_id)

    assert "error" not in summary
    assert summary["creator_id"] == creator_id
    assert "average_roi_percentage" in summary
    assert "capsule_count" in summary
    assert summary["capsule_count"] >= 1


def test_periodic_dividend_processing():
    """Test periodic dividend processing."""

    # Create some usage to generate dividends
    for i in range(3):
        capsule = ReasoningTraceCapsule(
            capsule_id=f"caps_2025_07_11_000000000000000{i}",
            version="7.0",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.SEALED,
            verification=Verification(
                signature="ed25519:0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                merkle_root="sha256:" + "0" * 64,
            ),
            reasoning_trace=ReasoningTracePayload(
                reasoning_steps=[], total_confidence=1.0
            ),
        )

        capsule_economics.register_capsule_creation(capsule, f"dividend_creator_{i}")
        capsule_economics.record_capsule_usage(capsule.capsule_id, "user_001")

    # Process periodic dividends
    initial_treasury = fcde_engine.system_treasury
    pool_id = capsule_economics.process_periodic_dividends()

    assert pool_id is not None
    assert pool_id in fcde_engine.dividend_pools

    # Check treasury was reduced
    assert fcde_engine.system_treasury < initial_treasury


def test_treasury_management():
    """Test treasury management functions."""

    initial_treasury = fcde_engine.system_treasury

    # Add to treasury
    fcde_engine.update_treasury(Decimal("500.0"), "Test deposit")
    assert fcde_engine.system_treasury == initial_treasury + Decimal("500.0")

    # Update dividend rate
    fcde_engine.set_dividend_rate(Decimal("0.10"))
    assert fcde_engine.dividend_rate == Decimal("0.10")

    # Test invalid dividend rate
    with pytest.raises(ValueError):
        fcde_engine.set_dividend_rate(Decimal("1.5"))


def test_attribution_record_validation():
    """Test attribution record validation."""

    # Create attribution record
    attribution = AttributionRecord(
        record_id="test_record",
        capsule_id="caps_2024_01_01_0123456789abcdef",
        original_creator="creator_001",
        contributors=["creator_001", "creator_002"],
        contribution_percentages={
            "creator_001": Decimal("60.0"),
            "creator_002": Decimal("40.0"),
        },
        total_value_generated=Decimal("100.0"),
        creation_timestamp=datetime.now(timezone.utc),
        last_updated=datetime.now(timezone.utc),
    )

    # Test validation passes
    assert attribution.validate_percentages() is True

    # Test validation fails
    attribution.contribution_percentages["creator_001"] = Decimal("70.0")
    assert attribution.validate_percentages() is False


def test_contribution_value_calculation():
    """Test contribution value calculation."""

    contribution = Contribution(
        contribution_id="test_contrib",
        contributor_id="test_creator",
        contribution_type=ContributionType.KNOWLEDGE_PROVISION,
        capsule_id="caps_2024_01_01_0123456789abcdef",
        timestamp=datetime.now(timezone.utc),
        quality_score=Decimal("1.5"),
        reward_multiplier=Decimal("2.0"),
    )

    base_value = contribution.calculate_base_value()

    # Should be: base_value * quality_score * reward_multiplier
    expected = Decimal("50.0") * Decimal("1.5") * Decimal("2.0")  # 150.0
    assert base_value == expected


if __name__ == "__main__":
    test_contribution_registration()
    test_capsule_usage_recording()
    test_quality_multiplier_calculation()
    test_dividend_distribution()
    test_dividend_claiming()
    test_creator_analytics()
    test_system_analytics()
    test_capsule_economics_integration()
    test_capsule_roi_calculation()
    test_creator_economic_summary()
    test_periodic_dividend_processing()
    test_treasury_management()
    test_attribution_record_validation()
    test_contribution_value_calculation()
    print("[OK] All FCDE economics tests passed!")
