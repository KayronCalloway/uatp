#!/usr/bin/env python3
"""
Reorganize TECHNICAL_QA_ENTERPRISE_BUYERS.md from technical to business order
New order: Business → Operational → Technical
"""


def reorganize_qa_document():
    """Reorganize Q&A document by increasing technical complexity"""

    input_file = "docs/TECHNICAL_QA_ENTERPRISE_BUYERS.md"
    output_file = "docs/TECHNICAL_QA_ENTERPRISE_BUYERS_REORGANIZED.md"

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into sections
    sections = content.split("\n## ")

    # Extract header (before first ##)
    header = sections[0]
    sections = sections[1:]  # Remove header from list

    # Parse sections into dict
    section_dict = {}
    for section in sections:
        # First line is the section title
        lines = section.split("\n", 1)
        title = lines[0]
        body = lines[1] if len(lines) > 1 else ""
        section_dict[title] = body

    # Define new order (business → operational → technical)
    new_order = [
        "8. Commercials & Risk",
        "7. Product Experience",
        "1. Deployment, Reliability & Ops",
        "4. Integration Surface",
        "5. Enforcement & Governance",
        "2. Security & Compliance",
        "6. Data Handling Nuances",
        "3. Capsule Integrity & Crypto Details",
    ]

    # Map to new numbers
    renumbered_sections = {
        "8. Commercials & Risk": "1. Commercials & Risk",
        "7. Product Experience": "2. Product Experience",
        "1. Deployment, Reliability & Ops": "3. Deployment, Reliability & Ops",
        "4. Integration Surface": "4. Integration Surface",
        "5. Enforcement & Governance": "5. Enforcement & Governance",
        "2. Security & Compliance": "6. Security & Compliance",
        "6. Data Handling Nuances": "7. Data Handling Nuances",
        "3. Capsule Integrity & Crypto Details": "8. Capsule Integrity & Crypto Details",
    }

    # Update header with new TOC
    new_header = """# UATP Technical Q&A for Enterprise Buyers

**Version:** 1.0
**Date:** October 26, 2025
**Audience:** Technical decision-makers, security teams, compliance officers
**Purpose:** Comprehensive answers to enterprise buyer technical questions

**Organization:** Questions progress from business/commercial → operational → technical/cryptographic

---

## Table of Contents

### Business & Commercial (Least Technical)
1. [Commercials & Risk](#1-commercials--risk)
2. [Product Experience](#2-product-experience)

### Operational & Integration (Medium Technical)
3. [Deployment, Reliability & Ops](#3-deployment-reliability--ops)
4. [Integration Surface](#4-integration-surface)
5. [Enforcement & Governance](#5-enforcement--governance)

### Technical & Security (Most Technical)
6. [Security & Compliance](#6-security--compliance)
7. [Data Handling Nuances](#7-data-handling-nuances)
8. [Capsule Integrity & Crypto Details](#8-capsule-integrity--crypto-details)

---

"""

    # Rebuild document in new order
    new_content = new_header

    for old_title in new_order:
        if old_title in section_dict:
            new_title = renumbered_sections[old_title]
            new_content += f"## {new_title}\n\n{section_dict[old_title]}\n"

    # Write to output
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ Reorganized document created: {output_file}")
    print(f"📊 Sections reordered: {len(new_order)}")
    print(f"📄 Output size: {len(new_content)} characters")

    return output_file


if __name__ == "__main__":
    reorganize_qa_document()
