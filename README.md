# UATP

**Cryptographic audit trails for AI decisions.**

[![CI](https://github.com/KayronCalloway/uatp/actions/workflows/ci.yml/badge.svg)](https://github.com/KayronCalloway/uatp/actions/workflows/ci.yml)
[![Security](https://github.com/KayronCalloway/uatp/actions/workflows/security.yml/badge.svg)](https://github.com/KayronCalloway/uatp/actions/workflows/security.yml)
[![PyPI](https://img.shields.io/pypi/v/uatp)](https://pypi.org/project/uatp/)
[![npm](https://img.shields.io/npm/v/@coolwithakay/uatp)](https://www.npmjs.com/package/@coolwithakay/uatp)
[![Downloads](https://img.shields.io/pypi/dm/uatp)](https://pypi.org/project/uatp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](STATUS.md)

---

## Try It Now

**Python:**
```bash
pip install uatp
python -c "
from uatp import UATP
result = UATP().certify(
    task='Hello World',
    decision='First cryptographic audit trail',
    reasoning=[{'step': 1, 'thought': 'It works', 'confidence': 1.0}]
)
print(f'Signed: {result.signature[:32]}...')
"
```

**TypeScript / JavaScript:**
```bash
npm install @coolwithakay/uatp
```
```typescript
import { UATP } from '@coolwithakay/uatp';

const client = new UATP();
const result = await client.certify({
  task: 'Hello World',
  decision: 'First cryptographic audit trail',
  reasoning: [{ step: 1, thought: 'It works', confidence: 1.0 }]
});
console.log(`Signed: ${result.signature.slice(0, 32)}...`);
```

Your private key was just generated locally and never transmitted anywhere.

---

## Packages

| Package | Install | Purpose |
|---------|---------|---------|
| `uatp` | `pip install uatp` | Python SDK (recommended) |
| `@coolwithakay/uatp` | `npm install @coolwithakay/uatp` | TypeScript SDK |
| `uatp-engine` | `pip install -e .` (local) | Backend server (for operators) |

**Most users should install the SDK.** The engine is only needed if you're running your own UATP server.

---

## Three Ways to Run

| Goal | Command | What You Get |
|------|---------|--------------|
| **SDK only** | `pip install uatp` | Local signing, no server needed |
| **Full local app** | `./start-dev.sh` | Backend + dashboard at localhost:3000 |
| **Docker** | `docker compose up` | Everything containerized |

### Option 1: SDK Only (Simplest)

```bash
pip install uatp
python examples/hello_world.py
```

Or with TypeScript:
```bash
npm install @coolwithakay/uatp
```

### Option 2: Full Local App (One Command)

```bash
git clone https://github.com/KayronCalloway/uatp.git
cd uatp
./start-dev.sh
```

Opens http://localhost:3000 automatically.

### Option 3: Docker (Least Setup)

```bash
git clone https://github.com/KayronCalloway/uatp.git
cd uatp
docker compose up
```

Open http://localhost:3000

### Web Dashboard

Once running, go to http://localhost:3000:

1. **Sign up** — Create account with email/username/password
2. **Login** — Cookie-based auth (HTTP-only, XSS-resistant)
3. **Browse capsules** — View your cryptographically signed audit trails

**Access model:**
- Regular users see only their own capsules
- Admin users see all capsules system-wide

---

## What It Does

UATP creates verifiable capsules for AI reasoning: cryptographically signed records that prove what decision was made, with what reasoning, at what time.

**What's working today:**
- **Ed25519 signatures** — tamper-evident, locally-signed, keys never leave your device
- **RFC 3161 timestamps** — external time authority (DigiCert) - beta*
- **Standalone verification** — verify capsules without trusting UATP servers
- **DSSE bundles** — Sigstore-compatible export

*\*RFC 3161: Timestamp presence is verified; full TSA signature verification requires optional `rfc3161ng` library. See [TRUST_MODEL.md](TRUST_MODEL.md).*

**What's experimental:**
- ML-DSA-65 post-quantum signatures (beta, not audited)
- Platform modules (attribution, governance, economics) - not part of core protocol

See [TRUST_MODEL.md](TRUST_MODEL.md) for security assumptions. See [STATUS.md](STATUS.md) for what's shipped.

![UATP Capsule Dashboard](docs/images/capsule-verified.png)
*Verified capsule showing reasoning process, confidence metrics, and cryptographic verification.*

---

## Create a Capsule

```python
from uatp import UATP

client = UATP()

result = client.certify(
    task="Loan decision",
    decision="Approved for $50,000 at 5.2% APR",
    reasoning=[
        {"step": 1, "thought": "Credit score 720 (excellent)", "confidence": 0.95},
        {"step": 2, "thought": "Debt-to-income 0.28 (acceptable)", "confidence": 0.90}
    ]
)

print(f"Capsule ID: {result.capsule_id}")
print(f"Signature: {result.signature[:32]}...")
```

More examples: [examples/](examples/)

---

## Start Here

| Goal | Path |
|------|------|
| **Try it locally** | [Try It Now](#try-it-now) → [Examples](examples/) |
| **Inspect the crypto** | [Trust Model](TRUST_MODEL.md) → [src/crypto/](src/crypto/) |
| **Integrate the SDK** | [SDK Docs](sdk/python/README.md) → [API Reference](docs/api-documentation.md) |
| **Understand the vision** | [Vision](docs/vision.md) |
| **Navigate the codebase** | [Repository Map](docs/repository-map.md) |

---

## Architecture

```
uatp/
├── src/                    # ~30 modules
│   ├── api/                # FastAPI backend
│   ├── auth/               # JWT, RBAC, middleware
│   ├── attestation/        # Workflow attestation (in-toto style)
│   ├── capsules/           # Core capsule logic
│   ├── cli/                # CLI tools (verify, export, inspect)
│   ├── crypto/             # Key management (UserKeyManager, LocalSigner)
│   ├── database/           # SQLite/PostgreSQL adapters
│   ├── export/             # DSSE bundle export (Sigstore style)
│   ├── live_capture/       # Real-time capture + signal detection
│   ├── models/             # SQLAlchemy models
│   ├── schema/             # Capsule schema, facets
│   ├── security/           # Ed25519/ML-DSA signatures, RFC 3161
│   ├── services/           # Search, lifecycle
│   └── ...                 # +17 more (middleware, observability, etc.)
├── sdk/
│   ├── python/             # Python SDK (pip install uatp)
│   └── typescript/         # TypeScript SDK (npm @coolwithakay/uatp)
├── frontend/               # Next.js dashboard (beta)
├── tests/                  # 1500+ tests
└── infra/                  # Docker, Kubernetes configs
```

Full module list: [Repository Map](docs/repository-map.md)

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
| `security.yml` | Bandit, Safety, Gitleaks, Trivy scans |
| `release.yml` | Versioned releases |

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

AI systems that shape outcomes should leave verifiable memory behind. UATP provides the cryptographic foundation—starting with audit trails, extensible to attribution and accountability.

[Full vision →](docs/vision.md)

---

## License

MIT — see [LICENSE](LICENSE).
