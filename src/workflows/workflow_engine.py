"""
Workflow Automation Engine
==========================

This module provides comprehensive workflow automation for the UATP Capsule Engine,
enabling complex business processes to be defined, executed, and monitored across
multiple services.

Features:
- Declarative workflow definitions
- Conditional branching and parallel execution
- Compensation/rollback mechanisms
- Workflow state persistence and recovery
- Real-time monitoring and metrics
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

from src.events.event_system import (
    Event,
    EventType,
    EventBus,
    get_event_bus,
    EventPublisher,
)

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Workflow step execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class ConditionOperator(Enum):
    """Condition operators for workflow branching."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    EXISTS = "exists"
    AND = "and"
    OR = "or"


@dataclass
class WorkflowCondition:
    """Represents a condition for workflow branching."""

    field_path: str
    operator: ConditionOperator
    value: Any = None
    conditions: List["WorkflowCondition"] = field(default_factory=list)

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the condition against workflow context."""
        try:
            if self.operator in [ConditionOperator.AND, ConditionOperator.OR]:
                if self.operator == ConditionOperator.AND:
                    return all(cond.evaluate(context) for cond in self.conditions)
                else:  # OR
                    return any(cond.evaluate(context) for cond in self.conditions)

            # Get field value from context
            field_value = self._get_field_value(context, self.field_path)

            if self.operator == ConditionOperator.EXISTS:
                return field_value is not None
            elif self.operator == ConditionOperator.EQUALS:
                return field_value == self.value
            elif self.operator == ConditionOperator.NOT_EQUALS:
                return field_value != self.value
            elif self.operator == ConditionOperator.GREATER_THAN:
                return float(field_value) > float(self.value)
            elif self.operator == ConditionOperator.LESS_THAN:
                return float(field_value) < float(self.value)
            elif self.operator == ConditionOperator.CONTAINS:
                return self.value in field_value

            return False
        except Exception as e:
            logger.warning(f"Condition evaluation failed: {e}")
            return False

    def _get_field_value(self, context: Dict[str, Any], path: str) -> Any:
        """Get nested field value from context using dot notation."""
        keys = path.split(".")
        value = context
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""

    step_id: str
    name: str
    service_name: str
    method_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[WorkflowCondition] = None
    retry_count: int = 3
    timeout_seconds: int = 300
    parallel_group: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    compensation_step: Optional["WorkflowStep"] = None

    # Execution state
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_attempts: int = 0


@dataclass
class WorkflowDefinition:
    """Defines a complete workflow with steps and configuration."""

    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    timeout_minutes: int = 60
    max_retries: int = 3
    compensation_enabled: bool = True
    variables: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """Represents an executing workflow instance."""

    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    context: Dict[str, Any]
    steps: List[WorkflowStep]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    compensation_executed: bool = False


class WorkflowEngine:
    """Main workflow automation engine."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()
        self.event_publisher = EventPublisher(self.event_bus, "workflow_engine")

        # Workflow storage
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.completed_executions: Dict[str, WorkflowExecution] = {}

        # Service registry
        self.service_registry: Dict[str, Any] = {}

        # Execution control
        self._running = False
        self._execution_tasks: Dict[str, asyncio.Task] = {}

        logger.info("Workflow engine initialized")

    async def start(self):
        """Start the workflow engine."""
        self._running = True
        logger.info("Workflow engine started")

    async def stop(self):
        """Stop the workflow engine."""
        self._running = False

        # Cancel all running executions
        for task in self._execution_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        if self._execution_tasks:
            await asyncio.gather(
                *self._execution_tasks.values(), return_exceptions=True
            )

        logger.info("Workflow engine stopped")

    def register_service(self, service_name: str, service_instance: Any):
        """Register a service for workflow step execution."""
        self.service_registry[service_name] = service_instance
        logger.info(f"Registered service: {service_name}")

    def define_workflow(self, workflow_def: WorkflowDefinition):
        """Register a workflow definition."""
        self.workflow_definitions[workflow_def.workflow_id] = workflow_def
        logger.info(f"Registered workflow: {workflow_def.workflow_id}")

    async def execute_workflow(
        self, workflow_id: str, context: Dict[str, Any] = None
    ) -> str:
        """Execute a workflow and return execution ID."""
        if workflow_id not in self.workflow_definitions:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow_def = self.workflow_definitions[workflow_id]
        execution_id = str(uuid.uuid4())

        # Create execution instance
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            context=context or {},
            steps=[
                WorkflowStep(
                    step_id=step.step_id,
                    name=step.name,
                    service_name=step.service_name,
                    method_name=step.method_name,
                    parameters=step.parameters.copy(),
                    condition=step.condition,
                    retry_count=step.retry_count,
                    timeout_seconds=step.timeout_seconds,
                    parallel_group=step.parallel_group,
                    depends_on=step.depends_on.copy(),
                    compensation_step=step.compensation_step,
                )
                for step in workflow_def.steps
            ],
            created_at=datetime.now(timezone.utc),
        )

        # Initialize context with workflow variables
        execution.context.update(workflow_def.variables)

        self.active_executions[execution_id] = execution

        # Start execution task
        task = asyncio.create_task(self._execute_workflow_async(execution))
        self._execution_tasks[execution_id] = task

        # Publish workflow started event
        await self.event_publisher.publish_workflow_started(
            execution_id=execution_id,
            workflow_id=workflow_id,
            context=execution.context,
        )

        logger.info(f"Started workflow execution: {execution_id}")
        return execution_id

    async def _execute_workflow_async(self, execution: WorkflowExecution):
        """Execute a workflow asynchronously."""
        try:
            execution.status = WorkflowStatus.RUNNING
            execution.started_at = datetime.now(timezone.utc)

            await self.event_publisher.publish_workflow_status_changed(
                execution_id=execution.execution_id,
                status=execution.status.value,
                context=execution.context,
            )

            # Execute workflow steps
            await self._execute_steps(execution)

            if execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.COMPLETED
                execution.completed_at = datetime.now(timezone.utc)

                await self.event_publisher.publish_workflow_completed(
                    execution_id=execution.execution_id,
                    workflow_id=execution.workflow_id,
                    result=execution.context,
                    duration=(
                        execution.completed_at - execution.started_at
                    ).total_seconds(),
                )

                logger.info(f"Workflow execution completed: {execution.execution_id}")

        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now(timezone.utc)

            logger.error(f"Workflow execution failed: {execution.execution_id}: {e}")

            # Execute compensation if enabled
            if self.workflow_definitions[execution.workflow_id].compensation_enabled:
                await self._execute_compensation(execution)

            await self.event_publisher.publish_workflow_failed(
                execution_id=execution.execution_id,
                workflow_id=execution.workflow_id,
                error=str(e),
                context=execution.context,
            )

        finally:
            # Move to completed executions
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]
            self.completed_executions[execution.execution_id] = execution

            # Clean up task reference
            if execution.execution_id in self._execution_tasks:
                del self._execution_tasks[execution.execution_id]

    async def _execute_steps(self, execution: WorkflowExecution):
        """Execute workflow steps with dependency resolution and parallelization."""
        completed_steps = set()
        parallel_groups = {}

        while len(completed_steps) < len(execution.steps):
            # Find steps that can be executed
            ready_steps = []

            for step in execution.steps:
                if step.status == StepStatus.PENDING and all(
                    dep in completed_steps for dep in step.depends_on
                ):
                    # Check condition if present
                    if step.condition and not step.condition.evaluate(
                        execution.context
                    ):
                        step.status = StepStatus.SKIPPED
                        completed_steps.add(step.step_id)
                        continue

                    ready_steps.append(step)

            if not ready_steps:
                # Check if we're waiting on parallel groups
                running_groups = [
                    group for group in parallel_groups.values() if not group.done()
                ]
                if running_groups:
                    # Wait for at least one parallel group to complete
                    done, pending = await asyncio.wait(
                        running_groups, return_when=asyncio.FIRST_COMPLETED
                    )
                    continue
                else:
                    break  # No more steps can be executed

            # Group steps by parallel group
            step_groups = {}
            for step in ready_steps:
                group_key = step.parallel_group or step.step_id
                if group_key not in step_groups:
                    step_groups[group_key] = []
                step_groups[group_key].append(step)

            # Execute step groups
            for group_key, steps in step_groups.items():
                if len(steps) == 1:
                    # Single step execution
                    step = steps[0]
                    await self._execute_step(execution, step)
                    completed_steps.add(step.step_id)
                else:
                    # Parallel execution
                    task = asyncio.create_task(
                        self._execute_parallel_steps(execution, steps)
                    )
                    parallel_groups[group_key] = task

            # Wait for any parallel groups to complete
            if parallel_groups:
                done, pending = await asyncio.wait(
                    parallel_groups.values(), return_when=asyncio.FIRST_COMPLETED
                )

                for task in done:
                    completed_step_ids = await task
                    completed_steps.update(completed_step_ids)

                    # Remove completed task
                    for key, group_task in list(parallel_groups.items()):
                        if group_task == task:
                            del parallel_groups[key]
                            break

    async def _execute_parallel_steps(
        self, execution: WorkflowExecution, steps: List[WorkflowStep]
    ) -> List[str]:
        """Execute steps in parallel."""
        tasks = [self._execute_step(execution, step) for step in steps]
        await asyncio.gather(*tasks, return_exceptions=True)
        return [step.step_id for step in steps]

    async def _execute_step(self, execution: WorkflowExecution, step: WorkflowStep):
        """Execute a single workflow step."""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now(timezone.utc)

        await self.event_publisher.publish_workflow_step_started(
            execution_id=execution.execution_id,
            step_id=step.step_id,
            step_name=step.name,
        )

        try:
            # Get service instance
            if step.service_name not in self.service_registry:
                raise ValueError(f"Service not registered: {step.service_name}")

            service = self.service_registry[step.service_name]

            # Get method
            if not hasattr(service, step.method_name):
                raise ValueError(
                    f"Method not found: {step.service_name}.{step.method_name}"
                )

            method = getattr(service, step.method_name)

            # Prepare parameters with context substitution
            parameters = self._substitute_parameters(step.parameters, execution.context)

            # Execute with timeout
            result = await asyncio.wait_for(
                method(**parameters), timeout=step.timeout_seconds
            )

            step.result = result
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now(timezone.utc)

            # Update context with step result
            execution.context[f"step_{step.step_id}_result"] = result

            await self.event_publisher.publish_workflow_step_completed(
                execution_id=execution.execution_id,
                step_id=step.step_id,
                step_name=step.name,
                result=result,
            )

            logger.info(
                f"Step completed: {step.step_id} in execution {execution.execution_id}"
            )

        except Exception as e:
            step.error = str(e)
            step.retry_attempts += 1

            if step.retry_attempts < step.retry_count:
                step.status = StepStatus.RETRYING
                logger.warning(
                    f"Step failed, retrying: {step.step_id} (attempt {step.retry_attempts})"
                )

                # Wait before retry
                await asyncio.sleep(min(2**step.retry_attempts, 30))

                # Retry the step
                await self._execute_step(execution, step)
            else:
                step.status = StepStatus.FAILED
                step.completed_at = datetime.now(timezone.utc)

                await self.event_publisher.publish_workflow_step_failed(
                    execution_id=execution.execution_id,
                    step_id=step.step_id,
                    step_name=step.name,
                    error=str(e),
                )

                logger.error(
                    f"Step failed: {step.step_id} in execution {execution.execution_id}: {e}"
                )
                raise

    def _substitute_parameters(
        self, parameters: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Substitute context variables in parameters."""
        substituted = {}

        for key, value in parameters.items():
            if (
                isinstance(value, str)
                and value.startswith("${")
                and value.endswith("}")
            ):
                # Context variable substitution
                var_name = value[2:-1]
                substituted[key] = context.get(var_name, value)
            elif isinstance(value, dict):
                substituted[key] = self._substitute_parameters(value, context)
            else:
                substituted[key] = value

        return substituted

    async def _execute_compensation(self, execution: WorkflowExecution):
        """Execute compensation steps for failed workflow."""
        if execution.compensation_executed:
            return

        execution.compensation_executed = True

        logger.info(f"Executing compensation for workflow: {execution.execution_id}")

        # Execute compensation steps in reverse order
        compensation_steps = [
            step
            for step in reversed(execution.steps)
            if step.status == StepStatus.COMPLETED and step.compensation_step
        ]

        for step in compensation_steps:
            try:
                await self._execute_step(execution, step.compensation_step)
            except Exception as e:
                logger.error(
                    f"Compensation step failed: {step.compensation_step.step_id}: {e}"
                )

    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow execution."""
        execution = self.active_executions.get(
            execution_id
        ) or self.completed_executions.get(execution_id)

        if not execution:
            return None

        return {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "created_at": execution.created_at.isoformat(),
            "started_at": execution.started_at.isoformat()
            if execution.started_at
            else None,
            "completed_at": execution.completed_at.isoformat()
            if execution.completed_at
            else None,
            "error": execution.error,
            "compensation_executed": execution.compensation_executed,
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "status": step.status.value,
                    "started_at": step.started_at.isoformat()
                    if step.started_at
                    else None,
                    "completed_at": step.completed_at.isoformat()
                    if step.completed_at
                    else None,
                    "error": step.error,
                    "retry_attempts": step.retry_attempts,
                }
                for step in execution.steps
            ],
        }

    def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get workflow engine metrics."""
        total_executions = len(self.active_executions) + len(self.completed_executions)

        status_counts = {}
        for execution in list(self.active_executions.values()) + list(
            self.completed_executions.values()
        ):
            status = execution.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_workflows": len(self.workflow_definitions),
            "active_executions": len(self.active_executions),
            "completed_executions": len(self.completed_executions),
            "total_executions": total_executions,
            "status_distribution": status_counts,
            "registered_services": len(self.service_registry),
        }


# Global workflow engine instance
_global_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get the global workflow engine instance."""
    global _global_workflow_engine
    if _global_workflow_engine is None:
        _global_workflow_engine = WorkflowEngine()
    return _global_workflow_engine


async def initialize_workflow_engine(
    event_bus: Optional[EventBus] = None,
) -> WorkflowEngine:
    """Initialize the global workflow engine."""
    global _global_workflow_engine
    _global_workflow_engine = WorkflowEngine(event_bus)
    await _global_workflow_engine.start()
    logger.info("Workflow engine initialized and started")
    return _global_workflow_engine
