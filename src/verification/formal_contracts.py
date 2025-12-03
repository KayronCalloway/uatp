"""
Formal Verification Contracts for UATP Capsule Engine.
Implements runtime contract checking with formal verification principles.
"""

import inspect
import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class ContractType(str, Enum):
    """Types of formal contracts."""

    PRECONDITION = "precondition"
    POSTCONDITION = "postcondition"
    INVARIANT = "invariant"
    TEMPORAL = "temporal"
    SAFETY = "safety"
    LIVENESS = "liveness"


class ContractSeverity(str, Enum):
    """Severity levels for contract violations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    WARNING = "warning"


@dataclass
class ContractViolation:
    """Represents a contract violation."""

    contract_id: str
    contract_type: ContractType
    severity: ContractSeverity
    message: str
    function_name: str
    file_path: str
    line_number: int
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "contract_id": self.contract_id,
            "contract_type": self.contract_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "function_name": self.function_name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "stack_trace": self.stack_trace,
        }


@dataclass
class FormalContract:
    """Represents a formal verification contract."""

    contract_id: str
    contract_type: ContractType
    predicate: Callable[[Any], bool]
    description: str
    severity: ContractSeverity
    enabled: bool = True
    violation_count: int = 0
    last_violation: Optional[datetime] = None

    def check(self, context: Dict[str, Any]) -> bool:
        """Check if the contract is satisfied."""
        try:
            return self.predicate(context)
        except Exception as e:
            logger.error(f"Contract {self.contract_id} check failed: {e}")
            return False

    def record_violation(self):
        """Record a contract violation."""
        self.violation_count += 1
        self.last_violation = datetime.now(timezone.utc)


class ContractRegistry:
    """Registry for formal verification contracts."""

    def __init__(self):
        self.contracts: Dict[str, FormalContract] = {}
        self.function_contracts: Dict[str, List[str]] = {}
        self.class_contracts: Dict[str, List[str]] = {}
        self.violations: List[ContractViolation] = []
        self.enabled = True

    def register_contract(self, contract: FormalContract):
        """Register a formal contract."""
        self.contracts[contract.contract_id] = contract
        logger.info(f"Registered formal contract: {contract.contract_id}")

    def register_function_contract(self, function_name: str, contract_id: str):
        """Associate a contract with a function."""
        if function_name not in self.function_contracts:
            self.function_contracts[function_name] = []
        self.function_contracts[function_name].append(contract_id)

    def register_class_contract(self, class_name: str, contract_id: str):
        """Associate a contract with a class."""
        if class_name not in self.class_contracts:
            self.class_contracts[class_name] = []
        self.class_contracts[class_name].append(contract_id)

    def check_contracts(
        self, function_name: str, context: Dict[str, Any]
    ) -> List[ContractViolation]:
        """Check all contracts for a function."""
        violations = []

        if not self.enabled:
            return violations

        contract_ids = self.function_contracts.get(function_name, [])

        for contract_id in contract_ids:
            if contract_id in self.contracts:
                contract = self.contracts[contract_id]

                if contract.enabled and not contract.check(context):
                    violation = ContractViolation(
                        contract_id=contract_id,
                        contract_type=contract.contract_type,
                        severity=contract.severity,
                        message=contract.description,
                        function_name=function_name,
                        file_path=context.get("file_path", "unknown"),
                        line_number=context.get("line_number", 0),
                        timestamp=datetime.now(timezone.utc),
                        context=context,
                        stack_trace=traceback.format_stack()[-1],
                    )

                    violations.append(violation)
                    contract.record_violation()
                    self.violations.append(violation)

        return violations

    def get_contract_statistics(self) -> Dict[str, Any]:
        """Get statistics about contract checking."""
        total_contracts = len(self.contracts)
        enabled_contracts = sum(1 for c in self.contracts.values() if c.enabled)
        total_violations = len(self.violations)

        severity_counts = {}
        for violation in self.violations:
            severity = violation.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total_contracts": total_contracts,
            "enabled_contracts": enabled_contracts,
            "total_violations": total_violations,
            "severity_counts": severity_counts,
            "registry_enabled": self.enabled,
        }


# Global contract registry
contract_registry = ContractRegistry()


def precondition(
    condition: Callable[[Dict[str, Any]], bool],
    description: str = "Precondition violated",
    severity: ContractSeverity = ContractSeverity.HIGH,
):
    """Decorator for precondition contracts."""

    def decorator(func: Callable) -> Callable:
        contract_id = f"pre_{func.__name__}_{id(condition)}"

        contract = FormalContract(
            contract_id=contract_id,
            contract_type=ContractType.PRECONDITION,
            predicate=condition,
            description=description,
            severity=severity,
        )

        contract_registry.register_contract(contract)
        contract_registry.register_function_contract(func.__name__, contract_id)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create context from function arguments
            context = {
                "args": args,
                "kwargs": kwargs,
                "function_name": func.__name__,
                "file_path": inspect.getfile(func),
                "line_number": inspect.currentframe().f_lineno,
            }

            # Check preconditions
            violations = contract_registry.check_contracts(func.__name__, context)

            if violations:
                critical_violations = [
                    v for v in violations if v.severity == ContractSeverity.CRITICAL
                ]
                if critical_violations:
                    raise RuntimeError(
                        f"Critical precondition violation: {critical_violations[0].message}"
                    )

                for violation in violations:
                    logger.warning(f"Precondition violation: {violation.message}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def postcondition(
    condition: Callable[[Dict[str, Any]], bool],
    description: str = "Postcondition violated",
    severity: ContractSeverity = ContractSeverity.HIGH,
):
    """Decorator for postcondition contracts."""

    def decorator(func: Callable) -> Callable:
        contract_id = f"post_{func.__name__}_{id(condition)}"

        contract = FormalContract(
            contract_id=contract_id,
            contract_type=ContractType.POSTCONDITION,
            predicate=condition,
            description=description,
            severity=severity,
        )

        contract_registry.register_contract(contract)
        contract_registry.register_function_contract(func.__name__, contract_id)

        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Create context with result
            context = {
                "args": args,
                "kwargs": kwargs,
                "result": result,
                "function_name": func.__name__,
                "file_path": inspect.getfile(func),
                "line_number": inspect.currentframe().f_lineno,
            }

            # Check postconditions
            violations = contract_registry.check_contracts(func.__name__, context)

            if violations:
                critical_violations = [
                    v for v in violations if v.severity == ContractSeverity.CRITICAL
                ]
                if critical_violations:
                    raise RuntimeError(
                        f"Critical postcondition violation: {critical_violations[0].message}"
                    )

                for violation in violations:
                    logger.warning(f"Postcondition violation: {violation.message}")

            return result

        return wrapper

    return decorator


def invariant(
    condition: Callable[[Any], bool],
    description: str = "Invariant violated",
    severity: ContractSeverity = ContractSeverity.CRITICAL,
):
    """Decorator for class invariant contracts."""

    def decorator(cls: Type) -> Type:
        contract_id = f"inv_{cls.__name__}_{id(condition)}"

        contract = FormalContract(
            contract_id=contract_id,
            contract_type=ContractType.INVARIANT,
            predicate=lambda ctx: condition(ctx.get("instance")),
            description=description,
            severity=severity,
        )

        contract_registry.register_contract(contract)
        contract_registry.register_class_contract(cls.__name__, contract_id)

        # Wrap all methods to check invariants
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if callable(attr) and not attr_name.startswith("_"):
                wrapped_method = _wrap_method_with_invariant(
                    attr, cls.__name__, contract_id
                )
                setattr(cls, attr_name, wrapped_method)

        return cls

    return decorator


def _wrap_method_with_invariant(
    method: Callable, class_name: str, contract_id: str
) -> Callable:
    """Wrap a method with invariant checking."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        # Check invariant before method execution
        context = {
            "instance": self,
            "class_name": class_name,
            "method_name": method.__name__,
        }

        violations = []
        if contract_id in contract_registry.contracts:
            contract = contract_registry.contracts[contract_id]
            if contract.enabled and not contract.check(context):
                violation = ContractViolation(
                    contract_id=contract_id,
                    contract_type=ContractType.INVARIANT,
                    severity=contract.severity,
                    message=f"Invariant violation in {class_name}.{method.__name__}",
                    function_name=f"{class_name}.{method.__name__}",
                    file_path=inspect.getfile(method),
                    line_number=inspect.currentframe().f_lineno,
                    timestamp=datetime.now(timezone.utc),
                    context=context,
                )
                violations.append(violation)
                contract.record_violation()
                contract_registry.violations.append(violation)

        # Execute method
        result = method(self, *args, **kwargs)

        # Check invariant after method execution
        if contract_id in contract_registry.contracts:
            contract = contract_registry.contracts[contract_id]
            if contract.enabled and not contract.check(context):
                violation = ContractViolation(
                    contract_id=contract_id,
                    contract_type=ContractType.INVARIANT,
                    severity=contract.severity,
                    message=f"Invariant violation after {class_name}.{method.__name__}",
                    function_name=f"{class_name}.{method.__name__}",
                    file_path=inspect.getfile(method),
                    line_number=inspect.currentframe().f_lineno,
                    timestamp=datetime.now(timezone.utc),
                    context=context,
                )
                violations.append(violation)
                contract.record_violation()
                contract_registry.violations.append(violation)

        # Handle violations
        if violations:
            critical_violations = [
                v for v in violations if v.severity == ContractSeverity.CRITICAL
            ]
            if critical_violations:
                raise RuntimeError(
                    f"Critical invariant violation: {critical_violations[0].message}"
                )

            for violation in violations:
                logger.warning(f"Invariant violation: {violation.message}")

        return result

    return wrapper


def temporal_property(
    property_checker: Callable[[List[Dict[str, Any]]], bool],
    description: str = "Temporal property violated",
    severity: ContractSeverity = ContractSeverity.HIGH,
):
    """Decorator for temporal property contracts."""

    def decorator(func: Callable) -> Callable:
        contract_id = f"temp_{func.__name__}_{id(property_checker)}"

        # Store execution history for temporal checking
        if not hasattr(func, "_execution_history"):
            func._execution_history = []

        contract = FormalContract(
            contract_id=contract_id,
            contract_type=ContractType.TEMPORAL,
            predicate=lambda ctx: property_checker(ctx.get("execution_history", [])),
            description=description,
            severity=severity,
        )

        contract_registry.register_contract(contract)
        contract_registry.register_function_contract(func.__name__, contract_id)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Record execution
            execution_record = {
                "timestamp": datetime.now(timezone.utc),
                "args": args,
                "kwargs": kwargs,
                "function_name": func.__name__,
            }

            result = func(*args, **kwargs)

            execution_record["result"] = result
            func._execution_history.append(execution_record)

            # Keep only recent history to avoid memory issues
            if len(func._execution_history) > 100:
                func._execution_history = func._execution_history[-100:]

            # Check temporal property
            context = {
                "execution_history": func._execution_history,
                "current_execution": execution_record,
                "function_name": func.__name__,
            }

            violations = contract_registry.check_contracts(func.__name__, context)

            if violations:
                critical_violations = [
                    v for v in violations if v.severity == ContractSeverity.CRITICAL
                ]
                if critical_violations:
                    raise RuntimeError(
                        f"Critical temporal property violation: {critical_violations[0].message}"
                    )

                for violation in violations:
                    logger.warning(f"Temporal property violation: {violation.message}")

            return result

        return wrapper

    return decorator


def safety_property(
    safety_checker: Callable[[Dict[str, Any]], bool],
    description: str = "Safety property violated",
    severity: ContractSeverity = ContractSeverity.CRITICAL,
):
    """Decorator for safety property contracts."""

    def decorator(func: Callable) -> Callable:
        contract_id = f"safety_{func.__name__}_{id(safety_checker)}"

        contract = FormalContract(
            contract_id=contract_id,
            contract_type=ContractType.SAFETY,
            predicate=safety_checker,
            description=description,
            severity=severity,
        )

        contract_registry.register_contract(contract)
        contract_registry.register_function_contract(func.__name__, contract_id)

        @wraps(func)
        def wrapper(*args, **kwargs):
            context = {
                "args": args,
                "kwargs": kwargs,
                "function_name": func.__name__,
                "timestamp": datetime.now(timezone.utc),
            }

            # Check safety property before execution
            violations = contract_registry.check_contracts(func.__name__, context)

            if violations:
                critical_violations = [
                    v for v in violations if v.severity == ContractSeverity.CRITICAL
                ]
                if critical_violations:
                    raise RuntimeError(
                        f"Critical safety violation: {critical_violations[0].message}"
                    )

            result = func(*args, **kwargs)

            # Check safety property after execution
            context["result"] = result
            post_violations = contract_registry.check_contracts(func.__name__, context)

            if post_violations:
                critical_violations = [
                    v
                    for v in post_violations
                    if v.severity == ContractSeverity.CRITICAL
                ]
                if critical_violations:
                    raise RuntimeError(
                        f"Critical safety violation: {critical_violations[0].message}"
                    )

                for violation in post_violations:
                    logger.warning(f"Safety violation: {violation.message}")

            return result

        return wrapper

    return decorator


class FormalVerificationEngine:
    """Engine for formal verification and contract management."""

    def __init__(self):
        self.registry = contract_registry
        self.verification_enabled = True

    def enable_verification(self):
        """Enable formal verification."""
        self.verification_enabled = True
        self.registry.enabled = True
        logger.info("Formal verification enabled")

    def disable_verification(self):
        """Disable formal verification."""
        self.verification_enabled = False
        self.registry.enabled = False
        logger.info("Formal verification disabled")

    def add_custom_contract(
        self,
        contract_id: str,
        contract_type: ContractType,
        predicate: Callable[[Dict[str, Any]], bool],
        description: str,
        severity: ContractSeverity = ContractSeverity.MEDIUM,
    ):
        """Add a custom verification contract."""
        contract = FormalContract(
            contract_id=contract_id,
            contract_type=contract_type,
            predicate=predicate,
            description=description,
            severity=severity,
        )

        self.registry.register_contract(contract)
        logger.info(f"Added custom contract: {contract_id}")

    def get_violation_report(self) -> Dict[str, Any]:
        """Get comprehensive violation report."""
        violations_by_severity = {}
        violations_by_type = {}
        recent_violations = []

        for violation in self.registry.violations:
            # Group by severity
            severity = violation.severity.value
            if severity not in violations_by_severity:
                violations_by_severity[severity] = []
            violations_by_severity[severity].append(violation.to_dict())

            # Group by type
            contract_type = violation.contract_type.value
            if contract_type not in violations_by_type:
                violations_by_type[contract_type] = []
            violations_by_type[contract_type].append(violation.to_dict())

            # Recent violations (last 24 hours)
            if (datetime.now(timezone.utc) - violation.timestamp).days < 1:
                recent_violations.append(violation.to_dict())

        return {
            "total_violations": len(self.registry.violations),
            "violations_by_severity": violations_by_severity,
            "violations_by_type": violations_by_type,
            "recent_violations": recent_violations,
            "contract_statistics": self.registry.get_contract_statistics(),
        }

    def clear_violations(self):
        """Clear all recorded violations."""
        self.registry.violations.clear()
        for contract in self.registry.contracts.values():
            contract.violation_count = 0
            contract.last_violation = None
        logger.info("Cleared all contract violations")

    def verify_capsule_contracts(
        self, capsule_data: Dict[str, Any]
    ) -> List[ContractViolation]:
        """Verify all contracts for a capsule."""
        violations = []

        # Check capsule-specific contracts
        capsule_contracts = [
            (
                "capsule_id_format",
                lambda ctx: isinstance(ctx.get("capsule_id"), str)
                and len(ctx.get("capsule_id", "")) > 0,
            ),
            ("capsule_timestamp", lambda ctx: ctx.get("timestamp") is not None),
            ("capsule_version", lambda ctx: ctx.get("version") in ["7.0", "6.0"]),
            (
                "capsule_status",
                lambda ctx: ctx.get("status")
                in ["draft", "active", "sealed", "retired"],
            ),
        ]

        for contract_id, predicate in capsule_contracts:
            if not predicate(capsule_data):
                violation = ContractViolation(
                    contract_id=contract_id,
                    contract_type=ContractType.SAFETY,
                    severity=ContractSeverity.HIGH,
                    message=f"Capsule contract violation: {contract_id}",
                    function_name="verify_capsule_contracts",
                    file_path=__file__,
                    line_number=inspect.currentframe().f_lineno,
                    timestamp=datetime.now(timezone.utc),
                    context=capsule_data,
                )
                violations.append(violation)

        return violations


# Global formal verification engine
formal_verification = FormalVerificationEngine()


# Common contract predicates
def not_none(ctx: Dict[str, Any]) -> bool:
    """Check that result is not None."""
    return ctx.get("result") is not None


def positive_result(ctx: Dict[str, Any]) -> bool:
    """Check that numeric result is positive."""
    result = ctx.get("result")
    return isinstance(result, (int, float)) and result > 0


def non_empty_string(ctx: Dict[str, Any]) -> bool:
    """Check that string result is not empty."""
    result = ctx.get("result")
    return isinstance(result, str) and len(result) > 0


def valid_capsule_id(ctx: Dict[str, Any]) -> bool:
    """Check that capsule ID is valid format."""
    capsule_id = ctx.get("capsule_id") or ctx.get("result")
    return isinstance(capsule_id, str) and len(capsule_id) >= 10
