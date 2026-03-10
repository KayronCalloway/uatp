"""
Setup Agent Budgets

Initialize budget configurations for AI agents in production.

Usage:
    python scripts/setup_agent_budgets.py

This script:
1. Creates default budget policies
2. Sets up budget tiers (free, basic, premium)
3. Configures alert thresholds
4. Initializes spending tracking
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

from src.agent.spending_limits import AgentSpendingManager
from src.auth.agent_auth import AgentAuthManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_budget_tiers():
    """
    Create standard budget tiers for agents.

    Tiers:
    - Free: $10/day, $100/month (for testing/development)
    - Basic: $100/day, $1,000/month (for production agents)
    - Premium: $500/day, $10,000/month (for high-value agents)
    - Enterprise: Custom limits
    """
    manager = AgentSpendingManager()

    logger.info(" Setting up agent budget tiers...")

    # Store tier definitions
    tiers = {
        "free": {
            "daily_limit": 10.00,
            "monthly_limit": 100.00,
            "description": "Free tier for testing and development",
        },
        "basic": {
            "daily_limit": 100.00,
            "monthly_limit": 1000.00,
            "description": "Basic tier for production agents",
        },
        "premium": {
            "daily_limit": 500.00,
            "monthly_limit": 10000.00,
            "description": "Premium tier for high-value agents",
        },
        "enterprise": {
            "daily_limit": 5000.00,
            "monthly_limit": 100000.00,
            "description": "Enterprise tier with custom limits",
        },
    }

    logger.info("\\n Available Budget Tiers:")
    for tier_name, tier_config in tiers.items():
        logger.info(f"\\n  {tier_name.upper()}:")
        logger.info(f"    Daily Limit:   ${tier_config['daily_limit']:,.2f}")
        logger.info(f"    Monthly Limit: ${tier_config['monthly_limit']:,.2f}")
        logger.info(f"    Description:   {tier_config['description']}")

    return tiers


async def create_example_agent_budget():
    """Create an example agent with budget"""

    auth_manager = AgentAuthManager()
    spending_manager = AgentSpendingManager()

    logger.info("\\n Creating example agent with budget...")

    # Register example agent
    try:
        agent, token = await auth_manager.register_agent(
            human_owner_id="example_user",
            human_owner_email="user@example.com",
            agent_name="ExampleResearchAgent",
            agent_type="research",
            capabilities=["read_capsules", "create_capsules", "search"],
            metadata={"tier": "basic"},
        )

        logger.info("\\n[OK] Agent registered:")
        logger.info(f"   Agent ID: {agent.agent_id}")
        logger.info(f"   Name: {agent.agent_name}")
        logger.info(f"   Type: {agent.agent_type}")

        # Set budget (Basic tier)
        await spending_manager.set_agent_budget(
            agent_id=agent.agent_id,
            daily_limit=100.00,
            monthly_limit=1000.00,
            currency="USD",
            metadata={"tier": "basic"},
        )

        logger.info("\\n Budget configured:")
        logger.info("   Daily Limit: $100.00")
        logger.info("   Monthly Limit: $1,000.00")

        logger.info("\\n Agent Token (save securely):")
        logger.info(f"   {token[:50]}...")

        # Get spending summary
        summary = await spending_manager.get_spending_summary(agent.agent_id)

        logger.info("\\n Initial Spending Summary:")
        logger.info(f"   Daily Spending: ${summary['spending']['daily']:.2f}")
        logger.info(f"   Monthly Spending: ${summary['spending']['monthly']:.2f}")
        logger.info(f"   Daily Remaining: ${summary['remaining']['daily']:.2f}")
        logger.info(f"   Monthly Remaining: ${summary['remaining']['monthly']:.2f}")

        return agent, token

    except Exception as e:
        logger.error(f"Failed to create example agent: {e}")
        return None, None


async def simulate_spending():
    """Simulate agent spending to demonstrate tracking"""

    auth_manager = AgentAuthManager()
    spending_manager = AgentSpendingManager()

    logger.info("\\n\\n Simulating agent spending...")

    # Get the example agent
    agents = auth_manager.list_agents(human_owner_id="example_user")

    if not agents:
        logger.error("No example agent found. Run create_example_agent_budget first.")
        return

    agent = agents[0]

    # Simulate various operations
    operations = [
        {"operation": "create_capsule", "cost": 5.00},
        {"operation": "api_call_openai", "cost": 2.50},
        {"operation": "search_capsules", "cost": 1.00},
        {"operation": "create_capsule", "cost": 5.00},
        {"operation": "reasoning_trace", "cost": 10.00},
    ]

    logger.info(
        f"\\nSimulating {len(operations)} operations for agent {agent.agent_id}..."
    )

    for op in operations:
        # Validate spending
        validation = await spending_manager.validate_spending(
            agent_id=agent.agent_id, amount=op["cost"], operation=op["operation"]
        )

        if validation["approved"]:
            # Record spending
            await spending_manager.record_spending(
                agent_id=agent.agent_id,
                amount=op["cost"],
                operation=op["operation"],
                approved=True,
                metadata={"simulated": True},
            )

            logger.info(f"   [OK] ${op['cost']:.2f} - {op['operation']} (approved)")
        else:
            logger.warning(
                f"   [ERROR] ${op['cost']:.2f} - {op['operation']} (rejected: {validation['reason']})"
            )

    # Get updated summary
    summary = await spending_manager.get_spending_summary(agent.agent_id)

    logger.info("\\n Updated Spending Summary:")
    logger.info(f"   Daily Spending: ${summary['spending']['daily']:.2f}")
    logger.info(f"   Daily Remaining: ${summary['remaining']['daily']:.2f}")
    logger.info(f"   Utilization: {summary['utilization']['daily_pct']:.1f}%")


async def main():
    """Main setup function"""

    logger.info("=" * 60)
    logger.info("UATP Agent Budget Setup")
    logger.info("=" * 60)

    # 1. Setup budget tiers
    tiers = await setup_budget_tiers()

    # 2. Create example agent with budget
    agent, token = await create_example_agent_budget()

    if not agent:
        return

    # 3. Simulate spending
    await simulate_spending()

    logger.info("\\n" + "=" * 60)
    logger.info("[OK] Setup Complete!")
    logger.info("=" * 60)

    logger.info("\\n Next Steps:")
    logger.info("   1. Use the agent token to make authenticated requests")
    logger.info("   2. Monitor spending in: economic/agent_spending/")
    logger.info(
        "   3. Check budget alerts in: economic/agent_spending/budget_alerts.jsonl"
    )
    logger.info(
        "   4. View spending history in: economic/agent_spending/spending_records.jsonl"
    )

    logger.info("\\n Integration:")
    logger.info("   - Use @enforce_agent_spending_limits decorator on API routes")
    logger.info("   - Check src/api/agent_spending_middleware.py for examples")
    logger.info("   - See src/agent/spending_limits.py for API documentation")


if __name__ == "__main__":
    asyncio.run(main())
