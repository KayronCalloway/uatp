# UATP Documentation — Start Here

This page is the public map. It points to current, claim-clean documents first and labels older planning docs as historical.

## Read first

1. [README](../README.md) — current product wedge and verifier path
2. [STATUS](../STATUS.md) — source of truth for what is stable, beta, alpha, planned, or experimental
3. [Trust Model](../TRUST_MODEL.md) — security assumptions and verification boundaries
4. [Roadmap](../ROADMAP.md) — near-term work and known registry drift
5. [Vision](vision.md) — full thesis: verifiable memory, attribution, and post-labor economics

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

A valid bundle proves cryptographic self-consistency. Trusted signer identity, trusted time, legal admissibility, insurance use, and compensation require additional policy and review layers.

## If you are evaluating adoption

Use these boundaries:

- Agent receipt bundles: beta, offline-verifiable, not externally audited
- MCP certifying gateway: alpha, useful as the external-boundary demo
- Dashboard/backend: beta/local-dev, not production infrastructure
- Python and TypeScript registries: behind the source tree; check [STATUS](../STATUS.md)

Do not rely on older market-sizing or launch-planning docs for current product status.

## If you are reading the vision

The vision is still the reason this exists:

- H1: prove what happened
- H2: prove what contributed
- H3: route value back to contributors

The public repo builds H1 first because H2 and H3 need independent proof underneath them.

## Historical planning docs

The files below preserve earlier thinking, but they are not the current source of truth:

- [UATP_COMPLETE_VISION.md](UATP_COMPLETE_VISION.md)
- [UATP_2025_MARKET_ANALYSIS.md](UATP_2025_MARKET_ANALYSIS.md)
- [DATA_MARKETPLACE_IMPLEMENTATION.md](DATA_MARKETPLACE_IMPLEMENTATION.md)

Treat financial projections, marketplace timelines, adoption counts, insurance claims, and legal conclusions in those files as historical planning notes unless restated in README, STATUS, ROADMAP, or vision.md.
