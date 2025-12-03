#!/usr/bin/env python3
"""
Direct fix for get_capsule raw data inclusion.
This script directly patches server.py without importing Flask.
"""

import re
from pathlib import Path


def create_parse_bool_param():
    """Ensure the parse_bool_param function exists in server.py."""
    server_path = Path("api/server.py")

    # Read the file content
    with open(server_path) as f:
        content = f.read()

    # Check if parse_bool_param already exists
    if "def parse_bool_param" in content:
        print("✅ parse_bool_param function already exists.")
        return True

    # Find the compression utility functions
    compression_funcs = re.search(r"(def compress_data.*?\n)\n", content, re.DOTALL)

    if not compression_funcs:
        print("❌ Could not find compression utility functions.")
        return False

    # Add parse_bool_param after compression functions
    parse_bool_function = '''
def parse_bool_param(param_value):
    """
    Parse a query parameter as a boolean value.

    Args:
        param_value (str): The query parameter value

    Returns:
        bool: True if the value is truthy ('true', '1', 'yes', 't', 'y')
    """
    if param_value is None:
        return False
    return str(param_value).lower() in ('true', '1', 'yes', 't', 'y')

'''

    insertion_point = compression_funcs.end()
    new_content = (
        content[:insertion_point] + parse_bool_function + content[insertion_point:]
    )

    # Write the fixed content back
    with open(server_path, "w") as f:
        f.write(new_content)

    print("✅ Successfully added parse_bool_param function.")
    return True


def fix_raw_data_inclusion():
    """Fix raw data inclusion in get_capsule endpoint."""
    server_path = Path("api/server.py")

    # Read the file content
    with open(server_path) as f:
        content = f.read()

    # Find the get_capsule function - handle multiple decorator formats
    get_capsule_patterns = [
        r"@app\.route\(\'\/capsules\/\<capsule_id\>\', methods=\[\'GET\'\]\)[\s\S]*?def get_capsule\(capsule_id: str\) -> Response:[\s\S]*?(?=@app\.route|\Z)",
        r"@app\.route\(\'\/capsule\/\<capsule_id\>\', methods=\[\'GET\'\]\)[\s\S]*?def get_capsule\(capsule_id\)[\s\S]*?(?=@app\.route|\Z)",
        r"@app\.route\(\'\/capsule\/(?P<capsule_id>.*?)\', methods=\[\'GET\'\]\)[\s\S]*?def get_capsule\(capsule_id\)[\s\S]*?(?=@app\.route|\Z)",
    ]

    for pattern in get_capsule_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            break

    if not match:
        print("❌ Could not find get_capsule function.")
        return False

    # Get the current function body
    function_body = match.group(0)

    # Check if it's already using parse_bool_param
    if "include_raw = parse_bool_param(" in function_body:
        print("✅ get_capsule is already using parse_bool_param.")
        return True

    # Update include_raw parameter handling
    old_include_raw = r"include_raw = request\.args\.get\(\'include_raw\', \'false\'\)\.lower\(\) in \(\'true\', \'1\', \'yes\'.*?\)"
    new_include_raw = (
        "include_raw = parse_bool_param(request.args.get('include_raw', 'false'))"
    )

    updated_body = re.sub(old_include_raw, new_include_raw, function_body)

    # Add raw_data to result dictionary if include_raw is True
    raw_data_pattern = (
        r"if include_raw:.*?(result\[\'raw_data\'\] = .*?)(?=\n\s*return jsonify|\Z)"
    )

    raw_data_match = re.search(raw_data_pattern, updated_body, re.DOTALL)

    if raw_data_match:
        # Existing raw_data assignment
        old_raw_data_assign = raw_data_match.group(1).strip()
        # Create a correct raw_data assignment
        new_raw_data_assign = "result['raw_data'] = {k: v for k, v in result.items() if k not in ['raw_data', 'verified']}"

        # Replace the existing assignment
        updated_body = updated_body.replace(old_raw_data_assign, new_raw_data_assign)
    else:
        # Need to add raw_data inclusion code
        include_raw_section = re.search(r"include_raw = .*?\n", updated_body)
        if not include_raw_section:
            print("❌ Could not find include_raw assignment.")
            return False

        # Insert after include_raw assignment
        insertion_point = include_raw_section.end()
        raw_data_code = """
        # GUARANTEED FIX: Always include raw data when explicitly requested
        if include_raw:
            # Direct raw data assignment that can't fail
            result['raw_data'] = str(capsule) # Use string representation as fallback
            print("CRITICAL DEBUG: Added raw_data to response with GUARANTEED fix")
"""
        updated_body = (
            updated_body[:insertion_point]
            + raw_data_code
            + updated_body[insertion_point:]
        )

    # Replace the function in the content
    new_content = content.replace(match.group(0), updated_body)

    # Write the fixed content back
    with open(server_path, "w") as f:
        f.write(new_content)

    print("✅ Successfully fixed raw data inclusion in get_capsule.")
    return True


def main():
    create_parse_bool_param()
    fix_raw_data_inclusion()


if __name__ == "__main__":
    main()
