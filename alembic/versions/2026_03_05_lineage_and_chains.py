"""
Lineage and Chain Sealing Tables Migration (UATP 7.2)
======================================================

Adds tables for persisting lineage edges and chain seals:
- lineage_edges: Directed parent→child relationships in the capsule DAG
- chain_seals: Cryptographic seals providing legal admissibility

Revision ID: 2026_03_05_lineage_and_chains
Revises: 2026_03_03_agent_execution_traces
Create Date: 2026-03-05
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_03_05_lineage_and_chains"
down_revision = "2026_03_03_agent_execution_traces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add tables for UATP 7.2 Lineage and Chain Sealing:
    - lineage_edges: Parent→child capsule relationships
    - chain_seals: Cryptographic chain finality seals
    """
    # Create lineage_edges table
    op.create_table(
        "lineage_edges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "parent_capsule_id",
            sa.String(64),
            nullable=False,
            comment="Source capsule ID (parent)",
        ),
        sa.Column(
            "child_capsule_id",
            sa.String(64),
            nullable=False,
            comment="Target capsule ID (child)",
        ),
        sa.Column(
            "relationship_type",
            sa.String(50),
            nullable=False,
            default="derived_from",
            comment="Type: derived_from, fork, remix, merge, inspiration",
        ),
        sa.Column(
            "attribution_weight",
            sa.String(10),
            nullable=False,
            default="1.0",
            comment="Attribution weight for temporal justice (0.0-1.0)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # Unique constraint on edge
        sa.UniqueConstraint(
            "parent_capsule_id", "child_capsule_id", name="uq_lineage_edge"
        ),
    )

    # Create indexes for efficient lineage traversal
    op.create_index("ix_lineage_parent", "lineage_edges", ["parent_capsule_id"])
    op.create_index("ix_lineage_child", "lineage_edges", ["child_capsule_id"])
    op.create_index("ix_lineage_created", "lineage_edges", ["created_at"])

    # Create chain_seals table
    op.create_table(
        "chain_seals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "seal_id",
            sa.String(64),
            unique=True,
            nullable=False,
            comment="Unique seal identifier",
        ),
        sa.Column(
            "chain_id",
            sa.String(64),
            nullable=False,
            comment="Chain being sealed",
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Seal creation time",
        ),
        sa.Column(
            "signer_id",
            sa.String(128),
            nullable=False,
            comment="Entity that created the seal",
        ),
        sa.Column(
            "chain_state_hash",
            sa.String(64),
            nullable=False,
            comment="SHA-256 hash of chain state",
        ),
        sa.Column(
            "signature",
            sa.Text(),
            nullable=False,
            comment="Base64-encoded Ed25519 signature",
        ),
        sa.Column(
            "verify_key",
            sa.String(128),
            nullable=False,
            comment="Hex-encoded verification key",
        ),
        sa.Column(
            "note",
            sa.String(500),
            nullable=True,
            comment="Optional seal note",
        ),
        sa.Column(
            "capsule_count",
            sa.Integer(),
            nullable=False,
            default=0,
            comment="Capsules in chain at seal time",
        ),
        sa.Column(
            "capsule_ids",
            sa.Text(),
            nullable=True,
            comment="JSON list of capsule IDs",
        ),
    )

    # Create indexes for chain seal queries
    op.create_index("ix_chain_seal_id", "chain_seals", ["seal_id"])
    op.create_index("ix_chain_seal_chain_id", "chain_seals", ["chain_id"])
    op.create_index("ix_chain_seal_timestamp", "chain_seals", ["timestamp"])
    op.create_index("ix_chain_seal_signer", "chain_seals", ["signer_id"])


def downgrade() -> None:
    """Remove lineage and chain seal tables."""
    # Drop indexes
    op.drop_index("ix_chain_seal_signer", table_name="chain_seals")
    op.drop_index("ix_chain_seal_timestamp", table_name="chain_seals")
    op.drop_index("ix_chain_seal_chain_id", table_name="chain_seals")
    op.drop_index("ix_chain_seal_id", table_name="chain_seals")

    op.drop_index("ix_lineage_created", table_name="lineage_edges")
    op.drop_index("ix_lineage_child", table_name="lineage_edges")
    op.drop_index("ix_lineage_parent", table_name="lineage_edges")

    # Drop tables
    op.drop_table("chain_seals")
    op.drop_table("lineage_edges")
