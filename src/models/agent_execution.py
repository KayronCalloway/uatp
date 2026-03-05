"""
Agent Execution Traces - SQLAlchemy ORM models for UATP 7.4 Agent Execution Provenance.

Captures AI agent execution provenance including:
- Agent sessions with goals, context, and outcomes
- Tool calls with inputs, outputs, and timing
- Action traces for terminal, browser, and file operations
- Decision points with reasoning and alternatives
- Environment snapshots for system state
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import db


class AgentSessionStatus(str, Enum):
    """Status of an agent session."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ToolCallStatus(str, Enum):
    """Status of a tool call."""

    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class ToolCategory(str, Enum):
    """Categories of tools."""

    TERMINAL = "terminal"
    FILE = "file"
    BROWSER = "browser"
    API = "api"
    MCP = "mcp"
    CUSTOM = "custom"


class ActionType(str, Enum):
    """Types of actions traced."""

    TERMINAL = "terminal"
    BROWSER = "browser"
    FILE = "file"
    API = "api"


class AgentSessionModel(db.Base):
    """
    Agent session model for UATP 7.4 Agent Execution Provenance.

    Tracks complete agent sessions with goals, user context,
    tool calls, actions, decisions, and outcomes.
    """

    __tablename__ = "agent_sessions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)

    # Agent information
    agent_type = Column(String(50), nullable=False, index=True)  # openclaw, claude_code, custom
    agent_version = Column(String(50), nullable=True)
    scheduler_type = Column(String(50), nullable=True)  # heartbeat, on_demand, scheduled

    # Trigger context
    trigger_message = Column(Text, nullable=True)
    trigger_source = Column(String(50), nullable=True)  # whatsapp, telegram, cli, api
    user_id_hash = Column(String(64), nullable=True, index=True)  # Privacy-preserving

    # Goals
    goals = Column(JSON, nullable=True)  # List of goals

    # Session status
    status = Column(String(50), nullable=False, default="pending")  # AgentSessionStatus

    # Execution counts
    tool_call_count = Column(Integer, default=0)
    action_count = Column(Integer, default=0)
    decision_count = Column(Integer, default=0)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_duration_ms = Column(Integer, nullable=True)

    # Outcome
    outcome_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Verification and capsule link
    verification = Column(JSON, nullable=True)
    capsule_id = Column(String(64), nullable=True)

    # Ownership
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    owner = relationship("UserModel", foreign_keys=[owner_id])

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    tool_calls = relationship(
        "ToolCallModel",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    action_traces = relationship(
        "ActionTraceModel",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    decision_points = relationship(
        "DecisionPointModel",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    environment_snapshots = relationship(
        "EnvironmentSnapshotModel",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary representation."""
        return {
            "session_id": self.session_id,
            "agent_type": self.agent_type,
            "agent_version": self.agent_version,
            "scheduler_type": self.scheduler_type,
            "trigger_message": self.trigger_message,
            "trigger_source": self.trigger_source,
            "user_id_hash": self.user_id_hash,
            "goals": self.goals or [],
            "status": self.status,
            "tool_call_count": self.tool_call_count,
            "action_count": self.action_count,
            "decision_count": self.decision_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_duration_ms": self.total_duration_ms,
            "outcome_summary": self.outcome_summary,
            "error_message": self.error_message,
            "capsule_id": self.capsule_id,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def get_duration_seconds(self) -> Optional[float]:
        """Get session duration in seconds if completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def __repr__(self) -> str:
        return (
            f"<AgentSessionModel(session_id='{self.session_id}', "
            f"agent_type='{self.agent_type}', status='{self.status}')>"
        )


class ToolCallModel(db.Base):
    """
    Tool call model for individual tool invocations.

    Records tool calls with inputs, outputs, timing, and status.
    """

    __tablename__ = "tool_calls"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    call_id = Column(String(64), unique=True, nullable=False, index=True)

    # Session link
    session_id = Column(
        String(64),
        ForeignKey("agent_sessions.session_id"),
        nullable=False,
        index=True,
    )
    session = relationship("AgentSessionModel", back_populates="tool_calls")

    # Tool information
    tool_name = Column(String(100), nullable=False, index=True)  # Bash, Read, Edit, WebFetch
    tool_category = Column(String(50), nullable=False, index=True)  # ToolCategory

    # Input/Output
    tool_inputs = Column(JSON, nullable=True)
    tool_outputs = Column(JSON, nullable=True)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Status
    status = Column(String(50), nullable=False, default="pending")  # ToolCallStatus
    error_message = Column(Text, nullable=True)

    # Execution order
    step_index = Column(Integer, nullable=False, index=True)
    parent_call_id = Column(String(64), nullable=True, index=True)  # For nested calls

    # Verification and capsule link
    verification = Column(JSON, nullable=True)
    capsule_id = Column(String(64), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    action_traces = relationship(
        "ActionTraceModel",
        back_populates="tool_call",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool call to dictionary representation."""
        return {
            "call_id": self.call_id,
            "session_id": self.session_id,
            "tool_name": self.tool_name,
            "tool_category": self.tool_category,
            "tool_inputs": self.tool_inputs,
            "tool_outputs": self.tool_outputs,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error_message": self.error_message,
            "step_index": self.step_index,
            "parent_call_id": self.parent_call_id,
            "capsule_id": self.capsule_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<ToolCallModel(call_id='{self.call_id}', "
            f"tool='{self.tool_name}', status='{self.status}')>"
        )


class ActionTraceModel(db.Base):
    """
    Action trace model for terminal, browser, and file operations.

    Records detailed action execution with type-specific fields.
    """

    __tablename__ = "action_traces"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    action_id = Column(String(64), unique=True, nullable=False, index=True)

    # Session link
    session_id = Column(
        String(64),
        ForeignKey("agent_sessions.session_id"),
        nullable=False,
        index=True,
    )
    session = relationship("AgentSessionModel", back_populates="action_traces")

    # Tool call link (optional)
    tool_call_id = Column(
        String(64),
        ForeignKey("tool_calls.call_id"),
        nullable=True,
        index=True,
    )
    tool_call = relationship("ToolCallModel", back_populates="action_traces")

    # Action type
    action_type = Column(String(50), nullable=False, index=True)  # ActionType

    # Terminal actions
    command = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)
    stdout_hash = Column(String(64), nullable=True)  # SHA-256 for privacy
    stderr_hash = Column(String(64), nullable=True)

    # Browser actions
    url = Column(String(2000), nullable=True)
    selector = Column(String(500), nullable=True)
    browser_action = Column(String(50), nullable=True)  # navigate, click, type, screenshot

    # File actions
    file_path = Column(String(1000), nullable=True)
    file_operation = Column(String(50), nullable=True)  # read, write, edit, delete, glob, grep
    bytes_affected = Column(Integer, nullable=True)

    # Timing
    executed_at = Column(DateTime(timezone=True), nullable=False)
    duration_ms = Column(Integer, nullable=False)

    # Verification and capsule link
    verification = Column(JSON, nullable=True)
    capsule_id = Column(String(64), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert action trace to dictionary representation."""
        result = {
            "action_id": self.action_id,
            "session_id": self.session_id,
            "tool_call_id": self.tool_call_id,
            "action_type": self.action_type,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "duration_ms": self.duration_ms,
            "capsule_id": self.capsule_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        # Add type-specific fields
        if self.action_type == "terminal":
            result.update({
                "command": self.command,
                "exit_code": self.exit_code,
                "stdout_hash": self.stdout_hash,
                "stderr_hash": self.stderr_hash,
            })
        elif self.action_type == "browser":
            result.update({
                "url": self.url,
                "selector": self.selector,
                "browser_action": self.browser_action,
            })
        elif self.action_type == "file":
            result.update({
                "file_path": self.file_path,
                "file_operation": self.file_operation,
                "bytes_affected": self.bytes_affected,
            })

        return result

    def __repr__(self) -> str:
        return (
            f"<ActionTraceModel(action_id='{self.action_id}', "
            f"type='{self.action_type}', duration_ms={self.duration_ms})>"
        )


class DecisionPointModel(db.Base):
    """
    Decision point model for agent reasoning capture.

    Records agent decision-making with reasoning, alternatives, and confidence.
    """

    __tablename__ = "decision_points"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    decision_id = Column(String(64), unique=True, nullable=False, index=True)

    # Session link
    session_id = Column(
        String(64),
        ForeignKey("agent_sessions.session_id"),
        nullable=False,
        index=True,
    )
    session = relationship("AgentSessionModel", back_populates="decision_points")

    # Decision context
    step_index = Column(Integer, nullable=False, index=True)
    reasoning = Column(Text, nullable=False)
    alternatives_considered = Column(JSON, nullable=True)  # List of strings
    selected_action = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)  # 0.0-1.0
    context_summary = Column(Text, nullable=True)
    constraints_applied = Column(JSON, nullable=True)  # List of strings

    # Timing
    timestamp = Column(DateTime(timezone=True), nullable=False)

    # Verification and capsule link
    verification = Column(JSON, nullable=True)
    capsule_id = Column(String(64), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert decision point to dictionary representation."""
        return {
            "decision_id": self.decision_id,
            "session_id": self.session_id,
            "step_index": self.step_index,
            "reasoning": self.reasoning,
            "alternatives_considered": self.alternatives_considered or [],
            "selected_action": self.selected_action,
            "confidence": self.confidence,
            "context_summary": self.context_summary,
            "constraints_applied": self.constraints_applied or [],
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "capsule_id": self.capsule_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<DecisionPointModel(decision_id='{self.decision_id}', "
            f"step={self.step_index}, confidence={self.confidence})>"
        )


class EnvironmentSnapshotModel(db.Base):
    """
    Environment snapshot model for system state capture.

    Records environment state at decision points including git, files, and system resources.
    """

    __tablename__ = "environment_snapshots"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(String(64), unique=True, nullable=False, index=True)

    # Session link
    session_id = Column(
        String(64),
        ForeignKey("agent_sessions.session_id"),
        nullable=False,
        index=True,
    )
    session = relationship("AgentSessionModel", back_populates="environment_snapshots")

    # Environment state
    working_directory = Column(String(1000), nullable=False)
    env_vars_hash = Column(String(64), nullable=False)  # SHA-256 for privacy

    # Git state
    git_branch = Column(String(255), nullable=True)
    git_commit_hash = Column(String(64), nullable=True)
    git_dirty = Column(Boolean, nullable=True)

    # File tracking
    open_files = Column(JSON, nullable=True)  # List of file paths

    # System resources
    system_load = Column(Float, nullable=True)
    memory_available_gb = Column(Float, nullable=True)

    # Timing
    timestamp = Column(DateTime(timezone=True), nullable=False)

    # Verification and capsule link
    verification = Column(JSON, nullable=True)
    capsule_id = Column(String(64), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary representation."""
        return {
            "snapshot_id": self.snapshot_id,
            "session_id": self.session_id,
            "working_directory": self.working_directory,
            "env_vars_hash": self.env_vars_hash,
            "git_branch": self.git_branch,
            "git_commit_hash": self.git_commit_hash,
            "git_dirty": self.git_dirty,
            "open_files": self.open_files or [],
            "system_load": self.system_load,
            "memory_available_gb": self.memory_available_gb,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "capsule_id": self.capsule_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<EnvironmentSnapshotModel(snapshot_id='{self.snapshot_id}', "
            f"cwd='{self.working_directory}', git='{self.git_branch}')>"
        )
