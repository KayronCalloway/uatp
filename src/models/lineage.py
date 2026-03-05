"""
LineageEdgeModel - SQLAlchemy ORM model for capsule lineage relationships.

UATP 7.2: Persists the capsule lineage DAG edges to the database for
durable lineage tracking and querying across restarts.

Design Decision:
    This model stores parent→child directed edges in the lineage graph.
    The in-memory graph (Constellations module) is the primary query interface,
    but edges are persisted here for durability and recovery.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

from src.core.database import db

if TYPE_CHECKING:
    pass


class LineageEdgeModel(db.Base):
    """
    Persisted lineage relationship between capsules.

    Each row represents a directed edge: parent_capsule_id → child_capsule_id
    with optional metadata about the relationship.
    """

    __tablename__ = "lineage_edges"
    __table_args__ = (
        UniqueConstraint(
            "parent_capsule_id", "child_capsule_id", name="uq_lineage_edge"
        ),
        Index("ix_lineage_parent", "parent_capsule_id"),
        Index("ix_lineage_child", "child_capsule_id"),
        Index("ix_lineage_created", "created_at"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True)

    # Edge endpoints
    parent_capsule_id = Column(String(64), nullable=False)
    child_capsule_id = Column(String(64), nullable=False)

    # Relationship metadata
    relationship_type = Column(
        String(50),
        default="derived_from",
        nullable=False,
        comment="Type: derived_from, fork, remix, merge, inspiration, etc.",
    )

    # Attribution weight for this edge (0.0 to 1.0)
    attribution_weight = Column(
        String(10),  # Store as string to avoid float precision issues
        default="1.0",
        nullable=False,
        comment="Attribution weight for temporal justice calculations",
    )

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<LineageEdge("
            f"{self.parent_capsule_id} → {self.child_capsule_id}, "
            f"type='{self.relationship_type}')>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "parent_capsule_id": self.parent_capsule_id,
            "child_capsule_id": self.child_capsule_id,
            "relationship_type": self.relationship_type,
            "attribution_weight": float(self.attribution_weight),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
