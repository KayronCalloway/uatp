#!/usr/bin/env python3
"""
Add the parse_bool_param function directly to server.py.
"""


def add_parse_bool_param():
    """Add the parse_bool_param function to server.py."""

    filename = "api/server.py"

    with open(filename) as file:
        content = file.read()

    # Add the function after the compression utility functions section
    if "# Compression utility functions" in content:
        target = "# Compression utility functions"
        replacement = """# Compression utility functions

def parse_bool_param(value: str) -> bool:
    # Parse a string query parameter as a boolean value
    if not value:
        return False
    return str(value).lower() in ('true', '1', 'yes', 't', 'y')"""

        if target in content:
            content = content.replace(target, replacement)

            # Write changes back to file
            with open(filename, "w") as file:
                file.write(content)

            print(f"Successfully added parse_bool_param function to {filename}")
            return True

    print("Could not find suitable location to add parse_bool_param function")
    return False


if __name__ == "__main__":
    add_parse_bool_param()
