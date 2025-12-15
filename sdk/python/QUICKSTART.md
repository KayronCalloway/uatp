# UATP SDK Quickstart

Get your first AI decision certified in **under 5 minutes**.

## Prerequisites

- Python 3.8+
- Backend API running (see below)

## Step 1: Start the Backend (30 seconds)

```bash
# Clone the repo (if you haven't already)
git clone https://github.com/your-org/uatp-capsule-engine
cd uatp-capsule-engine

# Start the backend API
./start_backend_dev.sh
```

Wait for: `✓ Server running on http://localhost:8000`

## Step 2: Install the SDK (10 seconds)

```bash
cd sdk/python
pip install -e .
```

## Step 3: Test It Works (30 seconds)

```bash
# Run the SDK test
python3 test_actual_sdk.py
```

You should see:
```
🚀 UATP SDK Full Test - Using Actual SDK
============================================================

1. Initializing UATP client...
✅ Client initialized

2. Creating capsule via SDK...
✅ Capsule created successfully!
   Capsule ID: cap_...
   Proof URL: http://localhost:8000/capsules/cap_.../verify

3. Retrieving proof...
✅ Proof retrieved!

4. Listing recent capsules...
✅ Retrieved 5 capsules

5. Verifying signature...
✅ Signature valid: True

🎉 All SDK tests passed!
```

## Step 4: Write Your First Script (3 minutes)

Create `my_first_decision.py`:

```python
from uatp import UATP

# Initialize client
client = UATP()

# Certify an AI decision
result = client.certify(
    task="Recommend movie for Friday night",
    decision="Recommend: Inception (2010)",
    reasoning=[
        {
            "step": 1,
            "thought": "User likes sci-fi and Christopher Nolan",
            "confidence": 0.95
        },
        {
            "step": 2,
            "thought": "Inception matches preferences: sci-fi, mind-bending, well-rated",
            "confidence": 0.92
        },
        {
            "step": 3,
            "thought": "Available on streaming platforms",
            "confidence": 0.88
        }
    ],
    metadata={
        "model": "recommendation-engine-v1",
        "user_id": "demo_user"
    }
)

print(f"✅ Decision certified!")
print(f"Capsule ID: {result.capsule_id}")
print(f"Proof URL: {result.proof_url}")
print(f"Timestamp: {result.timestamp}")
```

Run it:
```bash
python3 my_first_decision.py
```

## Step 5: Verify Your Proof (30 seconds)

```bash
# Visit the proof URL (or curl it)
curl http://localhost:8000/capsules/YOUR_CAPSULE_ID/verify
```

You'll see:
```json
{
  "verified": true,
  "capsule_id": "cap_...",
  "signature": "ed25519:...",
  "message": "Capsule signature verified successfully"
}
```

## That's It! 🎉

You just:
1. ✅ Started the UATP backend
2. ✅ Installed the SDK
3. ✅ Created a certified AI decision
4. ✅ Got cryptographic proof
5. ✅ Verified the signature

## What You Have Now

Your AI decision is now:
- **Cryptographically signed** (Ed25519 signature)
- **Immutably stored** (can't be tampered with)
- **Court-admissible** (Daubert-compliant evidence)
- **Auditable** (proof URL anyone can verify)

## Next Steps

### Real AI Integration

#### With OpenAI:
```python
from openai import OpenAI
from uatp import UATP

openai_client = OpenAI()
uatp_client = UATP()

def make_auditable_decision(prompt: str):
    # Get AI response
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    decision = response.choices[0].message.content

    # Certify it with UATP
    result = uatp_client.certify(
        task=prompt,
        decision=decision,
        reasoning=[
            {"step": 1, "thought": "Analyzed user request", "confidence": 0.9},
            {"step": 2, "thought": "Generated response with GPT-4", "confidence": 0.85}
        ],
        metadata={"model": "gpt-4", "tokens": response.usage.total_tokens}
    )

    return decision, result.proof_url

# Use it
decision, proof = make_auditable_decision("Should I invest in bonds or stocks?")
print(f"Decision: {decision}")
print(f"Proof: {proof}")
```

#### With Anthropic Claude:
```python
from anthropic import Anthropic
from uatp import UATP

anthropic_client = Anthropic()
uatp_client = UATP()

def make_auditable_decision(task: str):
    # Get Claude's response
    message = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": task}]
    )

    decision = message.content[0].text

    # Certify with UATP
    result = uatp_client.certify(
        task=task,
        decision=decision,
        reasoning=[
            {"step": 1, "thought": "Analyzed task with Claude", "confidence": 0.9}
        ],
        metadata={"model": "claude-3-5-sonnet", "stop_reason": message.stop_reason}
    )

    return decision, result.proof_url

# Use it
decision, proof = make_auditable_decision("Explain quantum computing simply")
print(f"Decision: {decision}")
print(f"Proof: {proof}")
```

## Common Use Cases

### Healthcare AI
```python
result = client.certify(
    task="Review patient symptoms",
    decision="Recommend: Schedule follow-up with cardiologist",
    reasoning=[
        {"step": 1, "thought": "Patient reports chest pain", "confidence": 0.98},
        {"step": 2, "thought": "Family history of heart disease", "confidence": 0.95},
        {"step": 3, "thought": "Elevated blood pressure readings", "confidence": 0.92}
    ],
    metadata={"model": "medical-ai-v2", "patient_id": "redacted"}
)
```

### Financial Services
```python
result = client.certify(
    task="Credit decision for mortgage",
    decision="Approved: $300,000 at 6.5% APR",
    reasoning=[
        {"step": 1, "thought": "Credit score 750 (excellent)", "confidence": 0.99},
        {"step": 2, "thought": "Debt-to-income ratio 0.25 (good)", "confidence": 0.97},
        {"step": 3, "thought": "5 years employment stability", "confidence": 0.95}
    ],
    metadata={"model": "lending-ai-v3", "application_id": "app_12345"}
)
```

### Legal AI
```python
result = client.certify(
    task="Contract risk analysis",
    decision="3 high-risk clauses identified",
    reasoning=[
        {"step": 1, "thought": "Non-compete clause too broad", "confidence": 0.88},
        {"step": 2, "thought": "Indemnification unlimited", "confidence": 0.92},
        {"step": 3, "thought": "IP assignment overly restrictive", "confidence": 0.85}
    ],
    metadata={"model": "legal-ai-v1", "contract_id": "contract_789"}
)
```

## Troubleshooting

### Backend not running?
```bash
# Check if it's running
curl http://localhost:8000/health

# If not, start it
cd /path/to/uatp-capsule-engine
./start_backend_dev.sh
```

### Import errors?
```bash
# Make sure SDK is installed
cd sdk/python
pip install -e .
```

### Can't find capsules?
```bash
# Test the API directly
curl http://localhost:8000/capsules?demo_mode=false&per_page=5
```

## Full Documentation

- **README:** [Full SDK documentation](./README.md)
- **API Reference:** [API docs](../../docs/)
- **Examples:** [Working examples](./examples/)

## Support

Questions? Issues?
- GitHub Issues: https://github.com/your-org/uatp-sdk/issues
- Email: support@uatp.ai
- Docs: https://docs.uatp.ai

---

**You're ready to ship auditable AI.** 🚀
