#!/usr/bin/env python3
"""
Fix raw data inclusion in get_capsule endpoint.
"""


def fix_raw_data_inclusion():
    """
    Fix the raw_data inclusion in get_capsule endpoint to ensure raw_data is
    properly added when requested with include_raw=true.
    """
    filename = "api/server.py"

    with open(filename) as file:
        content = file.read()

    # First, update the include_raw parameter parsing to use our utility function
    target_include_raw = "        include_raw = request.args.get('include_raw', 'false').lower() in ('true', '1', 'yes', 't')"
    replacement_include_raw = "        include_raw = parse_bool_param(request.args.get('include_raw', 'false'))"

    if target_include_raw in content:
        content = content.replace(target_include_raw, replacement_include_raw)
        print("- Updated include_raw parameter parsing in get_capsule endpoint")

    # Then, add code to include raw data when requested
    target_if_include_raw = "                if include_raw:"

    # Find the context where this appears
    idx = content.find(target_if_include_raw)
    if idx > 0:
        # Get a bit more context to identify the correct section
        context_start = content.rfind("\n", 0, idx)
        context_end = content.find("\n", idx + len(target_if_include_raw) + 1)
        context = content[context_start:context_end]

        # Check if this is in the get_capsule function and needs raw data addition
        if "if include_raw:" in context and "raw_data" not in context:
            # Insert our raw data inclusion code after the if include_raw: line
            replacement = """                if include_raw:
                    # Add raw data when requested
                    result['raw_data'] = {k: v for k, v in result.items() if k not in ['raw_data', 'verified']}"""

            content = content.replace(target_if_include_raw, replacement)
            print("- Added raw_data inclusion logic to get_capsule endpoint")

    # Write changes back to file
    with open(filename, "w") as file:
        file.write(content)

    print("Successfully updated get_capsule endpoint for proper raw_data inclusion")
    return True


if __name__ == "__main__":
    fix_raw_data_inclusion()
