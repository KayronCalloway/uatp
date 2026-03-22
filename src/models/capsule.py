"""
CapsuleModel - SQLAlchemy ORM model for UATP capsules.

Design Decision (2026-01-13):
    This model uses a single table with a JSON payload column for all capsule types.
    Type discrimination is handled by the `capsule_type` string column.

    We explicitly DO NOT use SQLAlchemy polymorphism because:
    1. All capsule types share identical columns
    2. Type-specific data lives in the JSON `payload` column
    3. Polymorphism adds complexity without benefit
    4. Empty subclasses caused async session bugs (see docs/incidents/2026-01-13_ORM_POLYMORPHISM_INCIDENT.md)

    To query by type:
        session.query(CapsuleModel).filter(CapsuleModel.capsule_type == "reasoning_trace")
"""

from pydantic import TypeAdapter
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.capsule_schema import AnyCapsule
from src.core.database import db
from src.utils.uatp_envelope import is_envelope_format, wrap_in_uatp_envelope


class CapsuleModel(db.Base):
    """
    Single unified model for all UATP capsule types.

    The capsule_type column indicates the type (e.g., "reasoning_trace", "economic_transaction").
    The payload column contains type-specific data as JSON.
    """

    __tablename__ = "capsules"
    __table_args__ = (
        UniqueConstraint("capsule_id", name="uq_capsule_id"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True)
    capsule_id = Column(String, nullable=False)

    # --- Ownership Fields ---
    # owner_id enables user-scoped capsule isolation
    # NULL owner_id indicates legacy/system capsules (visible to admin only)
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    owner = relationship("UserModel", back_populates="capsules")

    # --- Type Discriminator (NOT polymorphic - just a string column) ---
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
    # This field stores ALL type-specific data for each capsule type.
    # e.g., reasoning_trace, economic_transaction, etc.
    payload = Column(JSON, nullable=False)

    # --- Encrypted Payload Fields ---
    # For client-side encryption: payload is encrypted before storage
    # encrypted_payload stores Base64 ciphertext, encryption_metadata stores {iv, algorithm}
    encrypted_payload = Column(Text, nullable=True)  # Base64 ciphertext
    encryption_metadata = Column(JSON, nullable=True)  # {iv, algorithm, key_id}

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

    # --- Embedding Fields ---
    # Vector embeddings for semantic similarity search
    embedding = Column(JSON, nullable=True)  # TF-IDF or OpenAI embedding vector
    embedding_model = Column(String(100), nullable=True)  # Model used for embedding
    embedding_created_at = Column(DateTime(timezone=True), nullable=True)

    # --- UATP 7.2 Workflow Chain Fields ---
    # Link capsules to parent workflow for multi-step agent workflows
    workflow_capsule_id = Column(
        String(64), nullable=True, index=True
    )  # Parent workflow ID
    step_index = Column(Integer, nullable=True)  # Position in workflow (0-indexed)
    step_type = Column(
        String(50), nullable=True
    )  # plan, tool_call, inference, output, human_input, verification
    depends_on_steps = Column(
        JSON, nullable=True
    )  # List of step indices this depends on

    # --- Cryptographic Chaining ---
    # Creates tamper-evident chain where each capsule stores hash of previous
    prev_hash = Column(
        String(64), nullable=True, index=True
    )  # SHA256 of previous capsule
    content_hash = Column(
        String(64), nullable=True, index=True
    )  # SHA256 of this capsule's content

    # --- Compression ---
    # Auto-compress large capsules above threshold (default 10KB)
    is_compressed = Column(Boolean, nullable=True, default=False)
    compression_method = Column(String(20), nullable=True)  # zlib, lzma
    original_size = Column(Integer, nullable=True)
    compressed_size = Column(Integer, nullable=True)

    # No polymorphism - all capsule types use this single model
    __mapper_args__ = {}

    @classmethod
    def from_pydantic(cls, pydantic_obj: AnyCapsule) -> "CapsuleModel":
        """
        Creates a CapsuleModel instance from a Pydantic schema.

        Args:
            pydantic_obj: Any Pydantic capsule schema (ReasoningTraceCapsule, etc.)

        Returns:
            CapsuleModel instance ready for database insertion
        """
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

        # Get capsule_type as string
        capsule_type_str = (
            pydantic_obj.capsule_type.value
            if hasattr(pydantic_obj.capsule_type, "value")
            else str(pydantic_obj.capsule_type)
        )

        # Always return CapsuleModel - no subclass selection needed
        return cls(
            capsule_id=pydantic_obj.capsule_id,
            capsule_type=capsule_type_str,
            version=pydantic_obj.version,
            timestamp=pydantic_obj.timestamp,
            status=pydantic_obj.status,
            verification=pydantic_obj.verification.model_dump(),
            payload=payload_dict,
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

    def __repr__(self) -> str:
        return f"<CapsuleModel(id={self.id}, capsule_id='{self.capsule_id}', type='{self.capsule_type}')>"


# NOTE: All 26 subclasses (ReasoningTraceCapsuleModel, EconomicTransactionCapsuleModel, etc.)
# were removed on 2026-01-13. They added no value - just empty classes with polymorphic_identity.
# See docs/incidents/2026-01-13_ORM_POLYMORPHISM_INCIDENT.md for details.


# --- Immutability Constraint ---
# SECURITY: Sealed capsules are cryptographically signed and must never be modified.
# This event listener enforces immutability at the ORM level.

# Fields that can be modified on sealed capsules (metadata, not content)
MUTABLE_FIELDS_ON_SEALED = frozenset(
    {
        "outcome_status",
        "outcome_timestamp",
        "outcome_notes",
        "outcome_metrics",
        "user_feedback_rating",
        "user_feedback_text",
        "follow_up_capsule_ids",
        "embedding",
        "embedding_model",
        "embedding_created_at",
    }
)


@event.listens_for(CapsuleModel, "before_update")
def enforce_capsule_immutability(mapper, connection, target):
    """
    Prevent modification of sealed capsules except for allowed metadata fields.

    Sealed capsules have cryptographic signatures that would be invalidated
    by any content changes. This constraint ensures data integrity.
    """
    from sqlalchemy import inspect

    # Check if capsule is sealed (case-insensitive)
    if target.status and target.status.lower() == "sealed":
        state = inspect(target)

        # Check each attribute for modifications
        for attr in state.attrs:
            hist = attr.load_history()

            # If attribute was modified (has changes)
            if hist.has_changes():
                attr_name = attr.key

                # Allow status changes (e.g., unsealing for admin operations)
                if attr_name == "status":
                    continue

                # Allow mutable metadata fields
                if attr_name in MUTABLE_FIELDS_ON_SEALED:
                    continue

                # Block modification of immutable fields
                raise ValueError(
                    f"Cannot modify '{attr_name}' on sealed capsule {target.capsule_id}. "
                    f"Sealed capsules are cryptographically signed and immutable. "
                    f"Only metadata fields can be updated: {sorted(MUTABLE_FIELDS_ON_SEALED)}"
                )
