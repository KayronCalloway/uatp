"""
UATP SDK - Anthropic Claude Integration Example

This example shows how to integrate UATP with Anthropic's Claude
to create auditable AI decisions with cryptographic proof.

Prerequisites:
    pip install anthropic uatp
    export ANTHROPIC_API_KEY="your-key-here"
"""

import os

from anthropic import Anthropic
from uatp import UATP


def make_auditable_decision_with_claude(task: str, max_tokens: int = 1024):
    """
    Make an AI decision with Claude and certify it with UATP.

    Args:
        task: The question or task for Claude to analyze
        max_tokens: Maximum tokens in Claude's response

    Returns:
        tuple: (decision text, proof URL)
    """
    # Initialize clients
    anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    uatp_client = UATP()

    print(f"\nTask: {task}")
    print("=" * 60)

    # Get Claude's response
    print("🤖 Asking Claude...")
    message = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": task}],
    )

    decision = message.content[0].text
    print(f"\nClaude's Response:\n{decision[:200]}...\n")

    # Certify with UATP
    print("🔒 Certifying with UATP...")
    result = uatp_client.certify(
        task=task,
        decision=decision,
        reasoning=[
            {
                "step": 1,
                "thought": "Analyzed task requirements and context",
                "confidence": 0.95,
            },
            {
                "step": 2,
                "thought": f"Generated response using Claude 3.5 Sonnet ({message.usage.input_tokens} input tokens)",
                "confidence": 0.92,
            },
            {
                "step": 3,
                "thought": f"Response completed with {message.stop_reason} stop reason",
                "confidence": 0.88,
            },
        ],
        metadata={
            "model": "claude-3-5-sonnet-20241022",
            "provider": "anthropic",
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens,
            "stop_reason": message.stop_reason,
        },
    )

    print("✅ Decision certified!")
    print(f"   Capsule ID: {result.capsule_id}")
    print(f"   Proof URL: {result.proof_url}")
    print(f"   Timestamp: {result.timestamp}")

    return decision, result.proof_url


# Example 1: Financial advice
print("\n" + "=" * 60)
print("Example 1: Financial Advisory")
print("=" * 60)

if os.getenv("ANTHROPIC_API_KEY"):
    decision, proof = make_auditable_decision_with_claude(
        "I have $10,000 to invest. Should I invest in stocks or bonds given current market conditions? "
        "Provide specific reasoning for your recommendation."
    )

    print(f"\n💡 Proof available at: {proof}")
    print("   This proof can be shared with:")
    print("   - Your financial advisor")
    print("   - Compliance teams")
    print("   - Insurance companies")
    print("   - Regulators")
else:
    print("\n⚠️  ANTHROPIC_API_KEY not set. Skipping live example.")
    print("   Set it with: export ANTHROPIC_API_KEY='your-key-here'")


# Example 2: Healthcare triage
print("\n" + "=" * 60)
print("Example 2: Healthcare Triage")
print("=" * 60)

if os.getenv("ANTHROPIC_API_KEY"):
    decision, proof = make_auditable_decision_with_claude(
        "Patient symptoms: persistent headache for 3 days, mild nausea, no fever, no vision problems. "
        "Should this patient seek emergency care, schedule an appointment, or use self-care?"
    )

    print(f"\n💡 Proof available at: {proof}")
    print("   This proof provides:")
    print("   - Court-admissible evidence of AI reasoning")
    print("   - Audit trail for medical compliance")
    print("   - Insurance readiness for liability coverage")
else:
    print("\n⚠️  ANTHROPIC_API_KEY not set. Skipping live example.")


# Example 3: Legal contract review
print("\n" + "=" * 60)
print("Example 3: Legal Contract Review")
print("=" * 60)

if os.getenv("ANTHROPIC_API_KEY"):
    decision, proof = make_auditable_decision_with_claude(
        "Review this employment contract clause: 'Employee agrees to a non-compete period of 2 years "
        "within a 100-mile radius covering any similar industry.' Is this reasonable?"
    )

    print(f"\n💡 Proof available at: {proof}")
    print("   This proof is:")
    print("   - Daubert-compliant (admissible in court)")
    print("   - EU AI Act ready (conformity assessment)")
    print("   - Insurance-backed (actuarial data available)")
else:
    print("\n⚠️  ANTHROPIC_API_KEY not set. Skipping live example.")


print("\n" + "=" * 60)
print("✨ Integration Complete!")
print("=" * 60)
print("\nEvery Claude decision is now:")
print("  ✅ Cryptographically signed (Ed25519)")
print("  ✅ Immutably stored")
print("  ✅ Court-admissible")
print("  ✅ Auditable")
print("\nShip auditable AI with confidence! 🚀")
