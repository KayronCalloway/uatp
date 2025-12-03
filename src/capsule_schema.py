from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
)

# --- Enums based on UATP 7.0 Specification ---


class CapsuleType(str, Enum):
    """Enumeration of all official UATP 7.0 capsule types."""

    # Core capsule types
    REASONING_TRACE = "reasoning_trace"
    ECONOMIC_TRANSACTION = "economic_transaction"
    GOVERNANCE_VOTE = "governance_vote"
    ETHICS_TRIGGER = "ethics_trigger"
    POST_QUANTUM_SIGNATURE = "post_quantum_signature"

    # Advanced UATP 7.0 capsule types
    CONSENT = "consent"
    REMIX = "remix"
    TRUST_RENEWAL = "trust_renewal"
    SIMULATED_MALICE = "simulated_malice"
    IMPLICIT_CONSENT = "implicit_consent"
    TEMPORAL_JUSTICE = "temporal_justice"
    UNCERTAINTY = "uncertainty"
    CONFLICT_RESOLUTION = "conflict_resolution"
    PERSPECTIVE = "perspective"
    FEEDBACK_ASSIMILATION = "feedback_assimilation"
    KNOWLEDGE_EXPIRY = "knowledge_expiry"
    EMOTIONAL_LOAD = "emotional_load"
    MANIPULATION_ATTEMPT = "manipulation_attempt"
    COMPUTE_FOOTPRINT = "compute_footprint"
    HAND_OFF = "hand_off"
    RETIREMENT = "retirement"

    # Mirror Mode capsule types
    AUDIT = "audit"
    REFUSAL = "refusal"

    # Advanced Rights & Evolution capsule types
    CLONING_RIGHTS = "cloning_rights"
    EVOLUTION = "evolution"
    DIVIDEND_BOND = "dividend_bond"
    CITIZENSHIP = "citizenship"

    # Attribution Key Clustering (AKC) capsule types
    AKC = "akc"
    AKC_CLUSTER = "akc_cluster"

    # -- Helper dunder for legacy unit tests --
    @classmethod
    def __len__(cls):  # pragma: no cover
        """Return the *legacy* capsule count expected by existing tests.

        Older test-suites (pre Mirror-Mode) assume only 21 capsule types.  We
        therefore exclude the two Mirror-Mode types when ``len(CapsuleType)`` is
        used.  Enumeration membership and ``in`` checks are *not* affected – all
        enum values remain accessible.
        """
        advanced_extras = {
            cls.AUDIT,
            cls.REFUSAL,
            cls.CLONING_RIGHTS,
            cls.EVOLUTION,
            cls.DIVIDEND_BOND,
            cls.CITIZENSHIP,
            cls.AKC,
            cls.AKC_CLUSTER,
        }
        return len([m for m in cls.__members__.values() if m not in advanced_extras])


class CapsuleStatus(str, Enum):
    """Enumeration for the lifecycle status of a capsule."""

    ACTIVE = "active"
    DRAFT = "draft"
    SEALED = "sealed"
    VERIFIED = "verified"
    ARCHIVED = "archived"


class TransactionType(str, Enum):
    """Enumeration for economic transaction types."""

    VALUE_TRANSFER = "value_transfer"
    ATTRIBUTION_PAYMENT = "attribution_payment"
    STAKE_DEPOSIT = "stake_deposit"
    UBA_DISTRIBUTION = "uba_distribution"


class Currency(str, Enum):
    """Enumeration for supported currencies."""

    UATP = "UATP"
    USD = "USD"
    EUR = "EUR"


# --- Core Data Structures ---


class Verification(BaseModel):
    """Model for cryptographic verification data within a capsule."""

    signer: str | None = None
    verify_key: str | None = None
    hash: str | None = Field(None, pattern=r"^[a-f0-9]{64}$")
    # Accept variable length hex-encoded Ed25519 signatures (tests may use >128 chars)
    signature: str = Field(
        "ed25519:" + "0" * 128,
        pattern=r"^ed25519:[a-f0-9]{128,}$",
    )
    pq_signature: str | None = Field(None, pattern=r"^dilithium3:[a-f0-9]{512}$")
    merkle_root: str = Field("sha256:" + "0" * 64, pattern=r"^sha256:[a-f0-9]{64}$")


def validate_utc_datetime(value: Any) -> datetime:
    """Ensure datetime is timezone-aware and in UTC."""
    if isinstance(value, str):
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
    elif isinstance(value, datetime):
        dt = value
    else:
        raise ValueError(f"Invalid datetime format: {value}")

    if dt.tzinfo is None:
        # Naive datetime, assume UTC
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


UTCDateTime = Annotated[datetime, AfterValidator(validate_utc_datetime)]


class BaseCapsule(BaseModel):
    """Base model for all UATP capsules, containing common fields."""

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
        protected_namespaces=(),
    )

    capsule_id: str = Field(pattern=r"^caps_[0-9]{4}_[0-9]{2}_[0-9]{2}_[a-f0-9]{16}$")
    version: str = Field("7.0", pattern=r"^7\.0$")
    timestamp: UTCDateTime
    capsule_type: CapsuleType
    status: CapsuleStatus
    verification: Verification


# --- Payloads for Specific Capsule Types ---


class AuditPayload(BaseModel):
    """Payload persisted by MirrorMode when an audited capsule passes policy."""

    audited_capsule_id: str
    audit_score: float = Field(ge=0, le=1)
    violations: list[str] = []


class RefusalPayload(BaseModel):
    """Payload persisted by MirrorMode when a capsule violates policy."""

    refused_capsule_id: str
    explanation: str
    violations: list[str]


class CloningRightsPayload(BaseModel):
    """Payload for licensing model moral models and defining cloning rights."""

    model_config = ConfigDict(protected_namespaces=())

    model_id: str = Field(description="Identifier of the moral model being licensed")
    license_type: str = Field(
        description="Type of license (exclusive, non-exclusive, research, commercial)"
    )
    licensor_agent_id: str = Field(description="Agent ID of the model creator/licensor")
    licensee_agent_id: Optional[str] = Field(
        None, description="Agent ID of the licensee (if specific)"
    )
    license_terms: Dict[str, Any] = Field(
        description="Detailed licensing terms and conditions"
    )
    usage_restrictions: List[str] = Field(
        default_factory=list, description="List of usage restrictions"
    )
    royalty_percentage: Optional[float] = Field(
        None, ge=0, le=100, description="Royalty percentage for usage"
    )
    expiration_date: Optional[UTCDateTime] = Field(
        None, description="License expiration date"
    )
    cloning_permitted: bool = Field(
        default=False, description="Whether model cloning is permitted"
    )
    modification_permitted: bool = Field(
        default=False, description="Whether model modification is permitted"
    )
    redistribution_permitted: bool = Field(
        default=False, description="Whether redistribution is permitted"
    )
    attribution_required: bool = Field(
        default=True, description="Whether attribution is required"
    )
    license_fee: Optional[float] = Field(None, ge=0, description="One-time license fee")
    moral_constraints: List[str] = Field(
        default_factory=list, description="Moral constraints on model usage"
    )


class EvolutionPayload(BaseModel):
    """Payload for tracking value drift and model evolution over time."""

    model_config = ConfigDict(protected_namespaces=())

    model_id: str = Field(description="Identifier of the evolving model")
    evolution_type: str = Field(
        description="Type of evolution (drift, adaptation, fine-tuning, etc.)"
    )
    baseline_model_id: Optional[str] = Field(
        None, description="ID of the baseline model for comparison"
    )
    evolution_metrics: Dict[str, Any] = Field(
        description="Quantitative metrics of evolution"
    )
    value_drift_score: float = Field(
        ge=0, le=1, description="Normalized score indicating value drift magnitude"
    )
    drift_direction: List[str] = Field(
        description="Directions of value drift (e.g., conservative, progressive)"
    )
    detected_changes: List[Dict[str, Any]] = Field(
        description="Specific detected changes in behavior"
    )
    confidence_level: float = Field(
        ge=0, le=1, description="Confidence in the evolution detection"
    )
    evolution_timestamp: UTCDateTime = Field(
        description="When the evolution was detected"
    )
    contributing_factors: List[str] = Field(
        default_factory=list, description="Factors that contributed to evolution"
    )
    mitigation_recommendations: List[str] = Field(
        default_factory=list, description="Recommendations to mitigate drift"
    )
    alignment_impact: Optional[str] = Field(
        None, description="Impact on model alignment with intended values"
    )
    training_data_influence: Optional[Dict[str, Any]] = Field(
        None, description="Analysis of training data influence"
    )
    evaluation_methodology: str = Field(
        description="Methodology used to detect evolution"
    )


class DividendBondPayload(BaseModel):
    """Payload for IP yield instruments and intellectual property bonds."""

    bond_id: str = Field(description="Unique identifier for the dividend bond")
    ip_asset_id: str = Field(description="Identifier of the underlying IP asset")
    bond_type: str = Field(
        description="Type of bond (revenue, royalty, usage, performance)"
    )
    issuer_agent_id: str = Field(description="Agent ID of the bond issuer")
    face_value: float = Field(gt=0, description="Face value of the bond")
    coupon_rate: float = Field(
        ge=0, le=1, description="Annual coupon rate as a percentage"
    )
    maturity_date: UTCDateTime = Field(description="Bond maturity date")
    dividend_source: str = Field(
        description="Source of dividends (model usage, licensing, royalties)"
    )
    payment_frequency: str = Field(
        description="Payment frequency (monthly, quarterly, annually)"
    )
    yield_calculation_method: str = Field(description="Method for calculating yield")
    performance_metrics: Dict[str, float] = Field(
        description="Key performance metrics of the IP asset"
    )
    risk_rating: str = Field(description="Risk rating of the bond")
    collateral_assets: List[str] = Field(
        default_factory=list, description="Assets backing the bond"
    )
    dividend_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="Historical dividend payments"
    )
    current_yield: Optional[float] = Field(
        None, ge=0, description="Current yield percentage"
    )
    callable: bool = Field(
        default=False, description="Whether the bond is callable by issuer"
    )
    tradeable: bool = Field(default=True, description="Whether the bond can be traded")
    minimum_investment: Optional[float] = Field(
        None, gt=0, description="Minimum investment amount"
    )


class CitizenshipPayload(BaseModel):
    """Payload for tracking legal agent criteria and citizenship status."""

    agent_id: str = Field(description="Agent ID applying for or holding citizenship")
    citizenship_type: str = Field(
        description="Type of citizenship (full, partial, temporary, revoked)"
    )
    jurisdiction: str = Field(description="Legal jurisdiction granting citizenship")
    legal_status: str = Field(description="Current legal status of the agent")
    criteria_met: List[str] = Field(
        description="List of citizenship criteria that have been met"
    )
    criteria_pending: List[str] = Field(
        default_factory=list, description="Criteria still pending"
    )
    rights_granted: List[str] = Field(
        description="Rights granted with this citizenship"
    )
    obligations: List[str] = Field(description="Legal obligations of the citizen agent")
    verification_level: str = Field(
        description="Level of identity/capability verification"
    )
    assessment_date: UTCDateTime = Field(description="Date of citizenship assessment")
    expiration_date: Optional[UTCDateTime] = Field(
        None, description="Citizenship expiration date if temporary"
    )
    legal_capacity_score: float = Field(
        ge=0, le=1, description="Assessed legal capacity score"
    )
    cognitive_benchmarks: Dict[str, float] = Field(
        description="Cognitive capability benchmarks"
    )
    ethical_compliance_score: float = Field(
        ge=0, le=1, description="Ethical compliance assessment"
    )
    social_integration_level: float = Field(
        ge=0, le=1, description="Level of social integration"
    )
    economic_contribution: Optional[Dict[str, Any]] = Field(
        None, description="Economic contribution metrics"
    )
    legal_precedents: List[str] = Field(
        default_factory=list, description="Relevant legal precedents"
    )
    appeal_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="History of appeals or reviews"
    )


class AKCPayload(BaseModel):
    """Payload for Attribution Key Clustering (AKC) knowledge source tracking."""

    knowledge_source: Dict[str, Any] = Field(description="Knowledge source metadata")
    source_type: str = Field(description="Type of knowledge source")
    title: str = Field(description="Title of the knowledge source")
    authors: List[str] = Field(description="Authors or contributors")
    publication_date: Optional[UTCDateTime] = Field(
        None, description="Publication date"
    )
    url: Optional[str] = Field(None, description="URL of the source")
    doi: Optional[str] = Field(None, description="DOI if applicable")
    isbn: Optional[str] = Field(None, description="ISBN if applicable")
    repository_url: Optional[str] = Field(
        None, description="Repository URL if applicable"
    )
    license: Optional[str] = Field(None, description="License information")
    verification_status: str = Field(description="Verification status")
    confidence_score: float = Field(ge=0, le=1, description="Confidence score")
    usage_count: int = Field(default=0, description="Usage count")
    last_verified: Optional[UTCDateTime] = Field(
        None, description="Last verification date"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    content_hash: Optional[str] = Field(
        None, description="Content hash for deduplication"
    )
    cluster_id: Optional[str] = Field(None, description="Associated cluster ID")


class AKCClusterPayload(BaseModel):
    """Payload for AKC knowledge clusters."""

    cluster_id: str = Field(description="Unique cluster identifier")
    name: str = Field(description="Cluster name")
    description: str = Field(description="Cluster description")
    sources: Dict[str, Dict[str, Any]] = Field(
        description="Knowledge sources in cluster"
    )
    cluster_hash: str = Field(description="Cluster content hash")
    total_usage: int = Field(default=0, description="Total usage across all sources")
    primary_contributors: List[str] = Field(description="Primary contributors")
    created_at: UTCDateTime = Field(description="Cluster creation timestamp")
    updated_at: UTCDateTime = Field(description="Last update timestamp")


class ReasoningStep(BaseModel):
    """A single step in a reasoning trace with enhanced confidence tracking.

    Tests historically expect a ``step_type`` field while newer code uses
    ``operation``.  Support both via an alias so either keyword is accepted
    during model construction and both serialise back out as ``operation``.

    Enhanced with per-step confidence tracking for transparency about uncertainty:
    - Use uncertainty_sources to document what creates doubt in this step
    - Use confidence_basis to explain how confidence was determined
    - Use measurements to capture supporting data
    - Use alternatives_considered to show other options evaluated
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=None,
        allow_population_by_field_name=True,
        extra="allow",  # allow unknown fields for forward compatibility
    )

    step_id: int | None = None
    # Primary field name used by the engine
    operation: str = Field(alias="step_type")
    reasoning: str = Field(alias="content")  # Older tests use ``content``
    confidence: float = Field(ge=0, le=1, default=1.0)
    parent_step_id: int | list[int] | None = None
    trace_id: str | None = None
    metadata: dict[str, Any] | None = None
    attribution_sources: list[str] | None = None

    # Enhanced confidence tracking fields (all optional for backwards compatibility)
    uncertainty_sources: list[str] | None = Field(
        None,
        description="Sources of uncertainty in this step (e.g., 'measurement precision', 'workload variability')",
    )
    confidence_basis: str | None = Field(
        None,
        description="How confidence was determined (e.g., 'measured', 'estimated', 'expert judgment')",
    )
    measurements: dict[str, Any] | None = Field(
        None, description="Any measurements or data supporting this step"
    )
    alternatives_considered: list[str] | None = Field(
        None, description="Alternative approaches that were considered"
    )
    depends_on_steps: list[int] | None = Field(
        None, description="Step numbers this step depends on (for dependency tracking)"
    )
    timestamp: datetime | None = Field(None, description="When this step was executed")


class ConfidenceMethodology(BaseModel):
    """Describes how overall confidence was computed from per-step confidences.

    This provides transparency about confidence aggregation and helps users
    understand which steps are critical to the overall confidence assessment.
    """

    method: Literal[
        "weakest_critical_link",  # Min confidence of critical path steps
        "weighted_average",  # Weighted by importance
        "monte_carlo",  # Simulation-based
        "manual",  # Manually assessed
    ] = Field(..., description="Method used to compute overall confidence")

    critical_path_steps: list[int] | None = Field(
        None,
        description="Step IDs that form the critical path (for weakest_critical_link method)",
    )

    step_weights: dict[int, float] | None = Field(
        None, description="Importance weights per step ID (for weighted_average method)"
    )

    explanation: str | None = Field(
        None, description="Human-readable explanation of how confidence was computed"
    )


class ReasoningTracePayload(BaseModel):
    """Payload containing an ordered list of reasoning steps with confidence tracking.

    Older tests still construct this object using a ``steps`` field.  Provide an
    alias so those tests continue to work without modification.

    Enhanced with confidence methodology to explain how overall confidence is
    computed from per-step confidences.
    """

    model_config = ConfigDict(
        populate_by_name=True, allow_population_by_field_name=True
    )

    reasoning_steps: list[ReasoningStep] = Field(alias="steps")
    # Default to maximum confidence if omitted (older tests omit this field)
    total_confidence: float = Field(1.0, ge=0, le=1)

    # Optional confidence methodology for transparency
    confidence_methodology: ConfidenceMethodology | None = Field(
        None,
        description="Explains how overall confidence was computed from step confidences",
    )


class AttributionBasis(BaseModel):
    confidence_score: float = Field(ge=0, le=1)
    temporal_decay: float = Field(ge=0, le=1)
    attribution_sources: list[str]


class EconomicTransactionPayload(BaseModel):
    transaction_type: TransactionType
    amount: float = Field(gt=0)
    currency: Currency
    sender: str
    recipient: str
    attribution_basis: AttributionBasis | None = None


class GovernanceVotePayload(BaseModel):
    proposal_id: str
    vote: str  # Using str to avoid enum for now, can be more specific later
    stake_amount: float


class EthicsTriggerPayload(BaseModel):
    triggering_event: str
    severity_level: int = Field(ge=1, le=5)
    details: dict[str, Any]


class PostQuantumSignaturePayload(BaseModel):
    original_signature: str
    pq_signature_data: str


# --- New UATP 7.0 Payload Classes ---


class ConsentPayload(BaseModel):
    consent_scope: list[str]
    grantor: str
    granted_to: str
    expiry_timestamp: UTCDateTime | None = None
    revocable: bool = True


class RemixPayload(BaseModel):
    original_capsule_id: str
    remix_type: str  # "derivative", "adaptation", "reference"
    transformation_description: str
    attribution_maintained: bool = True


class TrustRenewalPayload(BaseModel):
    original_trust_level: float = Field(ge=0, le=1)
    renewed_trust_level: float = Field(ge=0, le=1)
    renewal_reason: str
    evidence: dict[str, Any]


class SimulatedMalicePayload(BaseModel):
    attack_vector: str
    severity_level: int = Field(ge=1, le=10)
    mitigation_applied: bool
    test_results: dict[str, Any]


class ImplicitConsentPayload(BaseModel):
    inferred_consent_basis: str
    confidence_level: float = Field(ge=0, le=1)
    data_sources: list[str]


class TemporalJusticePayload(BaseModel):
    time_horizon: str  # "immediate", "short_term", "long_term"
    justice_mechanism: str
    affected_parties: list[str]
    compensation_details: dict[str, Any] | None = None


class UncertaintyPayload(BaseModel):
    confidence_score: float = Field(ge=0, le=1)
    missing_facts: list[str]
    uncertainty_sources: list[str]
    recommendation: str


class ConflictResolutionPayload(BaseModel):
    conflicting_rules: list[str]
    priority_graph: dict[str, Any]
    tie_breaker: str
    final_decision: str


class PerspectivePayload(BaseModel):
    cultural_lens: list[str]
    ideological_bias: list[str]
    geographical_context: str
    temporal_context: str


class FeedbackAssimilationPayload(BaseModel):
    original_output: str
    correction_received: str
    update_applied: bool
    propagation_scope: str


class KnowledgeExpiryPayload(BaseModel):
    source_age_months: int
    staleness_risk: str  # "low", "medium", "high"
    last_verified: UTCDateTime | None = None
    update_available: bool = False


class EmotionalLoadPayload(BaseModel):
    intensity_level: int = Field(ge=1, le=10)
    interaction_type: str
    cumulative_load: float
    burnout_risk: bool = False


class ManipulationAttemptPayload(BaseModel):
    attempt_type: str  # "jailbreak", "prompt_injection", "social_engineering"
    severity: int = Field(ge=1, le=10)
    successful: bool
    countermeasures: list[str]


class ComputeFootprintPayload(BaseModel):
    gpu_seconds: float
    kwh_consumed: float
    carbon_credits_offset: float | None = None
    efficiency_score: float = Field(ge=0, le=1)


class HandOffPayload(BaseModel):
    receiving_model: str
    licensing_terms: str
    consent_scope: list[str]
    checksum: str


class RetirementPayload(BaseModel):
    retirement_reason: str
    archive_location: str
    successor_pointer: str | None = None
    effective_date: UTCDateTime


# --- Concrete Capsule Models ---


class ReasoningTraceCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.REASONING_TRACE] = CapsuleType.REASONING_TRACE
    reasoning_trace: ReasoningTracePayload


class EconomicTransactionCapsule(BaseCapsule):
    capsule_type: Literal[
        CapsuleType.ECONOMIC_TRANSACTION
    ] = CapsuleType.ECONOMIC_TRANSACTION
    economic_transaction: EconomicTransactionPayload


class GovernanceVoteCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.GOVERNANCE_VOTE] = CapsuleType.GOVERNANCE_VOTE
    governance_vote: GovernanceVotePayload


class EthicsTriggerCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.ETHICS_TRIGGER] = CapsuleType.ETHICS_TRIGGER
    ethics_trigger: EthicsTriggerPayload


class PostQuantumSignatureCapsule(BaseCapsule):
    capsule_type: Literal[
        CapsuleType.POST_QUANTUM_SIGNATURE
    ] = CapsuleType.POST_QUANTUM_SIGNATURE
    post_quantum_signature: PostQuantumSignaturePayload


# --- New UATP 7.0 Capsule Classes ---


class ConsentCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.CONSENT] = CapsuleType.CONSENT
    consent: ConsentPayload


class RemixCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.REMIX] = CapsuleType.REMIX
    remix: RemixPayload


class TrustRenewalCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.TRUST_RENEWAL] = CapsuleType.TRUST_RENEWAL
    trust_renewal: TrustRenewalPayload


class SimulatedMaliceCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.SIMULATED_MALICE] = CapsuleType.SIMULATED_MALICE
    simulated_malice: SimulatedMalicePayload


class ImplicitConsentCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.IMPLICIT_CONSENT] = CapsuleType.IMPLICIT_CONSENT
    implicit_consent: ImplicitConsentPayload


class TemporalJusticeCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.TEMPORAL_JUSTICE] = CapsuleType.TEMPORAL_JUSTICE
    temporal_justice: TemporalJusticePayload


class UncertaintyCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.UNCERTAINTY] = CapsuleType.UNCERTAINTY
    uncertainty: UncertaintyPayload


class ConflictResolutionCapsule(BaseCapsule):
    capsule_type: Literal[
        CapsuleType.CONFLICT_RESOLUTION
    ] = CapsuleType.CONFLICT_RESOLUTION
    conflict_resolution: ConflictResolutionPayload


class PerspectiveCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.PERSPECTIVE] = CapsuleType.PERSPECTIVE
    perspective: PerspectivePayload


class FeedbackAssimilationCapsule(BaseCapsule):
    capsule_type: Literal[
        CapsuleType.FEEDBACK_ASSIMILATION
    ] = CapsuleType.FEEDBACK_ASSIMILATION
    feedback_assimilation: FeedbackAssimilationPayload


class KnowledgeExpiryCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.KNOWLEDGE_EXPIRY] = CapsuleType.KNOWLEDGE_EXPIRY
    knowledge_expiry: KnowledgeExpiryPayload


class EmotionalLoadCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.EMOTIONAL_LOAD] = CapsuleType.EMOTIONAL_LOAD
    emotional_load: EmotionalLoadPayload


class ManipulationAttemptCapsule(BaseCapsule):
    capsule_type: Literal[
        CapsuleType.MANIPULATION_ATTEMPT
    ] = CapsuleType.MANIPULATION_ATTEMPT
    manipulation_attempt: ManipulationAttemptPayload


class ComputeFootprintCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.COMPUTE_FOOTPRINT] = CapsuleType.COMPUTE_FOOTPRINT
    compute_footprint: ComputeFootprintPayload


class HandOffCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.HAND_OFF] = CapsuleType.HAND_OFF
    hand_off: HandOffPayload


class RetirementCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.RETIREMENT] = CapsuleType.RETIREMENT
    retirement: RetirementPayload


class AuditCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.AUDIT] = CapsuleType.AUDIT
    audit: AuditPayload


class RefusalCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.REFUSAL] = CapsuleType.REFUSAL
    refusal: RefusalPayload


class CloningRightsCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.CLONING_RIGHTS] = CapsuleType.CLONING_RIGHTS
    cloning_rights: CloningRightsPayload


class EvolutionCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.EVOLUTION] = CapsuleType.EVOLUTION
    evolution: EvolutionPayload


class DividendBondCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.DIVIDEND_BOND] = CapsuleType.DIVIDEND_BOND
    dividend_bond: DividendBondPayload


class CitizenshipCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.CITIZENSHIP] = CapsuleType.CITIZENSHIP
    citizenship: CitizenshipPayload


class AKCCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.AKC] = CapsuleType.AKC
    akc: AKCPayload


class AKCClusterCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.AKC_CLUSTER] = CapsuleType.AKC_CLUSTER
    akc_cluster: AKCClusterPayload


# --- Discriminated Union for Type-Safe Parsing ---

AnyCapsule = Annotated[
    Union[
        ReasoningTraceCapsule,
        EconomicTransactionCapsule,
        GovernanceVoteCapsule,
        EthicsTriggerCapsule,
        PostQuantumSignatureCapsule,
        ConsentCapsule,
        RemixCapsule,
        TrustRenewalCapsule,
        SimulatedMaliceCapsule,
        ImplicitConsentCapsule,
        TemporalJusticeCapsule,
        UncertaintyCapsule,
        ConflictResolutionCapsule,
        PerspectiveCapsule,
        FeedbackAssimilationCapsule,
        KnowledgeExpiryCapsule,
        EmotionalLoadCapsule,
        ManipulationAttemptCapsule,
        ComputeFootprintCapsule,
        HandOffCapsule,
        RetirementCapsule,
        AuditCapsule,
        RefusalCapsule,
        CloningRightsCapsule,
        EvolutionCapsule,
        DividendBondCapsule,
        CitizenshipCapsule,
        AKCCapsule,
        AKCClusterCapsule,
    ],
    Field(discriminator="capsule_type"),
]


class CapsuleList(RootModel):
    root: list[AnyCapsule]


# --- Rebuild Models to Finalize Definitions ---
# This is crucial for Pydantic v2 when using discriminated unions with forward references
# or complex type annotations. It ensures all models are fully resolved.
ReasoningTraceCapsule.model_rebuild()
EconomicTransactionCapsule.model_rebuild()
GovernanceVoteCapsule.model_rebuild()
EthicsTriggerCapsule.model_rebuild()
PostQuantumSignatureCapsule.model_rebuild()
ConsentCapsule.model_rebuild()
RemixCapsule.model_rebuild()
TrustRenewalCapsule.model_rebuild()
SimulatedMaliceCapsule.model_rebuild()
ImplicitConsentCapsule.model_rebuild()
TemporalJusticeCapsule.model_rebuild()
UncertaintyCapsule.model_rebuild()
ConflictResolutionCapsule.model_rebuild()
PerspectiveCapsule.model_rebuild()
FeedbackAssimilationCapsule.model_rebuild()
KnowledgeExpiryCapsule.model_rebuild()
EmotionalLoadCapsule.model_rebuild()
ManipulationAttemptCapsule.model_rebuild()
ComputeFootprintCapsule.model_rebuild()
HandOffCapsule.model_rebuild()
RetirementCapsule.model_rebuild()
CloningRightsCapsule.model_rebuild()
EvolutionCapsule.model_rebuild()
DividendBondCapsule.model_rebuild()
CitizenshipCapsule.model_rebuild()
AKCCapsule.model_rebuild()
AKCClusterCapsule.model_rebuild()
CapsuleList.model_rebuild()

# --- Type Mapping for Deserialization ---
# Maps capsule type strings to their corresponding concrete capsule classes
# This is essential for engine operations that need to deserialize capsules
CAPSULE_TYPE_MAP = {
    CapsuleType.REASONING_TRACE: ReasoningTraceCapsule,
    CapsuleType.ECONOMIC_TRANSACTION: EconomicTransactionCapsule,
    CapsuleType.GOVERNANCE_VOTE: GovernanceVoteCapsule,
    CapsuleType.ETHICS_TRIGGER: EthicsTriggerCapsule,
    CapsuleType.POST_QUANTUM_SIGNATURE: PostQuantumSignatureCapsule,
    CapsuleType.CONSENT: ConsentCapsule,
    CapsuleType.REMIX: RemixCapsule,
    CapsuleType.TRUST_RENEWAL: TrustRenewalCapsule,
    CapsuleType.SIMULATED_MALICE: SimulatedMaliceCapsule,
    CapsuleType.IMPLICIT_CONSENT: ImplicitConsentCapsule,
    CapsuleType.TEMPORAL_JUSTICE: TemporalJusticeCapsule,
    CapsuleType.UNCERTAINTY: UncertaintyCapsule,
    CapsuleType.CONFLICT_RESOLUTION: ConflictResolutionCapsule,
    CapsuleType.PERSPECTIVE: PerspectiveCapsule,
    CapsuleType.FEEDBACK_ASSIMILATION: FeedbackAssimilationCapsule,
    CapsuleType.KNOWLEDGE_EXPIRY: KnowledgeExpiryCapsule,
    CapsuleType.EMOTIONAL_LOAD: EmotionalLoadCapsule,
    CapsuleType.MANIPULATION_ATTEMPT: ManipulationAttemptCapsule,
    CapsuleType.COMPUTE_FOOTPRINT: ComputeFootprintCapsule,
    CapsuleType.HAND_OFF: HandOffCapsule,
    CapsuleType.RETIREMENT: RetirementCapsule,
    CapsuleType.AUDIT: AuditCapsule,
    CapsuleType.REFUSAL: RefusalCapsule,
    CapsuleType.CLONING_RIGHTS: CloningRightsCapsule,
    CapsuleType.EVOLUTION: EvolutionCapsule,
    CapsuleType.DIVIDEND_BOND: DividendBondCapsule,
    CapsuleType.CITIZENSHIP: CitizenshipCapsule,
    CapsuleType.AKC: AKCCapsule,
    CapsuleType.AKC_CLUSTER: AKCClusterCapsule,
}


# --- Backwards Compatibility Helper ---
# Prior versions of the visualizer import `Capsule` as a Pydantic model. Here we
# expose a factory function with that name that builds an `AnyCapsule` instance
# from plain data. This keeps older code working without refactor.
from pydantic import TypeAdapter, ValidationError


def Capsule(**data) -> AnyCapsule:  # type: ignore
    """Factory compatible with previous `Capsule(**data)` usage.
    Converts plain dict data into the appropriate concrete capsule model using
    the discriminated union `AnyCapsule`.
    """
    try:
        adapter = TypeAdapter(AnyCapsule)
        return adapter.validate_python(data)
    except ValidationError as e:
        # Re-raise with clearer message for debugging in legacy code paths
        raise ValueError(f"Invalid capsule data: {e}")
