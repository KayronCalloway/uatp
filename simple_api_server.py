#!/usr/bin/env python3
"""
Simple API server for testing the frontend without complex dependencies
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import random

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:3001"])


# Mock data - Generate 50+ capsules
def generate_mock_capsules():
    capsules = []
    # Frontend expected types
    capsule_types = [
        "chat",
        "joint",
        "introspective",
        "refusal",
        "consent",
        "perspective",
    ]
    agents = [f"agent-{i:03d}" for i in range(1, 21)]
    content_samples = {
        "chat": "Hello, how can I help you today?",
        "joint": "I can assist with various tasks.",
        "introspective": "Analyzing my own reasoning process...",
        "refusal": "I cannot provide that information.",
        "consent": "User has provided explicit consent for data processing.",
        "perspective": "From my perspective, this approach would work best.",
    }

    for i in range(55):  # Generate 55 capsules
        capsule_id = f"capsule-{i+1}"
        capsule_type = random.choice(capsule_types)
        parent_id = (
            f"capsule-{random.randint(1, max(1, i))}"
            if i > 0 and random.random() > 0.3
            else None
        )

        capsules.append(
            {
                "id": capsule_id,
                "capsule_id": capsule_id,
                "type": capsule_type,  # Frontend expects 'type' not 'capsule_type'
                "timestamp": f"2024-01-{(i % 30) + 1:02d}T{random.randint(8, 18):02d}:{random.randint(0, 59):02d}:00Z",
                "verification": {
                    "hash": f"hash_{random.randint(1000000, 9999999)}",
                    "verified": True,
                    "signer": random.choice(agents),
                    "signature": f"ed25519:{random.randint(1000000000, 9999999999):010x}"
                    + "0" * 102,
                    "merkle_root": f"sha256:{'0' * 64}",
                },
                "content": {  # Frontend expects content as object
                    "type": capsule_type,
                    "content": content_samples[capsule_type],
                },
                "lineage": {  # Frontend expects lineage info
                    "parent_id": parent_id,
                    "depth": 1 if parent_id else 0,
                },
                "agent_id": random.choice(agents),
                "trust_score": round(random.uniform(0.75, 0.98), 2),
            }
        )

    return capsules


MOCK_CAPSULES = generate_mock_capsules()


@app.route("/health", methods=["GET", "OPTIONS"])
def health_check():
    return jsonify(
        {
            "status": "healthy",
            "version": "1.0.0",
            "engine": "OK",
            "database": "ok",
            "features": {"caching": False, "rate_limiting": True},
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@app.route("/capsules", methods=["GET", "OPTIONS"])
def list_capsules():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    compress = request.args.get("compress", "false").lower() == "true"

    # Simple pagination
    start = (page - 1) * per_page
    end = start + per_page

    capsules = MOCK_CAPSULES[start:end]

    if compress:
        # Compressed format
        return jsonify(
            {
                "capsules": [
                    {
                        "id": cap["id"],
                        "type": cap["capsule_type"],
                        "timestamp": cap["timestamp"],
                        "agent": cap["agent_id"],
                        "trust": cap["trust_score"],
                    }
                    for cap in capsules
                ],
                "total": len(MOCK_CAPSULES),
                "page": page,
                "per_page": per_page,
                "compressed": True,
            }
        )
    else:
        # Full format
        return jsonify(
            {
                "capsules": capsules,
                "total": len(MOCK_CAPSULES),
                "page": page,
                "per_page": per_page,
                "compressed": False,
            }
        )


@app.route("/capsules/<capsule_id>", methods=["GET", "OPTIONS"])
def get_capsule(capsule_id):
    capsule = next((cap for cap in MOCK_CAPSULES if cap["id"] == capsule_id), None)

    if not capsule:
        return jsonify({"error": "Capsule not found"}), 404

    return jsonify({"capsule": capsule, "verification": capsule["verification"]})


@app.route("/capsules/stats", methods=["GET", "OPTIONS"])
def capsule_stats():
    # Calculate real stats from generated capsules
    capsule_types = {}
    agents = {}

    for capsule in MOCK_CAPSULES:
        # Count capsule types
        capsule_type = capsule["type"]  # Updated to use 'type' field
        capsule_types[capsule_type] = capsule_types.get(capsule_type, 0) + 1

        # Count agents
        agent_id = capsule["agent_id"]
        agents[agent_id] = agents.get(agent_id, 0) + 1

    return jsonify(
        {
            "total_capsules": len(MOCK_CAPSULES),
            "by_type": capsule_types,  # Frontend expects 'by_type'
            "by_agent": agents,  # Frontend expects 'by_agent'
            "recent_activity": {  # Frontend expects this structure
                "last_24h": len(MOCK_CAPSULES) // 3,
                "last_week": len(MOCK_CAPSULES) // 2,
                "last_month": len(MOCK_CAPSULES),
            },
            "average_trust_score": round(
                sum(cap["trust_score"] for cap in MOCK_CAPSULES) / len(MOCK_CAPSULES), 3
            ),
        }
    )


@app.route("/trust/metrics", methods=["GET", "OPTIONS"])
def trust_metrics():
    return jsonify(
        [
            {
                "agent_id": "test-agent-001",
                "trust_score": 0.95,
                "last_updated": "2024-01-01T10:00:00Z",
            },
            {
                "agent_id": "test-agent-002",
                "trust_score": 0.87,
                "last_updated": "2024-01-01T11:00:00Z",
            },
            {
                "agent_id": "test-agent-003",
                "trust_score": 0.92,
                "last_updated": "2024-01-01T12:00:00Z",
            },
        ]
    )


@app.route("/analytics", methods=["GET", "OPTIONS"])
def analytics():
    return jsonify(
        {
            "capsules_per_day": [
                {"date": "2024-01-01", "count": 3},
                {"date": "2024-01-02", "count": 5},
                {"date": "2024-01-03", "count": 2},
            ],
            "trust_score_distribution": {"0.9-1.0": 2, "0.8-0.9": 1, "0.7-0.8": 0},
        }
    )


@app.route("/governance/proposals", methods=["GET", "OPTIONS"])
def governance_proposals():
    return jsonify(
        {
            "proposals": [
                {
                    "id": "prop_001",
                    "title": "Increase Trust Threshold",
                    "description": "Proposal to increase minimum trust threshold",
                    "status": "active",
                    "votes": {"for": 15, "against": 3, "abstain": 2},
                }
            ]
        }
    )


@app.route("/governance/stats", methods=["GET", "OPTIONS"])
def governance_stats():
    return jsonify(
        {
            "total_proposals": 5,
            "active_proposals": 1,
            "total_votes": 100,
            "participation_rate": 0.75,
        }
    )


@app.route("/economics/metrics", methods=["GET", "OPTIONS"])
def economic_metrics():
    return jsonify(
        {
            "total_value_generated": 1000000,
            "total_dividends_paid": 50000,
            "active_contributors": 25,
            "average_payout": 2000,
        }
    )


@app.route("/federation/nodes", methods=["GET", "OPTIONS"])
def federation_nodes():
    return jsonify(
        {
            "nodes": [
                {
                    "id": "node_001",
                    "name": "Primary Node",
                    "url": "https://api.example.com",
                    "status": "active",
                    "region": "us-east",
                }
            ]
        }
    )


@app.route("/federation/stats", methods=["GET", "OPTIONS"])
def federation_stats():
    return jsonify({"total_nodes": 3, "active_nodes": 2, "sync_status": "healthy"})


@app.route("/organization", methods=["GET", "OPTIONS"])
def organization():
    return jsonify(
        {
            "id": "org_001",
            "name": "Test Organization",
            "plan": "enterprise",
            "member_count": 5,
        }
    )


@app.route("/organization/members", methods=["GET", "OPTIONS"])
def organization_members():
    return jsonify(
        {
            "members": [
                {
                    "id": "member_001",
                    "name": "Test User",
                    "email": "test@example.com",
                    "role": "admin",
                }
            ]
        }
    )


# Onboarding API endpoints
@app.route("/onboarding/api/health", methods=["GET", "OPTIONS"])
def onboarding_health():
    return jsonify(
        {
            "status": "healthy",
            "version": "1.0.0",
            "onboarding_ready": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@app.route("/onboarding/api/start", methods=["POST", "OPTIONS"])
def start_onboarding():
    return jsonify(
        {
            "success": True,
            "session_id": f"session_{random.randint(1000, 9999)}",
            "user_id": f"user_{random.randint(100, 999)}",
            "progress": {
                "current_step": "welcome",
                "completed_steps": [],
                "total_steps": 5,
                "estimated_time_remaining": 300,
            },
        }
    )


@app.route("/onboarding/api/continue", methods=["POST", "OPTIONS"])
def continue_onboarding():
    return jsonify(
        {
            "success": True,
            "next_step": "environment_detection",
            "progress": {
                "current_step": "environment_detection",
                "completed_steps": ["welcome"],
                "total_steps": 5,
                "estimated_time_remaining": 240,
            },
        }
    )


@app.route("/onboarding/api/status/<user_id>", methods=["GET", "OPTIONS"])
def get_onboarding_status(user_id):
    return jsonify(
        {
            "user_id": user_id,
            "status": "in_progress",
            "progress": {
                "current_step": "platform_selection",
                "completed_steps": ["welcome", "environment_detection"],
                "total_steps": 5,
                "estimated_time_remaining": 180,
            },
        }
    )


@app.route("/onboarding/api/platforms", methods=["GET", "OPTIONS"])
def get_platforms():
    return jsonify(
        {
            "platforms": [
                {
                    "id": "openai",
                    "name": "OpenAI",
                    "status": "available",
                    "setup_time": "2 minutes",
                },
                {
                    "id": "anthropic",
                    "name": "Anthropic Claude",
                    "status": "available",
                    "setup_time": "2 minutes",
                },
            ]
        }
    )


@app.route("/onboarding/api/support", methods=["POST", "OPTIONS"])
def onboarding_support():
    return jsonify(
        {
            "success": True,
            "response": "Thanks for reaching out! Our onboarding system is designed to be intuitive. You're doing great!",
            "suggestions": [
                "Try the next step in the process",
                "Check our quick start guide",
                "Contact support if you need help",
            ],
        }
    )


if __name__ == "__main__":
    print("Starting simple API server on http://localhost:9090")
    app.run(host="0.0.0.0", port=9090, debug=True)
