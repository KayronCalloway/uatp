# UATP Capsule Engine

**Signed reasoning traces for AI systems. Capture decisions, detect failures, generate training data.**

[![CI](https://github.com/KayronCalloway/uatp/actions/workflows/ci.yml/badge.svg)](https://github.com/KayronCalloway/uatp/actions/workflows/ci.yml)
[![Security](https://github.com/KayronCalloway/uatp/actions/workflows/security.yml/badge.svg)](https://github.com/KayronCalloway/uatp/actions/workflows/security.yml)
[![PyPI](https://img.shields.io/pypi/v/uatp)](https://pypi.org/project/uatp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What It Does

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

The signature proves the capsule has not been tampered with. The signals tell you whether the AI succeeded or failed. The thinking shows you why.

---

## Architecture

UATP is a full-stack web platform, not just a library.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Next.js Frontend (localhost:3000)                                          │
│  ├── Auth (login / register)                                                │
│  ├── Capsule Browser (search, filter, verify)                               │
│  ├── Session Audit Dashboard (MCP tool-call graphs)                         │
│  └── System Overview (live topology)                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Proxy rewrite
                                    │ /api/v1/*  → FastAPI
                                    │ /mcp/*     → FastAPI
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FastAPI Backend (localhost:9000)                                           │
│  ├── Capsule API (CRUD, verify, search)                                     │
│  ├── Auth API (JWT, bcrypt, rate limiting)                                  │
│  ├── MCP Certifying Gateway (intercept → sign → audit)                      │
│  └── Health / Metrics / Calibration                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            ┌───────────────┐               ┌───────────────┐
            │  SQLite       │               │  PostgreSQL   │
            │  (dev mode)   │               │  (production) │
            └───────────────┘               └───────────────┘
```

**Capture sources** feed capsules into the engine:

| Source | How | What's Captured |
|--------|-----|-----------------|
|| **Claude Code** | Hook in `.claude/hooks/` | Thinking blocks, tool calls, usage, full transcript |
|| **Hermes Agent** | Plugin (`on_session_end`) | Reasoning, tool graphs, economics, session lineage |
|| **Ollama/Gemma** | Transparent proxy (`:11435→:11434`) | Prompt/response, `<think>` tags, eval metrics |
|| **Any OpenAI-compatible** | `BaseHook` subclass | Configurable per platform |
|| **MCP Gateway** | `python -m src.integrations.mcp.gateway` | Certified tool calls, DECISION_POINT → TOOL_CALL/REFUSAL graph |

---

## Quick Start (Development)

### 1. Clone and install

```bash
git clone https://github.com/KayronCalloway/uatp.git
cd uatp
```

### 2. Backend

```bash
# Python dependencies
pip install -e ".[dev]"

# Create env file (development uses SQLite, no Postgres needed)
cp .env.example .env
# Edit .env: ENVIRONMENT=development, DEV_DB_URL=sqlite:///./uatp_dev.db

# Run
python -m uvicorn src.main:app --host 0.0.0.0 --port 9000 --reload
```

The backend serves:
- API: `http://localhost:9000/api/v1/`
- MCP audit: `http://localhost:9000/mcp/`
- Health: `http://localhost:9000/health`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. In development mode, the app uses auto-login and SQLite — no external database required.

### 4. Verify both are running

```bash
curl http://localhost:9000/health
curl http://localhost:3000/api/v1/health  # proxied through Next.js
```

---

## MCP Certifying Gateway

The MCP Gateway is UATP's primary integration surface. It turns the Model Context Protocol — the emerging standard for AI tool access — into a certifying proxy that signs every action at the boundary.

Why MCP? Because tool calls are the highest-signal moment in an agent's lifecycle. Before the gateway, tool execution is invisible and ungoverned. After the gateway, every call becomes a signed, queryable audit record.

```
Agent (Claude, Cursor, any MCP client)
        │
        ▼
┌─────────────────────┐
│  UATP MCP Gateway   │  ← intercepts every tool_call
│  - Policy check     │
│  - Sign params      │
│  - Forward / Block  │
└─────────────────────┘
        │
    ┌───┴───┐
    ▼       ▼
TOOL_CALL  REFUSAL
    │
    ▼
Ed25519-signed capsule
(observed, not asserted)
```

Every intercepted call produces a lineage graph:

1. **DECISION_POINT** — the policy evaluation moment (what tool, what constraints)
2. **TOOL_CALL** or **REFUSAL** — the executed result or blocked reason
3. **Proof block** — appended to the MCP response so the client knows the call was certified

Evidence classes separate fact from inference:

| Class | Meaning | Example |
|-------|---------|---------|
| `observed` | Proxy-verified hard fact | Tool name, timestamp, argument hash |
| `asserted` | Model's self-reported claim | "I intended to read this file" |
| `derived` | Computed by the gateway | Latency, status classification |
| `policy` | Governance decision | Allow/deny, constraint check results |

This distinction matters. Critics of AI auditing often conflate "the system said it did X" with "we can prove X happened." UATP makes the trust boundary explicit.

### Usage

```bash
# Start an upstream MCP server (any compliant server)
python -m src.integrations.mcp.demo_server

# Start the certifying gateway
python -m src.integrations.mcp.gateway \
    --upstream-cmd python -m src.integrations.mcp.demo_server

# Configure your MCP client (Claude Desktop, Cursor, etc.) to point at the gateway
```

Browse the audit trail in the **Session Audit Dashboard** at `/system`, or query via CLI:

```bash
python -m src.integrations.mcp.graph_viewer --latest
```

### Current Limitations (Alpha)

- **stdio transport only** — HTTP/SSE transport is planned
- **single upstream server** — multi-server aggregation is planned
- **no streaming or cancellation** — standard request/response only
- **local anchoring only** — remote timestamping and blockchain anchoring are planned

Status: Alpha. Core protocol compliance and security hardening are complete. Concurrency, multi-server, and remote anchoring are next.

---

## Session Audit Dashboard

The dashboard renders MCP sessions as interactive graphs:

- **Nodes**: `USER_MESSAGE`, `AGENT_RESPONSE`, `TOOL_CALL`, `REFUSAL`, `DECISION_POINT`
- **Edges**: parent/child lineage, evidence-class coloring
- **Verification**: click any capsule to see the signature, timestamp, and upstream server ID

To seed demo data in dev:

```bash
python seed_mcp.py
```

---

## SDK (Client Libraries)

For programmatic capsule creation outside the web platform:

**Python**
```bash
pip install uatp
```

```python
from uatp import create_capsule, sign_capsule, verify_capsule

capsule = create_capsule(
    prompt="Deploy the service to production",
    response="Deployed via kubectl apply...",
    model="claude-opus-4",
)
signed = sign_capsule(capsule, passphrase="your-passphrase")
assert verify_capsule(signed)
```

**TypeScript**
```bash
npm install @coolwithakay/uatp
```

---

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

---

## Analysis Tools

```bash
# Cross-model comparison (which model gets corrected less?)
python3 scripts/analysis/cross_model_report.py

# Extract DPO training pairs
python3 scripts/analysis/extract_dpo_pairs.py

# Tool call sequence analysis
python3 scripts/analysis/tool_patterns.py

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

## What's Working

| Component | Status | Notes |
|-----------|--------|-------|
| Ed25519 signing + verification | Stable | Core protocol, local-only |
| Python SDK | Stable | `pip install uatp` |
| Signal detection (7 types) | Stable | Calibrated against 1042 DPO pairs |
| Capsule capture (Claude Code) | Stable | Thinking, tools, economics |
| Capsule capture (Hermes) | Stable | Plugin, auto-fires on session end |
| Capsule capture (Ollama proxy) | Stable | Standalone, zero UATP deps |
| DPO pair extraction | Stable | 1987 pairs from 79 capsules |
| Confidence calibration | Stable | Autoresearch via Gemma |
| Cross-model comparison | Stable | Query across all capture sources |
|| Next.js dashboard | Stable | Auth, browse, verify, search, MCP audit |
|| FastAPI backend | Stable | REST API, JWT auth, rate limiting |
|| MCP Certifying Gateway | Alpha | stdio transport, single-server, needs concurrency + anchoring |
|| ML-DSA-65 post-quantum | Beta | Ed25519 + ML-DSA-65 dual signing |
|| RFC 3161 timestamps | Beta | DigiCert TSA, local fallback |
|| TypeScript SDK | Beta | `npm install @coolwithakay/uatp` |

---

## Project Structure

```
uatp-capsule-engine/
├── src/
│   ├── security/          # Ed25519 + ML-DSA-65 signing, RFC 3161 timestamps
│   ├── live_capture/      # Signal detection, rich capture, conversation monitoring
│   ├── integrations/mcp/  # Certifying gateway, policy engine, graph viewer
│   ├── api/               # FastAPI routers (capsules, auth, MCP sessions, calibration)
│   ├── auth/              # JWT, bcrypt, middleware, routes
│   ├── models/            # SQLAlchemy ORM (User, Capsule, Session)
│   └── core/              # Config, database, provenance layers
├── frontend/              # Next.js 14+ app (app router)
│   ├── src/app/           # Routes (/, /system)
│   ├── src/components/    # Capsule browser, auth forms, session graphs
│   └── src/lib/           # API client, quality calculator
├── scripts/
│   ├── analysis/          # Cross-model reports, DPO extraction, tool patterns
│   ├── autoresearch/      # Gemma-powered confidence calibration
│   ├── capture/           # Claude Code hook capture + backfill
│   └── proxy/             # Standalone Ollama capture proxy
├── sdk/
│   ├── python/            # pip install uatp
│   └── typescript/        # npm install @coolwithakay/uatp
├── tests/                 # 1400+ tests
└── docs/                  # Trust model, threat model, capsule type specs, ADRs
```

---

## Version

All components are at **v1.1.0**. See [STATUS.md](STATUS.md) for detailed component status and [ROADMAP.md](ROADMAP.md) for what's next.

## License

MIT. See [LICENSE](LICENSE).
