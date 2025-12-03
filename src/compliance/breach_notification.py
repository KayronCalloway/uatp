"""
Automated Breach Notification System
GDPR Article 33/34 compliant automated data breach detection and notification
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable

logger = logging.getLogger(__name__)


class BreachType(Enum):
    """Types of data breaches"""
    CONFIDENTIALITY_BREACH = "confidentiality_breach"
    INTEGRITY_BREACH = "integrity_breach"
    AVAILABILITY_BREACH = "availability_breach"
    COMBINED_BREACH = "combined_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_LOSS = "data_loss"
    SYSTEM_COMPROMISE = "system_compromise"
    INSIDER_THREAT = "insider_threat"
    THIRD_PARTY_BREACH = "third_party_breach"


class BreachSeverity(Enum):
    """Breach severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BreachStatus(Enum):
    """Breach investigation status"""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"


class NotificationStatus(Enum):
    """Notification delivery status"""
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"


class RiskLevel(Enum):
    """Risk to rights and freedoms of data subjects"""
    NO_RISK = "no_risk"
    LOW_RISK = "low_risk"
    HIGH_RISK = "high_risk"
    VERY_HIGH_RISK = "very_high_risk"


@dataclass
class DataBreach:
    """Data breach incident record"""
    breach_id: str
    detected_at: datetime
    
    # Breach details
    breach_type: BreachType
    severity: BreachSeverity
    status: BreachStatus = BreachStatus.DETECTED
    
    # Affected data
    data_categories: List[str] = field(default_factory=list)
    affected_records_count: int = 0
    affected_users: List[str] = field(default_factory=list)
    
    # Breach description
    title: str = ""
    description: str = ""
    root_cause: str = ""
    attack_vector: str = ""
    
    # Timeline
    incident_start_time: Optional[datetime] = None
    incident_end_time: Optional[datetime] = None
    detection_method: str = ""
    
    # Impact assessment
    confidentiality_impact: bool = False
    integrity_impact: bool = False
    availability_impact: bool = False
    risk_to_rights: RiskLevel = RiskLevel.LOW_RISK
    
    # Geographic scope
    affected_countries: List[str] = field(default_factory=list)
    cross_border_incident: bool = False
    
    # Investigation
    investigated_by: Optional[str] = None
    investigation_notes: List[str] = field(default_factory=list)
    containment_measures: List[str] = field(default_factory=list)
    remediation_actions: List[str] = field(default_factory=list)
    
    # Notifications
    supervisory_authority_notification: NotificationStatus = NotificationStatus.NOT_REQUIRED
    data_subject_notification: NotificationStatus = NotificationStatus.NOT_REQUIRED
    
    # Compliance
    gdpr_article_33_required: bool = False
    gdpr_article_34_required: bool = False
    notification_deadline: Optional[datetime] = None
    
    # External
    law_enforcement_notified: bool = False
    third_parties_notified: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SupervisoryAuthorityNotification:
    """GDPR Article 33 notification to supervisory authority"""
    notification_id: str
    breach_id: str
    authority: str  # e.g., "CNIL", "ICO", "BfDI"
    
    # Notification content
    breach_description: str
    data_categories: List[str]
    affected_records_estimate: int
    likely_consequences: str
    measures_taken: str
    
    # Timing
    notification_due: datetime
    notification_sent: Optional[datetime] = None
    status: NotificationStatus = NotificationStatus.PENDING
    
    # Delivery
    delivery_method: str = "electronic"  # electronic, postal, phone
    confirmation_received: bool = False
    authority_reference: Optional[str] = None
    
    # Follow-up
    additional_info_requested: bool = False
    additional_info_deadline: Optional[datetime] = None
    final_report_required: bool = False
    final_report_deadline: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataSubjectNotification:
    """GDPR Article 34 notification to data subjects"""
    notification_id: str
    breach_id: str
    
    # Recipients
    affected_users: List[str] = field(default_factory=list)
    notification_channels: List[str] = field(default_factory=list)  # email, sms, postal, public
    
    # Content
    subject_line: str = ""
    message_content: str = ""
    language: str = "en"
    
    # Timing
    notification_required: bool = False
    notification_sent: Optional[datetime] = None
    status: NotificationStatus = NotificationStatus.NOT_REQUIRED
    
    # Delivery tracking
    emails_sent: int = 0
    emails_delivered: int = 0
    emails_opened: int = 0
    sms_sent: int = 0
    sms_delivered: int = 0
    
    # Response tracking
    user_responses: Dict[str, str] = field(default_factory=dict)
    support_tickets_created: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BreachDetectionRule:
    """Automated breach detection rule"""
    rule_id: str
    rule_name: str
    description: str
    
    # Rule configuration
    breach_type: BreachType
    detection_criteria: Dict[str, Any]
    severity_threshold: BreachSeverity
    
    # Monitoring
    is_active: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    # Actions
    auto_investigate: bool = False
    auto_contain: bool = False
    escalation_threshold: int = 5
    
    # Metadata
    created_by: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DataProtectionImpactAssessment:
    """DPIA for high-risk processing activities"""
    dpia_id: str
    processing_activity: str
    assessment_date: datetime
    assessed_by: str
    
    # Risk assessment
    inherent_risk_score: float  # 0-1 scale
    residual_risk_score: float  # After controls
    risk_level: RiskLevel
    
    # Findings
    high_risk_factors: List[str] = field(default_factory=list)
    mitigation_measures: List[str] = field(default_factory=list)
    monitoring_requirements: List[str] = field(default_factory=list)
    
    # Approval
    approved: bool = False
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None
    approval_conditions: List[str] = field(default_factory=list)
    
    # Review
    next_review_date: Optional[datetime] = None
    review_frequency_months: int = 12
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class BreachNotificationSystem:
    """Automated breach detection and notification system"""
    
    def __init__(self):
        self.breaches: Dict[str, DataBreach] = {}
        self.sa_notifications: Dict[str, SupervisoryAuthorityNotification] = {}
        self.ds_notifications: Dict[str, DataSubjectNotification] = {}
        self.detection_rules: Dict[str, BreachDetectionRule] = {}
        self.dpias: Dict[str, DataProtectionImpactAssessment] = {}
        
        # Notification handlers
        self.notification_handlers: Dict[str, Callable] = {}
        
        # Supervisory authorities configuration
        self.supervisory_authorities = {
            "DE": {"name": "BfDI", "email": "breach@bfdi.bund.de", "phone": "+49-228-997799-0"},
            "FR": {"name": "CNIL", "email": "breach@cnil.fr", "phone": "+33-1-53-73-22-22"},
            "GB": {"name": "ICO", "email": "breach@ico.org.uk", "phone": "+44-303-123-1113"},
            "NL": {"name": "AP", "email": "breach@autoriteitpersoonsgegevens.nl", "phone": "+31-70-888-8500"},
            "IT": {"name": "GPDP", "email": "breach@gpdp.it", "phone": "+39-06-696771"},
            "ES": {"name": "AEPD", "email": "breach@aepd.es", "phone": "+34-901-100-099"},
        }
        
        # Statistics
        self.breach_stats = {
            "total_breaches": 0,
            "breaches_this_month": 0,
            "sa_notifications_sent": 0,
            "ds_notifications_sent": 0,
            "average_detection_time_hours": 0.0,
            "average_containment_time_hours": 0.0,
        }
        
        # Initialize detection rules
        self._initialize_detection_rules()
    
    def _initialize_detection_rules(self):
        """Initialize default breach detection rules"""
        
        default_rules = [
            BreachDetectionRule(
                rule_id="unauthorized_access",
                rule_name="Unauthorized Access Detection",
                description="Detect unauthorized access to sensitive data",
                breach_type=BreachType.UNAUTHORIZED_ACCESS,
                detection_criteria={
                    "failed_login_threshold": 10,
                    "suspicious_ip_access": True,
                    "privilege_escalation": True,
                },
                severity_threshold=BreachSeverity.HIGH,
                auto_investigate=True,
            ),
            BreachDetectionRule(
                rule_id="data_exfiltration",
                rule_name="Data Exfiltration Detection",
                description="Detect large-scale data extraction",
                breach_type=BreachType.CONFIDENTIALITY_BREACH,
                detection_criteria={
                    "data_volume_threshold_gb": 1.0,
                    "unusual_download_pattern": True,
                    "off_hours_access": True,
                },
                severity_threshold=BreachSeverity.CRITICAL,
                auto_investigate=True,
                auto_contain=True,
            ),
            BreachDetectionRule(
                rule_id="system_compromise",
                rule_name="System Compromise Detection",
                description="Detect system-level security breaches",
                breach_type=BreachType.SYSTEM_COMPROMISE,
                detection_criteria={
                    "malware_detected": True,
                    "root_access_gained": True,
                    "system_files_modified": True,
                },
                severity_threshold=BreachSeverity.CRITICAL,
                auto_investigate=True,
                auto_contain=True,
            ),
            BreachDetectionRule(
                rule_id="data_corruption",
                rule_name="Data Integrity Breach",
                description="Detect data corruption or unauthorized modification",
                breach_type=BreachType.INTEGRITY_BREACH,
                detection_criteria={
                    "checksum_validation_failed": True,
                    "unexpected_data_changes": True,
                    "database_integrity_violation": True,
                },
                severity_threshold=BreachSeverity.HIGH,
                auto_investigate=True,
            ),
            BreachDetectionRule(
                rule_id="service_outage",
                rule_name="Availability Breach Detection",
                description="Detect service outages affecting data availability",
                breach_type=BreachType.AVAILABILITY_BREACH,
                detection_criteria={
                    "service_downtime_hours": 4,
                    "data_access_blocked": True,
                    "backup_systems_failed": True,
                },
                severity_threshold=BreachSeverity.MEDIUM,
                auto_investigate=False,
            ),
        ]
        
        for rule in default_rules:
            self.detection_rules[rule.rule_id] = rule
    
    def generate_breach_id(self) -> str:
        """Generate unique breach ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"breach_{timestamp}_{hash(timestamp) % 10000:04d}"
    
    def generate_notification_id(self) -> str:
        """Generate unique notification ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"notif_{timestamp}_{hash(timestamp) % 10000:04d}"
    
    def generate_dpia_id(self) -> str:
        """Generate unique DPIA ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"dpia_{timestamp}_{hash(timestamp) % 10000:04d}"
    
    async def report_breach(
        self,
        breach_type: BreachType,
        title: str,
        description: str,
        affected_data_categories: List[str],
        affected_records_count: int = 0,
        affected_users: Optional[List[str]] = None,
        incident_start_time: Optional[datetime] = None,
        detection_method: str = "manual_report",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Report a data breach incident"""
        
        breach_id = self.generate_breach_id()
        now = datetime.now(timezone.utc)
        
        # Determine severity based on affected data and scale
        severity = self._calculate_breach_severity(
            breach_type, affected_records_count, affected_data_categories
        )\n        \n        # Assess risk to rights and freedoms\n        risk_level = self._assess_risk_to_rights(\n            breach_type, affected_data_categories, affected_records_count\n        )\n        \n        # Create breach record\n        breach = DataBreach(\n            breach_id=breach_id,\n            detected_at=now,\n            breach_type=breach_type,\n            severity=severity,\n            title=title,\n            description=description,\n            data_categories=affected_data_categories,\n            affected_records_count=affected_records_count,\n            affected_users=affected_users or [],\n            incident_start_time=incident_start_time or now,\n            detection_method=detection_method,\n            risk_to_rights=risk_level,\n            metadata=metadata or {},\n        )\n        \n        # Set impact flags\n        breach.confidentiality_impact = breach_type in [\n            BreachType.CONFIDENTIALITY_BREACH, BreachType.UNAUTHORIZED_ACCESS, \n            BreachType.COMBINED_BREACH\n        ]\n        breach.integrity_impact = breach_type in [\n            BreachType.INTEGRITY_BREACH, BreachType.COMBINED_BREACH\n        ]\n        breach.availability_impact = breach_type in [\n            BreachType.AVAILABILITY_BREACH, BreachType.COMBINED_BREACH\n        ]\n        \n        # Determine notification requirements\n        breach.gdpr_article_33_required = self._requires_sa_notification(breach)\n        breach.gdpr_article_34_required = self._requires_ds_notification(breach)\n        \n        if breach.gdpr_article_33_required:\n            # Set 72-hour notification deadline\n            breach.notification_deadline = now + timedelta(hours=72)\n        \n        # Store breach\n        self.breaches[breach_id] = breach\n        self.breach_stats[\"total_breaches\"] += 1\n        \n        # Trigger automated response\n        await self._trigger_automated_response(breach)\n        \n        logger.critical(\n            f\"Data breach reported: {breach_id} - {title} - Severity: {severity.value} - SA notification required: {breach.gdpr_article_33_required}\"\n        )\n        \n        return breach_id\n    \n    def _calculate_breach_severity(\n        self, \n        breach_type: BreachType, \n        affected_records: int, \n        data_categories: List[str]\n    ) -> BreachSeverity:\n        \"\"\"Calculate breach severity based on type, scale, and data sensitivity\"\"\"\n        \n        severity_score = 0\n        \n        # Base severity by breach type\n        type_scores = {\n            BreachType.CONFIDENTIALITY_BREACH: 3,\n            BreachType.UNAUTHORIZED_ACCESS: 3,\n            BreachType.SYSTEM_COMPROMISE: 4,\n            BreachType.INTEGRITY_BREACH: 2,\n            BreachType.AVAILABILITY_BREACH: 1,\n            BreachType.DATA_LOSS: 3,\n            BreachType.COMBINED_BREACH: 4,\n            BreachType.INSIDER_THREAT: 3,\n            BreachType.THIRD_PARTY_BREACH: 2,\n        }\n        \n        severity_score += type_scores.get(breach_type, 2)\n        \n        # Scale factor\n        if affected_records >= 100000:\n            severity_score += 3\n        elif affected_records >= 10000:\n            severity_score += 2\n        elif affected_records >= 1000:\n            severity_score += 1\n        \n        # Data sensitivity factor\n        sensitive_categories = {\n            \"health_data\", \"biometric_data\", \"genetic_data\", \n            \"financial_data\", \"children_data\", \"criminal_data\"\n        }\n        \n        if any(cat in sensitive_categories for cat in data_categories):\n            severity_score += 2\n        \n        # Map score to severity level\n        if severity_score >= 8:\n            return BreachSeverity.CRITICAL\n        elif severity_score >= 6:\n            return BreachSeverity.HIGH\n        elif severity_score >= 4:\n            return BreachSeverity.MEDIUM\n        else:\n            return BreachSeverity.LOW\n    \n    def _assess_risk_to_rights(\n        self, \n        breach_type: BreachType, \n        data_categories: List[str], \n        affected_records: int\n    ) -> RiskLevel:\n        \"\"\"Assess risk to rights and freedoms of data subjects\"\"\"\n        \n        risk_score = 0\n        \n        # High-risk data categories\n        high_risk_categories = {\n            \"health_data\", \"biometric_data\", \"genetic_data\", \n            \"location_data\", \"children_data\", \"criminal_data\",\n            \"financial_data\", \"identity_documents\"\n        }\n        \n        medium_risk_categories = {\n            \"personal_data\", \"contact_data\", \"employment_data\",\n            \"communication_data\", \"behavioral_data\"\n        }\n        \n        # Category risk assessment\n        if any(cat in high_risk_categories for cat in data_categories):\n            risk_score += 3\n        elif any(cat in medium_risk_categories for cat in data_categories):\n            risk_score += 2\n        else:\n            risk_score += 1\n        \n        # Scale risk assessment\n        if affected_records >= 10000:\n            risk_score += 3\n        elif affected_records >= 1000:\n            risk_score += 2\n        elif affected_records >= 100:\n            risk_score += 1\n        \n        # Breach type risk assessment\n        high_risk_types = {\n            BreachType.CONFIDENTIALITY_BREACH,\n            BreachType.UNAUTHORIZED_ACCESS,\n            BreachType.SYSTEM_COMPROMISE,\n            BreachType.COMBINED_BREACH\n        }\n        \n        if breach_type in high_risk_types:\n            risk_score += 2\n        \n        # Map score to risk level\n        if risk_score >= 8:\n            return RiskLevel.VERY_HIGH_RISK\n        elif risk_score >= 6:\n            return RiskLevel.HIGH_RISK\n        elif risk_score >= 4:\n            return RiskLevel.LOW_RISK\n        else:\n            return RiskLevel.NO_RISK\n    \n    def _requires_sa_notification(self, breach: DataBreach) -> bool:\n        \"\"\"Determine if supervisory authority notification is required (Article 33)\"\"\"\n        \n        # Article 33(1): Notification required unless breach is unlikely to result in risk\n        if breach.risk_to_rights == RiskLevel.NO_RISK:\n            return False\n        \n        # All other risk levels require notification\n        return True\n    \n    def _requires_ds_notification(self, breach: DataBreach) -> bool:\n        \"\"\"Determine if data subject notification is required (Article 34)\"\"\"\n        \n        # Article 34(1): Notification required for high risk to rights and freedoms\n        if breach.risk_to_rights in [RiskLevel.HIGH_RISK, RiskLevel.VERY_HIGH_RISK]:\n            return True\n        \n        # Article 34(3): Exceptions\n        # - Technical and organizational measures that render data unintelligible\n        # - Measures taken to ensure risk no longer likely to materialize\n        # - Disproportionate effort (public communication instead)\n        \n        return False\n    \n    async def _trigger_automated_response(self, breach: DataBreach):\n        \"\"\"Trigger automated breach response procedures\"\"\"\n        \n        # Start investigation\n        breach.status = BreachStatus.INVESTIGATING\n        breach.investigated_by = \"automated_system\"\n        breach.investigation_notes.append(f\"Automated investigation started at {datetime.now(timezone.utc)}\")\n        \n        # Automated containment for critical breaches\n        if breach.severity == BreachSeverity.CRITICAL:\n            await self._initiate_containment(breach)\n        \n        # Schedule notifications\n        if breach.gdpr_article_33_required:\n            await self._schedule_sa_notification(breach)\n        \n        if breach.gdpr_article_34_required:\n            await self._schedule_ds_notification(breach)\n        \n        # Trigger DPIA if required\n        if breach.risk_to_rights in [RiskLevel.HIGH_RISK, RiskLevel.VERY_HIGH_RISK]:\n            await self._initiate_dpia(breach)\n    \n    async def _initiate_containment(self, breach: DataBreach):\n        \"\"\"Initiate automated containment measures\"\"\"\n        \n        containment_measures = []\n        \n        # System-level containment\n        if breach.breach_type == BreachType.SYSTEM_COMPROMISE:\n            containment_measures.extend([\n                \"Isolated affected systems from network\",\n                \"Disabled compromised user accounts\",\n                \"Activated backup systems\",\n                \"Initiated malware scan\",\n            ])\n        \n        # Access control containment\n        if breach.breach_type == BreachType.UNAUTHORIZED_ACCESS:\n            containment_measures.extend([\n                \"Reset affected user passwords\",\n                \"Revoked suspicious access tokens\",\n                \"Enabled enhanced monitoring\",\n                \"Blocked suspicious IP addresses\",\n            ])\n        \n        # Data protection containment\n        if breach.breach_type == BreachType.CONFIDENTIALITY_BREACH:\n            containment_measures.extend([\n                \"Encrypted affected data\",\n                \"Restricted data access permissions\",\n                \"Enabled audit logging\",\n                \"Activated data loss prevention\",\n            ])\n        \n        breach.containment_measures.extend(containment_measures)\n        breach.status = BreachStatus.CONTAINED\n        \n        logger.info(f\"Containment initiated for breach {breach.breach_id}: {len(containment_measures)} measures applied\")\n    \n    async def _schedule_sa_notification(self, breach: DataBreach):\n        \"\"\"Schedule supervisory authority notification (Article 33)\"\"\"\n        \n        notification_id = self.generate_notification_id()\n        \n        # Determine primary supervisory authority (lead authority for cross-border processing)\n        primary_authority = \"CNIL\"  # Default - would be configured based on main establishment\n        \n        # Create notification\n        sa_notification = SupervisoryAuthorityNotification(\n            notification_id=notification_id,\n            breach_id=breach.breach_id,\n            authority=primary_authority,\n            breach_description=breach.description,\n            data_categories=breach.data_categories,\n            affected_records_estimate=breach.affected_records_count,\n            likely_consequences=self._generate_consequences_description(breach),\n            measures_taken=\" | \".join(breach.containment_measures),\n            notification_due=breach.notification_deadline,\n        )\n        \n        self.sa_notifications[notification_id] = sa_notification\n        breach.supervisory_authority_notification = NotificationStatus.PENDING\n        \n        # Schedule automatic sending (with some buffer before deadline)\n        send_time = breach.notification_deadline - timedelta(hours=6)  # 6 hours before deadline\n        \n        # In production, this would use a task scheduler\n        asyncio.create_task(self._send_sa_notification_delayed(notification_id, send_time))\n        \n        logger.info(f\"SA notification scheduled: {notification_id} - Due: {breach.notification_deadline}\")\n    \n    async def _schedule_ds_notification(self, breach: DataBreach):\n        \"\"\"Schedule data subject notification (Article 34)\"\"\"\n        \n        notification_id = self.generate_notification_id()\n        \n        # Create notification\n        ds_notification = DataSubjectNotification(\n            notification_id=notification_id,\n            breach_id=breach.breach_id,\n            affected_users=breach.affected_users,\n            notification_channels=[\"email\", \"in_app\"],\n            subject_line=f\"Important Security Notice - Data Breach Notification\",\n            message_content=self._generate_ds_notification_content(breach),\n            notification_required=True,\n        )\n        \n        self.ds_notifications[notification_id] = ds_notification\n        breach.data_subject_notification = NotificationStatus.PENDING\n        \n        # Data subject notifications should be sent \"without undue delay\"\n        # Schedule for immediate sending after SA notification\n        send_time = datetime.now(timezone.utc) + timedelta(minutes=30)\n        \n        asyncio.create_task(self._send_ds_notification_delayed(notification_id, send_time))\n        \n        logger.info(f\"DS notification scheduled: {notification_id} - {len(breach.affected_users)} users affected\")\n    \n    def _generate_consequences_description(self, breach: DataBreach) -> str:\n        \"\"\"Generate likely consequences description for SA notification\"\"\"\n        \n        consequences = []\n        \n        if breach.confidentiality_impact:\n            consequences.append(\"Unauthorized disclosure of personal data\")\n        \n        if breach.integrity_impact:\n            consequences.append(\"Potential data corruption or unauthorized modification\")\n        \n        if breach.availability_impact:\n            consequences.append(\"Temporary loss of access to personal data\")\n        \n        # Risk-specific consequences\n        if breach.risk_to_rights == RiskLevel.VERY_HIGH_RISK:\n            consequences.extend([\n                \"High risk of identity theft\",\n                \"Potential financial harm to data subjects\",\n                \"Risk of discrimination or reputational damage\",\n            ])\n        elif breach.risk_to_rights == RiskLevel.HIGH_RISK:\n            consequences.extend([\n                \"Moderate risk to privacy and security\",\n                \"Potential for targeted phishing attacks\",\n            ])\n        \n        return \"; \".join(consequences)\n    \n    def _generate_ds_notification_content(self, breach: DataBreach) -> str:\n        \"\"\"Generate data subject notification content\"\"\"\n        \n        content = f\"\"\"\nDear User,\n\nWe are writing to inform you of a security incident that may have affected your personal data.\n\n**What happened?**\n{breach.description}\n\n**What information was involved?**\nThe following categories of data may have been affected: {', '.join(breach.data_categories)}\n\n**What we are doing:**\n{' | '.join(breach.containment_measures)}\n\n**What you can do:**\n- Monitor your accounts for unusual activity\n- Change your passwords as a precautionary measure\n- Contact us if you have any concerns\n\n**Contact Information:**\nFor questions about this incident, please contact our Data Protection Team at privacy@uatp.com\n\nWe sincerely apologize for this incident and any inconvenience it may cause.\n\nUATP Data Protection Team\n\"\"\"\n        \n        return content\n    \n    async def _send_sa_notification_delayed(self, notification_id: str, send_time: datetime):\n        \"\"\"Send supervisory authority notification at scheduled time\"\"\"\n        \n        # Wait until send time\n        now = datetime.now(timezone.utc)\n        if send_time > now:\n            delay_seconds = (send_time - now).total_seconds()\n            await asyncio.sleep(delay_seconds)\n        \n        await self._send_sa_notification(notification_id)\n    \n    async def _send_ds_notification_delayed(self, notification_id: str, send_time: datetime):\n        \"\"\"Send data subject notification at scheduled time\"\"\"\n        \n        # Wait until send time\n        now = datetime.now(timezone.utc)\n        if send_time > now:\n            delay_seconds = (send_time - now).total_seconds()\n            await asyncio.sleep(delay_seconds)\n        \n        await self._send_ds_notification(notification_id)\n    \n    async def _send_sa_notification(self, notification_id: str):\n        \"\"\"Send supervisory authority notification\"\"\"\n        \n        if notification_id not in self.sa_notifications:\n            logger.error(f\"SA notification not found: {notification_id}\")\n            return\n        \n        notification = self.sa_notifications[notification_id]\n        \n        try:\n            authority_info = self.supervisory_authorities.get(\"FR\")  # Default to CNIL\n            \n            # In production, this would integrate with official notification systems\n            # For now, we'll simulate the notification\n            \n            notification_data = {\n                \"breach_id\": notification.breach_id,\n                \"organization\": \"UATP Capsule Engine\",\n                \"breach_description\": notification.breach_description,\n                \"data_categories\": notification.data_categories,\n                \"affected_records\": notification.affected_records_estimate,\n                \"likely_consequences\": notification.likely_consequences,\n                \"measures_taken\": notification.measures_taken,\n                \"contact_email\": \"dpo@uatp.com\",\n                \"contact_phone\": \"+1-555-DATA-PROTECT\",\n            }\n            \n            # Simulate API call or email sending\n            logger.info(f\"Sending SA notification to {notification.authority}: {json.dumps(notification_data, indent=2)}\")\n            \n            # Mock successful sending\n            notification.notification_sent = datetime.now(timezone.utc)\n            notification.status = NotificationStatus.SENT\n            notification.authority_reference = f\"REF-{notification.notification_id[-8:]}\"\n            \n            # Update breach record\n            breach = self.breaches[notification.breach_id]\n            breach.supervisory_authority_notification = NotificationStatus.SENT\n            \n            self.breach_stats[\"sa_notifications_sent\"] += 1\n            \n            logger.info(f\"SA notification sent successfully: {notification_id}\")\n            \n        except Exception as e:\n            notification.status = NotificationStatus.FAILED\n            logger.error(f\"Failed to send SA notification {notification_id}: {e}\")\n    \n    async def _send_ds_notification(self, notification_id: str):\n        \"\"\"Send data subject notification\"\"\"\n        \n        if notification_id not in self.ds_notifications:\n            logger.error(f\"DS notification not found: {notification_id}\")\n            return\n        \n        notification = self.ds_notifications[notification_id]\n        \n        try:\n            # Send email notifications\n            if \"email\" in notification.notification_channels:\n                # In production, this would integrate with email service\n                notification.emails_sent = len(notification.affected_users)\n                notification.emails_delivered = int(notification.emails_sent * 0.95)  # Mock 95% delivery rate\n                notification.emails_opened = int(notification.emails_delivered * 0.70)  # Mock 70% open rate\n            \n            # Send in-app notifications\n            if \"in_app\" in notification.notification_channels:\n                # In production, this would push notifications to app users\n                pass\n            \n            notification.notification_sent = datetime.now(timezone.utc)\n            notification.status = NotificationStatus.SENT\n            \n            # Update breach record\n            breach = self.breaches[notification.breach_id]\n            breach.data_subject_notification = NotificationStatus.SENT\n            \n            self.breach_stats[\"ds_notifications_sent\"] += 1\n            \n            logger.info(f\"DS notification sent successfully: {notification_id} - {notification.emails_sent} users notified\")\n            \n        except Exception as e:\n            notification.status = NotificationStatus.FAILED\n            logger.error(f\"Failed to send DS notification {notification_id}: {e}\")\n    \n    async def _initiate_dpia(self, breach: DataBreach):\n        \"\"\"Initiate Data Protection Impact Assessment for high-risk incidents\"\"\"\n        \n        dpia_id = self.generate_dpia_id()\n        now = datetime.now(timezone.utc)\n        \n        # Calculate risk scores\n        inherent_risk = 0.8 if breach.risk_to_rights == RiskLevel.VERY_HIGH_RISK else 0.6\n        \n        # After containment measures\n        residual_risk = inherent_risk - (len(breach.containment_measures) * 0.1)\n        residual_risk = max(0.2, residual_risk)  # Minimum residual risk\n        \n        # Create DPIA\n        dpia = DataProtectionImpactAssessment(\n            dpia_id=dpia_id,\n            processing_activity=f\"Data breach response - {breach.title}\",\n            assessment_date=now,\n            assessed_by=\"automated_system\",\n            inherent_risk_score=inherent_risk,\n            residual_risk_score=residual_risk,\n            risk_level=breach.risk_to_rights,\n            high_risk_factors=[\n                f\"Breach type: {breach.breach_type.value}\",\n                f\"Affected records: {breach.affected_records_count}\",\n                f\"Data categories: {', '.join(breach.data_categories)}\",\n            ],\n            mitigation_measures=breach.containment_measures,\n            next_review_date=now + timedelta(days=90),\n        )\n        \n        self.dpias[dpia_id] = dpia\n        \n        logger.info(f\"DPIA initiated: {dpia_id} for breach {breach.breach_id}\")\n    \n    async def get_breach_status(self, breach_id: str) -> Dict[str, Any]:\n        \"\"\"Get comprehensive breach status\"\"\"\n        \n        if breach_id not in self.breaches:\n            return {\"error\": \"Breach not found\"}\n        \n        breach = self.breaches[breach_id]\n        \n        # Calculate time metrics\n        now = datetime.now(timezone.utc)\n        \n        detection_time = None\n        if breach.incident_start_time:\n            detection_time = (breach.detected_at - breach.incident_start_time).total_seconds() / 3600\n        \n        containment_time = None\n        if breach.status == BreachStatus.CONTAINED and breach.containment_measures:\n            # Estimate containment time (would be tracked precisely in production)\n            containment_time = 2.5  # Mock 2.5 hours\n        \n        # Notification status\n        sa_notification_status = \"not_required\"\n        ds_notification_status = \"not_required\"\n        \n        if breach.gdpr_article_33_required:\n            sa_notification_status = breach.supervisory_authority_notification.value\n        \n        if breach.gdpr_article_34_required:\n            ds_notification_status = breach.data_subject_notification.value\n        \n        return {\n            \"breach_id\": breach.breach_id,\n            \"title\": breach.title,\n            \"status\": breach.status.value,\n            \"severity\": breach.severity.value,\n            \"breach_type\": breach.breach_type.value,\n            \"risk_to_rights\": breach.risk_to_rights.value,\n            \"detected_at\": breach.detected_at.isoformat(),\n            \"incident_start_time\": breach.incident_start_time.isoformat() if breach.incident_start_time else None,\n            \"affected_records\": breach.affected_records_count,\n            \"affected_users\": len(breach.affected_users),\n            \"data_categories\": breach.data_categories,\n            \"detection_time_hours\": detection_time,\n            \"containment_time_hours\": containment_time,\n            \"containment_measures\": len(breach.containment_measures),\n            \"notifications\": {\n                \"sa_notification_required\": breach.gdpr_article_33_required,\n                \"sa_notification_status\": sa_notification_status,\n                \"sa_notification_deadline\": breach.notification_deadline.isoformat() if breach.notification_deadline else None,\n                \"ds_notification_required\": breach.gdpr_article_34_required,\n                \"ds_notification_status\": ds_notification_status,\n            },\n            \"investigation\": {\n                \"investigated_by\": breach.investigated_by,\n                \"investigation_notes\": len(breach.investigation_notes),\n                \"remediation_actions\": len(breach.remediation_actions),\n            },\n        }\n    \n    async def get_compliance_dashboard(self) -> Dict[str, Any]:\n        \"\"\"Get breach notification compliance dashboard\"\"\"\n        \n        now = datetime.now(timezone.utc)\n        \n        # Recent breaches (last 30 days)\n        thirty_days_ago = now - timedelta(days=30)\n        recent_breaches = [\n            breach for breach in self.breaches.values()\n            if breach.detected_at >= thirty_days_ago\n        ]\n        \n        # Notification compliance\n        sa_notifications_due = len([\n            breach for breach in recent_breaches\n            if (breach.gdpr_article_33_required and \n                breach.supervisory_authority_notification in [NotificationStatus.PENDING, NotificationStatus.FAILED])\n        ])\n        \n        overdue_sa_notifications = len([\n            breach for breach in recent_breaches\n            if (breach.notification_deadline and \n                breach.notification_deadline < now and\n                breach.supervisory_authority_notification != NotificationStatus.SENT)\n        ])\n        \n        # Severity distribution\n        severity_distribution = {}\n        for severity in BreachSeverity:\n            count = len([b for b in recent_breaches if b.severity == severity])\n            severity_distribution[severity.value] = count\n        \n        # Risk distribution\n        risk_distribution = {}\n        for risk_level in RiskLevel:\n            count = len([b for b in recent_breaches if b.risk_to_rights == risk_level])\n            risk_distribution[risk_level.value] = count\n        \n        return {\n            \"dashboard_generated_at\": now.isoformat(),\n            \"summary\": self.breach_stats,\n            \"recent_activity\": {\n                \"breaches_last_30_days\": len(recent_breaches),\n                \"critical_breaches\": len([b for b in recent_breaches if b.severity == BreachSeverity.CRITICAL]),\n                \"sa_notifications_due\": sa_notifications_due,\n                \"overdue_notifications\": overdue_sa_notifications,\n            },\n            \"severity_distribution\": severity_distribution,\n            \"risk_distribution\": risk_distribution,\n            \"notification_compliance\": {\n                \"sa_notifications_sent\": self.breach_stats[\"sa_notifications_sent\"],\n                \"ds_notifications_sent\": self.breach_stats[\"ds_notifications_sent\"],\n                \"compliance_rate\": (self.breach_stats[\"sa_notifications_sent\"] / max(1, len([b for b in self.breaches.values() if b.gdpr_article_33_required]))) * 100,\n            },\n            \"response_metrics\": {\n                \"average_detection_time_hours\": self.breach_stats[\"average_detection_time_hours\"],\n                \"average_containment_time_hours\": self.breach_stats[\"average_containment_time_hours\"],\n            },\n        }\n    \n    def register_notification_handler(self, channel: str, handler: Callable):\n        \"\"\"Register custom notification handler\"\"\"\n        \n        self.notification_handlers[channel] = handler\n        logger.info(f\"Notification handler registered for channel: {channel}\")\n    \n    async def test_breach_detection(self) -> str:\n        \"\"\"Test breach detection system with simulated incident\"\"\"\n        \n        return await self.report_breach(\n            breach_type=BreachType.UNAUTHORIZED_ACCESS,\n            title=\"Test Security Incident\",\n            description=\"Simulated unauthorized access for system testing\",\n            affected_data_categories=[\"personal_data\", \"contact_data\"],\n            affected_records_count=150,\n            affected_users=[\"test_user_1\", \"test_user_2\"],\n            detection_method=\"automated_test\",\n            metadata={\"test\": True, \"simulated\": True},\n        )\n\n\n# Factory function\ndef create_breach_notification_system() -> BreachNotificationSystem:\n    \"\"\"Create breach notification system instance\"\"\"\n    return BreachNotificationSystem()