"""
WorkflowCapsule - SQLAlchemy ORM model for UATP 7.2 Agentic Workflow Chains.

Represents a parent workflow container that links multiple step capsules
together with DAG-based dependency tracking and aggregated attribution.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import db


class WorkflowType(str, Enum):
    """Types of workflow structures."""

    LINEAR = "linear"
    BRANCHING = "branching"
    ITERATIVE = "iterative"
    PARALLEL = "parallel"


class WorkflowStatus(str, Enum):
    """Status of a workflow."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(str, Enum):
    """Types of workflow steps."""

    PLAN = "plan"
    TOOL_CALL = "tool_call"
    INFERENCE = "inference"
    OUTPUT = "output"
    HUMAN_INPUT = "human_input"
    VERIFICATION = "verification"
    DECISION = "decision"
    AGGREGATION = "aggregation"


class WorkflowCapsuleModel(db.Base):
    """
    Workflow capsule model for UATP 7.2 Agentic Workflow Chains.

    Serves as a container for multi-step agent workflows, tracking:
    - Step ordering and dependencies (DAG)
    - Aggregated attribution across steps
    - Workflow completion status
    """

    __tablename__ = "workflow_capsules"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    workflow_capsule_id = Column(String(64), unique=True, nullable=False, index=True)
    workflow_name = Column(String(255), nullable=False)
    workflow_type = Column(String(50), nullable=False)  # WorkflowType values
    status = Column(String(50), nullable=False, default="active")  # WorkflowStatus

    # Ownership
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    owner = relationship("UserModel", foreign_keys=[owner_id])

    # Workflow data (JSON fields)
    aggregated_attribution = Column(JSON, nullable=True)
    dag_definition = Column(JSON, nullable=True)
    final_output = Column(JSON, nullable=True)

    # Tracking
    step_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Verification
    verification = Column(JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary representation."""
        return {
            "workflow_capsule_id": self.workflow_capsule_id,
            "workflow_name": self.workflow_name,
            "workflow_type": self.workflow_type,
            "status": self.status,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "aggregated_attribution": self.aggregated_attribution,
            "dag_definition": self.dag_definition,
            "final_output": self.final_output,
            "step_count": self.step_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "verification": self.verification,
        }

    def get_duration_seconds(self) -> Optional[float]:
        """Get workflow duration in seconds if completed."""
        if self.created_at and self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None

    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.status in (
            WorkflowStatus.COMPLETED.value,
            WorkflowStatus.FAILED.value,
        )

    def __repr__(self) -> str:
        return (
            f"<WorkflowCapsuleModel(workflow_capsule_id='{self.workflow_capsule_id}', "
            f"name='{self.workflow_name}', status='{self.status}', "
            f"steps={self.step_count})>"
        )
