"""
Failure Dividend System for UATP Capsule Engine.

This module implements the Failure Dividend System, a novel component of the UATP
economic model that recognizes and rewards the value generated from failed
experiments, incomplete capsules, or rejected reasoning traces.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from src.integrations.economic.common_attribution_fund import (
    CommonAttributionFund,
    ContributionType,
)

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Types of failures that can be assigned value."""

    REASONING_REJECTED = auto()  # A reasoning trace was rejected by validation
    CAPSULE_INVALIDATED = auto()  # A capsule was later found to be invalid
    EXPERIMENT_FAILED = auto()  # An experimental path did not yield results
    USER_REFUSED = auto()  # A user explicitly marked the output as a failure
    GOVERNANCE_VIOLATION = auto()  # Failed due to violating a governance policy


@dataclass
class ValuedFailure:
    """Represents a failure that has been assigned a value."""

    id: str
    failure_type: FailureType
    source_capsule_ids: List[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = "No reason provided."
    assigned_value: Decimal = Decimal("0.0")
    currency: str = "USD"
    is_distributed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class FailureDividendSystem:
    """
    Implements the logic for capturing and distributing value from failures.
    """

    def __init__(self, attribution_fund: CommonAttributionFund):
        self.attribution_fund = attribution_fund
        self.valued_failures: Dict[str, ValuedFailure] = {}

    async def log_failure(
        self,
        failure_type: FailureType,
        source_capsule_ids: List[str],
        reason: str,
        assigned_value: Union[Decimal, str],
        currency: str = "USD",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ValuedFailure:
        """
        Log a failure and assign it an economic value.

        Args:
            failure_type: The type of failure.
            source_capsule_ids: The capsule(s) associated with the failure.
            reason: A description of why the failure occurred and why it has value.
            assigned_value: The economic value assigned to this failure.
            currency: The currency of the assigned value.
            metadata: Additional metadata.

        Returns:
            The created ValuedFailure object.
        """
        failure_id = str(uuid.uuid4())
        failure = ValuedFailure(
            id=failure_id,
            failure_type=failure_type,
            source_capsule_ids=source_capsule_ids,
            reason=reason,
            assigned_value=Decimal(str(assigned_value)),
            currency=currency,
            metadata=metadata or {},
        )
        self.valued_failures[failure_id] = failure
        logger.info(
            f"Logged valued failure {failure_id} of type {failure_type.name} with value {assigned_value} {currency}."
        )
        return failure

    async def distribute_failure_dividend(self, failure_id: str) -> bool:
        """
        Distribute the value of a failure to the Common Attribution Fund.

        This creates a new contribution in the CAF of type FAILURE and attributes
        the assigned value to it.
        """
        if failure_id not in self.valued_failures:
            logger.error(f"Failure {failure_id} not found.")
            return False

        failure = self.valued_failures[failure_id]
        if failure.is_distributed:
            logger.warning(
                f"Failure dividend for {failure_id} has already been distributed."
            )
            return True

        try:
            # For simplicity, we'll assign the contribution to the first capsule's author.
            # A more complex model could split it among all contributors of the source capsules.
            contributor_id = f"author_of_{failure.source_capsule_ids[0]}"

            # 1. Register the failure as a contribution to the fund
            contribution_id = await self.attribution_fund.register_contribution(
                contributor_id=contributor_id,  # In a real system, get this from the capsule
                contribution_type=ContributionType.FAILURE,
                capsule_ids=failure.source_capsule_ids,
                weight=1.0,  # Weight could be derived from the assigned value
                description=f"Failure Dividend: {failure.reason}",
                metadata=failure.metadata,
            )

            # 2. Attribute the failure's value to this new contribution
            await self.attribution_fund.attribute_value(
                source_capsule_id=failure.source_capsule_ids[
                    0
                ],  # The primary failed capsule
                contribution_ids=[contribution_id],
                value_amount=failure.assigned_value,
                currency=failure.currency,
                metadata={
                    "failure_id": failure.id,
                    "failure_type": failure.failure_type.name,
                },
            )

            failure.is_distributed = True
            logger.info(
                f"Successfully distributed failure dividend for {failure_id} to the Common Attribution Fund."
            )
            return True
        except Exception as e:
            logger.error(f"Failed to distribute failure dividend for {failure_id}: {e}")
            return False

    def get_failure_log(self) -> List[ValuedFailure]:
        """Return all logged failures."""
        return list(self.valued_failures.values())


async def demo_failure_dividend_system():
    """Demonstrate the Failure Dividend System functionality."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Set up dependencies
        fund = CommonAttributionFund(fund_id="failure-demo", registry_path=tmpdir)
        failure_system = FailureDividendSystem(attribution_fund=fund)

        print("--- Logging a Valued Failure ---")
        failure = await failure_system.log_failure(
            failure_type=FailureType.REASONING_REJECTED,
            source_capsule_ids=["capsule-failed-reasoning"],
            reason="The reasoning trace was rejected by 3/5 validators, but provided a novel approach to the problem.",
            assigned_value="5.00",
        )
        print(
            f"Logged failure {failure.id} with value {failure.assigned_value} {failure.currency}"
        )

        # 2. Distribute the dividend
        print("\n--- Distributing Failure Dividend ---")
        success = await failure_system.distribute_failure_dividend(failure.id)
        print(f"Distribution successful: {success}")

        # 3. Verify results in the Common Attribution Fund
        print("\n--- Verifying Fund State ---")
        fund_stats = await fund.get_fund_stats()
        print(f"Fund has {fund_stats['contribution_count']} contribution(s).")
        print(f"Fund total value received: {fund_stats['total_value_received']} USD")

        contributions = await fund.query_contributions({"contribution_type": "FAILURE"})
        if contributions:
            failure_contrib = contributions[0]
            print(f"Found FAILURE contribution: {failure_contrib.id}")
            print(f"Description: {failure_contrib.description}")

            balance = await fund.get_contributor_balance(failure_contrib.contributor_id)
            print(
                f"Contributor {failure_contrib.contributor_id} now has a balance of: {balance} USD"
            )
        else:
            print("FAILURE contribution not found in the fund.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo_failure_dividend_system())
