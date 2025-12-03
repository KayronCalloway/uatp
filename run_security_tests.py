#!/usr/bin/env python3
"""
Security Test Runner for UATP Economic Attack Protection.

This script runs comprehensive security tests to validate protection against
all major economic attack vectors and generates a detailed security report.
"""

import sys
import subprocess
import json
import time
from datetime import datetime, timezone
from pathlib import Path


def run_security_tests():
    """Run all security tests and generate report."""

    print("🔒 UATP Economic Security Test Suite")
    print("=" * 50)
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    print()

    # Test categories and their descriptions
    test_categories = {
        "TestAttributionGamingProtection": "Attribution Gaming Attack Prevention",
        "TestDividendPoolProtection": "Dividend Pool Drainage Protection",
        "TestSybilAttackProtection": "Sybil Attack Prevention",
        "TestFlashLoanProtection": "Flash Loan Attack Prevention",
        "TestGovernanceTokenProtection": "Governance Token Attack Prevention",
        "TestSecurityMonitoring": "Real-time Security Monitoring",
        "TestCircuitBreakers": "Economic Circuit Breaker Protection",
        "TestIntegratedSecurity": "Integrated Multi-Vector Security",
    }

    results = {}
    overall_passed = 0
    overall_failed = 0

    # Run each test category
    for test_class, description in test_categories.items():
        print(f"🧪 Running {description}...")

        # Run pytest for specific test class
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            f"tests/test_economic_security.py::{test_class}",
            "-v",
            "--tb=short",
            "--no-header",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            # Parse results
            output_lines = result.stdout.split("\n")
            passed_tests = []
            failed_tests = []

            for line in output_lines:
                if " PASSED " in line:
                    passed_tests.append(line.split("::")[-1].split()[0])
                elif " FAILED " in line:
                    failed_tests.append(line.split("::")[-1].split()[0])

            category_passed = len(passed_tests)
            category_failed = len(failed_tests)

            overall_passed += category_passed
            overall_failed += category_failed

            # Store results
            results[test_class] = {
                "description": description,
                "passed": category_passed,
                "failed": category_failed,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "status": "✅ PASS" if category_failed == 0 else "❌ FAIL",
            }

            print(
                f"   {results[test_class]['status']} - {category_passed} passed, {category_failed} failed"
            )

            if category_failed > 0:
                print(f"   Failed: {', '.join(failed_tests)}")

        except subprocess.TimeoutExpired:
            results[test_class] = {
                "description": description,
                "passed": 0,
                "failed": 1,
                "error": "Test timeout (>120s)",
            }
            overall_failed += 1
            print(f"   ⏰ TIMEOUT - Test category timed out")

        except Exception as e:
            results[test_class] = {
                "description": description,
                "passed": 0,
                "failed": 1,
                "error": str(e),
            }
            overall_failed += 1
            print(f"   💥 ERROR - {str(e)}")

        print()

    # Generate summary report
    print("📊 SECURITY TEST SUMMARY")
    print("=" * 50)

    total_tests = overall_passed + overall_failed
    pass_rate = (overall_passed / total_tests * 100) if total_tests > 0 else 0

    print(f"Total Tests Run: {total_tests}")
    print(f"Tests Passed: {overall_passed}")
    print(f"Tests Failed: {overall_failed}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print()

    # Security status assessment
    if overall_failed == 0:
        security_status = "🟢 SECURE - All security tests passed"
    elif pass_rate >= 90:
        security_status = "🟡 MOSTLY SECURE - Minor issues detected"
    elif pass_rate >= 70:
        security_status = "🟠 MODERATE RISK - Some security gaps"
    else:
        security_status = "🔴 HIGH RISK - Major security vulnerabilities"

    print(f"Security Status: {security_status}")
    print()

    # Detailed results by category
    print("📋 DETAILED RESULTS BY ATTACK VECTOR")
    print("=" * 50)

    for test_class, result in results.items():
        print(f"{result['status']} {result['description']}")
        print(f"   Tests: {result['passed']} passed, {result['failed']} failed")

        if result["failed"] > 0 and "failed_tests" in result:
            print(f"   Issues: {', '.join(result['failed_tests'])}")

        if "error" in result:
            print(f"   Error: {result['error']}")

        print()

    # Security recommendations
    print("🛡️  SECURITY RECOMMENDATIONS")
    print("=" * 50)

    recommendations = []

    if overall_failed > 0:
        recommendations.append(
            "• Fix all failing security tests before production deployment"
        )

    if any(
        "Attribution" in r["description"]
        for r in results.values()
        if r.get("failed", 0) > 0
    ):
        recommendations.append(
            "• Review and strengthen attribution gaming detection algorithms"
        )

    if any(
        "Dividend" in r["description"]
        for r in results.values()
        if r.get("failed", 0) > 0
    ):
        recommendations.append("• Implement stricter dividend concentration limits")

    if any(
        "Sybil" in r["description"] for r in results.values() if r.get("failed", 0) > 0
    ):
        recommendations.append(
            "• Enhance identity verification and rate limiting mechanisms"
        )

    if any(
        "Flash" in r["description"] for r in results.values() if r.get("failed", 0) > 0
    ):
        recommendations.append(
            "• Strengthen atomic transaction locking and state validation"
        )

    if any(
        "Governance" in r["description"]
        for r in results.values()
        if r.get("failed", 0) > 0
    ):
        recommendations.append("• Improve governance token legitimacy validation")

    if any(
        "Monitor" in r["description"]
        for r in results.values()
        if r.get("failed", 0) > 0
    ):
        recommendations.append("• Deploy real-time security monitoring in production")

    if any(
        "Circuit" in r["description"]
        for r in results.values()
        if r.get("failed", 0) > 0
    ):
        recommendations.append("• Configure and test circuit breaker thresholds")

    if not recommendations:
        recommendations.append(
            "• All security tests passed - system ready for production"
        )
        recommendations.append("• Continue regular security testing and monitoring")
        recommendations.append(
            "• Keep security thresholds updated based on threat landscape"
        )

    for rec in recommendations:
        print(rec)

    print()

    # Save detailed results to file
    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed": overall_passed,
            "failed": overall_failed,
            "pass_rate": pass_rate,
            "security_status": security_status,
        },
        "detailed_results": results,
        "recommendations": recommendations,
    }

    report_file = "security_test_report.json"
    with open(report_file, "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"📄 Detailed report saved to: {report_file}")
    print()

    # Exit with appropriate code
    return 0 if overall_failed == 0 else 1


def run_specific_attack_vector(attack_vector):
    """Run tests for a specific attack vector."""

    vector_map = {
        "attribution": "TestAttributionGamingProtection",
        "dividend": "TestDividendPoolProtection",
        "sybil": "TestSybilAttackProtection",
        "flash": "TestFlashLoanProtection",
        "governance": "TestGovernanceTokenProtection",
        "monitoring": "TestSecurityMonitoring",
        "circuits": "TestCircuitBreakers",
        "integrated": "TestIntegratedSecurity",
    }

    if attack_vector not in vector_map:
        print(f"❌ Unknown attack vector: {attack_vector}")
        print(f"Available vectors: {', '.join(vector_map.keys())}")
        return 1

    test_class = vector_map[attack_vector]

    print(f"🎯 Running tests for attack vector: {attack_vector}")
    print(f"Test class: {test_class}")
    print()

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        f"tests/test_economic_security.py::{test_class}",
        "-v",
        "--tb=long",
    ]

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific attack vector tests
        attack_vector = sys.argv[1].lower()
        exit_code = run_specific_attack_vector(attack_vector)
    else:
        # Run full security test suite
        exit_code = run_security_tests()

    sys.exit(exit_code)
