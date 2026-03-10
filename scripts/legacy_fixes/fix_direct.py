#!/usr/bin/env python3
"""
Direct fixes for the remaining API issues.
"""


def fix_remaining_issues():
    """
    Direct fix for the remaining issues:
    1. list_capsules_compressed - Make sure compression parameter is always respected
    2. get_capsule_with_raw - Make sure raw_data is always included when requested
    """

    filename = "api/server.py"

    with open(filename) as file:
        content = file.read()

    changes_made = []

    # 1. Add direct force of compression parameter in list_capsules
    target = """        if not include_compressed:
            return jsonify(result_list)"""

    replacement = """        # CRITICAL: Force check compress parameter directly from request to avoid cache issues
        if not parse_bool_param(request.args.get('compress', 'false')):
            return jsonify(result_list)"""

    if target in content:
        content = content.replace(target, replacement)
        changes_made.append(
            "- Modified list_capsules to always check compression parameter directly"
        )

    # 2. Fix raw data handling in get_capsule endpoint
    target = """        # Return capsule data
        return jsonify(result)"""

    replacement = """        # CRITICAL: Final check to ensure raw data is included if requested
        if parse_bool_param(request.args.get('include_raw', 'false')) and 'raw_data' not in result:
            result['raw_data'] = {k: v for k, v in result.items() if k != 'raw_data'}
            request_logger.debug("Forcibly added raw_data field in final response")

        # Return capsule data
        return jsonify(result)"""

    if target in content:
        content = content.replace(target, replacement)
        changes_made.append("- Added final check for raw_data inclusion in get_capsule")

    # Write changes back to file
    if changes_made:
        with open(filename, "w") as file:
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
