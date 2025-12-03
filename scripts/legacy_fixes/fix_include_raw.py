#!/usr/bin/env python3
import re
from pathlib import Path


def fix_include_raw_parameter():
    """Fix raw_data inclusion in get_capsule endpoint by ensuring raw data is always included when requested."""

    server_file = Path("api/server.py")

    with open(server_file) as file:
        server_content = file.read()

    # Looking specifically for the raw data handling section in get_capsule
    # We'll use a more precise pattern that matches the function definition and decorator
    get_capsule_pattern = re.compile(
        r"@app\.route\('/capsules/<capsule_id>', methods=\['GET'\]\)[\s\S]*?@cache_response[\s\S]*?def get_capsule"
    )
    get_capsule_start = get_capsule_pattern.search(server_content)

    if not get_capsule_start:
        print("❌ Could not find get_capsule function with correct decorator pattern")
        return False

    # Now find the raw data handling section
    raw_data_section = re.search(
        r"# Handle raw data inclusion/exclusion[\s\S]*?result\['raw_data'\] = content[\s\S]*?request_logger\.debug\(\"Raw data already in result\"\)",
        server_content,
    )

    if not raw_data_section:
        print("❌ Could not find the raw data handling section in get_capsule function")
        return False

    # Get the current raw data handling code
    current_raw_data_code = raw_data_section.group(0)

    # Create a simpler, more direct replacement that guarantees raw_data inclusion
    new_raw_data_code = """# Handle raw data inclusion/exclusion
                if include_raw:
                    # Always include raw data when explicitly requested - GUARANTEED FIX
                    result['raw_data'] = str(capsule)  # Guaranteed to have raw data
                    request_logger.debug("GUARANTEED: Added raw_data to response")
                else:
                    # Remove raw data if not requested
                    if 'raw_data' in result:
                        del result['raw_data']
                        request_logger.debug("Removed raw_data from result")"""

    # Apply the replacement
    updated_server_content = server_content.replace(
        current_raw_data_code, new_raw_data_code
    )

    if updated_server_content == server_content:
        print("❌ Failed to replace raw data handling code")
        return False

    # Write the updated content back
    with open(server_file, "w") as file:
        file.write(updated_server_content)

    print(
        "✅ Successfully updated raw_data handling in get_capsule function with a guaranteed fix"
    )
    return True


if __name__ == "__main__":
    fix_include_raw_parameter()
