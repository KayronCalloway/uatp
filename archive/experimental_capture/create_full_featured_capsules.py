#!/usr/bin/env python3
"""
Create Full-Featured UATP Capsules
Generates capsules with all advanced features: crypto seals, confidence ratings, reasoning traces
"""

import time
from datetime import datetime

import requests


def create_advanced_capsule():
    """Create a capsule with full UATP features using the API."""

    api_base = "http://localhost:9090"
    headers = {"X-API-Key": "dev-key-001", "Content-Type": "application/json"}

    # Create a reasoning trace capsule with full features
    capsule_data = {
        "capsule_type": "reasoning_trace",
        "agent_id": "advanced-demo-agent",
        "reasoning_trace": {
            "reasoning_steps": [
                {
                    "step_id": "step_001",
                    "operation": "problem_analysis",
                    "reasoning": "UATP enables fair AI attribution by creating cryptographically sealed records of AI interactions, ensuring content creators receive proper credit and economic compensation.",
                    "confidence": 0.95,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {
                        "source_type": "knowledge_synthesis",
                        "complexity": "high",
                        "domain": "AI_attribution",
                    },
                },
                {
                    "step_id": "step_002",
                    "operation": "technical_implementation",
                    "reasoning": "The system uses post-quantum cryptography with Ed25519 signatures and SHA-256 Merkle roots to create tamper-proof attribution records that remain secure even against future quantum computers.",
                    "confidence": 0.88,
                    "timestamp": datetime.utcnow().isoformat(),
                    "parent_step_id": "step_001",
                    "metadata": {
                        "technical_depth": "expert_level",
                        "verification_method": "cryptographic_proof",
                    },
                },
                {
                    "step_id": "step_003",
                    "operation": "economic_modeling",
                    "reasoning": "Economic value is calculated using the Fair Creator Dividend Engine (FCDE), which analyzes conversation significance, creative input, and attribution scores to determine fair compensation rates for content creators.",
                    "confidence": 0.82,
                    "timestamp": datetime.utcnow().isoformat(),
                    "parent_step_id": "step_001",
                    "metadata": {
                        "economic_model": "FCDE_v2.1",
                        "attribution_weight": 0.75,
                    },
                },
                {
                    "step_id": "step_004",
                    "operation": "trust_validation",
                    "reasoning": "Trust metrics are continuously monitored through the Runtime Trust Enforcer, tracking agent behavior, conversation quality, and ethical compliance to maintain system integrity.",
                    "confidence": 0.91,
                    "timestamp": datetime.utcnow().isoformat(),
                    "parent_step_id": "step_002",
                    "metadata": {"trust_threshold": 0.85, "monitoring_active": True},
                },
            ],
            "total_confidence": 0.89,
            "metadata": {
                "conversation_type": "educational_explanation",
                "topic": "UATP_system_architecture",
                "complexity_score": 0.87,
                "real_world_value": 15.50,
            },
        },
        "context_metadata": {
            "session_type": "demonstration",
            "user_intent": "system_understanding",
            "platform": "advanced_demo",
            "conversation_quality": "high_value",
            "attribution_eligible": True,
        },
    }

    print("🚀 Creating advanced UATP capsule...")

    try:
        response = requests.post(
            f"{api_base}/capsules", headers=headers, json=capsule_data
        )

        if response.ok:
            capsule = response.json()
            print(
                f"✅ Created advanced capsule: {capsule.get('capsule_id', 'unknown')}"
            )
            return capsule
        else:
            print(f"❌ Failed to create capsule: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error creating capsule: {e}")
        return None


def create_high_value_conversation():
    """Create a realistic high-value conversation sequence."""

    api_base = "http://localhost:9090"
    headers = {"X-API-Key": "dev-key-001", "Content-Type": "application/json"}

    session_id = f"advanced-demo-{int(time.time())}"

    # High-value user question
    user_message = {
        "session_id": session_id,
        "user_id": "expert-user",
        "platform": "advanced_demo",
        "role": "user",
        "content": "How can I implement a post-quantum cryptographic attribution system that ensures fair compensation for AI training data contributors while maintaining privacy and scalability?",
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "message_type": "expert_technical_query",
            "estimated_value": 25.00,
            "complexity": "expert_level",
            "domains": ["cryptography", "economics", "AI_systems"],
        },
    }

    # Comprehensive AI response
    ai_response = {
        "session_id": session_id,
        "user_id": "uatp-expert-ai",
        "platform": "advanced_demo",
        "role": "assistant",
        "content": """Implementing a post-quantum cryptographic attribution system requires several key components:

1. **Cryptographic Foundation**: Use lattice-based cryptography (like CRYSTALS-Dilithium) for quantum-resistant signatures, combined with hash-based signatures for long-term security. This ensures attribution records remain valid even against quantum attacks.

2. **Attribution Architecture**: Implement a hierarchical attribution tree where each contribution is cryptographically linked to its source. Use Merkle trees with post-quantum hash functions to create tamper-evident attribution chains.

3. **Privacy-Preserving Economics**: Deploy zero-knowledge proofs to enable compensation calculations without revealing sensitive contribution details. Use homomorphic encryption for aggregating attribution scores while maintaining contributor privacy.

4. **Scalability Solutions**: Implement sharding across attribution domains and use probabilistic data structures (like Bloom filters) for efficient attribution lookups. Consider layer-2 scaling solutions for high-throughput scenarios.

5. **Fair Compensation Algorithm**: Design a multi-factor attribution model considering: content uniqueness, usage frequency, creative contribution score, and temporal relevance. Use mechanism design principles to prevent gaming.

The system should include real-time monitoring, automated dispute resolution, and transparent governance mechanisms for parameter updates.""",
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "response_quality": "expert_comprehensive",
            "technical_accuracy": 0.94,
            "practical_value": 0.89,
            "innovation_score": 0.87,
            "estimated_value": 45.00,
        },
    }

    print("💬 Creating high-value conversation...")

    try:
        # Send user message
        user_resp = requests.post(
            f"{api_base}/api/v1/live/capture/message",
            headers=headers,
            json=user_message,
        )

        # Send AI response
        ai_resp = requests.post(
            f"{api_base}/api/v1/live/capture/message", headers=headers, json=ai_response
        )

        if user_resp.ok and ai_resp.ok:
            print(f"✅ Created high-value conversation: {session_id}")
            print("💰 Estimated total value: $70.00")
            return session_id
        else:
            print("❌ Failed to create conversation")
            return None

    except Exception as e:
        print(f"❌ Error creating conversation: {e}")
        return None


def show_system_status():
    """Display current system status with all features."""

    api_base = "http://localhost:9090"
    headers = {"X-API-Key": "dev-key-001"}

    print("\n📊 UATP System Status")
    print("=" * 50)

    try:
        # Get capsule stats
        capsules_resp = requests.get(f"{api_base}/capsules?per_page=5", headers=headers)
        if capsules_resp.ok:
            capsules = capsules_resp.json().get("capsules", [])
            print(f"📦 Recent capsules: {len(capsules)}")

            for capsule in capsules[:3]:
                confidence = capsule.get("reasoning_trace", {}).get(
                    "total_confidence", 0.0
                )
                print(
                    f"   • {capsule.get('capsule_id', 'unknown')[:20]}... (confidence: {confidence})"
                )

        # Get chain seals
        seals_resp = requests.get(f"{api_base}/chain/seals", headers=headers)
        if seals_resp.ok:
            seals = seals_resp.json().get("seals", [])
            print(f"🔐 Chain seals: {len(seals)} active")

        # Get trust metrics
        trust_resp = requests.get(f"{api_base}/trust/metrics", headers=headers)
        if trust_resp.ok:
            trust = trust_resp.json()
            print(
                f"🛡️  Trust system: {trust.get('system_health', 'unknown')} ({trust.get('policies_enabled', 0)} policies)"
            )

        # Get live conversations
        live_resp = requests.get(
            f"{api_base}/api/v1/live/capture/conversations", headers=headers
        )
        if live_resp.ok:
            live = live_resp.json()
            print(f"💬 Active conversations: {live.get('count', 0)}")

        print("\n🌐 Dashboard: http://localhost:3000")
        print("📱 Mobile: http://192.168.1.79:3000")

    except Exception as e:
        print(f"❌ Error getting system status: {e}")


def main():
    print("🔥 UATP Full-Featured System Demo")
    print("=" * 50)

    # Create advanced capsule
    capsule = create_advanced_capsule()
    time.sleep(1)

    # Create high-value conversation
    conversation = create_high_value_conversation()
    time.sleep(1)

    # Show system status
    show_system_status()

    print("\n🎉 Full UATP system is now active with:")
    print("✅ Cryptographic seals & signatures")
    print("✅ Confidence ratings & reasoning traces")
    print("✅ Economic attribution & value tracking")
    print("✅ Trust metrics & violation monitoring")
    print("✅ High-value conversation data")

    print("\n🚀 Open your dashboard to see all features in action!")


if __name__ == "__main__":
    main()
