#!/usr/bin/env python3
"""
Direct fix for list_capsules compressed response format.
"""


def fix_list_capsules_compressed():
    """
    Create a direct fix for the list_capsules endpoint to ensure it returns
    a dictionary with 'compressed': True and 'data' fields when compression is requested.

    The debug script shows that despite our previous fix, the endpoint still returns a list
    instead of a dictionary, which is causing the test failure.
    """
    filename = "api/server.py"

    with open(filename) as file:
        content = file.read()

    # Find the list_capsules function definition
    list_capsules_start = content.find("def list_capsules()")
    if list_capsules_start == -1:
        print("Could not find list_capsules function")
        return False

    # Find the end of the function (this is approximate)
    next_def = content.find("def ", list_capsules_start + 1)
    list_capsules_end = next_def if next_def != -1 else len(content)

    # Extract the function content
    list_capsules_content = content[list_capsules_start:list_capsules_end]

    # Check if the function already returns the right format when compressed
    if (
        "include_compressed = parse_bool_param(request.args.get('compress'"
        in list_capsules_content
    ):
        # Find the part where we return the response
        return_part_start = list_capsules_content.find("if not include_compressed:")
        if return_part_start != -1:
            # Extract the return logic
            return_part = list_capsules_content[return_part_start:]

            # Create the modified return logic
            new_return_part = """if not include_compressed:
            return jsonify(result_list)
        else:
            # For compressed responses, convert to string, compress it, and return in expected format
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
                return jsonify(result_list)"""

            # Replace the return logic in the function
            modified_list_capsules = list_capsules_content.replace(
                list_capsules_content[return_part_start:],
                new_return_part
                + list_capsules_content[return_part_start + len(return_part) :],
            )

            # Replace the function in the full content
            new_content = content.replace(list_capsules_content, modified_list_capsules)

            # Write the modified content back to the file
            with open(filename, "w") as file:
                file.write(new_content)

            print(
                "Successfully updated list_capsules for proper compressed response format"
            )
            return True

    print("Could not find appropriate section to modify in list_capsules function")
    return False


if __name__ == "__main__":
    fix_list_capsules_compressed()
