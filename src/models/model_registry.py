"""
ModelRegistry - SQLAlchemy ORM model for UATP 7.2 Training Provenance.

Tracks registered AI models with their lineage from base models through
fine-tuning and adaptation. Supports content-addressed model storage
and license verification.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import db


class ModelRegistryModel(db.Base):
    """
    Model registry for UATP 7.2 Training Provenance.

    Stores AI model metadata including lineage (base_model_id),
    training configuration, dataset provenance, and licensing.
    """

    __tablename__ = "model_registry"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    model_id = Column(String(64), unique=True, nullable=False, index=True)
    model_hash = Column(String(64), nullable=False)
    base_model_id = Column(String(64), nullable=True, index=True)

    # Model classification
    model_type = Column(
        String(50), nullable=False
    )  # 'base', 'fine_tune', 'adapter', 'merged'
    version = Column(String(32), nullable=False)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Provenance data (JSON fields)
    training_config = Column(JSON, nullable=True)
    dataset_provenance = Column(JSON, nullable=True)
    license_info = Column(JSON, nullable=True)
    attestation = Column(JSON, nullable=True)
    capabilities = Column(JSON, nullable=True)
    safety_evaluations = Column(JSON, nullable=True)

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
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    training_sessions = relationship(
        "TrainingSessionModel", back_populates="model", lazy="dynamic"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary representation."""
        return {
            "model_id": self.model_id,
            "model_hash": self.model_hash,
            "base_model_id": self.base_model_id,
            "model_type": self.model_type,
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "training_config": self.training_config,
            "dataset_provenance": self.dataset_provenance,
            "license_info": self.license_info,
            "attestation": self.attestation,
            "capabilities": self.capabilities,
            "safety_evaluations": self.safety_evaluations,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_lineage_chain(self) -> List[str]:
        """
        Get the lineage chain from this model back to its base.
        Returns list of model_ids from current to root.
        """
        chain = [self.model_id]
        if self.base_model_id:
            chain.append(self.base_model_id)
        return chain

    def __repr__(self) -> str:
        return (
            f"<ModelRegistryModel(model_id='{self.model_id}', "
            f"type='{self.model_type}', version='{self.version}')>"
        )
