# Changelog

All notable changes to UATP are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `docs/vision.md` - Accessible vision document covering three horizons
- `docs/repository-map.md` - Full repository structure with audit priorities
- `CHANGELOG.md` - Proper changelog following Keep a Changelog format
- Vision section in README linking to full vision doc

### Changed
- README security claims softened to reflect architectural intent vs guarantees
- README verification diagram updated with "by default" qualifiers
- Linked security claims to TRUST_MODEL.md for verification

### Fixed
- CI pipeline now passes reliably across all matrix combinations
- pytest-asyncio configuration moved to pytest.ini (was being ignored in pyproject.toml)
- Async database URLs corrected (sqlite+aiosqlite://, postgresql+asyncpg://)
- Missing dependencies added to pyproject.toml and requirements.txt

## [7.2.0] - 2026-03-08

### Added
- Claude Code live capture integration with hooks
- RFC 3161 timestamp support (DigiCert TSA integration)
- Post-quantum ML-DSA-65 signatures (experimental, not audited)
- Plain language capsule summaries (AI-generated explanations)
- Next.js frontend dashboard (beta)
- Gold standard zero-trust architecture
- User-sovereign key management (keys never leave device)
- Local signing with UserKeyManager and LocalSigner
- Standalone verification (no UATP server trust required)
- TRUST_MODEL.md documenting cryptographic guarantees
- THREAT_MODEL.md documenting attack surface

### Changed
- Consolidated 26 capsule subclasses into single CapsuleModel
- Archived dormant Phase 2/3 modules to `archive/`

### Fixed
- ORM polymorphism issues causing NULL returns
- Stats count mismatches from NULL IDs in database

### Security
- Private keys removed from repository
- Deployment secrets removed from repository
- User keys encrypted with PBKDF2 + Fernet
- Independently verifiable cryptographic proofs
- Tamper-evident capsule chains

## [7.1.0] - 2026-02-15

### Added
- Capsule chain linking
- Ethics circuit breaker
- Confidence calibration system
- Attribution tracking

### Changed
- Migrated from Flask to FastAPI
- Switched to async SQLAlchemy

## [7.0.0] - 2026-01-20

### Added
- Ed25519 signature support (NIST-approved, Daubert-compliant)
- Python SDK (`pip install uatp`)
- Local key management (zero-trust model)
- Standalone verification (no server required)
- PostgreSQL support
- SQLite support for development

### Changed
- Complete architecture rewrite from v6
- New capsule schema (v7)

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 7.2.0 | 2026-03-08 | Claude Code integration, RFC 3161, post-quantum |
| 7.1.0 | 2026-02-15 | Capsule chains, ethics breaker, FastAPI migration |
| 7.0.0 | 2026-01-20 | Architecture rewrite, Ed25519, Python SDK |

---

[Unreleased]: https://github.com/KayronCalloway/uatp/compare/v7.2.0...HEAD
[7.2.0]: https://github.com/KayronCalloway/uatp/releases/tag/v7.2.0
[7.1.0]: https://github.com/KayronCalloway/uatp/releases/tag/v7.1.0
[7.0.0]: https://github.com/KayronCalloway/uatp/releases/tag/v7.0.0
