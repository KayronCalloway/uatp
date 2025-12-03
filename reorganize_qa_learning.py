#!/usr/bin/env python3
"""
Reorganize TECHNICAL_QA_ENTERPRISE_BUYERS.md as a learning journey
Order: Understanding UATP → Using UATP → Operating UATP → Deep Technical Details
"""


def reorganize_for_learning():
    """Reorganize Q&A document as a learning progression"""

    input_file = "docs/TECHNICAL_QA_ENTERPRISE_BUYERS.md"
    output_file = "docs/TECHNICAL_QA_ENTERPRISE_BUYERS_LEARNING.md"

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into sections
    sections = content.split("\n## ")

    # Extract header (before first ##)
    header_part = sections[0]
    sections = sections[1:]  # Remove header from list

    # Parse sections into dict
    section_dict = {}
    for section in sections:
        # First line is the section title
        lines = section.split("\n", 1)
        title = lines[0]
        body = lines[1] if len(lines) > 1 else ""
        section_dict[title] = body

    # New header with learning progression
    new_header = """# UATP Technical Q&A for Enterprise Buyers

**Version:** 1.0
**Date:** October 26, 2025
**Audience:** Technical decision-makers, security teams, compliance officers
**Purpose:** Comprehensive answers to enterprise buyer technical questions

**Organization:** Learning progression from "What is UATP?" → Deep technical implementation

---

## Table of Contents

### Understanding UATP (Start Here)
1. [Product Experience](#1-product-experience) - What is UATP? Dashboard, reports, templates
2. [Commercials & Risk](#2-commercials--risk) - Pricing, pilots, references, offboarding

### Using UATP (Integration & Daily Operations)
3. [Integration Surface](#3-integration-surface) - Provider support, APIs, SDKs
4. [Enforcement & Governance](#4-enforcement--governance) - Policies, overrides, false positives

### Operating UATP (Production Operations)
5. [Deployment, Reliability & Ops](#5-deployment-reliability--ops) - SLOs, throughput, DR, scaling

### Technical Deep Dives (Advanced Topics)
6. [Security & Compliance](#6-security--compliance) - BAA/DPA, key management, pen testing
7. [Data Handling Nuances](#7-data-handling-nuances) - GDPR, retention, data residency
8. [Capsule Integrity & Crypto Details](#8-capsule-integrity--crypto-details) - Post-quantum crypto, Merkle trees

---

"""

    # Define new order (learning progression)
    new_order = [
        ("7. Product Experience", "1. Product Experience"),
        ("1. Commercials & Risk", "2. Commercials & Risk"),
        ("4. Integration Surface", "3. Integration Surface"),
        ("5. Enforcement & Governance", "4. Enforcement & Governance"),
        ("3. Deployment, Reliability & Ops", "5. Deployment, Reliability & Ops"),
        ("6. Security & Compliance", "6. Security & Compliance"),
        ("7. Data Handling Nuances", "7. Data Handling Nuances"),
        (
            "8. Capsule Integrity & Crypto Details",
            "8. Capsule Integrity & Crypto Details",
        ),
    ]

    # Rebuild document in new order
    new_content = new_header

    for old_title, new_title in new_order:
        if old_title in section_dict:
            new_content += f"## {new_title}\n\n{section_dict[old_title]}\n"

    # Write to output
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ Learning-ordered document created: {output_file}")
    print(f"📊 Sections reordered: {len(new_order)}")
    print(f"📄 Output size: {len(new_content)} characters")

    return output_file


if __name__ == "__main__":
    reorganize_for_learning()
