#!/usr/bin/env python3
"""
Fix duplicate list_capsules endpoint in server.py.
"""


def fix_duplicate_endpoint():
    """
    Fix the duplicate list_capsules endpoint in server.py.
    Our previous fix added a new definition of list_capsules without removing
    the original one, causing Flask to raise an AssertionError.
    """
    filename = "api/server.py"

    with open(filename) as file:
        content = file.read()

    # Find all occurrences of list_capsules function definitions
    list_capsules_definitions = []
    for i in range(len(content)):
        if content[i : i + 20] == "def list_capsules()":
            list_capsules_definitions.append(i)

    print(f"Found {len(list_capsules_definitions)} list_capsules function definitions")

    if len(list_capsules_definitions) <= 1:
        print("No duplicate list_capsules function found")
        return False

    # Find the beginning of the function for each definition
    function_beginnings = []
    for pos in list_capsules_definitions:
        # Look backwards for the @app.route decorator
        route_pos = content.rfind("@app.route('/capsules'", 0, pos)
        if route_pos >= 0:
            function_beginnings.append(route_pos)

    print(f"Found {len(function_beginnings)} function beginnings")

    if len(function_beginnings) <= 1:
        print("Could not locate function boundaries properly")
        return False

    # Keep only the second (most recent) definition
    keep_start = function_beginnings[1]
    keep_end = len(content)

    if len(function_beginnings) > 2:
        # If there are more than 2 definitions, find the end of the second definition
        keep_end = function_beginnings[2]

    # Remove the first definition
    remove_start = function_beginnings[0]
    remove_end = keep_start

    # Reconstruct the content without the duplicate
    new_content = content[:remove_start] + content[remove_end:]

    # Write the corrected content back to the file
    with open(filename, "w") as file:
        file.write(new_content)

    print("Successfully removed duplicate list_capsules function")
    return True


if __name__ == "__main__":
    fix_duplicate_endpoint()
