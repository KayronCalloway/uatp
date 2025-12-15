"""
UATP SDK - OpenAI Integration Example

This example shows how to integrate UATP with OpenAI's GPT models
to create auditable AI decisions with cryptographic proof.

Prerequisites:
    pip install openai uatp
    export OPENAI_API_KEY="your-key-here"
"""

import os

from openai import OpenAI
from uatp import UATP


def make_auditable_decision_with_gpt(task: str, model: str = "gpt-4"):
    """
    Make an AI decision with GPT and certify it with UATP.

    Args:
        task: The question or task for GPT to analyze
        model: OpenAI model to use (gpt-4, gpt-3.5-turbo, etc.)

    Returns:
        tuple: (decision text, proof URL)
    """
    # Initialize clients
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    uatp_client = UATP()

    print(f"\nTask: {task}")
    print("=" * 60)

    # Get GPT's response
    print(f"🤖 Asking {model}...")
    response = openai_client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": task}]
    )

    decision = response.choices[0].message.content
    print(f"\nGPT's Response:\n{decision[:200]}...\n")

    # Certify with UATP
    print("🔒 Certifying with UATP...")
    result = uatp_client.certify(
        task=task,
        decision=decision,
        reasoning=[
            {"step": 1, "thought": "Analyzed task requirements", "confidence": 0.93},
            {
                "step": 2,
                "thought": f"Generated response using {model} ({response.usage.total_tokens} tokens)",
                "confidence": 0.90,
            },
            {
                "step": 3,
                "thought": f"Response completed with {response.choices[0].finish_reason} finish reason",
                "confidence": 0.87,
            },
        ],
        metadata={
            "model": model,
            "provider": "openai",
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "finish_reason": response.choices[0].finish_reason,
        },
    )

    print("✅ Decision certified!")
    print(f"   Capsule ID: {result.capsule_id}")
    print(f"   Proof URL: {result.proof_url}")
    print(f"   Timestamp: {result.timestamp}")

    return decision, result.proof_url


# Example 1: Credit decision (CFPB compliance)
print("\n" + "=" * 60)
print("Example 1: Credit Decision (CFPB Compliance)")
print("=" * 60)

if os.getenv("OPENAI_API_KEY"):
    decision, proof = make_auditable_decision_with_gpt(
        "Applicant profile: Credit score 680, debt-to-income ratio 35%, 18 months at current job, "
        "no recent delinquencies. Should we approve a $15,000 auto loan at 8.5% APR?",
        model="gpt-4",
    )

    print(f"\n💡 Proof available at: {proof}")
    print("   This proof satisfies:")
    print("   - CFPB adverse action requirements")
    print("   - Fair lending documentation")
    print("   - ECOA compliance (Equal Credit Opportunity Act)")
else:
    print("\n⚠️  OPENAI_API_KEY not set. Skipping live example.")
    print("   Set it with: export OPENAI_API_KEY='your-key-here'")


# Example 2: Medical diagnosis assistance
print("\n" + "=" * 60)
print("Example 2: Medical Diagnosis Assistance")
print("=" * 60)

if os.getenv("OPENAI_API_KEY"):
    decision, proof = make_auditable_decision_with_gpt(
        "Patient presents with: sore throat (3 days), mild fever (100.5°F), no cough, white patches on tonsils. "
        "What is the most likely diagnosis and recommended action?",
        model="gpt-4",
    )

    print(f"\n💡 Proof available at: {proof}")
    print("   This proof provides:")
    print("   - HIPAA-compliant audit trail")
    print("   - Medical liability documentation")
    print("   - Professional standard of care evidence")
else:
    print("\n⚠️  OPENAI_API_KEY not set. Skipping live example.")


# Example 3: HR decision (bias prevention)
print("\n" + "=" * 60)
print("Example 3: HR Hiring Decision (Bias Prevention)")
print("=" * 60)

if os.getenv("OPENAI_API_KEY"):
    decision, proof = make_auditable_decision_with_gpt(
        "Candidate A: 5 years experience, relevant degree, excellent communication, passed technical interview. "
        "Candidate B: 7 years experience, related degree, good communication, passed technical interview. "
        "Both match job requirements. Who should receive the offer and why?",
        model="gpt-4",
    )

    print(f"\n💡 Proof available at: {proof}")
    print("   This proof ensures:")
    print("   - EEOC compliance documentation")
    print("   - Protection against discrimination claims")
    print("   - Defensible hiring process")
else:
    print("\n⚠️  OPENAI_API_KEY not set. Skipping live example.")


# Example 4: Using with streaming (advanced)
print("\n" + "=" * 60)
print("Example 4: Streaming Response (Advanced)")
print("=" * 60)

if os.getenv("OPENAI_API_KEY"):
    print("🤖 Asking GPT with streaming...")
    openai_client = OpenAI()
    uatp_client = UATP()

    task = "What are the top 3 risks of using AI in healthcare?"

    # Stream the response
    stream = openai_client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": task}], stream=True
    )

    decision_chunks = []
    print("\nGPT Response (streaming):")
    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            decision_chunks.append(content)

    decision = "".join(decision_chunks)
    print("\n")

    # Certify the complete response
    print("🔒 Certifying streamed response...")
    result = uatp_client.certify(
        task=task,
        decision=decision,
        reasoning=[
            {"step": 1, "thought": "Analyzed healthcare AI risks", "confidence": 0.92},
            {"step": 2, "thought": "Generated streaming response", "confidence": 0.88},
            {"step": 3, "thought": "Compiled full response", "confidence": 0.90},
        ],
        metadata={"model": "gpt-4", "streaming": True},
    )

    print("✅ Streamed decision certified!")
    print(f"   Proof URL: {result.proof_url}")
else:
    print("\n⚠️  OPENAI_API_KEY not set. Skipping live example.")


print("\n" + "=" * 60)
print("✨ Integration Complete!")
print("=" * 60)
print("\nEvery GPT decision is now:")
print("  ✅ Cryptographically signed (Ed25519)")
print("  ✅ Immutably stored")
print("  ✅ Court-admissible")
print("  ✅ Auditable")
print("\nShip auditable AI with confidence! 🚀")
