"""
Enterprise API Routes
=====================

Comprehensive API endpoints for enterprise features including SSO, governance,
compliance reporting, rate limiting, and multi-tenant management.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Query, Body
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from ..auth.enterprise_sso import (
    EnterpriseSSO,
    EnterpriseConfig,
    SAMLConfig,
    OIDCConfig,
    EnterpriseUser,
    require_permission,
    require_role,
    sso_manager,
)
from ..governance.enterprise_governance import (
    EnterpriseGovernance,
    GovernancePolicy,
    PolicyViolation,
    AuditEvent,
    ComplianceFramework,
    PolicyType,
    ViolationSeverity,
)
from ..compliance.reporting_engine import (
    ComplianceReportingEngine,
    ComplianceReport,
    ReportFormat,
    ReportFrequency,
)
from ..api.enterprise_rate_limiting import (
    EnterpriseRateLimiter,
    OrganizationPlan,
    OrganizationTier,
    UsageRecord,
)

logger = logging.getLogger(__name__)

# Initialize enterprise components
governance_system = EnterpriseGovernance()
reporting_engine = ComplianceReportingEngine(governance_system)
rate_limiter = EnterpriseRateLimiter()

# API Router
enterprise_router = APIRouter(prefix="/enterprise", tags=["enterprise"])
security = HTTPBearer()


# Pydantic models for API requests/responses
class SSOConfigRequest(BaseModel):
    """SSO configuration request."""

    organization_id: str
    provider_name: str
    protocol: str
    endpoint_url: str
    client_id: str
    client_secret: str
    metadata_url: Optional[str] = None
    certificate_path: Optional[str] = None


class PolicyCreateRequest(BaseModel):
    """Policy creation request."""

    name: str
    description: str
    policy_type: str
    rules: List[Dict[str, Any]]
    approval_required: bool = True
    auto_enforce: bool = True


class ComplianceReportRequest(BaseModel):
    """Compliance report generation request."""

    template_id: str
    start_date: datetime
    end_date: datetime
    format: str = "pdf"
    custom_parameters: Optional[Dict[str, Any]] = None


class OrganizationPlanRequest(BaseModel):
    """Organization plan update request."""

    tier: str
    plan_name: str
    features: List[str]
    rate_limits: List[Dict[str, Any]]
    quotas: List[Dict[str, Any]]
    price_per_month: float


# SSO Management Endpoints
@enterprise_router.post("/sso/configure")
async def configure_sso(
    config_request: SSOConfigRequest,
    current_user: EnterpriseUser = Depends(require_permission("sso.configure")),
):
    """Configure SSO for an organization."""
    try:
        # Create SSO configuration
        if config_request.protocol.lower() == "saml2":
            saml_config = SAMLConfig(
                entity_id=config_request.endpoint_url,
                sso_url=config_request.endpoint_url,
                x509_cert=None,  # Would load from certificate_path
            )
            enterprise_config = EnterpriseConfig(
                organization_id=config_request.organization_id,
                domain=config_request.organization_id,
                identity_provider="generic_saml",
                protocol="saml2",
                saml_config=saml_config,
            )
        else:
            oidc_config = OIDCConfig(
                client_id=config_request.client_id,
                client_secret=config_request.client_secret,
                discovery_url=config_request.metadata_url
                or f"{config_request.endpoint_url}/.well-known/openid_configuration",
                redirect_uri=f"/enterprise/sso/callback/{config_request.organization_id}",
            )
            enterprise_config = EnterpriseConfig(
                organization_id=config_request.organization_id,
                domain=config_request.organization_id,
                identity_provider="generic_oidc",
                protocol="oidc",
                oidc_config=oidc_config,
            )

        # Configure SSO
        sso_manager.configure_organization(enterprise_config)

        return {
            "success": True,
            "message": f"SSO configured for organization {config_request.organization_id}",
            "organization_id": config_request.organization_id,
            "protocol": config_request.protocol,
        }

    except Exception as e:
        logger.error(f"SSO configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@enterprise_router.get("/sso/login/{organization_id}")
async def initiate_sso_login(
    organization_id: str, return_url: Optional[str] = Query(None)
):
    """Initiate SSO login for organization."""
    try:
        result = await sso_manager.initiate_login(organization_id, return_url)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SSO login initiation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@enterprise_router.post("/sso/callback/{organization_id}")
async def handle_sso_callback(organization_id: str, request: Request):
    """Handle SSO callback."""
    try:
        # Extract callback data
        if request.method == "POST":
            form_data = await request.form()
            callback_data = dict(form_data)
        else:
            callback_data = dict(request.query_params)

        result = await sso_manager.handle_callback(organization_id, **callback_data)

        if result["success"]:
            return {
                "success": True,
                "user": result["user"].dict(),
                "tokens": result["tokens"],
            }
        else:
            raise HTTPException(status_code=401, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SSO callback handling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Governance Management Endpoints
@enterprise_router.post("/governance/policies")
async def create_governance_policy(
    policy_request: PolicyCreateRequest,
    current_user: EnterpriseUser = Depends(require_permission("policy.create")),
):
    """Create a new governance policy."""
    try:
        # Create policy object
        from ..governance.enterprise_governance import PolicyRule

        rules = []
        for rule_data in policy_request.rules:
            rule = PolicyRule(
                rule_id=rule_data["rule_id"],
                name=rule_data["name"],
                description=rule_data["description"],
                condition=rule_data["condition"],
                action=rule_data["action"],
                severity=ViolationSeverity(rule_data["severity"]),
            )
            rules.append(rule)

        policy = GovernancePolicy(
            policy_id=f"pol_{int(datetime.utcnow().timestamp())}",
            name=policy_request.name,
            description=policy_request.description,
            policy_type=PolicyType(policy_request.policy_type),
            status="pending_approval" if policy_request.approval_required else "active",
            rules=rules,
            created_by=current_user.user_id,
            created_at=datetime.utcnow(),
            effective_date=datetime.utcnow(),
            approval_required=policy_request.approval_required,
            auto_enforce=policy_request.auto_enforce,
        )

        policy_id = await governance_system.create_policy(policy, current_user.user_id)

        return {
            "success": True,
            "policy_id": policy_id,
            "message": "Policy created successfully",
            "status": policy.status.value
            if hasattr(policy.status, "value")
            else policy.status,
        }

    except Exception as e:
        logger.error(f"Policy creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@enterprise_router.get("/governance/policies")
async def list_governance_policies(
    current_user: EnterpriseUser = Depends(require_permission("policy.view")),
    policy_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """List governance policies."""
    try:
        policies = []

        for policy in governance_system.policies.values():
            # Apply filters
            if policy_type and policy.policy_type.value != policy_type:
                continue
            if status and policy.status.value != status:
                continue

            policy_data = {
                "policy_id": policy.policy_id,
                "name": policy.name,
                "description": policy.description,
                "policy_type": policy.policy_type.value,
                "status": policy.status.value
                if hasattr(policy.status, "value")
                else policy.status,
                "created_by": policy.created_by,
                "created_at": policy.created_at.isoformat(),
                "effective_date": policy.effective_date.isoformat(),
                "rules_count": len(policy.rules),
            }
            policies.append(policy_data)

        return {"policies": policies, "total_count": len(policies)}

    except Exception as e:
        logger.error(f"Policy listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@enterprise_router.post("/governance/evaluate")
async def evaluate_policy_compliance(
    evaluation_request: Dict[str, Any] = Body(...),
    current_user: EnterpriseUser = Depends(require_permission("policy.evaluate")),
):
    """Evaluate policy compliance for a resource/action."""
    try:
        resource_type = evaluation_request["resource_type"]
        resource_id = evaluation_request["resource_id"]
        action = evaluation_request["action"]
        context = evaluation_request.get("context", {})

        result = await governance_system.evaluate_policy_compliance(
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            context=context,
            user_id=current_user.user_id,
        )

        return result

    except Exception as e:
        logger.error(f"Policy evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@enterprise_router.get("/governance/violations")
async def list_policy_violations(
    current_user: EnterpriseUser = Depends(require_permission("audit.view")),
    severity: Optional[str] = Query(None),
    resolved: Optional[bool] = Query(None),
    limit: int = Query(100, le=1000),
):
    """List policy violations."""
    try:
        violations = []

        for violation in governance_system.violations:
            # Apply filters
            if severity and violation.severity.value != severity:
                continue
            if resolved is not None:
                is_resolved = violation.resolved_at is not None
                if resolved != is_resolved:
                    continue

            violation_data = {
                "violation_id": violation.violation_id,
                "policy_id": violation.policy_id,
                "rule_id": violation.rule_id,
                "user_id": violation.user_id,
                "resource_id": violation.resource_id,
                "violation_type": violation.violation_type,
                "severity": violation.severity.value,
                "description": violation.description,
                "detected_at": violation.detected_at.isoformat(),
                "resolved_at": violation.resolved_at.isoformat()
                if violation.resolved_at
                else None,
                "resolved_by": violation.resolved_by,
                "status": "resolved" if violation.resolved_at else "open",
            }
            violations.append(violation_data)

            if len(violations) >= limit:
                break

        return {"violations": violations, "total_count": len(violations)}

    except Exception as e:
        logger.error(f"Violation listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Compliance Reporting Endpoints
@enterprise_router.post("/compliance/reports/generate")
async def generate_compliance_report(
    report_request: ComplianceReportRequest,
    current_user: EnterpriseUser = Depends(require_permission("compliance.report")),
):
    """Generate compliance report."""
    try:
        reporting_period = {
            "start_date": report_request.start_date,
            "end_date": report_request.end_date,
        }

        report = await reporting_engine.generate_report(
            template_id=report_request.template_id,
            reporting_period=reporting_period,
            format=ReportFormat(report_request.format),
            generated_by=current_user.user_id,
            organization_id=current_user.organization_id,
            custom_parameters=report_request.custom_parameters,
        )

        return {
            "success": True,
            "report_id": report.report_id,
            "report_name": report.report_name,
            "compliance_score": report.compliance_score,
            "file_path": report.file_path,
            "file_size": report.file_size,
            "generation_timestamp": report.generation_timestamp.isoformat(),
        }

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@enterprise_router.get("/compliance/reports")
async def list_compliance_reports(
    current_user: EnterpriseUser = Depends(require_permission("compliance.view")),
    framework_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    """List generated compliance reports."""
    try:
        reports = []

        for report in reporting_engine.reports.values():
            # Apply filters
            if framework_id and report.framework_id != framework_id:
                continue

            # Check organization access
            if (
                report.organization_id != current_user.organization_id
                and not current_user.roles.count("super_admin")
            ):
                continue

            report_data = {
                "report_id": report.report_id,
                "template_id": report.template_id,
                "framework_id": report.framework_id,
                "report_name": report.report_name,
                "compliance_score": report.compliance_score,
                "generation_timestamp": report.generation_timestamp.isoformat(),
                "format": report.format.value,
                "file_size": report.file_size,
                "generated_by": report.generated_by,
            }
            reports.append(report_data)

            if len(reports) >= limit:
                break

        return {"reports": reports, "total_count": len(reports)}

    except Exception as e:
        logger.error(f"Report listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@enterprise_router.get("/compliance/reports/{report_id}/download")
async def download_compliance_report(
    report_id: str,
    current_user: EnterpriseUser = Depends(require_permission("compliance.view")),
):
    """Download compliance report file."""
    try:
        report = reporting_engine.reports.get(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Check access
        if (
            report.organization_id != current_user.organization_id
            and not current_user.roles.count("super_admin")
        ):
            raise HTTPException(status_code=403, detail="Access denied")

        if not report.file_path or not Path(report.file_path).exists():
            raise HTTPException(status_code=404, detail="Report file not found")

        return FileResponse(
            path=report.file_path,
            filename=f"{report.report_name}_{report_id}.{report.format.value}",
            media_type="application/octet-stream",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@enterprise_router.get("/compliance/frameworks")
async def list_compliance_frameworks(
    current_user: EnterpriseUser = Depends(require_permission("compliance.view")),
):
    """List available compliance frameworks."""
    try:
        frameworks = []

        for framework in governance_system.compliance_frameworks.values():
            framework_data = {
                "framework_id": framework.framework_id,
                "name": framework.name,
                "version": framework.version,
                "description": framework.description,
                "requirements_count": len(framework.requirements),
                "controls_count": len(framework.controls),
                "reporting_frequency": framework.reporting_frequency,
                "last_assessment": framework.last_assessment.isoformat()
                if framework.last_assessment
                else None,
                "compliance_score": framework.compliance_score,
            }
            frameworks.append(framework_data)

        return {"frameworks": frameworks, "total_count": len(frameworks)}

    except Exception as e:
        logger.error(f"Framework listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Rate Limiting and Usage Management Endpoints
@enterprise_router.get("/usage/analytics")
async def get_usage_analytics(
    current_user: EnterpriseUser = Depends(require_permission("usage.view")),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    organization_id: Optional[str] = Query(None),
):
    """Get usage analytics for organization."""
    try:
        # Use current user's organization if not specified or not authorized
        target_org_id = organization_id
        if not target_org_id or (
            target_org_id != current_user.organization_id
            and not current_user.roles.count("super_admin")
        ):
            target_org_id = current_user.organization_id

        analytics = await rate_limiter.get_usage_analytics(
            organization_id=target_org_id, start_date=start_date, end_date=end_date
        )

        return analytics

    except Exception as e:
        logger.error(f"Usage analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@enterprise_router.get("/usage/quotas")
async def get_quota_status(
    current_user: EnterpriseUser = Depends(require_permission("usage.view")),
):
    """Get current quota status for organization."""
    try:
        from ..api.enterprise_rate_limiting import QuotaType

        quota_status = {}

        # Check all quota types
        for quota_type in QuotaType:
            allowed, status = await rate_limiter.check_quota(
                current_user.organization_id, quota_type, 0
            )

            quota_status[quota_type.value] = {
                "current_usage": status.current_usage,
                "quota_value": status.quota_value,
                "usage_percent": status.usage_percent,
                "overage_amount": status.overage_amount,
                "estimated_cost": status.estimated_cost,
                "period_start": status.period_start.isoformat(),
                "period_end": status.period_end.isoformat(),
            }

        return {"organization_id": current_user.organization_id, "quotas": quota_status}

    except Exception as e:
        logger.error(f"Quota status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@enterprise_router.get("/usage/sla")
async def get_sla_metrics(
    current_user: EnterpriseUser = Depends(require_permission("usage.view")),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
):
    """Get SLA metrics for organization."""
    try:
        sla_metrics = await rate_limiter.get_sla_metrics(
            organization_id=current_user.organization_id,
            start_date=start_date,
            end_date=end_date,
        )

        return sla_metrics

    except Exception as e:
        logger.error(f"SLA metrics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@enterprise_router.post("/organizations/{organization_id}/plan")
async def update_organization_plan(
    organization_id: str,
    plan_request: OrganizationPlanRequest,
    current_user: EnterpriseUser = Depends(require_permission("organization.manage")),
):
    """Update organization subscription plan."""
    try:
        from ..api.enterprise_rate_limiting import (
            RateLimit,
            UsageQuota,
            RateLimitType,
            QuotaType,
        )

        # Create rate limits
        rate_limits = []
        for limit_data in plan_request.rate_limits:
            rate_limit = RateLimit(
                limit_type=RateLimitType(limit_data["limit_type"]),
                limit_value=limit_data["limit_value"],
                window_seconds=limit_data["window_seconds"],
            )
            rate_limits.append(rate_limit)

        # Create quotas
        quotas = []
        for quota_data in plan_request.quotas:
            quota = UsageQuota(
                quota_type=QuotaType(quota_data["quota_type"]),
                quota_value=quota_data["quota_value"],
                period_days=quota_data["period_days"],
                overage_allowed=quota_data.get("overage_allowed", True),
                overage_rate=quota_data.get("overage_rate", 0.0),
            )
            quotas.append(quota)

        # Create organization plan
        plan = OrganizationPlan(
            plan_id=f"custom_{int(datetime.utcnow().timestamp())}",
            organization_id=organization_id,
            tier=OrganizationTier(plan_request.tier),
            plan_name=plan_request.plan_name,
            rate_limits=rate_limits,
            quotas=quotas,
            features=plan_request.features,
            price_per_month=plan_request.price_per_month,
        )

        await rate_limiter.update_organization_plan(organization_id, plan)

        return {
            "success": True,
            "message": f"Plan updated for organization {organization_id}",
            "plan_id": plan.plan_id,
        }

    except Exception as e:
        logger.error(f"Plan update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Multi-tenant Management Endpoints
@enterprise_router.get("/organizations")
async def list_organizations(
    current_user: EnterpriseUser = Depends(require_role("super_admin")),
):
    """List all organizations (super admin only)."""
    try:
        organizations = []

        for org_id, plan in rate_limiter.organization_plans.items():
            org_data = {
                "organization_id": org_id,
                "plan_name": plan.plan_name,
                "tier": plan.tier.value,
                "features": plan.features,
                "price_per_month": plan.price_per_month,
                "effective_date": plan.effective_date.isoformat(),
                "expiry_date": plan.expiry_date.isoformat()
                if plan.expiry_date
                else None,
            }
            organizations.append(org_data)

        return {"organizations": organizations, "total_count": len(organizations)}

    except Exception as e:
        logger.error(f"Organization listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@enterprise_router.get("/audit/events")
async def list_audit_events(
    current_user: EnterpriseUser = Depends(require_permission("audit.view")),
    event_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
):
    """List audit events."""
    try:
        events = []

        for event in governance_system.audit_events:
            # Apply filters
            if event_type and event.event_type != event_type:
                continue
            if user_id and event.user_id != user_id:
                continue
            if start_date and event.timestamp < start_date:
                continue
            if end_date and event.timestamp > end_date:
                continue

            event_data = {
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "user_id": event.user_id,
                "session_id": event.session_id,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "action": event.action,
                "outcome": event.outcome,
                "risk_level": event.risk_level.value,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "details": event.details,
            }
            events.append(event_data)

            if len(events) >= limit:
                break

        return {"events": events, "total_count": len(events)}

    except Exception as e:
        logger.error(f"Audit events listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@enterprise_router.get("/health/enterprise")
async def enterprise_health_check():
    """Health check for enterprise components."""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "sso": {
                    "status": "healthy",
                    "active_sessions": len(sso_manager.active_sessions),
                    "configured_providers": len(sso_manager.configurations),
                },
                "governance": {
                    "status": "healthy",
                    "active_policies": len(
                        [
                            p
                            for p in governance_system.policies.values()
                            if p.status.value == "active"
                        ]
                    ),
                    "total_violations": len(governance_system.violations),
                    "pending_approvals": len(governance_system.pending_approvals),
                },
                "reporting": {
                    "status": "healthy",
                    "available_templates": len(reporting_engine.templates),
                    "generated_reports": len(reporting_engine.reports),
                },
                "rate_limiting": {
                    "status": "healthy",
                    "organization_plans": len(rate_limiter.organization_plans),
                    "usage_records": len(rate_limiter.usage_records),
                },
            },
        }

        return health_status

    except Exception as e:
        logger.error(f"Enterprise health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


# Dashboard and Analytics Endpoints
@enterprise_router.get("/dashboard/summary")
async def get_dashboard_summary(
    current_user: EnterpriseUser = Depends(require_permission("dashboard.view")),
):
    """Get enterprise dashboard summary."""
    try:
        # Get recent violations
        recent_violations = [
            v
            for v in governance_system.violations
            if v.detected_at >= datetime.utcnow() - timedelta(days=7)
        ]

        # Get usage summary
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        usage_analytics = await rate_limiter.get_usage_analytics(
            current_user.organization_id, start_date, end_date
        )

        summary = {
            "organization": {
                "id": current_user.organization_id,
                "name": current_user.organization_id,  # Would get from database
                "tier": "Enterprise",  # Would get from plan
            },
            "compliance": {
                "active_policies": len(
                    [
                        p
                        for p in governance_system.policies.values()
                        if p.status.value == "active"
                    ]
                ),
                "recent_violations": len(recent_violations),
                "critical_violations": len(
                    [
                        v
                        for v in recent_violations
                        if v.severity == ViolationSeverity.CRITICAL
                    ]
                ),
                "compliance_score": 85.5,  # Would calculate from real data
            },
            "usage": {
                "api_requests_30d": usage_analytics["summary"]["total_requests"],
                "data_transfer_30d": usage_analytics["summary"][
                    "total_data_transfer_bytes"
                ],
                "monthly_cost": usage_analytics["summary"]["total_cost"],
            },
            "sso": {
                "active_sessions": len(
                    [
                        s
                        for s in sso_manager.active_sessions.values()
                        if s.organization_id == current_user.organization_id
                    ]
                ),
                "configured_providers": len(sso_manager.configurations),
            },
        }

        return summary

    except Exception as e:
        logger.error(f"Dashboard summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
