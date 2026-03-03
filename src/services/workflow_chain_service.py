"""
Workflow Chain Service for UATP 7.2 Agentic Workflow Chains

This service handles:
- Creating workflow containers
- Adding steps to workflows
- DAG management and step dependencies
- Attribution aggregation
- Workflow completion and sealing
"""

import logging
import re
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.capsule_schema import (
    CapsuleStatus,
    Verification,
    WorkflowCompleteCapsule,
    WorkflowCompletePayload,
    WorkflowStepCapsule,
    WorkflowStepPayload,
)
from src.models.capsule import CapsuleModel
from src.models.workflow_capsule import WorkflowCapsuleModel, WorkflowStatus
from src.utils.attribution_aggregator import (
    aggregate_attributions,
    merge_dag_definitions,
)

logger = logging.getLogger(__name__)


# SECURITY: Placeholder signature patterns that must be rejected when sealing
PLACEHOLDER_SIGNATURES = {
    "ed25519:" + "0" * 128,  # All-zero Ed25519 signature
    "0" * 128,  # Raw all-zero signature
    "ed25519:" + "f" * 128,  # All-f signature (another common placeholder)
}


def is_placeholder_signature(signature: Optional[str]) -> bool:
    """
    Check if a signature is a placeholder that should be rejected.

    SECURITY: Placeholder signatures indicate the capsule was never properly
    signed. Accepting such capsules would bypass cryptographic verification.

    Args:
        signature: The signature string to check

    Returns:
        True if the signature is a placeholder or invalid
    """
    if not signature:
        return True

    # Check against known placeholder patterns
    if signature in PLACEHOLDER_SIGNATURES:
        return True

    # Check if it's a valid Ed25519 signature format
    if signature.startswith("ed25519:"):
        sig_hex = signature[8:]  # Remove "ed25519:" prefix
        # Ed25519 signatures are 64 bytes = 128 hex characters
        if len(sig_hex) != 128:
            return True
        # Check if it's all the same character (obvious placeholder)
        if len(set(sig_hex)) == 1:
            return True
    else:
        # Raw signature - should be 128 hex characters
        if len(signature) != 128:
            return True
        if len(set(signature)) == 1:
            return True

    return False


class StepRateLimiter:
    """
    Per-user rate limiter for workflow step creation.

    Prevents DoS attacks by limiting how many steps a user can create
    within a time window.
    """

    def __init__(
        self,
        max_steps_per_window: int = 100,
        window_seconds: int = 3600,  # 1 hour
    ):
        """
        Initialize the rate limiter.

        Args:
            max_steps_per_window: Maximum steps allowed per user per window
            window_seconds: Time window in seconds
        """
        self.max_steps_per_window = max_steps_per_window
        self.window_seconds = window_seconds
        self._user_steps: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()

    def check_and_record(self, user_id: str) -> Tuple[bool, int]:
        """
        Check if user can create a step and record the attempt.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (allowed: bool, remaining: int)
        """
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            # Remove expired entries
            self._user_steps[user_id] = [
                t for t in self._user_steps[user_id] if t > cutoff
            ]

            current_count = len(self._user_steps[user_id])
            remaining = max(0, self.max_steps_per_window - current_count)

            if current_count >= self.max_steps_per_window:
                return False, 0

            # Record this step
            self._user_steps[user_id].append(now)
            return True, remaining - 1

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get rate limit stats for a user."""
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            # Clean up expired entries
            self._user_steps[user_id] = [
                t for t in self._user_steps[user_id] if t > cutoff
            ]

            current_count = len(self._user_steps[user_id])
            oldest = (
                min(self._user_steps[user_id]) if self._user_steps[user_id] else now
            )

            return {
                "user_id": user_id,
                "steps_in_window": current_count,
                "max_steps_per_window": self.max_steps_per_window,
                "remaining": max(0, self.max_steps_per_window - current_count),
                "window_seconds": self.window_seconds,
                "window_resets_in": int(oldest + self.window_seconds - now)
                if current_count > 0
                else 0,
            }


# Global rate limiter instance
_step_rate_limiter = StepRateLimiter()


class WorkflowChainService:
    """Service for UATP 7.2 agentic workflow chains."""

    # SECURITY: Maximum steps per workflow to prevent unbounded growth
    MAX_STEPS_PER_WORKFLOW = 10000
    DEFAULT_MAX_STEPS = 1000

    # SECURITY: Workflow name constraints
    MIN_WORKFLOW_NAME_LENGTH = 1
    MAX_WORKFLOW_NAME_LENGTH = 255
    # Characters allowed in workflow names (alphanumeric, spaces, common punctuation)
    WORKFLOW_NAME_PATTERN = re.compile(
        r'^[\w\s\-_.,:;!?\'"()\[\]{}@#$%&*+=<>/\\|~`]+$', re.UNICODE
    )

    def __init__(self, session_factory=None, max_steps: int = None):
        """
        Initialize the workflow chain service.

        Args:
            session_factory: SQLAlchemy session factory for database access
            max_steps: Maximum steps allowed per workflow (default: 1000)
        """
        self.session_factory = session_factory
        self.max_steps = min(
            max_steps or self.DEFAULT_MAX_STEPS, self.MAX_STEPS_PER_WORKFLOW
        )

    async def create_workflow(
        self,
        workflow_name: str,
        workflow_type: str,
        session: AsyncSession,
        owner_id: Optional[str] = None,
        dag_definition: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new workflow container.

        Args:
            workflow_name: Human-readable workflow name
            workflow_type: Type (linear, branching, iterative, parallel)
            session: Database session
            owner_id: Owner user ID
            dag_definition: Optional initial DAG structure

        Returns:
            Dict with workflow creation result
        """
        try:
            # SECURITY: Validate workflow_name length and characters
            if not workflow_name:
                return {
                    "success": False,
                    "error": "workflow_name is required",
                }

            workflow_name = workflow_name.strip()
            if len(workflow_name) < self.MIN_WORKFLOW_NAME_LENGTH:
                return {
                    "success": False,
                    "error": f"workflow_name too short (minimum {self.MIN_WORKFLOW_NAME_LENGTH} characters)",
                }

            if len(workflow_name) > self.MAX_WORKFLOW_NAME_LENGTH:
                return {
                    "success": False,
                    "error": f"workflow_name too long (maximum {self.MAX_WORKFLOW_NAME_LENGTH} characters)",
                }

            if not self.WORKFLOW_NAME_PATTERN.match(workflow_name):
                return {
                    "success": False,
                    "error": "workflow_name contains invalid characters",
                }

            # Validate workflow_type
            valid_types = {"linear", "branching", "iterative", "parallel"}
            if workflow_type not in valid_types:
                return {
                    "success": False,
                    "error": f"Invalid workflow_type. Must be one of: {valid_types}",
                }

            # Generate workflow ID
            workflow_id = f"wf_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:16]}"

            # Create workflow
            workflow = WorkflowCapsuleModel(
                workflow_capsule_id=workflow_id,
                workflow_name=workflow_name,
                workflow_type=workflow_type,
                status=WorkflowStatus.ACTIVE.value,
                owner_id=owner_id,
                dag_definition=dag_definition,
                step_count=0,
            )

            session.add(workflow)
            await session.commit()

            logger.info(f"Created workflow {workflow_id} ({workflow_name})")

            return {
                "success": True,
                "workflow_capsule_id": workflow_id,
                "workflow_name": workflow_name,
                "workflow_type": workflow_type,
                "status": "active",
            }

        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            await session.rollback()
            return {"success": False, "error": str(e)}

    async def add_step(
        self,
        workflow_capsule_id: str,
        step_type: str,
        session: AsyncSession,
        step_name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        depends_on_steps: Optional[List[int]] = None,
        tool_name: Optional[str] = None,
        model_id: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        confidence: Optional[float] = None,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a step to an existing workflow.

        Args:
            workflow_capsule_id: Parent workflow ID
            step_type: Type of step (plan, tool_call, inference, output, etc.)
            session: Database session
            step_name: Optional human-readable step name
            input_data: Step input data
            output_data: Step output data
            depends_on_steps: List of step indices this depends on
            tool_name: Tool used (for tool_call steps)
            model_id: Model used (for inference steps)
            execution_time_ms: Step execution time
            confidence: Step confidence score
            owner_id: Owner user ID

        Returns:
            Dict with step creation result
        """
        # SECURITY: Per-user rate limiting to prevent DoS via unbounded step creation
        if owner_id:
            allowed, remaining = _step_rate_limiter.check_and_record(owner_id)
            if not allowed:
                stats = _step_rate_limiter.get_user_stats(owner_id)
                logger.warning(
                    f"Rate limit exceeded for user {owner_id}: "
                    f"{stats['steps_in_window']}/{stats['max_steps_per_window']} steps in window"
                )
                return {
                    "success": False,
                    "error": f"Rate limit exceeded: maximum {stats['max_steps_per_window']} "
                    f"steps per {stats['window_seconds']} seconds. "
                    f"Try again in {stats['window_resets_in']} seconds.",
                    "rate_limit": stats,
                }

        try:
            # SECURITY: Use SELECT FOR UPDATE immediately to prevent TOCTOU race conditions
            # The lock must be acquired BEFORE any status/ownership checks to ensure
            # consistent state throughout the operation

            locked_result = await session.execute(
                select(WorkflowCapsuleModel)
                .where(WorkflowCapsuleModel.workflow_capsule_id == workflow_capsule_id)
                .with_for_update()
            )
            workflow = locked_result.scalar_one_or_none()

            if not workflow:
                return {
                    "success": False,
                    "error": f"Workflow {workflow_capsule_id} not found",
                }

            # SECURITY: Verify caller owns the workflow before allowing step addition
            # Now protected by row lock - no TOCTOU possible
            if workflow.owner_id and owner_id and workflow.owner_id != owner_id:
                logger.warning(
                    f"Unauthorized add_step attempt: user {owner_id} tried to modify workflow owned by {workflow.owner_id}"
                )
                return {
                    "success": False,
                    "error": "Unauthorized: you do not own this workflow",
                }

            # Status check now protected by row lock
            if workflow.status != WorkflowStatus.ACTIVE.value:
                return {
                    "success": False,
                    "error": f"Workflow {workflow_capsule_id} is not active",
                }

            # SECURITY: Enforce maximum steps limit to prevent unbounded growth
            # Now protected by row lock - no race condition on step_count
            if workflow.step_count >= self.max_steps:
                logger.warning(
                    f"Workflow {workflow_capsule_id} has reached max steps limit ({self.max_steps})"
                )
                return {
                    "success": False,
                    "error": f"Workflow has reached maximum step limit ({self.max_steps}). "
                    "Complete this workflow and create a new one to continue.",
                }

            # Validate step_type
            valid_types = {
                "plan",
                "tool_call",
                "inference",
                "output",
                "human_input",
                "verification",
                "decision",
                "aggregation",
            }
            if step_type not in valid_types:
                return {
                    "success": False,
                    "error": f"Invalid step_type. Must be one of: {valid_types}",
                }

            # Get current step index (now protected by row lock)
            step_index = workflow.step_count

            # Validate depends_on_steps
            if depends_on_steps:
                for dep_idx in depends_on_steps:
                    if dep_idx >= step_index:
                        return {
                            "success": False,
                            "error": f"Invalid dependency: step {dep_idx} doesn't exist yet",
                        }

            # Generate capsule ID for this step
            capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

            # Build payload
            payload = {
                "workflow_capsule_id": workflow_capsule_id,
                "step_index": step_index,
                "step_type": step_type,
                "step_name": step_name,
                "input_data": input_data,
                "output_data": output_data,
                "depends_on_steps": depends_on_steps,
                "tool_name": tool_name,
                "model_id": model_id,
                "execution_time_ms": execution_time_ms,
                "confidence": confidence,
            }

            # Create step capsule
            step_capsule = CapsuleModel(
                capsule_id=capsule_id,
                capsule_type="workflow_step",
                version="7.2",
                timestamp=datetime.now(timezone.utc),
                status="sealed",
                verification={"signature": None, "hash": None},
                payload=payload,
                owner_id=owner_id,
                workflow_capsule_id=workflow_capsule_id,
                step_index=step_index,
                step_type=step_type,
                depends_on_steps=depends_on_steps,
            )

            session.add(step_capsule)

            # Increment workflow step count
            workflow.step_count = step_index + 1
            await session.commit()

            logger.info(
                f"Added step {step_index} ({step_type}) to workflow {workflow_capsule_id}"
            )

            return {
                "success": True,
                "capsule_id": capsule_id,
                "workflow_capsule_id": workflow_capsule_id,
                "step_index": step_index,
                "step_type": step_type,
            }

        except Exception as e:
            logger.error(f"Failed to add workflow step: {e}")
            await session.rollback()
            return {"success": False, "error": str(e)}

    async def get_workflow(
        self, workflow_capsule_id: str, session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        Get workflow details with steps.

        Args:
            workflow_capsule_id: Workflow ID
            session: Database session

        Returns:
            Workflow dict with steps or None if not found
        """
        # Get workflow
        workflow_result = await session.execute(
            select(WorkflowCapsuleModel).where(
                WorkflowCapsuleModel.workflow_capsule_id == workflow_capsule_id
            )
        )
        workflow = workflow_result.scalar_one_or_none()

        if not workflow:
            return None

        # Get steps
        steps_result = await session.execute(
            select(CapsuleModel)
            .where(CapsuleModel.workflow_capsule_id == workflow_capsule_id)
            .order_by(CapsuleModel.step_index)
        )
        steps = steps_result.scalars().all()

        step_list = []
        for step in steps:
            step_data = {
                "capsule_id": step.capsule_id,
                "step_index": step.step_index,
                "step_type": step.step_type,
                "depends_on_steps": step.depends_on_steps,
                "timestamp": step.timestamp.isoformat() if step.timestamp else None,
            }
            if step.payload:
                step_data["step_name"] = step.payload.get("step_name")
                step_data["execution_time_ms"] = step.payload.get("execution_time_ms")
                step_data["confidence"] = step.payload.get("confidence")
            step_list.append(step_data)

        workflow_data = workflow.to_dict()
        workflow_data["steps"] = step_list

        return workflow_data

    async def get_workflow_steps(
        self, workflow_capsule_id: str, session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Get steps for a workflow in order.

        Args:
            workflow_capsule_id: Workflow ID
            session: Database session

        Returns:
            List of step dicts
        """
        steps_result = await session.execute(
            select(CapsuleModel)
            .where(CapsuleModel.workflow_capsule_id == workflow_capsule_id)
            .order_by(CapsuleModel.step_index)
        )
        steps = steps_result.scalars().all()

        return [
            {
                "capsule_id": s.capsule_id,
                "step_index": s.step_index,
                "step_type": s.step_type,
                "depends_on_steps": s.depends_on_steps,
                "payload": s.payload,
                "verification": s.verification,  # Include verification for signature checks
                "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            }
            for s in steps
        ]

    async def get_aggregated_attribution(
        self, workflow_capsule_id: str, session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get aggregated attribution for a workflow.

        Args:
            workflow_capsule_id: Workflow ID
            session: Database session

        Returns:
            Aggregated attribution dict
        """
        # Get workflow
        workflow_result = await session.execute(
            select(WorkflowCapsuleModel).where(
                WorkflowCapsuleModel.workflow_capsule_id == workflow_capsule_id
            )
        )
        workflow = workflow_result.scalar_one_or_none()

        if not workflow:
            return {"error": f"Workflow {workflow_capsule_id} not found"}

        # If already computed, return it
        if workflow.aggregated_attribution:
            return workflow.aggregated_attribution

        # Get steps and aggregate
        steps = await self.get_workflow_steps(workflow_capsule_id, session)

        # Extract attributions from step payloads
        step_attributions = []
        for step in steps:
            payload = step.get("payload", {})
            if "attribution" in payload:
                step_attributions.append(payload["attribution"])

        aggregated = aggregate_attributions(step_attributions)

        return {
            "workflow_capsule_id": workflow_capsule_id,
            **aggregated,
        }

    async def complete_workflow(
        self,
        workflow_capsule_id: str,
        session: AsyncSession,
        final_output: Optional[Dict[str, Any]] = None,
        status: str = "completed",
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mark a workflow as complete and seal it.

        Args:
            workflow_capsule_id: Workflow ID
            session: Database session
            final_output: Final workflow output
            status: Final status (completed, failed, cancelled)

        Returns:
            Dict with completion result
        """
        try:
            # Get workflow
            workflow_result = await session.execute(
                select(WorkflowCapsuleModel).where(
                    WorkflowCapsuleModel.workflow_capsule_id == workflow_capsule_id
                )
            )
            workflow = workflow_result.scalar_one_or_none()

            if not workflow:
                return {
                    "success": False,
                    "error": f"Workflow {workflow_capsule_id} not found",
                }

            # SECURITY: Verify caller owns the workflow before allowing completion
            if workflow.owner_id and owner_id and workflow.owner_id != owner_id:
                logger.warning(
                    f"Unauthorized complete_workflow attempt: user {owner_id} tried to complete workflow owned by {workflow.owner_id}"
                )
                return {
                    "success": False,
                    "error": "Unauthorized: you do not own this workflow",
                }

            if workflow.status != WorkflowStatus.ACTIVE.value:
                return {
                    "success": False,
                    "error": f"Workflow {workflow_capsule_id} is already {workflow.status}",
                }

            # Get all steps
            steps = await self.get_workflow_steps(workflow_capsule_id, session)

            # SECURITY: Verify all steps have valid (non-placeholder) signatures
            # before sealing the workflow
            steps_with_placeholder_sigs = []
            for step in steps:
                # Check verification field on step (not inside payload)
                # Steps are created with verification={"signature": None, "hash": None}
                # and must be signed before workflow completion
                verification = step.get("verification", {})
                if isinstance(verification, dict):
                    sig = verification.get("signature")
                    if is_placeholder_signature(sig):
                        steps_with_placeholder_sigs.append(step.get("step_index", "?"))

            if steps_with_placeholder_sigs:
                logger.warning(
                    f"Workflow {workflow_capsule_id} has steps with placeholder signatures: "
                    f"{steps_with_placeholder_sigs}"
                )
                return {
                    "success": False,
                    "error": f"Cannot seal workflow: steps {steps_with_placeholder_sigs} have "
                    f"placeholder signatures. All steps must be properly signed before "
                    f"workflow completion.",
                    "steps_requiring_signature": steps_with_placeholder_sigs,
                }

            # Build DAG definition
            step_data_for_dag = [
                {
                    "step_index": s["step_index"],
                    "step_type": s["step_type"],
                    "capsule_id": s["capsule_id"],
                    "depends_on_steps": s.get("depends_on_steps"),
                }
                for s in steps
            ]
            dag_definition = merge_dag_definitions(step_data_for_dag)

            # Aggregate attribution
            aggregated = await self.get_aggregated_attribution(
                workflow_capsule_id, session
            )

            # Update workflow
            workflow.status = status
            workflow.completed_at = datetime.now(timezone.utc)
            workflow.final_output = final_output
            workflow.dag_definition = dag_definition
            workflow.aggregated_attribution = aggregated

            await session.commit()

            duration = workflow.get_duration_seconds()

            logger.info(
                f"Completed workflow {workflow_capsule_id} with status {status}"
            )

            return {
                "success": True,
                "workflow_capsule_id": workflow_capsule_id,
                "status": status,
                "step_count": workflow.step_count,
                "duration_seconds": duration,
            }

        except Exception as e:
            logger.error(f"Failed to complete workflow: {e}")
            await session.rollback()
            return {"success": False, "error": str(e)}

    def create_workflow_step_capsule(
        self,
        workflow_capsule_id: str,
        step_index: int,
        step_type: str,
        step_name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        depends_on_steps: Optional[List[int]] = None,
        tool_name: Optional[str] = None,
        model_id: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        confidence: Optional[float] = None,
    ) -> WorkflowStepCapsule:
        """
        Create a UATP capsule for a workflow step.

        Args:
            All workflow step parameters

        Returns:
            WorkflowStepCapsule instance
        """
        payload = WorkflowStepPayload(
            workflow_capsule_id=workflow_capsule_id,
            step_index=step_index,
            step_type=step_type,
            step_name=step_name,
            input_data=input_data,
            output_data=output_data,
            depends_on_steps=depends_on_steps,
            tool_name=tool_name,
            model_id=model_id,
            execution_time_ms=execution_time_ms,
            confidence=confidence,
        )

        capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        # SECURITY: Return capsule with DRAFT status - signature must be added by caller
        # Capsules without valid signatures should NOT be marked as SEALED
        # The placeholder signature clearly indicates this capsule requires proper signing
        return WorkflowStepCapsule(
            capsule_id=capsule_id,
            version="7.2",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,  # Not SEALED until properly signed
            verification=Verification(
                signature="ed25519:"
                + "0" * 128,  # Placeholder - must be replaced by signing service
                merkle_root="sha256:" + "0" * 64,  # Placeholder - must be computed
            ),
            workflow_step=payload,
        )

    def create_workflow_complete_capsule(
        self,
        workflow_capsule_id: str,
        workflow_name: str,
        workflow_type: str,
        step_capsule_ids: List[str],
        started_at: datetime,
        completed_at: datetime,
        aggregated_attribution: Optional[Dict[str, Any]] = None,
        dag_definition: Optional[Dict[str, Any]] = None,
        final_output: Optional[Dict[str, Any]] = None,
        status: str = "completed",
    ) -> WorkflowCompleteCapsule:
        """
        Create a UATP capsule for workflow completion.

        Args:
            All workflow completion parameters

        Returns:
            WorkflowCompleteCapsule instance
        """
        payload = WorkflowCompletePayload(
            workflow_capsule_id=workflow_capsule_id,
            workflow_name=workflow_name,
            workflow_type=workflow_type,
            total_steps=len(step_capsule_ids),
            step_capsule_ids=step_capsule_ids,
            aggregated_attribution=aggregated_attribution,
            dag_definition=dag_definition,
            started_at=started_at,
            completed_at=completed_at,
            final_output=final_output,
            status=status,
        )

        capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        # SECURITY: Return capsule with DRAFT status - signature must be added by caller
        # Capsules without valid signatures should NOT be marked as SEALED
        # The placeholder signature clearly indicates this capsule requires proper signing
        return WorkflowCompleteCapsule(
            capsule_id=capsule_id,
            version="7.2",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,  # Not SEALED until properly signed
            verification=Verification(
                signature="ed25519:"
                + "0" * 128,  # Placeholder - must be replaced by signing service
                merkle_root="sha256:" + "0" * 64,  # Placeholder - must be computed
            ),
            workflow_complete=payload,
        )


# Global service instance
workflow_chain_service = WorkflowChainService()
