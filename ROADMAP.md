# Roadmap

**Current source:** 1.1.0 | Capsule Schema 7.2 + 7.4 agent execution traces | See [STATUS.md](STATUS.md) for component-level detail.

---

## Shipped

**Cryptographic Core (March 2026)**
- Ed25519 signatures (FIPS 186-5)
- ML-DSA-65 post-quantum signatures (FIPS 204, beta)
- RFC 3161 timestamps (DigiCert TSA, beta)
- Python SDK (`pip install uatp`)
- FastAPI backend (capsule CRUD, verification, search)
- DSSE bundle export (Sigstore-compatible)
- Full-text search (FTS5/ts_vector)
- Capsule chaining (prev_hash/content_hash linking)

**Capture Pipeline (March 2026)**
- Claude Code hook capture
- Hermes Agent plugin
- Ollama/Gemma transparent proxy
- Signal detection (7 types, calibrated)
- DPO pair extraction
- Cross-model comparison

**Agent Receipt Verification (Local/Dev, June 2026)**
- Offline agent receipt bundle verifier for signed agent action receipts
- Deterministic tamper-failure fixtures for event, chain, signature, and artifact edits
- MCP gateway session export to detached receipt bundles that verify outside the gateway/runtime

---

## In Progress (Q2-Q3 2026)

- **Verifier policy hardening** — Trusted signer policy, trusted timestamp requirement, and explicit TSA certificate loading are exposed through the CLI
- **TSA trust-anchor validation** — Agent receipt and standalone capsule verifiers validate RFC 3161 tokens against explicit TSA trust anchors via OpenSSL; missing anchors/tooling remain fail-closed
- **MCP certifying gateway hardening** — Use MCP as the first external boundary after verifier UX and trust-policy demo polish are complete
- **External security audit** — Cryptographic review by third party
- **Frontend polish** — Production-ready dashboard
- **TypeScript SDK stabilization** — Browser and Node.js support
- **Registry release sync** — Publish source 1.1.0 to PyPI/npm or label older packages as historical
- **Hosted API** — Optional managed service

---

## Future (2027+)

- Enterprise integrations and compliance certifications
- Multi-language SDKs
- Attribution and provenance features (see [vision.md](docs/vision.md))

---

*Last updated: May 2026*
