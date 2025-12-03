"""
Micropayment Integration for UATP Capsule Engine.

This module provides the infrastructure for handling micropayments, integrating
with various payment providers, and automating disbursements from the Common
Attribution Fund.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum, auto
from typing import Any, Dict, Optional

from src.integrations.economic.common_attribution_fund import (
    CommonAttributionFund,
    Disbursement,
)

logger = logging.getLogger(__name__)


class PaymentStatus(Enum):
    """Status of a payment transaction."""

    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELED = auto()


@dataclass
class PaymentTransaction:
    """Represents a single payment transaction."""

    id: str
    provider_id: str
    disbursement_id: str
    amount: Decimal
    currency: str
    recipient_address: str
    status: PaymentStatus = PaymentStatus.PENDING
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    provider_transaction_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class PaymentProvider(ABC):
    """Abstract base class for payment provider integrations."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for the payment provider."""
        pass

    @abstractmethod
    async def process_payment(
        self, transaction: PaymentTransaction
    ) -> PaymentTransaction:
        """Process a payment transaction."""
        pass

    @abstractmethod
    async def get_transaction_status(
        self, provider_transaction_id: str
    ) -> PaymentStatus:
        """Get the status of a transaction from the provider."""
        pass

    @abstractmethod
    async def get_balance(self, currency: str) -> Decimal:
        """Get the account balance for a specific currency."""
        pass


class MockPaymentProvider(PaymentProvider):
    """A mock payment provider for testing and development."""

    @property
    def provider_id(self) -> str:
        return "mock_provider"

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self._balance = {"USD": Decimal("10000.00")}
        self._transactions: Dict[str, PaymentTransaction] = {}

    async def process_payment(
        self, transaction: PaymentTransaction
    ) -> PaymentTransaction:
        logger.info(
            f"[Mock] Processing payment {transaction.id} for {transaction.amount} {transaction.currency}"
        )
        if transaction.amount > self._balance.get(transaction.currency, Decimal("0.0")):
            transaction.status = PaymentStatus.FAILED
            transaction.error_message = "Insufficient funds"
        else:
            self._balance[transaction.currency] -= transaction.amount
            transaction.status = PaymentStatus.COMPLETED
            transaction.provider_transaction_id = f"mock_tx_{uuid.uuid4().hex}"
        self._transactions[transaction.provider_transaction_id] = transaction
        return transaction

    async def get_transaction_status(
        self, provider_transaction_id: str
    ) -> PaymentStatus:
        if provider_transaction_id in self._transactions:
            return self._transactions[provider_transaction_id].status
        return PaymentStatus.FAILED

    async def get_balance(self, currency: str) -> Decimal:
        return self._balance.get(currency, Decimal("0.0"))


class MicropaymentProcessor:
    """
    Handles micropayments by integrating with payment providers and the CAF.
    """

    def __init__(self, attribution_fund: CommonAttributionFund):
        self.attribution_fund = attribution_fund
        self.providers: Dict[str, PaymentProvider] = {}
        self.transactions: Dict[str, PaymentTransaction] = {}

    async def register_provider(self, provider: PaymentProvider):
        """Register a new payment provider."""
        if provider.provider_id in self.providers:
            logger.warning(f"Provider {provider.provider_id} is already registered.")
            return
        self.providers[provider.provider_id] = provider
        logger.info(f"Payment provider {provider.provider_id} registered.")

    async def process_disbursement(
        self, disbursement: Disbursement, provider_id: str, recipient_address: str
    ) -> PaymentTransaction:
        """
        Process a single disbursement from the Common Attribution Fund.
        """
        if provider_id not in self.providers:
            raise ValueError(f"Provider {provider_id} not registered.")

        provider = self.providers[provider_id]

        transaction = PaymentTransaction(
            id=str(uuid.uuid4()),
            provider_id=provider.provider_id,
            disbursement_id=disbursement.id,
            amount=disbursement.amount,
            currency=disbursement.currency,
            recipient_address=recipient_address,
        )

        try:
            processed_tx = await provider.process_payment(transaction)
            self.transactions[processed_tx.id] = processed_tx

            # Update the disbursement status in the attribution fund
            disbursement.status = (
                "processing"
                if processed_tx.status
                in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]
                else processed_tx.status.name.lower()
            )
            disbursement.transaction_reference = processed_tx.id
            if processed_tx.status == PaymentStatus.FAILED:
                disbursement.metadata["error"] = processed_tx.error_message

            self.attribution_fund.disbursements[disbursement.id] = disbursement
            self.attribution_fund._save_fund_data()

            return processed_tx
        except Exception as e:
            logger.error(
                f"Error processing payment for disbursement {disbursement.id}: {e}"
            )
            transaction.status = PaymentStatus.FAILED
            transaction.error_message = str(e)
            self.transactions[transaction.id] = transaction
            return transaction

    async def process_all_pending_disbursements(self, provider_map: Dict[str, str]):
        """
        Process all pending disbursements in the attribution fund.

        Args:
            provider_map: A dictionary mapping contributor IDs to their preferred provider and address.
                          Example: {"user-alice": ("mock_provider", "alice_wallet_address")}
        """
        pending_disbursements = [
            d
            for d in self.attribution_fund.disbursements.values()
            if d.status == "pending"
        ]

        for disbursement in pending_disbursements:
            recipient_id = disbursement.recipient_id
            if recipient_id in provider_map:
                provider_id, recipient_address = provider_map[recipient_id]
                if provider_id in self.providers:
                    await self.process_disbursement(
                        disbursement, provider_id, recipient_address
                    )
                else:
                    logger.warning(
                        f"Provider {provider_id} for {recipient_id} not available."
                    )
            else:
                logger.warning(
                    f"No payment provider mapping for recipient {recipient_id}. Skipping disbursement."
                )


async def demo_micropayment_integration():
    """Demonstrate the micropayment integration functionality."""
    import tempfile

    from src.integrations.economic.common_attribution_fund import ContributionType

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Set up the Common Attribution Fund
        fund = CommonAttributionFund(fund_id="micropayment-demo", registry_path=tmpdir)
        contrib_id = await fund.register_contribution(
            contributor_id="user-alice",
            contribution_type=ContributionType.DIRECT,
            capsule_ids=["capsule-abc"],
        )
        await fund.attribute_value(
            source_capsule_id="capsule-xyz",
            contribution_ids=[contrib_id],
            value_amount="0.05",
        )
        disbursement_map = await fund.calculate_disbursements()
        await fund.process_disbursements(disbursement_map)

        # 2. Set up the Micropayment Processor
        processor = MicropaymentProcessor(attribution_fund=fund)
        mock_provider = MockPaymentProvider()
        await processor.register_provider(mock_provider)

        print(
            f"Initial mock provider balance: {await mock_provider.get_balance('USD')} USD"
        )

        # 3. Process pending disbursements
        provider_map = {"user-alice": ("mock_provider", "alice_wallet_address")}
        await processor.process_all_pending_disbursements(provider_map)

        # 4. Verify results
        print("\n--- Verification ---")
        for tx in processor.transactions.values():
            print(
                f"Transaction {tx.id}: Status={tx.status.name}, Amount={tx.amount} {tx.currency}"
            )

        final_balance = await mock_provider.get_balance("USD")
        print(f"Final mock provider balance: {final_balance} USD")

        alice_balance = await fund.get_contributor_balance("user-alice")
        print(f"Alice's remaining balance in fund: {alice_balance} USD")

        disbursement = list(fund.disbursements.values())[0]
        print(f"Disbursement {disbursement.id} status: {disbursement.status}")


if __name__ == "__main__":
    asyncio.run(demo_micropayment_integration())
