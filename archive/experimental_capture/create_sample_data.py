#!/usr/bin/env python3
"""
Create sample data for the UATP visualizer.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from engine.legacy_capsule_engine import LegacyCapsuleEngine


def create_sample_data():
    """Create sample capsule data for the visualizer."""

    # Initialize engine
    engine = LegacyCapsuleEngine(
        agent_id="demo-agent-007", storage_path="capsule_chain.jsonl"
    )

    # Create sample capsules
    capsules_data = [
        {
            "capsule_type": "Introspective",
            "confidence": 0.91,
            "reasoning_trace": [
                "User asked: Should I approve this loan?",
                "Analyzing credit score and financial history",
                "Model found: Applicant flagged in credit rule B2",
                "Conclusion: Recommend denial due to risk factors",
            ],
            "metadata": {
                "epistemic_frame": "Stoicism",
                "jurisdiction": "EU",
                "case_id": "LOAN_001",
            },
        },
        {
            "capsule_type": "Joint",
            "confidence": 0.85,
            "reasoning_trace": [
                "Reviewing loan denial recommendation",
                "Human oversight: Checking for potential bias",
                "Additional context: Applicant's recent job promotion",
                "Joint decision: Approve with conditions",
            ],
            "metadata": {
                "human_reviewer": "Alex Chen",
                "override_reason": "Recent employment change",
            },
        },
        {
            "capsule_type": "Refusal",
            "confidence": 0.95,
            "reasoning_trace": [
                "Request: Generate misleading financial advice",
                "Ethical evaluation: Request violates harm prevention",
                "Refusal: Cannot provide information that could cause financial harm",
            ],
            "metadata": {"violation_type": "potential_harm", "policy_section": "4.2.1"},
        },
        {
            "capsule_type": "Introspective",
            "confidence": 0.78,
            "reasoning_trace": [
                "Processing investment recommendation request",
                "Market analysis: Tech sector showing volatility",
                "Risk assessment: Moderate to high risk",
                "Recommendation: Diversified portfolio with tech exposure limited to 20%",
            ],
            "metadata": {"market_conditions": "volatile", "risk_tolerance": "moderate"},
        },
        {
            "capsule_type": "Joint",
            "confidence": 0.88,
            "reasoning_trace": [
                "AI recommendation: Diversified portfolio",
                "Human input: Client has specific ESG preferences",
                "Joint adjustment: Include ESG-focused funds",
                "Final recommendation: 60% ESG equity, 30% bonds, 10% alternatives",
            ],
            "metadata": {
                "human_advisor": "Sarah Johnson",
                "client_preferences": "ESG_focused",
            },
        },
    ]

    print("Creating sample capsules...")
    created_capsules = []

    for i, capsule_data in enumerate(capsules_data):
        # Set parent relationships for some capsules
        previous_id = None
        if i == 1:  # Joint capsule follows first Introspective
            previous_id = created_capsules[0].capsule_id
        elif i == 4:  # Second Joint follows second Introspective
            previous_id = created_capsules[3].capsule_id

        capsule = engine.create_capsule(
            capsule_type=capsule_data["capsule_type"],
            confidence=capsule_data["confidence"],
            reasoning_trace=capsule_data["reasoning_trace"],
            metadata=capsule_data["metadata"],
            previous_capsule_id=previous_id,
        )

        engine.log_capsule(capsule)
        created_capsules.append(capsule)
        print(f"✅ Created {capsule.capsule_type} capsule: {capsule.capsule_id}")

    print(f"\n🎉 Created {len(created_capsules)} sample capsules!")
    print(f"   Data saved to: {os.path.abspath('capsule_chain.jsonl')}")
    print(f"   Chain contains {len(engine.load_chain())} total capsules")

    print("\nTo run the visualizer:")
    print("  streamlit run visualizer/app.py")

    return created_capsules


if __name__ == "__main__":
    create_sample_data()
