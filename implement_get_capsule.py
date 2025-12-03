#!/usr/bin/env python3
"""
Implement the missing get_capsule endpoint in server.py
"""

import re
from pathlib import Path


def implement_get_capsule():
    """Implement the get_capsule endpoint in server.py"""
    server_path = Path("api/server.py")

    # Read the file content
    with open(server_path) as f:
        content = f.read()

    # Function to implement
    get_capsule_code = """
@app.route('/capsules/<capsule_id>', methods=['GET'])
@require_api_key(["read"])
@limiter.limit("200 per minute")
@cache_response(ttl_seconds=60)  # Cache results for 60 seconds
def get_capsule(capsule_id: str) -> Response:
    \"\"\"Get a specific capsule by ID with caching for better performance.

    Args:
        capsule_id: The unique identifier of the capsule to retrieve

    Query Parameters:
        include_raw (bool): Whether to include raw data in the response (default: false)

    Returns:
        JSON response with capsule data or error message
    \"\"\"
    try:
        request_logger.info(f"Retrieving capsule {capsule_id}")

        # Parse query parameters
        include_raw = parse_bool_param(request.args.get('include_raw', 'false'))
        request_logger.debug(f"include_raw parameter: {include_raw}")

        if not capsule_id or not isinstance(capsule_id, str):
            request_logger.warning(f"Invalid capsule ID format: {capsule_id}")
            return jsonify({"error": "Invalid capsule ID"}), 400

        # Get all capsules (would be more efficient to have a get_capsule method in the engine)
        capsules = engine.get_all_capsules()

        # Find the requested capsule
        for capsule in capsules:
            if capsule.capsule_id == capsule_id:
                # Convert to dictionary for JSON serialization
                result = capsule.to_dict()

                # Remove raw data if not requested
                if not include_raw and 'raw_data' in result:
                    del result['raw_data']
                elif include_raw and 'raw_data' not in result:
                    # If raw data is requested but not available, add an empty entry
                    result['raw_data'] = None

                request_logger.info(f"Successfully retrieved capsule {capsule_id}")
                return jsonify(result)

        request_logger.warning(f"Capsule not found: {capsule_id}")
        return jsonify({"error": "Capsule not found", "capsule_id": capsule_id}), 404
    except Exception as e:
        request_logger.error(
            f"Error retrieving capsule {capsule_id}: {str(e)}",
            exc_info=True
        )
        return jsonify({"error": "Failed to retrieve capsule", "details": str(e)}), 500
"""

    # Find a good insertion point after the last endpoint
    # We'll insert after verify_capsule function
    verify_capsule_pattern = r"def verify_capsule\([^)]*\).*?(?=\n\n@app\.route|$)"
    match = re.search(verify_capsule_pattern, content, re.DOTALL)

    if not match:
        print("❌ Could not find verify_capsule function as insertion point.")
        return False

    # Insert after verify_capsule function
    insert_pos = match.end()
    new_content = (
        content[:insert_pos] + "\n\n" + get_capsule_code + content[insert_pos:]
    )

    # Write the modified content back
    with open(server_path, "w") as f:
        f.write(new_content)

    print("✅ Successfully implemented get_capsule endpoint.")
    return True


if __name__ == "__main__":
    implement_get_capsule()
