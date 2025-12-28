from pydantic import TypeAdapter
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
)

from src.capsule_schema import AnyCapsule, CapsuleType
from src.core.database import db
from src.utils.uatp_envelope import is_envelope_format, wrap_in_uatp_envelope


class CapsuleModel(db.Base):
    __tablename__ = "capsules"
    __table_args__ = (
        UniqueConstraint("capsule_id", name="uq_capsule_id"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True)
    capsule_id = Column(String, nullable=False)

    # --- Polymorphic Discriminator ---
    capsule_type = Column(String, nullable=False)

    # --- Common Fields from BaseCapsule ---
    version = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False)
    verification = Column(JSON, nullable=False)  # Stores the Verification model

    # --- Versioning Fields for Immutable Capsule Chain ---
    parent_capsule_id = Column(String, nullable=True)  # Reference to original capsule
    version_number = Column(Integer, nullable=False, default=1)  # Version in chain
    is_original = Column(
        Boolean, nullable=False, default=True
    )  # True for v1, False for enriched versions

    # --- Payload Field ---
    # This field will store the specific payload for each capsule type,
    # e.g., reasoning_trace, economic_transaction, etc.
    payload = Column(JSON, nullable=False)

    # --- Outcome Tracking Fields ---
    # Track whether the capsule's suggestions/decisions worked out
    outcome_status = Column(
        String, nullable=True
    )  # success | failure | partial | pending | unknown
    outcome_timestamp = Column(
        DateTime(timezone=True), nullable=True
    )  # When outcome was recorded
    outcome_notes = Column(String, nullable=True)  # Free-form notes about the outcome
    outcome_metrics = Column(
        JSON, nullable=True
    )  # Structured metrics (tests_passed, errors_fixed, etc.)
    user_feedback_rating = Column(Float, nullable=True)  # 1-5 rating from user
    user_feedback_text = Column(String, nullable=True)  # User's feedback text
    follow_up_capsule_ids = Column(
        JSON, nullable=True
    )  # List of related follow-up capsule IDs

    # Removed polymorphism for simpler, more scalable approach
    # All capsule types use the same model with flexible JSON payload
    __mapper_args__ = {}

    @classmethod
    def from_pydantic(cls, pydantic_obj: AnyCapsule) -> "CapsuleModel":
        """Creates a SQLAlchemy model instance from a Pydantic schema."""
        # Extract the payload by finding the field that matches the capsule_type
        payload_field_name = (
            pydantic_obj.capsule_type.value
            if hasattr(pydantic_obj.capsule_type, "value")
            else str(pydantic_obj.capsule_type)
        )
        payload_data = getattr(pydantic_obj, payload_field_name)

        # Convert payload to dict
        payload_dict = payload_data.model_dump()

        # Wrap in UATP 7.0 envelope structure if not already wrapped
        if not is_envelope_format(payload_dict):
            # Extract parent capsule ID and agent ID for lineage
            parent_capsules = []
            if (
                "parent_capsule_id" in payload_dict
                and payload_dict["parent_capsule_id"]
            ):
                parent_capsules = [payload_dict["parent_capsule_id"]]

            # Extract agent ID from verification if available
            agent_id = None
            if hasattr(pydantic_obj.verification, "signer"):
                agent_id = pydantic_obj.verification.signer

            # Wrap the payload in UATP 7.0 envelope
            payload_dict = wrap_in_uatp_envelope(
                payload_data=payload_dict,
                capsule_id=pydantic_obj.capsule_id,
                capsule_type=pydantic_obj.capsule_type.value
                if hasattr(pydantic_obj.capsule_type, "value")
                else str(pydantic_obj.capsule_type),
                agent_id=agent_id,
                parent_capsules=parent_capsules,
            )

        # Generate model_map dynamically from all available capsule types
        model_map = {
            CapsuleType.REASONING_TRACE: ReasoningTraceCapsuleModel,
            CapsuleType.ECONOMIC_TRANSACTION: EconomicTransactionCapsuleModel,
            CapsuleType.GOVERNANCE_VOTE: GovernanceVoteCapsuleModel,
            CapsuleType.ETHICS_TRIGGER: EthicsTriggerCapsuleModel,
            CapsuleType.POST_QUANTUM_SIGNATURE: PostQuantumSignatureCapsuleModel,
            CapsuleType.CONSENT: ConsentCapsuleModel,
            CapsuleType.REMIX: RemixCapsuleModel,
            CapsuleType.TRUST_RENEWAL: TrustRenewalCapsuleModel,
            CapsuleType.SIMULATED_MALICE: SimulatedMaliceCapsuleModel,
            CapsuleType.IMPLICIT_CONSENT: ImplicitConsentCapsuleModel,
            CapsuleType.TEMPORAL_JUSTICE: TemporalJusticeCapsuleModel,
            CapsuleType.UNCERTAINTY: UncertaintyCapsuleModel,
            CapsuleType.CONFLICT_RESOLUTION: ConflictResolutionCapsuleModel,
            CapsuleType.PERSPECTIVE: PerspectiveCapsuleModel,
            CapsuleType.FEEDBACK_ASSIMILATION: FeedbackAssimilationCapsuleModel,
            CapsuleType.KNOWLEDGE_EXPIRY: KnowledgeExpiryCapsuleModel,
            CapsuleType.EMOTIONAL_LOAD: EmotionalLoadCapsuleModel,
            CapsuleType.MANIPULATION_ATTEMPT: ManipulationAttemptCapsuleModel,
            CapsuleType.COMPUTE_FOOTPRINT: ComputeFootprintCapsuleModel,
            CapsuleType.HAND_OFF: HandOffCapsuleModel,
            CapsuleType.RETIREMENT: RetirementCapsuleModel,
            CapsuleType.AUDIT: AuditCapsuleModel,
            CapsuleType.REFUSAL: RefusalCapsuleModel,
            CapsuleType.CLONING_RIGHTS: CloningRightsCapsuleModel,
            CapsuleType.EVOLUTION: EvolutionCapsuleModel,
            CapsuleType.DIVIDEND_BOND: DividendBondCapsuleModel,
            CapsuleType.CITIZENSHIP: CitizenshipCapsuleModel,
        }

        # Get capsule_type - handle both enum and string
        if hasattr(pydantic_obj.capsule_type, "value"):
            # It's an enum
            capsule_type_enum = pydantic_obj.capsule_type
            capsule_type_str = pydantic_obj.capsule_type.value
        else:
            # It's a string, convert to enum
            capsule_type_str = str(pydantic_obj.capsule_type)
            capsule_type_enum = CapsuleType(capsule_type_str)

        model_class = model_map[capsule_type_enum]

        return model_class(
            capsule_id=pydantic_obj.capsule_id,
            capsule_type=capsule_type_str,
            version=pydantic_obj.version,
            timestamp=pydantic_obj.timestamp,
            status=pydantic_obj.status,
            verification=pydantic_obj.verification.model_dump(),
            payload=payload_dict,  # Now contains the wrapped envelope
        )

    def to_pydantic(self) -> AnyCapsule:
        """Converts the SQLAlchemy model to a Pydantic schema object."""
        # Check if payload is a complete capsule (backwards compatibility)
        if isinstance(self.payload, dict) and "capsule_id" in self.payload:
            # Payload contains the complete capsule data - use it directly
            adapter = TypeAdapter(AnyCapsule)
            return adapter.validate_python(self.payload)
        else:
            # Legacy format: payload contains only the type-specific data
            base_data = {
                "capsule_id": self.capsule_id,
                "version": self.version,
                "timestamp": self.timestamp,
                "status": self.status,
                "capsule_type": self.capsule_type,
                "verification": self.verification,
            }

            # The payload field name is the same as the capsule_type value
            payload_field_name = self.capsule_type
            full_data = {**base_data, payload_field_name: self.payload}

            # Use TypeAdapter to validate the specific capsule type
            adapter = TypeAdapter(AnyCapsule)
            return adapter.validate_python(full_data)


# --- Concrete Models for Single-Table Inheritance ---


class ReasoningTraceCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.REASONING_TRACE.value}


class EconomicTransactionCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.ECONOMIC_TRANSACTION.value}


class GovernanceVoteCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.GOVERNANCE_VOTE.value}


class EthicsTriggerCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.ETHICS_TRIGGER.value}


class PostQuantumSignatureCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.POST_QUANTUM_SIGNATURE.value}


# --- UATP 7.0 Advanced Capsule Models ---


class ConsentCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.CONSENT.value}


class RemixCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.REMIX.value}


class TrustRenewalCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.TRUST_RENEWAL.value}


class SimulatedMaliceCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.SIMULATED_MALICE.value}


class ImplicitConsentCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.IMPLICIT_CONSENT.value}


class TemporalJusticeCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.TEMPORAL_JUSTICE.value}


class UncertaintyCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.UNCERTAINTY.value}


class ConflictResolutionCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.CONFLICT_RESOLUTION.value}


class PerspectiveCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.PERSPECTIVE.value}


class FeedbackAssimilationCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.FEEDBACK_ASSIMILATION.value}


class KnowledgeExpiryCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.KNOWLEDGE_EXPIRY.value}


class EmotionalLoadCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.EMOTIONAL_LOAD.value}


class ManipulationAttemptCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.MANIPULATION_ATTEMPT.value}


class ComputeFootprintCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.COMPUTE_FOOTPRINT.value}


class HandOffCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.HAND_OFF.value}


class RetirementCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.RETIREMENT.value}


# --- Mirror Mode Capsule Models ---


class AuditCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.AUDIT.value}


class RefusalCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.REFUSAL.value}


# --- Rights & Evolution Capsule Models ---


class CloningRightsCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.CLONING_RIGHTS.value}


class EvolutionCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.EVOLUTION.value}


class DividendBondCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.DIVIDEND_BOND.value}


class CitizenshipCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": CapsuleType.CITIZENSHIP.value}
