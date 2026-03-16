"""
Database Models
===============

Comprehensive data models for the UATP Capsule Engine using modern PostgreSQL
features including JSONB, UUID, and advanced indexing.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# Define enums for database consistency
class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class CitizenshipStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class CitizenshipType(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    TEMPORARY = "temporary"


class CapsuleType(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    CLONING_RIGHTS = "cloning_rights"
    EVOLUTION = "evolution"
    DIVIDEND_BOND = "dividend_bond"
    CITIZENSHIP = "citizenship"


class BondType(str, Enum):
    REVENUE = "revenue"
    ROYALTY = "royalty"
    USAGE = "usage"
    PERFORMANCE = "performance"


class BondStatus(str, Enum):
    ACTIVE = "active"
    MATURED = "matured"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


class AssetType(str, Enum):
    AI_MODELS = "ai_models"
    ALGORITHMS = "algorithms"
    DATASETS = "datasets"
    SOFTWARE = "software"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    KNOWLEDGE_SOURCE = "knowledge_source"  # AKC integration


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class EventType(str, Enum):
    CITIZENSHIP_APPLICATION_SUBMITTED = "citizenship.application.submitted"
    CITIZENSHIP_ASSESSMENT_COMPLETED = "citizenship.assessment.completed"
    CITIZENSHIP_GRANTED = "citizenship.granted"
    CITIZENSHIP_DENIED = "citizenship.denied"
    CITIZENSHIP_REVOKED = "citizenship.revoked"
    CITIZENSHIP_STATUS_UPDATED = "citizenship.status.updated"
    IP_ASSET_REGISTERED = "bonds.asset.registered"
    DIVIDEND_BOND_CREATED = "bonds.bond.created"
    DIVIDEND_PAYMENT_PROCESSED = "bonds.payment.processed"
    BOND_MATURED = "bonds.bond.matured"
    BOND_DEFAULTED = "bonds.bond.defaulted"
    AGENT_RIGHTS_UPDATED = "agent.rights.updated"
    FINANCIAL_STATUS_CHANGED = "agent.financial.status_changed"
    COMPLIANCE_CHECK_REQUIRED = "compliance.check.required"
    RISK_ASSESSMENT_UPDATED = "risk.assessment.updated"
    SERVICE_STARTED = "system.service.started"
    SERVICE_STOPPED = "system.service.stopped"
    HEALTH_CHECK_FAILED = "system.health.check_failed"


class ProposalStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ProposalCategory(str, Enum):
    PROTOCOL = "protocol"
    ECONOMIC = "economic"
    GOVERNANCE = "governance"
    TECHNICAL = "technical"
    COMMUNITY = "community"


class VoteChoice(str, Enum):
    FOR = "for"
    AGAINST = "against"
    ABSTAIN = "abstain"


class FederationNodeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SYNCING = "syncing"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class OrganizationRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class KnowledgeSourceType(str, Enum):
    ACADEMIC_PAPER = "academic_paper"
    BOOK = "book"
    CODE_REPOSITORY = "code_repository"
    DATASET = "dataset"
    DOCUMENTATION = "documentation"
    BLOG_POST = "blog_post"
    PATENT = "patent"
    CONVERSATION = "conversation"
    TRAINING_DATA = "training_data"
    EXPERT_KNOWLEDGE = "expert_knowledge"
    CULTURAL_KNOWLEDGE = "cultural_knowledge"
    HISTORICAL_RECORD = "historical_record"


class KnowledgeVerificationStatus(str, Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    DISPUTED = "disputed"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


# Database schema definitions as Python classes for clarity
@dataclass
class Agent:
    """AI Agent entity."""

    agent_id: str
    name: str
    agent_type: str
    capabilities: List[str]
    status: AgentStatus
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

    # Optional fields
    description: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None
    verification_data: Optional[Dict[str, Any]] = None


@dataclass
class Citizenship:
    """Citizenship entity."""

    citizenship_id: str
    agent_id: str
    jurisdiction: str
    citizenship_type: CitizenshipType
    status: CitizenshipStatus
    granted_at: Optional[datetime]
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Assessment and metadata
    assessment_scores: Dict[str, float]
    rights: List[str]
    obligations: List[str]
    metadata: Dict[str, Any]


@dataclass
class CitizenshipApplication:
    """Citizenship application entity."""

    application_id: str
    agent_id: str
    jurisdiction: str
    citizenship_type: CitizenshipType
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    approved_at: Optional[datetime]
    reviewer_id: Optional[str]

    supporting_evidence: Dict[str, Any]
    assessment_results: Dict[str, Any]
    rejection_reason: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class IPAsset:
    """Intellectual Property Asset entity."""

    asset_id: str
    owner_agent_id: str
    asset_type: AssetType
    name: str
    description: str
    market_value: float
    created_at: datetime
    updated_at: datetime

    # Asset details
    revenue_streams: List[str]
    performance_metrics: Dict[str, float]
    legal_data: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class DividendBond:
    """Dividend Bond entity."""

    bond_id: str
    asset_id: str
    issuer_agent_id: str
    bond_type: BondType
    face_value: float
    coupon_rate: float
    issue_date: datetime
    maturity_date: datetime
    status: BondStatus
    created_at: datetime
    updated_at: datetime

    # Bond details
    yield_calculation_method: str
    risk_rating: str
    terms_conditions: Dict[str, Any]
    performance_data: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class DividendPayment:
    """Dividend Payment entity."""

    payment_id: str
    bond_id: str
    recipient_agent_id: str
    amount: float
    payment_date: datetime
    status: PaymentStatus
    created_at: datetime

    payment_source: str
    transaction_reference: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class Capsule:
    """Capsule entity."""

    capsule_id: str
    agent_id: str
    capsule_type: CapsuleType
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    # Capsule data
    capsule_data: Dict[str, Any]
    configuration: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class Event:
    """Event entity for event sourcing."""

    event_id: str
    event_type: EventType
    agent_id: Optional[str]
    source_service: str
    timestamp: datetime

    # Event data
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    correlation_id: Optional[str]
    causation_id: Optional[str]


@dataclass
class WorkflowExecution:
    """Workflow execution entity."""

    execution_id: str
    workflow_id: str
    agent_id: Optional[str]
    status: WorkflowStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime

    # Execution data
    context: Dict[str, Any]
    steps_data: List[Dict[str, Any]]
    error_message: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class ComplianceRecord:
    """Compliance record entity."""

    record_id: str
    agent_id: str
    check_type: str
    status: str
    checked_at: datetime
    next_check_due: Optional[datetime]

    # Compliance data
    results: Dict[str, Any]
    issues: List[Dict[str, Any]]
    remediation_actions: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class RiskAssessment:
    """Risk assessment entity."""

    assessment_id: str
    agent_id: str
    assessment_type: str
    risk_score: float
    risk_level: str
    assessed_at: datetime
    valid_until: Optional[datetime]

    # Risk data
    risk_factors: List[str]
    mitigation_measures: List[str]
    assessment_data: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class AuditLog:
    """Audit log entity."""

    log_id: str
    user_id: Optional[str]
    agent_id: Optional[str]
    action: str
    resource_type: str
    resource_id: str
    timestamp: datetime

    # Audit data
    before_state: Optional[Dict[str, Any]]
    after_state: Optional[Dict[str, Any]]
    request_data: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class Proposal:
    """Governance proposal entity."""

    proposal_id: str
    title: str
    description: str
    category: ProposalCategory
    status: ProposalStatus
    created_by: str
    created_at: datetime
    updated_at: datetime

    # Voting data
    voting_starts_at: datetime
    voting_ends_at: datetime
    quorum_required: int
    votes_for: int
    votes_against: int
    votes_abstain: int

    # Proposal details
    implementation_details: Optional[Dict[str, Any]]
    impact_assessment: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class Vote:
    """Vote entity."""

    vote_id: str
    proposal_id: str
    voter_id: str
    choice: VoteChoice
    timestamp: datetime

    # Vote details
    voting_power: float
    rationale: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class FederationNode:
    """Federation node entity."""

    node_id: str
    name: str
    url: str
    region: str
    status: FederationNodeStatus
    created_at: datetime
    updated_at: datetime

    # Node details
    capabilities: List[str]
    last_sync_at: Optional[datetime]
    sync_stats: Dict[str, Any]
    health_data: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class Organization:
    """Organization entity."""

    organization_id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Organization details
    settings: Dict[str, Any]
    billing_info: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class OrganizationMember:
    """Organization member entity."""

    member_id: str
    organization_id: str
    user_id: str
    role: OrganizationRole
    joined_at: datetime
    updated_at: datetime

    # Member details
    permissions: List[str]
    metadata: Dict[str, Any]


@dataclass
class OrganizationInvitation:
    """Organization invitation entity."""

    invitation_id: str
    organization_id: str
    email: str
    role: OrganizationRole
    status: InvitationStatus
    invited_by: str
    invited_at: datetime
    expires_at: datetime

    # Invitation details
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    metadata: Dict[str, Any]


from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

# Create the declarative base
Base = declarative_base()


# --- Attribution ORM Model ---
class Attribution(Base):
    __tablename__ = "attributions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)
    conversation_id = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    # Add other fields as needed


# Helper functions for model creation
def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


# Model validation helpers
class ModelValidator:
    """Validation utilities for models."""

    @staticmethod
    def validate_agent(agent: Agent) -> List[str]:
        """Validate agent data."""
        errors = []

        if not agent.agent_id:
            errors.append("Agent ID is required")

        if not agent.name:
            errors.append("Agent name is required")

        if not agent.capabilities:
            errors.append("Agent must have at least one capability")

        return errors

    @staticmethod
    def validate_citizenship(citizenship: Citizenship) -> List[str]:
        """Validate citizenship data."""
        errors = []

        if not citizenship.citizenship_id:
            errors.append("Citizenship ID is required")

        if not citizenship.agent_id:
            errors.append("Agent ID is required")

        if not citizenship.jurisdiction:
            errors.append("Jurisdiction is required")

        return errors

    @staticmethod
    def validate_bond(bond: DividendBond) -> List[str]:
        """Validate bond data."""
        errors = []

        if not bond.bond_id:
            errors.append("Bond ID is required")

        if bond.face_value <= 0:
            errors.append("Face value must be positive")

        if bond.coupon_rate < 0:
            errors.append("Coupon rate cannot be negative")

        if bond.maturity_date <= bond.issue_date:
            errors.append("Maturity date must be after issue date")

        return errors


@dataclass
class KnowledgeSource:
    """Knowledge Source entity for AKC system."""

    source_id: str
    source_type: KnowledgeSourceType
    title: str
    authors: List[str]
    publication_date: Optional[datetime]
    url: Optional[str]
    doi: Optional[str]
    isbn: Optional[str]
    repository_url: Optional[str]
    license: Optional[str]
    verification_status: KnowledgeVerificationStatus
    confidence_score: float
    usage_count: int
    last_verified: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

    # Content identification
    content_hash: Optional[str] = None
    cluster_id: Optional[str] = None

    # Attribution tracking
    attribution_count: int = 0
    total_attribution_value: float = 0.0


@dataclass
class KnowledgeCluster:
    """Knowledge Cluster entity for AKC system."""

    cluster_id: str
    name: str
    description: str
    cluster_hash: str
    total_usage: int
    primary_contributors: List[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

    # Cluster relationships
    source_ids: List[str]
    related_cluster_ids: List[str] = None


@dataclass
class KnowledgeAttribution:
    """Knowledge Attribution entity for tracking usage."""

    attribution_id: str
    source_id: str
    capsule_id: str
    contributor_id: str
    usage_context: str
    attribution_value: float
    timestamp: datetime
    metadata: Dict[str, Any]

    # Verification
    verified: bool = False
    verification_timestamp: Optional[datetime] = None
    verifier_id: Optional[str] = None


@dataclass
class AncestralContribution:
    """Ancestral Knowledge Contribution entity."""

    contribution_id: str
    source_id: str
    contributor_id: str
    capsule_id: str
    contribution_type: str
    base_value: float
    quality_score: float
    usage_count: int
    verification_count: int
    reward_multiplier: float
    timestamp: datetime
    metadata: Dict[str, Any]

    # Economic tracking
    dividends_earned: float = 0.0
    last_dividend_date: Optional[datetime] = None


# Add AKC validation methods to DataValidator
class AKCDataValidator:
    """Data validation methods for AKC system."""

    @staticmethod
    def validate_knowledge_source(source: KnowledgeSource) -> List[str]:
        """Validate knowledge source data."""
        errors = []

        if not source.source_id:
            errors.append("Source ID is required")

        if not source.title:
            errors.append("Source title is required")

        if not source.authors:
            errors.append("At least one author is required")

        if source.confidence_score < 0 or source.confidence_score > 1:
            errors.append("Confidence score must be between 0 and 1")

        if source.usage_count < 0:
            errors.append("Usage count cannot be negative")

        if source.doi and not source.doi.startswith("10."):
            errors.append("DOI must start with '10.'")

        return errors

    @staticmethod
    def validate_knowledge_cluster(cluster: KnowledgeCluster) -> List[str]:
        """Validate knowledge cluster data."""
        errors = []

        if not cluster.cluster_id:
            errors.append("Cluster ID is required")

        if not cluster.name:
            errors.append("Cluster name is required")

        if not cluster.description:
            errors.append("Cluster description is required")

        if not cluster.source_ids:
            errors.append("Cluster must contain at least one source")

        if cluster.total_usage < 0:
            errors.append("Total usage cannot be negative")

        return errors

    @staticmethod
    def validate_knowledge_attribution(attribution: KnowledgeAttribution) -> List[str]:
        """Validate knowledge attribution data."""
        errors = []

        if not attribution.attribution_id:
            errors.append("Attribution ID is required")

        if not attribution.source_id:
            errors.append("Source ID is required")

        if not attribution.capsule_id:
            errors.append("Capsule ID is required")

        if not attribution.contributor_id:
            errors.append("Contributor ID is required")

        if attribution.attribution_value < 0:
            errors.append("Attribution value cannot be negative")

        return errors

    @staticmethod
    def validate_ancestral_contribution(
        contribution: AncestralContribution,
    ) -> List[str]:
        """Validate ancestral contribution data."""
        errors = []

        if not contribution.contribution_id:
            errors.append("Contribution ID is required")

        if not contribution.source_id:
            errors.append("Source ID is required")

        if not contribution.contributor_id:
            errors.append("Contributor ID is required")

        if not contribution.capsule_id:
            errors.append("Capsule ID is required")

        if contribution.base_value < 0:
            errors.append("Base value cannot be negative")

        if contribution.quality_score < 0 or contribution.quality_score > 1:
            errors.append("Quality score must be between 0 and 1")

        if contribution.usage_count < 0:
            errors.append("Usage count cannot be negative")

        if contribution.verification_count < 0:
            errors.append("Verification count cannot be negative")

        if contribution.reward_multiplier < 0:
            errors.append("Reward multiplier cannot be negative")

        return errors


# Alias for backward compatibility
CapsuleModel = Capsule
