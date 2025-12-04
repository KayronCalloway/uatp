"""
Financial Compliance Framework
Complete KYC/AML compliance system for payment processing
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class KYCStatus(Enum):
    """KYC verification status"""

    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REQUIRES_ADDITIONAL_INFO = "requires_additional_info"


class RiskLevel(Enum):
    """Customer risk levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PROHIBITED = "prohibited"


class TransactionRiskFlag(Enum):
    """Transaction risk flags"""

    UNUSUAL_AMOUNT = "unusual_amount"
    FREQUENT_TRANSACTIONS = "frequent_transactions"
    HIGH_VELOCITY = "high_velocity"
    STRUCTURING = "structuring"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    SANCTIONS_MATCH = "sanctions_match"
    PEP_MATCH = "pep_match"
    ADVERSE_MEDIA = "adverse_media"


class SARStatus(Enum):
    """Suspicious Activity Report status"""

    NOT_REQUIRED = "not_required"
    PENDING_REVIEW = "pending_review"
    FILED = "filed"
    REJECTED = "rejected"


@dataclass
class IdentityDocument:
    """Identity document for KYC verification"""

    document_type: str  # passport, driver_license, national_id
    document_number: str
    issuing_country: str
    issuing_authority: str
    issue_date: datetime
    expiry_date: datetime
    document_hash: str  # SHA-256 hash of document image
    verification_status: str = "pending"
    verification_score: float = 0.0
    extracted_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomerRecord:
    """Customer KYC record"""

    customer_id: str
    user_id: str
    full_name: str
    date_of_birth: datetime
    nationality: str
    country_of_residence: str

    # Contact information
    address_line1: str
    city: str
    state_province: str
    postal_code: str
    phone_number: str
    email: str
    address_line2: Optional[str] = None

    # KYC status
    kyc_status: KYCStatus = KYCStatus.PENDING
    risk_level: RiskLevel = RiskLevel.MEDIUM
    verification_date: Optional[datetime] = None
    last_review_date: Optional[datetime] = None
    next_review_date: Optional[datetime] = None

    # Documents
    identity_documents: List[IdentityDocument] = field(default_factory=list)

    # Enhanced Due Diligence
    is_pep: bool = False  # Politically Exposed Person
    sanctions_check: bool = False
    adverse_media_check: bool = False
    source_of_funds: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransactionMonitoringRule:
    """Transaction monitoring rule"""

    rule_id: str
    rule_name: str
    description: str
    risk_flag: TransactionRiskFlag
    threshold_amount: Optional[Decimal] = None
    threshold_frequency: Optional[int] = None
    time_window_hours: Optional[int] = None
    enabled: bool = True
    severity: str = "medium"  # low, medium, high, critical


@dataclass
class SuspiciousTransaction:
    """Suspicious transaction record"""

    alert_id: str
    transaction_id: str
    customer_id: str
    amount: Decimal
    currency: str
    transaction_date: datetime

    # Risk assessment
    risk_flags: List[TransactionRiskFlag]
    risk_score: float
    triggered_rules: List[str]

    # Investigation
    investigation_status: str = "pending"  # pending, investigating, resolved, escalated
    assigned_investigator: Optional[str] = None
    investigation_notes: List[str] = field(default_factory=list)

    # SAR filing
    sar_status: SARStatus = SARStatus.NOT_REQUIRED
    sar_filed_date: Optional[datetime] = None
    sar_reference: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ComplianceAuditRecord:
    """Compliance audit record"""

    audit_id: str
    audit_type: str  # kyc_verification, transaction_monitoring, sar_filing
    customer_id: Optional[str] = None
    transaction_id: Optional[str] = None
    auditor: str = "system"
    audit_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    compliance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class FinancialComplianceEngine:
    """Complete financial compliance engine"""

    def __init__(self):
        self.customer_records: Dict[str, CustomerRecord] = {}
        self.monitoring_rules: Dict[str, TransactionMonitoringRule] = {}
        self.suspicious_transactions: Dict[str, SuspiciousTransaction] = {}
        self.audit_records: List[ComplianceAuditRecord] = []

        # Sanctions and PEP lists (would be external services in production)
        self.sanctions_list: List[str] = []
        self.pep_list: List[str] = []

        # Statistics
        self.compliance_stats = {
            "kyc_verifications": 0,
            "kyc_rejections": 0,
            "suspicious_transactions": 0,
            "sars_filed": 0,
            "compliance_score": 0.0,
        }

        self._initialize_monitoring_rules()

    def _initialize_monitoring_rules(self):
        """Initialize default transaction monitoring rules"""

        default_rules = [
            TransactionMonitoringRule(
                rule_id="large_transaction",
                rule_name="Large Transaction",
                description="Transaction amount exceeds threshold",
                risk_flag=TransactionRiskFlag.UNUSUAL_AMOUNT,
                threshold_amount=Decimal("10000.00"),
                severity="high",
            ),
            TransactionMonitoringRule(
                rule_id="frequent_transactions",
                rule_name="Frequent Transactions",
                description="Multiple transactions in short time period",
                risk_flag=TransactionRiskFlag.FREQUENT_TRANSACTIONS,
                threshold_frequency=10,
                time_window_hours=24,
                severity="medium",
            ),
            TransactionMonitoringRule(
                rule_id="high_velocity",
                rule_name="High Velocity Transactions",
                description="High frequency of transactions from same user",
                risk_flag=TransactionRiskFlag.HIGH_VELOCITY,
                threshold_frequency=5,
                time_window_hours=1,
                severity="high",
            ),
            TransactionMonitoringRule(
                rule_id="structuring_pattern",
                rule_name="Structuring Pattern",
                description="Multiple transactions just below reporting threshold",
                risk_flag=TransactionRiskFlag.STRUCTURING,
                threshold_amount=Decimal("9500.00"),
                threshold_frequency=3,
                time_window_hours=24,
                severity="critical",
            ),
        ]

        for rule in default_rules:
            self.monitoring_rules[rule.rule_id] = rule

    def generate_customer_id(self) -> str:
        """Generate unique customer ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"cust_{timestamp}_{hash(timestamp) % 10000:04d}"

    def generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"alert_{timestamp}_{hash(timestamp) % 10000:04d}"

    def generate_audit_id(self) -> str:
        """Generate unique audit ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"audit_{timestamp}_{hash(timestamp) % 10000:04d}"

    async def initiate_kyc_verification(
        self,
        user_id: str,
        personal_info: Dict[str, Any],
        identity_documents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Initiate KYC verification for a customer"""

        try:
            # Create customer record
            customer_id = self.generate_customer_id()

            # Process identity documents
            processed_documents = []
            for doc_info in identity_documents:
                document = IdentityDocument(
                    document_type=doc_info["type"],
                    document_number=doc_info["number"],
                    issuing_country=doc_info["issuing_country"],
                    issuing_authority=doc_info.get("issuing_authority", ""),
                    issue_date=datetime.fromisoformat(doc_info["issue_date"]),
                    expiry_date=datetime.fromisoformat(doc_info["expiry_date"]),
                    document_hash=hashlib.sha256(
                        doc_info["document_data"].encode()
                    ).hexdigest(),
                )

                # Perform document verification
                verification_result = await self._verify_identity_document(document)
                document.verification_status = verification_result["status"]
                document.verification_score = verification_result["score"]
                document.extracted_data = verification_result["extracted_data"]

                processed_documents.append(document)

            # Create customer record
            customer_record = CustomerRecord(
                customer_id=customer_id,
                user_id=user_id,
                full_name=personal_info["full_name"],
                date_of_birth=datetime.fromisoformat(personal_info["date_of_birth"]),
                nationality=personal_info["nationality"],
                country_of_residence=personal_info["country_of_residence"],
                address_line1=personal_info["address_line1"],
                address_line2=personal_info.get("address_line2"),
                city=personal_info["city"],
                state_province=personal_info["state_province"],
                postal_code=personal_info["postal_code"],
                phone_number=personal_info["phone_number"],
                email=personal_info["email"],
                identity_documents=processed_documents,
            )

            # Perform risk assessment
            risk_assessment = await self._assess_customer_risk(customer_record)
            customer_record.risk_level = risk_assessment["risk_level"]
            customer_record.is_pep = risk_assessment["is_pep"]
            customer_record.sanctions_check = risk_assessment["sanctions_clear"]
            customer_record.adverse_media_check = risk_assessment["adverse_media_clear"]

            # Determine KYC status
            if all(doc.verification_score >= 0.8 for doc in processed_documents):
                if customer_record.risk_level != RiskLevel.PROHIBITED:
                    customer_record.kyc_status = KYCStatus.VERIFIED
                    customer_record.verification_date = datetime.now(timezone.utc)
                    customer_record.next_review_date = datetime.now(
                        timezone.utc
                    ) + timedelta(days=365)
                else:
                    customer_record.kyc_status = KYCStatus.REJECTED
            else:
                customer_record.kyc_status = KYCStatus.REQUIRES_ADDITIONAL_INFO

            # Store customer record
            self.customer_records[customer_id] = customer_record

            # Update statistics
            self.compliance_stats["kyc_verifications"] += 1
            if customer_record.kyc_status == KYCStatus.REJECTED:
                self.compliance_stats["kyc_rejections"] += 1

            # Create audit record
            await self._create_audit_record(
                audit_type="kyc_verification",
                customer_id=customer_id,
                findings=[f"KYC status: {customer_record.kyc_status.value}"],
                compliance_score=min(
                    doc.verification_score for doc in processed_documents
                ),
            )

            logger.info(
                f"KYC verification initiated: {customer_id} - Status: {customer_record.kyc_status.value}"
            )

            return {
                "success": True,
                "customer_id": customer_id,
                "kyc_status": customer_record.kyc_status.value,
                "risk_level": customer_record.risk_level.value,
                "verification_score": min(
                    doc.verification_score for doc in processed_documents
                ),
                "next_review_date": customer_record.next_review_date.isoformat()
                if customer_record.next_review_date
                else None,
                "required_actions": self._get_required_actions(customer_record),
            }

        except Exception as e:
            logger.error(f"KYC verification failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "required_actions": ["Contact compliance team"],
            }

    async def _verify_identity_document(
        self, document: IdentityDocument
    ) -> Dict[str, Any]:
        """Verify identity document (mock implementation)"""

        # In production, this would integrate with:
        # - Document verification services (Jumio, Onfido, etc.)
        # - Government databases
        # - OCR and ML verification systems

        # Mock verification based on document type and data quality
        base_score = 0.7

        # Check document expiry
        if document.expiry_date < datetime.now(timezone.utc):
            return {
                "status": "rejected",
                "score": 0.0,
                "extracted_data": {},
                "reason": "Document expired",
            }

        # Simulate document verification score
        verification_score = min(
            1.0, base_score + (hash(document.document_number) % 30) / 100
        )

        extracted_data = {
            "name_match": verification_score > 0.8,
            "photo_quality": "high" if verification_score > 0.9 else "medium",
            "document_authenticity": verification_score > 0.85,
            "data_consistency": verification_score > 0.8,
        }

        status = "verified" if verification_score >= 0.8 else "requires_review"

        return {
            "status": status,
            "score": verification_score,
            "extracted_data": extracted_data,
        }

    async def _assess_customer_risk(self, customer: CustomerRecord) -> Dict[str, Any]:
        """Assess customer risk level"""

        risk_factors = []
        risk_score = 0.0

        # Geographic risk
        high_risk_countries = ["AF", "KP", "IR", "SY"]  # Example high-risk countries
        if customer.country_of_residence in high_risk_countries:
            risk_factors.append("High-risk jurisdiction")
            risk_score += 0.3

        # Age-based risk
        age = (datetime.now(timezone.utc) - customer.date_of_birth).days // 365
        if age < 18:
            risk_factors.append("Minor")
            risk_score += 0.5
        elif age > 80:
            risk_factors.append("Advanced age")
            risk_score += 0.1

        # PEP check (mock)
        is_pep = customer.full_name.lower() in [name.lower() for name in self.pep_list]
        if is_pep:
            risk_factors.append("Politically Exposed Person")
            risk_score += 0.4

        # Sanctions check (mock)
        sanctions_match = customer.full_name.lower() in [
            name.lower() for name in self.sanctions_list
        ]
        if sanctions_match:
            risk_factors.append("Sanctions list match")
            risk_score += 1.0  # Automatic high risk

        # Determine risk level
        if risk_score >= 1.0 or sanctions_match:
            risk_level = RiskLevel.PROHIBITED
        elif risk_score >= 0.6:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "is_pep": is_pep,
            "sanctions_clear": not sanctions_match,
            "adverse_media_clear": True,  # Would check adverse media in production
        }

    async def monitor_transaction(
        self,
        transaction_id: str,
        user_id: str,
        amount: Decimal,
        currency: str = "USD",
        transaction_type: str = "payment",
        counterparty: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Monitor transaction for suspicious activity"""

        try:
            # Find customer record
            customer_record = None
            for customer in self.customer_records.values():
                if customer.user_id == user_id:
                    customer_record = customer
                    break

            if not customer_record:
                return {
                    "success": False,
                    "error": "Customer not found - KYC verification required",
                    "kyc_required": True,
                }

            # Check if customer is verified
            if customer_record.kyc_status != KYCStatus.VERIFIED:
                return {
                    "success": False,
                    "error": f"Customer KYC status: {customer_record.kyc_status.value}",
                    "kyc_required": True,
                }

            # Apply monitoring rules
            risk_flags = []
            triggered_rules = []
            risk_score = 0.0

            for rule in self.monitoring_rules.values():
                if not rule.enabled:
                    continue

                rule_triggered = await self._check_monitoring_rule(
                    rule, customer_record, amount, transaction_id, metadata or {}
                )

                if rule_triggered["triggered"]:
                    risk_flags.append(rule.risk_flag)
                    triggered_rules.append(rule.rule_id)
                    risk_score += rule_triggered["risk_contribution"]

            # Customer risk level adjustment
            if customer_record.risk_level == RiskLevel.HIGH:
                risk_score += 0.2
            elif customer_record.risk_level == RiskLevel.MEDIUM:
                risk_score += 0.1

            # Determine if transaction is suspicious
            is_suspicious = risk_score >= 0.7 or any(
                flag
                in [
                    TransactionRiskFlag.SANCTIONS_MATCH,
                    TransactionRiskFlag.STRUCTURING,
                ]
                for flag in risk_flags
            )

            monitoring_result = {
                "success": True,
                "transaction_approved": not is_suspicious,
                "risk_score": risk_score,
                "risk_level": "high"
                if risk_score >= 0.8
                else "medium"
                if risk_score >= 0.4
                else "low",
                "risk_flags": [flag.value for flag in risk_flags],
                "triggered_rules": triggered_rules,
                "requires_manual_review": is_suspicious,
            }

            # Create suspicious transaction record if needed
            if is_suspicious:
                alert_id = self.generate_alert_id()
                suspicious_transaction = SuspiciousTransaction(
                    alert_id=alert_id,
                    transaction_id=transaction_id,
                    customer_id=customer_record.customer_id,
                    amount=amount,
                    currency=currency,
                    transaction_date=datetime.now(timezone.utc),
                    risk_flags=risk_flags,
                    risk_score=risk_score,
                    triggered_rules=triggered_rules,
                )

                self.suspicious_transactions[alert_id] = suspicious_transaction
                self.compliance_stats["suspicious_transactions"] += 1

                monitoring_result["alert_id"] = alert_id

                logger.warning(
                    f"Suspicious transaction detected: {transaction_id} - Risk score: {risk_score}"
                )

            # Create audit record
            await self._create_audit_record(
                audit_type="transaction_monitoring",
                customer_id=customer_record.customer_id,
                transaction_id=transaction_id,
                findings=[f"Risk score: {risk_score}", f"Flags: {len(risk_flags)}"],
                compliance_score=1.0 - risk_score,
            )

            return monitoring_result

        except Exception as e:
            logger.error(f"Transaction monitoring failed: {e}")
            return {"success": False, "error": str(e), "transaction_approved": False}

    async def _check_monitoring_rule(
        self,
        rule: TransactionMonitoringRule,
        customer: CustomerRecord,
        amount: Decimal,
        transaction_id: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check if a monitoring rule is triggered"""

        triggered = False
        risk_contribution = 0.0

        if rule.risk_flag == TransactionRiskFlag.UNUSUAL_AMOUNT:
            if rule.threshold_amount and amount >= rule.threshold_amount:
                triggered = True
                risk_contribution = 0.3

        elif rule.risk_flag == TransactionRiskFlag.FREQUENT_TRANSACTIONS:
            # Mock frequency check - in production would query transaction history
            recent_transactions = len(
                [
                    tx
                    for tx in self.suspicious_transactions.values()
                    if tx.customer_id == customer.customer_id
                    and (datetime.now(timezone.utc) - tx.created_at).total_seconds()
                    < (rule.time_window_hours or 24) * 3600
                ]
            )

            if (
                rule.threshold_frequency
                and recent_transactions >= rule.threshold_frequency
            ):
                triggered = True
                risk_contribution = 0.4

        elif rule.risk_flag == TransactionRiskFlag.STRUCTURING:
            # Check for structuring patterns
            if (
                rule.threshold_amount
                and amount >= rule.threshold_amount * Decimal("0.95")
                and amount < rule.threshold_amount
            ):
                triggered = True
                risk_contribution = 0.8

        # Add severity-based risk contribution adjustment
        severity_multiplier = {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0,
        }.get(rule.severity, 1.0)

        risk_contribution *= severity_multiplier

        return {
            "triggered": triggered,
            "risk_contribution": min(risk_contribution, 1.0),
        }

    async def file_suspicious_activity_report(
        self, alert_id: str, investigator: str, findings: str, filing_reason: str
    ) -> Dict[str, Any]:
        """File Suspicious Activity Report"""

        try:
            if alert_id not in self.suspicious_transactions:
                return {"success": False, "error": "Suspicious transaction not found"}

            suspicious_transaction = self.suspicious_transactions[alert_id]

            # Generate SAR reference
            sar_reference = (
                f"SAR-{datetime.now().strftime('%Y%m%d')}-{hash(alert_id) % 10000:04d}"
            )

            # Update suspicious transaction record
            suspicious_transaction.sar_status = SARStatus.FILED
            suspicious_transaction.sar_filed_date = datetime.now(timezone.utc)
            suspicious_transaction.sar_reference = sar_reference
            suspicious_transaction.investigation_status = "resolved"
            suspicious_transaction.investigation_notes.append(f"SAR filed: {findings}")

            # Update statistics
            self.compliance_stats["sars_filed"] += 1

            # Create audit record
            await self._create_audit_record(
                audit_type="sar_filing",
                customer_id=suspicious_transaction.customer_id,
                transaction_id=suspicious_transaction.transaction_id,
                findings=[f"SAR filed: {sar_reference}", findings],
                compliance_score=1.0,
            )

            # In production, this would integrate with FinCEN or other regulatory systems
            logger.info(f"SAR filed: {sar_reference} for alert {alert_id}")

            return {
                "success": True,
                "sar_reference": sar_reference,
                "filed_date": suspicious_transaction.sar_filed_date.isoformat(),
                "message": "Suspicious Activity Report filed successfully",
            }

        except Exception as e:
            logger.error(f"SAR filing failed: {e}")
            return {"success": False, "error": str(e)}

    async def _create_audit_record(
        self,
        audit_type: str,
        customer_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        findings: Optional[List[str]] = None,
        compliance_score: float = 0.0,
    ):
        """Create compliance audit record"""

        audit_record = ComplianceAuditRecord(
            audit_id=self.generate_audit_id(),
            audit_type=audit_type,
            customer_id=customer_id,
            transaction_id=transaction_id,
            findings=findings or [],
            compliance_score=compliance_score,
        )

        self.audit_records.append(audit_record)

    def _get_required_actions(self, customer: CustomerRecord) -> List[str]:
        """Get required actions for customer"""

        actions = []

        if customer.kyc_status == KYCStatus.REQUIRES_ADDITIONAL_INFO:
            actions.append("Provide additional identity verification documents")

        if customer.kyc_status == KYCStatus.REJECTED:
            actions.append("Contact compliance team for review")

        if customer.risk_level == RiskLevel.HIGH:
            actions.append("Enhanced due diligence required")

        if customer.is_pep:
            actions.append("PEP monitoring and reporting required")

        return actions

    async def get_customer_compliance_status(self, user_id: str) -> Dict[str, Any]:
        """Get customer compliance status"""

        customer_record = None
        for customer in self.customer_records.values():
            if customer.user_id == user_id:
                customer_record = customer
                break

        if not customer_record:
            return {
                "success": False,
                "error": "Customer not found",
                "kyc_required": True,
            }

        return {
            "success": True,
            "customer_id": customer_record.customer_id,
            "kyc_status": customer_record.kyc_status.value,
            "risk_level": customer_record.risk_level.value,
            "verification_date": customer_record.verification_date.isoformat()
            if customer_record.verification_date
            else None,
            "next_review_date": customer_record.next_review_date.isoformat()
            if customer_record.next_review_date
            else None,
            "is_pep": customer_record.is_pep,
            "required_actions": self._get_required_actions(customer_record),
            "transaction_limits": self._get_transaction_limits(customer_record),
        }

    def _get_transaction_limits(self, customer: CustomerRecord) -> Dict[str, Any]:
        """Get transaction limits based on risk level"""

        limits = {
            RiskLevel.LOW: {
                "daily_limit": 50000.00,
                "monthly_limit": 200000.00,
                "single_transaction_limit": 25000.00,
            },
            RiskLevel.MEDIUM: {
                "daily_limit": 25000.00,
                "monthly_limit": 100000.00,
                "single_transaction_limit": 10000.00,
            },
            RiskLevel.HIGH: {
                "daily_limit": 10000.00,
                "monthly_limit": 25000.00,
                "single_transaction_limit": 5000.00,
            },
            RiskLevel.PROHIBITED: {
                "daily_limit": 0.00,
                "monthly_limit": 0.00,
                "single_transaction_limit": 0.00,
            },
        }

        return limits.get(customer.risk_level, limits[RiskLevel.MEDIUM])

    async def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""

        total_customers = len(self.customer_records)
        verified_customers = len(
            [
                c
                for c in self.customer_records.values()
                if c.kyc_status == KYCStatus.VERIFIED
            ]
        )
        high_risk_customers = len(
            [
                c
                for c in self.customer_records.values()
                if c.risk_level == RiskLevel.HIGH
            ]
        )

        compliance_rate = (
            (verified_customers / total_customers * 100) if total_customers > 0 else 0
        )

        return {
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_customers": total_customers,
                "verified_customers": verified_customers,
                "high_risk_customers": high_risk_customers,
                "compliance_rate": compliance_rate,
                "suspicious_transactions": len(self.suspicious_transactions),
                "sars_filed": self.compliance_stats["sars_filed"],
            },
            "kyc_statistics": {
                "pending": len(
                    [
                        c
                        for c in self.customer_records.values()
                        if c.kyc_status == KYCStatus.PENDING
                    ]
                ),
                "verified": verified_customers,
                "rejected": len(
                    [
                        c
                        for c in self.customer_records.values()
                        if c.kyc_status == KYCStatus.REJECTED
                    ]
                ),
                "requires_additional_info": len(
                    [
                        c
                        for c in self.customer_records.values()
                        if c.kyc_status == KYCStatus.REQUIRES_ADDITIONAL_INFO
                    ]
                ),
            },
            "risk_distribution": {
                "low": len(
                    [
                        c
                        for c in self.customer_records.values()
                        if c.risk_level == RiskLevel.LOW
                    ]
                ),
                "medium": len(
                    [
                        c
                        for c in self.customer_records.values()
                        if c.risk_level == RiskLevel.MEDIUM
                    ]
                ),
                "high": high_risk_customers,
                "prohibited": len(
                    [
                        c
                        for c in self.customer_records.values()
                        if c.risk_level == RiskLevel.PROHIBITED
                    ]
                ),
            },
            "monitoring_statistics": {
                "active_alerts": len(
                    [
                        tx
                        for tx in self.suspicious_transactions.values()
                        if tx.investigation_status == "pending"
                    ]
                ),
                "resolved_alerts": len(
                    [
                        tx
                        for tx in self.suspicious_transactions.values()
                        if tx.investigation_status == "resolved"
                    ]
                ),
                "sar_filed": self.compliance_stats["sars_filed"],
            },
            "audit_summary": {
                "total_audits": len(self.audit_records),
                "average_compliance_score": sum(
                    audit.compliance_score for audit in self.audit_records
                )
                / len(self.audit_records)
                if self.audit_records
                else 0,
            },
        }


# Factory function
def create_financial_compliance_engine() -> FinancialComplianceEngine:
    """Create financial compliance engine instance"""
    return FinancialComplianceEngine()


# Aliases for backward compatibility
KYCAMLEngine = FinancialComplianceEngine
TransactionMonitor = FinancialComplianceEngine
SuspiciousActivityReporter = FinancialComplianceEngine
TransactionType = TransactionRiskFlag
ComplianceStatus = KYCStatus
