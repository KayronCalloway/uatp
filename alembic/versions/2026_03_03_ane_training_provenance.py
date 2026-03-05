"""
Apple Silicon Training Provenance Schema Migration (UATP 7.3)
=============================================================

Adds tables for tracking Apple Silicon training provenance:
- hardware_profiles: Device ANE, GPU/Metal, and MLX capabilities
- ane_training_sessions: Training sessions across all Apple accelerators
- kernel_executions: Per-kernel dispatch tracking (ANE, Metal, MLX, MPS)
- compile_artifacts: MIL programs, MLX graphs, Metal shader libraries

Revision ID: 2026_03_03_ane_training_provenance
Revises: 2026_03_02_model_artifacts
Create Date: 2026-03-03
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_03_03_ane_training_provenance"
down_revision = "2026_03_02_model_artifacts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add tables for UATP 7.3 ANE Training Provenance:
    - hardware_profiles: Device ANE capabilities
    - ane_training_sessions: ANE training sessions
    - kernel_executions: Per-kernel dispatch tracking
    - compile_artifacts: MIL compile artifacts
    """
    # Create hardware_profiles table
    op.create_table(
        "hardware_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "profile_id", sa.String(64), unique=True, nullable=False, index=True
        ),
        # Device identification
        sa.Column(
            "device_class",
            sa.String(50),
            nullable=False,
            comment="Device class: mac, iphone, ipad",
        ),
        sa.Column(
            "chip_identifier",
            sa.String(50),
            nullable=False,
            index=True,
            comment="Chip: M1, M2, M3, M4, A17, etc.",
        ),
        sa.Column(
            "chip_variant",
            sa.String(50),
            nullable=True,
            comment="Variant: Pro, Max, Ultra",
        ),
        sa.Column("device_id_hash", sa.String(64), nullable=False, index=True),
        # ANE capabilities
        sa.Column("ane_available", sa.Boolean(), nullable=False, default=True),
        sa.Column("ane_version", sa.String(50), nullable=True),
        sa.Column(
            "ane_tops",
            sa.Float(),
            nullable=True,
            comment="ANE performance in TOPS",
        ),
        sa.Column(
            "ane_compile_limit",
            sa.Integer(),
            nullable=True,
            comment="Max compiled models (~119 for M-series)",
        ),
        # GPU/Metal capabilities
        sa.Column(
            "gpu_core_count",
            sa.Integer(),
            nullable=True,
            comment="Number of GPU cores",
        ),
        sa.Column(
            "gpu_tflops",
            sa.Float(),
            nullable=True,
            comment="GPU compute performance in TFLOPS",
        ),
        sa.Column(
            "metal_version",
            sa.String(50),
            nullable=True,
            comment="Metal version e.g. 3.1",
        ),
        sa.Column(
            "metal_family",
            sa.String(50),
            nullable=True,
            comment="Metal GPU family e.g. apple9",
        ),
        sa.Column(
            "mps_available",
            sa.Boolean(),
            nullable=True,
            default=True,
            comment="Metal Performance Shaders available",
        ),
        sa.Column(
            "mlx_version",
            sa.String(50),
            nullable=True,
            comment="MLX framework version e.g. 0.20.0",
        ),
        sa.Column(
            "frameworks_used",
            sa.JSON(),
            nullable=True,
            comment="List: mlx, pytorch_mps, coreml, tensorflow_metal",
        ),
        # Memory and performance
        sa.Column(
            "memory_bandwidth_gbps",
            sa.Float(),
            nullable=True,
            comment="Memory bandwidth in GB/s",
        ),
        sa.Column(
            "unified_memory_gb",
            sa.Float(),
            nullable=True,
            comment="Unified memory in GB",
        ),
        # Software versions
        sa.Column("os_version", sa.String(50), nullable=True),
        sa.Column("coreml_version", sa.String(50), nullable=True),
        # Private API usage
        sa.Column(
            "private_apis_used",
            sa.JSON(),
            nullable=True,
            comment="List: _ANEClient, _ANECompiler, etc.",
        ),
        # Verification
        sa.Column("verification", sa.JSON(), nullable=True),
        sa.Column("capsule_id", sa.String(64), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create ane_training_sessions table
    op.create_table(
        "ane_training_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id", sa.String(64), unique=True, nullable=False, index=True
        ),
        # Model information
        sa.Column("model_id", sa.String(64), nullable=False, index=True),
        sa.Column("model_name", sa.String(255), nullable=True),
        # Hardware profile link
        sa.Column(
            "hardware_profile_id",
            sa.String(64),
            sa.ForeignKey("hardware_profiles.profile_id"),
            nullable=False,
            index=True,
        ),
        # Session status
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            default="pending",
            comment="Status: pending, running, completed, failed, cancelled",
        ),
        # Training progress
        sa.Column("total_steps", sa.Integer(), nullable=True),
        sa.Column("completed_steps", sa.Integer(), default=0),
        sa.Column("kernel_execution_count", sa.Integer(), default=0),
        # Performance metrics
        sa.Column("final_loss", sa.Float(), nullable=True),
        sa.Column("avg_ms_per_step", sa.Float(), nullable=True),
        sa.Column(
            "avg_ane_utilization",
            sa.Float(),
            nullable=True,
            comment="ANE utilization percentage",
        ),
        sa.Column("total_ane_time_seconds", sa.Float(), nullable=True),
        sa.Column("total_cpu_time_seconds", sa.Float(), nullable=True),
        # GPU/Metal metrics
        sa.Column(
            "avg_gpu_utilization",
            sa.Float(),
            nullable=True,
            comment="GPU utilization percentage",
        ),
        sa.Column(
            "peak_gpu_utilization",
            sa.Float(),
            nullable=True,
            comment="Peak GPU utilization percentage",
        ),
        sa.Column(
            "gpu_memory_used_gb",
            sa.Float(),
            nullable=True,
            comment="GPU memory used in GB",
        ),
        sa.Column("total_gpu_time_seconds", sa.Float(), nullable=True),
        sa.Column(
            "primary_accelerator",
            sa.String(50),
            nullable=True,
            comment="Primary accelerator: ane, gpu, cpu",
        ),
        # Configuration (JSON fields)
        sa.Column("hyperparameters", sa.JSON(), nullable=True),
        sa.Column("dataset_refs", sa.JSON(), nullable=True),
        sa.Column(
            "compile_artifact_ids",
            sa.JSON(),
            nullable=True,
            comment="List of compile artifact IDs",
        ),
        # Private API and legal
        sa.Column("private_apis_used", sa.JSON(), nullable=True),
        sa.Column(
            "dmca_1201f_claim",
            sa.Boolean(),
            default=False,
            comment="DMCA 1201(f) interoperability claim",
        ),
        sa.Column("research_purpose", sa.Text(), nullable=True),
        # Additional metadata
        sa.Column("session_metadata", sa.JSON(), nullable=True),
        # Timing
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=False, index=True
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # Verification
        sa.Column("verification", sa.JSON(), nullable=True),
        sa.Column("capsule_id", sa.String(64), nullable=True),
        # Ownership
        sa.Column(
            "owner_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
            index=True,
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create kernel_executions table
    op.create_table(
        "kernel_executions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "execution_id", sa.String(64), unique=True, nullable=False, index=True
        ),
        # Session link
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("ane_training_sessions.session_id"),
            nullable=False,
            index=True,
        ),
        # Accelerator type
        sa.Column(
            "accelerator_type",
            sa.String(50),
            nullable=False,
            default="ane",
            index=True,
            comment="Type: ane, metal, mlx, mps, cpu",
        ),
        # Kernel information
        sa.Column(
            "kernel_type",
            sa.String(50),
            nullable=False,
            index=True,
            comment="ANE: kFwdAttn, etc. Metal: metal_gemm. MLX: mlx_matmul",
        ),
        sa.Column("step_index", sa.Integer(), nullable=False, index=True),
        sa.Column("dispatch_index", sa.Integer(), nullable=False),
        # Timing
        sa.Column(
            "execution_time_us",
            sa.Integer(),
            nullable=False,
            comment="Execution time in microseconds",
        ),
        # Shape information
        sa.Column("input_shape", sa.JSON(), nullable=True),
        sa.Column("output_shape", sa.JSON(), nullable=True),
        sa.Column(
            "iosurface_format",
            sa.String(100),
            nullable=True,
            comment="e.g., [1,C,1,S]",
        ),
        # Compute attribution
        sa.Column(
            "compute_attribution",
            sa.JSON(),
            nullable=True,
            comment="HybridComputeAttribution",
        ),
        # ANE program reference
        sa.Column("ane_program_hash", sa.String(64), nullable=True),
        # Metal/MLX references
        sa.Column(
            "metal_buffer_mode",
            sa.String(50),
            nullable=True,
            comment="Metal buffer mode: shared, private, managed",
        ),
        sa.Column("metal_shader_hash", sa.String(64), nullable=True),
        sa.Column("mlx_graph_hash", sa.String(64), nullable=True),
        # Verification
        sa.Column("verification", sa.JSON(), nullable=True),
        sa.Column("capsule_id", sa.String(64), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create composite index for step queries
    op.create_index(
        "ix_kernel_executions_session_step",
        "kernel_executions",
        ["session_id", "step_index"],
    )

    # Create index for accelerator type queries
    op.create_index(
        "ix_kernel_executions_session_accelerator",
        "kernel_executions",
        ["session_id", "accelerator_type"],
    )

    # Create compile_artifacts table
    op.create_table(
        "compile_artifacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "artifact_id", sa.String(64), unique=True, nullable=False, index=True
        ),
        # Session link
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("ane_training_sessions.session_id"),
            nullable=False,
            index=True,
        ),
        # Artifact format
        sa.Column(
            "artifact_format",
            sa.String(50),
            nullable=False,
            default="mil",
            index=True,
            comment="Format: mil, mlx, metal, safetensors, gguf",
        ),
        # Content hashes (MIL/CoreML)
        sa.Column("mil_program_hash", sa.String(64), nullable=True, index=True),
        sa.Column("weight_blob_hash", sa.String(64), nullable=True),
        sa.Column("compiled_model_hash", sa.String(64), nullable=True),
        # MLX artifact hashes
        sa.Column("mlx_graph_hash", sa.String(64), nullable=True, index=True),
        sa.Column(
            "mlx_version",
            sa.String(50),
            nullable=True,
            comment="MLX version used for compilation",
        ),
        sa.Column(
            "mlx_simplifications",
            sa.JSON(),
            nullable=True,
            comment="List of MLX simplification passes",
        ),
        # Metal artifact hashes
        sa.Column("metal_library_hash", sa.String(64), nullable=True, index=True),
        # Target accelerator
        sa.Column(
            "target_accelerator",
            sa.String(50),
            nullable=True,
            comment="Target: ane, gpu, cpu",
        ),
        # Compilation details
        sa.Column(
            "compile_time_ms",
            sa.Integer(),
            nullable=True,
            comment="Compilation time in milliseconds",
        ),
        sa.Column("target_device", sa.String(50), nullable=True),
        sa.Column("coreml_spec_version", sa.Integer(), nullable=True),
        sa.Column(
            "mlmodel_size_bytes",
            sa.Integer(),
            nullable=True,
            comment="Size of compiled .mlmodel",
        ),
        # Fusion optimizations
        sa.Column(
            "fusion_optimizations",
            sa.JSON(),
            nullable=True,
            comment="List of MILFusionOptimization",
        ),
        # Storage
        sa.Column("storage_uri", sa.String(500), nullable=True),
        # Verification
        sa.Column("verification", sa.JSON(), nullable=True),
        sa.Column("capsule_id", sa.String(64), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove Apple Silicon training provenance tables."""
    op.drop_table("compile_artifacts")
    op.drop_index("ix_kernel_executions_session_accelerator", table_name="kernel_executions")
    op.drop_index("ix_kernel_executions_session_step", table_name="kernel_executions")
    op.drop_table("kernel_executions")
    op.drop_table("ane_training_sessions")
    op.drop_table("hardware_profiles")
