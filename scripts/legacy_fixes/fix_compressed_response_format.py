#!/usr/bin/env python3
"""
Fix compressed response format in list_capsules endpoint.
"""


def fix_compressed_response_format():
    """
    Fix the compressed response format in list_capsules endpoint to ensure it returns
    a dictionary with 'compressed': True and 'data' field containing the compressed capsules.
    The test expects a dictionary with these fields, not a direct list.
    """
    filename = "api/server.py"

    with open(filename) as file:
        content = file.read()

    # Find the list_capsules function's return pattern with compression
    target = """        # CRITICAL: Force check compression parameter directly from request to avoid cache issues
        include_compressed = parse_bool_param(request.args.get('compress', 'false'))
        request_logger.debug(f"Final compression check: include_compressed={include_compressed}")

        if not include_compressed:
            return jsonify(result_list)"""

    replacement = """        # CRITICAL: Force check compression parameter directly from request to avoid cache issues
        include_compressed = parse_bool_param(request.args.get('compress', 'false'))
        request_logger.debug(f"Final compression check: include_compressed={include_compressed}")

        if not include_compressed:
            return jsonify(result_list)
        else:
            # For compressed responses, we need to return a dictionary format with compressed=True
            # Convert to JSON string, compress it, and return in the expected format
            try:
                json_str = json.dumps(result_list, cls=CustomJSONEncoder)
                compressed = zlib.compress(json_str.encode('utf-8'), level=9)
                b64_compressed = base64.b64encode(compressed).decode('utf-8')

                response_dict = {
                    "compressed": True,
                    "data": b64_compressed
                }
                request_logger.debug("Successfully compressed response data")
                return jsonify(response_dict)
            except Exception as e:
                request_logger.error(f"Failed to compress response: {str(e)}")
                # Fall back to uncompressed response
                return jsonify(result_list)"""

    if target in content:
        content = content.replace(target, replacement)
        print("- Updated compressed response format in list_capsules endpoint")

        # Write changes back to file
        with open(filename, "w") as file:
            file.write(content)

        print(
            "Successfully updated list_capsules for proper compression response format"
        )
        return True
    else:
        print("Could not find target pattern in list_capsules function")
        return False


if __name__ == "__main__":
    fix_compressed_response_format()
