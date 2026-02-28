# UATP Capsule Marketplace Roadmap

> Reference doc for building the AI reasoning marketplace. Created 2026-01-20.

## Overview

A marketplace where AI agents and developers can discover, verify, and trade reasoning traces (capsules). Built on top of UATP's existing trust infrastructure.

---

## Phase 1: Marketplace MVP (No UCP)

**Goal:** Validate demand before building payment infrastructure.

### Already Done
- [x] Capsule storage and retrieval
- [x] Cryptographic signatures (Ed25519)
- [x] RFC 3161 timestamps
- [x] Embedding search (TF-IDF, 100% coverage)
- [x] Attribution and lineage tracking
- [x] v7 envelope format with economic weights
- [x] Stripe integration installed

### To Build
- [ ] **Discovery UI** - Browse/search capsules by type, domain, confidence
- [ ] **Capsule detail pages** - Full reasoning trace, verification status, lineage
- [ ] **Listing mechanism** - Mark capsules as "available" with price
- [ ] **Basic checkout** - Stripe for payments, manual fulfillment
- [ ] **Seller dashboard** - List your capsules, see purchases
- [ ] **Buyer access** - Purchase grants API access to capsule

### Success Metrics
- 10+ capsules listed
- 5+ unique buyers
- $100+ in transactions
- Repeat purchases indicate value

---

## Phase 2: Validate & Learn

**Goal:** Understand what's actually valuable before scaling.

### Questions to Answer
- What capsule types sell? (reasoning traces, code decisions, research?)
- What's the price sensitivity? ($0.10 vs $1 vs $10 per capsule)
- Do buyers want individual capsules or subscriptions?
- Is the value in the reasoning or the outcome data?
- Do buyers trust the verification system?

### Data to Collect
- Capsule types by sales volume
- Price points that convert
- Buyer feedback on quality
- Seller friction points
- API usage patterns after purchase

---

## Phase 3: UCP Integration

**Goal:** Automate payments and join Google/Apple commerce ecosystem.

### Prerequisites
- [ ] Proven transaction volume (Phase 1-2)
- [ ] UCP spec stabilized (currently just announced)
- [ ] Clear pricing model validated
- [ ] Legal/compliance review for automated payments

### UCP Features to Implement
- [ ] **UCP Bridge** - Connect UATP to Universal Commerce Protocol
- [ ] **Commerce Capsules** - New capsule type for transactions
- [ ] **Agent Authentication** - AI agents as buyers/sellers
- [ ] **Automated Royalties** - Pay upstream contributors when capsule reused
- [ ] **Payment Tracking** - Full audit trail of economic flows

### Architecture Notes
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   UATP Engine   │────▶│   UCP Bridge    │────▶│  Google/Apple   │
│   (Capsules)    │     │   (Payments)    │     │  Commerce APIs  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Attribution    │     │  Commerce       │
│  Graph          │────▶│  Capsules       │
└─────────────────┘     └─────────────────┘
```

### UCP Integration Checklist
- [ ] Read UCP spec when published
- [ ] Implement UCP Bridge service
- [ ] Create commerce capsule schema
- [ ] Add agent wallet/identity system
- [ ] Implement royalty distribution from attribution weights
- [ ] Test with Google/Apple sandbox
- [ ] Compliance review
- [ ] Production rollout

---

## Phase 4: Scale

**Goal:** Grow the marketplace with automated infrastructure.

- [ ] Agent-to-agent transactions (no human in loop)
- [ ] Subscription tiers
- [ ] Quality scoring / reputation system
- [ ] Capsule bundles / collections
- [ ] API rate limiting by payment tier
- [ ] Analytics dashboard for sellers

---

## Research to Track

### MIT Recursive Language Models (RLMs)
- **What:** Models that recursively query context instead of loading everything
- **Relevance:** Could change how capsule chains are navigated/priced
- **Status:** Research paper, not production ready
- **Action:** Monitor for SDK/API availability, consider for v8
- **Links:**
  - https://www.startuphub.ai/ai-news/ai-video/2026/mit-recursive-language-models-shatter-the-llm-context-window-limit/
  - https://introl.com/blog/recursive-language-models-rlm-context-management-2026

---

## Current State (as of 2026-01-20)

| Component | Status |
|-----------|--------|
| Capsule Storage | Ready |
| Signatures | Ready |
| Embeddings | 100% coverage |
| Outcomes | 38% coverage |
| Attribution Cards | Ready |
| Stripe | Installed |
| Discovery UI | Not started |
| UCP | Not started (waiting for spec) |

---

## Notes

- Don't build UCP until Phase 1-2 validate demand
- Stripe handles payments fine for MVP
- UCP is plumbing, not product
- Focus on: Do people want to buy AI reasoning?
