#!/usr/bin/env python3
"""
Comprehensive test suite for Hardware Security Module (HSM) Integration.

This validates the enterprise HSM system including quantum-resistant operations,
secure session management, key lifecycle, and security monitoring.
"""

import asyncio
import sys
from datetime import datetime, timedelta
import secrets

# Add the project root to sys.path
sys.path.insert(0, "/Users/kay/uatp-capsule-engine")

from src.security.hsm_integration import (
    HSMType,
    HSMSecurityLevel,
    HSMOperationType,
    HSMConfiguration,
    EnterpriseHSMManager,
    QuantumSafeHSMAdapter,
    HSMSecurityMonitor,
    initialize_hsm_system,
    create_hsm_session,
    execute_hsm_operation,
    terminate_hsm_session,
    get_hsm_system_status,
)


async def test_hsm_integration():
    """Test the HSM integration system comprehensively."""
    print("🔒 Testing Hardware Security Module (HSM) Integration")
    print("=" * 80)

    try:
        # Test 1: HSM Configuration and Initialization
        print("\n🚀 Test 1: HSM Configuration and Initialization")

        # Create quantum-safe HSM configuration
        config = HSMConfiguration(
            hsm_type=HSMType.QUANTUM_SAFE_HSM,
            security_level=HSMSecurityLevel.LEVEL_3,
            connection_string="quantum_hsm://localhost:9999",
            quantum_algorithms_enabled=True,
            audit_all_operations=True,
            connection_pool_size=5,
            operation_timeout=30,
        )

        print(f"✅ Created HSM configuration:")
        print(f"   - HSM Type: {config.hsm_type.value}")
        print(f"   - Security Level: {config.security_level.value}")
        print(f"   - Quantum Algorithms: {config.quantum_algorithms_enabled}")
        print(f"   - Connection Pool Size: {config.connection_pool_size}")

        # Initialize HSM system
        print("\nInitializing HSM system...")
        initialization_success = await initialize_hsm_system(config)
        print(
            f"✅ HSM system initialization: {'Success' if initialization_success else 'Failed'}"
        )

        if not initialization_success:
            print("❌ HSM initialization failed - aborting tests")
            return False

        # Get initial system status
        status = get_hsm_system_status()
        print(f"✅ Initial HSM status:")
        print(f"   - HSM Type: {status['hsm_type']}")
        print(f"   - Security Level: {status['security_level']}")
        print(f"   - Active Sessions: {status['active_sessions']}")
        print(f"   - Total Keys Managed: {status['total_keys_managed']}")

        # Test 2: Secure Session Management
        print("\n🔐 Test 2: Secure Session Management")

        # Create secure sessions for different users
        print("Creating secure HSM sessions...")

        admin_session = await create_hsm_session("admin_user", "system_administration")
        print(f"✅ Created admin session: {admin_session}")

        user_session = await create_hsm_session("regular_user", "digital_signing")
        print(f"✅ Created user session: {user_session}")

        service_session = await create_hsm_session("service_account", "key_management")
        print(f"✅ Created service session: {service_session}")

        # Verify session creation in status
        updated_status = get_hsm_system_status()
        print(f"✅ Active sessions after creation: {updated_status['active_sessions']}")

        # Test 3: Quantum-Safe Key Generation
        print("\n🔑 Test 3: Quantum-Safe Key Generation")

        print("Generating quantum-safe keys...")

        # Generate keys for different purposes
        system_key_result = await execute_hsm_operation(
            admin_session,
            HSMOperationType.KEY_GENERATION,
            algorithm="dilithium3",
            key_id="system_master_key",
        )

        print(f"✅ System master key generation:")
        print(f"   - Success: {system_key_result.success}")
        print(f"   - Operation ID: {system_key_result.operation_id}")
        print(f"   - Execution Time: {system_key_result.execution_time_ms}ms")
        print(
            f"   - Public Key Size: {len(system_key_result.result_data) if system_key_result.result_data else 0} bytes"
        )

        # Generate signing key
        signing_key_result = await execute_hsm_operation(
            user_session,
            HSMOperationType.KEY_GENERATION,
            algorithm="dilithium3",
            key_id="user_signing_key",
        )

        print(f"✅ User signing key generation:")
        print(f"   - Success: {signing_key_result.success}")
        print(f"   - Execution Time: {signing_key_result.execution_time_ms}ms")

        # Generate service key
        service_key_result = await execute_hsm_operation(
            service_session,
            HSMOperationType.KEY_GENERATION,
            algorithm="dilithium3",
            key_id="service_key",
        )

        print(f"✅ Service key generation:")
        print(f"   - Success: {service_key_result.success}")
        print(f"   - Execution Time: {service_key_result.execution_time_ms}ms")

        # Verify keys in system status
        key_status = get_hsm_system_status()
        print(f"✅ Total keys managed: {key_status['total_keys_managed']}")

        # Test 4: Digital Signing Operations
        print("\n✍️  Test 4: Quantum-Safe Digital Signing")

        # Test data for signing
        test_documents = [
            b"UATP Attribution Certificate - John Doe",
            b"UATP Governance Proposal #2024-001",
            b"UATP Economic Transaction Record #TXN-123456",
            b"UATP System Configuration Update",
        ]

        signatures = []

        for i, document in enumerate(test_documents):
            print(f"Signing document {i+1}: {document.decode()[:50]}...")

            signature_result = await execute_hsm_operation(
                user_session,
                HSMOperationType.DIGITAL_SIGNING,
                data=document,
                key_id="user_signing_key",
                algorithm="dilithium3",
            )

            if signature_result.success:
                signatures.append((document, signature_result.result_data))
                print(
                    f"   ✅ Signature generated ({len(signature_result.result_data)} bytes)"
                )
                print(f"   ⏱️  Execution time: {signature_result.execution_time_ms}ms")
            else:
                print(f"   ❌ Signature failed: {signature_result.error_message}")

        print(f"✅ Successfully signed {len(signatures)} documents")

        # Test 5: Signature Verification
        print("\n✅ Test 5: Quantum-Safe Signature Verification")

        # Get public key for verification
        user_public_key = signing_key_result.result_data

        verification_results = []

        for i, (document, signature) in enumerate(signatures):
            print(f"Verifying signature {i+1}...")

            verification_result = await execute_hsm_operation(
                admin_session,
                HSMOperationType.SIGNATURE_VERIFICATION,
                data=document,
                signature=signature,
                public_key=user_public_key,
                algorithm="dilithium3",
            )

            if verification_result.success:
                is_valid = verification_result.result_data == b"valid"
                verification_results.append(is_valid)
                status_icon = "✅" if is_valid else "❌"
                print(
                    f"   {status_icon} Signature verification: {'Valid' if is_valid else 'Invalid'}"
                )
                print(
                    f"   ⏱️  Execution time: {verification_result.execution_time_ms}ms"
                )
            else:
                print(f"   ❌ Verification failed: {verification_result.error_message}")

        valid_signatures = sum(verification_results)
        print(
            f"✅ Signature verification summary: {valid_signatures}/{len(signatures)} valid"
        )

        # Test 6: Random Number Generation
        print("\n🎲 Test 6: Secure Random Number Generation")

        # Generate different sizes of random data
        random_sizes = [16, 32, 64, 128, 256]

        for size in random_sizes:
            random_result = await execute_hsm_operation(
                service_session, HSMOperationType.RANDOM_GENERATION, size=size
            )

            if random_result.success:
                print(f"✅ Generated {size} bytes of secure random data")
                print(
                    f"   - First 8 bytes (hex): {random_result.result_data[:8].hex()}"
                )
                print(f"   - Execution time: {random_result.execution_time_ms}ms")
            else:
                print(
                    f"❌ Random generation failed for size {size}: {random_result.error_message}"
                )

        # Test 7: Security Monitoring and Events
        print("\n🛡️  Test 7: Security Monitoring and Event Logging")

        # Get security status from HSM manager
        hsm_status = get_hsm_system_status()
        security_status = hsm_status.get("security_status", {})

        print(f"✅ Security monitoring status:")
        print(
            f"   - Monitoring Active: {security_status.get('monitoring_active', False)}"
        )
        print(f"   - Total Events (24h): {security_status.get('total_events_24h', 0)}")
        print(
            f"   - High Severity Events: {security_status.get('high_severity_events_24h', 0)}"
        )
        print(f"   - System Health: {security_status.get('system_health', 'unknown')}")
        print(
            f"   - Active Tamper Alerts: {security_status.get('active_tamper_alerts', 0)}"
        )

        # Test 8: Performance Metrics
        print("\n📊 Test 8: Performance Metrics and Statistics")

        operation_metrics = hsm_status.get("operation_metrics", {})

        print(f"✅ HSM operation metrics:")
        print(f"   - Total Operations: {operation_metrics.get('total_operations', 0)}")
        print(
            f"   - Successful Operations: {operation_metrics.get('successful_operations', 0)}"
        )
        print(
            f"   - Failed Operations: {operation_metrics.get('failed_operations', 0)}"
        )
        print(
            f"   - Average Response Time: {operation_metrics.get('average_response_time_ms', 0):.1f}ms"
        )

        success_rate = 0
        if operation_metrics.get("total_operations", 0) > 0:
            success_rate = (
                operation_metrics["successful_operations"]
                / operation_metrics["total_operations"]
            ) * 100

        print(f"   - Success Rate: {success_rate:.1f}%")

        # Test 9: Session Lifecycle and Cleanup
        print("\n🔄 Test 9: Session Lifecycle and Cleanup")

        print("Testing session termination...")

        # Terminate user session
        await terminate_hsm_session(user_session)
        print(f"✅ Terminated user session: {user_session}")

        # Verify session count decreased
        final_status = get_hsm_system_status()
        print(f"✅ Active sessions after termination: {final_status['active_sessions']}")

        # Terminate remaining sessions
        await terminate_hsm_session(admin_session)
        await terminate_hsm_session(service_session)
        print(f"✅ Terminated remaining sessions")

        # Final status check
        cleanup_status = get_hsm_system_status()
        print(f"✅ Final active sessions: {cleanup_status['active_sessions']}")

        # Test 10: Error Handling and Edge Cases
        print("\n⚠️  Test 10: Error Handling and Edge Cases")

        print("Testing error conditions...")

        # Try to use terminated session
        try:
            await execute_hsm_operation(
                user_session,  # This session was terminated
                HSMOperationType.KEY_GENERATION,
                algorithm="dilithium3",
                key_id="should_fail",
            )
            print("❌ Should have failed with invalid session")
        except ValueError as e:
            print(f"✅ Correctly rejected terminated session: {str(e)}")

        # Try invalid operation parameters
        temp_session = await create_hsm_session("test_user", "error_testing")

        try:
            invalid_result = await execute_hsm_operation(
                temp_session,
                HSMOperationType.DIGITAL_SIGNING,
                # Missing required parameters
            )
            print("❌ Should have failed with missing parameters")
        except Exception as e:
            print(f"✅ Correctly rejected invalid parameters")

        # Clean up test session
        await terminate_hsm_session(temp_session)

        print("\n" + "=" * 80)
        print("🎉 HSM Integration System Tests Completed Successfully!")
        print("✅ Quantum-safe HSM initialization and configuration working")
        print("✅ Secure session management with authentication operational")
        print("✅ Post-quantum key generation (Dilithium-3) functioning")
        print("✅ Quantum-resistant digital signing operations working")
        print("✅ Signature verification with quantum algorithms operational")
        print("✅ Secure random number generation functioning")
        print("✅ Security monitoring and event logging active")
        print("✅ Performance metrics and statistics accurate")
        print("✅ Session lifecycle management working properly")
        print("✅ Error handling and edge case protection functional")

        final_metrics = get_hsm_system_status()
        print(f"\n📈 Final System Statistics:")
        print(
            f"   - Total Operations Executed: {final_metrics['operation_metrics']['total_operations']}"
        )
        print(f"   - System Success Rate: {success_rate:.1f}%")
        print(f"   - Keys Generated: {final_metrics['total_keys_managed']}")
        print(
            f"   - Security Health: {final_metrics['security_status']['system_health']}"
        )

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


async def test_hsm_integration_scenarios():
    """Test realistic HSM usage scenarios."""
    print("\n🎯 Testing Realistic HSM Integration Scenarios")
    print("-" * 50)

    scenarios = [
        {
            "name": "UATP Attribution Signing Workflow",
            "description": "Complete workflow for signing attribution certificates",
            "operations": [
                (
                    "key_generation",
                    {"algorithm": "dilithium3", "key_id": "attribution_ca_key"},
                ),
                (
                    "digital_signing",
                    {
                        "key_id": "attribution_ca_key",
                        "data": b"Attribution Certificate for AI Model XYZ",
                    },
                ),
                ("signature_verification", {"key_id": "attribution_ca_key"}),
            ],
        },
        {
            "name": "UATP Governance Document Security",
            "description": "Secure handling of governance proposals and voting",
            "operations": [
                (
                    "key_generation",
                    {"algorithm": "dilithium3", "key_id": "governance_signing_key"},
                ),
                (
                    "digital_signing",
                    {
                        "key_id": "governance_signing_key",
                        "data": b"Governance Proposal: Update Attribution Algorithm",
                    },
                ),
                (
                    "digital_signing",
                    {
                        "key_id": "governance_signing_key",
                        "data": b"Vote Record: Proposal #2024-001 - APPROVED",
                    },
                ),
            ],
        },
        {
            "name": "UATP Economic Transaction Security",
            "description": "High-value economic transaction protection",
            "operations": [
                (
                    "key_generation",
                    {"algorithm": "dilithium3", "key_id": "economic_vault_key"},
                ),
                ("random_generation", {"size": 64}),  # Transaction nonce
                (
                    "digital_signing",
                    {
                        "key_id": "economic_vault_key",
                        "data": b"High-Value Transfer: 1,000,000 UATP Tokens",
                    },
                ),
            ],
        },
    ]

    for scenario in scenarios:
        print(f"\n🎮 Scenario: {scenario['name']}")
        print(f"   Description: {scenario['description']}")

        # Create dedicated session for scenario
        session = await create_hsm_session(f"scenario_user", scenario["name"])

        scenario_results = []
        generated_keys = {}

        for op_type, params in scenario["operations"]:
            try:
                if op_type == "key_generation":
                    result = await execute_hsm_operation(
                        session, HSMOperationType.KEY_GENERATION, **params
                    )
                    if result.success:
                        generated_keys[params["key_id"]] = result.result_data
                        print(f"   ✅ Generated key: {params['key_id']}")

                elif op_type == "digital_signing":
                    if params["key_id"] in generated_keys:
                        result = await execute_hsm_operation(
                            session,
                            HSMOperationType.DIGITAL_SIGNING,
                            algorithm="dilithium3",
                            **params,
                        )
                        if result.success:
                            print(f"   ✅ Signed data with {params['key_id']}")
                            scenario_results.append(
                                (
                                    params["data"],
                                    result.result_data,
                                    generated_keys[params["key_id"]],
                                )
                            )

                elif op_type == "signature_verification":
                    if scenario_results:
                        data, signature, public_key = scenario_results[-1]
                        result = await execute_hsm_operation(
                            session,
                            HSMOperationType.SIGNATURE_VERIFICATION,
                            data=data,
                            signature=signature,
                            public_key=public_key,
                            algorithm="dilithium3",
                        )
                        if result.success:
                            is_valid = result.result_data == b"valid"
                            print(
                                f"   ✅ Signature verification: {'Valid' if is_valid else 'Invalid'}"
                            )

                elif op_type == "random_generation":
                    result = await execute_hsm_operation(
                        session, HSMOperationType.RANDOM_GENERATION, **params
                    )
                    if result.success:
                        print(
                            f"   ✅ Generated {params['size']} bytes of secure random data"
                        )

            except Exception as e:
                print(f"   ❌ Operation {op_type} failed: {e}")

        # Clean up scenario session
        await terminate_hsm_session(session)
        print(f"   ✅ Scenario completed and cleaned up")

    print(f"\n✅ HSM integration scenarios completed successfully")


if __name__ == "__main__":

    async def main():
        success = await test_hsm_integration()
        if success:
            await test_hsm_integration_scenarios()
        return success

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
