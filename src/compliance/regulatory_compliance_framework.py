"""
Regulatory Compliance Framework for UATP Capsule Engine

This framework provides comprehensive regulatory compliance management for AI systems,
including GDPR, AI Act, data protection, algorithmic transparency, and ethical AI compliance.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ComplianceStatus(Enum):
    """Compliance status levels."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL_COMPLIANCE = "partial_compliance"
    UNDER_REVIEW = "under_review"
    EXEMPT = "exempt"


class RegulatoryFramework(Enum):
    """Supported regulatory frameworks."""

    GDPR = "gdpr"
    AI_ACT = "ai_act"
    CCPA = "ccpa"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    ISO_27001 = "iso_27001"
    NIST_AI_RMF = "nist_ai_rmf"
    IEEE_2857 = "ieee_2857"
    ALGORITHMIC_ACCOUNTABILITY = "algorithmic_accountability"


class ComplianceRisk(Enum):
    """Compliance risk levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceRequirement:
    """Represents a specific compliance requirement."""

    requirement_id: str
    framework: RegulatoryFramework
    title: str
    description: str
    mandatory: bool = True
    risk_level: ComplianceRisk = ComplianceRisk.MEDIUM
    applicable_systems: Set[str] = field(default_factory=set)
    verification_methods: List[str] = field(default_factory=list)
    documentation_required: List[str] = field(default_factory=list)
    implementation_deadline: Optional[datetime] = None


@dataclass
class ComplianceAssessment:
    """Represents a compliance assessment result."""

    assessment_id: str
    framework: RegulatoryFramework
    system_id: str
    assessed_at: datetime
    status: ComplianceStatus
    score: float  # 0.0 to 1.0

    # Assessment details
    requirements_total: int = 0
    requirements_met: int = 0
    requirements_partial: int = 0
    requirements_failed: int = 0

    # Risk assessment
    risk_level: ComplianceRisk = ComplianceRisk.LOW
    critical_findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Evidence and documentation
    evidence_collected: List[Dict[str, Any]] = field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)

    # Next assessment
    next_assessment_due: Optional[datetime] = None
    assessor_id: str = "system"


@dataclass
class ComplianceReport:
    """Comprehensive compliance report."""

    report_id: str
    generated_at: datetime
    reporting_period_start: datetime
    reporting_period_end: datetime

    # Overall compliance status
    overall_status: ComplianceStatus
    overall_score: float

    # Framework-specific results
    framework_assessments: Dict[RegulatoryFramework, ComplianceAssessment] = field(
        default_factory=dict
    )

    # Risk analysis
    high_risk_items: List[Dict[str, Any]] = field(default_factory=list)
    mitigation_plans: List[Dict[str, Any]] = field(default_factory=list)

    # Trends and analytics
    compliance_trends: Dict[str, Any] = field(default_factory=dict)
    improvement_recommendations: List[str] = field(default_factory=list)


class RegulatoryComplianceFramework:
    """Comprehensive regulatory compliance management framework."""

    def __init__(self):
        self.requirements: Dict[RegulatoryFramework, List[ComplianceRequirement]] = {}
        self.assessments: Dict[str, ComplianceAssessment] = {}
        self.compliance_history: Dict[str, List[ComplianceAssessment]] = {}
        self.active_frameworks: Set[RegulatoryFramework] = set()

        # Initialize compliance requirements
        self._initialize_compliance_requirements()

        # Compliance monitoring
        self.monitoring_active = True
        self.last_global_assessment = None

    def _initialize_compliance_requirements(self):
        """Initialize compliance requirements for supported frameworks."""

        # GDPR Requirements
        gdpr_requirements = [
            ComplianceRequirement(
                requirement_id="GDPR-001",
                framework=RegulatoryFramework.GDPR,
                title="Lawful Basis for Processing",
                description="Establish and document lawful basis for processing personal data",
                risk_level=ComplianceRisk.HIGH,
                verification_methods=["documentation_review", "data_flow_analysis"],
                documentation_required=["privacy_policy", "data_processing_agreements"],
            ),
            ComplianceRequirement(
                requirement_id="GDPR-002",
                framework=RegulatoryFramework.GDPR,
                title="Data Subject Rights",
                description="Implement mechanisms for data subject rights (access, rectification, erasure)",
                risk_level=ComplianceRisk.HIGH,
                verification_methods=[
                    "rights_request_testing",
                    "process_documentation",
                ],
                documentation_required=["rights_procedures", "response_templates"],
            ),
            ComplianceRequirement(
                requirement_id="GDPR-003",
                framework=RegulatoryFramework.GDPR,
                title="Data Protection Impact Assessment",
                description="Conduct DPIA for high-risk processing activities",
                risk_level=ComplianceRisk.MEDIUM,
                verification_methods=["dpia_review", "risk_assessment"],
                documentation_required=["dpia_reports", "risk_mitigation_plans"],
            ),
            ComplianceRequirement(
                requirement_id="GDPR-004",
                framework=RegulatoryFramework.GDPR,
                title="Privacy by Design and Default",
                description="Implement privacy by design and default principles",
                risk_level=ComplianceRisk.MEDIUM,
                verification_methods=[
                    "system_architecture_review",
                    "privacy_controls_testing",
                ],
                documentation_required=["system_design_docs", "privacy_controls_list"],
            ),
        ]

        # AI Act Requirements
        ai_act_requirements = [
            ComplianceRequirement(
                requirement_id="AI-ACT-001",
                framework=RegulatoryFramework.AI_ACT,
                title="AI System Classification",
                description="Classify AI systems according to risk levels (minimal, limited, high, unacceptable)",
                risk_level=ComplianceRisk.HIGH,
                verification_methods=[
                    "system_classification_review",
                    "risk_assessment",
                ],
                documentation_required=[
                    "system_classification_report",
                    "risk_analysis",
                ],
            ),
            ComplianceRequirement(
                requirement_id="AI-ACT-002",
                framework=RegulatoryFramework.AI_ACT,
                title="Algorithmic Transparency",
                description="Provide transparency and explainability for AI decision-making",
                risk_level=ComplianceRisk.HIGH,
                verification_methods=[
                    "explainability_testing",
                    "transparency_documentation",
                ],
                documentation_required=["model_documentation", "decision_explanations"],
            ),
            ComplianceRequirement(
                requirement_id="AI-ACT-003",
                framework=RegulatoryFramework.AI_ACT,
                title="Human Oversight",
                description="Ensure appropriate human oversight of AI systems",
                risk_level=ComplianceRisk.MEDIUM,
                verification_methods=[
                    "oversight_process_review",
                    "human_intervention_testing",
                ],
                documentation_required=["oversight_procedures", "intervention_logs"],
            ),
            ComplianceRequirement(
                requirement_id="AI-ACT-004",
                framework=RegulatoryFramework.AI_ACT,
                title="Bias Monitoring and Mitigation",
                description="Implement bias monitoring and mitigation measures",
                risk_level=ComplianceRisk.HIGH,
                verification_methods=["bias_testing", "fairness_metrics"],
                documentation_required=[
                    "bias_assessment_reports",
                    "mitigation_procedures",
                ],
            ),
        ]

        # NIST AI Risk Management Framework
        nist_requirements = [
            ComplianceRequirement(
                requirement_id="NIST-001",
                framework=RegulatoryFramework.NIST_AI_RMF,
                title="AI Risk Management Strategy",
                description="Develop and maintain AI risk management strategy",
                risk_level=ComplianceRisk.MEDIUM,
                verification_methods=["strategy_review", "risk_governance_assessment"],
                documentation_required=[
                    "risk_strategy_document",
                    "governance_framework",
                ],
            ),
            ComplianceRequirement(
                requirement_id="NIST-002",
                framework=RegulatoryFramework.NIST_AI_RMF,
                title="AI System Inventory and Tracking",
                description="Maintain comprehensive inventory of AI systems",
                risk_level=ComplianceRisk.LOW,
                verification_methods=["inventory_review", "tracking_system_audit"],
                documentation_required=["ai_system_inventory", "tracking_procedures"],
            ),
        ]

        # Store requirements
        self.requirements[RegulatoryFramework.GDPR] = gdpr_requirements
        self.requirements[RegulatoryFramework.AI_ACT] = ai_act_requirements
        self.requirements[RegulatoryFramework.NIST_AI_RMF] = nist_requirements

        # Set active frameworks
        self.active_frameworks = {
            RegulatoryFramework.GDPR,
            RegulatoryFramework.AI_ACT,
            RegulatoryFramework.NIST_AI_RMF,
        }

    async def conduct_compliance_assessment(
        self,
        framework: RegulatoryFramework,
        system_id: str,
        assessor_id: str = "system",
        evidence: Optional[Dict[str, Any]] = None,
    ) -> ComplianceAssessment:
        """Conduct a comprehensive compliance assessment."""

        assessment_id = f"assess_{framework.value}_{uuid.uuid4().hex[:12]}"

        if framework not in self.requirements:
            raise ValueError(f"Framework {framework.value} not supported")

        requirements = self.requirements[framework]
        evidence = evidence or {}

        # Assess each requirement
        requirements_met = 0
        requirements_partial = 0
        requirements_failed = 0
        critical_findings = []
        recommendations = []
        audit_trail = []

        for requirement in requirements:
            # Simulate requirement assessment
            compliance_result = await self._assess_requirement(
                requirement, system_id, evidence
            )

            audit_trail.append(
                {
                    "requirement_id": requirement.requirement_id,
                    "assessment_result": compliance_result,
                    "timestamp": datetime.now(timezone.utc),
                }
            )

            if compliance_result["status"] == "compliant":
                requirements_met += 1
            elif compliance_result["status"] == "partial":
                requirements_partial += 1
                recommendations.extend(compliance_result.get("recommendations", []))
            else:
                requirements_failed += 1
                if requirement.risk_level in [
                    ComplianceRisk.HIGH,
                    ComplianceRisk.CRITICAL,
                ]:
                    critical_findings.append(
                        {
                            "requirement_id": requirement.requirement_id,
                            "title": requirement.title,
                            "finding": compliance_result.get(
                                "finding", "Non-compliant"
                            ),
                            "risk_level": requirement.risk_level.value,
                        }
                    )
                recommendations.extend(compliance_result.get("recommendations", []))

        # Calculate overall compliance score
        total_requirements = len(requirements)
        compliance_score = (
            requirements_met + (requirements_partial * 0.5)
        ) / total_requirements

        # Determine overall status
        if compliance_score >= 0.95:
            status = ComplianceStatus.COMPLIANT
        elif compliance_score >= 0.75:
            status = ComplianceStatus.PARTIAL_COMPLIANCE
        else:
            status = ComplianceStatus.NON_COMPLIANT

        # Determine risk level
        if critical_findings:
            risk_level = ComplianceRisk.CRITICAL
        elif requirements_failed > 0:
            risk_level = ComplianceRisk.HIGH
        elif requirements_partial > 0:
            risk_level = ComplianceRisk.MEDIUM
        else:
            risk_level = ComplianceRisk.LOW

        # Create assessment
        assessment = ComplianceAssessment(
            assessment_id=assessment_id,
            framework=framework,
            system_id=system_id,
            assessed_at=datetime.now(timezone.utc),
            status=status,
            score=compliance_score,
            requirements_total=total_requirements,
            requirements_met=requirements_met,
            requirements_partial=requirements_partial,
            requirements_failed=requirements_failed,
            risk_level=risk_level,
            critical_findings=critical_findings,
            recommendations=list(set(recommendations)),  # Remove duplicates
            audit_trail=audit_trail,
            next_assessment_due=datetime.now(timezone.utc) + timedelta(days=90),
            assessor_id=assessor_id,
        )

        # Store assessment
        self.assessments[assessment_id] = assessment

        # Update compliance history
        if system_id not in self.compliance_history:
            self.compliance_history[system_id] = []
        self.compliance_history[system_id].append(assessment)

        logger.info(
            f"Compliance assessment completed: {assessment_id} - {status.value} ({compliance_score:.2%})"
        )

        return assessment

    async def _assess_requirement(
        self,
        requirement: ComplianceRequirement,
        system_id: str,
        evidence: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess a specific compliance requirement."""

        # Mock assessment logic - in production, this would implement actual checks
        requirement_evidence = evidence.get(requirement.requirement_id, {})

        # Simulate different compliance outcomes
        import random

        compliance_probability = 0.8  # 80% chance of compliance for demo

        if requirement.risk_level == ComplianceRisk.CRITICAL:
            compliance_probability = 0.6
        elif requirement.risk_level == ComplianceRisk.HIGH:
            compliance_probability = 0.7

        rand_value = random.random()

        if rand_value < compliance_probability:
            return {
                "status": "compliant",
                "finding": "Requirement successfully implemented and verified",
                "evidence_score": 1.0,
            }
        elif rand_value < compliance_probability + 0.15:
            return {
                "status": "partial",
                "finding": "Requirement partially implemented, improvements needed",
                "evidence_score": 0.6,
                "recommendations": [
                    f"Complete implementation of {requirement.title}",
                    f"Provide additional documentation for {requirement.requirement_id}",
                ],
            }
        else:
            return {
                "status": "non_compliant",
                "finding": "Requirement not implemented or inadequately addressed",
                "evidence_score": 0.2,
                "recommendations": [
                    f"Implement {requirement.title} immediately",
                    f"Conduct risk assessment for {requirement.requirement_id}",
                    "Develop remediation plan with timeline",
                ],
            }

    async def generate_compliance_report(
        self,
        reporting_period_days: int = 90,
        include_frameworks: Optional[List[RegulatoryFramework]] = None,
    ) -> ComplianceReport:
        """Generate comprehensive compliance report."""

        report_id = f"report_{uuid.uuid4().hex[:12]}"
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=reporting_period_days)

        frameworks_to_include = include_frameworks or list(self.active_frameworks)

        # Collect recent assessments
        recent_assessments = {}
        overall_scores = []
        high_risk_items = []
        mitigation_plans = []

        for framework in frameworks_to_include:
            # Get most recent assessment for each framework
            framework_assessments = [
                assessment
                for assessment in self.assessments.values()
                if assessment.framework == framework
                and assessment.assessed_at >= start_date
            ]

            if framework_assessments:
                latest_assessment = max(
                    framework_assessments, key=lambda a: a.assessed_at
                )
                recent_assessments[framework] = latest_assessment
                overall_scores.append(latest_assessment.score)

                # Collect high-risk items
                for finding in latest_assessment.critical_findings:
                    high_risk_items.append(
                        {
                            "framework": framework.value,
                            "finding": finding,
                            "assessment_id": latest_assessment.assessment_id,
                        }
                    )

                # Generate mitigation plans for non-compliant items
                if latest_assessment.status != ComplianceStatus.COMPLIANT:
                    mitigation_plans.append(
                        {
                            "framework": framework.value,
                            "status": latest_assessment.status.value,
                            "priority": latest_assessment.risk_level.value,
                            "recommendations": latest_assessment.recommendations[
                                :3
                            ],  # Top 3
                            "timeline": "30-90 days",
                        }
                    )

        # Calculate overall compliance status
        if overall_scores:
            overall_score = sum(overall_scores) / len(overall_scores)
            if overall_score >= 0.95:
                overall_status = ComplianceStatus.COMPLIANT
            elif overall_score >= 0.75:
                overall_status = ComplianceStatus.PARTIAL_COMPLIANCE
            else:
                overall_status = ComplianceStatus.NON_COMPLIANT
        else:
            overall_score = 0.0
            overall_status = ComplianceStatus.UNDER_REVIEW

        # Generate improvement recommendations
        improvement_recommendations = [
            "Conduct regular compliance training for all team members",
            "Implement automated compliance monitoring where possible",
            "Establish clear documentation standards and procedures",
            "Regular third-party compliance audits",
            "Develop incident response procedures for compliance violations",
        ]

        # Compliance trends (mock data)
        compliance_trends = {
            "score_trend": "improving",
            "critical_findings_trend": "decreasing",
            "framework_maturity": {
                framework.value: "mature"
                if framework in recent_assessments
                else "developing"
                for framework in frameworks_to_include
            },
        }

        report = ComplianceReport(
            report_id=report_id,
            generated_at=datetime.now(timezone.utc),
            reporting_period_start=start_date,
            reporting_period_end=end_date,
            overall_status=overall_status,
            overall_score=overall_score,
            framework_assessments=recent_assessments,
            high_risk_items=high_risk_items,
            mitigation_plans=mitigation_plans,
            compliance_trends=compliance_trends,
            improvement_recommendations=improvement_recommendations,
        )

        logger.info(
            f"Compliance report generated: {report_id} - Overall status: {overall_status.value}"
        )

        return report

    def get_compliance_status(self, system_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current compliance status."""

        if system_id:
            # Get status for specific system
            system_assessments = [
                assessment
                for assessment in self.assessments.values()
                if assessment.system_id == system_id
            ]

            if not system_assessments:
                return {
                    "system_id": system_id,
                    "status": "no_assessments",
                    "frameworks": [],
                }

            # Get latest assessment per framework
            latest_by_framework = {}
            for assessment in system_assessments:
                if (
                    assessment.framework not in latest_by_framework
                    or assessment.assessed_at
                    > latest_by_framework[assessment.framework].assessed_at
                ):
                    latest_by_framework[assessment.framework] = assessment

            return {
                "system_id": system_id,
                "status": "assessed",
                "frameworks": [
                    {
                        "framework": framework.value,
                        "status": assessment.status.value,
                        "score": assessment.score,
                        "last_assessed": assessment.assessed_at.isoformat(),
                        "next_assessment_due": assessment.next_assessment_due.isoformat()
                        if assessment.next_assessment_due
                        else None,
                        "risk_level": assessment.risk_level.value,
                        "critical_findings": len(assessment.critical_findings),
                    }
                    for framework, assessment in latest_by_framework.items()
                ],
            }
        else:
            # Get overall compliance status
            framework_status = {}

            for framework in self.active_frameworks:
                framework_assessments = [
                    assessment
                    for assessment in self.assessments.values()
                    if assessment.framework == framework
                ]

                if framework_assessments:
                    latest = max(framework_assessments, key=lambda a: a.assessed_at)
                    framework_status[framework.value] = {
                        "status": latest.status.value,
                        "score": latest.score,
                        "last_assessed": latest.assessed_at.isoformat(),
                        "systems_assessed": len(
                            set(a.system_id for a in framework_assessments)
                        ),
                    }
                else:
                    framework_status[framework.value] = {
                        "status": "not_assessed",
                        "score": 0.0,
                        "systems_assessed": 0,
                    }

            return {
                "overall_status": "active",
                "active_frameworks": len(self.active_frameworks),
                "total_assessments": len(self.assessments),
                "framework_status": framework_status,
            }

    def get_compliance_requirements(
        self, framework: RegulatoryFramework
    ) -> List[Dict[str, Any]]:
        """Get compliance requirements for a specific framework."""

        if framework not in self.requirements:
            return []

        return [
            {
                "requirement_id": req.requirement_id,
                "title": req.title,
                "description": req.description,
                "mandatory": req.mandatory,
                "risk_level": req.risk_level.value,
                "verification_methods": req.verification_methods,
                "documentation_required": req.documentation_required,
            }
            for req in self.requirements[framework]
        ]

    async def schedule_assessment(
        self,
        framework: RegulatoryFramework,
        system_id: str,
        scheduled_date: datetime,
        assessor_id: str = "system",
    ) -> str:
        """Schedule a compliance assessment."""

        schedule_id = f"schedule_{uuid.uuid4().hex[:12]}"

        # In production, this would integrate with a scheduling system
        logger.info(
            f"Scheduled compliance assessment: {schedule_id} for {framework.value} on {scheduled_date}"
        )

        return schedule_id


# Factory function
def create_regulatory_compliance_framework() -> RegulatoryComplianceFramework:
    """Create a regulatory compliance framework instance."""
    return RegulatoryComplianceFramework()


# Example usage
if __name__ == "__main__":
    import asyncio

    async def demo_compliance_framework():
        """Demonstrate the regulatory compliance framework."""

        framework = create_regulatory_compliance_framework()

        print("🏛️ Regulatory Compliance Framework Demo")

        # Check overall status
        status = framework.get_compliance_status()
        print(f"\n📊 Overall Status:")
        print(f"   Active Frameworks: {status['active_frameworks']}")
        print(f"   Total Assessments: {status['total_assessments']}")

        # Get GDPR requirements
        gdpr_reqs = framework.get_compliance_requirements(RegulatoryFramework.GDPR)
        print(f"\n📋 GDPR Requirements: {len(gdpr_reqs)}")
        for req in gdpr_reqs[:2]:  # Show first 2
            print(f"   {req['requirement_id']}: {req['title']}")

        # Conduct compliance assessment
        print("\n🔍 Conducting GDPR Assessment...")
        assessment = await framework.conduct_compliance_assessment(
            RegulatoryFramework.GDPR, "uatp_capsule_engine", "compliance_officer"
        )
        print(f"   Status: {assessment.status.value}")
        print(f"   Score: {assessment.score:.1%}")
        print(
            f"   Requirements Met: {assessment.requirements_met}/{assessment.requirements_total}"
        )

        # Generate compliance report
        print("\n📄 Generating Compliance Report...")
        report = await framework.generate_compliance_report(90)
        print(f"   Report ID: {report.report_id}")
        print(f"   Overall Status: {report.overall_status.value}")
        print(f"   Overall Score: {report.overall_score:.1%}")
        print(f"   High Risk Items: {len(report.high_risk_items)}")

        print("\n✅ Compliance framework demo completed!")

    asyncio.run(demo_compliance_framework())
