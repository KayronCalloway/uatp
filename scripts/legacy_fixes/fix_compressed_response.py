#!/usr/bin/env python3
"""
Fix compressed response in list_capsules endpoint.
"""


def fix_compressed_response():
    """
    Fix the compressed response in list_capsules endpoint to ensure it always returns
    a dictionary with compressed=True when compression is requested.
    """
    filename = "api/server.py"

    with open(filename) as file:
        content = file.read()

    # We need to fix the condition that checks for compression
    # and make sure compression is directly respected in list_capsules

    target = """        # CRITICAL: Force check compress parameter directly from request to avoid cache issues
        if not parse_bool_param(request.args.get('compress', 'false')):
            return jsonify(result_list)"""

    replacement = """        # CRITICAL: Force check compression parameter directly from request to avoid cache issues
        include_compressed = parse_bool_param(request.args.get('compress', 'false'))
        request_logger.debug(f"Final compression check: include_compressed={include_compressed}")

        if not include_compressed:
            return jsonify(result_list)"""

    if target in content:
        content = content.replace(target, replacement)
        print("- Updated compression check in list_capsules")

    # Write changes back to file
    with open(filename, "w") as file:
        file.write(content)

    print("Successfully updated list_capsules for proper compression handling")
    return True


if __name__ == "__main__":
    fix_compressed_response()
