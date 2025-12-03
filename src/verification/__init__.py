"""
Verification module for UATP Capsule Engine.
Provides formal verification contracts and runtime checking.
"""

from .formal_contracts import (
    ContractSeverity,
    ContractType,
    ContractViolation,
    FormalContract,
    FormalVerificationEngine,
    contract_registry,
    formal_verification,
    invariant,
    non_empty_string,
    not_none,
    positive_result,
    postcondition,
    precondition,
    safety_property,
    temporal_property,
    valid_capsule_id,
)

__all__ = [
    "FormalVerificationEngine",
    "ContractType",
    "ContractSeverity",
    "FormalContract",
    "ContractViolation",
    "contract_registry",
    "formal_verification",
    "precondition",
    "postcondition",
    "invariant",
    "temporal_property",
    "safety_property",
    "not_none",
    "positive_result",
    "non_empty_string",
    "valid_capsule_id",
]
