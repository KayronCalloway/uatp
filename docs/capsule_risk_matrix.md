# Capsule Risk Matrix & Mitigation Overview

*Author: Capsule Engine Core Team*
*Status: Draft v0.1*
*Last-Updated: 2025-07-12*

---

| Capsule | Key Risk | Likelihood | Impact | Mitigation |
|---------|----------|-----------|--------|------------|
| Constellations | Graph bloat leading to degraded query latency | Medium | High | Pruning rules, summarisation nodes, sharding backend |
|  | Consistency divergence in distributed clusters | Low | High | CRDT-inspired merge + periodic reconciliation job |
|  | Neo4j license cost / lock-in | Medium | Medium | Abstraction layer, pluggable back-ends |
| Mirror Mode | Excess compute cost pushes latency > SLO | Medium | High | Configurable sample rate, batching, model compression |
|  | False positives blocking output | Low | High | Threshold tuning, rule testing suite, red-team benchmarking |
|  | Adversarial prompt bypass | Medium | Medium | Token entropy checks, random window inspection |
| Cloning Rights | Licence spoofing or tampering | Low | High | Ed25519 signatures, registry validation |
|  | Unlicensed forks in the wild | High | Medium | Runtime enforcement, refusal capsules, DMCA workflow |
|  | Complicated jurisdiction crossing | Medium | Medium | Jurisdiction field, legal advisory service |
| Evolution Capsules | Snapshot storage growth | High | Medium | Cold archive to glacier, diff-only retention |
|  | Expensive diff on large models | Medium | High | Async worker pool + caching hashes |
|  | Drift score manipulation | Low | Medium | Signed snapshots + diff verification |
| Dividend Bonds | Royalty shortfall vs face value | Medium | High | Over-collateralisation reserve, disclosure docs |
|  | Regulatory non-compliance | Medium | High | KYC/AML module, jurisdiction tags |
|  | Market illiquidity | High | Medium | Internal marketplace + buy-back facility |
| Citizenship Capsules | Identity spoofing via stolen keys | Low | High | Minimum audit trail, multi-sig revocation |
|  | Jurisdiction conflict | Medium | Medium | Declarative jurisdiction + override via governance vote |
|  | Abuse of elevated privileges | Medium | Medium | Mirror Mode monitoring, strike system |

---

## Cross-Capsule Mitigation Themes
* **Cryptographic Assurance** – All capsules signed; verify at ingress.
* **Governance Overrides** – Revocation, suspension, override votes across capsules.
* **Observability** – Emit uniform events to Kafka; aggregate dashboards.
* **Compliance Hooks** – KYC/AML, jurisdiction tags reused by multiple capsules.

---
*End of Matrix*
