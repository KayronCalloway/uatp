"""
Agentic Workflow Chains Migration (UATP 7.2)
=============================================

Adds workflow_capsules table and workflow linking columns to capsules table
for supporting multi-step agentic workflows with DAG-based lineage.

Revision ID: 2026_03_02_workflow_chains
Revises: 2026_03_02_training_provenance
Create Date: 2026-03-02
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_03_02_workflow_chains"
down_revision = "2026_03_02_training_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add tables and columns for UATP 7.2 Agentic Workflow Chains:
    - workflow_capsules: Parent workflow container
    - Capsule columns: workflow_capsule_id, step_index, step_type, depends_on_steps
    """
    # Create workflow_capsules table
    op.create_table(
        "workflow_capsules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "workflow_capsule_id",
            sa.String(64),
            unique=True,
            nullable=False,
            index=True,
        ),
        sa.Column("workflow_name", sa.String(255), nullable=False),
        sa.Column(
            "workflow_type",
            sa.String(50),
            nullable=False,
            comment="Type: linear, branching, iterative, parallel",
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            default="active",
            comment="Status: active, completed, failed, cancelled",
        ),
        sa.Column(
            "owner_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "aggregated_attribution",
            sa.JSON(),
            nullable=True,
            comment="Combined attribution from all workflow steps",
        ),
        sa.Column(
            "dag_definition",
            sa.JSON(),
            nullable=True,
            comment="DAG structure defining step dependencies",
        ),
        sa.Column(
            "final_output",
            sa.JSON(),
            nullable=True,
            comment="Final workflow output",
        ),
        sa.Column("step_count", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "verification",
            sa.JSON(),
            nullable=True,
            comment="Cryptographic verification when sealed",
        ),
    )

    # Add workflow linking columns to capsules table
    op.add_column(
        "capsules",
        sa.Column(
            "workflow_capsule_id",
            sa.String(64),
            nullable=True,
            comment="Parent workflow this capsule belongs to",
        ),
    )

    op.add_column(
        "capsules",
        sa.Column(
            "step_index",
            sa.Integer(),
            nullable=True,
            comment="Position in workflow (0-indexed)",
        ),
    )

    op.add_column(
        "capsules",
        sa.Column(
            "step_type",
            sa.String(50),
            nullable=True,
            comment="Type: plan, tool_call, inference, output, human_input, verification",
        ),
    )

    op.add_column(
        "capsules",
        sa.Column(
            "depends_on_steps",
            sa.JSON(),
            nullable=True,
            comment="List of step indices this step depends on",
        ),
    )

    # Create index for efficient workflow queries
    op.create_index(
        "ix_capsules_workflow_capsule_id", "capsules", ["workflow_capsule_id"]
    )

    # Create composite index for workflow step ordering
    op.create_index(
        "ix_capsules_workflow_step",
        "capsules",
        ["workflow_capsule_id", "step_index"],
    )


def downgrade() -> None:
    """Remove workflow chain columns and tables."""
    # Drop indexes
    op.drop_index("ix_capsules_workflow_step", table_name="capsules")
    op.drop_index("ix_capsules_workflow_capsule_id", table_name="capsules")

    # Drop columns from capsules
    op.drop_column("capsules", "depends_on_steps")
    op.drop_column("capsules", "step_type")
    op.drop_column("capsules", "step_index")
    op.drop_column("capsules", "workflow_capsule_id")

    # Drop workflow_capsules table
    op.drop_table("workflow_capsules")
