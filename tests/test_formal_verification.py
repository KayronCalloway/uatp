"""
Tests for the formal verification system.
"""

from datetime import datetime, timezone

import pytest

from src.verification.formal_contracts import (
    ContractSeverity,
    ContractType,
    ContractViolation,
    FormalContract,
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


def test_contract_registry():
    """Test contract registry functionality."""

    # Create a test contract
    contract = FormalContract(
        contract_id="test_contract_001",
        contract_type=ContractType.PRECONDITION,
        predicate=lambda ctx: ctx.get("value", 0) > 0,
        description="Value must be positive",
        severity=ContractSeverity.HIGH,
    )

    # Register the contract
    contract_registry.register_contract(contract)

    assert "test_contract_001" in contract_registry.contracts
    assert contract_registry.contracts["test_contract_001"] == contract


def test_precondition_decorator():
    """Test precondition decorator."""

    @precondition(
        lambda ctx: ctx["args"][0] > 0,
        "Value must be positive",
        ContractSeverity.MEDIUM,
    )
    def test_function(value):
        return value * 2

    # This should work
    result = test_function(5)
    assert result == 10

    # This should trigger a warning but not fail
    result = test_function(-1)  # Negative value - should violate precondition
    assert result == -2  # Function still executes

    # Check that violation was recorded
    violations = [
        v for v in contract_registry.violations if v.function_name == "test_function"
    ]
    assert len(violations) > 0


def test_postcondition_decorator():
    """Test postcondition decorator."""

    @postcondition(positive_result, "Result must be positive", ContractSeverity.HIGH)
    def positive_function(value):
        return abs(value)

    # This should work
    result = positive_function(-5)
    assert result == 5

    # Test with a function that violates postcondition
    @postcondition(positive_result, "Result must be positive", ContractSeverity.HIGH)
    def negative_function(value):
        return -abs(value)

    # This should trigger a warning
    result = negative_function(5)
    assert result == -5

    # Check that violation was recorded
    violations = [
        v
        for v in contract_registry.violations
        if v.function_name == "negative_function"
    ]
    assert len(violations) > 0


def test_invariant_decorator():
    """Test invariant decorator."""

    @invariant(
        lambda instance: instance.value >= 0,
        "Value must always be non-negative",
        ContractSeverity.CRITICAL,
    )
    class TestClass:
        def __init__(self, value):
            self.value = value

        def set_value(self, new_value):
            self.value = new_value

        def get_value(self):
            return self.value

    # This should work
    obj = TestClass(5)
    assert obj.get_value() == 5

    obj.set_value(10)
    assert obj.get_value() == 10

    # This should trigger a critical violation
    with pytest.raises(RuntimeError):
        obj.set_value(-5)


def test_temporal_property_decorator():
    """Test temporal property decorator."""

    @temporal_property(
        lambda history: len(history) <= 5,  # Max 5 calls
        "Function called too many times",
        ContractSeverity.MEDIUM,
    )
    def limited_function(value):
        return value + 1

    # First few calls should work
    for i in range(5):
        result = limited_function(i)
        assert result == i + 1

    # Sixth call should trigger violation
    result = limited_function(5)
    assert result == 6

    # Check that violation was recorded
    violations = [
        v for v in contract_registry.violations if v.function_name == "limited_function"
    ]
    assert len(violations) > 0


def test_safety_property_decorator():
    """Test safety property decorator."""

    @safety_property(
        lambda ctx: all(isinstance(arg, int) for arg in ctx["args"]),
        "All arguments must be integers",
        ContractSeverity.HIGH,
    )
    def integer_only_function(a, b):
        return a + b

    # This should work
    result = integer_only_function(1, 2)
    assert result == 3

    # This should trigger a violation
    result = integer_only_function(1.5, 2)
    assert result == 3.5

    # Check that violation was recorded
    violations = [
        v
        for v in contract_registry.violations
        if v.function_name == "integer_only_function"
    ]
    assert len(violations) > 0


def test_contract_violation_serialization():
    """Test contract violation serialization."""

    violation = ContractViolation(
        contract_id="test_violation",
        contract_type=ContractType.PRECONDITION,
        severity=ContractSeverity.HIGH,
        message="Test violation message",
        function_name="test_function",
        file_path="/test/path.py",
        line_number=42,
        timestamp=datetime.now(timezone.utc),
        context={"test": "data"},
    )

    violation_dict = violation.to_dict()

    assert violation_dict["contract_id"] == "test_violation"
    assert violation_dict["contract_type"] == "precondition"
    assert violation_dict["severity"] == "high"
    assert violation_dict["message"] == "Test violation message"
    assert violation_dict["function_name"] == "test_function"
    assert violation_dict["context"]["test"] == "data"


def test_formal_verification_engine():
    """Test formal verification engine."""

    # Test enabling/disabling verification
    formal_verification.disable_verification()
    assert not formal_verification.verification_enabled
    assert not contract_registry.enabled

    formal_verification.enable_verification()
    assert formal_verification.verification_enabled
    assert contract_registry.enabled

    # Test adding custom contract
    formal_verification.add_custom_contract(
        contract_id="custom_test",
        contract_type=ContractType.SAFETY,
        predicate=lambda ctx: True,
        description="Custom test contract",
        severity=ContractSeverity.LOW,
    )

    assert "custom_test" in contract_registry.contracts

    # Test violation report
    report = formal_verification.get_violation_report()
    assert "total_violations" in report
    assert "violations_by_severity" in report
    assert "violations_by_type" in report
    assert "contract_statistics" in report


def test_capsule_contract_verification():
    """Test capsule-specific contract verification."""

    # Valid capsule data
    valid_capsule = {
        "capsule_id": "valid_capsule_001",
        "timestamp": datetime.now(timezone.utc),
        "version": "7.0",
        "status": "active",
    }

    violations = formal_verification.verify_capsule_contracts(valid_capsule)
    assert len(violations) == 0

    # Invalid capsule data
    invalid_capsule = {
        "capsule_id": "",  # Empty ID
        "timestamp": None,  # No timestamp
        "version": "invalid",  # Invalid version
        "status": "unknown",  # Invalid status
    }

    violations = formal_verification.verify_capsule_contracts(invalid_capsule)
    assert len(violations) > 0


def test_common_contract_predicates():
    """Test common contract predicates."""

    # Test not_none
    assert not_none({"result": "something"}) is True
    assert not_none({"result": None}) is False

    # Test positive_result
    assert positive_result({"result": 5}) is True
    assert positive_result({"result": -5}) is False
    assert positive_result({"result": "not_a_number"}) is False

    # Test non_empty_string
    assert non_empty_string({"result": "hello"}) is True
    assert non_empty_string({"result": ""}) is False
    assert non_empty_string({"result": 123}) is False

    # Test valid_capsule_id
    assert valid_capsule_id({"capsule_id": "valid_id_123"}) is True
    assert valid_capsule_id({"capsule_id": "short"}) is False
    assert valid_capsule_id({"result": "valid_result_id"}) is True


def test_contract_statistics():
    """Test contract statistics generation."""

    # Add some test contracts
    for i in range(3):
        contract = FormalContract(
            contract_id=f"stats_test_{i}",
            contract_type=ContractType.PRECONDITION,
            predicate=lambda ctx: True,
            description=f"Test contract {i}",
            severity=ContractSeverity.MEDIUM,
        )
        contract_registry.register_contract(contract)

    stats = contract_registry.get_contract_statistics()

    assert stats["total_contracts"] >= 3
    assert stats["enabled_contracts"] >= 3
    assert "severity_counts" in stats
    assert stats["registry_enabled"] is True


def test_violation_clearing():
    """Test clearing violations."""

    # Create a violation
    @precondition(
        lambda ctx: False,
        "Always fails",
        ContractSeverity.LOW,  # Always fails
    )
    def failing_function():
        return "result"

    # Call function to generate violation
    result = failing_function()
    assert result == "result"

    # Check violation was recorded
    initial_violations = len(contract_registry.violations)
    assert initial_violations > 0

    # Clear violations
    formal_verification.clear_violations()

    # Check violations were cleared
    assert len(contract_registry.violations) == 0


def test_contract_enabling_disabling():
    """Test enabling/disabling individual contracts."""

    contract = FormalContract(
        contract_id="toggle_test",
        contract_type=ContractType.PRECONDITION,
        predicate=lambda ctx: False,  # Always fails
        description="Toggle test",
        severity=ContractSeverity.LOW,
    )

    contract_registry.register_contract(contract)

    # Contract should be enabled by default
    assert contract.enabled is True

    # Disable contract
    contract.enabled = False

    # Create function with this contract
    contract_registry.register_function_contract("toggle_function", "toggle_test")

    # Call function - should not generate violation because contract is disabled
    initial_violations = len(contract_registry.violations)
    violations = contract_registry.check_contracts(
        "toggle_function", {"test": "context"}
    )

    assert len(violations) == 0
    assert len(contract_registry.violations) == initial_violations


def test_contract_violation_recording():
    """Test violation recording and statistics."""

    contract = FormalContract(
        contract_id="violation_test",
        contract_type=ContractType.POSTCONDITION,
        predicate=lambda ctx: False,  # Always fails
        description="Violation recording test",
        severity=ContractSeverity.MEDIUM,
    )

    contract_registry.register_contract(contract)

    # Initially no violations
    assert contract.violation_count == 0
    assert contract.last_violation is None

    # Check contract (should fail)
    result = contract.check({"test": "context"})
    assert result is False

    # Record violation
    contract.record_violation()

    # Check violation was recorded
    assert contract.violation_count == 1
    assert contract.last_violation is not None
    assert isinstance(contract.last_violation, datetime)


if __name__ == "__main__":
    test_contract_registry()
    test_precondition_decorator()
    test_postcondition_decorator()
    test_invariant_decorator()
    test_temporal_property_decorator()
    test_safety_property_decorator()
    test_contract_violation_serialization()
    test_formal_verification_engine()
    test_capsule_contract_verification()
    test_common_contract_predicates()
    test_contract_statistics()
    test_violation_clearing()
    test_contract_enabling_disabling()
    test_contract_violation_recording()
    print("✅ All formal verification tests passed!")
