#!/usr/bin/env python3
"""
Clean implementation of list_capsules with compression fix.
"""

import re


def clean_server_fix():
    """
    Create a clean implementation of the list_capsules endpoint with compression fix.
    This approach completely rewrites the function with our compression fix.
    """
    filename = "api/server.py"

    with open(filename) as file:
        content = file.read()

    # Find the list_capsules function
    pattern = r'@app\.route\(\'/capsules\', methods=\[\'GET\'\]\)\n@require_api_key\(\["read"\]\)\n@limiter\.limit\("200 per minute"\)\ndef list_capsules\(\) -> Response:.*?(?=\n@app\.route|\Z)'
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        print("Could not find list_capsules function")
        return False

    # Create a clean implementation with our compression fix
    replacement = '''@app.route('/capsules', methods=['GET'])
@require_api_key(["read"])
@limiter.limit("200 per minute")
def list_capsules() -> Response:
    """List all capsules in the chain with caching for better performance.

    Query Parameters:
        compressed (bool): Whether to compress the response (default: false)

    Returns:
        JSON response with list of capsules or error message
    """
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

        # Check compression parameter
        include_compressed = parse_bool_param(request.args.get('compress', 'false'))
        request_logger.debug(f"Compression requested: {include_compressed}")

        if not include_compressed:
            request_logger.debug("Returning uncompressed response")
            return jsonify(result_list)
        else:
            request_logger.debug("Preparing compressed response")
            # For compressed responses, convert to string, compress it, and return in expected format
            try:
                # Convert to JSON string and compress
                json_str = json.dumps(result_list, cls=CustomJSONEncoder)
                compressed = zlib.compress(json_str.encode('utf-8'), level=9)
                b64_compressed = base64.b64encode(compressed).decode('utf-8')

                # Return the format expected by tests
                response_dict = {
                    "compressed": True,
                    "data": b64_compressed
                }
                request_logger.debug("Successfully compressed response")
                return jsonify(response_dict)
            except Exception as e:
                request_logger.error(f"Failed to compress response: {str(e)}")
                # Fall back to uncompressed response
                return jsonify(result_list)
    except Exception as e:
        request_logger.error(
            f"Error listing capsules: {str(e)}",
            exc_info=True
        )
        return jsonify({"error": "Failed to list capsules", "details": str(e)}), 500
'''

    # Replace the function in the content
    new_content = content[: match.start()] + replacement + content[match.end() :]

    # Write the corrected content back to the file
    with open(filename, "w") as file:
        file.write(new_content)

    print(
        "Successfully replaced list_capsules function with clean implementation including compression fix"
    )
    return True


if __name__ == "__main__":
    clean_server_fix()
