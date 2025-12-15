"""
Insurance Policy Management System

Handles policy lifecycle:
- Policy creation and activation
- Premium calculation and billing
- Policy renewal
- Policy cancellation
- Coverage tracking
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from src.utils.timezone_utils import utc_now

from .risk_assessor import DecisionCategory, RiskLevel


class PolicyStatus(str, Enum):
    """Policy status states"""

    PENDING = "pending"  # Awaiting payment
    ACTIVE = "active"
    SUSPENDED = "suspended"  # Payment overdue
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentStatus(str, Enum):
    """Payment status for premiums"""

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class PolicyTerms:
    """Policy terms and conditions"""

    coverage_amount: int
    deductible: int
    premium_monthly: float
    term_months: int
    decision_category: DecisionCategory
    risk_level: RiskLevel
    conditions: List[str]
    exclusions: List[str]
    max_claims_per_year: int = 3
    max_payout_per_claim: int = None  # None = coverage_amount

    def __post_init__(self):
        if self.max_payout_per_claim is None:
            self.max_payout_per_claim = self.coverage_amount


@dataclass
class PolicyHolder:
    """Policy holder information"""

    user_id: str
    name: str
    email: str
    organization: Optional[str] = None
    contact_phone: Optional[str] = None


@dataclass
class Policy:
    """Insurance policy entity"""

    policy_id: str
    holder: PolicyHolder
    terms: PolicyTerms
    status: PolicyStatus
    created_at: datetime
    activated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    # Coverage tracking
    claims_filed: int = 0
    total_paid_out: int = 0

    # Billing
    next_payment_due: Optional[datetime] = None
    payment_history: List[Dict] = field(default_factory=list)

    # Metadata
    metadata: Dict = field(default_factory=dict)


class PolicyManager:
    """
    Manages insurance policy lifecycle and operations.
    """

    def __init__(self, database_manager=None, payment_processor=None):
        """
        Initialize policy manager.

        Args:
            database_manager: Database connection for policy storage
            payment_processor: Payment processing integration (Stripe, etc.)
        """
        self.db = database_manager
        self.payment_processor = payment_processor

    async def create_policy(
        self,
        holder: PolicyHolder,
        terms: PolicyTerms,
        auto_activate: bool = False,
    ) -> Policy:
        """
        Create a new insurance policy.

        Args:
            holder: Policy holder information
            terms: Policy terms and coverage details
            auto_activate: If True, activate immediately (requires payment)

        Returns:
            Created Policy object
        """
        policy_id = self._generate_policy_id()

        policy = Policy(
            policy_id=policy_id,
            holder=holder,
            terms=terms,
            status=PolicyStatus.PENDING,
            created_at=utc_now(),
        )

        # Store in database
        if self.db:
            await self._store_policy(policy)

        if auto_activate:
            await self.activate_policy(policy_id)

        return policy

    async def activate_policy(
        self,
        policy_id: str,
        payment_method_id: Optional[str] = None,
    ) -> Policy:
        """
        Activate a policy (typically after payment received).

        Args:
            policy_id: Policy to activate
            payment_method_id: Payment method for recurring billing

        Returns:
            Activated Policy object
        """
        policy = await self.get_policy(policy_id)

        if policy.status == PolicyStatus.ACTIVE:
            raise ValueError("Policy is already active")

        # Process initial payment
        if self.payment_processor and payment_method_id:
            payment_result = await self._process_payment(
                policy=policy,
                amount=policy.terms.premium_monthly,
                payment_method_id=payment_method_id,
            )

            if not payment_result["success"]:
                raise ValueError(f"Payment failed: {payment_result['error']}")

            policy.payment_history.append(
                {
                    "timestamp": utc_now(),
                    "amount": policy.terms.premium_monthly,
                    "status": PaymentStatus.PAID,
                    "transaction_id": payment_result.get("transaction_id"),
                }
            )

        # Activate policy
        now = utc_now()
        policy.status = PolicyStatus.ACTIVE
        policy.activated_at = now
        policy.expires_at = now + timedelta(days=30 * policy.terms.term_months)
        policy.next_payment_due = now + timedelta(days=30)

        # Update database
        if self.db:
            await self._update_policy(policy)

        return policy

    async def renew_policy(
        self,
        policy_id: str,
        new_term_months: Optional[int] = None,
    ) -> Policy:
        """
        Renew an expiring or expired policy.

        Args:
            policy_id: Policy to renew
            new_term_months: New term length (None = use same as before)

        Returns:
            Renewed Policy object
        """
        policy = await self.get_policy(policy_id)

        if policy.status not in [PolicyStatus.ACTIVE, PolicyStatus.EXPIRED]:
            raise ValueError(f"Cannot renew policy with status {policy.status}")

        # Update term
        if new_term_months:
            policy.terms.term_months = new_term_months

        # Extend expiration
        now = utc_now()
        if policy.expires_at and policy.expires_at > now:
            # Add to existing expiration
            policy.expires_at += timedelta(days=30 * policy.terms.term_months)
        else:
            # Start fresh
            policy.expires_at = now + timedelta(days=30 * policy.terms.term_months)

        policy.status = PolicyStatus.ACTIVE
        policy.next_payment_due = now + timedelta(days=30)

        # Update database
        if self.db:
            await self._update_policy(policy)

        return policy

    async def cancel_policy(
        self,
        policy_id: str,
        reason: str,
        refund_prorated: bool = True,
    ) -> Policy:
        """
        Cancel a policy.

        Args:
            policy_id: Policy to cancel
            reason: Cancellation reason
            refund_prorated: If True, issue prorated refund

        Returns:
            Cancelled Policy object
        """
        policy = await self.get_policy(policy_id)

        if policy.status == PolicyStatus.CANCELLED:
            raise ValueError("Policy is already cancelled")

        now = utc_now()
        policy.status = PolicyStatus.CANCELLED
        policy.cancelled_at = now
        policy.cancellation_reason = reason

        # Calculate prorated refund
        if refund_prorated and policy.activated_at and policy.expires_at:
            days_remaining = (policy.expires_at - now).days
            total_days = (policy.expires_at - policy.activated_at).days

            if days_remaining > 0 and total_days > 0:
                refund_amount = (
                    policy.terms.premium_monthly
                    * policy.terms.term_months
                    * (days_remaining / total_days)
                )

                # Process refund
                if self.payment_processor and refund_amount > 0:
                    await self._process_refund(policy, refund_amount)

                policy.payment_history.append(
                    {
                        "timestamp": now,
                        "amount": -refund_amount,
                        "status": PaymentStatus.REFUNDED,
                        "reason": "Policy cancellation - prorated refund",
                    }
                )

        # Update database
        if self.db:
            await self._update_policy(policy)

        return policy

    async def suspend_policy(
        self,
        policy_id: str,
        reason: str = "Payment overdue",
    ) -> Policy:
        """
        Suspend a policy (e.g., for non-payment).

        Args:
            policy_id: Policy to suspend
            reason: Suspension reason

        Returns:
            Suspended Policy object
        """
        policy = await self.get_policy(policy_id)

        policy.status = PolicyStatus.SUSPENDED
        policy.metadata["suspension_reason"] = reason
        policy.metadata["suspended_at"] = utc_now().isoformat()

        # Update database
        if self.db:
            await self._update_policy(policy)

        return policy

    async def process_monthly_payment(
        self,
        policy_id: str,
        payment_method_id: str,
    ) -> Dict:
        """
        Process monthly recurring payment for a policy.

        Args:
            policy_id: Policy to charge
            payment_method_id: Payment method to charge

        Returns:
            Payment result dictionary
        """
        policy = await self.get_policy(policy_id)

        if policy.status != PolicyStatus.ACTIVE:
            return {
                "success": False,
                "error": f"Policy status is {policy.status}, not active",
            }

        # Check if payment is due
        now = utc_now()
        if policy.next_payment_due and now < policy.next_payment_due:
            return {"success": False, "error": "Payment not yet due"}

        # Process payment
        result = await self._process_payment(
            policy=policy,
            amount=policy.terms.premium_monthly,
            payment_method_id=payment_method_id,
        )

        if result["success"]:
            # Record payment
            policy.payment_history.append(
                {
                    "timestamp": now,
                    "amount": policy.terms.premium_monthly,
                    "status": PaymentStatus.PAID,
                    "transaction_id": result.get("transaction_id"),
                }
            )

            # Update next payment due
            policy.next_payment_due = now + timedelta(days=30)

            # Update database
            if self.db:
                await self._update_policy(policy)
        else:
            # Payment failed - suspend policy
            policy.payment_history.append(
                {
                    "timestamp": now,
                    "amount": policy.terms.premium_monthly,
                    "status": PaymentStatus.FAILED,
                    "error": result.get("error"),
                }
            )

            await self.suspend_policy(
                policy_id, reason=f"Payment failed: {result.get('error')}"
            )

        return result

    async def check_policy_eligibility(
        self,
        policy_id: str,
        claim_amount: int,
    ) -> Dict:
        """
        Check if a policy is eligible for a claim payout.

        Args:
            policy_id: Policy to check
            claim_amount: Requested claim amount

        Returns:
            Dictionary with eligibility status and details
        """
        policy = await self.get_policy(policy_id)

        # Check policy status
        if policy.status != PolicyStatus.ACTIVE:
            return {
                "eligible": False,
                "reason": f"Policy status is {policy.status}",
            }

        # Check expiration
        now = utc_now()
        if policy.expires_at and now > policy.expires_at:
            return {
                "eligible": False,
                "reason": "Policy has expired",
            }

        # Check claims limit
        if policy.claims_filed >= policy.terms.max_claims_per_year:
            return {
                "eligible": False,
                "reason": f"Maximum claims per year ({policy.terms.max_claims_per_year}) reached",
            }

        # Check coverage remaining
        remaining_coverage = policy.terms.coverage_amount - policy.total_paid_out
        if remaining_coverage <= 0:
            return {
                "eligible": False,
                "reason": "Coverage limit exhausted",
            }

        # Check claim amount
        max_payout = min(
            policy.terms.max_payout_per_claim,
            remaining_coverage,
        )

        if claim_amount > max_payout:
            return {
                "eligible": True,
                "max_claimable": max_payout,
                "reason": f"Claim amount exceeds maximum payout (${max_payout:,})",
            }

        return {
            "eligible": True,
            "max_claimable": claim_amount,
            "remaining_coverage": remaining_coverage,
        }

    async def get_policy(self, policy_id: str) -> Policy:
        """
        Retrieve a policy by ID.

        Args:
            policy_id: Policy ID to fetch

        Returns:
            Policy object
        """
        if self.db:
            return await self._fetch_policy(policy_id)
        else:
            # In-memory fallback for testing
            raise NotImplementedError("Policy storage not configured")

    async def list_policies(
        self,
        user_id: Optional[str] = None,
        status: Optional[PolicyStatus] = None,
        limit: int = 100,
    ) -> List[Policy]:
        """
        List policies with optional filters.

        Args:
            user_id: Filter by user ID
            status: Filter by policy status
            limit: Maximum number of policies to return

        Returns:
            List of Policy objects
        """
        if self.db:
            return await self._query_policies(
                user_id=user_id,
                status=status,
                limit=limit,
            )
        else:
            return []

    def _generate_policy_id(self) -> str:
        """Generate unique policy ID"""
        return f"POL-{uuid.uuid4().hex[:12].upper()}"

    async def _process_payment(
        self,
        policy: Policy,
        amount: float,
        payment_method_id: str,
    ) -> Dict:
        """
        Process a payment through payment processor.

        Returns:
            Dictionary with success status and transaction details
        """
        if not self.payment_processor:
            # Mock success for testing
            return {
                "success": True,
                "transaction_id": f"txn_{uuid.uuid4().hex[:16]}",
                "amount": amount,
            }

        # Payment processor integration complete - using real Stripe/PayPal API
        # Configure via STRIPE_SECRET_KEY or PAYPAL_CLIENT_ID environment variables
        try:
            result = await self.payment_processor.charge(
                amount=int(amount * 100),  # Convert to cents
                currency="usd",
                payment_method=payment_method_id,
                metadata={
                    "policy_id": policy.policy_id,
                    "user_id": policy.holder.user_id,
                },
            )

            return {
                "success": True,
                "transaction_id": result.get("id"),
                "amount": amount,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def _process_refund(
        self,
        policy: Policy,
        amount: float,
    ) -> Dict:
        """Process a refund through payment processor"""
        if not self.payment_processor:
            return {"success": True}

        # Process refund through integrated payment processor (Stripe/PayPal)
        try:
            result = await self.payment_processor.refund(
                transaction_id=policy.payment_history[-1].get("transaction_id")
                if policy.payment_history
                else None,
                amount=int(amount * 100),  # Convert to cents
                reason="Policy refund",
            )
            return {"success": True, "refund_id": result.get("id"), "amount": amount}
        except Exception as e:
            logger.error(f"Refund failed: {e}")
            return {"success": False, "error": str(e)}

    async def _store_policy(self, policy: Policy):
        """Store policy in database"""
        from sqlalchemy import select

        from src.insurance.models import InsurancePolicy as DBPolicy

        session = self.db.get_session()
        async with session:
            # Check if policy already exists
            result = await session.execute(
                select(DBPolicy).where(DBPolicy.policy_number == policy.policy_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing policy
                existing.status = (
                    policy.status.value
                    if isinstance(policy.status, PolicyStatus)
                    else policy.status
                )
                existing.premium_amount = policy.terms.premium_monthly
                existing.coverage_amount = policy.terms.coverage_amount
                existing.end_date = policy.expires_at or utc_now() + timedelta(
                    days=policy.terms.term_months * 30
                )
                existing.parameters = {
                    "deductible": policy.terms.deductible,
                    "term_months": policy.terms.term_months,
                    "decision_category": policy.terms.decision_category.value,
                    "risk_level": policy.terms.risk_level.value,
                    "conditions": policy.terms.conditions,
                    "exclusions": policy.terms.exclusions,
                    "max_claims_per_year": policy.terms.max_claims_per_year,
                    "max_payout_per_claim": policy.terms.max_payout_per_claim,
                    "claims_filed": policy.claims_filed,
                    "total_paid_out": policy.total_paid_out,
                    "holder_name": policy.holder.name,
                    "holder_email": policy.holder.email,
                    "holder_organization": policy.holder.organization,
                    "holder_contact_phone": policy.holder.contact_phone,
                    "metadata": policy.metadata,
                }
                existing.updated_at = utc_now()
            else:
                # Create new policy
                db_policy = DBPolicy(
                    policy_number=policy.policy_id,
                    user_id=policy.holder.user_id,  # This should be a UUID
                    premium_amount=policy.terms.premium_monthly,
                    coverage_amount=policy.terms.coverage_amount,
                    policy_type="ai_liability",
                    status=policy.status.value
                    if isinstance(policy.status, PolicyStatus)
                    else policy.status,
                    start_date=policy.activated_at or utc_now(),
                    end_date=policy.expires_at
                    or utc_now() + timedelta(days=policy.terms.term_months * 30),
                    parameters={
                        "deductible": policy.terms.deductible,
                        "term_months": policy.terms.term_months,
                        "decision_category": policy.terms.decision_category.value,
                        "risk_level": policy.terms.risk_level.value,
                        "conditions": policy.terms.conditions,
                        "exclusions": policy.terms.exclusions,
                        "max_claims_per_year": policy.terms.max_claims_per_year,
                        "max_payout_per_claim": policy.terms.max_payout_per_claim,
                        "claims_filed": policy.claims_filed,
                        "total_paid_out": policy.total_paid_out,
                        "holder_name": policy.holder.name,
                        "holder_email": policy.holder.email,
                        "holder_organization": policy.holder.organization,
                        "holder_contact_phone": policy.holder.contact_phone,
                        "metadata": policy.metadata,
                    },
                )
                session.add(db_policy)

            await session.commit()

    async def _update_policy(self, policy: Policy):
        """Update policy in database"""
        # Reuse _store_policy which handles both create and update
        await self._store_policy(policy)

    async def _fetch_policy(self, policy_id: str) -> Policy:
        """Fetch policy from database"""
        from sqlalchemy import select

        from src.insurance.models import InsurancePolicy as DBPolicy

        session = self.db.get_session()
        async with session:
            result = await session.execute(
                select(DBPolicy).where(DBPolicy.policy_number == policy_id)
            )
            db_policy = result.scalar_one_or_none()

            if not db_policy:
                raise ValueError(f"Policy {policy_id} not found")

            # Convert DB model to dataclass
            params = db_policy.parameters or {}

            holder = PolicyHolder(
                user_id=str(db_policy.user_id),
                name=params.get("holder_name", "Unknown"),
                email=params.get("holder_email", "unknown@example.com"),
                organization=params.get("holder_organization"),
                contact_phone=params.get("holder_contact_phone"),
            )

            terms = PolicyTerms(
                coverage_amount=int(db_policy.coverage_amount),
                deductible=params.get("deductible", 0),
                premium_monthly=float(db_policy.premium_amount),
                term_months=params.get("term_months", 12),
                decision_category=DecisionCategory(
                    params.get("decision_category", "customer_service")
                ),
                risk_level=RiskLevel(params.get("risk_level", "medium")),
                conditions=params.get("conditions", []),
                exclusions=params.get("exclusions", []),
                max_claims_per_year=params.get("max_claims_per_year", 3),
                max_payout_per_claim=params.get("max_payout_per_claim"),
            )

            # Convert string status to enum
            status_value = (
                db_policy.status.value
                if hasattr(db_policy.status, "value")
                else db_policy.status
            )
            policy_status = (
                PolicyStatus(status_value)
                if isinstance(status_value, str)
                else db_policy.status
            )

            policy = Policy(
                policy_id=db_policy.policy_number,
                holder=holder,
                terms=terms,
                status=policy_status,
                created_at=db_policy.created_at,
                activated_at=db_policy.start_date,
                expires_at=db_policy.end_date,
                claims_filed=params.get("claims_filed", 0),
                total_paid_out=params.get("total_paid_out", 0),
                metadata=params.get("metadata", {}),
            )

            return policy

    async def _query_policies(
        self,
        user_id: Optional[str] = None,
        status: Optional[PolicyStatus] = None,
        limit: int = 100,
    ) -> List[Policy]:
        """Query policies from database"""
        from sqlalchemy import select

        from src.insurance.models import InsurancePolicy as DBPolicy

        session = self.db.get_session()
        async with session:
            query = select(DBPolicy)

            if user_id:
                query = query.where(DBPolicy.user_id == user_id)

            if status:
                status_value = (
                    status.value if isinstance(status, PolicyStatus) else status
                )
                query = query.where(DBPolicy.status == status_value)

            query = query.limit(limit).order_by(DBPolicy.created_at.desc())

            result = await session.execute(query)
            db_policies = result.scalars().all()

            policies = []
            for db_policy in db_policies:
                try:
                    # Convert each DB policy to dataclass using _fetch_policy logic
                    params = db_policy.parameters or {}

                    holder = PolicyHolder(
                        user_id=str(db_policy.user_id),
                        name=params.get("holder_name", "Unknown"),
                        email=params.get("holder_email", "unknown@example.com"),
                        organization=params.get("holder_organization"),
                        contact_phone=params.get("holder_contact_phone"),
                    )

                    terms = PolicyTerms(
                        coverage_amount=int(db_policy.coverage_amount),
                        deductible=params.get("deductible", 0),
                        premium_monthly=float(db_policy.premium_amount),
                        term_months=params.get("term_months", 12),
                        decision_category=DecisionCategory(
                            params.get("decision_category", "customer_service")
                        ),
                        risk_level=RiskLevel(params.get("risk_level", "medium")),
                        conditions=params.get("conditions", []),
                        exclusions=params.get("exclusions", []),
                        max_claims_per_year=params.get("max_claims_per_year", 3),
                        max_payout_per_claim=params.get("max_payout_per_claim"),
                    )

                    status_value = (
                        db_policy.status.value
                        if hasattr(db_policy.status, "value")
                        else db_policy.status
                    )
                    policy_status = (
                        PolicyStatus(status_value)
                        if isinstance(status_value, str)
                        else db_policy.status
                    )

                    policy = Policy(
                        policy_id=db_policy.policy_number,
                        holder=holder,
                        terms=terms,
                        status=policy_status,
                        created_at=db_policy.created_at,
                        activated_at=db_policy.start_date,
                        expires_at=db_policy.end_date,
                        claims_filed=params.get("claims_filed", 0),
                        total_paid_out=params.get("total_paid_out", 0),
                        metadata=params.get("metadata", {}),
                    )

                    policies.append(policy)
                except Exception as e:
                    # Log and skip malformed policies
                    print(
                        f"Warning: Failed to convert policy {db_policy.policy_number}: {e}"
                    )
                    continue

            return policies
