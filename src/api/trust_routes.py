"""
Trust Management API Routes for UATP Capsule Engine.

Provides endpoints for monitoring and managing runtime trust enforcement.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel
from quart import Blueprint, jsonify, request

from .dependencies import get_engine, require_api_key

trust_bp = Blueprint("trust", __name__)


class TrustStatusResponse(BaseModel):
    """Response model for trust status queries."""

    agent_id: str
    trust_level: str
    reputation_score: float
    total_capsules: int
    successful_capsules: int
    success_rate: float
    violation_count: int
    last_activity: Optional[str]
    established_date: str
    quarantine_status: Optional[Dict[str, Any]]
    recent_violations: list


class SystemTrustMetricsResponse(BaseModel):
    """Response model for system trust metrics."""

    total_agents: int
    quarantined_agents: int
    trust_distribution: Dict[str, int]
    recent_violations_count: int
    policies_enabled: int
    system_health: str


@trust_bp.route("/agent/<agent_id>/status", methods=["GET"])
@require_api_key
async def get_agent_trust_status(agent_id: str):
    """Get detailed trust status for a specific agent."""
    engine = get_engine()

    try:
        trust_status = engine.get_agent_trust_status(agent_id)
        return jsonify(trust_status), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get trust status: {str(e)}"}), 500


@trust_bp.route("/metrics", methods=["GET", "OPTIONS"])
@require_api_key
async def get_system_trust_metrics():
    """Get overall system trust metrics and health status."""
    engine = get_engine()

    try:
        metrics = engine.get_system_trust_metrics()
        return jsonify(metrics), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get trust metrics: {str(e)}"}), 500


@trust_bp.route("/policies", methods=["GET", "OPTIONS"])
@require_api_key
async def get_trust_policies():
    """Get current trust enforcement policies."""
    engine = get_engine()

    try:
        policies = {}
        for policy_name, policy in engine.runtime_trust_enforcer.policies.items():
            policies[policy_name] = {
                "name": policy.name,
                "description": policy.description,
                "enabled": policy.enabled,
                "trust_threshold": policy.trust_threshold.value,
                "enforcement_action": policy.enforcement_action.value,
                "max_violations_per_hour": policy.max_violations_per_hour,
                "quarantine_duration_hours": policy.quarantine_duration_hours,
            }

        return jsonify({"policies": policies}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get policies: {str(e)}"}), 500


@trust_bp.route("/violations/recent", methods=["GET", "OPTIONS"])
@require_api_key
async def get_recent_violations():
    """Get recent trust violations across the system."""
    engine = get_engine()

    try:
        # Get query parameters
        limit = request.args.get("limit", 50, type=int)
        limit = min(limit, 100)  # Cap at 100

        # Get recent violations from violation history
        recent_violations = list(engine.runtime_trust_enforcer.violation_history)[
            -limit:
        ]

        # Format for response
        formatted_violations = []
        for violation in recent_violations:
            formatted_violations.append(
                {
                    "violation_type": violation.violation_type.value,
                    "severity": violation.severity,
                    "description": violation.description,
                    "agent_id": violation.agent_id,
                    "capsule_id": violation.capsule_id,
                    "timestamp": violation.timestamp.isoformat(),
                    "evidence": violation.evidence,
                }
            )

        return (
            jsonify(
                {
                    "violations": formatted_violations,
                    "count": len(formatted_violations),
                    "total_in_history": len(
                        engine.runtime_trust_enforcer.violation_history
                    ),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to get violations: {str(e)}"}), 500


@trust_bp.route("/agents/quarantined", methods=["GET", "OPTIONS"])
@require_api_key
async def get_quarantined_agents():
    """Get list of currently quarantined agents."""
    engine = get_engine()

    try:
        from datetime import datetime, timezone

        quarantined = []
        current_time = datetime.now(timezone.utc)

        for (
            agent_id,
            quarantine_end,
        ) in engine.runtime_trust_enforcer.quarantined_agents.items():
            if current_time < quarantine_end:
                quarantined.append(
                    {
                        "agent_id": agent_id,
                        "quarantine_end": quarantine_end.isoformat(),
                        "time_remaining_seconds": (
                            quarantine_end - current_time
                        ).total_seconds(),
                    }
                )

        return (
            jsonify({"quarantined_agents": quarantined, "count": len(quarantined)}),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to get quarantined agents: {str(e)}"}), 500


@trust_bp.route("/health", methods=["GET"])
async def trust_system_health():
    """Get trust system health status (no auth required for monitoring)."""
    engine = get_engine()

    try:
        metrics = engine.get_system_trust_metrics()

        # Determine health status
        health_status = "healthy"
        if metrics["system_health"] == "degraded":
            health_status = "degraded"

        # Check if any critical policies are disabled
        enabled_policies = metrics["policies_enabled"]
        total_policies = len(engine.runtime_trust_enforcer.policies)

        if enabled_policies < total_policies * 0.8:  # Less than 80% enabled
            health_status = "warning"

        return (
            jsonify(
                {
                    "status": health_status,
                    "policies_enabled": enabled_policies,
                    "total_policies": total_policies,
                    "quarantined_agents": metrics["quarantined_agents"],
                    "recent_violations": metrics["recent_violations_count"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )
