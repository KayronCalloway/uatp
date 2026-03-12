# Repository Map

## Overview

UATP is organized into four layers: core cryptography, API server, client SDK, and infrastructure.

```
uatp/
├── src/                 # Core engine (Python)
├── sdk/python/          # Published SDK (pip install uatp)
├── frontend/            # Next.js dashboard (beta)
├── infra/               # Docker, Kubernetes configs
├── tests/               # 1400+ tests
└── archive/             # Dormant modules (future phases)
```

---

## Source Code (`src/`)

### Audit Priority 1: Cryptography

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `src/crypto/` | Key generation, local signing | `local_signer.py`, `secure_key_manager.py` |
| `src/security/` | Signatures, timestamps, Merkle logs | `uatp_crypto_v7.py`, `rfc3161_timestamps.py`, `merkle_audit_log.py` |

**Security property:** Private keys never leave `src/crypto/`. Signing happens locally.

### Audit Priority 2: API & Verification

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `src/api/` | FastAPI routes | `capsules_fastapi_router.py`, `chain_fastapi_router.py` |
| `src/export/` | DSSE bundle export | `dsse_exporter.py` |
| `src/attestation/` | Workflow attestation | `policy.py` |
| `src/cli/` | CLI tools | `verify.py`, `export.py`, `inspect.py` |

### Audit Priority 3: Services & Storage

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `src/services/` | Search, lifecycle | `capsule_search_service.py`, `capsule_lifecycle_service.py` |
| `src/models/` | Database models | `capsule.py` |
| `src/database/` | DB connections | `connection.py` |

### Supporting (Lower Priority)

| Directory | Purpose |
|-----------|---------|
| `src/live_capture/` | Claude Code integration |
| `src/auth/` | JWT authentication |
| `src/middleware/` | Rate limiting, security headers |

---

## SDK (`sdk/python/`)

The published `pip install uatp` package.

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

**Security property:** The SDK can verify capsules without any network connection.

---

## Frontend (`frontend/`)

Next.js dashboard for viewing capsules. Beta.

```
frontend/
├── src/
│   ├── app/             # Next.js pages
│   ├── components/      # React components
│   └── lib/             # API client
└── public/              # Static assets
```

**Note:** The frontend is optional. All functionality is available via API.

---

## Tests (`tests/`)

| Directory | Purpose |
|-----------|---------|
| `tests/unit/` | Isolated function tests |
| `tests/integration/` | Database + API tests |
| `tests/security/` | Crypto edge cases |

Run: `pytest tests/ --ignore=tests/legacy`

---

## Infrastructure (`infra/`)

Docker and Kubernetes configs. Not required for local development.

---

## Archive (`archive/`)

Dormant modules preserved for future phases. Not maintained.

```
archive/src/
├── ai_rights/       # AI rights frameworks
├── governance/      # Governance systems
├── economic/        # Attribution economics
└── compliance/      # Regulatory frameworks
```

See [vision.md](vision.md) for when these may be activated.

---

## What's NOT in This Repo

| Absent | Reason |
|--------|--------|
| User data | Stored wherever you configure |
| Private keys | Generated client-side, never transmitted |
| TSA credentials | You bring your own |
| Production secrets | Use environment variables |

---

## Key Files for Contributors

1. `README.md` → `TRUST_MODEL.md` → `src/crypto/local_signer.py`
2. `docs/api-documentation.md` → `src/api/capsules_fastapi_router.py`
3. `sdk/python/examples/`

---

## Questions?

- [Discussions](https://github.com/KayronCalloway/uatp/discussions)
- [Issues](https://github.com/KayronCalloway/uatp/issues)
- [SECURITY.md](../SECURITY.md)
