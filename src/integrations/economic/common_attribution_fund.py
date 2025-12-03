"""
Common Attribution Fund (CAF) for UATP Capsule Engine.

This module implements the Common Attribution Fund, a core component of UATP's
economic justice layer, designed to capture and fairly distribute value from
diffuse or collective influence in AI systems.
"""

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from src.integrations.federated_registry import FederatedModelRegistry

logger = logging.getLogger(__name__)


class ContributionType(Enum):
    """Types of contributions that can be attributed to the fund."""

    DIRECT = auto()  # Direct contribution to content
    DERIVATIVE = auto()  # Derivative or influenced content
    COLLECTIVE = auto()  # General collective knowledge
    FAILURE = auto()  # Failed attempts that still provided value
    REMIX = auto()  # Combination of multiple sources


class DistributionStrategy(Enum):
    """Distribution strategies for fund allocation."""

    EQUAL = auto()  # Equal distribution among contributors
    WEIGHTED = auto()  # Weighted by contribution level
    PROPORTIONAL = auto()  # Proportional to usage/value
    MERIT_BASED = auto()  # Based on peer-reviewed merit
    CASCADE = auto()  # Cascade through attribution chain


@dataclass
class Contribution:
    """A contribution record for the attribution fund."""

    id: str
    contributor_id: str
    contribution_type: ContributionType
    timestamp: datetime
    capsule_ids: List[str]
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None


@dataclass
class Attribution:
    """An attribution record linking value to contributions."""

    id: str
    source_capsule_id: str
    contribution_ids: List[str]
    timestamp: datetime
    value_amount: Decimal
    currency: str = "USD"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Disbursement:
    """A disbursement record for payments from the fund."""

    id: str
    recipient_id: str
    attribution_ids: List[str]
    timestamp: datetime
    amount: Decimal
    currency: str = "USD"
    status: str = "pending"  # pending, processed, failed
    transaction_reference: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CommonAttributionFund:
    """
    Common Attribution Fund implementation for UATP Capsule Engine.

    The Common Attribution Fund (CAF) captures value from AI-generated content
    and distributes it fairly to all contributors along the attribution chain.
    It addresses diffuse influence, collective knowledge, and ensures economic
    justice for all forms of contribution.
    """

    def __init__(
        self,
        fund_id: str = None,
        registry_path: str = None,
        federated_registry: Optional[FederatedModelRegistry] = None,
    ):
        """
        Initialize the Common Attribution Fund.

        Args:
            fund_id: Unique identifier for this fund instance
            registry_path: Path to store fund data
            federated_registry: Optional federated registry for distributed attribution
        """
        self.fund_id = fund_id or str(uuid.uuid4())
        self.registry_path = registry_path or os.path.join(
            os.getcwd(), "attribution_fund"
        )
        self.federated_registry = federated_registry

        # Create registry directory if it doesn't exist
        os.makedirs(self.registry_path, exist_ok=True)

        # Data stores
        self.contributions: Dict[str, Contribution] = {}
        self.attributions: Dict[str, Attribution] = {}
        self.disbursements: Dict[str, Disbursement] = {}

        # Fund balance tracking
        self.total_value_received = Decimal("0.0")
        self.total_value_disbursed = Decimal("0.0")

        # Contributor tracking
        self.contributor_value_map: Dict[str, Decimal] = {}

        # Initialize the fund
        self._initialize_fund()

        logger.info(f"Common Attribution Fund initialized with ID {self.fund_id}")

    def _initialize_fund(self):
        """Initialize fund data structures and load existing data."""
        try:
            # Load existing data if available
            self._load_fund_data()
        except Exception as e:
            logger.warning(f"Could not load fund data: {e}. Starting with empty fund.")
            # Initialize empty data stores
            self._save_fund_data()

    def _load_fund_data(self):
        """Load fund data from registry files."""
        fund_file = os.path.join(self.registry_path, f"fund_{self.fund_id}.json")

        if os.path.exists(fund_file):
            with open(fund_file) as f:
                data = json.load(f)

            # Load fund metadata
            self.total_value_received = Decimal(
                str(data.get("total_value_received", "0.0"))
            )
            self.total_value_disbursed = Decimal(
                str(data.get("total_value_disbursed", "0.0"))
            )

            # Load contributions
            for contrib_data in data.get("contributions", []):
                contrib_data["timestamp"] = datetime.fromisoformat(
                    contrib_data["timestamp"]
                )
                contrib_data["contribution_type"] = ContributionType[
                    contrib_data["contribution_type"]
                ]
                contribution = Contribution(**contrib_data)
                self.contributions[contribution.id] = contribution

            # Load attributions
            for attr_data in data.get("attributions", []):
                attr_data["timestamp"] = datetime.fromisoformat(attr_data["timestamp"])
                attr_data["value_amount"] = Decimal(str(attr_data["value_amount"]))
                attribution = Attribution(**attr_data)
                self.attributions[attribution.id] = attribution

            # Load disbursements
            for disb_data in data.get("disbursements", []):
                disb_data["timestamp"] = datetime.fromisoformat(disb_data["timestamp"])
                disb_data["amount"] = Decimal(str(disb_data["amount"]))
                disbursement = Disbursement(**disb_data)
                self.disbursements[disbursement.id] = disbursement

            # Rebuild contributor value map
            self._rebuild_contributor_value_map()

            logger.info(
                f"Loaded fund data with {len(self.contributions)} contributions and {len(self.attributions)} attributions"
            )

    def _save_fund_data(self):
        """Save fund data to registry files."""
        fund_file = os.path.join(self.registry_path, f"fund_{self.fund_id}.json")

        # Prepare data for serialization
        data = {
            "fund_id": self.fund_id,
            "total_value_received": str(self.total_value_received),
            "total_value_disbursed": str(self.total_value_disbursed),
            "contributions": [],
            "attributions": [],
            "disbursements": [],
        }

        # Serialize contributions
        for contribution in self.contributions.values():
            contrib_dict = {
                "id": contribution.id,
                "contributor_id": contribution.contributor_id,
                "contribution_type": contribution.contribution_type.name,
                "timestamp": contribution.timestamp.isoformat(),
                "capsule_ids": contribution.capsule_ids,
                "weight": contribution.weight,
                "metadata": contribution.metadata,
            }
            if contribution.description:
                contrib_dict["description"] = contribution.description

            data["contributions"].append(contrib_dict)

        # Serialize attributions
        for attribution in self.attributions.values():
            attr_dict = {
                "id": attribution.id,
                "source_capsule_id": attribution.source_capsule_id,
                "contribution_ids": attribution.contribution_ids,
                "timestamp": attribution.timestamp.isoformat(),
                "value_amount": str(attribution.value_amount),
                "currency": attribution.currency,
                "metadata": attribution.metadata,
            }
            data["attributions"].append(attr_dict)

        # Serialize disbursements
        for disbursement in self.disbursements.values():
            disb_dict = {
                "id": disbursement.id,
                "recipient_id": disbursement.recipient_id,
                "attribution_ids": disbursement.attribution_ids,
                "timestamp": disbursement.timestamp.isoformat(),
                "amount": str(disbursement.amount),
                "currency": disbursement.currency,
                "status": disbursement.status,
                "metadata": disbursement.metadata,
            }
            if disbursement.transaction_reference:
                disb_dict["transaction_reference"] = disbursement.transaction_reference

            data["disbursements"].append(disb_dict)

        # Save to file
        with open(fund_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved fund data to {fund_file}")

    def _rebuild_contributor_value_map(self):
        """Rebuild the contributor value map from attributions and disbursements."""
        self.contributor_value_map = {}

        # Calculate allocated value by contribution
        contribution_value: Dict[str, Decimal] = {}
        for attribution in self.attributions.values():
            # Skip if already disbursed
            if any(
                attribution.id in d.attribution_ids
                for d in self.disbursements.values()
                if d.status == "processed"
            ):
                continue

            # Distribute value among contributions
            value_per_contribution = attribution.value_amount / len(
                attribution.contribution_ids
            )
            for contrib_id in attribution.contribution_ids:
                if contrib_id in contribution_value:
                    contribution_value[contrib_id] += value_per_contribution
                else:
                    contribution_value[contrib_id] = value_per_contribution

        # Map contribution value to contributors
        for contrib_id, value in contribution_value.items():
            if contrib_id in self.contributions:
                contributor_id = self.contributions[contrib_id].contributor_id
                if contributor_id in self.contributor_value_map:
                    self.contributor_value_map[contributor_id] += value
                else:
                    self.contributor_value_map[contributor_id] = value

    async def register_contribution(
        self,
        contributor_id: str,
        contribution_type: ContributionType,
        capsule_ids: List[str],
        weight: float = 1.0,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a contribution to the fund.

        Args:
            contributor_id: ID of the contributor
            contribution_type: Type of contribution
            capsule_ids: List of capsule IDs that constitute this contribution
            weight: Relative weight/importance of this contribution (default: 1.0)
            description: Optional description of the contribution
            metadata: Optional metadata about the contribution

        Returns:
            The ID of the new contribution record
        """
        contribution_id = str(uuid.uuid4())

        contribution = Contribution(
            id=contribution_id,
            contributor_id=contributor_id,
            contribution_type=contribution_type,
            timestamp=datetime.now(timezone.utc),
            capsule_ids=capsule_ids,
            weight=weight,
            metadata=metadata or {},
            description=description,
        )

        # Store the contribution
        self.contributions[contribution_id] = contribution

        # Save updated fund data
        self._save_fund_data()

        logger.info(f"Registered contribution {contribution_id} from {contributor_id}")
        return contribution_id

    async def attribute_value(
        self,
        source_capsule_id: str,
        contribution_ids: List[str],
        value_amount: Union[Decimal, float, str],
        currency: str = "USD",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Attribute economic value to a set of contributions.

        Args:
            source_capsule_id: ID of the capsule generating the value
            contribution_ids: List of contribution IDs that should receive attribution
            value_amount: The economic value to attribute
            currency: Currency code (default: USD)
            metadata: Optional metadata about this attribution

        Returns:
            The ID of the new attribution record
        """
        # Convert value_amount to Decimal if needed
        if isinstance(value_amount, float) or isinstance(value_amount, str):
            value_amount = Decimal(str(value_amount))

        # Validate the contributions exist
        missing_contributions = [
            cid for cid in contribution_ids if cid not in self.contributions
        ]
        if missing_contributions:
            raise ValueError(f"Contributions not found: {missing_contributions}")

        attribution_id = str(uuid.uuid4())

        attribution = Attribution(
            id=attribution_id,
            source_capsule_id=source_capsule_id,
            contribution_ids=contribution_ids,
            timestamp=datetime.now(timezone.utc),
            value_amount=value_amount,
            currency=currency,
            metadata=metadata or {},
        )

        # Store the attribution
        self.attributions[attribution_id] = attribution

        # Update fund balance
        self.total_value_received += value_amount

        # Update contributor value map
        self._rebuild_contributor_value_map()

        # Save updated fund data
        self._save_fund_data()

        logger.info(
            f"Attributed {value_amount} {currency} to {len(contribution_ids)} contributions"
        )
        return attribution_id

    async def calculate_disbursements(
        self, strategy: DistributionStrategy = DistributionStrategy.WEIGHTED
    ) -> Dict[str, Decimal]:
        """
        Calculate disbursements according to the specified strategy.

        Args:
            strategy: The distribution strategy to use

        Returns:
            A dictionary mapping contributor IDs to disbursement amounts
        """
        # Rebuild contributor value map to ensure it's current
        self._rebuild_contributor_value_map()

        disbursement_map: Dict[str, Decimal] = {}

        if strategy == DistributionStrategy.EQUAL:
            # Equal distribution among all contributors
            if self.contributor_value_map:
                equal_share = sum(self.contributor_value_map.values()) / len(
                    self.contributor_value_map
                )
                for contributor_id in self.contributor_value_map:
                    disbursement_map[contributor_id] = equal_share

        elif strategy == DistributionStrategy.WEIGHTED:
            # Use the current contributor value map as is
            disbursement_map = self.contributor_value_map.copy()

        elif strategy == DistributionStrategy.PROPORTIONAL:
            # Proportional to contributor's total contribution weight
            total_weight = Decimal("0.0")
            contributor_weights: Dict[str, Decimal] = {}

            # Calculate contributor weights
            for contrib in self.contributions.values():
                if contrib.contributor_id not in contributor_weights:
                    contributor_weights[contrib.contributor_id] = Decimal(
                        str(contrib.weight)
                    )
                else:
                    contributor_weights[contrib.contributor_id] += Decimal(
                        str(contrib.weight)
                    )
                total_weight += Decimal(str(contrib.weight))

            # Distribute based on weights
            total_value = sum(self.contributor_value_map.values())
            for contributor_id, weight in contributor_weights.items():
                if total_weight > 0:
                    proportion = weight / total_weight
                    disbursement_map[contributor_id] = total_value * proportion

        elif strategy == DistributionStrategy.MERIT_BASED:
            # Not implemented yet - requires peer review system
            # For now, fall back to weighted
            disbursement_map = self.contributor_value_map.copy()

        elif strategy == DistributionStrategy.CASCADE:
            # Cascade through attribution chain
            # Start with direct value mapping
            disbursement_map = self.contributor_value_map.copy()

            # Then cascade through ancestry
            # (This is a simplified implementation - a real one would follow capsule ancestry)
            for attribution in self.attributions.values():
                source_capsule_id = attribution.source_capsule_id
                # In a full implementation, we would traverse the capsule ancestry here

        return disbursement_map

    async def process_disbursements(
        self,
        disbursement_map: Dict[str, Decimal],
        currency: str = "USD",
        payment_processor: Any = None,
    ) -> List[str]:
        """
        Process disbursements to contributors.

        Args:
            disbursement_map: Mapping of contributor IDs to amounts
            currency: Currency code (default: USD)
            payment_processor: Optional payment processor to handle transactions

        Returns:
            List of disbursement IDs created
        """
        disbursement_ids = []

        # Group attributions by contributor
        contributor_attributions: Dict[str, List[str]] = {}

        # Find attributions that haven't been fully disbursed
        for attribution in self.attributions.values():
            # Skip if already fully disbursed
            if any(
                attribution.id in d.attribution_ids
                for d in self.disbursements.values()
                if d.status == "processed"
            ):
                continue

            # Group by contributors
            for contrib_id in attribution.contribution_ids:
                if contrib_id in self.contributions:
                    contributor_id = self.contributions[contrib_id].contributor_id
                    if contributor_id not in contributor_attributions:
                        contributor_attributions[contributor_id] = []
                    contributor_attributions[contributor_id].append(attribution.id)

        # Create disbursements
        for contributor_id, amount in disbursement_map.items():
            # Skip if no amount to disburse
            if amount <= 0:
                continue

            # Create disbursement record
            disbursement_id = str(uuid.uuid4())

            disbursement = Disbursement(
                id=disbursement_id,
                recipient_id=contributor_id,
                attribution_ids=contributor_attributions.get(contributor_id, []),
                timestamp=datetime.now(timezone.utc),
                amount=amount,
                currency=currency,
                status="pending",
                metadata={},
            )

            # Process payment if payment processor provided
            if payment_processor:
                try:
                    # Process payment (placeholder - would call payment processor in real impl)
                    transaction_id = f"tx-{uuid.uuid4()}"

                    # Update disbursement with transaction reference
                    disbursement.transaction_reference = transaction_id
                    disbursement.status = "processed"

                    # Update fund balance
                    self.total_value_disbursed += amount

                except Exception as e:
                    logger.error(f"Payment processing failed: {e}")
                    disbursement.status = "failed"
                    disbursement.metadata["error"] = str(e)

            # Store the disbursement
            self.disbursements[disbursement_id] = disbursement
            disbursement_ids.append(disbursement_id)

        # Update state after disbursements
        self._rebuild_contributor_value_map()

        # Save updated fund data
        self._save_fund_data()

        return disbursement_ids

    async def query_contributions(
        self, filters: Dict[str, Any] = None
    ) -> List[Contribution]:
        """
        Query contributions with optional filters.

        Args:
            filters: Dictionary of filter criteria

        Returns:
            List of matching contributions
        """
        results = []

        for contribution in self.contributions.values():
            # Apply filters if provided
            if filters:
                match = True

                # Filter by contributor_id
                if (
                    "contributor_id" in filters
                    and contribution.contributor_id != filters["contributor_id"]
                ):
                    match = False

                # Filter by contribution_type
                if "contribution_type" in filters:
                    filter_type = filters["contribution_type"]
                    if isinstance(filter_type, str):
                        filter_type = ContributionType[filter_type]
                    if contribution.contribution_type != filter_type:
                        match = False

                # Filter by capsule_id
                if (
                    "capsule_id" in filters
                    and filters["capsule_id"] not in contribution.capsule_ids
                ):
                    match = False

                # Filter by date range
                if "after" in filters:
                    after_date = filters["after"]
                    if isinstance(after_date, str):
                        after_date = datetime.fromisoformat(after_date)
                    if contribution.timestamp < after_date:
                        match = False

                if "before" in filters:
                    before_date = filters["before"]
                    if isinstance(before_date, str):
                        before_date = datetime.fromisoformat(before_date)
                    if contribution.timestamp > before_date:
                        match = False

                # Add to results if all filters match
                if match:
                    results.append(contribution)
            else:
                # No filters, include all
                results.append(contribution)

        return results

    async def query_attributions(
        self, filters: Dict[str, Any] = None
    ) -> List[Attribution]:
        """
        Query attributions with optional filters.

        Args:
            filters: Dictionary of filter criteria

        Returns:
            List of matching attributions
        """
        results = []

        for attribution in self.attributions.values():
            # Apply filters if provided
            if filters:
                match = True

                # Filter by source_capsule_id
                if (
                    "source_capsule_id" in filters
                    and attribution.source_capsule_id != filters["source_capsule_id"]
                ):
                    match = False

                # Filter by contribution_id
                if (
                    "contribution_id" in filters
                    and filters["contribution_id"] not in attribution.contribution_ids
                ):
                    match = False

                # Filter by min_value
                if "min_value" in filters and attribution.value_amount < Decimal(
                    str(filters["min_value"])
                ):
                    match = False

                # Filter by max_value
                if "max_value" in filters and attribution.value_amount > Decimal(
                    str(filters["max_value"])
                ):
                    match = False

                # Filter by currency
                if (
                    "currency" in filters
                    and attribution.currency != filters["currency"]
                ):
                    match = False

                # Filter by date range
                if "after" in filters:
                    after_date = filters["after"]
                    if isinstance(after_date, str):
                        after_date = datetime.fromisoformat(after_date)
                    if attribution.timestamp < after_date:
                        match = False

                if "before" in filters:
                    before_date = filters["before"]
                    if isinstance(before_date, str):
                        before_date = datetime.fromisoformat(before_date)
                    if attribution.timestamp > before_date:
                        match = False

                # Add to results if all filters match
                if match:
                    results.append(attribution)
            else:
                # No filters, include all
                results.append(attribution)

        return results

    async def get_contributor_balance(self, contributor_id: str) -> Decimal:
        """Get the current undisbursed balance for a contributor."""
        self._rebuild_contributor_value_map()
        return self.contributor_value_map.get(contributor_id, Decimal("0.0"))

    async def get_fund_stats(self) -> Dict[str, Any]:
        """Get statistics about the fund."""
        # Count active contributors (those with value to disburse)
        active_contributors = len(
            [cid for cid, val in self.contributor_value_map.items() if val > 0]
        )

        # Count contributions by type
        contributions_by_type = {}
        for contrib in self.contributions.values():
            contrib_type = contrib.contribution_type.name
            if contrib_type not in contributions_by_type:
                contributions_by_type[contrib_type] = 0
            contributions_by_type[contrib_type] += 1

        # Calculate remaining balance
        remaining_balance = self.total_value_received - self.total_value_disbursed

        return {
            "fund_id": self.fund_id,
            "total_value_received": str(self.total_value_received),
            "total_value_disbursed": str(self.total_value_disbursed),
            "remaining_balance": str(remaining_balance),
            "contribution_count": len(self.contributions),
            "attribution_count": len(self.attributions),
            "disbursement_count": len(self.disbursements),
            "active_contributors": active_contributors,
            "contributions_by_type": contributions_by_type,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    async def sync_with_federation(self) -> Dict[str, Any]:
        """
        Synchronize fund data with the federation.

        Returns:
            Dictionary with sync statistics
        """
        if not self.federated_registry:
            logger.warning(
                "No federated registry configured. Skipping federation sync."
            )
            return {"synced": False, "reason": "No federated registry configured"}

        try:
            # This would be implemented to exchange contribution and attribution
            # data with other federation members
            # For now, we just return a placeholder
            return {
                "synced": True,
                "contributions_sent": 0,
                "contributions_received": 0,
                "attributions_sent": 0,
                "attributions_received": 0,
            }
        except Exception as e:
            logger.error(f"Federation sync failed: {e}")
            return {"synced": False, "reason": str(e)}


async def demo_common_attribution_fund():
    """Demonstrate the Common Attribution Fund functionality."""
    # Create a temporary directory for the fund
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create the fund
        fund = CommonAttributionFund(fund_id="demo-fund", registry_path=tmpdir)

        print(f"Created Common Attribution Fund with ID: {fund.fund_id}")

        # Register some contributions
        alice_contrib = await fund.register_contribution(
            contributor_id="alice",
            contribution_type=ContributionType.DIRECT,
            capsule_ids=["capsule-1", "capsule-2"],
            weight=1.0,
            description="Original creative work",
        )

        bob_contrib = await fund.register_contribution(
            contributor_id="bob",
            contribution_type=ContributionType.DERIVATIVE,
            capsule_ids=["capsule-3"],
            weight=0.8,
            description="Derivative work based on Alice's content",
        )

        charlie_contrib = await fund.register_contribution(
            contributor_id="charlie",
            contribution_type=ContributionType.COLLECTIVE,
            capsule_ids=["capsule-4", "capsule-5"],
            weight=0.6,
            description="Editorial review and improvements",
        )

        print(
            f"Registered 3 contributions: {alice_contrib}, {bob_contrib}, {charlie_contrib}"
        )

        # Attribute value to these contributions
        attr1 = await fund.attribute_value(
            source_capsule_id="result-capsule-1",
            contribution_ids=[alice_contrib, bob_contrib],
            value_amount=Decimal("100.00"),
        )

        attr2 = await fund.attribute_value(
            source_capsule_id="result-capsule-2",
            contribution_ids=[alice_contrib, charlie_contrib],
            value_amount=Decimal("50.00"),
        )

        print(f"Created 2 attributions: {attr1}, {attr2}")

        # Calculate disbursements with different strategies
        print("\nCalculating disbursements with different strategies:")

        equal_disbursements = await fund.calculate_disbursements(
            DistributionStrategy.EQUAL
        )
        print(f"Equal: {equal_disbursements}")

        weighted_disbursements = await fund.calculate_disbursements(
            DistributionStrategy.WEIGHTED
        )
        print(f"Weighted: {weighted_disbursements}")

        proportional_disbursements = await fund.calculate_disbursements(
            DistributionStrategy.PROPORTIONAL
        )
        print(f"Proportional: {proportional_disbursements}")

        # Process disbursements
        disbursement_ids = await fund.process_disbursements(weighted_disbursements)
        print(f"\nProcessed {len(disbursement_ids)} disbursements")

        # Get fund statistics
        stats = await fund.get_fund_stats()
        print("\nFund statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    import asyncio

    # Run the demo
    asyncio.run(demo_common_attribution_fund())
