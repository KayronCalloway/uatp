#!/usr/bin/env python3

import re

# Path to the file we want to modify
file_path = "demo_reasoning.py"

# Read the file content
with open(file_path) as file:
    content = file.read()

# Define the pattern we want to find and the replacement
pattern = r'"step_type": step\.step_type\.name(\.upper\(\))?  # API expects uppercase enum values,?'
replacement = (
    '"step_type": step.step_type.name.upper(),  # API expects uppercase enum values'
)

# Replace all occurrences of the pattern with the replacement
content_fixed = re.sub(pattern, replacement, content)

# Fix any instances without the comment
pattern_simple = r'"step_type": step\.step_type\.name(?!\.upper)'
replacement_simple = '"step_type": step.step_type.name.upper()'

content_fixed = re.sub(pattern_simple, replacement_simple, content_fixed)

# Write the modified content back to the file
with open(file_path, "w") as file:
    file.write(content_fixed)

print("Fixed step_type formatting in", file_path)
