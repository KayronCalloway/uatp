#!/usr/bin/env python3
"""
Automated script to replace datetime.utcnow() with timezone_utils.utc_now().

This fixes the systemic timezone bug across the entire codebase.

Usage:
    python3 scripts/fix_datetime_utcnow.py [--dry-run]

Options:
    --dry-run    Show what would be changed without modifying files
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def fix_file(file_path: Path, dry_run: bool = False) -> Tuple[bool, int, List[str]]:
    """
    Fix datetime.utcnow() in a single file.

    Returns:
        (modified, replacement_count, changes_made)
    """
    try:
        content = file_path.read_text()
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}")
        return False, 0, []

    original_content = content
    changes = []

    # Count replacements
    count = content.count("datetime.utcnow()")

    if count == 0:
        return False, 0, []

    # Replace datetime.utcnow() with utc_now()
    content = content.replace("datetime.utcnow()", "utc_now()")
    changes.append(f"Replaced {count} instances of datetime.utcnow() with utc_now()")

    # Check if timezone_utils import exists
    has_import = "from src.utils.timezone_utils import utc_now" in content
    has_old_style_import = "from ..utils.timezone_utils import utc_now" in content

    # Check what kind of imports this file uses
    has_absolute_import = bool(re.search(r"from src\.", content))
    has_relative_import = bool(re.search(r"from \.\.", content))

    if not has_import and not has_old_style_import and count > 0:
        # Find the imports section and add our import
        lines = content.split("\n")
        import_added = False

        # Try to find a good place to add the import
        for i, line in enumerate(lines):
            # Add after datetime import if it exists
            if "from datetime import" in line or "import datetime" in line:
                # Determine which import style to use based on file's existing imports
                if has_relative_import:
                    import_line = "from ..utils.timezone_utils import utc_now"
                else:
                    import_line = "from src.utils.timezone_utils import utc_now"

                lines.insert(i + 1, import_line)
                import_added = True
                changes.append(f"Added import: {import_line}")
                break

        # If we didn't find datetime import, add at the top of imports
        if not import_added:
            for i, line in enumerate(lines):
                if line.startswith("from ") or line.startswith("import "):
                    if has_relative_import:
                        import_line = "from ..utils.timezone_utils import utc_now"
                    else:
                        import_line = "from src.utils.timezone_utils import utc_now"

                    lines.insert(i, import_line)
                    changes.append(f"Added import at top: {import_line}")
                    break

        content = "\n".join(lines)

    if content != original_content:
        if not dry_run:
            try:
                file_path.write_text(content)
            except Exception as e:
                print(f"⚠️  Error writing {file_path}: {e}")
                return False, 0, []
        return True, count, changes

    return False, 0, []


def main():
    """Fix all Python files in src/ directory."""
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("🔍 DRY RUN MODE - No files will be modified\n")
    else:
        print("🔧 FIXING MODE - Files will be modified\n")

    src_dir = Path("src")
    if not src_dir.exists():
        print("❌ Error: src/ directory not found")
        sys.exit(1)

    total_files = 0
    total_replacements = 0
    modified_files = []

    print("Scanning files...")
    for py_file in sorted(src_dir.rglob("*.py")):
        # Skip timezone_utils.py itself
        if "timezone_utils.py" in str(py_file):
            continue

        modified, count, changes = fix_file(py_file, dry_run=dry_run)
        if modified:
            total_files += 1
            total_replacements += count
            modified_files.append((py_file, count, changes))

            if dry_run:
                print(f"📋 Would fix {count} instances in {py_file}")
            else:
                print(f"✅ Fixed {count} instances in {py_file}")

            for change in changes:
                print(f"   - {change}")

    print("\n" + "=" * 70)
    print("📊 Summary:")
    print(f"   Files {'would be ' if dry_run else ''}modified: {total_files}")
    print(f"   Total replacements: {total_replacements}")
    print("=" * 70)

    if modified_files and not dry_run:
        print("\n✅ All files fixed successfully!")
        print("\n🔍 Next steps:")
        print("   1. Run tests: python3 -m pytest tests/test_timezone_consistency.py")
        print("   2. Review changes: git diff")
        print(
            "   3. Commit: git add -A && git commit -m 'Fix: Replace datetime.utcnow() with timezone-aware utc_now()'"
        )
    elif modified_files and dry_run:
        print("\n💡 To apply these changes, run without --dry-run:")
        print("   python3 scripts/fix_datetime_utcnow.py")


if __name__ == "__main__":
    main()
