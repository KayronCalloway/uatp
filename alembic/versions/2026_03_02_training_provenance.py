"""
Training Provenance Schema Migration (UATP 7.2)
================================================

Adds model_registry and training_sessions tables for tracking AI model lineage
from base model through fine-tuning to deployment.

Revision ID: 2026_03_02_training_provenance
Revises: 2026_02_27_user_capsule_isolation
Create Date: 2026-03-02
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_03_02_training_provenance"
down_revision = "2026_02_27_user_capsule_isolation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add tables for UATP 7.2 Training Provenance:
    - model_registry: Tracks registered AI models with lineage
    - training_sessions: Records fine-tuning and adaptation sessions
    """
    # Create model_registry table
    op.create_table(
        "model_registry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_id", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("model_hash", sa.String(64), nullable=False),
        sa.Column("base_model_id", sa.String(64), nullable=True),
        sa.Column(
            "model_type",
            sa.String(50),
            nullable=False,
            comment="Type: base, fine_tune, adapter, merged",
        ),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "training_config",
            sa.JSON(),
            nullable=True,
            comment="Training hyperparameters and configuration",
        ),
        sa.Column(
            "dataset_provenance",
            sa.JSON(),
            nullable=True,
            comment="Dataset references and attribution",
        ),
        sa.Column(
            "license_info",
            sa.JSON(),
            nullable=True,
            comment="License type, permissions, restrictions",
        ),
        sa.Column(
            "attestation",
            sa.JSON(),
            nullable=True,
            comment="Hardware attestation if available",
        ),
        sa.Column(
            "capabilities",
            sa.JSON(),
            nullable=True,
            comment="Declared model capabilities",
        ),
        sa.Column(
            "safety_evaluations",
            sa.JSON(),
            nullable=True,
            comment="Safety benchmark results",
        ),
        sa.Column(
            "owner_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Create index for base_model_id lookups (lineage queries)
    op.create_index(
        "ix_model_registry_base_model_id", "model_registry", ["base_model_id"]
    )

    # Create training_sessions table
    op.create_table(
        "training_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id", sa.String(64), unique=True, nullable=False, index=True
        ),
        sa.Column(
            "model_id",
            sa.String(64),
            sa.ForeignKey("model_registry.model_id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "session_type",
            sa.String(50),
            nullable=False,
            comment="Type: pre_training, fine_tuning, rlhf, dpo, sft, adapter",
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            default="pending",
            comment="Status: pending, running, completed, failed, cancelled",
        ),
        sa.Column(
            "dataset_refs",
            sa.JSON(),
            nullable=False,
            comment="References to training datasets with provenance",
        ),
        sa.Column(
            "hyperparameters",
            sa.JSON(),
            nullable=True,
            comment="Training hyperparameters",
        ),
        sa.Column(
            "compute_resources",
            sa.JSON(),
            nullable=True,
            comment="GPU/TPU configuration used",
        ),
        sa.Column(
            "metrics",
            sa.JSON(),
            nullable=True,
            comment="Training metrics and evaluation results",
        ),
        sa.Column(
            "checkpoints",
            sa.JSON(),
            nullable=True,
            comment="References to saved checkpoints",
        ),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=False, index=True
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "verification",
            sa.JSON(),
            nullable=True,
            comment="Cryptographic verification of session",
        ),
        sa.Column(
            "capsule_id",
            sa.String(64),
            nullable=True,
            comment="Associated UATP capsule ID",
        ),
        sa.Column(
            "owner_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove training provenance tables."""
    op.drop_table("training_sessions")
    op.drop_index("ix_model_registry_base_model_id", table_name="model_registry")
    op.drop_table("model_registry")
