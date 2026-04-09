# UATP

**Signed reasoning traces for AI systems. Capture decisions, detect failures, generate training data.**

[![CI](https://github.com/KayronCalloway/uatp/actions/workflows/ci.yml/badge.svg)](https://github.com/KayronCalloway/uatp/actions/workflows/ci.yml)
[![Security](https://github.com/KayronCalloway/uatp/actions/workflows/security.yml/badge.svg)](https://github.com/KayronCalloway/uatp/actions/workflows/security.yml)
[![PyPI](https://img.shields.io/pypi/v/uatp)](https://pypi.org/project/uatp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What UATP Does

UATP captures what AI systems do, signs it cryptographically, and turns it into training signal.

```
Your AI tool  →  UATP captures interaction  →  Ed25519 signs it  →  Capsule stored
                                                                         │
     ┌───────────────────────────────────────────────────────────────────┘
     │
     ▼
Signal detector finds corrections/acceptances  →  DPO training pairs extracted
                                                         │
                                                         ▼
                                          Autoresearch calibrates confidence
                                          against actual outcomes (Gemma, $0)
```

A **capsule** is a signed record of an AI interaction containing:
- The conversation (user messages, assistant responses, tool calls)
- Extended thinking (chain-of-thought, when available)
- Implicit feedback signals (corrections, acceptances, abandonments)
- Economics (tokens, cache hit rates, cost)
- Cryptographic signature (Ed25519, optionally ML-DSA-65 post-quantum)

The signature proves the capsule hasn't been tampered with. The signals tell you whether the AI succeeded or failed. The thinking shows you why.

## Quick Start

```bash
pip install uatp
```

```python
from uatp import create_capsule, sign_capsule, verify_capsule

# Create
capsule = create_capsule(
    prompt="Deploy the service to production",
    response="Deployed via kubectl apply...",
    model="claude-opus-4",
)

# Sign locally (private key never leaves your machine)
signed = sign_capsule(capsule, passphrase="your-passphrase")

# Verify independently (no server needed)
assert verify_capsule(signed)
```

## Capture Sources

UATP captures from multiple AI platforms into the same capsule format:

| Source | How | What's Captured |
|--------|-----|-----------------|
| **Claude Code** | Hook in `.claude/hooks/` | Thinking blocks, tool calls, usage, full transcript |
| **Hermes Agent** | Plugin (`on_session_end`) | Reasoning, tool graphs, economics, session lineage |
| **Ollama/Gemma** | Transparent proxy (`:11435→:11434`) | Prompt/response, `<think>` tags, eval metrics |
| **Any OpenAI-compatible** | BaseHook subclass | Configurable per platform |

### Standalone Ollama Proxy (zero dependencies on UATP)

```bash
cd scripts/proxy
pip install -r requirements.txt
python3 proxy.py
# Now: export OLLAMA_HOST=http://localhost:11435
# Every Ollama interaction is captured and signed automatically
```

## Analysis Tools

Once capsules exist, extract intelligence from them:

```bash
# Cross-model comparison (which model gets corrected less?)
python3 scripts/analysis/cross_model_report.py

# Extract DPO training pairs (720 correction chains + 1267 labeled)
python3 scripts/analysis/extract_dpo_pairs.py

# Tool call sequence analysis (which patterns lead to success?)
python3 scripts/analysis/tool_patterns.py

# Backfill old capsules with thinking/tools/economics from transcripts
python3 scripts/capture/rich_hook_capture.py --backfill <transcript.jsonl>

# Re-score all capsules with improved signal detector
python3 scripts/analysis/rescore_capsules.py
```

### Confidence Calibration (Autoresearch)

The confidence scores on capsules are calibrated against real outcomes,
not hardcoded guesses. A local Gemma model tunes the weights:

```bash
# Iterates: Gemma proposes weight changes → eval against DPO pairs → keep if better
python3 scripts/autoresearch/calibrate_confidence.py --iterations 30
# Baseline MAE 0.567 → 0.176 (69% reduction, $0 compute cost)
```

## Signal Detection

Every user message is analyzed for implicit feedback:

| Signal | Meaning | Example |
|--------|---------|---------|
| `correction` | Previous response was wrong | "no, I asked about X" |
| `acceptance` | Response was useful | "yes", "perfect", "do it" |
| `refinement` | Response was good, wants more | "can you also..." |
| `soft_rejection` | User ignored the response entirely | Topic change, no acknowledgment |
| `abandonment` | User gave up | "never mind", "I'll do it myself" |
| `requery` | Same question repeated | High similarity to previous message |

These signals become the reward signal for DPO training and the ground truth for confidence calibration.

## Trust Model

UATP is zero-trust by design:

- **Private keys never leave your device.** Signing happens locally.
- **Only hashes go to the timestamp server.** Content stays with you.
- **Verification is independent.** Anyone with the public key can verify, no UATP server needed.
- **Sealed capsules are immutable.** Modifying one invalidates the signature.

See [TRUST_MODEL.md](TRUST_MODEL.md) for the full security model, including what UATP explicitly cannot do.

## Architecture

```
uatp-capsule-engine/
├── src/
│   ├── security/          # Ed25519 + ML-DSA-65 signing, RFC 3161 timestamps
│   ├── live_capture/      # Signal detection, rich capture, conversation monitoring
│   ├── analysis/          # Confidence explainer, uncertainty quantification
│   ├── api/               # FastAPI capsule endpoints
│   ├── models/            # Capsule ORM (SQLAlchemy)
│   └── core/              # Config, database, provenance layers
├── scripts/
│   ├── analysis/          # Cross-model reports, DPO extraction, tool patterns
│   ├── autoresearch/      # Gemma-powered confidence calibration
│   ├── capture/           # Claude Code hook capture + backfill
│   └── proxy/             # Standalone Ollama capture proxy
├── sdk/
│   ├── python/            # pip install uatp
│   └── typescript/        # npm install @coolwithakay/uatp
├── frontend/              # Next.js capsule dashboard
├── tests/                 # 1400+ tests
└── docs/                  # Trust model, threat model, capsule type specs
```

## What's Working

| Component | Status | Notes |
|-----------|--------|-------|
| Ed25519 signing + verification | ✅ Stable | Core protocol, local-only |
| Python SDK | ✅ Stable | `pip install uatp` |
| Signal detection (7 types) | ✅ Stable | Calibrated against 1042 DPO pairs |
| Capsule capture (Claude Code) | ✅ Stable | Thinking, tools, economics |
| Capsule capture (Hermes) | ✅ Stable | Plugin, auto-fires on session end |
| Capsule capture (Ollama proxy) | ✅ Stable | Standalone, zero UATP deps |
| DPO pair extraction | ✅ Stable | 1987 pairs from 79 capsules |
| Confidence calibration | ✅ Stable | Autoresearch via Gemma |
| Cross-model comparison | ✅ Stable | Query across all capture sources |
| ML-DSA-65 post-quantum | 🔶 Beta | Ed25519 + ML-DSA-65 dual signing |
| RFC 3161 timestamps | 🔶 Beta | DigiCert TSA, local fallback |
| Next.js dashboard | 🔶 Beta | Browse, verify, search capsules |
| TypeScript SDK | 🔶 Beta | `npm install @coolwithakay/uatp` |
| FastAPI backend | 🔶 Beta | REST API for capsule CRUD |

## Version

All components are at **v1.1.0**. See [STATUS.md](STATUS.md) for detailed component status and [ROADMAP.md](ROADMAP.md) for what's next.

## Packages

| Package | Version | Install |
|---------|---------|---------|
| Python SDK | 1.1.0 | `pip install uatp` |
| TypeScript SDK | 1.1.0 | `npm install @coolwithakay/uatp` |
| Engine | 1.1.0 | Clone this repo |

## How UATP Compares

| | UATP | MLflow | W&B | Sigstore |
|--|------|--------|-----|----------|
| Local signing | ✅ Ed25519 | ❌ | ❌ | ✅ |
| Reasoning traces | ✅ Full chain-of-thought | ❌ | ❌ | ❌ |
| Implicit feedback | ✅ 7 signal types | ❌ | ❌ | ❌ |
| DPO training data | ✅ Correction chains | ❌ | ❌ | ❌ |
| Post-quantum | ✅ ML-DSA-65 | ❌ | ❌ | ❌ |
| Independent verify | ✅ | ❌ | ❌ | ✅ |
| AI-specific | ✅ | Partial | Partial | ❌ |

## License

MIT. See [LICENSE](LICENSE).
