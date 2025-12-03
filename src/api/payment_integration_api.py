"""
External Payment Integration API for UATP Capsule Engine

This module provides comprehensive API endpoints for external payment processing,
including Stripe, PayPal, cryptocurrency payments, and payment webhooks.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from quart import Blueprint, jsonify, request
from quart_schema import validate_request

from .schemas import ErrorResponse
from src.audit.events import audit_emitter
from payments.real_payment_service import (
    PaymentConfig,
    PaymentStatus,
    RealPaymentService,
    create_real_payment_service,
)
from user_management.user_service import PayoutMethod, create_user_service

logger = logging.getLogger(__name__)


# --- Schema Definitions ---


class InitiatePayoutRequest(BaseModel):
    """Schema for initiating a payout."""

    user_id: str
    amount: float = Field(gt=0, description="Payout amount")
    currency: str = Field(default="USD", description="Payment currency")
    description: Optional[str] = Field(None, description="Payment description")
    force_immediate: bool = Field(
        default=False, description="Force immediate processing"
    )


class ConfigurePayoutMethodRequest(BaseModel):
    """Schema for configuring user payout method."""

    user_id: str
    payout_method: str = Field(
        description="Payout method (paypal, stripe, crypto, bank_transfer)"
    )
    payout_details: Dict[str, Any] = Field(description="Payout method specific details")
    set_as_default: bool = Field(
        default=True, description="Set as default payout method"
    )


class ProcessWebhookRequest(BaseModel):
    """Schema for processing payment webhooks."""

    provider: str = Field(description="Payment provider (stripe, paypal)")
    event_type: str = Field(description="Webhook event type")
    event_data: Dict[str, Any] = Field(description="Webhook event data")
    signature: Optional[str] = Field(
        None, description="Webhook signature for verification"
    )


class BulkPayoutRequest(BaseModel):
    """Schema for bulk payout processing."""

    payouts: List[Dict[str, Any]] = Field(description="List of payout requests")
    batch_description: Optional[str] = Field(None, description="Batch description")
    processing_priority: str = Field(
        default="normal", description="Processing priority (low, normal, high)"
    )


class PaymentAnalyticsRequest(BaseModel):
    """Schema for payment analytics."""

    time_range: str = Field(
        default="month", description="Analytics time range (week, month, quarter, year)"
    )
    user_ids: Optional[List[str]] = Field(
        None, description="Specific user IDs to analyze"
    )
    payment_methods: Optional[List[str]] = Field(
        None, description="Filter by payment methods"
    )


class PayoutResponse(BaseModel):
    """Schema for payout response."""

    success: bool
    transaction_id: Optional[str]
    amount: float
    currency: str
    payout_method: str
    status: str
    processing_fee: float
    net_amount: float
    external_id: Optional[str]
    estimated_completion: Optional[str]
    error: Optional[str]


class PaymentHistoryResponse(BaseModel):
    """Schema for payment history response."""

    user_id: str
    total_transactions: int
    transactions: List[Dict[str, Any]]
    summary: Dict[str, Any]


class PaymentAnalyticsResponse(BaseModel):
    """Schema for payment analytics response."""

    time_range: str
    total_volume: float
    transaction_count: int
    average_transaction: float
    success_rate: float
    fee_analysis: Dict[str, Any]
    method_breakdown: Dict[str, Any]
    trend_analysis: Dict[str, Any]


class WebhookResponse(BaseModel):
    """Schema for webhook processing response."""

    success: bool
    processed_events: int
    failed_events: int
    details: List[Dict[str, Any]]


def create_payment_integration_blueprint(engine_getter, require_api_key):
    """Create and return the payment integration API blueprint."""
    blueprint = Blueprint(
        "payment_integration", __name__, url_prefix="/api/v1/payments"
    )

    # Initialize services
    user_service = create_user_service()
    payment_config = PaymentConfig(
        min_payout_amount=Decimal("5.00"),
        max_payout_amount=Decimal("50000.00"),
        enable_stripe=True,
        enable_paypal=True,
        enable_crypto=True,
    )
    payment_service = create_real_payment_service(user_service, payment_config)

    # --- Core Payment Endpoints ---

    @blueprint.route("/payouts", methods=["POST"])
    @require_api_key(["write", "admin"])
    @validate_request(InitiatePayoutRequest)
    async def initiate_payout(data: InitiatePayoutRequest):
        """Initiate a payout to a user."""
        try:
            result = await payment_service.initiate_payout(
                user_id=data.user_id,
                amount=Decimal(str(data.amount)),
                description=data.description,
            )

            if result["success"]:
                response = PayoutResponse(
                    success=True,
                    transaction_id=result["transaction_id"],
                    amount=result["amount"],
                    currency=data.currency,
                    payout_method=result["payout_method"],
                    status=result["status"],
                    processing_fee=result["processing_fee"],
                    net_amount=result["net_amount"],
                    external_id=result.get("external_id"),
                    estimated_completion=_get_estimated_completion(
                        result["payout_method"]
                    ),
                )
                return jsonify(response.model_dump()), 201
            else:
                return (
                    jsonify(
                        ErrorResponse(
                            error="Payout failed",
                            details=result.get("error", "Unknown error"),
                        ).model_dump()
                    ),
                    400,
                )

        except Exception as e:
            logger.error(f"Error initiating payout: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to initiate payout", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/payouts/bulk", methods=["POST"])
    @require_api_key(["admin"])
    @validate_request(BulkPayoutRequest)
    async def process_bulk_payouts(data: BulkPayoutRequest):
        """Process multiple payouts in bulk."""
        try:
            results = []
            batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

            for payout_data in data.payouts:
                try:
                    result = await payment_service.initiate_payout(
                        user_id=payout_data["user_id"],
                        amount=Decimal(str(payout_data["amount"])),
                        description=payout_data.get(
                            "description", f"Bulk payout - {batch_id}"
                        ),
                    )
                    results.append(
                        {
                            "user_id": payout_data["user_id"],
                            "success": result["success"],
                            "transaction_id": result.get("transaction_id"),
                            "error": result.get("error"),
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "user_id": payout_data["user_id"],
                            "success": False,
                            "error": str(e),
                        }
                    )

            successful = len([r for r in results if r["success"]])
            failed = len(results) - successful

            return (
                jsonify(
                    {
                        "batch_id": batch_id,
                        "total_payouts": len(results),
                        "successful": successful,
                        "failed": failed,
                        "processing_priority": data.processing_priority,
                        "results": results,
                    }
                ),
                200,
            )

        except Exception as e:
            logger.error(f"Error processing bulk payouts: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to process bulk payouts", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/payouts/<transaction_id>", methods=["GET"])
    @require_api_key(["read", "write", "admin"])
    async def get_payout_details(transaction_id: str):
        """Get details of a specific payout."""
        try:
            details = await payment_service.get_transaction_details(transaction_id)

            if details:
                return jsonify(details), 200
            else:
                return (
                    jsonify(
                        ErrorResponse(
                            error=f"Transaction {transaction_id} not found"
                        ).model_dump()
                    ),
                    404,
                )

        except Exception as e:
            logger.error(f"Error getting payout details: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve payout details", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/users/<user_id>/payment-history", methods=["GET"])
    @require_api_key(["read", "write", "admin"])
    async def get_user_payment_history(user_id: str):
        """Get payment history for a user."""
        try:
            limit = request.args.get("limit", 50, type=int)
            history = await payment_service.get_user_payment_history(user_id, limit)

            response = PaymentHistoryResponse(
                user_id=history["user_id"],
                total_transactions=history["total_transactions"],
                transactions=history["transactions"],
                summary={
                    "total_amount": sum(tx["amount"] for tx in history["transactions"]),
                    "total_net": sum(
                        tx["net_amount"] for tx in history["transactions"]
                    ),
                    "completed_count": len(
                        [
                            tx
                            for tx in history["transactions"]
                            if tx["status"] == "completed"
                        ]
                    ),
                },
            )

            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"Error getting payment history: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve payment history", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    # --- Payout Method Configuration ---

    @blueprint.route("/payout-methods", methods=["POST"])
    @require_api_key(["write", "admin"])
    @validate_request(ConfigurePayoutMethodRequest)
    async def configure_payout_method(data: ConfigurePayoutMethodRequest):
        """Configure user payout method."""
        try:
            # Validate payout method
            try:
                payout_method = PayoutMethod(data.payout_method.upper())
            except ValueError:
                return (
                    jsonify(
                        ErrorResponse(
                            error=f"Invalid payout method: {data.payout_method}"
                        ).model_dump()
                    ),
                    400,
                )

            # Validate payout details based on method
            validation_result = _validate_payout_details(
                payout_method, data.payout_details
            )
            if not validation_result["valid"]:
                return (
                    jsonify(
                        ErrorResponse(
                            error="Invalid payout details",
                            details=validation_result["error"],
                        ).model_dump()
                    ),
                    400,
                )

            # Configure payout method
            success = await user_service.setup_payout_method(
                user_id=data.user_id,
                payout_method=payout_method,
                payout_details=data.payout_details,
            )

            if success:
                return (
                    jsonify(
                        {
                            "user_id": data.user_id,
                            "payout_method": data.payout_method,
                            "configured": True,
                            "default": data.set_as_default,
                        }
                    ),
                    201,
                )
            else:
                return (
                    jsonify(
                        ErrorResponse(
                            error="Failed to configure payout method"
                        ).model_dump()
                    ),
                    400,
                )

        except Exception as e:
            logger.error(f"Error configuring payout method: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to configure payout method", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/payout-methods/<user_id>", methods=["GET"])
    @require_api_key(["read", "write", "admin"])
    async def get_user_payout_methods(user_id: str):
        """Get user's configured payout methods."""
        try:
            profile = await user_service.get_user_profile(user_id)

            if not profile:
                return (
                    jsonify(
                        ErrorResponse(error=f"User {user_id} not found").model_dump()
                    ),
                    404,
                )

            return (
                jsonify(
                    {
                        "user_id": user_id,
                        "default_method": profile.payout_method.value
                        if profile.payout_method
                        else None,
                        "payout_details": profile.payout_details,
                        "payout_threshold": float(profile.payout_threshold),
                        "supported_methods": [method.value for method in PayoutMethod],
                    }
                ),
                200,
            )

        except Exception as e:
            logger.error(f"Error getting payout methods: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve payout methods", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    # --- Webhook Endpoints ---

    @blueprint.route("/webhooks/stripe", methods=["POST"])
    async def stripe_webhook():
        """Handle Stripe webhook events with comprehensive security."""
        try:
            # SECURITY: Always verify webhook signatures - never skip in production
            if not payment_service.stripe_webhook_secret:
                logger.error("Stripe webhook secret not configured - rejecting request")
                audit_emitter.emit_security_event(
                    "stripe_webhook_security_failure",
                    {"reason": "missing_webhook_secret", "ip": request.remote_addr},
                )
                return (
                    jsonify(
                        ErrorResponse(error="Webhook configuration error").model_dump()
                    ),
                    500,
                )

            # Get raw payload for signature verification
            payload = await request.get_data()
            sig_header = request.headers.get("Stripe-Signature")

            # SECURITY: Verify signature before processing
            if not verify_webhook_signature(
                payload, sig_header, payment_service.stripe_webhook_secret, "stripe"
            ):
                logger.warning(
                    f"Invalid Stripe webhook signature from IP {request.remote_addr}"
                )
                audit_emitter.emit_security_event(
                    "stripe_webhook_signature_verification_failed",
                    {
                        "ip": request.remote_addr,
                        "signature": sig_header[:20] if sig_header else None,
                    },
                )
                return (
                    jsonify(
                        ErrorResponse(error="Invalid webhook signature").model_dump()
                    ),
                    401,
                )

            # Parse the event after signature verification
            try:
                import stripe

                event = stripe.Webhook.construct_event(
                    payload, sig_header, payment_service.stripe_webhook_secret
                )
            except stripe.error.SignatureVerificationError as e:
                logger.warning(f"Stripe signature verification failed: {e}")
                return (
                    jsonify(
                        ErrorResponse(error="Invalid Stripe signature").model_dump()
                    ),
                    401,
                )
            except Exception as e:
                logger.error(f"Error constructing Stripe event: {e}")
                return (
                    jsonify(ErrorResponse(error="Invalid webhook event").model_dump()),
                    400,
                )

            # SECURITY: Rate limiting for webhook processing
            if not check_webhook_rate_limit(request.remote_addr, "stripe"):
                logger.warning(
                    f"Webhook rate limit exceeded for IP {request.remote_addr}"
                )
                audit_emitter.emit_security_event(
                    "webhook_rate_limit_exceeded",
                    {"provider": "stripe", "ip": request.remote_addr},
                )
                return (
                    jsonify(ErrorResponse(error="Rate limit exceeded").model_dump()),
                    429,
                )

            # Process the verified webhook
            await payment_service.handle_stripe_webhook(event)

            # SECURITY: Log successful webhook processing
            audit_emitter.emit_security_event(
                "stripe_webhook_processed_successfully",
                {"event_type": event.get("type"), "event_id": event.get("id")},
            )

            return jsonify({"success": True, "processed": True}), 200

        except Exception as e:
            logger.error(f"Error processing Stripe webhook: {e}", exc_info=True)
            audit_emitter.emit_security_event(
                "stripe_webhook_processing_error",
                {"error": str(e), "ip": request.remote_addr},
            )
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to process webhook", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/webhooks/paypal", methods=["POST"])
    async def paypal_webhook():
        """Handle PayPal webhook events."""
        try:
            event_data = await request.get_json()

            if not event_data:
                return (
                    jsonify(ErrorResponse(error="Invalid webhook data").model_dump()),
                    400,
                )

            headers = dict(request.headers)
            body = await request.get_data()

            is_verified = await payment_service.verify_paypal_webhook(
                headers, body.decode("utf-8")
            )
            if not is_verified:
                logger.warning("PayPal webhook verification failed.")
                return (
                    jsonify(
                        ErrorResponse(error="Invalid PayPal signature").model_dump()
                    ),
                    400,
                )

            await payment_service.handle_paypal_webhook(event_data)

            return jsonify({"success": True, "processed": True}), 200

        except Exception as e:
            logger.error(f"Error processing PayPal webhook: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to process webhook", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/webhooks/process", methods=["POST"])
    @require_api_key(["admin"])
    @validate_request(ProcessWebhookRequest)
    async def process_webhook(data: ProcessWebhookRequest):
        """Process webhook events manually."""
        try:
            if data.provider.lower() == "stripe":
                await payment_service.handle_stripe_webhook(data.event_data)
            elif data.provider.lower() == "paypal":
                await payment_service.handle_paypal_webhook(data.event_data)
            else:
                return (
                    jsonify(
                        ErrorResponse(
                            error=f"Unsupported webhook provider: {data.provider}"
                        ).model_dump()
                    ),
                    400,
                )

            response = WebhookResponse(
                success=True,
                processed_events=1,
                failed_events=0,
                details=[
                    {
                        "provider": data.provider,
                        "event_type": data.event_type,
                        "status": "processed",
                    }
                ],
            )

            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to process webhook", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    # --- Analytics Endpoints ---

    @blueprint.route("/analytics", methods=["POST"])
    @require_api_key(["read", "admin"])
    @validate_request(PaymentAnalyticsRequest)
    async def get_payment_analytics(data: PaymentAnalyticsRequest):
        """Get payment analytics and insights."""
        try:
            async with engine_getter() as engine:
                payment_service = await engine.get_payment_service()
                analytics_data = await payment_service.get_payment_analytics(
                    time_range=data.time_range,
                    user_ids=data.user_ids,
                    payment_methods=data.payment_methods,
                )
                response = PaymentAnalyticsResponse(**analytics_data)
                return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"Error generating payment analytics: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to generate payment analytics", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/health", methods=["GET"])
    async def payment_health_check():
        """Check payment system health."""
        try:
            health_status = {
                "payment_service": "healthy",
                "stripe_integration": "healthy"
                if payment_service.stripe_enabled
                else "disabled",
                "paypal_integration": "healthy"
                if payment_service.paypal_enabled
                else "disabled",
                "crypto_integration": "disabled",  # Mock status
                "pending_transactions": len(
                    [
                        tx
                        for tx in payment_service.transactions.values()
                        if tx.status == PaymentStatus.PENDING
                    ]
                ),
                "processing_transactions": len(
                    [
                        tx
                        for tx in payment_service.transactions.values()
                        if tx.status == PaymentStatus.PROCESSING
                    ]
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            return jsonify(health_status), 200

        except Exception as e:
            logger.error(f"Error checking payment health: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to check payment health", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    return blueprint


# --- Helper Functions ---


def _get_estimated_completion(payout_method: str) -> str:
    """Get estimated completion time for payout method."""
    completion_times = {
        "paypal": "1-3 business days",
        "stripe": "2-5 business days",
        "crypto": "10-30 minutes",
        "bank_transfer": "3-7 business days",
    }
    return completion_times.get(payout_method.lower(), "3-5 business days")


def _validate_payout_details(
    payout_method: PayoutMethod, details: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate payout details for specific method."""

    if payout_method == PayoutMethod.PAYPAL:
        if not details.get("email"):
            return {"valid": False, "error": "PayPal email is required"}
    elif payout_method == PayoutMethod.STRIPE:
        if not details.get("bank_account") and not details.get("debit_card"):
            return {
                "valid": False,
                "error": "Bank account or debit card required for Stripe",
            }
    elif payout_method == PayoutMethod.CRYPTO:
        if not details.get("wallet_address") or not details.get("currency"):
            return {
                "valid": False,
                "error": "Wallet address and currency required for crypto",
            }
    elif payout_method == PayoutMethod.BANK_TRANSFER:
        required_fields = ["account_number", "routing_number", "account_holder_name"]
        for field in required_fields:
            if not details.get(field):
                return {
                    "valid": False,
                    "error": f"{field} is required for bank transfer",
                }

    return {"valid": True}


def verify_webhook_signature(
    payload: bytes, signature: str, secret: str, provider: str
) -> bool:
    """Verify webhook signature for security."""
    if not signature or not secret:
        return False

    try:
        if provider == "stripe":
            import stripe

            # Use Stripe's built-in verification
            stripe.Webhook.construct_event(payload, signature, secret)
            return True
        elif provider == "paypal":
            # PayPal webhook verification logic
            import hmac
            import hashlib

            expected_signature = hmac.new(
                secret.encode(), payload, hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.warning(f"Webhook signature verification failed for {provider}: {e}")
        return False

    return False


# SECURITY: Webhook rate limiting
webhook_rate_limits = defaultdict(list)


def check_webhook_rate_limit(
    ip_address: str, provider: str, max_requests: int = 100, window_minutes: int = 5
) -> bool:
    """Check webhook rate limits to prevent abuse."""
    from datetime import datetime, timedelta

    current_time = datetime.now()
    window_start = current_time - timedelta(minutes=window_minutes)

    # Clean old entries
    rate_key = f"{ip_address}:{provider}"
    webhook_rate_limits[rate_key] = [
        timestamp
        for timestamp in webhook_rate_limits[rate_key]
        if timestamp > window_start
    ]

    # Check current count
    if len(webhook_rate_limits[rate_key]) >= max_requests:
        return False

    # Add current request
    webhook_rate_limits[rate_key].append(current_time)
    return True
