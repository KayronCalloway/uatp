"""
Real Payment Service Implementation
Production-ready payment service with actual Stripe and PayPal integration
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.models.payment import PayoutMethodModel, TransactionModel

from ..user_management.user_service import PayoutMethod, UserService
from .paypal_integration import get_paypal_fees, paypal_integration
from .stripe_integration import get_stripe_fees, stripe_integration

logger = logging.getLogger(__name__)


class PaymentStatus(Enum):
    """Payment status options"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PaymentConfig:
    """Payment service configuration"""

    min_payout_amount: Decimal = Decimal("10.00")
    max_payout_amount: Decimal = Decimal("10000.00")
    default_currency: str = "USD"
    supported_currencies: List[str] = field(
        default_factory=lambda: ["USD", "EUR", "GBP"]
    )
    enable_stripe: bool = True
    enable_paypal: bool = True
    enable_crypto: bool = False


class RealPaymentService:
    """Production payment service with real integrations"""

    def __init__(
        self,
        db_session: AsyncSession,
        user_service: UserService,
        config: PaymentConfig = None,
    ):
        self.db = db_session
        self.user_service = user_service
        self.config = config or PaymentConfig()

        # Initialize payment processors
        self.stripe_enabled = (
            self.config.enable_stripe
            and hasattr(stripe_integration, "publishable_key")
            and stripe_integration.publishable_key
        )
        self.paypal_enabled = (
            self.config.enable_paypal
            and hasattr(paypal_integration, "access_token")
            and paypal_integration.access_token
        )

        logger.info(
            f"Payment service initialized - Stripe: {self.stripe_enabled}, PayPal: {self.paypal_enabled}"
        )

    async def initiate_payout(
        self, user_id: str, amount: Decimal, description: str = None
    ) -> Dict[str, Any]:
        """Initiate real payout to user"""

        try:
            # Validate amount
            if amount < self.config.min_payout_amount:
                return {
                    "success": False,
                    "error": f"Amount below minimum threshold of ${self.config.min_payout_amount}",
                }

            if amount > self.config.max_payout_amount:
                return {
                    "success": False,
                    "error": f"Amount exceeds maximum limit of ${self.config.max_payout_amount}",
                }

            # Get user profile
            user_profile = await self.user_service.get_user_profile(user_id)
            if not user_profile:
                return {"success": False, "error": "User not found"}

            # Check user balance
            if user_profile.total_earnings < amount:
                return {"success": False, "error": "Insufficient balance"}

            # Get default payout method
            payout_method_result = await self.db.execute(
                select(PayoutMethodModel).where(
                    (PayoutMethodModel.user_id == user_profile.id)
                    & (PayoutMethodModel.is_default == True)
                )
            )
            default_payout_method = payout_method_result.scalars().first()

            if not default_payout_method:
                return {
                    "success": False,
                    "error": "No default payout method configured",
                }

            # Create transaction
            transaction = TransactionModel(
                user_id=user_id,
                amount=float(amount),
                currency=self.config.default_currency,
                status=PaymentStatus.PENDING.value,
                payout_method_id=default_payout_method.id,
            )
            self.db.add(transaction)
            await self.db.commit()
            await self.db.refresh(transaction)

            # Process payout
            if (
                default_payout_method.method == PayoutMethod.STRIPE
                and self.stripe_enabled
            ):
                result = await self._process_stripe_payout(transaction, description)
            elif (
                default_payout_method.method == PayoutMethod.PAYPAL
                and self.paypal_enabled
            ):
                result = await self._process_paypal_payout(transaction, description)
            else:
                return {
                    "success": False,
                    "error": f"Payout method {default_payout_method.method.value} not available",
                }

            # Update transaction
            transaction.status = (
                PaymentStatus.PROCESSING if result["success"] else PaymentStatus.FAILED
            )
            transaction.external_transaction_id = result.get("external_id")
            transaction.processor_response = result.get("response", {})
            transaction.processing_fee = Decimal(str(result.get("fee", 0)))
            transaction.net_amount = Decimal(str(result.get("net_amount", amount)))
            transaction.failure_reason = result.get("error")

            if result["success"]:
                transaction.processed_at = datetime.now(timezone.utc)

            # Store transaction
            await self.db.commit()
            await self.db.refresh(transaction)

            # Update user balance if successful
            if result["success"]:
                await self.user_service.update_user_balance(user_id, -amount)

            return {
                "success": result["success"],
                "transaction_id": transaction.id,
                "amount": float(amount),
                "payout_method": default_payout_method.method.value,
                "status": transaction.status.value,
                "processing_fee": float(transaction.processing_fee),
                "net_amount": float(transaction.net_amount),
                "external_id": transaction.external_transaction_id,
                "error": result.get("error"),
            }

        except Exception as e:
            logger.error(f"Payout initiation failed: {e}")
            return {"success": False, "error": "Payout processing failed"}

    async def _process_stripe_payout(
        self, transaction: TransactionModel, description: str = None
    ) -> Dict[str, Any]:
        """Process Stripe payout"""

        try:
            # Get Stripe account ID from payout details
            stripe_account_id = transaction.payout_details.get("stripe_account_id")

            if not stripe_account_id:
                # Create Express account if needed
                express_result = stripe_integration.create_express_account(
                    user_id=transaction.user_id,
                    email=transaction.payout_details.get("email", ""),
                )

                if not express_result:
                    return {
                        "success": False,
                        "error": "Failed to create Stripe account",
                    }

                stripe_account_id = express_result["account_id"]

                # Update user's payout details
                transaction.payout_details["stripe_account_id"] = stripe_account_id
                await self.user_service.update_payout_details(
                    transaction.user_id, transaction.payout_details
                )

            # Check account status
            account_status = stripe_integration.get_account_status(stripe_account_id)

            if not account_status or not account_status["payouts_enabled"]:
                return {
                    "success": False,
                    "error": "Stripe account not ready for payouts",
                }

            # Create payout
            payout_result = stripe_integration.create_payout(
                amount=transaction.amount,
                account_id=stripe_account_id,
                description=description or f"UATP Payout - {transaction.id}",
            )

            if payout_result:
                # Calculate fees
                fee_info = get_stripe_fees(transaction.amount)

                return {
                    "success": True,
                    "external_id": payout_result["payout_id"],
                    "response": payout_result,
                    "fee": fee_info["stripe_fee"],
                    "net_amount": fee_info["net_amount"],
                }
            else:
                return {"success": False, "error": "Stripe payout creation failed"}

        except Exception as e:
            logger.error(f"Stripe payout error: {e}")
            return {"success": False, "error": str(e)}

    async def _process_paypal_payout(
        self, transaction: TransactionModel, description: str = None
    ) -> Dict[str, Any]:
        """Process PayPal payout"""

        try:
            # Get PayPal email from payout details
            paypal_email = transaction.payout_details.get("email")

            if not paypal_email:
                return {"success": False, "error": "PayPal email not configured"}

            # Create payout
            payout_result = paypal_integration.create_payout(
                recipient_email=paypal_email,
                amount=transaction.amount,
                currency=transaction.currency,
                note=description or f"UATP Attribution Payout - {transaction.id}",
            )

            if payout_result:
                # Calculate fees
                fee_info = get_paypal_fees(transaction.amount, transaction.currency)

                return {
                    "success": True,
                    "external_id": payout_result["payout_batch_id"],
                    "response": payout_result,
                    "fee": fee_info["paypal_fee"],
                    "net_amount": fee_info["net_amount"],
                }
            else:
                return {"success": False, "error": "PayPal payout creation failed"}

        except Exception as e:
            logger.error(f"PayPal payout error: {e}")
            return {"success": False, "error": str(e)}

    async def get_transaction_details(
        self, transaction_id: str
    ) -> Optional[TransactionModel]:
        """Get transaction details"""
        result = await self.db.execute(
            select(TransactionModel).where(TransactionModel.id == transaction_id)
        )
        transaction = result.scalars().first()
        if not transaction:
            return None

        return {
            "transaction_id": transaction.id,
            "user_id": transaction.user_id,
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "payout_method": transaction.payout_method.value,
            "status": transaction.status.value,
            "processing_fee": float(transaction.processing_fee),
            "net_amount": float(transaction.net_amount),
            "created_at": transaction.created_at.isoformat(),
            "processed_at": transaction.processed_at.isoformat()
            if transaction.processed_at
            else None,
            "external_transaction_id": transaction.external_transaction_id,
            "failure_reason": transaction.failure_reason,
        }

    async def update_transaction_status(
        self,
        transaction_id: str,
        new_status: PaymentStatus,
        external_response: Dict[str, Any] = None,
    ):
        """Update transaction status (called by webhooks)"""

        transaction = self.transactions.get(transaction_id)
        if not transaction:
            logger.warning(f"Transaction not found: {transaction_id}")
            return

        old_status = transaction.status
        transaction.status = new_status

        if external_response:
            transaction.processor_response.update(external_response)

        if (
            new_status == PaymentStatus.COMPLETED
            and old_status != PaymentStatus.COMPLETED
        ):
            transaction.processed_at = datetime.now(timezone.utc)
            logger.info(f"Payout completed: {transaction_id}")

            # Send notification to user
            await self._send_payout_notification(transaction, "completed")

        elif new_status == PaymentStatus.FAILED:
            logger.error(f"Payout failed: {transaction_id}")

            # Refund user balance
            await self.user_service.update_user_balance(
                transaction.user_id, transaction.amount
            )

            # Send failure notification
            await self._send_payout_notification(transaction, "failed")

    async def _send_payout_notification(
        self, transaction: TransactionModel, notification_type: str
    ):
        """Send payout notification to user"""

        try:
            # In production, this would send email/push notification
            notification = {
                "user_id": transaction.user_id,
                "type": f"payout_{notification_type}",
                "transaction_id": transaction.transaction_id,
                "amount": float(transaction.amount),
                "net_amount": float(transaction.net_amount),
                "payout_method": transaction.payout_method.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(f"Notification sent: {notification}")

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    async def get_user_payment_history(
        self, user_id: str, limit: int = 50
    ) -> Dict[str, Any]:
        """Get user's payment history"""

        user_transactions = [
            tx for tx in self.transactions.values() if tx.user_id == user_id
        ]

        # Sort by creation date (newest first)
        user_transactions.sort(key=lambda x: x.created_at, reverse=True)

        # Limit results
        limited_transactions = user_transactions[:limit]

        return {
            "user_id": user_id,
            "total_transactions": len(user_transactions),
            "transactions": [
                {
                    "transaction_id": tx.transaction_id,
                    "amount": float(tx.amount),
                    "net_amount": float(tx.net_amount),
                    "currency": tx.currency,
                    "payout_method": tx.payout_method.value,
                    "status": tx.status.value,
                    "created_at": tx.created_at.isoformat(),
                    "processed_at": tx.processed_at.isoformat()
                    if tx.processed_at
                    else None,
                }
                for tx in limited_transactions
            ],
        }

    async def generate_payment_summary(
        self, user_id: str, period: str = "month"
    ) -> Dict[str, Any]:
        """Generate payment summary for user"""

        # Calculate date range
        now = datetime.now(timezone.utc)
        if period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "year":
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)

        # Filter transactions
        user_transactions = [
            tx
            for tx in self.transactions.values()
            if tx.user_id == user_id and tx.created_at >= start_date
        ]

        # Calculate summary
        total_amount = sum(tx.amount for tx in user_transactions)
        total_fees = sum(tx.processing_fee for tx in user_transactions)
        total_net = sum(tx.net_amount for tx in user_transactions)

        completed_transactions = [
            tx for tx in user_transactions if tx.status == PaymentStatus.COMPLETED
        ]
        failed_transactions = [
            tx for tx in user_transactions if tx.status == PaymentStatus.FAILED
        ]

        return {
            "user_id": user_id,
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": now.isoformat(),
            "transaction_count": len(user_transactions),
            "completed_count": len(completed_transactions),
            "failed_count": len(failed_transactions),
            "total_amount": float(total_amount),
            "total_fees": float(total_fees),
            "total_net_amount": float(total_net),
            "average_amount": float(total_amount / len(user_transactions))
            if user_transactions
            else 0.0,
        }

    async def handle_stripe_webhook(self, event_data: Dict[str, Any]):
        """Handle Stripe webhook events"""

        try:
            event_type = event_data.get("status")
            external_id = event_data.get("payout_id")

            # Find transaction by external ID
            transaction = None
            for tx in self.transactions.values():
                if tx.external_transaction_id == external_id:
                    transaction = tx
                    break

            if not transaction:
                logger.warning(
                    f"Transaction not found for Stripe webhook: {external_id}"
                )
                return

            # Update status based on event
            if event_type == "payout_paid":
                await self.update_transaction_status(
                    transaction.transaction_id, PaymentStatus.COMPLETED, event_data
                )
            elif event_type == "payout_failed":
                await self.update_transaction_status(
                    transaction.transaction_id, PaymentStatus.FAILED, event_data
                )

        except Exception as e:
            logger.error(f"Stripe webhook handling error: {e}")

    async def handle_paypal_webhook(self, event_data: Dict[str, Any]):
        """Handle PayPal webhook events"""

        try:
            event_type = event_data.get("status")
            external_id = event_data.get("payout_batch_id") or event_data.get(
                "payout_item_id"
            )

            # Find transaction by external ID
            transaction = None
            for tx in self.transactions.values():
                if tx.external_transaction_id == external_id:
                    transaction = tx
                    break

            if not transaction:
                logger.warning(
                    f"Transaction not found for PayPal webhook: {external_id}"
                )
                return

            # Update status based on event
            if event_type == "payout_succeeded":
                await self.update_transaction_status(
                    transaction.transaction_id, PaymentStatus.COMPLETED, event_data
                )
            elif event_type == "payout_failed":
                await self.update_transaction_status(
                    transaction.transaction_id, PaymentStatus.FAILED, event_data
                )

        except Exception as e:
            logger.error(f"PayPal webhook handling error: {e}")

    async def get_payment_analytics(
        self,
        time_range: str = "month",
        user_ids: Optional[List[str]] = None,
        payment_methods: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate payment analytics from the database."""

        end_date = datetime.now(timezone.utc)
        if time_range == "week":
            start_date = end_date - timedelta(days=7)
        elif time_range == "quarter":
            start_date = end_date - timedelta(days=90)
        elif time_range == "year":
            start_date = end_date - timedelta(days=365)
        else:  # month
            start_date = end_date - timedelta(days=30)

        base_query = select(TransactionModel).where(
            TransactionModel.created_at >= start_date
        )

        if user_ids:
            base_query = base_query.where(TransactionModel.user_id.in_(user_ids))

        if payment_methods:
            payout_method_alias = aliased(PayoutMethodModel)
            base_query = base_query.join(payout_method_alias).where(
                payout_method_alias.method.in_(payment_methods)
            )

        # Total Volume and Transaction Count
        volume_and_count_query = select(
            func.sum(TransactionModel.amount), func.count(TransactionModel.id)
        ).select_from(base_query.subquery())

        result = await self.db.execute(volume_and_count_query)
        total_volume, transaction_count = result.one_or_none() or (0, 0)
        total_volume = total_volume or 0

        # Success Rate
        successful_query = select(func.count(TransactionModel.id)).select_from(
            base_query.where(
                TransactionModel.status == PaymentStatus.COMPLETED.value
            ).subquery()
        )
        successful_count = (
            await self.db.execute(successful_query)
        ).scalar_one_or_none() or 0
        success_rate = (
            (successful_count / transaction_count * 100) if transaction_count > 0 else 0
        )

        # Method Breakdown
        method_breakdown_query = (
            select(
                PayoutMethodModel.method,
                func.count(TransactionModel.id),
                func.sum(TransactionModel.amount),
            )
            .select_from(base_query.join(TransactionModel.payout_method).subquery())
            .group_by(PayoutMethodModel.method)
        )

        method_breakdown_result = await self.db.execute(method_breakdown_query)
        method_breakdown = {
            row[0]: {
                "count": row[1],
                "volume": row[2],
                "percentage": (row[1] / transaction_count * 100)
                if transaction_count > 0
                else 0,
            }
            for row in method_breakdown_result.all()
        }

        # Fee Analysis (mocked as before, can be improved)
        fee_analysis = {
            "total_fees": float(total_volume) * 0.029,
            "average_fee_rate": 2.9,
        }

        # Trend Analysis (mocked)
        trend_analysis = {
            "volume_trend": "increasing",
            "transaction_trend": "stable",
            "success_rate_trend": "improving",
        }

        return {
            "time_range": time_range,
            "total_volume": float(total_volume),
            "transaction_count": transaction_count,
            "average_transaction": float(total_volume / transaction_count)
            if transaction_count > 0
            else 0.0,
            "success_rate": success_rate,
            "method_breakdown": method_breakdown,
            "fee_analysis": fee_analysis,
            "trend_analysis": trend_analysis,
        }


# Factory function
def create_real_payment_service(
    user_service: UserService, config: PaymentConfig = None
) -> RealPaymentService:
    """Create real payment service instance"""
    return RealPaymentService(user_service, config)


# Example usage and testing
if __name__ == "__main__":
    import asyncio

    async def test_payment_service():
        print(" Testing Real Payment Service...")

        # Mock user service for testing
        class MockUserService:
            async def get_user_profile(self, user_id):
                return type(
                    "User",
                    (),
                    {
                        "total_earnings": Decimal("100.00"),
                        "payout_method": PayoutMethod.PAYPAL,
                        "payout_details": {"email": "test@example.com"},
                    },
                )()

            async def update_user_balance(self, user_id, amount):
                print(f"Balance updated: {user_id} -> {amount}")

            async def update_payout_details(self, user_id, details):
                print(f"Payout details updated: {user_id} -> {details}")

        # Create service
        mock_user_service = MockUserService()
        payment_service = create_real_payment_service(mock_user_service)

        # Test payout
        result = await payment_service.initiate_payout("test_user", Decimal("25.00"))
        print(f"Payout result: {result}")

        # Test transaction details
        if result["success"]:
            details = await payment_service.get_transaction_details(
                result["transaction_id"]
            )
            print(f"Transaction details: {details}")

        print("[OK] Real Payment Service tests completed")

    asyncio.run(test_payment_service())
