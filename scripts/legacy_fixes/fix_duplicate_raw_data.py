#!/usr/bin/env python3
"""
Fix duplicate raw_data assignment in get_capsule endpoint.
"""


def fix_duplicate_raw_data():
    """
    Fix the duplicate raw_data assignment in get_capsule endpoint.
    The function currently has two identical lines that set result['raw_data'],
    which might be causing confusion in how raw_data is processed.
    """
    filename = "api/server.py"

    with open(filename) as file:
        content = file.read()

    # Find and fix the duplicate raw_data assignment
    target = """                if include_raw:
                    # Add raw data when requested
                    result['raw_data'] = {k: v for k, v in result.items() if k not in ['raw_data', 'verified']}
                    # Add raw data when requested (using original capsule data as raw data for demo purposes)
                    result['raw_data'] = {k: v for k, v in result.items() if k not in ['raw_data', 'verified']}"""

    replacement = """                if include_raw:
                    # Add raw data when requested (using original capsule data as raw data for demo purposes)
                    request_logger.debug(f"Adding raw_data to response for capsule {capsule_id}")
                    result['raw_data'] = {k: v for k, v in result.items() if k not in ['raw_data', 'verified']}"""

    if target in content:
        content = content.replace(target, replacement)
        print("- Fixed duplicate raw_data assignment in get_capsule endpoint")

        # Write changes back to file
        with open(filename, "w") as file:
            file.write(content)

        print("Successfully updated get_capsule for proper raw_data inclusion")
        return True
    else:
        print("Could not find duplicate raw_data assignment in get_capsule function")
        return False


if __name__ == "__main__":
    fix_duplicate_raw_data()
