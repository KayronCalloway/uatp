# UATP

**Cryptographic proof that AI made a decision, with this reasoning, at this time.**

[![CI](https://github.com/KayronCalloway/uatp/actions/workflows/ci.yml/badge.svg)](https://github.com/KayronCalloway/uatp/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](STATUS.md)

---

## Why This Exists

- **AI decisions are black boxes.** Regulators can't audit them. Courts can't examine them.
- **Liability is undefined.** When AI fails, who's responsible? No evidence trail exists.
- **Trust requires proof.** Not logs. Not promises. Cryptographic proof.

---

## The Proof

```python
from uatp import UATP

# 1. Create proof
capsule = UATP().certify(
    decision="Loan approved: $50,000 at 5.2% APR",
    reasoning=[
        {"step": 1, "thought": "Credit score 720 (excellent)"},
        {"step": 2, "thought": "Debt-to-income 0.28 (acceptable)"}
    ]
)

# 2. Verify proof
assert capsule.verify() == True

# 3. Tamper with it
capsule.decision = "Loan approved: $500,000"

# 4. Verification fails
assert capsule.verify() == False  # Signature invalid
```

**That's the entire value proposition.** Generate proof. Verify proof. Tamper. Verification fails.

---

## 60-Second Start

```bash
git clone https://github.com/KayronCalloway/uatp && cd uatp
pip install -e sdk/python
python -c "from uatp import UATP; print(UATP().certify(decision='test').verify())"
# Output: True
```

---

## What You Get

| Feature | Status | Notes |
|---------|--------|-------|
| Ed25519 signatures | Shipped | NIST-approved, Daubert-compliant |
| User-sovereign keys | Shipped | Private keys never leave your device |
| RFC 3161 timestamps | Beta | External TSA (DigiCert) |
| Python SDK | Shipped | `pip install` ready |
| Standalone verification | Shipped | No UATP trust required |

Full status: [STATUS.md](STATUS.md)

---

## Start Here

| You are... | Start with |
|------------|------------|
| **Developer** | [SDK Quickstart](sdk/python/QUICKSTART.md) → [Examples](examples/) → [API Docs](sdk/python/README.md) |
| **Security Reviewer** | [Trust Model](TRUST_MODEL.md) → [Threat Model](THREAT_MODEL.md) → [src/crypto/](src/crypto/) |
| **Evaluating for your org** | [Status](STATUS.md) → [Architecture](#architecture) → [Pricing](#pricing) |
| **Researcher** | [Trust Model](TRUST_MODEL.md) → [docs/](docs/) → [Roadmap](ROADMAP.md) |

---

## Architecture

```
uatp/
├── src/crypto/         # The core: Ed25519 signatures, key management
├── src/api/            # FastAPI backend
├── sdk/python/         # Python SDK
├── frontend/           # Next.js dashboard (beta)
├── tests/              # Test suite
├── infra/              # Docker, Kubernetes, monitoring
└── docs/               # Documentation
```

**Security architecture:**
- [TRUST_MODEL.md](TRUST_MODEL.md) - What UATP can and cannot do
- [THREAT_MODEL.md](THREAT_MODEL.md) - Attack surface and mitigations
- [SECURITY.md](SECURITY.md) - Vulnerability reporting

---

## The Trust Guarantee

UATP uses a zero-trust architecture:

```
┌─────────────────────────────┐
│  YOUR DEVICE                │
│  - Private key (encrypted)  │
│  - Signing happens here     │
│  - Content stays here       │
└──────────────┬──────────────┘
               │ Only hash sent
               ▼
┌─────────────────────────────┐
│  UATP SERVER                │
│  - Receives hash only       │
│  - Cannot see content       │
│  - Cannot forge signatures  │
└──────────────┬──────────────┘
               │ Hash for timestamp
               ▼
┌─────────────────────────────┐
│  EXTERNAL TSA (DigiCert)    │
│  - RFC 3161 timestamp       │
│  - Not controlled by UATP   │
└─────────────────────────────┘
```

**UATP cannot:**
- See your private key (it never leaves your device)
- Read your capsule content (only the hash)
- Forge your signature (cryptographically impossible)
- Backdate timestamps (external TSA)

---

## Pricing

**Open beta** - free while we gather feedback.

Planned:
- **Free:** 1,000 capsules/month
- **Pro:** $49/month (10,000 capsules)
- **Enterprise:** Custom

---

## Support

- [GitHub Issues](https://github.com/KayronCalloway/uatp/issues)
- [Discussions](https://github.com/KayronCalloway/uatp/discussions)
- Email: Kayron@houseofcalloway.com

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security issues: [SECURITY.md](SECURITY.md).

---

## License

MIT - see [LICENSE](LICENSE).

---

**The thesis:** AI decisions should be auditable with cryptographic proof.

**The proof:** `capsule.verify() == True` until someone tampers. Then `False`.

**The guarantee:** We can't forge it. We can't see it. We can't backdate it. [Here's why.](TRUST_MODEL.md)
