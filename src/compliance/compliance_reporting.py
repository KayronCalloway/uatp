"""
Automated Regulatory Reporting System
Comprehensive compliance reporting and regulatory submission automation
"""

import asyncio
import csv
import hashlib
import json
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from io import StringIO
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Types of regulatory reports"""

    GDPR_ARTICLE_30 = "gdpr_article_30"  # Records of Processing Activities
    GDPR_DPIA = "gdpr_dpia"  # Data Protection Impact Assessment
    SAR_FINCEN = "sar_fincen"  # Suspicious Activity Report to FinCEN
    CTR_FINCEN = "ctr_fincen"  # Currency Transaction Report
    KYC_AUDIT = "kyc_audit"  # KYC Compliance Audit Report
    AML_MONITORING = "aml_monitoring"  # AML Transaction Monitoring Report
    PCI_DSS_COMPLIANCE = "pci_dss_compliance"  # PCI DSS Compliance Report
    HIPAA_AUDIT = "hipaa_audit"  # HIPAA Compliance Audit
    ISO_27001_AUDIT = "iso_27001_audit"  # ISO 27001 Audit Report
    SOX_CONTROLS = "sox_controls"  # SOX Internal Controls Report
    DATA_BREACH_SUMMARY = "data_breach_summary"  # Data Breach Summary Report
    TRANSFER_IMPACT_ASSESSMENT = "transfer_impact_assessment"  # TIA Report


class ReportFormat(Enum):
    """Report output formats"""

    PDF = "pdf"
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    HTML = "html"
    XLSX = "xlsx"


class ReportStatus(Enum):
    """Report generation status"""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"


class ReportFrequency(Enum):
    """Report generation frequency"""

    ON_DEMAND = "on_demand"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    TRIGGERED = "triggered"


@dataclass
class ReportTemplate:
    """Report template configuration"""

    template_id: str
    template_name: str
    report_type: ReportType
    regulation_type: str

    # Template configuration
    data_sources: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)

    # Formatting
    default_format: ReportFormat = ReportFormat.PDF
    supported_formats: List[ReportFormat] = field(default_factory=list)

    # Validation
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    quality_checks: List[str] = field(default_factory=list)

    # Submission
    submission_endpoint: Optional[str] = None
    submission_method: str = "manual"  # manual, api, email, portal
    submission_auth: Dict[str, Any] = field(default_factory=dict)

    # Schedule
    default_frequency: ReportFrequency = ReportFrequency.ON_DEMAND
    generation_time: str = "09:00"  # HH:MM format
    retention_days: int = 2555  # 7 years default

    # Metadata
    created_by: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True


@dataclass
class ReportInstance:
    """Individual report instance"""

    report_id: str
    template_id: str
    report_type: ReportType

    # Generation details
    generated_at: datetime
    generated_by: str
    report_period_start: datetime
    report_period_end: datetime

    # Content
    report_format: ReportFormat
    report_data: Dict[str, Any] = field(default_factory=dict)
    report_content: Optional[str] = None
    report_file_path: Optional[str] = None

    # Status
    status: ReportStatus = ReportStatus.PENDING
    generation_started_at: Optional[datetime] = None
    generation_completed_at: Optional[datetime] = None
    generation_duration_seconds: float = 0.0

    # Validation
    validation_passed: bool = False
    validation_errors: List[str] = field(default_factory=list)
    quality_score: float = 0.0

    # Submission
    submitted_at: Optional[datetime] = None
    submission_reference: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    # Security
    report_hash: Optional[str] = None
    digital_signature: Optional[str] = None
    encryption_applied: bool = False

    # Metadata
    file_size_bytes: int = 0
    record_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportSchedule:
    """Scheduled report configuration"""

    schedule_id: str
    template_id: str
    schedule_name: str

    # Schedule configuration
    frequency: ReportFrequency
    generation_time: str  # HH:MM format
    timezone: str = "UTC"

    # Period configuration
    report_period_days: int = 30  # Days to include in each report
    overlap_days: int = 0  # Days to overlap between reports

    # Generation options
    auto_generate: bool = True
    auto_submit: bool = False
    auto_validate: bool = True

    # Recipients
    recipients: List[str] = field(default_factory=list)
    notification_channels: List[str] = field(
        default_factory=list
    )  # email, slack, webhook

    # Status
    is_active: bool = True
    last_generated: Optional[datetime] = None
    next_generation: Optional[datetime] = None

    # Error handling
    max_retries: int = 3
    retry_delay_minutes: int = 60
    failure_notification: bool = True

    # Metadata
    created_by: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RegulatorySubmission:
    """Regulatory authority submission record"""

    submission_id: str
    report_id: str
    authority: str

    # Submission details
    submission_method: str  # api, portal, email, postal
    submitted_at: datetime
    submitted_by: str

    # Tracking
    submission_reference: Optional[str] = None
    acknowledgment_received: bool = False
    acknowledgment_date: Optional[datetime] = None

    # Status
    submission_status: str = "submitted"  # submitted, processing, accepted, rejected
    status_message: Optional[str] = None

    # Follow-up
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class ComplianceReportingSystem:
    """Automated regulatory reporting system"""

    def __init__(self):
        self.report_templates: Dict[str, ReportTemplate] = {}
        self.report_instances: Dict[str, ReportInstance] = {}
        self.report_schedules: Dict[str, ReportSchedule] = {}
        self.regulatory_submissions: Dict[str, RegulatorySubmission] = {}

        # Data extractors and formatters
        self.data_extractors: Dict[str, Callable] = {}
        self.report_formatters: Dict[ReportFormat, Callable] = {}
        self.validation_rules: Dict[str, Callable] = {}

        # External integrations
        self.submission_handlers: Dict[str, Callable] = {}
        self.notification_handlers: Dict[str, Callable] = {}

        # Statistics
        self.reporting_stats = {
            "total_reports_generated": 0,
            "reports_generated_today": 0,
            "successful_submissions": 0,
            "failed_generations": 0,
            "average_generation_time_seconds": 0.0,
            "data_quality_score": 0.0,
        }

        # Initialize default templates
        self._initialize_default_templates()

        # Scheduler state
        self.scheduler_running = False
        self.scheduler_task: Optional[asyncio.Task] = None

    def _initialize_default_templates(self):
        """Initialize default report templates"""

        default_templates = [
            ReportTemplate(
                template_id="gdpr_article_30_ropa",
                template_name="GDPR Article 30 - Records of Processing Activities",
                report_type=ReportType.GDPR_ARTICLE_30,
                regulation_type="GDPR",
                data_sources=[
                    "consent_manager",
                    "data_retention_enforcer",
                    "regulatory_frameworks",
                ],
                required_fields=[
                    "organization_name",
                    "data_controller_contact",
                    "processing_purposes",
                    "data_categories",
                    "data_subjects",
                    "recipients",
                    "retention_periods",
                ],
                supported_formats=[
                    ReportFormat.PDF,
                    ReportFormat.JSON,
                    ReportFormat.XML,
                ],
                default_frequency=ReportFrequency.ANNUALLY,
                retention_days=2555,
            ),
            ReportTemplate(
                template_id="sar_fincen_report",
                template_name="Suspicious Activity Report - FinCEN",
                report_type=ReportType.SAR_FINCEN,
                regulation_type="AML",
                data_sources=["financial_compliance_engine"],
                required_fields=[
                    "filing_institution",
                    "subject_information",
                    "suspicious_activity",
                    "transaction_details",
                    "narrative_description",
                ],
                supported_formats=[ReportFormat.XML, ReportFormat.JSON],
                submission_endpoint="https://bsaefiling.fincen.treas.gov/",
                submission_method="api",
                default_frequency=ReportFrequency.TRIGGERED,
            ),
            ReportTemplate(
                template_id="pci_dss_compliance_report",
                template_name="PCI DSS Compliance Assessment Report",
                report_type=ReportType.PCI_DSS_COMPLIANCE,
                regulation_type="PCI_DSS",
                data_sources=["regulatory_frameworks"],
                required_fields=[
                    "merchant_information",
                    "assessment_details",
                    "requirements_status",
                    "vulnerabilities",
                    "remediation_plan",
                ],
                supported_formats=[ReportFormat.PDF, ReportFormat.HTML],
                default_frequency=ReportFrequency.ANNUALLY,
            ),
            ReportTemplate(
                template_id="data_breach_summary",
                template_name="Data Breach Summary Report",
                report_type=ReportType.DATA_BREACH_SUMMARY,
                regulation_type="GDPR",
                data_sources=["breach_notification_system"],
                required_fields=[
                    "breach_summary",
                    "affected_individuals",
                    "data_categories",
                    "notification_timeline",
                    "remediation_measures",
                ],
                supported_formats=[ReportFormat.PDF, ReportFormat.JSON],
                default_frequency=ReportFrequency.QUARTERLY,
            ),
            ReportTemplate(
                template_id="kyc_audit_report",
                template_name="KYC Compliance Audit Report",
                report_type=ReportType.KYC_AUDIT,
                regulation_type="AML",
                data_sources=["financial_compliance_engine"],
                required_fields=[
                    "audit_period",
                    "kyc_statistics",
                    "verification_rates",
                    "compliance_gaps",
                    "remediation_actions",
                ],
                supported_formats=[ReportFormat.PDF, ReportFormat.XLSX],
                default_frequency=ReportFrequency.QUARTERLY,
            ),
        ]

        for template in default_templates:
            self.report_templates[template.template_id] = template

    def generate_report_id(self) -> str:
        """Generate unique report ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"rpt_{timestamp}_{hash(timestamp) % 10000:04d}"

    def generate_schedule_id(self) -> str:
        """Generate unique schedule ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"sched_{timestamp}_{hash(timestamp) % 10000:04d}"

    def generate_submission_id(self) -> str:
        """Generate unique submission ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"sub_{timestamp}_{hash(timestamp) % 10000:04d}"

    async def generate_report(
        self,
        template_id: str,
        report_period_start: datetime,
        report_period_end: datetime,
        report_format: Optional[ReportFormat] = None,
        generated_by: str = "system",
        custom_parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate regulatory report"""

        try:
            # Get template
            template = self.report_templates.get(template_id)
            if not template:
                raise ValueError(f"Report template not found: {template_id}")

            # Create report instance
            report_id = self.generate_report_id()
            now = datetime.now(timezone.utc)

            report_instance = ReportInstance(
                report_id=report_id,
                template_id=template_id,
                report_type=template.report_type,
                generated_at=now,
                generated_by=generated_by,
                report_period_start=report_period_start,
                report_period_end=report_period_end,
                report_format=report_format or template.default_format,
                status=ReportStatus.GENERATING,
                generation_started_at=now,
                metadata=custom_parameters or {},
            )

            # Store report instance
            self.report_instances[report_id] = report_instance

            # Generate report content
            await self._generate_report_content(report_id)

            logger.info(
                f"Report generation completed: {report_id} - {template.template_name}"
            )

            return report_id

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            if "report_instance" in locals():
                report_instance.status = ReportStatus.FAILED
                report_instance.validation_errors.append(str(e))
            raise

    async def _generate_report_content(self, report_id: str):
        """Generate report content"""

        report_instance = self.report_instances.get(report_id)
        if not report_instance:
            raise ValueError(f"Report instance not found: {report_id}")

        template = self.report_templates.get(report_instance.template_id)
        if not template:
            raise ValueError(
                f"Report template not found: {report_instance.template_id}"
            )

        try:
            # Extract data from sources
            report_data = await self._extract_report_data(report_instance, template)
            report_instance.report_data = report_data

            # Validate data
            validation_result = await self._validate_report_data(
                report_instance, template
            )
            report_instance.validation_passed = validation_result["passed"]
            report_instance.validation_errors = validation_result["errors"]
            report_instance.quality_score = validation_result["quality_score"]

            if not report_instance.validation_passed and template.validation_rules:
                raise ValueError(
                    f"Report validation failed: {report_instance.validation_errors}"
                )

            # Format report
            report_content = await self._format_report_content(
                report_instance, template
            )
            report_instance.report_content = report_content

            # Calculate metadata
            report_instance.record_count = self._count_report_records(report_data)
            report_instance.file_size_bytes = len(report_content.encode("utf-8"))
            report_instance.report_hash = hashlib.sha256(
                report_content.encode("utf-8")
            ).hexdigest()

            # Update status
            report_instance.status = ReportStatus.COMPLETED
            report_instance.generation_completed_at = datetime.now(timezone.utc)
            report_instance.generation_duration_seconds = (
                report_instance.generation_completed_at
                - report_instance.generation_started_at
            ).total_seconds()

            # Update statistics
            self.reporting_stats["total_reports_generated"] += 1
            self.reporting_stats["reports_generated_today"] += 1  # Would reset daily
            self.reporting_stats["average_generation_time_seconds"] = (
                self.reporting_stats["average_generation_time_seconds"]
                * (self.reporting_stats["total_reports_generated"] - 1)
                + report_instance.generation_duration_seconds
            ) / self.reporting_stats["total_reports_generated"]

        except Exception as e:
            report_instance.status = ReportStatus.FAILED
            report_instance.validation_errors.append(str(e))
            report_instance.generation_completed_at = datetime.now(timezone.utc)
            self.reporting_stats["failed_generations"] += 1
            raise

    async def _extract_report_data(
        self, report_instance: ReportInstance, template: ReportTemplate
    ) -> Dict[str, Any]:
        """Extract data for report generation"""

        report_data = {
            "report_metadata": {
                "report_id": report_instance.report_id,
                "report_type": template.report_type.value,
                "regulation_type": template.regulation_type,
                "generation_date": report_instance.generated_at.isoformat(),
                "period_start": report_instance.report_period_start.isoformat(),
                "period_end": report_instance.report_period_end.isoformat(),
                "generated_by": report_instance.generated_by,
            }
        }

        # Extract data from each source
        for data_source in template.data_sources:
            try:
                extractor = self.data_extractors.get(data_source)
                if extractor:
                    source_data = await extractor(report_instance, template)
                    report_data[data_source] = source_data
                else:
                    # Default extraction (mock data for demo)
                    report_data[data_source] = await self._default_data_extraction(
                        data_source, report_instance, template
                    )
            except Exception as e:
                logger.error(f"Failed to extract data from {data_source}: {e}")
                report_data[data_source] = {"error": str(e)}

        return report_data

    async def _default_data_extraction(
        self,
        data_source: str,
        report_instance: ReportInstance,
        template: ReportTemplate,
    ) -> Dict[str, Any]:
        """Default data extraction (mock implementation)"""

        # Mock data extraction based on source and report type
        if (
            data_source == "consent_manager"
            and template.report_type == ReportType.GDPR_ARTICLE_30
        ):
            return {
                "total_consents": 1250,
                "active_consents": 1180,
                "withdrawn_consents": 70,
                "consent_types": [
                    {"type": "attribution_tracking", "count": 1180},
                    {"type": "analytics", "count": 920},
                    {"type": "marketing", "count": 450},
                ],
                "data_categories": [
                    "personal_data",
                    "conversation_data",
                    "attribution_data",
                ],
            }

        elif (
            data_source == "financial_compliance_engine"
            and template.report_type == ReportType.SAR_FINCEN
        ):
            return {
                "suspicious_transactions": [
                    {
                        "transaction_id": "txn_123456",
                        "amount": 15000.00,
                        "currency": "USD",
                        "suspicious_activity_type": "Structuring",
                        "risk_score": 0.95,
                        "date": "2024-01-15T10:30:00Z",
                    }
                ],
                "filing_institution": "UATP Capsule Engine",
                "total_sars": 3,
            }

        elif data_source == "breach_notification_system":
            return {
                "total_breaches": 2,
                "breaches": [
                    {
                        "breach_id": "breach_001",
                        "date": "2024-01-10T14:22:00Z",
                        "type": "unauthorized_access",
                        "affected_records": 150,
                        "notification_sent": True,
                        "sa_notified": True,
                    }
                ],
                "notification_compliance_rate": 100.0,
            }

        else:
            return {
                "data_source": data_source,
                "extraction_date": datetime.now(timezone.utc).isoformat(),
                "status": "mock_data",
            }

    async def _validate_report_data(
        self, report_instance: ReportInstance, template: ReportTemplate
    ) -> Dict[str, Any]:
        """Validate report data quality and completeness"""

        validation_errors = []
        quality_score = 1.0

        # Check required fields
        for field in template.required_fields:
            if not self._field_exists_in_data(field, report_instance.report_data):
                validation_errors.append(f"Required field missing: {field}")
                quality_score -= 0.1

        # Apply custom validation rules
        for rule_name in template.validation_rules:
            validator = self.validation_rules.get(rule_name)
            if validator:
                try:
                    rule_result = await validator(report_instance, template)
                    if not rule_result["passed"]:
                        validation_errors.extend(rule_result["errors"])
                        quality_score -= rule_result.get("score_penalty", 0.1)
                except Exception as e:
                    validation_errors.append(
                        f"Validation rule '{rule_name}' failed: {str(e)}"
                    )
                    quality_score -= 0.05

        # Data quality checks
        if template.quality_checks:
            quality_result = await self._perform_quality_checks(
                report_instance, template
            )
            validation_errors.extend(quality_result["errors"])
            quality_score *= quality_result["score_multiplier"]

        return {
            "passed": len(validation_errors) == 0,
            "errors": validation_errors,
            "quality_score": max(0.0, min(1.0, quality_score)),
        }

    def _field_exists_in_data(self, field_path: str, data: Dict[str, Any]) -> bool:
        """Check if field exists in nested data structure"""

        keys = field_path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False

        return current is not None

    async def _perform_quality_checks(
        self, report_instance: ReportInstance, template: ReportTemplate
    ) -> Dict[str, Any]:
        """Perform data quality checks"""

        errors = []
        score_multiplier = 1.0

        # Check data completeness
        total_fields = len(template.required_fields) + len(template.optional_fields)
        present_fields = sum(
            1
            for field in template.required_fields + template.optional_fields
            if self._field_exists_in_data(field, report_instance.report_data)
        )

        if total_fields > 0:
            completeness_ratio = present_fields / total_fields
            if completeness_ratio < 0.8:
                errors.append(
                    f"Data completeness below threshold: {completeness_ratio:.2%}"
                )
                score_multiplier *= 0.9

        # Check data freshness
        generation_age = datetime.now(timezone.utc) - report_instance.generated_at
        if generation_age.total_seconds() > 3600:  # 1 hour
            errors.append("Report data may be stale")
            score_multiplier *= 0.95

        return {
            "errors": errors,
            "score_multiplier": score_multiplier,
        }

    async def _format_report_content(
        self, report_instance: ReportInstance, template: ReportTemplate
    ) -> str:
        """Format report content in requested format"""

        formatter = self.report_formatters.get(report_instance.report_format)

        if formatter:
            return await formatter(report_instance, template)
        else:
            return await self._default_format_report(report_instance, template)

    async def _default_format_report(
        self, report_instance: ReportInstance, template: ReportTemplate
    ) -> str:
        """Default report formatting"""

        if report_instance.report_format == ReportFormat.JSON:
            return json.dumps(report_instance.report_data, indent=2, default=str)

        elif report_instance.report_format == ReportFormat.XML:
            return self._dict_to_xml(report_instance.report_data, "report")

        elif report_instance.report_format == ReportFormat.CSV:
            return self._dict_to_csv(report_instance.report_data)

        elif report_instance.report_format == ReportFormat.HTML:
            return self._dict_to_html(report_instance, template)

        else:  # Default to JSON
            return json.dumps(report_instance.report_data, indent=2, default=str)

    def _dict_to_xml(self, data: Dict[str, Any], root_name: str) -> str:
        """Convert dictionary to XML format"""

        def _dict_to_element(d: Any, name: str) -> ET.Element:
            element = ET.Element(name)

            if isinstance(d, dict):
                for key, value in d.items():
                    child = _dict_to_element(value, key)
                    element.append(child)
            elif isinstance(d, list):
                for i, item in enumerate(d):
                    child = _dict_to_element(item, f"item_{i}")
                    element.append(child)
            else:
                element.text = str(d)

            return element

        root = _dict_to_element(data, root_name)
        return ET.tostring(root, encoding="unicode")

    def _dict_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert dictionary to CSV format (flattened)"""

        def _flatten_dict(
            d: Dict[str, Any], parent_key: str = "", sep: str = "."
        ) -> Dict[str, Any]:
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k

                if isinstance(v, dict):
                    items.extend(_flatten_dict(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            items.extend(
                                _flatten_dict(item, f"{new_key}_{i}", sep=sep).items()
                            )
                        else:
                            items.append((f"{new_key}_{i}", item))
                else:
                    items.append((new_key, v))

            return dict(items)

        flattened = _flatten_dict(data)

        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(flattened.keys())

        # Write data
        writer.writerow(flattened.values())

        return output.getvalue()

    def _dict_to_html(
        self, report_instance: ReportInstance, template: ReportTemplate
    ) -> str:
        """Convert dictionary to HTML format"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{template.template_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .metadata {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>{template.template_name}</h1>

    <div class="metadata">
        <h2>Report Information</h2>
        <p><strong>Report ID:</strong> {report_instance.report_id}</p>
        <p><strong>Generated:</strong> {report_instance.generated_at.isoformat()}</p>
        <p><strong>Period:</strong> {report_instance.report_period_start.date()} to {report_instance.report_period_end.date()}</p>
        <p><strong>Generated By:</strong> {report_instance.generated_by}</p>
    </div>

    <h2>Report Data</h2>
    {self._dict_to_html_table(report_instance.report_data)}
</body>
</html>
        """

        return html_content

    def _dict_to_html_table(self, data: Any, level: int = 0) -> str:
        """Convert nested dictionary to HTML tables"""

        if isinstance(data, dict):
            html = "<table>\
"
            for key, value in data.items():
                html += f"<tr><th>{key}</th><td>{self._dict_to_html_table(value, level+1)}</td></tr>\
"
            html += "</table>\
"
            return html
        elif isinstance(data, list):
            html = "<ul>\
"
            for item in data:
                html += f"<li>{self._dict_to_html_table(item, level+1)}</li>\
"
            html += "</ul>\
"
            return html
        else:
            return str(data)

    def _count_report_records(self, data: Dict[str, Any]) -> int:
        """Count the number of records in report data"""

        count = 0

        def _count_items(obj: Any) -> int:
            if isinstance(obj, dict):
                return sum(_count_items(v) for v in obj.values())
            elif isinstance(obj, list):
                return len(obj) + sum(_count_items(item) for item in obj)
            else:
                return 1

        return _count_items(data)

    async def submit_report(
        self,
        report_id: str,
        authority: str,
        submission_method: str = "manual",
        submitted_by: str = "system",
    ) -> str:
        """Submit report to regulatory authority"""

        report_instance = self.report_instances.get(report_id)
        if not report_instance:
            raise ValueError(f"Report not found: {report_id}")

        if report_instance.status != ReportStatus.COMPLETED:
            raise ValueError(
                f"Report not ready for submission: {report_instance.status.value}"
            )

        # Create submission record
        submission_id = self.generate_submission_id()
        now = datetime.now(timezone.utc)

        submission = RegulatorySubmission(
            submission_id=submission_id,
            report_id=report_id,
            authority=authority,
            submission_method=submission_method,
            submitted_at=now,
            submitted_by=submitted_by,
        )

        try:
            # Execute submission
            submission_result = await self._execute_submission(
                submission, report_instance
            )

            # Update submission record
            submission.submission_reference = submission_result.get("reference")
            submission.submission_status = submission_result.get("status", "submitted")
            submission.status_message = submission_result.get("message")

            # Update report instance
            report_instance.status = ReportStatus.SUBMITTED
            report_instance.submitted_at = now
            report_instance.submission_reference = submission.submission_reference

            # Store submission
            self.regulatory_submissions[submission_id] = submission

            # Update statistics
            self.reporting_stats["successful_submissions"] += 1

            logger.info(
                f"Report submitted: {report_id} to {authority} - Reference: {submission.submission_reference}"
            )

            return submission_id

        except Exception as e:
            submission.submission_status = "failed"
            submission.status_message = str(e)
            self.regulatory_submissions[submission_id] = submission
            logger.error(f"Report submission failed: {report_id} - {e}")
            raise

    async def _execute_submission(
        self, submission: RegulatorySubmission, report_instance: ReportInstance
    ) -> Dict[str, Any]:
        """Execute report submission to authority"""

        # Get submission handler
        handler = self.submission_handlers.get(submission.authority.lower())

        if handler:
            return await handler(submission, report_instance)
        else:
            # Default submission (mock)
            return {
                "reference": f"REF-{submission.submission_id[-8:]}",
                "status": "submitted",
                "message": "Report submitted successfully (mock)",
            }

    async def schedule_report(
        self,
        template_id: str,
        frequency: ReportFrequency,
        generation_time: str = "09:00",
        auto_generate: bool = True,
        auto_submit: bool = False,
        recipients: Optional[List[str]] = None,
    ) -> str:
        """Schedule automatic report generation"""

        template = self.report_templates.get(template_id)
        if not template:
            raise ValueError(f"Report template not found: {template_id}")

        schedule_id = self.generate_schedule_id()
        now = datetime.now(timezone.utc)

        # Create schedule
        schedule = ReportSchedule(
            schedule_id=schedule_id,
            template_id=template_id,
            schedule_name=f"Scheduled {template.template_name}",
            frequency=frequency,
            generation_time=generation_time,
            auto_generate=auto_generate,
            auto_submit=auto_submit,
            recipients=recipients or [],
        )

        # Calculate next generation time
        schedule.next_generation = self._calculate_next_generation(schedule)

        # Store schedule
        self.report_schedules[schedule_id] = schedule

        logger.info(
            f"Report scheduled: {schedule_id} - {template.template_name} - Frequency: {frequency.value}"
        )

        return schedule_id

    def _calculate_next_generation(self, schedule: ReportSchedule) -> datetime:
        """Calculate next report generation time"""

        now = datetime.now(timezone.utc)

        # Parse generation time
        hour, minute = map(int, schedule.generation_time.split(":"))

        if schedule.frequency == ReportFrequency.DAILY:
            next_gen = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_gen <= now:
                next_gen += timedelta(days=1)

        elif schedule.frequency == ReportFrequency.WEEKLY:
            next_gen = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            days_ahead = 6 - now.weekday()  # Next Sunday
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_gen += timedelta(days=days_ahead)

        elif schedule.frequency == ReportFrequency.MONTHLY:
            next_gen = now.replace(
                day=1, hour=hour, minute=minute, second=0, microsecond=0
            )
            if next_gen <= now:
                # Next month
                if next_gen.month == 12:
                    next_gen = next_gen.replace(year=next_gen.year + 1, month=1)
                else:
                    next_gen = next_gen.replace(month=next_gen.month + 1)

        elif schedule.frequency == ReportFrequency.QUARTERLY:
            # First day of next quarter
            current_quarter = (now.month - 1) // 3
            next_quarter_month = (current_quarter + 1) * 3 + 1
            if next_quarter_month > 12:
                next_gen = now.replace(
                    year=now.year + 1,
                    month=1,
                    day=1,
                    hour=hour,
                    minute=minute,
                    second=0,
                    microsecond=0,
                )
            else:
                next_gen = now.replace(
                    month=next_quarter_month,
                    day=1,
                    hour=hour,
                    minute=minute,
                    second=0,
                    microsecond=0,
                )

        elif schedule.frequency == ReportFrequency.ANNUALLY:
            next_gen = now.replace(
                month=1, day=1, hour=hour, minute=minute, second=0, microsecond=0
            )
            if next_gen <= now:
                next_gen = next_gen.replace(year=next_gen.year + 1)

        else:
            # Default to next day
            next_gen = now + timedelta(days=1)

        return next_gen

    async def start_scheduler(self):
        """Start report scheduler"""

        if self.scheduler_running:
            logger.warning("Report scheduler already running")
            return

        self.scheduler_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Report scheduler started")

    async def stop_scheduler(self):
        """Stop report scheduler"""

        self.scheduler_running = False

        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

        logger.info("Report scheduler stopped")

    async def _scheduler_loop(self):
        """Report scheduler main loop"""

        while self.scheduler_running:
            try:
                now = datetime.now(timezone.utc)

                # Check scheduled reports
                for schedule in list(self.report_schedules.values()):
                    if (
                        schedule.is_active
                        and schedule.auto_generate
                        and schedule.next_generation
                        and schedule.next_generation <= now
                    ):
                        await self._execute_scheduled_report(schedule)

                # Sleep for 1 minute
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)

    async def _execute_scheduled_report(self, schedule: ReportSchedule):
        """Execute scheduled report generation"""

        try:
            # Calculate report period
            now = datetime.now(timezone.utc)
            period_end = now
            period_start = now - timedelta(days=schedule.report_period_days)

            # Generate report
            report_id = await self.generate_report(
                template_id=schedule.template_id,
                report_period_start=period_start,
                report_period_end=period_end,
                generated_by="scheduler",
            )

            # Auto-submit if configured
            if schedule.auto_submit:
                # Would need authority configuration
                pass

            # Send notifications
            if schedule.recipients:
                await self._send_report_notifications(report_id, schedule)

            # Update schedule
            schedule.last_generated = now
            schedule.next_generation = self._calculate_next_generation(schedule)

            logger.info(
                f"Scheduled report generated: {report_id} from schedule {schedule.schedule_id}"
            )

        except Exception as e:
            logger.error(
                f"Scheduled report generation failed: {schedule.schedule_id} - {e}"
            )

            # Handle retry logic
            if hasattr(schedule, "retry_count"):
                schedule.retry_count = getattr(schedule, "retry_count", 0) + 1
            else:
                schedule.retry_count = 1

            if schedule.retry_count < schedule.max_retries:
                # Schedule retry
                schedule.next_generation = now + timedelta(
                    minutes=schedule.retry_delay_minutes
                )
            else:
                # Disable schedule after max retries
                schedule.is_active = False
                if schedule.failure_notification:
                    await self._send_failure_notification(schedule, str(e))

    async def _send_report_notifications(
        self, report_id: str, schedule: ReportSchedule
    ):
        """Send report generation notifications"""

        report_instance = self.report_instances.get(report_id)
        if not report_instance:
            return

        for channel in schedule.notification_channels:
            handler = self.notification_handlers.get(channel)
            if handler:
                try:
                    await handler(report_instance, schedule)
                except Exception as e:
                    logger.error(f"Notification failed for channel {channel}: {e}")

    async def _send_failure_notification(
        self, schedule: ReportSchedule, error_message: str
    ):
        """Send failure notification"""

        for channel in schedule.notification_channels:
            handler = self.notification_handlers.get(channel)
            if handler:
                try:
                    await handler(
                        {
                            "type": "report_generation_failure",
                            "schedule_id": schedule.schedule_id,
                            "template_name": schedule.schedule_name,
                            "error": error_message,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                except Exception as e:
                    logger.error(
                        f"Failure notification failed for channel {channel}: {e}"
                    )

    async def get_report_status(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report generation status"""

        report_instance = self.report_instances.get(report_id)
        if not report_instance:
            return None

        return {
            "report_id": report_instance.report_id,
            "template_id": report_instance.template_id,
            "report_type": report_instance.report_type.value,
            "status": report_instance.status.value,
            "generated_at": report_instance.generated_at.isoformat(),
            "generated_by": report_instance.generated_by,
            "period_start": report_instance.report_period_start.isoformat(),
            "period_end": report_instance.report_period_end.isoformat(),
            "format": report_instance.report_format.value,
            "validation_passed": report_instance.validation_passed,
            "validation_errors": report_instance.validation_errors,
            "quality_score": report_instance.quality_score,
            "record_count": report_instance.record_count,
            "file_size_bytes": report_instance.file_size_bytes,
            "generation_duration_seconds": report_instance.generation_duration_seconds,
            "submitted_at": report_instance.submitted_at.isoformat()
            if report_instance.submitted_at
            else None,
            "submission_reference": report_instance.submission_reference,
        }

    async def get_report_content(self, report_id: str) -> Optional[str]:
        """Get report content"""

        report_instance = self.report_instances.get(report_id)
        if not report_instance or report_instance.status != ReportStatus.COMPLETED:
            return None

        return report_instance.report_content

    async def get_reporting_dashboard(self) -> Dict[str, Any]:
        """Get reporting system dashboard"""

        now = datetime.now(timezone.utc)

        # Recent reports (last 30 days)
        thirty_days_ago = now - timedelta(days=30)
        recent_reports = [
            report
            for report in self.report_instances.values()
            if report.generated_at >= thirty_days_ago
        ]

        # Status distribution
        status_distribution = {}
        for status in ReportStatus:
            count = len([r for r in recent_reports if r.status == status])
            status_distribution[status.value] = count

        # Type distribution
        type_distribution = {}
        for report_type in ReportType:
            count = len([r for r in recent_reports if r.report_type == report_type])
            type_distribution[report_type.value] = count

        return {
            "dashboard_generated_at": now.isoformat(),
            "summary": self.reporting_stats,
            "recent_activity": {
                "reports_last_30_days": len(recent_reports),
                "successful_reports": len(
                    [r for r in recent_reports if r.status == ReportStatus.COMPLETED]
                ),
                "failed_reports": len(
                    [r for r in recent_reports if r.status == ReportStatus.FAILED]
                ),
                "pending_reports": len(
                    [
                        r
                        for r in recent_reports
                        if r.status in [ReportStatus.PENDING, ReportStatus.GENERATING]
                    ]
                ),
            },
            "status_distribution": status_distribution,
            "type_distribution": type_distribution,
            "active_schedules": len(
                [s for s in self.report_schedules.values() if s.is_active]
            ),
            "total_submissions": len(self.regulatory_submissions),
            "templates_available": len(self.report_templates),
        }

    def register_data_extractor(self, source_name: str, extractor: Callable):
        """Register custom data extractor"""

        self.data_extractors[source_name] = extractor
        logger.info(f"Data extractor registered: {source_name}")

    def register_report_formatter(
        self, report_format: ReportFormat, formatter: Callable
    ):
        """Register custom report formatter"""

        self.report_formatters[report_format] = formatter
        logger.info(f"Report formatter registered: {report_format.value}")

    def register_submission_handler(self, authority: str, handler: Callable):
        """Register custom submission handler"""

        self.submission_handlers[authority.lower()] = handler
        logger.info(f"Submission handler registered: {authority}")

    def register_validation_rule(self, rule_name: str, validator: Callable):
        """Register custom validation rule"""

        self.validation_rules[rule_name] = validator
        logger.info(f"Validation rule registered: {rule_name}")


# Factory function
def create_compliance_reporting_system() -> ComplianceReportingSystem:
    """Create compliance reporting system instance"""
    return ComplianceReportingSystem()
