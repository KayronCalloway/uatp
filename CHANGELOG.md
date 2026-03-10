# Changelog

All notable changes to UATP will be documented in this file.

## [Unreleased]

### Added
- Gold standard zero-trust architecture
- User-sovereign key management (keys never leave device)
- Local signing with UserKeyManager and LocalSigner
- Standalone verification (no UATP trust required)
- RFC 3161 timestamps from external TSA (DigiCert)
- TRUST_MODEL.md documenting cryptographic guarantees

### Security
- Private keys removed from repository
- Deployment secrets removed from repository
- User keys encrypted with PBKDF2 + Fernet

## [7.2.0] - 2026-03-08

### Added
- UATP Capsule Engine v7.2
- Ed25519 + ML-DSA-65 (post-quantum) signatures
- RFC 3161 trusted timestamps
- Capsule verification system
- FastAPI backend
- Next.js frontend
- Claude Code integration hooks
- Plain language summaries

### Security
- Independently verifiable cryptographic proofs
- Tamper-evident capsule chains
- Attribution tracking

---

For detailed changes, see [GitHub commits](https://github.com/KayronCalloway/uatp/commits/main).
