# UATP Python SDK

Cryptographic proof that AI made a decision, with this reasoning, at this time.

## Installation

```bash
pip install uatp
```

Or from source:
```bash
git clone https://github.com/KayronCalloway/uatp
cd uatp/sdk/python
pip install -e .
```

## Quick Start

```python
from uatp import UATP

client = UATP()

# Create proof
capsule = client.certify(
    decision="Loan approved: $50,000 at 5.2% APR",
    reasoning=[
        {"step": 1, "thought": "Credit score 720 (excellent)"},
        {"step": 2, "thought": "Debt-to-income 0.28 (acceptable)"}
    ]
)

# Verify proof
assert capsule.verify() == True

# Tamper detection
capsule.decision = "Loan approved: $500,000"
assert capsule.verify() == False  # Signature invalid
```

## What This Does

UATP creates independently verifiable proof that:
- A decision existed in this form
- At this specific time
- Tampering breaks verification

## Features

| Feature | Status |
|---------|--------|
| Ed25519 signatures | Shipped |
| User-sovereign keys | Shipped |
| RFC 3161 timestamps | Beta |
| Standalone verification | Shipped |

## API Reference

### `UATP(base_url="http://localhost:8000")`

Initialize client.

```python
client = UATP()  # Local development
client = UATP(base_url="https://your-server.com")  # Production
```

### `client.certify(decision, reasoning, task=None, confidence=None, metadata=None)`

Create cryptographically signed capsule.

```python
result = client.certify(
    task="Approve loan",
    decision="Approved for $50,000",
    reasoning=[
        {"step": 1, "thought": "Good credit", "confidence": 0.95}
    ],
    confidence=0.87,
    metadata={"model": "gpt-4"}
)
```

**Returns:** `CertificationResult` with `capsule_id`, `proof_url`, `signature`, `timestamp`

### `client.get_proof(capsule_id)`

Retrieve full proof.

```python
proof = client.get_proof("cap_abc123")
print(proof.decision)
print(proof.verify())  # True or False
```

### `client.list_capsules(limit=10)`

List capsules.

```python
capsules = client.list_capsules(limit=10)
for c in capsules:
    print(f"{c.capsule_id}: {c.task}")
```

## Local Signing (Recommended)

For maximum security, sign locally without sending content to server:

```python
from uatp import UATP

client = UATP()

# Sign locally - private key never leaves your device
result = client.certify_local(
    decision="Sensitive decision",
    reasoning=[...],
    passphrase="your-secure-passphrase"
)

# Only hash sent to server for timestamping
# Content stays local
```

## Running the Backend

```bash
cd uatp
./scripts/dev/start_backend_dev.sh
# Server runs on http://localhost:8000
```

## Integration Examples

### With OpenAI

```python
from openai import OpenAI
from uatp import UATP

openai = OpenAI()
uatp = UATP()

response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Should I invest in stocks?"}]
)

result = uatp.certify(
    task="Investment advice",
    decision=response.choices[0].message.content,
    reasoning=[{"step": 1, "thought": "Analyzed request"}],
    metadata={"model": "gpt-4"}
)

print(result.proof_url)
```

### With Anthropic

```python
from anthropic import Anthropic
from uatp import UATP

claude = Anthropic()
uatp = UATP()

message = claude.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Review this contract"}]
)

result = uatp.certify(
    task="Contract review",
    decision=message.content[0].text,
    reasoning=[{"step": 1, "thought": "Analyzed contract"}]
)
```

## Error Handling

```python
try:
    result = client.certify(...)
except ValueError as e:
    print(f"Invalid parameters: {e}")
except ConnectionError as e:
    print(f"Server unavailable: {e}")
```

## Status

See [STATUS.md](../../STATUS.md) for what's shipped vs beta vs experimental.

## Support

- Issues: https://github.com/KayronCalloway/uatp/issues
- Email: Kayron@houseofcalloway.com

## License

MIT
