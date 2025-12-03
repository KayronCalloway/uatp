#!/usr/bin/env python3
"""
Manual fix for raw data inclusion in get_capsule endpoint.
This script directly patches the critical section in server.py.
"""

import re
from pathlib import Path


def fix_raw_data_inclusion():
    """Fix raw data inclusion logic in get_capsule endpoint."""
    server_path = Path("api/server.py")

    # Read the file content
    with open(server_path) as f:
        content = f.read()

    # Look for raw_data inclusion logic pattern inside get_capsule function
    raw_data_pattern = re.compile(
        r"(# Handle raw data inclusion/exclusion.*?if include_raw:.*?)(result\[\'raw_data\'\] = [^\n]*)(.*?)else:.*?del result\[\'raw_data\'\]",
        re.DOTALL,
    )

    match = raw_data_pattern.search(content)

    if not match:
        print("❌ Could not find raw data handling section in get_capsule.")
        return False

    # Get the current implementation
    before_assignment = match.group(1)
    assignment = match.group(2)
    after_assignment = match.group(3)

    print(f"Current raw data assignment: {assignment}")

    # Create the new implementation with a guaranteed fix
    new_assignment = (
        "result['raw_data'] = str(capsule)  # GUARANTEED: Direct string representation"
    )

    # Replace the raw data assignment
    new_content = content.replace(
        match.group(0),
        f"{before_assignment}{new_assignment}{after_assignment}else:\n                    # Remove raw data if not requested\n                    if 'raw_data' in result:\n                        del result['raw_data']\n                        print(\"Raw data removed as not requested.\")",
    )

    # Write the updated content back
    with open(server_path, "w") as f:
        f.write(new_content)

    print(
        "✅ Successfully applied manual raw data inclusion fix to get_capsule endpoint."
    )
    return True


# Execute the fix
if __name__ == "__main__":
    fix_raw_data_inclusion()
