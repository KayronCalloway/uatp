#!/usr/bin/env python3
"""
Simple mock API server for testing UATP frontend
"""

from datetime import datetime, timedelta
import json
import random
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Mock data
MOCK_CAPSULES = []
MOCK_TRUST_METRICS = []
MOCK_VIOLATIONS = []
MOCK_QUARANTINED = []


# Generate mock data
def generate_mock_capsules(count: int = 50):
    capsule_types = [
        "chat",
        "refusal",
        "introspective",
        "joint",
        "consent",
        "perspective",
        "governance",
    ]
    agents = ["agent-001", "agent-002", "agent-003", "agent-004", "agent-005"]

    for i in range(count):
        capsule = {
            "id": str(uuid.uuid4()),
            "type": random.choice(capsule_types),
            "content": f"Mock capsule content {i+1}. This is a sample capsule for testing the frontend application.",
            "agent_id": random.choice(agents),
            "timestamp": (
                datetime.now() - timedelta(hours=random.randint(0, 168))
            ).isoformat(),
            "metadata": {
                "source": "mock",
                "priority": random.choice(["high", "medium", "low"]),
                "tags": random.sample(
                    ["test", "development", "production", "ai", "demo"], 2
                ),
            },
        }
        MOCK_CAPSULES.append(capsule)


def generate_mock_trust_metrics():
    agents = ["agent-001", "agent-002", "agent-003", "agent-004", "agent-005"]

    for agent in agents:
        metric = {
            "agent_id": agent,
            "trust_score": random.randint(40, 100),
            "reputation": random.randint(50, 100),
            "violations": random.randint(0, 5),
            "last_updated": datetime.now().isoformat(),
        }
        MOCK_TRUST_METRICS.append(metric)


def generate_mock_violations():
    agents = ["agent-001", "agent-002", "agent-003", "agent-004"]
    violation_types = [
        "trust_violation",
        "policy_breach",
        "security_issue",
        "quota_exceeded",
    ]

    for i in range(random.randint(0, 3)):
        violation = {
            "agent_id": random.choice(agents),
            "type": random.choice(violation_types),
            "severity": random.choice(["low", "medium", "high"]),
            "description": f"Mock violation {i+1}: Test violation for development",
            "timestamp": (
                datetime.now() - timedelta(hours=random.randint(0, 24))
            ).isoformat(),
        }
        MOCK_VIOLATIONS.append(violation)


def generate_mock_quarantined():
    agents = ["agent-002", "agent-004"]

    for agent in agents:
        quarantine = {
            "agent_id": agent,
            "reason": "Trust violation detected",
            "quarantine_date": (
                datetime.now() - timedelta(hours=random.randint(1, 48))
            ).isoformat(),
        }
        MOCK_QUARANTINED.append(quarantine)


# Initialize mock data
generate_mock_capsules()
generate_mock_trust_metrics()
generate_mock_violations()
generate_mock_quarantined()


@app.route("/")
def index():
    return jsonify(
        {
            "service": "UATP Capsule Engine (Mock)",
            "version": "1.0.0-mock",
            "documentation": "Mock API for frontend testing",
        }
    )


@app.route("/health")
def health():
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0-mock",
            "engine": {
                "status": "running",
                "capsules": len(MOCK_CAPSULES),
                "trust_agents": len(MOCK_TRUST_METRICS),
            },
            "features": {
                "authentication": True,
                "capsule_management": True,
                "trust_monitoring": True,
                "chain_sealing": True,
            },
        }
    )


@app.route("/health/detailed")
def health_detailed():
    return health()


@app.route("/capsules")
def list_capsules():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    compress = request.args.get("compress", "false").lower() == "true"

    start = (page - 1) * per_page
    end = start + per_page

    capsules = MOCK_CAPSULES[start:end]

    if compress:
        # Simplified capsule data for compression
        capsules = [
            {
                "id": c["id"],
                "type": c["type"],
                "agent_id": c["agent_id"],
                "timestamp": c["timestamp"],
                "content_preview": c["content"][:100] + "..."
                if len(c["content"]) > 100
                else c["content"],
            }
            for c in capsules
        ]

    return jsonify({"capsules": capsules})


@app.route("/capsules/<capsule_id>")
def get_capsule(capsule_id):
    include_raw = request.args.get("include_raw", "false").lower() == "true"

    capsule = next((c for c in MOCK_CAPSULES if c["id"] == capsule_id), None)
    if not capsule:
        return jsonify({"error": "Capsule not found"}), 404

    response = {"capsule": capsule}

    if include_raw:
        response["raw_data"] = {
            "original_request": "mock_request_data",
            "processing_metadata": {
                "created_at": capsule["timestamp"],
                "processed_by": "mock_processor",
                "validation_status": "passed",
            },
        }

    return jsonify(response)


@app.route("/capsules/<capsule_id>/verify")
def verify_capsule(capsule_id):
    capsule = next((c for c in MOCK_CAPSULES if c["id"] == capsule_id), None)
    if not capsule:
        return jsonify({"error": "Capsule not found"}), 404

    # Mock verification - randomly pass/fail for testing
    verified = random.random() > 0.1  # 90% pass rate

    return jsonify(
        {
            "capsule_id": capsule_id,
            "verified": verified,
            "from_cache": False,
            "metadata_has_verify_key": True,
            "verification_error": None if verified else "Mock verification failure",
        }
    )


@app.route("/capsules/stats")
def capsule_stats():
    types = {}
    for capsule in MOCK_CAPSULES:
        capsule_type = capsule["type"]
        types[capsule_type] = types.get(capsule_type, 0) + 1

    unique_agents = len(set(c["agent_id"] for c in MOCK_CAPSULES))

    return jsonify(
        {
            "total_capsules": len(MOCK_CAPSULES),
            "types": types,
            "unique_agents": unique_agents,
        }
    )


@app.route("/trust/metrics")
def trust_metrics():
    return jsonify(MOCK_TRUST_METRICS)


@app.route("/trust/agent/<agent_id>/status")
def trust_agent_status(agent_id):
    metric = next((m for m in MOCK_TRUST_METRICS if m["agent_id"] == agent_id), None)
    if not metric:
        return jsonify({"error": "Agent not found"}), 404

    return jsonify(
        {
            "agent_id": agent_id,
            "trust_score": metric["trust_score"],
            "status": "active" if metric["trust_score"] > 60 else "restricted",
            "last_updated": metric["last_updated"],
        }
    )


@app.route("/trust/policies")
def trust_policies():
    return jsonify(
        {
            "policies": [
                {
                    "name": "minimum_trust_score",
                    "value": 40,
                    "description": "Minimum trust score required for agent activity",
                },
                {
                    "name": "violation_threshold",
                    "value": 3,
                    "description": "Maximum violations before quarantine",
                },
            ]
        }
    )


@app.route("/trust/violations/recent")
def recent_violations():
    return jsonify({"violations": MOCK_VIOLATIONS})


@app.route("/trust/agents/quarantined")
def quarantined_agents():
    return jsonify({"agents": MOCK_QUARANTINED})


@app.route("/metrics")
def metrics():
    # Simple Prometheus-style metrics
    return (
        """
# HELP uatp_capsules_total Total number of capsules
# TYPE uatp_capsules_total counter
uatp_capsules_total{type="all"} 50

# HELP uatp_agents_total Total number of agents
# TYPE uatp_agents_total counter
uatp_agents_total 5

# HELP uatp_trust_score_avg Average trust score
# TYPE uatp_trust_score_avg gauge
uatp_trust_score_avg 75.2
""",
        200,
        {"Content-Type": "text/plain"},
    )


@app.route("/reasoning/validate", methods=["POST"])
def validate_reasoning():
    data = request.get_json()

    return jsonify(
        {
            "valid": True,
            "errors": [],
            "warnings": ["Mock validation warning"],
            "confidence": 0.95,
        }
    )


@app.route("/reasoning/analyze", methods=["POST"])
def analyze_reasoning():
    data = request.get_json()

    return jsonify(
        {
            "analysis": {
                "complexity": "medium",
                "reasoning_type": "deductive",
                "confidence_score": 0.87,
            },
            "insights": [
                "Mock insight 1: Reasoning appears consistent",
                "Mock insight 2: Good logical flow detected",
            ],
            "confidence": 0.87,
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/ai/generate", methods=["POST"])
def generate_ai():
    data = request.get_json()

    return jsonify(
        {
            "status": "success",
            "generated_text": f'Mock AI response to: {data.get("prompt", "")}',
        }
    )


# Federation endpoints
@app.route("/federation/nodes", methods=["GET"])
def get_federation_nodes():
    nodes = [
        {
            "id": "node-001",
            "name": "UATP North America",
            "url": "https://na.uatp.network",
            "status": "online",
            "version": "7.0.0",
            "last_seen": datetime.now().isoformat(),
            "capsule_count": 15420,
            "agent_count": 2156,
            "trust_score": 0.94,
            "sync_progress": 100,
            "region": "North America",
            "latency": 45,
        },
        {
            "id": "node-002",
            "name": "UATP Europe",
            "url": "https://eu.uatp.network",
            "status": "online",
            "version": "7.0.0",
            "last_seen": (datetime.now() - timedelta(seconds=30)).isoformat(),
            "capsule_count": 12890,
            "agent_count": 1876,
            "trust_score": 0.91,
            "sync_progress": 100,
            "region": "Europe",
            "latency": 78,
        },
        {
            "id": "node-003",
            "name": "UATP Asia Pacific",
            "url": "https://ap.uatp.network",
            "status": "syncing",
            "version": "6.9.5",
            "last_seen": (datetime.now() - timedelta(minutes=2)).isoformat(),
            "capsule_count": 8945,
            "agent_count": 1234,
            "trust_score": 0.88,
            "sync_progress": 67,
            "region": "Asia Pacific",
            "latency": 156,
        },
    ]
    return jsonify(nodes)


@app.route("/federation/stats", methods=["GET"])
def get_federation_stats():
    return jsonify(
        {
            "total_nodes": 3,
            "online_nodes": 2,
            "total_capsules": 37255,
            "total_agents": 5266,
            "average_latency": 93,
            "sync_status": "degraded",
        }
    )


@app.route("/federation/nodes", methods=["POST"])
def add_federation_node():
    data = request.json
    node = {
        "id": str(uuid.uuid4()),
        "name": data.get("name", "New Node"),
        "url": data.get("url", ""),
        "region": data.get("region", "Unknown"),
        "status": "connecting",
        "version": "7.0.0",
        "last_seen": datetime.now().isoformat(),
        "capsule_count": 0,
        "agent_count": 0,
        "trust_score": 0.0,
        "sync_progress": 0,
        "latency": 0,
    }
    return jsonify(node), 201


@app.route("/federation/nodes/<node_id>/sync", methods=["POST"])
def sync_federation_node(node_id):
    return jsonify({"status": "syncing", "progress": 0})


# Governance endpoints
@app.route("/governance/proposals", methods=["GET"])
def get_proposals():
    proposals = [
        {
            "id": "prop-001",
            "title": "Adjust Trust Score Threshold for Economic Participation",
            "description": "Proposal to lower the minimum trust score required for economic participation from 0.85 to 0.80 to increase inclusion while maintaining security.",
            "category": "economic",
            "status": "active",
            "proposer": "governance-council",
            "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
            "voting_ends": (datetime.now() + timedelta(days=4)).isoformat(),
            "votes": {"for": 156, "against": 23, "abstain": 12},
            "quorum": 100,
            "participation_rate": 0.76,
            "comments": 28,
        },
        {
            "id": "prop-002",
            "title": "Implement Quarterly Trust Score Decay",
            "description": "Introduce a quarterly decay mechanism for trust scores to ensure active participation and prevent stagnation.",
            "category": "trust",
            "status": "active",
            "proposer": "trust-committee",
            "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
            "voting_ends": (datetime.now() + timedelta(days=5)).isoformat(),
            "votes": {"for": 89, "against": 67, "abstain": 15},
            "quorum": 100,
            "participation_rate": 0.68,
            "comments": 42,
        },
    ]
    return jsonify(proposals)


@app.route("/governance/proposals", methods=["POST"])
def create_proposal():
    data = request.json
    proposal = {
        "id": str(uuid.uuid4()),
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "category": data.get("category", "governance"),
        "status": "pending",
        "proposer": "user",
        "created_at": datetime.now().isoformat(),
        "voting_ends": (datetime.now() + timedelta(days=7)).isoformat(),
        "votes": {"for": 0, "against": 0, "abstain": 0},
        "quorum": 100,
        "participation_rate": 0.0,
        "comments": 0,
    }
    return jsonify(proposal), 201


@app.route("/governance/proposals/<proposal_id>/vote", methods=["POST"])
def vote_on_proposal(proposal_id):
    data = request.json
    vote = data.get("vote", "abstain")
    return jsonify({"status": "voted", "vote": vote})


@app.route("/governance/stats", methods=["GET"])
def get_governance_stats():
    return jsonify(
        {
            "active_proposals": 2,
            "total_voters": 251,
            "average_participation": 0.72,
            "recent_decisions": 5,
        }
    )


# Analytics endpoints
@app.route("/analytics", methods=["GET"])
def get_analytics():
    return jsonify(
        {
            "total_capsules": len(MOCK_CAPSULES),
            "trust_metrics": len(MOCK_TRUST_METRICS),
            "violations": len(MOCK_VIOLATIONS),
            "quarantined": len(MOCK_QUARANTINED),
        }
    )


@app.route("/economics/metrics", methods=["GET"])
def get_economic_metrics():
    return jsonify(
        {
            "total_attribution_value": 125420.50,
            "monthly_dividends": 8945.75,
            "common_fund_balance": 89234.25,
            "total_payouts": 567890.00,
            "active_contributors": 2156,
            "average_contribution": 58.25,
        }
    )


# Organization endpoints
@app.route("/organization", methods=["GET"])
def get_organization():
    return jsonify(
        {
            "id": "org-001",
            "name": "AI Research Collective",
            "description": "Advanced AI research organization focused on ethical AI development and attribution systems.",
            "type": "research",
            "created_at": "2024-01-15T10:00:00Z",
            "member_count": 24,
            "tier": "enterprise",
            "settings": {
                "public_profile": True,
                "allow_invites": True,
                "require_approval": False,
                "trust_threshold": 0.75,
            },
            "metrics": {
                "total_capsules": 1547,
                "monthly_contributions": 342,
                "average_trust_score": 0.87,
                "economic_value": 45890.50,
            },
        }
    )


@app.route("/organization/members", methods=["GET"])
def get_organization_members():
    members = [
        {
            "id": "member-001",
            "name": "Dr. Sarah Chen",
            "email": "sarah.chen@research.org",
            "role": "owner",
            "joined_at": "2024-01-15T10:00:00Z",
            "last_active": "2024-01-16T14:30:00Z",
            "trust_score": 0.95,
            "contribution_level": "high",
        },
        {
            "id": "member-002",
            "name": "Alex Rodriguez",
            "email": "alex.r@research.org",
            "role": "admin",
            "joined_at": "2024-01-20T09:15:00Z",
            "last_active": "2024-01-16T12:45:00Z",
            "trust_score": 0.89,
            "contribution_level": "high",
        },
    ]
    return jsonify(members)


@app.route("/organization/invite", methods=["POST"])
def invite_organization_member():
    data = request.json
    return jsonify(
        {
            "status": "sent",
            "email": data.get("email"),
            "message": "Invitation sent successfully",
        }
    )


# Advanced attribution endpoints
@app.route("/attribution/models", methods=["GET"])
def get_attribution_models():
    models = [
        {
            "id": "direct",
            "name": "Direct Contribution",
            "type": "direct",
            "description": "Simple attribution based on direct capsule contributions",
            "weight": 0.3,
            "active": True,
        },
        {
            "id": "collaborative",
            "name": "Collaborative Impact",
            "type": "collaborative",
            "description": "Attribution based on joint capsule creation and cross-references",
            "weight": 0.25,
            "active": True,
        },
    ]
    return jsonify(models)


@app.route("/attribution/analysis", methods=["GET"])
def get_attribution_analysis():
    return jsonify(
        {
            "model": "hybrid",
            "timestamp": datetime.now().isoformat(),
            "total_value": 567890.25,
            "participants": 2156,
            "results": [
                {
                    "agent_id": "agent-001",
                    "agent_name": "Dr. Sarah Chen",
                    "total_attribution": 12847.50,
                    "breakdown": {
                        "direct": 4500.00,
                        "collaborative": 3200.00,
                        "temporal": 2500.00,
                        "network": 1800.00,
                        "impact": 847.50,
                    },
                    "rank": 1,
                    "change": 0.15,
                }
            ],
            "convergence": 0.94,
        }
    )


@app.route("/attribution/compute", methods=["POST"])
def compute_attribution():
    data = request.json
    return jsonify(
        {
            "status": "computing",
            "job_id": str(uuid.uuid4()),
            "estimated_completion": (datetime.now() + timedelta(minutes=5)).isoformat(),
        }
    )


if __name__ == "__main__":
    print("🚀 Starting UATP Mock API Server")
    print("📊 Generated mock data:")
    print(f"   • {len(MOCK_CAPSULES)} capsules")
    print(f"   • {len(MOCK_TRUST_METRICS)} trust metrics")
    print(f"   • {len(MOCK_VIOLATIONS)} violations")
    print(f"   • {len(MOCK_QUARANTINED)} quarantined agents")
    print("✅ Server running at http://localhost:8000")
    print("🔗 Test frontend at http://localhost:3000")
    print("🔑 Use any API key (e.g., 'test-key-123') to authenticate")

    app.run(host="0.0.0.0", port=8000, debug=True)
