# UATP Project Status

> This file is the truth serum. It tells you exactly what's ready, what's not, and what's planned.

## Production Ready

| Component | Status | Notes |
|-----------|--------|-------|
| Ed25519 Signatures | **Shipped** | Standard Ed25519 implementation |
| Capsule Creation API | **Shipped** | FastAPI backend, fully functional |
| Python SDK | **Shipped** | `pip install uatp` (v0.2.1 on PyPI) |
| Local Key Management | **Shipped** | User-sovereign, zero-trust |
| Capsule Verification | **Shipped** | Standalone verification possible |
| SQLite Storage | **Shipped** | Development/single-node ready |

## Beta

| Component | Status | Notes |
|-----------|--------|-------|
| PostgreSQL Storage | **Beta** | Works, needs production hardening |
| RFC 3161 Timestamps | **Beta** | DigiCert integration working |
| Claude Code Integration | **Beta** | Hook-based capture functional |
| Next.js Frontend | **Beta** | Dashboard viewable, needs polish |
| Plain Language Summaries | **Beta** | AI-generated explanations |

## Experimental

| Component | Status | Notes |
|-----------|--------|-------|
| ML-DSA-65 (Post-Quantum) | **Experimental** | Implemented, not audited |
| Capsule Chains | **Experimental** | Linking works, UX incomplete |

## Planned (Not Yet Built)

| Component | Target | Notes |
|-----------|--------|-------|
| JavaScript/TypeScript SDK | Q2 2026 | Design complete |
| Hosted SaaS | Q3 2026 | Architecture designed |
| Data Marketplace | Q4 2026 | Specification complete |
| API Key Authentication | Q2 2026 | Design complete |

## Not for Production Use

- **Demo scripts** (`scripts/demo/`) - For demonstration only
- **Test databases** (`*.db` files) - Not persistent storage
- **Archive folder** - Historical artifacts, not current truth

## Not Independently Validated

The following have not been audited by external security firms:

- Cryptographic implementation (internal review only)
- Key derivation parameters (follows OWASP guidelines)
- Post-quantum signatures (experimental)

We welcome security review. See [SECURITY.md](SECURITY.md) for responsible disclosure.

## Version

- **Current**: 7.2.0 (Beta)
- **Last Updated**: 2026-03-08
- **Stability**: Beta - API may change

## Confidence Levels

When we say something is:

- **Shipped**: We'd bet the company on it working
- **Beta**: Works in testing, needs real-world validation
- **Experimental**: Proof of concept, expect breaking changes
- **Planned**: Design exists, code doesn't

---

*This document is updated with every release. If reality differs from this file, this file is wrong and should be fixed.*
