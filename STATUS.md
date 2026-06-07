# UATP Project Status

> Source of truth. What's ready, what's not, what's planned.

## Core Protocol (Stable Local/Dev)

| Component | Status | Notes |
|-----------|--------|-------|
| Ed25519 Signatures | **Stable local/dev** | FIPS 186-5 algorithm, not FIPS-certified |
| Python SDK | **Stable local/dev** | Source version 1.1.0; PyPI currently publishes 0.2.1 |
| Local Key Management | **Stable local/dev** | Keys never leave the device |
| Capsule Verification | **Stable local/dev** | Standalone legacy capsule verification; agent receipt bundle verification is beta and offline-capable |
| DSSE Bundle Export | **Stable local/dev** | Sigstore-compatible |
| Signal Detection | **Stable local/dev** | 7 signal types, calibrated against local outcomes |
| Confidence Calibration | **Stable local/dev** | Autoresearch via Gemma, MAE 0.176 |

## Capture Pipeline (Stable Local/Dev)

| Component | Status | Notes |
|-----------|--------|-------|
| Claude Code capture | **Stable local/dev** | Thinking, tool calls, usage, full transcripts |
| Hermes Agent capture | **Stable local/dev** | Plugin, fires on session end (CLI + gateway); not externally audited |
| Agent receipt bundles | **Beta** | Signed receipt chains, CLI verifier, and deterministic tamper fixtures exist; not externally audited |
| Ollama proxy capture | **Stable local/dev** | Standalone, zero UATP deps |
| DPO pair extraction | **Stable local/dev** | Held-out correction-chain evals, non-mutating learning reports |
| Cross-model comparison | **Stable local/dev** | Queries across all capture sources |
| Capsule rescore | **Stable local/dev** | Re-runs detector on existing capsules |

## Backend (Beta)

| Component | Status | Notes |
|-----------|--------|-------|
| Capsule Creation API | **Beta** | FastAPI |
| Full-Text Search | **Beta** | FTS5 (SQLite) / ts_vector (PostgreSQL) |
| SQLite Storage | **Beta** | Development/single-node |
| PostgreSQL Storage | **Beta** | Works, needs production hardening |
| Next.js Frontend | **Beta** | Dashboard functional, needs polish |
| CLI Tools | **Beta** | `uatp verify`, `uatp export`, `uatp inspect` |
| TypeScript SDK | **Beta** | Source version 1.1.0; npm currently publishes 1.0.1 |
| ML-DSA-65 Post-Quantum | **Beta** | FIPS 204 algorithm, not audited |
| RFC 3161 Timestamps | **Beta** | Timestamp evidence is fail-closed; no trusted-time claim without verifiable TSA trust-anchor validation |
| MCP Certifying Gateway | **Alpha** | Stdio/single-server certifying proxy; exported receipt bundles verify offline; needs concurrency, multi-server, remote anchoring, and trust-policy demo hardening |

## Planned

| Component | Target | Notes |
|-----------|--------|-------|
| External Security Audit | Q2 2026 | Seeking auditors |
| Verifier hardening | Q2 2026 | Trusted signer policy CLI, TSA trust-anchor validation, and MCP trust-policy demo polish |
| Hosted SaaS | Q3 2026 | Architecture designed |
| Registry release sync | Q2 2026 | Publish source 1.1.0 to PyPI/npm or mark registry packages historical |

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

## Versions

Source tree: **1.1.0**
GitHub latest release: **v1.1.0**

| Artifact | Version |
|----------|---------|
| Python SDK source | 1.1.0 |
| Python SDK on PyPI | 0.2.1 |
| TypeScript SDK source | 1.1.0 |
| TypeScript SDK on npm | 1.0.1 |
| Backend Engine | 1.1.0 |
| Capsule Schema | 7.2 legacy capsules; 7.4 agent execution traces |

Last Updated: 2026-05-21

## What These Labels Mean

- **Stable local/dev**: Functions correctly in local/dev workflows, API intended to hold steady, not externally audited
- **Alpha**: Working integration, but missing production hardening or scale properties
- **Beta**: Works but may need configuration or has known limitations
- **Experimental**: Code exists, not maintained to protocol standards
- **Planned**: Design exists, code doesn't

---

*If reality differs from this file, this file is wrong and should be fixed.*
