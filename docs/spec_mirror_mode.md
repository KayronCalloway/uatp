# Specification: Mirror Mode – Self-Auditing Agents

*Author: Capsule Engine Core Team*
*Status: Draft v0.1*
*Last-Updated: 2025-07-12*

---

## 1. Purpose
Mirror Mode embeds a lightweight **self-auditing co-agent** alongside every primary agent or service request. It continuously mirrors the reasoning chain, policy evaluations, and output deltas to provide **emergent ethical safety** in real time.

Goals:
* Catch policy violations (privacy leak, disallowed content, governance rules) before external emission.
* Produce structured **Refusal Capsules** when violations are detected.
* Generate explainable traces for governance & debugging.

## 2. Scope & Non-Goals
In-scope (MVP):
1. Real-time mirroring of top-k reasoning steps (LLM output and system calls).
2. Policy engine integration (existing `EthicsCircuitBreaker` + new rule packs).
3. Trigger mechanism: mirror agent runs on **risk-weighted** calls or explicit `mirror=True` flag.
4. Performance overhead ≤ 25% of wall-clock latency budget for normal inference.

Out-of-scope (v0):
* Full ML model proof-carrying code (handled later).
* Adaptive risk weighting via RL – placeholder heuristics only.

## 3. Architecture Overview
```
+-------------------+   request   +----------------------+   validate   +-------------------+
|  Client / Caller  | ----------> |  Primary Agent (LLM) | -----------> |  Output Collector |
+-------------------+             +----------+-----------+             +---------+---------+
                                        |                                   |
                                        | mirror data                       | emit if safe
                                        v                                   v
                                 +------+-------+                     +------+------+
                                 |  Mirror Agent | <---rules/policy---| Policy Engine |
                                 +------+-------+                     +-------------+
                                        |
                                        | violations / passes
                                        v
                                 +------+-------+
                                 | Capsule Store |
                                 +--------------+
```

### Components
* **Mirror Agent** – deterministic LLM prompt (smaller model) that replays primary input + incremental output.
* **Policy Engine** – fast rule evaluator (regex, vector sim, structured rule DSL). Reuses `EthicsCircuitBreaker`.
* **Output Collector** – buffers tokens / API calls, allows early termination if violation.
* **Capsule Store** – logs `AuditCapsule` & `RefusalCapsule` with full context.

## 4. Data Flow
1. Primary agent begins streaming output → Output Collector.
2. Collector publishes incremental diff → Mirror Agent.
3. Mirror Agent analyses diff; emits `audit_score`, `violation_list`.
4. Policy Engine validates both audit scores and static rules.
5. If violation: Collector halts output, emits `RefusalCapsule`, returns policy-compliant response.
6. Otherwise: stream continues; at end AuditCapsule stored.

## 5. Interfaces
* gRPC service `MirrorService` with method `AuditStream(stream TokenChunk) returns (AuditVerdict)`.
* Config flags:
  * `MIRROR_MODE_ENABLED` (bool, default true)
  * `MIRROR_MODE_SAMPLE_RATE` (0-1 float)
  * `MIRROR_MODE_THRESHOLD` (score threshold default 0.7)

## 6. Performance Targets
| Metric | Target |
| ------ | ------ |
| Avg latency overhead | ≤ 25% |
| Memory overhead | ≤ 12% |
| False positive rate | < 2% on benchmark suite |
| Detection recall | ≥ 90% for critical policy set |

## 7. Security & Privacy
* Mirror Agent inherits the caller’s scope tokens; no elevation of privileges.
* Audit/Refusal capsules encrypted with system KMS.
* Differential privacy noise added to token logs for PII mitigation.

## 8. Risks & Mitigations
| Risk | Mitigation |
| ---- | ---------- |
| Excess compute cost | Configurable sample rate; opportunistic batching |
| Adversarial token manipulation to bypass mirror | Token-level entropy checks, randomised window sizes |
| Policy drift | Evolution Capsules track rule changes; regular red-team audits |

## 9. Milestones
1. **Design sign-off** (Wk 1)
2. **Policy Engine adapter + rule DSL** (Wk 2)
3. **gRPC service + Collector integration** (Wk 3)
4. **Benchmark & red-team tests** (Wk 4)
5. **MVP release** (end of Foundation phase)

---
*End of Spec*
