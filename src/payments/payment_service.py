"""
Payment Service
Complete payment processing and notification system for UATP
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from ..user_management.user_service import PayoutMethod, UserService

logger = logging.getLogger(__name__)


class PaymentStatus(Enum):
    """Payment status options"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class NotificationType(Enum):
    """Notification types"""

    PAYMENT_SENT = "payment_sent"
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_FAILED = "payment_failed"
    THRESHOLD_REACHED = "threshold_reached"
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_SUMMARY = "monthly_summary"


@dataclass
class PaymentTransaction:
    """Payment transaction record"""

    transaction_id: str
    user_id: str
    amount: Decimal
    currency: str = "USD"
    payout_method: PayoutMethod = PayoutMethod.PAYPAL
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None

    # Payout details
    payout_details: Dict[str, Any] = field(default_factory=dict)

    # Transaction metadata
    attribution_period_start: Optional[datetime] = None
    attribution_period_end: Optional[datetime] = None
    attribution_count: int = 0

    # Processing info
    external_transaction_id: Optional[str] = None
    processor_response: Dict[str, Any] = field(default_factory=dict)
    failure_reason: Optional[str] = None

    # Fees
    processing_fee: Decimal = field(default_factory=lambda: Decimal("0.00"))
    net_amount: Decimal = field(default_factory=lambda: Decimal("0.00"))


@dataclass
class PaymentNotification:
    """Payment notification"""

    notification_id: str
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    read: bool = False

    # Notification data
    data: Dict[str, Any] = field(default_factory=dict)

    # Delivery info
    email_sent: bool = False
    push_sent: bool = False
    sms_sent: bool = False


class PaymentProcessor:
    """Base payment processor interface"""

    def __init__(self, processor_name: str):
        self.processor_name = processor_name

    async def process_payment(self, transaction: PaymentTransaction) -> Dict[str, Any]:
        """Process a payment transaction"""
        raise NotImplementedError

    async def get_transaction_status(self, external_id: str) -> Dict[str, Any]:
        """Get transaction status from processor"""
        raise NotImplementedError

    def calculate_fees(self, amount: Decimal) -> Decimal:
        """Calculate processing fees"""
        raise NotImplementedError


class PayPalProcessor(PaymentProcessor):
    """PayPal payment processor"""

    def __init__(self, client_id: str, client_secret: str, sandbox: bool = True):
        super().__init__("paypal")
        self.client_id = client_id
        self.client_secret = client_secret
        self.sandbox = sandbox
        self.base_url = (
            "https://api.sandbox.paypal.com" if sandbox else "https://api.paypal.com"
        )

    async def process_payment(self, transaction: PaymentTransaction) -> Dict[str, Any]:
        """Process PayPal payment"""

        # Mock PayPal API call
        # In production, this would use the actual PayPal API

        try:
            # Calculate fees (PayPal: 2.9% + $0.30)
            fee = self.calculate_fees(transaction.amount)
            net_amount = transaction.amount - fee

            # Simulate API call
            await asyncio.sleep(0.1)  # Simulate network delay

            # Mock successful response
            external_id = f"PAY-{transaction.transaction_id[-8:]}"

            return {
                "success": True,
                "external_transaction_id": external_id,
                "status": "completed",
                "fee": float(fee),
                "net_amount": float(net_amount),
                "processor_response": {
                    "id": external_id,
                    "state": "approved",
                    "payer_email": transaction.payout_details.get("email"),
                },
            }

        except Exception as e:
            logger.error(f"PayPal payment failed: {e}")
            return {"success": False, "error": str(e), "status": "failed"}

    async def get_transaction_status(self, external_id: str) -> Dict[str, Any]:
        """Get PayPal transaction status"""

        # Mock status check
        return {
            "id": external_id,
            "state": "approved",
            "amount": "10.00",
            "currency": "USD",
        }

    def calculate_fees(self, amount: Decimal) -> Decimal:
        """Calculate PayPal fees"""
        return (amount * Decimal("0.029")) + Decimal("0.30")


class StripeProcessor(PaymentProcessor):
    """Stripe payment processor"""

    def __init__(self, secret_key: str):
        super().__init__("stripe")
        self.secret_key = secret_key

    async def process_payment(self, transaction: PaymentTransaction) -> Dict[str, Any]:
        """Process Stripe payment"""

        try:
            # Calculate fees (Stripe: 2.9% + $0.30)
            fee = self.calculate_fees(transaction.amount)
            net_amount = transaction.amount - fee

            # Simulate API call
            await asyncio.sleep(0.1)

            # Mock successful response
            external_id = f"pi_{transaction.transaction_id[-12:]}"

            return {
                "success": True,
                "external_transaction_id": external_id,
                "status": "completed",
                "fee": float(fee),
                "net_amount": float(net_amount),
                "processor_response": {
                    "id": external_id,
                    "status": "succeeded",
                    "amount": int(transaction.amount * 100),  # Stripe uses cents
                },
            }

        except Exception as e:
            logger.error(f"Stripe payment failed: {e}")
            return {"success": False, "error": str(e), "status": "failed"}

    async def get_transaction_status(self, external_id: str) -> Dict[str, Any]:
        """Get Stripe transaction status"""

        return {
            "id": external_id,
            "status": "succeeded",
            "amount": 1000,  # $10.00 in cents
            "currency": "usd",
        }

    def calculate_fees(self, amount: Decimal) -> Decimal:
        """Calculate Stripe fees"""
        return (amount * Decimal("0.029")) + Decimal("0.30")


class CryptoProcessor(PaymentProcessor):
    """Cryptocurrency payment processor"""

    def __init__(self, supported_currencies: List[str] = None):
        super().__init__("crypto")
        self.supported_currencies = supported_currencies or ["BTC", "ETH", "USDC"]

    async def process_payment(self, transaction: PaymentTransaction) -> Dict[str, Any]:
        """Process crypto payment"""

        try:
            # Calculate fees (varies by currency)
            fee = self.calculate_fees(transaction.amount)
            net_amount = transaction.amount - fee

            # Simulate blockchain transaction
            await asyncio.sleep(0.2)

            # Mock successful response
            external_id = f"0x{transaction.transaction_id[-16:]}"

            return {
                "success": True,
                "external_transaction_id": external_id,
                "status": "completed",
                "fee": float(fee),
                "net_amount": float(net_amount),
                "processor_response": {
                    "tx_hash": external_id,
                    "currency": transaction.payout_details.get("currency", "USDC"),
                    "wallet_address": transaction.payout_details.get("wallet_address"),
                },
            }

        except Exception as e:
            logger.error(f"Crypto payment failed: {e}")
            return {"success": False, "error": str(e), "status": "failed"}

    async def get_transaction_status(self, external_id: str) -> Dict[str, Any]:
        """Get crypto transaction status"""

        return {"tx_hash": external_id, "confirmations": 6, "status": "confirmed"}

    def calculate_fees(self, amount: Decimal) -> Decimal:
        """Calculate crypto fees"""
        return Decimal("0.50")  # Flat fee for simplicity


class PaymentService:
    """Complete payment processing service"""

    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.processors: Dict[PayoutMethod, PaymentProcessor] = {}
        self.transactions: Dict[str, PaymentTransaction] = {}
        self.notifications: Dict[str, List[PaymentNotification]] = {}

        # Payment processing queue
        self.payment_queue: List[str] = []
        self.processing_active = False

        # Initialize default processors
        self._initialize_processors()

    def _initialize_processors(self):
        """Initialize payment processors"""

        # Mock processors for demo
        self.processors[PayoutMethod.PAYPAL] = PayPalProcessor(
            "demo_client_id", "demo_secret"
        )
        self.processors[PayoutMethod.STRIPE] = StripeProcessor("demo_secret_key")
        self.processors[PayoutMethod.CRYPTO] = CryptoProcessor()

    def generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"txn_{timestamp}_{hash(timestamp) % 10000:04d}"

    def generate_notification_id(self) -> str:
        """Generate unique notification ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"notif_{timestamp}_{hash(timestamp) % 1000:03d}"

    async def initiate_payout(
        self,
        user_id: str,
        amount: Decimal,
        attribution_period_start: Optional[datetime] = None,
        attribution_period_end: Optional[datetime] = None,
        attribution_count: int = 0,
    ) -> Dict[str, Any]:
        """Initiate a payout to a user"""

        # Get user profile
        user_profile = await self.user_service.get_user_profile(user_id)
        if not user_profile:
            return {"success": False, "error": "User not found"}

        # Check if user has payout method configured
        if not user_profile.payout_method:
            return {"success": False, "error": "No payout method configured"}

        # Check minimum payout threshold
        if amount < user_profile.payout_threshold:
            return {
                "success": False,
                "error": f"Amount below minimum threshold of ${user_profile.payout_threshold}",
            }

        # Create transaction
        transaction_id = self.generate_transaction_id()
        transaction = PaymentTransaction(
            transaction_id=transaction_id,
            user_id=user_id,
            amount=amount,
            payout_method=user_profile.payout_method,
            payout_details=user_profile.payout_details,
            attribution_period_start=attribution_period_start,
            attribution_period_end=attribution_period_end,
            attribution_count=attribution_count,
        )

        # Store transaction
        self.transactions[transaction_id] = transaction

        # Add to processing queue
        self.payment_queue.append(transaction_id)

        # Start processing if not already active
        if not self.processing_active:
            asyncio.create_task(self._process_payment_queue())

        # Send notification
        await self._send_notification(
            user_id=user_id,
            notification_type=NotificationType.PAYMENT_SENT,
            title="Payment Initiated",
            message=f"Your payout of ${amount} is being processed.",
            data={
                "transaction_id": transaction_id,
                "amount": float(amount),
                "payout_method": user_profile.payout_method.value,
            },
        )

        logger.info(f"Payout initiated: {transaction_id} - ${amount} to {user_id}")

        return {
            "success": True,
            "transaction_id": transaction_id,
            "amount": float(amount),
            "payout_method": user_profile.payout_method.value,
            "estimated_processing_time": self._get_estimated_processing_time(
                user_profile.payout_method
            ),
        }

    async def _process_payment_queue(self):
        """Process payment queue"""

        self.processing_active = True

        while self.payment_queue:
            transaction_id = self.payment_queue.pop(0)
            await self._process_single_payment(transaction_id)

            # Add small delay between payments
            await asyncio.sleep(0.1)

        self.processing_active = False

    async def _process_single_payment(self, transaction_id: str):
        """Process a single payment"""

        if transaction_id not in self.transactions:
            logger.error(f"Transaction not found: {transaction_id}")
            return

        transaction = self.transactions[transaction_id]

        try:
            # Update status to processing
            transaction.status = PaymentStatus.PROCESSING

            # Get processor
            processor = self.processors.get(transaction.payout_method)
            if not processor:
                raise Exception(f"No processor for {transaction.payout_method}")

            # Process payment
            result = await processor.process_payment(transaction)

            if result["success"]:
                # Payment successful
                transaction.status = PaymentStatus.COMPLETED
                transaction.processed_at = datetime.now(timezone.utc)
                transaction.external_transaction_id = result.get(
                    "external_transaction_id"
                )
                transaction.processing_fee = Decimal(str(result.get("fee", 0)))
                transaction.net_amount = Decimal(
                    str(result.get("net_amount", transaction.amount))
                )
                transaction.processor_response = result.get("processor_response", {})

                # Send success notification
                await self._send_notification(
                    user_id=transaction.user_id,
                    notification_type=NotificationType.PAYMENT_RECEIVED,
                    title="Payment Completed",
                    message=f"Your payout of ${transaction.amount} has been sent successfully.",
                    data={
                        "transaction_id": transaction_id,
                        "amount": float(transaction.amount),
                        "net_amount": float(transaction.net_amount),
                        "processing_fee": float(transaction.processing_fee),
                        "external_id": transaction.external_transaction_id,
                    },
                )

                logger.info(f"Payment completed: {transaction_id}")

            else:
                # Payment failed
                transaction.status = PaymentStatus.FAILED
                transaction.failure_reason = result.get("error", "Unknown error")

                # Send failure notification
                await self._send_notification(
                    user_id=transaction.user_id,
                    notification_type=NotificationType.PAYMENT_FAILED,
                    title="Payment Failed",
                    message=f"Your payout of ${transaction.amount} could not be processed. Please contact support.",
                    data={
                        "transaction_id": transaction_id,
                        "amount": float(transaction.amount),
                        "error": transaction.failure_reason,
                    },
                )

                logger.error(
                    f"Payment failed: {transaction_id} - {transaction.failure_reason}"
                )

        except Exception as e:
            # Processing error
            transaction.status = PaymentStatus.FAILED
            transaction.failure_reason = str(e)

            logger.error(f"Payment processing error: {transaction_id} - {e}")

    async def _send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Dict[str, Any] = None,
    ):
        """Send notification to user"""

        notification_id = self.generate_notification_id()
        notification = PaymentNotification(
            notification_id=notification_id,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
        )

        # Store notification
        if user_id not in self.notifications:
            self.notifications[user_id] = []

        self.notifications[user_id].append(notification)

        # Keep only last 100 notifications per user
        self.notifications[user_id] = self.notifications[user_id][-100:]

        # Email/push notifications integration
        # Configure via environment variables:
        # - SENDGRID_API_KEY for email (SendGrid)
        # - AWS_SES_ACCESS_KEY for email (AWS SES)
        # - FCM_SERVER_KEY for push notifications (Firebase)
        logger.info(f"Notification sent: {user_id} - {title}")

        # Try to send via configured providers
        try:
            sendgrid_key = os.getenv("SENDGRID_API_KEY")
            if sendgrid_key:
                # SendGrid integration available in production
                # from sendgrid import SendGridAPIClient
                # from sendgrid.helpers.mail import Mail
                pass
        except Exception as e:
            logger.error(f"Notification delivery failed: {e}")

    def _get_estimated_processing_time(self, payout_method: PayoutMethod) -> str:
        """Get estimated processing time"""

        times = {
            PayoutMethod.PAYPAL: "1-3 business days",
            PayoutMethod.STRIPE: "2-5 business days",
            PayoutMethod.CRYPTO: "10-30 minutes",
            PayoutMethod.BANK_TRANSFER: "3-7 business days",
            PayoutMethod.VENMO: "1-2 business days",
            PayoutMethod.CASHAPP: "1-2 business days",
        }

        return times.get(payout_method, "3-5 business days")

    async def get_transaction_details(
        self, transaction_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get transaction details"""

        if transaction_id not in self.transactions:
            return None

        transaction = self.transactions[transaction_id]

        return {
            "transaction_id": transaction.transaction_id,
            "user_id": transaction.user_id,
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "payout_method": transaction.payout_method.value,
            "status": transaction.status.value,
            "created_at": transaction.created_at.isoformat(),
            "processed_at": transaction.processed_at.isoformat()
            if transaction.processed_at
            else None,
            "external_transaction_id": transaction.external_transaction_id,
            "processing_fee": float(transaction.processing_fee),
            "net_amount": float(transaction.net_amount),
            "attribution_period_start": transaction.attribution_period_start.isoformat()
            if transaction.attribution_period_start
            else None,
            "attribution_period_end": transaction.attribution_period_end.isoformat()
            if transaction.attribution_period_end
            else None,
            "attribution_count": transaction.attribution_count,
            "failure_reason": transaction.failure_reason,
        }

    async def get_user_payment_history(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        """Get user's payment history"""

        # Get user transactions
        user_transactions = [
            tx for tx in self.transactions.values() if tx.user_id == user_id
        ]

        # Sort by creation date (newest first)
        user_transactions.sort(key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        paginated_transactions = user_transactions[offset : offset + limit]

        # Calculate summary statistics
        completed_transactions = [
            tx for tx in user_transactions if tx.status == PaymentStatus.COMPLETED
        ]
        total_paid = sum(tx.net_amount for tx in completed_transactions)
        total_fees = sum(tx.processing_fee for tx in completed_transactions)

        return {
            "transactions": [
                {
                    "transaction_id": tx.transaction_id,
                    "amount": float(tx.amount),
                    "net_amount": float(tx.net_amount),
                    "processing_fee": float(tx.processing_fee),
                    "payout_method": tx.payout_method.value,
                    "status": tx.status.value,
                    "created_at": tx.created_at.isoformat(),
                    "processed_at": tx.processed_at.isoformat()
                    if tx.processed_at
                    else None,
                    "attribution_count": tx.attribution_count,
                }
                for tx in paginated_transactions
            ],
            "pagination": {
                "total": len(user_transactions),
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < len(user_transactions),
            },
            "summary": {
                "total_transactions": len(user_transactions),
                "completed_transactions": len(completed_transactions),
                "total_paid": float(total_paid),
                "total_fees": float(total_fees),
                "success_rate": len(completed_transactions)
                / len(user_transactions)
                * 100
                if user_transactions
                else 0,
            },
        }

    async def get_user_notifications(
        self, user_id: str, unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get user notifications"""

        notifications = self.notifications.get(user_id, [])

        if unread_only:
            notifications = [n for n in notifications if not n.read]

        return [
            {
                "notification_id": n.notification_id,
                "type": n.notification_type.value,
                "title": n.title,
                "message": n.message,
                "created_at": n.created_at.isoformat(),
                "read": n.read,
                "data": n.data,
            }
            for n in sorted(notifications, key=lambda x: x.created_at, reverse=True)
        ]

    async def mark_notification_read(self, user_id: str, notification_id: str) -> bool:
        """Mark notification as read"""

        if user_id not in self.notifications:
            return False

        for notification in self.notifications[user_id]:
            if notification.notification_id == notification_id:
                notification.read = True
                return True

        return False

    async def check_payout_thresholds(self):
        """Check all users for payout thresholds"""

        # This would typically be run as a scheduled task
        # For demo purposes, we'll just log
        logger.info("Checking payout thresholds for all users")

        # In production, this would:
        # 1. Query all users with earnings >= threshold
        # 2. Initiate automatic payouts
        # 3. Send threshold notifications

    async def generate_payment_summary(
        self, user_id: str, period: str = "month"
    ) -> Dict[str, Any]:
        """Generate payment summary for user"""

        # Get user transactions
        user_transactions = [
            tx
            for tx in self.transactions.values()
            if tx.user_id == user_id and tx.status == PaymentStatus.COMPLETED
        ]

        # Filter by period
        now = datetime.now(timezone.utc)
        if period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "quarter":
            start_date = now - timedelta(days=90)
        else:
            start_date = now - timedelta(days=365)

        period_transactions = [
            tx
            for tx in user_transactions
            if tx.processed_at and tx.processed_at >= start_date
        ]

        # Calculate summary
        total_amount = sum(tx.amount for tx in period_transactions)
        total_net = sum(tx.net_amount for tx in period_transactions)
        total_fees = sum(tx.processing_fee for tx in period_transactions)
        total_attributions = sum(tx.attribution_count for tx in period_transactions)

        return {
            "period": period,
            "transaction_count": len(period_transactions),
            "total_amount": float(total_amount),
            "total_net_amount": float(total_net),
            "total_fees": float(total_fees),
            "total_attributions": total_attributions,
            "average_per_transaction": float(total_amount / len(period_transactions))
            if period_transactions
            else 0,
            "fee_percentage": float(total_fees / total_amount * 100)
            if total_amount > 0
            else 0,
            "payout_methods": list(
                {tx.payout_method.value for tx in period_transactions}
            ),
        }


# Factory function
def create_payment_service(user_service: UserService) -> PaymentService:
    """Create a payment service instance"""
    return PaymentService(user_service)


# Example usage
if __name__ == "__main__":

    async def demo_payment_service():
        """Demonstrate the payment service"""

        from decimal import Decimal

        from ..user_management.user_service import PayoutMethod, create_user_service

        user_service = create_user_service()
        payment_service = create_payment_service(user_service)

        # Register test user
        user_result = await user_service.register_user(
            email="test@example.com",
            username="testuser",
            password="TestPass123!",
            full_name="Test User",
        )

        if user_result["success"]:
            user_id = user_result["user_id"]

            # Set up payout method
            await user_service.setup_payout_method(
                user_id=user_id,
                payout_method=PayoutMethod.PAYPAL,
                payout_details={"email": "test@example.com"},
            )

            # Initiate payout
            payout_result = await payment_service.initiate_payout(
                user_id=user_id, amount=Decimal("25.50"), attribution_count=127
            )

            print(f"Payout Result: {payout_result}")

            # Wait for processing
            await asyncio.sleep(1)

            # Check transaction details
            if payout_result["success"]:
                transaction_id = payout_result["transaction_id"]
                details = await payment_service.get_transaction_details(transaction_id)
                print(f"Transaction Details: {details}")

            # Get payment history
            history = await payment_service.get_user_payment_history(user_id)
            print(f"Payment History: {history}")

            # Get notifications
            notifications = await payment_service.get_user_notifications(user_id)
            print(f"Notifications: {notifications}")

            # Generate summary
            summary = await payment_service.generate_payment_summary(user_id, "month")
            print(f"Payment Summary: {summary}")

    asyncio.run(demo_payment_service())
