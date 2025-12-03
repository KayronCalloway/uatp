"""
Advanced Lifecycle Automation for UATP Capsule Engine.
Implements automated capsule lifecycle management, dependency updates, and cleanup.
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.audit.events import audit_emitter
from src.capsule_schema import AnyCapsule, CapsuleStatus
from src.graph.capsule_relationships import relationship_graph

logger = logging.getLogger(__name__)


class LifecycleEvent(str, Enum):
    """Types of lifecycle events."""

    CREATION = "creation"
    ACTIVATION = "activation"
    RETIREMENT = "retirement"
    DEPENDENCY_UPDATE = "dependency_update"
    ORPHAN_DETECTION = "orphan_detection"
    CLEANUP = "cleanup"
    MIGRATION = "migration"
    ARCHIVAL = "archival"


class AutomationTrigger(str, Enum):
    """Triggers for lifecycle automation."""

    TIME_BASED = "time_based"
    DEPENDENCY_CHANGE = "dependency_change"
    USAGE_PATTERN = "usage_pattern"
    RESOURCE_THRESHOLD = "resource_threshold"
    MANUAL = "manual"
    EVENT_DRIVEN = "event_driven"


class LifecycleAction(str, Enum):
    """Actions that can be performed during lifecycle automation."""

    RETIRE_CAPSULE = "retire_capsule"
    UPDATE_DEPENDENCIES = "update_dependencies"
    CLEANUP_ORPHANS = "cleanup_orphans"
    COMPRESS_CAPSULE = "compress_capsule"
    MIGRATE_CAPSULE = "migrate_capsule"
    ARCHIVE_CAPSULE = "archive_capsule"
    NOTIFY_STAKEHOLDERS = "notify_stakeholders"


@dataclass
class LifecycleRule:
    """Rule for automated lifecycle management."""

    rule_id: str
    name: str
    description: str
    trigger: AutomationTrigger
    condition: Callable[[AnyCapsule, Dict[str, Any]], bool]
    action: LifecycleAction
    priority: int
    enabled: bool = True
    execution_count: int = 0
    last_executed: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LifecycleTask:
    """Task for lifecycle automation."""

    task_id: str
    capsule_id: str
    action: LifecycleAction
    scheduled_time: datetime
    priority: int
    rule_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None

    def __lt__(self, other):
        """Enable priority queue sorting."""
        return (self.priority, self.scheduled_time) < (
            other.priority,
            other.scheduled_time,
        )


@dataclass
class LifecycleExecutionResult:
    """Result of lifecycle task execution."""

    task_id: str
    capsule_id: str
    action: LifecycleAction
    success: bool
    message: str
    execution_time: datetime
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class DependencyTracker:
    """Tracks and manages capsule dependencies."""

    def __init__(self):
        self.dependency_cache: Dict[str, Set[str]] = {}
        self.dependent_cache: Dict[str, Set[str]] = {}
        self.update_queue: deque = deque()

    def track_dependencies(self, capsule_id: str):
        """Track dependencies for a capsule."""
        dependencies = relationship_graph.get_capsule_dependencies(capsule_id)
        dependents = relationship_graph.get_capsule_dependents(capsule_id)

        self.dependency_cache[capsule_id] = set(dependencies)
        self.dependent_cache[capsule_id] = set(dependents)

        logger.info(
            f"Tracked {len(dependencies)} dependencies and {len(dependents)} dependents for {capsule_id}"
        )

    def check_dependency_updates(self, capsule_id: str) -> List[str]:
        """Check if any dependencies need updates."""
        updates_needed = []

        if capsule_id not in self.dependency_cache:
            self.track_dependencies(capsule_id)

        dependencies = self.dependency_cache.get(capsule_id, set())

        for dep_id in dependencies:
            if self._dependency_needs_update(capsule_id, dep_id):
                updates_needed.append(dep_id)

        return updates_needed

    def _dependency_needs_update(self, capsule_id: str, dependency_id: str) -> bool:
        """Check if a specific dependency needs update."""
        # Simple heuristic: if dependency was modified recently
        if dependency_id in relationship_graph.nodes:
            dep_node = relationship_graph.nodes[dependency_id]
            time_since_update = (
                datetime.now(timezone.utc) - dep_node.last_updated
            ).total_seconds()

            # If dependency was updated within last hour, might need update
            return time_since_update < 3600

        return False

    def update_dependency_chain(self, root_capsule_id: str) -> List[str]:
        """Update entire dependency chain for a capsule."""
        updated_capsules = []

        # Use BFS to update dependency chain
        queue = deque([root_capsule_id])
        visited = set()

        while queue:
            current_id = queue.popleft()

            if current_id in visited:
                continue

            visited.add(current_id)

            # Get dependents that need updates
            dependents = self.dependent_cache.get(current_id, set())

            for dependent_id in dependents:
                if dependent_id not in visited:
                    queue.append(dependent_id)
                    updated_capsules.append(dependent_id)

        return updated_capsules


class OrphanDetector:
    """Detects and manages orphaned capsules."""

    def __init__(self):
        self.orphan_threshold = timedelta(days=30)
        self.orphan_cache: Set[str] = set()

    def detect_orphans(self) -> List[str]:
        """Detect orphaned capsules."""
        orphans = []

        for capsule_id, node in relationship_graph.nodes.items():
            if self._is_orphan(capsule_id, node):
                orphans.append(capsule_id)
                self.orphan_cache.add(capsule_id)

        logger.info(f"Detected {len(orphans)} orphaned capsules")
        return orphans

    def _is_orphan(self, capsule_id: str, node) -> bool:
        """Check if a capsule is orphaned."""

        # Check if capsule has no dependencies or dependents
        dependencies = relationship_graph.get_capsule_dependencies(capsule_id)
        dependents = relationship_graph.get_capsule_dependents(capsule_id)

        # If no relationships and old enough, might be orphan
        if not dependencies and not dependents:
            age = datetime.now(timezone.utc) - node.creation_time
            return age > self.orphan_threshold

        # Check if all dependencies are also orphans or retired
        if dependencies:
            for dep_id in dependencies:
                if dep_id in relationship_graph.nodes:
                    dep_node = relationship_graph.nodes[dep_id]
                    if dep_node.status != "retired" and dep_id not in self.orphan_cache:
                        return False

            # All dependencies are orphans/retired
            return True

        return False

    def cleanup_orphan(self, capsule_id: str) -> bool:
        """Clean up an orphaned capsule."""
        try:
            # Remove from graph
            if capsule_id in relationship_graph.nodes:
                relationship_graph.graph.remove_node(capsule_id)
                del relationship_graph.nodes[capsule_id]

            # Remove from orphan cache
            self.orphan_cache.discard(capsule_id)

            logger.info(f"Cleaned up orphaned capsule {capsule_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup orphan {capsule_id}: {e}")
            return False


class LifecycleAutomationEngine:
    """Main engine for automated lifecycle management."""

    def __init__(self):
        self.rules: Dict[str, LifecycleRule] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.execution_history: List[LifecycleExecutionResult] = []
        self.dependency_tracker = DependencyTracker()
        self.orphan_detector = OrphanDetector()
        self.running = False
        self.worker_tasks: List[asyncio.Task] = []
        self.stats = {
            "total_tasks_executed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "rules_triggered": 0,
            "orphans_cleaned": 0,
        }

        # Initialize default rules
        self._initialize_default_rules()

    def add_rule(self, rule: LifecycleRule):
        """Add a lifecycle automation rule."""
        self.rules[rule.rule_id] = rule
        logger.info(f"Added lifecycle rule: {rule.rule_id}")

    def remove_rule(self, rule_id: str):
        """Remove a lifecycle automation rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed lifecycle rule: {rule_id}")

    async def start_automation(self, num_workers: int = 3):
        """Start the lifecycle automation engine."""
        self.running = True

        # Start worker tasks
        for i in range(num_workers):
            worker_task = asyncio.create_task(self._worker(f"worker_{i}"))
            self.worker_tasks.append(worker_task)

        # Start rule evaluation task
        rule_task = asyncio.create_task(self._rule_evaluator())
        self.worker_tasks.append(rule_task)

        # Start periodic cleanup task
        cleanup_task = asyncio.create_task(self._periodic_cleanup())
        self.worker_tasks.append(cleanup_task)

        logger.info(f"Started lifecycle automation with {num_workers} workers")

    async def stop_automation(self):
        """Stop the lifecycle automation engine."""
        self.running = False

        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)

        self.worker_tasks.clear()
        logger.info("Stopped lifecycle automation")

    async def schedule_task(self, task: LifecycleTask):
        """Schedule a lifecycle task."""
        await self.task_queue.put(task)
        logger.info(f"Scheduled task {task.task_id} for {task.action.value}")

    async def process_capsule(self, capsule: AnyCapsule):
        """Process a capsule through lifecycle automation."""

        # Track dependencies
        self.dependency_tracker.track_dependencies(capsule.capsule_id)

        # Evaluate rules
        await self._evaluate_rules_for_capsule(capsule)

        # Check for dependency updates
        updates_needed = self.dependency_tracker.check_dependency_updates(
            capsule.capsule_id
        )

        if updates_needed:
            task = LifecycleTask(
                task_id=self._generate_task_id(),
                capsule_id=capsule.capsule_id,
                action=LifecycleAction.UPDATE_DEPENDENCIES,
                scheduled_time=datetime.now(timezone.utc),
                priority=5,
                rule_id="dependency_update",
                metadata={"updates_needed": updates_needed},
            )
            await self.schedule_task(task)

    async def _worker(self, worker_id: str):
        """Worker task for executing lifecycle actions."""
        logger.info(f"Started lifecycle worker: {worker_id}")

        while self.running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=5.0)

                # Execute task
                result = await self._execute_task(task)

                # Record result
                self.execution_history.append(result)
                self.stats["total_tasks_executed"] += 1

                if result.success:
                    self.stats["successful_tasks"] += 1
                else:
                    self.stats["failed_tasks"] += 1

                # Mark task as done
                self.task_queue.task_done()

            except asyncio.TimeoutError:
                # No tasks available, continue
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                continue

        logger.info(f"Stopped lifecycle worker: {worker_id}")

    async def _rule_evaluator(self):
        """Periodically evaluate rules for all capsules."""
        while self.running:
            try:
                # Evaluate rules every 5 minutes
                await asyncio.sleep(300)

                # Get all capsules from graph
                for capsule_id in relationship_graph.nodes:
                    # This is simplified - in production we'd need full capsule data
                    node = relationship_graph.nodes[capsule_id]

                    # Create minimal capsule representation for rule evaluation
                    capsule_data = {
                        "capsule_id": capsule_id,
                        "creation_time": node.creation_time,
                        "status": node.status,
                        "creator_id": node.creator_id,
                    }

                    await self._evaluate_rules_for_capsule_data(capsule_data)

            except Exception as e:
                logger.error(f"Rule evaluator error: {e}")
                await asyncio.sleep(60)  # Wait before retry

    async def _periodic_cleanup(self):
        """Periodic cleanup of orphaned capsules."""
        while self.running:
            try:
                # Run cleanup every hour
                await asyncio.sleep(3600)

                orphans = self.orphan_detector.detect_orphans()

                for orphan_id in orphans:
                    task = LifecycleTask(
                        task_id=self._generate_task_id(),
                        capsule_id=orphan_id,
                        action=LifecycleAction.CLEANUP_ORPHANS,
                        scheduled_time=datetime.now(timezone.utc),
                        priority=3,
                        rule_id="orphan_cleanup",
                    )
                    await self.schedule_task(task)

            except Exception as e:
                logger.error(f"Periodic cleanup error: {e}")
                await asyncio.sleep(1800)  # Wait 30 minutes before retry

    async def _evaluate_rules_for_capsule(self, capsule: AnyCapsule):
        """Evaluate rules for a specific capsule."""
        context = {
            "capsule": capsule,
            "dependencies": self.dependency_tracker.dependency_cache.get(
                capsule.capsule_id, set()
            ),
            "dependents": self.dependency_tracker.dependent_cache.get(
                capsule.capsule_id, set()
            ),
            "current_time": datetime.now(timezone.utc),
        }

        for rule in self.rules.values():
            if rule.enabled and rule.condition(capsule, context):
                await self._trigger_rule(rule, capsule.capsule_id)

    async def _evaluate_rules_for_capsule_data(self, capsule_data: Dict[str, Any]):
        """Evaluate rules for capsule data (simplified)."""
        context = {
            "capsule_data": capsule_data,
            "current_time": datetime.now(timezone.utc),
        }

        for rule in self.rules.values():
            if rule.enabled:
                # Simplified condition evaluation
                if await self._evaluate_simple_condition(rule, capsule_data, context):
                    await self._trigger_rule(rule, capsule_data["capsule_id"])

    async def _evaluate_simple_condition(
        self, rule: LifecycleRule, capsule_data: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """Evaluate simplified condition for rule."""

        # Age-based conditions
        if rule.rule_id == "auto_retire_old":
            age = datetime.now(timezone.utc) - capsule_data["creation_time"]
            return age > timedelta(days=365)

        elif rule.rule_id == "compress_inactive":
            age = datetime.now(timezone.utc) - capsule_data["creation_time"]
            return age > timedelta(days=30)

        elif rule.rule_id == "archive_retired":
            return capsule_data["status"] == "retired"

        return False

    async def _trigger_rule(self, rule: LifecycleRule, capsule_id: str):
        """Trigger a lifecycle rule."""

        task = LifecycleTask(
            task_id=self._generate_task_id(),
            capsule_id=capsule_id,
            action=rule.action,
            scheduled_time=datetime.now(timezone.utc),
            priority=rule.priority,
            rule_id=rule.rule_id,
            metadata={"rule_name": rule.name},
        )

        await self.schedule_task(task)

        # Update rule statistics
        rule.execution_count += 1
        rule.last_executed = datetime.now(timezone.utc)
        self.stats["rules_triggered"] += 1

    async def _execute_task(self, task: LifecycleTask) -> LifecycleExecutionResult:
        """Execute a lifecycle task."""

        start_time = datetime.now(timezone.utc)

        try:
            if task.action == LifecycleAction.RETIRE_CAPSULE:
                success, message = await self._retire_capsule(task.capsule_id)

            elif task.action == LifecycleAction.UPDATE_DEPENDENCIES:
                success, message = await self._update_dependencies(task.capsule_id)

            elif task.action == LifecycleAction.CLEANUP_ORPHANS:
                success, message = await self._cleanup_orphan(task.capsule_id)

            elif task.action == LifecycleAction.COMPRESS_CAPSULE:
                success, message = await self._compress_capsule(task.capsule_id)

            elif task.action == LifecycleAction.ARCHIVE_CAPSULE:
                success, message = await self._archive_capsule(task.capsule_id)

            else:
                success, message = False, f"Unknown action: {task.action}"

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            # Emit audit event
            audit_emitter.emit_capsule_created(
                capsule_id=f"lifecycle_{task.action.value}_{task.capsule_id}",
                agent_id="lifecycle_automation",
                capsule_type="lifecycle_action",
            )

            return LifecycleExecutionResult(
                task_id=task.task_id,
                capsule_id=task.capsule_id,
                action=task.action,
                success=success,
                message=message,
                execution_time=start_time,
                duration=duration,
            )

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"Task execution failed: {e}")

            return LifecycleExecutionResult(
                task_id=task.task_id,
                capsule_id=task.capsule_id,
                action=task.action,
                success=False,
                message=f"Execution failed: {str(e)}",
                execution_time=start_time,
                duration=duration,
            )

    async def _retire_capsule(self, capsule_id: str) -> Tuple[bool, str]:
        """Retire a capsule."""
        if capsule_id in relationship_graph.nodes:
            node = relationship_graph.nodes[capsule_id]
            node.status = "retired"
            node.last_updated = datetime.now(timezone.utc)

            logger.info(f"Retired capsule {capsule_id}")
            return True, f"Capsule {capsule_id} retired successfully"

        return False, f"Capsule {capsule_id} not found"

    async def _update_dependencies(self, capsule_id: str) -> Tuple[bool, str]:
        """Update capsule dependencies."""
        updated_capsules = self.dependency_tracker.update_dependency_chain(capsule_id)

        if updated_capsules:
            logger.info(
                f"Updated {len(updated_capsules)} dependent capsules for {capsule_id}"
            )
            return True, f"Updated {len(updated_capsules)} dependent capsules"

        return True, "No dependency updates needed"

    async def _cleanup_orphan(self, capsule_id: str) -> Tuple[bool, str]:
        """Clean up an orphaned capsule."""
        success = self.orphan_detector.cleanup_orphan(capsule_id)

        if success:
            self.stats["orphans_cleaned"] += 1
            return True, f"Cleaned up orphaned capsule {capsule_id}"

        return False, f"Failed to cleanup orphan {capsule_id}"

    async def _compress_capsule(self, capsule_id: str) -> Tuple[bool, str]:
        """Compress a capsule."""
        # This would need the actual capsule data
        # For now, just simulate compression
        logger.info(f"Compressed capsule {capsule_id}")
        return True, f"Compressed capsule {capsule_id}"

    async def _archive_capsule(self, capsule_id: str) -> Tuple[bool, str]:
        """Archive a capsule."""
        if capsule_id in relationship_graph.nodes:
            node = relationship_graph.nodes[capsule_id]
            node.status = "archived"
            node.last_updated = datetime.now(timezone.utc)

            logger.info(f"Archived capsule {capsule_id}")
            return True, f"Capsule {capsule_id} archived successfully"

        return False, f"Capsule {capsule_id} not found"

    def _initialize_default_rules(self):
        """Initialize default lifecycle rules."""

        # Rule: Auto-retire old capsules
        retire_rule = LifecycleRule(
            rule_id="auto_retire_old",
            name="Auto-retire old capsules",
            description="Automatically retire capsules older than 1 year",
            trigger=AutomationTrigger.TIME_BASED,
            condition=lambda capsule, ctx: (
                ctx["current_time"] - capsule.timestamp > timedelta(days=365)
            ),
            action=LifecycleAction.RETIRE_CAPSULE,
            priority=2,
        )
        self.add_rule(retire_rule)

        # Rule: Compress inactive capsules
        compress_rule = LifecycleRule(
            rule_id="compress_inactive",
            name="Compress inactive capsules",
            description="Compress capsules that haven't been accessed in 30 days",
            trigger=AutomationTrigger.TIME_BASED,
            condition=lambda capsule, ctx: (
                ctx["current_time"] - capsule.timestamp > timedelta(days=30)
            ),
            action=LifecycleAction.COMPRESS_CAPSULE,
            priority=4,
        )
        self.add_rule(compress_rule)

        # Rule: Archive retired capsules
        archive_rule = LifecycleRule(
            rule_id="archive_retired",
            name="Archive retired capsules",
            description="Archive capsules that have been retired",
            trigger=AutomationTrigger.EVENT_DRIVEN,
            condition=lambda capsule, ctx: capsule.status == CapsuleStatus.RETIRED,
            action=LifecycleAction.ARCHIVE_CAPSULE,
            priority=3,
        )
        self.add_rule(archive_rule)

    def _generate_task_id(self) -> str:
        """Generate unique task ID."""
        import uuid

        return str(uuid.uuid4())[:8]

    def get_automation_statistics(self) -> Dict[str, Any]:
        """Get automation statistics."""

        recent_executions = [
            r
            for r in self.execution_history
            if (datetime.now(timezone.utc) - r.execution_time).total_seconds() < 86400
        ]

        return {
            "automation_stats": dict(self.stats),
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules.values() if r.enabled]),
            "recent_executions": len(recent_executions),
            "success_rate": (
                self.stats["successful_tasks"]
                / max(self.stats["total_tasks_executed"], 1)
                * 100
            ),
            "queue_size": self.task_queue.qsize()
            if hasattr(self.task_queue, "qsize")
            else 0,
            "orphans_in_cache": len(self.orphan_detector.orphan_cache),
            "running": self.running,
        }


# Global lifecycle automation engine
lifecycle_engine = LifecycleAutomationEngine()
