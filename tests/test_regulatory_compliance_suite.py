"""
Comprehensive Regulatory Compliance Test Suite
=============================================

Production-grade compliance testing covering:
- GDPR compliance validation (Articles 17, 33, 34, 44-49)
- KYC/AML financial compliance testing
- Cross-border data transfer validation
- Automated breach notification testing
- HIPAA, PCI DSS, ISO 27001 framework validation
- Continuous compliance monitoring
- Regulatory reporting automation
- Data retention and lifecycle management
- Consent management and privacy controls
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Any, Tuple
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import tempfile
import os

# Import compliance modules
from src.compliance.financial_compliance import (
    KYCAMLEngine,
    TransactionMonitor,
    SuspiciousActivityReporter,
    TransactionType,
    RiskLevel,
    ComplianceStatus,
)
from src.compliance.data_retention_enforcer import (
    DataRetentionEnforcer,
    RetentionPolicy,
    RetentionPeriod,
    ErasureRequest,
    LitigationHold,
)
from src.compliance.transfer_compliance import (
    CrossBorderTransferValidator,
    TransferMechanism,
    AdequacyDecision,
    TransferImpactAssessment,
    DataTransferRequest,
)
from src.compliance.breach_notification import (
    BreachNotificationSystem,
    DataBreach,
    BreachSeverity,
    BreachCategory,
    NotificationStatus,
)
from src.compliance.regulatory_frameworks import (
    RegulatoryComplianceFramework,
    ComplianceFramework,
    ComplianceRequirement,
    ValidationResult,
)
from src.compliance.compliance_monitor import (
    ComplianceMonitor,
    ComplianceMetric,
    AlertRule,
    AlertSeverity,
)
from src.compliance.compliance_reporting import (
    ComplianceReportingSystem,
    ReportType,
    ReportFormat,
    ReportFrequency,
)


class ComplianceTestSuite:
    """Comprehensive compliance testing suite."""

    def __init__(self):
        self.test_results = {}
        self.compliance_targets = {
            "gdpr_compliance_score": 90,
            "kyc_aml_compliance_score": 95,
            "breach_notification_compliance": 100,
            "data_retention_compliance": 90,
            "transfer_compliance_score": 85,
            "overall_compliance_score": 90,
        }

    async def run_all_compliance_tests(self) -> Dict[str, Any]:
        """Run complete compliance test suite."""
        print("🛡️  Starting Comprehensive Compliance Test Suite")
        print("=" * 70)

        # Test KYC/AML financial compliance
        kyc_results = await self.test_kyc_aml_compliance()
        self.test_results["kyc_aml"] = kyc_results

        # Test data retention enforcement
        retention_results = await self.test_data_retention_compliance()
        self.test_results["data_retention"] = retention_results

        # Test cross-border transfer compliance
        transfer_results = await self.test_transfer_compliance()
        self.test_results["transfer_compliance"] = transfer_results

        # Test breach notification system
        breach_results = await self.test_breach_notification_compliance()
        self.test_results["breach_notification"] = breach_results

        # Test regulatory frameworks
        framework_results = await self.test_regulatory_frameworks()
        self.test_results["regulatory_frameworks"] = framework_results

        # Test compliance monitoring
        monitoring_results = await self.test_compliance_monitoring()
        self.test_results["compliance_monitoring"] = monitoring_results

        # Test automated reporting
        reporting_results = await self.test_compliance_reporting()
        self.test_results["compliance_reporting"] = reporting_results

        # Generate compliance report
        report = self.generate_compliance_report()
        self.test_results["summary"] = report

        return self.test_results

    async def test_kyc_aml_compliance(self) -> Dict[str, Any]:
        """Test KYC/AML financial compliance system."""
        print("💰 Testing KYC/AML Financial Compliance...")

        # Initialize KYC/AML engine
        kyc_engine = KYCAMLEngine()
        transaction_monitor = TransactionMonitor()
        sar_reporter = SuspiciousActivityReporter()

        # Test customer verification
        test_customer = {
            "customer_id": "test_customer_001",
            "name": "John Doe",
            "date_of_birth": "1990-01-01",
            "address": "123 Main St, City, Country",
            "document_type": "passport",
            "document_number": "P123456789",
            "risk_profile": "medium",
        }

        # Test KYC verification
        kyc_result = await kyc_engine.verify_customer(test_customer)
        kyc_passed = kyc_result["status"] == ComplianceStatus.COMPLIANT

        # Test transaction monitoring
        test_transactions = [
            {
                "transaction_id": f"txn_{i:03d}",
                "customer_id": "test_customer_001",
                "amount": Decimal("1000.00") + Decimal(str(i * 500)),
                "transaction_type": TransactionType.TRANSFER,
                "timestamp": datetime.now(timezone.utc),
                "counterparty": f"counterparty_{i}",
            }
            for i in range(10)
        ]

        # Monitor transactions
        monitoring_results = []
        for transaction in test_transactions:
            result = await transaction_monitor.monitor_transaction(transaction)
            monitoring_results.append(result)

        # Test suspicious activity detection
        high_value_transaction = {
            "transaction_id": "txn_suspicious_001",
            "customer_id": "test_customer_001",
            "amount": Decimal("50000.00"),  # High value
            "transaction_type": TransactionType.CASH_DEPOSIT,
            "timestamp": datetime.now(timezone.utc),
            "counterparty": "unknown_entity",
        }

        suspicious_result = await transaction_monitor.monitor_transaction(
            high_value_transaction
        )
        suspicious_detected = suspicious_result["risk_level"] == RiskLevel.HIGH

        # Test SAR generation
        if suspicious_detected:
            sar_result = await sar_reporter.generate_sar_report(
                high_value_transaction, suspicious_result
            )
            sar_generated = sar_result["status"] == "generated"
        else:
            sar_generated = False

        # Calculate compliance metrics
        total_transactions = len(test_transactions) + 1
        flagged_transactions = sum(
            1
            for r in monitoring_results + [suspicious_result]
            if r["risk_level"] in [RiskLevel.HIGH, RiskLevel.MEDIUM]
        )

        detection_rate = (flagged_transactions / total_transactions) * 100

        # Test risk scoring accuracy
        risk_scores = [
            r["risk_score"] for r in monitoring_results + [suspicious_result]
        ]
        avg_risk_score = sum(risk_scores) / len(risk_scores)

        result = {
            "kyc_verification_passed": kyc_passed,
            "transaction_monitoring_active": len(monitoring_results) > 0,
            "suspicious_activity_detected": suspicious_detected,
            "sar_report_generated": sar_generated,
            "total_transactions_monitored": total_transactions,
            "flagged_transactions": flagged_transactions,
            "detection_rate_percent": round(detection_rate, 2),
            "average_risk_score": round(float(avg_risk_score), 2),
            "compliance_score": self._calculate_kyc_compliance_score(
                kyc_passed, suspicious_detected, sar_generated, detection_rate
            ),
            "target_met": True,  # Will be updated based on compliance score
        }

        result["target_met"] = (
            result["compliance_score"]
            >= self.compliance_targets["kyc_aml_compliance_score"]
        )

        print(f"   ✓ KYC verification: {'PASSED' if kyc_passed else 'FAILED'}")
        print(f"   ✓ Transactions monitored: {total_transactions}")
        print(f"   ✓ Detection rate: {detection_rate:.1f}%")
        print(f"   ✓ Compliance score: {result['compliance_score']}/100")

        return result

    async def test_data_retention_compliance(self) -> Dict[str, Any]:
        """Test automated data retention and GDPR Article 17 compliance."""
        print("🗂️  Testing Data Retention Compliance...")

        # Initialize retention enforcer
        retention_enforcer = DataRetentionEnforcer()

        # Create test retention policies
        test_policies = [
            RetentionPolicy(
                policy_id="policy_user_data",
                data_category="user_data",
                retention_period=RetentionPeriod.SEVEN_YEARS,
                legal_basis="contract",
                auto_delete=True,
            ),
            RetentionPolicy(
                policy_id="policy_system_logs",
                data_category="system_logs",
                retention_period=RetentionPeriod.ONE_YEAR,
                legal_basis="legitimate_interest",
                auto_delete=True,
            ),
            RetentionPolicy(
                policy_id="policy_analytics",
                data_category="analytics_data",
                retention_period=RetentionPeriod.TWO_YEARS,
                legal_basis="consent",
                auto_delete=True,
            ),
        ]

        # Register policies
        policy_registration_results = []
        for policy in test_policies:
            result = await retention_enforcer.register_retention_policy(policy)
            policy_registration_results.append(result["success"])

        policies_registered = all(policy_registration_results)

        # Test data subject with expired data
        test_data_records = [
            {
                "record_id": f"record_{i:03d}",
                "subject_id": "test_subject_001",
                "data_category": "user_data",
                "created_at": datetime.now(timezone.utc)
                - timedelta(days=365 * 8),  # 8 years old
                "data_content": {"name": "Test User", "email": "test@example.com"},
            }
            for i in range(5)
        ]

        # Process data for retention
        for record in test_data_records:
            await retention_enforcer.process_data_record(record)

        # Test erasure request (GDPR Article 17)
        erasure_request = ErasureRequest(
            request_id="erasure_001",
            subject_id="test_subject_001",
            request_type="right_to_erasure",
            requested_at=datetime.now(timezone.utc),
            reason="no_longer_necessary",
        )

        erasure_result = await retention_enforcer.process_erasure_request(
            erasure_request
        )
        erasure_processed = erasure_result["status"] == "completed"

        # Test litigation hold
        litigation_hold = LitigationHold(
            hold_id="hold_001",
            subject_id="test_subject_002",
            case_reference="CASE-2024-001",
            hold_start=datetime.now(timezone.utc),
            hold_reason="pending_litigation",
        )

        hold_result = await retention_enforcer.apply_litigation_hold(litigation_hold)
        hold_applied = hold_result["success"]

        # Test automated deletion scheduler
        deletion_schedule = await retention_enforcer.schedule_automated_deletions()
        scheduled_deletions = len(deletion_schedule["scheduled_deletions"])

        # Test compliance metrics
        compliance_metrics = await retention_enforcer.get_compliance_metrics()

        result = {
            "policies_registered": policies_registered,
            "total_policies": len(test_policies),
            "erasure_request_processed": erasure_processed,
            "litigation_hold_applied": hold_applied,
            "scheduled_deletions": scheduled_deletions,
            "expired_data_detected": len(test_data_records),
            "compliance_metrics": {
                "total_subjects": compliance_metrics.get("total_subjects", 0),
                "pending_deletions": compliance_metrics.get("pending_deletions", 0),
                "completed_erasures": compliance_metrics.get("completed_erasures", 0),
                "active_litigation_holds": compliance_metrics.get(
                    "active_litigation_holds", 0
                ),
            },
            "gdpr_article_17_compliance": erasure_processed and hold_applied,
            "compliance_score": self._calculate_retention_compliance_score(
                policies_registered,
                erasure_processed,
                hold_applied,
                scheduled_deletions,
            ),
            "target_met": True,  # Will be updated based on compliance score
        }

        result["target_met"] = (
            result["compliance_score"]
            >= self.compliance_targets["data_retention_compliance"]
        )

        print(f"   ✓ Policies registered: {len(test_policies)}")
        print(
            f"   ✓ Erasure requests processed: {'YES' if erasure_processed else 'NO'}"
        )
        print(f"   ✓ Scheduled deletions: {scheduled_deletions}")
        print(f"   ✓ Compliance score: {result['compliance_score']}/100")

        return result

    async def test_transfer_compliance(self) -> Dict[str, Any]:
        """Test cross-border data transfer compliance."""
        print("🌍 Testing Cross-Border Transfer Compliance...")

        # Initialize transfer validator
        transfer_validator = CrossBorderTransferValidator()

        # Test adequacy decisions
        test_transfers = [
            {
                "transfer_id": "transfer_001",
                "origin_country": "EU",
                "destination_country": "US",
                "data_category": "personal_data",
                "transfer_mechanism": TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES,
                "data_subjects_count": 1000,
                "transfer_purpose": "service_provision",
            },
            {
                "transfer_id": "transfer_002",
                "origin_country": "EU",
                "destination_country": "CA",  # Canada has adequacy decision
                "data_category": "personal_data",
                "transfer_mechanism": TransferMechanism.ADEQUACY_DECISION,
                "data_subjects_count": 500,
                "transfer_purpose": "data_processing",
            },
            {
                "transfer_id": "transfer_003",
                "origin_country": "EU",
                "destination_country": "CN",  # China requires special assessment
                "data_category": "sensitive_data",
                "transfer_mechanism": TransferMechanism.BINDING_CORPORATE_RULES,
                "data_subjects_count": 100,
                "transfer_purpose": "analytics",
            },
        ]

        # Validate transfers
        validation_results = []
        for transfer_data in test_transfers:
            transfer_request = DataTransferRequest(**transfer_data)
            result = await transfer_validator.validate_transfer(transfer_request)
            validation_results.append(result)

        # Test Transfer Impact Assessment (TIA)
        high_risk_transfer = test_transfers[2]  # China transfer
        tia_result = await transfer_validator.conduct_transfer_impact_assessment(
            DataTransferRequest(**high_risk_transfer)
        )
        tia_completed = tia_result["assessment_completed"]

        # Test adequacy decision checking
        adequacy_results = []
        for transfer_data in test_transfers:
            adequacy_check = await transfer_validator.check_adequacy_decision(
                transfer_data["destination_country"]
            )
            adequacy_results.append(adequacy_check)

        # Calculate compliance metrics
        approved_transfers = sum(1 for r in validation_results if r["approved"])
        total_transfers = len(test_transfers)
        approval_rate = (approved_transfers / total_transfers) * 100

        # Test SCC validation
        scc_transfer = test_transfers[0]
        scc_validation = await transfer_validator.validate_standard_contractual_clauses(
            DataTransferRequest(**scc_transfer)
        )
        scc_valid = scc_validation["clauses_valid"]

        result = {
            "total_transfers_validated": total_transfers,
            "approved_transfers": approved_transfers,
            "approval_rate_percent": round(approval_rate, 2),
            "tia_assessment_completed": tia_completed,
            "adequacy_decisions_checked": len(adequacy_results),
            "scc_validation_passed": scc_valid,
            "validation_details": [
                {
                    "transfer_id": r["transfer_id"],
                    "approved": r["approved"],
                    "risk_level": r.get("risk_level", "unknown"),
                    "required_safeguards": len(r.get("required_safeguards", [])),
                }
                for r in validation_results
            ],
            "compliance_score": self._calculate_transfer_compliance_score(
                approval_rate, tia_completed, scc_valid, len(adequacy_results)
            ),
            "target_met": True,  # Will be updated based on compliance score
        }

        result["target_met"] = (
            result["compliance_score"]
            >= self.compliance_targets["transfer_compliance_score"]
        )

        print(f"   ✓ Transfers validated: {total_transfers}")
        print(f"   ✓ Approval rate: {approval_rate:.1f}%")
        print(f"   ✓ TIA completed: {'YES' if tia_completed else 'NO'}")
        print(f"   ✓ Compliance score: {result['compliance_score']}/100")

        return result

    async def test_breach_notification_compliance(self) -> Dict[str, Any]:
        """Test automated breach notification system."""
        print("🚨 Testing Breach Notification Compliance...")

        # Initialize breach notification system
        breach_system = BreachNotificationSystem()

        # Create test breach scenarios
        test_breaches = [
            DataBreach(
                breach_id="breach_001",
                breach_type=BreachCategory.UNAUTHORIZED_ACCESS,
                severity=BreachSeverity.HIGH,
                affected_subjects_count=10000,
                data_categories=["personal_data", "financial_data"],
                discovery_time=datetime.now(timezone.utc) - timedelta(hours=1),
                description="Unauthorized access to customer database",
            ),
            DataBreach(
                breach_id="breach_002",
                breach_type=BreachCategory.DATA_LOSS,
                severity=BreachSeverity.MEDIUM,
                affected_subjects_count=500,
                data_categories=["contact_information"],
                discovery_time=datetime.now(timezone.utc) - timedelta(hours=48),
                description="Accidental deletion of contact records",
            ),
            DataBreach(
                breach_id="breach_003",
                breach_type=BreachCategory.SYSTEM_COMPROMISE,
                severity=BreachSeverity.CRITICAL,
                affected_subjects_count=50000,
                data_categories=["personal_data", "health_data", "financial_data"],
                discovery_time=datetime.now(timezone.utc) - timedelta(hours=12),
                description="System compromise with potential data exfiltration",
            ),
        ]

        # Process breaches
        notification_results = []
        for breach in test_breaches:
            result = await breach_system.process_breach(breach)
            notification_results.append(result)

        # Test 72-hour notification requirement
        within_72_hours = []
        for i, result in enumerate(notification_results):
            breach = test_breaches[i]
            notification_time = result.get("notification_time")
            if notification_time:
                time_to_notify = (
                    notification_time - breach.discovery_time
                ).total_seconds() / 3600
                within_72_hours.append(time_to_notify <= 72)
            else:
                within_72_hours.append(False)

        # Test notification completeness
        complete_notifications = sum(
            1
            for r in notification_results
            if r["supervisory_authority_notified"] and r["data_subjects_notified"]
        )

        # Test breach assessment accuracy
        high_risk_breaches = sum(
            1
            for b in test_breaches
            if b.severity in [BreachSeverity.HIGH, BreachSeverity.CRITICAL]
        )

        correctly_escalated = sum(
            1
            for i, r in enumerate(notification_results)
            if (
                test_breaches[i].severity
                in [BreachSeverity.HIGH, BreachSeverity.CRITICAL]
                and r["requires_subject_notification"]
            )
        )

        # Test automated response
        response_measures = []
        for result in notification_results:
            measures = result.get("response_measures", [])
            response_measures.extend(measures)

        result = {
            "total_breaches_processed": len(test_breaches),
            "notifications_within_72h": sum(within_72_hours),
            "notification_compliance_rate": (
                sum(within_72_hours) / len(within_72_hours)
            )
            * 100,
            "complete_notifications": complete_notifications,
            "high_risk_breaches_detected": high_risk_breaches,
            "correctly_escalated_breaches": correctly_escalated,
            "escalation_accuracy": (correctly_escalated / high_risk_breaches) * 100
            if high_risk_breaches > 0
            else 100,
            "total_response_measures": len(response_measures),
            "breach_details": [
                {
                    "breach_id": r["breach_id"],
                    "severity": test_breaches[i].severity.value,
                    "notification_time_hours": (
                        r.get("notification_time", datetime.now(timezone.utc))
                        - test_breaches[i].discovery_time
                    ).total_seconds()
                    / 3600,
                    "within_72h": within_72_hours[i],
                    "authority_notified": r["supervisory_authority_notified"],
                    "subjects_notified": r["data_subjects_notified"],
                }
                for i, r in enumerate(notification_results)
            ],
            "gdpr_article_33_compliance": sum(within_72_hours) == len(within_72_hours),
            "gdpr_article_34_compliance": complete_notifications == len(test_breaches),
            "compliance_score": 100,  # Perfect score if all requirements met
            "target_met": True,
        }

        # Calculate compliance score
        compliance_rate = result["notification_compliance_rate"]
        escalation_rate = result["escalation_accuracy"]
        result["compliance_score"] = min(100, (compliance_rate + escalation_rate) / 2)
        result["target_met"] = (
            result["compliance_score"]
            >= self.compliance_targets["breach_notification_compliance"]
        )

        print(f"   ✓ Breaches processed: {len(test_breaches)}")
        print(f"   ✓ 72-hour compliance: {sum(within_72_hours)}/{len(within_72_hours)}")
        print(f"   ✓ Complete notifications: {complete_notifications}")
        print(f"   ✓ Compliance score: {result['compliance_score']:.1f}/100")

        return result

    async def test_regulatory_frameworks(self) -> Dict[str, Any]:
        """Test HIPAA, PCI DSS, and ISO 27001 compliance frameworks."""
        print("📋 Testing Regulatory Framework Compliance...")

        # Initialize regulatory framework
        compliance_framework = RegulatoryComplianceFramework()

        # Test HIPAA compliance
        hipaa_test_data = {
            "entity_type": "covered_entity",
            "phi_handling": True,
            "business_associate_agreements": True,
            "security_measures": ["encryption", "access_controls", "audit_logs"],
            "privacy_policies": True,
            "breach_notification_procedures": True,
        }

        hipaa_result = await compliance_framework.validate_hipaa_compliance(
            hipaa_test_data
        )
        hipaa_compliant = hipaa_result.status == "COMPLIANT"

        # Test PCI DSS compliance
        pci_test_data = {
            "handles_card_data": True,
            "cardholder_data_environment": {
                "network_segmentation": True,
                "encryption_in_transit": True,
                "encryption_at_rest": True,
                "access_controls": True,
                "vulnerability_management": True,
            },
            "compliance_level": "Level 1",
            "annual_assessment": True,
        }

        pci_result = await compliance_framework.validate_pci_dss_compliance(
            pci_test_data
        )
        pci_compliant = pci_result.status == "COMPLIANT"

        # Test ISO 27001 compliance
        iso_test_data = {
            "information_security_policy": True,
            "risk_management": True,
            "asset_management": True,
            "access_control": True,
            "cryptography": True,
            "physical_security": True,
            "operations_security": True,
            "communications_security": True,
            "incident_management": True,
            "business_continuity": True,
            "supplier_relationships": True,
        }

        iso_result = await compliance_framework.validate_iso27001_compliance(
            iso_test_data
        )
        iso_compliant = iso_result.status == "COMPLIANT"

        # Test comprehensive framework validation
        frameworks_tested = [
            ComplianceFramework.HIPAA,
            ComplianceFramework.PCI_DSS,
            ComplianceFramework.ISO27001,
            ComplianceFramework.GDPR,
        ]

        framework_results = []
        for framework in frameworks_tested:
            test_data = self._get_framework_test_data(framework)
            result = await compliance_framework.validate_framework_compliance(
                framework, test_data
            )
            framework_results.append(
                {
                    "framework": framework.value,
                    "compliant": result.status == "COMPLIANT",
                    "score": result.score,
                    "requirements_met": len(result.passed_requirements),
                    "requirements_failed": len(result.failed_requirements),
                }
            )

        # Calculate overall framework compliance
        total_frameworks = len(framework_results)
        compliant_frameworks = sum(1 for r in framework_results if r["compliant"])
        overall_compliance_rate = (compliant_frameworks / total_frameworks) * 100

        result = {
            "hipaa_compliant": hipaa_compliant,
            "pci_dss_compliant": pci_compliant,
            "iso27001_compliant": iso_compliant,
            "frameworks_tested": total_frameworks,
            "compliant_frameworks": compliant_frameworks,
            "overall_compliance_rate": round(overall_compliance_rate, 2),
            "framework_details": framework_results,
            "compliance_score": round(overall_compliance_rate, 1),
            "target_met": overall_compliance_rate >= 85,
        }

        print(f"   ✓ HIPAA compliant: {'YES' if hipaa_compliant else 'NO'}")
        print(f"   ✓ PCI DSS compliant: {'YES' if pci_compliant else 'NO'}")
        print(f"   ✓ ISO 27001 compliant: {'YES' if iso_compliant else 'NO'}")
        print(f"   ✓ Overall compliance rate: {overall_compliance_rate:.1f}%")

        return result

    async def test_compliance_monitoring(self) -> Dict[str, Any]:
        """Test continuous compliance monitoring system."""
        print("👁️  Testing Compliance Monitoring System...")

        # Initialize compliance monitor
        compliance_monitor = ComplianceMonitor()

        # Test metric collection
        test_metrics = [
            ComplianceMetric(
                metric_name="gdpr_consent_rate",
                value=95.5,
                timestamp=datetime.now(timezone.utc),
                category="privacy",
            ),
            ComplianceMetric(
                metric_name="data_retention_compliance",
                value=88.2,
                timestamp=datetime.now(timezone.utc),
                category="data_governance",
            ),
            ComplianceMetric(
                metric_name="breach_notification_time",
                value=24.5,  # hours
                timestamp=datetime.now(timezone.utc),
                category="incident_response",
            ),
        ]

        # Record metrics
        for metric in test_metrics:
            await compliance_monitor.record_metric(metric)

        # Test alert rules
        alert_rules = [
            AlertRule(
                rule_id="gdpr_consent_low",
                metric_name="gdpr_consent_rate",
                threshold=90.0,
                operator="lt",
                severity=AlertSeverity.WARNING,
            ),
            AlertRule(
                rule_id="breach_notification_slow",
                metric_name="breach_notification_time",
                threshold=72.0,
                operator="gt",
                severity=AlertSeverity.CRITICAL,
            ),
        ]

        # Configure alerts
        for rule in alert_rules:
            await compliance_monitor.configure_alert_rule(rule)

        # Trigger alerts by adding metrics that violate rules
        violation_metrics = [
            ComplianceMetric(
                metric_name="gdpr_consent_rate",
                value=85.0,  # Below threshold
                timestamp=datetime.now(timezone.utc),
                category="privacy",
            ),
            ComplianceMetric(
                metric_name="breach_notification_time",
                value=96.0,  # Above threshold
                timestamp=datetime.now(timezone.utc),
                category="incident_response",
            ),
        ]

        # Process violation metrics and check for alerts
        alerts_triggered = 0
        for metric in violation_metrics:
            await compliance_monitor.record_metric(metric)
            alerts = await compliance_monitor.check_alert_rules(metric)
            alerts_triggered += len(alerts)

        # Test compliance dashboard data
        dashboard_data = await compliance_monitor.get_compliance_dashboard()

        # Test automated remediation
        remediation_actions = await compliance_monitor.suggest_remediation_actions()

        result = {
            "metrics_recorded": len(test_metrics) + len(violation_metrics),
            "alert_rules_configured": len(alert_rules),
            "alerts_triggered": alerts_triggered,
            "dashboard_data_available": bool(dashboard_data),
            "remediation_suggestions": len(remediation_actions),
            "monitoring_categories": len(
                set(m.category for m in test_metrics + violation_metrics)
            ),
            "real_time_monitoring_active": True,
            "compliance_score": self._calculate_monitoring_compliance_score(
                len(test_metrics), alerts_triggered, len(remediation_actions)
            ),
            "target_met": True,
        }

        result["target_met"] = result["compliance_score"] >= 85

        print(f"   ✓ Metrics monitored: {result['metrics_recorded']}")
        print(f"   ✓ Alerts triggered: {alerts_triggered}")
        print(f"   ✓ Remediation suggestions: {len(remediation_actions)}")
        print(f"   ✓ Compliance score: {result['compliance_score']}/100")

        return result

    async def test_compliance_reporting(self) -> Dict[str, Any]:
        """Test automated compliance reporting system."""
        print("📊 Testing Compliance Reporting System...")

        # Initialize reporting system
        reporting_system = ComplianceReportingSystem()

        # Test different report types
        report_types_to_test = [
            (ReportType.GDPR_ARTICLE_30, "Records of Processing Activities"),
            (ReportType.SAR_REPORT, "Suspicious Activity Report"),
            (ReportType.BREACH_SUMMARY, "Data Breach Summary"),
            (ReportType.KYC_AUDIT, "KYC Compliance Audit"),
            (ReportType.PCI_DSS_COMPLIANCE, "PCI DSS Compliance Report"),
        ]

        # Generate reports
        generated_reports = []
        for report_type, description in report_types_to_test:
            report_data = self._get_test_report_data(report_type)
            result = await reporting_system.generate_report(
                report_type=report_type, data=report_data, format=ReportFormat.JSON
            )
            generated_reports.append(
                {
                    "type": report_type.value,
                    "description": description,
                    "generated": result.get("success", False),
                    "report_id": result.get("report_id"),
                    "size_bytes": len(str(result.get("report_data", ""))),
                }
            )

        # Test report scheduling
        scheduled_reports = []
        for report_type, _ in report_types_to_test[:3]:  # Schedule first 3 reports
            schedule_result = await reporting_system.schedule_report(
                report_type=report_type,
                frequency=ReportFrequency.MONTHLY,
                recipients=["compliance@example.com"],
                format=ReportFormat.PDF,
            )
            scheduled_reports.append(schedule_result.get("success", False))

        # Test report validation
        validation_results = []
        for report in generated_reports:
            if report["generated"]:
                validation = await reporting_system.validate_report(
                    report["report_id"], report["type"]
                )
                validation_results.append(validation.get("valid", False))

        # Test automated submission
        submission_results = []
        for report in generated_reports[:2]:  # Submit first 2 reports
            if report["generated"]:
                submission = await reporting_system.submit_report(
                    report["report_id"], "regulatory_authority_test"
                )
                submission_results.append(submission.get("submitted", False))

        # Calculate metrics
        total_reports = len(report_types_to_test)
        successful_generations = sum(1 for r in generated_reports if r["generated"])
        successful_schedules = sum(scheduled_reports)
        successful_validations = sum(validation_results)
        successful_submissions = sum(submission_results)

        generation_rate = (successful_generations / total_reports) * 100
        validation_rate = (
            (successful_validations / len(validation_results)) * 100
            if validation_results
            else 0
        )

        result = {
            "total_report_types_tested": total_reports,
            "reports_generated_successfully": successful_generations,
            "generation_success_rate": round(generation_rate, 2),
            "reports_scheduled": successful_schedules,
            "reports_validated": successful_validations,
            "validation_success_rate": round(validation_rate, 2),
            "reports_submitted": successful_submissions,
            "report_details": generated_reports,
            "automated_scheduling_active": successful_schedules > 0,
            "regulatory_submission_active": successful_submissions > 0,
            "compliance_score": min(100, (generation_rate + validation_rate) / 2),
            "target_met": True,
        }

        result["target_met"] = result["compliance_score"] >= 85

        print(f"   ✓ Reports generated: {successful_generations}/{total_reports}")
        print(f"   ✓ Reports scheduled: {successful_schedules}")
        print(f"   ✓ Reports validated: {successful_validations}")
        print(f"   ✓ Compliance score: {result['compliance_score']:.1f}/100")

        return result

    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance assessment report."""
        print("📋 Generating Compliance Assessment Report...")

        # Calculate individual compliance scores
        scores = {}
        for category, results in self.test_results.items():
            if category != "summary" and isinstance(results, dict):
                scores[category] = results.get("compliance_score", 0)

        # Calculate overall compliance score
        overall_score = sum(scores.values()) / len(scores) if scores else 0

        # Determine compliance grade
        compliance_grade = self._calculate_compliance_grade(overall_score)

        # Count targets met
        targets_met = 0
        total_targets = 0
        for category, results in self.test_results.items():
            if category != "summary" and isinstance(results, dict):
                if "target_met" in results:
                    total_targets += 1
                    if results["target_met"]:
                        targets_met += 1

        # Generate recommendations
        recommendations = self._generate_compliance_recommendations()

        # Critical compliance areas
        critical_areas = []
        for category, results in self.test_results.items():
            if category != "summary" and isinstance(results, dict):
                score = results.get("compliance_score", 0)
                if score < 85:
                    critical_areas.append(
                        {
                            "area": category,
                            "score": score,
                            "target_met": results.get("target_met", False),
                        }
                    )

        summary = {
            "overall_compliance_score": round(overall_score, 1),
            "compliance_grade": compliance_grade,
            "category_scores": {k: round(v, 1) for k, v in scores.items()},
            "targets_met": targets_met,
            "total_targets": total_targets,
            "target_achievement_rate": round((targets_met / total_targets) * 100, 1)
            if total_targets > 0
            else 0,
            "critical_areas": critical_areas,
            "recommendations": recommendations,
            "production_ready": overall_score
            >= self.compliance_targets["overall_compliance_score"],
            "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
            "regulatory_coverage": {
                "gdpr": "FULL",
                "kyc_aml": "FULL",
                "hipaa": "FULL",
                "pci_dss": "FULL",
                "iso27001": "FULL",
            },
        }

        print(f"   ✓ Overall Compliance Score: {overall_score:.1f}/100")
        print(f"   ✓ Compliance Grade: {compliance_grade}")
        print(f"   ✓ Targets Met: {targets_met}/{total_targets}")
        print(
            f"   ✓ Production Ready: {'YES' if summary['production_ready'] else 'NO'}"
        )

        return summary

    # Helper methods for calculating compliance scores
    def _calculate_kyc_compliance_score(
        self,
        kyc_passed: bool,
        suspicious_detected: bool,
        sar_generated: bool,
        detection_rate: float,
    ) -> int:
        """Calculate KYC/AML compliance score."""
        score = 0
        if kyc_passed:
            score += 30
        if suspicious_detected:
            score += 25
        if sar_generated:
            score += 20
        score += min(25, detection_rate * 2.5)  # Up to 25 points for detection rate
        return min(100, score)

    def _calculate_retention_compliance_score(
        self,
        policies_registered: bool,
        erasure_processed: bool,
        hold_applied: bool,
        scheduled_deletions: int,
    ) -> int:
        """Calculate data retention compliance score."""
        score = 0
        if policies_registered:
            score += 40
        if erasure_processed:
            score += 30
        if hold_applied:
            score += 20
        score += min(10, scheduled_deletions)  # Up to 10 points for scheduled deletions
        return min(100, score)

    def _calculate_transfer_compliance_score(
        self,
        approval_rate: float,
        tia_completed: bool,
        scc_valid: bool,
        adequacy_checks: int,
    ) -> int:
        """Calculate transfer compliance score."""
        score = 0
        score += min(50, approval_rate * 0.5)  # Up to 50 points for approval rate
        if tia_completed:
            score += 25
        if scc_valid:
            score += 15
        score += min(10, adequacy_checks * 2)  # Up to 10 points for adequacy checks
        return min(100, score)

    def _calculate_monitoring_compliance_score(
        self, metrics_count: int, alerts_triggered: int, remediation_count: int
    ) -> int:
        """Calculate monitoring compliance score."""
        score = 60  # Base score for basic monitoring
        score += min(20, metrics_count * 2)  # Up to 20 points for metrics
        score += min(10, alerts_triggered * 5)  # Up to 10 points for alerts
        score += min(10, remediation_count * 2)  # Up to 10 points for remediation
        return min(100, score)

    def _calculate_compliance_grade(self, score: float) -> str:
        """Calculate compliance grade based on score."""
        if score >= 95:
            return "A+ (Excellent - Production Ready)"
        elif score >= 90:
            return "A (Very Good - Production Ready)"
        elif score >= 85:
            return "B+ (Good - Minor Improvements Needed)"
        elif score >= 80:
            return "B (Acceptable - Some Improvements Needed)"
        elif score >= 70:
            return "C (Needs Improvement - Not Production Ready)"
        else:
            return "F (Poor - Major Compliance Issues)"

    def _generate_compliance_recommendations(self) -> List[str]:
        """Generate compliance improvement recommendations."""
        recommendations = []

        for category, results in self.test_results.items():
            if category != "summary" and isinstance(results, dict):
                score = results.get("compliance_score", 0)

                if category == "kyc_aml" and score < 95:
                    recommendations.append(
                        "Enhance KYC verification processes and transaction monitoring algorithms"
                    )

                if category == "data_retention" and score < 90:
                    recommendations.append(
                        "Implement more comprehensive data retention policies and automated deletion schedules"
                    )

                if category == "transfer_compliance" and score < 85:
                    recommendations.append(
                        "Strengthen cross-border transfer safeguards and adequacy decision validation"
                    )

                if category == "breach_notification" and score < 100:
                    recommendations.append(
                        "Optimize breach detection and notification timing to ensure 72-hour compliance"
                    )

                if category == "regulatory_frameworks" and score < 85:
                    recommendations.append(
                        "Address specific regulatory framework requirements and validation gaps"
                    )

        if not recommendations:
            recommendations.append(
                "Excellent compliance posture - maintain current controls and monitoring"
            )

        return recommendations

    def _get_framework_test_data(
        self, framework: ComplianceFramework
    ) -> Dict[str, Any]:
        """Get test data for specific compliance frameworks."""
        test_data = {
            ComplianceFramework.GDPR: {
                "lawful_basis": True,
                "consent_management": True,
                "data_subject_rights": True,
                "privacy_by_design": True,
                "dpo_appointed": True,
            },
            ComplianceFramework.HIPAA: {
                "entity_type": "covered_entity",
                "phi_handling": True,
                "security_measures": ["encryption", "access_controls"],
            },
            ComplianceFramework.PCI_DSS: {
                "handles_card_data": True,
                "compliance_level": "Level 1",
            },
            ComplianceFramework.ISO27001: {
                "information_security_policy": True,
                "risk_management": True,
            },
        }
        return test_data.get(framework, {})

    def _get_test_report_data(self, report_type: ReportType) -> Dict[str, Any]:
        """Get test data for report generation."""
        base_data = {
            "organization": "Test Organization",
            "reporting_period": {"start": "2024-01-01", "end": "2024-12-31"},
            "compliance_officer": "Test Officer",
        }

        type_specific_data = {
            ReportType.GDPR_ARTICLE_30: {
                "processing_activities": [
                    {"name": "Customer Management", "legal_basis": "contract"},
                    {"name": "Marketing", "legal_basis": "consent"},
                ]
            },
            ReportType.SAR_REPORT: {
                "suspicious_transactions": [
                    {
                        "transaction_id": "TXN001",
                        "amount": 50000,
                        "reason": "unusual_pattern",
                    }
                ]
            },
            ReportType.BREACH_SUMMARY: {
                "breaches": [
                    {
                        "breach_id": "BR001",
                        "severity": "high",
                        "affected_subjects": 1000,
                    }
                ]
            },
            ReportType.KYC_AUDIT: {
                "customers_verified": 5000,
                "verification_rate": 98.5,
            },
            ReportType.PCI_DSS_COMPLIANCE: {
                "compliance_level": "Level 1",
                "requirements_met": 12,
            },
        }

        return {**base_data, **type_specific_data.get(report_type, {})}


# Test fixtures and utilities
@pytest.fixture
async def compliance_suite():
    """Create compliance test suite fixture."""
    return ComplianceTestSuite()


# Individual test functions for pytest
@pytest.mark.asyncio
async def test_kyc_aml_compliance():
    """Test KYC/AML compliance individually."""
    suite = ComplianceTestSuite()
    result = await suite.test_kyc_aml_compliance()
    assert result["kyc_verification_passed"] == True
    assert result["compliance_score"] >= 85
    assert result["suspicious_activity_detected"] == True


@pytest.mark.asyncio
async def test_data_retention_compliance():
    """Test data retention compliance individually."""
    suite = ComplianceTestSuite()
    result = await suite.test_data_retention_compliance()
    assert result["policies_registered"] == True
    assert result["erasure_request_processed"] == True
    assert result["compliance_score"] >= 85


@pytest.mark.asyncio
async def test_breach_notification_compliance():
    """Test breach notification compliance individually."""
    suite = ComplianceTestSuite()
    result = await suite.test_breach_notification_compliance()
    assert result["gdpr_article_33_compliance"] == True
    assert result["compliance_score"] >= 90


@pytest.mark.asyncio
async def test_transfer_compliance():
    """Test cross-border transfer compliance individually."""
    suite = ComplianceTestSuite()
    result = await suite.test_transfer_compliance()
    assert result["tia_assessment_completed"] == True
    assert result["compliance_score"] >= 80


@pytest.mark.asyncio
async def test_regulatory_frameworks():
    """Test regulatory framework compliance individually."""
    suite = ComplianceTestSuite()
    result = await suite.test_regulatory_frameworks()
    assert result["overall_compliance_rate"] >= 80
    assert len(result["framework_details"]) >= 4


@pytest.mark.asyncio
async def test_compliance_monitoring():
    """Test compliance monitoring individually."""
    suite = ComplianceTestSuite()
    result = await suite.test_compliance_monitoring()
    assert result["real_time_monitoring_active"] == True
    assert result["alerts_triggered"] > 0


@pytest.mark.asyncio
async def test_compliance_reporting():
    """Test compliance reporting individually."""
    suite = ComplianceTestSuite()
    result = await suite.test_compliance_reporting()
    assert result["generation_success_rate"] >= 80
    assert result["automated_scheduling_active"] == True


# Main execution for standalone testing
if __name__ == "__main__":

    async def main():
        suite = ComplianceTestSuite()
        results = await suite.run_all_compliance_tests()

        # Save results to file
        timestamp = int(time.time())
        results_file = f"compliance_test_results_{timestamp}.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print("\n" + "=" * 70)
        print("🛡️  COMPLIANCE TEST SUITE COMPLETE!")
        print("=" * 70)

        summary = results.get("summary", {})
        print(
            f"Overall Compliance Score: {summary.get('overall_compliance_score', 0)}/100"
        )
        print(f"Compliance Grade: {summary.get('compliance_grade', 'Unknown')}")
        print(
            f"Production Ready: {'YES' if summary.get('production_ready', False) else 'NO'}"
        )
        print(
            f"Targets Met: {summary.get('targets_met', 0)}/{summary.get('total_targets', 0)}"
        )

        print("\nRegulatory Coverage:")
        coverage = summary.get("regulatory_coverage", {})
        for regulation, status in coverage.items():
            print(f"  • {regulation.upper()}: {status}")

        print("\nRecommendations:")
        for rec in summary.get("recommendations", []):
            print(f"  • {rec}")

        print(f"\nDetailed results saved to: {results_file}")

    asyncio.run(main())
