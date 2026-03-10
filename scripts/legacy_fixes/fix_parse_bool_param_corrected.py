#!/usr/bin/env python3
"""
Fix the missing parse_bool_param function.
"""


def fix_parse_bool_param():
    """
    Add the missing parse_bool_param function to the API server.
    """

    filename = "api/server.py"

    with open(filename) as file:
        content = file.read()

    # 1. Add parse_bool_param utility function right before validate_capsule
    if "def parse_bool_param(value: str) -> bool:" not in content:
        target = (
            "# Utility functions\ndef validate_capsule(capsule_data: dict) -> bool:"
        )
        replacement = """# Utility functions
def parse_bool_param(value: str) -> bool:
    # Parse a string query parameter as a boolean value
    if not value:
        return False
    return str(value).lower() in ('true', '1', 'yes', 't', 'y')

def validate_capsule(capsule_data: dict) -> bool:"""

        if target in content:
            content = content.replace(target, replacement)
            print("- Added parse_bool_param utility function")

            # Write changes back to file
            with open(filename, "w") as file:
                file.write(content)

            print(f"Successfully updated {filename}")
            return True
        else:
            print("Could not find target insertion point for parse_bool_param function")
            return False
    else:
        print("parse_bool_param function already exists")
        return False


if __name__ == "__main__":
    fix_parse_bool_param()
