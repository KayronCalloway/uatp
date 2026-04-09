# UATP Development Roadmap

## Current Status: Beta

**Versions:** SDK 1.1.0 (PyPI) | Capsule Schema 7.2 | See [STATUS.md](STATUS.md)

Core cryptographic proof infrastructure is complete. See [STATUS.md](STATUS.md) for detailed component status.

---

## Phase 1: Core Infrastructure - COMPLETE

**Completion Date:** July 2024

- Test suite foundation
- Code quality pipeline (pre-commit, linting, type checking)
- Application architecture (app factory pattern)
- CI/CD (GitHub Actions)
- Database foundation (SQLAlchemy, migrations)

---

## Phase 2: Cryptographic Core - COMPLETE

**Completion Date:** March 2026

### Shipped
- **Ed25519 Signatures** - FIPS 186-5 compliant signing
- **ML-DSA-65 Signatures** - Post-quantum (FIPS 204), beta
- **RFC 3161 Timestamps** - DigiCert TSA integration, beta
- **Python SDK** - `pip install uatp` (v1.1.0 on PyPI)
- **FastAPI Backend** - Capsule creation, verification, search
- **DSSE Bundle Export** - Sigstore-compatible portable proofs
- **Workflow Attestation** - in-toto style chain-of-custody
- **CLI Tools** - `uatp verify`, `uatp export`, `uatp inspect`
- **Full-Text Search** - FTS5/ts_vector with relevance scoring
- **Capsule Chaining** - Cryptographic prev_hash/content_hash linking
- **Next.js Dashboard** - Capsule viewer (beta)
- **Claude Code Integration** - Hook-based capture (beta)

---

## Phase 3: Production & Distribution - IN PROGRESS

**Target:** Q2-Q3 2026

### Goals
1. **Hosted API** - Optional managed service
2. **JavaScript SDK** - Browser and Node.js support
3. **External Security Audit** - Cryptographic review by third party
4. **Frontend Polish** - Production-ready dashboard

---

## Phase 4: Ecosystem - FUTURE

**Target:** 2027+

### Vision
- Enterprise integrations
- Compliance certifications (SOC 2, etc.)
- Multi-language SDKs
- Attribution and provenance features (see [vision.md](docs/vision.md))

---

## Current Project Health

### What's Verified
- Ed25519 + ML-DSA-65 signature generation and verification
- Capsule creation, retrieval, and search API
- RFC 3161 timestamp integration
- DSSE bundle export and verification
- Database persistence (SQLite/PostgreSQL)
- 1400+ tests passing

### What Needs Work
- External security audit
- Frontend polish
- Performance benchmarks at scale

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute.

---

## Resources

- [SDK Documentation](sdk/python/README.md)
- [Trust Model](TRUST_MODEL.md)
- [Security Policy](SECURITY.md)
- [Status](STATUS.md)

---

*Last Updated: March 2026*
