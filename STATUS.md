# UATP Project Status

> This file is the source of truth. It tells you exactly what's ready, what's not, and what's planned.

## Honesty Note

This repo contains two things:
1. **Core trust protocol** (SDK, signing, verification) — the focus of this project
2. **Experimental platform code** (attribution, governance, economics) — not part of the core protocol

The "Shipped" items below refer to the **core protocol only**. The platform modules exist in `src/` but are experimental and not maintained to the same standard.

## Working (SDK Path)

| Component | Status | Notes |
|-----------|--------|-------|
| Ed25519 Signatures | **Working** | FIPS 186-5 compliant, not externally audited |
| Python SDK | **Working** | `pip install uatp` (v0.3.0) |
| Local Key Management | **Working** | UserKeyManager, LocalSigner |
| Capsule Verification | **Working** | Standalone, no server needed |
| DSSE Bundle Export | **Working** | Sigstore-compatible |

## Working (Backend Path)

| Component | Status | Notes |
|-----------|--------|-------|
| Capsule Creation API | **Working** | FastAPI backend |
| Full-Text Search | **Working** | FTS5 (SQLite) / ts_vector (PostgreSQL) |
| SQLite Storage | **Working** | Development/single-node |
| CLI Tools | **Working** | `uatp verify`, `uatp export`, `uatp inspect` |

## Beta

| Component | Status | Notes |
|-----------|--------|-------|
| RFC 3161 Timestamps | **Beta** | DigiCert TSA integration working, requires config |
| ML-DSA-65 (Post-Quantum) | **Beta** | FIPS 204 compliant, not externally audited |
| Capsule Chaining | **Beta** | Cryptographic linking works, prev_hash/content_hash |
| Workflow Attestation | **Beta** | in-toto style chain-of-custody |
| PostgreSQL Storage | **Beta** | Works, needs production hardening |
| Next.js Frontend | **Beta** | Dashboard functional, needs polish |
| Claude Code Integration | **Beta** | Hook-based capture functional |

## Planned (Not Yet Built)

| Component | Target | Notes |
|-----------|--------|-------|
| JavaScript/TypeScript SDK | Q2 2026 | Design complete |
| Hosted SaaS | Q3 2026 | Architecture designed |
| External Security Audit | Q2 2026 | Seeking auditors |

## Not Part of Core Protocol

The following modules exist in `src/` but are **experimental platform code**, not the core trust protocol:

- `src/attribution/` - Attribution tracking (placeholder)
- `src/consensus/` - Governance mechanisms (experimental)
- `src/economic/` - Economic engines (experimental)
- `src/ethics/` - Ethics circuit breakers (experimental)
- `src/privacy/` - Privacy primitives (experimental)

These modules are not maintained to the same standard as the SDK and core signing code. They exist as explorations of where the protocol could go, not claims about what it does today.

## Not for Production Use

- **Demo scripts** (`scripts/demo/`) - For demonstration only
- **Test databases** (`*.db` files) - Not persistent storage
- **Archive folder** (`archive/`) - Historical artifacts, not maintained

## Not Independently Audited

The following have not been reviewed by external security firms:

- Cryptographic implementation (internal review only)
- Key derivation parameters (follows OWASP guidelines)
- Post-quantum signatures (FIPS 204 compliant, not audited)

We welcome security review. See [SECURITY.md](SECURITY.md) for responsible disclosure.

## Version

| Artifact | Version | Notes |
|----------|---------|-------|
| **SDK (PyPI)** | 0.3.0 | `pip install uatp` |
| **Backend** | 0.3.0 | pyproject.toml |
| **Capsule Schema** | 7.2 | Internal capsule format |

- **Last Updated**: 2026-03-13
- **Stability**: Beta - Core signing is stable, API may evolve

## Confidence Levels

When we say something is:

- **Working**: Functions correctly in testing, API is stable, not externally audited
- **Beta**: Works but may need configuration, polish, or has known limitations
- **Experimental**: Code exists but is not maintained to protocol standards
- **Planned**: Design exists, code doesn't

**What "Working" does NOT mean:**
- Externally audited
- Battle-tested in adversarial production environments
- Guaranteed to be free of security vulnerabilities

We are seeking external security auditors. See [SECURITY.md](SECURITY.md).

---

*This document is updated with every release. If reality differs from this file, this file is wrong and should be fixed.*
