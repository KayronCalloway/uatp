"""
User-Scoped Capsule Isolation Migration
======================================

Adds owner_id and encrypted_payload columns for privacy-first capsule isolation.

Revision ID: 2026_02_27_user_capsule_isolation
Revises: (previous revision)
Create Date: 2026-02-27
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_02_27_user_capsule_isolation"
down_revision = None  # Update this to your latest revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add columns for user-scoped capsule isolation:
    - owner_id: Links capsule to owning user (NULL = legacy/system capsule)
    - encrypted_payload: Client-side encrypted payload (Base64 ciphertext)
    - encryption_metadata: Encryption details {iv, algorithm, key_id}
    """
    # Add owner_id column with foreign key to users table
    op.add_column(
        "capsules",
        sa.Column(
            "owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
    )

    # Create index for efficient owner-based queries
    op.create_index("ix_capsules_owner_id", "capsules", ["owner_id"])

    # Add encrypted payload column (Text for large Base64 ciphertext)
    op.add_column("capsules", sa.Column("encrypted_payload", sa.Text(), nullable=True))

    # Add encryption metadata column (JSON for {iv, algorithm, key_id})
    op.add_column(
        "capsules", sa.Column("encryption_metadata", sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    """Remove user-scoped isolation columns."""
    op.drop_index("ix_capsules_owner_id", table_name="capsules")
    op.drop_column("capsules", "owner_id")
    op.drop_column("capsules", "encrypted_payload")
    op.drop_column("capsules", "encryption_metadata")
