"""
Ethics module for UATP Capsule Engine.
Provides real-time ethical monitoring and intervention systems.
"""

from .rect_system import (
    EthicalInterventionSystem,
    EthicalMonitor,
    EthicalRule,
    EthicalRuleEngine,
    EthicalViolation,
    EthicalViolationType,
    InterventionAction,
    InterventionResult,
    RECTSystem,
    SeverityLevel,
    rect_system,
)

__all__ = [
    "RECTSystem",
    "EthicalMonitor",
    "EthicalRuleEngine",
    "EthicalInterventionSystem",
    "EthicalViolationType",
    "SeverityLevel",
    "InterventionAction",
    "EthicalViolation",
    "EthicalRule",
    "InterventionResult",
    "rect_system",
]
