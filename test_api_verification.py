#!/usr/bin/env python3
"""
Simplified UATP Capsule Verification Test via API

This script tests the UATP verification system by creating capsules via API
and verifying they show as "Verified" in both the API and frontend.
"""

import asyncio
import aiohttp
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class APIVerificationTest:
    """Test UATP verification via API endpoints."""

    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_api_key = "test-write-key"  # From .env
        self.created_capsules = []

    def create_comprehensive_reasoning_capsule_data(self) -> Dict[str, Any]:
        """Create comprehensive reasoning capsule data for API submission."""
        capsule_id = (
            f"caps_{datetime.now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"
        )

        return {
            "capsule_id": capsule_id,
            "version": "7.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "capsule_type": "reasoning_trace",
            "status": "active",
            "verification": {
                "signer": None,
                "verify_key": None,
                "hash": None,
                "signature": "ed25519:" + "0" * 128,
                "pq_signature": None,
                "merkle_root": "sha256:" + "0" * 64,
            },
            "reasoning_trace": {
                "reasoning_steps": [
                    {
                        "step_id": 1,
                        "operation": "observation",
                        "reasoning": "Analyzing comprehensive UATP verification system testing requirements",
                        "confidence": 0.95,
                        "metadata": {
                            "input_source": "verification_test",
                            "complexity_level": "high",
                            "domain": "system_testing",
                        },
                        "attribution_sources": [
                            "test_specification",
                            "verification_protocols",
                        ],
                    },
                    {
                        "step_id": 2,
                        "operation": "analysis",
                        "reasoning": "Breaking down verification requirements: API functionality, cryptographic integrity, frontend compatibility, and security validation",
                        "confidence": 0.90,
                        "parent_step_id": 1,
                        "metadata": {
                            "analysis_type": "requirement_analysis",
                            "verification_aspects": [
                                "api",
                                "crypto",
                                "frontend",
                                "security",
                            ],
                            "test_phase": "comprehensive",
                        },
                        "attribution_sources": [
                            "api_documentation",
                            "security_specifications",
                        ],
                    },
                    {
                        "step_id": 3,
                        "operation": "reasoning",
                        "reasoning": "Determining optimal test structure to validate all UATP 7.0 capabilities including multi-agent reasoning, economic attribution, and metadata preservation",
                        "confidence": 0.88,
                        "parent_step_id": 2,
                        "metadata": {
                            "reasoning_type": "test_design",
                            "features_tested": [
                                "reasoning",
                                "economics",
                                "metadata",
                                "verification",
                            ],
                            "uatp_version": "7.0",
                        },
                        "attribution_sources": [
                            "uatp_7_specification",
                            "testing_best_practices",
                        ],
                    },
                    {
                        "step_id": 4,
                        "operation": "conclusion",
                        "reasoning": "Comprehensive verification test should demonstrate: complex reasoning chains, proper economic attribution, rich metadata handling, cryptographic verification, and frontend display compatibility",
                        "confidence": 0.92,
                        "parent_step_id": [2, 3],
                        "metadata": {
                            "conclusion_type": "test_specification",
                            "validation_criteria": [
                                "completeness",
                                "correctness",
                                "compatibility",
                                "security",
                            ],
                            "expected_result": "verified_status",
                        },
                        "attribution_sources": [
                            "comprehensive_analysis",
                            "verification_requirements",
                        ],
                    },
                ],
                "total_confidence": 0.91,
            },
        }

    def create_economic_transaction_capsule_data(self) -> Dict[str, Any]:
        """Create economic transaction capsule data for API submission."""
        capsule_id = (
            f"caps_{datetime.now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"
        )

        return {
            "capsule_id": capsule_id,
            "version": "7.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "capsule_type": "economic_transaction",
            "status": "active",
            "verification": {
                "signer": None,
                "verify_key": None,
                "hash": None,
                "signature": "ed25519:" + "0" * 128,
                "pq_signature": None,
                "merkle_root": "sha256:" + "0" * 64,
            },
            "economic_transaction": {
                "transaction_type": "attribution_payment",
                "amount": 247.50,
                "currency": "UATP",
                "sender": "test-agent",
                "recipient": "verification-attribution-pool",
                "attribution_basis": {
                    "confidence_score": 0.89,
                    "temporal_decay": 0.96,
                    "attribution_sources": [
                        "reasoning_trace_verification",
                        "economic_modeling_analysis",
                        "attribution_calculation_engine",
                    ],
                },
            },
        }

    async def test_api_server_status(self) -> bool:
        """Test if the API server is running and accessible."""
        logger.info("Testing API server accessibility...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/health") as response:
                    if response.status == 200:
                        logger.info("✓ API server is accessible")
                        return True
                    else:
                        logger.error(f"✗ API server returned status {response.status}")
                        return False
        except Exception as e:
            logger.error(f"✗ Could not connect to API server: {e}")
            return False

    async def create_capsules_via_api(self) -> bool:
        """Create test capsules via API endpoints."""
        logger.info("Creating capsules via API...")

        headers = {"X-API-Key": self.test_api_key, "Content-Type": "application/json"}

        capsules_to_create = [
            self.create_comprehensive_reasoning_capsule_data(),
            self.create_economic_transaction_capsule_data(),
        ]

        try:
            async with aiohttp.ClientSession() as session:
                for capsule_data in capsules_to_create:
                    async with session.post(
                        f"{self.api_base_url}/capsules",
                        headers=headers,
                        json=capsule_data,
                    ) as response:
                        if response.status == 201:
                            response_data = await response.json()
                            capsule_id = response_data["capsule_id"]
                            self.created_capsules.append(capsule_id)
                            logger.info(f"✓ Created capsule: {capsule_id}")
                        else:
                            error_text = await response.text()
                            logger.error(
                                f"✗ Failed to create capsule. Status: {response.status}, Error: {error_text}"
                            )
                            return False

            logger.info(f"Successfully created {len(self.created_capsules)} capsules")
            return True

        except Exception as e:
            logger.error(f"Capsule creation failed: {e}")
            return False

    async def test_verification_endpoints(self) -> bool:
        """Test verification endpoints for all created capsules."""
        logger.info("Testing verification endpoints...")

        headers = {"X-API-Key": self.test_api_key, "Content-Type": "application/json"}

        try:
            async with aiohttp.ClientSession() as session:
                all_verified = True

                for capsule_id in self.created_capsules:
                    # Test verification endpoint
                    async with session.get(
                        f"{self.api_base_url}/capsules/{capsule_id}/verify",
                        headers=headers,
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("verified") is True:
                                logger.info(f"✓ Capsule {capsule_id} shows as VERIFIED")
                            else:
                                logger.error(
                                    f"✗ Capsule {capsule_id} not verified: {data.get('verification_error')}"
                                )
                                all_verified = False
                        else:
                            logger.error(
                                f"✗ Verification endpoint failed for {capsule_id}: {response.status}"
                            )
                            all_verified = False

                return all_verified

        except Exception as e:
            logger.error(f"Verification testing failed: {e}")
            return False

    async def test_capsule_retrieval(self) -> bool:
        """Test capsule retrieval endpoints."""
        logger.info("Testing capsule retrieval...")

        headers = {"X-API-Key": self.test_api_key, "Content-Type": "application/json"}

        try:
            async with aiohttp.ClientSession() as session:
                all_retrieved = True

                for capsule_id in self.created_capsules:
                    # Test get capsule endpoint with raw data
                    async with session.get(
                        f"{self.api_base_url}/capsules/{capsule_id}?include_raw=true",
                        headers=headers,
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            capsule_data = data["capsule"]

                            # Validate required fields
                            required_fields = [
                                "capsule_id",
                                "timestamp",
                                "capsule_type",
                                "status",
                                "verification",
                            ]
                            missing_fields = [
                                field
                                for field in required_fields
                                if field not in capsule_data
                            ]

                            if missing_fields:
                                logger.error(
                                    f"✗ Missing fields in {capsule_id}: {missing_fields}"
                                )
                                all_retrieved = False
                            else:
                                logger.info(
                                    f"✓ Capsule {capsule_id} retrieved with complete data structure"
                                )

                                # Check verification data
                                verification = capsule_data.get("verification", {})
                                if verification.get("signature") and verification.get(
                                    "verify_key"
                                ):
                                    logger.info(
                                        f"✓ Capsule {capsule_id} has valid cryptographic data"
                                    )
                                else:
                                    logger.warning(
                                        f"⚠ Capsule {capsule_id} missing cryptographic verification data"
                                    )

                        else:
                            logger.error(
                                f"✗ Failed to retrieve capsule {capsule_id}: {response.status}"
                            )
                            all_retrieved = False

                return all_retrieved

        except Exception as e:
            logger.error(f"Capsule retrieval testing failed: {e}")
            return False

    async def test_frontend_compatibility(self) -> bool:
        """Test frontend compatibility by checking data structures."""
        logger.info("Testing frontend compatibility...")

        headers = {
            "X-API-Key": self.test_api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                # Test list endpoint for frontend
                async with session.get(
                    f"{self.api_base_url}/capsules?per_page=20", headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "capsules" in data and len(data["capsules"]) > 0:
                            logger.info(
                                "✓ List endpoint returns capsules in frontend-compatible format"
                            )

                            # Check if our created capsules are in the list
                            found_capsules = []
                            for capsule in data["capsules"]:
                                if capsule.get("capsule_id") in self.created_capsules:
                                    found_capsules.append(capsule["capsule_id"])

                            if len(found_capsules) == len(self.created_capsules):
                                logger.info(
                                    "✓ All created capsules are visible in list endpoint"
                                )
                                return True
                            else:
                                logger.warning(
                                    f"⚠ Only {len(found_capsules)}/{len(self.created_capsules)} capsules found in list"
                                )
                                return False
                        else:
                            logger.error("✗ List endpoint returned no capsules")
                            return False
                    else:
                        logger.error(f"✗ List endpoint failed: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Frontend compatibility testing failed: {e}")
            return False

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run the complete verification test suite."""
        logger.info("Starting comprehensive API verification test...")

        test_results = {
            "api_server_accessible": False,
            "capsule_creation": False,
            "verification_endpoints": False,
            "capsule_retrieval": False,
            "frontend_compatibility": False,
            "created_capsules": self.created_capsules,
        }

        # Test API server
        test_results["api_server_accessible"] = await self.test_api_server_status()

        if test_results["api_server_accessible"]:
            # Create capsules
            test_results["capsule_creation"] = await self.create_capsules_via_api()

            if test_results["capsule_creation"]:
                # Test verification
                test_results[
                    "verification_endpoints"
                ] = await self.test_verification_endpoints()

                # Test retrieval
                test_results["capsule_retrieval"] = await self.test_capsule_retrieval()

                # Test frontend compatibility
                test_results[
                    "frontend_compatibility"
                ] = await self.test_frontend_compatibility()

        # Generate report
        passed_tests = sum(
            1 for result in test_results.values() if isinstance(result, bool) and result
        )
        total_tests = sum(
            1 for result in test_results.values() if isinstance(result, bool)
        )

        report = {
            "summary": {
                "passed": passed_tests,
                "total": total_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.1f}%"
                if total_tests > 0
                else "0%",
                "overall_status": "PASSED" if passed_tests == total_tests else "FAILED",
            },
            "detailed_results": test_results,
            "created_capsules": self.created_capsules,
        }

        return report


async def main():
    """Main test execution."""
    print("🔍 UATP Capsule API Verification Test")
    print("=" * 50)

    test_runner = APIVerificationTest()

    try:
        report = await test_runner.run_comprehensive_test()

        # Display results
        print("\n📊 TEST RESULTS")
        print("-" * 30)
        print(f"Overall Status: {report['summary']['overall_status']}")
        print(
            f"Tests Passed: {report['summary']['passed']}/{report['summary']['total']}"
        )
        print(f"Success Rate: {report['summary']['success_rate']}")

        print("\n📋 DETAILED RESULTS")
        print("-" * 30)
        for test_name, result in report["detailed_results"].items():
            if isinstance(result, bool):
                status = "✓ PASS" if result else "✗ FAIL"
                print(f"{test_name}: {status}")
            elif test_name == "created_capsules":
                print(f"Created Capsules: {len(result)} capsules")
                for capsule_id in result:
                    print(f"  - {capsule_id}")

        # Frontend access instructions
        if report["summary"]["overall_status"] == "PASSED":
            print("\n🌐 FRONTEND ACCESS")
            print("-" * 30)
            print("Your VERIFIED capsules should now be visible at:")
            print(f"👉 {test_runner.frontend_url}")
            print("\nLook for capsules with 'Verified' status in the visualizer.")
            print("The capsules should display:")
            print("  • Complex multi-step reasoning")
            print("  • Economic transaction details")
            print("  • Rich metadata")
            print("  • Cryptographic verification badges")
        else:
            print("\n❌ ISSUES DETECTED")
            print("-" * 30)
            print("Please ensure:")
            print("  • API server is running on http://localhost:8000")
            print("  • Database is properly initialized")
            print("  • Environment variables are configured")
            print("  • API keys are valid")

        # Save report
        with open("api_verification_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved: api_verification_report.json")

        return report["summary"]["overall_status"] == "PASSED"

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\n❌ Test execution failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
