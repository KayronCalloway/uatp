#!/usr/bin/env python3
"""
Fix the get_capsule endpoint implementation to use the correct method for retrieving capsules
"""

import re
from pathlib import Path


def fix_get_capsule():
    """Fix the get_capsule endpoint in server.py to use load_chain() instead of get_all_capsules()"""
    server_path = Path("api/server.py")

    # Read the file content
    with open(server_path) as f:
        content = f.read()

    # Find the get_capsule function implementation
    get_capsule_pattern = r"def get_capsule\([^)]*\).*?(?=\n\n@app\.route|$)"
    match = re.search(get_capsule_pattern, content, re.DOTALL)

    if not match:
        print("❌ Could not find get_capsule function.")
        return False

    # Extract the function body
    get_capsule_code = match.group(0)

    # Replace the incorrect capsule retrieval code
    incorrect_code = "        # Get all capsules (would be more efficient to have a get_capsule method in the engine)\n        capsules = engine.get_all_capsules()"
    correct_code = """        # Try to get from chain cache first
        chain_id = "default"  # Use a unique ID if you have multiple chains
        cached_chain = get_cached_chain(chain_id)

        if cached_chain is not None:
            request_logger.debug("Using cached chain for get_capsule operation")
            capsules = cached_chain
        else:
            request_logger.debug("Chain cache miss, loading from storage for get_capsule operation")
            capsules = list(engine.load_chain())
            # Cache the loaded chain
            cache_chain(chain_id, capsules)"""

    fixed_get_capsule_code = get_capsule_code.replace(incorrect_code, correct_code)

    # Apply the fix to the main content
    new_content = content.replace(get_capsule_code, fixed_get_capsule_code)

    # Write the modified content back
    with open(server_path, "w") as f:
        f.write(new_content)

    print("✅ Successfully fixed get_capsule endpoint.")
    return True


if __name__ == "__main__":
    fix_get_capsule()
