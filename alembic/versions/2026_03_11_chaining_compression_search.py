"""
Features Migration
================================

Adds columns for:
- Cryptographic capsule chaining (prev_hash, content_hash)
- Compression support (is_compressed, compression_method, original_size, compressed_size)
- FTS5 full-text search (virtual table for SQLite)

Revision ID: 2026_03_11_chaining_compression_search
Revises: 2026_03_05_lineage_and_chains
Create Date: 2026-03-11
"""

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_03_11_chaining_compression_search"
down_revision = "2026_03_05_lineage_and_chains"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add columns for new features:
    - Cryptographic chaining: prev_hash, content_hash
    - Compression: is_compressed, compression_method, original_size, compressed_size
    - FTS5 virtual table for full-text search (SQLite only)
    """
    # --- Cryptographic Chaining Columns ---
    op.add_column(
        "capsules",
        sa.Column("prev_hash", sa.String(64), nullable=True),
    )
    op.add_column(
        "capsules",
        sa.Column("content_hash", sa.String(64), nullable=True),
    )
    op.create_index("ix_capsules_prev_hash", "capsules", ["prev_hash"])
    op.create_index("ix_capsules_content_hash", "capsules", ["content_hash"])

    # --- Compression Columns ---
    op.add_column(
        "capsules",
        sa.Column("is_compressed", sa.Boolean(), nullable=True, server_default="0"),
    )
    op.add_column(
        "capsules",
        sa.Column("compression_method", sa.String(20), nullable=True),
    )
    op.add_column(
        "capsules",
        sa.Column("original_size", sa.Integer(), nullable=True),
    )
    op.add_column(
        "capsules",
        sa.Column("compressed_size", sa.Integer(), nullable=True),
    )

    # --- SQLite FTS5 Virtual Table ---
    # Only create for SQLite; PostgreSQL uses ts_vector natively
    connection = op.get_bind()
    if connection.dialect.name == "sqlite":
        # Create standalone FTS5 virtual table (not content-synced)
        # This avoids schema mismatches with the capsules table
        connection.execute(
            text(
                """
            CREATE VIRTUAL TABLE IF NOT EXISTS capsules_fts USING fts5(
                capsule_id,
                payload_text
            )
            """
            )
        )

        # Backfill existing capsules into FTS index
        connection.execute(
            text(
                """
            INSERT INTO capsules_fts(capsule_id, payload_text)
            SELECT
                capsule_id,
                COALESCE(
                    json_extract(payload, '$.content.data.reasoning_steps[0].content'),
                    json_extract(payload, '$.reasoning_steps[0].reasoning'),
                    json_extract(payload, '$.session_metadata.topics'),
                    CAST(payload AS TEXT)
                )
            FROM capsules
            WHERE id IS NOT NULL
            """
            )
        )

        # Create triggers to keep FTS in sync with capsules table
        # INSERT trigger
        connection.execute(
            text(
                """
            CREATE TRIGGER IF NOT EXISTS capsules_fts_insert AFTER INSERT ON capsules BEGIN
                INSERT INTO capsules_fts(capsule_id, payload_text)
                VALUES (
                    NEW.capsule_id,
                    COALESCE(
                        json_extract(NEW.payload, '$.content.data.reasoning_steps[0].content'),
                        json_extract(NEW.payload, '$.reasoning_steps[0].reasoning'),
                        json_extract(NEW.payload, '$.session_metadata.topics'),
                        CAST(NEW.payload AS TEXT)
                    )
                );
            END
            """
            )
        )

        # DELETE trigger
        connection.execute(
            text(
                """
            CREATE TRIGGER IF NOT EXISTS capsules_fts_delete AFTER DELETE ON capsules BEGIN
                DELETE FROM capsules_fts WHERE capsule_id = OLD.capsule_id;
            END
            """
            )
        )

        # UPDATE trigger
        connection.execute(
            text(
                """
            CREATE TRIGGER IF NOT EXISTS capsules_fts_update AFTER UPDATE ON capsules BEGIN
                DELETE FROM capsules_fts WHERE capsule_id = OLD.capsule_id;
                INSERT INTO capsules_fts(capsule_id, payload_text)
                VALUES (
                    NEW.capsule_id,
                    COALESCE(
                        json_extract(NEW.payload, '$.content.data.reasoning_steps[0].content'),
                        json_extract(NEW.payload, '$.reasoning_steps[0].reasoning'),
                        json_extract(NEW.payload, '$.session_metadata.topics'),
                        CAST(NEW.payload AS TEXT)
                    )
                );
            END
            """
            )
        )


def downgrade() -> None:
    """Remove feature columns and FTS table."""
    connection = op.get_bind()

    # Drop FTS triggers and table for SQLite
    if connection.dialect.name == "sqlite":
        connection.execute(text("DROP TRIGGER IF EXISTS capsules_fts_insert"))
        connection.execute(text("DROP TRIGGER IF EXISTS capsules_fts_delete"))
        connection.execute(text("DROP TRIGGER IF EXISTS capsules_fts_update"))
        connection.execute(text("DROP TABLE IF EXISTS capsules_fts"))

    # Drop compression columns
    op.drop_column("capsules", "compressed_size")
    op.drop_column("capsules", "original_size")
    op.drop_column("capsules", "compression_method")
    op.drop_column("capsules", "is_compressed")

    # Drop chaining columns
    op.drop_index("ix_capsules_content_hash", table_name="capsules")
    op.drop_index("ix_capsules_prev_hash", table_name="capsules")
    op.drop_column("capsules", "content_hash")
    op.drop_column("capsules", "prev_hash")
