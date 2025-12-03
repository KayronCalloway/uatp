"""
Organization API Routes
======================

API endpoints for organization management including members, invitations, and organization settings.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

from quart import Blueprint, jsonify, request, g
from quart_schema import validation

from ..database.models import (
    Organization,
    OrganizationMember,
    OrganizationInvitation,
    OrganizationRole,
    InvitationStatus,
    generate_id,
    utc_now,
)
from .dependencies import require_api_key

organization_bp = Blueprint("organization", __name__)


@organization_bp.route("/", methods=["GET"])
@require_api_key(["read"])
async def get_organization():
    """Get organization details."""
    try:
        # In a real implementation, this would query the database
        # For now, we'll return mock organization data
        organization = {
            "organization_id": "org_001",
            "name": "UATP Foundation",
            "description": "The Universal AI Attribution Protocol Foundation is dedicated to advancing fair attribution in AI systems.",
            "created_at": (datetime.now() - timedelta(days=365)).isoformat(),
            "updated_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "settings": {
                "default_member_role": "member",
                "invitation_expiry_days": 7,
                "require_approval_for_members": True,
                "allow_public_capsules": True,
                "enable_analytics": True,
                "max_api_keys_per_member": 5,
            },
            "billing_info": {
                "plan": "enterprise",
                "billing_email": "billing@uatp.ai",
                "subscription_status": "active",
                "next_billing_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "monthly_cost": 2999.99,
                "usage_limits": {
                    "max_members": 100,
                    "max_capsules": 10000,
                    "max_api_requests": 1000000,
                },
            },
            "metadata": {
                "industry": "AI/ML",
                "company_size": "50-100",
                "region": "global",
                "compliance_requirements": ["GDPR", "CCPA", "SOC2"],
            },
            "statistics": {
                "total_members": 23,
                "total_capsules": 1547,
                "total_api_requests": 45892,
                "active_members_last_30_days": 18,
            },
        }

        return jsonify(organization)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@organization_bp.route("/members", methods=["GET"])
@require_api_key(["read"])
async def get_organization_members():
    """Get organization members."""
    try:
        # In a real implementation, this would query the database
        # For now, we'll return mock member data
        members = [
            {
                "member_id": "member_001",
                "organization_id": "org_001",
                "user_id": "user_001",
                "role": "owner",
                "joined_at": (datetime.now() - timedelta(days=365)).isoformat(),
                "updated_at": (datetime.now() - timedelta(days=30)).isoformat(),
                "permissions": ["read", "write", "admin", "billing", "members"],
                "user_info": {
                    "name": "Alice Johnson",
                    "email": "alice@uatp.ai",
                    "avatar": "https://avatars.uatp.ai/user_001.jpg",
                    "status": "active",
                    "last_active": (datetime.now() - timedelta(hours=2)).isoformat(),
                },
                "activity_stats": {
                    "capsules_created": 127,
                    "api_requests_last_30_days": 2547,
                    "last_login": (datetime.now() - timedelta(hours=2)).isoformat(),
                },
                "metadata": {
                    "department": "Engineering",
                    "title": "CTO",
                    "timezone": "UTC-8",
                },
            },
            {
                "member_id": "member_002",
                "organization_id": "org_001",
                "user_id": "user_002",
                "role": "admin",
                "joined_at": (datetime.now() - timedelta(days=300)).isoformat(),
                "updated_at": (datetime.now() - timedelta(days=5)).isoformat(),
                "permissions": ["read", "write", "admin", "members"],
                "user_info": {
                    "name": "Bob Smith",
                    "email": "bob@uatp.ai",
                    "avatar": "https://avatars.uatp.ai/user_002.jpg",
                    "status": "active",
                    "last_active": (datetime.now() - timedelta(hours=6)).isoformat(),
                },
                "activity_stats": {
                    "capsules_created": 89,
                    "api_requests_last_30_days": 1823,
                    "last_login": (datetime.now() - timedelta(hours=6)).isoformat(),
                },
                "metadata": {
                    "department": "Research",
                    "title": "Lead Researcher",
                    "timezone": "UTC-5",
                },
            },
            {
                "member_id": "member_003",
                "organization_id": "org_001",
                "user_id": "user_003",
                "role": "member",
                "joined_at": (datetime.now() - timedelta(days=180)).isoformat(),
                "updated_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "permissions": ["read", "write"],
                "user_info": {
                    "name": "Carol Williams",
                    "email": "carol@uatp.ai",
                    "avatar": "https://avatars.uatp.ai/user_003.jpg",
                    "status": "active",
                    "last_active": (datetime.now() - timedelta(hours=1)).isoformat(),
                },
                "activity_stats": {
                    "capsules_created": 45,
                    "api_requests_last_30_days": 967,
                    "last_login": (datetime.now() - timedelta(hours=1)).isoformat(),
                },
                "metadata": {
                    "department": "Engineering",
                    "title": "Senior Developer",
                    "timezone": "UTC+1",
                },
            },
            {
                "member_id": "member_004",
                "organization_id": "org_001",
                "user_id": "user_004",
                "role": "member",
                "joined_at": (datetime.now() - timedelta(days=90)).isoformat(),
                "updated_at": (datetime.now() - timedelta(days=7)).isoformat(),
                "permissions": ["read", "write"],
                "user_info": {
                    "name": "David Chen",
                    "email": "david@uatp.ai",
                    "avatar": "https://avatars.uatp.ai/user_004.jpg",
                    "status": "active",
                    "last_active": (datetime.now() - timedelta(days=3)).isoformat(),
                },
                "activity_stats": {
                    "capsules_created": 23,
                    "api_requests_last_30_days": 445,
                    "last_login": (datetime.now() - timedelta(days=3)).isoformat(),
                },
                "metadata": {
                    "department": "Operations",
                    "title": "DevOps Engineer",
                    "timezone": "UTC+8",
                },
            },
            {
                "member_id": "member_005",
                "organization_id": "org_001",
                "user_id": "user_005",
                "role": "viewer",
                "joined_at": (datetime.now() - timedelta(days=30)).isoformat(),
                "updated_at": (datetime.now() - timedelta(days=15)).isoformat(),
                "permissions": ["read"],
                "user_info": {
                    "name": "Emma Davis",
                    "email": "emma@uatp.ai",
                    "avatar": "https://avatars.uatp.ai/user_005.jpg",
                    "status": "active",
                    "last_active": (datetime.now() - timedelta(hours=12)).isoformat(),
                },
                "activity_stats": {
                    "capsules_created": 0,
                    "api_requests_last_30_days": 123,
                    "last_login": (datetime.now() - timedelta(hours=12)).isoformat(),
                },
                "metadata": {
                    "department": "Business",
                    "title": "Product Manager",
                    "timezone": "UTC-7",
                },
            },
        ]

        return jsonify(members)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@organization_bp.route("/members/<member_id>", methods=["GET"])
@require_api_key(["read"])
async def get_organization_member(member_id: str):
    """Get a specific organization member."""
    try:
        # In a real implementation, this would query the database
        # For now, we'll return mock data based on member_id
        if member_id == "member_001":
            member = {
                "member_id": "member_001",
                "organization_id": "org_001",
                "user_id": "user_001",
                "role": "owner",
                "joined_at": (datetime.now() - timedelta(days=365)).isoformat(),
                "updated_at": (datetime.now() - timedelta(days=30)).isoformat(),
                "permissions": ["read", "write", "admin", "billing", "members"],
                "user_info": {
                    "name": "Alice Johnson",
                    "email": "alice@uatp.ai",
                    "avatar": "https://avatars.uatp.ai/user_001.jpg",
                    "status": "active",
                    "last_active": (datetime.now() - timedelta(hours=2)).isoformat(),
                },
                "activity_stats": {
                    "capsules_created": 127,
                    "api_requests_last_30_days": 2547,
                    "last_login": (datetime.now() - timedelta(hours=2)).isoformat(),
                },
                "metadata": {
                    "department": "Engineering",
                    "title": "CTO",
                    "timezone": "UTC-8",
                },
            }
            return jsonify(member)
        else:
            return jsonify({"error": "Member not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@organization_bp.route("/invite", methods=["POST"])
@require_api_key(["admin"])
async def invite_organization_member():
    """Invite a new member to the organization."""
    try:
        data = await request.get_json()

        # Validate required fields
        if "email" not in data:
            return jsonify({"error": "Missing required field: email"}), 400

        # Create invitation
        invitation_id = generate_id()
        invitation = {
            "invitation_id": invitation_id,
            "organization_id": "org_001",
            "email": data["email"],
            "role": data.get("role", "member"),
            "status": "pending",
            "invited_by": g.api_key_data.get("agent_id", "unknown"),
            "invited_at": utc_now().isoformat(),
            "expires_at": (utc_now() + timedelta(days=7)).isoformat(),
            "accepted_at": None,
            "rejected_at": None,
            "metadata": {
                "invite_message": data.get("message", ""),
                "department": data.get("department", ""),
                "title": data.get("title", ""),
            },
        }

        # In a real implementation, this would:
        # 1. Save invitation to database
        # 2. Send invitation email
        # 3. Create user account if needed

        return (
            jsonify(
                {"message": "Invitation sent successfully", "invitation": invitation}
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@organization_bp.route("/invitations", methods=["GET"])
@require_api_key(["read"])
async def get_organization_invitations():
    """Get organization invitations."""
    try:
        # In a real implementation, this would query the database
        # For now, we'll return mock invitation data
        invitations = [
            {
                "invitation_id": "inv_001",
                "organization_id": "org_001",
                "email": "john@example.com",
                "role": "member",
                "status": "pending",
                "invited_by": "user_001",
                "invited_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "expires_at": (datetime.now() + timedelta(days=5)).isoformat(),
                "accepted_at": None,
                "rejected_at": None,
                "metadata": {
                    "invite_message": "Welcome to the UATP Foundation!",
                    "department": "Engineering",
                    "title": "Software Engineer",
                },
            },
            {
                "invitation_id": "inv_002",
                "organization_id": "org_001",
                "email": "sarah@example.com",
                "role": "viewer",
                "status": "accepted",
                "invited_by": "user_002",
                "invited_at": (datetime.now() - timedelta(days=10)).isoformat(),
                "expires_at": (datetime.now() - timedelta(days=3)).isoformat(),
                "accepted_at": (datetime.now() - timedelta(days=8)).isoformat(),
                "rejected_at": None,
                "metadata": {
                    "invite_message": "Join our research team!",
                    "department": "Research",
                    "title": "Research Analyst",
                },
            },
            {
                "invitation_id": "inv_003",
                "organization_id": "org_001",
                "email": "mark@example.com",
                "role": "admin",
                "status": "expired",
                "invited_by": "user_001",
                "invited_at": (datetime.now() - timedelta(days=15)).isoformat(),
                "expires_at": (datetime.now() - timedelta(days=8)).isoformat(),
                "accepted_at": None,
                "rejected_at": None,
                "metadata": {
                    "invite_message": "We need your expertise!",
                    "department": "Operations",
                    "title": "Senior Manager",
                },
            },
        ]

        return jsonify(invitations)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@organization_bp.route("/members/<member_id>/role", methods=["PUT"])
@require_api_key(["admin"])
async def update_member_role(member_id: str):
    """Update a member's role."""
    try:
        data = await request.get_json()

        # Validate required fields
        if "role" not in data:
            return jsonify({"error": "Missing required field: role"}), 400

        # Validate role
        valid_roles = ["owner", "admin", "member", "viewer"]
        if data["role"] not in valid_roles:
            return (
                jsonify({"error": f"Invalid role. Must be one of: {valid_roles}"}),
                400,
            )

        # In a real implementation, this would:
        # 1. Update member role in database
        # 2. Update permissions
        # 3. Send notification to member

        return (
            jsonify(
                {
                    "message": "Member role updated successfully",
                    "member_id": member_id,
                    "new_role": data["role"],
                    "updated_at": utc_now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@organization_bp.route("/members/<member_id>", methods=["DELETE"])
@require_api_key(["admin"])
async def remove_organization_member(member_id: str):
    """Remove a member from the organization."""
    try:
        # In a real implementation, this would:
        # 1. Remove member from database
        # 2. Revoke API keys
        # 3. Transfer ownership of capsules if needed
        # 4. Send notification

        return (
            jsonify(
                {
                    "message": "Member removed successfully",
                    "member_id": member_id,
                    "removed_at": utc_now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@organization_bp.route("/settings", methods=["GET"])
@require_api_key(["read"])
async def get_organization_settings():
    """Get organization settings."""
    try:
        # In a real implementation, this would query the database
        # For now, we'll return mock settings
        settings = {
            "organization_id": "org_001",
            "general": {
                "name": "UATP Foundation",
                "description": "The Universal AI Attribution Protocol Foundation",
                "website": "https://uatp.ai",
                "logo": "https://assets.uatp.ai/logo.png",
                "timezone": "UTC",
            },
            "members": {
                "default_role": "member",
                "require_approval": True,
                "invitation_expiry_days": 7,
                "max_members": 100,
            },
            "api": {
                "max_keys_per_member": 5,
                "rate_limit_per_key": 1000,
                "enable_webhooks": True,
            },
            "security": {
                "require_2fa": False,
                "session_timeout": 8,
                "ip_whitelist": [],
                "audit_logs_retention_days": 90,
            },
            "billing": {
                "plan": "enterprise",
                "billing_email": "billing@uatp.ai",
                "auto_renew": True,
            },
            "features": {
                "enable_analytics": True,
                "enable_federation": True,
                "enable_governance": True,
                "enable_economics": True,
            },
        }

        return jsonify(settings)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@organization_bp.route("/settings", methods=["PUT"])
@require_api_key(["admin"])
async def update_organization_settings():
    """Update organization settings."""
    try:
        data = await request.get_json()

        # In a real implementation, this would:
        # 1. Validate settings
        # 2. Update settings in database
        # 3. Apply changes to the system

        return (
            jsonify(
                {
                    "message": "Organization settings updated successfully",
                    "updated_at": utc_now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@organization_bp.route("/usage", methods=["GET"])
@require_api_key(["read"])
async def get_organization_usage():
    """Get organization usage statistics."""
    try:
        # In a real implementation, this would query usage data
        # For now, we'll return mock usage statistics
        usage = {
            "organization_id": "org_001",
            "period": {
                "start": (datetime.now() - timedelta(days=30)).isoformat(),
                "end": datetime.now().isoformat(),
            },
            "summary": {
                "total_api_requests": 45892,
                "total_capsules": 1547,
                "total_members": 23,
                "storage_used_gb": 12.7,
            },
            "limits": {
                "max_api_requests": 1000000,
                "max_capsules": 10000,
                "max_members": 100,
                "max_storage_gb": 1000,
            },
            "daily_usage": [
                {
                    "date": (datetime.now() - timedelta(days=7)).date().isoformat(),
                    "api_requests": 1547,
                    "capsules_created": 23,
                    "storage_used_gb": 12.3,
                },
                {
                    "date": (datetime.now() - timedelta(days=6)).date().isoformat(),
                    "api_requests": 1823,
                    "capsules_created": 31,
                    "storage_used_gb": 12.5,
                },
                {
                    "date": (datetime.now() - timedelta(days=5)).date().isoformat(),
                    "api_requests": 1689,
                    "capsules_created": 19,
                    "storage_used_gb": 12.6,
                },
            ],
            "top_users": [
                {
                    "user_id": "user_001",
                    "name": "Alice Johnson",
                    "api_requests": 2547,
                    "capsules_created": 127,
                },
                {
                    "user_id": "user_002",
                    "name": "Bob Smith",
                    "api_requests": 1823,
                    "capsules_created": 89,
                },
            ],
        }

        return jsonify(usage)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
