# Capsule Feature Roll-out Sequence & Milestones

*Author: Capsule Engine Core Team*
*Status: Draft v0.1*
*Last-Updated: 2025-07-12*

---

## Overview
Implementation is sequenced to minimise dependency risk and align with Phase-2 timeline. Each capsule delivers testable increments that unlock the next set.

| Order | Capsule(s) | Phase | Week Window | Key Deliverables |
|-------|------------|-------|-------------|------------------|
| 1 | Constellations, Mirror Mode | Foundation | Wk 1-4 | Graph store + query API; Mirror Agent runtime; >80% test coverage |
| 2 | Cloning Rights, Evolution Capsules | Foundation / Edge | Wk 3-4 overlap | License capsule schema + registry hooks; Snapshot service + diff lib|
| 3 | Dividend Bonds | Economic Attribution | Wk 9-12 | Bond Issuer service; Dividend router; compliance checks |
| 4 | Citizenship Capsules | Governance | Wk 13-16 | Citizenship Registry; runtime middleware; revocation flow |

## Detailed Milestones
### Constellations
1. Wk 1: In-memory DAG + API stub
2. Wk 2: Neo4j backend adapter + integration tests
3. Wk 3: Pruning logic + performance benchmark (<200 ms p50 query)
4. Wk 4: Security hardening & docs

### Mirror Mode
1. Wk 1: Mirror Agent skeleton + sampling config
2. Wk 2: Policy engine integration + refusal capsule path
3. Wk 3: Load test & cost optimisation (<5% latency hit p95)
4. Wk 4: Red-team evaluation & threshold tuning

### Cloning Rights
1. Wk 3: `ModelLicenseCapsule` class + OpenAPI schema
2. Wk 3: LLM Registry upload validator
3. Wk 4: Runtime licence check in CapsuleEngine
4. Wk 4: End-to-end royalty split smoke test

### Evolution Capsules
1. Wk 3: Snapshot store + scheduler CRON
2. Wk 4: Diff algorithms (JSON, weights, policy)
3. Wk 4: REST `/evolution/*` endpoints
4. Wk 4: Drift metrics dashboard plug-in

### Dividend Bonds
1. Wk 9: Bond schema + issuer micro-service
2. Wk 10: Dividend Engine routing update
3. Wk 11: Compliance module hookup
4. Wk 12: Marketplace PoC & documentation

### Citizenship Capsules
1. Wk 13: Schema + registry DB tables
2. Wk 14: Eligibility validator CLI + tests
3. Wk 15: Runtime middleware enforcement
4. Wk 16: Governance vote smart-contract integration stub

---
*End of Sequence*
