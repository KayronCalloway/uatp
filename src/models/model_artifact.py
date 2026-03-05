"""
Model Artifact SQLAlchemy Model - UATP 7.2 Model Registry Protocol

Content-addressed storage for model files with integrity verification.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.core.database import db


class ArtifactType(str, Enum):
    """Type of model artifact."""

    WEIGHTS = "weights"
    CONFIG = "config"
    TOKENIZER = "tokenizer"
    ADAPTER = "adapter"
    CHECKPOINT = "checkpoint"
    MERGED = "merged"
    VOCABULARY = "vocabulary"
    EMBEDDING = "embedding"


class StorageBackend(str, Enum):
    """Storage backend for artifacts."""

    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"
    IPFS = "ipfs"


class UploadStatus(str, Enum):
    """Status of artifact upload."""

    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class ArtifactFormat(str, Enum):
    """File format of artifact."""

    SAFETENSORS = "safetensors"
    PYTORCH = "pytorch"
    GGUF = "gguf"
    ONNX = "onnx"
    TENSORFLOW = "tensorflow"
    JAX = "jax"


class ModelArtifactModel(db.Base):
    """
    SQLAlchemy model for content-addressed model artifacts.

    Provides secure, verifiable storage of model files with
    cryptographic integrity checking.
    """

    __tablename__ = "model_artifacts"

    id = Column(Integer, primary_key=True)
    artifact_id = Column(String(64), unique=True, nullable=False, index=True)
    model_id = Column(
        String(64),
        ForeignKey("model_registry.model_id"),
        nullable=False,
        index=True,
    )

    # Artifact type and format
    artifact_type = Column(String(50), nullable=False)
    format = Column(String(50), nullable=True)

    # Content addressing
    content_hash = Column(String(64), nullable=False, index=True)
    size_bytes = Column(BigInteger, nullable=False)

    # Storage location
    storage_uri = Column(String(512), nullable=False)
    storage_backend = Column(String(50), nullable=True, default="local")

    # Security
    encryption_key_id = Column(String(64), nullable=True)
    compression = Column(String(50), nullable=True)

    # Metadata and verification
    artifact_metadata = Column(JSON, nullable=True)
    verification = Column(JSON, nullable=True)

    # Status
    upload_status = Column(String(50), nullable=False, default="pending")

    # Ownership
    owner_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ModelArtifact(artifact_id={self.artifact_id}, type={self.artifact_type})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "artifact_id": self.artifact_id,
            "model_id": self.model_id,
            "artifact_type": self.artifact_type,
            "format": self.format,
            "content_hash": self.content_hash,
            "size_bytes": self.size_bytes,
            "storage_uri": self.storage_uri,
            "storage_backend": self.storage_backend,
            "encryption_key_id": self.encryption_key_id,
            "compression": self.compression,
            "metadata": self.artifact_metadata,
            "verification": self.verification,
            "upload_status": self.upload_status,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_verified(self) -> bool:
        """Check if artifact has been cryptographically verified."""
        return bool(self.verification and self.verification.get("verified"))

    @property
    def is_encrypted(self) -> bool:
        """Check if artifact is encrypted."""
        return bool(self.encryption_key_id)

    @property
    def size_mb(self) -> float:
        """Get size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def size_gb(self) -> float:
        """Get size in gigabytes."""
        return self.size_bytes / (1024 * 1024 * 1024)
