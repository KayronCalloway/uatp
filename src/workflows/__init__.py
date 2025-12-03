"""
Workflow Automation Package
===========================

This package provides comprehensive workflow automation capabilities for the
UATP Capsule Engine, enabling complex business processes to be defined,
executed, and monitored across multiple services.

Components:
- WorkflowEngine: Core workflow execution engine
- PredefinedWorkflows: Common business process definitions
- WorkflowServices: Service implementations for workflow steps
"""

from .workflow_engine import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowCondition,
    WorkflowExecution,
    WorkflowStatus,
    StepStatus,
    ConditionOperator,
    get_workflow_engine,
    initialize_workflow_engine,
)

from .predefined_workflows import PredefinedWorkflows, register_predefined_workflows

from .workflow_services import (
    ValidationService,
    RiskAssessmentService,
    ComplianceService,
    AnalyticsService,
    NotificationService,
    ValidationResult,
    EligibilityResult,
    ComplianceResult,
    PerformanceData,
)

__all__ = [
    # Core workflow engine
    "WorkflowEngine",
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowCondition",
    "WorkflowExecution",
    "WorkflowStatus",
    "StepStatus",
    "ConditionOperator",
    "get_workflow_engine",
    "initialize_workflow_engine",
    # Predefined workflows
    "PredefinedWorkflows",
    "register_predefined_workflows",
    # Workflow services
    "ValidationService",
    "RiskAssessmentService",
    "ComplianceService",
    "AnalyticsService",
    "NotificationService",
    # Data structures
    "ValidationResult",
    "EligibilityResult",
    "ComplianceResult",
    "PerformanceData",
]
