#!/usr/bin/env python3
"""
Fix the OpenAI client initialization in openai_client.py
"""

import re
import sys

# Path to the OpenAI client file
client_file = "src/integrations/openai_client.py"

# Read the current file
try:
    with open(client_file) as f:
        content = f.read()

    # Create a backup
    with open(f"{client_file}.bak", "w") as f:
        f.write(content)

    print(f"Created backup at {client_file}.bak")

    # Replace the OpenAI client initialization
    # Old: self.client = OpenAI(api_key=self.api_key)
    # New: self.client = OpenAI(api_key=self.api_key) # proxies removed
    pattern = (
        r"self\.client = OpenAI\(api_key=self\.api_key(?:, proxies=self\.proxies)?\)"
    )
    replacement = "self.client = OpenAI(api_key=self.api_key) # proxies removed"

    new_content = re.sub(pattern, replacement, content)

    # Write the modified file
    with open(client_file, "w") as f:
        f.write(new_content)

    print(f"Successfully patched {client_file}")
    print("Now you can run openai_capsule.py without the 'proxies' error")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
