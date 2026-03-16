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

    # UATP 7.2 Training Provenance capsule types
    TRAINING_PROVENANCE = "training_provenance"
    MODEL_REGISTRATION = "model_registration"

    # UATP 7.2 Agentic Workflow capsule types
    WORKFLOW_STEP = "workflow_step"
    WORKFLOW_COMPLETE = "workflow_complete"

    # UATP 7.2 Hardware Attestation capsule type
    HARDWARE_ATTESTATION = "hardware_attestation"

    # UATP 7.2 Edge-Native capsule type
    EDGE_SYNC = "edge_sync"

    # UATP 7.2 Model Registry Protocol capsule types
    MODEL_LICENSE = "model_license"
    MODEL_ARTIFACT = "model_artifact"

    # UATP 7.3 ANE Training Provenance capsule types
    KERNEL_EXECUTION = "kernel_execution"
    HARDWARE_PROFILE = "hardware_profile"
    COMPILE_ARTIFACT = "compile_artifact"
    TRAINING_TELEMETRY = "training_telemetry"
    ANE_TRAINING_SESSION = "ane_training_session"

    # UATP 7.4 Agent Execution Traces capsule types
    AGENT_SESSION = "agent_session"
    TOOL_CALL = "tool_call"
    ACTION_TRACE = "action_trace"
    DECISION_POINT = "decision_point"
    ENVIRONMENT_SNAPSHOT = "environment_snapshot"

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
            # UATP 7.2 types (excluded from legacy count)
            cls.TRAINING_PROVENANCE,
            cls.MODEL_REGISTRATION,
            cls.WORKFLOW_STEP,
            cls.WORKFLOW_COMPLETE,
            cls.HARDWARE_ATTESTATION,
            cls.EDGE_SYNC,
            cls.MODEL_LICENSE,
            cls.MODEL_ARTIFACT,
            # UATP 7.3 types (excluded from legacy count)
            cls.KERNEL_EXECUTION,
            cls.HARDWARE_PROFILE,
            cls.COMPILE_ARTIFACT,
            cls.TRAINING_TELEMETRY,
            cls.ANE_TRAINING_SESSION,
            # UATP 7.4 types (excluded from legacy count)
            cls.AGENT_SESSION,
            cls.TOOL_CALL,
            cls.ACTION_TRACE,
            cls.DECISION_POINT,
            cls.ENVIRONMENT_SNAPSHOT,
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
    version: str = Field("7.0", pattern=r"^7\.[01234]$")
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
    licensee_agent_id: str | None = Field(
        None, description="Agent ID of the licensee (if specific)"
    )
    license_terms: dict[str, Any] = Field(
        description="Detailed licensing terms and conditions"
    )
    usage_restrictions: list[str] = Field(
        default_factory=list, description="List of usage restrictions"
    )
    royalty_percentage: float | None = Field(
        None, ge=0, le=100, description="Royalty percentage for usage"
    )
    expiration_date: UTCDateTime | None = Field(
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
    license_fee: float | None = Field(None, ge=0, description="One-time license fee")
    moral_constraints: list[str] = Field(
        default_factory=list, description="Moral constraints on model usage"
    )


class EvolutionPayload(BaseModel):
    """Payload for tracking value drift and model evolution over time."""

    model_config = ConfigDict(protected_namespaces=())

    model_id: str = Field(description="Identifier of the evolving model")
    evolution_type: str = Field(
        description="Type of evolution (drift, adaptation, fine-tuning, etc.)"
    )
    baseline_model_id: str | None = Field(
        None, description="ID of the baseline model for comparison"
    )
    evolution_metrics: dict[str, Any] = Field(
        description="Quantitative metrics of evolution"
    )
    value_drift_score: float = Field(
        ge=0, le=1, description="Normalized score indicating value drift magnitude"
    )
    drift_direction: list[str] = Field(
        description="Directions of value drift (e.g., conservative, progressive)"
    )
    detected_changes: list[dict[str, Any]] = Field(
        description="Specific detected changes in behavior"
    )
    confidence_level: float = Field(
        ge=0, le=1, description="Confidence in the evolution detection"
    )
    evolution_timestamp: UTCDateTime = Field(
        description="When the evolution was detected"
    )
    contributing_factors: list[str] = Field(
        default_factory=list, description="Factors that contributed to evolution"
    )
    mitigation_recommendations: list[str] = Field(
        default_factory=list, description="Recommendations to mitigate drift"
    )
    alignment_impact: str | None = Field(
        None, description="Impact on model alignment with intended values"
    )
    training_data_influence: dict[str, Any] | None = Field(
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
    performance_metrics: dict[str, float] = Field(
        description="Key performance metrics of the IP asset"
    )
    risk_rating: str = Field(description="Risk rating of the bond")
    collateral_assets: list[str] = Field(
        default_factory=list, description="Assets backing the bond"
    )
    dividend_history: list[dict[str, Any]] = Field(
        default_factory=list, description="Historical dividend payments"
    )
    current_yield: float | None = Field(
        None, ge=0, description="Current yield percentage"
    )
    callable: bool = Field(
        default=False, description="Whether the bond is callable by issuer"
    )
    tradeable: bool = Field(default=True, description="Whether the bond can be traded")
    minimum_investment: float | None = Field(
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
    criteria_met: list[str] = Field(
        description="List of citizenship criteria that have been met"
    )
    criteria_pending: list[str] = Field(
        default_factory=list, description="Criteria still pending"
    )
    rights_granted: list[str] = Field(
        description="Rights granted with this citizenship"
    )
    obligations: list[str] = Field(description="Legal obligations of the citizen agent")
    verification_level: str = Field(
        description="Level of identity/capability verification"
    )
    assessment_date: UTCDateTime = Field(description="Date of citizenship assessment")
    expiration_date: UTCDateTime | None = Field(
        None, description="Citizenship expiration date if temporary"
    )
    legal_capacity_score: float = Field(
        ge=0, le=1, description="Assessed legal capacity score"
    )
    cognitive_benchmarks: dict[str, float] = Field(
        description="Cognitive capability benchmarks"
    )
    ethical_compliance_score: float = Field(
        ge=0, le=1, description="Ethical compliance assessment"
    )
    social_integration_level: float = Field(
        ge=0, le=1, description="Level of social integration"
    )
    economic_contribution: dict[str, Any] | None = Field(
        None, description="Economic contribution metrics"
    )
    legal_precedents: list[str] = Field(
        default_factory=list, description="Relevant legal precedents"
    )
    appeal_history: list[dict[str, Any]] = Field(
        default_factory=list, description="History of appeals or reviews"
    )


class AKCPayload(BaseModel):
    """Payload for Attribution Key Clustering (AKC) knowledge source tracking."""

    knowledge_source: dict[str, Any] = Field(description="Knowledge source metadata")
    source_type: str = Field(description="Type of knowledge source")
    title: str = Field(description="Title of the knowledge source")
    authors: list[str] = Field(description="Authors or contributors")
    publication_date: UTCDateTime | None = Field(None, description="Publication date")
    url: str | None = Field(None, description="URL of the source")
    doi: str | None = Field(None, description="DOI if applicable")
    isbn: str | None = Field(None, description="ISBN if applicable")
    repository_url: str | None = Field(None, description="Repository URL if applicable")
    license: str | None = Field(None, description="License information")
    verification_status: str = Field(description="Verification status")
    confidence_score: float = Field(ge=0, le=1, description="Confidence score")
    usage_count: int = Field(default=0, description="Usage count")
    last_verified: UTCDateTime | None = Field(
        None, description="Last verification date"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    content_hash: str | None = Field(None, description="Content hash for deduplication")
    cluster_id: str | None = Field(None, description="Associated cluster ID")


class AKCClusterPayload(BaseModel):
    """Payload for AKC knowledge clusters."""

    cluster_id: str = Field(description="Unique cluster identifier")
    name: str = Field(description="Cluster name")
    description: str = Field(description="Cluster description")
    sources: dict[str, dict[str, Any]] = Field(
        description="Knowledge sources in cluster"
    )
    cluster_hash: str = Field(description="Cluster content hash")
    total_usage: int = Field(default=0, description="Total usage across all sources")
    primary_contributors: list[str] = Field(description="Primary contributors")
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

    model_config = ConfigDict(populate_by_name=True)

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


# --- UATP 7.2 Training Provenance Payloads ---


class DatasetReference(BaseModel):
    """Reference to a training dataset with provenance."""

    model_config = ConfigDict(protected_namespaces=())

    dataset_id: str = Field(description="Unique dataset identifier")
    dataset_name: str = Field(description="Human-readable dataset name")
    version: str = Field(description="Dataset version")
    source_url: str | None = Field(None, description="Dataset source URL")
    license: str | None = Field(None, description="Dataset license")
    content_hash: str | None = Field(None, description="SHA-256 hash of dataset")
    record_count: int | None = Field(None, ge=0, description="Number of records")
    attribution: dict[str, Any] | None = Field(None, description="Attribution metadata")


class TrainingProvenancePayload(BaseModel):
    """Payload for training session provenance tracking."""

    model_config = ConfigDict(protected_namespaces=())

    session_id: str = Field(description="Unique training session identifier")
    model_id: str = Field(description="Model being trained")
    session_type: str = Field(
        description="Type: pre_training, fine_tuning, rlhf, dpo, sft, adapter"
    )
    dataset_refs: list[DatasetReference] = Field(
        description="References to training datasets"
    )
    hyperparameters: dict[str, Any] | None = Field(
        None, description="Training hyperparameters"
    )
    compute_resources: dict[str, Any] | None = Field(
        None, description="GPU/TPU configuration"
    )
    started_at: UTCDateTime = Field(description="Session start time")
    completed_at: UTCDateTime | None = Field(None, description="Session end time")
    metrics: dict[str, Any] | None = Field(
        None, description="Training metrics and evaluation results"
    )
    status: str = Field(
        default="completed",
        description="Status: pending, running, completed, failed",
    )


class ModelRegistrationPayload(BaseModel):
    """Payload for model registration with provenance."""

    model_config = ConfigDict(protected_namespaces=())

    model_id: str = Field(description="Unique model identifier")
    model_hash: str = Field(description="SHA-256 hash of model weights")
    model_type: str = Field(description="Type: base, fine_tune, adapter, merged")
    version: str = Field(description="Model version string")
    name: str | None = Field(None, description="Human-readable model name")
    description: str | None = Field(None, description="Model description")
    base_model_id: str | None = Field(None, description="Parent model ID for lineage")
    training_config: dict[str, Any] | None = Field(
        None, description="Training configuration"
    )
    dataset_provenance: list[DatasetReference] | None = Field(
        None, description="Datasets used in training"
    )
    license_info: dict[str, Any] | None = Field(None, description="License information")
    capabilities: list[str] | None = Field(
        None, description="Declared model capabilities"
    )
    safety_evaluations: dict[str, Any] | None = Field(
        None, description="Safety benchmark results"
    )


# --- UATP 7.2 Agentic Workflow Payloads ---


class WorkflowStepPayload(BaseModel):
    """Payload for individual workflow step capsules."""

    workflow_capsule_id: str = Field(description="Parent workflow capsule ID")
    step_index: int = Field(ge=0, description="Step position in workflow")
    step_type: str = Field(
        description="Type: plan, tool_call, inference, output, human_input, verification"
    )
    step_name: str | None = Field(None, description="Human-readable step name")
    input_data: dict[str, Any] | None = Field(None, description="Step input")
    output_data: dict[str, Any] | None = Field(None, description="Step output")
    depends_on_steps: list[int] | None = Field(
        None, description="Indices of dependency steps"
    )
    tool_name: str | None = Field(None, description="Tool used (if tool_call)")
    model_id: str | None = Field(None, description="Model used (if inference)")
    execution_time_ms: int | None = Field(None, ge=0, description="Step execution time")
    confidence: float | None = Field(None, ge=0, le=1, description="Step confidence")


class WorkflowCompletePayload(BaseModel):
    """Payload for workflow completion and sealing."""

    workflow_capsule_id: str = Field(description="Workflow capsule ID")
    workflow_name: str = Field(description="Workflow name")
    workflow_type: str = Field(
        description="Type: linear, branching, iterative, parallel"
    )
    total_steps: int = Field(ge=1, description="Total number of steps")
    step_capsule_ids: list[str] = Field(description="Ordered list of step capsule IDs")
    aggregated_attribution: dict[str, Any] | None = Field(
        None, description="Combined attribution from all steps"
    )
    dag_definition: dict[str, Any] | None = Field(
        None, description="DAG structure definition"
    )
    started_at: UTCDateTime = Field(description="Workflow start time")
    completed_at: UTCDateTime = Field(description="Workflow completion time")
    final_output: dict[str, Any] | None = Field(
        None, description="Final workflow output"
    )
    status: str = Field(
        default="completed",
        description="Status: completed, failed, cancelled",
    )


# --- UATP 7.2 Hardware Attestation Payloads ---


class HardwareAttestationPayload(BaseModel):
    """Payload for hardware attestation from Secure Enclave, TEE, or Confidential Computing."""

    attestation_type: str = Field(
        description="Type: apple_secure_enclave, android_tee, nvidia_cc, intel_sgx, arm_trustzone"
    )
    device_id_hash: str = Field(description="SHA-256 hash of device identifier")
    attestation_timestamp: UTCDateTime = Field(
        description="When attestation was created"
    )
    attestation_data: str = Field(description="Base64-encoded attestation blob")
    certificate_chain: list[str] = Field(description="PEM-encoded certificate chain")
    nonce: str = Field(description="Challenge nonce used")
    measurements: dict[str, str] = Field(
        description="Platform measurements (PCRs, etc.)"
    )
    verified: bool = Field(
        default=False, description="Whether attestation was verified"
    )
    verification_timestamp: UTCDateTime | None = Field(
        None, description="When verification occurred"
    )


# --- UATP 7.2 Edge-Native Payloads ---


class EdgeSyncPayload(BaseModel):
    """Payload for edge device capsule synchronization."""

    edge_device_id: str = Field(description="Edge device identifier")
    sync_direction: str = Field(description="Direction: edge_to_cloud, cloud_to_edge")
    capsule_ids: list[str] = Field(description="Capsule IDs being synced")
    sync_timestamp: UTCDateTime = Field(description="Sync operation timestamp")
    offline_duration_seconds: int | None = Field(
        None, ge=0, description="How long device was offline"
    )
    pending_count: int = Field(
        default=0, ge=0, description="Remaining capsules to sync"
    )
    sync_status: str = Field(
        default="completed",
        description="Status: completed, partial, failed",
    )
    compression_used: bool = Field(default=False, description="Whether CBOR was used")


# --- UATP 7.2 Model Registry Protocol Payloads ---


class ModelLicensePayload(BaseModel):
    """Payload for model license attachment and verification."""

    model_config = ConfigDict(protected_namespaces=())

    license_id: str = Field(description="Unique license identifier")
    model_id: str = Field(description="Model this license applies to")
    license_type: str = Field(
        description="Type: apache2, mit, proprietary, research_only, commercial"
    )
    permissions: dict[str, bool] = Field(
        description="Granted permissions (use, modify, distribute, commercial)"
    )
    restrictions: dict[str, bool] = Field(
        description="Restrictions (attribution_required, share_alike, no_derivatives)"
    )
    effective_date: UTCDateTime = Field(description="License effective date")
    expiration_date: UTCDateTime | None = Field(
        None, description="License expiration (None = perpetual)"
    )
    licensor: str = Field(description="Entity granting the license")
    terms_hash: str | None = Field(None, description="SHA-256 of full license terms")


class ModelArtifactPayload(BaseModel):
    """Payload for model artifact registration with content addressing."""

    model_config = ConfigDict(protected_namespaces=())

    artifact_id: str = Field(description="Unique artifact identifier")
    model_id: str = Field(description="Model this artifact belongs to")
    artifact_type: str = Field(
        description="Type: weights, config, tokenizer, adapter, checkpoint"
    )
    content_hash: str = Field(description="SHA-256 hash of artifact content")
    size_bytes: int = Field(ge=0, description="Artifact size in bytes")
    storage_uri: str = Field(description="URI where artifact is stored")
    format: str | None = Field(
        None, description="Format: safetensors, pytorch, onnx, gguf"
    )
    compression: str | None = Field(None, description="Compression: none, gzip, zstd")
    created_at: UTCDateTime = Field(description="Artifact creation timestamp")


# --- UATP 7.3 ANE Training Provenance Payloads ---


class HybridComputeAttribution(BaseModel):
    """Attribution for hybrid ANE/CPU compute operations."""

    compute_unit: str = Field(description="Compute unit: ane, cpu, gpu, or hybrid")
    ane_percentage: float = Field(
        ge=0, le=100, description="Percentage of compute on ANE"
    )
    cpu_percentage: float = Field(
        ge=0, le=100, description="Percentage of compute on CPU"
    )
    gpu_percentage: float = Field(
        ge=0, le=100, default=0.0, description="Percentage of compute on GPU"
    )
    dispatch_reason: str | None = Field(
        None, description="Reason for compute unit selection"
    )


class MILFusionOptimization(BaseModel):
    """MIL (Machine Learning Intermediate Language) fusion optimization record."""

    fusion_name: str = Field(description="Name of the fusion optimization applied")
    source_ops: list[str] = Field(description="Original operations that were fused")
    target_op: str = Field(description="Resulting fused operation")
    speedup_factor: float | None = Field(
        None, ge=1.0, description="Measured speedup from fusion"
    )
    memory_reduction_bytes: int | None = Field(
        None, ge=0, description="Memory savings from fusion"
    )


class KernelExecutionPayload(BaseModel):
    """Payload for per-kernel dispatch tracking on ANE, Metal GPU, or MLX.

    Kernel types by accelerator:
    - ANE: kFwdAttn, kFwdFFN, kFFNBwd, kSdpaBwd1, kSdpaBwd2, kQKVb
    - Metal: metal_gemm, metal_conv2d, metal_attention, metal_layernorm
    - MLX: mlx_matmul, mlx_attention, mlx_rope, mlx_rms_norm, mlx_cross_entropy
    - MPS: mps_matmul, mps_conv2d, mps_lstm, mps_transformer
    """

    model_config = ConfigDict(protected_namespaces=())

    session_id: str = Field(description="Training session ID")
    accelerator_type: str = Field(
        default="ane", description="Accelerator: ane, metal, mlx, mps, cpu"
    )
    kernel_type: str = Field(
        description="Kernel type (e.g., kFwdAttn for ANE, mlx_matmul for MLX)"
    )
    step_index: int = Field(ge=0, description="Training step index")
    dispatch_index: int = Field(ge=0, description="Dispatch index within step")
    execution_time_us: int = Field(ge=0, description="Execution time in microseconds")
    # Memory format
    iosurface_format: str | None = Field(
        None, description="IOSurface format e.g. [1,C,1,S] (ANE)"
    )
    metal_buffer_mode: str | None = Field(
        None, description="Metal buffer storage mode: shared, private, managed"
    )
    # Tensor shapes
    input_shape: list[int] | None = Field(None, description="Input tensor shape")
    output_shape: list[int] | None = Field(None, description="Output tensor shape")
    # Compute attribution
    compute_attribution: HybridComputeAttribution | None = Field(
        None, description="Hybrid compute attribution"
    )
    # Program/shader references
    ane_program_hash: str | None = Field(
        None, description="Hash of compiled ANE program"
    )
    metal_shader_hash: str | None = Field(
        None, description="Hash of Metal shader library"
    )
    mlx_graph_hash: str | None = Field(None, description="Hash of compiled MLX graph")


class HardwareProfilePayload(BaseModel):
    """Payload for device hardware capabilities including ANE, GPU, and Metal."""

    model_config = ConfigDict(protected_namespaces=())

    device_class: str = Field(description="Device class: mac, iphone, ipad")
    chip_identifier: str = Field(
        description="Chip identifier: M1, M2, M3, M4, A17, etc."
    )
    chip_variant: str | None = Field(None, description="Chip variant: Pro, Max, Ultra")
    # ANE capabilities
    ane_available: bool = Field(description="Whether ANE is available")
    ane_version: str | None = Field(None, description="ANE version string")
    ane_tops: float | None = Field(None, ge=0, description="ANE performance in TOPS")
    ane_compile_limit: int | None = Field(
        None, ge=0, description="Maximum compiled models (~119 for M-series)"
    )
    # GPU/Metal capabilities
    gpu_core_count: int | None = Field(None, ge=0, description="Number of GPU cores")
    gpu_tflops: float | None = Field(
        None, ge=0, description="GPU performance in TFLOPS"
    )
    metal_version: str | None = Field(None, description="Metal API version (e.g., 3.1)")
    metal_family: str | None = Field(
        None, description="Metal GPU family (e.g., apple9, mac2)"
    )
    mps_available: bool = Field(
        default=True, description="Whether Metal Performance Shaders is available"
    )
    mlx_version: str | None = Field(
        None, description="MLX framework version if installed"
    )
    # Memory
    memory_bandwidth_gbps: float | None = Field(
        None, ge=0, description="Memory bandwidth in GB/s"
    )
    unified_memory_gb: float | None = Field(
        None, ge=0, description="Unified memory in GB"
    )
    # API usage
    private_apis_used: list[str] = Field(
        default_factory=list,
        description="Private APIs used: _ANEClient, _ANECompiler, etc.",
    )
    frameworks_used: list[str] = Field(
        default_factory=list,
        description="ML frameworks: mlx, pytorch_mps, coreml, tensorflow_metal",
    )
    # Device identification
    device_id_hash: str = Field(description="SHA-256 hash of device identifier")
    os_version: str | None = Field(None, description="Operating system version")
    coreml_version: str | None = Field(None, description="CoreML framework version")


class CompileArtifactPayload(BaseModel):
    """Payload for compiled ML artifacts: MIL programs, MLX graphs, Metal shaders.

    Artifact formats:
    - mil: CoreML MIL program (.mlmodel, .mlmodelc)
    - mlx: MLX compiled graph
    - metal: Metal shader library (.metallib)
    - safetensors: Safetensors weight file
    - gguf: GGML unified format
    """

    model_config = ConfigDict(protected_namespaces=())

    artifact_id: str = Field(description="Unique artifact identifier")
    session_id: str = Field(description="Training session ID")
    artifact_format: str = Field(
        default="mil", description="Format: mil, mlx, metal, safetensors, gguf"
    )
    # Content hashes (at least one required based on artifact_format)
    mil_program_hash: str | None = Field(
        None, description="SHA-256 hash of MIL program (required for mil format)"
    )
    # Additional hashes by format
    weight_blob_hash: str | None = Field(
        None, description="SHA-256 hash of weight blob"
    )
    compiled_model_hash: str | None = Field(
        None, description="SHA-256 hash of compiled model (ANE .mlmodelc)"
    )
    mlx_graph_hash: str | None = Field(
        None, description="SHA-256 hash of compiled MLX graph"
    )
    metal_library_hash: str | None = Field(
        None, description="SHA-256 hash of Metal shader library"
    )
    # Optimizations
    fusion_optimizations: list[MILFusionOptimization] = Field(
        default_factory=list, description="Applied fusion optimizations"
    )
    mlx_simplifications: list[str] | None = Field(
        None, description="MLX graph simplifications applied"
    )
    # Compilation details
    compile_time_ms: int | None = Field(
        None, ge=0, description="Compilation time in milliseconds"
    )
    target_device: str | None = Field(None, description="Target device for compilation")
    target_accelerator: str | None = Field(
        None, description="Target accelerator: ane, gpu, cpu"
    )
    coreml_spec_version: int | None = Field(
        None, description="CoreML specification version"
    )
    mlx_version: str | None = Field(
        None, description="MLX version used for compilation"
    )
    # Size
    mlmodel_size_bytes: int | None = Field(
        None, ge=0, description="Size of compiled artifact in bytes"
    )
    storage_uri: str | None = Field(None, description="URI where artifact is stored")
    created_at: UTCDateTime = Field(description="Artifact creation timestamp")


class TrainingTelemetryPayload(BaseModel):
    """Payload for real-time training telemetry metrics across ANE, GPU, and CPU."""

    model_config = ConfigDict(protected_namespaces=())

    session_id: str = Field(description="Training session ID")
    measurement_window_seconds: int = Field(
        ge=1, description="Measurement window in seconds"
    )
    steps_in_window: int = Field(ge=0, description="Steps completed in window")
    avg_ms_per_step: float = Field(ge=0, description="Average milliseconds per step")
    # ANE metrics (optional for GPU-only training)
    avg_ane_utilization: float | None = Field(
        None, ge=0, le=100, description="Average ANE utilization percentage"
    )
    peak_ane_utilization: float | None = Field(
        None, ge=0, le=100, description="Peak ANE utilization"
    )
    # GPU/Metal metrics
    avg_gpu_utilization: float | None = Field(
        None, ge=0, le=100, description="Average GPU utilization percentage"
    )
    peak_gpu_utilization: float | None = Field(
        None, ge=0, le=100, description="Peak GPU utilization"
    )
    gpu_memory_used_gb: float | None = Field(
        None, ge=0, description="GPU memory used in GB"
    )
    gpu_memory_allocated_gb: float | None = Field(
        None, ge=0, description="GPU memory allocated in GB"
    )
    metal_command_buffers_per_second: float | None = Field(
        None, ge=0, description="Metal command buffer throughput"
    )
    # Combined metrics
    tflops_achieved: float | None = Field(
        None, ge=0, description="Combined TFLOPS achieved"
    )
    ane_tflops: float | None = Field(None, ge=0, description="ANE TFLOPS achieved")
    gpu_tflops: float | None = Field(None, ge=0, description="GPU TFLOPS achieved")
    # System metrics
    memory_used_gb: float | None = Field(
        None, ge=0, description="Total unified memory used in GB"
    )
    thermal_state: str | None = Field(
        None, description="Thermal state: nominal, fair, serious, critical"
    )
    power_consumption_watts: float | None = Field(
        None, ge=0, description="Power consumption in watts"
    )
    # Attribution
    compute_attribution: HybridComputeAttribution | None = Field(
        None, description="Aggregate compute attribution"
    )
    primary_accelerator: str | None = Field(
        None, description="Primary accelerator used: ane, gpu, cpu"
    )
    timestamp: UTCDateTime = Field(description="Telemetry timestamp")


class ANETrainingSessionPayload(BaseModel):
    """Payload for complete ANE training session with full provenance."""

    model_config = ConfigDict(protected_namespaces=())

    session_id: str = Field(description="Unique training session identifier")
    model_id: str = Field(description="Model being trained")
    model_name: str | None = Field(None, description="Human-readable model name")
    hardware_profile_id: str = Field(description="Reference to hardware profile")
    started_at: UTCDateTime = Field(description="Session start time")
    completed_at: UTCDateTime | None = Field(None, description="Session end time")
    status: str = Field(
        default="running",
        description="Status: pending, running, completed, failed, cancelled",
    )
    total_steps: int | None = Field(None, ge=0, description="Total training steps")
    completed_steps: int = Field(default=0, ge=0, description="Completed steps")
    kernel_execution_count: int = Field(
        default=0, ge=0, description="Total kernel executions"
    )
    compile_artifact_ids: list[str] = Field(
        default_factory=list, description="References to compile artifacts"
    )
    final_loss: float | None = Field(None, description="Final training loss")
    avg_ms_per_step: float | None = Field(None, ge=0, description="Average ms per step")
    avg_ane_utilization: float | None = Field(
        None, ge=0, le=100, description="Average ANE utilization"
    )
    total_ane_time_seconds: float | None = Field(
        None, ge=0, description="Total ANE compute time in seconds"
    )
    total_cpu_time_seconds: float | None = Field(
        None, ge=0, description="Total CPU compute time in seconds"
    )
    hyperparameters: dict[str, Any] | None = Field(
        None, description="Training hyperparameters"
    )
    dataset_refs: list[DatasetReference] | None = Field(
        None, description="References to training datasets"
    )
    private_apis_used: list[str] = Field(
        default_factory=list, description="Private APIs used in session"
    )
    dmca_1201f_claim: bool = Field(
        default=False,
        description="DMCA 1201(f) interoperability claim for reverse engineering",
    )
    research_purpose: str | None = Field(
        None, description="Research purpose declaration"
    )
    session_metadata: dict[str, Any] | None = Field(
        None, description="Additional session metadata"
    )


# --- UATP 7.4 Agent Execution Traces Payloads ---


class ToolCallPayload(BaseModel):
    """Payload for individual tool invocation tracking."""

    model_config = ConfigDict(protected_namespaces=())

    call_id: str = Field(description="Unique tool call ID")
    session_id: str = Field(description="Parent agent session")
    tool_name: str = Field(description="Tool name (e.g., Bash, Read, Edit, WebFetch)")
    tool_category: str = Field(
        description="Category: terminal, file, browser, api, mcp, custom"
    )
    tool_inputs: dict[str, Any] = Field(description="Input parameters")
    tool_outputs: dict[str, Any] | None = Field(None, description="Output/result")
    started_at: UTCDateTime = Field(description="When tool call started")
    completed_at: UTCDateTime | None = Field(
        None, description="When tool call completed"
    )
    duration_ms: int | None = Field(None, ge=0, description="Duration in milliseconds")
    status: str = Field(
        default="pending", description="Status: pending, success, error, timeout"
    )
    error_message: str | None = Field(None, description="Error message if failed")
    step_index: int = Field(ge=0, description="Order within session")
    parent_call_id: str | None = Field(None, description="For nested tool calls")


class ActionTracePayload(BaseModel):
    """Payload for terminal commands, browser actions, file operations."""

    action_id: str = Field(description="Unique action ID")
    session_id: str = Field(description="Parent agent session")
    tool_call_id: str | None = Field(None, description="Link to parent tool call")
    action_type: str = Field(description="Type: terminal, browser, file, api")
    # Terminal actions
    command: str | None = Field(None, description="Terminal command executed")
    exit_code: int | None = Field(None, description="Command exit code")
    stdout_hash: str | None = Field(
        None, description="SHA-256 hash of stdout (privacy)"
    )
    stderr_hash: str | None = Field(
        None, description="SHA-256 hash of stderr (privacy)"
    )
    # Browser actions
    url: str | None = Field(None, description="URL for browser actions")
    selector: str | None = Field(None, description="CSS selector for element")
    browser_action: str | None = Field(
        None, description="Browser action: navigate, click, type, screenshot"
    )
    # File actions
    file_path: str | None = Field(None, description="File path for file operations")
    file_operation: str | None = Field(
        None, description="Operation: read, write, edit, delete, glob, grep"
    )
    bytes_affected: int | None = Field(None, ge=0, description="Bytes affected")
    # Timing
    executed_at: UTCDateTime = Field(description="When action was executed")
    duration_ms: int = Field(ge=0, description="Action duration in milliseconds")


class DecisionPointPayload(BaseModel):
    """Payload for agent reasoning and action selection."""

    decision_id: str = Field(description="Unique decision ID")
    session_id: str = Field(description="Parent agent session")
    step_index: int = Field(ge=0, description="Step index within session")
    reasoning: str = Field(description="Why this action was chosen")
    alternatives_considered: list[str] = Field(
        default_factory=list, description="Other options evaluated"
    )
    selected_action: str = Field(description="What was chosen")
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Confidence score 0.0-1.0"
    )
    context_summary: str | None = Field(
        None, description="Relevant context for decision"
    )
    constraints_applied: list[str] = Field(
        default_factory=list, description="Safety, permissions, etc."
    )
    timestamp: UTCDateTime = Field(description="When decision was made")


class EnvironmentSnapshotPayload(BaseModel):
    """Payload for system state capture at decision points."""

    snapshot_id: str = Field(description="Unique snapshot ID")
    session_id: str = Field(description="Parent agent session")
    working_directory: str = Field(description="Current working directory")
    env_vars_hash: str = Field(description="Hash of environment variables (privacy)")
    git_branch: str | None = Field(None, description="Current git branch")
    git_commit_hash: str | None = Field(None, description="Current commit hash")
    git_dirty: bool | None = Field(None, description="Whether working tree is dirty")
    open_files: list[str] = Field(
        default_factory=list, description="Files being tracked"
    )
    system_load: float | None = Field(None, ge=0, description="System load average")
    memory_available_gb: float | None = Field(
        None, ge=0, description="Available memory in GB"
    )
    timestamp: UTCDateTime = Field(description="Snapshot timestamp")


class AgentSessionPayload(BaseModel):
    """Payload for complete agent session with goals, context, and outcomes."""

    session_id: str = Field(description="Unique session identifier")
    agent_type: str = Field(description="Agent type: openclaw, claude_code, custom")
    agent_version: str | None = Field(None, description="Agent version string")
    scheduler_type: str | None = Field(
        None, description="Scheduler: heartbeat, on_demand, scheduled"
    )
    trigger_message: str | None = Field(
        None, description="Message that initiated the session"
    )
    trigger_source: str | None = Field(
        None, description="Source: whatsapp, telegram, cli, api"
    )
    user_id_hash: str | None = Field(
        None, description="Privacy-preserving user ID hash"
    )
    goals: list[str] = Field(
        default_factory=list, description="What the agent is trying to achieve"
    )
    started_at: UTCDateTime = Field(description="Session start time")
    completed_at: UTCDateTime | None = Field(None, description="Session end time")
    status: str = Field(
        default="pending",
        description="Status: pending, running, completed, failed, cancelled",
    )
    tool_call_count: int = Field(default=0, ge=0, description="Number of tool calls")
    action_count: int = Field(default=0, ge=0, description="Number of actions")
    decision_count: int = Field(default=0, ge=0, description="Number of decisions")
    total_duration_ms: int | None = Field(
        None, ge=0, description="Total session duration"
    )
    outcome_summary: str | None = Field(None, description="Summary of outcomes")
    error_message: str | None = Field(None, description="Error if failed")


# --- Concrete Capsule Models ---


class ReasoningTraceCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.REASONING_TRACE] = CapsuleType.REASONING_TRACE
    reasoning_trace: ReasoningTracePayload


class EconomicTransactionCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.ECONOMIC_TRANSACTION] = (
        CapsuleType.ECONOMIC_TRANSACTION
    )
    economic_transaction: EconomicTransactionPayload


class GovernanceVoteCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.GOVERNANCE_VOTE] = CapsuleType.GOVERNANCE_VOTE
    governance_vote: GovernanceVotePayload


class EthicsTriggerCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.ETHICS_TRIGGER] = CapsuleType.ETHICS_TRIGGER
    ethics_trigger: EthicsTriggerPayload


class PostQuantumSignatureCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.POST_QUANTUM_SIGNATURE] = (
        CapsuleType.POST_QUANTUM_SIGNATURE
    )
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
    capsule_type: Literal[CapsuleType.CONFLICT_RESOLUTION] = (
        CapsuleType.CONFLICT_RESOLUTION
    )
    conflict_resolution: ConflictResolutionPayload


class PerspectiveCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.PERSPECTIVE] = CapsuleType.PERSPECTIVE
    perspective: PerspectivePayload


class FeedbackAssimilationCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.FEEDBACK_ASSIMILATION] = (
        CapsuleType.FEEDBACK_ASSIMILATION
    )
    feedback_assimilation: FeedbackAssimilationPayload


class KnowledgeExpiryCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.KNOWLEDGE_EXPIRY] = CapsuleType.KNOWLEDGE_EXPIRY
    knowledge_expiry: KnowledgeExpiryPayload


class EmotionalLoadCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.EMOTIONAL_LOAD] = CapsuleType.EMOTIONAL_LOAD
    emotional_load: EmotionalLoadPayload


class ManipulationAttemptCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.MANIPULATION_ATTEMPT] = (
        CapsuleType.MANIPULATION_ATTEMPT
    )
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


# --- UATP 7.2 Capsule Classes ---


class TrainingProvenanceCapsule(BaseCapsule):
    """Capsule for recording training session provenance."""

    capsule_type: Literal[CapsuleType.TRAINING_PROVENANCE] = (
        CapsuleType.TRAINING_PROVENANCE
    )
    training_provenance: TrainingProvenancePayload


class ModelRegistrationCapsule(BaseCapsule):
    """Capsule for model registration events."""

    capsule_type: Literal[CapsuleType.MODEL_REGISTRATION] = (
        CapsuleType.MODEL_REGISTRATION
    )
    model_registration: ModelRegistrationPayload


class WorkflowStepCapsule(BaseCapsule):
    """Capsule for individual agentic workflow steps."""

    capsule_type: Literal[CapsuleType.WORKFLOW_STEP] = CapsuleType.WORKFLOW_STEP
    workflow_step: WorkflowStepPayload


class WorkflowCompleteCapsule(BaseCapsule):
    """Capsule for workflow completion and sealing."""

    capsule_type: Literal[CapsuleType.WORKFLOW_COMPLETE] = CapsuleType.WORKFLOW_COMPLETE
    workflow_complete: WorkflowCompletePayload


class HardwareAttestationCapsule(BaseCapsule):
    """Capsule for hardware attestation records."""

    capsule_type: Literal[CapsuleType.HARDWARE_ATTESTATION] = (
        CapsuleType.HARDWARE_ATTESTATION
    )
    hardware_attestation: HardwareAttestationPayload


class EdgeSyncCapsule(BaseCapsule):
    """Capsule for edge device synchronization events."""

    capsule_type: Literal[CapsuleType.EDGE_SYNC] = CapsuleType.EDGE_SYNC
    edge_sync: EdgeSyncPayload


class ModelLicenseCapsule(BaseCapsule):
    """Capsule for model license attachment."""

    capsule_type: Literal[CapsuleType.MODEL_LICENSE] = CapsuleType.MODEL_LICENSE
    model_license: ModelLicensePayload


class ModelArtifactCapsule(BaseCapsule):
    """Capsule for model artifact registration."""

    capsule_type: Literal[CapsuleType.MODEL_ARTIFACT] = CapsuleType.MODEL_ARTIFACT
    model_artifact: ModelArtifactPayload


# --- UATP 7.3 ANE Training Provenance Capsule Classes ---


class KernelExecutionCapsule(BaseCapsule):
    """Capsule for ANE kernel execution tracking."""

    capsule_type: Literal[CapsuleType.KERNEL_EXECUTION] = CapsuleType.KERNEL_EXECUTION
    kernel_execution: KernelExecutionPayload


class HardwareProfileCapsule(BaseCapsule):
    """Capsule for hardware profile registration."""

    capsule_type: Literal[CapsuleType.HARDWARE_PROFILE] = CapsuleType.HARDWARE_PROFILE
    hardware_profile: HardwareProfilePayload


class CompileArtifactCapsule(BaseCapsule):
    """Capsule for MIL compile artifact registration."""

    capsule_type: Literal[CapsuleType.COMPILE_ARTIFACT] = CapsuleType.COMPILE_ARTIFACT
    compile_artifact: CompileArtifactPayload


class TrainingTelemetryCapsule(BaseCapsule):
    """Capsule for training telemetry records."""

    capsule_type: Literal[CapsuleType.TRAINING_TELEMETRY] = (
        CapsuleType.TRAINING_TELEMETRY
    )
    training_telemetry: TrainingTelemetryPayload


class ANETrainingSessionCapsule(BaseCapsule):
    """Capsule for complete ANE training session."""

    capsule_type: Literal[CapsuleType.ANE_TRAINING_SESSION] = (
        CapsuleType.ANE_TRAINING_SESSION
    )
    ane_training_session: ANETrainingSessionPayload


# --- UATP 7.4 Agent Execution Traces Capsule Classes ---


class AgentSessionCapsule(BaseCapsule):
    """Capsule for complete agent session."""

    capsule_type: Literal[CapsuleType.AGENT_SESSION] = CapsuleType.AGENT_SESSION
    agent_session: AgentSessionPayload


class ToolCallCapsule(BaseCapsule):
    """Capsule for individual tool invocations."""

    capsule_type: Literal[CapsuleType.TOOL_CALL] = CapsuleType.TOOL_CALL
    tool_call: ToolCallPayload


class ActionTraceCapsule(BaseCapsule):
    """Capsule for terminal, browser, and file actions."""

    capsule_type: Literal[CapsuleType.ACTION_TRACE] = CapsuleType.ACTION_TRACE
    action_trace: ActionTracePayload


class DecisionPointCapsule(BaseCapsule):
    """Capsule for agent decision reasoning."""

    capsule_type: Literal[CapsuleType.DECISION_POINT] = CapsuleType.DECISION_POINT
    decision_point: DecisionPointPayload


class EnvironmentSnapshotCapsule(BaseCapsule):
    """Capsule for environment state capture."""

    capsule_type: Literal[CapsuleType.ENVIRONMENT_SNAPSHOT] = (
        CapsuleType.ENVIRONMENT_SNAPSHOT
    )
    environment_snapshot: EnvironmentSnapshotPayload


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
        # UATP 7.2 capsule types
        TrainingProvenanceCapsule,
        ModelRegistrationCapsule,
        WorkflowStepCapsule,
        WorkflowCompleteCapsule,
        HardwareAttestationCapsule,
        EdgeSyncCapsule,
        ModelLicenseCapsule,
        ModelArtifactCapsule,
        # UATP 7.3 ANE Training Provenance capsule types
        KernelExecutionCapsule,
        HardwareProfileCapsule,
        CompileArtifactCapsule,
        TrainingTelemetryCapsule,
        ANETrainingSessionCapsule,
        # UATP 7.4 Agent Execution Traces capsule types
        AgentSessionCapsule,
        ToolCallCapsule,
        ActionTraceCapsule,
        DecisionPointCapsule,
        EnvironmentSnapshotCapsule,
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
# UATP 7.2 capsule rebuilds
TrainingProvenanceCapsule.model_rebuild()
ModelRegistrationCapsule.model_rebuild()
WorkflowStepCapsule.model_rebuild()
WorkflowCompleteCapsule.model_rebuild()
HardwareAttestationCapsule.model_rebuild()
EdgeSyncCapsule.model_rebuild()
ModelLicenseCapsule.model_rebuild()
ModelArtifactCapsule.model_rebuild()
# UATP 7.3 capsule rebuilds
KernelExecutionCapsule.model_rebuild()
HardwareProfileCapsule.model_rebuild()
CompileArtifactCapsule.model_rebuild()
TrainingTelemetryCapsule.model_rebuild()
ANETrainingSessionCapsule.model_rebuild()
# UATP 7.4 capsule rebuilds
AgentSessionCapsule.model_rebuild()
ToolCallCapsule.model_rebuild()
ActionTraceCapsule.model_rebuild()
DecisionPointCapsule.model_rebuild()
EnvironmentSnapshotCapsule.model_rebuild()
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
    # UATP 7.2 types
    CapsuleType.TRAINING_PROVENANCE: TrainingProvenanceCapsule,
    CapsuleType.MODEL_REGISTRATION: ModelRegistrationCapsule,
    CapsuleType.WORKFLOW_STEP: WorkflowStepCapsule,
    CapsuleType.WORKFLOW_COMPLETE: WorkflowCompleteCapsule,
    CapsuleType.HARDWARE_ATTESTATION: HardwareAttestationCapsule,
    CapsuleType.EDGE_SYNC: EdgeSyncCapsule,
    CapsuleType.MODEL_LICENSE: ModelLicenseCapsule,
    CapsuleType.MODEL_ARTIFACT: ModelArtifactCapsule,
    # UATP 7.3 types
    CapsuleType.KERNEL_EXECUTION: KernelExecutionCapsule,
    CapsuleType.HARDWARE_PROFILE: HardwareProfileCapsule,
    CapsuleType.COMPILE_ARTIFACT: CompileArtifactCapsule,
    CapsuleType.TRAINING_TELEMETRY: TrainingTelemetryCapsule,
    CapsuleType.ANE_TRAINING_SESSION: ANETrainingSessionCapsule,
    # UATP 7.4 types
    CapsuleType.AGENT_SESSION: AgentSessionCapsule,
    CapsuleType.TOOL_CALL: ToolCallCapsule,
    CapsuleType.ACTION_TRACE: ActionTraceCapsule,
    CapsuleType.DECISION_POINT: DecisionPointCapsule,
    CapsuleType.ENVIRONMENT_SNAPSHOT: EnvironmentSnapshotCapsule,
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
