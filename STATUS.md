# UATP Project Status

> This file is the source of truth. It tells you exactly what's ready, what's not, and what's planned.

## Production Ready

| Component | Status | Notes |
|-----------|--------|-------|
| Ed25519 Signatures | **Shipped** | FIPS 186-5 compliant |
| Capsule Creation API | **Shipped** | FastAPI backend |
| Python SDK | **Shipped** | `pip install uatp` (v0.2.1 on PyPI) |
| Local Key Management | **Shipped** | User-sovereign, zero-trust |
| Capsule Verification | **Shipped** | Standalone, no server needed |
| DSSE Bundle Export | **Shipped** | Sigstore-compatible |
| CLI Tools | **Shipped** | `uatp verify`, `uatp export`, `uatp inspect` |
| Full-Text Search | **Shipped** | FTS5 (SQLite) / ts_vector (PostgreSQL) |
| SQLite Storage | **Shipped** | Development/single-node ready |

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

- **Current**: 7.3.0
- **Last Updated**: 2026-03-12
- **Stability**: Beta - Core signing is stable, API may evolve

## Confidence Levels

When we say something is:

- **Shipped**: Production-ready, stable API
- **Beta**: Works in testing, may need configuration or polish
- **Planned**: Design exists, code doesn't

---

*This document is updated with every release. If reality differs from this file, this file is wrong and should be fixed.*
