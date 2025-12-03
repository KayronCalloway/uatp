"""
Compliance Reporting Engine
===========================

Automated compliance report generation supporting SOX, GDPR, HIPAA, ISO 27001
and other regulatory frameworks with real-time monitoring and alerting.
"""

import json
import logging
import uuid
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import csv
import io
import base64

from pydantic import BaseModel, Field
import jinja2
from weasyprint import HTML, CSS
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Supported report formats."""

    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    XML = "xml"


class ReportFrequency(Enum):
    """Report generation frequencies."""

    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    ON_DEMAND = "on_demand"


class ComplianceStatus(Enum):
    """Compliance status levels."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNDER_REVIEW = "under_review"
    NOT_ASSESSED = "not_assessed"


@dataclass
class ReportTemplate:
    """Compliance report template definition."""

    template_id: str
    name: str
    description: str
    framework_id: str
    sections: List[Dict[str, Any]]
    format_settings: Dict[str, Any] = field(default_factory=dict)
    styling: Dict[str, Any] = field(default_factory=dict)
    data_sources: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)


@dataclass
class ComplianceMetric:
    """Individual compliance metric."""

    metric_id: str
    name: str
    description: str
    value: float
    target: float
    unit: str
    status: ComplianceStatus
    last_updated: datetime
    trend: str  # increasing, decreasing, stable
    risk_level: str  # low, medium, high, critical


class ComplianceReport(BaseModel):
    """Generated compliance report."""

    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_id: str
    framework_id: str
    report_name: str
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    reporting_period: Dict[str, datetime]
    generated_by: str
    organization_id: str
    format: ReportFormat
    status: str = "completed"
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    executive_summary: Dict[str, Any] = Field(default_factory=dict)
    detailed_findings: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: List[ComplianceMetric] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    compliance_score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ViolationReport(BaseModel):
    """Policy violation report."""

    violation_id: str
    policy_id: str
    rule_id: str
    severity: str
    description: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    status: str  # open, resolved, dismissed
    affected_users: List[str] = Field(default_factory=list)
    affected_systems: List[str] = Field(default_factory=list)
    remediation_actions: List[str] = Field(default_factory=list)
    business_impact: Optional[str] = None
    root_cause: Optional[str] = None


class ComplianceReportingEngine:
    """Main compliance reporting engine."""

    def __init__(self, governance_system=None, data_sources=None):
        self.governance_system = governance_system
        self.data_sources = data_sources or {}

        # Report templates
        self.templates: Dict[str, ReportTemplate] = {}

        # Generated reports
        self.reports: Dict[str, ComplianceReport] = {}

        # Scheduled reports
        self.scheduled_reports: Dict[str, Dict[str, Any]] = {}

        # Report cache
        self.report_cache: Dict[str, Any] = {}

        # Initialize Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.DictLoader({}),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )

        # Initialize default templates
        self._initialize_default_templates()

        # Metrics collectors
        self.metric_collectors = {
            "gdpr": GDPRMetricsCollector(),
            "sox": SOXMetricsCollector(),
            "hipaa": HIPAAMetricsCollector(),
            "iso27001": ISO27001MetricsCollector(),
        }

    def _initialize_default_templates(self):
        """Initialize default report templates for each framework."""

        # GDPR Report Template
        gdpr_template = ReportTemplate(
            template_id="gdpr_comprehensive",
            name="GDPR Comprehensive Compliance Report",
            description="Complete GDPR compliance assessment report",
            framework_id="gdpr_2018",
            sections=[
                {
                    "section_id": "executive_summary",
                    "title": "Executive Summary",
                    "content_type": "summary",
                    "required": True,
                },
                {
                    "section_id": "compliance_overview",
                    "title": "Compliance Overview",
                    "content_type": "metrics_dashboard",
                    "required": True,
                },
                {
                    "section_id": "data_processing_activities",
                    "title": "Data Processing Activities",
                    "content_type": "detailed_analysis",
                    "required": True,
                },
                {
                    "section_id": "consent_management",
                    "title": "Consent Management",
                    "content_type": "metrics_table",
                    "required": True,
                },
                {
                    "section_id": "data_subject_rights",
                    "title": "Data Subject Rights",
                    "content_type": "detailed_analysis",
                    "required": True,
                },
                {
                    "section_id": "security_measures",
                    "title": "Technical and Organizational Measures",
                    "content_type": "security_assessment",
                    "required": True,
                },
                {
                    "section_id": "violations_incidents",
                    "title": "Violations and Incidents",
                    "content_type": "violations_table",
                    "required": True,
                },
                {
                    "section_id": "recommendations",
                    "title": "Recommendations",
                    "content_type": "action_items",
                    "required": True,
                },
            ],
            data_sources=[
                "audit_events",
                "policy_violations",
                "consent_records",
                "data_processing_records",
            ],
            required_permissions=["compliance.view", "gdpr.report"],
        )

        # SOX Report Template
        sox_template = ReportTemplate(
            template_id="sox_controls_assessment",
            name="SOX Internal Controls Assessment",
            description="Sarbanes-Oxley internal controls effectiveness report",
            framework_id="sox_2002",
            sections=[
                {
                    "section_id": "executive_summary",
                    "title": "Executive Summary",
                    "content_type": "summary",
                    "required": True,
                },
                {
                    "section_id": "control_environment",
                    "title": "Control Environment Assessment",
                    "content_type": "detailed_analysis",
                    "required": True,
                },
                {
                    "section_id": "financial_reporting_controls",
                    "title": "Financial Reporting Controls",
                    "content_type": "controls_matrix",
                    "required": True,
                },
                {
                    "section_id": "deficiencies",
                    "title": "Control Deficiencies",
                    "content_type": "deficiencies_table",
                    "required": True,
                },
                {
                    "section_id": "testing_results",
                    "title": "Control Testing Results",
                    "content_type": "testing_summary",
                    "required": True,
                },
                {
                    "section_id": "management_assertions",
                    "title": "Management Assertions",
                    "content_type": "assertions_table",
                    "required": True,
                },
                {
                    "section_id": "remediation_plan",
                    "title": "Remediation Plan",
                    "content_type": "action_items",
                    "required": True,
                },
            ],
            data_sources=[
                "financial_controls",
                "audit_events",
                "control_testing",
                "deficiencies",
            ],
            required_permissions=["compliance.view", "sox.report", "financial.view"],
        )

        # HIPAA Report Template
        hipaa_template = ReportTemplate(
            template_id="hipaa_security_assessment",
            name="HIPAA Security and Privacy Assessment",
            description="HIPAA compliance assessment for healthcare data protection",
            framework_id="hipaa_1996",
            sections=[
                {
                    "section_id": "executive_summary",
                    "title": "Executive Summary",
                    "content_type": "summary",
                    "required": True,
                },
                {
                    "section_id": "phi_inventory",
                    "title": "Protected Health Information Inventory",
                    "content_type": "data_inventory",
                    "required": True,
                },
                {
                    "section_id": "administrative_safeguards",
                    "title": "Administrative Safeguards",
                    "content_type": "safeguards_assessment",
                    "required": True,
                },
                {
                    "section_id": "physical_safeguards",
                    "title": "Physical Safeguards",
                    "content_type": "safeguards_assessment",
                    "required": True,
                },
                {
                    "section_id": "technical_safeguards",
                    "title": "Technical Safeguards",
                    "content_type": "safeguards_assessment",
                    "required": True,
                },
                {
                    "section_id": "risk_assessment",
                    "title": "Risk Assessment",
                    "content_type": "risk_matrix",
                    "required": True,
                },
                {
                    "section_id": "breach_incidents",
                    "title": "Breach Incidents",
                    "content_type": "incidents_table",
                    "required": True,
                },
                {
                    "section_id": "business_associate_agreements",
                    "title": "Business Associate Agreements",
                    "content_type": "agreements_table",
                    "required": True,
                },
            ],
            data_sources=[
                "phi_access_logs",
                "security_incidents",
                "risk_assessments",
                "baa_records",
            ],
            required_permissions=["compliance.view", "hipaa.report", "phi.view"],
        )

        # ISO 27001 Report Template
        iso27001_template = ReportTemplate(
            template_id="iso27001_isms_assessment",
            name="ISO 27001 ISMS Assessment Report",
            description="Information Security Management System assessment report",
            framework_id="iso27001_2013",
            sections=[
                {
                    "section_id": "executive_summary",
                    "title": "Executive Summary",
                    "content_type": "summary",
                    "required": True,
                },
                {
                    "section_id": "isms_scope",
                    "title": "ISMS Scope and Context",
                    "content_type": "scope_definition",
                    "required": True,
                },
                {
                    "section_id": "risk_management",
                    "title": "Information Security Risk Management",
                    "content_type": "risk_assessment",
                    "required": True,
                },
                {
                    "section_id": "controls_implementation",
                    "title": "Security Controls Implementation",
                    "content_type": "controls_matrix",
                    "required": True,
                },
                {
                    "section_id": "performance_monitoring",
                    "title": "Performance Monitoring and Measurement",
                    "content_type": "metrics_dashboard",
                    "required": True,
                },
                {
                    "section_id": "internal_audit",
                    "title": "Internal Audit Results",
                    "content_type": "audit_findings",
                    "required": True,
                },
                {
                    "section_id": "management_review",
                    "title": "Management Review",
                    "content_type": "review_summary",
                    "required": True,
                },
                {
                    "section_id": "improvement_opportunities",
                    "title": "Continual Improvement",
                    "content_type": "improvement_plan",
                    "required": True,
                },
            ],
            data_sources=[
                "security_controls",
                "risk_register",
                "audit_findings",
                "incident_reports",
            ],
            required_permissions=[
                "compliance.view",
                "iso27001.report",
                "security.view",
            ],
        )

        self.templates.update(
            {
                "gdpr_comprehensive": gdpr_template,
                "sox_controls_assessment": sox_template,
                "hipaa_security_assessment": hipaa_template,
                "iso27001_isms_assessment": iso27001_template,
            }
        )

    async def generate_report(
        self,
        template_id: str,
        reporting_period: Dict[str, datetime],
        format: ReportFormat = ReportFormat.PDF,
        generated_by: str = "system",
        organization_id: str = "default",
        custom_parameters: Optional[Dict[str, Any]] = None,
    ) -> ComplianceReport:
        """Generate compliance report using specified template."""

        try:
            template = self.templates.get(template_id)
            if not template:
                raise ValueError(f"Report template not found: {template_id}")

            logger.info(
                f"Generating report {template.name} for period {reporting_period}"
            )

            # Collect data for report
            report_data = await self._collect_report_data(
                template, reporting_period, custom_parameters
            )

            # Calculate compliance metrics
            metrics = await self._calculate_compliance_metrics(
                template.framework_id, report_data
            )

            # Generate executive summary
            executive_summary = await self._generate_executive_summary(
                template, report_data, metrics
            )

            # Generate detailed findings
            detailed_findings = await self._generate_detailed_findings(
                template, report_data
            )

            # Calculate overall compliance score
            compliance_score = self._calculate_overall_score(metrics)

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                template.framework_id, report_data, metrics
            )

            # Create report object
            report = ComplianceReport(
                template_id=template_id,
                framework_id=template.framework_id,
                report_name=template.name,
                reporting_period=reporting_period,
                generated_by=generated_by,
                organization_id=organization_id,
                format=format,
                executive_summary=executive_summary,
                detailed_findings=detailed_findings,
                metrics=metrics,
                recommendations=recommendations,
                compliance_score=compliance_score,
                metadata={
                    "template_version": "1.0",
                    "data_sources": template.data_sources,
                    "generation_parameters": custom_parameters or {},
                },
            )

            # Generate report file
            file_path = await self._generate_report_file(report, template, report_data)
            report.file_path = file_path

            if file_path:
                report.file_size = Path(file_path).stat().st_size

            # Store report
            self.reports[report.report_id] = report

            logger.info(f"Report generated successfully: {report.report_id}")
            return report

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise

    async def _collect_report_data(
        self,
        template: ReportTemplate,
        reporting_period: Dict[str, datetime],
        custom_parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Collect data from various sources for report generation."""

        report_data = {
            "reporting_period": reporting_period,
            "template": template,
            "custom_parameters": custom_parameters or {},
        }

        start_date = reporting_period["start_date"]
        end_date = reporting_period["end_date"]

        # Collect data from governance system
        if self.governance_system:
            # Get audit events
            audit_events = [
                event
                for event in self.governance_system.audit_events
                if start_date <= event.timestamp <= end_date
            ]
            report_data["audit_events"] = audit_events

            # Get policy violations
            violations = [
                violation
                for violation in self.governance_system.violations
                if start_date <= violation.detected_at <= end_date
            ]
            report_data["violations"] = violations

            # Get active policies
            report_data["active_policies"] = [
                policy
                for policy in self.governance_system.policies.values()
                if policy.status.value == "active"
            ]

            # Get compliance frameworks
            framework = self.governance_system.compliance_frameworks.get(
                template.framework_id
            )
            if framework:
                report_data["framework"] = framework

        # Collect from external data sources
        for data_source in template.data_sources:
            if data_source in self.data_sources:
                collector = self.data_sources[data_source]
                source_data = await collector.collect_data(start_date, end_date)
                report_data[data_source] = source_data

        # Framework-specific data collection
        if template.framework_id in self.metric_collectors:
            collector = self.metric_collectors[template.framework_id]
            framework_data = await collector.collect_metrics(
                start_date, end_date, report_data
            )
            report_data.update(framework_data)

        return report_data

    async def _calculate_compliance_metrics(
        self, framework_id: str, report_data: Dict[str, Any]
    ) -> List[ComplianceMetric]:
        """Calculate compliance metrics for the framework."""

        metrics = []

        if framework_id in self.metric_collectors:
            collector = self.metric_collectors[framework_id]
            metrics = await collector.calculate_metrics(report_data)

        return metrics

    async def _generate_executive_summary(
        self,
        template: ReportTemplate,
        report_data: Dict[str, Any],
        metrics: List[ComplianceMetric],
    ) -> Dict[str, Any]:
        """Generate executive summary section."""

        violations = report_data.get("violations", [])
        audit_events = report_data.get("audit_events", [])

        # Calculate key statistics
        total_violations = len(violations)
        critical_violations = len([v for v in violations if v.severity == "critical"])
        resolved_violations = len([v for v in violations if v.resolved_at])

        # Calculate compliance score
        compliance_score = self._calculate_overall_score(metrics)

        # Determine overall status
        if compliance_score >= 95:
            overall_status = "Fully Compliant"
        elif compliance_score >= 80:
            overall_status = "Largely Compliant"
        elif compliance_score >= 60:
            overall_status = "Partially Compliant"
        else:
            overall_status = "Non-Compliant"

        return {
            "overall_status": overall_status,
            "compliance_score": compliance_score,
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "resolved_violations": resolved_violations,
            "resolution_rate": (resolved_violations / max(1, total_violations)) * 100,
            "total_audit_events": len(audit_events),
            "key_findings": self._extract_key_findings(violations, metrics),
            "top_risks": self._identify_top_risks(violations, metrics),
            "improvement_areas": self._identify_improvement_areas(metrics),
        }

    async def _generate_detailed_findings(
        self, template: ReportTemplate, report_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate detailed findings for each section."""

        findings = []

        for section in template.sections:
            section_data = await self._generate_section_data(section, report_data)
            findings.append(
                {
                    "section_id": section["section_id"],
                    "title": section["title"],
                    "content_type": section["content_type"],
                    "data": section_data,
                    "status": self._assess_section_status(section_data),
                    "recommendations": self._generate_section_recommendations(
                        section, section_data
                    ),
                }
            )

        return findings

    async def _generate_section_data(
        self, section: Dict[str, Any], report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate data for a specific report section."""

        content_type = section["content_type"]

        if content_type == "metrics_dashboard":
            return self._generate_metrics_dashboard(report_data)
        elif content_type == "violations_table":
            return self._generate_violations_table(report_data)
        elif content_type == "detailed_analysis":
            return self._generate_detailed_analysis(section, report_data)
        elif content_type == "controls_matrix":
            return self._generate_controls_matrix(report_data)
        elif content_type == "risk_assessment":
            return self._generate_risk_assessment(report_data)
        else:
            return {"message": f"Content type {content_type} not implemented"}

    def _generate_metrics_dashboard(
        self, report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate metrics dashboard data."""

        violations = report_data.get("violations", [])
        audit_events = report_data.get("audit_events", [])

        return {
            "total_events": len(audit_events),
            "total_violations": len(violations),
            "events_by_type": self._group_by_field(audit_events, "event_type"),
            "violations_by_severity": self._group_by_field(violations, "severity"),
            "trends": self._calculate_trends(audit_events, violations),
            "top_users": self._get_top_users(audit_events),
            "top_resources": self._get_top_resources(audit_events),
        }

    def _generate_violations_table(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate violations table data."""

        violations = report_data.get("violations", [])

        violations_data = []
        for violation in violations:
            violations_data.append(
                {
                    "id": violation.violation_id,
                    "policy": violation.policy_id,
                    "rule": violation.rule_id,
                    "severity": violation.severity.value
                    if hasattr(violation.severity, "value")
                    else violation.severity,
                    "description": violation.description,
                    "detected_at": violation.detected_at.isoformat()
                    if hasattr(violation.detected_at, "isoformat")
                    else str(violation.detected_at),
                    "status": "Resolved" if violation.resolved_at else "Open",
                    "user_id": violation.user_id,
                    "resource_id": violation.resource_id,
                }
            )

        return {
            "violations": violations_data,
            "summary": {
                "total": len(violations),
                "open": len([v for v in violations if not v.resolved_at]),
                "resolved": len([v for v in violations if v.resolved_at]),
                "by_severity": self._group_by_field(violations, "severity"),
            },
        }

    def _generate_detailed_analysis(
        self, section: Dict[str, Any], report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed analysis for a section."""

        section_id = section["section_id"]

        if section_id == "data_processing_activities":
            return self._analyze_data_processing(report_data)
        elif section_id == "consent_management":
            return self._analyze_consent_management(report_data)
        elif section_id == "data_subject_rights":
            return self._analyze_data_subject_rights(report_data)
        else:
            return {"analysis": f"Detailed analysis for {section_id}"}

    def _analyze_data_processing(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data processing activities."""

        audit_events = report_data.get("audit_events", [])

        processing_events = [
            event for event in audit_events if "data_processing" in event.event_type
        ]

        return {
            "total_processing_activities": len(processing_events),
            "processing_by_type": self._group_by_field(processing_events, "event_type"),
            "data_categories": self._extract_data_categories(processing_events),
            "legal_bases": self._extract_legal_bases(processing_events),
            "retention_compliance": self._assess_retention_compliance(
                processing_events
            ),
        }

    def _analyze_consent_management(
        self, report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze consent management effectiveness."""

        audit_events = report_data.get("audit_events", [])

        consent_events = [
            event
            for event in audit_events
            if event.event_type
            in ["consent_granted", "consent_revoked", "consent_updated"]
        ]

        return {
            "total_consent_events": len(consent_events),
            "consent_granted": len(
                [e for e in consent_events if e.event_type == "consent_granted"]
            ),
            "consent_revoked": len(
                [e for e in consent_events if e.event_type == "consent_revoked"]
            ),
            "consent_updated": len(
                [e for e in consent_events if e.event_type == "consent_updated"]
            ),
            "consent_rate": self._calculate_consent_rate(consent_events),
            "granular_consent": self._analyze_granular_consent(consent_events),
        }

    def _analyze_data_subject_rights(
        self, report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze data subject rights compliance."""

        audit_events = report_data.get("audit_events", [])

        rights_events = [
            event
            for event in audit_events
            if event.event_type.startswith("data_subject_")
        ]

        return {
            "total_requests": len(rights_events),
            "requests_by_type": self._group_by_field(rights_events, "event_type"),
            "response_times": self._calculate_response_times(rights_events),
            "completion_rate": self._calculate_completion_rate(rights_events),
            "escalations": self._count_escalations(rights_events),
        }

    def _generate_controls_matrix(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate controls effectiveness matrix."""

        # This would analyze control effectiveness
        return {
            "controls": [
                {
                    "control_id": "AC-001",
                    "name": "Access Control Policy",
                    "status": "Effective",
                    "effectiveness_score": 95,
                    "last_tested": "2024-01-15",
                    "deficiencies": [],
                },
                {
                    "control_id": "AC-002",
                    "name": "User Access Management",
                    "status": "Needs Improvement",
                    "effectiveness_score": 78,
                    "last_tested": "2024-01-10",
                    "deficiencies": ["Manual provisioning process"],
                },
            ],
            "overall_effectiveness": 86.5,
            "controls_by_status": {
                "effective": 15,
                "needs_improvement": 3,
                "ineffective": 1,
            },
        }

    def _generate_risk_assessment(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk assessment data."""

        violations = report_data.get("violations", [])

        # Calculate risk scores
        high_risk_violations = [
            v for v in violations if v.severity in ["high", "critical"]
        ]

        return {
            "overall_risk_score": self._calculate_risk_score(violations),
            "risk_categories": {
                "data_protection": 75,
                "access_control": 60,
                "security": 85,
                "operational": 70,
            },
            "top_risks": [
                {
                    "risk_id": "RISK-001",
                    "description": "Unauthorized data access",
                    "likelihood": "Medium",
                    "impact": "High",
                    "risk_score": 7.5,
                    "mitigation_status": "In Progress",
                }
            ],
            "risk_trends": "Improving",
            "mitigation_effectiveness": 82,
        }

    def _calculate_overall_score(self, metrics: List[ComplianceMetric]) -> float:
        """Calculate overall compliance score."""

        if not metrics:
            return 0.0

        total_score = sum(
            (metric.value / metric.target * 100) if metric.target > 0 else 0
            for metric in metrics
        )

        return min(100.0, total_score / len(metrics))

    async def _generate_recommendations(
        self,
        framework_id: str,
        report_data: Dict[str, Any],
        metrics: List[ComplianceMetric],
    ) -> List[str]:
        """Generate compliance improvement recommendations."""

        recommendations = []

        violations = report_data.get("violations", [])

        # Critical violations
        critical_violations = [v for v in violations if v.severity == "critical"]
        if critical_violations:
            recommendations.append(
                f"Immediately address {len(critical_violations)} critical violations to reduce compliance risk"
            )

        # Low-performing metrics
        low_metrics = [m for m in metrics if m.value < m.target * 0.8]
        for metric in low_metrics:
            recommendations.append(
                f"Improve {metric.name} - currently at {metric.value:.1f}% vs target {metric.target:.1f}%"
            )

        # Framework-specific recommendations
        if framework_id == "gdpr_2018":
            recommendations.extend(
                [
                    "Implement automated data subject request processing",
                    "Enhance consent management granularity",
                    "Conduct privacy impact assessments for new processing activities",
                ]
            )
        elif framework_id == "sox_2002":
            recommendations.extend(
                [
                    "Strengthen financial reporting controls",
                    "Implement continuous monitoring for key controls",
                    "Enhance segregation of duties in financial processes",
                ]
            )
        elif framework_id == "hipaa_1996":
            recommendations.extend(
                [
                    "Implement role-based access controls for PHI",
                    "Enhance audit logging for all PHI access",
                    "Conduct regular security risk assessments",
                ]
            )

        return recommendations

    async def _generate_report_file(
        self,
        report: ComplianceReport,
        template: ReportTemplate,
        report_data: Dict[str, Any],
    ) -> Optional[str]:
        """Generate physical report file in requested format."""

        try:
            if report.format == ReportFormat.PDF:
                return await self._generate_pdf_report(report, template, report_data)
            elif report.format == ReportFormat.HTML:
                return await self._generate_html_report(report, template, report_data)
            elif report.format == ReportFormat.JSON:
                return await self._generate_json_report(report, template, report_data)
            elif report.format == ReportFormat.CSV:
                return await self._generate_csv_report(report, template, report_data)
            else:
                logger.warning(f"Unsupported report format: {report.format}")
                return None

        except Exception as e:
            logger.error(f"Failed to generate report file: {e}")
            return None

    async def _generate_pdf_report(
        self,
        report: ComplianceReport,
        template: ReportTemplate,
        report_data: Dict[str, Any],
    ) -> str:
        """Generate PDF report."""

        # Generate HTML first
        html_content = await self._create_html_content(report, template, report_data)

        # Convert to PDF
        file_path = f"reports/{report.report_id}.pdf"
        Path("reports").mkdir(exist_ok=True)

        HTML(string=html_content).write_pdf(file_path)

        return file_path

    async def _generate_html_report(
        self,
        report: ComplianceReport,
        template: ReportTemplate,
        report_data: Dict[str, Any],
    ) -> str:
        """Generate HTML report."""

        html_content = await self._create_html_content(report, template, report_data)

        file_path = f"reports/{report.report_id}.html"
        Path("reports").mkdir(exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return file_path

    async def _create_html_content(
        self,
        report: ComplianceReport,
        template: ReportTemplate,
        report_data: Dict[str, Any],
    ) -> str:
        """Create HTML content for report."""

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ report.report_name }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 30px; }
                .section { margin-bottom: 30px; }
                .metric { display: inline-block; margin: 10px; padding: 15px; border: 1px solid #ddd; }
                .violation { background-color: #ffe6e6; padding: 10px; margin: 5px 0; border-left: 5px solid #ff0000; }
                .compliant { color: green; }
                .non-compliant { color: red; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ report.report_name }}</h1>
                <p>Framework: {{ report.framework_id }}</p>
                <p>Period: {{ report.reporting_period.start_date.strftime('%Y-%m-%d') }} to {{ report.reporting_period.end_date.strftime('%Y-%m-%d') }}</p>
                <p>Generated: {{ report.generation_timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                <p>Score: <span class="{% if report.compliance_score >= 80 %}compliant{% else %}non-compliant{% endif %}">{{ "%.1f"|format(report.compliance_score) }}%</span></p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <p>Overall Status: {{ report.executive_summary.overall_status }}</p>
                <p>Total Violations: {{ report.executive_summary.total_violations }}</p>
                <p>Critical Violations: {{ report.executive_summary.critical_violations }}</p>
            </div>
            
            <div class="section">
                <h2>Compliance Metrics</h2>
                {% for metric in report.metrics %}
                <div class="metric">
                    <h4>{{ metric.name }}</h4>
                    <p>Value: {{ "%.1f"|format(metric.value) }} {{ metric.unit }}</p>
                    <p>Target: {{ "%.1f"|format(metric.target) }} {{ metric.unit }}</p>
                    <p>Status: {{ metric.status.value }}</p>
                </div>
                {% endfor %}
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
                <ul>
                {% for recommendation in report.recommendations %}
                    <li>{{ recommendation }}</li>
                {% endfor %}
                </ul>
            </div>
        </body>
        </html>
        """

        template_obj = self.jinja_env.from_string(html_template)
        return template_obj.render(report=report, report_data=report_data)

    async def _generate_json_report(
        self,
        report: ComplianceReport,
        template: ReportTemplate,
        report_data: Dict[str, Any],
    ) -> str:
        """Generate JSON report."""

        file_path = f"reports/{report.report_id}.json"
        Path("reports").mkdir(exist_ok=True)

        # Convert report to dict and handle datetime serialization
        report_dict = report.dict()

        # Custom JSON encoder for datetime objects
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, "dict"):
                return obj.dict()
            elif hasattr(obj, "value"):
                return obj.value
            return str(obj)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, default=json_serializer)

        return file_path

    async def _generate_csv_report(
        self,
        report: ComplianceReport,
        template: ReportTemplate,
        report_data: Dict[str, Any],
    ) -> str:
        """Generate CSV report with key metrics and violations."""

        file_path = f"reports/{report.report_id}.csv"
        Path("reports").mkdir(exist_ok=True)

        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Report header
            writer.writerow(["Report Name", report.report_name])
            writer.writerow(["Framework", report.framework_id])
            writer.writerow(["Period Start", report.reporting_period["start_date"]])
            writer.writerow(["Period End", report.reporting_period["end_date"]])
            writer.writerow(["Compliance Score", f"{report.compliance_score:.1f}%"])
            writer.writerow([])

            # Metrics section
            writer.writerow(["Compliance Metrics"])
            writer.writerow(["Metric", "Value", "Target", "Unit", "Status"])
            for metric in report.metrics:
                writer.writerow(
                    [
                        metric.name,
                        metric.value,
                        metric.target,
                        metric.unit,
                        metric.status.value
                        if hasattr(metric.status, "value")
                        else metric.status,
                    ]
                )

            writer.writerow([])

            # Violations section if available
            violations = report_data.get("violations", [])
            if violations:
                writer.writerow(["Policy Violations"])
                writer.writerow(
                    [
                        "ID",
                        "Policy",
                        "Rule",
                        "Severity",
                        "Description",
                        "Detected",
                        "Status",
                    ]
                )
                for violation in violations:
                    writer.writerow(
                        [
                            violation.violation_id,
                            violation.policy_id,
                            violation.rule_id,
                            violation.severity.value
                            if hasattr(violation.severity, "value")
                            else violation.severity,
                            violation.description,
                            violation.detected_at,
                            "Resolved" if violation.resolved_at else "Open",
                        ]
                    )

        return file_path

    # Helper methods
    def _group_by_field(self, items: List[Any], field: str) -> Dict[str, int]:
        """Group items by field value."""
        groups = {}
        for item in items:
            if hasattr(item, field):
                value = getattr(item, field)
                if hasattr(value, "value"):
                    value = value.value
                groups[str(value)] = groups.get(str(value), 0) + 1
            elif isinstance(item, dict):
                value = item.get(field, "Unknown")
                groups[str(value)] = groups.get(str(value), 0) + 1
        return groups

    def _extract_key_findings(
        self, violations: List[Any], metrics: List[ComplianceMetric]
    ) -> List[str]:
        """Extract key findings from violations and metrics."""
        findings = []

        if violations:
            critical_count = len(
                [v for v in violations if getattr(v, "severity", None) == "critical"]
            )
            if critical_count > 0:
                findings.append(
                    f"{critical_count} critical policy violations require immediate attention"
                )

        poor_metrics = [m for m in metrics if m.value < m.target * 0.7]
        if poor_metrics:
            findings.append(
                f"{len(poor_metrics)} compliance metrics are significantly below target"
            )

        return findings

    def _identify_top_risks(
        self, violations: List[Any], metrics: List[ComplianceMetric]
    ) -> List[str]:
        """Identify top compliance risks."""
        risks = []

        # Risk from violations
        violation_types = self._group_by_field(violations, "violation_type")
        for violation_type, count in sorted(
            violation_types.items(), key=lambda x: x[1], reverse=True
        )[:3]:
            risks.append(
                f"High frequency of {violation_type} violations ({count} incidents)"
            )

        return risks

    def _identify_improvement_areas(self, metrics: List[ComplianceMetric]) -> List[str]:
        """Identify areas for improvement."""
        areas = []

        declining_metrics = [m for m in metrics if m.trend == "decreasing"]
        for metric in declining_metrics:
            areas.append(f"{metric.name} showing declining trend")

        return areas

    def _assess_section_status(self, section_data: Dict[str, Any]) -> str:
        """Assess status of a report section."""
        # Simple assessment logic
        if "violations" in section_data:
            violations = section_data["violations"]
            if isinstance(violations, list) and len(violations) > 0:
                return "Issues Identified"

        return "Compliant"

    def _generate_section_recommendations(
        self, section: Dict[str, Any], section_data: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for a section."""
        return [f"Review {section['title']} implementation"]

    def _calculate_trends(
        self, audit_events: List[Any], violations: List[Any]
    ) -> Dict[str, str]:
        """Calculate compliance trends."""
        return {"violations": "decreasing", "events": "stable", "overall": "improving"}

    def _get_top_users(self, audit_events: List[Any]) -> List[Dict[str, Any]]:
        """Get top users by activity."""
        user_counts = self._group_by_field(audit_events, "user_id")
        return [
            {"user_id": user, "event_count": count}
            for user, count in sorted(
                user_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]
        ]

    def _get_top_resources(self, audit_events: List[Any]) -> List[Dict[str, Any]]:
        """Get top resources by access."""
        resource_counts = self._group_by_field(audit_events, "resource_id")
        return [
            {"resource_id": resource, "access_count": count}
            for resource, count in sorted(
                resource_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]
        ]


# Framework-specific metric collectors
class GDPRMetricsCollector:
    """GDPR-specific metrics collector."""

    async def collect_metrics(
        self, start_date: datetime, end_date: datetime, report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect GDPR-specific metrics."""
        return {
            "gdpr_metrics": {
                "consent_requests": 150,
                "data_subject_requests": 25,
                "breach_notifications": 2,
                "privacy_assessments": 5,
            }
        }

    async def calculate_metrics(
        self, report_data: Dict[str, Any]
    ) -> List[ComplianceMetric]:
        """Calculate GDPR compliance metrics."""
        metrics = []

        audit_events = report_data.get("audit_events", [])

        # Consent management effectiveness
        consent_events = [e for e in audit_events if "consent" in e.event_type]
        consent_metric = ComplianceMetric(
            metric_id="gdpr_consent_management",
            name="Consent Management Effectiveness",
            description="Percentage of consent requests processed within required timeframe",
            value=95.0,
            target=98.0,
            unit="%",
            status=ComplianceStatus.COMPLIANT,
            last_updated=datetime.utcnow(),
            trend="stable",
            risk_level="low",
        )
        metrics.append(consent_metric)

        # Data subject rights response time
        dsr_events = [
            e for e in audit_events if e.event_type.startswith("data_subject_")
        ]
        dsr_metric = ComplianceMetric(
            metric_id="gdpr_dsr_response_time",
            name="Data Subject Request Response Time",
            description="Average response time for data subject requests",
            value=25.0,
            target=30.0,
            unit="days",
            status=ComplianceStatus.COMPLIANT,
            last_updated=datetime.utcnow(),
            trend="improving",
            risk_level="low",
        )
        metrics.append(dsr_metric)

        return metrics


class SOXMetricsCollector:
    """SOX-specific metrics collector."""

    async def collect_metrics(
        self, start_date: datetime, end_date: datetime, report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {"sox_metrics": {}}

    async def calculate_metrics(
        self, report_data: Dict[str, Any]
    ) -> List[ComplianceMetric]:
        return []


class HIPAAMetricsCollector:
    """HIPAA-specific metrics collector."""

    async def collect_metrics(
        self, start_date: datetime, end_date: datetime, report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {"hipaa_metrics": {}}

    async def calculate_metrics(
        self, report_data: Dict[str, Any]
    ) -> List[ComplianceMetric]:
        return []


class ISO27001MetricsCollector:
    """ISO 27001-specific metrics collector."""

    async def collect_metrics(
        self, start_date: datetime, end_date: datetime, report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {"iso27001_metrics": {}}

    async def calculate_metrics(
        self, report_data: Dict[str, Any]
    ) -> List[ComplianceMetric]:
        return []
