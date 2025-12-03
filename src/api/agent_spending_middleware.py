"""
Agent Spending Middleware

Enforces spending limits for AI agents making API calls.

Automatically validates and tracks spending for operations that have economic cost.

Usage:
    from quart import Quart
    from src.api.agent_spending_middleware import enforce_agent_spending_limits

    app = Quart(__name__)

    # Apply middleware to routes
    @app.route("/api/v1/capsules", methods=["POST"])
    @enforce_agent_spending_limits(cost=5.00, operation="create_capsule")
    async def create_capsule():
        # Spending already validated and will be recorded automatically
        ...
"""

import functools
import logging
from typing import Callable, Optional, Any
from quart import request, jsonify

from src.agent.spending_limits import agent_spending_manager, InsufficientBudgetError
from src.auth.agent_auth import agent_auth_manager

logger = logging.getLogger(__name__)


def enforce_agent_spending_limits(
    cost: float, operation: str, require_approval: bool = False
):
    """
    Decorator to enforce spending limits on API endpoints.

    Args:
        cost: Cost of this operation (in USD)
        operation: Operation type (for tracking)
        require_approval: Whether to require human approval for over-budget

    Example:
        @app.route("/api/v1/expensive-operation", methods=["POST"])
        @enforce_agent_spending_limits(cost=50.00, operation="expensive_op")
        async def expensive_operation():
            # Spending validated before this runs
            return {"success": True}
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Extract agent ID from request
            agent_id = await _extract_agent_id(request)

            if not agent_id:
                # Not an agent request - proceed normally
                return await func(*args, **kwargs)

            # Validate spending
            try:
                validation = await agent_spending_manager.validate_spending(
                    agent_id=agent_id,
                    amount=cost,
                    operation=operation,
                    metadata={
                        "endpoint": request.path,
                        "method": request.method,
                        "ip_address": request.remote_addr,
                    },
                )

                if not validation["approved"]:
                    if require_approval or validation.get("requires_human_approval"):
                        # Log for human review
                        logger.warning(
                            f"Agent {agent_id} requires human approval for {operation} "
                            f"(cost: ${cost})"
                        )

                        return (
                            jsonify(
                                {
                                    "error": "Budget limit exceeded",
                                    "reason": validation["reason"],
                                    "requires_human_approval": True,
                                    "agent_id": agent_id,
                                    "operation": operation,
                                    "cost": cost,
                                }
                            ),
                            402,
                        )  # Payment Required

                    raise InsufficientBudgetError(validation["reason"])

            except InsufficientBudgetError as e:
                logger.error(f"Agent {agent_id} spending validation failed: {e}")

                return (
                    jsonify(
                        {
                            "error": "Insufficient budget",
                            "message": str(e),
                            "agent_id": agent_id,
                            "operation": operation,
                            "cost": cost,
                        }
                    ),
                    402,
                )  # Payment Required

            # Execute operation
            try:
                result = await func(*args, **kwargs)

                # Record successful spending
                await agent_spending_manager.record_spending(
                    agent_id=agent_id,
                    amount=cost,
                    operation=operation,
                    approved=True,
                    approval_method="automatic",
                    metadata={"endpoint": request.path, "success": True},
                )

                return result

            except Exception as e:
                # Operation failed - don't record spending
                logger.error(f"Operation failed for agent {agent_id}: {e}")

                # Record failed attempt (no charge)
                await agent_spending_manager.record_spending(
                    agent_id=agent_id,
                    amount=0.00,  # No charge for failed operations
                    operation=operation,
                    approved=False,
                    approval_method="automatic",
                    metadata={
                        "endpoint": request.path,
                        "error": str(e),
                        "success": False,
                    },
                )

                raise

        return wrapper

    return decorator


async def _extract_agent_id(request) -> Optional[str]:
    """
    Extract agent ID from request.

    Checks:
    1. Authorization header (Bearer token with agent JWT)
    2. X-Agent-ID header
    3. Request body agent_id field
    """
    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]

        # Verify agent token
        payload = await agent_auth_manager.verify_agent_token(token)
        if payload:
            return payload.get("agent_id")

    # Check X-Agent-ID header
    agent_id_header = request.headers.get("X-Agent-ID")
    if agent_id_header:
        return agent_id_header

    # Check request body
    try:
        data = await request.get_json()
        if data and "agent_id" in data:
            return data["agent_id"]
    except:
        pass

    return None


def get_agent_spending_summary():
    """
    Endpoint handler to get agent spending summary.

    Returns spending breakdown for the authenticated agent.
    """

    async def handler():
        agent_id = await _extract_agent_id(request)

        if not agent_id:
            return jsonify({"error": "Agent authentication required"}), 401

        summary = await agent_spending_manager.get_spending_summary(agent_id)

        return jsonify(summary), 200

    return handler
