#!/usr/bin/env python3
"""
Fix absolute paths in Python files after migration.
Replaces hardcoded /Users/kay/uatp-capsule-engine/ with relative paths or os.path.dirname(__file__).
"""

import os
import re
import sys
from pathlib import Path

# The old absolute path to replace
OLD_PATH = "/Users/kay/uatp-capsule-engine"

# Files to process (from grep results)
FILES_TO_FIX = [
    "antigravity_capture_integration.py",
    "src/auto_capture/enhanced_universal_capture.py",
    "src/live_capture/claude_code_capture.py",
    "src/integrations/cursor_ide_capture.py",
]


def fix_log_file_paths(content: str) -> str:
    """Fix hardcoded log file paths to use relative paths."""
    # Pattern: '/Users/kay/uatp-capsule-engine/something.log'
    pattern = rf"'{OLD_PATH}/([^']+\.log)'"

    def replace_log_path(match):
        filename = match.group(1)
        return f"os.path.join(os.path.dirname(__file__), '{filename}')"

    content = re.sub(pattern, replace_log_path, content)

    # Also handle double quotes
    pattern = rf'"{OLD_PATH}/([^"]+\.log)"'
    content = re.sub(pattern, replace_log_path, content)

    return content


def fix_db_paths(content: str) -> str:
    """Fix hardcoded database paths."""
    # Pattern: self.db_path = "/Users/kay/uatp-capsule-engine/something.db"
    pattern = rf'self\.db_path = "{OLD_PATH}/([^"]+\.db)"'
    replacement = (
        r'self.db_path = os.path.join(os.path.dirname(__file__), "..", "..", "\1")'
    )
    content = re.sub(pattern, replacement, content)

    return content


def fix_test_paths(content: str) -> str:
    """Fix hardcoded test paths."""
    # Pattern: await start_cursor_capture_session("test-user", "/Users/kay/uatp-capsule-engine")
    pattern = rf'("{OLD_PATH}")'
    replacement = r"os.path.dirname(os.path.dirname(__file__))"
    content = re.sub(pattern, replacement, content)

    return content


def ensure_os_import(content: str) -> str:
    """Ensure 'import os' is present in the file."""
    if "import os" not in content:
        # Add import after the shebang and docstring if present
        lines = content.split("\n")
        insert_index = 0

        # Skip shebang
        if lines and lines[0].startswith("#!"):
            insert_index = 1

        # Skip docstring
        if insert_index < len(lines) and (
            lines[insert_index].startswith('"""')
            or lines[insert_index].startswith("'''")
        ):
            # Find end of docstring
            quote = '"""' if lines[insert_index].startswith('"""') else "'''"
            for i in range(insert_index, len(lines)):
                if lines[i].count(quote) >= 2 or (
                    i > insert_index and quote in lines[i]
                ):
                    insert_index = i + 1
                    break

        # Find first import or insert at beginning
        for i in range(insert_index, len(lines)):
            if lines[i].strip().startswith("import ") or lines[i].strip().startswith(
                "from "
            ):
                insert_index = i
                break

        lines.insert(insert_index, "import os")
        content = "\n".join(lines)

    return content


def fix_file(filepath: str):
    """Fix a single file."""
    print(f"Processing {filepath}...")

    if not os.path.exists(filepath):
        print(f"  ⚠️  File not found: {filepath}")
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Apply fixes
        content = fix_log_file_paths(content)
        content = fix_db_paths(content)
        content = fix_test_paths(content)

        # Ensure os is imported if we made changes
        if content != original_content:
            content = ensure_os_import(content)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"  ✓ Fixed {filepath}")
        else:
            print(f"  - No changes needed for {filepath}")

    except Exception as e:
        print(f"  ✗ Error processing {filepath}: {e}")


def main():
    """Main function."""
    print("Fixing absolute paths in Python files...\n")

    repo_root = Path(__file__).parent
    os.chdir(repo_root)

    for filepath in FILES_TO_FIX:
        fix_file(filepath)

    print("\n✓ All files processed!")
    print("\nNote: Review the changes with 'git diff' before committing.")


if __name__ == "__main__":
    main()
