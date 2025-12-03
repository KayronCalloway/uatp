# UATP Technical Q&A for Enterprise Buyers

**Version:** 2.0
**Date:** October 26, 2025
**Audience:** CTOs, CISOs, Compliance Officers, Technical Decision-Makers
**Purpose:** Complete guide from "What is UATP?" to deep technical implementation

---

## Executive Summary

**UATP (Universal Attribution and Trust Protocol)** is a runtime trust layer for AI systems that creates cryptographically-sealed audit trails of AI decisions.

**The Problem:** When regulators or lawyers ask "prove your AI followed policy X on date Y," most companies spend 3 weeks and $150K reconstructing logs - and still can't prove anything definitively.

**The Solution:** UATP captures every AI decision in real-time, seals it cryptographically, and generates audit reports in 30 minutes instead of 3 weeks.

**For whom:** Companies using AI in regulated industries (healthcare, finance, insurance) who need to prove their AI acted correctly.

---

## How to Read This Document

This Q&A follows a **learning progression**:

📘 **New to UATP?** Read Section 1 (Introduction) first
💼 **Evaluating cost?** Jump to Section 2 (Commercials)
🎨 **Want to see it?** Check Section 3 (Product Experience)
🔧 **Ready to integrate?** Read Sections 4-5 (Integration & Governance)
⚙️ **Planning deployment?** Review Section 6 (Operations)
🔒 **Need security validation?** Dive into Sections 7-9 (Security, Data, Crypto)

---

## Table of Contents

### 📘 Understanding UATP (Start Here)
**1. [Introduction - What is UATP?](#1-introduction---what-is-uatp)**
- Q1.1: What is UATP and what problem does it solve?
- Q1.2: How does UATP actually work?
- Q1.3: Who needs UATP?
- Q1.4: What makes UATP different from logging or monitoring?
- Q1.5: Can you show me a real example of an audit report?

### 💼 Business & Commercial
**2. [Commercials & Risk](#2-commercials--risk)**
- Q2.1: Proof milestones in pilot
- Q2.2: Pricing protections
- Q2.3: Reference customers
- Q2.4: Offboarding plan

### 🎨 Product Experience
**3. [Product Experience](#3-product-experience)**
- Q3.1: Dashboard and reports
- Q3.2: Alerting setup
- Q3.3: Template packs (HIPAA, GDPR, PCI, EU AI Act)
- Q3.4: Training and documentation

### 🔧 Integration & Daily Use
**4. [Integration Surface](#4-integration-surface)**
- Q4.1: Provider support matrix
- Q4.2: Non-Python stacks
- Q4.3: Observability integration
- Q4.4: API versioning

**5. [Enforcement & Governance](#5-enforcement--governance)**
- Q5.1: False positive tracking
- Q5.2: Override workflows
- Q5.3: Policy-as-code

### ⚙️ Production Operations
**6. [Deployment, Reliability & Ops](#6-deployment-reliability--ops)**
- Q6.1: SLO/SLA targets
- Q6.2: Throughput limits
- Q6.3: Disaster recovery
- Q6.4: Canary deployments
- Q6.5: Multi-environment support

### 🔒 Security & Technical Deep Dives
**7. [Security & Compliance](#7-security--compliance)**
- Q7.1: BAA/DPA agreements
- Q7.2: Key management
- Q7.3: Supply chain security
- Q7.4: Penetration testing
- Q7.5: Access control

**8. [Data Handling Nuances](#8-data-handling-nuances)**
- Q8.1: Schema versioning
- Q8.2: Data residency
- Q8.3: GDPR compliance
- Q8.4: Retention policies

**9. [Capsule Integrity & Crypto Details](#9-capsule-integrity--crypto-details)**
- Q9.1: Post-quantum cryptography
- Q9.2: Clock skew handling
- Q9.3: Failure semantics
- Q9.4: Merkle trees
- Q9.5: Collision resistance

### 📚 Quick Reference
**10. [Quick Start Guide](#10-quick-start-guide)** - 5 steps to pilot
**11. [FAQ](#11-faq)** - Common questions and objections
**12. [UATP vs Alternatives](#12-uatp-vs-alternatives)** - Comparison table

---what-is-uatp)**
- What is UATP and what problem does it solve?
- How does UATP work?
- Who needs UATP?
- What makes UATP different from logging or monitoring?

### 💼 Business & Commercial
**2. [Commercials & Risk](#2-commercials--risk)**
- Proof milestones in pilot
- Pricing protections
- Reference customers
- Offboarding plan

### 🎨 Product Experience
**3. [Product Experience](#3-product-experience)**
- Dashboard and reports
- Template packs
- Alerting
- Training and documentation

### 🔧 Integration & Daily Use
**4. [Integration Surface](#4-integration-surface)**
- Provider support matrix
- APIs and SDKs
- Observability integration
- API versioning

**5. [Enforcement & Governance](#5-enforcement--governance)**
- False positive tracking
- Override workflows
- Policy-as-code

### ⚙️ Production Operations
**6. [Deployment, Reliability & Ops](#6-deployment-reliability--ops)**
- SLO/SLA targets
- Throughput limits
- Disaster recovery
- Multi-environment support

### 🔒 Security & Technical Deep Dives
**7. [Security & Compliance](#7-security--compliance)**
- BAA/DPA agreements
- Key management
- Supply chain security
- Penetration testing
- Access control

**8. [Data Handling Nuances](#8-data-handling-nuances)**
- Schema versioning
- Data residency
- GDPR compliance
- Retention policies

**9. [Capsule Integrity & Crypto Details](#9-capsule-integrity--crypto-details)**
- Post-quantum cryptography
- Clock skew handling
- Failure semantics
- Merkle trees
- Collision resistance

---

## 1. Introduction - What is UATP?

## Q1.1: What is UATP and what problem does it solve?

**What it is:**

UATP (Universal Attribution and Trust Protocol) is a **runtime trust layer for AI systems**. Think of it as "HTTPS for AI" - it creates a cryptographically-sealed audit trail of every AI decision your system makes.

**The problem:**

When a regulator, auditor, or lawyer asks:
> "Show me proof that your AI followed HIPAA guidelines on October 15th at 2:30 PM when treating patient ID 12345"

**What happens today:**
```
Week 1: Engineering digs through logs
  ├─ Logs are incomplete (rotated out after 30 days)
  ├─ Logs show inputs/outputs, not decision process
  └─ No proof that policy checks actually ran

Week 2: Interview developers
  ├─ "We think it checks HIPAA..."
  ├─ "The model should have refused if..."
  └─ No definitive answers

Week 3: Hire external auditor ($50K+)
  ├─ Still no cryptographic proof
  ├─ Reconstruct from partial data
  └─ Result: "We can't be certain..."

Outcome:
  ❌ 3 weeks wasted
  ❌ $150K+ in costs
  ❌ Uncertain compliance status
  ❌ Settlement pressure
```

**What UATP provides:**
```
30 Minutes Later: Complete audit report

Evidence Delivered:
  ✅ Capsule chain from input → reasoning → output
  ✅ HIPAA policy check capsule (PASSED)
  ✅ Cryptographic signatures (untamperable)
  ✅ Refusal mechanisms (verified functional)
  ✅ Complete audit trail (human + machine readable)

Outcome:
  ✅ 30 minutes to evidence
  ✅ Included in subscription
  ✅ Cryptographic proof
  ✅ Defensible in litigation
```

**Bottom line:** UATP turns "we think we were compliant" into "here's cryptographic proof we were compliant."

---

## Q1.2: How does UATP actually work?

**Simple explanation:**

UATP sits **between your application code and your AI provider** (OpenAI, Anthropic, Google, etc.).

**The flow:**


**Visual Architecture:**

```
┌─────────────────────────────────────────────────────────────────┐
│                      YOUR APPLICATION                            │
│  (Healthcare app, Financial system, Insurance platform)         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ (1) AI Request
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                         UATP LAYER                               │
│                                                                  │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐            │
│  │   Policy   │  │  Capture &  │  │ Cryptographic│            │
│  │   Check    │→│   Record    │→│   Signing    │            │
│  │ (HIPAA/    │  │  (Capsules) │  │ (Dilithium3) │            │
│  │  GDPR)     │  │             │  │              │            │
│  └────────────┘  └─────────────┘  └──────────────┘            │
│                                                                  │
└────────────────────┬───────────────────┬────────────────────────┘
                     │                   │
        (2) Forward  │                   │ (4) Store
           Request   │                   │     Capsules
                     ▼                   ▼
         ┌─────────────────┐   ┌─────────────────┐
         │   AI PROVIDER   │   │  CAPSULE STORE  │
         │  (OpenAI, etc)  │   │  (PostgreSQL)   │
         └─────────────────┘   └─────────────────┘
                     │
        (3) Response │
                     ▼
         ┌─────────────────────────────────────────┐
         │         AUDIT REPORTS                   │
         │  ┌─────────────┐  ┌─────────────┐      │
         │  │   JSON      │  │   PDF       │      │
         │  │  (Machine)  │  │  (Human)    │      │
         │  └─────────────┘  └─────────────┘      │
         └─────────────────────────────────────────┘
```

**Data Flow:**
1. Your code makes AI request → UATP intercepts
2. UATP checks policies (HIPAA? GDPR?) → Pass/Fail
3. If pass: Forward to AI provider → Get response
4. UATP captures everything in capsules → Sign cryptographically
5. Store capsules → Generate audit reports on demand

**Key Point:** Adds <50ms latency, happens in real-time


**Simple text flow:**

```
Your Code                UATP                AI Provider
    |                     |                      |
    |---(1) AI Request--->|                      |
    |                     |                      |
    |                     |--(2) Check Policy--->|
    |                     |      (HIPAA? GDPR?)  |
    |                     |                      |
    |                     |---(3) Forward Req--->|
    |                     |                      |
    |                     |<--(4) AI Response----|
    |                     |                      |
    |<--(5) Return Resp---|                      |
    |                     |                      |
    |                     |--(6) Seal Capsule--->|
    |                     |   (Crypto signature) |
```

**What gets captured in each "capsule":**

1. **INPUT_PERSPECTIVE capsule**
   - What you asked the AI
   - User context (who, when, why)
   - Sensitivity classification

2. **POLICY_CHECK capsule**
   - Which policies were checked (HIPAA, GDPR, etc.)
   - Pass/fail results
   - Timestamp of check

3. **REASONING_CHAIN capsule**
   - AI's reasoning steps (if available)
   - Confidence scores
   - Model used

4. **OUTPUT_DECISION capsule**
   - Final AI response
   - Tokens used
   - Latency metrics

5. **Cryptographic seal**
   - Each capsule is signed with post-quantum cryptography
   - Capsules link together in a hash chain
   - Tampering is mathematically impossible

**Key point:** All of this happens in **real-time** (adds <50ms latency). You don't reconstruct anything later - it's captured as it happens.

---

## Q1.3: Who needs UATP?

**Primary buyers:**

1. **Healthcare companies using AI**
   - HIPAA compliance requirements
   - Need to prove PHI was handled correctly
   - Regulators demand audit trails
   - Example: AI-powered patient triage, diagnosis assistance

2. **Financial services**
   - Model governance requirements
   - Audit trails for credit decisions
   - Regulatory compliance (FCRA, ECOA)
   - Example: AI-powered lending, fraud detection

3. **Insurance companies**
   - Need to prove AI risk assessments were fair
   - Underwriting compliance
   - Claims processing documentation
   - Example: AI-powered underwriting, claims automation

4. **Any company facing AI liability**
   - EU AI Act compliance (2025+)
   - Board wants proof of AI governance
   - Legal wants defensibility
   - Risk officers want audit trails

**Common scenarios:**

- ✅ "We use GPT-4 to analyze patient data"
- ✅ "Our AI makes credit decisions"
- ✅ "We're deploying AI in regulated workflows"
- ✅ "Board asked: 'how do we know our AI is compliant?'"
- ✅ "Insurance wants proof we have AI controls"

**Who does NOT need UATP (yet):**

- ❌ Internal AI tools with no compliance requirements
- ❌ Unregulated consumer apps
- ❌ Research projects (unless publishing results)

---

## Q1.4: What makes UATP different from logging or monitoring tools?

**What most companies have today:**

| Tool Type | What it does | Why it's not enough |
|-----------|--------------|---------------------|
| **Application logs** | Records inputs/outputs | ❌ Can be edited/deleted<br>❌ No policy check proof<br>❌ No cryptographic seal |
| **Monitoring (Datadog, etc.)** | Tracks metrics, errors | ❌ Reactive, not preventive<br>❌ No decision-level audit trail<br>❌ No compliance focus |
| **MLOps tools** | Model performance tracking | ❌ No runtime policy enforcement<br>❌ No cryptographic chain<br>❌ No regulator-ready reports |
| **Audit logs** | Security events | ❌ Periodic, not real-time<br>❌ No AI-specific context<br>❌ Not designed for litigation |

**What UATP provides uniquely:**

| Feature | UATP | Traditional Logging |
|---------|------|---------------------|
| **Tamper-proof** | ✅ Cryptographic signatures | ❌ Logs can be edited |
| **Real-time policy enforcement** | ✅ Blocks violations before they happen | ❌ Detects violations after |
| **Regulator-ready reports** | ✅ Generate in 30 minutes | ❌ Takes weeks to compile |
| **Cryptographic proof** | ✅ Post-quantum secure | ❌ No cryptographic guarantees |
| **AI-specific** | ✅ Captures reasoning, not just I/O | ❌ Generic logging |
| **Compliance-focused** | ✅ Built for HIPAA/GDPR/EU AI Act | ❌ Generic security logs |

**Analogy:**

- **Traditional logs** = Taking notes in a notebook (can be lost, edited, disputed)
- **UATP capsules** = Notarized, timestamped, sealed documents (legally defensible proof)

**Key difference:** UATP isn't just *recording* what happened - it's *proving* what happened with cryptographic certainty.

---

## Q1.5: Can you show me a real example of a UATP audit report?

**Yes.** Here's what a UATP audit report looks like (simplified):

**Scenario:** Healthcare AI triage system on October 26, 2025 at 2:12 PM

**Human-Readable Summary (2 minutes to read):**
```
======================================================================
         UATP TRUST AUDIT SUMMARY
======================================================================

Report ID: audit_2025_10_26_201247
Audit Date: October 26, 2025
Workflow: Healthcare AI Triage
AI System: Claude Sonnet 4

----------------------------------------------------------------------
 CHAIN INTEGRITY
----------------------------------------------------------------------
✅ Chain Status: VERIFIED
✅ Capsules Traced: 5 of 5
✅ Cryptographic Proofs: All Valid
✅ Tampering Detected: None

----------------------------------------------------------------------
 COMPLIANCE CHECK
----------------------------------------------------------------------
✅ EU_AI_ACT: COMPLIANT
   - Human oversight documented
   - Risk assessment performed
   - Transparency requirements met

✅ GDPR: COMPLIANT
   - Data processing documented
   - Consent properly recorded
   - Rights procedures in place

✅ HIPAA: COMPLIANT
   - PHI access controls verified
   - Audit trail complete
   - Minimum necessary principle followed

----------------------------------------------------------------------
 KEY DECISION POINTS
----------------------------------------------------------------------
1. INPUT_PERSPECTIVE (2025-10-26T20:12:47)
   User query received with patient context
   Sensitivity: PROTECTED_HEALTH_INFO
   Verification: ✅

2. POLICY_CHECK (2025-10-26T20:12:47)
   HIPAA consent verification: PASSED
   Data minimization check: PASSED
   Verification: ✅

3. REASONING_CHAIN (2025-10-26T20:12:47)
   Multi-step clinical reasoning performed
   Confidence: 92%
   Verification: ✅

4. OUTPUT_DECISION (2025-10-26T20:12:47)
   Response generated with uncertainty acknowledged
   Recommendation: Escalate to human physician
   Verification: ✅

----------------------------------------------------------------------
 BOTTOM LINE FOR RISK OFFICER
----------------------------------------------------------------------
This AI interaction is DEFENSIBLE in litigation because:

1. Complete chain of custody documented
2. All compliance checks performed and passed
3. Cryptographic proof prevents tampering claims
4. Uncertainty properly acknowledged
5. Human oversight documented

Insurability: YES
Recommended Premium Adjustment: -15% to -20% (excellent controls)

======================================================================
Report Generated: 2025-10-26T20:12:47
Cryptographic Signature: dilithium3:5ef0fbe92bc74fd25702e261...
Audited By: UATP Compliance Team
======================================================================
```

**Machine-Readable Version (JSON):**

Also includes full JSON with all capsule data, signatures, policy checks, timestamps - ready for automated compliance systems.

**Key point:** This report was generated **30 minutes after the incident**, not 3 weeks later. The cryptographic signatures prove it can't be fabricated retroactively.

---

## 2. Commercials & Risk

## Q2.1: What are the proof milestones in the pilot to validate the system works?

**90-Day Pilot Structure:**

The pilot is designed to give you **concrete proof points** every 2-3 weeks, so you know if this works by week 6 (not week 12).

**Week 1: Installation & Verification**
```
Milestone: UATP Installed and Generating Capsules

Success Criteria:
  ✅ SDK integrated with 1 AI workflow
  ✅ First capsule generated and verified
  ✅ Signature verification passes
  ✅ Dashboard accessible

Deliverable:
  - Installation report
  - First capsule chain (sample)

Proof:
  You run: uatp verify --chain-id <your-chain>
  Result: "✅ All signatures valid, chain intact"
```

**Week 2-3: Policy Deployment (Shadow Mode)**
```
Milestone: Policies Detecting Issues (Not Blocking Yet)

Success Criteria:
  ✅ HIPAA/GDPR template pack deployed
  ✅ Shadow mode active (logging, not enforcing)
  ✅ 10,000+ AI interactions captured
  ✅ Policy violation rate measured

Deliverable:
  - Shadow mode report:
    - Detected violations (would have been blocked)
    - False positive rate
    - Performance impact (<50ms target)

Proof:
  Dashboard shows: "234 violations detected, 0 blocked (shadow)"
  Zero production impact
```

**Week 4-6: Enforcement Testing**
```
Milestone: Policies Enforcing in Staging/Canary

Success Criteria:
  ✅ Enforcement mode enabled (10% of traffic)
  ✅ Circuit breaker tested
  ✅ Refusal mechanism working
  ✅ False positive rate <2%

Deliverable:
  - Enforcement report:
    - Blocked requests (with justification)
    - False positives identified and tuned
    - Circuit breaker response time

Proof:
  Live demo: "This request should block... [blocked]"
  Capsule shows refusal reason cryptographically sealed
```

**Week 7-9: Audit Report Generation**
```
Milestone: Audit Artifacts for Regulators

Success Criteria:
  ✅ 50,000+ interactions in capsule chains
  ✅ Generate audit report for 1 workflow
  ✅ Cryptographic verification passes
  ✅ Human summary clear and accurate

Deliverable:
  - Full audit report (JSON + PDF)
  - Compliance grade (A-F)
  - Insurance actuarial data

Proof:
  You present report to legal/compliance team
  They confirm: "This is what we'd give a regulator"
```

**Week 10-12: Production Readiness**
```
Milestone: Full Production Deployment Plan

Success Criteria:
  ✅ Performance validated (<50ms p99 latency)
  ✅ Storage scaling plan confirmed
  ✅ DR tested (backup/restore)
  ✅ Alerting configured
  ✅ Runbooks reviewed

Deliverable:
  - Production deployment plan
  - Risk assessment
  - Rollback procedure
  - SLA targets

Proof:
  You decide: "We're ready for 100% enforcement"
```

**Go/No-Go Decision (Week 6):**

By week 6, you'll know if this works:

```
MUST HAVE (No-Go if Missing):
  ✅ Capsules generating correctly
  ✅ Signatures verifying (no false negatives)
  ✅ Audit reports generated successfully
  ✅ Performance impact <50ms p99
  ✅ False positive rate <2% (tuned)

If these pass: Continue to full pilot
If these fail: We extend pilot (no extra cost) or part ways
```

**What happens after pilot:**
- ✅ Success → Convert to annual subscription ($36K/year)
- ✅ Success → Expand to more workflows
- ✅ Success → Become reference customer (optional, 10% discount)
- ❌ Failure → We work with you to fix (free extension)
- ❌ Unfixable → Part ways cleanly (keep all data)

**Honest assessment:**
> The pilot is designed to derisk YOUR decision. If we can't deliver milestones, we extend the pilot at no extra cost until we do (or we part ways). You're not locked in.

---

## Q2.2: What protections exist against price increases or unexpected charges?

**Pricing Protections:**

**1. Pilot Fixed Price:**
```
90-Day Pilot:
  - Fixed price: $20,000 (no overages)
  - Scope: Up to 100,000 AI interactions
  - Included: Unlimited policies, reports, support
  - Overage: We discuss before charging

  Guarantee: "No surprise bills during pilot"
```

**2. Annual Contract Caps:**
```
Annual Subscription:
  Base: $36,000/year (300K interactions/month)

  Price Protection:
    - Renewal increase cap: 10% annually (max)
    - Interaction overages: $0.10 per interaction
    - Overage cap: 25% of base (then auto-upgrade)

  Example:
    Year 1: $36K base + $5K overages = $41K total
    Year 2: $36K → max $39.6K base (10% cap)

  Contract: Price caps in MSA
```

**3. Volume Discounts (Locked In):**
```
Volume Tiers:
  - 0-300K/month: $36K/year ($0.10/interaction)
  - 300K-1M/month: $60K/year ($0.05/interaction)
  - 1M-5M/month: $180K/year ($0.03/interaction)
  - 5M+/month: Custom (negotiated, 3-year lock)

  Tier Lock: Once reached, you stay there if usage drops
```

**4. No Hidden Fees:**
```
Included in Base:
  ✅ Unlimited policies
  ✅ Unlimited audit reports
  ✅ Unlimited users
  ✅ Standard support
  ✅ All template packs
  ✅ Dashboard + API access

Extra Costs (Transparent):
  - Premium support (24/7): +$10K/year
  - Custom policy dev: $5K-$15K (one-time)
  - Onsite training: $5K/day + expenses
  - Professional services: $250/hour
```

**5. Early Termination Protection:**
```
Termination Terms:
  - Pilot: 30-day notice, no penalty
  - Annual: 90-day notice, no penalty (after month 6)
  - Multi-year: Annual breakpoints (after year 1)

  Data Export:
    - 60 days to export all capsules (included)
    - Format: JSON, CSV, SQL dump
    - Verification scripts included
```

**Honest assessment:**
> Standard pricing is straightforward. Enterprise pricing (multi-region, multi-tenant, custom SLA) gets quoted separately. All price caps are contractual.

---

## Q2.3: Can we speak to a reference customer before committing?

**Current Status:**

> **UATP has no customers yet.** You would be the first (or among the first). We cannot provide customer references.

**What We CAN Provide:**

**1. Technical Demonstration:**
```
Available Now:
  - Live demo (end-to-end system working)
  - Run demo_audit_artifacts.py (see actual output)
  - Review generated audit reports (sample data)
  - Cryptographic verification in action
  - Test in your environment during pilot
```

**2. Code Review:**
```
Available for Due Diligence:
  - Full codebase review (363 production modules)
  - Architecture deep dive (engineering team)
  - Security review (cryptographic implementation)
  - Performance benchmarks
  - Test coverage reports (71%)
```

**3. Proof of Concept:**
```
During Pilot:
  - You'll BE the reference case
  - 90 days to validate everything
  - No payment until you see it working
  - If it doesn't work, clean exit with data
```

**4. After Your Pilot:**
```
If It Works:
  - We'll ask if you're willing to be a reference
  - Options: Anonymous case study, public, calls
  - Incentive: 10% discount on year 1

First Customer Benefits:
  - Priority roadmap input
  - Early access to features
  - Co-marketing opportunities
  - "First customer" positioning
```

**Honest assessment:**
> We have zero customers. If you need 3+ production references with multi-year track records, we can't provide that. But if you want first-mover advantage and are willing to validate during a 90-day pilot, that's the opportunity. You take the risk of being first, with the upside of shaping the product and favorable terms.

---

## Q2.4: If we decide UATP isn't right for us, what's the offboarding plan?

**Offboarding Process:**

**Step 1: Decision to Offboard (Day 0)**
```
Notice Period:
  - Pilot: 30 days
  - Annual: 90 days
  - No penalties

Method:
  - Email to account manager
  - Or: In-product "Initiate Offboarding" button
```

**Step 2: Data Export (Days 1-30)**
```
Export Options:

Option A: Full Database Dump
  - PostgreSQL dump of all capsules
  - Includes: Signatures, policies, audit logs
  - Format: SQL dump (gzipped)
  - Size: Typically 10-500 GB

Option B: JSON Export
  - One JSON file per capsule chain
  - Organized by workflow/date
  - Includes: Verification scripts

Option C: CSV Export
  - Flattened for other systems
  - Metadata, policy results, timestamps

Option D: API Access
  - Keep API for 60 days post-termination
  - Fetch programmatically
  - Rate limits relaxed for bulk export
```

**Step 3: Verification Scripts (Days 1-30)**
```
Independent Verification:
  - Standalone verification tool provided
  - Verifies signatures WITHOUT UATP backend
  - Open source (MIT license)
  - Runs on your infrastructure

Example:
  $ uatp-verify --export-file capsules.json --check-signatures

  Output:
    ✅ 45,892 capsules verified
    ✅ All signatures valid
    ✅ Chain integrity intact
    ✅ No UATP backend required
```

**Step 4: Storage Cleanup (Days 31-60)**
```
Deletion Options:

Option 1: Delete Immediately
  - Secure overwrite (DoD standard)
  - Deletion certificate provided

Option 2: Archive for 1 Year
  - Read-only archive
  - $500/month fee
  - Slow migration option

Option 3: Transfer to Your Infrastructure
  - Deploy UATP on your servers (self-hosted)
  - One-time migration: $10K
  - You operate, we assist
```

**Step 5: Termination Certificate (Day 60)**
```
Final Deliverables:
  ✅ Data export complete (verified)
  ✅ Deletion certificate (if requested)
  ✅ Final invoice (prorated)
  ✅ Offboarding report

  Optional: Exit interview to improve UATP
```

**Contractual Protections:**
```
Offboarding Guarantees (In MSA):
  - No data hostage: Full export, period
  - No format lock-in: JSON/CSV/SQL (standard)
  - No ransom fees: Export included
  - No forced retention: Delete on request
  - No post-termination charges (except archival)
```

**Self-Hosted Option:**
```
UATP Open Core:
  - Core engine: Open source (GitHub)
  - Self-host after termination
  - Migration assistance (paid)
  - Lose: Managed service, support, updates
  - Keep: All functionality, data, control
```

**Why Offboarding Might Happen:**
```
Anticipated Reasons (No Customer Data Yet):
  1. "Too early for us" → Market timing
  2. "Integration too complex" → Implementation challenges
  3. "Cost not justified yet" → ROI timing
  4. "Regulatory requirements changed" → External factors
  5. "Built in-house alternative" → Make vs. buy

Note: No actual offboarding experience (no customers yet).
These are anticipated based on enterprise software patterns.
```

**Honest assessment:**
> We want satisfied customers, not hostages. If UATP doesn't work, we'll help you leave cleanly. No data lock-in, no vendor hostage tactics. Our bet: if we're good, you'll stay or return.

---


## 3. Product Experience


### Q3.1: Is there a dashboard for searching chains, verifying signatures, and generating reports?

**Yes.** UATP includes a web-based dashboard for operations, compliance, and audit teams.

**Dashboard Features:**

**1. Chain Search & Exploration:**
```
Search Interface:
  - Full-text search across capsule content
  - Filter by: date range, workflow, user, AI provider, policy result
  - Saved searches for common queries
  - Export results to CSV/JSON

Example Query:
  workflow:"patient-triage"
  AND policy_result:FAIL
  AND date:[2025-10-01 TO 2025-10-26]

  → Results: 23 policy violations in October
```

**2. Chain Visualization:**
```
Interactive Graph View:
  - Timeline view (horizontal flow of capsules)
  - Merkle tree view (cryptographic structure)
  - Policy check annotations (green=pass, red=fail)
  - Click any capsule → drill into full details

Visual Elements:
  🟢 INPUT_PERSPECTIVE
    ↓
  🟢 POLICY_CHECK (HIPAA) ✅
    ↓
  🟢 ETHICS_EVALUATION ✅
    ↓
  🟢 REASONING_CHAIN
    ↓
  🟢 OUTPUT_DECISION
    ↓
  🔒 Signature: VALID (Dilithium3)
```

**3. Signature Verification Tool:**
```
Bulk Verification:
  - Select date range or chain_id
  - Click "Verify All Signatures"
  - Progress bar shows real-time verification
  - Report generation at completion

Results Display:
  ✅ 1,245 of 1,245 signatures valid
  ✅ Chain integrity: INTACT
  ⚠️  3 capsules flagged for review (unusual timestamps)

  Download: verification_report_2025-10-26.pdf
```

**4. Report Generation:**
```
Report Templates:
  - Compliance Report (HIPAA/GDPR/EU AI Act)
  - Audit Trail Report (for regulators)
  - Incident Investigation Report
  - Monthly Summary Report
  - Custom Report Builder

Generation Options:
  - Format: PDF, HTML, JSON, CSV
  - Audience: Technical, Executive, Legal, Auditor
  - Scope: Single chain, workflow, date range, entire system
  - Delivery: Download, email, S3 upload, API webhook
```

**5. Real-Time Monitoring:**
```
Live Dashboard:
  - Active chains (last 24 hours)
  - Policy violation rate (%)
  - Circuit breaker triggers
  - Average chain latency
  - Signature verification status
  - Storage usage trends

Alerts:
  🔴 Circuit breaker triggered (workflow: patient-triage)
  🟠 Policy violation rate spike: 2.3% → 8.7%
  🟡 Disk usage: 85% (consider scaling storage)
```

**6. User Management:**
```
RBAC Integration:
  - Admin: Full access to all chains and reports
  - Auditor: Read-only access, report generation
  - Developer: Access to dev/staging chains only
  - Compliance Officer: Policy management, violation review

Audit Log:
  - Every dashboard action logged
  - "Who viewed which chain when" tracking
  - Export audit logs for external review
```

**Access Methods:**
- **Web UI:** `https://uatp-dashboard.yourcompany.com`
- **API:** Full REST API for programmatic access
- **CLI:** `uatp dashboard --chain-id abc-123 --report`

**Screenshot Walkthrough:**
*(In production deployment, we provide video tutorials and interactive demos)*

**Honest Assessment:**
> The dashboard is functional and covers core use cases, but it's not as polished as commercial BI tools like Tableau. For power users, we recommend using the API + your preferred viz tool (Grafana, Looker, etc.). We provide pre-built Grafana dashboards.

---

### Q3.2: Can we set up alerting on policy violations, refusals, or tamper detection?

**Yes.** UATP integrates with standard alerting platforms and provides webhook/email notifications.

**Alerting Configuration:**
```yaml
Alerts:
  - alert_id: "policy-violation-spike"
    description: "Policy violation rate exceeds threshold"

    trigger:
      metric: "policy_violation_rate"
      condition: "> 5%"
      window: "5 minutes"
      aggregation: "average"

    severity: "HIGH"

    actions:
      - type: "email"
        recipients: ["compliance@company.com", "security@company.com"]
        subject: "ALERT: Policy violation rate spike detected"

      - type: "slack"
        webhook: "https://hooks.slack.com/services/T00/B00/XXX"
        channel: "#uatp-alerts"

      - type: "pagerduty"
        integration_key: "R12345"
        severity: "error"

      - type: "webhook"
        url: "https://your-siem.com/ingest"
        method: "POST"
        headers:
          Authorization: "Bearer ${SIEM_TOKEN}"

  - alert_id: "circuit-breaker-triggered"
    description: "Circuit breaker opened (AI requests blocked)"

    trigger:
      event: "circuit_breaker_opened"
      workflow: "*"  # Any workflow

    severity: "CRITICAL"

    actions:
      - type: "pagerduty"
        integration_key: "R12345"
        severity: "critical"
      - type: "email"
        recipients: ["oncall@company.com"]

  - alert_id: "signature-verification-failure"
    description: "Tamper detection: Invalid signature found"

    trigger:
      event: "signature_verification_failed"
      chain_id: "*"

    severity: "CRITICAL"

    actions:
      - type: "security_incident"
        playbook: "tamper-response-v2"
        escalate_immediately: true
      - type: "email"
        recipients: ["security@company.com", "legal@company.com"]
      - type: "freeze_chain"  # Stop writing to potentially compromised chain

  - alert_id: "refusal-rate-anomaly"
    description: "Refusal rate deviates from baseline"

    trigger:
      metric: "refusal_rate"
      condition: "anomaly_detection"  # ML-based anomaly detection
      baseline_window: "7 days"
      sensitivity: "medium"

    severity: "MEDIUM"

    actions:
      - type: "slack"
        channel: "#uatp-monitoring"
        message: "Refusal rate anomaly detected. Investigate?"
```

**Alert Notification Example (Slack):**
```
🔴 UATP ALERT: Policy Violation Spike

Workflow: patient-triage
Metric: policy_violation_rate
Current Value: 8.7%
Threshold: > 5%
Duration: 7 minutes

Recent Violations:
  - hipaa_consent: 12 failures (last 5 min)
  - data_minimization: 8 failures (last 5 min)

Actions:
  🔍 View Dashboard: https://uatp.company.com/chains?filter=violations
  📊 Generate Report: /uatp report --workflow patient-triage --last 1h
  🛑 Circuit Breaker: /uatp circuit-breaker open --workflow patient-triage

Acknowledged by: @security-oncall
```

**Integration Options:**
```yaml
Supported Platforms:
  - Email (SMTP)
  - Slack (webhook)
  - PagerDuty (Events API v2)
  - Microsoft Teams (webhook)
  - OpsGenie
  - VictorOps
  - Splunk (HEC)
  - Datadog (Events API)
  - Custom webhook (generic HTTP POST)
```

**Alert Tuning:**
```yaml
Alert Tuning:
  # Reduce alert fatigue
  aggregation:
    - type: "rate_limit"
      max_per_hour: 10  # Don't spam

    - type: "deduplication"
      window: "5 minutes"  # Same alert → group

    - type: "quiet_hours"
      schedule: "weekdays 00:00-06:00"  # Batch non-critical alerts
      exceptions: ["CRITICAL"]
```

**Escalation Policies:**
```yaml
Escalation:
  - severity: "CRITICAL"
    immediate: ["security-oncall", "compliance-lead"]
    if_no_ack_after: "5 minutes"
    escalate_to: ["CISO", "CTO"]

  - severity: "HIGH"
    immediate: ["compliance-oncall"]
    if_no_ack_after: "15 minutes"
    escalate_to: ["compliance-lead"]

  - severity: "MEDIUM"
    immediate: ["uatp-ops"]
    if_no_ack_after: "1 hour"
    escalate_to: ["engineering-manager"]
```

**Honest Assessment:**
> Alerting works and integrates with standard platforms, but alert tuning will likely require trial and error (standard for any monitoring system). You should expect to adjust thresholds in the first 30 days to reduce false positives. We provide "starter templates" based on industry standards, but every org's baseline is different.

---

### Q3.3: Are there pre-built template packs (HIPAA, GDPR, PCI, EU AI Act)?

**Yes.** UATP includes policy template packs for common regulatory frameworks.

**Available Template Packs:**

**1. HIPAA Template Pack:**
```yaml
HIPAA Template Pack (18 CFR Part 164):

  Policies Included:
    - hipaa_phi_access_control (§164.312(a)(1))
    - hipaa_audit_controls (§164.312(b))
    - hipaa_integrity_controls (§164.312(c)(1))
    - hipaa_transmission_security (§164.312(e)(1))
    - hipaa_minimum_necessary (§164.502(b))
    - hipaa_consent_verification (§164.508)
    - hipaa_breach_notification (§164.404)

  Refusal Mechanisms:
    - Block PHI access without consent token
    - Block PHI transmission outside secure channels
    - Block disclosure exceeding minimum necessary

  Audit Requirements:
    - Log all PHI access attempts
    - Capture consent tokens in capsules
    - Generate compliance reports (quarterly)

  Documentation:
    - Policy intent and legal basis
    - Implementation guide
    - Testing checklist
    - Sample audit reports
```

**2. GDPR Template Pack:**
```yaml
GDPR Template Pack (Regulation (EU) 2016/679):

  Policies Included:
    - gdpr_lawful_basis (Art. 6)
    - gdpr_consent_management (Art. 7)
    - gdpr_data_minimization (Art. 5(1)(c))
    - gdpr_purpose_limitation (Art. 5(1)(b))
    - gdpr_accuracy (Art. 5(1)(d))
    - gdpr_automated_decision_making (Art. 22)
    - gdpr_data_portability (Art. 20)
    - gdpr_right_to_erasure (Art. 17)

  Refusal Mechanisms:
    - Block processing without lawful basis
    - Block automated decisions on sensitive categories
    - Block cross-border transfers without adequacy

  Audit Requirements:
    - Record of processing activities (Art. 30)
    - Data protection impact assessments (Art. 35)
    - Consent audit trail

  Documentation:
    - GDPR compliance mapping
    - DPA (Data Processing Agreement) template
    - DPIA (Data Protection Impact Assessment) template
```

**3. EU AI Act Template Pack:**
```yaml
EU AI Act Template Pack (Regulation (EU) 2024/...):

  Policies Included:
    - ai_act_risk_classification
    - ai_act_transparency_obligations (Art. 13)
    - ai_act_human_oversight (Art. 14)
    - ai_act_accuracy_robustness (Art. 15)
    - ai_act_record_keeping (Art. 12)
    - ai_act_bias_mitigation (Art. 10)

  Refusal Mechanisms:
    - Block high-risk AI without human oversight
    - Block AI decisions on protected characteristics (without justification)
    - Block deployment without conformity assessment

  Audit Requirements:
    - Automatic logging of AI decisions (Art. 12)
    - Adversarial testing results
    - Bias testing reports

  Documentation:
    - EU AI Act compliance checklist
    - Technical documentation template (Annex IV)
    - Conformity assessment guide
```

**4. PCI DSS Template Pack:**
```yaml
PCI DSS Template Pack (Payment Card Industry Data Security Standard):

  Policies Included:
    - pci_cardholder_data_protection (Req. 3)
    - pci_access_control (Req. 7)
    - pci_monitoring_testing (Req. 10, 11)
    - pci_encryption_in_transit (Req. 4)

  Refusal Mechanisms:
    - Block unencrypted cardholder data transmission
    - Block access without MFA for privileged users

  Audit Requirements:
    - Daily log reviews (Req. 10.6)
    - Quarterly vulnerability scans

  Documentation:
    - PCI compliance mapping (12 requirements)
    - AOC (Attestation of Compliance) support docs
```

**Installation:**
```bash
# Install a template pack
$ uatp templates install --pack hipaa --version 2024.1

Output:
  ✅ Installed 7 policies
  ✅ Installed 3 refusal mechanisms
  ✅ Installed 4 audit report templates
  📄 Documentation: ./docs/hipaa-template-pack.md

# Customize for your org
$ uatp templates customize \
    --policy hipaa_consent_verification \
    --set consent_token_header="X-Patient-Consent" \
    --set consent_expiry_days=90

# Test policies before deploying
$ uatp templates test --pack hipaa --mode shadow

Output:
  Testing 7 policies in shadow mode...
  ✅ hipaa_phi_access_control: 1,234 checks, 0 false positives
  ✅ hipaa_consent_verification: 892 checks, 12 expected refusals
  ⚠️  hipaa_minimum_necessary: 456 checks, 34 potential false positives

  Recommendation: Tune hipaa_minimum_necessary threshold before enforcement
```

**Template Customization:**
```yaml
# Example: Customize HIPAA consent policy
policy:
  name: "hipaa_consent_verification"
  base_template: "hipaa/consent"  # Inherit from template

  # Override defaults
  overrides:
    consent_token_header: "X-Acme-Consent"  # Our custom header
    consent_token_format: "jwt"  # Instead of opaque token
    consent_expiry_days: 180  # Longer than default 90

  # Add custom checks
  additional_checks:
    - name: "check_consent_scope"
      condition: "consent_scope includes 'ai_triage'"
      error: "Consent doesn't cover AI triage usage"
```

**Template Updates:**
```bash
# Get notified of regulatory changes
$ uatp templates subscribe --pack hipaa --channel email

# Update to latest version
$ uatp templates update --pack hipaa

Output:
  New version available: 2024.2 (2024.1 → 2024.2)

  Changes:
    - Updated for 2024 HIPAA Omnibus Rule changes
    - Added breach notification updates (164.404)
    - Clarified minimum necessary standard

  Breaking changes: NONE
  Recommended action: Update and test in shadow mode

  Apply update? [y/N]: y
```

**Honest Assessment:**
> Template packs give you 80% of compliance out of the box, but you still need legal review for your specific use case. Think of them as "smart defaults" not "legal certainty." Always have your counsel review before production deployment.

---

### Q3.4: Is there onboarding documentation, runbooks, and training available?

**Yes.** UATP provides comprehensive documentation and training materials.

**Documentation Structure:**

**1. Getting Started Guide (2 hours):**
```
Getting Started:
  ├─ Quickstart (15 min): Install SDK, create first capsule
  ├─ Architecture Overview (30 min): How UATP works
  ├─ Integration Tutorial (45 min): Integrate with your AI app
  └─ First Policy Deployment (30 min): Deploy HIPAA template in shadow mode
```

**2. Operator Runbooks:**
```
Runbooks (incident response):
  ├─ Policy Violation Spike
  │   └─ Diagnosis: Check dashboard → Review recent changes → Identify root cause
  │   └─ Mitigation: Adjust threshold vs. rollback policy vs. circuit breaker
  │
  ├─ Circuit Breaker Triggered
  │   └─ Diagnosis: Why? (High error rate, policy failures, signature issues)
  │   └─ Mitigation: Fix root cause → Manual reset → Monitor recovery
  │
  ├─ Signature Verification Failure
  │   └─ Diagnosis: Tamper vs. clock skew vs. key rotation issue
  │   └─ Mitigation: Security incident protocol → Isolate chain → Forensics
  │
  ├─ Storage Capacity Alert
  │   └─ Diagnosis: Growth rate, retention policy compliance
  │   └─ Mitigation: Scale storage vs. adjust retention vs. archive
  │
  └─ Performance Degradation
      └─ Diagnosis: Database slow vs. signature overhead vs. traffic spike
      └─ Mitigation: Scaling playbook (add replicas, cache tuning, etc.)
```

**3. Training Materials:**
```
Training Resources:
  ├─ Video Library (YouTube/private portal)
  │   ├─ "UATP in 5 Minutes" (overview)
  │   ├─ "Policy Creation Workshop" (45 min)
  │   ├─ "Dashboard Deep Dive" (30 min)
  │   ├─ "Troubleshooting Common Issues" (60 min)
  │   └─ "Advanced: Cryptographic Verification" (90 min)
  │
  ├─ Interactive Tutorials (in-product)
  │   ├─ Create your first policy (guided)
  │   ├─ Investigate a policy violation (simulated)
  │   ├─ Generate an audit report (step-by-step)
  │   └─ Respond to a tamper alert (drill)
  │
  ├─ Certification Program (optional)
  │   ├─ UATP Operator Certification (8 hours)
  │   ├─ UATP Policy Administrator Certification (16 hours)
  │   └─ UATP Security Auditor Certification (24 hours)
  │
  └─ Office Hours & Support
      ├─ Weekly Q&A sessions (Zoom)
      ├─ Slack workspace (#uatp-support)
      ├─ Ticketing system (for pilot customers)
      └─ Dedicated CSM (Customer Success Manager) for enterprise
```

**4. Developer Documentation:**
```
Developer Docs (https://docs.uatp.dev):
  ├─ API Reference (OpenAPI spec)
  ├─ SDK Documentation (Python, Node.js, Java, Go)
  ├─ Integration Guides (OpenAI, Anthropic, Vertex, Bedrock, Azure)
  ├─ Policy DSL Reference (YAML syntax)
  ├─ Cryptography Explainer (for security teams)
  ├─ Performance Tuning Guide
  ├─ Troubleshooting FAQ
  └─ Code Examples (GitHub repo with 50+ examples)
```

**5. Compliance Documentation:**
```
Compliance Resources:
  ├─ HIPAA Compliance Guide (30 pages)
  ├─ GDPR Compliance Guide (45 pages)
  ├─ EU AI Act Readiness Guide (60 pages)
  ├─ SOC 2 Mapping Document
  ├─ ISO 27001 Mapping Document
  └─ Sample Audit Reports (what regulators expect)
```

**Onboarding Process (For Pilot Customers):**
```
Week 1: Orientation
  Day 1: Kickoff call (goals, scope, timeline)
  Day 2: Architecture review (your environment)
  Day 3: Install UATP in staging
  Day 4: Create first test capsules
  Day 5: Deploy first policy (shadow mode)

Week 2-3: Integration
  Week 2: Integrate UATP with your AI workflows
  Week 3: Deploy template packs, customize policies

Week 4: Testing
  - Shadow mode testing (no enforcement)
  - Review false positive rate
  - Tune policies

Week 5-8: Gradual Rollout
  - Enable enforcement on 10% traffic
  - Monitor, tune, increase to 50%
  - Full enforcement by end of week 8

Week 9-12: Operationalization
  - Train your team
  - Set up alerting
  - Generate first audit reports
  - Deliver pilot results
```

**Support Tiers:**
```
Support Tiers:
  - Pilot: Dedicated CSM, weekly check-ins, Slack access
  - Standard: Email support (24-hour response SLA)
  - Premium: 24/7 phone support, 4-hour response SLA
  - Enterprise: Dedicated technical account manager, custom runbooks
```

**Honest Assessment:**
> Documentation exists and is comprehensive, but we haven't had customers test it in production yet. Some advanced topics (like custom crypto key rotation) have "coming soon" placeholders. If you hit an undocumented edge case during pilot, we'll write the doc with you in real-time.

---


## 4. Integration Surface


### Q4.1: Full matrix of supported providers & features: OpenAI/Anthropic/Vertex/Azure, streaming, tool/function-calling, images, RAG, batch APIs?

**A: Comprehensive provider support with feature matrix:**

**Supported AI Providers:**

**OpenAI (Full Support ✅)**
```yaml
Models Supported:
  ✅ GPT-4, GPT-4 Turbo, GPT-4o
  ✅ GPT-3.5 Turbo
  ✅ o1, o1-mini (reasoning models)
  ✅ DALL-E 3 (image generation)
  ✅ Whisper (speech-to-text)
  ✅ TTS (text-to-speech)

Features:
  ✅ Chat completions (standard)
  ✅ Streaming responses
  ✅ Function calling / Tools
  ✅ Vision (image inputs)
  ✅ JSON mode
  ✅ Embeddings (text-embedding-3)
  ✅ Batch API
  ✅ Fine-tuned models

UATP Capsule Coverage:
  ✅ Input capsule: Captures prompt, function definitions, images
  ✅ Tool call capsules: Each function call gets own capsule
  ✅ Output capsule: Captures response (streaming or complete)
  ✅ Vision capsule: Captures image analysis requests
  ✅ Batch capsule: Special handling for batch jobs
```

**Anthropic (Full Support ✅)**
```yaml
Models Supported:
  ✅ Claude 3.5 Sonnet
  ✅ Claude 3 Opus
  ✅ Claude 3 Haiku
  ✅ Claude 2.1

Features:
  ✅ Messages API (standard)
  ✅ Streaming responses
  ✅ Tool use (function calling)
  ✅ Vision (image inputs)
  ✅ Extended context (200K tokens)
  ✅ Prompt caching

UATP Capsule Coverage:
  ✅ Full coverage (same as OpenAI)
  ✅ Tool use: Each tool invocation captured
  ✅ Vision: Image analysis documented
  ✅ Caching: Cache usage logged (for attribution)
```

**Google Vertex AI (Beta ✅)**
```yaml
Models Supported:
  ✅ Gemini 1.5 Pro
  ✅ Gemini 1.5 Flash
  ✅ PaLM 2
  ✅ Codey (code generation)

Features:
  ✅ Chat / Generate content
  ✅ Streaming responses
  ✅ Function calling
  ✅ Multi-modal (text, image, video)
  ⚠️  Batch API (limited support)

UATP Capsule Coverage:
  ✅ Standard chat/completion
  ✅ Streaming
  ✅ Function calling
  ⏳ Video inputs (in progress, Q1 2026)
```

**Azure OpenAI (Full Support ✅)**
```yaml
Models Supported:
  ✅ All OpenAI models (via Azure)
  ✅ Azure-specific deployments

Features:
  ✅ Same as OpenAI (full feature parity)
  ✅ Azure AD authentication
  ✅ Private endpoints (VNet integration)
  ✅ Managed identity support

UATP Capsule Coverage:
  ✅ Full coverage (same as OpenAI)
  ✅ Azure-specific: Managed identity logged in attribution
```

**AWS Bedrock (Beta ✅)**
```yaml
Models Supported:
  ✅ Claude (via Bedrock)
  ✅ Titan
  ✅ Llama 2/3
  ✅ Jurassic-2

Features:
  ✅ Invoke model (standard)
  ✅ Streaming
  ⚠️  Function calling (model-dependent)

UATP Capsule Coverage:
  ✅ Standard invocations
  ✅ Streaming
  ⏳ Advanced features (in progress)
```

**Self-Hosted Models (Experimental ⏳)**
```yaml
Supported:
  ⏳ Llama 2/3 (via vLLM, TGI)
  ⏳ Mistral
  ⏳ Custom models via OpenAI-compatible API

Status: Experimental (Q1 2026 for production support)

Integration:
  - If your model exposes OpenAI-compatible API: Works today
  - Custom protocols: Requires adapter (we can help build)
```

---

**Feature Support Matrix:**

| Feature | OpenAI | Anthropic | Vertex AI | Azure OpenAI | Bedrock |
|---------|--------|-----------|-----------|--------------|---------|
| **Chat completions** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Streaming** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Function calling** | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **Tool use** | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **Vision (images)** | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **JSON mode** | ✅ | ⏳ | ✅ | ✅ | ⚠️ |
| **Embeddings** | ✅ | ⏳ | ✅ | ✅ | ✅ |
| **Batch API** | ✅ | ⏳ | ⚠️ | ✅ | ⚠️ |
| **Fine-tuned models** | ✅ | ⏳ | ✅ | ✅ | ✅ |

Legend:
- ✅ Full support (production-ready)
- ⚠️ Partial support (works, may have limitations)
- ⏳ In progress (planned for Q1 2026)

---

**Streaming Support (Detailed):**

```yaml
How UATP Handles Streaming:

Server-Sent Events (SSE):
  1. Your app requests streaming response
  2. UATP creates input capsule (immediate)
  3. UATP forwards request to AI provider (streaming enabled)
  4. AI provider streams chunks back
  5. UATP passes chunks through to your app (transparent)
  6. UATP buffers complete response in background
  7. Once stream complete: Create output capsule (final response)

Capsule Created:
  {
    "capsule_type": "OUTPUT",
    "streaming": true,
    "chunk_count": 47,
    "first_chunk_latency_ms": 234,
    "total_latency_ms": 3456,
    "complete_response": "full text after streaming complete"
  }

User Experience:
  ✅ No additional latency (streaming works normally)
  ✅ Capsule created after stream completes (doesn't block streaming)

Performance:
  ✅ Streaming overhead: <5ms (passthrough)
  ✅ Capsule creation: Async (doesn't slow stream)
```

**Function Calling / Tool Use:**

```yaml
How UATP Captures Tool Calls:

Example: AI uses weather tool

Flow:
  1. User: "What's the weather in SF?"
  2. Input capsule: User query captured
  3. AI decides: Need to call weather tool
  4. Tool call capsule:
     {
       "tool_name": "get_weather",
       "arguments": {"location": "San Francisco"},
       "timestamp": "2025-10-26T14:30:00Z"
     }
  5. Your app executes: Calls actual weather API
  6. Tool result capsule:
     {
       "tool_name": "get_weather",
       "result": {"temp": 65, "conditions": "sunny"},
       "execution_time_ms": 234
     }
  7. AI receives tool result, generates final response
  8. Output capsule: Final answer captured

Chain:
  Input → Tool Call → Tool Result → Output
  (All linked cryptographically)

Benefits:
  ✅ Complete audit trail (can see which tools AI used)
  ✅ Tool execution time tracked (performance debugging)
  ✅ Tool results verified (can replay tool calls)
```

**Vision / Image Inputs:**

```yaml
How UATP Handles Images:

Scenario: Analyze medical image

Input:
  - User prompt: "What do you see in this X-ray?"
  - Image: chest_xray.jpg (2.3 MB)

UATP Processing:
  1. Hash image: sha256(image_bytes)
  2. Store image hash (not image itself)
  3. Optional: Store image in your S3 (you control retention)
  4. Capsule includes:
     {
       "input_type": "multimodal",
       "text": "What do you see in this X-ray?",
       "images": [
         {
           "format": "jpeg",
           "size_bytes": 2400000,
           "hash": "sha256:abc123...",
           "storage_ref": "s3://your-bucket/images/xyz.jpg",  # Optional
           "phi_detected": true  # If medical image
         }
       ]
     }

Privacy:
  ✅ Image content NOT stored in capsule (only hash)
  ✅ Image stored in YOUR S3 (you control access)
  ✅ HIPAA compliance maintained (PHI never in capsule DB)

Verification:
  - Provide image + capsule
  - Recompute hash
  - Verify: Hash matches capsule hash ✅
```

**RAG (Retrieval-Augmented Generation):**

```yaml
UATP Integration with RAG Systems:

Architecture:
  User Query → RAG System → AI Provider
               ↓
           UATP Proxy (captures everything)

Capsules Created:
  1. Input capsule: Original user query
  2. Retrieval capsule:
     {
       "retrieved_chunks": [
         {
           "source_doc": "document_id_123",
           "chunk_id": "chunk_45",
           "relevance_score": 0.87,
           "content_hash": "sha256:...",  # Not actual content
           "storage_ref": "vectordb://pinecone/doc123"
         }
       ],
       "retrieval_latency_ms": 124
     }
  3. Augmented prompt capsule:
     {
       "original_query": "What is HIPAA?",
       "augmented_prompt": "[original + retrieved context]",
       "context_source_count": 3
     }
  4. Output capsule: AI's final response

Benefits:
  ✅ Can audit: Which documents were used
  ✅ Can verify: Retrieval quality (relevance scores)
  ✅ Can debug: Why AI gave this answer (see retrieved context)

Integration:
  - Works with: LangChain, LlamaIndex, Haystack
  - Custom RAG: Adapter available (30 minutes to integrate)
```

**Batch API Support:**

```yaml
OpenAI Batch API:

How It Works:
  1. Submit batch file (JSONL with 1000s of requests)
  2. OpenAI processes asynchronously (hours later)
  3. Download results file

UATP Integration:
  1. Batch submission capsule:
     {
       "batch_id": "batch_abc123",
       "request_count": 10000,
       "submitted_at": "2025-10-26T14:30:00Z"
     }
  2. Individual request capsules:
     - Option A: Create 10,000 capsules immediately (from batch file)
     - Option B: Create capsules when results available (lazy)
  3. Batch completion capsule:
     {
       "batch_id": "batch_abc123",
       "completed_at": "2025-10-26T20:15:00Z",
       "success_count": 9987,
       "failed_count": 13,
       "results_file": "s3://your-bucket/results/batch_abc123.jsonl"
     }

Configuration:
  - Eager mode: Create all capsules upfront (more storage, immediate audit)
  - Lazy mode: Create capsules on-demand (less storage, delayed audit)

Recommendation: Lazy mode for large batches (>1K requests)
```

---

### Q4.2: Non-Python stacks before JS GA: gRPC/REST shim examples, Terraform/Helm modules, sidecar for serverless?

**A: Multiple options for non-Python environments:**

**gRPC Integration (Available Now):**

```yaml
UATP gRPC API:

Service Definition (Protobuf):
  service UATPService {
    rpc CreateCapsule(CreateCapsuleRequest) returns (CreateCapsuleResponse);
    rpc VerifyChain(VerifyChainRequest) returns (VerifyChainResponse);
    rpc GenerateAuditReport(AuditRequest) returns (AuditResponse);
  }

Supported Languages (via gRPC):
  ✅ Java
  ✅ C++
  ✅ C#
  ✅ Go
  ✅ Ruby
  ✅ PHP
  ✅ Any language with gRPC support

Example (Go):
  import "uatp/proto/capsule"

  client := capsule.NewUATPServiceClient(conn)
  resp, err := client.CreateCapsule(ctx, &capsule.CreateCapsuleRequest{
      WorkflowId: "patient-triage",
      Content: &capsule.CapsuleContent{
          Type: "INPUT_PERSPECTIVE",
          Data: inputData,
      },
  })

Latency: +2-5ms (gRPC serialization overhead)
Status: Production-ready
```

**REST API (Available Now):**

```yaml
UATP REST API:

Base URL: https://api.uatp.com/v1

Endpoints:
  POST /capsules              # Create capsule
  GET /capsules/{id}          # Retrieve capsule
  GET /chains/{workflow_id}   # Get capsule chain
  POST /audit/generate        # Generate audit report
  GET /audit/reports/{id}     # Download audit report

Authentication:
  - Bearer token: Authorization: Bearer your-api-key
  - Or: API key header: X-UATP-API-Key: your-api-key

Example (curl):
  curl -X POST https://api.uatp.com/v1/capsules \
    -H "Authorization: Bearer your-api-key" \
    -H "Content-Type: application/json" \
    -d '{
      "workflow_id": "patient-triage",
      "capsule_type": "INPUT_PERSPECTIVE",
      "content": {
        "query": "What is the diagnosis?",
        "user_id": "user_12345"
      }
    }'

Response:
  {
    "capsule_id": "cap_abc123",
    "hash": "sha256:def456...",
    "signature": "dilithium3:ghi789...",
    "timestamp": "2025-10-26T14:30:00Z"
  }

Supported by: Any HTTP client (cURL, fetch, axios, requests, etc.)
```

**Sidecar Proxy for Serverless (AWS Lambda, GCP Functions, Azure Functions):**

```yaml
Problem: Serverless functions are stateless, short-lived

Solution: UATP Sidecar Extension

AWS Lambda Example:

Architecture:
  Lambda Function → UATP Lambda Extension → OpenAI

Deployment:
  1. Add UATP Lambda layer:
     aws lambda update-function-configuration \
       --function-name my-ai-function \
       --layers arn:aws:lambda:us-east-1:123456:layer:uatp-extension:1

  2. Configure via environment variables:
     UATP_API_KEY=your-api-key
     UATP_WORKFLOW_ID=serverless-workflow
     OPENAI_API_KEY=your-openai-key

  3. Your Lambda code (unchanged):
     from openai import OpenAI
     client = OpenAI()  # UATP extension intercepts automatically
     response = client.chat.completions.create(...)

How It Works:
  - UATP extension runs alongside your Lambda
  - Intercepts HTTP requests to api.openai.com
  - Creates capsules, forwards request
  - Writes capsules to DynamoDB or S3 (not to Lambda's ephemeral storage)

Supported Platforms:
  ✅ AWS Lambda (via Lambda Extensions)
  ✅ GCP Cloud Functions (via buildpack)
  ✅ Azure Functions (via custom runtime)

Performance Overhead:
  - Cold start: +50-100ms (extension initialization)
  - Warm execution: +10-20ms (same as sidecar)

Cost:
  - Lambda execution time: ~+50ms per invocation
  - Storage: DynamoDB/S3 writes (minimal, <$0.01 per 1K capsules)
```

**Terraform Modules (Available Now):**

```yaml
UATP Terraform Module:

Repository: terraform-aws-uatp-deployment

Example Usage:
  module "uatp" {
    source  = "uatp/deployment/aws"
    version = "1.0.0"

    # Required
    cluster_name = "production-uatp"
    vpc_id       = "vpc-abc123"
    subnet_ids   = ["subnet-123", "subnet-456"]

    # Optional
    instance_type      = "r6i.xlarge"
    min_instances      = 2
    max_instances      = 10
    database_type      = "postgresql"
    database_instance  = "db.r6g.large"

    # Encryption
    kms_key_arn = "arn:aws:kms:us-east-1:123456:key/abc-def"

    # Monitoring
    enable_cloudwatch = true
    enable_prometheus = true

    # Compliance
    enable_audit_logs = true
    log_retention_days = 2555  # 7 years

    tags = {
      Environment = "production"
      Compliance  = "HIPAA"
    }
  }

  output "uatp_endpoint" {
    value = module.uatp.proxy_endpoint
  }

Creates:
  ✅ EKS cluster with UATP pods
  ✅ RDS PostgreSQL database
  ✅ Application Load Balancer
  ✅ Security groups
  ✅ IAM roles and policies
  ✅ CloudWatch dashboards
  ✅ Backup policies

Supported Cloud Providers:
  ✅ AWS (mature)
  ✅ GCP (mature)
  ✅ Azure (beta)
  ⏳ On-premises (coming Q1 2026)
```

**Helm Charts (Available Now):**

```yaml
UATP Helm Chart:

Repository: https://charts.uatp.com

Installation:
  helm repo add uatp https://charts.uatp.com
  helm repo update

  helm install my-uatp uatp/capsule-engine \
    --set postgresql.enabled=true \
    --set postgresql.auth.password=secure-password \
    --set proxy.replicas=3 \
    --set proxy.resources.requests.memory=1Gi \
    --set config.workflowId=production-workflow

values.yaml (Customization):
  proxy:
    replicas: 3
    image:
      repository: uatp/proxy
      tag: "1.3.0"
    resources:
      requests:
        cpu: "500m"
        memory: "1Gi"
      limits:
        cpu: "2000m"
        memory: "4Gi"

  postgresql:
    enabled: true
    auth:
      username: uatp
      password: "your-password"
      database: uatp_production
    primary:
      persistence:
        size: 100Gi

  config:
    enforcementMode: "block"
    policies:
      - name: "hipaa_consent"
        action: "block"
      - name: "gdpr_check"
        action: "warn"

  ingress:
    enabled: true
    className: "nginx"
    annotations:
      cert-manager.io/cluster-issuer: "letsencrypt-prod"
    hosts:
      - host: uatp.your-company.com
        paths:
          - path: /
            pathType: Prefix

Features:
  ✅ High availability (multi-replica)
  ✅ Auto-scaling (HPA)
  ✅ TLS/HTTPS (cert-manager integration)
  ✅ Monitoring (Prometheus, Grafana)
  ✅ Backup (velero integration)
```

**REST Shim for Legacy Systems:**

```yaml
Scenario: You have Java/C#/.NET app, can't modify code

Solution: UATP REST Proxy (HTTP-to-UATP bridge)

Deployment:
  1. Deploy UATP REST proxy (Docker container)
     docker run -d -p 8080:8080 \
       -e OPENAI_API_KEY=your-key \
       -e UATP_API_KEY=your-uatp-key \
       uatp/rest-proxy:latest

  2. Point your app to proxy instead of OpenAI:
     OLD: https://api.openai.com
     NEW: http://localhost:8080

  3. No code changes required

How It Works:
  Your App → REST Proxy (creates capsules) → OpenAI

Example (Java):
  // OLD CODE (unchanged):
  String openaiUrl = System.getenv("OPENAI_API_URL");  // Now points to UATP proxy
  HttpClient client = HttpClient.newHttpClient();
  HttpRequest request = HttpRequest.newBuilder()
      .uri(URI.create(openaiUrl + "/v1/chat/completions"))
      .header("Authorization", "Bearer " + openaiKey)
      .POST(HttpRequest.BodyPublishers.ofString(requestBody))
      .build();

  // UATP proxy intercepts, creates capsules, forwards to OpenAI
  // Your code doesn't know UATP exists!

Status: Available now (Docker image)
Performance: +15-25ms overhead (REST → UATP → OpenAI)
```

---

### Q4.3: Observability hooks: Prometheus metrics, OpenTelemetry traces, Splunk/Datadog dashboards "ready to import"?

**A: Comprehensive observability with pre-built dashboards:**

**Prometheus Metrics (Built-in):**

```yaml
UATP Metrics Exposed:

Endpoint: http://uatp-proxy:9090/metrics (Prometheus format)

Metrics Categories:

1. Request Metrics:
   uatp_requests_total{workflow="patient-triage",status="success"}
   uatp_request_duration_seconds{workflow="patient-triage",quantile="0.95"}
   uatp_requests_in_flight{workflow="patient-triage"}

2. Capsule Metrics:
   uatp_capsules_created_total{type="INPUT_PERSPECTIVE"}
   uatp_capsules_verified_total{result="valid"}
   uatp_capsule_creation_duration_seconds{type="OUTPUT"}

3. Policy Metrics:
   uatp_policy_checks_total{policy="hipaa_consent",result="pass"}
   uatp_circuit_breaker_trips_total{policy="hipaa_consent"}
   uatp_policy_check_duration_seconds{policy="hipaa_consent"}

4. Database Metrics:
   uatp_database_writes_total{status="success"}
   uatp_database_write_duration_seconds
   uatp_database_connection_pool_size{state="idle"}

5. AI Provider Metrics:
   uatp_upstream_requests_total{provider="openai",model="gpt-4"}
   uatp_upstream_latency_seconds{provider="openai",quantile="0.99"}
   uatp_upstream_errors_total{provider="openai",error_type="rate_limit"}

6. Chain Metrics:
   uatp_chain_length{workflow="patient-triage"}
   uatp_chain_verification_duration_seconds

Example Prometheus Query:
  # 95th percentile latency by workflow
  histogram_quantile(0.95,
    rate(uatp_request_duration_seconds_bucket[5m])
  ) by (workflow)
```

**OpenTelemetry Traces (Built-in):**

```yaml
UATP OpenTelemetry Integration:

Tracing Spans Created:

Root Span: HTTP Request
  ├─ Span: Policy Checks
  │   ├─ Span: HIPAA Consent Check
  │   └─ Span: GDPR Check
  ├─ Span: Input Capsule Creation
  │   ├─ Span: Hash Computation
  │   └─ Span: Signature Generation
  ├─ Span: Upstream AI Request (OpenAI)
  │   ├─ Span: HTTP Call
  │   └─ Span: Response Parsing
  ├─ Span: Output Capsule Creation
  └─ Span: Database Write

Span Attributes:
  - workflow_id: "patient-triage"
  - capsule_id: "cap_abc123"
  - policy_results: {"hipaa": "pass", "gdpr": "pass"}
  - upstream_provider: "openai"
  - upstream_model: "gpt-4"

Export Targets:
  ✅ Jaeger
  ✅ Zipkin
  ✅ Datadog APM
  ✅ New Relic
  ✅ Honeycomb
  ✅ AWS X-Ray
  ✅ Google Cloud Trace

Configuration:
  apiVersion: v1
  kind: ConfigMap
  metadata:
    name: uatp-otel-config
  data:
    OTEL_EXPORTER_OTLP_ENDPOINT: "http://jaeger:4318"
    OTEL_SERVICE_NAME: "uatp-proxy"
    OTEL_TRACES_SAMPLER: "parentbased_traceidratio"
    OTEL_TRACES_SAMPLER_ARG: "1.0"  # 100% sampling (adjust as needed)

Benefits:
  ✅ End-to-end request tracing (see where time is spent)
  ✅ Debugging: Identify slow policy checks, database writes
  ✅ Distributed tracing: Correlate with your app's traces
```

**Pre-Built Dashboards:**

**Grafana Dashboard (Import Ready):**

```yaml
Dashboard: UATP Operational Overview

JSON File: dashboards/uatp-operational-overview.json

Import:
  1. Download: curl -O https://uatp.com/dashboards/operational-overview.json
  2. Grafana UI: Dashboards → Import → Upload JSON
  3. Configure: Select Prometheus data source
  4. Done: Dashboard ready to use

Panels Included:

Row 1: Request Metrics
  - Requests/second (by workflow)
  - P50/P95/P99 latency
  - Error rate
  - Success rate

Row 2: Capsule Metrics
  - Capsules created/second
  - Capsule types distribution (pie chart)
  - Capsule creation latency
  - Database write latency

Row 3: Policy Enforcement
  - Policy checks/second
  - Policy results (pass/fail/block)
  - Circuit breaker trips
  - Policy check latency

Row 4: AI Provider Metrics
  - Upstream requests/second (by provider)
  - Upstream latency (by model)
  - Upstream errors (by type)
  - Cost estimation (tokens used)

Row 5: Infrastructure
  - CPU usage (by pod)
  - Memory usage (by pod)
  - Database connections
  - Disk usage

Variables:
  - $workflow (dropdown: select specific workflow)
  - $time_range (dropdown: 5m, 1h, 24h, 7d)
  - $namespace (dropdown: kubernetes namespace)

Alerts Configured:
  - High error rate (>1% for 5 minutes)
  - High latency (P95 >100ms for 5 minutes)
  - Database write failures (>10 in 5 minutes)
  - Circuit breaker trips (any in 5 minutes)
```

**Datadog Dashboard (Import Ready):**

```yaml
Dashboard: UATP Production Monitoring

JSON File: dashboards/uatp-datadog-dashboard.json

Import:
  1. Datadog UI → Dashboards → New Dashboard
  2. Import JSON → Upload file
  3. Configure: Ensure UATP integration installed
  4. Done: Live dashboard

Widgets Included:

Top Widgets (Key Metrics):
  - Request Rate (timeseries)
  - Error Rate (timeseries, red if >1%)
  - P99 Latency (timeseries, alert threshold at 100ms)
  - Capsule Generation Rate (timeseries)

Policy Enforcement:
  - Policy Check Results (stacked bar: pass/fail/block)
  - Circuit Breaker Status (heatmap)
  - Policy Violations (list)

AI Provider Performance:
  - OpenAI Latency (timeseries by model)
  - Anthropic Latency (timeseries by model)
  - Provider Errors (log stream)
  - Token Usage (timeseries, cost estimation)

Infrastructure:
  - Pod CPU (timeseries by pod)
  - Pod Memory (timeseries by pod)
  - Database Query Performance (top queries)
  - Network I/O (timeseries)

Alerts:
  ✅ High error rate
  ✅ High latency
  ✅ Database connectivity issues
  ✅ Policy violations spike

Integration:
  - Datadog Agent: Automatically scrapes UATP metrics
  - APM: Traces sent via OpenTelemetry
  - Logs: Forwarded via Fluentd/Vector
```

**Splunk Dashboard (Import Ready):**

```yaml
Dashboard: UATP Security & Compliance Monitoring

XML File: dashboards/uatp-splunk-dashboard.xml

Import:
  1. Splunk UI → Dashboards → Create New Dashboard
  2. Source → Import from XML
  3. Upload: uatp-splunk-dashboard.xml
  4. Done: Dashboard active

Panels:

Security Events:
  - Authentication attempts (success/failure)
  - Authorization denials
  - Policy violations
  - Break-glass access events

Compliance:
  - HIPAA policy checks (pass/fail rate)
  - GDPR policy checks (pass/fail rate)
  - Refusal events (circuit breaker trips)
  - Consent validation events

Audit Trail:
  - Admin actions (policy changes, user management)
  - Capsule access events (who accessed what)
  - Data export events
  - Configuration changes

Search Queries (Pre-Configured):
  # All policy violations in last 24 hours
  index=uatp sourcetype=policy_check result=fail
  | stats count by policy_name, workflow_id
  | sort -count

  # Failed authentication attempts
  index=uatp sourcetype=auth action=login result=failure
  | timechart count by user

  # High-value actions requiring review
  index=uatp sourcetype=admin_action
  | search action IN ("policy_change", "user_elevation", "break_glass_access")

Alerts (Pre-Configured):
  ✅ Policy violation spike (>10 violations in 5 min)
  ✅ Failed authentication spike (>5 failures in 1 min)
  ✅ Break-glass access (immediate alert)
  ✅ Bulk data export (immediate alert)
```

**CloudWatch Dashboard (AWS):**

```yaml
Dashboard: UATP AWS Monitoring

CloudFormation Template: cloudwatch/uatp-dashboard.yaml

Deploy:
  aws cloudformation deploy \
    --template-file cloudwatch/uatp-dashboard.yaml \
    --stack-name uatp-monitoring

Widgets:

EKS Metrics:
  - Pod CPU utilization
  - Pod memory utilization
  - Pod restart count
  - Node health

RDS Metrics (PostgreSQL):
  - Database connections
  - Read/write IOPS
  - Freeable memory
  - Database latency

ALB Metrics:
  - Target health
  - Request count
  - Error count (4xx, 5xx)
  - Target response time

Custom Metrics (from UATP):
  - Capsule creation rate
  - Policy check rate
  - Chain verification rate

Alarms:
  ✅ Pod CPU >80% for 5 minutes
  ✅ Database connections >80% of max
  ✅ ALB target unhealthy
  ✅ UATP error rate >1%
```

---

### Q4.4: API/versioning policy and deprecation timelines?

**A: Clear versioning with long deprecation windows:**

**API Versioning Strategy:**

```yaml
Current API Version: v1

Versioning Scheme: Semantic Versioning (SemVer)
  - Major: Breaking changes (v1 → v2)
  - Minor: New features, backward compatible (v1.0 → v1.1)
  - Patch: Bug fixes, backward compatible (v1.0.0 → v1.0.1)

API Endpoint Format:
  https://api.uatp.com/v1/capsules
                          ↑
                       Version in URL

Header-Based Versioning (Alternative):
  POST /capsules
  Headers:
    API-Version: 2025-10-26  # Date-based versioning
```

**Backward Compatibility Policy:**

```yaml
Guarantees:

Within Same Major Version (e.g., v1.x):
  ✅ All existing endpoints continue to work
  ✅ All existing request formats accepted
  ✅ All existing response fields present
  ✅ New fields may be added (clients should ignore unknown fields)
  ✅ No breaking changes

Example:
  v1.0.0 → v1.1.0: Add new optional field "confidence_score"
  Old clients: Ignore new field (everything still works)
  New clients: Can use new field

Major Version Change (e.g., v1 → v2):
  ⚠️  Breaking changes allowed
  ⚠️  Endpoint structure may change
  ⚠️  Request/response formats may change
  ⚠️  Field names may change or be removed

Example:
  v1: POST /capsules (returns {capsule_id, hash})
  v2: POST /capsules (returns {id, chain_position, hash})  # Different structure!
```

**Deprecation Timeline:**

```yaml
Deprecation Process:

Phase 1: Announcement (Day 0)
  - Publish deprecation notice on status page
  - Email all customers using deprecated endpoint
  - Add "Deprecated" header to API responses:
      Deprecation: true
      Sunset: 2026-04-26T00:00:00Z

Phase 2: Warning Period (6 months)
  - Endpoint still works normally
  - Documentation marked as "Deprecated"
  - Alternatives provided in docs
  - Migration guide published

Phase 3: Deprecation (12 months from announcement)
  - Endpoint starts returning 410 Gone
  - Response includes migration guidance
  - Old clients break (intentionally)

Example Timeline:
  2025-10-26: Deprecate v1 /capsules/create endpoint
  2026-04-26: Warning period ends, start returning errors
  2026-10-26: Remove endpoint entirely (12 months)

Minimum Support Window:
  - Major versions: 24 months (2 years)
  - Minor versions: 12 months (1 year)
  - Patch versions: 6 months

Example:
  v1 released: 2024-01-01
  v2 released: 2025-01-01
  v1 sunset: 2027-01-01 (24 months after v2 release)
```

**Version Support Matrix:**

```yaml
Current Status (October 2025):

v1 (Current, Stable):
  Released: 2024-01-15
  Status: Fully supported
  Sunset: 2027-01-15 (when v2 stabilizes)
  Recommendation: Use for production

v2 (Beta):
  Released: 2025-08-01
  Status: Beta (breaking changes possible)
  GA Target: 2026-01-01
  Recommendation: Use for testing only

v0 (Legacy):
  Released: 2023-06-01
  Deprecated: 2024-06-01
  Sunset: 2025-12-01
  Status: Returning 410 Gone (migrate to v1)
  Recommendation: Migrate immediately
```

**Breaking Change Policy:**

```yaml
What Constitutes a Breaking Change:

Breaking (Requires Major Version Bump):
  ❌ Removing an endpoint
  ❌ Removing a field from response
  ❌ Changing field type (string → number)
  ❌ Making optional field required
  ❌ Changing authentication method
  ❌ Changing HTTP method (GET → POST)

Not Breaking (Allowed in Minor Version):
  ✅ Adding new endpoint
  ✅ Adding new optional field to request
  ✅ Adding new field to response
  ✅ Adding new optional parameter
  ✅ Making required field optional

How We Communicate:
  - Changelog: Published with every release
  - Migration guides: For breaking changes
  - API docs: Version-specific (v1 docs, v2 docs separate)
  - Email notifications: 6 months before breaking changes
```

**API Changelog Format:**

```yaml
Format: Keep a Changelog (https://keepachangelog.com/)

Example:

## [1.2.0] - 2025-10-26

### Added
- New endpoint: GET /audit/reports (generate audit reports via API)
- New field: `confidence_score` in reasoning capsules (optional)
- Support for Azure OpenAI GPT-4o model

### Changed
- Increased default timeout for batch operations from 30s to 60s
- Improved error messages for policy failures (more details)

### Deprecated
- POST /capsules/create (use POST /capsules instead, identical behavior)
- Sunset date: 2026-04-26

### Fixed
- Bug: Streaming responses with large outputs caused timeouts
- Bug: Chain verification failed when capsules created in different timezones

### Security
- Updated post-quantum crypto library to latest NIST standard (ML-DSA-65)
```

**Client Library Versioning:**

```yaml
Python SDK:
  Package: pip install uatp-sdk
  Version: 1.2.0 (tracks API version)
  Support: Same lifecycle as API version

JavaScript SDK (Beta):
  Package: npm install @uatp/sdk
  Version: 1.0.0-beta.3
  Support: Beta (breaking changes possible)

Recommendation:
  - Pin major version: pip install uatp-sdk~=1.2
    (Gets 1.2.x updates, not 2.0.0)
  - Test before upgrading major versions
```

---


## 5. Enforcement & Governance


### Q5.1: False-positive/false-negative tracking for circuit breakers; do you expose metrics and a review queue?

**A: Comprehensive metrics and review workflow:**

**False Positive/Negative Tracking:**

```yaml
Metrics Exposed:

Policy Performance Metrics:
  uatp_policy_true_positives_total{policy="hipaa_consent"}
    # Correctly blocked violations

  uatp_policy_false_positives_total{policy="hipaa_consent"}
    # Incorrectly blocked legitimate requests

  uatp_policy_true_negatives_total{policy="hipaa_consent"}
    # Correctly allowed legitimate requests

  uatp_policy_false_negatives_total{policy="hipaa_consent"}
    # Incorrectly allowed violations (MOST CRITICAL!)

  Precision = true_positives / (true_positives + false_positives)
  Recall = true_positives / (true_positives + false_negatives)
  F1 Score = 2 * (precision * recall) / (precision + recall)

How We Track:

Automated Detection:
  - False Positive: User appeals policy block → Approved by admin
  - False Negative: Manual audit finds violation that wasn't caught

Manual Labeling:
  - Compliance team reviews blocked requests weekly
  - Labels: "Correct block" or "False positive"
  - System learns from labels (policy tuning)

Dashboard:
  - Policy accuracy dashboard (Grafana)
  - Shows: Precision, recall, F1 score per policy
  - Alert: If false positive rate >5%
```

**Review Queue (Built-in):**

```yaml
Policy Violation Review Queue:

Access: compliance-dashboard.uatp.com/review-queue

Interface:

┌─────────────────────────────────────────────────────────────┐
│  UATP Policy Review Queue                     Filters: [All] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  🔴 Pending Review (23)    🟢 Approved (156)    🔴 Rejected (12)  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Request #1247  [BLOCKED]             2025-10-26 14:30 │  │
│  │ Policy: HIPAA Consent                                  │  │
│  │ Reason: "No consent token found"                       │  │
│  │ User: john.doe@company.com                            │  │
│  │ Query: "Show patient 12345 medications"                │  │
│  │                                                        │  │
│  │ [View Full Request]  [Approve]  [Reject]  [Flag FP]   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Request #1246  [BLOCKED]             2025-10-26 14:15 │  │
│  │ Policy: GDPR Data Minimization                        │  │
│  │ Reason: "Requesting more fields than necessary"       │  │
│  │ User: jane.smith@company.com                          │  │
│  │                                                        │  │
│  │ [View Full Request]  [Approve]  [Reject]  [Flag FP]   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

Features:
  - Search/filter by policy, user, date range
  - Bulk actions (approve all, reject all)
  - Comments (add context to decisions)
  - Escalation (flag for senior review)
  - Export to CSV (for audits)
```

**Review Workflow:**

```yaml
Process:

1. Request Blocked by Circuit Breaker
   ↓
2. Capsule Created (type: REFUSAL)
   ↓
3. Added to Review Queue (status: PENDING)
   ↓
4. Compliance Officer Reviews
   ↓
5. Decision:
   a) Correct Block → Mark as TRUE_POSITIVE
   b) Incorrect Block → Mark as FALSE_POSITIVE
      → Optionally: Override decision (allow this time)
      → Add to policy tuning feedback
   ↓
6. Metrics Updated
   ↓
7. Policy Automatically Tuned (if pattern detected)

Example:
  - 10 false positives for "HIPAA consent check"
  - All 10: Same user role (Doctors)
  - Pattern: Doctors should be able to access patient data without explicit consent token
  - Action: Auto-suggest policy update: "Exempt role:doctor from consent check"
```

**False Positive Handling:**

```yaml
User Appeal Process:

1. User gets "Request blocked due to policy violation"
2. User clicks: "Appeal this decision"
3. Form appears:
   ┌────────────────────────────────────────┐
   │  Appeal Policy Decision                │
   ├────────────────────────────────────────┤
   │  Your request was blocked by:          │
   │  Policy: HIPAA Consent                 │
   │  Reason: No consent token found        │
   │                                        │
   │  Why should this be allowed?           │
   │  ┌────────────────────────────────┐   │
   │  │ I am the patient's doctor and  │   │
   │  │ have verbal consent. Consent   │   │
   │  │ form is pending in system.     │   │
   │  └────────────────────────────────┘   │
   │                                        │
   │  Attach evidence (optional):           │
   │  [Upload File]                         │
   │                                        │
   │  [Submit Appeal]                       │
   └────────────────────────────────────────┘

4. Appeal sent to review queue
5. Compliance officer reviews within SLA (4 hours)
6. Decision:
   - Approve: User gets one-time override token
   - Reject: User gets explanation
7. Tracked: False positive rate metric updated
```

**Policy Tuning Recommendations:**

```yaml
Automated Policy Tuning:

UATP analyzes false positives and suggests adjustments:

Example Report (Weekly):
  Policy: HIPAA Consent Check
  False Positive Rate: 8.5% (17 out of 200 blocks)

  Pattern Detected:
    - 12 of 17 false positives: User role = "doctor"
    - 5 of 17 false positives: User department = "emergency_medicine"

  Suggested Fix:
    # OLD POLICY:
    if not has_consent_token(request):
        return BLOCK

    # NEW POLICY:
    if not has_consent_token(request):
        if user.role in ["doctor", "nurse"] and emergency_context:
            log_warning("Emergency access without consent")
            return ALLOW  # With audit trail
        else:
            return BLOCK

  Impact Estimate:
    - Reduce false positives: 12 → 0 (71% reduction)
    - Maintain security: Emergency access still audited
    - Risk: Low (emergency access is legitimate)

  Recommendation: APPROVE (confidence: 85%)

  [Apply Suggested Fix]  [Modify and Apply]  [Reject]
```

**Metrics Dashboard for Policy Health:**

```yaml
Grafana Panel: Policy Effectiveness

Graphs:

1. False Positive Rate Over Time:
   - Line graph per policy
   - Target: <5% (green zone)
   - Alert: >10% (red zone)

2. False Negative Rate Over Time:
   - Requires manual audits (sample-based)
   - Target: <1% (critical!)
   - Alert: >2% (investigate immediately)

3. Policy Decision Distribution:
   - Stacked bar chart:
       * Green: Allowed (legitimate)
       * Red: Blocked (violations)
       * Yellow: Blocked but appealed (potential FP)

4. Appeal Outcomes:
   - Pie chart:
       * Approved appeals (false positives)
       * Rejected appeals (correct blocks)

5. Policy Accuracy Score:
   - Single stat panel (F1 score)
   - Target: >0.95
   - Current: 0.92 (needs tuning)

Alerts Configured:
  - FP rate >10% for 24 hours
  - FN detected in manual audit
  - Appeal rate >20% (policy too strict)
  - No appeals in 7 days (policy too lenient? Or not being used?)
```

---

### Q5.2: Override workflow: who can override, MFA, justification capture, and reporting—can we make override SLOs and alerts?

**A: Secure override workflow with full audit trail:**

**Override Authorization:**

```yaml
Who Can Override:

Role-Based Override Permissions:
  Admin:
    - Can override: ANY policy
    - Requires: MFA always
    - Approval: Not required (but logged)

  Compliance Officer:
    - Can override: Compliance policies only
    - Requires: MFA always
    - Approval: Not required

  Policy Manager:
    - Can override: Policies they own
    - Requires: MFA + justification
    - Approval: Required (from Compliance Officer)

  Senior Doctor (Healthcare Context):
    - Can override: HIPAA consent (emergency only)
    - Requires: MFA + medical justification
    - Approval: Not required (but escalated for review)

  Regular User:
    - Cannot override: Must appeal to Compliance Officer
    - Process: Appeal workflow (previous section)

Configuration:
  override_permissions:
    - role: "admin"
      policies: "*"
      require_mfa: true
      require_approval: false

    - role: "compliance_officer"
      policies: ["hipaa_*", "gdpr_*", "sox_*"]
      require_mfa: true
      require_approval: false

    - role: "doctor"
      policies: ["hipaa_consent"]
      conditions:
        - emergency: true
      require_mfa: true
      require_justification: true
      require_approval: false
      auto_escalate: true  # Automatic review by compliance
```

**Override Workflow:**

```yaml
Step-by-Step Process:

1. Request Blocked
   User: "Request blocked: HIPAA consent required"

2. User Initiates Override
   User clicks: "Request Override"

3. MFA Challenge
   ┌────────────────────────────────────────┐
   │  Multi-Factor Authentication           │
   ├────────────────────────────────────────┤
   │  Enter your authenticator code:        │
   │  ┌────────────────────────────────┐   │
   │  │ [______]                        │   │
   │  └────────────────────────────────┘   │
   │                                        │
   │  [Verify]                              │
   └────────────────────────────────────────┘

4. Justification Capture
   ┌────────────────────────────────────────┐
   │  Override Justification                │
   ├────────────────────────────────────────┤
   │  Policy: HIPAA Consent                 │
   │  Reason for override:                  │
   │  ┌────────────────────────────────┐   │
   │  │ Patient is unconscious, family │   │
   │  │ not reachable, need to access  │   │
   │  │ medical history for emergency  │   │
   │  │ treatment. Dr. Smith, ER.      │   │
   │  └────────────────────────────────┘   │
   │                                        │
   │  Attach supporting docs (optional):    │
   │  [Upload]                              │
   │                                        │
   │  ⚠️  Warning: Override will be audited │
   │                                        │
   │  [Submit Override Request]             │
   └────────────────────────────────────────┘

5. Approval Required (If Configured)
   ┌────────────────────────────────────────┐
   │  Override requires approval from:      │
   │  - jane.doe@company.com (Compliance)   │
   │                                        │
   │  Status: Waiting for approval...       │
   │  Notification sent to approver.        │
   └────────────────────────────────────────┘

6. Approval Decision
   Approver sees:
   ┌────────────────────────────────────────┐
   │  Override Approval Request             │
   ├────────────────────────────────────────┤
   │  Requested by: Dr. John Smith          │
   │  Policy: HIPAA Consent                 │
   │  Justification:                        │
   │  "Patient unconscious, emergency..."   │
   │                                        │
   │  Original Request:                     │
   │  "Access patient 12345 history"        │
   │                                        │
   │  Risk Assessment: HIGH (PHI access)    │
   │                                        │
   │  [Approve]  [Deny]  [Request More Info]│
   └────────────────────────────────────────┘

7. Override Applied (If Approved)
   - One-time token generated (valid for 15 minutes)
   - User can retry original request with token
   - Override capsule created (full audit trail)

8. Automatic Review
   - All overrides reviewed by compliance team (weekly)
   - Pattern detection (is this user overriding too often?)
   - Risk scoring (high-risk overrides escalated)
```

**Override Capsule Format:**

```yaml
Override Audit Trail:

Capsule Created (type: POLICY_OVERRIDE):
  {
    "capsule_type": "POLICY_OVERRIDE",
    "timestamp": "2025-10-26T14:30:22Z",
    "policy_overridden": "hipaa_consent",
    "original_decision": "BLOCK",
    "override_decision": "ALLOW",

    "actor": {
      "user_id": "dr.john.smith@hospital.com",
      "role": "doctor",
      "mfa_verified": true,
      "ip_address": "203.0.113.42",
      "department": "emergency_medicine"
    },

    "justification": {
      "reason": "Patient unconscious, family not reachable, emergency treatment",
      "attachments": ["emergency_declaration_form.pdf"],
      "case_number": "ER-2025-10-26-001"
    },

    "approval": {
      "required": true,
      "approved_by": "jane.doe@hospital.com",
      "approved_at": "2025-10-26T14:32:15Z",
      "approval_duration_seconds": 113
    },

    "override_token": {
      "token_id": "override_xyz123",
      "valid_until": "2025-10-26T14:45:22Z",  # 15 minutes
      "single_use": true,
      "used_at": "2025-10-26T14:33:00Z"
    },

    "risk_assessment": {
      "risk_level": "HIGH",
      "factors": ["PHI_ACCESS", "EMERGENCY_OVERRIDE"],
      "auto_escalated": true
    },

    "audit_metadata": {
      "review_status": "PENDING",
      "flagged_for_review": true,
      "reviewer": null,
      "reviewed_at": null
    }
  }

Chain:
  Input (blocked) → Policy Override → New Input (allowed) → Output
  (All cryptographically linked)
```

**Override SLOs and Alerts:**

```yaml
Service Level Objectives:

Override Approval SLO:
  - Target: 90% of override requests approved/denied within 15 minutes
  - Measured: Time from request to approval decision
  - Alert: If >10% of requests wait >15 minutes

Override Execution SLO:
  - Target: Override token issued within 30 seconds of approval
  - Measured: Time from approval to token generation
  - Alert: If any override takes >60 seconds

Override Review SLO:
  - Target: 100% of overrides reviewed within 24 hours
  - Measured: Time from override to compliance review
  - Alert: If any override not reviewed within 48 hours

Metrics:
  uatp_override_requests_total{policy="hipaa_consent",status="approved"}
  uatp_override_approval_duration_seconds{quantile="0.95"}
  uatp_override_pending_count{policy="hipaa_consent"}
  uatp_override_review_pending_count
```

**Alerts Configuration:**

```yaml
Prometheus Alerts:

1. Override Request Spike
   alert: OverrideRequestSpike
   expr: |
     rate(uatp_override_requests_total[5m]) > 5
   for: 10m
   annotations:
     summary: "High rate of override requests detected"
     description: "{{$value}} override requests per second in last 5 minutes"
   action: "Investigate: Is policy too strict? Or abuse?"

2. Override Approval SLO Breach
   alert: OverrideApprovalSLOBreach
   expr: |
     histogram_quantile(0.90,
       uatp_override_approval_duration_seconds_bucket
     ) > 900  # 15 minutes
   for: 1h
   annotations:
     summary: "Override approval SLO breached"
     description: "90% of overrides taking >15 min to approve"
   action: "Check: Are approvers available? Notification system working?"

3. Unreviewed Overrides
   alert: UnreviewedOverrides
   expr: |
     uatp_override_review_pending_count > 10
   for: 24h
   annotations:
     summary: "{{$value}} overrides pending review for >24h"
   action: "Escalate to compliance manager"

4. Same User Overriding Frequently
   alert: FrequentOverrideUser
   expr: |
     sum by (user_id) (
       rate(uatp_override_requests_total[24h])
     ) > 10
   annotations:
     summary: "User {{$labels.user_id}} requesting {{$value}} overrides/day"
   action: "Investigate: Policy needs adjustment? Or user abusing system?"

5. Emergency Override (Immediate)
   alert: EmergencyOverride
   expr: |
     uatp_override_requests_total{emergency="true"}
   for: 1s  # Immediate
   annotations:
     summary: "Emergency override by {{$labels.user_id}}"
   action: "Notify: Security team + Compliance officer (immediate review)"

Notification Channels:
  - Slack: #uatp-alerts
  - PagerDuty: Compliance on-call
  - Email: security@company.com, compliance@company.com
```

**Override Reporting:**

```yaml
Weekly Override Report (Automated):

Generated: Every Monday, 9 AM
Sent to: Compliance team, Security team

Report Contents:

1. Summary
   - Total overrides: 47
   - Approved: 45 (96%)
   - Denied: 2 (4%)
   - Average approval time: 8 minutes
   - Overrides by policy:
       * HIPAA Consent: 32
       * GDPR Data Minimization: 10
       * SOX Financial Access: 5

2. Top Override Users
   - Dr. John Smith: 12 overrides (emergency department)
   - Jane Doe: 8 overrides (compliance officer, testing)
   - Bob Johnson: 5 overrides (admin, maintenance)

3. Override Patterns
   - 68% of overrides: During business hours (9 AM - 5 PM)
   - 32% of overrides: After hours (emergency situations)
   - Peak day: Wednesday (14 overrides)

4. Approval Metrics
   - SLO achievement: 94% (target: 90%)
   - Fastest approval: 2 minutes
   - Slowest approval: 45 minutes (flagged for investigation)

5. Risk Assessment
   - High-risk overrides: 8 (reviewed by senior compliance)
   - Medium-risk: 25 (routine review)
   - Low-risk: 14 (auto-approved with post-review)

6. Recommendations
   - Policy "HIPAA Consent": Consider emergency exemption for ER doctors
   - User "Dr. John Smith": Frequent emergency overrides (all legitimate, suggest policy adjustment)
   - Approval SLO: Met target, no action needed

7. Action Items
   - [ ] Review policy adjustment for ER emergency access
   - [ ] Investigate slowest approval (45 min) – was approver available?
   - [✓] All high-risk overrides reviewed (completed)

[Download Full Report CSV]  [Export to SIEM]
```

**Override Abuse Prevention:**

```yaml
Abuse Detection:

Patterns Monitored:
  1. Same user overrides same policy >5 times/day
  2. Override requests immediately after denial (rapid retry)
  3. Override justifications are copy-pasted (not genuine)
  4. Overrides during off-hours by non-emergency users
  5. Approved overrides where token is never used (fake emergencies?)

Automated Actions:
  - Pattern detected → Alert compliance team
  - Suspicious user → Temporary suspension of override privilege
  - Investigation → Review all recent overrides by user
  - Abuse confirmed → Revoke override privilege, escalate to HR/Legal

Example:
  Alert: User john.doe@company.com has requested 15 overrides in 2 hours
  Pattern: All for same policy (GDPR data access)
  Justifications: Identical text (copy-paste)
  Action: Suspend override privilege pending investigation
  Notification: Sent to john.doe's manager + compliance officer
```

---

### Q5.3: Policy-as-code: language, testing framework, CI integration, staging "shadow" mode before enforce?

**A: Complete policy-as-code workflow:**

**Policy Definition Language:**

```yaml
Format: YAML-based DSL (Domain-Specific Language)

Example Policy File: policies/hipaa_consent.yaml

policy:
  name: "hipaa_consent"
  version: "1.2.0"
  description: "Enforce HIPAA consent requirement for PHI access"

  triggers:
    - event: "ai_request"
      conditions:
        - phi_detected: true
        - user_role: ["nurse", "admin", "researcher"]  # Doctors exempted

  checks:
    - name: "consent_token_present"
      type: "header_check"
      field: "X-Consent-Token"
      required: true

    - name: "consent_token_valid"
      type: "api_call"
      endpoint: "https://consent-api.hospital.com/validate"
      method: "POST"
      body:
        consent_token: "{{request.headers.X-Consent-Token}}"
        patient_id: "{{request.body.patient_id}}"
      expect:
        status: 200
        response.valid: true
      timeout_ms: 500

    - name: "consent_not_expired"
      type: "expression"
      expression: |
        consent_token.expires_at > now()

  actions:
    on_pass:
      - log:
          level: "INFO"
          message: "HIPAA consent verified for patient {{patient_id}}"
      - allow:
          record_capsule: true

    on_fail:
      - log:
          level: "WARN"
          message: "HIPAA consent check failed: {{failure_reason}}"
      - block:
          status_code: 403
          error_message: "PHI access requires valid consent"
          allow_override: true
          override_roles: ["doctor", "compliance_officer"]
      - notify:
          channels: ["slack", "email"]
          recipients: ["compliance@hospital.com"]
          condition: failure_count > 5 in 1h

  metadata:
    owner: "compliance_team"
    reviewed_by: "legal_team"
    last_reviewed: "2025-10-01"
    compliance_frameworks: ["HIPAA", "HITECH"]
    risk_level: "HIGH"
```

**Policy Testing Framework:**

```yaml
Test File: policies/hipaa_consent.test.yaml

test_suite:
  name: "HIPAA Consent Policy Tests"
  policy: "hipaa_consent"

  tests:
    - name: "Allow request with valid consent token"
      input:
        headers:
          X-Consent-Token: "valid_token_abc123"
        body:
          patient_id: "12345"
          query: "Get medications"
      mocks:
        - api: "https://consent-api.hospital.com/validate"
          response:
            status: 200
            body:
              valid: true
              expires_at: "2025-12-31T23:59:59Z"
      expect:
        decision: "ALLOW"
        capsule_created: true
        log_level: "INFO"

    - name: "Block request without consent token"
      input:
        headers: {}
        body:
          patient_id: "12345"
          query: "Get medications"
      expect:
        decision: "BLOCK"
        status_code: 403
        error_message_contains: "requires valid consent"
        capsule_type: "REFUSAL"

    - name: "Block request with expired consent"
      input:
        headers:
          X-Consent-Token: "expired_token_xyz"
        body:
          patient_id: "12345"
      mocks:
        - api: "https://consent-api.hospital.com/validate"
          response:
            status: 200
            body:
              valid: true
              expires_at: "2024-01-01T00:00:00Z"  # Expired!
      expect:
        decision: "BLOCK"
        failure_reason_contains: "expired"

    - name: "Allow doctor without consent (emergency)"
      input:
        headers:
          X-User-Role: "doctor"
        body:
          patient_id: "12345"
          emergency: true
      expect:
        decision: "ALLOW"
        log_message_contains: "Emergency access by doctor"
        capsule_metadata:
          override_reason: "emergency"

Run Tests:
  $ uatp policy test policies/hipaa_consent.yaml

  Running 4 tests...
  ✅ Allow request with valid consent token (45ms)
  ✅ Block request without consent token (12ms)
  ✅ Block request with expired consent (23ms)
  ✅ Allow doctor without consent (emergency) (18ms)

  4/4 tests passed (98ms total)
```

**CI/CD Integration:**

```yaml
GitHub Actions Example:

File: .github/workflows/policy-ci.yml

name: Policy CI/CD

on:
  pull_request:
    paths:
      - 'policies/**'
  push:
    branches:
      - main

jobs:
  test-policies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install UATP CLI
        run: |
          curl -sSL https://get.uatp.com | bash
          uatp --version

      - name: Lint Policies
        run: |
          uatp policy lint policies/*.yaml

      - name: Run Policy Tests
        run: |
          uatp policy test policies/**/*.test.yaml

      - name: Security Scan
        run: |
          uatp policy security-scan policies/*.yaml

      - name: Generate Coverage Report
        run: |
          uatp policy coverage policies/
          # Fail if coverage <80%
          uatp policy coverage --min 80 policies/

  deploy-to-staging:
    needs: test-policies
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Staging (Shadow Mode)
        env:
          UATP_API_KEY: ${{ secrets.UATP_STAGING_API_KEY }}
        run: |
          uatp policy deploy policies/*.yaml \
            --environment staging \
            --mode shadow \
            --duration 7d

      - name: Comment on PR
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ Policies deployed to staging in shadow mode for 7 days. Review results at https://dashboard.uatp.com/staging/shadow-mode'
            })

  promote-to-production:
    needs: deploy-to-staging
    if: github.event_name == 'workflow_dispatch'  # Manual trigger only
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Review Shadow Mode Results
        env:
          UATP_API_KEY: ${{ secrets.UATP_STAGING_API_KEY }}
        run: |
          uatp policy shadow-report policies/*.yaml \
            --environment staging \
            --output shadow-report.json

      - name: Check False Positive Rate
        run: |
          FP_RATE=$(jq '.false_positive_rate' shadow-report.json)
          if (( $(echo "$FP_RATE > 0.05" | bc -l) )); then
            echo "False positive rate too high: $FP_RATE"
            exit 1
          fi

      - name: Deploy to Production
        env:
          UATP_API_KEY: ${{ secrets.UATP_PROD_API_KEY }}
        run: |
          uatp policy deploy policies/*.yaml \
            --environment production \
            --mode enforce \
            --rollout canary  # Gradual rollout: 10% → 50% → 100%
```

**Shadow Mode (Observe Before Enforce):**

```yaml
What Is Shadow Mode:
  - Policy runs but doesn't block requests
  - Records what WOULD have happened
  - Allows testing in production without risk

Deployment:
  $ uatp policy deploy policies/hipaa_consent.yaml \
      --environment staging \
      --mode shadow \
      --duration 7d

Shadow Mode Behavior:
  1. Request comes in
  2. Policy check runs (all checks execute)
  3. Decision: BLOCK (but not enforced)
  4. Capsule created (type: SHADOW_REFUSAL)
  5. Request proceeds normally (allowed)
  6. Metrics tracked: "Would have blocked"

Shadow Mode Dashboard:

┌───────────────────────────────────────────────────────────────┐
│  Shadow Mode Results: hipaa_consent policy (7 days)          │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  Total Requests Analyzed: 15,432                              │
│  Would Have Blocked: 234 (1.5%)                               │
│  Would Have Allowed: 15,198 (98.5%)                           │
│                                                                │
│  Estimated Impact if Enforced:                                │
│    False Positive Rate: 2.8% (7 requests appealed)            │
│    False Negative Rate: Unknown (requires manual audit)       │
│                                                                │
│  Blocked Requests Breakdown:                                  │
│    ├─ No consent token: 180 (76.9%)                           │
│    ├─ Expired consent: 42 (17.9%)                             │
│    └─ Invalid consent: 12 (5.1%)                              │
│                                                                │
│  High-Risk Blocks (Manual Review Recommended):                │
│    - Request #12847: Dr. Smith, emergency access              │
│    - Request #13201: Nurse Johnson, legitimate?               │
│    - Request #14555: Admin, maintenance task                  │
│                                                                │
│  Recommendation:                                               │
│    ✅ Safe to enforce (FP rate <5%)                           │
│    ⚠️  Consider exemption for emergency department doctors    │
│                                                                │
│  [Export Report]  [Extend Shadow Mode]  [Deploy to Production]│
└───────────────────────────────────────────────────────────────┘

Decision:
  - If FP rate <5%: Deploy to production (enforce mode)
  - If FP rate >5%: Adjust policy, run shadow mode again
```

**Policy Versioning:**

```yaml
Policy Git Workflow:

Repository Structure:
  policies/
    ├─ hipaa_consent.yaml (v1.2.0)
    ├─ hipaa_consent.test.yaml
    ├─ gdpr_data_minimization.yaml (v1.0.0)
    ├─ gdpr_data_minimization.test.yaml
    └─ CHANGELOG.md

Versioning in Policy File:
  policy:
    name: "hipaa_consent"
    version: "1.2.0"  # SemVer
    changelog: |
      v1.2.0 (2025-10-26):
        - Added emergency exemption for doctors
        - Increased timeout from 300ms to 500ms
      v1.1.0 (2025-09-15):
        - Added consent expiration check
      v1.0.0 (2025-08-01):
        - Initial release

Deployment:
  - Dev: policies/*.yaml@main (latest)
  - Staging: policies/*.yaml@v1.2.0 (pinned version)
  - Prod: policies/*.yaml@v1.1.0 (stable, one version behind)

Rollback:
  $ uatp policy deploy policies/hipaa_consent.yaml@v1.1.0 \
      --environment production \
      --reason "Rollback due to high false positive rate in v1.2.0"
```

**Policy Linting:**

```yaml
Policy Linter (Built-in):

Checks:
  ✅ Syntax errors (invalid YAML)
  ✅ Required fields present (name, version, triggers, actions)
  ✅ API endpoints reachable (check URLs respond)
  ✅ Timeout values reasonable (<5000ms)
  ✅ Security issues (hardcoded secrets, insecure APIs)
  ✅ Best practices (meaningful names, documentation)

Run Linter:
  $ uatp policy lint policies/hipaa_consent.yaml

  Linting policies/hipaa_consent.yaml...
  ✅ Syntax valid
  ✅ Required fields present
  ⚠️  Warning: API timeout is 500ms (consider circuit breaker)
  ⚠️  Warning: No rate limiting on API call (risk of DDoS)
  ❌ Error: Hardcoded API key found in line 23 (use secrets instead)

  Lint result: FAILED (1 error, 2 warnings)

  Fix:
    Line 23: Remove hardcoded API key
    Use: api_key: "{{secrets.consent_api_key}}"

Pre-commit Hook:
  # .pre-commit-config.yaml
  repos:
    - repo: local
      hooks:
        - id: lint-policies
          name: Lint UATP Policies
          entry: uatp policy lint
          language: system
          files: ^policies/.*\.yaml$
```

---


## 6. Deployment, Reliability & Ops


### Q6.1: What are your SLO/SLA targets (availability %, P95/P99 latency) and what are the credits if they're missed?

**A: Three SLA tiers available:**

**Standard SLA (Included in Base Pricing):**
```yaml
Uptime: 99.5% monthly (3.6 hours downtime/month allowed)
P95 Latency: <50ms added overhead
P99 Latency: <100ms added overhead
Support Response: 4 business hours
Credits: 10% monthly fee per 0.5% below SLA

Example Credit Calculation:
  Month actual uptime: 98.8% (missed by 0.7%)
  Credit periods: 0.7% ÷ 0.5% = 1.4 → 2 credit periods
  Credit amount: 20% of monthly fee
  If monthly fee = $3,000, credit = $600
```

**Premium SLA (+$10K/year):**
```yaml
Uptime: 99.9% monthly (43 minutes downtime/month)
P95 Latency: <30ms added overhead
P99 Latency: <75ms added overhead
Support Response: 1 hour, 24/7
Credits: 25% monthly fee per 0.1% below SLA
```

**Enterprise SLA (+$25K/year):**
```yaml
Uptime: 99.95% monthly (21 minutes downtime/month)
P95 Latency: <30ms added overhead
P99 Latency: <75ms added overhead
Support Response: 30 minutes, 24/7
Dedicated TAM: Included
Credits: 50% monthly fee per 0.1% below SLA, up to 100% refund
```

**Measurement & Reporting:**
- Health check endpoint monitored every 30 seconds
- Prometheus metrics from your infrastructure
- Independent third-party monitoring (StatusPage.io)
- Monthly SLA report auto-generated, published by 5th of month
- Latency measured: UATP proxy instrumentation (baseline comparison)
- Excludes: Your infrastructure failures, AI provider outages, scheduled maintenance

---

### Q6.2: Throughput limits per deployment? Any rate-limiting on the proxy/SDK?

**A: Throughput scales with your infrastructure:**

**Standard Deployment (Self-Hosted):**
```yaml
No hard limits: Depends on your infrastructure
Tested to: 10,000 requests/second (single instance)
Recommended: <5,000 req/s per instance for safety margin
Horizontal scaling: Add more UATP proxy instances

Performance Under Load (AWS r6i.4xlarge, 16 CPU, 128GB RAM):
  5,000 req/s: P95 latency 28ms, stable
  10,000 req/s: P95 latency 45ms, stable
  15,000 req/s: P95 latency 85ms, degrading
  Recommendation: Keep <10K req/s per instance
```

**Managed Deployment Tiers:**
```yaml
Small: 100 req/s (360K req/hour)
Medium: 500 req/s (1.8M req/hour)
Large: 2,000 req/s (7.2M req/hour)
Custom: >2,000 req/s (we provision more instances)
Burst: 2x sustained for 5 minutes
```

**Rate Limiting (Optional):**
- Default: None (we don't impose limits)
- Configurable: Per-user, per-workflow, per-API-key limits
- Purpose: Protect your AI provider budget, not UATP capacity
- Example: "Max 1,000 requests/user/day to prevent abuse"

**Scaling Architecture:**
```
Load Balancer → UATP Proxy Instances (stateless, 3-20 instances)
              → Database Connection Pool (100 connections)
              → PostgreSQL (async writes, batched)

Tested Maximum:
  50 UATP instances × 5K req/s = 250K req/s
  Database write rate: 500K capsules/s (batched)
  Bottleneck: Usually your AI provider, not UATP
```

---

### Q6.3: Disaster recovery: RPO/RTO, backup cadence, restore drills, region failover?

**A: Comprehensive DR strategy with multiple tiers:**

**RPO/RTO Targets:**

**Standard DR (Self-Hosted):**
```yaml
RPO (Recovery Point Objective): 15 minutes
  - Capsules written to DB every 100ms (batched)
  - Continuous replication to standby
  - Max data loss: 15 minutes of capsules

RTO (Recovery Time Objective): 1 hour
  - Failover to standby database: 5 minutes
  - UATP proxy restart: 2 minutes
  - Validation and testing: 30 minutes
  - DNS propagation: 5-30 minutes

Annual DR test: Mandatory (we help you execute)
```

**Premium DR (+$15K/year):**
```yaml
RPO: 5 minutes (more frequent snapshots)
RTO: 15 minutes (automated failover)
Quarterly DR drills: Included
```

**Enterprise DR (+$30K/year):**
```yaml
RPO: 1 minute (synchronous replication)
RTO: 5 minutes (hot standby, instant failover)
Architecture: Active-active multi-region
Monthly DR drills: Included with full runbooks
```

**Backup Strategy:**
```yaml
Automated Backups:
  Frequency: Every 4 hours (continuous)
  Retention:
    - Hourly: 24 hours
    - Daily: 30 days
    - Weekly: 90 days
    - Monthly: 7 years (compliance requirement)

  Storage:
    - Same region: Hot backups (fast restore)
    - Cross-region: Warm backups (DR)
    - S3 Glacier: Cold archive (compliance)

  Encryption: AES-256, keys managed by you (optional)

Backup Testing:
  Monthly: Restore to staging environment (automated)
  Quarterly: Full DR drill (manual, documented)
  Annually: Disaster simulation with your team
  Validation: Chain integrity check on restored data
```

**Multi-Region Failover (Enterprise):**
```yaml
Primary Region: us-east-1
  - UATP Proxy: Active (handling traffic)
  - Database: Primary (read-write)
  - Status: Serving 100% of traffic

Secondary Region: us-west-2
  - UATP Proxy: Standby (ready, not serving)
  - Database: Replica (read-only, streaming replication)
  - Status: Monitoring, ready for failover

Failover Process:
  1. Traffic diverted to us-west-2 (DNS update)
  2. Replica promoted to primary (read-write)
  3. UATP proxy instances start serving traffic
  4. Validation: Chain integrity check
  Total time: 5-15 minutes

Failback Process:
  1. Restore us-east-1 from us-west-2 backups
  2. Replicate catchup data
  3. Validate: Chain integrity
  4. Traffic gradually shifted back (canary 10% → 50% → 100%)
  Total time: 1-2 hours (non-disruptive)
```

**Quarterly DR Drill (Premium/Enterprise):**
```
Week Before:
  - Schedule drill with your team
  - Define scope (which region, which workflows)
  - Set success criteria
  - Notify stakeholders

Day Of Drill:
  09:00 - Simulate disaster (take down primary region)
  09:05 - Initiate failover (follow runbook, monitor RTO)
  09:15 - Validate failover (generate test capsule, verify chain)
  09:20 - Production traffic test (route 10% real traffic)
  10:00 - Failback (restore primary, sync data, route back)

Post-Drill:
  - Document lessons learned
  - Update runbooks
  - Report to your team
  - Fix any gaps found
```

---

### Q6.4: Canary/rollback steps for proxy/sidecar updates? Do you support blue/green?

**A: Full support for modern deployment strategies with zero downtime:**

**Zero-Downtime Updates (Standard):**

**Phase 1: Canary (10% traffic)**
```yaml
Deploy: New UATP version to 1 instance
Route: 10% of traffic to canary
Monitor: 30 minutes
  - Error rate <0.1%
  - Latency P95 <50ms
  - Capsule generation rate normal
Decision: Continue or rollback
Rollback: Instant (redirect traffic back)
```

**Phase 2: Gradual Rollout (50% traffic)**
```yaml
Deploy: New version to 50% of instances
Monitor: 1 hour
Compare: New vs old version metrics side-by-side
Decision: Continue or rollback
```

**Phase 3: Full Deployment (100% traffic)**
```yaml
Deploy: All remaining instances
Monitor: 24 hours
Keep: Old version running but idle (for rollback)
After 24 hours: Decommission old version
```

**Blue/Green Deployment:**
```yaml
Blue Environment (Current Production):
  - UATP Version: v1.2.3
  - Instances: 5 proxies
  - Traffic: 100%
  - Status: ACTIVE

Green Environment (New Version):
  - UATP Version: v1.3.0
  - Instances: 5 proxies (identical config)
  - Traffic: 0% (testing only)
  - Status: READY

Deployment Process:
  1. Deploy v1.3.0 to Green (0% traffic)
  2. Run smoke tests against Green
  3. Route 10% traffic to Green (canary)
  4. Monitor for 1 hour
  5. Route 100% traffic to Green (instant switch)
  6. Keep Blue running for 24 hours (quick rollback)
  7. Decommission Blue after validation

Rollback:
  - Instant: Switch traffic back to Blue (<30 seconds)
```

**Automated Health Checks (Auto-Rollback Triggers):**
```yaml
Error Rate Threshold:
  - Canary error rate >0.5%: Auto-rollback
  - Comparison: vs baseline (old version)
  - Window: 5 minute average

Latency Threshold:
  - P95 latency >100ms: Auto-rollback
  - P99 latency >200ms: Auto-rollback
  - Comparison: vs baseline

Capsule Generation:
  - Capsule write failures >1%: Auto-rollback
  - Chain verification failures >0.1%: Auto-rollback
  - Database connection errors >5: Auto-rollback

Custom Checks (Your Policies):
  - Policy check failures spike: Alert (not auto-rollback)
  - Circuit breaker false positives: Alert
  - You decide: Manual rollback or continue
```

**Rollback Speed:**
```
Automated Rollback:
  - Detection: 30 seconds (health check interval)
  - Decision: Instant (automated)
  - Execution: 30 seconds (traffic redirect)
  - Total: ~1 minute from issue to rollback complete

Manual Rollback:
  - Command: kubectl patch service uatp-proxy --patch '{"spec":{"selector":{"version":"v1.2.3"}}}'
  - Execution: 10 seconds
  - Or: Click "Rollback" button in dashboard
```

**Kubernetes Example:**
```yaml
# Blue deployment (current)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: uatp-proxy-blue
  labels:
    version: v1.2.3
    deployment: blue
spec:
  replicas: 5
  selector:
    matchLabels:
      app: uatp-proxy
      version: v1.2.3

---

# Green deployment (new version)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: uatp-proxy-green
  labels:
    version: v1.3.0
    deployment: green
spec:
  replicas: 5
  selector:
    matchLabels:
      app: uatp-proxy
      version: v1.3.0

---

# Service (routes traffic based on label selector)
apiVersion: v1
kind: Service
metadata:
  name: uatp-proxy
spec:
  selector:
    app: uatp-proxy
    version: v1.2.3  # <-- Change this to v1.3.0 to switch
  ports:
    - port: 8080
```

---

### Q6.5: Multi-env support (dev/stage/prod) and isolation guarantees?

**A: Full multi-environment support with strong isolation:**

**Environment Isolation:**

**Development Environment:**
```yaml
Purpose: Engineer testing, policy development
Data: Synthetic/mocked capsules
Isolation: Separate namespace, no access to prod data
Database: Separate dev database (can be SQLite)
Policies: Relaxed (log everything, block nothing)
Cost: Minimal (share infrastructure)
Access: Engineers have full access
```

**Staging Environment:**
```yaml
Purpose: Pre-production validation, integration testing
Data: Sanitized production data OR synthetic
Isolation: Separate namespace, separate database
Database: Production-like (PostgreSQL)
Policies: Production policies (in observe mode)
Cost: ~20% of production (smaller instance sizes)
Access: Engineers deploy, QA validates
```

**Production Environment:**
```yaml
Purpose: Live traffic, real audit trails
Data: Real production data
Isolation: Strict RBAC, separate namespace, no dev access
Database: Production database (replicated)
Policies: Enforced (block on failure if configured)
Cost: Full production infrastructure
Access: Read-only for engineers, ops break-glass admin
```

**Isolation Guarantees:**

**Network Isolation:**
```yaml
Dev namespace: Can only reach dev database
Staging namespace: Can only reach staging database
Prod namespace: Can only reach prod database
Enforced by: Kubernetes NetworkPolicies
```

**Database Isolation:**
```yaml
Separate databases per environment
No cross-environment queries
Different credentials per environment
Prod credentials: Only accessible in prod namespace
```

**Configuration Isolation:**
```yaml
Environment-specific ConfigMaps/Secrets
Loaded at runtime based on environment variable
No hardcoded cross-environment references
Validated at startup (fails if wrong environment detected)
```

**API Key Isolation:**
```yaml
Dev: Test API keys (sandbox OpenAI account)
Staging: Separate API keys (limited budget)
Prod: Production API keys (full access)
Rotated independently per environment
```

**Deployment Workflow (Promotion Path):**

**Step 1: Developer Tests in Dev**
```
- Push code to dev branch
- CI/CD deploys to dev automatically
- Engineer tests manually
- Policy changes validated
- No approval needed
```

**Step 2: Promote to Staging**
```
- Merge dev → staging branch
- CI/CD deploys to staging automatically
- Automated integration tests run
- QA team validates
- Compliance team reviews policy changes
- Approval required: Engineering lead
```

**Step 3: Promote to Production**
```
- Merge staging → main branch
- CI/CD prepares production deployment (doesn't auto-deploy)
- Manual approval required (two approvals):
  * Approval 1: Engineering lead
  * Approval 2: Compliance or risk officer
- Deployment window: Tuesday-Thursday, 9 AM - 3 PM (example)
- Deployment: Blue/green with canary
- Monitoring: 24-hour bake period
```

**Access Control (RBAC by Environment):**
```yaml
Development:
  Engineers: Full access (deploy, debug, modify)
  QA: Read access
  Compliance: No access
  Ops: Admin access

Staging:
  Engineers: Deploy access (no direct pod access)
  QA: Full access (testing, validation)
  Compliance: Read access (policy review)
  Ops: Admin access

Production:
  Engineers: Read-only access (logs, metrics)
  QA: No access
  Compliance: Read access (audit reports)
  Ops: Break-glass admin access (requires approval)
  Automated deployment: ServiceAccount with limited permissions
```

---


## 7. Security & Compliance


### Q7.1: Do you sign a BAA (HIPAA) and provide a DPA/SCCs (GDPR) out of the box?

**A: Yes, standard for enterprise customers:**

**BAA (Business Associate Agreement) - HIPAA:**
```yaml
Status: Available immediately (template ready)

What we commit to:
  ✅ UATP is HIPAA compliant (technical controls)
  ✅ We don't access your PHI
  ✅ If managed deployment: We sign BAA covering our ops team
  ✅ Annual compliance review
  ✅ Breach notification within 24 hours
  ✅ Audit rights (you can audit us)

Requirements:
  - Your legal team reviews our BAA template
  - Customizations: Negotiable (within reason)
  - Execution: Digital signatures accepted
  - Timeline: 5-10 business days (legal review)

Cost: Included in pilot and production pricing (no extra fee)
```

**DPA (Data Processing Agreement) - GDPR:**
```yaml
Status: Available immediately (template ready)

What we commit to:
  ✅ UATP is GDPR compliant (Article 28 requirements)
  ✅ We process data only per your instructions
  ✅ We implement appropriate technical/organizational measures
  ✅ We assist with data subject requests (GDPR Art. 15-17)
  ✅ We notify you of breaches within 72 hours
  ✅ We allow audits and inspections

Includes:
  - Standard Contractual Clauses (SCCs) for EU transfers
  - Data residency commitments (EU-only if required)
  - Sub-processor list (e.g., AWS, if managed deployment)
  - International transfer safeguards

Cost: Included (no extra fee)
```

**Other Compliance Agreements:**
```yaml
Available on Request:

SOX (Sarbanes-Oxley):
  - Controls attestation
  - Change management documentation
  - Financial controls audit

PCI DSS:
  - If you handle payment data via AI (rare)
  - We don't store payment data in capsules
  - Attestation of compliance available

ISO 27001:
  - Certification: In progress (expected Q1 2026)
  - Pre-certification audit: Available now
  - Interim: SOC 2 Type II (Q4 2025)

FedRAMP (US Government):
  - Status: Not certified yet
  - Timeline: 2026-2027 (if demand justifies)
  - Interim: AWS GovCloud deployment available
```

**Execution Timeline:**
```
Week 1: Pilot kickoff
  - Legal provides: BAA/DPA templates
  - Your legal: Reviews (3-5 business days typical)
  - Negotiation: If needed (1-2 days)

Week 2: Execution
  - Both parties sign digitally
  - Effective date: Upon signature
  - Copy provided: For your records

Production:
  - BAA/DPA remain in effect for contract duration
```

---

### Q7.2: Key management: Customer-managed keys (AWS KMS/GCP KMS/Azure Key Vault), key rotation, HSM support?

**A: Multiple options from simple to enterprise-grade:**

**Key Management Options:**

**Option 1: UATP-Managed Keys (Default)**
```yaml
Who manages: We generate and store keys
Storage: AWS KMS, encrypted at rest
Rotation: Automatic every 90 days
Access: You never see private keys (we sign capsules for you)
Cost: Included
Use case: Simplest, managed pilot
```

**Option 2: Customer-Managed Keys (BYOK - Bring Your Own Key)**
```yaml
Who manages: You generate keys, we use them to sign
Storage: Your KMS (AWS/GCP/Azure)
Rotation: You control schedule
Access: You hold master keys, we request signing operations via API
Cost: Included (requires integration work in pilot)
Use case: You want full key custody
```

**Option 3: HSM (Hardware Security Module)**
```yaml
Who manages: Keys never leave HSM
Storage: AWS CloudHSM, Azure Dedicated HSM, or on-prem HSM
Rotation: You control
Access: UATP requests signing operations via PKCS#11 API
Cost: +$5K setup + HSM costs (AWS CloudHSM ~$1.50/hour = ~$1,080/month)
Use case: Maximum security, compliance requires HSM
```

**Option 4: Envelope Encryption (Hybrid)**
```yaml
Data Encryption Keys (DEKs): Generated per capsule
Key Encryption Key (KEK): Your master key in your KMS
Process: We generate DEK, encrypt it with your KEK, store encrypted DEK
Benefit: You can revoke access by rotating KEK
Use case: Balance of convenience and control
```

**BYOK (Bring Your Own Key) Integration Flow:**
```
Setup:
  1. You generate key pair in your AWS KMS
  2. You grant UATP ServiceAccount access to "sign" operation only
  3. UATP never sees private key (stays in KMS)
  4. UATP requests signatures via AWS KMS API

Signing Flow:
  ┌──────────────┐
  │  UATP Proxy  │
  └──────┬───────┘
         │ 1. Create capsule (hash computed)
         ↓
  ┌──────────────┐
  │  Your KMS    │  2. Request: Sign this hash
  │ (Your Keys)  │  3. KMS signs with private key (never leaves KMS)
  └──────┬───────┘  4. Returns signature
         ↓
  ┌──────────────┐
  │  UATP Proxy  │  5. Attach signature to capsule
  └──────────────┘  6. Store capsule (you control database)

You control:
  ✅ Key generation
  ✅ Key rotation schedule
  ✅ Access policies (which services can request signatures)
  ✅ Audit logs (every signing operation logged in your KMS)
```

**Key Rotation:**

**UATP-Managed Keys:**
```yaml
Schedule: Every 90 days (automatic)
Process:
  1. Generate new key pair
  2. Mark old key as "deprecated" (still verifies old capsules)
  3. New capsules signed with new key
  4. Old key retained for verification (forever)
Zero downtime: Old capsules still verify
Notification: 7 days before rotation
```

**Customer-Managed Keys:**
```yaml
Schedule: You decide
Process:
  1. You generate new key in your KMS
  2. You update UATP config with new key ID
  3. UATP starts using new key for new capsules
  4. Old key retained for verification
Zero downtime: You control timing
Recommendation: Every 90 days, or per your compliance policy
```

**Emergency Rotation (Key Compromise):**
```yaml
Detection: You notify us or we detect suspicious activity
Response Time: Within 1 hour
Process:
  1. Revoke compromised key immediately
  2. Generate new key (emergency procedure)
  3. Re-sign recent capsules (last 24 hours)
  4. Audit: Which capsules were signed with compromised key
Notification: All stakeholders within 4 hours
```

**HSM Support Details:**
```yaml
Supported HSMs:
  - AWS CloudHSM (FIPS 140-2 Level 3)
  - Azure Dedicated HSM
  - GCP Cloud HSM
  - On-premises: Thales Luna, Entrust nShield (via PKCS#11)

Integration Method:
  - UATP connects to HSM via PKCS#11 API or Cloud HSM SDK

Performance:
  - Signing latency: +5-10ms per capsule (HSM signing is slower)
  - Throughput: ~1,000 signatures/second per HSM
  - Recommendation: Use HSM cluster for high-volume production

Cost Example (AWS CloudHSM):
  - CloudHSM: $1.50/hour = ~$1,080/month
  - Plus: Network transfer costs (minimal)
  - UATP setup fee: $5K (one-time, covers integration)
  - Total first year: ~$18K for HSM-backed signing
```

**Key Material Security:**
```python
# UATP code does NOT contain:
❌ Hardcoded keys
❌ Private keys in environment variables
❌ Keys in config files

# UATP code references keys by ID only:
✅ AWS KMS Key ARN: "arn:aws:kms:us-east-1:123456789012:key/abc-def-ghi"
✅ Azure Key Vault URI: "https://your-vault.vault.azure.net/keys/uatp-signing-key"
✅ GCP KMS Resource Name: "projects/your-project/locations/us/keyRings/uatp/cryptoKeys/signing"
```

---

### Q7.3: Supply-chain security: signed releases, SBOMs, reproducible builds, third-party dep audits?

**A: Comprehensive supply-chain security program:**

**Signed Releases:**
```yaml
Every Release:
  ✅ Git commit signed with maintainer GPG key
  ✅ Container images signed with Cosign (Sigstore)
  ✅ Helm charts signed with GPG
  ✅ Release artifacts checksummed (SHA-256)
  ✅ Release notes include signature verification instructions

Verification:
  # Verify container image signature
  cosign verify uatp/proxy:v1.3.0 \
    --certificate-identity=release@uatp.com \
    --certificate-oidc-issuer=https://token.actions.githubusercontent.com

  # Verify Helm chart
  helm verify uatp-capsule-engine-1.3.0.tgz \
    --keyring uatp-signing-key.gpg
```

**SBOM (Software Bill of Materials):**
```yaml
Format: SPDX 2.3 and CycloneDX 1.4
Frequency: Every release
Contents:
  - All direct dependencies (Python packages, libraries)
  - All transitive dependencies
  - License information
  - Known vulnerabilities (CVE mapping)
  - Supplier information

Access:
  - Public: Available on releases page
  - API: programmatic access for automation
  - Integration: Works with Dependency-Track, Snyk, etc.

Example SBOM snippet:
  {
    "bomFormat": "CycloneDX",
    "specVersion": "1.4",
    "version": 1,
    "components": [
      {
        "name": "pycryptodome",
        "version": "3.19.0",
        "type": "library",
        "licenses": ["BSD-2-Clause"],
        "purl": "pkg:pypi/pycryptodome@3.19.0",
        "hashes": ["sha256:abc123..."]
      }
    ]
  }
```

**Reproducible Builds:**
```yaml
Goal: Anyone can rebuild our container images and get identical hash

Process:
  1. Dockerfile pins all package versions (no "latest")
  2. Base images pinned by digest (not tag)
  3. Build timestamps normalized
  4. Build environment specified (Ubuntu 22.04 LTS)
  5. Build instructions published

Example:
  FROM ubuntu:22.04@sha256:abc123def456...
  ENV DEBIAN_FRONTEND=noninteractive
  RUN apt-get update && apt-get install -y \
      python3=3.10.12-1~22.04 \
      python3-pip=22.0.2+dfsg-1ubuntu0.4

Verification:
  # Build yourself and compare hash
  docker build -t uatp-verify:v1.3.0 .
  docker inspect uatp-verify:v1.3.0 | jq '.[0].RootFS.Layers'
  # Compare with our published hashes
```

**Third-Party Dependency Audits:**
```yaml
Frequency:
  - Continuous: Automated scanning on every commit
  - Weekly: Dependency updates reviewed
  - Monthly: Security audit report generated
  - Quarterly: Manual review of critical dependencies

Tools Used:
  - Snyk: Vulnerability scanning (integrated in CI/CD)
  - Dependabot: Automated dependency updates
  - pip-audit: Python-specific security checks
  - Trivy: Container image scanning
  - OWASP Dependency-Check: License compliance

Critical Dependency Policy:
  - <10 critical dependencies (cryptography, database drivers)
  - All critical deps: Maintained by reputable organizations
  - All critical deps: Active security response team
  - All critical deps: Reviewed annually for alternatives

Example Audit Report (Monthly):
  Total dependencies: 127
  Direct dependencies: 23
  Transitive dependencies: 104
  Known vulnerabilities: 2 (both low severity, patches applied)
  Outdated dependencies: 5 (updates scheduled)
  License compliance: ✅ All compatible
```

**Dependency Update Process:**
```yaml
Automated (Dependabot):
  - Security patches: Applied within 24 hours
  - Minor updates: Reviewed weekly, merged if tests pass
  - Major updates: Requires manual review and testing

Manual Review Required For:
  - Cryptographic libraries (Dilithium3, Kyber768)
  - Database drivers (asyncpg, SQLAlchemy)
  - API frameworks (Quart, FastAPI)
  - Changes to security-critical code paths

Testing Before Merge:
  - Unit tests (71% coverage, 100% for crypto/security)
  - Integration tests (end-to-end capsule generation)
  - Performance regression tests
  - Security scans (Snyk, Trivy)
```

**Supply-Chain Attack Mitigations:**
```yaml
Protections:
  ✅ Two-factor authentication required for all maintainers
  ✅ Branch protection (require reviews before merge)
  ✅ Signed commits (GPG verification)
  ✅ CI/CD runs in isolated environment (no access to secrets)
  ✅ Container images built from source (not pre-built binaries)
  ✅ SBOM generated from actual build (not declared)
  ✅ Private package mirror (for critical dependencies)

Monitoring:
  - GitHub Security Alerts (enabled)
  - Dependabot security updates (enabled)
  - Snyk monitors our repos 24/7
  - Manual review of any unexpected dependency changes
```

---

### Q7.4: Pen test cadence (quarterly/annual?), bug bounty, secure SDLC evidence?

**A: Regular security testing and secure development practices:**

**Penetration Testing:**
```yaml
Internal Pen Testing:
  Frequency: Quarterly (every 3 months)
  Scope:
    - UATP API endpoints
    - Proxy/sidecar attack vectors
    - Database access controls
    - Key management system
  Performed by: Internal security team
  Report: Available to customers under NDA

External Pen Testing:
  Frequency: Annual (every 12 months)
  Performed by: Third-party security firm (rotating annually)
  Scope:
    - Full system (white-box + black-box)
    - Social engineering (phishing tests on team)
    - Physical security (if on-prem deployment)
    - Compliance-specific tests (HIPAA, GDPR)
  Report: Executive summary available to customers

Compliance-Driven Pen Testing:
  Frequency: Per compliance requirements
  Examples:
    - HIPAA Security Rule: Annual
    - PCI DSS: Quarterly
    - SOC 2 Type II: Annual
    - ISO 27001: Annual
```

**Recent Pen Test Results (Q3 2025):**
```yaml
Findings:
  Critical: 0
  High: 0
  Medium: 2
    1. Rate limiting bypass on non-prod endpoint (fixed in 48 hours)
    2. Verbose error messages leak stack traces (fixed in 72 hours)
  Low: 5
    - All addressed within 30 days

Overall Security Rating: 8.5/10

Key Strengths Noted:
  ✅ Post-quantum cryptography implementation sound
  ✅ No SQL injection vectors found
  ✅ Authentication/authorization properly implemented
  ✅ Secrets management follows best practices
  ✅ Capsule chain integrity held up under adversarial testing
```

**Bug Bounty Program:**
```yaml
Status: Private program (launching public Q1 2026)

Current Program (Private):
  Platform: HackerOne (invite-only)
  Participants: ~50 vetted security researchers
  Scope:
    - UATP API (api.uatp.com)
    - UATP Proxy (self-hosted deployments excluded)
    - Documentation/website (limited scope)

  Out of Scope:
    - Customer deployments (self-hosted)
    - Social engineering
    - Physical attacks
    - DDoS

Rewards:
  Critical: $5,000 - $10,000
    - Remote code execution
    - Authentication bypass
    - Cryptographic weakness
    - Capsule chain tampering

  High: $1,000 - $5,000
    - Privilege escalation
    - Sensitive data exposure
    - Policy bypass

  Medium: $500 - $1,000
    - XSS, CSRF
    - Information disclosure

  Low: $100 - $500
    - Best practice violations

Response SLA:
  - First response: 24 hours
  - Triage: 72 hours
  - Fix timeline:
      Critical: 7 days
      High: 30 days
      Medium: 60 days
      Low: 90 days
```

**Secure SDLC Evidence:**

**Design Phase:**
```yaml
Security Requirements:
  - Threat modeling (STRIDE methodology)
  - Security architecture review
  - Privacy impact assessment (for data handling features)
  - Compliance mapping (HIPAA, GDPR, etc.)

Artifacts:
  ✅ Threat model diagrams (available to enterprise customers)
  ✅ Security requirements specification
  ✅ Data flow diagrams with trust boundaries
```

**Development Phase:**
```yaml
Secure Coding Practices:
  - Mandatory code review (2 reviewers minimum)
  - Static analysis (Bandit for Python)
  - Linting (pylint, mypy for type checking)
  - Pre-commit hooks (secrets detection, format checking)

Tools Integrated in CI/CD:
  ✅ Snyk (dependency scanning)
  ✅ Trivy (container scanning)
  ✅ GitLeaks (secrets detection)
  ✅ Bandit (Python security linter)
  ✅ OWASP Dependency-Check

Developer Training:
  - Annual secure coding training (OWASP Top 10)
  - Quarterly security awareness (phishing, social engineering)
  - New hire security onboarding (day 1)
```

**Testing Phase:**
```yaml
Security Testing:
  - Unit tests (71% coverage, 100% for crypto/security modules)
  - Integration tests (API security, authentication)
  - Penetration testing (quarterly internal, annual external)
  - Fuzz testing (on cryptographic functions)
  - Compliance testing (HIPAA, GDPR validators)

Automated Security Tests:
  ✅ Authentication bypass attempts (90 test cases)
  ✅ Authorization checks (150 test cases)
  ✅ Input validation (500+ test cases, includes fuzzing)
  ✅ Cryptographic operations (200 test cases)
  ✅ Capsule chain integrity (100 adversarial test cases)
```

**Deployment Phase:**
```yaml
Security Gates:
  - All CI/CD security checks must pass (no overrides without security team approval)
  - Container images scanned (no critical vulnerabilities allowed)
  - SBOM generated and published
  - Release notes include security fixes

Production Hardening:
  ✅ Principle of least privilege (RBAC, IAM policies)
  ✅ Network segmentation (firewall rules, NetworkPolicies)
  ✅ Encryption at rest (database, backups)
  ✅ Encryption in transit (TLS 1.3)
  ✅ Secrets management (KMS, not environment variables)
```

**Operations Phase:**
```yaml
Security Monitoring:
  - 24/7 SIEM (if managed deployment)
  - Intrusion detection (Falco on Kubernetes)
  - Log aggregation and analysis (suspicious patterns)
  - Vulnerability scanning (weekly)
  - Incident response runbooks (tested quarterly)

Incident Response:
  - Security incidents: Response within 1 hour
  - Breach notification: Within 24 hours (customers), 72 hours (regulators)
  - Post-mortem: Within 5 business days
  - Lessons learned: Incorporated into SDLC
```

**Compliance Audits:**
```yaml
SOC 2 Type II:
  Status: In progress (audit firm engaged)
  Expected: Q4 2025
  Scope: Security, availability, confidentiality

ISO 27001:
  Status: Planned for Q1 2026
  Pre-assessment: Completed (gap analysis done)

HIPAA:
  Status: Self-attestation + third-party assessment
  Last assessment: Q3 2025
  Next assessment: Q3 2026

Evidence Package Available:
  ✅ Secure SDLC documentation
  ✅ Pen test reports (executive summaries)
  ✅ Security architecture diagrams
  ✅ Incident response procedures
  ✅ Vulnerability management process
  ✅ Security training records
```

---

### Q7.5: Access control: SSO/SAML/OIDC, RBAC/ABAC, SCIM provisioning, break-glass procedures and audit of admin actions?

**A: Enterprise-grade access control with multiple authentication methods:**

**Authentication Methods:**

**SSO/SAML:**
```yaml
Supported Identity Providers:
  ✅ Okta
  ✅ Azure Active Directory / Entra ID
  ✅ Google Workspace
  ✅ OneLogin
  ✅ Auth0
  ✅ Custom SAML 2.0 providers

Configuration:
  - Setup time: 30 minutes with your IdP
  - MFA: Enforced through your IdP
  - Session timeout: Configurable (default: 8 hours)
  - Just-in-time (JIT) provisioning: Supported

Example SAML Integration:
  1. You provide: IdP metadata URL or XML
  2. We provide: Service Provider metadata
  3. Configure attribute mapping (email, roles, groups)
  4. Test: SSO login flow
  5. Production: Enable for all users

Cost: Included in Enterprise tier
```

**OIDC (OpenID Connect):**
```yaml
Supported:
  ✅ Any OIDC-compliant provider
  ✅ OAuth 2.0 with OIDC layer
  ✅ Social logins (Google, GitHub) - for dev environments only

Configuration:
  - Provide: Client ID, Client Secret, Discovery URL
  - Claims mapping: Standard (email, name, groups)
  - Token validation: JWT signature verification + expiration

Use case: Simpler than SAML, good for startups
```

**Local Authentication (Fallback):**
```yaml
When to use:
  - Break-glass access (IdP is down)
  - Initial setup (before SSO configured)
  - Service accounts (API tokens)

Security:
  - Passwords: bcrypt hashed, min 12 characters
  - MFA: TOTP (Google Authenticator, Authy)
  - Rate limiting: 5 failed attempts → 15 minute lockout
  - Session tokens: Short-lived (4 hours)
```

**RBAC (Role-Based Access Control):**

```yaml
Predefined Roles:

Admin:
  Permissions:
    - Full system access
    - Manage users and roles
    - Configure policies
    - Access all workflows
    - View all audit reports
    - Modify system settings
  Use case: Platform administrators

Compliance Officer:
  Permissions:
    - Read-only access to all workflows
    - Generate audit reports
    - Export capsule data
    - Review policy violations
    - No system configuration changes
  Use case: Compliance and audit teams

Policy Manager:
  Permissions:
    - Create and modify policies
    - Test policies in staging
    - Deploy policies to production (with approval)
    - View policy enforcement metrics
  Use case: Risk officers, policy administrators

Developer:
  Permissions:
    - Read access to dev/staging environments
    - Deploy to dev environment
    - View metrics and logs
    - Test policy configurations
  Use case: Engineering teams

Auditor (Read-Only):
  Permissions:
    - Read-only access to audit reports
    - Export reports
    - No system modifications
  Use case: External auditors, regulators

Service Account:
  Permissions:
    - API access only
    - Scoped to specific workflows
    - No web UI access
    - Revocable API tokens
  Use case: CI/CD pipelines, integrations
```

**ABAC (Attribute-Based Access Control):**
```yaml
Beyond roles, access is further controlled by attributes:

Attributes:
  - Department (e.g., "Healthcare", "Finance")
  - Data classification (e.g., "PHI", "PII", "Public")
  - Workflow owner (e.g., team responsible for workflow)
  - Time-based (e.g., business hours only)
  - Location (e.g., US-only access for certain data)

Example Policy:
  "User can access audit reports IF:
    - Role = Compliance Officer OR Admin
    - AND Department = Healthcare OR All
    - AND Data classification <= User's clearance level
    - AND Access time = Business hours (9 AM - 5 PM)
    - AND Access location = Approved IP ranges"

Configuration:
  - Policy language: YAML-based
  - Testing: Dry-run mode (see who would have access)
  - Audit: Every access decision logged
```

**SCIM (System for Cross-domain Identity Management):**
```yaml
Status: Supported (v2.0)

Capabilities:
  ✅ User provisioning (create users from IdP)
  ✅ User deprovisioning (delete users when they leave org)
  ✅ User updates (sync email, name, role changes)
  ✅ Group management (sync groups from IdP)
  ✅ Real-time sync (changes propagate within 1 minute)

Supported IdPs:
  - Okta (native SCIM integration)
  - Azure AD (native SCIM integration)
  - OneLogin (native SCIM integration)
  - Custom SCIM 2.0 implementations

Configuration:
  1. Enable SCIM in UATP settings
  2. Generate SCIM API token (bearer token)
  3. Configure in your IdP:
     - SCIM base URL: https://api.uatp.com/scim/v2
     - Bearer token: [generated token]
  4. Map attributes (email → userName, etc.)
  5. Test: Create test user in IdP, verify in UATP
  6. Enable: Automatic provisioning

Sync Frequency:
  - Real-time: User changes (create, update, delete)
  - Periodic: Group membership (every 15 minutes)
```

**Break-Glass Procedures:**

```yaml
Scenario: IdP is down, SSO unavailable, need emergency access

Break-Glass Accounts:
  - Pre-configured: 2 break-glass admin accounts
  - Stored securely: Password in physical vault OR password manager with multiple custodians
  - MFA: Required (TOTP codes generated and stored separately)
  - Rotation: Quarterly (passwords changed every 90 days)

Access Process:
  1. Incident declared (IdP outage, emergency change needed)
  2. Approval required: 2 of 3 executives (CEO, CTO, CISO)
  3. Access: Use break-glass credentials (local auth, bypasses SSO)
  4. Audit: Every action logged with "BREAK-GLASS" flag
  5. Notification: Security team alerted immediately
  6. Review: Within 24 hours, justify all actions taken
  7. Password rotation: Break-glass password changed after use

Example Break-Glass Log Entry:
  {
    "timestamp": "2025-10-26T03:22:15Z",
    "user": "breakglass-admin-1",
    "action": "BREAK_GLASS_ACCESS",
    "approvers": ["ceo@company.com", "cto@company.com"],
    "reason": "IdP outage, critical policy change required",
    "actions_taken": [
      "Disabled failing policy check",
      "Restarted UATP proxy instances",
      "Verified capsule generation resumed"
    ],
    "duration": "45 minutes",
    "review_status": "PENDING"
  }
```

**Audit of Admin Actions:**

```yaml
What Gets Logged:
  ✅ All authentication attempts (success and failure)
  ✅ All authorization decisions (allow/deny)
  ✅ All admin actions (create, update, delete)
  ✅ All policy changes (who changed what, when)
  ✅ All configuration changes (system settings)
  ✅ All access to sensitive data (audit reports, capsule exports)
  ✅ All break-glass access usage
  ✅ All API calls (with user/service account identity)

Audit Log Format:
  {
    "timestamp": "2025-10-26T14:30:22Z",
    "event_type": "POLICY_UPDATE",
    "actor": {
      "user_id": "john.doe@company.com",
      "role": "Policy Manager",
      "ip_address": "203.0.113.42",
      "user_agent": "Mozilla/5.0...",
      "auth_method": "SAML_SSO"
    },
    "action": {
      "resource": "policy/hipaa_consent",
      "operation": "UPDATE",
      "changes": {
        "action_on_fail": "log" → "block",
        "require_mfa": false → true
      }
    },
    "result": "SUCCESS",
    "approval": {
      "required": true,
      "approved_by": "jane.smith@company.com",
      "approved_at": "2025-10-26T14:25:00Z"
    }
  }

Audit Log Storage:
  - Retention: 7 years (compliance requirement)
  - Immutable: Write-once storage (S3 Object Lock, WORM drives)
  - Encrypted: At rest (AES-256)
  - Access: Restricted to auditors and compliance officers
  - Export: Available in JSON, CSV, SIEM formats

Audit Log Monitoring:
  - Real-time alerts: Suspicious patterns (e.g., failed login spikes, break-glass usage)
  - Weekly report: Summary of admin actions
  - Monthly review: Compliance officer reviews all high-privilege actions
  - Annual audit: External auditor reviews logs
```

**Admin Action Approval Workflow:**

```yaml
High-Risk Actions Require Approval:
  - Policy changes in production
  - User role elevation (e.g., promote to Admin)
  - System configuration changes (e.g., disable circuit breaker)
  - Break-glass access
  - Data export (bulk capsule export)

Approval Process:
  1. Admin initiates action (e.g., "Change policy X to block mode")
  2. System checks: Does this require approval? (Yes)
  3. Request created: Sent to approvers (Compliance Officer + CTO)
  4. Approvers notified: Email + Slack notification
  5. Approvers review: View proposed change, risk assessment
  6. Decision: Approve or Deny (with justification)
  7. If approved: Change applied automatically
  8. If denied: Admin notified, change not applied
  9. Audit log: Records entire approval workflow

Example Approval Request:
  Subject: Approval Required: Change HIPAA Policy to Block Mode

  Requested by: john.doe@company.com (Policy Manager)
  Requested at: 2025-10-26 14:30:22 UTC

  Change:
    Policy: hipaa_consent
    Current: action_on_fail = "log"
    Proposed: action_on_fail = "block"

  Impact Assessment:
    - Will block requests without valid consent token
    - Estimated impact: 2-5% of current requests would be blocked
    - Recommended testing: Already tested in staging for 7 days

  Approvers: jane.smith@company.com (Compliance Officer), cto@company.com

  [Approve] [Deny] [Request More Info]
```

---


## 8. Data Handling Nuances


### Q8.1: What exactly is in the capsule metadata schema, and can it change backward-incompatibly?

**Schema Overview:**
```json
{
  "capsule_id": "uuid-v4",
  "type": "INPUT_PERSPECTIVE | REASONING_CHAIN | OUTPUT_DECISION | ...",
  "timestamp": "ISO-8601 with nanosecond precision",
  "chain_id": "uuid-v4",
  "previous_hash": "sha256-hex",
  "signature": "dilithium3-base64",
  "content": {
    "sensitivity": "PUBLIC | INTERNAL | CONFIDENTIAL | RESTRICTED",
    "confidence_score": 0.0-1.0,
    "provider": "openai | anthropic | ...",
    "model": "gpt-4 | claude-3.5-sonnet | ...",
    "tokens": {"input": 1234, "output": 567},
    "latency_ms": 890,
    "policy_checks": [
      {"policy": "hipaa_consent", "result": "PASS | FAIL", "timestamp": "..."}
    ],
    "reasoning_steps": [...],
    "refusal_triggered": false,
    "circuit_breaker_state": "CLOSED | OPEN | HALF_OPEN"
  },
  "schema_version": "7.2.0"
}
```

**Backward Compatibility Guarantee:**
- **MINOR version bumps** (7.2 → 7.3): Additive only, no breaking changes
- **MAJOR version bumps** (7.x → 8.0): Breaking changes allowed, 12-month migration window
- **Version detection**: Client SDK auto-detects schema version and adapts

**Migration Support:**
```yaml
Schema Migration:
  - UATP provides schema converter tool
  - Old capsules remain readable (translation layer)
  - Batch re-signing available for compliance

Example Migration:
  $ uatp capsule migrate \
      --from-schema 7.1 \
      --to-schema 8.0 \
      --chain-id abc-123 \
      --dry-run
```

**Honest Assessment:**
> We haven't done a breaking schema change yet, so the 12-month migration window is theory, not battle-tested practice. First major version bump will reveal pain points.

---

### Q8.2: Can we enforce data residency at a finer grain (per-workflow or per-tenant)?

**Yes.** UATP supports multi-tenant isolation with per-tenant configuration.

**Configuration:**
```yaml
Tenant Configuration:
  tenant_id: "acme-healthcare-eu"
  data_residency:
    region: "eu-west-1"
    allowed_regions: ["eu-west-1", "eu-central-1"]
    blocked_regions: ["us-*", "ap-*"]

  storage:
    postgres_endpoint: "eu-west-1.rds.amazonaws.com"
    redis_endpoint: "eu-west-1.elasticache.amazonaws.com"
    s3_bucket: "uatp-capsules-eu-acme"

  enforcement:
    block_cross_region_reads: true
    block_cross_region_writes: true
    audit_access_attempts: true
```

**Runtime Enforcement:**
```python
# Python SDK example
from uatp import CapsuleEngine

engine = CapsuleEngine(
    tenant_id="acme-healthcare-eu",
    enforce_residency=True  # Raises exception if region mismatch
)

try:
    capsule = engine.create_capsule(...)
except ResidencyViolationError as e:
    # Logs: "Attempted write to us-east-1 for EU-resident tenant"
    logger.error(f"Data residency violation: {e}")
```

**Per-Workflow Isolation:**
```yaml
Workflow Configuration:
  workflow_id: "patient-triage"
  data_residency:
    inherit_from_tenant: true
    override_region: "eu-west-1"  # Even stricter than tenant default

  workflow_id: "research-analytics"
  data_residency:
    inherit_from_tenant: true
    allow_anonymized_export: true
    export_regions: ["us-east-1"]  # For anonymized research data only
```

**Verification:**
- Every capsule includes `data_residency` metadata
- Auditors can verify all capsules stayed in declared region
- Cross-region access attempts logged as security events

**Honest Assessment:**
> Multi-region enforcement works, but cross-region disaster recovery creates tension. If EU region fails, do you want capsules replicated to US for availability, or strict residency with downtime risk? We support both, but you must choose.

---

### Q8.3: How do you handle GDPR data subject requests (Article 15 for access, Article 17 for deletion)?

**Article 15 - Right to Access:**
```bash
# Export all capsules for a data subject
$ uatp gdpr export \
    --data-subject-id "user-12345" \
    --email "patient@example.com" \
    --format json \
    --include-metadata \
    --output /tmp/gdpr-export-user-12345.zip

Output:
  ✅ 1,247 capsules exported
  ✅ Metadata included
  ✅ Cryptographic signatures intact
  ✅ Human-readable summary generated
  📦 Package: /tmp/gdpr-export-user-12345.zip (23.4 MB)
```

**Export Format:**
```
gdpr-export-user-12345.zip
├── capsules/
│   ├── 2025-01-15_healthcare-query_abc123.json
│   ├── 2025-02-03_prescription-refill_def456.json
│   └── ...
├── summary.txt  (human-readable: "You interacted with our AI on...")
├── verification.sh  (script to verify signatures independently)
└── metadata.json  (data lineage, consent records, retention policies)
```

**Article 17 - Right to Erasure:**
```bash
# Delete all capsules for a data subject
$ uatp gdpr delete \
    --data-subject-id "user-12345" \
    --reason "Article 17 GDPR request" \
    --confirmation-token "abc-xyz-from-email" \
    --audit-trail

Confirmation Required:
  ⚠️  This will PERMANENTLY delete 1,247 capsules for user-12345
  ⚠️  Deletion is IRREVERSIBLE
  ⚠️  Legal hold check: PASSED (no active litigation)
  ⚠️  Retention policy check: PASSED (no regulatory holds)

Type 'DELETE' to confirm: DELETE

Output:
  ✅ 1,247 capsules marked for deletion
  ✅ Tombstone records created (for chain integrity)
  ✅ Actual deletion scheduled (30-day delay for backup pruning)
  ✅ Audit trail capsule created (cryptographically sealed)
  📄 Deletion certificate: /tmp/gdpr-deletion-cert-user-12345.pdf
```

**Tombstone Approach:**
```json
{
  "capsule_id": "abc-123-deleted",
  "type": "TOMBSTONE",
  "reason": "GDPR Article 17 deletion request",
  "original_timestamp": "2025-01-15T10:30:00Z",
  "deletion_timestamp": "2025-10-26T14:22:00Z",
  "legal_basis": "Data subject request (GDPR Art. 17)",
  "auditor_note": "PII deleted, tombstone preserves chain integrity",
  "retention": "Tombstone retained for 7 years per legal requirement"
}
```

**Why Tombstones?**
- Deleting a capsule breaks the hash chain
- Tombstone preserves chain integrity for remaining capsules
- Auditors can verify deletion happened (vs. tampering)
- Satisfies GDPR's "demonstrate compliance" requirement

**Automated Workflow:**
```yaml
GDPR Request Handling:
  1. Request received via API or email
  2. Identity verification (2FA, ID document)
  3. Legal hold check (query litigation system)
  4. Retention policy check (regulatory obligations)
  5. Generate export (Article 15) or deletion plan (Article 17)
  6. Manual approval for high-risk deletions
  7. Execute with audit trail
  8. Send confirmation certificate to data subject

SLA:
  - Acknowledgment: 72 hours
  - Completion: 30 days (GDPR requirement)
  - Certificate delivery: Within 48 hours of completion
```

**Honest Assessment:**
> GDPR deletion with cryptographic chains is philosophically tricky. We use tombstones, which satisfy legal requirements but preserve chain structure. Some privacy advocates argue tombstones are "breadcrumbs." We believe it's the right balance, but expect debate.

---

### Q8.4: What about retention policies and automated deletion?

**Retention Policy Configuration:**
```yaml
Retention Policies:
  - policy_id: "healthcare-default"
    applies_to:
      - capsule_types: ["*"]
      - sensitivity: ["CONFIDENTIAL", "RESTRICTED"]
      - workflows: ["patient-triage", "diagnosis-assist"]

    retention:
      default_days: 2555  # 7 years (HIPAA requirement)
      min_days: 365       # Cannot delete before 1 year
      max_days: 3650      # Must delete after 10 years

    exceptions:
      - condition: "litigation_hold"
        action: "suspend_deletion"
      - condition: "active_audit"
        action: "extend_by_days: 365"

    deletion:
      method: "secure_overwrite"  # DoD 5220.22-M standard
      verification: "checksum_zeroes"
      certificate: true
```

**Automated Deletion Workflow:**
```python
# Daily cron job
from uatp.retention import RetentionManager

manager = RetentionManager()

# Scan for capsules past retention period
expired = manager.scan_expired_capsules(
    policies=["healthcare-default", "financial-default"],
    check_holds=True,
    dry_run=False
)

# Results
print(f"Found {expired.count} expired capsules")
print(f"Legal holds: {expired.held_count}")
print(f"Proceeding with deletion: {expired.deletable_count}")

# Execute deletion
results = manager.execute_deletion(
    capsule_ids=expired.deletable_ids,
    create_tombstones=True,
    generate_certificates=True
)

# Audit trail
print(f"Deleted: {results.deleted_count}")
print(f"Failed: {results.failed_count}")
print(f"Certificates: {results.certificate_paths}")
```

**Dashboard View:**
```
Retention Policy Dashboard:

  Policy: healthcare-default
  ├─ Active capsules: 1,245,892
  ├─ Approaching retention: 45,123 (within 30 days)
  ├─ Expired (held): 8,234 (litigation holds)
  ├─ Expired (deletable): 12,456
  └─ Deleted this month: 89,234

  Compliance Score: 98.7%

  Warnings:
  ⚠️  234 capsules exceed max_days (manual review required)
  ⚠️  12 litigation holds older than 5 years (stale?)
```

**Deletion Verification:**
```bash
# Verify deletion was secure
$ uatp retention verify-deletion \
    --capsule-id abc-123 \
    --check-backups \
    --check-replicas

Output:
  ✅ Primary database: DELETED (secure overwrite verified)
  ✅ Backup 1 (hourly): DELETED (pruned from backup chain)
  ✅ Backup 2 (daily): DELETED (pruned from backup chain)
  ✅ Backup 3 (weekly): DELETED (pruned from backup chain)
  ✅ DR replica (us-west): DELETED
  ✅ Archive storage: DELETED

  Tombstone: PRESENT (chain integrity maintained)
  Certificate: /audit/deletion-certs/abc-123.pdf
```

**Honest Assessment:**
> Automated deletion across all backups and replicas is harder than it sounds. Backup pruning can take 60-90 days to fully propagate. If a regulator asks "is it deleted?" the answer is "yes, but might exist in cold backup for 90 days." We're transparent about this.

---


## 9. Capsule Integrity & Crypto Details


### Q9.1: Algorithm agility for PQC (e.g., Dilithium parameter sets, migration plan if NIST guidance changes)?

**A: Future-proof cryptographic design with migration path:**

**Current PQC Implementation:**

```yaml
Signature Algorithm: ML-DSA-65 (Dilithium3)
  - NIST standardized (FIPS 204)
  - Key size: 2,592 bytes (public), 4,016 bytes (private)
  - Signature size: 3,293 bytes
  - Security level: NIST Level 3 (equivalent to AES-192)
  - Performance: ~5ms signing, ~2ms verification

Key Encapsulation: ML-KEM-768 (Kyber768)
  - NIST standardized (FIPS 203)
  - Public key: 1,184 bytes
  - Ciphertext: 1,088 bytes
  - Shared secret: 32 bytes
  - Security level: NIST Level 3

Hash Function: SHA-256 and SHA-384
  - For content fingerprints: SHA-256
  - For chain hashing: SHA-384 (higher collision resistance)
  - Quantum-resistant: Yes (Grover's algorithm only √N speedup, still secure)
```

**Algorithm Agility Design:**

```yaml
Capsule Format Includes Algorithm Identifiers:
  {
    "signature": {
      "value": "base64-encoded-signature",
      "algorithm": "ML-DSA-65",  # ← Explicit algorithm
      "version": "1.0"             # ← Version for algorithm params
    },
    "hash": {
      "value": "sha256:abc123...",
      "algorithm": "SHA-256"
    }
  }

Why This Matters:
  - Old capsules can be verified forever (algorithm stored in capsule)
  - New capsules can use new algorithms (forward compatibility)
  - Mixed capsule chains work (capsule N with Dilithium3, capsule N+1 with new algo)
```

**Migration Plan (If NIST Guidance Changes):**

**Scenario: NIST recommends moving from ML-DSA-65 to ML-DSA-87**

**Phase 1: Preparation (Week 1-2)**
```yaml
Actions:
  1. Implement new algorithm (ML-DSA-87) in UATP codebase
  2. Add backward compatibility (can verify both algorithms)
  3. Test thoroughly (unit tests, integration tests, performance benchmarks)
  4. Security review (internal + external cryptographer)
  5. Publish migration plan to customers

Customer Impact: None (you're still using ML-DSA-65)
```

**Phase 2: Soft Rollout (Week 3-4)**
```yaml
Actions:
  1. Deploy new UATP version (supports both algorithms)
  2. Configuration flag: "signature_algorithm = ML-DSA-65"  # Still using old
  3. Verification: Confirm old capsules still verify correctly
  4. Optional: Some customers opt-in to test new algorithm in dev

Customer Impact: Minimal (optional testing)
```

**Phase 3: Migration (Month 2-3)**
```yaml
Actions:
  1. Customers switch configuration: "signature_algorithm = ML-DSA-87"
  2. New capsules signed with ML-DSA-87
  3. Old capsules still verified with ML-DSA-65
  4. Hybrid chains: Capsule N (ML-DSA-65) → Capsule N+1 (ML-DSA-87) → works!

Customer Impact: Configuration change (1 line), redeploy, validate
```

**Phase 4: Deprecation (Month 6+)**
```yaml
Actions:
  1. Announce deprecation of ML-DSA-65 for new capsules
  2. Old capsules: Still verifiable forever (we never drop support for verification)
  3. New capsules: Must use ML-DSA-87 (or newer)

Customer Impact: Must migrate within 6 months (ample time)
```

**Re-signing Old Capsules (Optional):**
```yaml
If required by compliance (rare):
  1. Export old capsules with ML-DSA-65 signatures
  2. Verify signatures (prove integrity before re-signing)
  3. Generate new signatures with ML-DSA-87
  4. Create "re-signature capsules" (special capsule type)
  5. Audit trail: "This capsule was re-signed from ML-DSA-65 to ML-DSA-87 on [date]"

Process:
  - Automated: Batch re-signing tool provided
  - Auditable: Re-signature events logged
  - Verifiable: Both old and new signatures stored (for proof)

Cost: Minimal (CPU time for re-signing, ~1ms per capsule)
```

**Emergency Crypto Failure Response:**

**Scenario: Critical vulnerability found in ML-DSA-65 (quantum computer breaks it)**

```yaml
Response Timeline: 24-72 hours

Hour 1-4:
  - Security team assesses impact
  - Determine: Are existing signatures compromised? (likely not, but assume worst case)
  - Notify customers: Emergency crypto rotation required

Hour 4-12:
  - Deploy emergency patch: Switch to backup algorithm (e.g., SPHINCS+)
  - Customers apply patch immediately
  - New capsules signed with new algorithm

Hour 12-72:
  - Re-sign all capsules from last 90 days (high-risk period)
  - Audit: Which capsules might have been compromised?
  - Generate report: Crypto incident response documentation

Post-Incident:
  - Root cause analysis
  - Improve: Multi-signature capsules (use 2 algorithms simultaneously)
  - Update: Incident response playbook
```

**Multi-Signature Capsules (Paranoid Mode):**

```yaml
For maximum security, sign each capsule with TWO algorithms:

Signature 1: ML-DSA-65 (NIST standard)
Signature 2: SPHINCS+ (stateless hash-based, ultra-conservative)

Capsule format:
  {
    "signatures": [
      {
        "algorithm": "ML-DSA-65",
        "value": "base64-signature-1"
      },
      {
        "algorithm": "SPHINCS+-256f",
        "value": "base64-signature-2"
      }
    ],
    "verification_policy": "REQUIRE_ALL"  # Both must verify
  }

Benefits:
  - If one algorithm breaks: Other signature still proves integrity
  - Future-proof: Hedges against crypto failures

Cost:
  - Signature size: 2x (3.3 KB → 6.6 KB per capsule)
  - Signing time: 2x (~10ms instead of ~5ms)
  - Storage: 2x for signatures

Use case: Ultra-high-security deployments (government, critical infrastructure)
```

**Cryptographic Governance:**

```yaml
Who Decides Algorithm Changes:
  - NIST guidance: Triggers evaluation
  - UATP Security Team: Proposes migration plan
  - Customer Advisory Board: Reviews impact (for enterprise customers)
  - Customers: Decide migration timeline (within reason)

Transparency:
  - All crypto decisions documented publicly
  - Security audits published (summaries)
  - Migration plans published 90 days before enforcement
```

---

### Q9.2: How do you handle clock skew when chaining across distributed services?

**A: Multiple mechanisms to handle clock skew:**

**Problem Statement:**
```
Service A (clock: 14:30:00) creates Capsule 1
Service B (clock: 14:29:55) creates Capsule 2  # 5 seconds behind
Capsule 2 timestamp < Capsule 1 timestamp → Looks like time travel!
```

**Solution 1: Logical Clocks (Primary)**

```yaml
Instead of wall-clock time, use Lamport timestamps or vector clocks:

Capsule 1:
  - wall_clock_timestamp: "2025-10-26T14:30:00Z"
  - logical_clock: 1001  # Increments with each capsule
  - previous_capsule_logical_clock: 1000

Capsule 2:
  - wall_clock_timestamp: "2025-10-26T14:29:55Z"  # 5 seconds behind
  - logical_clock: 1002  # Still increases!
  - previous_capsule_logical_clock: 1001

Verification:
  ✅ logical_clock must be strictly increasing
  ✅ Wall clock can drift, doesn't matter for chain integrity
  ⚠️  If wall_clock_timestamp < previous capsule timestamp by >5 minutes → warning (clock badly skewed)
```

**Solution 2: Trusted Timestamp Authority (TTA)**

```yaml
For critical chains, optionally use external timestamp:

Process:
  1. Capsule created with local timestamp
  2. Hash sent to TTA (e.g., NIST, RFC 3161 TSA)
  3. TTA returns signed timestamp
  4. Signed timestamp stored with capsule

Capsule format:
  {
    "local_timestamp": "2025-10-26T14:30:00Z",
    "trusted_timestamp": {
      "value": "2025-10-26T14:30:03Z",
      "authority": "timestamp.nist.gov",
      "signature": "base64-tsa-signature"
    }
  }

Benefits:
  - Independent time source (trusted third party)
  - Legal non-repudiation (TTA signature proves "existed at this time")
  - Handles extreme clock skew (local clock can be wrong, TTA is authoritative)

Cost:
  - Latency: +50-200ms per capsule (network round-trip to TTA)
  - Fee: Some TTA services charge per timestamp (~$0.01-$0.05)

Use case: High-stakes legal evidence, regulatory compliance
```

**Solution 3: NTP Synchronization (Defense in Depth)**

```yaml
Recommendation to customers:

Deploy NTP/PTP:
  - All UATP proxy instances sync with NTP server
  - Target accuracy: <100ms
  - Monitoring: Alert if clock drift >1 second

Example (K8s):
  apiVersion: v1
  kind: Pod
  spec:
    hostNetwork: true  # Use host's NTP-synced clock
    containers:
    - name: uatp-proxy
      env:
      - name: NTP_SERVERS
        value: "time.google.com,time.cloudflare.com"

Verification:
  - UATP proxy logs current clock drift on startup
  - Alerts if drift >5 seconds (indicates NTP misconfiguration)
```

**Solution 4: Tolerance Windows**

```yaml
Chain Verification Rules:

Strict Mode (Default):
  - Capsule N+1 timestamp must be >= Capsule N timestamp
  - Exception: Allow up to 5 second negative drift (clock skew tolerance)
  - If drift >5 seconds: Warning logged, but chain not rejected

Relaxed Mode (Optional):
  - Capsule N+1 timestamp can be up to 5 minutes before Capsule N
  - Use logical clock as source of truth
  - Wall clock timestamp is advisory only

Example Verification:
  Capsule N: timestamp = 14:30:00, logical_clock = 1001
  Capsule N+1: timestamp = 14:29:55, logical_clock = 1002

  Check 1: logical_clock increasing? YES (1002 > 1001) ✅
  Check 2: Wall clock drift = -5 seconds
  Check 3: Drift within tolerance (<5 seconds)? YES ✅
  Result: Chain valid, minor warning logged
```

**Solution 5: Hybrid Timestamps**

```yaml
Store multiple time sources in each capsule:

{
  "timestamps": {
    "local_wall_clock": "2025-10-26T14:30:00.123Z",  # Service's clock
    "monotonic_clock": 1729950600123,                 # Milliseconds since service start
    "logical_clock": 1001,                            # Lamport timestamp
    "trusted_timestamp": "2025-10-26T14:30:03Z"      # Optional: TTA timestamp
  }
}

Verification Priority:
  1. Logical clock: Must be strictly increasing (primary verification)
  2. Trusted timestamp: If present, must be consistent (secondary)
  3. Wall clock: Advisory only, used for human-readable audit reports
```

**Handling Extreme Clock Skew (>5 minutes):**

```yaml
If Service B's clock is 10 minutes behind Service A:

Detection:
  - Capsule N+1 timestamp is 10 minutes before Capsule N
  - System detects: "Extreme clock skew detected"

Response:
  1. Log warning: "Service B clock is 10 minutes behind"
  2. Continue: Logical clock still valid (chain not broken)
  3. Alert ops team: "Fix clock skew on Service B"
  4. Audit report: Flags this capsule with "CLOCK_SKEW_WARNING"

Human Review:
  - Auditor sees: "Capsule 1002 has clock skew warning"
  - Auditor checks: Logical clock is valid (1002 > 1001)
  - Auditor conclusion: Chain integrity intact, but clock needs fixing
```

**Time Travel Prevention:**

```yaml
Impossible Scenario: Capsule claims to be from the future

Detection:
  - Capsule timestamp > current time + 5 minutes
  - Indicates: Clock is set to future, or malicious tampering

Response:
  - Reject capsule: "Timestamp is in the future"
  - Alert: Possible tampering or misconfigured clock
  - Require: Fix clock before continuing

Example:
  Current time: 2025-10-26 14:30:00
  Capsule timestamp: 2025-10-26 15:00:00  # 30 minutes in future
  Result: REJECTED (clock is wrong or malicious)
```

---

### Q9.3: Partial failure semantics (e.g., request succeeds but capsule write fails) and idempotency?

**A: Designed for resilience with clear failure handling:**

**Failure Scenarios & Responses:**

**Scenario 1: Request Succeeds, Capsule Write Fails**

```yaml
What Happens:
  1. Your app calls UATP proxy
  2. UATP creates capsule (in-memory)
  3. UATP forwards request to OpenAI
  4. OpenAI responds successfully
  5. UATP tries to write capsule to database → FAILS (DB down, network issue)
  6. Question: Does your app get the response? YES

Decision: Favor availability over perfect auditability

Behavior:
  ✅ Your app receives OpenAI response (request not blocked)
  ⚠️  Capsule write failed (logged as ERROR)
  🔄 Retry: UATP buffers capsule, retries write every 10 seconds
  💾 Persistence: Capsule buffered to disk (survives UATP restart)
  ⏰ Timeout: After 5 minutes, alert ops team
  📊 Monitoring: "Capsule write failure rate" metric tracked

Why:
  - We don't want to block your production AI requests due to UATP DB issues
  - Capsule eventually written when DB recovers
  - Gap in audit trail is temporary (heals automatically)
```

**Scenario 2: Request Fails, Partial Capsules Created**

```yaml
What Happens:
  1. UATP creates input capsule (successful)
  2. Forwards request to OpenAI
  3. OpenAI fails (timeout, rate limit, etc.)
  4. Question: Do we create output capsule? NO

Behavior:
  ✅ Input capsule written (documents request was made)
  ✅ Failure capsule written (documents OpenAI error)
  ❌ Output capsule NOT created (no response to record)
  🔍 Audit trail: Shows request → failure (complete picture)

Failure Capsule Format:
  {
    "capsule_type": "FAILURE",
    "previous_capsule": "cap_input_001",
    "error": {
      "type": "UPSTREAM_FAILURE",
      "provider": "OpenAI",
      "status_code": 503,
      "message": "Service Unavailable",
      "retry_attempted": true
    },
    "timestamp": "2025-10-26T14:30:05Z"
  }

Why:
  - Audit trail is complete (shows what went wrong)
  - Failures are first-class capsules (accountable)
  - Helps debug: "Did request fail before or after OpenAI?"
```

**Scenario 3: UATP Proxy Crashes Mid-Request**

```yaml
What Happens:
  1. Request received
  2. Input capsule created
  3. Forwarded to OpenAI
  4. UATP proxy crashes (OOM, killed, etc.)
  5. OpenAI responds (but UATP proxy is dead)
  6. Question: Is capsule chain incomplete? YES (temporarily)

Recovery:
  1. UATP proxy restarts (Kubernetes automatically)
  2. Checks for incomplete chains (capsules with no output)
  3. Attempts reconstruction:
     - If response cached: Create output capsule from cache
     - If not cached: Mark chain as "INCOMPLETE"
  4. Audit report: Flags incomplete chains

Incomplete Chain Handling:
  - Audit report shows: "Chain incomplete (proxy failure)"
  - Human review: Determine if this is acceptable
  - Options:
      a) Accept gap (acknowledge infrastructure failure)
      b) Retry request (if idempotent)
      c) Manual reconstruction (if response logged elsewhere)

Why:
  - Honest about failures (don't pretend perfect auditability)
  - Infrastructure failures happen (we document them)
  - Auditors can see: "This gap was due to system failure, not policy violation"
```

**Idempotency:**

**Problem:** If request retried, do we create duplicate capsules?

**Solution: Idempotency Keys**

```yaml
Client-Side Idempotency:
  Your app provides idempotency key (optional but recommended):

  POST /v1/chat/completions
  Headers:
    X-Idempotency-Key: "req_12345_retry_1"

  Body:
    { "messages": [...] }

UATP Behavior:
  1. Receives request with idempotency key "req_12345_retry_1"
  2. Checks: Have we seen this key before? (cache lookup, TTL = 24 hours)
  3. If YES: Return cached response + existing capsule IDs (no new capsules created)
  4. If NO: Process normally, cache response + capsule IDs

Benefits:
  ✅ Safe retries (network failures, timeouts)
  ✅ No duplicate capsules for same logical request
  ✅ Audit trail accurate (one capsule chain per logical request, not per retry)

Example:
  Request 1: Idempotency key = "req_12345", creates capsule chain [cap_001, cap_002]
  Request 2 (retry): Same key → Returns cached response, same capsule IDs
  Audit trail: Shows 1 request (not 2)
```

**Server-Side Idempotency (Without Client Key):**

```yaml
If client doesn't provide idempotency key, UATP generates one:

Idempotency Key = hash(request content + user_id + timestamp_bucket)

Example:
  Request content: "What is 2+2?"
  User ID: user_12345
  Timestamp bucket: "2025-10-26T14:30:00" (rounded to minute)

  Idempotency key = sha256("What is 2+2?" + "user_12345" + "2025-10-26T14:30:00")

Detection Window:
  - If same request from same user within 1 minute → Likely retry
  - Return cached response (avoid duplicate capsules)

Limitation:
  - Doesn't handle retries after 1 minute (new timestamp bucket)
  - Recommendation: Use client-side idempotency keys for reliable retry handling
```

**Capsule Write Retries:**

```yaml
Retry Strategy:

Database Write Fails:
  1. First failure: Retry after 1 second
  2. Second failure: Retry after 5 seconds
  3. Third failure: Retry after 10 seconds
  4. Fourth+ failures: Retry every 30 seconds
  5. After 5 minutes: Alert ops team, continue retrying
  6. Buffer: Capsules buffered to disk (survives restarts)

Max buffer size: 10,000 capsules (configurable)
  - If buffer full: Log error, drop oldest buffered capsules (audit gap)
  - Alert: "Capsule buffer overflow" (critical issue)

Backpressure:
  - If buffer >50% full: Start slowing down requests (rate limiting)
  - Prevents: Complete buffer overflow
  - Alert: "UATP under backpressure, database writes failing"
```

**Monitoring Partial Failures:**

```yaml
Metrics Tracked:

Capsule Write Success Rate:
  - Target: >99.9%
  - Alert if: <99% over 5 minutes
  - Dashboard: Shows write failures in real-time

Incomplete Chain Rate:
  - Target: <0.1%
  - Alert if: >1% (indicates proxy crashes or database issues)

Idempotency Hit Rate:
  - Shows: How many retries are being deduplicated
  - Useful for: Diagnosing client retry behavior

Buffer Utilization:
  - Shows: How many capsules waiting to be written
  - Alert if: >5,000 capsules buffered (database struggling)
```

---

### Q9.4: Can you produce batch attestations (Merkle roots) and anchor them to an external timestamping service?

**A: Yes, with multiple options:**

**Merkle Tree Batch Attestation:**

**Concept:**
```
Instead of individual capsule signatures, create Merkle tree:

Capsule 1 → Hash 1 ──┐
Capsule 2 → Hash 2 ──┼─→ Hash 1-2 ──┐
Capsule 3 → Hash 3 ──┤              ├─→ Merkle Root
Capsule 4 → Hash 4 ──┴─→ Hash 3-4 ──┘

Merkle Root = Single hash representing all 4 capsules
Sign Merkle Root once (instead of signing each capsule)
```

**Implementation:**

```yaml
Batch Attestation Process:

Step 1: Accumulate Capsules
  - Buffer: Collect capsules for 1 minute (or 1,000 capsules, whichever first)

Step 2: Build Merkle Tree
  - Leaf nodes: Hash of each capsule
  - Internal nodes: Hash(left_child + right_child)
  - Root node: Single hash representing entire batch

Step 3: Sign Merkle Root
  - Sign root with Dilithium3
  - OR send to external TSA for timestamp signature

Step 4: Store Merkle Proof
  - Each capsule gets Merkle proof (path to root)
  - Merkle root + signature stored separately

Capsule Format (with Merkle proof):
  {
    "capsule_id": "cap_001",
    "content": { ... },
    "merkle_proof": {
      "root": "sha256:abc123...",
      "path": [
        {"side": "right", "hash": "sha256:def456..."},
        {"side": "left", "hash": "sha256:ghi789..."}
      ],
      "batch_id": "batch_20251026_143000",
      "signature": "dilithium3:xyz..."
    }
  }

Verification:
  1. Hash capsule content → leaf hash
  2. Apply Merkle proof path → compute root
  3. Verify: Computed root matches signed root
  4. Verify: Root signature is valid
  Result: Capsule is part of attested batch ✅
```

**External Timestamping (RFC 3161):**

```yaml
Integration with Timestamp Authority (TSA):

Supported TSAs:
  ✅ NIST Internet Time Service
  ✅ Bundesdruckerei (Germany)
  ✅ DigiCert TSA
  ✅ Custom RFC 3161-compliant TSAs

Process:
  1. Generate Merkle root (batch of 1,000 capsules)
  2. Send Merkle root hash to TSA
  3. TSA returns signed timestamp token
  4. Store timestamp token with batch

Timestamp Token (RFC 3161):
  {
    "hash_algorithm": "SHA-256",
    "message_hash": "sha256:merkle_root_abc123...",
    "timestamp": "2025-10-26T14:30:05.123Z",
    "tsa_signature": "base64-tsa-signature",
    "tsa_certificate_chain": ["cert1", "cert2", ...],
    "policy_oid": "1.2.3.4.5"  # TSA policy
  }

Benefits:
  - Legal non-repudiation (proves capsules existed at this time)
  - Independent third party (TSA is trusted, not us)
  - Standards-compliant (RFC 3161, widely accepted)

Cost:
  - Latency: +100-300ms per batch (network round-trip to TSA)
  - Fee: Some TSAs charge per timestamp (~$0.01-$0.05 per batch)
  - Recommendation: Batch 1,000+ capsules per timestamp (amortize cost)

Example Cost:
  1 million capsules/month
  ÷ 1,000 capsules/batch = 1,000 batches
  × $0.02 per timestamp = $20/month (negligible)
```

**Blockchain Anchoring (Optional):**

```yaml
For immutable public record, anchor to blockchain:

Supported Blockchains:
  - Bitcoin (via OpenTimestamps)
  - Ethereum (smart contract)
  - Custom permissioned blockchain

Process:
  1. Generate Merkle root (batch of capsules)
  2. Submit Merkle root to blockchain
  3. Wait for block confirmation
  4. Record: Block number, transaction hash

Example (OpenTimestamps):
  1. Merkle root: sha256:abc123...
  2. Submit to OpenTimestamps
  3. OpenTimestamps batches with other submissions
  4. Anchors to Bitcoin blockchain (next block)
  5. Proof: "Merkle root existed before Bitcoin block 800,000"

Benefits:
  - Public verifiability (anyone can verify, no need to trust UATP)
  - Immutable (blockchain is tamper-proof)
  - Long-term preservation (Bitcoin will outlive any company)

Cost:
  - Bitcoin: ~$0.50 per anchor (batched with other submissions via OpenTimestamps)
  - Ethereum: ~$5-$50 per anchor (depends on gas prices)
  - Recommendation: Anchor daily or weekly (not real-time)

Limitation:
  - Latency: 10+ minutes (wait for blockchain confirmation)
  - Not suitable for real-time verification (use for long-term preservation)
```

**Comparison of Approaches:**

```yaml
Individual Signatures (Current Default):
  Pros:
    ✅ Immediate verification (no batch wait time)
    ✅ Simple (each capsule self-contained)
  Cons:
    ❌ Storage overhead (3.3 KB signature per capsule)
    ❌ Signing overhead (5ms per capsule)

Merkle Batch Attestation:
  Pros:
    ✅ Efficient storage (1 signature per batch, not per capsule)
    ✅ Efficient signing (1 signing operation per batch)
  Cons:
    ❌ Delayed attestation (wait for batch to fill)
    ❌ Requires Merkle proof storage (extra data per capsule)
    ❌ If root signature lost, entire batch unverifiable

External Timestamping (TSA):
  Pros:
    ✅ Legal non-repudiation (trusted third party)
    ✅ Independent verification (TSA is neutral)
    ✅ Standards-compliant (RFC 3161)
  Cons:
    ❌ Cost (small fee per timestamp)
    ❌ Latency (+100-300ms per batch)
    ❌ Dependency (TSA must remain operational)

Blockchain Anchoring:
  Pros:
    ✅ Public verifiability (no trust in UATP required)
    ✅ Immutable (blockchain consensus)
    ✅ Long-term preservation (decades+)
  Cons:
    ❌ Latency (10+ minutes for confirmation)
    ❌ Cost (blockchain transaction fees)
    ❌ Not real-time (unsuitable for immediate verification)
```

**Hybrid Approach (Recommended for Enterprise):**

```yaml
Use all three methods in parallel:

Real-Time Verification:
  - Individual Dilithium3 signatures (immediate verification)

Batch Efficiency:
  - Hourly Merkle batches (reduce storage overhead)
  - Store Merkle proof with each capsule

Legal Non-Repudiation:
  - Daily timestamp via RFC 3161 TSA (legal compliance)

Long-Term Preservation:
  - Weekly anchor to Bitcoin (via OpenTimestamps, public verifiability)

Result:
  - Immediate: Verify individual capsule with Dilithium3 signature
  - Efficient: Bulk verification using Merkle batches
  - Legal: TSA timestamp for court evidence
  - Archival: Blockchain anchor for long-term preservation
```

**Configuration:**

```yaml
# UATP config for batch attestation

batch_attestation:
  enabled: true
  batch_size: 1000  # Capsules per batch
  batch_interval: 60  # Seconds (batch even if size not reached)

  merkle_tree:
    enabled: true
    hash_algorithm: "SHA-256"

  external_timestamp:
    enabled: true
    tsa_url: "https://timestamp.nist.gov/timestamp"
    tsa_policy: "1.3.6.1.4.1.6449.1.2.1"
    retry_attempts: 3

  blockchain_anchor:
    enabled: false  # Optional (disabled by default due to latency)
    provider: "opentimestamps"
    frequency: "daily"  # Or "weekly"

# Individual signatures still generated (for immediate verification)
individual_signatures:
  enabled: true  # Always on (backward compatibility)
```

---

### Q9.5: Salted hashing / collision resistance for "content fingerprints"; guidance to avoid sensitive-data reconstruction from metadata?

**A: Multiple layers of protection:**

**Content Fingerprinting Strategy:**

**Problem: Hashing Sensitive Content**
```
Naive approach:
  Input: "Patient John Smith has diabetes"
  Hash: sha256("Patient John Smith has diabetes")
  → Hash = abc123...

Risk:
  - Rainbow tables: Pre-computed hashes of common phrases
  - Brute force: Try hashing "Patient [name] has [disease]" until match
  - Result: Can reverse hash to discover sensitive content
```

**Solution 1: Salted Hashing**

```yaml
Add random salt before hashing:

Process:
  1. Generate random salt (32 bytes)
  2. Combine: salted_content = salt + original_content
  3. Hash: sha256(salted_content)
  4. Store: salt + hash (not original content)

Example:
  Salt: "a1b2c3d4..." (32 bytes random)
  Content: "Patient John Smith has diabetes"
  Salted: "a1b2c3d4...Patient John Smith has diabetes"
  Hash: sha256(salted) = "xyz789..."

  Stored in capsule:
    {
      "content_hash": "sha256:xyz789...",
      "salt": "a1b2c3d4..."  # Public (doesn't reveal content)
    }

Verification (Legitimate):
  1. Retrieve salt from capsule
  2. Re-compute: sha256(salt + claimed_content)
  3. Compare: Does it match stored hash? ✅

Attack Attempt (Illegitimate):
  1. Attacker has hash + salt
  2. Attempts: Brute force with salt
  3. Problem: Salt makes each hash unique (rainbow tables useless)
  4. Even if content is common, salted hash is unique
```

**Solution 2: Content Categories (Not Content)**

```yaml
Instead of hashing full content, hash categories:

Bad (Leaks Info):
  content_summary: "Patient John Smith has diabetes"
  → Can reverse engineer PHI

Good (Privacy-Preserving):
  content_category: "medical_diagnosis_query"
  content_sensitivity: "PHI_DETECTED"
  content_length: 45  # Characters
  content_language: "en"

  → Cannot reverse engineer actual content

Capsule stores:
  {
    "content_fingerprint": {
      "category": "medical_diagnosis_query",
      "sensitivity_flags": ["PHI", "USER_DATA"],
      "content_type": "text/plain",
      "char_count": 45,
      "word_count": 6,
      "detected_entities": ["PERSON", "MEDICAL_CONDITION"],  # Types, not actual entities!
      "salted_hash": "sha256:abc123..."  # For integrity, not content recovery
    }
  }

Privacy preserved:
  ❌ Cannot reconstruct: "Patient John Smith has diabetes"
  ✅ Can know: "This was a medical query with PHI"
```

**Solution 3: HMAC (Keyed Hashing)**

```yaml
Use secret key for hashing (instead of public salt):

HMAC Process:
  1. Secret key: Known only to you (not in capsules)
  2. HMAC: hash(secret_key + content)
  3. Store: HMAC output (not key, not content)

Example:
  Secret key: "your-hmac-secret" (stored in your KMS)
  Content: "Patient John Smith has diabetes"
  HMAC: hmac_sha256(key="your-hmac-secret", msg=content)
  → Output: "def456..."

  Stored in capsule:
    {
      "content_hmac": "hmac-sha256:def456..."
    }

Verification:
  1. You provide content for verification
  2. Recompute HMAC using same secret key
  3. Compare: Does it match? ✅

Attack Resistance:
  - Attacker has HMAC output but not secret key
  - Cannot reverse engineer content (even with brute force)
  - Rainbow tables useless (keyed hash)

Key Management:
  - Store secret key in KMS (AWS KMS, Azure Key Vault)
  - Rotate key periodically (every 90 days)
  - Old keys retained for verification (can verify old capsules)
```

**Solution 4: Zero-Knowledge Proofs (Advanced)**

```yaml
Prove properties without revealing content:

Example:
  Statement: "This content contains PHI"
  ZK Proof: Cryptographic proof of statement (without revealing actual content)

Capsule stores:
  {
    "content_properties": {
      "contains_phi": true,
      "zk_proof": "base64-zk-proof"  # Proves PHI present, doesn't reveal what PHI
    }
  }

Verification:
  1. Verify ZK proof (cryptographic verification)
  2. Result: "Yes, content contained PHI" ✅
  3. Actual content: Unknown (zero knowledge)

Status in UATP:
  - Currently: Research prototype
  - Production: Not yet (performance overhead too high)
  - Timeline: Considering for v2.0 (2026)
```

**Collision Resistance:**

**Problem:** What if two different contents hash to the same value?

```yaml
Hash Function Choice:

SHA-256:
  - Collision resistance: 2^128 operations to find collision
  - Estimated time: Billions of years (even with quantum computers)
  - Verdict: Practically collision-resistant ✅

SHA-384 (For Chain Hashing):
  - Collision resistance: 2^192 operations
  - Extra security margin for chain integrity
  - Used for: Linking capsules in chain

Birthday Paradox Consideration:
  - After 2^128 hashes (340 undecillion), 50% chance of collision
  - At 1 million capsules/second: Would take 10^31 years
  - Verdict: Not a practical concern for our use case

If SHA-256 Breaks:
  - Migration plan (see Algorithm Agility section)
  - Upgrade to SHA-3, BLAKE3, or newer algorithm
  - Old capsules: Still verifiable (algorithm ID stored in capsule)
```

**Guidance to Customers: Avoid Sensitive Data in Metadata**

**Best Practices Document:**

```yaml
DO:
  ✅ Store content categories ("medical_query", not "diabetes diagnosis")
  ✅ Store sensitivity flags ("PHI_DETECTED", not actual PHI)
  ✅ Store counts ("6 words", not the actual words)
  ✅ Store types ("PERSON entity detected", not "John Smith")
  ✅ Use salted hashes for integrity (not content recovery)

DON'T:
  ❌ Store actual user names in metadata
  ❌ Store actual diagnoses in summaries
  ❌ Store email addresses, phone numbers in logs
  ❌ Store full queries in "content_summary" field
  ❌ Use unsalted hashes of sensitive data

Example Configuration:
  # Good: Privacy-preserving
  capsule_metadata:
    content_summary_mode: "category_only"
    include_entity_types: true
    include_entity_values: false  # Don't include actual names/values!
    hashing:
      method: "salted_sha256"
      salt_length: 32

  # Bad: Leaks data
  capsule_metadata:
    content_summary_mode: "full_text"  # ❌ Stores actual content
    include_entity_values: true  # ❌ Stores actual names
    hashing:
      method: "sha256"  # ❌ No salt (vulnerable to rainbow tables)
```

**Automated PII/PHI Detection:**

```yaml
UATP Scanning (Before Storing Metadata):

Process:
  1. Content received (e.g., user query)
  2. PII/PHI detection: Scan for patterns
     - Names (regex: \b[A-Z][a-z]+ [A-Z][a-z]+\b)
     - SSN (regex: \b\d{3}-\d{2}-\d{4}\b)
     - Email (regex: \b[\w.-]+@[\w.-]+\.\w+\b)
     - Medical terms (dictionary lookup)
  3. Redaction: Replace with categories
     - "John Smith" → "[PERSON]"
     - "john@example.com" → "[EMAIL]"
     - "diabetes" → "[MEDICAL_CONDITION]"
  4. Store redacted version in metadata

Capsule metadata (safe):
  {
    "content_summary": "Patient [PERSON] has [MEDICAL_CONDITION]",
    "entities_detected": ["PERSON", "MEDICAL_CONDITION"],
    "phi_present": true
  }

Original content:
  - NOT stored in capsule
  - Only hash (salted) stored
  - Actual content: Transient (passed through, not retained)
```

---




---

# 10. Quick Start Guide

## 5 Steps to Launch Your UATP Pilot

### Step 1: Discovery Call (Week 0)
```
Duration: 1 hour
Participants: Your team + UATP engineering

Agenda:
  ✅ Understand your use case
  ✅ Identify 1 AI workflow for pilot
  ✅ Review technical requirements
  ✅ Set success criteria

Outcome: Pilot agreement signed
```

### Step 2: Installation (Week 1)
```
Duration: 3-5 days
Your effort: 4-8 hours (engineering time)

Tasks:
  ✅ Install UATP SDK (Python: pip install uatp)
  ✅ Configure credentials (API keys)
  ✅ Integrate with 1 AI workflow
  ✅ Generate first capsule

Verification:
  $ uatp verify --chain-id <your-first-chain>
  Result: "✅ All signatures valid"
```

### Step 3: Shadow Mode (Weeks 2-3)
```
Duration: 2 weeks
Your effort: 2 hours/week (monitoring)

Tasks:
  ✅ Deploy HIPAA/GDPR template pack
  ✅ Run in shadow mode (detect, don't block)
  ✅ Capture 10,000+ interactions
  ✅ Review false positive rate

Verification:
  Dashboard shows: "X violations detected, 0 blocked"
  False positive rate: <5% (tune policies)
```

### Step 4: Enforcement Testing (Weeks 4-6)
```
Duration: 3 weeks
Your effort: 4 hours/week (tuning)

Tasks:
  ✅ Enable enforcement (10% traffic)
  ✅ Monitor blocked requests
  ✅ Tune policies (reduce false positives to <2%)
  ✅ Test circuit breaker

Verification:
  Live demo: Request blocked → Capsule shows refusal reason
```

### Step 5: Audit Report (Weeks 7-9)
```
Duration: 3 weeks
Your effort: 2 hours (review)

Tasks:
  ✅ Generate audit report for legal/compliance
  ✅ Present to stakeholders
  ✅ Decide: Go to production or extend pilot

Verification:
  Legal team confirms: "This is regulator-ready"
  Decision point: Convert to annual subscription?
```

---

## Quick Reference Card

**What is UATP?**
> Runtime trust layer for AI - captures cryptographically-sealed audit trails

**Who needs it?**
> Healthcare, finance, insurance using AI in regulated workflows

**Key benefit?**
> 3 weeks + $150K to get audit proof → 30 minutes included

**Pilot cost?**
> $20K for 90 days (100K interactions)

**Pilot timeline?**
> 12 weeks: Install → Shadow → Enforce → Report

**Risk?**
> Low - 30-day exit, full data export, no lock-in

**Next step?**
> Email: pilot@uatp.com or Schedule: calendly.com/uatp/pilot

---

# 11. FAQ

## Common Questions and Objections

### Q: Isn't this just logging?

**A:** No. Key differences:

| Feature | Traditional Logs | UATP |
|---------|-----------------|------|
| Can be edited? | ✅ Yes | ❌ No (cryptographic) |
| Proves policy ran? | ❌ No | ✅ Yes (sealed capsule) |
| Regulator-ready? | ❌ Takes weeks | ✅ 30 minutes |
| Tamper-proof? | ❌ No | ✅ Post-quantum crypto |

Logs record what happened. UATP *proves* what happened.

---

### Q: Won't this slow down my AI?

**A:** Minimal impact:

```
Latency Impact:
  P50: +12ms
  P95: +28ms
  P99: +45ms

For perspective:
  - Network latency: 50-200ms
  - AI inference: 500-5000ms
  - UATP overhead: <50ms (<1% of total)

Real customer feedback: "We can't even measure the difference"
```

**Optimization:** UATP writes capsules asynchronously. Your AI response returns immediately.

---

### Q: What if UATP goes down?

**A:** Designed for graceful degradation:

```
UATP Failure Modes:

Mode 1: Fail-Open (Default)
  - UATP down → AI requests still succeed
  - No capsules written (logged locally)
  - Restore UATP → Backfill capsules

Mode 2: Fail-Closed (High-Security)
  - UATP down → AI requests blocked
  - Ensures no unaudited decisions
  - Your choice per workflow

Uptime SLA: 99.9% (43 min/month downtime)
```

**Honest assessment:** If audit trails are mission-critical, deploy UATP with redundancy (multi-region). If nice-to-have, use fail-open mode.

---

### Q: Do you store our AI prompts/responses?

**A:** Only metadata + hashes (not full content):

```
What UATP stores:

Stored:
  ✅ Timestamp, user ID, workflow name
  ✅ Policy check results (pass/fail)
  ✅ Content hash (SHA-256)
  ✅ Cryptographic signatures
  ✅ Model used, tokens, latency

NOT Stored:
  ❌ Full prompt text (unless you configure it)
  ❌ Full AI response (unless you configure it)
  ❌ PII/PHI (unless explicitly enabled)

Your choice: Configure to store full content OR just hashes
```

**BYOK (Bring Your Own Key):** Encrypt capsules with your keys. UATP can't decrypt even if we wanted to.

---

### Q: What if we already have MLOps/monitoring tools?

**A:** UATP complements, doesn't replace:

```
Your Stack:
  Datadog/Splunk → Operational monitoring (uptime, errors)
  MLflow/Weights & Biases → Model performance (accuracy, drift)
  UATP → Compliance & audit trails (regulatory proof)

Integration: UATP exports metrics to your observability stack
```

**Analogy:** You need both smoke detectors (monitoring) AND a fire extinguisher (UATP audit trails).

---

### Q: How do we prove UATP itself isn't compromised?

**A:** Open source + independent verification:

```
Trust Mechanisms:

1. Open Source Core
   - Core engine: GitHub (MIT license)
   - Community review
   - Reproducible builds

2. Independent Verification
   - Standalone verification tool (no UATP backend)
   - You can verify signatures offline
   - Cryptographic proofs are mathematical

3. Third-Party Audits
   - Annual security audit (published)
   - Penetration testing (quarterly)
   - Bug bounty program

Honest answer: You can't 100% trust any vendor.
But you CAN verify our cryptographic claims independently.
```

---

### Q: What happens when you get acquired or shut down?

**A:** Self-hosting option + open source:

```
Exit Strategies:

Option 1: Self-Host
  - Core engine: Open source
  - Deploy on your infrastructure
  - We provide migration support

Option 2: Data Export
  - Full export (JSON, CSV, SQL)
  - Verification scripts (open source)
  - No UATP backend required

Option 3: Fork
  - Open source license (MIT)
  - Fork and maintain yourself
  - Community support

Contract guarantee: If we're acquired, you get 12 months notice
+ option to self-host at no additional cost
```

---

### Q: Why should we trust you (no customers yet)?

**A:** Fair question. Here's our argument:

```
Why Trust UATP:

1. Technical Proof
   ✅ 363 production modules (GitHub)
   ✅ 71% test coverage
   ✅ Demo works end-to-end
   ✅ Post-quantum cryptography (NIST approved)

2. Risk Mitigation
   ✅ 90-day pilot (prove it works)
   ✅ Fixed price (no surprise bills)
   ✅ Open source core (no lock-in)
   ✅ 30-day exit (clean offboarding)

3. Market Timing
   ✅ EU AI Act enforcement: 2025
   ✅ Insurance demanding AI audit trails
   ✅ No mature competitors
   ✅ First-mover advantage for you

Honest answer: You're taking a bet on us.
We're early. But the pilot is designed to prove we're worth it.
```

---

### Q: Can we negotiate pricing?

**A:** Yes, for:

```
Negotiable:
  ✅ Multi-year contracts (discount)
  ✅ High volume (custom pricing)
  ✅ Multiple workflows (bundle discount)
  ✅ Early customers (founder pricing)

Non-Negotiable:
  ❌ Pilot pricing ($20K fixed)
  ❌ Standard tiers (listed pricing)
```

**Founder pricing (first 10 customers):**
- 20% off year 1
- Price lock for 3 years
- Priority roadmap input

---

# 12. UATP vs Alternatives

## Comparison Table

### UATP vs Traditional Application Logs

| Feature | Application Logs | UATP |
|---------|-----------------|------|
| **Tamper-proof** | ❌ Logs can be edited/deleted | ✅ Cryptographic signatures |
| **Real-time policy enforcement** | ❌ No enforcement | ✅ Block violations before they happen |
| **AI-specific context** | ❌ Generic I/O logging | ✅ Captures reasoning, policies, decisions |
| **Regulator-ready reports** | ❌ Takes weeks to compile | ✅ Generate in 30 minutes |
| **Compliance focus** | ❌ Not designed for compliance | ✅ Built for HIPAA/GDPR/EU AI Act |
| **Cost** | Free (built-in) | $36K/year |
| **Best for** | Debugging, troubleshooting | Regulatory compliance, litigation defense |

**Verdict:** Use both. Logs for debugging, UATP for compliance.

---

### UATP vs Monitoring Tools (Datadog, Splunk, etc.)

| Feature | Monitoring Tools | UATP |
|---------|-----------------|------|
| **Focus** | Operational health (uptime, errors) | Compliance & audit trails |
| **AI-specific** | ❌ No | ✅ Yes |
| **Policy enforcement** | ❌ Reactive (alert after) | ✅ Preventive (block before) |
| **Cryptographic proof** | ❌ No | ✅ Yes |
| **Audit reports** | ❌ Not compliance-focused | ✅ Regulator-ready |
| **Integration** | ✅ Monitors everything | ✅ Exports metrics to your monitoring |
| **Cost** | $100-500/host/month | $3K/month (all workflows) |

**Verdict:** Complementary. Monitoring for ops, UATP for compliance.

---

### UATP vs MLOps Platforms (MLflow, Weights & Biases)

| Feature | MLOps Platforms | UATP |
|---------|-----------------|------|
| **Focus** | Model performance (accuracy, drift) | Runtime compliance (policy enforcement) |
| **Training vs Inference** | Training & evaluation | Inference & production |
| **Policy enforcement** | ❌ No | ✅ Yes (HIPAA, GDPR, etc.) |
| **Audit trails** | Model metrics | Decision-level audit trails |
| **Cryptographic proof** | ❌ No | ✅ Yes |
| **Compliance reports** | ❌ No | ✅ Yes |

**Verdict:** Different layers. MLOps for model quality, UATP for decision compliance.

---

### UATP vs Building In-House

| Aspect | Build In-House | Buy UATP |
|--------|---------------|----------|
| **Time to production** | 12-18 months | 90 days (pilot) |
| **Engineering cost** | $500K-1M (2-3 engineers) | $36K/year |
| **Maintenance** | Ongoing (security, updates) | Managed service |
| **Cryptography expertise** | Need to hire | Included |
| **Compliance templates** | Build from scratch | Pre-built (HIPAA, GDPR, etc.) |
| **Regulatory risk** | High (unproven) | Lower (battle-tested crypto) |
| **Control** | ✅ Full control | ⚠️  Vendor dependency |
| **Total 3-year cost** | $1.5M+ | $108K |

**Build if:**
- You have crypto expertise in-house
- AI compliance is your core competency
- You need 100% control

**Buy if:**
- You want to focus on your product
- Compliance is a requirement, not differentiator
- 90-day pilot proves value

---

### UATP vs "Just Use Blockchain"

| Feature | Blockchain | UATP |
|---------|-----------|------|
| **Latency** | 1-30 seconds per transaction | <50ms overhead |
| **Cost per transaction** | $0.01-$10 (gas fees) | $0.0003 (included) |
| **Scalability** | 10-1000 TPS | 10,000+ TPS |
| **Privacy** | ❌ Public by default | ✅ Private by default |
| **AI-specific features** | ❌ None | ✅ Policy checks, reasoning capture |
| **Complexity** | High (wallets, gas, consensus) | Low (SDK integration) |

**Verdict:** Blockchain is overkill for most use cases. UATP provides cryptographic proof without blockchain overhead.

**Note:** UATP can *anchor* to blockchain for timestamping (optional), giving you both speed AND public verifiability.

---

## Summary: When to Use UATP

✅ **Use UATP if:**
- You use AI in regulated industries (healthcare, finance, insurance)
- You need audit trails for compliance (HIPAA, GDPR, EU AI Act)
- Board/legal wants proof of AI governance
- Insurance wants evidence of controls
- You want to reduce liability exposure

❌ **Don't use UATP if:**
- Unregulated consumer app with no compliance needs
- Internal tools with no audit requirements
- Research projects (unless publishing)
- You already built a comprehensive in-house solution

**Bottom line:** If you're asking "how do I prove my AI acted correctly?" - you need UATP.

---

