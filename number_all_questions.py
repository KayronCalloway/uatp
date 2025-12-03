#!/usr/bin/env python3
"""
Number all questions within each section sequentially
"""

import re


def number_all_questions():
    input_file = "docs/TECHNICAL_QA_ENTERPRISE_BUYERS.md"

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    new_lines = []
    current_section = 0
    question_count = 0

    for line in lines:
        # Check for section header (## 1. Something, ## 2. Something, etc.)
        section_match = re.match(r"^## (\d+)\. (.+)$", line)
        if section_match:
            current_section = int(section_match.group(1))
            question_count = 0  # Reset question counter for new section
            new_lines.append(line)
            continue

        # Check for question header (either "### Q:" or "### QX.Y:")
        # Match both formats
        question_match = re.match(r"^### Q(?:\d+\.\d+)?:\s*(.+)$", line)
        if question_match and current_section > 0:
            question_count += 1
            question_text = question_match.group(1)
            new_line = f"### Q{current_section}.{question_count}: {question_text}"
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    new_content = "\n".join(new_lines)

    with open(input_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    # Count questions
    question_pattern = r"^### Q\d+\.\d+:"
    questions = [line for line in new_lines if re.match(question_pattern, line)]

    print(f"✅ All questions numbered: {input_file}")
    print(f"📊 Total questions: {len(questions)}")

    # Show sample
    print(f"\n📋 Sample questions:")
    for q in questions[:5]:
        print(f"   {q}")
    if len(questions) > 5:
        print(f"   ...")
        for q in questions[-3:]:
            print(f"   {q}")


if __name__ == "__main__":
    number_all_questions()
