"""
Regulatory Compliance Framework System
Implements GDPR, CCPA, SOX, HIPAA, and other regulatory compliance requirements
"""

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..attribution.cross_conversation_tracker import CrossConversationTracker
from ..capsules.specialized_capsules import create_specialized_capsule
from ..economic.fcde_engine import FCDEEngine
from ..engine.capsule_engine import CapsuleEngine

logger = logging.getLogger(__name__)


class RegulationType(Enum):
    """Types of regulatory frameworks"""

    GDPR = "gdpr"  # General Data Protection Regulation
    CCPA = "ccpa"  # California Consumer Privacy Act
    SOX = "sox"  # Sarbanes-Oxley Act
    HIPAA = "hipaa"  # Health Insurance Portability and Accountability Act
    PCI_DSS = "pci_dss"  # Payment Card Industry Data Security Standard
    ISO_27001 = "iso_27001"  # Information Security Management
    NIST = "nist"  # National Institute of Standards and Technology
    COPPA = "coppa"  # Children's Online Privacy Protection Act


class DataCategory(Enum):
    """Categories of data subject to regulation"""

    PERSONAL_DATA = "personal_data"
    SENSITIVE_DATA = "sensitive_data"
    HEALTH_DATA = "health_data"
    FINANCIAL_DATA = "financial_data"
    PAYMENT_DATA = "payment_data"
    BIOMETRIC_DATA = "biometric_data"
    LOCATION_DATA = "location_data"
    BEHAVIORAL_DATA = "behavioral_data"
    CHILDREN_DATA = "children_data"


class ProcessingPurpose(Enum):
    """Legal purposes for data processing"""

    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class ComplianceAction(Enum):
    """Types of compliance actions"""

    DATA_COLLECTION = "data_collection"
    DATA_PROCESSING = "data_processing"
    DATA_STORAGE = "data_storage"
    DATA_TRANSFER = "data_transfer"
    DATA_DELETION = "data_deletion"
    CONSENT_MANAGEMENT = "consent_management"
    ACCESS_REQUEST = "access_request"
    RECTIFICATION = "rectification"
    AUDIT_LOG = "audit_log"


@dataclass
class ComplianceRequirement:
    """Individual compliance requirement"""

    requirement_id: str
    regulation_type: RegulationType
    title: str
    description: str
    data_categories: List[DataCategory]
    mandatory: bool
    implementation_status: str
    risk_level: str
    due_date: Optional[datetime] = None
    responsible_party: Optional[str] = None
    evidence: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.due_date:
            data["due_date"] = self.due_date.isoformat()
        data["regulation_type"] = self.regulation_type.value
        data["data_categories"] = [cat.value for cat in self.data_categories]
        return data


@dataclass
class DataProcessingRecord:
    """Record of data processing activity"""

    record_id: str
    purpose: ProcessingPurpose
    data_categories: List[DataCategory]
    data_subjects: List[str]
    legal_basis: str
    retention_period: int
    processing_start: datetime
    processing_end: Optional[datetime] = None
    recipients: List[str] = None
    international_transfers: bool = False
    safeguards: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["purpose"] = self.purpose.value
        data["data_categories"] = [cat.value for cat in self.data_categories]
        data["processing_start"] = self.processing_start.isoformat()
        if self.processing_end:
            data["processing_end"] = self.processing_end.isoformat()
        return data


@dataclass
class ConsentRecord:
    """Record of user consent"""

    consent_id: str
    user_id: str
    purpose: ProcessingPurpose
    data_categories: List[DataCategory]
    consent_given: bool
    consent_timestamp: datetime
    consent_method: str
    withdrawal_timestamp: Optional[datetime] = None
    consent_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["purpose"] = self.purpose.value
        data["data_categories"] = [cat.value for cat in self.data_categories]
        data["consent_timestamp"] = self.consent_timestamp.isoformat()
        if self.withdrawal_timestamp:
            data["withdrawal_timestamp"] = self.withdrawal_timestamp.isoformat()
        return data


class ComplianceFramework(ABC):
    """Abstract base class for compliance frameworks"""

    @abstractmethod
    def get_regulation_type(self) -> RegulationType:
        """Get the regulation type this framework implements"""
        pass

    @abstractmethod
    async def validate_compliance(
        self, action: ComplianceAction, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate compliance for a specific action"""
        pass

    @abstractmethod
    async def get_requirements(self) -> List[ComplianceRequirement]:
        """Get all compliance requirements"""
        pass

    @abstractmethod
    async def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report"""
        pass


class GDPRFramework(ComplianceFramework):
    """GDPR compliance framework"""

    def __init__(self):
        self.requirements = [
            ComplianceRequirement(
                requirement_id="gdpr_001",
                regulation_type=RegulationType.GDPR,
                title="Lawful Basis for Processing",
                description="Establish lawful basis for processing personal data",
                data_categories=[DataCategory.PERSONAL_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="high",
            ),
            ComplianceRequirement(
                requirement_id="gdpr_002",
                regulation_type=RegulationType.GDPR,
                title="Data Subject Rights",
                description="Implement data subject rights (access, rectification, erasure)",
                data_categories=[
                    DataCategory.PERSONAL_DATA,
                    DataCategory.SENSITIVE_DATA,
                ],
                mandatory=True,
                implementation_status="implemented",
                risk_level="high",
            ),
            ComplianceRequirement(
                requirement_id="gdpr_003",
                regulation_type=RegulationType.GDPR,
                title="Data Protection Impact Assessment",
                description="Conduct DPIA for high-risk processing",
                data_categories=[
                    DataCategory.SENSITIVE_DATA,
                    DataCategory.BIOMETRIC_DATA,
                ],
                mandatory=True,
                implementation_status="in_progress",
                risk_level="medium",
            ),
            ComplianceRequirement(
                requirement_id="gdpr_004",
                regulation_type=RegulationType.GDPR,
                title="Privacy by Design",
                description="Implement privacy by design principles",
                data_categories=[DataCategory.PERSONAL_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="medium",
            ),
        ]

    def get_regulation_type(self) -> RegulationType:
        return RegulationType.GDPR

    async def validate_compliance(
        self, action: ComplianceAction, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate GDPR compliance"""
        validation_result = {
            "compliant": True,
            "violations": [],
            "recommendations": [],
            "required_actions": [],
        }

        # Check lawful basis
        if action in [
            ComplianceAction.DATA_COLLECTION,
            ComplianceAction.DATA_PROCESSING,
        ]:
            legal_basis = data.get("legal_basis")
            if not legal_basis:
                validation_result["compliant"] = False
                validation_result["violations"].append(
                    "Missing legal basis for processing"
                )
                validation_result["required_actions"].append("Establish lawful basis")

        # Check consent for sensitive data
        data_categories = data.get("data_categories", [])
        if DataCategory.SENSITIVE_DATA.value in data_categories:
            consent = data.get("consent")
            if not consent:
                validation_result["compliant"] = False
                validation_result["violations"].append(
                    "Missing explicit consent for sensitive data"
                )
                validation_result["required_actions"].append("Obtain explicit consent")

        # Check data minimization
        if action == ComplianceAction.DATA_COLLECTION:
            purpose = data.get("purpose")
            if not purpose:
                validation_result["recommendations"].append(
                    "Specify purpose for data collection"
                )

        # Check retention period
        retention_period = data.get("retention_period")
        if retention_period and retention_period > 365 * 7:  # 7 years
            validation_result["recommendations"].append(
                "Review retention period - consider if excessive"
            )

        return validation_result

    async def get_requirements(self) -> List[ComplianceRequirement]:
        return self.requirements

    async def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate GDPR compliance report"""
        implemented_count = sum(
            1 for req in self.requirements if req.implementation_status == "implemented"
        )
        total_count = len(self.requirements)

        return {
            "regulation": "GDPR",
            "compliance_score": (implemented_count / total_count) * 100,
            "implemented_requirements": implemented_count,
            "total_requirements": total_count,
            "high_risk_requirements": [
                req.to_dict() for req in self.requirements if req.risk_level == "high"
            ],
            "pending_requirements": [
                req.to_dict()
                for req in self.requirements
                if req.implementation_status != "implemented"
            ],
            "last_updated": datetime.now().isoformat(),
        }


class CCPAFramework(ComplianceFramework):
    """CCPA compliance framework"""

    def __init__(self):
        self.requirements = [
            ComplianceRequirement(
                requirement_id="ccpa_001",
                regulation_type=RegulationType.CCPA,
                title="Consumer Right to Know",
                description="Provide consumers with right to know what personal information is collected",
                data_categories=[DataCategory.PERSONAL_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="high",
            ),
            ComplianceRequirement(
                requirement_id="ccpa_002",
                regulation_type=RegulationType.CCPA,
                title="Consumer Right to Delete",
                description="Provide consumers with right to delete personal information",
                data_categories=[DataCategory.PERSONAL_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="high",
            ),
            ComplianceRequirement(
                requirement_id="ccpa_003",
                regulation_type=RegulationType.CCPA,
                title="Consumer Right to Opt-Out",
                description="Provide consumers with right to opt-out of sale of personal information",
                data_categories=[DataCategory.PERSONAL_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="medium",
            ),
        ]

    def get_regulation_type(self) -> RegulationType:
        return RegulationType.CCPA

    async def validate_compliance(
        self, action: ComplianceAction, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate CCPA compliance"""
        validation_result = {
            "compliant": True,
            "violations": [],
            "recommendations": [],
            "required_actions": [],
        }

        # Check consumer rights implementation
        if action == ComplianceAction.DATA_COLLECTION:
            privacy_notice = data.get("privacy_notice")
            if not privacy_notice:
                validation_result["recommendations"].append(
                    "Provide privacy notice at collection"
                )

        # Check opt-out mechanism
        if action == ComplianceAction.DATA_TRANSFER:
            is_sale = data.get("is_sale", False)
            if is_sale:
                opt_out_available = data.get("opt_out_available", False)
                if not opt_out_available:
                    validation_result["compliant"] = False
                    validation_result["violations"].append(
                        "Missing opt-out mechanism for sale of personal information"
                    )
                    validation_result["required_actions"].append(
                        "Implement opt-out mechanism"
                    )

        return validation_result

    async def get_requirements(self) -> List[ComplianceRequirement]:
        return self.requirements

    async def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate CCPA compliance report"""
        implemented_count = sum(
            1 for req in self.requirements if req.implementation_status == "implemented"
        )
        total_count = len(self.requirements)

        return {
            "regulation": "CCPA",
            "compliance_score": (implemented_count / total_count) * 100,
            "implemented_requirements": implemented_count,
            "total_requirements": total_count,
            "consumer_rights_status": "implemented",
            "opt_out_mechanism": "available",
            "last_updated": datetime.now().isoformat(),
        }


class SOXFramework(ComplianceFramework):
    """SOX compliance framework"""

    def __init__(self):
        self.requirements = [
            ComplianceRequirement(
                requirement_id="sox_001",
                regulation_type=RegulationType.SOX,
                title="Financial Reporting Controls",
                description="Implement internal controls for financial reporting",
                data_categories=[DataCategory.FINANCIAL_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="high",
            ),
            ComplianceRequirement(
                requirement_id="sox_002",
                regulation_type=RegulationType.SOX,
                title="Audit Trail",
                description="Maintain detailed audit trail of financial transactions",
                data_categories=[DataCategory.FINANCIAL_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="high",
            ),
            ComplianceRequirement(
                requirement_id="sox_003",
                regulation_type=RegulationType.SOX,
                title="Change Management",
                description="Implement change management controls for financial systems",
                data_categories=[DataCategory.FINANCIAL_DATA],
                mandatory=True,
                implementation_status="in_progress",
                risk_level="medium",
            ),
        ]

    def get_regulation_type(self) -> RegulationType:
        return RegulationType.SOX

    async def validate_compliance(
        self, action: ComplianceAction, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate SOX compliance"""
        validation_result = {
            "compliant": True,
            "violations": [],
            "recommendations": [],
            "required_actions": [],
        }

        # Check audit trail
        if action == ComplianceAction.DATA_PROCESSING:
            data_categories = data.get("data_categories", [])
            if DataCategory.FINANCIAL_DATA.value in data_categories:
                audit_log = data.get("audit_log", False)
                if not audit_log:
                    validation_result["compliant"] = False
                    validation_result["violations"].append(
                        "Missing audit trail for financial data processing"
                    )
                    validation_result["required_actions"].append("Enable audit logging")

        # Check segregation of duties
        if action == ComplianceAction.DATA_PROCESSING:
            approver = data.get("approver")
            processor = data.get("processor")
            if approver and processor and approver == processor:
                validation_result["violations"].append(
                    "Segregation of duties violation"
                )
                validation_result["required_actions"].append(
                    "Separate approval and processing roles"
                )

        return validation_result

    async def get_requirements(self) -> List[ComplianceRequirement]:
        return self.requirements

    async def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate SOX compliance report"""
        implemented_count = sum(
            1 for req in self.requirements if req.implementation_status == "implemented"
        )
        total_count = len(self.requirements)

        return {
            "regulation": "SOX",
            "compliance_score": (implemented_count / total_count) * 100,
            "implemented_requirements": implemented_count,
            "total_requirements": total_count,
            "financial_controls_status": "implemented",
            "audit_trail_status": "active",
            "last_updated": datetime.now().isoformat(),
        }


class HIPAAFramework(ComplianceFramework):
    """HIPAA compliance framework"""

    def __init__(self):
        self.requirements = [
            ComplianceRequirement(
                requirement_id="hipaa_001",
                regulation_type=RegulationType.HIPAA,
                title="Administrative Safeguards",
                description="Implement administrative safeguards for PHI protection",
                data_categories=[DataCategory.HEALTH_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="high",
            ),
            ComplianceRequirement(
                requirement_id="hipaa_002",
                regulation_type=RegulationType.HIPAA,
                title="Physical Safeguards",
                description="Implement physical safeguards for PHI protection",
                data_categories=[DataCategory.HEALTH_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="high",
            ),
            ComplianceRequirement(
                requirement_id="hipaa_003",
                regulation_type=RegulationType.HIPAA,
                title="Technical Safeguards",
                description="Implement technical safeguards including access controls and encryption",
                data_categories=[DataCategory.HEALTH_DATA],
                mandatory=True,
                implementation_status="in_progress",
                risk_level="high",
            ),
            ComplianceRequirement(
                requirement_id="hipaa_004",
                regulation_type=RegulationType.HIPAA,
                title="Breach Notification",
                description="Implement breach notification procedures for PHI",
                data_categories=[DataCategory.HEALTH_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="medium",
            ),
        ]

    def get_regulation_type(self) -> RegulationType:
        return RegulationType.HIPAA

    async def validate_compliance(
        self, action: ComplianceAction, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate HIPAA compliance"""
        validation_result = {
            "compliant": True,
            "violations": [],
            "recommendations": [],
            "required_actions": [],
        }

        # Check for PHI handling
        data_categories = data.get("data_categories", [])
        if DataCategory.HEALTH_DATA.value in data_categories:
            # Minimum necessary standard
            if not data.get("minimum_necessary"):
                validation_result["recommendations"].append(
                    "Apply minimum necessary standard for PHI access"
                )

            # Access controls
            if action == ComplianceAction.DATA_ACCESS:
                user_role = data.get("user_role")
                if not user_role:
                    validation_result["compliant"] = False
                    validation_result["violations"].append(
                        "Role-based access control required for PHI"
                    )
                    validation_result["required_actions"].append("Implement RBAC")

            # Audit logging
            if not data.get("audit_logging", False):
                validation_result["compliant"] = False
                validation_result["violations"].append(
                    "Audit logging required for PHI access"
                )
                validation_result["required_actions"].append("Enable audit logging")

            # Encryption requirements
            if action == ComplianceAction.DATA_STORAGE:
                encryption = data.get("encryption", False)
                if not encryption:
                    validation_result["violations"].append(
                        "PHI must be encrypted at rest"
                    )
                    validation_result["required_actions"].append("Implement encryption")

        return validation_result

    async def get_requirements(self) -> List[ComplianceRequirement]:
        return self.requirements

    async def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate HIPAA compliance report"""
        implemented_count = sum(
            1 for req in self.requirements if req.implementation_status == "implemented"
        )
        total_count = len(self.requirements)

        return {
            "regulation": "HIPAA",
            "compliance_score": (implemented_count / total_count) * 100,
            "implemented_requirements": implemented_count,
            "total_requirements": total_count,
            "safeguards_status": {
                "administrative": "implemented",
                "physical": "implemented",
                "technical": "in_progress",
            },
            "last_updated": datetime.now().isoformat(),
        }


class PCIDSSFramework(ComplianceFramework):
    """PCI DSS compliance framework"""

    def __init__(self):
        self.requirements = [
            ComplianceRequirement(
                requirement_id="pci_001",
                regulation_type=RegulationType.PCI_DSS,
                title="Install and Maintain Firewall Configuration",
                description="Build and maintain secure network and systems",
                data_categories=[DataCategory.PAYMENT_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="high",
            ),
            ComplianceRequirement(
                requirement_id="pci_002",
                regulation_type=RegulationType.PCI_DSS,
                title="Remove Default Passwords",
                description="Do not use vendor-supplied defaults for system passwords",
                data_categories=[DataCategory.PAYMENT_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="high",
            ),
            ComplianceRequirement(
                requirement_id="pci_003",
                regulation_type=RegulationType.PCI_DSS,
                title="Protect Stored Cardholder Data",
                description="Protect stored cardholder data through encryption",
                data_categories=[DataCategory.PAYMENT_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="high",
            ),
            ComplianceRequirement(
                requirement_id="pci_004",
                regulation_type=RegulationType.PCI_DSS,
                title="Encrypt Transmission of Cardholder Data",
                description="Encrypt transmission of cardholder data across open networks",
                data_categories=[DataCategory.PAYMENT_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="high",
            ),
        ]

    def get_regulation_type(self) -> RegulationType:
        return RegulationType.PCI_DSS

    async def validate_compliance(
        self, action: ComplianceAction, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate PCI DSS compliance"""
        validation_result = {
            "compliant": True,
            "violations": [],
            "recommendations": [],
            "required_actions": [],
        }

        # Check for payment data handling
        data_categories = data.get("data_categories", [])
        if DataCategory.PAYMENT_DATA.value in data_categories:
            # Encryption requirements
            if action in [
                ComplianceAction.DATA_STORAGE,
                ComplianceAction.DATA_TRANSFER,
            ]:
                encryption = data.get("encryption", False)
                if not encryption:
                    validation_result["compliant"] = False
                    validation_result["violations"].append(
                        "Payment data must be encrypted"
                    )
                    validation_result["required_actions"].append(
                        "Implement strong encryption"
                    )

            # Access control
            if action == ComplianceAction.DATA_ACCESS:
                access_control = data.get("access_control", False)
                if not access_control:
                    validation_result["compliant"] = False
                    validation_result["violations"].append(
                        "Role-based access control required for payment data"
                    )
                    validation_result["required_actions"].append(
                        "Implement access controls"
                    )

            # Network security
            if action == ComplianceAction.DATA_TRANSFER:
                secure_transmission = data.get("secure_transmission", False)
                if not secure_transmission:
                    validation_result["compliant"] = False
                    validation_result["violations"].append(
                        "Secure transmission required for payment data"
                    )
                    validation_result["required_actions"].append("Use secure protocols")

            # Vulnerability management
            vulnerability_scanning = data.get("vulnerability_scanning", False)
            if not vulnerability_scanning:
                validation_result["recommendations"].append(
                    "Regular vulnerability scanning recommended"
                )

        return validation_result

    async def get_requirements(self) -> List[ComplianceRequirement]:
        return self.requirements

    async def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate PCI DSS compliance report"""
        implemented_count = sum(
            1 for req in self.requirements if req.implementation_status == "implemented"
        )
        total_count = len(self.requirements)

        return {
            "regulation": "PCI DSS",
            "compliance_score": (implemented_count / total_count) * 100,
            "implemented_requirements": implemented_count,
            "total_requirements": total_count,
            "pci_requirements_status": {
                "network_security": "implemented",
                "access_control": "implemented",
                "data_protection": "implemented",
                "vulnerability_management": "in_progress",
            },
            "last_updated": datetime.now().isoformat(),
        }


class ISO27001Framework(ComplianceFramework):
    """ISO 27001 compliance framework"""

    def __init__(self):
        self.requirements = [
            ComplianceRequirement(
                requirement_id="iso_001",
                regulation_type=RegulationType.ISO_27001,
                title="Information Security Management System",
                description="Establish, implement, maintain and continually improve ISMS",
                data_categories=[
                    DataCategory.PERSONAL_DATA,
                    DataCategory.FINANCIAL_DATA,
                ],
                mandatory=True,
                implementation_status="implemented",
                risk_level="high",
            ),
            ComplianceRequirement(
                requirement_id="iso_002",
                regulation_type=RegulationType.ISO_27001,
                title="Information Security Policies",
                description="Establish information security policies and procedures",
                data_categories=[DataCategory.PERSONAL_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="medium",
            ),
            ComplianceRequirement(
                requirement_id="iso_003",
                regulation_type=RegulationType.ISO_27001,
                title="Risk Assessment and Treatment",
                description="Conduct information security risk assessment and treatment",
                data_categories=[
                    DataCategory.PERSONAL_DATA,
                    DataCategory.FINANCIAL_DATA,
                ],
                mandatory=True,
                implementation_status="in_progress",
                risk_level="high",
            ),
            ComplianceRequirement(
                requirement_id="iso_004",
                regulation_type=RegulationType.ISO_27001,
                title="Security Awareness and Training",
                description="Provide information security awareness and training",
                data_categories=[DataCategory.PERSONAL_DATA],
                mandatory=True,
                implementation_status="implemented",
                risk_level="medium",
            ),
        ]

    def get_regulation_type(self) -> RegulationType:
        return RegulationType.ISO_27001

    async def validate_compliance(
        self, action: ComplianceAction, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate ISO 27001 compliance"""
        validation_result = {
            "compliant": True,
            "violations": [],
            "recommendations": [],
            "required_actions": [],
        }

        # Risk assessment
        if action == ComplianceAction.DATA_PROCESSING:
            risk_assessment = data.get("risk_assessment", False)
            if not risk_assessment:
                validation_result["recommendations"].append(
                    "Conduct risk assessment for data processing activities"
                )

        # Security controls
        security_controls = data.get("security_controls", [])
        if not security_controls:
            validation_result["recommendations"].append(
                "Implement appropriate security controls"
            )

        # Incident management
        if action == ComplianceAction.AUDIT_LOG:
            incident_response = data.get("incident_response", False)
            if not incident_response:
                validation_result["recommendations"].append(
                    "Implement incident response procedures"
                )

        # Continuous monitoring
        monitoring = data.get("continuous_monitoring", False)
        if not monitoring:
            validation_result["recommendations"].append(
                "Implement continuous security monitoring"
            )

        # Documentation
        documentation = data.get("documentation", False)
        if not documentation:
            validation_result["violations"].append(
                "Proper documentation required for ISMS"
            )
            validation_result["required_actions"].append(
                "Maintain proper documentation"
            )

        return validation_result

    async def get_requirements(self) -> List[ComplianceRequirement]:
        return self.requirements

    async def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate ISO 27001 compliance report"""
        implemented_count = sum(
            1 for req in self.requirements if req.implementation_status == "implemented"
        )
        total_count = len(self.requirements)

        return {
            "regulation": "ISO 27001",
            "compliance_score": (implemented_count / total_count) * 100,
            "implemented_requirements": implemented_count,
            "total_requirements": total_count,
            "isms_status": {
                "policies": "implemented",
                "risk_management": "in_progress",
                "security_controls": "implemented",
                "monitoring": "implemented",
            },
            "certification_status": "in_progress",
            "last_updated": datetime.now().isoformat(),
        }


class RegulatoryComplianceSystem:
    """
    Comprehensive regulatory compliance management system
    """

    def __init__(
        self,
        capsule_engine: CapsuleEngine,
        attribution_tracker: CrossConversationTracker,
        fcde_engine: FCDEEngine,
    ):
        self.capsule_engine = capsule_engine
        self.attribution_tracker = attribution_tracker
        self.fcde_engine = fcde_engine

        # Compliance frameworks
        self.frameworks = {
            RegulationType.GDPR: GDPRFramework(),
            RegulationType.CCPA: CCPAFramework(),
            RegulationType.SOX: SOXFramework(),
            RegulationType.HIPAA: HIPAAFramework(),
            RegulationType.PCI_DSS: PCIDSSFramework(),
            RegulationType.ISO_27001: ISO27001Framework(),
        }

        # Data processing records
        self.processing_records = {}

        # Consent records
        self.consent_records = {}

        # Compliance audit log
        self.audit_log = []

        # Compliance statistics
        self.compliance_stats = {
            "total_validations": 0,
            "compliant_validations": 0,
            "violations_found": 0,
            "by_regulation": {reg.value: 0 for reg in RegulationType},
            "by_action": {action.value: 0 for action in ComplianceAction},
        }

    async def validate_action_compliance(
        self,
        action: ComplianceAction,
        data: Dict[str, Any],
        regulations: List[RegulationType] = None,
    ) -> Dict[str, Any]:
        """Validate compliance for a specific action"""

        if regulations is None:
            regulations = list(self.frameworks.keys())

        validation_results = {}
        overall_compliant = True
        all_violations = []
        all_recommendations = []
        all_required_actions = []

        self.compliance_stats["total_validations"] += 1
        self.compliance_stats["by_action"][action.value] += 1

        # Validate against each regulation
        for regulation in regulations:
            framework = self.frameworks.get(regulation)
            if framework:
                result = await framework.validate_compliance(action, data)
                validation_results[regulation.value] = result

                if not result["compliant"]:
                    overall_compliant = False
                    all_violations.extend(result["violations"])
                    all_required_actions.extend(result["required_actions"])

                all_recommendations.extend(result["recommendations"])
                self.compliance_stats["by_regulation"][regulation.value] += 1

        # Update statistics
        if overall_compliant:
            self.compliance_stats["compliant_validations"] += 1
        else:
            self.compliance_stats["violations_found"] += len(all_violations)

        # Create audit log entry
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action.value,
            "data_hash": hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest(),
            "regulations_checked": [reg.value for reg in regulations],
            "overall_compliant": overall_compliant,
            "violations_count": len(all_violations),
            "recommendations_count": len(all_recommendations),
        }
        self.audit_log.append(audit_entry)

        # Create compliance capsule
        await self._create_compliance_capsule(
            action, data, validation_results, overall_compliant
        )

        return {
            "overall_compliant": overall_compliant,
            "violations": all_violations,
            "recommendations": all_recommendations,
            "required_actions": all_required_actions,
            "detailed_results": validation_results,
            "audit_entry": audit_entry,
        }

    async def record_data_processing(
        self, processing_record: DataProcessingRecord
    ) -> str:
        """Record data processing activity"""

        record_id = processing_record.record_id
        self.processing_records[record_id] = processing_record

        # Validate processing compliance
        validation_data = {
            "purpose": processing_record.purpose.value,
            "data_categories": [cat.value for cat in processing_record.data_categories],
            "legal_basis": processing_record.legal_basis,
            "retention_period": processing_record.retention_period,
            "international_transfers": processing_record.international_transfers,
        }

        validation_result = await self.validate_action_compliance(
            ComplianceAction.DATA_PROCESSING, validation_data
        )

        # Log the processing activity
        logger.info(
            f"Recorded data processing: {record_id}, Compliant: {validation_result['overall_compliant']}"
        )

        return record_id

    async def record_consent(self, consent_record: ConsentRecord) -> str:
        """Record user consent"""

        consent_id = consent_record.consent_id
        self.consent_records[consent_id] = consent_record

        # Validate consent compliance
        validation_data = {
            "consent_given": consent_record.consent_given,
            "consent_method": consent_record.consent_method,
            "data_categories": [cat.value for cat in consent_record.data_categories],
            "purpose": consent_record.purpose.value,
        }

        validation_result = await self.validate_action_compliance(
            ComplianceAction.CONSENT_MANAGEMENT, validation_data
        )

        logger.info(
            f"Recorded consent: {consent_id}, Compliant: {validation_result['overall_compliant']}"
        )

        return consent_id

    async def handle_data_subject_request(
        self, request_type: str, user_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle data subject requests (access, rectification, erasure)"""

        request_id = f"dsr_{int(datetime.now().timestamp())}_{user_id}"

        # Find user's data processing records
        user_records = [
            record
            for record in self.processing_records.values()
            if user_id in record.data_subjects
        ]

        # Find user's consent records
        user_consents = [
            consent
            for consent in self.consent_records.values()
            if consent.user_id == user_id
        ]

        response = {
            "request_id": request_id,
            "request_type": request_type,
            "user_id": user_id,
            "status": "processed",
            "timestamp": datetime.now().isoformat(),
        }

        if request_type == "access":
            response["data"] = {
                "processing_records": [record.to_dict() for record in user_records],
                "consent_records": [consent.to_dict() for consent in user_consents],
            }
        elif request_type == "rectification":
            # Handle data rectification
            response["action"] = "Data rectification initiated"
        elif request_type == "erasure":
            # Handle data erasure
            response["action"] = "Data erasure initiated"

        # Validate request handling compliance
        validation_result = await self.validate_action_compliance(
            ComplianceAction.ACCESS_REQUEST, data
        )

        response["compliance_check"] = validation_result

        return response

    async def generate_compliance_report(
        self, regulations: List[RegulationType] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""

        if regulations is None:
            regulations = list(self.frameworks.keys())

        report = {
            "report_id": f"compliance_report_{int(datetime.now().timestamp())}",
            "generated_at": datetime.now().isoformat(),
            "scope": [reg.value for reg in regulations],
            "frameworks": {},
            "overall_statistics": self.compliance_stats.copy(),
            "data_processing_summary": {
                "total_records": len(self.processing_records),
                "by_purpose": {},
                "by_data_category": {},
            },
            "consent_management_summary": {
                "total_consents": len(self.consent_records),
                "active_consents": 0,
                "withdrawn_consents": 0,
            },
            "audit_summary": {
                "total_entries": len(self.audit_log),
                "recent_violations": [],
            },
        }

        # Generate framework-specific reports
        for regulation in regulations:
            framework = self.frameworks.get(regulation)
            if framework:
                framework_report = await framework.generate_compliance_report()
                report["frameworks"][regulation.value] = framework_report

        # Analyze data processing records
        for record in self.processing_records.values():
            purpose = record.purpose.value
            report["data_processing_summary"]["by_purpose"][purpose] = (
                report["data_processing_summary"]["by_purpose"].get(purpose, 0) + 1
            )

            for category in record.data_categories:
                cat_value = category.value
                report["data_processing_summary"]["by_data_category"][cat_value] = (
                    report["data_processing_summary"]["by_data_category"].get(
                        cat_value, 0
                    )
                    + 1
                )

        # Analyze consent records
        for consent in self.consent_records.values():
            if consent.withdrawal_timestamp:
                report["consent_management_summary"]["withdrawn_consents"] += 1
            else:
                report["consent_management_summary"]["active_consents"] += 1

        # Recent violations
        recent_violations = [
            entry
            for entry in self.audit_log[-100:]  # Last 100 entries
            if not entry["overall_compliant"]
        ]
        report["audit_summary"]["recent_violations"] = recent_violations

        return report

    async def _create_compliance_capsule(
        self,
        action: ComplianceAction,
        data: Dict[str, Any],
        validation_results: Dict[str, Any],
        overall_compliant: bool,
    ):
        """Create capsule for compliance validation"""

        capsule_data = {
            "type": "compliance_validation",
            "action": action.value,
            "input_data": data,
            "validation_results": validation_results,
            "overall_compliant": overall_compliant,
            "timestamp": datetime.now().isoformat(),
            "compliance_metadata": {
                "regulations_checked": list(validation_results.keys()),
                "violations_count": sum(
                    len(result["violations"]) for result in validation_results.values()
                ),
                "recommendations_count": sum(
                    len(result["recommendations"])
                    for result in validation_results.values()
                ),
            },
        }

        # Create specialized capsule
        capsule = create_specialized_capsule(
            capsule_type="compliance_validation",
            data=capsule_data,
            metadata={"source": "regulatory_compliance"},
        )

        # Store in capsule engine
        await self.capsule_engine.store_capsule(capsule)

    async def get_compliance_statistics(self) -> Dict[str, Any]:
        """Get compliance statistics"""
        stats = self.compliance_stats.copy()

        if stats["total_validations"] > 0:
            stats["compliance_rate"] = (
                stats["compliant_validations"] / stats["total_validations"]
            )
        else:
            stats["compliance_rate"] = 0.0

        return stats

    async def get_supported_regulations(self) -> List[str]:
        """Get list of supported regulations"""
        return [reg.value for reg in self.frameworks.keys()]

    async def get_data_processing_records(
        self, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get data processing records"""
        records = list(self.processing_records.values())

        if user_id:
            records = [record for record in records if user_id in record.data_subjects]

        return [record.to_dict() for record in records]

    async def get_consent_records(
        self, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get consent records"""
        records = list(self.consent_records.values())

        if user_id:
            records = [record for record in records if record.user_id == user_id]

        return [record.to_dict() for record in records]

    async def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        return self.audit_log[-limit:] if limit else self.audit_log
