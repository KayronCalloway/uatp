"""
Agent Execution Traces Schema Migration (UATP 7.4)
==================================================

Adds tables for tracking AI agent execution provenance:
- agent_sessions: Complete agent sessions with goals, context, outcomes
- tool_calls: Individual tool invocations with inputs, outputs, timing
- action_traces: Terminal, browser, and file operation traces
- decision_points: Agent reasoning and action selection
- environment_snapshots: System state at decision points

Revision ID: 2026_03_03_agent_execution_traces
Revises: 2026_03_03_ane_training_provenance
Create Date: 2026-03-03
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_03_03_agent_execution_traces"
down_revision = "2026_03_03_ane_training_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add tables for UATP 7.4 Agent Execution Traces:
    - agent_sessions: Complete agent sessions
    - tool_calls: Tool invocation tracking
    - action_traces: Terminal/browser/file actions
    - decision_points: Agent reasoning
    - environment_snapshots: System state
    """
    # Create agent_sessions table
    op.create_table(
        "agent_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.String(64), unique=True, nullable=False, index=True),
        # Agent information
        sa.Column(
            "agent_type",
            sa.String(50),
            nullable=False,
            index=True,
            comment="Agent type: openclaw, claude_code, custom",
        ),
        sa.Column("agent_version", sa.String(50), nullable=True),
        sa.Column(
            "scheduler_type",
            sa.String(50),
            nullable=True,
            comment="Scheduler: heartbeat, on_demand, scheduled",
        ),
        # Trigger context
        sa.Column(
            "trigger_message",
            sa.Text(),
            nullable=True,
            comment="Message that initiated the session",
        ),
        sa.Column(
            "trigger_source",
            sa.String(50),
            nullable=True,
            comment="Source: whatsapp, telegram, cli, api",
        ),
        sa.Column(
            "user_id_hash",
            sa.String(64),
            nullable=True,
            index=True,
            comment="Privacy-preserving user ID hash",
        ),
        # Goals
        sa.Column(
            "goals",
            sa.JSON(),
            nullable=True,
            comment="List of goals the agent is trying to achieve",
        ),
        # Session status
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            default="pending",
            comment="Status: pending, running, completed, failed, cancelled",
        ),
        # Execution counts
        sa.Column("tool_call_count", sa.Integer(), default=0),
        sa.Column("action_count", sa.Integer(), default=0),
        sa.Column("decision_count", sa.Integer(), default=0),
        # Timing
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "total_duration_ms",
            sa.Integer(),
            nullable=True,
            comment="Total session duration in milliseconds",
        ),
        # Outcome
        sa.Column("outcome_summary", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Verification
        sa.Column("verification", sa.JSON(), nullable=True),
        sa.Column("capsule_id", sa.String(64), nullable=True),
        # Ownership
        sa.Column(
            "owner_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
            index=True,
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create tool_calls table
    op.create_table(
        "tool_calls",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("call_id", sa.String(64), unique=True, nullable=False, index=True),
        # Session link
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("agent_sessions.session_id"),
            nullable=False,
            index=True,
        ),
        # Tool information
        sa.Column(
            "tool_name",
            sa.String(100),
            nullable=False,
            index=True,
            comment="Tool name: Bash, Read, Edit, WebFetch, etc.",
        ),
        sa.Column(
            "tool_category",
            sa.String(50),
            nullable=False,
            index=True,
            comment="Category: terminal, file, browser, api, mcp, custom",
        ),
        # Input/Output
        sa.Column("tool_inputs", sa.JSON(), nullable=True),
        sa.Column("tool_outputs", sa.JSON(), nullable=True),
        # Timing
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "duration_ms",
            sa.Integer(),
            nullable=True,
            comment="Duration in milliseconds",
        ),
        # Status
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            default="pending",
            comment="Status: pending, success, error, timeout",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Execution order
        sa.Column(
            "step_index",
            sa.Integer(),
            nullable=False,
            index=True,
            comment="Order within session",
        ),
        sa.Column(
            "parent_call_id",
            sa.String(64),
            nullable=True,
            index=True,
            comment="For nested tool calls",
        ),
        # Verification
        sa.Column("verification", sa.JSON(), nullable=True),
        sa.Column("capsule_id", sa.String(64), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create composite index for session tool queries
    op.create_index(
        "ix_tool_calls_session_step",
        "tool_calls",
        ["session_id", "step_index"],
    )

    # Create index for tool category analysis
    op.create_index(
        "ix_tool_calls_category_name",
        "tool_calls",
        ["tool_category", "tool_name"],
    )

    # Create action_traces table
    op.create_table(
        "action_traces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("action_id", sa.String(64), unique=True, nullable=False, index=True),
        # Session link
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("agent_sessions.session_id"),
            nullable=False,
            index=True,
        ),
        # Tool call link (optional)
        sa.Column(
            "tool_call_id",
            sa.String(64),
            sa.ForeignKey("tool_calls.call_id"),
            nullable=True,
            index=True,
        ),
        # Action type
        sa.Column(
            "action_type",
            sa.String(50),
            nullable=False,
            index=True,
            comment="Type: terminal, browser, file, api",
        ),
        # Terminal actions
        sa.Column("command", sa.Text(), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column(
            "stdout_hash",
            sa.String(64),
            nullable=True,
            comment="SHA-256 hash of stdout for privacy",
        ),
        sa.Column(
            "stderr_hash",
            sa.String(64),
            nullable=True,
            comment="SHA-256 hash of stderr for privacy",
        ),
        # Browser actions
        sa.Column("url", sa.String(2000), nullable=True),
        sa.Column("selector", sa.String(500), nullable=True),
        sa.Column(
            "browser_action",
            sa.String(50),
            nullable=True,
            comment="Action: navigate, click, type, screenshot",
        ),
        # File actions
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column(
            "file_operation",
            sa.String(50),
            nullable=True,
            comment="Operation: read, write, edit, delete, glob, grep",
        ),
        sa.Column("bytes_affected", sa.Integer(), nullable=True),
        # Timing
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "duration_ms",
            sa.Integer(),
            nullable=False,
            comment="Duration in milliseconds",
        ),
        # Verification
        sa.Column("verification", sa.JSON(), nullable=True),
        sa.Column("capsule_id", sa.String(64), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create index for action type analysis
    op.create_index(
        "ix_action_traces_session_type",
        "action_traces",
        ["session_id", "action_type"],
    )

    # Create decision_points table
    op.create_table(
        "decision_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "decision_id", sa.String(64), unique=True, nullable=False, index=True
        ),
        # Session link
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("agent_sessions.session_id"),
            nullable=False,
            index=True,
        ),
        # Decision context
        sa.Column(
            "step_index",
            sa.Integer(),
            nullable=False,
            index=True,
            comment="Step index within session",
        ),
        sa.Column(
            "reasoning",
            sa.Text(),
            nullable=False,
            comment="Why this action was chosen",
        ),
        sa.Column(
            "alternatives_considered",
            sa.JSON(),
            nullable=True,
            comment="List of other options evaluated",
        ),
        sa.Column(
            "selected_action",
            sa.Text(),
            nullable=False,
            comment="What was chosen",
        ),
        sa.Column(
            "confidence",
            sa.Float(),
            nullable=True,
            comment="Confidence score 0.0-1.0",
        ),
        sa.Column(
            "context_summary",
            sa.Text(),
            nullable=True,
            comment="Relevant context for decision",
        ),
        sa.Column(
            "constraints_applied",
            sa.JSON(),
            nullable=True,
            comment="List of safety, permissions, etc.",
        ),
        # Timing
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        # Verification
        sa.Column("verification", sa.JSON(), nullable=True),
        sa.Column("capsule_id", sa.String(64), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create index for step-based queries
    op.create_index(
        "ix_decision_points_session_step",
        "decision_points",
        ["session_id", "step_index"],
    )

    # Create environment_snapshots table
    op.create_table(
        "environment_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "snapshot_id", sa.String(64), unique=True, nullable=False, index=True
        ),
        # Session link
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("agent_sessions.session_id"),
            nullable=False,
            index=True,
        ),
        # Environment state
        sa.Column("working_directory", sa.String(1000), nullable=False),
        sa.Column(
            "env_vars_hash",
            sa.String(64),
            nullable=False,
            comment="SHA-256 hash of environment variables for privacy",
        ),
        # Git state
        sa.Column("git_branch", sa.String(255), nullable=True),
        sa.Column("git_commit_hash", sa.String(64), nullable=True),
        sa.Column("git_dirty", sa.Boolean(), nullable=True),
        # File tracking
        sa.Column(
            "open_files",
            sa.JSON(),
            nullable=True,
            comment="List of files being tracked",
        ),
        # System resources
        sa.Column("system_load", sa.Float(), nullable=True),
        sa.Column(
            "memory_available_gb",
            sa.Float(),
            nullable=True,
            comment="Available memory in GB",
        ),
        # Timing
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        # Verification
        sa.Column("verification", sa.JSON(), nullable=True),
        sa.Column("capsule_id", sa.String(64), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove agent execution trace tables."""
    op.drop_table("environment_snapshots")
    op.drop_index("ix_decision_points_session_step", table_name="decision_points")
    op.drop_table("decision_points")
    op.drop_index("ix_action_traces_session_type", table_name="action_traces")
    op.drop_table("action_traces")
    op.drop_index("ix_tool_calls_category_name", table_name="tool_calls")
    op.drop_index("ix_tool_calls_session_step", table_name="tool_calls")
    op.drop_table("tool_calls")
    op.drop_table("agent_sessions")
