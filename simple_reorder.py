#!/usr/bin/env python3
"""
Simple section reordering - just move sections around, keep content intact
"""

import re


def simple_reorder():
    input_file = "docs/TECHNICAL_QA_ENTERPRISE_BUYERS_OLD.md"
    output_file = "docs/TECHNICAL_QA_ENTERPRISE_BUYERS.md"

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by ## headers
    parts = re.split(r"\n(?=## \d+\.)", content)
    header = parts[0]  # Everything before first ## X.
    section_parts = parts[1:]

    # Build section dictionary
    sections = {}
    for part in section_parts:
        # Extract section number and title
        match = re.match(r"## (\d+)\. (.+?)\n", part)
        if match:
            num = int(match.group(1))
            title = match.group(2)
            sections[num] = {"title": title, "content": part}

    # Define new header
    new_header = """# UATP Technical Q&A for Enterprise Buyers

**Version:** 1.0
**Date:** October 26, 2025
**Audience:** Technical decision-makers, security teams, compliance officers
**Purpose:** Comprehensive answers to enterprise buyer technical questions

**Organization:** Learning progression from "What is UATP?" to deep cryptographic implementation details.

---

## How to Read This Document

📖 **New to UATP?** Start with Sections 1-2 (Product overview, business terms)
🔧 **Evaluating integration?** Jump to Sections 3-4 (APIs, policies)
⚙️ **Preparing for production?** Review Sections 5-6 (Operations, security)
🔬 **Need technical validation?** Deep dive into Sections 7-8 (Data handling, cryptography)

Each section progresses from basic to advanced questions.

---

## Table of Contents

### 📘 Understanding UATP (Start Here)
1. [Product Experience](#1-product-experience) - Dashboard, templates, training
2. [Commercials & Risk](#2-commercials--risk) - Pricing, pilots, offboarding

### 🔧 Using UATP (Integration & Daily Use)
3. [Integration Surface](#3-integration-surface) - APIs, SDKs, providers
4. [Enforcement & Governance](#4-enforcement--governance) - Policies, overrides

### ⚙️ Operating UATP (Production Deployment)
5. [Deployment, Reliability & Ops](#5-deployment-reliability--ops) - SLOs, scaling, DR

### 🔬 Technical Deep Dives (Advanced Topics)
6. [Security & Compliance](#6-security--compliance) - BAA/DPA, key management
7. [Data Handling Nuances](#7-data-handling-nuances) - GDPR, retention
8. [Capsule Integrity & Crypto Details](#8-capsule-integrity--crypto-details) - Post-quantum crypto

---

"""

    # Section mapping: old number → new number
    mapping = {
        7: 1,  # Product Experience
        8: 2,  # Commercials & Risk
        4: 3,  # Integration Surface
        5: 4,  # Enforcement & Governance
        1: 5,  # Deployment, Reliability & Ops
        2: 6,  # Security & Compliance
        6: 7,  # Data Handling Nuances
        3: 8,  # Capsule Integrity & Crypto Details
    }

    # Build new content
    new_content = new_header

    for new_num in range(1, 9):
        # Find which old section maps to this new number
        old_num = [k for k, v in mapping.items() if v == new_num][0]

        if old_num in sections:
            section = sections[old_num]
            # Replace old number with new number in content
            updated_content = section["content"].replace(
                f"## {old_num}. {section['title']}", f"## {new_num}. {section['title']}"
            )
            new_content += updated_content + "\n"

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ Document reorganized: {output_file}")
    print(f"📊 Sections reordered: {len(mapping)}")
    print(f"📄 Size: {len(new_content):,} characters")


if __name__ == "__main__":
    simple_reorder()
