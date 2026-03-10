#!/usr/bin/env python3
"""
Pragmatic Attribution System Demo

This demonstrates the key insight from our conversation:
"what we can attribute we do and what we can't its general fund until we can"

Also incorporates temporal decay routing to commons fund as suggested.
"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.specialized_engine import SpecializedCapsuleEngine

from engine.economic_engine import UatpEconomicEngine


def demo_pragmatic_attribution():
    """Demonstrate the pragmatic attribution system."""

    print(" UATP Pragmatic Attribution System Demo")
    print("=" * 50)

    # Initialize the engines
    base_engine = SpecializedCapsuleEngine(
        agent_id="demo-agent", storage_path="demo_chain.jsonl"
    )

    economic_engine = UatpEconomicEngine(base_engine)

    print(" Initial State:")
    print(f"Commons Fund: ${economic_engine.commons_fund_balance:.2f}")
    print(f"UBA Percentage: {economic_engine.uba_percentage * 100}%")
    print()

    # Register some historical conversations
    print(" Registering historical conversations...")

    # Alice's conversation from 2 years ago (will have temporal decay)
    alice_conv_time = datetime.utcnow() - timedelta(days=730)  # 2 years ago
    economic_engine.register_conversation(
        conversation_id="alice_econ_2022",
        participant_id="alice",
        content_summary="Discussion about economic attribution systems and fair value distribution",
        timestamp=alice_conv_time,
        metadata={"topic": "economics", "quality": "high"},
    )

    # Bob's recent conversation (minimal decay)
    bob_conv_time = datetime.utcnow() - timedelta(days=30)  # 1 month ago
    economic_engine.register_conversation(
        conversation_id="bob_ai_2024",
        participant_id="bob",
        content_summary="Analysis of AI attribution challenges and technological solutions",
        timestamp=bob_conv_time,
        metadata={"topic": "technology", "quality": "medium"},
    )

    # Charlie's conversation from 5 years ago (heavy temporal decay)
    charlie_conv_time = datetime.utcnow() - timedelta(days=1825)  # 5 years ago
    economic_engine.register_conversation(
        conversation_id="charlie_old_2019",
        participant_id="charlie",
        content_summary="Early thoughts on economic distribution mechanisms",
        timestamp=charlie_conv_time,
        metadata={"topic": "economics", "quality": "medium"},
    )

    print(f"[OK] Registered {len(economic_engine.conversation_registry)} conversations")
    print()

    # Simulate AI generating value that references these conversations
    print(" AI generates valuable content...")

    ai_output = """
    The key to fair economic attribution is implementing a system where
    we can attribute what we can to specific contributors, while routing
    unattributable value to a commons fund that benefits everyone. This
    approach solves the attribution challenges by being pragmatic about
    uncertainty while ensuring fair distribution through temporal decay
    mechanisms that account for generational fairness.
    """

    value_generated = 1000.0  # $1000 worth of economic value

    print(f" AI Output Value: ${value_generated}")
    print(" Content relates to attribution and economic distribution")
    print()

    # Perform pragmatic attribution
    print(" Performing pragmatic attribution analysis...")

    attribution_results = economic_engine.attribute_ai_output(
        ai_output, value_generated
    )

    print(" Attribution Analysis Results:")
    for i, result in enumerate(attribution_results[:3]):  # Show top 3
        print(f"  {i + 1}. {result.source_id}: {result.confidence:.3f} confidence")
        print(
            f"     Semantic: {result.semantic_similarity:.3f}, Temporal: {result.temporal_relevance:.3f}"
        )
        print(f"     Level: {result.confidence_level.value}")
    print()

    # Calculate and apply pragmatic distribution
    distribution = economic_engine.calculate_pragmatic_distribution(
        attribution_results, value_generated
    )

    print(" Pragmatic Distribution Results:")
    print(
        f"  Direct Attributions: ${sum(distribution.direct_attributions.values()):.2f}"
    )
    for contributor, amount in distribution.direct_attributions.items():
        print(f"    {contributor}: ${amount:.2f}")

    print(f"  Commons Fund Contribution: ${distribution.commons_contribution:.2f}")
    print(
        f"    (Includes UBA: ${value_generated * economic_engine.uba_percentage:.2f})"
    )
    print(
        f"    (Includes temporal decay routing: ${distribution.commons_contribution - value_generated * economic_engine.uba_percentage:.2f})"
    )
    print(f"  Emergence Bonus: ${distribution.emergence_bonus:.2f}")
    print(f"  Total Distributed: ${distribution.total_distributed:.2f}")
    print(f"  Attribution Confidence: {distribution.attribution_confidence:.3f}")
    print(f"  Method: {distribution.distribution_method}")
    print()

    # Create the attribution payment capsule
    capsule = economic_engine.create_pragmatic_attribution_payment(
        ai_output=ai_output,
        total_value=value_generated,
        description="AI-generated content on economic attribution systems",
        context={"domain": "economics", "type": "analysis"},
    )

    print(" Created attribution payment capsule:")
    print(f"  Capsule ID: {capsule.capsule_id}")
    print(f"  Transaction Type: {capsule.economic_event_type}")
    print()

    # Show updated economic state
    print(" Updated Economic State:")
    summary = economic_engine.get_economic_summary()

    print("  Agent Balances:")
    for agent_id, balance in summary["top_by_balance"]:
        print(f"    {agent_id}: ${balance:.2f}")

    print(f"  Commons Fund: ${summary['commons_fund_balance']:.2f}")
    print(f"  Total Economic Value: ${summary['total_economic_value']:.2f}")

    attribution_analytics = summary["attribution_analytics"]
    print("  Attribution Analytics:")
    print(f"    Total Attributions: {attribution_analytics['total_attributions']}")
    print(f"    Average Confidence: {attribution_analytics['average_confidence']:.3f}")
    print(
        f"    Confidence Distribution: {attribution_analytics['confidence_distribution']}"
    )
    print()

    # Demonstrate commons fund distribution (Universal Basic Attribution)
    print(" Demonstrating Universal Basic Attribution...")

    if summary["commons_fund_balance"] > 0:
        # Simple equal distribution to all participants
        recipients = {
            "alice": 0.33,
            "bob": 0.33,
            "charlie": 0.34,  # Slight adjustment for rounding
        }

        uba_capsule = economic_engine.distribute_commons_fund(
            recipients=recipients,
            distribution_reason="Monthly Universal Basic Attribution distribution",
        )

        print("[OK] Distributed Universal Basic Attribution")
        print(f"  Capsule ID: {uba_capsule.capsule_id}")

        # Show final state
        final_summary = economic_engine.get_economic_summary()
        print("  Final Agent Balances:")
        for agent_id, balance in final_summary["top_by_balance"]:
            print(f"    {agent_id}: ${balance:.2f}")
        print(f"  Final Commons Fund: ${final_summary['commons_fund_balance']:.2f}")

    print()
    print(" Key Insights Demonstrated:")
    print("  1. [OK] High-confidence attributions → direct compensation")
    print("  2. [OK] Low-confidence/unattributable → commons fund")
    print("  3. [OK] Temporal decay value → commons fund (not lost)")
    print("  4. [OK] 15% Universal Basic Attribution to global commons")
    print("  5. [OK] Pragmatic approach: work with what we can attribute")
    print()
    print(" The system successfully implements the core principle:")
    print("   'What we can attribute we do, what we can't goes to")
    print("    general fund until we can'")


if __name__ == "__main__":
    demo_pragmatic_attribution()
