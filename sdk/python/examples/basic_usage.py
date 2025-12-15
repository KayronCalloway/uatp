"""
UATP SDK - Basic Usage Example
"""

from uatp import UATP

# Initialize client
client = UATP(api_key="demo-api-key")  # Replace with your actual API key

# Example 1: Simple decision
print("Example 1: Simple AI Decision")
print("=" * 50)

result = client.certify(
    task="Should I bring an umbrella today?",
    decision="Yes, bring an umbrella",
    reasoning=[
        {
            "step": 1,
            "thought": "Checked weather forecast for today",
            "confidence": 0.98,
        },
        {"step": 2, "thought": "70% chance of rain this afternoon", "confidence": 0.92},
        {"step": 3, "thought": "Recommendation: carry umbrella", "confidence": 0.90},
    ],
)

print(f"Capsule ID: {result.capsule_id}")
print(f"Proof URL: {result.proof_url}")
print(f"Timestamp: {result.timestamp}")
print()

# Example 2: Healthcare decision
print("Example 2: Healthcare AI Decision")
print("=" * 50)

result = client.certify(
    task="Triage patient symptoms",
    decision="Schedule appointment within 48 hours",
    reasoning=[
        {
            "step": 1,
            "thought": "Patient reports persistent headache for 3 days",
            "confidence": 0.95,
        },
        {
            "step": 2,
            "thought": "No emergency symptoms (no fever, vision issues, or loss of consciousness)",
            "confidence": 0.88,
        },
        {
            "step": 3,
            "thought": "Recommend non-urgent appointment for evaluation",
            "confidence": 0.85,
        },
    ],
    confidence=0.85,
    metadata={
        "model": "medical-triage-ai-v2",
        "patient_severity": "low",
        "requires_human_review": False,
    },
)

print(f"Capsule ID: {result.capsule_id}")
print(f"Proof URL: {result.proof_url}")
print()

# Example 3: Financial decision
print("Example 3: Financial AI Decision")
print("=" * 50)

result = client.certify(
    task="Approve personal loan application",
    decision="Loan approved: $25,000 at 7.2% APR",
    reasoning=[
        {
            "step": 1,
            "thought": "Credit score: 705 (good)",
            "confidence": 0.99,
            "data_source": "Credit bureau",
        },
        {
            "step": 2,
            "thought": "Debt-to-income ratio: 32% (acceptable)",
            "confidence": 0.94,
            "data_source": "Income verification",
        },
        {
            "step": 3,
            "thought": "Employment: 2.5 years current employer (stable)",
            "confidence": 0.91,
            "data_source": "Employment records",
        },
        {
            "step": 4,
            "thought": "No recent delinquencies",
            "confidence": 0.97,
            "data_source": "Credit history",
        },
    ],
    confidence=0.88,
    metadata={
        "model": "lending-ai-v3",
        "fair_lending_check": "passed",
        "bias_audit": "compliant",
        "application_id": "app_789012",
    },
)

print(f"Capsule ID: {result.capsule_id}")
print(f"Proof URL: {result.proof_url}")
print()

# Example 4: Retrieve proof
print("Example 4: Retrieve Proof")
print("=" * 50)

proof = client.get_proof(result.capsule_id)

print(f"Task: {proof.task}")
print(f"Decision: {proof.decision}")
print(f"Confidence: {proof.confidence}")
print(f"Steps: {len(proof.reasoning_chain)}")
print(f"Signature valid: {proof.verify()}")
print()

# Example 5: List capsules
print("Example 5: List Recent Capsules")
print("=" * 50)

capsules = client.list_capsules(limit=5)

for i, capsule in enumerate(capsules, 1):
    print(f"{i}. {capsule.task[:50]}... (confidence: {capsule.confidence:.2f})")

print("\nDone!")
