#!/usr/bin/env python3
"""
Fix syntax error in server.py after previous automated changes.
"""


def fix_syntax_error():
    """
    Fix the syntax error in server.py where function definitions were incorrectly merged.
    The error is at line ~563 where 'return jsonify(result_list)def get_capsule' appears
    without proper separation.
    """
    filename = "api/server.py"

    with open(filename) as file:
        content = file.read()

    # Find and fix the syntax error where functions are merged
    if "return jsonify(result_list)def " in content:
        corrected_content = content.replace(
            "return jsonify(result_list)def ", "return jsonify(result_list)\n\ndef "
        )
        print("- Fixed syntax error: added missing newlines between functions")

        # Write the corrected content back to the file
        with open(filename, "w") as file:
            file.write(corrected_content)

        print("Successfully fixed syntax error in server.py")
        return True
    else:
        print("Could not find the exact syntax error pattern")

        # As a backup, let's check for any missing newlines between 'return' and 'def'
        error_patterns = [
            ")]def ",
            ")def ",
            "}def ",
            '"def ',
            "'def ",
            "jsonify(result_list)def",
        ]

        fixed = False
        for pattern in error_patterns:
            if pattern in content:
                replacement = pattern.replace("def ", "\n\ndef ")
                content = content.replace(pattern, replacement)
                fixed = True
                print(f"- Fixed potential syntax error pattern: {pattern}")

        if fixed:
            with open(filename, "w") as file:
                file.write(content)
            print("Successfully fixed potential syntax errors in server.py")
            return True

        print("Could not identify any clear syntax errors to fix")
        return False


if __name__ == "__main__":
    fix_syntax_error()
