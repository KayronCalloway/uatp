"""
Unit tests for Agent Spending Limits.
"""

import tempfile
from decimal import Decimal

import pytest

from src.agent.spending_limits import (
    AgentBudget,
    AgentSpendingManager,
    BudgetAlert,
    InsufficientBudgetError,
    SpendingRecord,
)


class TestAgentBudget:
    """Tests for AgentBudget dataclass."""

    def test_create_budget(self):
        """Test creating an agent budget."""
        budget = AgentBudget(
            agent_id="agent_123",
            daily_limit=Decimal("100.00"),
            monthly_limit=Decimal("1000.00"),
            currency="USD",
        )

        assert budget.agent_id == "agent_123"
        assert budget.daily_limit == Decimal("100.00")
        assert budget.monthly_limit == Decimal("1000.00")
        assert budget.currency == "USD"

    def test_budget_with_lifetime_limit(self):
        """Test budget with lifetime limit."""
        budget = AgentBudget(
            agent_id="agent_123",
            daily_limit=Decimal("100"),
            monthly_limit=Decimal("1000"),
            lifetime_limit=Decimal("50000"),
        )

        assert budget.lifetime_limit == Decimal("50000")

    def test_budget_default_currency(self):
        """Test default currency is USD."""
        budget = AgentBudget(
            agent_id="agent_123",
            daily_limit=Decimal("100"),
            monthly_limit=Decimal("1000"),
        )

        assert budget.currency == "USD"


class TestSpendingRecord:
    """Tests for SpendingRecord dataclass."""

    def test_create_record(self):
        """Test creating a spending record."""
        record = SpendingRecord(
            spending_id="spend_abc123",
            agent_id="agent_123",
            amount=Decimal("10.50"),
            operation="create_capsule",
            timestamp="2026-03-12T10:00:00+00:00",
            approved=True,
            approval_method="automatic",
            metadata={"capsule_id": "cap_123"},
        )

        assert record.spending_id == "spend_abc123"
        assert record.agent_id == "agent_123"
        assert record.amount == Decimal("10.50")
        assert record.operation == "create_capsule"
        assert record.approved is True
        assert record.metadata["capsule_id"] == "cap_123"


class TestBudgetAlert:
    """Tests for BudgetAlert dataclass."""

    def test_create_alert(self):
        """Test creating a budget alert."""
        alert = BudgetAlert(
            alert_id="alert_123",
            agent_id="agent_123",
            alert_type="limit_exceeded",
            severity="critical",
            message="Daily spending limit exceeded",
            current_spending=Decimal("110"),
            limit=Decimal("100"),
            period="daily",
            timestamp="2026-03-12T10:00:00+00:00",
        )

        assert alert.alert_type == "limit_exceeded"
        assert alert.severity == "critical"
        assert alert.acknowledged is False


class TestAgentSpendingManager:
    """Tests for AgentSpendingManager."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def manager(self, temp_storage):
        """Create a spending manager instance."""
        return AgentSpendingManager(storage_path=temp_storage)

    @pytest.mark.asyncio
    async def test_set_agent_budget(self, manager):
        """Test setting an agent budget."""
        budget = await manager.set_agent_budget(
            agent_id="agent_123",
            daily_limit=100.00,
            monthly_limit=1000.00,
            currency="USD",
        )

        assert budget.agent_id == "agent_123"
        assert budget.daily_limit == Decimal("100")
        assert budget.monthly_limit == Decimal("1000")

    @pytest.mark.asyncio
    async def test_set_agent_budget_with_metadata(self, manager):
        """Test setting budget with metadata."""
        budget = await manager.set_agent_budget(
            agent_id="agent_123",
            daily_limit=100.00,
            monthly_limit=1000.00,
            metadata={"tier": "premium"},
        )

        assert budget.metadata["tier"] == "premium"

    def test_get_agent_budget(self, manager, temp_storage):
        """Test getting agent budget."""
        # Manually add budget to cache
        budget = AgentBudget(
            agent_id="agent_456",
            daily_limit=Decimal("50"),
            monthly_limit=Decimal("500"),
        )
        manager.budgets["agent_456"] = budget

        result = manager.get_agent_budget("agent_456")
        assert result is not None
        assert result.daily_limit == Decimal("50")

    def test_get_agent_budget_not_found(self, manager):
        """Test getting non-existent budget."""
        result = manager.get_agent_budget("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_spending_no_budget(self, manager):
        """Test validation fails when no budget configured."""
        result = await manager.validate_spending(
            agent_id="no_budget_agent",
            amount=10.00,
            operation="test",
        )

        assert result["approved"] is False
        assert "No budget configured" in result["reason"]
        assert result["requires_human_approval"] is True

    @pytest.mark.asyncio
    async def test_validate_spending_approved(self, manager):
        """Test spending validation within limits."""
        await manager.set_agent_budget(
            agent_id="agent_123",
            daily_limit=100.00,
            monthly_limit=1000.00,
        )

        result = await manager.validate_spending(
            agent_id="agent_123",
            amount=10.00,
            operation="create_capsule",
        )

        assert result["approved"] is True
        assert "Within budget" in result["reason"]

    @pytest.mark.asyncio
    async def test_validate_spending_exceeds_daily(self, manager):
        """Test validation fails when exceeding daily limit."""
        await manager.set_agent_budget(
            agent_id="agent_123",
            daily_limit=10.00,
            monthly_limit=1000.00,
        )

        result = await manager.validate_spending(
            agent_id="agent_123",
            amount=15.00,  # Over daily limit
            operation="expensive_op",
        )

        assert result["approved"] is False
        assert "daily limit" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_record_spending(self, manager):
        """Test recording spending."""
        record = await manager.record_spending(
            agent_id="agent_123",
            amount=10.50,
            operation="create_capsule",
            metadata={"capsule_id": "cap_123"},
        )

        assert record.agent_id == "agent_123"
        assert record.amount == Decimal("10.5")
        assert record.operation == "create_capsule"
        assert record.approved is True
        assert record.approval_method == "automatic"

    @pytest.mark.asyncio
    async def test_get_agent_spending_empty(self, manager):
        """Test getting spending for agent with no records."""
        spending = await manager.get_agent_spending("new_agent", "daily")
        assert spending == Decimal("0")

    @pytest.mark.asyncio
    async def test_get_agent_spending_invalid_period(self, manager):
        """Test getting spending with invalid period."""
        with pytest.raises(ValueError, match="Invalid period"):
            await manager.get_agent_spending("agent", "invalid_period")

    @pytest.mark.asyncio
    async def test_get_spending_summary(self, manager):
        """Test getting spending summary."""
        await manager.set_agent_budget(
            agent_id="agent_123",
            daily_limit=100.00,
            monthly_limit=1000.00,
        )

        summary = await manager.get_spending_summary("agent_123")

        assert summary["agent_id"] == "agent_123"
        assert summary["budget"]["daily_limit"] == 100.00
        assert summary["budget"]["monthly_limit"] == 1000.00
        assert summary["spending"]["daily"] == 0
        assert summary["spending"]["monthly"] == 0

    @pytest.mark.asyncio
    async def test_spending_accumulation(self, manager):
        """Test that spending accumulates correctly."""
        await manager.set_agent_budget(
            agent_id="agent_123",
            daily_limit=100.00,
            monthly_limit=1000.00,
        )

        # Record some spending
        await manager.record_spending(
            agent_id="agent_123",
            amount=20.00,
            operation="op1",
        )
        await manager.record_spending(
            agent_id="agent_123",
            amount=30.00,
            operation="op2",
        )

        # Check total spending
        daily_spending = await manager.get_agent_spending("agent_123", "daily")
        assert daily_spending == Decimal("50")


class TestInsufficientBudgetError:
    """Tests for InsufficientBudgetError exception."""

    def test_raise_insufficient_budget(self):
        """Test raising InsufficientBudgetError."""
        with pytest.raises(InsufficientBudgetError):
            raise InsufficientBudgetError("Agent over budget")

    def test_exception_message(self):
        """Test exception contains message."""
        try:
            raise InsufficientBudgetError("Custom message")
        except InsufficientBudgetError as e:
            assert "Custom message" in str(e)


class TestManagerPersistence:
    """Tests for spending manager persistence."""

    @pytest.mark.asyncio
    async def test_budget_persistence(self):
        """Test that budgets persist across manager instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manager and set budget
            manager1 = AgentSpendingManager(storage_path=tmpdir)
            await manager1.set_agent_budget(
                agent_id="agent_123",
                daily_limit=100.00,
                monthly_limit=1000.00,
            )

            # Create new manager with same storage
            manager2 = AgentSpendingManager(storage_path=tmpdir)

            # Budget should be loaded
            budget = manager2.get_agent_budget("agent_123")
            assert budget is not None
            assert budget.daily_limit == Decimal("100")


class TestAlertThreshold:
    """Tests for alert threshold configuration."""

    @pytest.fixture
    def temp_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_default_threshold(self, temp_storage):
        """Test default alert threshold."""
        manager = AgentSpendingManager(storage_path=temp_storage)
        assert manager.alert_threshold == 0.80

    def test_custom_threshold(self, temp_storage):
        """Test custom alert threshold."""
        manager = AgentSpendingManager(storage_path=temp_storage, alert_threshold=0.90)
        assert manager.alert_threshold == 0.90
