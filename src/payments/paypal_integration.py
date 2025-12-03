"""
PayPal Payment Integration
Real PayPal API integration for payment processing and payouts
"""

import base64
import json
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class PayPalIntegration:
    """Real PayPal integration for payment processing"""

    def __init__(self):
        self.client_id = os.getenv("PAYPAL_CLIENT_ID")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
        self.mode = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox or live

        if self.mode == "sandbox":
            self.base_url = "https://api.sandbox.paypal.com"
        else:
            self.base_url = "https://api.paypal.com"

        self.access_token = None
        self.token_expires_at = None

        if not self.client_id or not self.client_secret:
            logger.warning("PayPal credentials not found - payments will not work")
        else:
            self._authenticate()

    def _authenticate(self) -> bool:
        """Authenticate with PayPal and get access token"""
        try:
            # Create basic auth header
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode("ascii")
            auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            data = "grant_type=client_credentials"

            response = requests.post(
                f"{self.base_url}/v1/oauth2/token", headers=headers, data=data
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = (
                    datetime.now(timezone.utc).timestamp() + expires_in
                )

                logger.info("PayPal authentication successful")
                return True
            else:
                logger.error(
                    f"PayPal authentication failed: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"PayPal authentication error: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with valid access token"""
        # Check if token needs refresh
        if (
            not self.access_token
            or not self.token_expires_at
            or datetime.now(timezone.utc).timestamp() > self.token_expires_at - 300
        ):
            self._authenticate()

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def create_payout(
        self,
        recipient_email: str,
        amount: Decimal,
        currency: str = "USD",
        note: str = None,
        sender_batch_id: str = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a payout to recipient"""
        try:
            if not sender_batch_id:
                import uuid

                sender_batch_id = f"uatp_payout_{uuid.uuid4().hex[:12]}"

            payout_data = {
                "sender_batch_header": {
                    "sender_batch_id": sender_batch_id,
                    "email_subject": "You have received a payment from UATP",
                    "email_message": note
                    or "You have received a payment for your AI contributions",
                },
                "items": [
                    {
                        "recipient_type": "EMAIL",
                        "amount": {"value": str(amount), "currency": currency},
                        "receiver": recipient_email,
                        "note": note or "UATP Attribution Payout",
                        "sender_item_id": f"item_{uuid.uuid4().hex[:8]}",
                    }
                ],
            }

            headers = self._get_headers()

            response = requests.post(
                f"{self.base_url}/v1/payments/payouts",
                headers=headers,
                json=payout_data,
            )

            if response.status_code == 201:
                result = response.json()
                batch_header = result["batch_header"]

                logger.info(f"PayPal payout created: {batch_header['payout_batch_id']}")

                return {
                    "payout_batch_id": batch_header["payout_batch_id"],
                    "batch_status": batch_header["batch_status"],
                    "sender_batch_id": sender_batch_id,
                    "amount": float(amount),
                    "currency": currency,
                    "recipient_email": recipient_email,
                }
            else:
                logger.error(
                    f"PayPal payout creation failed: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"PayPal payout creation error: {e}")
            return None

    def get_payout_status(self, payout_batch_id: str) -> Optional[Dict[str, Any]]:
        """Get payout status"""
        try:
            headers = self._get_headers()

            response = requests.get(
                f"{self.base_url}/v1/payments/payouts/{payout_batch_id}",
                headers=headers,
            )

            if response.status_code == 200:
                result = response.json()
                batch_header = result["batch_header"]

                return {
                    "payout_batch_id": batch_header["payout_batch_id"],
                    "batch_status": batch_header["batch_status"],
                    "sender_batch_id": batch_header.get("sender_batch_id"),
                    "amount": float(batch_header.get("amount", {}).get("value", 0)),
                    "currency": batch_header.get("amount", {}).get("currency", "USD"),
                    "fees": float(batch_header.get("fees", {}).get("value", 0)),
                    "time_created": batch_header.get("time_created"),
                    "time_completed": batch_header.get("time_completed"),
                }
            else:
                logger.error(
                    f"PayPal payout status retrieval failed: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"PayPal payout status error: {e}")
            return None

    def get_payout_item_details(self, payout_item_id: str) -> Optional[Dict[str, Any]]:
        """Get individual payout item details"""
        try:
            headers = self._get_headers()

            response = requests.get(
                f"{self.base_url}/v1/payments/payouts-item/{payout_item_id}",
                headers=headers,
            )

            if response.status_code == 200:
                result = response.json()

                return {
                    "payout_item_id": result["payout_item_id"],
                    "transaction_id": result.get("transaction_id"),
                    "transaction_status": result.get("transaction_status"),
                    "amount": float(
                        result.get("payout_item", {}).get("amount", {}).get("value", 0)
                    ),
                    "currency": result.get("payout_item", {})
                    .get("amount", {})
                    .get("currency", "USD"),
                    "receiver": result.get("payout_item", {}).get("receiver"),
                    "note": result.get("payout_item", {}).get("note"),
                    "time_processed": result.get("time_processed"),
                }
            else:
                logger.error(
                    f"PayPal payout item details retrieval failed: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"PayPal payout item details error: {e}")
            return None

    def cancel_payout_item(self, payout_item_id: str) -> bool:
        """Cancel a payout item"""
        try:
            headers = self._get_headers()

            response = requests.post(
                f"{self.base_url}/v1/payments/payouts-item/{payout_item_id}/cancel",
                headers=headers,
            )

            if response.status_code == 200:
                logger.info(f"PayPal payout item canceled: {payout_item_id}")
                return True
            else:
                logger.error(
                    f"PayPal payout item cancellation failed: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"PayPal payout item cancellation error: {e}")
            return False

    def calculate_fees(
        self, amount: Decimal, currency: str = "USD"
    ) -> Dict[str, Decimal]:
        """Calculate PayPal fees for payout"""
        # PayPal payout fees (as of 2024)
        if currency == "USD":
            # $0.30 per payout item
            paypal_fee = Decimal("0.30")
        else:
            # 2% of payout amount for international payouts
            paypal_fee = amount * Decimal("0.02")

        net_amount = amount - paypal_fee

        return {
            "gross_amount": amount,
            "paypal_fee": paypal_fee,
            "net_amount": net_amount,
        }

    def verify_webhook(self, headers: Dict[str, str], body: str) -> bool:
        """Verify PayPal webhook signature"""
        try:
            # PayPal webhook verification
            verification_data = {
                "auth_algo": headers.get("PAYPAL-AUTH-ALGO"),
                "cert_id": headers.get("PAYPAL-CERT-ID"),
                "transmission_id": headers.get("PAYPAL-TRANSMISSION-ID"),
                "transmission_sig": headers.get("PAYPAL-TRANSMISSION-SIG"),
                "transmission_time": headers.get("PAYPAL-TRANSMISSION-TIME"),
                "webhook_id": os.getenv("PAYPAL_WEBHOOK_ID"),
                "webhook_event": json.loads(body),
            }

            headers = self._get_headers()

            response = requests.post(
                f"{self.base_url}/v1/notifications/verify-webhook-signature",
                headers=headers,
                json=verification_data,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("verification_status") == "SUCCESS"
            else:
                logger.error(
                    f"PayPal webhook verification failed: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"PayPal webhook verification error: {e}")
            return False

    def handle_webhook(
        self, headers: Dict[str, str], body: str
    ) -> Optional[Dict[str, Any]]:
        """Handle PayPal webhook events"""
        try:
            # Verify webhook signature
            if not self.verify_webhook(headers, body):
                logger.warning("PayPal webhook signature verification failed")
                return None

            event = json.loads(body)
            event_type = event.get("event_type")

            logger.info(f"PayPal webhook received: {event_type}")

            if event_type == "PAYMENT.PAYOUTS-ITEM.SUCCEEDED":
                return self._handle_payout_succeeded(event)
            elif event_type == "PAYMENT.PAYOUTS-ITEM.FAILED":
                return self._handle_payout_failed(event)
            elif event_type == "PAYMENT.PAYOUTS-ITEM.CANCELED":
                return self._handle_payout_canceled(event)
            elif event_type == "PAYMENT.PAYOUTS-ITEM.BLOCKED":
                return self._handle_payout_blocked(event)

            return {"status": "unhandled", "type": event_type}

        except Exception as e:
            logger.error(f"PayPal webhook handling error: {e}")
            return None

    def _handle_payout_succeeded(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payout webhook"""
        resource = event.get("resource", {})
        payout_item = resource.get("payout_item", {})

        logger.info(f"PayPal payout succeeded: {resource.get('payout_item_id')}")

        return {
            "status": "payout_succeeded",
            "payout_item_id": resource.get("payout_item_id"),
            "transaction_id": resource.get("transaction_id"),
            "amount": float(payout_item.get("amount", {}).get("value", 0)),
            "currency": payout_item.get("amount", {}).get("currency", "USD"),
            "receiver": payout_item.get("receiver"),
        }

    def _handle_payout_failed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payout webhook"""
        resource = event.get("resource", {})
        payout_item = resource.get("payout_item", {})

        logger.error(f"PayPal payout failed: {resource.get('payout_item_id')}")

        return {
            "status": "payout_failed",
            "payout_item_id": resource.get("payout_item_id"),
            "amount": float(payout_item.get("amount", {}).get("value", 0)),
            "currency": payout_item.get("amount", {}).get("currency", "USD"),
            "receiver": payout_item.get("receiver"),
            "error": resource.get("error"),
        }

    def _handle_payout_canceled(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle canceled payout webhook"""
        resource = event.get("resource", {})
        payout_item = resource.get("payout_item", {})

        logger.info(f"PayPal payout canceled: {resource.get('payout_item_id')}")

        return {
            "status": "payout_canceled",
            "payout_item_id": resource.get("payout_item_id"),
            "amount": float(payout_item.get("amount", {}).get("value", 0)),
            "currency": payout_item.get("amount", {}).get("currency", "USD"),
            "receiver": payout_item.get("receiver"),
        }

    def _handle_payout_blocked(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle blocked payout webhook"""
        resource = event.get("resource", {})
        payout_item = resource.get("payout_item", {})

        logger.warning(f"PayPal payout blocked: {resource.get('payout_item_id')}")

        return {
            "status": "payout_blocked",
            "payout_item_id": resource.get("payout_item_id"),
            "amount": float(payout_item.get("amount", {}).get("value", 0)),
            "currency": payout_item.get("amount", {}).get("currency", "USD"),
            "receiver": payout_item.get("receiver"),
        }

    def get_account_balance(self) -> Optional[Dict[str, Any]]:
        """Get PayPal account balance"""
        try:
            headers = self._get_headers()

            response = requests.get(
                f"{self.base_url}/v1/reporting/balances", headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                balances = result.get("balances", [])

                return {
                    "balances": [
                        {
                            "currency": balance.get("currency"),
                            "primary": balance.get("primary", False),
                            "total_balance": float(
                                balance.get("total_balance", {}).get("value", 0)
                            ),
                            "available_balance": float(
                                balance.get("available_balance", {}).get("value", 0)
                            ),
                            "withheld_balance": float(
                                balance.get("withheld_balance", {}).get("value", 0)
                            ),
                        }
                        for balance in balances
                    ]
                }
            else:
                logger.error(
                    f"PayPal balance retrieval failed: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"PayPal balance retrieval error: {e}")
            return None


# Global PayPal integration instance
paypal_integration = PayPalIntegration()


# Helper functions
def create_paypal_payout(
    recipient_email: str, amount: Decimal, currency: str = "USD", note: str = None
) -> Optional[Dict[str, Any]]:
    """Create PayPal payout"""
    return paypal_integration.create_payout(recipient_email, amount, currency, note)


def get_paypal_payout_status(payout_batch_id: str) -> Optional[Dict[str, Any]]:
    """Get PayPal payout status"""
    return paypal_integration.get_payout_status(payout_batch_id)


def get_paypal_fees(amount: Decimal, currency: str = "USD") -> Dict[str, Decimal]:
    """Calculate PayPal fees"""
    return paypal_integration.calculate_fees(amount, currency)


# Example usage and testing
if __name__ == "__main__":
    print("💰 Testing PayPal Integration...")

    # Test authentication
    if paypal_integration.access_token:
        print("✅ PayPal authentication successful")
    else:
        print("❌ PayPal authentication failed")

    # Test fee calculation
    test_amount = Decimal("100.00")
    fees = paypal_integration.calculate_fees(test_amount)
    print(f"Fees for ${test_amount}: {fees}")

    # Test balance retrieval
    try:
        balance = paypal_integration.get_account_balance()
        print(f"PayPal balance: {balance}")
    except Exception as e:
        print(f"Balance retrieval failed: {e}")

    print("✅ PayPal Integration tests completed")
