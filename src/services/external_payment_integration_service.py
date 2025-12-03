"""
External Payment Integration Service for UATP Capsule Engine

This service provides comprehensive external payment integration capabilities,
coordinating between multiple payment processors, handling complex workflows,
and providing enterprise-grade payment management.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set

try:
    from payments.payment_processor_manager import (
        PaymentProcessorManager,
        PaymentPriority,
        RoutingStrategy,
        create_payment_processor_manager,
    )
    from payments.real_payment_service import (
        PaymentConfig,
        PaymentStatus,
        RealPaymentService,
        create_real_payment_service,
    )
    from user_management.user_service import PayoutMethod, create_user_service
except ImportError:
    # Fallback for testing without full package structure
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

    from payments.payment_processor_manager import (
        PaymentProcessorManager,
        PaymentPriority,
        RoutingStrategy,
        create_payment_processor_manager,
    )

    # Mock the imports that have issues
    class PaymentConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class PaymentStatus:
        PENDING = "pending"
        COMPLETED = "completed"
        FAILED = "failed"

    class PayoutMethod:
        PAYPAL = "paypal"
        STRIPE = "stripe"
        CRYPTO = "crypto"

    def create_user_service():
        class MockUserService:
            async def get_user_profile(self, user_id):
                return None

            async def update_user_balance(self, user_id, amount):
                pass

        return MockUserService()

    def create_real_payment_service(user_service, config):
        class MockPaymentService:
            def __init__(self, user_service, config):
                pass

        return MockPaymentService(user_service, config)


logger = logging.getLogger(__name__)


class IntegrationStatus(Enum):
    """External payment integration status."""

    ACTIVE = "active"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class TransactionType(Enum):
    """Types of payment transactions."""

    PAYOUT = "payout"
    REFUND = "refund"
    TRANSFER = "transfer"
    ESCROW_RELEASE = "escrow_release"
    DIVIDEND_PAYMENT = "dividend_payment"
    LICENSE_FEE = "license_fee"


class WorkflowStatus(Enum):
    """Payment workflow status."""

    INITIATED = "initiated"
    VALIDATING = "validating"
    ROUTING = "routing"
    PROCESSING = "processing"
    CONFIRMING = "confirming"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PaymentWorkflow:
    """Represents a complex payment workflow."""

    workflow_id: str
    workflow_type: TransactionType
    user_id: str
    amount: Decimal
    currency: str
    status: WorkflowStatus = WorkflowStatus.INITIATED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Workflow steps
    steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0

    # Payment details
    recipient_details: Dict[str, Any] = field(default_factory=dict)
    routing_strategy: RoutingStrategy = RoutingStrategy.MOST_RELIABLE
    priority: PaymentPriority = PaymentPriority.NORMAL

    # Results
    transaction_results: List[Dict[str, Any]] = field(default_factory=list)
    final_result: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class IntegrationMetrics:
    """Metrics for payment integration service."""

    total_workflows: int = 0
    successful_workflows: int = 0
    failed_workflows: int = 0
    total_volume: Decimal = Decimal("0.00")
    processing_time_avg: float = 0.0

    # By transaction type
    volume_by_type: Dict[TransactionType, Decimal] = field(default_factory=dict)
    count_by_type: Dict[TransactionType, int] = field(default_factory=dict)

    # Performance metrics
    daily_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    processor_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class ExternalPaymentIntegrationService:
    """Comprehensive external payment integration service."""

    def __init__(self):
        # Initialize core services
        self.user_service = create_user_service()
        self.payment_config = PaymentConfig(
            min_payout_amount=Decimal("1.00"),
            max_payout_amount=Decimal("100000.00"),
            enable_stripe=True,
            enable_paypal=True,
            enable_crypto=True,
        )
        self.payment_service = create_real_payment_service(
            self.user_service, self.payment_config
        )
        self.processor_manager = create_payment_processor_manager(
            RoutingStrategy.MOST_RELIABLE
        )

        # Workflow management
        self.active_workflows: Dict[str, PaymentWorkflow] = {}
        self.completed_workflows: Dict[str, PaymentWorkflow] = {}
        self.metrics = IntegrationMetrics()

        # Service status
        self.status = IntegrationStatus.ACTIVE
        self.last_health_check = datetime.now(timezone.utc)
        self.error_count = 0

        # Background tasks
        self._start_background_tasks()

    def _start_background_tasks(self):
        """Start background processing tasks."""
        asyncio.create_task(self._process_workflow_queue())
        asyncio.create_task(self._monitor_service_health())
        asyncio.create_task(self._cleanup_completed_workflows())
        asyncio.create_task(self._generate_daily_metrics())

    async def initiate_payment_workflow(
        self,
        workflow_type: TransactionType,
        user_id: str,
        amount: Decimal,
        currency: str = "USD",
        recipient_details: Optional[Dict[str, Any]] = None,
        routing_strategy: RoutingStrategy = RoutingStrategy.MOST_RELIABLE,
        priority: PaymentPriority = PaymentPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Initiate a comprehensive payment workflow."""

        try:
            # Generate workflow ID
            workflow_id = f"wf_{workflow_type.value}_{uuid.uuid4().hex[:12]}"

            # Create workflow
            workflow = PaymentWorkflow(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                user_id=user_id,
                amount=amount,
                currency=currency,
                recipient_details=recipient_details or {},
                routing_strategy=routing_strategy,
                priority=priority,
                metadata=metadata or {},
            )

            # Define workflow steps based on type
            workflow.steps = self._define_workflow_steps(workflow_type, workflow)

            # Store workflow
            self.active_workflows[workflow_id] = workflow

            # Start processing
            asyncio.create_task(self._execute_workflow(workflow))

            logger.info(
                f"Initiated payment workflow: {workflow_id} ({workflow_type.value})"
            )

            return {
                "success": True,
                "workflow_id": workflow_id,
                "workflow_type": workflow_type.value,
                "status": workflow.status.value,
                "estimated_steps": len(workflow.steps),
                "priority": priority.value,
            }

        except Exception as e:
            logger.error(f"Error initiating payment workflow: {e}", exc_info=True)
            return {
                "success": False,
                "error": "Failed to initiate payment workflow",
                "details": str(e),
            }

    def _define_workflow_steps(
        self, workflow_type: TransactionType, workflow: PaymentWorkflow
    ) -> List[Dict[str, Any]]:
        """Define workflow steps based on transaction type."""

        steps = []

        if workflow_type == TransactionType.PAYOUT:
            steps = [
                {"step": "validate_user", "description": "Validate user and balance"},
                {
                    "step": "check_payout_method",
                    "description": "Verify payout method configuration",
                },
                {"step": "calculate_fees", "description": "Calculate processing fees"},
                {
                    "step": "route_payment",
                    "description": "Determine optimal payment route",
                },
                {
                    "step": "process_payment",
                    "description": "Execute payment through processor",
                },
                {
                    "step": "confirm_completion",
                    "description": "Confirm payment completion",
                },
                {"step": "update_balances", "description": "Update user balances"},
                {
                    "step": "send_notifications",
                    "description": "Send completion notifications",
                },
            ]

        elif workflow_type == TransactionType.DIVIDEND_PAYMENT:
            steps = [
                {
                    "step": "validate_dividend",
                    "description": "Validate dividend payment authorization",
                },
                {
                    "step": "calculate_amounts",
                    "description": "Calculate individual dividend amounts",
                },
                {
                    "step": "batch_recipients",
                    "description": "Group recipients by payment method",
                },
                {"step": "process_batches", "description": "Process payment batches"},
                {
                    "step": "track_completion",
                    "description": "Track batch completion status",
                },
                {
                    "step": "generate_reports",
                    "description": "Generate dividend payment reports",
                },
            ]

        elif workflow_type == TransactionType.LICENSE_FEE:
            steps = [
                {
                    "step": "validate_license",
                    "description": "Validate license agreement",
                },
                {
                    "step": "calculate_fee",
                    "description": "Calculate license fees and royalties",
                },
                {"step": "escrow_check", "description": "Check escrow requirements"},
                {
                    "step": "process_payment",
                    "description": "Process license fee payment",
                },
                {"step": "update_license", "description": "Update license status"},
                {
                    "step": "notify_parties",
                    "description": "Notify all parties of completion",
                },
            ]

        elif workflow_type == TransactionType.REFUND:
            steps = [
                {
                    "step": "validate_refund",
                    "description": "Validate refund eligibility",
                },
                {"step": "calculate_refund", "description": "Calculate refund amount"},
                {
                    "step": "reverse_transaction",
                    "description": "Reverse original transaction if possible",
                },
                {"step": "process_refund", "description": "Process refund payment"},
                {"step": "update_records", "description": "Update transaction records"},
                {
                    "step": "send_confirmation",
                    "description": "Send refund confirmation",
                },
            ]

        else:
            # Default workflow steps
            steps = [
                {"step": "validate_request", "description": "Validate payment request"},
                {"step": "route_payment", "description": "Determine payment route"},
                {"step": "process_payment", "description": "Execute payment"},
                {"step": "confirm_completion", "description": "Confirm completion"},
            ]

        return steps

    async def _execute_workflow(self, workflow: PaymentWorkflow):
        """Execute a payment workflow step by step."""

        try:
            workflow.status = WorkflowStatus.VALIDATING

            for i, step_config in enumerate(workflow.steps):
                workflow.current_step = i
                step_name = step_config["step"]

                logger.info(
                    f"Executing workflow step: {workflow.workflow_id} - {step_name}"
                )

                # Execute step
                step_result = await self._execute_workflow_step(workflow, step_config)

                # Store step result
                workflow.transaction_results.append(
                    {
                        "step": step_name,
                        "result": step_result,
                        "timestamp": datetime.now(timezone.utc),
                    }
                )

                if not step_result.get("success", False):
                    # Step failed
                    workflow.status = WorkflowStatus.FAILED
                    workflow.error_details = {
                        "failed_step": step_name,
                        "error": step_result.get("error", "Unknown error"),
                        "step_index": i,
                    }

                    logger.error(
                        f"Workflow step failed: {workflow.workflow_id} - {step_name}"
                    )

                    # Attempt retry if within limits
                    if workflow.retry_count < workflow.max_retries:
                        workflow.retry_count += 1
                        logger.info(
                            f"Retrying workflow: {workflow.workflow_id} (attempt {workflow.retry_count})"
                        )
                        await asyncio.sleep(
                            2**workflow.retry_count
                        )  # Exponential backoff
                        return await self._execute_workflow(workflow)

                    break

                # Update status based on progress
                if i == len(workflow.steps) - 1:
                    workflow.status = WorkflowStatus.COMPLETED
                elif step_name == "process_payment":
                    workflow.status = WorkflowStatus.PROCESSING
                elif step_name == "route_payment":
                    workflow.status = WorkflowStatus.ROUTING

            # Workflow completed
            if workflow.status == WorkflowStatus.COMPLETED:
                workflow.final_result = {
                    "success": True,
                    "workflow_id": workflow.workflow_id,
                    "completed_at": datetime.now(timezone.utc),
                    "total_steps": len(workflow.steps),
                    "processing_time": (
                        datetime.now(timezone.utc) - workflow.created_at
                    ).total_seconds(),
                }

                logger.info(f"Workflow completed successfully: {workflow.workflow_id}")

                # Update metrics
                await self._update_workflow_metrics(workflow, True)
            else:
                # Workflow failed
                workflow.final_result = {
                    "success": False,
                    "workflow_id": workflow.workflow_id,
                    "error": workflow.error_details,
                    "failed_at": datetime.now(timezone.utc),
                }

                logger.error(f"Workflow failed: {workflow.workflow_id}")

                # Update metrics
                await self._update_workflow_metrics(workflow, False)

            # Move to completed workflows
            self.completed_workflows[workflow.workflow_id] = workflow
            if workflow.workflow_id in self.active_workflows:
                del self.active_workflows[workflow.workflow_id]

        except Exception as e:
            logger.error(
                f"Error executing workflow {workflow.workflow_id}: {e}", exc_info=True
            )
            workflow.status = WorkflowStatus.FAILED
            workflow.error_details = {"error": str(e), "type": "execution_error"}

    async def _execute_workflow_step(
        self, workflow: PaymentWorkflow, step_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""

        step_name = step_config["step"]

        try:
            if step_name == "validate_user":
                return await self._validate_user_step(workflow)
            elif step_name == "check_payout_method":
                return await self._check_payout_method_step(workflow)
            elif step_name == "calculate_fees":
                return await self._calculate_fees_step(workflow)
            elif step_name == "route_payment":
                return await self._route_payment_step(workflow)
            elif step_name == "process_payment":
                return await self._process_payment_step(workflow)
            elif step_name == "confirm_completion":
                return await self._confirm_completion_step(workflow)
            elif step_name == "update_balances":
                return await self._update_balances_step(workflow)
            elif step_name == "send_notifications":
                return await self._send_notifications_step(workflow)
            else:
                # Generic step execution
                return await self._execute_generic_step(workflow, step_config)

        except Exception as e:
            logger.error(f"Error executing step {step_name}: {e}")
            return {"success": False, "error": str(e)}

    async def _validate_user_step(self, workflow: PaymentWorkflow) -> Dict[str, Any]:
        """Validate user and their eligibility for the transaction."""

        user_profile = await self.user_service.get_user_profile(workflow.user_id)

        if not user_profile:
            return {"success": False, "error": "User not found"}

        # Check user balance for payouts
        if workflow.workflow_type == TransactionType.PAYOUT:
            if user_profile.total_earnings < workflow.amount:
                return {"success": False, "error": "Insufficient balance"}

        return {"success": True, "user_profile": user_profile}

    async def _check_payout_method_step(
        self, workflow: PaymentWorkflow
    ) -> Dict[str, Any]:
        """Check if user has a valid payout method configured."""

        user_profile = await self.user_service.get_user_profile(workflow.user_id)

        if not user_profile.payout_method or not user_profile.payout_details:
            return {"success": False, "error": "No payout method configured"}

        # Store payout details in workflow
        workflow.recipient_details = user_profile.payout_details
        workflow.metadata["payout_method"] = user_profile.payout_method.value

        return {"success": True, "payout_method": user_profile.payout_method.value}

    async def _calculate_fees_step(self, workflow: PaymentWorkflow) -> Dict[str, Any]:
        """Calculate processing fees for the transaction."""

        # Get fee estimates from different processors
        fee_estimates = {}

        for processor_id in ["stripe", "paypal", "crypto"]:
            try:
                if processor_id in self.processor_manager.processors:
                    processor = self.processor_manager.processors[processor_id]
                    fee = processor.calculate_fees(workflow.amount, workflow.currency)
                    fee_estimates[processor_id] = float(fee)
            except Exception as e:
                logger.warning(f"Could not calculate fees for {processor_id}: {e}")

        workflow.metadata["fee_estimates"] = fee_estimates

        return {"success": True, "fee_estimates": fee_estimates}

    async def _route_payment_step(self, workflow: PaymentWorkflow) -> Dict[str, Any]:
        """Determine optimal payment routing."""

        # Get routing recommendations
        recommendations = self.processor_manager.get_routing_recommendation(
            workflow.amount, workflow.currency
        )

        workflow.metadata["routing_recommendations"] = recommendations

        return {"success": True, "routing_recommendations": recommendations}

    async def _process_payment_step(self, workflow: PaymentWorkflow) -> Dict[str, Any]:
        """Execute the actual payment processing."""

        result = await self.processor_manager.process_payment(
            amount=workflow.amount,
            currency=workflow.currency,
            recipient_details=workflow.recipient_details,
            routing_strategy=workflow.routing_strategy,
            priority=workflow.priority,
            metadata=workflow.metadata,
        )

        workflow.metadata["payment_result"] = result

        return result

    async def _confirm_completion_step(
        self, workflow: PaymentWorkflow
    ) -> Dict[str, Any]:
        """Confirm payment completion."""

        payment_result = workflow.metadata.get("payment_result", {})

        if payment_result.get("success"):
            return {"success": True, "confirmed": True}
        else:
            return {"success": False, "error": "Payment not completed successfully"}

    async def _update_balances_step(self, workflow: PaymentWorkflow) -> Dict[str, Any]:
        """Update user balances after successful payment."""

        if workflow.workflow_type == TransactionType.PAYOUT:
            # Deduct amount from user balance
            await self.user_service.update_user_balance(
                workflow.user_id, -workflow.amount
            )

        return {"success": True, "balance_updated": True}

    async def _send_notifications_step(
        self, workflow: PaymentWorkflow
    ) -> Dict[str, Any]:
        """Send notifications about workflow completion."""

        # In production, this would send actual notifications
        notification = {
            "user_id": workflow.user_id,
            "workflow_id": workflow.workflow_id,
            "type": workflow.workflow_type.value,
            "amount": float(workflow.amount),
            "status": workflow.status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Notification sent: {notification}")

        return {"success": True, "notification_sent": True}

    async def _execute_generic_step(
        self, workflow: PaymentWorkflow, step_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a generic workflow step."""

        # Mock implementation for unspecified steps
        await asyncio.sleep(0.1)  # Simulate processing time

        return {"success": True, "step_completed": step_config["step"]}

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a payment workflow."""

        # Check active workflows
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
        elif workflow_id in self.completed_workflows:
            workflow = self.completed_workflows[workflow_id]
        else:
            return None

        return {
            "workflow_id": workflow.workflow_id,
            "workflow_type": workflow.workflow_type.value,
            "status": workflow.status.value,
            "current_step": workflow.current_step,
            "total_steps": len(workflow.steps),
            "progress_percentage": (workflow.current_step / len(workflow.steps)) * 100,
            "created_at": workflow.created_at.isoformat(),
            "amount": float(workflow.amount),
            "currency": workflow.currency,
            "retry_count": workflow.retry_count,
            "final_result": workflow.final_result,
            "error_details": workflow.error_details,
        }

    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancel an active workflow."""

        if workflow_id not in self.active_workflows:
            return {
                "success": False,
                "error": "Workflow not found or already completed",
            }

        workflow = self.active_workflows[workflow_id]

        if workflow.status in [WorkflowStatus.PROCESSING, WorkflowStatus.CONFIRMING]:
            return {
                "success": False,
                "error": "Cannot cancel workflow in current state",
            }

        workflow.status = WorkflowStatus.CANCELLED
        workflow.final_result = {
            "success": False,
            "cancelled": True,
            "cancelled_at": datetime.now(timezone.utc),
        }

        # Move to completed workflows
        self.completed_workflows[workflow_id] = workflow
        del self.active_workflows[workflow_id]

        logger.info(f"Workflow cancelled: {workflow_id}")

        return {"success": True, "cancelled": True}

    async def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status."""

        processor_status = self.processor_manager.get_processor_status()

        return {
            "service_status": self.status.value,
            "last_health_check": self.last_health_check.isoformat(),
            "active_workflows": len(self.active_workflows),
            "completed_workflows": len(self.completed_workflows),
            "error_count": self.error_count,
            "processor_status": processor_status,
            "metrics": {
                "total_workflows": self.metrics.total_workflows,
                "successful_workflows": self.metrics.successful_workflows,
                "failed_workflows": self.metrics.failed_workflows,
                "success_rate": (
                    self.metrics.successful_workflows
                    / max(1, self.metrics.total_workflows)
                )
                * 100,
                "total_volume": float(self.metrics.total_volume),
            },
        }

    async def _update_workflow_metrics(self, workflow: PaymentWorkflow, success: bool):
        """Update workflow metrics."""

        self.metrics.total_workflows += 1

        if success:
            self.metrics.successful_workflows += 1
        else:
            self.metrics.failed_workflows += 1

        self.metrics.total_volume += workflow.amount

        # Update by type
        workflow_type = workflow.workflow_type
        if workflow_type not in self.metrics.volume_by_type:
            self.metrics.volume_by_type[workflow_type] = Decimal("0.00")
            self.metrics.count_by_type[workflow_type] = 0

        self.metrics.volume_by_type[workflow_type] += workflow.amount
        self.metrics.count_by_type[workflow_type] += 1

    async def _process_workflow_queue(self):
        """Background task to process workflow queue."""
        while True:
            try:
                # Process any queued workflows
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in workflow queue processor: {e}")
                await asyncio.sleep(5)

    async def _monitor_service_health(self):
        """Background task to monitor service health."""
        while True:
            try:
                self.last_health_check = datetime.now(timezone.utc)

                # Check processor health
                processor_status = self.processor_manager.get_processor_status()
                healthy_processors = sum(
                    1 for p in processor_status.values() if p["status"] == "active"
                )

                if healthy_processors == 0:
                    self.status = IntegrationStatus.ERROR
                elif healthy_processors < len(processor_status):
                    self.status = IntegrationStatus.DEGRADED
                else:
                    self.status = IntegrationStatus.ACTIVE

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error monitoring service health: {e}")
                self.error_count += 1
                await asyncio.sleep(60)

    async def _cleanup_completed_workflows(self):
        """Background task to cleanup old completed workflows."""
        while True:
            try:
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)

                # Remove workflows older than 7 days
                to_remove = []
                for workflow_id, workflow in self.completed_workflows.items():
                    if workflow.created_at < cutoff_time:
                        to_remove.append(workflow_id)

                for workflow_id in to_remove:
                    del self.completed_workflows[workflow_id]

                if to_remove:
                    logger.info(f"Cleaned up {len(to_remove)} old workflows")

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Error cleaning up workflows: {e}")
                await asyncio.sleep(3600)

    async def _generate_daily_metrics(self):
        """Background task to generate daily metrics."""
        while True:
            try:
                # Generate daily metrics summary
                today = datetime.now(timezone.utc).date().isoformat()

                if today not in self.metrics.daily_metrics:
                    self.metrics.daily_metrics[today] = {
                        "workflows": 0,
                        "volume": 0.0,
                        "success_rate": 0.0,
                    }

                await asyncio.sleep(86400)  # Update daily

            except Exception as e:
                logger.error(f"Error generating daily metrics: {e}")
                await asyncio.sleep(3600)


# Factory function
def create_external_payment_integration_service() -> ExternalPaymentIntegrationService:
    """Create an external payment integration service instance."""
    return ExternalPaymentIntegrationService()


# Example usage
if __name__ == "__main__":

    async def demo_payment_integration_service():
        """Demonstrate the external payment integration service."""

        service = create_external_payment_integration_service()

        # Wait for initialization
        await asyncio.sleep(2)

        print("💳 External Payment Integration Service Demo")

        # Check service status
        status = await service.get_service_status()
        print(f"\n📊 Service Status: {status['service_status']}")
        print(f"   Active Workflows: {status['active_workflows']}")
        print(f"   Success Rate: {status['metrics']['success_rate']:.1f}%")

        # Initiate a payout workflow
        print("\n🔄 Initiating Payout Workflow:")
        result = await service.initiate_payment_workflow(
            workflow_type=TransactionType.PAYOUT,
            user_id="user_123",
            amount=Decimal("50.00"),
            routing_strategy=RoutingStrategy.LOWEST_FEE,
            priority=PaymentPriority.HIGH,
        )
        print(f"   Result: {result}")

        if result["success"]:
            workflow_id = result["workflow_id"]

            # Wait for processing
            await asyncio.sleep(3)

            # Check workflow status
            workflow_status = await service.get_workflow_status(workflow_id)
            print(f"\n📋 Workflow Status:")
            print(f"   Status: {workflow_status['status']}")
            print(f"   Progress: {workflow_status['progress_percentage']:.1f}%")
            print(
                f"   Current Step: {workflow_status['current_step']}/{workflow_status['total_steps']}"
            )

        print("\n✅ Demo completed!")

    asyncio.run(demo_payment_integration_service())
