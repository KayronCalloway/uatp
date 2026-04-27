# UATP Capsule Engine

**Signed reasoning traces for AI systems. Capture decisions, detect failures, generate training data.**

[![CI](https://github.com/KayronCalloway/uatp/actions/workflows/ci.yml/badge.svg)](https://github.com/KayronCalloway/uatp/actions/workflows/ci.yml)
[![Security](https://github.com/KayronCalloway/uatp/actions/workflows/security.yml/badge.svg)](https://github.com/KayronCalloway/uatp/actions/workflows/security.yml)
[![PyPI](https://img.shields.io/pypi/v/uatp)](https://pypi.org/project/uatp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## The Stakes

A handful of companies built the most powerful systems in history by treating human expression as free raw material. Every post, every debugged line, every image shared, every late-night answer — scraped, ingested, and monetized without consent, without compensation, and without a mechanism to opt out.

At the same time, AI is entering high-stakes domains where opacity is unacceptable. When a robotaxi crashes, when a doctor's AI recommends the wrong medication, when a bank algorithm denies a mortgage, there is no record of what was decided, with what reasoning, at what moment. Liability is unprovable. Trust collapses.

Both failures trace to the same absence: memory — verifiable memory, owned by the people who created it.

**[Read the full vision →](docs/vision.md)**

---

## What It Does

UATP captures what AI systems do, signs it cryptographically, and turns it into training signal.

A **capsule** is a signed record of an AI interaction containing:
- The conversation (user messages, assistant responses, tool calls)
- Extended thinking (chain-of-thought, when available)
- Implicit feedback signals (corrections, acceptances, abandonments)
- Economics (tokens, cache hit rates, cost)
- Cryptographic signature (Ed25519, optionally ML-DSA-65 post-quantum)

The signature proves the capsule has not been tampered with. The signals reveal whether the AI succeeded or failed, and the thinking shows why.

---

## Quick Start

```bash
git clone https://github.com/KayronCalloway/uatp.git
cd uatp
pip install -e ".[dev]"
cp .env.example .env
# Edit .env: ENVIRONMENT=development, DEV_DB_URL=sqlite:///./uatp_dev.db
python -m uvicorn src.main:app --host 0.0.0.0 --port 9000 --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. Development mode uses auto-login and SQLite — no external database required.

---

## Architecture

UATP is a full-stack web platform.

```
Next.js Frontend (localhost:3000)  ↔  FastAPI Backend (localhost:9000)  ↔  SQLite (dev) / PostgreSQL (prod)
```

**Capture sources:**
- **Claude Code** — Hook in `.claude/hooks/`, captures thinking blocks and tool calls
- **Hermes Agent** — Plugin (`on_session_end`), captures reasoning and economics
- **Ollama/Gemma** — Transparent proxy (`:11435→:11434`), captures `<think>` tags
- **MCP Gateway** — Certifying proxy that signs every tool call at the boundary

---

## MCP Certifying Gateway

The gateway intercepts every MCP tool call, applies policy checks, signs the parameters, and forwards or blocks. Every call produces a lineage graph: **DECISION_POINT** → **TOOL_CALL/REFUSAL** → **proof block**.

Evidence classes separate fact from inference: `observed` (proxy-verified), `asserted` (model claim), `derived` (computed), `policy` (governance decision).

```bash
python -m src.integrations.mcp.gateway --upstream-cmd "python -m src.integrations.mcp.demo_server"
```

Browse audits at `/system` or query via CLI: `python -m src.integrations.mcp.graph_viewer --latest`

**Status:** Alpha. Core protocol compliance and security hardening are complete. Concurrency, multi-server, and remote anchoring are next.

---

## SDK

**Python**
```bash
pip install uatp
```
```python
from uatp import create_capsule, sign_capsule, verify_capsule

capsule = create_capsule(prompt="Deploy the service", response="Deployed via kubectl...", model="claude-opus-4")
signed = sign_capsule(capsule, passphrase="your-passphrase")
assert verify_capsule(signed)
```

**TypeScript**
```bash
npm install @coolwithakay/uatp
```

---

## Analysis Tools

```bash
# Cross-model comparison
python3 scripts/analysis/cross_model_report.py

# Extract DPO training pairs
python3 scripts/analysis/extract_dpo_pairs.py

# Confidence calibration (Gemma, local, $0)
python3 scripts/autoresearch/calibrate_confidence.py --iterations 30
```

---

## Trust Model

UATP is zero-trust by design:
- **Private keys never leave your device.** Signing happens locally.
- **Only hashes go to the timestamp server.** Content stays with you.
- **Verification is independent.** Anyone with the public key can verify, no UATP server needed.
- **Sealed capsules are immutable.** Modifying one invalidates the signature.

See [TRUST_MODEL.md](TRUST_MODEL.md) for the full security model.

---

## Project Structure

```
src/
  security/          # Ed25519 + ML-DSA-65 signing, RFC 3161 timestamps
  live_capture/      # Signal detection, rich capture
  integrations/mcp/  # Certifying gateway, policy engine, graph viewer
  api/               # FastAPI routers
  auth/              # JWT, bcrypt, middleware
  models/            # SQLAlchemy ORM
  core/              # Config, database, provenance layers
frontend/            # Next.js 14+ app
tests/               # 1400+ tests
docs/                # Vision, trust model, architecture decisions
```

---

## Version

All components are at **v1.1.0**. See [STATUS.md](STATUS.md) for detailed component status and [ROADMAP.md](ROADMAP.md) for what's next.

## License

MIT. See [LICENSE](LICENSE).
