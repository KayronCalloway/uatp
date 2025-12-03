#!/usr/bin/env python3
"""
Debug Script: UATP Capsule API Validation Issue

This script diagnoses why POST /capsules is returning 400 HTML errors instead of 
creating capsules. It tests the validation pipeline step by step.
"""

import asyncio
import json
import httpx
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any

# Add src to path
sys.path.insert(0, "/Users/kay/uatp-capsule-engine/src")

from capsule_schema import (
    ReasoningTraceCapsule,
    ReasoningTracePayload,
    ReasoningStep,
    Verification,
    CapsuleStatus,
    CapsuleType,
    AnyCapsule,
)
from pydantic import ValidationError


class CapsuleValidationDebugger:
    """Debug the capsule validation pipeline."""

    def __init__(self):
        self.api_base = "http://localhost:9090"
        self.api_key = "dev-key-001"

    def create_minimal_valid_capsule(self) -> Dict[str, Any]:
        """Create the most minimal valid capsule matching existing format."""

        import uuid

        now = datetime.now(timezone.utc)
        capsule_id = (
            f"caps_{now.year}_{now.month:02d}_{now.day:02d}_{uuid.uuid4().hex[:16]}"
        )

        # Create minimal reasoning step
        reasoning_step = ReasoningStep(
            operation="debug_test",
            reasoning="Testing API validation pipeline",
            confidence=1.0,
        )

        # Create minimal reasoning payload
        reasoning_payload = ReasoningTracePayload(
            reasoning_steps=[reasoning_step], total_confidence=1.0
        )

        # Create minimal verification (matching defaults)
        verification = Verification(
            signer=None,
            verify_key=None,
            hash=None,
            signature="ed25519:" + "0" * 128,
            merkle_root="sha256:" + "0" * 64,
        )

        # Create the capsule
        capsule = ReasoningTraceCapsule(
            capsule_id=capsule_id,
            version="7.0",
            timestamp=now,
            capsule_type=CapsuleType.REASONING_TRACE,
            status=CapsuleStatus.ACTIVE,
            verification=verification,
            reasoning_trace=reasoning_payload,
        )

        # Convert to dict with proper serialization
        return capsule.model_dump(mode="json")

    def test_pydantic_validation_locally(self, capsule_data: Dict[str, Any]) -> bool:
        """Test if capsule data validates against AnyCapsule schema locally."""

        print("🔍 Testing Pydantic validation locally...")

        try:
            from pydantic import TypeAdapter

            adapter = TypeAdapter(AnyCapsule)
            validated_capsule = adapter.validate_python(capsule_data)
            print(f"✅ Local validation PASSED: {type(validated_capsule).__name__}")
            return True
        except ValidationError as e:
            print(f"❌ Local validation FAILED:")
            for error in e.errors():
                print(f"   • {error['loc']}: {error['msg']}")
            return False
        except Exception as e:
            print(f"❌ Local validation ERROR: {e}")
            return False

    async def test_api_validation(self, capsule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test the API validation by calling POST /capsules."""

        print("🌐 Testing API validation...")

        headers = {"Content-Type": "application/json", "X-API-Key": self.api_key}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/capsules",
                    json=capsule_data,
                    headers=headers,
                    timeout=30.0,
                )

                result = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content_type": response.headers.get("content-type", ""),
                    "raw_content": response.text[:1000],  # First 1000 chars
                }

                # Try to parse as JSON
                try:
                    result["json_response"] = response.json()
                except:
                    result["json_response"] = None

                return result

        except Exception as e:
            return {
                "status_code": None,
                "error": str(e),
                "raw_content": f"Connection error: {e}",
            }

    async def test_get_endpoint(self) -> Dict[str, Any]:
        """Test if GET /capsules works to verify API is running."""

        print("🔌 Testing GET /capsules endpoint...")

        headers = {"X-API-Key": self.api_key}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/capsules", headers=headers, timeout=30.0
                )

                result = {
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "works": response.status_code == 200,
                }

                if response.status_code == 200:
                    try:
                        json_data = response.json()
                        result["total_capsules"] = len(json_data.get("capsules", []))
                    except:
                        result["total_capsules"] = None

                return result

        except Exception as e:
            return {"status_code": None, "error": str(e), "works": False}

    def analyze_existing_capsules(self) -> Dict[str, Any]:
        """Analyze existing capsules in the chain for format comparison."""

        print("📊 Analyzing existing capsule formats...")

        try:
            chain_file = "/Users/kay/uatp-capsule-engine/capsule_chain.jsonl"

            if not os.path.exists(chain_file):
                return {"error": "Chain file not found"}

            with open(chain_file, "r") as f:
                lines = f.readlines()

            if not lines:
                return {"error": "No capsules in chain"}

            # Parse first few capsules
            capsules = []
            for line in lines[:3]:
                if line.strip():
                    try:
                        capsule = json.loads(line)
                        capsules.append(capsule)
                    except:
                        pass

            if not capsules:
                return {"error": "Could not parse capsules"}

            # Analyze structure
            first_capsule = capsules[0]
            analysis = {
                "total_capsules": len(lines),
                "sample_structure": {
                    "keys": list(first_capsule.keys()),
                    "capsule_id_format": first_capsule.get("capsule_id", ""),
                    "has_version": "version" in first_capsule,
                    "has_timestamp": "timestamp" in first_capsule,
                    "has_verification": "verification" in first_capsule,
                    "status": first_capsule.get("status", ""),
                    "type": first_capsule.get("type", ""),
                },
            }

            return analysis

        except Exception as e:
            return {"error": str(e)}


async def main():
    """Run the debugging analysis."""

    print("🔧 UATP Capsule API Validation Debugger")
    print("=" * 60)

    debugger = CapsuleValidationDebugger()

    # Step 1: Test if API is running
    print("\n1️⃣ TESTING API CONNECTIVITY")
    print("-" * 40)

    get_result = await debugger.test_get_endpoint()
    if get_result["works"]:
        print(f"✅ GET /capsules works (Status: {get_result['status_code']})")
        print(f"📊 Total capsules: {get_result.get('total_capsules', 'unknown')}")
    else:
        print(f"❌ GET /capsules failed: {get_result.get('error', 'Unknown error')}")
        return

    # Step 2: Analyze existing capsule format
    print("\n2️⃣ ANALYZING EXISTING CAPSULE FORMAT")
    print("-" * 40)

    existing_analysis = debugger.analyze_existing_capsules()
    if "error" in existing_analysis:
        print(f"❌ Could not analyze existing capsules: {existing_analysis['error']}")
    else:
        print(f"📊 Found {existing_analysis['total_capsules']} existing capsules")
        structure = existing_analysis["sample_structure"]
        print(f"🏗️ Keys: {', '.join(structure['keys'])}")
        print(f"🆔 ID Format: {structure['capsule_id_format']}")
        print(f"📅 Has version: {structure['has_version']}")
        print(f"🔒 Has verification: {structure['has_verification']}")

    # Step 3: Create minimal valid capsule
    print("\n3️⃣ CREATING MINIMAL VALID CAPSULE")
    print("-" * 40)

    capsule_data = debugger.create_minimal_valid_capsule()
    print(f"🆔 Capsule ID: {capsule_data['capsule_id']}")
    print(f"📝 Type: {capsule_data['capsule_type']}")
    print(f"⏱️ Timestamp: {capsule_data['timestamp']}")
    print(f"🔑 Top-level keys: {', '.join(capsule_data.keys())}")

    # Step 4: Test local Pydantic validation
    print("\n4️⃣ TESTING LOCAL PYDANTIC VALIDATION")
    print("-" * 40)

    local_valid = debugger.test_pydantic_validation_locally(capsule_data)

    if not local_valid:
        print("❌ Data fails local validation - fixing required before API test")
        return

    # Step 5: Test API validation
    print("\n5️⃣ TESTING API VALIDATION")
    print("-" * 40)

    api_result = await debugger.test_api_validation(capsule_data)

    print(f"📡 Status Code: {api_result.get('status_code', 'None')}")
    print(f"📄 Content Type: {api_result.get('content_type', 'None')}")

    if api_result["status_code"] == 201:
        print("✅ API validation PASSED - Capsule created!")
        if api_result["json_response"]:
            print(
                f"🎯 Created: {api_result['json_response'].get('capsule_id', 'unknown')}"
            )
    elif api_result["status_code"] == 400:
        print("❌ API validation FAILED with 400 error")

        if api_result["json_response"]:
            print(f"🔍 Error: {api_result['json_response']}")
        else:
            print("🔍 Raw response (HTML?):")
            print(
                api_result["raw_content"][:500] + "..."
                if len(api_result["raw_content"]) > 500
                else api_result["raw_content"]
            )
    else:
        print(f"❌ Unexpected API response: {api_result['status_code']}")
        print(f"🔍 Response: {api_result['raw_content'][:200]}...")

    # Step 6: Summary and recommendations
    print("\n6️⃣ SUMMARY & RECOMMENDATIONS")
    print("-" * 40)

    if local_valid and api_result["status_code"] == 201:
        print("🎉 SUCCESS: Capsule validation pipeline works correctly!")
    elif local_valid and api_result["status_code"] == 400:
        print("🔍 ISSUE: Local validation passes but API validation fails")
        print("   Possible causes:")
        print("   • Middleware validation differs from schema validation")
        print("   • Missing required fields in API context")
        print("   • Agent ID or authentication issues")
        print("   • Server-side validation errors")
        print("   • Quart schema validation configuration issues")
    else:
        print("❌ MULTIPLE ISSUES: Both local and API validation have problems")

    print(f"\n📋 Debug data saved for analysis")

    # Save debug results
    debug_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_connectivity": get_result,
        "existing_capsules": existing_analysis,
        "test_capsule": capsule_data,
        "local_validation": local_valid,
        "api_validation": api_result,
    }

    with open("/Users/kay/uatp-capsule-engine/debug_validation_results.json", "w") as f:
        json.dump(debug_data, f, indent=2, default=str)

    return debug_data


if __name__ == "__main__":
    asyncio.run(main())
