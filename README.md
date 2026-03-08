# UATP: Court-Admissible AI Evidence in 3 Lines of Code

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)]()

Make AI decisions auditable with cryptographic proof. Ready to use today.

```python
from uatp import UATP

client = UATP()
result = client.certify(
    task="Approve loan application",
    decision="Loan approved for $50,000 at 5.2% APR",
    reasoning=[
        {"step": 1, "thought": "Credit score 720 (excellent)", "confidence": 0.99},
        {"step": 2, "thought": "Debt-to-income ratio 0.28 (acceptable)", "confidence": 0.95}
    ]
)

print(result.proof_url)
# http://localhost:8000/capsules/cap_abc123/verify
```

## Why UATP?

**Problem:** AI decisions are black boxes. Users don't trust them. Regulators can't audit them. Insurance companies won't cover them.

**Solution:** UATP provides **court-admissible cryptographic evidence** of AI reasoning.

### What You Get:

- **Ed25519 signatures** (NIST-approved, Daubert-compliant)
- **Immutable audit trails** (tamper-proof capsules)
- **EU AI Act compliance** (conformity assessments ready)
- **Insurance readiness** (actuarial data for AI liability coverage)

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/KayronCalloway/uatp
cd uatp
```

### 2. Start Backend

```bash
./start_backend_dev.sh
# Wait for: Server running on http://localhost:8000
```

### 3. Install Python SDK

```bash
cd sdk/python
pip install -e .
```

### 4. Test It Works

```bash
python3 test_actual_sdk.py
```

You should see:
```
UATP SDK Full Test - Using Actual SDK
============================================================

[OK] Client initialized
[OK] Capsule created successfully!
[OK] Proof retrieved!
[OK] Signature valid: True

All SDK tests passed!
```

### 5. Make Your First Decision Auditable

See the [SDK Quickstart](sdk/python/QUICKSTART.md) for detailed instructions.

## Use Cases

### Healthcare AI

```python
result = client.certify(
    task="Diagnose patient symptoms",
    decision="Likely common cold, recommend rest and fluids",
    reasoning=[
        {"step": 1, "thought": "Patient reports sore throat, congestion", "confidence": 0.98},
        {"step": 2, "thought": "No fever >101°F rules out flu", "confidence": 0.85}
    ],
    metadata={"patient_id": "redacted", "model": "medical-ai-v1"}
)
```

### Financial Services

```python
result = client.certify(
    task="Credit decision for auto loan",
    decision="Approved: $25,000 at 6.5% APR",
    reasoning=[...],
    metadata={"applicant_id": "redacted", "fair_lending_check": "passed"}
)
```

### Legal AI

```python
result = client.certify(
    task="Review employment contract",
    decision="3 concerning clauses identified",
    reasoning=[...],
    metadata={"contract_id": "contract_789", "jurisdiction": "CA"}
)
```

## Integration Examples

### With OpenAI

```python
from openai import OpenAI
from uatp import UATP

openai_client = OpenAI()
uatp_client = UATP()

# Get AI decision
response = openai_client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Should I invest in stocks or bonds?"}]
)

# Certify with UATP
result = uatp_client.certify(
    task="Investment advice",
    decision=response.choices[0].message.content,
    reasoning=[{"step": 1, "thought": "Analyzed market conditions", "confidence": 0.9}],
    metadata={"model": "gpt-4", "tokens": response.usage.total_tokens}
)

print(f"Proof: {result.proof_url}")
```

**Full examples:** [sdk/python/examples/](sdk/python/examples/)

## What's Working Today

- **Backend API** - FastAPI server with all endpoints working
- **Python SDK** - Full-featured client library
- **PostgreSQL database** - Persistent storage with 73+ capsules
- **Ed25519 signatures** - Cryptographic proof generation
- **Test suite** - All tests passing
- **Documentation** - Complete with examples
- **Integration examples** - OpenAI and Anthropic ready

See [TECHNICAL_READINESS.md](TECHNICAL_READINESS.md) for detailed status.

## Documentation

- **SDK Documentation:** [sdk/python/README.md](sdk/python/README.md)
- **SDK Quickstart:** [sdk/python/QUICKSTART.md](sdk/python/QUICKSTART.md)
- **API Examples:** [sdk/python/examples/](sdk/python/examples/)
- **Technical Readiness:** [TECHNICAL_READINESS.md](TECHNICAL_READINESS.md)
- **System Manual:** [docs/COMPREHENSIVE_SYSTEM_MANUAL.md](docs/COMPREHENSIVE_SYSTEM_MANUAL.md)

## Architecture

```
uatp-capsule-engine/
├── sdk/
│   └── python/              # Python SDK (ready to use)
│       ├── uatp/            # Core SDK code
│       ├── examples/        # Integration examples
│       ├── README.md        # SDK docs
│       └── QUICKSTART.md    # 5-minute quickstart
│
├── src/
│   ├── api/                 # FastAPI backend
│   ├── engine/              # Capsule engine core
│   ├── security/            # Cryptographic signatures
│   └── core/                # Database & models
│
├── frontend/                # React dashboard (in development)
├── tests/                   # Test suite
└── docs/                    # Documentation
```

## Pricing

Currently in **open beta** - free to use while we gather feedback!

Planned pricing:
- **Free tier:** 1,000 capsules/month
- **Professional:** $49/month (10,000 capsules)
- **Enterprise:** Custom pricing (unlimited + SLA)

## Support

- **Issues:** [GitHub Issues](https://github.com/KayronCalloway/uatp/issues)
- **Discussions:** [GitHub Discussions](https://github.com/KayronCalloway/uatp/discussions)
- **Email:** Kayron@houseofcalloway.com

**Looking for beta testers!** We'd love your feedback.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Why Cryptographic Proof Matters

### Without UATP:
- AI decisions are black boxes
- No audit trail for regulators
- Insurance companies won't cover
- Users don't trust the system
- Liability is unclear

### With UATP:
- Cryptographic evidence of reasoning
- Court-admissible proof (Daubert-compliant)
- EU AI Act conformity assessments ready
- Insurance-ready actuarial data
- User transparency via proof URLs

## Roadmap

**Shipping now (Beta):**
- Python SDK
- Backend API
- Cryptographic signatures
- PostgreSQL storage

**Coming soon:**
- Web dashboard for viewing proofs
- JavaScript/TypeScript SDK
- API key authentication
- PyPI package
- Hosted service (SaaS)
- Payment integration
- Data marketplace

**Future releases:**
- Advanced consensus mechanisms
- Post-quantum cryptography
- Zero-knowledge proofs
- Economic attribution systems

## Get Started Now

```bash
git clone https://github.com/KayronCalloway/uatp
cd uatp
./start_backend_dev.sh

cd sdk/python
pip install -e .
python3 test_actual_sdk.py
```

**Ship auditable AI in 5 minutes.**

---

**Built with:** Python, FastAPI, PostgreSQL, Ed25519, React
**Status:** Open Beta
**Community:** [Join the discussion](https://github.com/KayronCalloway/uatp/discussions)
