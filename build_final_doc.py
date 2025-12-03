#!/usr/bin/env python3
"""
Build final complete Q&A document with proper intro and all content
"""

import re


def build_final_document():
    # Read the intro we created
    with open("docs/TECHNICAL_QA_ENTERPRISE_BUYERS_FINAL.md", "r") as f:
        intro_content = f.read()

    # Read the full old document
    with open("docs/TECHNICAL_QA_ENTERPRISE_BUYERS.md", "r") as f:
        old_content = f.read()

    # Extract sections 3-9 from old document (renumber to match new structure)
    # Old Section 1 (Product Experience) → New Section 3
    # Old Section 3 (Integration) → New Section 4
    # Old Section 4 (Enforcement) → New Section 5
    # Old Section 5 (Deployment) → New Section 6
    # Old Section 6 (Security) → New Section 7
    # Old Section 7 (Data Handling) → New Section 8
    # Old Section 8 (Capsule Integrity) → New Section 9

    # Split old document by sections
    sections = re.split(r"\n## \d+\.", old_content)

    # Parse sections
    section_dict = {}
    for i, section_text in enumerate(sections[1:], 1):  # Skip header
        lines = section_text.split("\n", 1)
        if len(lines) >= 2:
            title = lines[0].strip()
            body = lines[1]
            section_dict[i] = {"title": title, "body": body}

    # Build final document
    final_content = intro_content

    # Add remaining sections in new order
    section_mapping = [
        (1, 3, "Product Experience"),  # Old 1 → New 3
        (3, 4, "Integration Surface"),  # Old 3 → New 4
        (4, 5, "Enforcement & Governance"),  # Old 4 → New 5
        (5, 6, "Deployment, Reliability & Ops"),  # Old 5 → New 6
        (6, 7, "Security & Compliance"),  # Old 6 → New 7
        (7, 8, "Data Handling Nuances"),  # Old 7 → New 8
        (8, 9, "Capsule Integrity & Crypto Details"),  # Old 8 → New 9
    ]

    for old_num, new_num, title in section_mapping:
        if old_num in section_dict:
            section = section_dict[old_num]

            # Renumber questions in this section
            body = section["body"]

            # Replace question numbers (Q{old}.X → Q{new}.X)
            body = re.sub(
                r"### Q" + str(old_num) + r"\.(\d+):",
                r"### Q" + str(new_num) + r".\1:",
                body,
            )

            final_content += f"\n## {new_num}. {title}\n\n{body}\n"

    # Write final document
    output_file = "docs/TECHNICAL_QA_ENTERPRISE_BUYERS.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_content)

    print(f"✅ Final document built: {output_file}")
    print(f"📊 Size: {len(final_content):,} characters")

    # Count sections and questions
    sections_count = len(re.findall(r"^## \d+\.", final_content, re.MULTILINE))
    questions_count = len(re.findall(r"^### Q\d+\.\d+:", final_content, re.MULTILINE))

    print(f"📚 Sections: {sections_count}")
    print(f"❓ Questions: {questions_count}")


if __name__ == "__main__":
    build_final_document()
