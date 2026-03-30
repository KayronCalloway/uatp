# UATP v1.1

**Cryptographic audit trails for AI decisions — with honest truth separation.**

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

## What's New in v1.1

**Gold Standard Architecture** — Honest separation between what's verified and what's interpretation:

| Layer | What It Contains | Proof Level |
|-------|------------------|-------------|
| **Events** | What literally happened (tool calls, messages) | `tool_verified` |
| **Evidence** | What artifacts prove (signatures, hashes) | `crypto_verified` |
| **Interpretation** | What the model thinks | `model_generated` (unverified) |
| **Judgment** | Gated labels (court-admissible, insurance-ready) | Only when gates pass |

**Self-Inspection** — A protocol that can accuse itself is closer to truth:
- Semantic drift detection (summary doesn't address the question)
- Quality consistency checks (perfect scores with failing grades)
- Confidence-evidence alignment (high confidence without evidence)
- Unearned label detection (claiming court-admissible without verification)

**Honest Compliance** — Labels are earned, not claimed:
- `court_admissible` requires: signature + trusted timestamp + no semantic drift
- `insurance_ready` requires: historical accuracy data + risk assessment
- Blockers are shown transparently when gates don't pass

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

### The Problem

Most AI audit systems conflate two different things:
1. **Provenance** — cryptographic proof that data exists and hasn't been tampered with
2. **Interpretation** — what the AI thinks, which is valuable but unverified

When a system claims "court-admissible" or "insurance-ready" without separating these layers, it's theater.

### The Solution: Layered Capsules

UATP v1.1 separates truth into layers with explicit proof tags:

```
┌─────────────────────────────────────────────────────────────┐
│  CAPSULE                                                     │
├─────────────────────────────────────────────────────────────┤
│  EVENTS (tool_verified)                                      │
│  - User sent message at 14:32:01                            │
│  - Tool "Read" executed on config.py                        │
│  - Git commit abc123 was current                            │
├─────────────────────────────────────────────────────────────┤
│  EVIDENCE (crypto_verified)                                  │
│  - Ed25519 signature: valid                                  │
│  - RFC 3161 timestamp: DigiCert, trusted                    │
│  - File hash: sha256:def456...                              │
├─────────────────────────────────────────────────────────────┤
│  INTERPRETATION (model_generated — UNVERIFIED)              │
│  - Summary: "Fixed the authentication bug"                  │
│  - Confidence: 0.85 (heuristic, not calibrated)            │
│  - Quality grade: B                                          │
├─────────────────────────────────────────────────────────────┤
│  JUDGMENT (gated — must be earned)                          │
│  - court_admissible: true (all gates passed)                │
│  - insurance_ready: false (missing historical data)         │
│  - blockers: ["Insufficient accuracy history"]              │
└─────────────────────────────────────────────────────────────┘
```

### Proof Levels

Every claim carries a proof tag:

| Proof Level | Meaning | Example |
|-------------|---------|---------|
| `tool_verified` | Verified by tool execution | Message captured, file read |
| `artifact_verified` | Verified from artifact | Git commit hash, file hash |
| `crypto_verified` | Cryptographically verified | Ed25519 signature, RFC 3161 |
| `derived` | Derived from verified facts | Logical inference from events |
| `heuristic` | Based on patterns (not calibrated) | Confidence scores |
| `model_generated` | AI output (unverified) | Summaries, quality assessments |
| `speculative` | Uncertain | Predictions without evidence |
| `untested` | Not yet verified | Claims awaiting validation |

### Self-Inspection

Before finalizing a capsule, UATP runs contradiction detection:

```
[!] SEMANTIC_DRIFT: Summary does not address user request.
    User asked about: authentication, bug, login
    Summary covers: database, caching, redis
    Recommendation: Regenerate summary to address the actual question

[?] EVIDENCE_GAP: High confidence (95%) claimed with no supporting evidence
    Recommendation: Confidence should be proportional to evidence

[!] UNEARNED_LABEL: Claims 'court_admissible' but missing:
    - verified timestamp
    - semantic consistency (drift detected)
    Recommendation: Remove court_admissible label until gates pass
```

**What's working today:**
- **Ed25519 signatures** — tamper-evident, locally-signed, keys never leave your device
- **RFC 3161 timestamps** — external time authority (DigiCert) - beta*
- **Layered capsule architecture** — events, evidence, interpretation, judgment
- **Self-inspection** — contradiction detection before signing
- **Honest compliance gates** — labels only claimed when earned
- **Standalone verification** — verify capsules without trusting UATP servers
- **DSSE bundles** — Sigstore-compatible export

*\*RFC 3161: Timestamp presence is verified; full TSA signature verification requires optional `rfc3161ng` library. See [TRUST_MODEL.md](TRUST_MODEL.md).*

**What's experimental:**
- ML-DSA-65 post-quantum signatures (beta, not audited)
- Confidence calibration against historical outcomes

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
| **Understand the layers** | [What It Does](#what-it-does) → [Proof Levels](#proof-levels) |
| **Inspect the crypto** | [Trust Model](TRUST_MODEL.md) → [src/crypto/](src/crypto/) |
| **Integrate the SDK** | [SDK Docs](sdk/python/README.md) → [API Reference](docs/api-documentation.md) |
| **Understand the vision** | [Vision](docs/vision.md) |
| **Navigate the codebase** | [Repository Map](docs/repository-map.md) |

---

## Architecture

```
uatp/
├── src/
│   ├── api/                # FastAPI backend
│   ├── auth/               # JWT, RBAC, middleware
│   ├── core/               # Gold standard modules
│   │   ├── provenance.py   # Layered capsule architecture
│   │   ├── contradiction_engine.py  # Self-inspection
│   │   └── layered_capsule_builder.py
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
│  - Private key (encrypted)  │
│  - ALL signing happens here │
│  - Ed25519 + PBKDF2 480K    │
│  - Keys stored ~/.uatp/keys │
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

**Backend (`python run.py`) — Gold Standard v1.1:**

| Component | Status | Notes |
|-----------|--------|-------|
| Capsule storage API | Working | SQLite/PostgreSQL |
| Layered capsule architecture | **New in v1.1** | Events → Evidence → Interpretation → Judgment |
| Self-inspection | **New in v1.1** | Contradiction detection before signing |
| Honest compliance gates | **New in v1.1** | Labels earned, not claimed |
| Proof level tags | **New in v1.1** | Every claim carries its proof status |
| Full-text search | Working | FTS5 / ts_vector |
| RFC 3161 timestamps | Beta | DigiCert TSA integration |

**Experimental (code exists, not stable):**

| Component | Status |
|-----------|--------|
| ML-DSA-65 (post-quantum) | Beta, not audited |
| Confidence calibration | Planned |
| Workflow attestation | Beta |
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

**What makes v1.1 different:** Most audit systems claim compliance without earning it. UATP v1.1 separates verified facts from model interpretation, runs self-inspection for contradictions, and only claims labels when verification gates pass.

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

**v1.1 Philosophy:** A protocol that can accuse itself is closer to truth. By separating verified facts from interpretation, detecting its own contradictions, and only claiming labels when they're earned, UATP moves beyond "audit theater" toward genuine accountability.

[Full vision →](docs/vision.md)

---

## License

MIT — see [LICENSE](LICENSE).
