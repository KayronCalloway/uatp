# UATP docs: start here

This is the public map. Current docs first. Older planning notes are labeled as history, not product claims.

## Read first

1. [README](../README.md) — the public wedge: signed receipts for AI-agent actions
2. [STATUS](../STATUS.md) — what is stable, beta, alpha, planned, or experimental
3. [Trust Model](../TRUST_MODEL.md) — what the verifier proves and what it does not
4. [Roadmap](../ROADMAP.md) — near-term work and registry drift
5. [Vision](vision.md) — the full thesis: verifiable memory, attribution, and post-labor economics

## If you are verifying the core claim

Start with the offline receipt bundle path:

```bash
uatp verify-receipts \
  docs/examples/agent-receipts/valid_bundle.json \
  --artifact-root docs/examples/agent-receipts/artifacts \
  --strict \
  --no-color
```

Then run the tamper fixture demo:

```bash
./.venv/bin/python scripts/demo/verify_agent_receipt_tamper_demo.py
```

A valid bundle proves cryptographic self-consistency. It does not magically prove trusted identity, trusted time, legal admissibility, insurance use, or compensation. Those need policy and review layers on top.

## If you are evaluating adoption

Use these boundaries:

- Agent receipt bundles: beta, offline-verifiable, not externally audited
- MCP certifying gateway: alpha, useful as the external-boundary demo
- Dashboard/backend: beta/local-dev, not production infrastructure
- Python and TypeScript registries: behind the source tree; check [STATUS](../STATUS.md)

Do not use older market-sizing or launch-planning docs as current product status.

## If you are reading the vision

The vision is still the reason this exists:

- H1: prove what happened
- H2: prove what contributed
- H3: route value back to contributors

The public repo builds H1 first because H2 and H3 need independent proof underneath them. Otherwise they are just promises.

## Historical planning docs

These files preserve earlier thinking. They are not the current source of truth:

- [UATP_COMPLETE_VISION.md](UATP_COMPLETE_VISION.md)
- [UATP_2025_MARKET_ANALYSIS.md](UATP_2025_MARKET_ANALYSIS.md)
- [DATA_MARKETPLACE_IMPLEMENTATION.md](DATA_MARKETPLACE_IMPLEMENTATION.md)

Treat financial projections, marketplace timelines, adoption counts, insurance claims, and legal conclusions in those files as historical planning notes unless restated in README, STATUS, ROADMAP, or vision.md.
