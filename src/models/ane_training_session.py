"""
Apple Silicon Training Session - SQLAlchemy ORM models for UATP 7.3 Training Provenance.

Captures Apple Silicon training provenance including:
- Hardware profiles with ANE, GPU/Metal, and MLX capabilities
- Training sessions with full provenance across accelerators
- Per-kernel execution traces (ANE, Metal, MLX, MPS)
- Compile artifacts: MIL programs, MLX graphs, Metal shader libraries
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import db


class ANESessionStatus(str, Enum):
    """Status of an ANE training session."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class KernelType(str, Enum):
    """Types of ANE kernels dispatched during training."""

    K_FWD_ATTN = "kFwdAttn"  # Forward attention
    K_FWD_FFN = "kFwdFFN"  # Forward feed-forward network
    K_FFN_BWD = "kFFNBwd"  # Backward FFN
    K_SDPA_BWD1 = "kSdpaBwd1"  # Scaled dot-product attention backward pass 1
    K_SDPA_BWD2 = "kSdpaBwd2"  # Scaled dot-product attention backward pass 2
    K_QKV_B = "kQKVb"  # Query/Key/Value backward
    OTHER = "other"


class HardwareProfileModel(db.Base):
    """
    Hardware profile model for ANE device capabilities.

    Records device hardware information including ANE availability,
    performance characteristics, and private API usage.
    """

    __tablename__ = "hardware_profiles"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    profile_id = Column(String(64), unique=True, nullable=False, index=True)

    # Device identification
    device_class = Column(String(50), nullable=False)  # mac, iphone, ipad
    chip_identifier = Column(String(50), nullable=False, index=True)  # M1, M2, M3, M4, A17
    chip_variant = Column(String(50), nullable=True)  # Pro, Max, Ultra
    device_id_hash = Column(String(64), nullable=False, index=True)

    # ANE capabilities
    ane_available = Column(Boolean, nullable=False, default=True)
    ane_version = Column(String(50), nullable=True)
    ane_tops = Column(Float, nullable=True)  # TOPS performance
    ane_compile_limit = Column(Integer, nullable=True)  # ~119 for M-series

    # GPU/Metal capabilities
    gpu_core_count = Column(Integer, nullable=True)  # GPU cores
    gpu_tflops = Column(Float, nullable=True)  # GPU compute performance
    metal_version = Column(String(50), nullable=True)  # e.g., "3.1"
    metal_family = Column(String(50), nullable=True)  # e.g., "apple9"
    mps_available = Column(Boolean, nullable=True, default=True)  # Metal Performance Shaders
    mlx_version = Column(String(50), nullable=True)  # e.g., "0.20.0"
    frameworks_used = Column(JSON, nullable=True)  # ["mlx", "pytorch_mps", "coreml"]

    # Memory and performance
    memory_bandwidth_gbps = Column(Float, nullable=True)
    unified_memory_gb = Column(Float, nullable=True)

    # Software versions
    os_version = Column(String(50), nullable=True)
    coreml_version = Column(String(50), nullable=True)

    # Private API usage
    private_apis_used = Column(JSON, nullable=True)  # List of private APIs

    # Verification
    verification = Column(JSON, nullable=True)
    capsule_id = Column(String(64), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    ane_sessions = relationship("ANETrainingSessionModel", back_populates="hardware_profile")

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary representation."""
        return {
            "profile_id": self.profile_id,
            "device_class": self.device_class,
            "chip_identifier": self.chip_identifier,
            "chip_variant": self.chip_variant,
            "device_id_hash": self.device_id_hash,
            "ane_available": self.ane_available,
            "ane_version": self.ane_version,
            "ane_tops": self.ane_tops,
            "ane_compile_limit": self.ane_compile_limit,
            "gpu_core_count": self.gpu_core_count,
            "gpu_tflops": self.gpu_tflops,
            "metal_version": self.metal_version,
            "metal_family": self.metal_family,
            "mps_available": self.mps_available,
            "mlx_version": self.mlx_version,
            "frameworks_used": self.frameworks_used or [],
            "memory_bandwidth_gbps": self.memory_bandwidth_gbps,
            "unified_memory_gb": self.unified_memory_gb,
            "os_version": self.os_version,
            "coreml_version": self.coreml_version,
            "private_apis_used": self.private_apis_used or [],
            "capsule_id": self.capsule_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<HardwareProfileModel(profile_id='{self.profile_id}', "
            f"chip='{self.chip_identifier}', ane={self.ane_available}, "
            f"gpu_cores={self.gpu_core_count})>"
        )


class ANETrainingSessionModel(db.Base):
    """
    ANE training session model for UATP 7.3 ANE Training Provenance.

    Tracks complete ANE training sessions with hardware profile,
    kernel executions, compile artifacts, and performance metrics.
    """

    __tablename__ = "ane_training_sessions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)

    # Model information
    model_id = Column(String(64), nullable=False, index=True)
    model_name = Column(String(255), nullable=True)

    # Hardware profile link
    hardware_profile_id = Column(
        String(64),
        ForeignKey("hardware_profiles.profile_id"),
        nullable=False,
        index=True,
    )
    hardware_profile = relationship("HardwareProfileModel", back_populates="ane_sessions")

    # Session status
    status = Column(String(50), nullable=False, default="pending")  # ANESessionStatus

    # Training progress
    total_steps = Column(Integer, nullable=True)
    completed_steps = Column(Integer, default=0)
    kernel_execution_count = Column(Integer, default=0)

    # Performance metrics
    final_loss = Column(Float, nullable=True)
    avg_ms_per_step = Column(Float, nullable=True)
    avg_ane_utilization = Column(Float, nullable=True)  # Percentage
    total_ane_time_seconds = Column(Float, nullable=True)
    total_cpu_time_seconds = Column(Float, nullable=True)

    # GPU/Metal metrics
    avg_gpu_utilization = Column(Float, nullable=True)  # Percentage
    peak_gpu_utilization = Column(Float, nullable=True)  # Percentage
    gpu_memory_used_gb = Column(Float, nullable=True)
    total_gpu_time_seconds = Column(Float, nullable=True)
    primary_accelerator = Column(String(50), nullable=True)  # ane, gpu, cpu

    # Configuration (JSON fields)
    hyperparameters = Column(JSON, nullable=True)
    dataset_refs = Column(JSON, nullable=True)
    compile_artifact_ids = Column(JSON, nullable=True)  # List of artifact IDs

    # Private API and legal
    private_apis_used = Column(JSON, nullable=True)
    dmca_1201f_claim = Column(Boolean, default=False)
    research_purpose = Column(Text, nullable=True)

    # Additional metadata
    session_metadata = Column(JSON, nullable=True)

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

    # Relationships
    kernel_executions = relationship(
        "KernelExecutionModel",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    compile_artifacts = relationship(
        "CompileArtifactModel",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary representation."""
        return {
            "session_id": self.session_id,
            "model_id": self.model_id,
            "model_name": self.model_name,
            "hardware_profile_id": self.hardware_profile_id,
            "status": self.status,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "kernel_execution_count": self.kernel_execution_count,
            "final_loss": self.final_loss,
            "avg_ms_per_step": self.avg_ms_per_step,
            "avg_ane_utilization": self.avg_ane_utilization,
            "total_ane_time_seconds": self.total_ane_time_seconds,
            "total_cpu_time_seconds": self.total_cpu_time_seconds,
            "avg_gpu_utilization": self.avg_gpu_utilization,
            "peak_gpu_utilization": self.peak_gpu_utilization,
            "gpu_memory_used_gb": self.gpu_memory_used_gb,
            "total_gpu_time_seconds": self.total_gpu_time_seconds,
            "primary_accelerator": self.primary_accelerator,
            "hyperparameters": self.hyperparameters,
            "dataset_refs": self.dataset_refs,
            "compile_artifact_ids": self.compile_artifact_ids or [],
            "private_apis_used": self.private_apis_used or [],
            "dmca_1201f_claim": self.dmca_1201f_claim,
            "research_purpose": self.research_purpose,
            "session_metadata": self.session_metadata,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "capsule_id": self.capsule_id,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def get_duration_seconds(self) -> Optional[float]:
        """Get session duration in seconds if completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def get_ane_percentage(self) -> Optional[float]:
        """Calculate ANE usage percentage."""
        if self.total_ane_time_seconds and self.total_cpu_time_seconds:
            total = self.total_ane_time_seconds + self.total_cpu_time_seconds
            if total > 0:
                return (self.total_ane_time_seconds / total) * 100
        return None

    def __repr__(self) -> str:
        return (
            f"<ANETrainingSessionModel(session_id='{self.session_id}', "
            f"model_id='{self.model_id}', status='{self.status}')>"
        )


class KernelExecutionModel(db.Base):
    """
    Kernel execution model for per-kernel dispatch tracking.

    Records individual kernel executions on ANE, Metal GPU, or MLX including
    timing, shapes, and compute attribution.
    """

    __tablename__ = "kernel_executions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    execution_id = Column(String(64), unique=True, nullable=False, index=True)

    # Session link
    session_id = Column(
        String(64),
        ForeignKey("ane_training_sessions.session_id"),
        nullable=False,
        index=True,
    )
    session = relationship("ANETrainingSessionModel", back_populates="kernel_executions")

    # Accelerator type
    accelerator_type = Column(
        String(50), nullable=False, default="ane", index=True
    )  # ane, metal, mlx, mps, cpu

    # Kernel information
    kernel_type = Column(String(50), nullable=False, index=True)  # KernelType values or Metal/MLX kernels
    step_index = Column(Integer, nullable=False, index=True)
    dispatch_index = Column(Integer, nullable=False)

    # Timing
    execution_time_us = Column(Integer, nullable=False)  # Microseconds

    # Shape information
    input_shape = Column(JSON, nullable=True)
    output_shape = Column(JSON, nullable=True)
    iosurface_format = Column(String(100), nullable=True)  # e.g., [1,C,1,S]

    # Compute attribution
    compute_attribution = Column(JSON, nullable=True)  # HybridComputeAttribution

    # ANE program reference
    ane_program_hash = Column(String(64), nullable=True)

    # Metal/MLX references
    metal_buffer_mode = Column(String(50), nullable=True)  # shared, private, managed
    metal_shader_hash = Column(String(64), nullable=True)
    mlx_graph_hash = Column(String(64), nullable=True)

    # Verification
    verification = Column(JSON, nullable=True)
    capsule_id = Column(String(64), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert execution to dictionary representation."""
        return {
            "execution_id": self.execution_id,
            "session_id": self.session_id,
            "accelerator_type": self.accelerator_type,
            "kernel_type": self.kernel_type,
            "step_index": self.step_index,
            "dispatch_index": self.dispatch_index,
            "execution_time_us": self.execution_time_us,
            "input_shape": self.input_shape,
            "output_shape": self.output_shape,
            "iosurface_format": self.iosurface_format,
            "compute_attribution": self.compute_attribution,
            "ane_program_hash": self.ane_program_hash,
            "metal_buffer_mode": self.metal_buffer_mode,
            "metal_shader_hash": self.metal_shader_hash,
            "mlx_graph_hash": self.mlx_graph_hash,
            "capsule_id": self.capsule_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<KernelExecutionModel(execution_id='{self.execution_id}', "
            f"accelerator='{self.accelerator_type}', kernel='{self.kernel_type}', step={self.step_index})>"
        )


class CompileArtifactModel(db.Base):
    """
    Compile artifact model for MIL programs, MLX graphs, and Metal shaders.

    Records compiled ML artifacts with content hashes, optimizations,
    and storage references across ANE, Metal GPU, and MLX.
    """

    __tablename__ = "compile_artifacts"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    artifact_id = Column(String(64), unique=True, nullable=False, index=True)

    # Session link
    session_id = Column(
        String(64),
        ForeignKey("ane_training_sessions.session_id"),
        nullable=False,
        index=True,
    )
    session = relationship("ANETrainingSessionModel", back_populates="compile_artifacts")

    # Artifact format
    artifact_format = Column(
        String(50), nullable=False, default="mil", index=True
    )  # mil, mlx, metal, safetensors, gguf

    # Content hashes (MIL/CoreML)
    mil_program_hash = Column(String(64), nullable=True, index=True)
    weight_blob_hash = Column(String(64), nullable=True)
    compiled_model_hash = Column(String(64), nullable=True)

    # MLX artifact hashes
    mlx_graph_hash = Column(String(64), nullable=True, index=True)
    mlx_version = Column(String(50), nullable=True)
    mlx_simplifications = Column(JSON, nullable=True)  # List of simplification passes

    # Metal artifact hashes
    metal_library_hash = Column(String(64), nullable=True, index=True)

    # Target accelerator
    target_accelerator = Column(String(50), nullable=True)  # ane, gpu, cpu

    # Compilation details
    compile_time_ms = Column(Integer, nullable=True)
    target_device = Column(String(50), nullable=True)
    coreml_spec_version = Column(Integer, nullable=True)
    mlmodel_size_bytes = Column(Integer, nullable=True)

    # Fusion optimizations
    fusion_optimizations = Column(JSON, nullable=True)  # List of MILFusionOptimization

    # Storage
    storage_uri = Column(String(500), nullable=True)

    # Verification
    verification = Column(JSON, nullable=True)
    capsule_id = Column(String(64), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert artifact to dictionary representation."""
        return {
            "artifact_id": self.artifact_id,
            "session_id": self.session_id,
            "artifact_format": self.artifact_format,
            "mil_program_hash": self.mil_program_hash,
            "weight_blob_hash": self.weight_blob_hash,
            "compiled_model_hash": self.compiled_model_hash,
            "mlx_graph_hash": self.mlx_graph_hash,
            "mlx_version": self.mlx_version,
            "mlx_simplifications": self.mlx_simplifications or [],
            "metal_library_hash": self.metal_library_hash,
            "target_accelerator": self.target_accelerator,
            "compile_time_ms": self.compile_time_ms,
            "target_device": self.target_device,
            "coreml_spec_version": self.coreml_spec_version,
            "mlmodel_size_bytes": self.mlmodel_size_bytes,
            "fusion_optimizations": self.fusion_optimizations or [],
            "storage_uri": self.storage_uri,
            "capsule_id": self.capsule_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def get_fusion_count(self) -> int:
        """Get number of fusion optimizations applied."""
        if self.fusion_optimizations:
            return len(self.fusion_optimizations)
        return 0

    def get_primary_hash(self) -> Optional[str]:
        """Get the primary content hash based on artifact format."""
        if self.artifact_format == "mlx":
            return self.mlx_graph_hash
        elif self.artifact_format == "metal":
            return self.metal_library_hash
        return self.mil_program_hash

    def __repr__(self) -> str:
        primary_hash = self.get_primary_hash()
        hash_preview = primary_hash[:8] if primary_hash else "none"
        return (
            f"<CompileArtifactModel(artifact_id='{self.artifact_id}', "
            f"format='{self.artifact_format}', hash='{hash_preview}...')>"
        )
