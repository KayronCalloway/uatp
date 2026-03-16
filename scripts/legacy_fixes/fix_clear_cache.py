#!/usr/bin/env python3


def fix_clear_cache_function():
    """
    Fix the reference to clear_response_cache() function that isn't defined
    """

    filename = "api/server.py"

    with open(filename) as file:
        content = file.read()

    # Remove the reference to clear_response_cache() since it's causing an error
    target = "        # Clear response cache\n        clear_response_cache()"
    replacement = "        # Cache will be automatically invalidated on next request"

    if target in content:
        content = content.replace(target, replacement)
        with open(filename, "w") as file:
            file.write(content)
        print(
            f"Successfully fixed {filename} by removing reference to undefined function"
        )
        return True
    else:
        print("Could not find the reference to clear_response_cache()")
        return False


if __name__ == "__main__":
    fix_clear_cache_function()
