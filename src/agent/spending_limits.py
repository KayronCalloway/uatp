"""
Agent Spending Limits & Economic Constraints

Implements budget controls and spending tracking for autonomous AI agents.

Key Features:
- Per-agent budget limits (daily, monthly, lifetime)
- Real-time spending validation
- Budget alerts and notifications
- Approval workflows for over-budget spending
- Integration with economic engine (FCDE)
- Audit logging of all spending decisions

Prevents scenarios like:
- Rogue agent spending unlimited funds
- Agent making expensive API calls without limit
- Agent creating infinite capsules
- Agent triggering costly operations

Usage:
    from src.agent.spending_limits import AgentSpendingManager

    manager = AgentSpendingManager()

    # Set agent budget
    await manager.set_agent_budget(
        agent_id="agent_123",
        daily_limit=100.00,
        monthly_limit=1000.00,
        currency="USD"
    )

    # Validate spending before operation
    can_spend = await manager.validate_spending(
        agent_id="agent_123",
        amount=10.50,
        operation="create_capsule"
    )

    if not can_spend:
        raise InsufficientBudgetError("Agent over budget")

    # Record actual spending
    await manager.record_spending(
        agent_id="agent_123",
        amount=10.50,
        operation="create_capsule",
        metadata={"capsule_id": "cap_123"}
    )
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentBudget:
    """Budget configuration for an AI agent"""

    agent_id: str
    daily_limit: Decimal
    monthly_limit: Decimal
    lifetime_limit: Optional[Decimal] = None
    currency: str = "USD"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpendingRecord:
    """Record of agent spending"""

    spending_id: str
    agent_id: str
    amount: Decimal
    operation: str  # Type of operation (e.g., "create_capsule", "api_call")
    timestamp: str
    approved: bool
    approval_method: str  # "automatic", "human_approved", "budget_override"
    metadata: Dict[str, Any]


@dataclass
class BudgetAlert:
    """Alert when agent approaches or exceeds budget"""

    alert_id: str
    agent_id: str
    alert_type: str  # "approaching_limit", "limit_exceeded", "unusual_spending"
    severity: str  # "warning", "critical"
    message: str
    current_spending: Decimal
    limit: Decimal
    period: str  # "daily", "monthly", "lifetime"
    timestamp: str
    acknowledged: bool = False


class InsufficientBudgetError(Exception):
    """Raised when agent doesn't have sufficient budget"""

    pass


class AgentSpendingManager:
    """
    Manages agent spending limits and budget tracking.

    This system provides:
    1. Budget configuration per agent
    2. Real-time spending validation
    3. Spending tracking and audit trail
    4. Budget alerts and notifications
    5. Approval workflows for over-budget requests
    """

    def __init__(
        self,
        storage_path: str = "economic/agent_spending",
        alert_threshold: float = 0.80,  # Alert at 80% of budget
    ):
        """
        Initialize spending manager.

        Args:
            storage_path: Directory for spending data
            alert_threshold: Percentage threshold for budget alerts (0-1)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.alert_threshold = alert_threshold

        # In-memory caches
        self.budgets: Dict[str, AgentBudget] = {}
        self.spending_cache: Dict[str, List[SpendingRecord]] = {}  # agent_id -> records

        # Load existing data
        self._load_budgets()

    def _load_budgets(self):
        """Load agent budgets from storage"""
        budget_file = self.storage_path / "agent_budgets.jsonl"

        if not budget_file.exists():
            return

        with open(budget_file) as f:
            for line in f:
                budget_dict = json.loads(line)
                # Convert string to Decimal
                budget_dict["daily_limit"] = Decimal(str(budget_dict["daily_limit"]))
                budget_dict["monthly_limit"] = Decimal(
                    str(budget_dict["monthly_limit"])
                )
                if budget_dict.get("lifetime_limit"):
                    budget_dict["lifetime_limit"] = Decimal(
                        str(budget_dict["lifetime_limit"])
                    )

                budget = AgentBudget(**budget_dict)
                self.budgets[budget.agent_id] = budget

    def _save_budget(self, budget: AgentBudget):
        """Save budget to storage"""
        budget_file = self.storage_path / "agent_budgets.jsonl"

        # Convert Decimal to string for JSON serialization
        budget_dict = asdict(budget)
        budget_dict["daily_limit"] = str(budget_dict["daily_limit"])
        budget_dict["monthly_limit"] = str(budget_dict["monthly_limit"])
        if budget_dict.get("lifetime_limit"):
            budget_dict["lifetime_limit"] = str(budget_dict["lifetime_limit"])

        with open(budget_file, "a") as f:
            f.write(json.dumps(budget_dict) + "\n")

    def _save_spending(self, record: SpendingRecord):
        """Save spending record to storage"""
        spending_file = self.storage_path / "spending_records.jsonl"

        # Convert Decimal to string
        record_dict = asdict(record)
        record_dict["amount"] = str(record_dict["amount"])

        with open(spending_file, "a") as f:
            f.write(json.dumps(record_dict) + "\n")

    def _save_alert(self, alert: BudgetAlert):
        """Save budget alert to storage"""
        alerts_file = self.storage_path / "budget_alerts.jsonl"

        # Convert Decimal to string
        alert_dict = asdict(alert)
        alert_dict["current_spending"] = str(alert_dict["current_spending"])
        alert_dict["limit"] = str(alert_dict["limit"])

        with open(alerts_file, "a") as f:
            f.write(json.dumps(alert_dict) + "\n")

    async def set_agent_budget(
        self,
        agent_id: str,
        daily_limit: float,
        monthly_limit: float,
        lifetime_limit: Optional[float] = None,
        currency: str = "USD",
        metadata: Optional[Dict] = None,
    ) -> AgentBudget:
        """
        Set budget limits for an agent.

        Args:
            agent_id: Agent ID
            daily_limit: Daily spending limit
            monthly_limit: Monthly spending limit
            lifetime_limit: Optional lifetime spending limit
            currency: Currency code (default: USD)
            metadata: Additional metadata

        Returns:
            AgentBudget object
        """
        budget = AgentBudget(
            agent_id=agent_id,
            daily_limit=Decimal(str(daily_limit)),
            monthly_limit=Decimal(str(monthly_limit)),
            lifetime_limit=Decimal(str(lifetime_limit)) if lifetime_limit else None,
            currency=currency,
            updated_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

        self.budgets[agent_id] = budget
        self._save_budget(budget)

        logger.info(
            f"Set budget for agent {agent_id}: "
            f"Daily ${daily_limit}, Monthly ${monthly_limit}, Currency {currency}"
        )

        # Emit audit event
        try:
            from src.audit.events import audit_emitter

            audit_emitter.emit_security_event(
                event_name="agent_budget_set",
                metadata={
                    "agent_id": agent_id,
                    "daily_limit": daily_limit,
                    "monthly_limit": monthly_limit,
                    "currency": currency,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event: {e}")

        return budget

    async def get_agent_spending(self, agent_id: str, period: str = "daily") -> Decimal:
        """
        Get agent's spending for a period.

        Args:
            agent_id: Agent ID
            period: "daily", "monthly", or "lifetime"

        Returns:
            Total spending amount
        """
        now = datetime.now(timezone.utc)

        # Determine time window
        if period == "daily":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "monthly":
            start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "lifetime":
            start_time = datetime.min.replace(tzinfo=timezone.utc)
        else:
            raise ValueError(f"Invalid period: {period}")

        # Load spending records from storage
        spending_file = self.storage_path / "spending_records.jsonl"

        if not spending_file.exists():
            return Decimal("0")

        total_spending = Decimal("0")

        with open(spending_file) as f:
            for line in f:
                record_dict = json.loads(line)

                if record_dict["agent_id"] != agent_id:
                    continue

                record_time = datetime.fromisoformat(record_dict["timestamp"])

                if record_time >= start_time and record_dict["approved"]:
                    total_spending += Decimal(record_dict["amount"])

        return total_spending

    async def validate_spending(
        self,
        agent_id: str,
        amount: float,
        operation: str,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Validate if agent can spend amount.

        Args:
            agent_id: Agent ID
            amount: Amount to spend
            operation: Type of operation
            metadata: Additional context

        Returns:
            Dict with validation result:
            {
                "approved": bool,
                "reason": str,
                "requires_human_approval": bool
            }
        """
        amount_decimal = Decimal(str(amount))

        # Check if budget exists
        budget = self.budgets.get(agent_id)
        if not budget:
            logger.warning(f"No budget configured for agent {agent_id}")
            return {
                "approved": False,
                "reason": "No budget configured for agent",
                "requires_human_approval": True,
            }

        # Get current spending
        daily_spending = await self.get_agent_spending(agent_id, "daily")
        monthly_spending = await self.get_agent_spending(agent_id, "monthly")

        # Check daily limit
        if daily_spending + amount_decimal > budget.daily_limit:
            logger.warning(
                f"Agent {agent_id} exceeds daily limit: "
                f"${daily_spending + amount_decimal} > ${budget.daily_limit}"
            )

            # Create alert
            await self._create_alert(
                agent_id=agent_id,
                alert_type="limit_exceeded",
                severity="critical",
                message="Daily spending limit exceeded",
                current_spending=daily_spending + amount_decimal,
                limit=budget.daily_limit,
                period="daily",
            )

            return {
                "approved": False,
                "reason": f"Exceeds daily limit (${budget.daily_limit})",
                "current_spending": float(daily_spending),
                "requires_human_approval": True,
            }

        # Check monthly limit
        if monthly_spending + amount_decimal > budget.monthly_limit:
            logger.warning(
                f"Agent {agent_id} exceeds monthly limit: "
                f"${monthly_spending + amount_decimal} > ${budget.monthly_limit}"
            )

            await self._create_alert(
                agent_id=agent_id,
                alert_type="limit_exceeded",
                severity="critical",
                message="Monthly spending limit exceeded",
                current_spending=monthly_spending + amount_decimal,
                limit=budget.monthly_limit,
                period="monthly",
            )

            return {
                "approved": False,
                "reason": f"Exceeds monthly limit (${budget.monthly_limit})",
                "current_spending": float(monthly_spending),
                "requires_human_approval": True,
            }

        # Check if approaching limits (80% threshold)
        if daily_spending + amount_decimal > budget.daily_limit * Decimal(
            str(self.alert_threshold)
        ):
            await self._create_alert(
                agent_id=agent_id,
                alert_type="approaching_limit",
                severity="warning",
                message="Approaching daily spending limit",
                current_spending=daily_spending + amount_decimal,
                limit=budget.daily_limit,
                period="daily",
            )

        # Approved
        logger.info(
            f"Spending validated for agent {agent_id}: ${amount} for {operation}"
        )

        return {
            "approved": True,
            "reason": "Within budget limits",
            "current_daily_spending": float(daily_spending),
            "current_monthly_spending": float(monthly_spending),
            "remaining_daily": float(budget.daily_limit - daily_spending),
            "remaining_monthly": float(budget.monthly_limit - monthly_spending),
        }

    async def record_spending(
        self,
        agent_id: str,
        amount: float,
        operation: str,
        approved: bool = True,
        approval_method: str = "automatic",
        metadata: Optional[Dict] = None,
    ) -> SpendingRecord:
        """
        Record actual agent spending.

        Args:
            agent_id: Agent ID
            amount: Amount spent
            operation: Type of operation
            approved: Whether spending was approved
            approval_method: How it was approved
            metadata: Additional context

        Returns:
            SpendingRecord object
        """
        import secrets

        spending_id = f"spend_{secrets.token_hex(16)}"

        record = SpendingRecord(
            spending_id=spending_id,
            agent_id=agent_id,
            amount=Decimal(str(amount)),
            operation=operation,
            timestamp=datetime.now(timezone.utc).isoformat(),
            approved=approved,
            approval_method=approval_method,
            metadata=metadata or {},
        )

        self._save_spending(record)

        logger.info(
            f"Recorded spending for agent {agent_id}: "
            f"${amount} for {operation} ({approval_method})"
        )

        # Emit audit event
        try:
            from src.audit.events import audit_emitter

            audit_emitter.emit_economic_event(
                event_name="agent_spending_recorded",
                metadata={
                    "agent_id": agent_id,
                    "spending_id": spending_id,
                    "amount": amount,
                    "operation": operation,
                    "approved": approved,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event: {e}")

        return record

    async def _create_alert(
        self,
        agent_id: str,
        alert_type: str,
        severity: str,
        message: str,
        current_spending: Decimal,
        limit: Decimal,
        period: str,
    ) -> BudgetAlert:
        """Create and store budget alert"""
        import secrets

        alert_id = f"alert_{secrets.token_hex(16)}"

        alert = BudgetAlert(
            alert_id=alert_id,
            agent_id=agent_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            current_spending=current_spending,
            limit=limit,
            period=period,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        self._save_alert(alert)

        # Log critical alerts
        if severity == "critical":
            logger.critical(
                f" BUDGET ALERT: Agent {agent_id} - {message} "
                f"(${current_spending} / ${limit} {period})"
            )
        else:
            logger.warning(
                f"[WARN] Budget Warning: Agent {agent_id} - {message} "
                f"(${current_spending} / ${limit} {period})"
            )

        # Emit audit event
        try:
            from src.audit.events import audit_emitter

            audit_emitter.emit_security_event(
                event_name="agent_budget_alert",
                metadata={
                    "alert_id": alert_id,
                    "agent_id": agent_id,
                    "alert_type": alert_type,
                    "severity": severity,
                    "current_spending": float(current_spending),
                    "limit": float(limit),
                    "period": period,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event: {e}")

        return alert

    def get_agent_budget(self, agent_id: str) -> Optional[AgentBudget]:
        """Get agent's budget configuration"""
        return self.budgets.get(agent_id)

    async def get_spending_summary(self, agent_id: str) -> Dict[str, Any]:
        """
        Get comprehensive spending summary for agent.

        Returns:
            Dict with spending breakdown by period
        """
        budget = self.budgets.get(agent_id)

        daily_spending = await self.get_agent_spending(agent_id, "daily")
        monthly_spending = await self.get_agent_spending(agent_id, "monthly")
        lifetime_spending = await self.get_agent_spending(agent_id, "lifetime")

        return {
            "agent_id": agent_id,
            "budget": {
                "daily_limit": float(budget.daily_limit) if budget else None,
                "monthly_limit": float(budget.monthly_limit) if budget else None,
                "lifetime_limit": float(budget.lifetime_limit)
                if budget and budget.lifetime_limit
                else None,
                "currency": budget.currency if budget else "USD",
            },
            "spending": {
                "daily": float(daily_spending),
                "monthly": float(monthly_spending),
                "lifetime": float(lifetime_spending),
            },
            "remaining": {
                "daily": float(budget.daily_limit - daily_spending) if budget else None,
                "monthly": float(budget.monthly_limit - monthly_spending)
                if budget
                else None,
            },
            "utilization": {
                "daily_pct": float(daily_spending / budget.daily_limit * 100)
                if budget
                else None,
                "monthly_pct": float(monthly_spending / budget.monthly_limit * 100)
                if budget
                else None,
            },
        }


# Global spending manager
agent_spending_manager = AgentSpendingManager()
