"""
Safety Systems for AI Decision Making

Provides comprehensive safety rails for high-stakes AI decisions.

Components:
- High-Stakes Decision Validator (src/safety/high_stakes_decisions.py)
- Human Approval Workflows
- Multi-Agent Consensus
- Emergency Stop Mechanisms
- Explainable AI Requirements

Usage:
    from src.safety import decision_safety_validator, RiskLevel

    # Validate a medical decision
    validation = await decision_safety_validator.validate_decision(
        decision={
            "domain": "medical",
            "type": "diagnosis",
            "recommendation": "...",
            "confidence": 0.92,
            "explanation": "Based on symptoms X, Y, Z..."
        },
        agent_id="agent_123",
        context={"patient_severity": "high"}
    )

    if validation.approved:
        # Execute decision
        await execute_decision()
    elif validation.approval_status == "pending_human":
        # Wait for human approval
        await notify_human_reviewer(validation.approval_request_id)
    else:
        # Decision rejected
        logger.error(f"Decision rejected: {validation.reason}")
"""

from .high_stakes_decisions import (
    DecisionSafetyValidator,
    decision_safety_validator,
    RiskLevel,
    DecisionDomain,
    ApprovalStatus,
    SafetyThresholds,
    DecisionValidation,
    HumanApprovalRequest,
    ConsensusRequest,
    EmergencyStop,
)

__all__ = [
    "DecisionSafetyValidator",
    "decision_safety_validator",
    "RiskLevel",
    "DecisionDomain",
    "ApprovalStatus",
    "SafetyThresholds",
    "DecisionValidation",
    "HumanApprovalRequest",
    "ConsensusRequest",
    "EmergencyStop",
]
