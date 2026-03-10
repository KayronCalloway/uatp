"""Add SQLite trigger for auto-generating capsule IDs.

Revision ID: 2026_03_05_auto_id
Revises: 
Create Date: 2026-03-05

The capsules table was created with 'id SERIAL PRIMARY KEY' which is
PostgreSQL syntax. SQLite doesn't recognize SERIAL and won't auto-increment.
This trigger fixes the issue by auto-generating IDs for rows with NULL id.
"""
from alembic import op
from sqlalchemy import text

revision = "2026_03_05_auto_id"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Only create trigger for SQLite
    connection = op.get_bind()
    if connection.dialect.name == "sqlite":
        connection.execute(text("""
            CREATE TRIGGER IF NOT EXISTS capsules_auto_id
            AFTER INSERT ON capsules
            WHEN NEW.id IS NULL
            BEGIN
                UPDATE capsules
                SET id = (SELECT COALESCE(MAX(id), 0) + 1 FROM capsules WHERE id IS NOT NULL)
                WHERE rowid = NEW.rowid;
            END
        """))


def downgrade() -> None:
    connection = op.get_bind()
    if connection.dialect.name == "sqlite":
        connection.execute(text("DROP TRIGGER IF EXISTS capsules_auto_id"))
