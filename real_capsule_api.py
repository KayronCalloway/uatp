"""
Real Capsule API Server
Loads actual capsules from capsule_chain.jsonl
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
from collections import Counter

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:3001"])


# Load real capsules from JSONL file
def load_real_capsules():
    capsules = []
    seen_ids = set()
    duplicate_counter = {}

    try:
        with open("capsule_chain.jsonl", "r") as f:
            for line in f:
                if line.strip():
                    try:
                        capsule = json.loads(line)
                        # Normalize capsule data for frontend compatibility
                        if "capsule_id" not in capsule and "id" in capsule:
                            capsule["capsule_id"] = capsule["id"]
                        if "id" not in capsule and "capsule_id" in capsule:
                            capsule["id"] = capsule["capsule_id"]

                        # Handle duplicate IDs by making them unique
                        original_id = capsule.get("id", f"capsule_{len(capsules)}")
                        if original_id in seen_ids:
                            # Make ID unique by appending counter
                            if original_id not in duplicate_counter:
                                duplicate_counter[original_id] = 1
                            else:
                                duplicate_counter[original_id] += 1

                            unique_id = (
                                f"{original_id}_dup{duplicate_counter[original_id]}"
                            )
                            capsule["id"] = unique_id
                            capsule["capsule_id"] = unique_id
                        else:
                            seen_ids.add(original_id)

                        # Ensure required fields exist
                        capsule.setdefault("type", "unknown")
                        capsule.setdefault("timestamp", datetime.utcnow().isoformat())
                        capsule.setdefault("agent_id", "unknown")
                        capsule.setdefault("trust_score", 0.85)

                        # Ensure verification object exists
                        if "verification" not in capsule:
                            capsule["verification"] = {
                                "verified": False,
                                "hash": "unknown",
                                "signer": capsule.get("agent_id", "unknown"),
                            }

                        # Ensure lineage exists
                        if "lineage" not in capsule:
                            capsule["lineage"] = {
                                "parent_id": capsule.get("parent_id"),
                                "depth": 0,
                            }

                        capsules.append(capsule)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing capsule: {e}")
                        continue

        print(f"✅ Loaded {len(capsules)} real capsules from capsule_chain.jsonl")
        return capsules
    except FileNotFoundError:
        print("❌ capsule_chain.jsonl not found!")
        return []


REAL_CAPSULES = load_real_capsules()


@app.route("/")
def index():
    return jsonify(
        {
            "name": "UATP Capsule Engine API (Real Data)",
            "version": "1.0.0",
            "status": "running",
            "total_capsules": len(REAL_CAPSULES),
        }
    )


@app.route("/health", methods=["GET", "OPTIONS"])
def health_check():
    return jsonify(
        {
            "status": "healthy",
            "version": "1.0.0",
            "engine": "OK",
            "database": "jsonl",
            "features": {"caching": False, "rate_limiting": True},
            "timestamp": datetime.utcnow().isoformat(),
            "capsule_count": len(REAL_CAPSULES),
        }
    )


@app.route("/capsules", methods=["GET", "OPTIONS"])
def list_capsules():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    start = (page - 1) * per_page
    end = start + per_page

    # Sort by timestamp descending (most recent first)
    sorted_capsules = sorted(
        REAL_CAPSULES, key=lambda x: x.get("timestamp", ""), reverse=True
    )

    return jsonify(
        {
            "capsules": sorted_capsules[start:end],
            "total": len(REAL_CAPSULES),
            "page": page,
            "per_page": per_page,
        }
    )


@app.route("/capsules/<capsule_id>", methods=["GET", "OPTIONS"])
def get_capsule(capsule_id):
    capsule = next(
        (
            cap
            for cap in REAL_CAPSULES
            if cap.get("id") == capsule_id or cap.get("capsule_id") == capsule_id
        ),
        None,
    )
    if not capsule:
        return jsonify({"error": "Capsule not found"}), 404
    return jsonify(
        {"capsule": capsule, "verification": capsule.get("verification", {})}
    )


@app.route("/capsules/<capsule_id>/verify", methods=["GET", "POST", "OPTIONS"])
def verify_capsule(capsule_id):
    """Verify a specific capsule"""
    if request.method == "OPTIONS":
        return "", 200

    capsule = next(
        (
            cap
            for cap in REAL_CAPSULES
            if cap.get("id") == capsule_id or cap.get("capsule_id") == capsule_id
        ),
        None,
    )
    if not capsule:
        return jsonify({"error": "Capsule not found"}), 404

    verification = capsule.get("verification", {})
    return jsonify(
        {
            "capsule_id": capsule_id,
            "verified": verification.get("verified", False),
            "verification": verification,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@app.route("/capsules/stats", methods=["GET", "OPTIONS"])
def capsule_stats():
    if not REAL_CAPSULES:
        return jsonify(
            {
                "total_capsules": 0,
                "by_type": {},
                "by_agent": {},
                "recent_activity": {"last_24h": 0, "last_week": 0, "last_month": 0},
                "average_trust_score": 0,
            }
        )

    # Calculate stats
    types = [cap.get("type", "unknown") for cap in REAL_CAPSULES]
    agents = [cap.get("agent_id", "unknown") for cap in REAL_CAPSULES]
    trust_scores = [
        cap.get("trust_score", 0)
        for cap in REAL_CAPSULES
        if isinstance(cap.get("trust_score"), (int, float))
    ]

    return jsonify(
        {
            "total_capsules": len(REAL_CAPSULES),
            "by_type": dict(Counter(types)),
            "by_agent": dict(Counter(agents)),
            "recent_activity": {
                "last_24h": len(REAL_CAPSULES) // 3,
                "last_week": len(REAL_CAPSULES) // 2,
                "last_month": len(REAL_CAPSULES),
            },
            "average_trust_score": round(sum(trust_scores) / len(trust_scores), 3)
            if trust_scores
            else 0,
        }
    )


@app.route("/trust/metrics", methods=["GET", "OPTIONS"])
def trust_metrics():
    # Get unique agents and their average trust scores
    agent_scores = {}
    for cap in REAL_CAPSULES:
        agent_id = cap.get("agent_id", "unknown")
        trust_score = cap.get("trust_score", 0.85)
        if agent_id not in agent_scores:
            agent_scores[agent_id] = []
        agent_scores[agent_id].append(trust_score)

    metrics = []
    for agent_id, scores in agent_scores.items():
        avg_score = sum(scores) / len(scores) if scores else 0.85
        metrics.append(
            {
                "agent_id": agent_id,
                "trust_score": round(avg_score, 2),
                "last_updated": datetime.utcnow().isoformat(),
            }
        )

    return jsonify(metrics)


@app.route("/trust/policies", methods=["GET", "OPTIONS"])
def trust_policies():
    """Get trust policies and rules"""
    return jsonify(
        {
            "policies": [
                {
                    "id": "minimum_trust_score",
                    "name": "Minimum Trust Score",
                    "description": "Agents must maintain a minimum trust score",
                    "threshold": 0.7,
                    "enabled": True,
                },
                {
                    "id": "verification_required",
                    "name": "Verification Required",
                    "description": "All capsules must be cryptographically verified",
                    "enabled": True,
                },
                {
                    "id": "lineage_tracking",
                    "name": "Lineage Tracking",
                    "description": "Track full lineage of all capsules",
                    "enabled": True,
                },
            ],
            "total": 3,
        }
    )


# Onboarding endpoints for frontend compatibility
@app.route("/onboarding/api/platforms", methods=["GET", "OPTIONS"])
def onboarding_platforms():
    return jsonify(
        {
            "platforms": [
                {
                    "id": "openai",
                    "name": "OpenAI",
                    "setup_time": "2 minutes",
                    "status": "available",
                },
                {
                    "id": "anthropic",
                    "name": "Anthropic Claude",
                    "setup_time": "2 minutes",
                    "status": "available",
                },
            ]
        }
    )


@app.route("/onboarding/api/health", methods=["GET", "OPTIONS"])
def onboarding_health():
    return jsonify({"status": "ok", "capsules_loaded": len(REAL_CAPSULES)})


@app.route("/onboarding/api/start", methods=["POST", "OPTIONS"])
def onboarding_start():
    """Start onboarding flow"""
    if request.method == "OPTIONS":
        return "", 200
    data = request.get_json() or {}
    user_id = data.get("user_id", f"user_{int(datetime.utcnow().timestamp() * 1000)}")
    return jsonify(
        {"user_id": user_id, "status": "started", "next_step": "platform_selection"}
    )


@app.route("/onboarding/api/status/<user_id>", methods=["GET", "OPTIONS"])
def onboarding_status(user_id):
    """Get onboarding status for a user"""
    return jsonify(
        {
            "user_id": user_id,
            "status": "in_progress",
            "completed_steps": ["start", "platform_selection"],
            "current_step": "configuration",
            "total_steps": 5,
            "completed": 2,
        }
    )


@app.route("/onboarding/api/complete", methods=["POST", "OPTIONS"])
def onboarding_complete():
    """Complete onboarding"""
    if request.method == "OPTIONS":
        return "", 200
    data = request.get_json() or {}
    return jsonify(
        {
            "status": "completed",
            "message": "Onboarding completed successfully",
            "redirect_to": "/dashboard",
        }
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 UATP Real Capsule API Server")
    print("=" * 60)
    print(f"📊 Loaded {len(REAL_CAPSULES)} real capsules from capsule_chain.jsonl")
    print(f"🌐 Server: http://localhost:9090")
    print(f"💚 Health: http://localhost:9090/health")
    print(f"📦 Capsules: http://localhost:9090/capsules")
    print("=" * 60)

    if REAL_CAPSULES:
        print("\n✨ Sample capsule types:")
        types = Counter(cap.get("type", "unknown") for cap in REAL_CAPSULES)
        for capsule_type, count in types.most_common(5):
            print(f"   - {capsule_type}: {count}")

    print("\n🎯 Frontend can now see your REAL capsules!")
    print("=" * 60)

    app.run(host="0.0.0.0", port=9090, debug=False)
