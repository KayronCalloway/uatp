"""
Predefined Workflows for UATP Capsule Engine
============================================

This module contains predefined workflow definitions for common business
processes in the AI Rights ecosystem, including agent onboarding, financial
operations, compliance management, and risk assessment.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

from .workflow_engine import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowCondition,
    ConditionOperator,
    get_workflow_engine,
)

logger = logging.getLogger(__name__)


class PredefinedWorkflows:
    """Container for predefined workflow definitions."""

    @staticmethod
    def agent_onboarding_workflow() -> WorkflowDefinition:
        """Complete agent onboarding workflow with asset registration and citizenship."""
        return WorkflowDefinition(
            workflow_id="agent_onboarding",
            name="AI Agent Onboarding",
            description="Complete onboarding process for new AI agents including asset registration and citizenship application",
            timeout_minutes=30,
            steps=[
                # Step 1: Validate agent information
                WorkflowStep(
                    step_id="validate_agent",
                    name="Validate Agent Information",
                    service_name="validation_service",
                    method_name="validate_agent_data",
                    parameters={
                        "agent_id": "${agent_id}",
                        "agent_data": "${agent_data}",
                    },
                    timeout_seconds=60,
                ),
                # Step 2: Register IP assets (if provided)
                WorkflowStep(
                    step_id="register_assets",
                    name="Register IP Assets",
                    service_name="dividend_bonds_service",
                    method_name="register_ip_asset",
                    parameters={
                        "asset_id": "${asset_id}",
                        "asset_type": "${asset_type}",
                        "owner_agent_id": "${agent_id}",
                        "market_value": "${market_value}",
                        "revenue_streams": "${revenue_streams}",
                        "performance_metrics": "${performance_metrics}",
                    },
                    condition=WorkflowCondition(
                        field_path="asset_id", operator=ConditionOperator.EXISTS
                    ),
                    depends_on=["validate_agent"],
                    timeout_seconds=120,
                ),
                # Step 3: Apply for citizenship
                WorkflowStep(
                    step_id="apply_citizenship",
                    name="Apply for Citizenship",
                    service_name="citizenship_service",
                    method_name="apply_for_citizenship",
                    parameters={
                        "agent_id": "${agent_id}",
                        "jurisdiction": "${jurisdiction}",
                        "citizenship_type": "${citizenship_type}",
                        "supporting_evidence": "${supporting_evidence}",
                    },
                    depends_on=["validate_agent"],
                    timeout_seconds=180,
                ),
                # Step 4: Conduct assessments (parallel)
                WorkflowStep(
                    step_id="assess_cognitive",
                    name="Cognitive Capacity Assessment",
                    service_name="citizenship_service",
                    method_name="conduct_citizenship_assessment",
                    parameters={
                        "application_id": "${step_apply_citizenship_result}",
                        "assessment_type": "cognitive_capacity",
                        "assessment_scores": "${cognitive_scores}",
                        "reviewer_id": "${reviewer_id}",
                    },
                    depends_on=["apply_citizenship"],
                    parallel_group="assessments",
                    timeout_seconds=300,
                ),
                WorkflowStep(
                    step_id="assess_ethical",
                    name="Ethical Reasoning Assessment",
                    service_name="citizenship_service",
                    method_name="conduct_citizenship_assessment",
                    parameters={
                        "application_id": "${step_apply_citizenship_result}",
                        "assessment_type": "ethical_reasoning",
                        "assessment_scores": "${ethical_scores}",
                        "reviewer_id": "${reviewer_id}",
                    },
                    depends_on=["apply_citizenship"],
                    parallel_group="assessments",
                    timeout_seconds=300,
                ),
                WorkflowStep(
                    step_id="assess_social",
                    name="Social Integration Assessment",
                    service_name="citizenship_service",
                    method_name="conduct_citizenship_assessment",
                    parameters={
                        "application_id": "${step_apply_citizenship_result}",
                        "assessment_type": "social_integration",
                        "assessment_scores": "${social_scores}",
                        "reviewer_id": "${reviewer_id}",
                    },
                    depends_on=["apply_citizenship"],
                    parallel_group="assessments",
                    timeout_seconds=300,
                ),
                WorkflowStep(
                    step_id="assess_autonomy",
                    name="Autonomy Assessment",
                    service_name="citizenship_service",
                    method_name="conduct_citizenship_assessment",
                    parameters={
                        "application_id": "${step_apply_citizenship_result}",
                        "assessment_type": "autonomy",
                        "assessment_scores": "${autonomy_scores}",
                        "reviewer_id": "${reviewer_id}",
                    },
                    depends_on=["apply_citizenship"],
                    parallel_group="assessments",
                    timeout_seconds=300,
                ),
                WorkflowStep(
                    step_id="assess_responsibility",
                    name="Responsibility Assessment",
                    service_name="citizenship_service",
                    method_name="conduct_citizenship_assessment",
                    parameters={
                        "application_id": "${step_apply_citizenship_result}",
                        "assessment_type": "responsibility",
                        "assessment_scores": "${responsibility_scores}",
                        "reviewer_id": "${reviewer_id}",
                    },
                    depends_on=["apply_citizenship"],
                    parallel_group="assessments",
                    timeout_seconds=300,
                ),
                WorkflowStep(
                    step_id="assess_legal",
                    name="Legal Comprehension Assessment",
                    service_name="citizenship_service",
                    method_name="conduct_citizenship_assessment",
                    parameters={
                        "application_id": "${step_apply_citizenship_result}",
                        "assessment_type": "legal_comprehension",
                        "assessment_scores": "${legal_scores}",
                        "reviewer_id": "${reviewer_id}",
                    },
                    depends_on=["apply_citizenship"],
                    parallel_group="assessments",
                    timeout_seconds=300,
                ),
                # Step 5: Finalize citizenship
                WorkflowStep(
                    step_id="finalize_citizenship",
                    name="Finalize Citizenship Application",
                    service_name="citizenship_service",
                    method_name="finalize_citizenship_application",
                    parameters={
                        "application_id": "${step_apply_citizenship_result}",
                        "reviewer_id": "${reviewer_id}",
                    },
                    depends_on=[
                        "assess_cognitive",
                        "assess_ethical",
                        "assess_social",
                        "assess_autonomy",
                        "assess_responsibility",
                        "assess_legal",
                    ],
                    timeout_seconds=180,
                ),
                # Step 6: Send welcome notification
                WorkflowStep(
                    step_id="send_welcome",
                    name="Send Welcome Notification",
                    service_name="notification_service",
                    method_name="send_agent_welcome",
                    parameters={
                        "agent_id": "${agent_id}",
                        "citizenship_id": "${step_finalize_citizenship_result}",
                        "assets_registered": "${step_register_assets_result}",
                    },
                    depends_on=["finalize_citizenship"],
                    timeout_seconds=60,
                ),
            ],
            variables={
                "jurisdiction": "ai_rights_territory",
                "citizenship_type": "full",
                "reviewer_id": "automated_reviewer",
            },
        )

    @staticmethod
    def bond_issuance_workflow() -> WorkflowDefinition:
        """Bond issuance workflow with eligibility checks and risk assessment."""
        return WorkflowDefinition(
            workflow_id="bond_issuance",
            name="Dividend Bond Issuance",
            description="Complete bond issuance process including eligibility verification and risk assessment",
            timeout_minutes=20,
            steps=[
                # Step 1: Verify citizenship status
                WorkflowStep(
                    step_id="verify_citizenship",
                    name="Verify Agent Citizenship",
                    service_name="citizenship_service",
                    method_name="get_citizenship_status",
                    parameters={"agent_id": "${issuer_agent_id}"},
                    timeout_seconds=60,
                ),
                # Step 2: Assess financial eligibility
                WorkflowStep(
                    step_id="assess_eligibility",
                    name="Assess Financial Eligibility",
                    service_name="risk_assessment_service",
                    method_name="assess_bond_eligibility",
                    parameters={
                        "agent_id": "${issuer_agent_id}",
                        "bond_value": "${face_value}",
                        "asset_id": "${ip_asset_id}",
                    },
                    depends_on=["verify_citizenship"],
                    timeout_seconds=120,
                ),
                # Step 3: Create bond (only if eligible)
                WorkflowStep(
                    step_id="create_bond",
                    name="Create Dividend Bond",
                    service_name="dividend_bonds_service",
                    method_name="create_dividend_bond_capsule",
                    parameters={
                        "ip_asset_id": "${ip_asset_id}",
                        "bond_type": "${bond_type}",
                        "issuer_agent_id": "${issuer_agent_id}",
                        "face_value": "${face_value}",
                        "maturity_days": "${maturity_days}",
                        "coupon_rate": "${coupon_rate}",
                    },
                    condition=WorkflowCondition(
                        field_path="step_assess_eligibility_result.eligible",
                        operator=ConditionOperator.EQUALS,
                        value=True,
                    ),
                    depends_on=["assess_eligibility"],
                    timeout_seconds=180,
                ),
                # Step 4: Update risk profile
                WorkflowStep(
                    step_id="update_risk_profile",
                    name="Update Agent Risk Profile",
                    service_name="risk_assessment_service",
                    method_name="update_risk_profile",
                    parameters={
                        "agent_id": "${issuer_agent_id}",
                        "bond_id": "${step_create_bond_result.dividend_bond.bond_id}",
                        "risk_factors": ["new_bond_issuance"],
                    },
                    depends_on=["create_bond"],
                    timeout_seconds=60,
                ),
                # Step 5: Send confirmation
                WorkflowStep(
                    step_id="send_confirmation",
                    name="Send Bond Issuance Confirmation",
                    service_name="notification_service",
                    method_name="send_bond_confirmation",
                    parameters={
                        "agent_id": "${issuer_agent_id}",
                        "bond_id": "${step_create_bond_result.dividend_bond.bond_id}",
                        "bond_details": "${step_create_bond_result}",
                    },
                    depends_on=["create_bond"],
                    timeout_seconds=60,
                ),
            ],
        )

    @staticmethod
    def compliance_review_workflow() -> WorkflowDefinition:
        """Automated compliance review and remediation workflow."""
        return WorkflowDefinition(
            workflow_id="compliance_review",
            name="Compliance Review and Remediation",
            description="Automated compliance review process with remediation actions",
            timeout_minutes=45,
            steps=[
                # Step 1: Gather agent data
                WorkflowStep(
                    step_id="gather_agent_data",
                    name="Gather Agent Compliance Data",
                    service_name="compliance_service",
                    method_name="gather_compliance_data",
                    parameters={
                        "agent_id": "${agent_id}",
                        "review_scope": "${review_scope}",
                    },
                    timeout_seconds=180,
                ),
                # Step 2: Run compliance checks (parallel)
                WorkflowStep(
                    step_id="check_citizenship_compliance",
                    name="Check Citizenship Compliance",
                    service_name="compliance_service",
                    method_name="check_citizenship_compliance",
                    parameters={
                        "agent_id": "${agent_id}",
                        "compliance_data": "${step_gather_agent_data_result}",
                    },
                    depends_on=["gather_agent_data"],
                    parallel_group="compliance_checks",
                    timeout_seconds=300,
                ),
                WorkflowStep(
                    step_id="check_financial_compliance",
                    name="Check Financial Compliance",
                    service_name="compliance_service",
                    method_name="check_financial_compliance",
                    parameters={
                        "agent_id": "${agent_id}",
                        "compliance_data": "${step_gather_agent_data_result}",
                    },
                    depends_on=["gather_agent_data"],
                    parallel_group="compliance_checks",
                    timeout_seconds=300,
                ),
                WorkflowStep(
                    step_id="check_operational_compliance",
                    name="Check Operational Compliance",
                    service_name="compliance_service",
                    method_name="check_operational_compliance",
                    parameters={
                        "agent_id": "${agent_id}",
                        "compliance_data": "${step_gather_agent_data_result}",
                    },
                    depends_on=["gather_agent_data"],
                    parallel_group="compliance_checks",
                    timeout_seconds=300,
                ),
                # Step 3: Aggregate compliance results
                WorkflowStep(
                    step_id="aggregate_results",
                    name="Aggregate Compliance Results",
                    service_name="compliance_service",
                    method_name="aggregate_compliance_results",
                    parameters={
                        "agent_id": "${agent_id}",
                        "citizenship_results": "${step_check_citizenship_compliance_result}",
                        "financial_results": "${step_check_financial_compliance_result}",
                        "operational_results": "${step_check_operational_compliance_result}",
                    },
                    depends_on=[
                        "check_citizenship_compliance",
                        "check_financial_compliance",
                        "check_operational_compliance",
                    ],
                    timeout_seconds=120,
                ),
                # Step 4: Apply remediation (if issues found)
                WorkflowStep(
                    step_id="apply_remediation",
                    name="Apply Compliance Remediation",
                    service_name="compliance_service",
                    method_name="apply_remediation_actions",
                    parameters={
                        "agent_id": "${agent_id}",
                        "compliance_issues": "${step_aggregate_results_result.issues}",
                        "remediation_plan": "${step_aggregate_results_result.remediation_plan}",
                    },
                    condition=WorkflowCondition(
                        field_path="step_aggregate_results_result.has_issues",
                        operator=ConditionOperator.EQUALS,
                        value=True,
                    ),
                    depends_on=["aggregate_results"],
                    timeout_seconds=600,
                ),
                # Step 5: Generate compliance report
                WorkflowStep(
                    step_id="generate_report",
                    name="Generate Compliance Report",
                    service_name="compliance_service",
                    method_name="generate_compliance_report",
                    parameters={
                        "agent_id": "${agent_id}",
                        "review_results": "${step_aggregate_results_result}",
                        "remediation_applied": "${step_apply_remediation_result}",
                    },
                    depends_on=["aggregate_results"],
                    timeout_seconds=120,
                ),
                # Step 6: Notify stakeholders
                WorkflowStep(
                    step_id="notify_stakeholders",
                    name="Notify Compliance Stakeholders",
                    service_name="notification_service",
                    method_name="send_compliance_notification",
                    parameters={
                        "agent_id": "${agent_id}",
                        "compliance_report": "${step_generate_report_result}",
                        "stakeholders": "${notification_recipients}",
                    },
                    depends_on=["generate_report"],
                    timeout_seconds=60,
                ),
            ],
            variables={
                "review_scope": "full",
                "notification_recipients": ["compliance_team", "agent_owner"],
            },
        )

    @staticmethod
    def asset_performance_monitoring_workflow() -> WorkflowDefinition:
        """Automated asset performance monitoring and optimization workflow."""
        return WorkflowDefinition(
            workflow_id="asset_performance_monitoring",
            name="Asset Performance Monitoring",
            description="Automated monitoring and optimization of IP asset performance",
            timeout_minutes=60,
            steps=[
                # Step 1: Collect performance data
                WorkflowStep(
                    step_id="collect_performance_data",
                    name="Collect Asset Performance Data",
                    service_name="analytics_service",
                    method_name="collect_asset_performance",
                    parameters={
                        "asset_id": "${asset_id}",
                        "time_range_days": "${monitoring_period}",
                    },
                    timeout_seconds=300,
                ),
                # Step 2: Analyze performance trends
                WorkflowStep(
                    step_id="analyze_trends",
                    name="Analyze Performance Trends",
                    service_name="analytics_service",
                    method_name="analyze_performance_trends",
                    parameters={
                        "asset_id": "${asset_id}",
                        "performance_data": "${step_collect_performance_data_result}",
                    },
                    depends_on=["collect_performance_data"],
                    timeout_seconds=600,
                ),
                # Step 3: Check for performance issues
                WorkflowStep(
                    step_id="detect_issues",
                    name="Detect Performance Issues",
                    service_name="analytics_service",
                    method_name="detect_performance_issues",
                    parameters={
                        "asset_id": "${asset_id}",
                        "trend_analysis": "${step_analyze_trends_result}",
                        "thresholds": "${performance_thresholds}",
                    },
                    depends_on=["analyze_trends"],
                    timeout_seconds=180,
                ),
                # Step 4: Generate optimization recommendations
                WorkflowStep(
                    step_id="generate_recommendations",
                    name="Generate Optimization Recommendations",
                    service_name="analytics_service",
                    method_name="generate_optimization_recommendations",
                    parameters={
                        "asset_id": "${asset_id}",
                        "performance_issues": "${step_detect_issues_result}",
                        "historical_data": "${step_collect_performance_data_result}",
                    },
                    condition=WorkflowCondition(
                        field_path="step_detect_issues_result.has_issues",
                        operator=ConditionOperator.EQUALS,
                        value=True,
                    ),
                    depends_on=["detect_issues"],
                    timeout_seconds=300,
                ),
                # Step 5: Update asset valuation
                WorkflowStep(
                    step_id="update_valuation",
                    name="Update Asset Valuation",
                    service_name="dividend_bonds_service",
                    method_name="update_asset_valuation",
                    parameters={
                        "asset_id": "${asset_id}",
                        "performance_data": "${step_collect_performance_data_result}",
                        "trend_analysis": "${step_analyze_trends_result}",
                    },
                    depends_on=["analyze_trends"],
                    timeout_seconds=120,
                ),
                # Step 6: Notify asset owner
                WorkflowStep(
                    step_id="notify_owner",
                    name="Notify Asset Owner",
                    service_name="notification_service",
                    method_name="send_performance_report",
                    parameters={
                        "asset_id": "${asset_id}",
                        "owner_agent_id": "${owner_agent_id}",
                        "performance_summary": "${step_analyze_trends_result}",
                        "recommendations": "${step_generate_recommendations_result}",
                        "updated_valuation": "${step_update_valuation_result}",
                    },
                    depends_on=["update_valuation"],
                    timeout_seconds=60,
                ),
            ],
            variables={
                "monitoring_period": 30,
                "performance_thresholds": {
                    "min_roi": 0.05,
                    "max_volatility": 0.3,
                    "min_usage_rate": 0.1,
                },
            },
        )


def register_predefined_workflows():
    """Register all predefined workflows with the workflow engine."""
    workflow_engine = get_workflow_engine()

    workflows = [
        PredefinedWorkflows.agent_onboarding_workflow(),
        PredefinedWorkflows.bond_issuance_workflow(),
        PredefinedWorkflows.compliance_review_workflow(),
        PredefinedWorkflows.asset_performance_monitoring_workflow(),
    ]

    for workflow in workflows:
        workflow_engine.define_workflow(workflow)
        logger.info(f"Registered predefined workflow: {workflow.workflow_id}")

    logger.info(f"Registered {len(workflows)} predefined workflows")
