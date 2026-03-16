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
from uatp import UATP, verify_capsule_standalone

client = UATP()

# Create proof (signs locally, sends hash only to server by default)
signed = client.certify(
    task="Loan decision",
    decision="Loan approved: $50,000 at 5.2% APR",
    reasoning=[
        {"step": 1, "thought": "Credit score 720 (excellent)"},
        {"step": 2, "thought": "Debt-to-income 0.28 (acceptable)"}
    ]
)

print(f"Capsule ID: {signed.capsule_id}")
print(f"Signature: {signed.signature[:32]}...")

# Verify locally (no server needed)
from uatp import LocalSigner
signer = LocalSigner(passphrase="your-passphrase")
is_valid = signer.verify_capsule(signed)
print(f"Valid: {is_valid}")
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

### `client.certify(task, decision, reasoning, confidence=None, metadata=None, store_on_server=False)`

Create cryptographically signed capsule. Signs locally by default.

```python
signed = client.certify(
    task="Approve loan",
    decision="Approved for $50,000",
    reasoning=[
        {"step": 1, "thought": "Good credit", "confidence": 0.95}
    ],
    confidence=0.87,
    metadata={"model": "gpt-4"}
)
```

**Returns:** `SignedCapsule` with:
- `capsule_id` - Unique identifier
- `signature` - Ed25519 signature (hex)
- `public_key` - Verification key (hex)
- `content_hash` - SHA-256 of content
- `signed_at` - Timestamp
- `content` - The actual capsule content (stays local unless stored)

### `client.get_proof(capsule_id)`

Retrieve proof from server (requires `store_on_server=True` when creating).

```python
proof = client.get_proof("cap_abc123")
print(proof.capsule_id)
print(proof.verify())  # True if signature valid, False otherwise
```

### `client.list_capsules(limit=10)`

List capsules.

```python
capsules = client.list_capsules(limit=10)
for c in capsules:
    print(f"{c.capsule_id}: {c.capsule_type} ({c.status})")
```

## Local Signing (Default)

All signing happens locally. Private key never leaves your device.

```python
from uatp import UATP

client = UATP()

# Default: store_on_server=False
# Signs locally, sends only hash for timestamping
signed = client.certify(
    task="Sensitive decision",
    decision="Approved",
    reasoning=[{"step": 1, "thought": "Analysis complete"}],
    passphrase="your-secure-passphrase"  # Optional: uses device-bound key if omitted
)

# Content stays local, only hash sent to server
print(f"Content hash: {signed.content_hash}")

# To also store on server (for retrieval/search):
signed = client.certify(
    ...,
    store_on_server=True  # Full capsule sent to server
)
```

## Running the Backend

```bash
git clone https://github.com/KayronCalloway/uatp.git
cd uatp
pip install -e .
python run.py
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
