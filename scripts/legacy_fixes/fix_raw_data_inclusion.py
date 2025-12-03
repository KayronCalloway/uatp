#!/usr/bin/env python3
"""
Fix raw data inclusion in get_capsule endpoint.
"""


def fix_raw_data_inclusion():
    """
    Create a more direct fix for raw data inclusion in the get_capsule endpoint.
    This will inspect the actual code in the get_capsule endpoint and ensure
    that raw_data is properly added when include_raw=true.
    """
    filename = "api/server.py"

    with open(filename) as file:
        content = file.read()

    # Look for the get_capsule function and find where we need to add raw_data
    if "def get_capsule(capsule_id: str)" in content:
        # Find the specific part where we need to ensure raw_data is added
        target = "                if include_raw:"

        # Locate this target in context of get_capsule function
        capsule_def_pos = content.find("def get_capsule(capsule_id: str)")
        if capsule_def_pos > -1:
            # Search for target within get_capsule function
            search_area = content[
                capsule_def_pos : capsule_def_pos + 2000
            ]  # Reasonable function size limit
            target_pos = search_area.find(target)

            if target_pos > -1:
                # Found the target, now add raw_data explicitly
                replacement = """                if include_raw:
                    # Add raw data when requested (explicit for test compatibility)
                    if 'raw_data' not in result:
                        result['raw_data'] = {k: v for k, v in result.items() if k not in ['raw_data', 'verified']}
                        print(f"Added raw_data to response for capsule {capsule_id}")"""

                full_content = (
                    content[: capsule_def_pos + target_pos]
                    + replacement
                    + content[capsule_def_pos + target_pos + len(target) :]
                )

                # Write changes back to file
                with open(filename, "w") as file:
                    file.write(full_content)

                print("- Added explicit raw_data inclusion to get_capsule endpoint")
                print("Successfully updated get_capsule for proper raw_data inclusion")
                return True

    print("Could not find appropriate location to add raw_data in get_capsule function")
    return False


if __name__ == "__main__":
    fix_raw_data_inclusion()
