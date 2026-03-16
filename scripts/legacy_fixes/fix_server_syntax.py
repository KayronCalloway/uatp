#!/usr/bin/env python3
"""
More thorough fix for syntax errors in server.py.
"""


def fix_syntax_errors():
    """
    Fix syntax errors in server.py more thoroughly by examining the structure.
    The current error indicates a missing except or finally block.
    """
    filename = "api/server.py"

    with open(filename) as file:
        lines = file.readlines()

    # Let's attempt a more thorough repair by focusing on the list_capsules function
    # and ensuring all try blocks have corresponding except blocks

    list_capsules_start = -1
    list_capsules_end = -1

    # Find the list_capsules function boundaries
    for i, line in enumerate(lines):
        if "def list_capsules()" in line:
            list_capsules_start = i
        elif (
            list_capsules_start > -1 and "def " in line and i > list_capsules_start + 10
        ):  # Reasonable function size
            list_capsules_end = i
            break

    if list_capsules_start == -1:
        print("Could not find list_capsules function")
        return False

    if list_capsules_end == -1:
        list_capsules_end = len(
            lines
        )  # If we can't find the end, assume it goes to the end of file

    # Let's completely rewrite the list_capsules function with the correct structure
    list_capsules_code = """@app.route('/capsules', methods=['GET'])
@require_api_key(["read"])
@limiter.limit("200 per minute")
def list_capsules() -> Response:
    \"\"\"List all capsules in the chain with caching for better performance.

    Query Parameters:
        compressed (bool): Whether to compress the response (default: false)

    Returns:
        JSON response with list of capsules or error message
    \"\"\"
    try:
        request_logger.info("Listing all capsules")

        # Try to get from chain cache first
        chain_id = "default"  # Use a unique ID if you have multiple chains
        cached_chain = get_cached_chain(chain_id)

        if cached_chain is not None:
            request_logger.debug("Using cached chain for list operation")
            chain = cached_chain
        else:
            request_logger.debug("Chain cache miss, loading from storage for list operation")
            chain = list(engine.load_chain())
            # Cache the loaded chain
            cache_chain(chain_id, chain)

        # Convert capsules to dictionaries for JSON serialization
        result_list = [capsule.to_dict() for capsule in chain]

        # Add metadata
        for capsule_dict in result_list:
            capsule_dict["retrieved_at"] = datetime.now(timezone.utc).isoformat()

        # CRITICAL: Force check compression parameter directly from request to avoid cache issues
        include_compressed = parse_bool_param(request.args.get('compress', 'false'))
        request_logger.debug(f"Final compression check: include_compressed={include_compressed}")

        if not include_compressed:
            return jsonify(result_list)
        else:
            # For compressed responses, convert to JSON string, compress it, and return in expected format
            try:
                # Directly create the structure expected by tests
                json_str = json.dumps(result_list, cls=CustomJSONEncoder)
                compressed = zlib.compress(json_str.encode('utf-8'), level=9)
                b64_compressed = base64.b64encode(compressed).decode('utf-8')

                # Return the exact format expected by tests
                return jsonify({
                    "compressed": True,
                    "data": b64_compressed
                })
            except Exception as e:
                logger.error(f"Compression error in list_capsules: {e}")
                # Fall back to uncompressed response
                return jsonify(result_list)
    except Exception as e:
        request_logger.error(
            f"Error listing capsules: {str(e)}",
            exc_info=True
        )
        return jsonify({"error": "Failed to list capsules", "details": str(e)}), 500
"""

    # Replace the function in the file
    new_lines = (
        lines[:list_capsules_start] + [list_capsules_code] + lines[list_capsules_end:]
    )

    # Write the corrected content back to the file
    with open(filename, "w") as file:
        file.writelines(new_lines)

    print("Successfully rewrote list_capsules function with correct syntax")
    return True


if __name__ == "__main__":
    fix_syntax_errors()
