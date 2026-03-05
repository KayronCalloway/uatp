"""
Agent Execution Service for UATP 7.4 Agent Execution Traces

This service handles:
- Agent session management
- Tool call tracking
- Action trace recording
- Decision point capture
- Environment snapshot management
- Session statistics aggregation
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.capsule_schema import (
    ActionTraceCapsule,
    ActionTracePayload,
    AgentSessionCapsule,
    AgentSessionPayload,
    CapsuleStatus,
    DecisionPointCapsule,
    DecisionPointPayload,
    EnvironmentSnapshotCapsule,
    EnvironmentSnapshotPayload,
    ToolCallCapsule,
    ToolCallPayload,
    Verification,
)
from src.models.agent_execution import (
    ActionTraceModel,
    ActionType,
    AgentSessionModel,
    AgentSessionStatus,
    DecisionPointModel,
    EnvironmentSnapshotModel,
    ToolCallModel,
    ToolCallStatus,
    ToolCategory,
)

logger = logging.getLogger(__name__)


class AgentExecutionService:
    """Service for UATP 7.4 agent execution traces."""

    def __init__(self, session_factory=None):
        """
        Initialize the agent execution service.

        Args:
            session_factory: SQLAlchemy session factory for database access
        """
        self.session_factory = session_factory

    # --- Agent Session Methods ---

    async def create_agent_session(
        self,
        agent_type: str,
        session: AsyncSession,
        agent_version: Optional[str] = None,
        scheduler_type: Optional[str] = None,
        trigger_message: Optional[str] = None,
        trigger_source: Optional[str] = None,
        user_id_hash: Optional[str] = None,
        goals: Optional[List[str]] = None,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new agent session.

        Args:
            agent_type: Type of agent (openclaw, claude_code, custom)
            session: Database session
            ... additional parameters

        Returns:
            Dict with creation result
        """
        try:
            # Validate agent_type
            valid_types = {"openclaw", "claude_code", "custom"}
            if agent_type not in valid_types:
                return {
                    "success": False,
                    "error": f"Invalid agent_type. Must be one of: {valid_types}",
                }

            # Validate trigger_source if provided
            if trigger_source:
                valid_sources = {"whatsapp", "telegram", "cli", "api", "web"}
                if trigger_source not in valid_sources:
                    return {
                        "success": False,
                        "error": f"Invalid trigger_source. Must be one of: {valid_sources}",
                    }

            # Generate session ID
            session_id = f"agent_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:12]}"

            # Create session
            agent_session = AgentSessionModel(
                session_id=session_id,
                agent_type=agent_type,
                agent_version=agent_version,
                scheduler_type=scheduler_type,
                trigger_message=trigger_message,
                trigger_source=trigger_source,
                user_id_hash=user_id_hash,
                goals=goals or [],
                status=AgentSessionStatus.RUNNING.value,
                started_at=datetime.now(timezone.utc),
                owner_id=owner_id,
            )

            session.add(agent_session)
            await session.commit()

            logger.info(f"Created agent session {session_id} for {agent_type}")

            return {
                "success": True,
                "session_id": session_id,
                "agent_type": agent_type,
                "status": "running",
            }

        except Exception as e:
            logger.error(f"Error creating agent session: {e}")
            await session.rollback()
            return {"success": False, "error": "Failed to create agent session"}

    async def get_agent_session(
        self, session_id: str, session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get agent session by ID."""
        result = await session.execute(
            select(AgentSessionModel).where(
                AgentSessionModel.session_id == session_id
            )
        )
        agent_session = result.scalar_one_or_none()
        if agent_session:
            return agent_session.to_dict()
        return None

    async def complete_agent_session(
        self,
        session_id: str,
        session: AsyncSession,
        status: str = "completed",
        outcome_summary: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mark an agent session as complete."""
        try:
            result = await session.execute(
                select(AgentSessionModel).where(
                    AgentSessionModel.session_id == session_id
                )
            )
            agent_session = result.scalar_one_or_none()

            if not agent_session:
                return {"success": False, "error": f"Session {session_id} not found"}

            # Update session
            agent_session.status = status
            agent_session.completed_at = datetime.now(timezone.utc)
            if outcome_summary:
                agent_session.outcome_summary = outcome_summary
            if error_message:
                agent_session.error_message = error_message

            # Calculate duration
            if agent_session.started_at:
                duration_ms = int(
                    (agent_session.completed_at - agent_session.started_at).total_seconds() * 1000
                )
                agent_session.total_duration_ms = duration_ms

            await session.commit()

            logger.info(f"Completed agent session {session_id} with status {status}")

            return {
                "success": True,
                "session_id": session_id,
                "status": status,
                "total_duration_ms": agent_session.total_duration_ms,
            }

        except Exception as e:
            logger.error(f"Error completing agent session: {e}")
            await session.rollback()
            return {"success": False, "error": "Failed to complete agent session"}

    async def get_session_stats(self, session: AsyncSession) -> Dict[str, Any]:
        """Get aggregate statistics for agent sessions."""
        # Count by status
        status_query = select(
            AgentSessionModel.status,
            func.count(AgentSessionModel.id)
        ).group_by(AgentSessionModel.status)
        status_result = await session.execute(status_query)
        by_status = {row[0]: row[1] for row in status_result.fetchall()}

        # Count by agent type
        type_query = select(
            AgentSessionModel.agent_type,
            func.count(AgentSessionModel.id)
        ).group_by(AgentSessionModel.agent_type)
        type_result = await session.execute(type_query)
        by_agent_type = {row[0]: row[1] for row in type_result.fetchall()}

        # Total
        total_result = await session.execute(
            select(func.count(AgentSessionModel.id))
        )
        total = total_result.scalar() or 0

        # Average duration for completed sessions
        avg_query = select(
            func.avg(AgentSessionModel.total_duration_ms),
        ).where(AgentSessionModel.status == "completed")
        avg_result = await session.execute(avg_query)
        avg_row = avg_result.fetchone()

        return {
            "total_sessions": total,
            "by_status": by_status,
            "by_agent_type": by_agent_type,
            "avg_duration_ms": float(avg_row[0]) if avg_row and avg_row[0] else None,
        }

    # --- Tool Call Methods ---

    async def record_tool_call(
        self,
        session_id: str,
        tool_name: str,
        tool_category: str,
        step_index: int,
        session: AsyncSession,
        tool_inputs: Optional[Dict[str, Any]] = None,
        tool_outputs: Optional[Dict[str, Any]] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        parent_call_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a tool call."""
        try:
            # Validate session exists
            agent_session_result = await session.execute(
                select(AgentSessionModel).where(
                    AgentSessionModel.session_id == session_id
                )
            )
            agent_session = agent_session_result.scalar_one_or_none()
            if not agent_session:
                return {"success": False, "error": f"Session {session_id} not found"}

            # Validate tool_category
            valid_categories = {c.value for c in ToolCategory}
            if tool_category not in valid_categories:
                return {
                    "success": False,
                    "error": f"Invalid tool_category. Must be one of: {valid_categories}",
                }

            # Generate call ID
            call_id = f"tool_{uuid.uuid4().hex[:16]}"

            # Use current time if not provided
            if started_at is None:
                started_at = datetime.now(timezone.utc)

            # Create tool call
            tool_call = ToolCallModel(
                call_id=call_id,
                session_id=session_id,
                tool_name=tool_name,
                tool_category=tool_category,
                tool_inputs=tool_inputs,
                tool_outputs=tool_outputs,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                status=status,
                error_message=error_message,
                step_index=step_index,
                parent_call_id=parent_call_id,
            )

            session.add(tool_call)

            # Update session tool count
            agent_session.tool_call_count += 1

            await session.commit()

            logger.info(f"Recorded tool call {call_id}: {tool_name}")

            return {
                "success": True,
                "call_id": call_id,
                "session_id": session_id,
                "tool_name": tool_name,
            }

        except Exception as e:
            logger.error(f"Error recording tool call: {e}")
            await session.rollback()
            return {"success": False, "error": "Failed to record tool call"}

    async def batch_record_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """Record a batch of tool calls."""
        try:
            if not tool_calls:
                return {"success": False, "error": "No tool calls provided"}

            session_id = tool_calls[0]["session_id"]

            # Validate session exists
            agent_session_result = await session.execute(
                select(AgentSessionModel).where(
                    AgentSessionModel.session_id == session_id
                )
            )
            agent_session = agent_session_result.scalar_one_or_none()
            if not agent_session:
                return {"success": False, "error": f"Session {session_id} not found"}

            call_ids = []

            for call_data in tool_calls:
                call_id = f"tool_{uuid.uuid4().hex[:16]}"
                tool_call = ToolCallModel(
                    call_id=call_id,
                    session_id=call_data["session_id"],
                    tool_name=call_data["tool_name"],
                    tool_category=call_data["tool_category"],
                    tool_inputs=call_data.get("tool_inputs"),
                    tool_outputs=call_data.get("tool_outputs"),
                    started_at=call_data.get("started_at", datetime.now(timezone.utc)),
                    completed_at=call_data.get("completed_at"),
                    duration_ms=call_data.get("duration_ms"),
                    status=call_data.get("status", "success"),
                    error_message=call_data.get("error_message"),
                    step_index=call_data["step_index"],
                    parent_call_id=call_data.get("parent_call_id"),
                )
                session.add(tool_call)
                call_ids.append(call_id)

            # Update session
            agent_session.tool_call_count += len(tool_calls)

            await session.commit()

            return {
                "success": True,
                "call_ids": call_ids,
                "count": len(tool_calls),
                "session_id": session_id,
            }

        except Exception as e:
            logger.error(f"Error batch recording tool calls: {e}")
            await session.rollback()
            return {"success": False, "error": "Failed to batch record tool calls"}

    async def list_tool_calls(
        self,
        session_id: str,
        session: AsyncSession,
        tool_name: Optional[str] = None,
        tool_category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List tool calls for a session."""
        query = select(ToolCallModel).where(
            ToolCallModel.session_id == session_id
        )

        if tool_name:
            query = query.where(ToolCallModel.tool_name == tool_name)
        if tool_category:
            query = query.where(ToolCallModel.tool_category == tool_category)

        query = query.order_by(ToolCallModel.step_index).offset(offset).limit(limit)

        result = await session.execute(query)
        return [t.to_dict() for t in result.scalars().all()]

    # --- Action Trace Methods ---

    async def record_action_trace(
        self,
        session_id: str,
        action_type: str,
        executed_at: datetime,
        duration_ms: int,
        session: AsyncSession,
        tool_call_id: Optional[str] = None,
        # Terminal fields
        command: Optional[str] = None,
        exit_code: Optional[int] = None,
        stdout_hash: Optional[str] = None,
        stderr_hash: Optional[str] = None,
        # Browser fields
        url: Optional[str] = None,
        selector: Optional[str] = None,
        browser_action: Optional[str] = None,
        # File fields
        file_path: Optional[str] = None,
        file_operation: Optional[str] = None,
        bytes_affected: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Record an action trace."""
        try:
            # Validate session exists
            agent_session_result = await session.execute(
                select(AgentSessionModel).where(
                    AgentSessionModel.session_id == session_id
                )
            )
            agent_session = agent_session_result.scalar_one_or_none()
            if not agent_session:
                return {"success": False, "error": f"Session {session_id} not found"}

            # Validate action_type
            valid_types = {t.value for t in ActionType}
            if action_type not in valid_types:
                return {
                    "success": False,
                    "error": f"Invalid action_type. Must be one of: {valid_types}",
                }

            # Generate action ID
            action_id = f"act_{uuid.uuid4().hex[:16]}"

            # Create action trace
            action_trace = ActionTraceModel(
                action_id=action_id,
                session_id=session_id,
                tool_call_id=tool_call_id,
                action_type=action_type,
                command=command,
                exit_code=exit_code,
                stdout_hash=stdout_hash,
                stderr_hash=stderr_hash,
                url=url,
                selector=selector,
                browser_action=browser_action,
                file_path=file_path,
                file_operation=file_operation,
                bytes_affected=bytes_affected,
                executed_at=executed_at,
                duration_ms=duration_ms,
            )

            session.add(action_trace)

            # Update session action count
            agent_session.action_count += 1

            await session.commit()

            logger.info(f"Recorded action trace {action_id}: {action_type}")

            return {
                "success": True,
                "action_id": action_id,
                "session_id": session_id,
                "action_type": action_type,
            }

        except Exception as e:
            logger.error(f"Error recording action trace: {e}")
            await session.rollback()
            return {"success": False, "error": "Failed to record action trace"}

    async def list_action_traces(
        self,
        session_id: str,
        session: AsyncSession,
        action_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List action traces for a session."""
        query = select(ActionTraceModel).where(
            ActionTraceModel.session_id == session_id
        )

        if action_type:
            query = query.where(ActionTraceModel.action_type == action_type)

        query = query.order_by(ActionTraceModel.executed_at).offset(offset).limit(limit)

        result = await session.execute(query)
        return [a.to_dict() for a in result.scalars().all()]

    # --- Decision Point Methods ---

    async def record_decision_point(
        self,
        session_id: str,
        step_index: int,
        reasoning: str,
        selected_action: str,
        session: AsyncSession,
        alternatives_considered: Optional[List[str]] = None,
        confidence: Optional[float] = None,
        context_summary: Optional[str] = None,
        constraints_applied: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Record a decision point."""
        try:
            # Validate session exists
            agent_session_result = await session.execute(
                select(AgentSessionModel).where(
                    AgentSessionModel.session_id == session_id
                )
            )
            agent_session = agent_session_result.scalar_one_or_none()
            if not agent_session:
                return {"success": False, "error": f"Session {session_id} not found"}

            # Validate confidence if provided
            if confidence is not None and (confidence < 0.0 or confidence > 1.0):
                return {
                    "success": False,
                    "error": "Confidence must be between 0.0 and 1.0",
                }

            # Generate decision ID
            decision_id = f"dec_{uuid.uuid4().hex[:16]}"

            # Use current time if not provided
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)

            # Create decision point
            decision_point = DecisionPointModel(
                decision_id=decision_id,
                session_id=session_id,
                step_index=step_index,
                reasoning=reasoning,
                alternatives_considered=alternatives_considered or [],
                selected_action=selected_action,
                confidence=confidence,
                context_summary=context_summary,
                constraints_applied=constraints_applied or [],
                timestamp=timestamp,
            )

            session.add(decision_point)

            # Update session decision count
            agent_session.decision_count += 1

            await session.commit()

            logger.info(f"Recorded decision point {decision_id}")

            return {
                "success": True,
                "decision_id": decision_id,
                "session_id": session_id,
                "step_index": step_index,
            }

        except Exception as e:
            logger.error(f"Error recording decision point: {e}")
            await session.rollback()
            return {"success": False, "error": "Failed to record decision point"}

    async def list_decision_points(
        self,
        session_id: str,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List decision points for a session."""
        result = await session.execute(
            select(DecisionPointModel)
            .where(DecisionPointModel.session_id == session_id)
            .order_by(DecisionPointModel.step_index)
            .offset(offset)
            .limit(limit)
        )
        return [d.to_dict() for d in result.scalars().all()]

    # --- Environment Snapshot Methods ---

    async def record_environment_snapshot(
        self,
        session_id: str,
        working_directory: str,
        env_vars_hash: str,
        session: AsyncSession,
        git_branch: Optional[str] = None,
        git_commit_hash: Optional[str] = None,
        git_dirty: Optional[bool] = None,
        open_files: Optional[List[str]] = None,
        system_load: Optional[float] = None,
        memory_available_gb: Optional[float] = None,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Record an environment snapshot."""
        try:
            # Validate session exists
            agent_session_result = await session.execute(
                select(AgentSessionModel).where(
                    AgentSessionModel.session_id == session_id
                )
            )
            agent_session = agent_session_result.scalar_one_or_none()
            if not agent_session:
                return {"success": False, "error": f"Session {session_id} not found"}

            # Generate snapshot ID
            snapshot_id = f"snap_{uuid.uuid4().hex[:16]}"

            # Use current time if not provided
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)

            # Create snapshot
            snapshot = EnvironmentSnapshotModel(
                snapshot_id=snapshot_id,
                session_id=session_id,
                working_directory=working_directory,
                env_vars_hash=env_vars_hash,
                git_branch=git_branch,
                git_commit_hash=git_commit_hash,
                git_dirty=git_dirty,
                open_files=open_files or [],
                system_load=system_load,
                memory_available_gb=memory_available_gb,
                timestamp=timestamp,
            )

            session.add(snapshot)
            await session.commit()

            logger.info(f"Recorded environment snapshot {snapshot_id}")

            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "session_id": session_id,
                "working_directory": working_directory,
            }

        except Exception as e:
            logger.error(f"Error recording environment snapshot: {e}")
            await session.rollback()
            return {"success": False, "error": "Failed to record environment snapshot"}

    async def list_environment_snapshots(
        self,
        session_id: str,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List environment snapshots for a session."""
        result = await session.execute(
            select(EnvironmentSnapshotModel)
            .where(EnvironmentSnapshotModel.session_id == session_id)
            .order_by(EnvironmentSnapshotModel.timestamp)
            .offset(offset)
            .limit(limit)
        )
        return [s.to_dict() for s in result.scalars().all()]

    # --- Session Statistics ---

    async def get_session_statistics(
        self, session_id: str, session: AsyncSession
    ) -> Dict[str, Any]:
        """Get aggregate statistics for a session."""
        # Verify session exists
        agent_session_result = await session.execute(
            select(AgentSessionModel).where(
                AgentSessionModel.session_id == session_id
            )
        )
        agent_session = agent_session_result.scalar_one_or_none()
        if not agent_session:
            return {"error": f"Session {session_id} not found"}

        # Tool call stats by category
        tool_query = select(
            ToolCallModel.tool_category,
            func.count(ToolCallModel.id),
            func.avg(ToolCallModel.duration_ms),
        ).where(
            ToolCallModel.session_id == session_id
        ).group_by(ToolCallModel.tool_category)

        tool_result = await session.execute(tool_query)
        by_tool_category = {}
        for row in tool_result.fetchall():
            by_tool_category[row[0]] = {
                "count": row[1],
                "avg_duration_ms": float(row[2]) if row[2] else 0,
            }

        # Action trace stats by type
        action_query = select(
            ActionTraceModel.action_type,
            func.count(ActionTraceModel.id),
            func.avg(ActionTraceModel.duration_ms),
        ).where(
            ActionTraceModel.session_id == session_id
        ).group_by(ActionTraceModel.action_type)

        action_result = await session.execute(action_query)
        by_action_type = {}
        for row in action_result.fetchall():
            by_action_type[row[0]] = {
                "count": row[1],
                "avg_duration_ms": float(row[2]) if row[2] else 0,
            }

        # Decision point stats
        decision_query = select(
            func.count(DecisionPointModel.id),
            func.avg(DecisionPointModel.confidence),
        ).where(DecisionPointModel.session_id == session_id)

        decision_result = await session.execute(decision_query)
        decision_row = decision_result.fetchone()

        return {
            "session_id": session_id,
            "status": agent_session.status,
            "tool_call_count": agent_session.tool_call_count,
            "action_count": agent_session.action_count,
            "decision_count": agent_session.decision_count,
            "total_duration_ms": agent_session.total_duration_ms,
            "by_tool_category": by_tool_category,
            "by_action_type": by_action_type,
            "avg_decision_confidence": (
                float(decision_row[1]) if decision_row and decision_row[1] else None
            ),
        }

    # --- Capsule Creation Methods ---

    def create_agent_session_capsule(
        self,
        session_id: str,
        agent_type: str,
        started_at: datetime,
        goals: Optional[List[str]] = None,
        agent_version: Optional[str] = None,
        scheduler_type: Optional[str] = None,
        trigger_message: Optional[str] = None,
        trigger_source: Optional[str] = None,
        user_id_hash: Optional[str] = None,
        status: str = "running",
        completed_at: Optional[datetime] = None,
        tool_call_count: int = 0,
        action_count: int = 0,
        decision_count: int = 0,
        total_duration_ms: Optional[int] = None,
        outcome_summary: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> AgentSessionCapsule:
        """Create a UATP capsule for agent session."""
        payload = AgentSessionPayload(
            session_id=session_id,
            agent_type=agent_type,
            agent_version=agent_version,
            scheduler_type=scheduler_type,
            trigger_message=trigger_message,
            trigger_source=trigger_source,
            user_id_hash=user_id_hash,
            goals=goals or [],
            started_at=started_at,
            completed_at=completed_at,
            status=status,
            tool_call_count=tool_call_count,
            action_count=action_count,
            decision_count=decision_count,
            total_duration_ms=total_duration_ms,
            outcome_summary=outcome_summary,
            error_message=error_message,
        )

        capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        return AgentSessionCapsule(
            capsule_id=capsule_id,
            version="7.4",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(
                signature=f"ed25519:{'0' * 128}",
                merkle_root=f"sha256:{'0' * 64}",
            ),
            agent_session=payload,
        )

    def create_tool_call_capsule(
        self,
        call_id: str,
        session_id: str,
        tool_name: str,
        tool_category: str,
        tool_inputs: Dict[str, Any],
        started_at: datetime,
        step_index: int,
        tool_outputs: Optional[Dict[str, Any]] = None,
        completed_at: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        parent_call_id: Optional[str] = None,
    ) -> ToolCallCapsule:
        """Create a UATP capsule for tool call."""
        payload = ToolCallPayload(
            call_id=call_id,
            session_id=session_id,
            tool_name=tool_name,
            tool_category=tool_category,
            tool_inputs=tool_inputs,
            tool_outputs=tool_outputs,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            step_index=step_index,
            parent_call_id=parent_call_id,
        )

        capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        return ToolCallCapsule(
            capsule_id=capsule_id,
            version="7.4",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(
                signature=f"ed25519:{'0' * 128}",
                merkle_root=f"sha256:{'0' * 64}",
            ),
            tool_call=payload,
        )

    def create_decision_point_capsule(
        self,
        decision_id: str,
        session_id: str,
        step_index: int,
        reasoning: str,
        selected_action: str,
        timestamp: datetime,
        alternatives_considered: Optional[List[str]] = None,
        confidence: Optional[float] = None,
        context_summary: Optional[str] = None,
        constraints_applied: Optional[List[str]] = None,
    ) -> DecisionPointCapsule:
        """Create a UATP capsule for decision point."""
        payload = DecisionPointPayload(
            decision_id=decision_id,
            session_id=session_id,
            step_index=step_index,
            reasoning=reasoning,
            alternatives_considered=alternatives_considered or [],
            selected_action=selected_action,
            confidence=confidence,
            context_summary=context_summary,
            constraints_applied=constraints_applied or [],
            timestamp=timestamp,
        )

        capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        return DecisionPointCapsule(
            capsule_id=capsule_id,
            version="7.4",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(
                signature=f"ed25519:{'0' * 128}",
                merkle_root=f"sha256:{'0' * 64}",
            ),
            decision_point=payload,
        )


# Global service instance
agent_execution_service = AgentExecutionService()
