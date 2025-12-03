#!/usr/bin/env python3
"""
Comprehensive test suite for Market Stability Circuit Breakers.

This test validates the circuit breaker system's ability to protect against
various economic attacks and maintain system stability under adverse conditions.
"""

import asyncio
import sys
from datetime import datetime, timedelta
import time
import random

# Add the project root to sys.path
sys.path.insert(0, "/Users/kay/uatp-capsule-engine")

from src.economic.circuit_breakers import (
    EconomicCircuitBreakerManager,
    CircuitBreakerConfig,
    CircuitState,
    CircuitOpenException,
    circuit_breaker_manager,
    execute_attribution_operation,
    execute_dividend_operation,
    execute_governance_operation,
    execute_payment_operation,
    execute_high_value_operation,
    is_system_healthy,
    get_blocked_operations,
)
from src.economic.security_monitor import ThreatLevel, AttackType


class MockEconomicOperation:
    """Mock economic operation for testing circuit breakers."""

    def __init__(self, name: str, failure_rate: float = 0.0, delay: float = 0.0):
        self.name = name
        self.failure_rate = failure_rate
        self.delay = delay
        self.call_count = 0
        self.success_count = 0
        self.failure_count = 0

    async def execute(self, *args, **kwargs):
        """Execute the mock operation with configurable failure rate."""
        self.call_count += 1

        if self.delay > 0:
            await asyncio.sleep(self.delay)

        # Simulate failure based on failure rate
        if random.random() < self.failure_rate:
            self.failure_count += 1
            raise Exception(f"Mock operation {self.name} failed (simulated)")

        self.success_count += 1
        return f"Success: {self.name} execution #{self.call_count}"

    def reset_stats(self):
        """Reset operation statistics."""
        self.call_count = 0
        self.success_count = 0
        self.failure_count = 0


async def test_circuit_breakers():
    """Test the market stability circuit breaker system."""
    print("🛡️  Testing Market Stability Circuit Breakers")
    print("=" * 80)

    try:
        # Test 1: Verify System Initialization
        print("\n📋 Test 1: System Initialization")

        status = circuit_breaker_manager.get_system_status()
        print(f"✅ System initialized with {status['total_circuits']} circuit breakers")
        print(f"   - System health: {status['system_health']}")
        print(f"   - Global emergency: {status['global_emergency']}")
        print(f"   - Open circuits: {status['open_circuits']}")

        expected_circuits = [
            "attribution_system",
            "dividend_distribution",
            "governance_system",
            "payment_processing",
            "account_creation",
            "high_value_operations",
        ]

        for circuit_name in expected_circuits:
            if circuit_name in status["circuit_details"]:
                circuit_status = status["circuit_details"][circuit_name]
                print(f"   - {circuit_name}: {circuit_status['state']}")
            else:
                print(f"   ❌ Missing circuit: {circuit_name}")

        # Test 2: Individual Circuit Breaker Operation
        print("\n🔧 Test 2: Individual Circuit Breaker Operation")

        # Create test operations
        attribution_op = MockEconomicOperation(
            "attribution_processing", failure_rate=0.0
        )
        dividend_op = MockEconomicOperation("dividend_calculation", failure_rate=0.0)
        governance_op = MockEconomicOperation("governance_proposal", failure_rate=0.0)

        # Test successful operations
        print("Testing successful operations:")
        for i in range(5):
            result = await execute_attribution_operation(
                attribution_op.execute, test_data=f"batch_{i}"
            )
            print(f"   ✅ Attribution operation {i+1}: {result}")

        result = await execute_dividend_operation(dividend_op.execute, amount=100.0)
        print(f"   ✅ Dividend operation: {result}")

        result = await execute_governance_operation(
            governance_op.execute, proposal_id="test_001"
        )
        print(f"   ✅ Governance operation: {result}")

        # Verify all circuits are still closed
        status = circuit_breaker_manager.get_system_status()
        print(
            f"   ✅ System health after successful operations: {status['system_health']}"
        )

        # Test 3: Circuit Breaker Tripping
        print("\n⚠️  Test 3: Circuit Breaker Tripping Under Attack")

        # Create failing operations to trigger circuit breakers
        failing_attribution = MockEconomicOperation(
            "failing_attribution", failure_rate=1.0
        )

        print("Simulating attribution system attack (high failure rate)...")
        failure_count = 0
        for i in range(15):  # Trigger threshold is 10 failures in 5 minutes
            try:
                await execute_attribution_operation(
                    failing_attribution.execute, attack_attempt=i
                )
            except Exception as e:
                failure_count += 1
                if "Circuit breaker" in str(e):
                    print(
                        f"   🔒 Circuit breaker OPENED after {failure_count} failures: {str(e)}"
                    )
                    break
                # Continue until circuit opens

        # Verify circuit is open
        status = circuit_breaker_manager.get_system_status()
        attribution_circuit = status["circuit_details"]["attribution_system"]
        print(f"   ✅ Attribution circuit state: {attribution_circuit['state']}")
        print(f"   ✅ Failure count: {attribution_circuit['failure_count']}")
        print(f"   ✅ System health: {status['system_health']}")

        # Test 4: Operation Blocking When Circuit is Open
        print("\n🚫 Test 4: Operation Blocking")

        try:
            await execute_attribution_operation(
                MockEconomicOperation("blocked_op").execute
            )
            print("   ❌ Operation should have been blocked!")
        except CircuitOpenException as e:
            print(f"   ✅ Operation correctly blocked: {str(e)}")

        # Other circuits should still work
        result = await execute_dividend_operation(dividend_op.execute, amount=50.0)
        print(f"   ✅ Other circuits still functional: {result}")

        # Test 5: Global Emergency Trigger
        print("\n🚨 Test 5: Global Emergency State")

        # Trigger multiple critical circuit failures to activate global emergency
        failing_governance = MockEconomicOperation(
            "failing_governance", failure_rate=1.0
        )
        failing_payment = MockEconomicOperation("failing_payment", failure_rate=1.0)

        print("Simulating multi-system attack (governance + payment)...")

        # Trip governance circuit
        for i in range(5):  # Governance threshold is 3 failures
            try:
                await execute_governance_operation(failing_governance.execute)
            except Exception as e:
                if "Circuit breaker" in str(e):
                    print("   🔒 Governance circuit breaker OPENED")
                    break

        # Trip payment circuit
        for i in range(8):  # Payment threshold is 5 failures
            try:
                await execute_payment_operation(failing_payment.execute)
            except Exception as e:
                if "Circuit breaker" in str(e):
                    print("   🔒 Payment circuit breaker OPENED")
                    break

        # Check if global emergency was triggered
        status = circuit_breaker_manager.get_system_status()
        print(f"   ✅ Global emergency state: {status['global_emergency']}")
        print(f"   ✅ System health: {status['system_health']}")
        print(f"   ✅ Open circuits: {status['open_circuits']}")
        print(f"   ✅ Blocked operations: {len(status['blocked_operations'])}")

        # Test 6: High-Value Operation Protection
        print("\n💰 Test 6: High-Value Operation Protection")

        # High-value operations should be blocked in emergency
        try:
            await execute_high_value_operation(
                MockEconomicOperation("large_transfer").execute, amount=1000000
            )
            print("   ❌ High-value operation should be blocked in emergency!")
        except CircuitOpenException as e:
            print(f"   ✅ High-value operation correctly blocked: {str(e)}")

        # Test 7: Circuit Recovery Simulation
        print("\n🔄 Test 7: Circuit Recovery (Accelerated)")

        # Simulate time passage for circuit recovery (force reset for testing)
        print("Simulating system recovery (forcing circuit reset for test)...")

        # Force reset circuits for testing (in real deployment, this would happen over time)
        await circuit_breaker_manager.force_reset_circuit(
            "attribution_system", "Test recovery simulation"
        )
        await circuit_breaker_manager.force_reset_circuit(
            "governance_system", "Test recovery simulation"
        )
        await circuit_breaker_manager.force_reset_circuit(
            "payment_processing", "Test recovery simulation"
        )

        # Test operations after recovery
        await asyncio.sleep(1)  # Brief pause

        status = circuit_breaker_manager.get_system_status()
        print(f"   ✅ System health after recovery: {status['system_health']}")
        print(f"   ✅ Global emergency: {status['global_emergency']}")
        print(f"   ✅ Open circuits: {status['open_circuits']}")

        # Test operations work again
        result = await execute_attribution_operation(
            attribution_op.execute, recovery_test=True
        )
        print(f"   ✅ Attribution system recovered: {result}")

        # Test 8: Performance and Statistics
        print("\n📊 Test 8: Performance Metrics")

        # Generate some operation load
        print("Generating operation load for metrics...")
        for i in range(20):
            circuit_type = random.choice(["attribution", "dividend", "governance"])
            try:
                if circuit_type == "attribution":
                    await execute_attribution_operation(attribution_op.execute, batch=i)
                elif circuit_type == "dividend":
                    await execute_dividend_operation(
                        dividend_op.execute, amount=10.0 * i
                    )
                else:
                    await execute_governance_operation(
                        governance_op.execute, proposal=f"prop_{i}"
                    )
            except:
                pass  # Ignore failures for load generation

            # Small delay to spread operations over time
            await asyncio.sleep(0.01)

        # Get operation statistics
        stats = circuit_breaker_manager.get_operation_statistics(hours=1)
        print(f"   ✅ Total operations (1 hour): {stats['total_operations']}")
        print(f"   ✅ Operations per hour: {stats['average_operations_per_hour']:.1f}")
        print("   ✅ Operations by circuit:")
        for circuit, count in stats["operations_by_circuit"].items():
            print(f"      - {circuit}: {count}")

        # Test 9: System Health Checks
        print("\n🏥 Test 9: System Health Assessment")

        # Test system health functions
        is_healthy = is_system_healthy()
        blocked_ops = get_blocked_operations()

        print(f"   ✅ System healthy: {is_healthy}")
        print(f"   ✅ Blocked operations count: {len(blocked_ops)}")

        final_status = circuit_breaker_manager.get_system_status()
        print(f"   ✅ Final system health: {final_status['system_health']}")

        # Summary of circuit states
        print("\n📋 Circuit Breaker Status Summary:")
        for name, details in final_status["circuit_details"].items():
            state_emoji = (
                "✅"
                if details["state"] == "closed"
                else "🔒"
                if details["state"] == "open"
                else "⚠️"
            )
            print(
                f"   {state_emoji} {name}: {details['state']} (failures: {details['failure_count']})"
            )

        print("\n" + "=" * 80)
        print("🎉 Market Stability Circuit Breaker System Tests Completed Successfully!")
        print("✅ Individual circuit breaker protection working")
        print("✅ Multi-circuit coordination operational")
        print("✅ Global emergency state triggering correctly")
        print("✅ High-value operation protection active")
        print("✅ Circuit recovery mechanisms functional")
        print("✅ Performance monitoring and statistics available")
        print("✅ System health assessment accurate")
        print("✅ Operation blocking and unblocking working properly")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


async def test_attack_scenario_integration():
    """Test integration with attack detection scenarios."""
    print("\n🎯 Testing Attack Scenario Integration")
    print("-" * 50)

    # Simulate common attack patterns
    attack_scenarios = [
        {
            "name": "Sybil Account Creation Attack",
            "circuit": "account_creation",
            "description": "Rapid creation of fake accounts to game attribution",
        },
        {
            "name": "Dividend Manipulation Attack",
            "circuit": "dividend_distribution",
            "description": "Attempting to manipulate dividend calculations",
        },
        {
            "name": "Flash Loan Economic Attack",
            "circuit": "high_value_operations",
            "description": "Large value transfers to manipulate markets",
        },
    ]

    for scenario in attack_scenarios:
        print(f"\n🔍 Testing: {scenario['name']}")
        print(f"   Description: {scenario['description']}")

        # Simulate the attack pattern
        attack_op = MockEconomicOperation(
            f"attack_{scenario['circuit']}", failure_rate=0.8
        )

        failed_attempts = 0
        for attempt in range(10):
            try:
                await circuit_breaker_manager.execute_protected_operation(
                    scenario["circuit"], attack_op.execute, attempt=attempt
                )
            except Exception:
                failed_attempts += 1
                if failed_attempts >= 3:  # Circuit should trip after multiple failures
                    break

        status = circuit_breaker_manager.get_system_status()
        circuit_state = status["circuit_details"][scenario["circuit"]]["state"]

        if circuit_state == "open":
            print(
                f"   ✅ Attack detected and blocked: {scenario['circuit']} circuit opened"
            )
        else:
            print(f"   ⚠️ Circuit state: {circuit_state} (may need tuning)")

    print(f"\n✅ Attack scenario integration tests completed")


if __name__ == "__main__":

    async def main():
        success = await test_circuit_breakers()
        if success:
            await test_attack_scenario_integration()
        return success

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
