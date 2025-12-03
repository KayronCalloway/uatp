#!/usr/bin/env python3
"""
Direct fix for list_capsules compression response format.
This script directly patches server.py without importing Flask.
"""

import re
from pathlib import Path


def fix_compression_response():
    """Fix the compressed response format in list_capsules."""
    server_path = Path("api/server.py")

    # Read the file content
    with open(server_path) as f:
        content = f.read()

    # Look for the compression section
    compression_pattern = r"if not include_compressed:.*?else:.*?try:.*?json_str = json\.dumps\((.*?), cls=CustomJSONEncoder\).*?compressed = zlib\.compress.*?b64_compressed = base64\.b64encode\(compressed\)\.decode\(\'utf-8\'\)(.*?)return jsonify\((.*?)\)"

    match = re.search(compression_pattern, content, re.DOTALL)

    if not match:
        print("❌ Could not find compression code section.")
        return False

    # Extract what's being returned and replace it with the correct format
    result_var = match.group(1).strip()
    current_return = match.group(3).strip()

    if "compressed" in current_return and "data" in current_return:
        print("✅ Compression response format is already correct.")
        return True

    # Replace the return statement with the correct format
    new_return = """
                # Return the format expected by tests
                response_dict = {
                    "compressed": True,
                    "data": b64_compressed
                }
                request_logger.debug("Successfully compressed response")
                return jsonify(response_dict)"""

    # Construct the replacement pattern using the extracted variables
    replacement_pattern = f"""if not include_compressed:
            request_logger.debug("Returning uncompressed response")
            return jsonify({result_var})
        else:
            request_logger.debug("Preparing compressed response")
            # For compressed responses, convert to string, compress it, and return in expected format
            try:
                # Convert to JSON string and compress
                json_str = json.dumps({result_var}, cls=CustomJSONEncoder)
                compressed = zlib.compress(json_str.encode('utf-8'), level=9)
                b64_compressed = base64.b64encode(compressed).decode('utf-8')
                {new_return}"""

    # Apply the replacement
    new_content = re.sub(
        compression_pattern, replacement_pattern, content, flags=re.DOTALL
    )

    # Write the fixed content back
    with open(server_path, "w") as f:
        f.write(new_content)

    print("✅ Successfully fixed compression response format in list_capsules.")
    return True


def main():
    fix_compression_response()


if __name__ == "__main__":
    main()
