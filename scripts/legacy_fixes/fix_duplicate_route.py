#!/usr/bin/env python3
"""
Fix duplicate route in server.py
"""

from pathlib import Path


def fix_duplicate_route():
    """Fix duplicate route for list_capsules in server.py"""
    server_path = Path("api/server.py")

    # Read the file content
    with open(server_path) as f:
        content = f.read()

    # Check for duplicate route pattern
    first_route = "@app.route('/capsules', methods=['GET'])"

    # Find the first occurrence
    first_pos = content.find(first_route)
    if first_pos == -1:
        print("[ERROR] Could not find the first route declaration.")
        return False

    # Find the second occurrence
    second_pos = content.find(first_route, first_pos + len(first_route))
    if second_pos == -1:
        print("[OK] No duplicate route found.")
        return True

    # Remove the first occurrence and its corresponding line
    # We'll keep the second one which has the higher rate limit (200 per minute)
    line_end = content.find("\n", first_pos) + 1
    new_content = content[:first_pos] + content[line_end:]

    # Write the fixed content back
    with open(server_path, "w") as f:
        f.write(new_content)

    print("[OK] Successfully removed duplicate route declaration.")
    return True


if __name__ == "__main__":
    fix_duplicate_route()
