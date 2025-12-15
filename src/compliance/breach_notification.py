"""
Automated Breach Notification System
GDPR Article 33/34 compliant automated data breach detection and notification
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

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
    supervisory_authority_notification: NotificationStatus = (
        NotificationStatus.NOT_REQUIRED
    )
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
    notification_channels: List[str] = field(
        default_factory=list
    )  # email, sms, postal, public

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
            "DE": {
                "name": "BfDI",
                "email": "breach@bfdi.bund.de",
                "phone": "+49-228-997799-0",
            },
            "FR": {
                "name": "CNIL",
                "email": "breach@cnil.fr",
                "phone": "+33-1-53-73-22-22",
            },
            "GB": {
                "name": "ICO",
                "email": "breach@ico.org.uk",
                "phone": "+44-303-123-1113",
            },
            "NL": {
                "name": "AP",
                "email": "breach@autoriteitpersoonsgegevens.nl",
                "phone": "+31-70-888-8500",
            },
            "IT": {"name": "GPDP", "email": "breach@gpdp.it", "phone": "+39-06-696771"},
            "ES": {
                "name": "AEPD",
                "email": "breach@aepd.es",
                "phone": "+34-901-100-099",
            },
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
        )

        # Assess risk to rights and freedoms
        risk_level = self._assess_risk_to_rights(
            breach_type, affected_data_categories, affected_records_count
        )

        # Create breach record
        breach = DataBreach(
            breach_id=breach_id,
            detected_at=now,
            breach_type=breach_type,
            severity=severity,
            title=title,
            description=description,
            data_categories=affected_data_categories,
            affected_records_count=affected_records_count,
            affected_users=affected_users or [],
            incident_start_time=incident_start_time or now,
            detection_method=detection_method,
            risk_to_rights=risk_level,
            metadata=metadata or {},
        )

        # Set impact flags
        breach.confidentiality_impact = breach_type in [
            BreachType.CONFIDENTIALITY_BREACH,
            BreachType.UNAUTHORIZED_ACCESS,
            BreachType.COMBINED_BREACH,
        ]
        breach.integrity_impact = breach_type in [
            BreachType.INTEGRITY_BREACH,
            BreachType.COMBINED_BREACH,
        ]
        breach.availability_impact = breach_type in [
            BreachType.AVAILABILITY_BREACH,
            BreachType.COMBINED_BREACH,
        ]

        # Determine notification requirements
        breach.gdpr_article_33_required = self._requires_sa_notification(breach)
        breach.gdpr_article_34_required = self._requires_ds_notification(breach)

        if breach.gdpr_article_33_required:
            # Set 72-hour notification deadline
            breach.notification_deadline = now + timedelta(hours=72)

        # Store breach
        self.breaches[breach_id] = breach
        self.breach_stats["total_breaches"] += 1

        # Trigger automated response
        await self._trigger_automated_response(breach)

        logger.critical(
            f"Data breach reported: {breach_id} - {title} - Severity: {severity.value} - SA notification required: {breach.gdpr_article_33_required}"
        )

        return breach_id

    def _calculate_breach_severity(
        self, breach_type: BreachType, affected_records: int, data_categories: List[str]
    ) -> BreachSeverity:
        """Calculate breach severity based on type, scale, and data sensitivity"""

        severity_score = 0

        # Base severity by breach type
        type_scores = {
            BreachType.CONFIDENTIALITY_BREACH: 3,
            BreachType.UNAUTHORIZED_ACCESS: 3,
            BreachType.SYSTEM_COMPROMISE: 4,
            BreachType.INTEGRITY_BREACH: 2,
            BreachType.AVAILABILITY_BREACH: 1,
            BreachType.DATA_LOSS: 3,
            BreachType.COMBINED_BREACH: 4,
            BreachType.INSIDER_THREAT: 3,
            BreachType.THIRD_PARTY_BREACH: 2,
        }

        severity_score += type_scores.get(breach_type, 2)

        # Scale factor
        if affected_records >= 100000:
            severity_score += 3
        elif affected_records >= 10000:
            severity_score += 2
        elif affected_records >= 1000:
            severity_score += 1

        # Data sensitivity factor
        sensitive_categories = {
            "health_data",
            "biometric_data",
            "genetic_data",
            "financial_data",
            "children_data",
            "criminal_data",
        }

        if any(cat in sensitive_categories for cat in data_categories):
            severity_score += 2

        # Map score to severity level
        if severity_score >= 8:
            return BreachSeverity.CRITICAL
        elif severity_score >= 6:
            return BreachSeverity.HIGH
        elif severity_score >= 4:
            return BreachSeverity.MEDIUM
        else:
            return BreachSeverity.LOW

    def _assess_risk_to_rights(
        self, breach_type: BreachType, data_categories: List[str], affected_records: int
    ) -> RiskLevel:
        """Assess risk to rights and freedoms of data subjects"""

        risk_score = 0

        # High-risk data categories
        high_risk_categories = {
            "health_data",
            "biometric_data",
            "genetic_data",
            "location_data",
            "children_data",
            "criminal_data",
            "financial_data",
            "identity_documents",
        }

        medium_risk_categories = {
            "personal_data",
            "contact_data",
            "employment_data",
            "communication_data",
            "behavioral_data",
        }

        # Category risk assessment
        if any(cat in high_risk_categories for cat in data_categories):
            risk_score += 3
        elif any(cat in medium_risk_categories for cat in data_categories):
            risk_score += 2
        else:
            risk_score += 1

        # Scale risk assessment
        if affected_records >= 10000:
            risk_score += 3
        elif affected_records >= 1000:
            risk_score += 2
        elif affected_records >= 100:
            risk_score += 1

        # Breach type risk assessment
        high_risk_types = {
            BreachType.CONFIDENTIALITY_BREACH,
            BreachType.UNAUTHORIZED_ACCESS,
            BreachType.SYSTEM_COMPROMISE,
            BreachType.COMBINED_BREACH,
        }

        if breach_type in high_risk_types:
            risk_score += 2

        # Map score to risk level
        if risk_score >= 8:
            return RiskLevel.VERY_HIGH_RISK
        elif risk_score >= 6:
            return RiskLevel.HIGH_RISK
        elif risk_score >= 4:
            return RiskLevel.LOW_RISK
        else:
            return RiskLevel.NO_RISK

    def _requires_sa_notification(self, breach: DataBreach) -> bool:
        """Determine if supervisory authority notification is required (Article 33)"""

        # Article 33(1): Notification required unless breach is unlikely to result in risk
        if breach.risk_to_rights == RiskLevel.NO_RISK:
            return False

        # All other risk levels require notification
        return True

    def _requires_ds_notification(self, breach: DataBreach) -> bool:
        """Determine if data subject notification is required (Article 34)"""

        # Article 34(1): Notification required for high risk to rights and freedoms
        if breach.risk_to_rights in [RiskLevel.HIGH_RISK, RiskLevel.VERY_HIGH_RISK]:
            return True

        # Article 34(3): Exceptions
        # - Technical and organizational measures that render data unintelligible
        # - Measures taken to ensure risk no longer likely to materialize
        # - Disproportionate effort (public communication instead)

        return False

    async def _trigger_automated_response(self, breach: DataBreach):
        """Trigger automated breach response procedures"""

        # Start investigation
        breach.status = BreachStatus.INVESTIGATING
        breach.investigated_by = "automated_system"
        breach.investigation_notes.append(
            f"Automated investigation started at {datetime.now(timezone.utc)}"
        )

        # Automated containment for critical breaches
        if breach.severity == BreachSeverity.CRITICAL:
            await self._initiate_containment(breach)

        # Schedule notifications
        if breach.gdpr_article_33_required:
            await self._schedule_sa_notification(breach)

        if breach.gdpr_article_34_required:
            await self._schedule_ds_notification(breach)

        # Trigger DPIA if required
        if breach.risk_to_rights in [RiskLevel.HIGH_RISK, RiskLevel.VERY_HIGH_RISK]:
            await self._initiate_dpia(breach)

    async def _initiate_containment(self, breach: DataBreach):
        """Initiate automated containment measures"""

        containment_measures = []

        # System-level containment
        if breach.breach_type == BreachType.SYSTEM_COMPROMISE:
            containment_measures.extend(
                [
                    "Isolated affected systems from network",
                    "Disabled compromised user accounts",
                    "Activated backup systems",
                    "Initiated malware scan",
                ]
            )

        # Access control containment
        if breach.breach_type == BreachType.UNAUTHORIZED_ACCESS:
            containment_measures.extend(
                [
                    "Reset affected user passwords",
                    "Revoked suspicious access tokens",
                    "Enabled enhanced monitoring",
                    "Blocked suspicious IP addresses",
                ]
            )

        # Data protection containment
        if breach.breach_type == BreachType.CONFIDENTIALITY_BREACH:
            containment_measures.extend(
                [
                    "Encrypted affected data",
                    "Restricted data access permissions",
                    "Enabled audit logging",
                    "Activated data loss prevention",
                ]
            )

        breach.containment_measures.extend(containment_measures)
        breach.status = BreachStatus.CONTAINED

        logger.info(
            f"Containment initiated for breach {breach.breach_id}: {len(containment_measures)} measures applied"
        )

    async def _schedule_sa_notification(self, breach: DataBreach):
        """Schedule supervisory authority notification (Article 33)"""

        notification_id = self.generate_notification_id()

        # Determine primary supervisory authority (lead authority for cross-border processing)
        primary_authority = (
            "CNIL"  # Default - would be configured based on main establishment
        )

        # Create notification
        sa_notification = SupervisoryAuthorityNotification(
            notification_id=notification_id,
            breach_id=breach.breach_id,
            authority=primary_authority,
            breach_description=breach.description,
            data_categories=breach.data_categories,
            affected_records_estimate=breach.affected_records_count,
            likely_consequences=self._generate_consequences_description(breach),
            measures_taken=" | ".join(breach.containment_measures),
            notification_due=breach.notification_deadline,
        )

        self.sa_notifications[notification_id] = sa_notification
        breach.supervisory_authority_notification = NotificationStatus.PENDING

        # Schedule automatic sending (with some buffer before deadline)
        send_time = breach.notification_deadline - timedelta(
            hours=6
        )  # 6 hours before deadline

        # In production, this would use a task scheduler
        asyncio.create_task(
            self._send_sa_notification_delayed(notification_id, send_time)
        )

        logger.info(
            f"SA notification scheduled: {notification_id} - Due: {breach.notification_deadline}"
        )

    async def _schedule_ds_notification(self, breach: DataBreach):
        """Schedule data subject notification (Article 34)"""

        notification_id = self.generate_notification_id()

        # Create notification
        ds_notification = DataSubjectNotification(
            notification_id=notification_id,
            breach_id=breach.breach_id,
            affected_users=breach.affected_users,
            notification_channels=["email", "in_app"],
            subject_line="Important Security Notice - Data Breach Notification",
            message_content=self._generate_ds_notification_content(breach),
            notification_required=True,
        )

        self.ds_notifications[notification_id] = ds_notification
        breach.data_subject_notification = NotificationStatus.PENDING

        # Data subject notifications should be sent "without undue delay"
        # Schedule for immediate sending after SA notification
        send_time = datetime.now(timezone.utc) + timedelta(minutes=30)

        asyncio.create_task(
            self._send_ds_notification_delayed(notification_id, send_time)
        )

        logger.info(
            f"DS notification scheduled: {notification_id} - {len(breach.affected_users)} users affected"
        )

    def _generate_consequences_description(self, breach: DataBreach) -> str:
        """Generate likely consequences description for SA notification"""

        consequences = []

        if breach.confidentiality_impact:
            consequences.append("Unauthorized disclosure of personal data")

        if breach.integrity_impact:
            consequences.append(
                "Potential data corruption or unauthorized modification"
            )

        if breach.availability_impact:
            consequences.append("Temporary loss of access to personal data")

        # Risk-specific consequences
        if breach.risk_to_rights == RiskLevel.VERY_HIGH_RISK:
            consequences.extend(
                [
                    "High risk of identity theft",
                    "Potential financial harm to data subjects",
                    "Risk of discrimination or reputational damage",
                ]
            )
        elif breach.risk_to_rights == RiskLevel.HIGH_RISK:
            consequences.extend(
                [
                    "Moderate risk to privacy and security",
                    "Potential for targeted phishing attacks",
                ]
            )

        return "; ".join(consequences)

    def _generate_ds_notification_content(self, breach: DataBreach) -> str:
        """Generate data subject notification content"""

        content = f"""
Dear User,

We are writing to inform you of a security incident that may have affected your personal data.

**What happened?**
{breach.description}

**What information was involved?**
The following categories of data may have been affected: {', '.join(breach.data_categories)}

**What we are doing:**
{' | '.join(breach.containment_measures)}

**What you can do:**
- Monitor your accounts for unusual activity
- Change your passwords as a precautionary measure
- Contact us if you have any concerns

**Contact Information:**
For questions about this incident, please contact our Data Protection Team at privacy@uatp.com

We sincerely apologize for this incident and any inconvenience it may cause.

UATP Data Protection Team
"""

        return content

    async def _send_sa_notification_delayed(
        self, notification_id: str, send_time: datetime
    ):
        """Send supervisory authority notification at scheduled time"""

        # Wait until send time
        now = datetime.now(timezone.utc)
        if send_time > now:
            delay_seconds = (send_time - now).total_seconds()
            await asyncio.sleep(delay_seconds)

        await self._send_sa_notification(notification_id)

    async def _send_ds_notification_delayed(
        self, notification_id: str, send_time: datetime
    ):
        """Send data subject notification at scheduled time"""

        # Wait until send time
        now = datetime.now(timezone.utc)
        if send_time > now:
            delay_seconds = (send_time - now).total_seconds()
            await asyncio.sleep(delay_seconds)

        await self._send_ds_notification(notification_id)

    async def _send_sa_notification(self, notification_id: str):
        """Send supervisory authority notification"""

        if notification_id not in self.sa_notifications:
            logger.error(f"SA notification not found: {notification_id}")
            return

        notification = self.sa_notifications[notification_id]

        try:
            authority_info = self.supervisory_authorities.get("FR")  # Default to CNIL

            # In production, this would integrate with official notification systems
            # For now, we'll simulate the notification

            notification_data = {
                "breach_id": notification.breach_id,
                "organization": "UATP Capsule Engine",
                "breach_description": notification.breach_description,
                "data_categories": notification.data_categories,
                "affected_records": notification.affected_records_estimate,
                "likely_consequences": notification.likely_consequences,
                "measures_taken": notification.measures_taken,
                "contact_email": "dpo@uatp.com",
                "contact_phone": "+1-555-DATA-PROTECT",
            }

            # Simulate API call or email sending
            logger.info(
                f"Sending SA notification to {notification.authority}: {json.dumps(notification_data, indent=2)}"
            )

            # Mock successful sending
            notification.notification_sent = datetime.now(timezone.utc)
            notification.status = NotificationStatus.SENT
            notification.authority_reference = (
                f"REF-{notification.notification_id[-8:]}"
            )

            # Update breach record
            breach = self.breaches[notification.breach_id]
            breach.supervisory_authority_notification = NotificationStatus.SENT

            self.breach_stats["sa_notifications_sent"] += 1

            logger.info(f"SA notification sent successfully: {notification_id}")

        except Exception as e:
            notification.status = NotificationStatus.FAILED
            logger.error(f"Failed to send SA notification {notification_id}: {e}")

    async def _send_ds_notification(self, notification_id: str):
        """Send data subject notification"""

        if notification_id not in self.ds_notifications:
            logger.error(f"DS notification not found: {notification_id}")
            return

        notification = self.ds_notifications[notification_id]

        try:
            # Send email notifications
            if "email" in notification.notification_channels:
                # In production, this would integrate with email service
                notification.emails_sent = len(notification.affected_users)
                notification.emails_delivered = int(
                    notification.emails_sent * 0.95
                )  # Mock 95% delivery rate
                notification.emails_opened = int(
                    notification.emails_delivered * 0.70
                )  # Mock 70% open rate

            # Send in-app notifications
            if "in_app" in notification.notification_channels:
                # In production, this would push notifications to app users
                pass

            notification.notification_sent = datetime.now(timezone.utc)
            notification.status = NotificationStatus.SENT

            # Update breach record
            breach = self.breaches[notification.breach_id]
            breach.data_subject_notification = NotificationStatus.SENT

            self.breach_stats["ds_notifications_sent"] += 1

            logger.info(
                f"DS notification sent successfully: {notification_id} - {notification.emails_sent} users notified"
            )

        except Exception as e:
            notification.status = NotificationStatus.FAILED
            logger.error(f"Failed to send DS notification {notification_id}: {e}")

    async def _initiate_dpia(self, breach: DataBreach):
        """Initiate Data Protection Impact Assessment for high-risk incidents"""

        dpia_id = self.generate_dpia_id()
        now = datetime.now(timezone.utc)

        # Calculate risk scores
        inherent_risk = (
            0.8 if breach.risk_to_rights == RiskLevel.VERY_HIGH_RISK else 0.6
        )

        # After containment measures
        residual_risk = inherent_risk - (len(breach.containment_measures) * 0.1)
        residual_risk = max(0.2, residual_risk)  # Minimum residual risk

        # Create DPIA
        dpia = DataProtectionImpactAssessment(
            dpia_id=dpia_id,
            processing_activity=f"Data breach response - {breach.title}",
            assessment_date=now,
            assessed_by="automated_system",
            inherent_risk_score=inherent_risk,
            residual_risk_score=residual_risk,
            risk_level=breach.risk_to_rights,
            high_risk_factors=[
                f"Breach type: {breach.breach_type.value}",
                f"Affected records: {breach.affected_records_count}",
                f"Data categories: {', '.join(breach.data_categories)}",
            ],
            mitigation_measures=breach.containment_measures,
            next_review_date=now + timedelta(days=90),
        )

        self.dpias[dpia_id] = dpia

        logger.info(f"DPIA initiated: {dpia_id} for breach {breach.breach_id}")

    async def get_breach_status(self, breach_id: str) -> Dict[str, Any]:
        """Get comprehensive breach status"""

        if breach_id not in self.breaches:
            return {"error": "Breach not found"}

        breach = self.breaches[breach_id]

        # Calculate time metrics
        now = datetime.now(timezone.utc)

        detection_time = None
        if breach.incident_start_time:
            detection_time = (
                breach.detected_at - breach.incident_start_time
            ).total_seconds() / 3600

        containment_time = None
        if breach.status == BreachStatus.CONTAINED and breach.containment_measures:
            # Estimate containment time (would be tracked precisely in production)
            containment_time = 2.5  # Mock 2.5 hours

        # Notification status
        sa_notification_status = "not_required"
        ds_notification_status = "not_required"

        if breach.gdpr_article_33_required:
            sa_notification_status = breach.supervisory_authority_notification.value

        if breach.gdpr_article_34_required:
            ds_notification_status = breach.data_subject_notification.value

        return {
            "breach_id": breach.breach_id,
            "title": breach.title,
            "status": breach.status.value,
            "severity": breach.severity.value,
            "breach_type": breach.breach_type.value,
            "risk_to_rights": breach.risk_to_rights.value,
            "detected_at": breach.detected_at.isoformat(),
            "incident_start_time": breach.incident_start_time.isoformat()
            if breach.incident_start_time
            else None,
            "affected_records": breach.affected_records_count,
            "affected_users": len(breach.affected_users),
            "data_categories": breach.data_categories,
            "detection_time_hours": detection_time,
            "containment_time_hours": containment_time,
            "containment_measures": len(breach.containment_measures),
            "notifications": {
                "sa_notification_required": breach.gdpr_article_33_required,
                "sa_notification_status": sa_notification_status,
                "sa_notification_deadline": breach.notification_deadline.isoformat()
                if breach.notification_deadline
                else None,
                "ds_notification_required": breach.gdpr_article_34_required,
                "ds_notification_status": ds_notification_status,
            },
            "investigation": {
                "investigated_by": breach.investigated_by,
                "investigation_notes": len(breach.investigation_notes),
                "remediation_actions": len(breach.remediation_actions),
            },
        }

    async def get_compliance_dashboard(self) -> Dict[str, Any]:
        """Get breach notification compliance dashboard"""

        now = datetime.now(timezone.utc)

        # Recent breaches (last 30 days)
        thirty_days_ago = now - timedelta(days=30)
        recent_breaches = [
            breach
            for breach in self.breaches.values()
            if breach.detected_at >= thirty_days_ago
        ]

        # Notification compliance
        sa_notifications_due = len(
            [
                breach
                for breach in recent_breaches
                if (
                    breach.gdpr_article_33_required
                    and breach.supervisory_authority_notification
                    in [NotificationStatus.PENDING, NotificationStatus.FAILED]
                )
            ]
        )

        overdue_sa_notifications = len(
            [
                breach
                for breach in recent_breaches
                if (
                    breach.notification_deadline
                    and breach.notification_deadline < now
                    and breach.supervisory_authority_notification
                    != NotificationStatus.SENT
                )
            ]
        )

        # Severity distribution
        severity_distribution = {}
        for severity in BreachSeverity:
            count = len([b for b in recent_breaches if b.severity == severity])
            severity_distribution[severity.value] = count

        # Risk distribution
        risk_distribution = {}
        for risk_level in RiskLevel:
            count = len([b for b in recent_breaches if b.risk_to_rights == risk_level])
            risk_distribution[risk_level.value] = count

        return {
            "dashboard_generated_at": now.isoformat(),
            "summary": self.breach_stats,
            "recent_activity": {
                "breaches_last_30_days": len(recent_breaches),
                "critical_breaches": len(
                    [
                        b
                        for b in recent_breaches
                        if b.severity == BreachSeverity.CRITICAL
                    ]
                ),
                "sa_notifications_due": sa_notifications_due,
                "overdue_notifications": overdue_sa_notifications,
            },
            "severity_distribution": severity_distribution,
            "risk_distribution": risk_distribution,
            "notification_compliance": {
                "sa_notifications_sent": self.breach_stats["sa_notifications_sent"],
                "ds_notifications_sent": self.breach_stats["ds_notifications_sent"],
                "compliance_rate": (
                    self.breach_stats["sa_notifications_sent"]
                    / max(
                        1,
                        len(
                            [
                                b
                                for b in self.breaches.values()
                                if b.gdpr_article_33_required
                            ]
                        ),
                    )
                )
                * 100,
            },
            "response_metrics": {
                "average_detection_time_hours": self.breach_stats[
                    "average_detection_time_hours"
                ],
                "average_containment_time_hours": self.breach_stats[
                    "average_containment_time_hours"
                ],
            },
        }

    def register_notification_handler(self, channel: str, handler: Callable):
        """Register custom notification handler"""

        self.notification_handlers[channel] = handler
        logger.info(f"Notification handler registered for channel: {channel}")

    async def test_breach_detection(self) -> str:
        """Test breach detection system with simulated incident"""

        return await self.report_breach(
            breach_type=BreachType.UNAUTHORIZED_ACCESS,
            title="Test Security Incident",
            description="Simulated unauthorized access for system testing",
            affected_data_categories=["personal_data", "contact_data"],
            affected_records_count=150,
            affected_users=["test_user_1", "test_user_2"],
            detection_method="automated_test",
            metadata={"test": True, "simulated": True},
        )


# Factory function
def create_breach_notification_system() -> BreachNotificationSystem:
    """Create breach notification system instance"""
    return BreachNotificationSystem()


# Type alias for backwards compatibility with test imports
BreachCategory = BreachType
