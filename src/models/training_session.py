"""
TrainingSession - SQLAlchemy ORM model for UATP 7.2 Training Provenance.

Records training sessions including fine-tuning, RLHF, DPO, and adapter
training with full provenance tracking for dataset references,
hyperparameters, and compute resources.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import db


class SessionType(str, Enum):
    """Types of training sessions."""

    PRE_TRAINING = "pre_training"
    FINE_TUNING = "fine_tuning"
    RLHF = "rlhf"
    DPO = "dpo"
    SFT = "sft"
    ADAPTER = "adapter"
    DISTILLATION = "distillation"
    QUANTIZATION = "quantization"


class SessionStatus(str, Enum):
    """Status of a training session."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingSessionModel(db.Base):
    """
    Training session model for UATP 7.2 Training Provenance.

    Tracks individual training runs with full provenance including
    dataset references, hyperparameters, compute resources, and
    cryptographic verification.
    """

    __tablename__ = "training_sessions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)

    # Link to model registry
    model_id = Column(
        String(64),
        ForeignKey("model_registry.model_id"),
        nullable=False,
        index=True,
    )
    model = relationship("ModelRegistryModel", back_populates="training_sessions")

    # Session classification
    session_type = Column(String(50), nullable=False)  # SessionType values
    status = Column(String(50), nullable=False, default="pending")  # SessionStatus

    # Training data and configuration (JSON fields)
    dataset_refs = Column(JSON, nullable=False)  # Required: dataset provenance
    hyperparameters = Column(JSON, nullable=True)
    compute_resources = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    checkpoints = Column(JSON, nullable=True)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Verification and capsule link
    verification = Column(JSON, nullable=True)
    capsule_id = Column(String(64), nullable=True)

    # Ownership
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    owner = relationship("UserModel", foreign_keys=[owner_id])

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary representation."""
        return {
            "session_id": self.session_id,
            "model_id": self.model_id,
            "session_type": self.session_type,
            "status": self.status,
            "dataset_refs": self.dataset_refs,
            "hyperparameters": self.hyperparameters,
            "compute_resources": self.compute_resources,
            "metrics": self.metrics,
            "checkpoints": self.checkpoints,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "verification": self.verification,
            "capsule_id": self.capsule_id,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def get_duration_seconds(self) -> Optional[float]:
        """Get training duration in seconds if completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def get_dataset_ids(self) -> List[str]:
        """Extract dataset IDs from dataset_refs."""
        if not self.dataset_refs:
            return []
        if isinstance(self.dataset_refs, list):
            return [ref.get("dataset_id", "") for ref in self.dataset_refs if ref]
        return []

    def __repr__(self) -> str:
        return (
            f"<TrainingSessionModel(session_id='{self.session_id}', "
            f"model_id='{self.model_id}', type='{self.session_type}', "
            f"status='{self.status}')>"
        )
