"""
Cross-Border Data Transfer Compliance
GDPR Articles 44-49 compliant international data transfer validation and controls
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class TransferMechanism(Enum):
    """Legal mechanisms for international data transfers"""

    ADEQUACY_DECISION = "adequacy_decision"
    STANDARD_CONTRACTUAL_CLAUSES = "standard_contractual_clauses"
    BINDING_CORPORATE_RULES = "binding_corporate_rules"
    CERTIFICATION = "certification"
    CODE_OF_CONDUCT = "code_of_conduct"
    DEROGATION = "derogation"
    NO_MECHANISM = "no_mechanism"


class TransferRisk(Enum):
    """Risk levels for data transfers"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PROHIBITED = "prohibited"


class DataType(Enum):
    """Types of data being transferred"""

    PERSONAL_DATA = "personal_data"
    SENSITIVE_DATA = "sensitive_data"
    FINANCIAL_DATA = "financial_data"
    HEALTH_DATA = "health_data"
    BIOMETRIC_DATA = "biometric_data"
    GENETIC_DATA = "genetic_data"
    LOCATION_DATA = "location_data"
    COMMUNICATION_DATA = "communication_data"
    BEHAVIORAL_DATA = "behavioral_data"


class TransferPurpose(Enum):
    """Purposes for data transfers"""

    CONTRACT_PERFORMANCE = "contract_performance"
    CONSENT = "consent"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_INTEREST = "public_interest"
    LEGITIMATE_INTERESTS = "legitimate_interests"
    LEGAL_COMPLIANCE = "legal_compliance"
    SERVICE_PROVISION = "service_provision"
    TECHNICAL_SUPPORT = "technical_support"
    ANALYTICS = "analytics"
    BACKUP_STORAGE = "backup_storage"


@dataclass
class AdequacyDecision:
    """EU Commission adequacy decision for a country"""

    country_code: str
    country_name: str
    decision_date: datetime
    effective_date: datetime
    expiry_date: Optional[datetime] = None

    # Decision details
    commission_decision_reference: str
    scope_limitations: List[str] = field(default_factory=list)
    sector_limitations: List[str] = field(default_factory=list)

    # Status
    is_active: bool = True
    review_date: Optional[datetime] = None

    # Metadata
    decision_url: Optional[str] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class StandardContractualClauses:
    """Standard Contractual Clauses (SCCs) configuration"""

    scc_id: str
    scc_version: str  # "2021/914/EU" for latest EU SCCs
    effective_date: datetime

    # Parties
    data_controller: str
    data_processor: str
    controller_country: str
    processor_country: str

    # Transfer details
    data_categories: List[DataType]
    processing_purposes: List[TransferPurpose]
    data_subjects_categories: List[str]

    # Technical and organizational measures
    security_measures: List[str] = field(default_factory=list)
    access_controls: List[str] = field(default_factory=list)
    encryption_required: bool = True

    # Status
    signed_date: Optional[datetime] = None
    is_active: bool = True
    expiry_date: Optional[datetime] = None

    # Metadata
    contract_reference: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransferImpactAssessment:
    """Transfer Impact Assessment (TIA) for high-risk transfers"""

    tia_id: str
    transfer_id: str
    assessment_date: datetime
    assessed_by: str

    # Transfer details
    origin_country: str
    destination_country: str
    data_types: List[DataType]
    transfer_mechanism: TransferMechanism

    # Risk assessment
    legal_framework_score: float  # 0-1 scale
    surveillance_risk_score: float
    data_protection_score: float
    enforcement_score: float
    overall_risk_score: float
    risk_level: TransferRisk

    # Findings and recommendations
    risk_factors: List[str] = field(default_factory=list)
    mitigation_measures: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

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


@dataclass
class DataTransferRecord:
    """Individual data transfer record"""

    transfer_id: str
    transfer_date: datetime

    # Transfer parties
    data_controller: str
    data_processor: str
    origin_country: str
    destination_country: str

    # Data details
    data_types: List[DataType]
    data_categories: List[str]
    data_subjects_count: int
    data_volume_mb: float

    # Legal basis
    transfer_mechanism: TransferMechanism
    legal_basis: str
    purpose: TransferPurpose

    # Compliance validation
    adequacy_validated: bool = False
    scc_reference: Optional[str] = None
    tia_reference: Optional[str] = None
    compliance_validated: bool = False
    validation_date: Optional[datetime] = None

    # Security measures
    encryption_in_transit: bool = False
    encryption_at_rest: bool = False
    access_controls: List[str] = field(default_factory=list)
    audit_logging: bool = False

    # Status
    transfer_status: str = "pending"  # pending, approved, blocked, completed
    blocked_reason: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransferMonitoringAlert:
    """Transfer monitoring alert"""

    alert_id: str
    transfer_id: str
    alert_type: str
    severity: str  # low, medium, high, critical
    created_at: datetime

    # Alert details
    title: str
    description: str
    risk_factors: List[str] = field(default_factory=list)

    # Status
    status: str = "open"  # open, investigating, resolved, false_positive
    assigned_to: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    # Actions
    actions_taken: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class CrossBorderTransferController:
    """Cross-border data transfer compliance controller"""

    def __init__(self):
        self.adequacy_decisions: Dict[str, AdequacyDecision] = {}
        self.scc_configurations: Dict[str, StandardContractualClauses] = {}
        self.transfer_assessments: Dict[str, TransferImpactAssessment] = {}
        self.transfer_records: Dict[str, DataTransferRecord] = {}
        self.monitoring_alerts: Dict[str, TransferMonitoringAlert] = {}

        # Country risk profiles
        self.country_risk_profiles: Dict[str, Dict[str, float]] = {}

        # Statistics
        self.transfer_stats = {
            "total_transfers": 0,
            "approved_transfers": 0,
            "blocked_transfers": 0,
            "high_risk_transfers": 0,
            "adequacy_transfers": 0,
            "scc_transfers": 0,
        }

        # Initialize data
        self._initialize_adequacy_decisions()
        self._initialize_country_risk_profiles()

    def _initialize_adequacy_decisions(self):
        """Initialize EU adequacy decisions"""

        # Current EU adequacy decisions (simplified list)
        adequacy_countries = [
            {
                "country_code": "AD",
                "country_name": "Andorra",
                "decision_date": "2010-10-19",
                "decision_ref": "2010/625/EU",
            },
            {
                "country_code": "AR",
                "country_name": "Argentina",
                "decision_date": "2003-06-30",
                "decision_ref": "2003/490/EC",
            },
            {
                "country_code": "CA",
                "country_name": "Canada",
                "decision_date": "2001-12-20",
                "decision_ref": "2002/2/EC",
                "scope_limitations": ["Commercial organizations only"],
            },
            {
                "country_code": "FO",
                "country_name": "Faroe Islands",
                "decision_date": "2010-03-05",
                "decision_ref": "2010/146/EU",
            },
            {
                "country_code": "GG",
                "country_name": "Guernsey",
                "decision_date": "2003-11-21",
                "decision_ref": "2003/821/EC",
            },
            {
                "country_code": "IL",
                "country_name": "Israel",
                "decision_date": "2011-01-31",
                "decision_ref": "2011/61/EU",
            },
            {
                "country_code": "IM",
                "country_name": "Isle of Man",
                "decision_date": "2004-04-28",
                "decision_ref": "2004/411/EC",
            },
            {
                "country_code": "JP",
                "country_name": "Japan",
                "decision_date": "2019-01-23",
                "decision_ref": "2019/419/EU",
            },
            {
                "country_code": "JE",
                "country_name": "Jersey",
                "decision_date": "2008-05-08",
                "decision_ref": "2008/393/EC",
            },
            {
                "country_code": "NZ",
                "country_name": "New Zealand",
                "decision_date": "2013-12-19",
                "decision_ref": "2013/65/EU",
            },
            {
                "country_code": "KR",
                "country_name": "South Korea",
                "decision_date": "2021-12-17",
                "decision_ref": "2021/2484/EU",
            },
            {
                "country_code": "CH",
                "country_name": "Switzerland",
                "decision_date": "2000-07-26",
                "decision_ref": "2000/518/EC",
            },
            {
                "country_code": "GB",
                "country_name": "United Kingdom",
                "decision_date": "2021-06-28",
                "decision_ref": "2021/1772/EU",
                "expiry_date": "2025-06-27",  # Temporary adequacy
            },
            {
                "country_code": "UY",
                "country_name": "Uruguay",
                "decision_date": "2012-08-21",
                "decision_ref": "2012/484/EU",
            },
        ]

        for country_data in adequacy_countries:
            adequacy = AdequacyDecision(
                country_code=country_data["country_code"],
                country_name=country_data["country_name"],
                decision_date=datetime.fromisoformat(country_data["decision_date"]),
                effective_date=datetime.fromisoformat(country_data["decision_date"]),
                commission_decision_reference=country_data["decision_ref"],
                scope_limitations=country_data.get("scope_limitations", []),
                expiry_date=datetime.fromisoformat(country_data["expiry_date"])
                if country_data.get("expiry_date")
                else None,
            )

            self.adequacy_decisions[country_data["country_code"]] = adequacy

    def _initialize_country_risk_profiles(self):
        """Initialize country risk profiles for transfer assessment"""

        # Risk factors: legal_framework, surveillance_risk, data_protection, enforcement
        # Scale: 0.0 (high risk) to 1.0 (low risk)

        risk_profiles = {
            # High-protection countries
            "DE": {
                "legal_framework": 0.95,
                "surveillance_risk": 0.90,
                "data_protection": 0.95,
                "enforcement": 0.90,
            },
            "FR": {
                "legal_framework": 0.95,
                "surveillance_risk": 0.85,
                "data_protection": 0.95,
                "enforcement": 0.90,
            },
            "NL": {
                "legal_framework": 0.95,
                "surveillance_risk": 0.90,
                "data_protection": 0.95,
                "enforcement": 0.90,
            },
            "CH": {
                "legal_framework": 0.90,
                "surveillance_risk": 0.95,
                "data_protection": 0.90,
                "enforcement": 0.85,
            },
            "CA": {
                "legal_framework": 0.85,
                "surveillance_risk": 0.80,
                "data_protection": 0.85,
                "enforcement": 0.80,
            },
            # Medium-protection countries
            "US": {
                "legal_framework": 0.70,
                "surveillance_risk": 0.60,
                "data_protection": 0.75,
                "enforcement": 0.80,
            },
            "GB": {
                "legal_framework": 0.85,
                "surveillance_risk": 0.75,
                "data_protection": 0.85,
                "enforcement": 0.85,
            },
            "JP": {
                "legal_framework": 0.80,
                "surveillance_risk": 0.85,
                "data_protection": 0.80,
                "enforcement": 0.75,
            },
            "KR": {
                "legal_framework": 0.75,
                "surveillance_risk": 0.80,
                "data_protection": 0.75,
                "enforcement": 0.70,
            },
            "AU": {
                "legal_framework": 0.80,
                "surveillance_risk": 0.75,
                "data_protection": 0.80,
                "enforcement": 0.80,
            },
            # Lower-protection countries
            "IN": {
                "legal_framework": 0.65,
                "surveillance_risk": 0.70,
                "data_protection": 0.60,
                "enforcement": 0.55,
            },
            "BR": {
                "legal_framework": 0.70,
                "surveillance_risk": 0.75,
                "data_protection": 0.65,
                "enforcement": 0.60,
            },
            "MX": {
                "legal_framework": 0.65,
                "surveillance_risk": 0.80,
                "data_protection": 0.60,
                "enforcement": 0.55,
            },
            "SG": {
                "legal_framework": 0.75,
                "surveillance_risk": 0.70,
                "data_protection": 0.75,
                "enforcement": 0.80,
            },
            # High-risk countries
            "RU": {
                "legal_framework": 0.30,
                "surveillance_risk": 0.20,
                "data_protection": 0.40,
                "enforcement": 0.35,
            },
            "CN": {
                "legal_framework": 0.25,
                "surveillance_risk": 0.15,
                "data_protection": 0.30,
                "enforcement": 0.40,
            },
            "IR": {
                "legal_framework": 0.20,
                "surveillance_risk": 0.10,
                "data_protection": 0.25,
                "enforcement": 0.20,
            },
            "KP": {
                "legal_framework": 0.10,
                "surveillance_risk": 0.05,
                "data_protection": 0.15,
                "enforcement": 0.10,
            },
        }

        self.country_risk_profiles = risk_profiles

    def generate_transfer_id(self) -> str:
        """Generate unique transfer ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"xfer_{timestamp}_{hash(timestamp) % 10000:04d}"

    def generate_tia_id(self) -> str:
        """Generate unique TIA ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"tia_{timestamp}_{hash(timestamp) % 10000:04d}"

    def generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"alert_{timestamp}_{hash(timestamp) % 10000:04d}"

    async def validate_transfer(
        self,
        origin_country: str,
        destination_country: str,
        data_types: List[DataType],
        purpose: TransferPurpose,
        data_volume_mb: float = 0.0,
        data_subjects_count: int = 0,
    ) -> Dict[str, Any]:
        """Validate international data transfer"""

        try:
            transfer_id = self.generate_transfer_id()
            now = datetime.now(timezone.utc)

            # Check if transfer is within EU/EEA (no restrictions)
            eu_eea_countries = {
                "AT",
                "BE",
                "BG",
                "HR",
                "CY",
                "CZ",
                "DK",
                "EE",
                "FI",
                "FR",
                "DE",
                "GR",
                "HU",
                "IE",
                "IT",
                "LV",
                "LT",
                "LU",
                "MT",
                "NL",
                "PL",
                "PT",
                "RO",
                "SK",
                "SI",
                "ES",
                "SE",
                "IS",
                "LI",
                "NO",
            }

            if (
                origin_country in eu_eea_countries
                and destination_country in eu_eea_countries
            ):
                # Internal EU/EEA transfer - no additional restrictions
                return {
                    "transfer_id": transfer_id,
                    "approved": True,
                    "mechanism": TransferMechanism.NO_MECHANISM.value,
                    "risk_level": TransferRisk.LOW.value,
                    "message": "Internal EU/EEA transfer - no restrictions",
                    "compliance_requirements": [],
                }

            # Step 1: Check adequacy decision
            adequacy_result = await self._check_adequacy_decision(
                destination_country, data_types
            )

            if adequacy_result["has_adequacy"]:
                # Adequacy decision exists - transfer allowed
                validation_result = {
                    "transfer_id": transfer_id,
                    "approved": True,
                    "mechanism": TransferMechanism.ADEQUACY_DECISION.value,
                    "risk_level": TransferRisk.LOW.value,
                    "adequacy_decision": adequacy_result["decision"],
                    "message": "Transfer allowed under adequacy decision",
                    "compliance_requirements": adequacy_result.get("limitations", []),
                }
            else:
                # No adequacy decision - need alternative mechanism
                alternative_result = await self._evaluate_alternative_mechanisms(
                    origin_country, destination_country, data_types, purpose
                )

                validation_result = {
                    "transfer_id": transfer_id,
                    "approved": alternative_result["approved"],
                    "mechanism": alternative_result["mechanism"],
                    "risk_level": alternative_result["risk_level"],
                    "message": alternative_result["message"],
                    "compliance_requirements": alternative_result["requirements"],
                }

                # Check if TIA is required
                if alternative_result["tia_required"]:
                    tia_id = await self._initiate_transfer_impact_assessment(
                        transfer_id,
                        origin_country,
                        destination_country,
                        data_types,
                        alternative_result["mechanism"],
                    )
                    validation_result["tia_required"] = True
                    validation_result["tia_id"] = tia_id

            # Create transfer record
            transfer_record = DataTransferRecord(
                transfer_id=transfer_id,
                transfer_date=now,
                data_controller="UATP Controller",
                data_processor="UATP Processor",
                origin_country=origin_country,
                destination_country=destination_country,
                data_types=data_types,
                data_categories=[dt.value for dt in data_types],
                data_subjects_count=data_subjects_count,
                data_volume_mb=data_volume_mb,
                transfer_mechanism=TransferMechanism(validation_result["mechanism"]),
                legal_basis=validation_result["message"],
                purpose=purpose,
                adequacy_validated=adequacy_result["has_adequacy"],
                compliance_validated=validation_result["approved"],
                validation_date=now,
                transfer_status="approved"
                if validation_result["approved"]
                else "blocked",
                blocked_reason=None
                if validation_result["approved"]
                else validation_result["message"],
            )

            self.transfer_records[transfer_id] = transfer_record

            # Update statistics
            self.transfer_stats["total_transfers"] += 1
            if validation_result["approved"]:
                self.transfer_stats["approved_transfers"] += 1
                if (
                    validation_result["mechanism"]
                    == TransferMechanism.ADEQUACY_DECISION.value
                ):
                    self.transfer_stats["adequacy_transfers"] += 1
                elif (
                    validation_result["mechanism"]
                    == TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES.value
                ):
                    self.transfer_stats["scc_transfers"] += 1
            else:
                self.transfer_stats["blocked_transfers"] += 1

            if validation_result["risk_level"] == TransferRisk.HIGH.value:
                self.transfer_stats["high_risk_transfers"] += 1

            logger.info(
                f"Transfer validation completed: {transfer_id} - Approved: {validation_result['approved']}"
            )

            return validation_result

        except Exception as e:
            logger.error(f"Transfer validation failed: {e}")
            return {
                "approved": False,
                "error": str(e),
                "mechanism": TransferMechanism.NO_MECHANISM.value,
                "risk_level": TransferRisk.PROHIBITED.value,
            }

    async def _check_adequacy_decision(
        self, destination_country: str, data_types: List[DataType]
    ) -> Dict[str, Any]:
        """Check if destination country has adequacy decision"""

        adequacy = self.adequacy_decisions.get(destination_country)

        if not adequacy:
            return {"has_adequacy": False}

        # Check if adequacy decision is still valid
        now = datetime.now(timezone.utc)
        if adequacy.expiry_date and adequacy.expiry_date < now:
            return {"has_adequacy": False, "reason": "Adequacy decision expired"}

        if not adequacy.is_active:
            return {"has_adequacy": False, "reason": "Adequacy decision revoked"}

        # Check scope limitations
        limitations = []

        # Check sector limitations
        sensitive_data_types = {
            DataType.SENSITIVE_DATA,
            DataType.HEALTH_DATA,
            DataType.BIOMETRIC_DATA,
        }
        if (
            any(dt in sensitive_data_types for dt in data_types)
            and adequacy.sector_limitations
        ):
            limitations.extend(adequacy.sector_limitations)

        # Check scope limitations
        if adequacy.scope_limitations:
            limitations.extend(adequacy.scope_limitations)

        return {
            "has_adequacy": True,
            "decision": {
                "country": adequacy.country_name,
                "decision_date": adequacy.decision_date.isoformat(),
                "reference": adequacy.commission_decision_reference,
                "expiry_date": adequacy.expiry_date.isoformat()
                if adequacy.expiry_date
                else None,
            },
            "limitations": limitations,
        }

    async def _evaluate_alternative_mechanisms(
        self,
        origin_country: str,
        destination_country: str,
        data_types: List[DataType],
        purpose: TransferPurpose,
    ) -> Dict[str, Any]:
        """Evaluate alternative transfer mechanisms"""

        # Get country risk profile
        risk_profile = self.country_risk_profiles.get(
            destination_country,
            {
                "legal_framework": 0.50,
                "surveillance_risk": 0.50,
                "data_protection": 0.50,
                "enforcement": 0.50,
            },
        )

        # Calculate overall risk score
        overall_risk = sum(risk_profile.values()) / len(risk_profile)

        # Determine risk level
        if overall_risk >= 0.80:
            risk_level = TransferRisk.LOW
        elif overall_risk >= 0.60:
            risk_level = TransferRisk.MEDIUM
        elif overall_risk >= 0.40:
            risk_level = TransferRisk.HIGH
        else:
            risk_level = TransferRisk.PROHIBITED

        # Check if transfer is prohibited
        if risk_level == TransferRisk.PROHIBITED:
            return {
                "approved": False,
                "mechanism": TransferMechanism.NO_MECHANISM.value,
                "risk_level": risk_level.value,
                "message": "Transfer prohibited due to inadequate data protection",
                "requirements": ["Transfer blocked"],
                "tia_required": False,
            }

        # Evaluate Standard Contractual Clauses (SCCs)
        scc_viable = await self._evaluate_scc_viability(
            destination_country, data_types, risk_level
        )

        if scc_viable["viable"]:
            requirements = [
                "Standard Contractual Clauses (SCCs) must be implemented",
                "Technical and organizational measures required",
                "Regular compliance monitoring needed",
            ]

            if risk_level == TransferRisk.HIGH:
                requirements.extend(
                    [
                        "Enhanced security measures required",
                        "Data localization restrictions may apply",
                        "Additional safeguards needed",
                    ]
                )

            return {
                "approved": True,
                "mechanism": TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES.value,
                "risk_level": risk_level.value,
                "message": "Transfer allowed under Standard Contractual Clauses",
                "requirements": requirements,
                "tia_required": risk_level in [TransferRisk.MEDIUM, TransferRisk.HIGH],
                "scc_requirements": scc_viable["requirements"],
            }

        # Check derogations (Article 49)
        derogation_result = await self._evaluate_derogations(purpose, data_types)

        if derogation_result["applicable"]:
            return {
                "approved": True,
                "mechanism": TransferMechanism.DEROGATION.value,
                "risk_level": risk_level.value,
                "message": f"Transfer allowed under derogation: {derogation_result['basis']}",
                "requirements": derogation_result["requirements"],
                "tia_required": False,
            }

        # No viable mechanism found
        return {
            "approved": False,
            "mechanism": TransferMechanism.NO_MECHANISM.value,
            "risk_level": risk_level.value,
            "message": "No viable transfer mechanism available",
            "requirements": ["Transfer blocked - implement additional safeguards"],
            "tia_required": False,
        }

    async def _evaluate_scc_viability(
        self,
        destination_country: str,
        data_types: List[DataType],
        risk_level: TransferRisk,
    ) -> Dict[str, Any]:
        """Evaluate if SCCs are viable for transfer"""

        # SCCs generally viable unless country actively blocks them
        blocked_countries = {
            "CN",
            "RU",
            "IR",
            "KP",
        }  # Countries that may block or restrict SCCs

        if destination_country in blocked_countries:
            return {
                "viable": False,
                "reason": "Destination country restrictions on SCCs",
            }

        # Additional requirements based on risk level and data sensitivity
        requirements = [
            "EU Commission SCCs (2021/914/EU) must be used",
            "Data Protection Impact Assessment may be required",
            "Technical safeguards must be implemented",
        ]

        # Sensitive data requirements
        sensitive_data = {
            DataType.SENSITIVE_DATA,
            DataType.HEALTH_DATA,
            DataType.BIOMETRIC_DATA,
            DataType.GENETIC_DATA,
        }
        if any(dt in sensitive_data for dt in data_types):
            requirements.extend(
                [
                    "Enhanced encryption required for sensitive data",
                    "Access controls must be strictly enforced",
                    "Additional audit requirements",
                ]
            )

        # High-risk country requirements
        if risk_level == TransferRisk.HIGH:
            requirements.extend(
                [
                    "Government access assessment required",
                    "Additional safeguards needed",
                    "Regular compliance reviews mandatory",
                ]
            )

        return {
            "viable": True,
            "requirements": requirements,
        }

    async def _evaluate_derogations(
        self,
        purpose: TransferPurpose,
        data_types: List[DataType],
    ) -> Dict[str, Any]:
        """Evaluate if Article 49 derogations apply"""

        # Article 49 derogations are restrictive and case-specific

        if purpose == TransferPurpose.CONSENT:
            return {
                "applicable": True,
                "basis": "Article 49(1)(a) - Explicit consent",
                "requirements": [
                    "Explicit consent must be obtained",
                    "Consent must be informed and specific",
                    "Transfer must be occasional and limited",
                ],
            }

        if purpose == TransferPurpose.CONTRACT_PERFORMANCE:
            return {
                "applicable": True,
                "basis": "Article 49(1)(b) - Contract performance",
                "requirements": [
                    "Transfer must be necessary for contract performance",
                    "Transfer must be occasional",
                    "Limited data volume",
                ],
            }

        if purpose == TransferPurpose.VITAL_INTERESTS:
            return {
                "applicable": True,
                "basis": "Article 49(1)(c) - Vital interests",
                "requirements": [
                    "Vital interests of data subject at stake",
                    "No other means available",
                    "Urgent transfer required",
                ],
            }

        # Other derogations are very specific and rare
        return {"applicable": False}

    async def _initiate_transfer_impact_assessment(
        self,
        transfer_id: str,
        origin_country: str,
        destination_country: str,
        data_types: List[DataType],
        mechanism: str,
    ) -> str:
        """Initiate Transfer Impact Assessment"""

        tia_id = self.generate_tia_id()
        now = datetime.now(timezone.utc)

        # Get country risk profile for assessment
        risk_profile = self.country_risk_profiles.get(
            destination_country,
            {
                "legal_framework": 0.50,
                "surveillance_risk": 0.50,
                "data_protection": 0.50,
                "enforcement": 0.50,
            },
        )

        # Calculate risk scores
        legal_framework_score = risk_profile["legal_framework"]
        surveillance_risk_score = risk_profile["surveillance_risk"]
        data_protection_score = risk_profile["data_protection"]
        enforcement_score = risk_profile["enforcement"]

        overall_risk_score = (
            legal_framework_score * 0.3
            + surveillance_risk_score * 0.25
            + data_protection_score * 0.25
            + enforcement_score * 0.20
        )

        # Determine risk level
        if overall_risk_score >= 0.80:
            risk_level = TransferRisk.LOW
        elif overall_risk_score >= 0.60:
            risk_level = TransferRisk.MEDIUM
        elif overall_risk_score >= 0.40:
            risk_level = TransferRisk.HIGH
        else:
            risk_level = TransferRisk.PROHIBITED

        # Identify risk factors
        risk_factors = []
        if legal_framework_score < 0.70:
            risk_factors.append("Inadequate legal framework")
        if surveillance_risk_score < 0.70:
            risk_factors.append("High surveillance risk")
        if data_protection_score < 0.70:
            risk_factors.append("Weak data protection laws")
        if enforcement_score < 0.70:
            risk_factors.append("Poor enforcement mechanisms")

        # Generate mitigation measures
        mitigation_measures = []
        if risk_level in [TransferRisk.MEDIUM, TransferRisk.HIGH]:
            mitigation_measures.extend(
                [
                    "Implement end-to-end encryption",
                    "Establish data localization restrictions",
                    "Implement access controls and monitoring",
                    "Regular compliance audits required",
                ]
            )

        if risk_level == TransferRisk.HIGH:
            mitigation_measures.extend(
                [
                    "Consider data minimization",
                    "Implement government access procedures",
                    "Establish data subject notification procedures",
                ]
            )

        # Create TIA record
        tia = TransferImpactAssessment(
            tia_id=tia_id,
            transfer_id=transfer_id,
            assessment_date=now,
            assessed_by="automated_system",
            origin_country=origin_country,
            destination_country=destination_country,
            data_types=data_types,
            transfer_mechanism=TransferMechanism(mechanism),
            legal_framework_score=legal_framework_score,
            surveillance_risk_score=surveillance_risk_score,
            data_protection_score=data_protection_score,
            enforcement_score=enforcement_score,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            risk_factors=risk_factors,
            mitigation_measures=mitigation_measures,
            next_review_date=now + timedelta(days=365),  # Annual review
        )

        # Auto-approve low and medium risk transfers
        if risk_level in [TransferRisk.LOW, TransferRisk.MEDIUM]:
            tia.approved = True
            tia.approved_by = "automated_system"
            tia.approval_date = now
            tia.approval_conditions = mitigation_measures

        self.transfer_assessments[tia_id] = tia

        logger.info(f"TIA initiated: {tia_id} - Risk level: {risk_level.value}")

        return tia_id

    async def get_transfer_status(self, transfer_id: str) -> Dict[str, Any]:
        """Get status of data transfer"""

        if transfer_id not in self.transfer_records:
            return {"error": "Transfer not found"}

        transfer = self.transfer_records[transfer_id]

        result = {
            "transfer_id": transfer.transfer_id,
            "status": transfer.transfer_status,
            "origin_country": transfer.origin_country,
            "destination_country": transfer.destination_country,
            "data_types": [dt.value for dt in transfer.data_types],
            "transfer_mechanism": transfer.transfer_mechanism.value,
            "compliance_validated": transfer.compliance_validated,
            "validation_date": transfer.validation_date.isoformat()
            if transfer.validation_date
            else None,
        }

        if transfer.blocked_reason:
            result["blocked_reason"] = transfer.blocked_reason

        if transfer.tia_reference:
            result["tia_reference"] = transfer.tia_reference

        return result

    async def get_compliance_dashboard(self) -> Dict[str, Any]:
        """Get transfer compliance dashboard"""

        now = datetime.now(timezone.utc)

        # Recent transfers (last 30 days)
        thirty_days_ago = now - timedelta(days=30)
        recent_transfers = [
            t
            for t in self.transfer_records.values()
            if t.transfer_date >= thirty_days_ago
        ]

        # Risk distribution
        risk_distribution = {}
        for risk_level in TransferRisk:
            count = len(
                [
                    t
                    for t in recent_transfers
                    if self._get_transfer_risk_level(t.destination_country)
                    == risk_level
                ]
            )
            risk_distribution[risk_level.value] = count

        # Mechanism distribution
        mechanism_distribution = {}
        for mechanism in TransferMechanism:
            count = len(
                [t for t in recent_transfers if t.transfer_mechanism == mechanism]
            )
            mechanism_distribution[mechanism.value] = count

        return {
            "dashboard_generated_at": now.isoformat(),
            "summary": self.transfer_stats,
            "recent_activity": {
                "transfers_last_30_days": len(recent_transfers),
                "approved_last_30_days": len(
                    [t for t in recent_transfers if t.transfer_status == "approved"]
                ),
                "blocked_last_30_days": len(
                    [t for t in recent_transfers if t.transfer_status == "blocked"]
                ),
            },
            "risk_distribution": risk_distribution,
            "mechanism_distribution": mechanism_distribution,
            "adequacy_countries": len(self.adequacy_decisions),
            "active_tias": len(
                [tia for tia in self.transfer_assessments.values() if not tia.approved]
            ),
            "monitoring_alerts": len(
                [
                    alert
                    for alert in self.monitoring_alerts.values()
                    if alert.status == "open"
                ]
            ),
        }

    def _get_transfer_risk_level(self, destination_country: str) -> TransferRisk:
        """Get risk level for destination country"""

        if destination_country in self.adequacy_decisions:
            return TransferRisk.LOW

        risk_profile = self.country_risk_profiles.get(
            destination_country,
            {
                "legal_framework": 0.50,
                "surveillance_risk": 0.50,
                "data_protection": 0.50,
                "enforcement": 0.50,
            },
        )

        overall_risk = sum(risk_profile.values()) / len(risk_profile)

        if overall_risk >= 0.80:
            return TransferRisk.LOW
        elif overall_risk >= 0.60:
            return TransferRisk.MEDIUM
        elif overall_risk >= 0.40:
            return TransferRisk.HIGH
        else:
            return TransferRisk.PROHIBITED

    async def monitor_ongoing_transfers(self):
        """Monitor ongoing transfers for compliance changes"""

        # This would run periodically to check for:
        # - Changes in adequacy decisions
        # - New country risk assessments
        # - Expired SCCs
        # - Required TIA reviews

        now = datetime.now(timezone.utc)
        alerts_created = 0

        # Check for expired adequacy decisions
        for country_code, adequacy in self.adequacy_decisions.items():
            if adequacy.expiry_date and adequacy.expiry_date <= now + timedelta(
                days=90
            ):  # 90 days warning
                alert_id = self.generate_alert_id()
                alert = TransferMonitoringAlert(
                    alert_id=alert_id,
                    transfer_id="",  # System-wide alert
                    alert_type="adequacy_expiry",
                    severity="high",
                    created_at=now,
                    title=f"Adequacy Decision Expiring: {adequacy.country_name}",
                    description=f"Adequacy decision for {adequacy.country_name} expires on {adequacy.expiry_date}",
                    recommendations=[
                        "Monitor EU Commission updates",
                        "Prepare alternative transfer mechanisms",
                        "Review affected transfers",
                    ],
                )
                self.monitoring_alerts[alert_id] = alert
                alerts_created += 1

        # Check TIAs requiring review
        for tia in self.transfer_assessments.values():
            if tia.next_review_date and tia.next_review_date <= now:
                alert_id = self.generate_alert_id()
                alert = TransferMonitoringAlert(
                    alert_id=alert_id,
                    transfer_id=tia.transfer_id,
                    alert_type="tia_review_due",
                    severity="medium",
                    created_at=now,
                    title="TIA Review Required",
                    description=f"Transfer Impact Assessment {tia.tia_id} requires review",
                    recommendations=[
                        "Reassess country risk profile",
                        "Review transfer necessity",
                        "Update mitigation measures",
                    ],
                )
                self.monitoring_alerts[alert_id] = alert
                alerts_created += 1

        logger.info(f"Transfer monitoring completed - {alerts_created} alerts created")

        return alerts_created


# Factory function
def create_cross_border_transfer_controller() -> CrossBorderTransferController:
    """Create cross-border transfer controller instance"""
    return CrossBorderTransferController()
