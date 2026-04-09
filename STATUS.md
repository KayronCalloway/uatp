# UATP Project Status

> Source of truth. What's ready, what's not, what's planned.

## Core Protocol (Stable)

| Component | Status | Notes |
|-----------|--------|-------|
| Ed25519 Signatures | **Stable** | FIPS 186-5 algorithm, not FIPS-certified |
| Python SDK | **Stable** | `pip install uatp` v1.1.0 |
| Local Key Management | **Stable** | Keys never leave the device |
| Capsule Verification | **Stable** | Standalone, no server needed |
| DSSE Bundle Export | **Stable** | Sigstore-compatible |
| Signal Detection | **Stable** | 7 signal types, calibrated against 1042 outcomes |
| Confidence Calibration | **Stable** | Autoresearch via Gemma, MAE 0.176 |

## Capture Pipeline (Stable)

| Component | Status | Notes |
|-----------|--------|-------|
| Claude Code capture | **Stable** | Thinking, tool calls, usage, full transcripts |
| Hermes Agent capture | **Stable** | Plugin, fires on session end (CLI + gateway) |
| Ollama proxy capture | **Stable** | Standalone, zero UATP deps |
| DPO pair extraction | **Stable** | 1987 pairs (720 correction chains) |
| Cross-model comparison | **Stable** | Queries across all capture sources |
| Capsule rescore | **Stable** | Re-runs detector on existing capsules |

## Backend (Beta)

| Component | Status | Notes |
|-----------|--------|-------|
| Capsule Creation API | **Beta** | FastAPI |
| Full-Text Search | **Beta** | FTS5 (SQLite) / ts_vector (PostgreSQL) |
| SQLite Storage | **Beta** | Development/single-node |
| PostgreSQL Storage | **Beta** | Works, needs production hardening |
| Next.js Frontend | **Beta** | Dashboard functional, needs polish |
| CLI Tools | **Beta** | `uatp verify`, `uatp export`, `uatp inspect` |
| TypeScript SDK | **Beta** | `npm install @coolwithakay/uatp` |
| ML-DSA-65 Post-Quantum | **Beta** | FIPS 204 algorithm, not audited |
| RFC 3161 Timestamps | **Beta** | DigiCert TSA, local fallback |

## Planned

| Component | Target | Notes |
|-----------|--------|-------|
| External Security Audit | Q2 2026 | Seeking auditors |
| Hosted SaaS | Q3 2026 | Architecture designed |
| PyPI publish v1.1.0 | Q2 2026 | Currently 0.2.1 on PyPI |

## Experimental (Not Core)

Modules in `src/` that explore future directions. Not maintained to protocol standards:
- `src/attribution/` — Attribution tracking
- `src/consensus/` — Governance mechanisms
- `src/economic/` — Economic models
- `src/ethics/` — Ethics circuit breakers
- `src/privacy/` — Privacy primitives

In production (`ENVIRONMENT=production`), only core routes are exposed.

## Not Audited

- Cryptographic implementation (internal review only)
- Key derivation parameters (follows OWASP guidelines)
- Post-quantum signatures (FIPS 204 algorithm, not audited)

We welcome security review. See [SECURITY.md](SECURITY.md).

## Version

All components: **v1.1.0**

| Artifact | Version |
|----------|---------|
| Python SDK | 1.1.0 |
| TypeScript SDK | 1.1.0 |
| Backend Engine | 1.1.0 |
| Capsule Schema | 7.2 |

Last Updated: 2026-04-08

## What These Labels Mean

- **Stable**: Functions correctly, API won't break, not externally audited
- **Beta**: Works but may need configuration or has known limitations
- **Experimental**: Code exists, not maintained to protocol standards
- **Planned**: Design exists, code doesn't

---

*If reality differs from this file, this file is wrong and should be fixed.*
