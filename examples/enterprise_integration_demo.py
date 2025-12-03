"""
UATP Capsule Engine - Enterprise Integration Demo
=================================================

This demo showcases the complete enterprise features including SSO integration,
governance policies, compliance reporting, and rate limiting management.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import httpx
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnterpriseIntegrationDemo:
    """Complete enterprise integration demonstration."""

    def __init__(self, base_url: str, admin_token: str):
        self.base_url = base_url
        self.admin_token = admin_token
        self.client = httpx.AsyncClient(
            timeout=30.0, headers={"Authorization": f"Bearer {admin_token}"}
        )

    async def run_complete_demo(self):
        """Run complete enterprise integration demo."""

        logger.info("🚀 Starting UATP Enterprise Integration Demo")

        try:
            # 1. System Health Check
            await self.check_system_health()

            # 2. Configure SSO Integration
            await self.configure_enterprise_sso()

            # 3. Set up Governance Policies
            await self.setup_governance_policies()

            # 4. Configure Rate Limiting
            await self.configure_rate_limiting()

            # 5. Generate Compliance Reports
            await self.generate_compliance_reports()

            # 6. Demonstrate Multi-Tenant Management
            await self.demonstrate_multi_tenant_management()

            # 7. Test Security and Monitoring
            await self.test_security_monitoring()

            # 8. Show Analytics and Reporting
            await self.show_analytics_and_reporting()

            logger.info("✅ Enterprise Integration Demo completed successfully!")

        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise
        finally:
            await self.client.aclose()

    async def check_system_health(self):
        """Check enterprise system health."""

        logger.info("🔍 Checking system health...")

        response = await self.client.get(
            f"{self.base_url}/enterprise/health/enterprise"
        )
        response.raise_for_status()

        health_data = response.json()
        logger.info(f"System Status: {health_data['status']}")

        for component, status in health_data["components"].items():
            logger.info(f"  {component}: {status['status']}")

        return health_data

    async def configure_enterprise_sso(self):
        """Configure enterprise SSO integration."""

        logger.info("🔐 Configuring Enterprise SSO...")

        # Configure Azure AD SSO
        azure_config = {
            "organization_id": "demo-enterprise",
            "provider_name": "Azure AD",
            "protocol": "oidc",
            "endpoint_url": "https://login.microsoftonline.com/demo-tenant-id/v2.0",
            "client_id": "demo-azure-client-id",
            "client_secret": "demo-azure-client-secret",
            "metadata_url": "https://login.microsoftonline.com/demo-tenant-id/v2.0/.well-known/openid_configuration",
        }

        response = await self.client.post(
            f"{self.base_url}/enterprise/sso/configure", json=azure_config
        )

        if response.status_code == 200:
            logger.info("✅ Azure AD SSO configured successfully")
        else:
            logger.warning(f"⚠️ SSO configuration response: {response.status_code}")

        # Configure Okta SSO
        okta_config = {
            "organization_id": "demo-enterprise",
            "provider_name": "Okta",
            "protocol": "oidc",
            "endpoint_url": "https://demo-company.okta.com",
            "client_id": "demo-okta-client-id",
            "client_secret": "demo-okta-client-secret",
            "metadata_url": "https://demo-company.okta.com/.well-known/openid_configuration",
        }

        response = await self.client.post(
            f"{self.base_url}/enterprise/sso/configure", json=okta_config
        )

        if response.status_code == 200:
            logger.info("✅ Okta SSO configured successfully")
        else:
            logger.warning(
                f"⚠️ Okta SSO configuration response: {response.status_code}"
            )

        # Test SSO login initiation
        response = await self.client.get(
            f"{self.base_url}/enterprise/sso/login/demo-enterprise"
        )

        if response.status_code == 200:
            login_data = response.json()
            logger.info(
                f"✅ SSO login URL generated: {login_data.get('redirect_url', 'N/A')[:100]}..."
            )

        return True

    async def setup_governance_policies(self):
        """Set up comprehensive governance policies."""

        logger.info("📋 Setting up Governance Policies...")

        policies = []

        # Data Protection Policy
        data_protection_policy = {
            "name": "Enterprise Data Protection Policy",
            "description": "Comprehensive data protection and privacy policy",
            "policy_type": "data_protection",
            "rules": [
                {
                    "rule_id": "pii_encryption_required",
                    "name": "PII Encryption Requirement",
                    "description": "All PII must be encrypted at rest and in transit",
                    "condition": '{"data_type": "PII", "encryption": {"$ne": true}}',
                    "action": "block_operation",
                    "severity": "high",
                },
                {
                    "rule_id": "pii_access_logging",
                    "name": "PII Access Logging",
                    "description": "All PII access must be logged for audit purposes",
                    "condition": '{"data_type": "PII", "access_logged": {"$ne": true}}',
                    "action": "notify_admin",
                    "severity": "medium",
                },
                {
                    "rule_id": "data_retention_limit",
                    "name": "Data Retention Limit",
                    "description": "Personal data must not exceed retention periods",
                    "condition": '{"retention_days": {"$gt": 2555}}',
                    "action": "trigger_deletion",
                    "severity": "medium",
                },
            ],
            "approval_required": True,
            "auto_enforce": True,
        }

        response = await self.client.post(
            f"{self.base_url}/enterprise/governance/policies",
            json=data_protection_policy,
        )

        if response.status_code == 200:
            policy_data = response.json()
            policies.append(policy_data["policy_id"])
            logger.info(f"✅ Data Protection Policy created: {policy_data['policy_id']}")

        # Access Control Policy
        access_control_policy = {
            "name": "Enterprise Access Control Policy",
            "description": "Role-based access control and authorization policy",
            "policy_type": "access_control",
            "rules": [
                {
                    "rule_id": "least_privilege",
                    "name": "Principle of Least Privilege",
                    "description": "Users should have minimum necessary permissions",
                    "condition": '{"permission_level": {"$gt": "required_level"}}',
                    "action": "escalate_approval",
                    "severity": "medium",
                },
                {
                    "rule_id": "mfa_required",
                    "name": "Multi-Factor Authentication Required",
                    "description": "MFA required for privileged access",
                    "condition": '{"role": "admin", "mfa_enabled": false}',
                    "action": "block_access",
                    "severity": "high",
                },
                {
                    "rule_id": "session_timeout",
                    "name": "Session Timeout Enforcement",
                    "description": "Sessions must timeout after maximum period",
                    "condition": '{"session_duration": {"$gt": 28800}}',
                    "action": "terminate_session",
                    "severity": "low",
                },
            ],
            "approval_required": False,
            "auto_enforce": True,
        }

        response = await self.client.post(
            f"{self.base_url}/enterprise/governance/policies",
            json=access_control_policy,
        )

        if response.status_code == 200:
            policy_data = response.json()
            policies.append(policy_data["policy_id"])
            logger.info(f"✅ Access Control Policy created: {policy_data['policy_id']}")

        # Security Policy
        security_policy = {
            "name": "Enterprise Security Policy",
            "description": "Comprehensive security controls and monitoring",
            "policy_type": "security",
            "rules": [
                {
                    "rule_id": "encryption_in_transit",
                    "name": "Encryption in Transit Required",
                    "description": "All data transmission must use encryption",
                    "condition": '{"transport_encryption": false}',
                    "action": "block_operation",
                    "severity": "critical",
                },
                {
                    "rule_id": "security_logging",
                    "name": "Security Event Logging",
                    "description": "Security events must be logged",
                    "condition": '{"security_event": true, "logged": false}',
                    "action": "notify_admin",
                    "severity": "high",
                },
            ],
            "approval_required": True,
            "auto_enforce": True,
        }

        response = await self.client.post(
            f"{self.base_url}/enterprise/governance/policies", json=security_policy
        )

        if response.status_code == 200:
            policy_data = response.json()
            policies.append(policy_data["policy_id"])
            logger.info(f"✅ Security Policy created: {policy_data['policy_id']}")

        # Test policy evaluation
        test_context = {
            "resource_type": "capsule",
            "resource_id": "test-capsule-123",
            "action": "create",
            "context": {
                "data_type": "PII",
                "encryption": True,
                "access_logged": True,
                "user_consent": True,
                "transport_encryption": True,
            },
        }

        response = await self.client.post(
            f"{self.base_url}/enterprise/governance/evaluate", json=test_context
        )

        if response.status_code == 200:
            evaluation_result = response.json()
            logger.info(
                f"✅ Policy evaluation completed - Compliant: {evaluation_result['compliant']}"
            )
            if evaluation_result.get("violations"):
                logger.warning(
                    f"⚠️ Found {len(evaluation_result['violations'])} violations"
                )

        return policies

    async def configure_rate_limiting(self):
        """Configure enterprise rate limiting and quotas."""

        logger.info("⚡ Configuring Rate Limiting...")

        # Configure enterprise plan
        enterprise_plan = {
            "tier": "enterprise",
            "plan_name": "Enterprise Plan",
            "features": [
                "premium_support",
                "enterprise_sla",
                "comprehensive_analytics",
                "custom_integrations",
                "dedicated_success_manager",
                "priority_processing",
            ],
            "rate_limits": [
                {
                    "limit_type": "requests_per_minute",
                    "limit_value": 2000,
                    "window_seconds": 60,
                },
                {
                    "limit_type": "requests_per_hour",
                    "limit_value": 50000,
                    "window_seconds": 3600,
                },
                {
                    "limit_type": "concurrent_requests",
                    "limit_value": 200,
                    "window_seconds": 0,
                },
            ],
            "quotas": [
                {
                    "quota_type": "api_calls",
                    "quota_value": 1000000,
                    "period_days": 30,
                    "overage_allowed": True,
                    "overage_rate": 0.0005,
                },
                {
                    "quota_type": "data_transfer",
                    "quota_value": 100000000000,  # 100GB
                    "period_days": 30,
                    "overage_allowed": True,
                    "overage_rate": 0.00005,
                },
                {
                    "quota_type": "users",
                    "quota_value": 100,
                    "period_days": 30,
                    "overage_allowed": True,
                    "overage_rate": 5.0,
                },
            ],
            "price_per_month": 999.0,
        }

        response = await self.client.post(
            f"{self.base_url}/enterprise/organizations/demo-enterprise/plan",
            json=enterprise_plan,
        )

        if response.status_code == 200:
            logger.info("✅ Enterprise rate limiting plan configured")
        else:
            logger.warning(
                f"⚠️ Rate limiting configuration response: {response.status_code}"
            )

        # Check quota status
        response = await self.client.get(f"{self.base_url}/enterprise/usage/quotas")

        if response.status_code == 200:
            quota_data = response.json()
            logger.info("📊 Current Quota Status:")
            for quota_type, status in quota_data.get("quotas", {}).items():
                logger.info(f"  {quota_type}: {status['usage_percent']:.1f}% used")

        return True

    async def generate_compliance_reports(self):
        """Generate comprehensive compliance reports."""

        logger.info("📊 Generating Compliance Reports...")

        reports = []

        # Generate GDPR Compliance Report
        gdpr_report_request = {
            "template_id": "gdpr_comprehensive",
            "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "format": "pdf",
            "custom_parameters": {
                "include_recommendations": True,
                "detailed_violations": True,
                "privacy_impact_assessment": True,
            },
        }

        response = await self.client.post(
            f"{self.base_url}/enterprise/compliance/reports/generate",
            json=gdpr_report_request,
        )

        if response.status_code == 200:
            report_data = response.json()
            reports.append(report_data["report_id"])
            logger.info(f"✅ GDPR Report generated: {report_data['report_id']}")
            logger.info(f"   Compliance Score: {report_data['compliance_score']:.1f}%")

        # Generate SOX Compliance Report
        sox_report_request = {
            "template_id": "sox_controls_assessment",
            "start_date": (datetime.utcnow() - timedelta(days=90)).isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "format": "pdf",
            "custom_parameters": {
                "include_control_testing": True,
                "management_assertions": True,
            },
        }

        response = await self.client.post(
            f"{self.base_url}/enterprise/compliance/reports/generate",
            json=sox_report_request,
        )

        if response.status_code == 200:
            report_data = response.json()
            reports.append(report_data["report_id"])
            logger.info(f"✅ SOX Report generated: {report_data['report_id']}")
            logger.info(f"   Compliance Score: {report_data['compliance_score']:.1f}%")

        # List all available compliance frameworks
        response = await self.client.get(
            f"{self.base_url}/enterprise/compliance/frameworks"
        )

        if response.status_code == 200:
            frameworks_data = response.json()
            logger.info(f"📋 Available Compliance Frameworks:")
            for framework in frameworks_data.get("frameworks", []):
                logger.info(f"  {framework['name']} ({framework['framework_id']})")

        # List generated reports
        response = await self.client.get(
            f"{self.base_url}/enterprise/compliance/reports?limit=10"
        )

        if response.status_code == 200:
            reports_data = response.json()
            logger.info(f"📊 Generated Reports: {reports_data.get('total_count', 0)}")

        return reports

    async def demonstrate_multi_tenant_management(self):
        """Demonstrate multi-tenant organization management."""

        logger.info("🏢 Demonstrating Multi-Tenant Management...")

        # List all organizations (requires super admin)
        response = await self.client.get(f"{self.base_url}/enterprise/organizations")

        if response.status_code == 200:
            orgs_data = response.json()
            logger.info(f"🏢 Total Organizations: {orgs_data.get('total_count', 0)}")

            for org in orgs_data.get("organizations", []):
                logger.info(
                    f"  {org['organization_id']} ({org['tier']}) - ${org['price_per_month']}/month"
                )
        elif response.status_code == 403:
            logger.info("⚠️ Organization listing requires super admin privileges")

        # Get usage analytics for demonstration
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        response = await self.client.get(
            f"{self.base_url}/enterprise/usage/analytics", params=params
        )

        if response.status_code == 200:
            analytics_data = response.json()
            summary = analytics_data.get("summary", {})
            logger.info("📈 Usage Analytics (30 days):")
            logger.info(f"  Total Requests: {summary.get('total_requests', 0):,}")
            logger.info(
                f"  Data Transfer: {summary.get('total_data_transfer_bytes', 0):,} bytes"
            )
            logger.info(f"  Total Cost: ${summary.get('total_cost', 0):.2f}")

        return True

    async def test_security_monitoring(self):
        """Test security and monitoring features."""

        logger.info("🔒 Testing Security and Monitoring...")

        # Get audit events
        params = {
            "limit": 10,
            "start_date": (datetime.utcnow() - timedelta(hours=24)).isoformat(),
        }

        response = await self.client.get(
            f"{self.base_url}/enterprise/audit/events", params=params
        )

        if response.status_code == 200:
            audit_data = response.json()
            logger.info(f"📋 Recent Audit Events: {audit_data.get('total_count', 0)}")

            for event in audit_data.get("events", [])[:5]:
                logger.info(
                    f"  {event['timestamp']}: {event['event_type']} - {event['outcome']}"
                )

        # Get policy violations
        response = await self.client.get(
            f"{self.base_url}/enterprise/governance/violations?limit=10"
        )

        if response.status_code == 200:
            violations_data = response.json()
            logger.info(
                f"⚠️ Policy Violations: {violations_data.get('total_count', 0)}"
            )

            for violation in violations_data.get("violations", [])[:5]:
                logger.info(f"  {violation['severity']}: {violation['description']}")

        # Test SLA metrics
        params = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "end_date": datetime.utcnow().isoformat(),
        }

        response = await self.client.get(
            f"{self.base_url}/enterprise/usage/sla", params=params
        )

        if response.status_code == 200:
            sla_data = response.json()
            logger.info("📊 SLA Metrics (7 days):")
            metrics = sla_data.get("metrics", {})

            if "availability" in metrics:
                avail = metrics["availability"]
                logger.info(
                    f"  Availability: {avail['actual']:.2f}% (target: {avail['target']:.2f}%)"
                )

            if "avg_response_time" in metrics:
                resp_time = metrics["avg_response_time"]
                logger.info(
                    f"  Avg Response Time: {resp_time['actual']:.0f}ms (target: {resp_time['target']:.0f}ms)"
                )

        return True

    async def show_analytics_and_reporting(self):
        """Show analytics and reporting capabilities."""

        logger.info("📈 Showing Analytics and Reporting...")

        # Get dashboard summary
        response = await self.client.get(
            f"{self.base_url}/enterprise/dashboard/summary"
        )

        if response.status_code == 200:
            dashboard_data = response.json()

            logger.info("🎯 Enterprise Dashboard Summary:")
            logger.info(f"  Organization: {dashboard_data['organization']['name']}")
            logger.info(f"  Tier: {dashboard_data['organization']['tier']}")

            compliance = dashboard_data.get("compliance", {})
            logger.info(f"  Active Policies: {compliance.get('active_policies', 0)}")
            logger.info(
                f"  Compliance Score: {compliance.get('compliance_score', 0):.1f}%"
            )
            logger.info(
                f"  Recent Violations: {compliance.get('recent_violations', 0)}"
            )

            usage = dashboard_data.get("usage", {})
            logger.info(f"  API Requests (30d): {usage.get('api_requests_30d', 0):,}")
            logger.info(f"  Monthly Cost: ${usage.get('monthly_cost', 0):.2f}")

            sso = dashboard_data.get("sso", {})
            logger.info(f"  Active SSO Sessions: {sso.get('active_sessions', 0)}")
            logger.info(f"  Configured Providers: {sso.get('configured_providers', 0)}")

        # List policies
        response = await self.client.get(
            f"{self.base_url}/enterprise/governance/policies?limit=5"
        )

        if response.status_code == 200:
            policies_data = response.json()
            logger.info(f"📋 Active Policies: {policies_data.get('total_count', 0)}")

            for policy in policies_data.get("policies", []):
                logger.info(
                    f"  {policy['name']} ({policy['policy_type']}) - {policy['status']}"
                )

        return True


class EnterpriseClientDemo:
    """Demonstration of enterprise client integration."""

    def __init__(self, base_url: str, user_token: str):
        self.base_url = base_url
        self.user_token = user_token
        self.client = httpx.AsyncClient(
            timeout=30.0, headers={"Authorization": f"Bearer {user_token}"}
        )

    async def demonstrate_user_operations(self):
        """Demonstrate typical user operations under enterprise policies."""

        logger.info("👤 Demonstrating User Operations...")

        try:
            # Create a capsule with compliance context
            capsule_data = {
                "type": "conversation_capsule",
                "content": {
                    "conversation_id": "demo-conversation-123",
                    "messages": [
                        {
                            "role": "user",
                            "content": "Can you help me process this customer data?",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                        {
                            "role": "assistant",
                            "content": "I'll help you process the customer data while ensuring GDPR compliance.",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    ],
                },
                "metadata": {
                    "data_type": "customer_service",
                    "contains_pii": False,
                    "encryption": True,
                    "user_consent": True,
                    "transport_encryption": True,
                },
            }

            # This would be intercepted by governance policies
            response = await self.client.post(
                f"{self.base_url}/api/capsules", json=capsule_data
            )

            if response.status_code == 201:
                capsule = response.json()
                logger.info(
                    f"✅ Capsule created successfully: {capsule.get('capsule_id', 'N/A')}"
                )
            elif response.status_code == 403:
                logger.info("⚠️ Capsule creation blocked by governance policy")
            else:
                logger.warning(f"⚠️ Capsule creation response: {response.status_code}")

            # Check rate limiting headers
            if response.headers.get("X-RateLimit-Requests-Per-Minute-Remaining"):
                remaining = response.headers[
                    "X-RateLimit-Requests-Per-Minute-Remaining"
                ]
                logger.info(f"📊 Rate Limit Remaining: {remaining} requests/minute")

            # Get user's quota status
            response = await self.client.get(f"{self.base_url}/enterprise/usage/quotas")

            if response.status_code == 200:
                quota_data = response.json()
                logger.info("📊 User Quota Status:")
                for quota_type, status in quota_data.get("quotas", {}).items():
                    if status["usage_percent"] > 0:
                        logger.info(
                            f"  {quota_type}: {status['usage_percent']:.1f}% used"
                        )

        except Exception as e:
            logger.error(f"User operation demo failed: {e}")
        finally:
            await self.client.aclose()


async def main():
    """Main demonstration function."""

    # Configuration
    BASE_URL = "http://localhost:8000"  # Update with your UATP instance URL
    ADMIN_TOKEN = "your-admin-jwt-token"  # Update with actual admin token
    USER_TOKEN = "your-user-jwt-token"  # Update with actual user token

    logger.info("🌟 UATP Capsule Engine - Enterprise Integration Demo")
    logger.info("=" * 60)

    # Run admin demonstrations
    admin_demo = EnterpriseIntegrationDemo(BASE_URL, ADMIN_TOKEN)

    try:
        await admin_demo.run_complete_demo()
    except Exception as e:
        logger.error(f"Admin demo failed: {e}")

    logger.info("\n" + "=" * 60)

    # Run user demonstrations
    user_demo = EnterpriseClientDemo(BASE_URL, USER_TOKEN)

    try:
        await user_demo.demonstrate_user_operations()
    except Exception as e:
        logger.error(f"User demo failed: {e}")

    logger.info("\n🎉 Enterprise Integration Demo completed!")
    logger.info("Check the logs above for detailed results and any issues.")


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())
