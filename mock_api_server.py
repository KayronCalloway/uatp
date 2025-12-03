#!/usr/bin/env python3
"""
Mock API server for testing UATP frontend
"""

from datetime import datetime, timedelta
import json
import random
import uuid
from typing import Dict, List, Any
from quart import Quart, request, jsonify
from quart_cors import cors

app = Quart(__name__)
app = cors(app)

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
            "content": f"Mock capsule content {i+1}. This is a sample capsule for testing purposes.",
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
async def index():
    return {
        "service": "UATP Capsule Engine (Mock)",
        "version": "1.0.0-mock",
        "documentation": "Mock API for frontend testing",
    }


@app.route("/health")
async def health():
    return {
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


@app.route("/health/detailed")
async def health_detailed():
    return await health()


@app.route("/capsules")
async def list_capsules():
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

    return {"capsules": capsules}


@app.route("/capsules/<capsule_id>")
async def get_capsule(capsule_id: str):
    include_raw = request.args.get("include_raw", "false").lower() == "true"

    capsule = next((c for c in MOCK_CAPSULES if c["id"] == capsule_id), None)
    if not capsule:
        return {"error": "Capsule not found"}, 404

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

    return response


@app.route("/capsules/<capsule_id>/verify")
async def verify_capsule(capsule_id: str):
    capsule = next((c for c in MOCK_CAPSULES if c["id"] == capsule_id), None)
    if not capsule:
        return {"error": "Capsule not found"}, 404

    # Mock verification - randomly pass/fail for testing
    verified = random.random() > 0.1  # 90% pass rate

    return {
        "capsule_id": capsule_id,
        "verified": verified,
        "from_cache": False,
        "metadata_has_verify_key": True,
        "verification_error": None if verified else "Mock verification failure",
    }


@app.route("/capsules/stats")
async def capsule_stats():
    types = {}
    for capsule in MOCK_CAPSULES:
        capsule_type = capsule["type"]
        types[capsule_type] = types.get(capsule_type, 0) + 1

    unique_agents = len(set(c["agent_id"] for c in MOCK_CAPSULES))

    return {
        "total_capsules": len(MOCK_CAPSULES),
        "types": types,
        "unique_agents": unique_agents,
    }


@app.route("/trust/metrics")
async def trust_metrics():
    return MOCK_TRUST_METRICS


@app.route("/trust/agent/<agent_id>/status")
async def trust_agent_status(agent_id: str):
    metric = next((m for m in MOCK_TRUST_METRICS if m["agent_id"] == agent_id), None)
    if not metric:
        return {"error": "Agent not found"}, 404

    return {
        "agent_id": agent_id,
        "trust_score": metric["trust_score"],
        "status": "active" if metric["trust_score"] > 60 else "restricted",
        "last_updated": metric["last_updated"],
    }


@app.route("/trust/policies")
async def trust_policies():
    return {
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


@app.route("/trust/violations/recent")
async def recent_violations():
    return {"violations": MOCK_VIOLATIONS}


@app.route("/trust/agents/quarantined")
async def quarantined_agents():
    return {"agents": MOCK_QUARANTINED}


@app.route("/metrics")
async def metrics():
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
async def validate_reasoning():
    data = await request.get_json()

    return {
        "valid": True,
        "errors": [],
        "warnings": ["Mock validation warning"],
        "confidence": 0.95,
    }


@app.route("/reasoning/analyze", methods=["POST"])
async def analyze_reasoning():
    data = await request.get_json()

    return {
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


@app.route("/ai/generate", methods=["POST"])
async def generate_ai():
    data = await request.get_json()

    return {
        "status": "success",
        "generated_text": f'Mock AI response to: {data.get("prompt", "")}',
    }


if __name__ == "__main__":
    print("🚀 Starting UATP Mock API Server")
    print("📊 Generated mock data:")
    print(f"   • {len(MOCK_CAPSULES)} capsules")
    print(f"   • {len(MOCK_TRUST_METRICS)} trust metrics")
    print(f"   • {len(MOCK_VIOLATIONS)} violations")
    print(f"   • {len(MOCK_QUARANTINED)} quarantined agents")
    print("✅ Server running at http://localhost:8000")
    print("🔗 Frontend at http://localhost:3000")

    app.run(host="0.0.0.0", port=8000, debug=True)
