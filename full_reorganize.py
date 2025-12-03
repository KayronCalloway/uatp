#!/usr/bin/env python3
"""
Complete reorganization of TECHNICAL_QA_ENTERPRISE_BUYERS.md
- Reorder sections by learning progression
- Reorder questions within sections from basic to advanced
- Renumber all questions properly
"""

import re


def full_reorganize():
    """Complete reorganization for learning flow"""

    input_file = "docs/TECHNICAL_QA_ENTERPRISE_BUYERS_OLD.md"  # Use the original
    output_file = "docs/TECHNICAL_QA_ENTERPRISE_BUYERS.md"

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by ## headers (main sections)
    parts = re.split(r"\n## ", content)
    header = parts[0]  # Everything before first ##
    section_texts = parts[1:]

    # Parse into structured data
    sections = {}
    for section_text in section_texts:
        lines = section_text.split("\n", 1)
        section_title = lines[0].strip()
        section_body = lines[1] if len(lines) > 1 else ""

        # Extract questions from this section
        questions = []
        question_parts = re.split(r"\n### Q\d+\.\d+:", section_body)

        if len(question_parts) > 1:
            # First part is intro text before questions
            intro = question_parts[0]

            # Parse each question
            for i, q_text in enumerate(question_parts[1:], 1):
                # Extract question title (first line)
                q_lines = q_text.split("\n", 1)
                q_title = q_lines[0].strip()
                q_body = q_lines[1] if len(q_lines) > 1 else ""

                questions.append({"title": q_title, "body": q_body})

            sections[section_title] = {"intro": intro, "questions": questions}
        else:
            sections[section_title] = {"intro": section_body, "questions": []}

    # Define section order and question reordering
    section_order = [
        {
            "old": "7. Product Experience",
            "new": "1. Product Experience",
            "question_order": [
                "Is there a dashboard for searching chains, verifying signatures, and generating reports?",
                "Are there pre-built template packs (HIPAA, GDPR, PCI, EU AI Act)?",
                "Can we set up alerting on policy violations, refusals, or tamper detection?",
                "Is there onboarding documentation, runbooks, and training available?",
            ],
        },
        {
            "old": "8. Commercials & Risk",
            "new": "2. Commercials & Risk",
            "question_order": [
                "What are the proof milestones in the pilot to validate the system works?",
                "What protections exist against price increases or unexpected charges?",
                "Can we speak to a reference customer before committing?",
                "If we decide UATP isn't right for us, what's the offboarding plan?",
            ],
        },
        {
            "old": "4. Integration Surface",
            "new": "3. Integration Surface",
            "question_order": [
                "What's the full provider support matrix (OpenAI, Anthropic, Vertex AI, Azure OpenAI, Bedrock, others)?",
                "Does it support streaming, function calling, vision, RAG, and batch API modes?",
                "For non-Python stacks, is there a gRPC or REST API?",
                "How does UATP integrate with existing observability (Prometheus, Datadog, Splunk, CloudWatch)?",
                "What's the API versioning and backwards compatibility policy?",
            ],
        },
        {
            "old": "5. Enforcement & Governance",
            "new": "4. Enforcement & Governance",
            "question_order": [
                "How do you track false positives/negatives and tune policies?",
                "What's the override workflow if we need to bypass a policy in an emergency?",
                "Can we define policies-as-code and test them in CI/CD before production?",
            ],
        },
        {
            "old": "1. Deployment, Reliability & Ops",
            "new": "5. Deployment, Reliability & Ops",
            "question_order": [
                "What are your SLO/SLA targets (availability %, P95/P99 latency) and what are the credits if they're missed?",
                "Throughput limits per deployment? Any rate-limiting on the proxy/SDK?",
                "DR (disaster recovery): what's the RPO/RTO, backup cadence, region failover approach?",
                "Does it support canary/blue-green deployments, gradual rollout?",
                "How do we isolate dev/staging/prod environments? Any multi-tenancy support?",
            ],
        },
        {
            "old": "2. Security & Compliance",
            "new": "6. Security & Compliance",
            "question_order": [
                "Do you sign a BAA (HIPAA) or DPA (GDPR)? What compliance certs do you hold?",
                "Can we use our own keys (BYOK) or do you manage them?",
                "Supply-chain security: signed releases, SBOMs, dependency scanning?",
                "Pen testing cadence? Bug bounty program?",
                "How does access control work (SSO/SAML/OIDC, RBAC/ABAC, SCIM provisioning)?",
            ],
        },
        {
            "old": "6. Data Handling Nuances",
            "new": "7. Data Handling Nuances",
            "question_order": [
                "What exactly is in the capsule metadata schema, and can it change backward-incompatibly?",
                "Can we enforce data residency at a finer grain (per-workflow or per-tenant)?",
                "How do you handle GDPR data subject requests (Article 15 for access, Article 17 for deletion)?",
                "What about retention policies and automated deletion?",
            ],
        },
        {
            "old": "3. Capsule Integrity & Crypto Details",
            "new": "8. Capsule Integrity & Crypto Details",
            "question_order": [
                "Which post-quantum algorithm (Dilithium, Kyber, etc.)? Can we swap algorithms if a break is discovered?",
                "How do you handle clock skew across distributed systems when signing capsules?",
                "If a capsule fails to write (e.g., database down), does the AI request still succeed? What's the fallback semantics?",
                "Are capsule chains Merkle trees? Can we anchor them to a blockchain for timestamping?",
                "Do you use salted hashing for PII to prevent rainbow table attacks in audit logs?",
            ],
        },
    ]

    # Build new document
    new_header = """# UATP Technical Q&A for Enterprise Buyers

**Version:** 1.0
**Date:** October 26, 2025
**Audience:** Technical decision-makers, security teams, compliance officers
**Purpose:** Comprehensive answers to enterprise buyer technical questions

**Organization:** Learning progression - start with "What is UATP?" and progress to deep cryptographic details

---

## How to Read This Document

This Q&A is organized as a **learning journey**:

1. **Start with Section 1-2** if you're new to UATP (product overview, business terms)
2. **Read Sections 3-4** when you're ready to integrate (APIs, policies)
3. **Review Section 5** before production deployment (operations, scaling)
4. **Dive into Sections 6-8** for deep technical validation (security, crypto)

Each section progresses from basic to advanced questions.

---

## Table of Contents

### Understanding UATP (Start Here)
1. [Product Experience](#1-product-experience) - Dashboard, templates, training
2. [Commercials & Risk](#2-commercials--risk) - Pricing, pilots, offboarding

### Using UATP (Integration & Daily Operations)
3. [Integration Surface](#3-integration-surface) - APIs, SDKs, providers
4. [Enforcement & Governance](#4-enforcement--governance) - Policies, overrides

### Operating UATP (Production Operations)
5. [Deployment, Reliability & Ops](#5-deployment-reliability--ops) - SLOs, scaling, DR

### Technical Deep Dives (Advanced Topics)
6. [Security & Compliance](#6-security--compliance) - BAA/DPA, key management
7. [Data Handling Nuances](#7-data-handling-nuances) - GDPR, retention
8. [Capsule Integrity & Crypto Details](#8-capsule-integrity--crypto-details) - Post-quantum crypto

---

"""

    new_content = new_header

    # Rebuild document in new order
    for section_spec in section_order:
        old_title = section_spec["old"]
        new_title = section_spec["new"]
        question_order = section_spec["question_order"]

        if old_title in sections:
            section_data = sections[old_title]

            # Write section header
            new_content += f"## {new_title}\n\n"

            # Write intro (if any)
            if section_data["intro"].strip():
                new_content += section_data["intro"].strip() + "\n\n"

            # Reorder and renumber questions
            section_num = new_title.split(".")[0]

            # Create question lookup
            question_lookup = {}
            for q in section_data["questions"]:
                question_lookup[q["title"]] = q["body"]

            # Write questions in specified order
            for q_num, q_title in enumerate(question_order, 1):
                if q_title in question_lookup:
                    new_content += f"### Q{section_num}.{q_num}: {q_title}\n\n"
                    new_content += question_lookup[q_title].strip() + "\n\n---\n\n"
                else:
                    print(f"⚠️  Question not found: {q_title}")

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ Fully reorganized document: {output_file}")
    print(f"📊 Sections: {len(section_order)}")
    print(f"📄 Total size: {len(new_content)} characters")

    return output_file


if __name__ == "__main__":
    full_reorganize()
