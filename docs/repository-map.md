# Repository Map

## Overview

UATP is organized into four layers: core cryptography, API server, client SDK, and infrastructure. Each can be audited independently.

```
uatp/
├── src/                 # Core engine (Python)
├── sdk/python/          # Published SDK (pip install uatp)
├── frontend/            # Next.js dashboard (beta)
├── infra/               # Docker, Kubernetes configs
├── tests/               # Test suite
├── docs/                # Documentation
└── archive/             # Dormant modules (future phases)
```

---

## Source Code (`src/`)

### Security-Critical (Audit Priority 1)

| Directory | Purpose | Key Files | Notes |
|-----------|---------|-----------|-------|
| `src/crypto/` | Core cryptographic operations | `local_signer.py`, `post_quantum.py`, `secure_key_manager.py` | Ed25519 signing, key generation. **Private keys never leave this module.** |
| `src/security/` | Timestamps, HSM, crypto utilities | `uatp_crypto_v7.py`, `rfc3161_timestamps.py`, `hsm_integration.py` | External integrations with DigiCert TSA. |

### API Layer (Audit Priority 2)

| Directory | Purpose | Key Files | Notes |
|-----------|---------|-----------|-------|
| `src/api/` | FastAPI routes, request handling | `capsules_fastapi_router.py`, `chain_fastapi_router.py` | HTTP attack surface. Input validation happens here. |
| `src/auth/` | Authentication, authorization | `jwt_handler.py`, `jwt_manager.py`, `rbac.py` | JWT tokens, role-based access control. |
| `src/middleware/` | Request processing | `security.py`, `rate_limiting.py`, `logging.py` | Security headers, rate limits, audit logging. |

### Core Engine (Audit Priority 3)

| Directory | Purpose | Key Files | Notes |
|-----------|---------|-----------|-------|
| `src/engine/` | Capsule processing logic | `capsule_engine.py`, `ethics_circuit_breaker.py` | Business logic for capsule creation/verification. |
| `src/models/` | Database models | `capsule.py`, `user.py`, `payment.py` | SQLAlchemy models. Schema definitions. |
| `src/database/` | Database connections | `connection.py`, `migrations.py` | PostgreSQL/SQLite async support. |

### Supporting Modules

| Directory | Purpose | Notes |
|-----------|---------|-------|
| `src/live_capture/` | Real-time capsule generation | Claude Code integration, conversation monitoring. |
| `src/analysis/` | Confidence calibration, quality assessment | Post-hoc analysis of capsule chains. |
| `src/reasoning/` | Reasoning chain extraction | Causal graphs, structural models. |
| `src/filters/` | Content filtering, capsule creation helpers | Universal filter, integration layer. |
| `src/resilience/` | Circuit breakers, crisis response | Fault tolerance patterns. |
| `src/privacy/` | Privacy controls, consent | Zero-knowledge proofs, consent management. |
| `src/payments/` | Payment processing | Stripe integration, payment service. |
| `src/insurance/` | Insurance API models | Liability coverage schemas (Phase 2). |

---

## SDK (`sdk/python/`)

The published `pip install uatp` package. Minimal dependencies, designed for airgapped environments.

```
sdk/python/
├── uatp/
│   ├── client.py        # Main API client
│   ├── signer.py        # Local signing (never transmits private keys)
│   ├── verifier.py      # Standalone verification (no server needed)
│   └── types.py         # Type definitions
├── examples/            # Usage examples
└── QUICKSTART.md        # Getting started guide
```

**Security property:** The SDK can verify capsules without any network connection. Verification is cryptographic, not trust-based.

---

## Frontend (`frontend/`)

Next.js dashboard for viewing and managing capsules. Currently in beta.

```
frontend/
├── src/
│   ├── app/             # Next.js app router pages
│   ├── components/      # React components
│   │   └── capsules/    # Capsule display components
│   └── lib/             # API client, utilities
└── public/              # Static assets
```

**Note:** The frontend is optional. All functionality is available via API.

---

## Tests (`tests/`)

| Directory | Coverage | Notes |
|-----------|----------|-------|
| `tests/unit/` | Isolated function tests | Fast, no external dependencies. |
| `tests/integration/` | Database + API tests | Requires running database. |
| `tests/security/` | Crypto edge cases | Timing attacks, malformed inputs. |
| `tests/capture/` | Live capture integration | Local development only. |
| `tests/legacy/` | Archived tests | Excluded from CI. |

Run tests: `pytest tests/ --ignore=tests/legacy --ignore=tests/integration`

---

## Infrastructure (`infra/`)

Docker, Kubernetes, and deployment configs. Not required for local development.

```
infra/
├── docker/              # Dockerfile, docker-compose
├── kubernetes/          # K8s manifests
└── monitoring/          # Prometheus, Grafana configs
```

---

## Documentation (`docs/`)

| File | Audience | Content |
|------|----------|---------|
| `vision.md` | Everyone | Where UATP is going |
| `repository-map.md` | Developers | This file |
| `api-documentation.md` | Integrators | API reference |
| `deployment_guide.md` | Operators | Production setup |
| `TRUST_MODEL.md` (root) | Security reviewers | What UATP can/cannot guarantee |
| `THREAT_MODEL.md` (root) | Security reviewers | Attack surface and mitigations |

---

## Archive (`archive/`)

Dormant modules for future phases. Code is preserved but not maintained.

```
archive/
├── src/
│   ├── ai_rights/       # AI rights frameworks (Phase 3)
│   ├── governance/      # Governance systems (Phase 2)
│   ├── economic/        # Attribution economics (Phase 3)
│   └── compliance/      # Regulatory frameworks (Phase 2)
└── README.md            # Why these are archived
```

**Activation criteria:** These modules will be restored when UATP reaches sufficient scale. See [vision.md](vision.md) for phase triggers.

---

## What's NOT in This Repo

| Intentionally Absent | Reason |
|---------------------|--------|
| User data | Capsules are stored wherever you configure |
| Private keys | Generated client-side, never transmitted |
| External TSA credentials | You bring your own DigiCert/other |
| Production secrets | Use environment variables or secret managers |

---

## Key Files for New Contributors

1. **Start here:** `README.md` → `docs/vision.md`
2. **Understand the crypto:** `TRUST_MODEL.md` → `src/crypto/local_signer.py`
3. **See the API:** `docs/api-documentation.md` → `src/api/capsules_fastapi_router.py`
4. **Run tests:** `pytest tests/unit/ -v`
5. **Try the SDK:** `sdk/python/examples/`

---

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| Ed25519 for signatures | NIST-approved, fast, small keys, Daubert-compliant |
| SQLAlchemy async | Support both SQLite (dev) and PostgreSQL (prod) |
| FastAPI | Modern Python async, automatic OpenAPI docs |
| Separate SDK from engine | SDK can work offline, minimal dependencies |
| Archive dormant modules | Focus on Phase 1, preserve future optionality |

---

## Questions?

- Architecture: Open a [Discussion](https://github.com/KayronCalloway/uatp/discussions)
- Bugs: Open an [Issue](https://github.com/KayronCalloway/uatp/issues)
- Security: See [SECURITY.md](../SECURITY.md)
