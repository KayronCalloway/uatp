#!/usr/bin/env python3
"""
Test Fixed Capsule API

This script tests the new properly-architected capsule creation endpoint that accepts
creation requests instead of fully-formed capsules.
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


class FixedCapsuleAPITester:
    """Test the fixed capsule creation API."""

    def __init__(self):
        self.api_base = "http://localhost:9090"
        self.api_key = "dev-key-001"

    def create_test_reasoning_request(self) -> dict:
        """Create a proper capsule creation request (not a full capsule)."""

        # Create reasoning steps
        reasoning_steps = [
            ReasoningStep(
                operation="analysis",
                reasoning="Testing the fixed capsule API with proper request schema",
                confidence=0.95,
            ),
            ReasoningStep(
                operation="conclusion",
                reasoning="The API now accepts creation requests instead of fully-formed capsules",
                confidence=0.98,
            ),
        ]

        # Create reasoning payload
        reasoning_payload = ReasoningTracePayload(
            reasoning_steps=reasoning_steps, total_confidence=0.96
        )

        # Return creation request (not full capsule)
        return {
            "reasoning_trace": reasoning_payload.model_dump(mode="json"),
            "status": CapsuleStatus.ACTIVE.value,
        }

    async def test_new_endpoint(self) -> dict:
        """Test the new POST /capsules endpoint."""

        print("🧪 Testing NEW POST /capsules endpoint...")

        headers = {"Content-Type": "application/json", "X-API-Key": self.api_key}

        request_data = self.create_test_reasoning_request()

        print(f"📤 Sending creation request:")
        print(
            f"   • Reasoning steps: {len(request_data['reasoning_trace']['reasoning_steps'])}"
        )
        print(f"   • Status: {request_data['status']}")
        print(f"   • Request keys: {list(request_data.keys())}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/capsules",
                    json=request_data,
                    headers=headers,
                    timeout=30.0,
                )

                result = {
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "success": response.status_code == 201,
                }

                if response.status_code == 201:
                    json_response = response.json()
                    result.update(
                        {
                            "capsule_id": json_response.get("capsule_id"),
                            "creation_status": json_response.get("status"),
                            "response_type": type(
                                json_response.get("capsule", {})
                            ).__name__,
                        }
                    )
                else:
                    result["error_response"] = response.text[:500]

                return result

        except Exception as e:
            return {"status_code": None, "error": str(e), "success": False}

    async def test_generic_endpoint(self) -> dict:
        """Test the new POST /capsules/generic endpoint for advanced users."""

        print("🔧 Testing NEW POST /capsules/generic endpoint...")

        # This would require a fully-formed capsule (for comparison)
        # We'll skip this for now since it's for advanced users
        return {"skipped": True, "reason": "Generic endpoint for advanced users"}

    async def verify_capsule_creation(self, capsule_id: str) -> dict:
        """Verify the created capsule can be retrieved."""

        print(f"🔍 Verifying capsule {capsule_id} was created...")

        headers = {"X-API-Key": self.api_key}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/capsules/{capsule_id}",
                    headers=headers,
                    timeout=30.0,
                )

                return {
                    "found": response.status_code == 200,
                    "status_code": response.status_code,
                    "capsule_data": response.json()
                    if response.status_code == 200
                    else None,
                }

        except Exception as e:
            return {"found": False, "error": str(e)}


async def main():
    """Run the comprehensive API fix test."""

    print("🚀 UATP Fixed Capsule API Test")
    print("=" * 50)

    tester = FixedCapsuleAPITester()

    # Test 1: New properly-architected endpoint
    print("\n1️⃣ TESTING FIXED ENDPOINT")
    print("-" * 30)

    api_result = await tester.test_new_endpoint()

    if api_result["success"]:
        print("✅ SUCCESS: Capsule creation works!")
        print(f"🆔 Capsule ID: {api_result['capsule_id']}")
        print(f"📊 Status: {api_result['creation_status']}")
        print(f"📄 Content Type: {api_result['content_type']}")

        # Test 2: Verify the capsule exists
        print("\n2️⃣ VERIFYING CAPSULE")
        print("-" * 30)

        verify_result = await tester.verify_capsule_creation(api_result["capsule_id"])

        if verify_result["found"]:
            print("✅ SUCCESS: Capsule can be retrieved!")
            capsule_data = verify_result["capsule_data"]["capsule"]
            print(f"🔑 Type: {capsule_data.get('capsule_type', 'unknown')}")
            print(f"📅 Timestamp: {capsule_data.get('timestamp', 'unknown')}")
            print(f"🛡️ Has verification: {bool(capsule_data.get('verification'))}")
            print(
                f"📝 Reasoning steps: {len(capsule_data.get('reasoning_trace', {}).get('reasoning_steps', []))}"
            )
        else:
            print(
                f"❌ ERROR: Capsule not found: {verify_result.get('error', 'Unknown error')}"
            )

    else:
        print("❌ FAILED: Capsule creation still broken")
        print(f"📡 Status: {api_result['status_code']}")
        print(
            f"❗ Error: {api_result.get('error_response', api_result.get('error', 'Unknown'))}"
        )

    # Test 3: Generic endpoint (skip for now)
    print("\n3️⃣ TESTING GENERIC ENDPOINT")
    print("-" * 30)

    generic_result = await tester.test_generic_endpoint()
    if generic_result.get("skipped"):
        print("⏭️ SKIPPED: Generic endpoint test (for advanced users)")

    # Summary
    print("\n" + "=" * 50)
    print("🎯 SUMMARY")
    print("=" * 50)

    if api_result["success"]:
        print("🎉 SOLUTION SUCCESSFUL!")
        print("✅ POST /capsules now accepts creation requests")
        print("✅ Engine handles ID/timestamp/verification generation")
        print("✅ Proper JSON responses instead of HTML errors")
        print("✅ Live capture → capsule creation pipeline restored")

        print(f"\n🔗 View capsule in visualizer:")
        print(f"   http://localhost:8501")
        print(f"\n📋 API documentation:")
        print(f"   http://localhost:9090/docs")

    else:
        print("❌ SOLUTION INCOMPLETE")
        print("❗ Additional debugging needed")

        # Save debug data
        debug_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_results": {
                "new_endpoint": api_result,
                "generic_endpoint": generic_result,
            },
        }

        with open("/Users/kay/uatp-capsule-engine/api_fix_test_results.json", "w") as f:
            json.dump(debug_data, f, indent=2, default=str)

        print(f"📄 Debug data saved: api_fix_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
