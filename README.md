# UATP Capsule Engine

**Signed receipts for AI agent actions, verifiable outside the agent runtime.**

UATP turns tool calls, decisions, artifacts, corrections, and session traces into tamper-evident records. The near-term product is narrow: prove what an agent did, under whose key, with which artifacts, and whether the record was changed afterward. The long-term thesis is bigger: systems that shape the world should leave verifiable memory behind.

[![CI](https://github.com/KayronCalloway/uatp/actions/workflows/ci.yml/badge.svg)](https://github.com/KayronCalloway/uatp/actions/workflows/ci.yml)
[![Security](https://github.com/KayronCalloway/uatp/actions/workflows/security.yml/badge.svg)](https://github.com/KayronCalloway/uatp/actions/workflows/security.yml)
[![PyPI](https://img.shields.io/pypi/v/uatp)](https://pypi.org/project/uatp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

---

## Why this exists

AI systems are becoming acting systems. They call tools, touch files, make recommendations, trigger workflows, and increasingly operate across personal or enterprise context. A log inside the agent runtime is not enough. If the runtime, database, or dashboard has to be trusted, the proof is weak.

UATP starts with a smaller claim: an agent action should leave a signed receipt that can be checked elsewhere.

That receipt can later become more than audit evidence. It can become training signal, attribution evidence, consent metadata, and the basis for compensated reuse. The public code here focuses on the proof layer first.

Full thesis: [docs/vision.md](docs/vision.md)

---

## The thesis

UATP is infrastructure, not an end application. It does not try to be the model, the dashboard, the insurer, the marketplace, or the regulator. It provides the memory layer those systems need if their outputs are going to be trusted, attributed, licensed, or compensated.

The horizons are one tree at different depths:

- **H1 — Trust:** prove what happened.
- **H2 — Attribution:** prove what contributed.
- **H3 — Post-labor economics:** route value back to the people and processes that improved the system.

The public repo builds H1 first because every later claim depends on it. Without independently verifiable receipts, attribution and compensation are just promises.

---

## What UATP does today

UATP can:

- capture agent sessions and tool-boundary events
- emit signed receipt chains for agent actions
- export detached receipt bundles
- verify those bundles offline without Hermes, SQLite, or the running app
- check Ed25519 signatures, event hashes, parent-hash chains, bundle manifests, and artifact refs
- show deterministic tamper failures for event, chain, signature, and artifact edits
- export MCP gateway activity as signed receipt bundles

The current wedge is **signed receipts for AI agent actions**. Broader attribution, marketplace, and compensation features are future layers, not current product claims.

---

## Core concepts

### Receipt

A receipt is a signed record of one event: a decision, tool call, action trace, refusal, environment snapshot, or session boundary.

Each receipt contains:

- canonical event payload
- event hash
- Ed25519 signature
- public verification key
- signer identity
- parent event hash when part of a chain

### Receipt bundle

A receipt bundle is a detached, public verification artifact. It includes signed receipts, a chain report, capsule drafts, and a signed bundle manifest.

The verifier checks whether the bundle is internally consistent. If a trusted signer policy is provided, it also checks whether the signing key is one the verifier accepts.

### Capsule

A capsule is the broader UATP record format. Legacy capsules use schema 7.2. Agent execution traces use schema 7.4. Agent receipt bundles are the current verifier-first path for independent proof.

---

## Quick start from source

```bash
git clone https://github.com/KayronCalloway/uatp.git
cd uatp
pip install -e ".[dev]"
cp .env.example .env
# Edit .env for local development, for example:
# ENVIRONMENT=development
# DEV_DB_URL=sqlite:///./uatp_dev.db
```

Run the backend:

```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 9000 --reload
```

Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. Development mode uses SQLite and local/dev defaults. See [STATUS.md](STATUS.md) before treating any component as production infrastructure.

---

## Verify an agent receipt bundle

Use the checked-in fixture:

```bash
uatp verify-receipts \
  docs/examples/agent-receipts/valid_bundle.json \
  --artifact-root docs/examples/agent-receipts/artifacts \
  --strict \
  --no-color
```

Expected shape:

```text
✓ Agent receipt verification PASSED

  Schema: agent_receipts.v1
  Receipts: 2
  Capsule drafts: 2
  Artifacts checked: 1
  Chain root: sha256:...
  Chain tip: sha256:...
  Trusted timestamp: missing
```

A passing result without `--trusted-signer` proves cryptographic self-consistency. It does not prove the signer identity is trusted by the verifier. A result with `Trusted timestamp: missing` does not claim trusted time.

Machine-readable output:

```bash
uatp verify-receipts \
  docs/examples/agent-receipts/valid_bundle.json \
  --artifact-root docs/examples/agent-receipts/artifacts \
  --strict \
  --output json
```

More detail: [docs/architecture/agent-receipt-verification.md](docs/architecture/agent-receipt-verification.md)

---

## Tamper demo

Run the deterministic tamper fixture demo:

```bash
./.venv/bin/python scripts/demo/verify_agent_receipt_tamper_demo.py
```

It checks five cases:

- valid bundle passes
- event payload edit fails
- parent hash edit fails
- signature edit fails
- artifact edit fails

This is the public proof path: do not trust the agent runtime; verify the receipt bundle outside it.

---

## MCP certifying gateway

The MCP gateway is the flagship external boundary. It intercepts MCP tool calls, applies policy checks, forwards or blocks the call, and records the boundary as signed evidence.

Current export path:

```bash
python -m src.integrations.mcp.gateway \
  --upstream-cmd "python -m src.integrations.mcp.demo_server"
```

Inspect stored gateway sessions:

```bash
python -m src.integrations.mcp.graph_viewer --latest
```

Export a stored MCP session as an offline-verifiable receipt bundle:

```bash
uatp export-mcp-receipts uatp_mcp_store.db \
  --session-id sess_<id> \
  --output /tmp/mcp_receipts.json

uatp verify-receipts /tmp/mcp_receipts.json \
  --trusted-signer uatp-mcp-gateway=<ed25519_public_key_hex> \
  --strict \
  --no-color
```

Status: alpha. The gateway proves the boundary pattern, but still needs concurrency, multi-server handling, remote anchoring, and demo hardening before it should be presented as production infrastructure.

---

## Capture surfaces

Current local/dev capture surfaces:

- Claude Code hook capture
- Hermes Agent session capture
- Ollama/Gemma transparent proxy
- MCP certifying gateway

See [STATUS.md](STATUS.md) for exact component labels. “Stable local/dev” means useful in local workflows, not externally audited.

---

## Trust boundaries

UATP is designed around independent verification:

- private keys stay local to the signer
- content can be represented by hashes and artifact refs
- receipt bundles can be checked without the original app runtime
- strict mode fails when expected artifacts are missing or tampered
- trusted signer policy is explicit; a valid signature alone only proves possession of a key
- trusted timestamp verification is fail-closed when timestamp evidence or TSA trust anchors are missing

See [TRUST_MODEL.md](TRUST_MODEL.md) for the broader model.

---

## What is not claimed yet

UATP is not externally audited.

The public verifier can prove bundle integrity, signatures, chain linkage, artifact integrity, and optional trusted-signer/timestamp checks. It does not by itself prove legal admissibility, insurance eligibility, full attribution, or marketplace compensation.

Those are downstream uses that require policy, identity, legal review, adoption, and product layers beyond the current core.

---

## Project structure

```text
src/
  agent_receipts/     # receipt events, signing, chains, verifier, artifact refs
  integrations/mcp/   # certifying gateway, policy checks, graph/export tooling
  cli/                # verify, verify-receipts, export, inspect commands
  security/           # Ed25519, ML-DSA-65 beta support, RFC 3161 timestamping
  live_capture/       # local capture and signal detection
  api/                # FastAPI routers
  models/             # SQLAlchemy models
frontend/             # Next.js dashboard
sdk/python/           # Python SDK package source
sdk/typescript/       # TypeScript SDK package source
docs/                 # vision, status, architecture, trust docs
tests/                # pytest suites and fixture tests
```

---

## SDK packages

Registry packages currently lag the source tree.

Python:

```bash
pip install uatp
```

TypeScript:

```bash
npm install @coolwithakay/uatp
```

Before relying on registry behavior, check [STATUS.md](STATUS.md). The source tree is ahead of at least one published package.

---

## Development checks

Useful local checks:

```bash
# Receipt verifier focused tests
./.venv/bin/python -m pytest tests/agent_receipts tests/unit/test_cli_verify_receipts.py -q

# MCP gateway integration tests
./.venv/bin/python -m pytest tests/integration/test_mcp_gateway.py -q

# Full suite
./.venv/bin/python -m pytest -q

# Whitespace/conflict check before commit
git diff --check
```

---

## Versions and status

Source tree: **1.1.0**
GitHub latest release: **v1.1.0**
License on main: **Apache-2.0**

Registry state at last status update:

- PyPI `uatp`: **0.2.1** published; **1.1.0** source in `sdk/python/`
- npm `@coolwithakay/uatp`: **1.0.1** published; **1.1.0** source in `sdk/typescript/`
- Capsule schema: **7.2** legacy capsules; **7.4** agent execution traces

See [STATUS.md](STATUS.md) for the source of truth.

---

## Roadmap

Near-term priorities:

1. keep the verifier path small and trustworthy
2. harden trusted signer and timestamp policy UX
3. make MCP receipt export the clearest external-boundary demo
4. map agent receipts cleanly to OpenTelemetry-style traces where useful
5. add user-owned memory and consent features only after the receipt layer remains independently verifiable

The long-term aim remains post-labor economics: if human judgment, corrections, and workflows improve AI systems, there should be infrastructure to prove, control, license, and compensate that contribution. The current repo builds the receipt layer first.

---

## License

Apache License 2.0. See [LICENSE](LICENSE).

Earlier public versions of UATP were released under the MIT License. The main branch is now Apache-2.0; prior MIT grants remain valid for those earlier releases.
