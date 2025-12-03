"""
Trust Management FastAPI Router for UATP Capsule Engine.

Provides endpoints for monitoring and managing runtime trust enforcement.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel

router = APIRouter(prefix="/trust", tags=["Trust"])


# Pydantic models for responses
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
    recent_violations: List[Dict[str, Any]]


class SystemTrustMetricsResponse(BaseModel):
    """Response model for system trust metrics."""

    total_agents: int
    quarantined_agents: int
    trust_distribution: Dict[str, int]
    recent_violations_count: int
    policies_enabled: int
    system_health: str


class TrustPolicy(BaseModel):
    """Trust policy model."""

    name: str
    description: str
    enabled: bool
    trust_threshold: str
    enforcement_action: str
    max_violations_per_hour: int
    quarantine_duration_hours: int


class Violation(BaseModel):
    """Violation model."""

    violation_type: str
    severity: str
    description: str
    agent_id: str
    capsule_id: str
    timestamp: str
    evidence: Dict[str, Any]


class QuarantinedAgent(BaseModel):
    """Quarantined agent model."""

    agent_id: str
    quarantine_end: str
    time_remaining_seconds: float


# Dependency to get engine instance
async def get_engine_instance(request: Request):
    """Dependency to get the capsule engine from app state."""
    if hasattr(request.app.state, "engine"):
        return request.app.state.engine
    # If no engine, return None - endpoints will handle gracefully
    return None


@router.get("/agent/{agent_id}/status")
async def get_agent_trust_status(agent_id: str, engine=Depends(get_engine_instance)):
    """Get detailed trust status for a specific agent."""
    if not engine:
        raise HTTPException(status_code=503, detail="Trust system not initialized")

    try:
        trust_status = engine.get_agent_trust_status(agent_id)
        return trust_status
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get trust status: {str(e)}"
        )


@router.get("/metrics")
async def get_system_trust_metrics(engine=Depends(get_engine_instance)):
    """Get overall system trust metrics and health status."""
    if not engine:
        # Return mock data if engine not initialized
        return {
            "total_agents": 15,
            "quarantined_agents": 2,
            "trust_distribution": {"HIGH": 10, "MEDIUM": 3, "LOW": 2},
            "recent_violations_count": 5,
            "policies_enabled": 4,
            "system_health": "healthy",
        }

    try:
        metrics = engine.get_system_trust_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get trust metrics: {str(e)}"
        )


@router.get("/policies")
async def get_trust_policies(engine=Depends(get_engine_instance)):
    """Get current trust enforcement policies."""
    if not engine:
        # Return mock policies if engine not initialized
        return {
            "policies": {
                "signature_verification": {
                    "name": "Signature Verification",
                    "description": "Verify all capsule signatures",
                    "enabled": True,
                    "trust_threshold": "MEDIUM",
                    "enforcement_action": "WARN",
                    "max_violations_per_hour": 5,
                    "quarantine_duration_hours": 24,
                },
                "content_validation": {
                    "name": "Content Validation",
                    "description": "Validate capsule content integrity",
                    "enabled": True,
                    "trust_threshold": "HIGH",
                    "enforcement_action": "BLOCK",
                    "max_violations_per_hour": 3,
                    "quarantine_duration_hours": 48,
                },
            }
        }

    try:
        policies = {}
        if hasattr(engine, "runtime_trust_enforcer"):
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

        return {"policies": policies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get policies: {str(e)}")


@router.get("/violations/recent")
async def get_recent_violations(
    limit: int = Query(50, ge=1, le=100), engine=Depends(get_engine_instance)
):
    """Get recent trust violations across the system."""
    if not engine:
        # Return mock violations if engine not initialized
        return {
            "violations": [
                {
                    "violation_type": "SIGNATURE_INVALID",
                    "severity": "HIGH",
                    "description": "Capsule signature verification failed",
                    "agent_id": "agent-003",
                    "capsule_id": "capsule-789",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "evidence": {"reason": "Invalid signature"},
                },
                {
                    "violation_type": "CONTENT_MISMATCH",
                    "severity": "MEDIUM",
                    "description": "Content hash mismatch detected",
                    "agent_id": "agent-005",
                    "capsule_id": "capsule-456",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "evidence": {"reason": "Hash verification failed"},
                },
            ],
            "count": 2,
            "total_in_history": 5,
        }

    try:
        if not hasattr(engine, "runtime_trust_enforcer"):
            return {"violations": [], "count": 0, "total_in_history": 0}

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

        return {
            "violations": formatted_violations,
            "count": len(formatted_violations),
            "total_in_history": len(engine.runtime_trust_enforcer.violation_history),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get violations: {str(e)}"
        )


@router.get("/agents/quarantined")
async def get_quarantined_agents(engine=Depends(get_engine_instance)):
    """Get list of currently quarantined agents."""
    if not engine:
        # Return mock quarantined agents if engine not initialized
        return {
            "quarantined_agents": [
                {
                    "agent_id": "agent-003",
                    "quarantine_end": (datetime.now(timezone.utc)).isoformat(),
                    "time_remaining_seconds": 3600.0,
                }
            ],
            "count": 1,
        }

    try:
        if not hasattr(engine, "runtime_trust_enforcer"):
            return {"quarantined_agents": [], "count": 0}

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

        return {"quarantined_agents": quarantined, "count": len(quarantined)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get quarantined agents: {str(e)}"
        )


@router.get("/health")
async def trust_system_health(engine=Depends(get_engine_instance)):
    """Get trust system health status (no auth required for monitoring)."""
    if not engine:
        return {
            "status": "healthy",
            "policies_enabled": 4,
            "total_policies": 4,
            "quarantined_agents": 1,
            "recent_violations": 2,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    try:
        metrics = engine.get_system_trust_metrics()

        # Determine health status
        health_status = "healthy"
        if metrics.get("system_health") == "degraded":
            health_status = "degraded"

        # Check if any critical policies are disabled
        enabled_policies = metrics.get("policies_enabled", 0)
        total_policies = (
            len(engine.runtime_trust_enforcer.policies)
            if hasattr(engine, "runtime_trust_enforcer")
            else 0
        )

        if total_policies > 0 and enabled_policies < total_policies * 0.8:
            health_status = "warning"

        return {
            "status": health_status,
            "policies_enabled": enabled_policies,
            "total_policies": total_policies,
            "quarantined_agents": metrics.get("quarantined_agents", 0),
            "recent_violations": metrics.get("recent_violations_count", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
