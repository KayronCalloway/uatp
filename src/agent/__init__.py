"""
Agent Governance Framework

Provides authentication, authorization, and economic constraints for AI agents.

Components:
- Agent Authentication (src/auth/agent_auth.py)
- Agent Spending Limits (src/agent/spending_limits.py)
- Agent Audit Trail (integrated with immutable audit logs)

Usage:
    from src.agent import agent_spending_manager
    from src.auth.agent_auth import agent_auth_manager

    # Register agent
    agent, token = await agent_auth_manager.register_agent(
        human_owner_id="user_123",
        human_owner_email="user@example.com",
        agent_name="ResearchAssistant"
    )

    # Set budget
    await agent_spending_manager.set_agent_budget(
        agent_id=agent.agent_id,
        daily_limit=100.00,
        monthly_limit=1000.00
    )

    # Validate spending before operation
    validation = await agent_spending_manager.validate_spending(
        agent_id=agent.agent_id,
        amount=10.50,
        operation="create_capsule"
    )

    if validation["approved"]:
        # Perform operation
        await perform_operation()

        # Record actual spending
        await agent_spending_manager.record_spending(
            agent_id=agent.agent_id,
            amount=10.50,
            operation="create_capsule"
        )
"""

from .spending_limits import (
    AgentBudget,
    AgentSpendingManager,
    BudgetAlert,
    InsufficientBudgetError,
    SpendingRecord,
    agent_spending_manager,
)

__all__ = [
    "AgentSpendingManager",
    "agent_spending_manager",
    "AgentBudget",
    "SpendingRecord",
    "BudgetAlert",
    "InsufficientBudgetError",
]
