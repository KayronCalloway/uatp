#!/usr/bin/env python3
"""
Fix question numbering to match new section numbers
"""

import re


def fix_question_numbers():
    input_file = "docs/TECHNICAL_QA_ENTERPRISE_BUYERS.md"

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Section mapping (old number → new number)
    # We know from the reorg:
    # Product Experience (was 7) → now 1
    # Commercials (was 8) → now 2
    # Integration (was 4) → now 3
    # Enforcement (was 5) → now 4
    # Deployment (was 1) → now 5
    # Security (was 2) → now 6
    # Data Handling (was 6) → now 7
    # Capsule Integrity (was 3) → now 8

    # Track current section as we process
    current_section = 0
    lines = content.split("\n")
    new_lines = []

    for line in lines:
        # Check if this is a section header
        section_match = re.match(r"^## (\d+)\. (.+)$", line)
        if section_match:
            current_section = int(section_match.group(1))
            new_lines.append(line)
            continue

        # Check if this is a question header with old numbering
        # Patterns: Q7.1, Q8.2, Q1.1, etc.
        question_match = re.match(r"^### Q(\d+)\.(\d+): (.+)$", line)
        if question_match:
            old_section_num = int(question_match.group(1))
            question_num = question_match.group(2)
            question_text = question_match.group(3)

            # Replace with current section number
            new_line = f"### Q{current_section}.{question_num}: {question_text}"
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    # Write back
    new_content = "\n".join(new_lines)

    with open(input_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ Fixed question numbering in {input_file}")

    # Count changes
    old_q_pattern = r"### Q\d+\.\d+:"
    old_count = len(re.findall(old_q_pattern, content))
    new_count = len(re.findall(old_q_pattern, new_content))

    print(f"📊 Questions found: {old_count}")
    print(f"✏️  Questions renumbered to match sections")


if __name__ == "__main__":
    fix_question_numbers()
