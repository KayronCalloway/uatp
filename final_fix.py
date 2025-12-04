#!/usr/bin/env python3
"""
Final fix for the remaining API issues.
"""

def fix_remaining_issues():
    """
    Direct fix for the remaining issues:
    1. list_capsules_compressed - Make sure compression parameter is always respected
    2. get_capsule_with_raw - Make sure raw_data is always included when requested
    """

    filename = 'api/server.py'

    with open(filename, 'r') as file:
        content = file.read()

    changes_made = []

    # 1. Fix list_capsules compression issue more directly by:
    #    - Moving cache_response decorator below the route and require_api_key decorators
    #    - This ensures query parameters are processed before the cache check
    if "@app.route('/capsules', methods=['GET'])\n@require_api_key([\"read\"])\n@limiter.limit(\"5 per minute\")\n@cache_response(ttl_seconds=30)" in content:
        target = "@app.route('/capsules', methods=['GET'])\n@require_api_key([\"read\"])\n@limiter.limit(\"5 per minute\")\n@cache_response(ttl_seconds=30)"
        replacement = "@app.route('/capsules', methods=['GET'])\n@require_api_key([\"read\"])\n@limiter.limit(\"5 per minute\")"

        content = content.replace(target, replacement)
        changes_made.append("- Removed cache_response decorator from list_capsules")

    # 2. Create a utility function for parsing boolean query parameters
    if "def parse_bool_param(value: str) -> bool:" not in content:
        target = "# Utility functions\ndef validate_capsule(capsule_data: dict) -> bool:"
        replacement = """# Utility functions
def parse_bool_param(value: str) -> bool:
    """Parse a string query parameter as a boolean value."""
    if not value:
        return False
    return str(value).lower() in ('true', '1', 'yes', 't', 'y')

def validate_capsule(capsule_data: dict) -> bool:"""

        if target in content:
            content = content.replace(target, replacement)
            changes_made.append("- Added parse_bool_param utility function")

    # 3. Fix list_capsules endpoint to use the parse_bool_param function and directly check cache key
    if "def list_capsules()" in content:
        # Fix how parameters are parsed
        target = """        # Parse query parameters with proper validation
        # Handle multiple truthy values for compression parameter to match test expectations
        compress_param = request.args.get('compress', 'false').lower()
        include_compressed = compress_param in ('true', '1', 'yes', 't')
        request_logger.debug(f"Compression param received: '{compress_param}', interpreted as include_compressed={include_compressed}")
        # Debug log the actual value in request args
        request_logger.debug(f"All request args: {dict(request.args)}")
        include_raw = request.args.get('include_raw', 'false').lower() in ('true', '1', 'yes', 't')"""

        replacement = """        # Parse query parameters with proper validation
        # Use the centralized function for boolean parameter parsing
        include_compressed = parse_bool_param(request.args.get('compress', 'false'))
        request_logger.debug(f"Compression param received, interpreted as include_compressed={include_compressed}")
        # Debug log the actual value in request args
        request_logger.debug(f"All request args: {dict(request.args)}")
        include_raw = parse_bool_param(request.args.get('include_raw', 'false'))"""

        if target in content:
            content = content.replace(target, replacement)
            changes_made.append("- Updated list_capsules to use parse_bool_param")

        # Add cache key variation based on compression parameter
        target = """def list_capsules() -> Response:
    """List all capsules, with optional compression for the whole list.""""""

        replacement = """@cache_response(ttl_seconds=30, cache_key_func=lambda: f"list_capsules:{parse_bool_param(request.args.get('compress', 'false'))}")
def list_capsules() -> Response:
    """List all capsules, with optional compression for the whole list.""""""

        if target in content:
            content = content.replace(target, replacement)
            changes_made.append("- Added cache key variation based on compression parameter")

    # 4. Fix get_capsule endpoint to use the parse_bool_param function and always include raw data when requested
    target = """        # Parse include_raw parameter
        include_raw = request.args.get('include_raw', 'false').lower() in ('true', '1', 'yes', 't')"""

        replacement = """        # Parse include_raw parameter using centralized function
        include_raw = parse_bool_param(request.args.get('include_raw', 'false'))"""

        if target in content:
            content = content.replace(target, replacement)
            changes_made.append("- Updated get_capsule to use parse_bool_param")

        # Make sure raw data is always included when requested
        target = """                # Handle raw data based on request
                if include_raw:
                    # Add raw data when requested (using original capsule data as raw data for demo purposes)
                    result['raw_data'] = {k: v for k, v in result.items() if k not in ['raw_data', 'verified']}
                elif 'raw_data' in result:"""

        replacement = """                # Handle raw data based on request
                if include_raw:
                    # Always ensure raw_data is included when requested
                    # Use capsule data as raw_data for demo purposes if not already present
                    if 'raw_data' not in result or not result['raw_data']:
                        result['raw_data'] = {k: v for k, v in result.items() if k not in ['raw_data', 'verified']}
                elif 'raw_data' in result:"""

        if target in content:
            content = content.replace(target, replacement)
            changes_made.append("- Improved raw data inclusion logic in get_capsule")

    # Write changes back to file
    if changes_made:
        with open(filename, 'w') as file:
            file.write(content)
        print(f"Successfully updated {filename} with the following changes:")
        for change in changes_made:
            print(change)
        return True
    else:
        print("No changes needed or applicable sections not found")
        return False

if __name__ == "__main__":
    fix_remaining_issues()
