"""Create insurance tables for policies, claims, and event logs

Revision ID: 202510061545
Revises: 0eb20474e8c4
Create Date: 2025-10-06 18:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "202510061545"
down_revision: Union[str, None] = "0eb20474e8c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create insurance tables"""

    # Create insurance_policies table
    op.create_table(
        "insurance_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_number", sa.String(), nullable=False),
        sa.Column("premium_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("coverage_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("policy_type", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "EXPIRED", "PAID_OUT", "CANCELLED", name="policystatus"),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for insurance_policies
    op.create_index(
        "ix_insurance_policies_policy_number",
        "insurance_policies",
        ["policy_number"],
        unique=True,
    )
    op.create_index(
        "ix_insurance_policies_user_id", "insurance_policies", ["user_id"], unique=False
    )
    op.create_index(
        "ix_insurance_policies_status", "insurance_policies", ["status"], unique=False
    )
    op.create_index(
        "ix_insurance_policies_created_at",
        "insurance_policies",
        ["created_at"],
        unique=False,
    )

    # Create insurance_claims table
    op.create_table(
        "insurance_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "claim_status",
            sa.Enum("PENDING", "APPROVED", "REJECTED", "PAID", name="claimstatus"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("payout_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capsule_id", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["policy_id"], ["insurance_policies.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for insurance_claims
    op.create_index(
        "ix_insurance_claims_policy_id", "insurance_claims", ["policy_id"], unique=False
    )
    op.create_index(
        "ix_insurance_claims_capsule_id",
        "insurance_claims",
        ["capsule_id"],
        unique=False,
    )
    op.create_index(
        "ix_insurance_claims_claim_status",
        "insurance_claims",
        ["claim_status"],
        unique=False,
    )
    op.create_index(
        "ix_insurance_claims_created_at",
        "insurance_claims",
        ["created_at"],
        unique=False,
    )

    # Create ai_liability_event_logs table
    op.create_table(
        "ai_liability_event_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_entity_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["claim_id"], ["insurance_claims.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for ai_liability_event_logs
    op.create_index(
        "ix_ai_liability_event_logs_claim_id",
        "ai_liability_event_logs",
        ["claim_id"],
        unique=False,
    )
    op.create_index(
        "ix_ai_liability_event_logs_source_entity_id",
        "ai_liability_event_logs",
        ["source_entity_id"],
        unique=False,
    )
    op.create_index(
        "ix_ai_liability_event_logs_event_timestamp",
        "ai_liability_event_logs",
        ["event_timestamp"],
        unique=False,
    )


def downgrade() -> None:
    """Drop insurance tables"""

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_index(
        "ix_ai_liability_event_logs_event_timestamp",
        table_name="ai_liability_event_logs",
    )
    op.drop_index(
        "ix_ai_liability_event_logs_source_entity_id",
        table_name="ai_liability_event_logs",
    )
    op.drop_index(
        "ix_ai_liability_event_logs_claim_id", table_name="ai_liability_event_logs"
    )
    op.drop_table("ai_liability_event_logs")

    op.drop_index("ix_insurance_claims_created_at", table_name="insurance_claims")
    op.drop_index("ix_insurance_claims_claim_status", table_name="insurance_claims")
    op.drop_index("ix_insurance_claims_capsule_id", table_name="insurance_claims")
    op.drop_index("ix_insurance_claims_policy_id", table_name="insurance_claims")
    op.drop_table("insurance_claims")

    op.drop_index("ix_insurance_policies_created_at", table_name="insurance_policies")
    op.drop_index("ix_insurance_policies_status", table_name="insurance_policies")
    op.drop_index("ix_insurance_policies_user_id", table_name="insurance_policies")
    op.drop_index(
        "ix_insurance_policies_policy_number", table_name="insurance_policies"
    )
    op.drop_table("insurance_policies")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS claimstatus")
    op.execute("DROP TYPE IF EXISTS policystatus")
