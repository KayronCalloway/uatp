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

# 1. Introduction - What is UATP?

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

# 2. Commercials & Risk

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

