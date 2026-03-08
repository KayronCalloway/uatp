"""
Stripe Payment Integration
Real Stripe API integration for payment processing and payouts
"""

import logging
import os
from decimal import Decimal
from typing import Any, Dict, List, Optional

import stripe

logger = logging.getLogger(__name__)


class StripeIntegration:
    """Real Stripe integration for payment processing"""

    def __init__(self):
        # Initialize Stripe with API key
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        if not stripe.api_key:
            logger.warning("Stripe API key not found - payments will not work")

        # Test connection
        try:
            stripe.Account.retrieve()
            logger.info("Stripe connection established successfully")
        except Exception as e:
            logger.error(f"Stripe connection failed: {e}")

    def create_customer(self, email: str, name: str, user_id: str) -> Optional[str]:
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"user_id": user_id, "platform": "uatp"},
            )

            logger.info(f"Stripe customer created: {customer.id}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed: {e}")
            return None

    def create_express_account(
        self, user_id: str, email: str, country: str = "US"
    ) -> Optional[Dict[str, Any]]:
        """Create Stripe Express account for payouts"""
        try:
            account = stripe.Account.create(
                type="express",
                country=country,
                email=email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                business_type="individual",
                metadata={"user_id": user_id, "platform": "uatp"},
            )

            logger.info(f"Stripe Express account created: {account.id}")

            return {
                "account_id": account.id,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "details_submitted": account.details_submitted,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe Express account creation failed: {e}")
            return None

    def create_account_link(
        self, account_id: str, return_url: str, refresh_url: str
    ) -> Optional[str]:
        """Create account link for Express account onboarding"""
        try:
            account_link = stripe.AccountLink.create(
                account=account_id,
                return_url=return_url,
                refresh_url=refresh_url,
                type="account_onboarding",
            )

            return account_link.url

        except stripe.error.StripeError as e:
            logger.error(f"Stripe account link creation failed: {e}")
            return None

    def create_payout(
        self,
        amount: Decimal,
        currency: str = "usd",
        account_id: str = None,
        description: str = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a payout to user's bank account"""
        try:
            # Convert amount to cents
            amount_cents = int(amount * 100)

            payout_data = {
                "amount": amount_cents,
                "currency": currency,
                "description": description or "UATP Attribution Payout",
            }

            if account_id:
                # Payout to Express account
                payout = stripe.Payout.create(**payout_data, stripe_account=account_id)
            else:
                # Payout from platform account
                payout = stripe.Payout.create(**payout_data)

            logger.info(f"Stripe payout created: {payout.id}")

            return {
                "payout_id": payout.id,
                "amount": float(payout.amount / 100),
                "currency": payout.currency,
                "status": payout.status,
                "arrival_date": payout.arrival_date,
                "description": payout.description,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe payout creation failed: {e}")
            return None

    def create_transfer(
        self, amount: Decimal, destination_account: str, description: str = None
    ) -> Optional[Dict[str, Any]]:
        """Create a transfer to Express account"""
        try:
            amount_cents = int(amount * 100)

            transfer = stripe.Transfer.create(
                amount=amount_cents,
                currency="usd",
                destination=destination_account,
                description=description or "UATP Attribution Transfer",
            )

            logger.info(f"Stripe transfer created: {transfer.id}")

            return {
                "transfer_id": transfer.id,
                "amount": float(transfer.amount / 100),
                "currency": transfer.currency,
                "destination": transfer.destination,
                "status": "pending",
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe transfer creation failed: {e}")
            return None

    def get_account_status(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get Express account status"""
        try:
            account = stripe.Account.retrieve(account_id)

            return {
                "account_id": account.id,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "details_submitted": account.details_submitted,
                "requirements": account.requirements.to_dict()
                if account.requirements
                else None,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe account status retrieval failed: {e}")
            return None

    def get_payout_status(
        self, payout_id: str, account_id: str = None
    ) -> Optional[Dict[str, Any]]:
        """Get payout status"""
        try:
            if account_id:
                payout = stripe.Payout.retrieve(payout_id, stripe_account=account_id)
            else:
                payout = stripe.Payout.retrieve(payout_id)

            return {
                "payout_id": payout.id,
                "amount": float(payout.amount / 100),
                "currency": payout.currency,
                "status": payout.status,
                "arrival_date": payout.arrival_date,
                "failure_code": payout.failure_code,
                "failure_message": payout.failure_message,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe payout status retrieval failed: {e}")
            return None

    def list_payouts(
        self, account_id: str = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """List recent payouts"""
        try:
            if account_id:
                payouts = stripe.Payout.list(limit=limit, stripe_account=account_id)
            else:
                payouts = stripe.Payout.list(limit=limit)

            return [
                {
                    "payout_id": payout.id,
                    "amount": float(payout.amount / 100),
                    "currency": payout.currency,
                    "status": payout.status,
                    "arrival_date": payout.arrival_date,
                    "created": payout.created,
                    "description": payout.description,
                }
                for payout in payouts.data
            ]

        except stripe.error.StripeError as e:
            logger.error(f"Stripe payout listing failed: {e}")
            return []

    def calculate_fees(
        self, amount: Decimal, payout_method: str = "ach"
    ) -> Dict[str, Decimal]:
        """Calculate Stripe fees for payout"""
        # Stripe Express account fees
        if payout_method == "ach":
            # ACH transfers are free for Express accounts
            stripe_fee = Decimal("0.00")
        elif payout_method == "instant":
            # Instant payouts: 1.5% with $0.50 minimum
            stripe_fee = max(amount * Decimal("0.015"), Decimal("0.50"))
        else:
            # Standard payout fee
            stripe_fee = Decimal("0.25")

        net_amount = amount - stripe_fee

        return {
            "gross_amount": amount,
            "stripe_fee": stripe_fee,
            "net_amount": net_amount,
        }

    def handle_webhook(self, payload: str, sig_header: str) -> Optional[Dict[str, Any]]:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )

            logger.info(f"Stripe webhook received: {event['type']}")

            if event["type"] == "payout.paid":
                return self._handle_payout_paid(event["data"]["object"])
            elif event["type"] == "payout.failed":
                return self._handle_payout_failed(event["data"]["object"])
            elif event["type"] == "account.updated":
                return self._handle_account_updated(event["data"]["object"])
            elif event["type"] == "transfer.created":
                return self._handle_transfer_created(event["data"]["object"])

            return {"status": "unhandled", "type": event["type"]}

        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return None

    def _handle_payout_paid(self, payout_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payout webhook"""
        logger.info(f"Payout paid: {payout_obj['id']}")

        return {
            "status": "payout_paid",
            "payout_id": payout_obj["id"],
            "amount": float(payout_obj["amount"] / 100),
            "currency": payout_obj["currency"],
        }

    def _handle_payout_failed(self, payout_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payout webhook"""
        logger.error(
            f"Payout failed: {payout_obj['id']} - {payout_obj.get('failure_message')}"
        )

        return {
            "status": "payout_failed",
            "payout_id": payout_obj["id"],
            "amount": float(payout_obj["amount"] / 100),
            "failure_code": payout_obj.get("failure_code"),
            "failure_message": payout_obj.get("failure_message"),
        }

    def _handle_account_updated(self, account_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Handle account update webhook"""
        logger.info(f"Account updated: {account_obj['id']}")

        return {
            "status": "account_updated",
            "account_id": account_obj["id"],
            "charges_enabled": account_obj["charges_enabled"],
            "payouts_enabled": account_obj["payouts_enabled"],
            "details_submitted": account_obj["details_submitted"],
        }

    def _handle_transfer_created(self, transfer_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Handle transfer creation webhook"""
        logger.info(f"Transfer created: {transfer_obj['id']}")

        return {
            "status": "transfer_created",
            "transfer_id": transfer_obj["id"],
            "amount": float(transfer_obj["amount"] / 100),
            "destination": transfer_obj["destination"],
        }

    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str = "usd",
        customer_id: str = None,
        description: str = None,
    ) -> Optional[Dict[str, Any]]:
        """Create payment intent for collecting payments"""
        try:
            amount_cents = int(amount * 100)

            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                customer=customer_id,
                description=description or "UATP Platform Payment",
                automatic_payment_methods={"enabled": True},
            )

            logger.info(f"Payment intent created: {payment_intent.id}")

            return {
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": float(payment_intent.amount / 100),
                "currency": payment_intent.currency,
                "status": payment_intent.status,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Payment intent creation failed: {e}")
            return None

    def get_balance(self, account_id: str = None) -> Optional[Dict[str, Any]]:
        """Get account balance"""
        try:
            if account_id:
                balance = stripe.Balance.retrieve(stripe_account=account_id)
            else:
                balance = stripe.Balance.retrieve()

            return {
                "available": [
                    {"amount": float(fund.amount / 100), "currency": fund.currency}
                    for fund in balance.available
                ],
                "pending": [
                    {"amount": float(fund.amount / 100), "currency": fund.currency}
                    for fund in balance.pending
                ],
            }

        except stripe.error.StripeError as e:
            logger.error(f"Balance retrieval failed: {e}")
            return None


# Global Stripe integration instance
stripe_integration = StripeIntegration()


# Helper functions
def create_stripe_customer(email: str, name: str, user_id: str) -> Optional[str]:
    """Create Stripe customer"""
    return stripe_integration.create_customer(email, name, user_id)


def create_stripe_express_account(
    user_id: str, email: str, country: str = "US"
) -> Optional[Dict[str, Any]]:
    """Create Stripe Express account"""
    return stripe_integration.create_express_account(user_id, email, country)


def process_stripe_payout(
    amount: Decimal, account_id: str = None, description: str = None
) -> Optional[Dict[str, Any]]:
    """Process Stripe payout"""
    return stripe_integration.create_payout(
        amount, account_id=account_id, description=description
    )


def get_stripe_fees(amount: Decimal, payout_method: str = "ach") -> Dict[str, Decimal]:
    """Calculate Stripe fees"""
    return stripe_integration.calculate_fees(amount, payout_method)


# Example usage and testing
if __name__ == "__main__":
    print(" Testing Stripe Integration...")

    # Test connection
    try:
        balance = stripe_integration.get_balance()
        print(f"Stripe balance: {balance}")
    except Exception as e:
        print(f"Stripe connection test failed: {e}")

    # Test fee calculation
    test_amount = Decimal("100.00")
    fees = stripe_integration.calculate_fees(test_amount)
    print(f"Fees for ${test_amount}: {fees}")

    print("[OK] Stripe Integration tests completed")
