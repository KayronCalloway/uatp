"""
Model Artifacts and Licenses Migration (UATP 7.2 Phase 5)
=========================================================

Adds model_artifacts and model_licenses tables for content-addressed
model storage with license verification.

Revision ID: 2026_03_02_model_artifacts
Revises: 2026_03_02_workflow_chains
Create Date: 2026-03-02
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_03_02_model_artifacts"
down_revision = "2026_03_02_workflow_chains"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add tables for UATP 7.2 Model Registry Protocol:
    - model_artifacts: Content-addressed model file storage
    - model_licenses: License information and compliance
    """
    # Create model_artifacts table
    op.create_table(
        "model_artifacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "artifact_id",
            sa.String(64),
            unique=True,
            nullable=False,
            index=True,
            comment="Unique artifact identifier",
        ),
        sa.Column(
            "model_id",
            sa.String(64),
            sa.ForeignKey("model_registry.model_id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "artifact_type",
            sa.String(50),
            nullable=False,
            comment="Type: weights, config, tokenizer, adapter, checkpoint, merged",
        ),
        sa.Column(
            "content_hash",
            sa.String(64),
            nullable=False,
            index=True,
            comment="SHA-256 hash of content for content-addressing",
        ),
        sa.Column(
            "size_bytes",
            sa.BigInteger(),
            nullable=False,
            comment="Size of artifact in bytes",
        ),
        sa.Column(
            "storage_uri",
            sa.String(512),
            nullable=False,
            comment="URI to artifact storage location (S3, GCS, etc.)",
        ),
        sa.Column(
            "storage_backend",
            sa.String(50),
            nullable=True,
            default="local",
            comment="Backend type: local, s3, gcs, azure, ipfs",
        ),
        sa.Column(
            "encryption_key_id",
            sa.String(64),
            nullable=True,
            comment="Key ID if artifact is encrypted",
        ),
        sa.Column(
            "format",
            sa.String(50),
            nullable=True,
            comment="File format: safetensors, pytorch, gguf, onnx",
        ),
        sa.Column(
            "compression",
            sa.String(50),
            nullable=True,
            comment="Compression: none, gzip, zstd, lz4",
        ),
        sa.Column(
            "artifact_metadata",
            sa.JSON(),
            nullable=True,
            comment="Additional artifact metadata",
        ),
        sa.Column(
            "verification",
            sa.JSON(),
            nullable=True,
            comment="Cryptographic verification data",
        ),
        sa.Column(
            "upload_status",
            sa.String(50),
            nullable=False,
            default="pending",
            comment="Status: pending, uploading, completed, failed, deleted",
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

    # Create unique constraint on model_id + artifact_type (one of each type per model)
    # Actually, allow multiple - e.g., multiple checkpoints
    # Instead, create index for common queries
    op.create_index(
        "ix_model_artifacts_model_type",
        "model_artifacts",
        ["model_id", "artifact_type"],
    )

    # Create model_licenses table
    op.create_table(
        "model_licenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "license_id",
            sa.String(64),
            unique=True,
            nullable=False,
            index=True,
            comment="Unique license identifier",
        ),
        sa.Column(
            "model_id",
            sa.String(64),
            sa.ForeignKey("model_registry.model_id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "license_type",
            sa.String(100),
            nullable=False,
            comment="License type: MIT, Apache-2.0, CC-BY-4.0, proprietary, custom",
        ),
        sa.Column(
            "license_name",
            sa.String(255),
            nullable=True,
            comment="Human-readable license name",
        ),
        sa.Column(
            "license_url",
            sa.String(512),
            nullable=True,
            comment="URL to full license text",
        ),
        sa.Column(
            "license_text",
            sa.Text(),
            nullable=True,
            comment="Full license text if custom",
        ),
        sa.Column(
            "permissions",
            sa.JSON(),
            nullable=False,
            comment="Allowed uses: commercial, derivative, distribution, etc.",
        ),
        sa.Column(
            "restrictions",
            sa.JSON(),
            nullable=False,
            comment="Restrictions: no_medical, attribution_required, etc.",
        ),
        sa.Column(
            "conditions",
            sa.JSON(),
            nullable=True,
            comment="Conditions: include_license, state_changes, etc.",
        ),
        sa.Column(
            "attribution_requirements",
            sa.JSON(),
            nullable=True,
            comment="Required attribution format and information",
        ),
        sa.Column(
            "usage_limitations",
            sa.JSON(),
            nullable=True,
            comment="Specific usage limitations: max_users, no_compete, etc.",
        ),
        sa.Column(
            "effective_date",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="When license becomes effective",
        ),
        sa.Column(
            "expiration_date",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When license expires (null = perpetual)",
        ),
        sa.Column(
            "supersedes_license_id",
            sa.String(64),
            nullable=True,
            comment="Previous license ID this replaces",
        ),
        sa.Column(
            "verification",
            sa.JSON(),
            nullable=True,
            comment="Cryptographic signature of license",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            default=True,
            comment="Whether this license is currently active",
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

    # Create index for active licenses lookup
    op.create_index(
        "ix_model_licenses_active",
        "model_licenses",
        ["model_id", "is_active"],
    )


def downgrade() -> None:
    """Remove model artifacts and licenses tables."""
    op.drop_index("ix_model_licenses_active", table_name="model_licenses")
    op.drop_table("model_licenses")
    op.drop_index("ix_model_artifacts_model_type", table_name="model_artifacts")
    op.drop_table("model_artifacts")
