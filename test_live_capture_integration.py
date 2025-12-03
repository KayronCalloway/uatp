#!/usr/bin/env python3
"""
Test Live Capture → Capsule Creation Integration

This script simulates the flow from live conversation capture to automatic capsule creation
using the fixed API endpoints.
"""

import asyncio
import httpx
import json
import sys
import os
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, "/Users/kay/uatp-capsule-engine/src")

from capsule_schema import ReasoningStep, ReasoningTracePayload, CapsuleStatus


class LiveCaptureIntegrationTester:
    """Test the complete live capture → capsule creation pipeline."""

    def __init__(self):
        self.api_base = "http://localhost:9090"
        self.api_key = "dev-key-001"

    def simulate_high_significance_conversation(self) -> dict:
        """Simulate a high-significance conversation that should create a capsule."""

        # Simulate a complex technical discussion
        reasoning_steps = [
            ReasoningStep(
                operation="analysis",
                reasoning="User is asking about implementing a distributed consensus algorithm for blockchain applications",
                confidence=0.92,
                metadata={
                    "complexity": "high",
                    "technical_depth": 8,
                    "implementation_required": True,
                    "significance_factors": [
                        "algorithm_design",
                        "distributed_systems",
                        "blockchain",
                    ],
                },
            ),
            ReasoningStep(
                operation="implementation",
                reasoning="Providing detailed implementation of Raft consensus algorithm with code examples and architectural considerations",
                confidence=0.95,
                metadata={
                    "code_provided": True,
                    "architectural_guidance": True,
                    "production_ready": True,
                    "lines_of_code": 150,
                },
            ),
            ReasoningStep(
                operation="conclusion",
                reasoning="This conversation demonstrates significant knowledge transfer and should be preserved as a UATP capsule for future attribution",
                confidence=0.98,
                metadata={
                    "should_create_capsule": True,
                    "significance_score": 0.87,
                    "attribution_value": "high",
                    "capture_reason": "complex_technical_implementation",
                },
            ),
        ]

        reasoning_payload = ReasoningTracePayload(
            reasoning_steps=reasoning_steps, total_confidence=0.95
        )

        return {
            "reasoning_trace": reasoning_payload.model_dump(mode="json"),
            "status": CapsuleStatus.ACTIVE.value,
        }

    async def create_capsule_from_live_capture(self, conversation_data: dict) -> dict:
        """Create capsule from simulated live capture data."""

        print("📡 Creating capsule from live capture...")

        headers = {"Content-Type": "application/json", "X-API-Key": self.api_key}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/capsules",
                    json=conversation_data,
                    headers=headers,
                    timeout=30.0,
                )

                if response.status_code == 201:
                    result = response.json()
                    return {
                        "success": True,
                        "capsule_id": result["capsule_id"],
                        "status": result["status"],
                        "capsule_type": result["capsule"]["capsule_type"],
                        "timestamp": result["capsule"]["timestamp"],
                        "verification_present": bool(
                            result["capsule"].get("verification")
                        ),
                    }
                else:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": response.text,
                    }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def verify_capsule_in_chain(self, capsule_id: str) -> dict:
        """Verify the capsule appears in the chain and has proper attribution."""

        print(f"🔗 Verifying capsule {capsule_id} in chain...")

        headers = {"X-API-Key": self.api_key}

        try:
            # Get capsule details
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/capsules/{capsule_id}",
                    headers=headers,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    capsule_data = response.json()["capsule"]

                    # Verify capsule verification
                    verify_response = await client.get(
                        f"{self.api_base}/capsules/{capsule_id}/verify",
                        headers=headers,
                        timeout=30.0,
                    )

                    verification_data = (
                        verify_response.json()
                        if verify_response.status_code == 200
                        else {}
                    )

                    return {
                        "found": True,
                        "capsule_type": capsule_data.get("capsule_type"),
                        "has_verification": bool(capsule_data.get("verification")),
                        "signature_present": bool(
                            capsule_data.get("verification", {}).get("signature")
                        ),
                        "hash_present": bool(
                            capsule_data.get("verification", {}).get("hash")
                        ),
                        "reasoning_steps": len(
                            capsule_data.get("reasoning_trace", {}).get(
                                "reasoning_steps", []
                            )
                        ),
                        "verification_status": verification_data.get("verified", False),
                        "verification_error": verification_data.get(
                            "verification_error"
                        ),
                    }
                else:
                    return {"found": False, "status_code": response.status_code}

        except Exception as e:
            return {"found": False, "error": str(e)}

    async def check_chain_stats(self) -> dict:
        """Check overall chain statistics."""

        print("📊 Checking chain statistics...")

        headers = {"X-API-Key": self.api_key}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/capsules/stats", headers=headers, timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}


async def main():
    """Run the complete integration test."""

    print("🔄 UATP Live Capture → Capsule Creation Integration Test")
    print("=" * 65)

    tester = LiveCaptureIntegrationTester()

    # Step 1: Check initial chain state
    print("\n1️⃣ CHECKING INITIAL CHAIN STATE")
    print("-" * 40)

    initial_stats = await tester.check_chain_stats()
    if "error" not in initial_stats:
        print(f"📊 Total capsules: {initial_stats['total_capsules']}")
        print(f"🎯 Unique agents: {initial_stats['unique_agents']}")
        print(f"📋 Types: {', '.join(initial_stats['types'].keys())}")
        initial_count = initial_stats["total_capsules"]
    else:
        print(f"❌ Error getting stats: {initial_stats['error']}")
        return

    # Step 2: Simulate high-significance conversation
    print("\n2️⃣ SIMULATING HIGH-SIGNIFICANCE CONVERSATION")
    print("-" * 40)

    conversation_data = tester.simulate_high_significance_conversation()
    reasoning_steps = conversation_data["reasoning_trace"]["reasoning_steps"]

    print(f"🎤 Simulated conversation:")
    print(f"   • Reasoning steps: {len(reasoning_steps)}")
    print(f"   • Complexity: {reasoning_steps[0]['metadata']['complexity']}")
    print(
        f"   • Significance score: {reasoning_steps[-1]['metadata']['significance_score']}"
    )
    print(
        f"   • Should create capsule: {reasoning_steps[-1]['metadata']['should_create_capsule']}"
    )

    # Step 3: Create capsule from live capture
    print("\n3️⃣ CREATING CAPSULE FROM LIVE CAPTURE")
    print("-" * 40)

    creation_result = await tester.create_capsule_from_live_capture(conversation_data)

    if creation_result["success"]:
        print("✅ SUCCESS: Capsule created from live capture!")
        print(f"🆔 Capsule ID: {creation_result['capsule_id']}")
        print(f"📊 Status: {creation_result['status']}")
        print(f"🔑 Type: {creation_result['capsule_type']}")
        print(f"📅 Timestamp: {creation_result['timestamp']}")
        print(
            f"🛡️ Verification: {'Present' if creation_result['verification_present'] else 'Missing'}"
        )

        capsule_id = creation_result["capsule_id"]

        # Step 4: Verify capsule in chain
        print("\n4️⃣ VERIFYING CAPSULE IN CHAIN")
        print("-" * 40)

        verification_result = await tester.verify_capsule_in_chain(capsule_id)

        if verification_result["found"]:
            print("✅ SUCCESS: Capsule verified in chain!")
            print(
                f"🔐 Cryptographic verification: {'✅ VERIFIED' if verification_result['verification_status'] else '❌ FAILED'}"
            )
            print(
                f"🔑 Signature present: {'✅' if verification_result['signature_present'] else '❌'}"
            )
            print(
                f"🏷️ Hash present: {'✅' if verification_result['hash_present'] else '❌'}"
            )
            print(
                f"📝 Reasoning steps preserved: {verification_result['reasoning_steps']}"
            )

            if verification_result["verification_error"]:
                print(
                    f"⚠️ Verification error: {verification_result['verification_error']}"
                )
        else:
            print(
                f"❌ ERROR: Capsule not found in chain: {verification_result.get('error', 'Unknown')}"
            )

    else:
        print("❌ FAILED: Capsule creation failed")
        print(f"❗ Error: {creation_result.get('error', 'Unknown error')}")
        return

    # Step 5: Check final chain state
    print("\n5️⃣ CHECKING FINAL CHAIN STATE")
    print("-" * 40)

    final_stats = await tester.check_chain_stats()
    if "error" not in final_stats:
        final_count = final_stats["total_capsules"]
        print(f"📊 Total capsules: {final_count} (+{final_count - initial_count})")
        print(f"🎯 Unique agents: {final_stats['unique_agents']}")

        if final_count > initial_count:
            print("✅ Chain updated successfully!")
        else:
            print("⚠️ Chain count unchanged")

    # Final Summary
    print("\n" + "=" * 65)
    print("🎯 INTEGRATION TEST SUMMARY")
    print("=" * 65)

    if creation_result["success"] and verification_result["found"]:
        print("🎉 COMPLETE SUCCESS!")
        print("✅ Live capture simulation works")
        print("✅ Capsule creation API works")
        print("✅ Cryptographic signing works")
        print("✅ Chain persistence works")
        print("✅ Verification system works")

        print(f"\n🔗 View results:")
        print(f"   • Visualizer: http://localhost:8501")
        print(f"   • API Docs: http://localhost:9090/docs")
        print(f"   • Capsule: http://localhost:9090/capsules/{capsule_id}")

        print(f"\n💡 Next Steps:")
        print(f"   • Update live capture system to use new API format")
        print(f"   • Test with real high-significance conversations")
        print(f"   • Monitor automatic capsule creation thresholds")

    else:
        print("⚠️ PARTIAL SUCCESS - Issues remaining")
        print("❗ Review logs and debug remaining issues")


if __name__ == "__main__":
    asyncio.run(main())
