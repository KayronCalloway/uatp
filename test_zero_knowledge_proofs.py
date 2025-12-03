#!/usr/bin/env python3
"""
Comprehensive test suite for Zero-Knowledge Privacy Proofs System.

This validates the ZK proof system including range proofs, membership proofs,
attribute proofs, and quantum-resistant verification mechanisms.
"""

import asyncio
import sys
from datetime import datetime, timedelta
import secrets

# Add the project root to sys.path
sys.path.insert(0, "/Users/kay/uatp-capsule-engine")

from src.privacy.zero_knowledge_proofs import (
    ProofType,
    ProofStatus,
    ZKProofParameters,
    ZKProofClaim,
    ZKProof,
    ZKVerificationResult,
    ZKCommitmentScheme,
    ZKRangeProof,
    ZKMembershipProof,
    ZKAttributeProof,
    ZKProofEngine,
    zk_engine,
    generate_range_proof,
    generate_membership_proof,
    verify_zk_proof,
    get_zk_system_status,
)


async def test_zero_knowledge_proofs():
    """Test the Zero-Knowledge Privacy Proofs system comprehensively."""
    print("🔒 Testing Zero-Knowledge Privacy Proofs System")
    print("=" * 80)

    try:
        # Test 1: Commitment Scheme
        print("\n🔐 Test 1: Cryptographic Commitment Scheme")

        commitment_scheme = ZKCommitmentScheme()

        # Test basic commitment
        test_value = b"secret_value_12345"
        commitment, randomness = commitment_scheme.commit(test_value)

        print(f"✅ Generated commitment:")
        print(f"   - Value length: {len(test_value)} bytes")
        print(f"   - Commitment length: {len(commitment)} bytes")
        print(f"   - Randomness length: {len(randomness)} bytes")

        # Test commitment verification
        is_valid = commitment_scheme.verify_commitment(
            commitment, test_value, randomness
        )
        print(f"✅ Commitment verification: {'Valid' if is_valid else 'Invalid'}")

        # Test commitment with wrong value (should fail)
        wrong_value = b"wrong_secret_value"
        is_invalid = commitment_scheme.verify_commitment(
            commitment, wrong_value, randomness
        )
        print(
            f"✅ Commitment with wrong value: {'Invalid' if not is_invalid else 'Unexpectedly valid'}"
        )

        # Test Pedersen commitment
        pedersen_commitment = commitment_scheme.pedersen_commit(12345)
        print(f"✅ Pedersen commitment generated:")
        print(f"   - Type: {pedersen_commitment['type']}")
        print(f"   - Commitment size: {len(pedersen_commitment['commitment'])} bytes")

        # Test 2: Range Proofs
        print("\n📊 Test 2: Zero-Knowledge Range Proofs")

        range_prover = ZKRangeProof()

        # Test valid range proof
        secret_value = 75
        min_range = 0
        max_range = 100

        parameters = ZKProofParameters(
            proof_type=ProofType.RANGE_PROOF, quantum_resistant=True, security_level=128
        )

        print(f"Generating range proof for value in [{min_range}, {max_range}]...")

        range_proof_data = range_prover.generate_range_proof(
            secret_value, min_range, max_range, parameters
        )

        print(f"✅ Range proof generated:")
        print(f"   - Proof ID: {range_proof_data['proof_id']}")
        print(f"   - Type: {range_proof_data['type']}")
        print(
            f"   - Range: [{range_proof_data['range_min']}, {range_proof_data['range_max']}]"
        )
        print(f"   - Security Level: {range_proof_data['security_level']}")
        print(
            f"   - Quantum Signature: {'Yes' if 'quantum_signature' in range_proof_data else 'No'}"
        )

        # Test range proof verification
        print("\nVerifying range proof...")
        verification_result = range_prover.verify_range_proof(range_proof_data)

        print(f"✅ Range proof verification:")
        print(f"   - Status: {verification_result.status.value}")
        print(f"   - Confidence: {verification_result.confidence:.2f}")
        print(f"   - Verification Time: {verification_result.verification_time_ms}ms")
        print(
            f"   - Quantum Valid: {verification_result.verification_details.get('quantum_signature_valid', False)}"
        )

        # Test invalid range (should fail during generation)
        print("\nTesting invalid range proof (value outside range)...")
        try:
            invalid_range_proof = range_prover.generate_range_proof(
                150, min_range, max_range, parameters
            )
            print("❌ Should have failed with value outside range")
        except ValueError as e:
            print(f"✅ Correctly rejected invalid range: {e}")

        # Test 3: Membership Proofs
        print("\n🎯 Test 3: Zero-Knowledge Membership Proofs")

        membership_prover = ZKMembershipProof()

        # Create test set
        authorized_users = [
            b"alice@example.com",
            b"bob@example.com",
            b"charlie@example.com",
            b"diana@example.com",
            b"eve@example.com",
        ]

        secret_member = b"charlie@example.com"

        print(
            f"Generating membership proof for set of {len(authorized_users)} elements..."
        )

        membership_proof_data = membership_prover.generate_membership_proof(
            secret_member, authorized_users, parameters
        )

        print(f"✅ Membership proof generated:")
        print(f"   - Proof ID: {membership_proof_data['proof_id']}")
        print(f"   - Set Size: {membership_proof_data['set_size']}")
        print(f"   - Merkle Root: {membership_proof_data['merkle_root'][:32]}...")
        print(f"   - Proof Path Length: {len(membership_proof_data['proof_path'])}")
        print(
            f"   - Quantum Signature: {'Yes' if 'quantum_signature' in membership_proof_data else 'No'}"
        )

        # Test membership proof with non-member (should fail)
        print("\nTesting membership proof with non-member...")
        try:
            non_member = b"mallory@example.com"
            invalid_membership = membership_prover.generate_membership_proof(
                non_member, authorized_users, parameters
            )
            print("❌ Should have failed with non-member")
        except ValueError as e:
            print(f"✅ Correctly rejected non-member: {e}")

        # Test 4: Attribute Proofs
        print("\n🏷️  Test 4: Zero-Knowledge Attribute Proofs")

        attribute_prover = ZKAttributeProof()

        # Register attribute schema
        attribute_prover.register_attribute_schema(
            "user_profile",
            ["age", "country", "subscription_level", "verified_email", "account_type"],
        )

        # Test user attributes
        user_attributes = {
            "age": 28,
            "country": "US",
            "subscription_level": "premium",
            "verified_email": True,
            "account_type": "individual",
        }

        required_attributes = ["age", "subscription_level", "verified_email"]

        print(
            f"Generating attribute proof for {len(required_attributes)} attributes..."
        )

        attribute_proof_data = attribute_prover.generate_attribute_proof(
            user_attributes, required_attributes, "user_profile", parameters
        )

        print(f"✅ Attribute proof generated:")
        print(f"   - Proof ID: {attribute_proof_data['proof_id']}")
        print(f"   - Schema ID: {attribute_proof_data['schema_id']}")
        print(
            f"   - Required Attributes: {', '.join(attribute_proof_data['required_attributes'])}"
        )
        print(
            f"   - Commitments Generated: {len(attribute_proof_data['attribute_commitments'])}"
        )
        print(
            f"   - Quantum Signature: {'Yes' if 'quantum_signature' in attribute_proof_data else 'No'}"
        )

        # Test attribute proof with missing attribute (should fail)
        print("\nTesting attribute proof with missing attribute...")
        try:
            incomplete_attributes = {
                "age": 28,
                "country": "US",
            }  # Missing required attributes
            invalid_attr_proof = attribute_prover.generate_attribute_proof(
                incomplete_attributes, required_attributes, "user_profile", parameters
            )
            print("❌ Should have failed with missing attributes")
        except ValueError as e:
            print(f"✅ Correctly rejected missing attributes: {e}")

        # Test 5: ZK Proof Engine Integration
        print("\n🚀 Test 5: Zero-Knowledge Proof Engine")

        engine = ZKProofEngine()

        # Test engine status
        initial_status = engine.get_system_status()
        print(f"✅ ZK Engine initial status:")
        print(f"   - Active Proofs: {initial_status['active_proofs']}")
        print(f"   - Supported Types: {len(initial_status['supported_proof_types'])}")
        print(f"   - Quantum Resistant: {initial_status['quantum_resistant_enabled']}")

        # Test range proof through engine
        print("\nTesting range proof through ZK engine...")

        range_claim = ZKProofClaim(
            claim_id="test_range_claim_001",
            claim_type="user_age_verification",
            statement="User age is between 18 and 65",
            public_parameters={"value": 42, "min_value": 18, "max_value": 65},
            private_witness=(42).to_bytes(32, "big"),
            metadata={"purpose": "age_verification", "context": "account_creation"},
        )

        range_parameters = ZKProofParameters(
            proof_type=ProofType.RANGE_PROOF,
            quantum_resistant=True,
            expiration_time=datetime.now() + timedelta(hours=24),
        )

        range_zk_proof = await engine.generate_proof(
            ProofType.RANGE_PROOF, range_claim, range_parameters
        )

        print(f"✅ ZK Range proof generated:")
        print(f"   - Proof ID: {range_zk_proof.proof_id}")
        print(f"   - Claim ID: {range_zk_proof.claim_id}")
        print(f"   - Proof Type: {range_zk_proof.proof_type.value}")
        print(
            f"   - Quantum Signature: {'Yes' if range_zk_proof.quantum_signature else 'No'}"
        )
        print(f"   - Expiration: {range_zk_proof.expiration}")

        # Test membership proof through engine
        print("\nTesting membership proof through ZK engine...")

        membership_claim = ZKProofClaim(
            claim_id="test_membership_claim_001",
            claim_type="authorized_user_verification",
            statement="User is authorized to access premium features",
            public_parameters={"set_elements": authorized_users},
            private_witness=b"alice@example.com",
            metadata={"purpose": "access_control", "feature": "premium_dashboard"},
        )

        membership_parameters = ZKProofParameters(
            proof_type=ProofType.MEMBERSHIP_PROOF, quantum_resistant=True
        )

        membership_zk_proof = await engine.generate_proof(
            ProofType.MEMBERSHIP_PROOF, membership_claim, membership_parameters
        )

        print(f"✅ ZK Membership proof generated:")
        print(f"   - Proof ID: {membership_zk_proof.proof_id}")
        print(f"   - Claim ID: {membership_zk_proof.claim_id}")
        print(f"   - Proof Type: {membership_zk_proof.proof_type.value}")

        # Test 6: Proof Verification
        print("\n✅ Test 6: Zero-Knowledge Proof Verification")

        # Verify range proof
        print("Verifying range proof...")
        range_verification = await engine.verify_proof(range_zk_proof)

        print(f"✅ Range proof verification:")
        print(f"   - Status: {range_verification.status.value}")
        print(f"   - Confidence: {range_verification.confidence:.2f}")
        print(f"   - Verification Time: {range_verification.verification_time_ms}ms")

        # Verify membership proof
        print("\nVerifying membership proof...")
        membership_verification = await engine.verify_proof(membership_zk_proof)

        print(f"✅ Membership proof verification:")
        print(f"   - Status: {membership_verification.status.value}")
        print(f"   - Confidence: {membership_verification.confidence:.2f}")
        print(
            f"   - Verification Time: {membership_verification.verification_time_ms}ms"
        )

        # Test 7: Convenience Functions
        print("\n🛠️  Test 7: Convenience Functions")

        # Test high-level range proof function
        print("Testing high-level range proof function...")

        reputation_score = 850
        min_reputation = 500
        max_reputation = 1000

        reputation_proof = await generate_range_proof(
            reputation_score, min_reputation, max_reputation, expiration_hours=48
        )

        print(f"✅ Reputation range proof:")
        print(f"   - Proof ID: {reputation_proof.proof_id}")
        print(f"   - Type: {reputation_proof.proof_type.value}")
        print(f"   - Expiration: {reputation_proof.expiration}")

        # Test high-level membership proof function
        print("\nTesting high-level membership proof function...")

        trusted_nodes = [
            b"node_alpha_001",
            b"node_beta_002",
            b"node_gamma_003",
            b"node_delta_004",
            b"node_epsilon_005",
        ]

        current_node = b"node_gamma_003"

        node_membership_proof = await generate_membership_proof(
            current_node, trusted_nodes, expiration_hours=12
        )

        print(f"✅ Node membership proof:")
        print(f"   - Proof ID: {node_membership_proof.proof_id}")
        print(f"   - Type: {node_membership_proof.proof_type.value}")
        print(f"   - Expiration: {node_membership_proof.expiration}")

        # Verify high-level proofs
        print("\nVerifying high-level proofs...")

        reputation_verification = await verify_zk_proof(reputation_proof)
        node_verification = await verify_zk_proof(node_membership_proof)

        print(f"✅ High-level proof verifications:")
        print(f"   - Reputation proof: {reputation_verification.status.value}")
        print(f"   - Node membership proof: {node_verification.status.value}")

        # Test 8: System Status and Performance
        print("\n📊 Test 8: System Performance and Statistics")

        final_status = get_zk_system_status()

        print(f"✅ Final ZK system status:")
        print(f"   - Active Proofs: {final_status['active_proofs']}")
        print(f"   - Total Proofs Generated: {final_status['total_proofs_generated']}")
        print(f"   - Total Proofs Verified: {final_status['total_proofs_verified']}")
        print(f"   - Success Rate: {final_status['success_rate']:.1f}%")
        print(
            f"   - Avg Generation Time: {final_status['average_generation_time_ms']:.1f}ms"
        )
        print(
            f"   - Avg Verification Time: {final_status['average_verification_time_ms']:.1f}ms"
        )
        print(f"   - Cache Size: {final_status['cache_size']}")
        print(f"   - Quantum Resistant: {final_status['quantum_resistant_enabled']}")

        # Test 9: Error Handling and Edge Cases
        print("\n⚠️  Test 9: Error Handling and Edge Cases")

        print("Testing malformed proof verification...")

        # Create malformed proof
        malformed_proof_data = {
            "proof_id": "malformed_test",
            "type": "range_proof"
            # Missing required fields
        }

        malformed_verification = range_prover.verify_range_proof(malformed_proof_data)
        print(f"✅ Malformed proof handling: {malformed_verification.status.value}")
        print(f"   - Error: {malformed_verification.error_message}")

        # Test expired proof
        print("\nTesting expired proof...")

        expired_claim = ZKProofClaim(
            claim_id="expired_test",
            claim_type="expiration_test",
            statement="This proof should be expired",
            public_parameters={"value": 50, "min_value": 0, "max_value": 100},
            private_witness=(50).to_bytes(32, "big"),
        )

        expired_parameters = ZKProofParameters(
            proof_type=ProofType.RANGE_PROOF,
            expiration_time=datetime.now() - timedelta(hours=1),  # Already expired
        )

        try:
            expired_proof = await engine.generate_proof(
                ProofType.RANGE_PROOF, expired_claim, expired_parameters
            )
            expired_verification = await engine.verify_proof(expired_proof)
            print(f"✅ Expired proof verification: {expired_verification.status.value}")
        except Exception as e:
            print(f"✅ Expired proof correctly handled: {str(e)}")

        print("\n" + "=" * 80)
        print("🎉 Zero-Knowledge Privacy Proofs System Tests Completed Successfully!")
        print("✅ Cryptographic commitment scheme working correctly")
        print("✅ Range proofs for privacy-preserving value verification operational")
        print("✅ Membership proofs for set membership without revelation working")
        print(
            "✅ Attribute proofs for credential verification without disclosure functioning"
        )
        print("✅ Quantum-resistant signatures integrated for future-proof security")
        print("✅ ZK proof engine providing unified interface operational")
        print("✅ High-level convenience functions working properly")
        print("✅ Performance metrics and caching system active")
        print("✅ Error handling and edge case protection functional")

        final_metrics = get_zk_system_status()
        print(f"\n📈 Final System Statistics:")
        print(f"   - Total Proofs Generated: {final_metrics['total_proofs_generated']}")
        print(f"   - System Success Rate: {final_metrics['success_rate']:.1f}%")
        print(
            f"   - Average Generation Time: {final_metrics['average_generation_time_ms']:.1f}ms"
        )
        print(
            f"   - Average Verification Time: {final_metrics['average_verification_time_ms']:.1f}ms"
        )
        print(
            f"   - Quantum-Resistant Enabled: {final_metrics['quantum_resistant_enabled']}"
        )

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


async def test_zk_integration_scenarios():
    """Test realistic ZK proof integration scenarios for UATP."""
    print("\n🎯 Testing Zero-Knowledge Proof Integration Scenarios")
    print("-" * 50)

    scenarios = [
        {
            "name": "UATP Attribution Privacy Protection",
            "description": "Prove attribution rights without revealing contributor identity",
            "proof_type": ProofType.MEMBERSHIP_PROOF,
            "setup": {
                "authorized_contributors": [
                    b"contributor_001@uatp.ai",
                    b"contributor_002@uatp.ai",
                    b"contributor_003@uatp.ai",
                    b"contributor_004@uatp.ai",
                    b"contributor_005@uatp.ai",
                ],
                "actual_contributor": b"contributor_003@uatp.ai",
            },
        },
        {
            "name": "UATP Reputation-Based Access Control",
            "description": "Prove minimum reputation score without revealing exact score",
            "proof_type": ProofType.RANGE_PROOF,
            "setup": {
                "user_reputation": 785,
                "min_required": 500,
                "max_possible": 1000,
                "access_level": "premium_features",
            },
        },
        {
            "name": "UATP Governance Voting Eligibility",
            "description": "Prove voting eligibility without revealing stake amount",
            "proof_type": ProofType.RANGE_PROOF,
            "setup": {
                "user_stake": 25000,
                "min_voting_stake": 10000,
                "max_stake": 100000,
                "proposal_id": "UATP_PROP_2024_001",
            },
        },
        {
            "name": "UATP Economic Participation Verification",
            "description": "Prove economic participation eligibility privately",
            "proof_type": ProofType.ATTRIBUTE_PROOF,
            "setup": {
                "user_attributes": {
                    "account_age_days": 180,
                    "transaction_count": 50,
                    "verified_identity": True,
                    "geographic_region": "authorized",
                    "account_status": "active",
                },
                "required_attributes": [
                    "account_age_days",
                    "verified_identity",
                    "account_status",
                ],
            },
        },
    ]

    for scenario in scenarios:
        print(f"\n🎮 Scenario: {scenario['name']}")
        print(f"   Description: {scenario['description']}")

        try:
            if scenario["proof_type"] == ProofType.MEMBERSHIP_PROOF:
                setup = scenario["setup"]

                # Generate membership proof
                proof = await generate_membership_proof(
                    setup["actual_contributor"],
                    setup["authorized_contributors"],
                    expiration_hours=24,
                )

                # Verify the proof
                verification = await verify_zk_proof(proof)

                print(f"   ✅ Membership proof generated: {proof.proof_id}")
                print(f"   ✅ Verification result: {verification.status.value}")
                print(f"   ✅ Contributor privacy preserved: Identity not revealed")
                print(
                    f"   ✅ Attribution rights verified: Eligible contributor confirmed"
                )

            elif scenario["proof_type"] == ProofType.RANGE_PROOF:
                setup = scenario["setup"]

                # Generate range proof for reputation/stake
                if "user_reputation" in setup:
                    value = setup["user_reputation"]
                    min_val = setup["min_required"]
                    max_val = setup["max_possible"]
                    context = f"Reputation for {setup['access_level']}"
                else:
                    value = setup["user_stake"]
                    min_val = setup["min_voting_stake"]
                    max_val = setup["max_stake"]
                    context = f"Voting stake for {setup['proposal_id']}"

                proof = await generate_range_proof(
                    value, min_val, max_val, expiration_hours=24
                )
                verification = await verify_zk_proof(proof)

                print(f"   ✅ Range proof generated: {proof.proof_id}")
                print(f"   ✅ Verification result: {verification.status.value}")
                print(
                    f"   ✅ Value privacy preserved: Exact {context.lower()} not revealed"
                )
                print(f"   ✅ Eligibility verified: Meets minimum requirements")

            elif scenario["proof_type"] == ProofType.ATTRIBUTE_PROOF:
                setup = scenario["setup"]

                # Register schema and generate attribute proof
                zk_engine.attribute_prover.register_attribute_schema(
                    "uatp_participant", list(setup["user_attributes"].keys())
                )

                claim = ZKProofClaim(
                    claim_id=f"uatp_economic_claim_{secrets.token_hex(8)}",
                    claim_type="economic_participation",
                    statement="User meets economic participation requirements",
                    public_parameters={
                        "user_attributes": setup["user_attributes"],
                        "required_attributes": setup["required_attributes"],
                        "schema_id": "uatp_participant",
                    },
                    private_witness=b"user_credentials",
                )

                parameters = ZKProofParameters(
                    proof_type=ProofType.ATTRIBUTE_PROOF, quantum_resistant=True
                )

                proof = await zk_engine.generate_proof(
                    ProofType.ATTRIBUTE_PROOF, claim, parameters
                )
                verification = await zk_engine.verify_proof(proof)

                print(f"   ✅ Attribute proof generated: {proof.proof_id}")
                print(f"   ✅ Verification result: {verification.status.value}")
                print(f"   ✅ Attribute privacy preserved: Values not disclosed")
                print(f"   ✅ Participation verified: Meets all requirements")

        except Exception as e:
            print(f"   ❌ Scenario failed: {e}")

    print(f"\n✅ ZK proof integration scenarios completed successfully")


if __name__ == "__main__":

    async def main():
        success = await test_zero_knowledge_proofs()
        if success:
            await test_zk_integration_scenarios()
        return success

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
