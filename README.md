# UATP

**Cryptographic audit trails for AI decisions.**

[![CI](https://github.com/KayronCalloway/uatp/actions/workflows/ci.yml/badge.svg)](https://github.com/KayronCalloway/uatp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/uatp)](https://pypi.org/project/uatp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](STATUS.md)

> **Current state: Beta.** The SDK and core signing work. Not independently audited. The repo also contains experimental platform code beyond the core protocol. See [STATUS.md](STATUS.md) for what's actually shipped.

---

## What It Does

UATP creates verifiable capsules for AI reasoning: cryptographically signed records that prove what decision was made, with what reasoning, at what time.

**What's working today (SDK path):**
- **Ed25519 signatures** — tamper-evident, locally-signed, keys never leave your device
- **RFC 3161 timestamps** — external time authority (DigiCert) - beta
- **Standalone verification** — verify capsules without trusting UATP servers
- **DSSE bundles** — Sigstore-compatible export

**What's experimental:**
- ML-DSA-65 post-quantum signatures (beta, not audited)
- Server-side capture engine (legacy architecture, being deprecated)
- Platform modules (attribution, governance, economics) - not part of core protocol

See [TRUST_MODEL.md](TRUST_MODEL.md) for security assumptions and limitations.

![UATP Capsule Dashboard](docs/images/capsule-verified.png)
*A verified capsule showing reasoning process, confidence metrics, and cryptographic verification status.*

---

## Quick Start

### 1. Install the SDK

```bash
pip install uatp
```

### 2. Start the backend (if running locally)

```bash
git clone https://github.com/KayronCalloway/uatp.git
cd uatp
pip install -e .
python run.py
```

**That's it for development.** The backend:
- Uses SQLite by default (no database setup needed)
- Runs on `http://localhost:8000`
- Auto-creates `uatp_dev.db` on first run

**Optional:** Copy `.env.example` to `.env` to customize settings (JWT secrets, PostgreSQL, etc.)

### 2b. Start the frontend (optional)

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Opens dashboard at `http://localhost:3000`

### 3. Create a capsule

```python
from uatp import UATP

client = UATP()  # Connects to localhost:8000

# Zero-trust: signing happens locally, private key never leaves your device
result = client.certify(
    task="Loan decision",
    decision="Approved for $50,000 at 5.2% APR",
    reasoning=[
        {"step": 1, "thought": "Credit score 720 (excellent)", "confidence": 0.95},
        {"step": 2, "thought": "Debt-to-income 0.28 (acceptable)", "confidence": 0.90}
    ]
)

print(f"Capsule ID: {result.capsule_id}")
print(f"Signature: {result.signature[:32]}...")  # Ed25519 signature
print(f"Public Key: {result.public_key[:32]}...")  # Your verify key
```

**Security modes:**
```python
# Device-bound (default): CONVENIENCE mode - passphrase derived from machine info
# Good for: development, demos, low-stakes use
# Not recommended for: production with sensitive data
result = client.certify(task=..., decision=..., reasoning=...)

# Custom passphrase: RECOMMENDED for production
# Provides: user-controlled entropy, portability across machines
result = client.certify(
    task=..., decision=..., reasoning=...,
    passphrase="your-secure-passphrase",
    device_bound=False
)
```

Full setup: [SDK Quickstart](sdk/python/QUICKSTART.md)

---

## Start Here

| Goal | Path |
|------|------|
| **Try it locally** | [Quick Start](#quick-start) → [Examples](examples/) |
| **Inspect the crypto** | [Trust Model](TRUST_MODEL.md) → [src/crypto/](src/crypto/) |
| **Integrate the SDK** | [SDK Docs](sdk/python/README.md) → [API Reference](docs/api-documentation.md) |
| **Understand the vision** | [Vision](docs/vision.md) → [Complete Vision](docs/UATP_COMPLETE_VISION.md) |
| **Navigate the codebase** | [Repository Map](docs/repository-map.md) |

---

## Architecture

```
uatp/
├── src/
│   ├── api/            # FastAPI backend
│   ├── attestation/    # Workflow attestation (in-toto style)
│   ├── cli/            # CLI tools (verify, export, inspect)
│   ├── crypto/         # Key management
│   ├── export/         # DSSE bundle export (Sigstore style)
│   ├── live_capture/   # Real-time capture with feedback signal detection
│   ├── schema/         # Schema definitions and facets
│   ├── security/       # Ed25519/ML-DSA signatures, RFC 3161
│   └── services/       # Search, lifecycle services
├── sdk/python/         # Python SDK
├── frontend/           # Next.js dashboard (beta)
├── tests/              # 1400+ tests
└── infra/              # Docker, Kubernetes configs
```

Full structure with audit priorities: [Repository Map](docs/repository-map.md)

**Security documentation:**
- [TRUST_MODEL.md](TRUST_MODEL.md) — What UATP can and cannot do
- [THREAT_MODEL.md](THREAT_MODEL.md) — Attack surface and mitigations
- [SECURITY.md](SECURITY.md) — Vulnerability reporting

---

## How Verification Works

**SDK Zero-Trust Flow:** The SDK signs capsules locally. Your private key never leaves your device.

```
┌─────────────────────────────┐
│  YOUR DEVICE                │
│  ✓ Private key (encrypted)  │
│  ✓ ALL signing happens here │
│  ✓ Ed25519 + PBKDF2 480K    │
│  ✓ Keys stored ~/.uatp/keys │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  UATP SERVER                │
│  Default: hash only         │
│  Optional: store capsule    │
└──────────────┬──────────────┘
               │ Hash for timestamp
               ▼
┌─────────────────────────────┐
│  EXTERNAL TSA (DigiCert)    │
│  - RFC 3161 timestamp       │
│  - Independent authority    │
└─────────────────────────────┘
```

**What the server sees (SDK default `store_on_server=False`):**
- Hash only (32 bytes) — for timestamping
- No capsule content transmitted

**What the server sees (if `store_on_server=True`):**
- Full signed capsule including content
- Use this for server-side storage/search

UATP operators **cannot** sign on behalf of users—the SDK generates and stores private keys locally and never transmits them. See [TRUST_MODEL.md](TRUST_MODEL.md) for security assumptions.

---

## CI/CD

| Workflow | Purpose |
|----------|---------|
| `ci.yml` | Tests, lint, type checking on push/PR |
| `security-scan.yml` | Comprehensive security analysis |
| `security.yml` | Gitleaks, Trivy scans |
| `release.yml` | Versioned releases |
| `build.yml` | Docker image builds |
| `code-quality.yml` | Pre-commit, ruff, mypy |
| `test.yml` | Test matrix (Python 3.10/3.11, SQLite/PostgreSQL) |
| `performance.yml` | Performance benchmarks |
| `blue-green-deploy.yml` | Production deployments |

---

## What's Shipped vs Planned

**SDK (`pip install uatp`) — the recommended path:**

| Component | Status | Notes |
|-----------|--------|-------|
| Ed25519 local signing | Working | Keys never leave device |
| Capsule verification | Working | Standalone, no server needed |
| Local key management | Working | UserKeyManager, LocalSigner |
| Device-bound keys | Working | Convenience mode, see security notes below |
| DSSE bundle export | Working | Sigstore-compatible |

**Backend (`python run.py`) — less mature:**

| Component | Status | Notes |
|-----------|--------|-------|
| Capsule storage API | Working | SQLite/PostgreSQL |
| Full-text search | Working | FTS5 / ts_vector |
| RFC 3161 timestamps | Beta | DigiCert TSA integration |
| Server-side signing | Legacy | Being deprecated, see TRUST_MODEL.md |

**Experimental (code exists, not stable):**

| Component | Status |
|-----------|--------|
| ML-DSA-65 (post-quantum) | Beta, not audited |
| Workflow attestation | Beta |
| Platform modules (attribution, governance) | Experimental |
| Next.js frontend | Beta |
| Hosted SaaS | Planned Q3 2026 |

Full breakdown: [STATUS.md](STATUS.md)

---

## How UATP Compares

| System | Primary Purpose | What UATP Adds |
|--------|-----------------|----------------|
| **MLflow** | Experiment tracking | Cryptographic proof, user-sovereign keys |
| **Weights & Biases** | ML observability | Independent verification, zero-trust |
| **Sigstore / DSSE** | Artifact signing | AI decision-specific capsules, reasoning traces |
| **in-toto** | Supply chain attestation | Decision memory, not just build steps |
| **OpenTelemetry** | Distributed tracing | Tamper-evident, legally defensible records |

UATP is not a replacement for these tools—it adds a cryptographic proof layer for AI decisions that can integrate with existing infrastructure.

---

## Support

- [GitHub Issues](https://github.com/KayronCalloway/uatp/issues)
- [Discussions](https://github.com/KayronCalloway/uatp/discussions)
- Email: Kayron@houseofcalloway.com

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security issues: [SECURITY.md](SECURITY.md).

---

## Vision

UATP begins as a cryptographic audit trail for AI decisions. Over time, that same proof infrastructure can support broader accountability: provenance, attribution, consent, auditability, and eventually fairer economic participation in AI systems. The core idea is simple: systems that shape the world should leave verifiable memory behind.

Read the full vision → [docs/vision.md](docs/vision.md)

---

## License

MIT — see [LICENSE](LICENSE).
