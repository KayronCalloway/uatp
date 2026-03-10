# UATP Development Roadmap

## Current Status: Beta

Core cryptographic proof infrastructure is complete. Economic and governance features are experimental/archived. **Status: Beta - suitable for development and testing.**

---

## Phase 1: Core Infrastructure - COMPLETE

**Status:** Complete
**Completion Date:** July 2024

### Shipped
- **Test Suite** - Core tests passing
- **Code Quality Pipeline** - Pre-commit hooks, linting, type checking
- **Application Architecture** - App factory pattern, proper separation
- **CI/CD** - GitHub Actions pipeline
- **Database Foundation** - SQLAlchemy, migrations, health checks

---

## Phase 2: Cryptographic Core - COMPLETE

**Status:** Complete
**Completion Date:** March 2026

### Shipped
- **Ed25519 Signatures** - FIPS 186-5 compliant signing
- **RFC 3161 Timestamps** - External TSA integration (DigiCert)
- **Python SDK** - `pip install uatp`
- **FastAPI Backend** - Capsule creation and verification API
- **Claude Code Integration** - Hook-based capture (beta)
- **Next.js Dashboard** - Capsule viewer (beta)

### Experimental (in `archive/`)
- Economic attribution engine
- Governance/refusal mechanisms
- Advanced analytics dashboards

*Note: Experimental features were archived during codebase cleanup. See `archive/` for code.*

---

## Phase 3: Production & Distribution - PLANNED

**Status:** Planning
**Target:** Q2-Q3 2026

### Goals
1. **PyPI Publication** - `pip install uatp` from PyPI
2. **Hosted API** - Optional managed service
3. **JavaScript SDK** - Browser and Node.js support
4. **Security Audit** - External cryptographic review

---

## Phase 4: Ecosystem - FUTURE

**Status:** Future
**Target:** 2027+

### Vision
- Enterprise integrations
- Compliance certifications
- Multi-language SDKs

---

## Current Project Health

### What's Verified
- Ed25519 signature generation and verification
- Capsule creation and retrieval API
- RFC 3161 timestamp integration
- Database persistence (SQLite/PostgreSQL)
- Python SDK functional

### What Needs Work
- External security audit (not yet performed)
- PyPI publication
- Performance benchmarks
- Expanded test coverage

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
