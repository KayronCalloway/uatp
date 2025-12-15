# Set high precision for financial calculations
from decimal import Decimal, getcontext

import pytest

from src.economic.fcde_engine import ContributionType, FCDEEngine
from src.security.identity_verification import TestIdentityVerifier

getcontext().prec = 28


@pytest.fixture
def engine():
    """Provides a fresh instance of the FCDEEngine for each test."""
    return FCDEEngine(identity_verifier=TestIdentityVerifier())


def test_engine_initialization(engine: FCDEEngine):
    """Test that the FCDEEngine initializes with correct default values."""
    assert isinstance(engine, FCDEEngine)
    assert engine.system_treasury == Decimal("1000000.0")
    assert engine.dividend_rate == Decimal("0.05")
    assert not engine.contributions
    assert not engine.creator_accounts


def test_register_contribution(engine: FCDEEngine):
    """Test registering a single contribution."""
    capsule_id = "cap_1"
    creator_id = "creator_a"

    contribution_id = engine.register_contribution(
        capsule_id=capsule_id,
        contributor_id=creator_id,
        contribution_type=ContributionType.CAPSULE_CREATION,
        quality_score=Decimal("1.5"),
    )

    assert contribution_id in engine.contributions
    contribution = engine.contributions[contribution_id]
    assert contribution.contributor_id == creator_id
    assert contribution.capsule_id == capsule_id
    assert contribution.quality_score == Decimal("1.5")

    assert creator_id in engine.creator_accounts
    creator_account = engine.creator_accounts[creator_id]
    assert creator_account.total_contributions == contribution.calculate_base_value()
    assert contribution_id in creator_account.contribution_history


def test_process_dividend_distribution_single_contributor(engine: FCDEEngine):
    """Test dividend distribution with one contributor."""
    capsule_id = "cap_1"
    creator_id = "creator_a"

    engine.register_contribution(
        capsule_id=capsule_id,
        contributor_id=creator_id,
        contribution_type=ContributionType.CAPSULE_CREATION,
    )

    engine.record_capsule_usage(capsule_id, usage_value=Decimal("100"))

    pool_id = engine.process_dividend_distribution()

    assert pool_id in engine.dividend_pools
    creator_account = engine.creator_accounts[creator_id]
    assert creator_account.unclaimed_dividends > Decimal("0.0")
    assert creator_account.total_dividends_earned == creator_account.unclaimed_dividends


def test_claim_dividends(engine: FCDEEngine):
    """Test a creator claiming their earned dividends."""
    capsule_id = "cap_1"
    creator_id = "creator_a"

    engine.register_contribution(
        capsule_id, creator_id, ContributionType.CAPSULE_CREATION
    )
    engine.record_capsule_usage(capsule_id, usage_value=Decimal("200"))
    engine.process_dividend_distribution()

    creator_account = engine.creator_accounts[creator_id]
    initial_dividends = creator_account.unclaimed_dividends
    assert initial_dividends > 0

    claimed_amount, message = engine.claim_dividends(creator_id)

    assert claimed_amount == initial_dividends
    assert creator_account.unclaimed_dividends == Decimal("0.0")
    assert creator_account.total_dividends_claimed == initial_dividends
    assert "Successfully claimed" in message


def test_dividend_distribution_multiple_contributors(engine: FCDEEngine):
    """Test that dividends are split correctly between multiple contributors."""
    # Register contributions from two creators
    engine.register_contribution(
        "cap_1",
        "creator_a",
        ContributionType.CAPSULE_CREATION,
        quality_score=Decimal("1.0"),
    )
    engine.register_contribution(
        "cap_2",
        "creator_b",
        ContributionType.KNOWLEDGE_PROVISION,
        quality_score=Decimal("2.0"),
    )

    # Record usage for both capsules
    engine.record_capsule_usage("cap_1", usage_value=Decimal("50"))
    engine.record_capsule_usage("cap_2", usage_value=Decimal("100"))

    # Process dividends
    engine.process_dividend_distribution()

    account_a = engine.creator_accounts["creator_a"]
    account_b = engine.creator_accounts["creator_b"]

    assert account_a.unclaimed_dividends > 0
    assert account_b.unclaimed_dividends > 0

    # Creator B should have earned more due to higher quality score and usage
    assert account_b.total_dividends_earned > account_a.total_dividends_earned

    # Verify total distributed amount
    total_distributed = (
        account_a.total_dividends_earned + account_b.total_dividends_earned
    )
    pool = engine.dividend_pools[list(engine.dividend_pools.keys())[0]]
    assert abs(total_distributed - pool.distributed_dividends) < Decimal("0.00001")
