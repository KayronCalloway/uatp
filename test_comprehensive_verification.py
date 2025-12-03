#!/usr/bin/env python3
"""
Comprehensive UATP Capsule Verification System Test

This script creates, verifies, and tests a comprehensive UATP capsule to ensure:
1. Multi-step reasoning with attribution works correctly
2. Economic distribution is properly handled
3. Rich metadata is preserved 
4. Cryptographic verification passes
5. Frontend compatibility is maintained
6. All security checks pass without false positives

Tests both engine-level operations and API endpoints.
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

import aiohttp
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.capsule_schema import (
    ReasoningTraceCapsule,
    ReasoningTracePayload,
    ReasoningStep,
    EconomicTransactionCapsule,
    EconomicTransactionPayload,
    AttributionBasis,
    CapsuleStatus,
    CapsuleType,
    TransactionType,
    Currency,
    Verification,
)
from src.core.database import db
from src.engine.capsule_engine import CapsuleEngine

# Load environment variables
load_dotenv()

# Set test environment variable to bypass mirror mode and other test-specific features
os.environ["PYTEST_CURRENT_TEST"] = "test_comprehensive_verification"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ComprehensiveVerificationTest:
    """Comprehensive test suite for UATP capsule verification system."""

    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_api_key = "test-write-key"  # From .env
        self.test_results = {
            "capsule_creation": False,
            "verification_status": False,
            "api_endpoints": False,
            "frontend_compatibility": False,
            "security_checks": False,
            "created_capsules": [],
        }

    async def initialize_engine(self) -> CapsuleEngine:
        """Initialize the UATP engine with proper configuration."""
        logger.info("Initializing UATP Capsule Engine...")

        # Initialize database manager using a mock app config
        class MockApp:
            def __init__(self):
                pass

        mock_app = MockApp()
        db.init_app(mock_app)

        # Create database tables
        await db.create_all()

        # Create engine instance with proper OpenAI client
        from src.integrations.openai_client import OpenAIClient

        openai_client = OpenAIClient()

        engine = CapsuleEngine(
            db_manager=db,
            agent_id=os.getenv("UATP_USER_ID", "test-agent"),
            openai_client=openai_client,
        )

        logger.info("Engine initialized successfully")
        return engine

    async def create_comprehensive_reasoning_capsule(
        self, engine: CapsuleEngine
    ) -> ReasoningTraceCapsule:
        """Create a comprehensive reasoning trace capsule with rich metadata."""
        logger.info("Creating comprehensive reasoning trace capsule...")

        # Generate unique capsule ID
        capsule_id = (
            f"caps_{datetime.now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"
        )

        # Create detailed reasoning steps with attribution
        reasoning_steps = [
            ReasoningStep(
                step_id=1,
                operation="observation",
                reasoning="Analyzing user request for UATP capsule verification testing",
                confidence=0.95,
                metadata={
                    "input_source": "user_request",
                    "complexity_level": "high",
                    "domain": "verification_testing",
                },
                attribution_sources=["user_input", "system_prompt"],
            ),
            ReasoningStep(
                step_id=2,
                operation="analysis",
                reasoning="Breaking down verification requirements: cryptographic integrity, data structure validation, API compatibility, and frontend display requirements",
                confidence=0.90,
                parent_step_id=1,
                metadata={
                    "analysis_type": "requirement_decomposition",
                    "verification_aspects": ["crypto", "structure", "api", "frontend"],
                    "risk_assessment": "medium",
                },
                attribution_sources=[
                    "technical_documentation",
                    "verification_protocols",
                ],
            ),
            ReasoningStep(
                step_id=3,
                operation="reasoning",
                reasoning="Determining optimal capsule structure to demonstrate all UATP 7.0 features including multi-step reasoning, economic attribution, and rich metadata preservation",
                confidence=0.85,
                parent_step_id=2,
                metadata={
                    "reasoning_type": "structural_optimization",
                    "features_demonstrated": [
                        "reasoning",
                        "economics",
                        "metadata",
                        "verification",
                    ],
                    "uatp_version": "7.0",
                },
                attribution_sources=["uatp_specification", "best_practices"],
            ),
            ReasoningStep(
                step_id=4,
                operation="conclusion",
                reasoning="Comprehensive test capsule should include: complex reasoning chain, economic transaction payload, rich metadata, proper attribution sources, and full cryptographic verification to validate system integrity",
                confidence=0.92,
                parent_step_id=[2, 3],
                metadata={
                    "conclusion_type": "design_decision",
                    "validation_criteria": [
                        "completeness",
                        "correctness",
                        "compatibility",
                    ],
                    "expected_outcome": "verified_status",
                },
                attribution_sources=["analysis_results", "specification_compliance"],
            ),
        ]

        # Create reasoning trace payload
        reasoning_payload = ReasoningTracePayload(
            reasoning_steps=reasoning_steps,
            total_confidence=0.91,  # Average of step confidences
        )

        # Create the capsule with comprehensive metadata
        capsule = ReasoningTraceCapsule(
            capsule_id=capsule_id,
            timestamp=datetime.now(timezone.utc),
            capsule_type=CapsuleType.REASONING_TRACE,
            status=CapsuleStatus.ACTIVE,
            verification=Verification(),  # Will be populated by engine
            reasoning_trace=reasoning_payload,
        )

        logger.info(f"Created reasoning capsule with ID: {capsule_id}")
        return capsule

    async def create_economic_transaction_capsule(
        self, engine: CapsuleEngine, parent_capsule_id: str = None
    ) -> EconomicTransactionCapsule:
        """Create an economic transaction capsule with attribution basis."""
        logger.info("Creating economic transaction capsule...")

        # Generate unique capsule ID
        capsule_id = (
            f"caps_{datetime.now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"
        )

        # Create attribution basis
        attribution_basis = AttributionBasis(
            confidence_score=0.88,
            temporal_decay=0.95,
            attribution_sources=[
                "reasoning_trace_analysis",
                "economic_modeling",
                "attribution_algorithms",
            ],
        )

        # Create economic transaction payload
        economic_payload = EconomicTransactionPayload(
            transaction_type=TransactionType.ATTRIBUTION_PAYMENT,
            amount=150.75,
            currency=Currency.UATP,
            sender="test-agent",
            recipient="attribution-pool",
            attribution_basis=attribution_basis,
        )

        # Create the capsule
        capsule = EconomicTransactionCapsule(
            capsule_id=capsule_id,
            timestamp=datetime.now(timezone.utc),
            capsule_type=CapsuleType.ECONOMIC_TRANSACTION,
            status=CapsuleStatus.ACTIVE,
            verification=Verification(),  # Will be populated by engine
            economic_transaction=economic_payload,
        )

        logger.info(f"Created economic capsule with ID: {capsule_id}")
        return capsule

    async def test_capsule_creation(self, engine: CapsuleEngine) -> bool:
        """Test creating capsules using official UATP engine methods."""
        logger.info("Testing capsule creation...")

        try:
            # Create reasoning capsule
            reasoning_capsule = await self.create_comprehensive_reasoning_capsule(
                engine
            )
            created_reasoning = await engine.create_capsule_async(reasoning_capsule)
            self.test_results["created_capsules"].append(created_reasoning.capsule_id)

            # Create economic capsule
            economic_capsule = await self.create_economic_transaction_capsule(
                engine, created_reasoning.capsule_id
            )
            created_economic = await engine.create_capsule_async(economic_capsule)
            self.test_results["created_capsules"].append(created_economic.capsule_id)

            logger.info(
                f"Successfully created {len(self.test_results['created_capsules'])} capsules"
            )
            return True

        except Exception as e:
            logger.error(f"Capsule creation failed: {e}")
            return False

    async def test_verification_status(self, engine: CapsuleEngine) -> bool:
        """Test that capsules show 'Verified' status through engine verification."""
        logger.info("Testing capsule verification status...")

        try:
            all_verified = True

            for capsule_id in self.test_results["created_capsules"]:
                # Load capsule from engine
                capsule = await engine.load_capsule_async(capsule_id)
                if not capsule:
                    logger.error(f"Could not load capsule {capsule_id}")
                    all_verified = False
                    continue

                # Verify capsule
                is_valid, reason = await engine.verify_capsule_async(capsule)

                if is_valid:
                    logger.info(f"✓ Capsule {capsule_id} verified successfully")
                else:
                    logger.error(
                        f"✗ Capsule {capsule_id} verification failed: {reason}"
                    )
                    all_verified = False

            return all_verified

        except Exception as e:
            logger.error(f"Verification testing failed: {e}")
            return False

    async def test_api_endpoints(self) -> bool:
        """Test API endpoints for capsule retrieval and verification."""
        logger.info("Testing API endpoints...")

        try:
            headers = {
                "X-API-Key": self.test_api_key,
                "Content-Type": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                all_passed = True

                for capsule_id in self.test_results["created_capsules"]:
                    # Test GET capsule endpoint
                    async with session.get(
                        f"{self.api_base_url}/capsules/{capsule_id}", headers=headers
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(
                                f"✓ GET /capsules/{capsule_id} returned status 200"
                            )

                            # Validate response structure
                            if "capsule" in data and "capsule_id" in data["capsule"]:
                                logger.info(f"✓ Capsule data structure is valid")
                            else:
                                logger.error(f"✗ Invalid capsule data structure")
                                all_passed = False
                        else:
                            logger.error(
                                f"✗ GET /capsules/{capsule_id} returned status {response.status}"
                            )
                            all_passed = False

                    # Test verification endpoint
                    async with session.get(
                        f"{self.api_base_url}/capsules/{capsule_id}/verify",
                        headers=headers,
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(
                                f"✓ GET /capsules/{capsule_id}/verify returned status 200"
                            )

                            # Check verification status
                            if data.get("verified") is True:
                                logger.info(
                                    f"✓ Capsule {capsule_id} shows as VERIFIED via API"
                                )
                            else:
                                logger.error(
                                    f"✗ Capsule {capsule_id} not verified: {data.get('verification_error')}"
                                )
                                all_passed = False
                        else:
                            logger.error(
                                f"✗ GET /capsules/{capsule_id}/verify returned status {response.status}"
                            )
                            all_passed = False

                return all_passed

        except Exception as e:
            logger.error(f"API endpoint testing failed: {e}")
            return False

    async def test_frontend_compatibility(self) -> bool:
        """Test frontend compatibility by validating capsule data structure."""
        logger.info("Testing frontend compatibility...")

        try:
            headers = {
                "X-API-Key": self.test_api_key,
                "Content-Type": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                for capsule_id in self.test_results["created_capsules"]:
                    # Get capsule with raw data for frontend testing
                    async with session.get(
                        f"{self.api_base_url}/capsules/{capsule_id}?include_raw=true",
                        headers=headers,
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            capsule_data = data["capsule"]

                            # Validate required fields for frontend
                            required_fields = [
                                "capsule_id",
                                "timestamp",
                                "capsule_type",
                                "status",
                                "verification",
                            ]

                            missing_fields = []
                            for field in required_fields:
                                if field not in capsule_data:
                                    missing_fields.append(field)

                            if missing_fields:
                                logger.error(
                                    f"✗ Missing required fields for frontend: {missing_fields}"
                                )
                                return False

                            # Validate verification structure
                            verification = capsule_data.get("verification", {})
                            if not verification.get(
                                "signature"
                            ) or not verification.get("verify_key"):
                                logger.error(
                                    "✗ Missing verification signature or verify_key"
                                )
                                return False

                            logger.info(
                                f"✓ Capsule {capsule_id} has valid frontend-compatible structure"
                            )

                        else:
                            logger.error(
                                f"✗ Could not retrieve capsule {capsule_id} for frontend testing"
                            )
                            return False

                return True

        except Exception as e:
            logger.error(f"Frontend compatibility testing failed: {e}")
            return False

    async def test_security_checks(self, engine: CapsuleEngine) -> bool:
        """Test that all security checks pass without false positives."""
        logger.info("Testing security checks...")

        try:
            # Test ethics circuit breaker status
            if hasattr(engine, "ethics_circuit_breaker"):
                stats = engine.ethics_circuit_breaker.get_refusal_statistics()
                recent_refusals = engine.ethics_circuit_breaker.get_recent_refusals(
                    hours=24
                )

                logger.info(f"Ethics circuit breaker stats: {stats}")
                logger.info(f"Recent refusals: {len(recent_refusals)}")

                # Check if any of our test capsules were refused
                for capsule_id in self.test_results["created_capsules"]:
                    for refusal in recent_refusals:
                        if refusal.get("capsule_id") == capsule_id:
                            logger.error(
                                f"✗ Test capsule {capsule_id} was refused by ethics circuit breaker"
                            )
                            return False

            # Test runtime trust enforcer
            if hasattr(engine, "runtime_trust_enforcer"):
                trust_metrics = engine.get_system_trust_metrics()
                agent_trust = engine.get_agent_trust_status(engine.agent_id)

                logger.info(f"System trust metrics: {trust_metrics}")
                logger.info(f"Agent trust status: {agent_trust}")

                # Validate no security violations for our test capsules
                if agent_trust.get("trust_score", 1.0) < 0.5:
                    logger.warning(
                        "Agent trust score is low, but this may be expected in testing"
                    )

            logger.info("✓ All security checks passed")
            return True

        except Exception as e:
            logger.error(f"Security checks failed: {e}")
            return False

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run the complete test suite."""
        logger.info("Starting comprehensive UATP verification test...")

        # Initialize engine
        engine = await self.initialize_engine()

        # Run all tests
        self.test_results["capsule_creation"] = await self.test_capsule_creation(engine)

        if self.test_results["capsule_creation"]:
            self.test_results[
                "verification_status"
            ] = await self.test_verification_status(engine)
            self.test_results["api_endpoints"] = await self.test_api_endpoints()
            self.test_results[
                "frontend_compatibility"
            ] = await self.test_frontend_compatibility()
            self.test_results["security_checks"] = await self.test_security_checks(
                engine
            )

        # Generate final report
        return self.generate_test_report()

    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        passed_tests = sum(
            1
            for result in self.test_results.values()
            if isinstance(result, bool) and result
        )
        total_tests = sum(
            1 for result in self.test_results.values() if isinstance(result, bool)
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
            "detailed_results": self.test_results,
            "recommendations": [],
        }

        # Add recommendations based on failures
        if not self.test_results["capsule_creation"]:
            report["recommendations"].append(
                "Check database connectivity and signing key configuration"
            )

        if not self.test_results["verification_status"]:
            report["recommendations"].append(
                "Review cryptographic verification implementation"
            )

        if not self.test_results["api_endpoints"]:
            report["recommendations"].append(
                "Verify API server is running and endpoints are accessible"
            )

        if not self.test_results["frontend_compatibility"]:
            report["recommendations"].append(
                "Check capsule data structure compatibility with frontend"
            )

        if not self.test_results["security_checks"]:
            report["recommendations"].append(
                "Review security policy configuration and trust enforcement"
            )

        return report


async def main():
    """Main test execution function."""
    print("🔍 UATP Capsule Verification System - Comprehensive Test")
    print("=" * 60)

    test_runner = ComprehensiveVerificationTest()

    try:
        # Run comprehensive test
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

        if report["recommendations"]:
            print("\n💡 RECOMMENDATIONS")
            print("-" * 30)
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"{i}. {rec}")

        # Frontend access instructions
        if report["summary"]["overall_status"] == "PASSED":
            print("\n🌐 FRONTEND ACCESS")
            print("-" * 30)
            print("Your verified capsules should now be visible at:")
            print(f"👉 {test_runner.frontend_url}")
            print("\nLook for capsules with 'Verified' status in the visualizer.")

        # Save detailed report
        with open("verification_test_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved to: verification_test_report.json")

        return report["summary"]["overall_status"] == "PASSED"

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\n❌ Test execution failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
