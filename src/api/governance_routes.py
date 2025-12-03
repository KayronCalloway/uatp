"""
Governance API Routes
====================

API endpoints for governance features including proposals, voting, and governance statistics.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

from quart import Blueprint, jsonify, request, g
from quart_schema import validation

from ..database.models import (
    Proposal,
    Vote,
    ProposalStatus,
    ProposalCategory,
    VoteChoice,
    generate_id,
    utc_now,
)
from .dependencies import require_api_key

governance_bp = Blueprint("governance", __name__)


@governance_bp.route("/proposals", methods=["GET", "OPTIONS"])
@require_api_key(["read"])
async def get_proposals():
    """Get all governance proposals."""
    try:
        # In a real implementation, this would query the database
        # For now, we'll return mock data that matches the frontend expectations
        proposals = [
            {
                "proposal_id": "prop_001",
                "title": "Increase Agent Trust Score Threshold",
                "description": "Proposal to increase the minimum trust score threshold for new agents from 0.7 to 0.8 to improve system security.",
                "category": "governance",
                "status": "active",
                "created_by": "agent-admin-001",
                "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
                "updated_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "voting_starts_at": (datetime.now() - timedelta(days=5)).isoformat(),
                "voting_ends_at": (datetime.now() + timedelta(days=3)).isoformat(),
                "quorum_required": 100,
                "votes_for": 45,
                "votes_against": 12,
                "votes_abstain": 8,
                "implementation_details": {
                    "code_changes": ["src/trust/scoring.py"],
                    "migration_required": True,
                },
                "impact_assessment": {"affected_agents": 250, "risk_level": "medium"},
                "metadata": {},
            },
            {
                "proposal_id": "prop_002",
                "title": "Economic Attribution Model Update",
                "description": "Update the economic attribution model to better reflect collaborative AI contributions.",
                "category": "economic",
                "status": "active",
                "created_by": "agent-econ-001",
                "created_at": (datetime.now() - timedelta(days=14)).isoformat(),
                "updated_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "voting_starts_at": (datetime.now() - timedelta(days=10)).isoformat(),
                "voting_ends_at": (datetime.now() + timedelta(days=5)).isoformat(),
                "quorum_required": 150,
                "votes_for": 89,
                "votes_against": 23,
                "votes_abstain": 15,
                "implementation_details": {
                    "code_changes": ["src/economic/attribution.py"],
                    "migration_required": False,
                },
                "impact_assessment": {"affected_agents": 500, "risk_level": "high"},
                "metadata": {},
            },
            {
                "proposal_id": "prop_003",
                "title": "New Capsule Type: Research Collaboration",
                "description": "Introduce a new capsule type specifically for research collaboration between AI agents.",
                "category": "technical",
                "status": "draft",
                "created_by": "agent-research-001",
                "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
                "updated_at": (datetime.now() - timedelta(hours=6)).isoformat(),
                "voting_starts_at": (datetime.now() + timedelta(days=2)).isoformat(),
                "voting_ends_at": (datetime.now() + timedelta(days=12)).isoformat(),
                "quorum_required": 100,
                "votes_for": 0,
                "votes_against": 0,
                "votes_abstain": 0,
                "implementation_details": {
                    "code_changes": [
                        "src/capsules/types.py",
                        "src/capsules/research.py",
                    ],
                    "migration_required": True,
                },
                "impact_assessment": {"affected_agents": 100, "risk_level": "low"},
                "metadata": {},
            },
        ]

        return jsonify(proposals)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@governance_bp.route("/proposals/<proposal_id>", methods=["GET"])
@require_api_key(["read"])
async def get_proposal(proposal_id: str):
    """Get a specific governance proposal."""
    try:
        # In a real implementation, this would query the database
        # For now, we'll return mock data based on the proposal_id
        if proposal_id == "prop_001":
            proposal = {
                "proposal_id": "prop_001",
                "title": "Increase Agent Trust Score Threshold",
                "description": "Proposal to increase the minimum trust score threshold for new agents from 0.7 to 0.8 to improve system security.",
                "category": "governance",
                "status": "active",
                "created_by": "agent-admin-001",
                "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
                "updated_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "voting_starts_at": (datetime.now() - timedelta(days=5)).isoformat(),
                "voting_ends_at": (datetime.now() + timedelta(days=3)).isoformat(),
                "quorum_required": 100,
                "votes_for": 45,
                "votes_against": 12,
                "votes_abstain": 8,
                "implementation_details": {
                    "code_changes": ["src/trust/scoring.py"],
                    "migration_required": True,
                    "estimated_effort": "2 weeks",
                    "dependencies": ["trust-system-update"],
                },
                "impact_assessment": {
                    "affected_agents": 250,
                    "risk_level": "medium",
                    "benefits": ["Improved security", "Better agent quality"],
                    "risks": ["Potential exclusion of legitimate agents"],
                },
                "metadata": {
                    "discussion_url": "https://governance.uatp.ai/proposals/prop_001",
                    "related_issues": ["issue-123", "issue-456"],
                },
            }
            return jsonify(proposal)
        else:
            return jsonify({"error": "Proposal not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@governance_bp.route("/proposals", methods=["POST"])
@require_api_key(["write"])
async def create_proposal():
    """Create a new governance proposal."""
    try:
        data = await request.get_json()

        # Validate required fields
        required_fields = ["title", "description", "category"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Create new proposal
        proposal_id = generate_id()
        proposal = {
            "proposal_id": proposal_id,
            "title": data["title"],
            "description": data["description"],
            "category": data["category"],
            "status": "draft",
            "created_by": g.api_key_data.get("agent_id", "unknown"),
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat(),
            "voting_starts_at": (utc_now() + timedelta(days=3)).isoformat(),
            "voting_ends_at": (utc_now() + timedelta(days=10)).isoformat(),
            "quorum_required": data.get("quorum_required", 100),
            "votes_for": 0,
            "votes_against": 0,
            "votes_abstain": 0,
            "implementation_details": data.get("implementation_details", {}),
            "impact_assessment": data.get("impact_assessment", {}),
            "metadata": data.get("metadata", {}),
        }

        # In a real implementation, this would save to database
        # For now, we'll just return the created proposal

        return jsonify(proposal), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@governance_bp.route("/proposals/<proposal_id>/vote", methods=["POST"])
@require_api_key(["write"])
async def vote_on_proposal(proposal_id: str):
    """Vote on a governance proposal."""
    try:
        data = await request.get_json()

        # Validate vote choice
        if "vote" not in data:
            return jsonify({"error": "Missing vote choice"}), 400

        vote_choice = data["vote"]
        if vote_choice not in ["for", "against", "abstain"]:
            return (
                jsonify(
                    {
                        "error": "Invalid vote choice. Must be 'for', 'against', or 'abstain'"
                    }
                ),
                400,
            )

        # Create vote record
        vote = {
            "vote_id": generate_id(),
            "proposal_id": proposal_id,
            "voter_id": g.api_key_data.get("agent_id", "unknown"),
            "choice": vote_choice,
            "timestamp": utc_now().isoformat(),
            "voting_power": 1.0,
            "rationale": data.get("rationale"),
            "metadata": data.get("metadata", {}),
        }

        # In a real implementation, this would:
        # 1. Check if user has already voted
        # 2. Validate voting period
        # 3. Save vote to database
        # 4. Update proposal vote counts

        return jsonify({"message": "Vote recorded successfully", "vote": vote}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@governance_bp.route("/stats", methods=["GET", "OPTIONS"])
@require_api_key(["read"])
async def get_governance_stats():
    """Get governance statistics."""
    try:
        # In a real implementation, this would query the database
        # For now, we'll return mock statistics
        stats = {
            "total_proposals": 15,
            "active_proposals": 3,
            "passed_proposals": 8,
            "rejected_proposals": 2,
            "total_votes": 1247,
            "unique_voters": 89,
            "average_participation": 0.67,
            "proposals_by_category": {
                "governance": 5,
                "economic": 4,
                "technical": 3,
                "protocol": 2,
                "community": 1,
            },
            "recent_activity": {
                "last_7_days": {
                    "new_proposals": 2,
                    "new_votes": 67,
                    "proposals_passed": 1,
                },
                "last_30_days": {
                    "new_proposals": 8,
                    "new_votes": 289,
                    "proposals_passed": 3,
                },
            },
            "upcoming_deadlines": [
                {
                    "proposal_id": "prop_001",
                    "title": "Increase Agent Trust Score Threshold",
                    "voting_ends_at": (datetime.now() + timedelta(days=3)).isoformat(),
                },
                {
                    "proposal_id": "prop_002",
                    "title": "Economic Attribution Model Update",
                    "voting_ends_at": (datetime.now() + timedelta(days=5)).isoformat(),
                },
            ],
        }

        return jsonify(stats)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@governance_bp.route("/proposals/<proposal_id>/votes", methods=["GET"])
@require_api_key(["read"])
async def get_proposal_votes(proposal_id: str):
    """Get votes for a specific proposal."""
    try:
        # In a real implementation, this would query the database
        # For now, we'll return mock vote data
        votes = [
            {
                "vote_id": "vote_001",
                "proposal_id": proposal_id,
                "voter_id": "agent-001",
                "choice": "for",
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "voting_power": 1.0,
                "rationale": "This proposal will improve system security.",
            },
            {
                "vote_id": "vote_002",
                "proposal_id": proposal_id,
                "voter_id": "agent-002",
                "choice": "against",
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "voting_power": 1.0,
                "rationale": "The threshold is too restrictive.",
            },
            {
                "vote_id": "vote_003",
                "proposal_id": proposal_id,
                "voter_id": "agent-003",
                "choice": "abstain",
                "timestamp": (datetime.now() - timedelta(hours=12)).isoformat(),
                "voting_power": 1.0,
                "rationale": "Need more information before deciding.",
            },
        ]

        return jsonify(votes)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
