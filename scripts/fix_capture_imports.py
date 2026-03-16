#!/usr/bin/env python3
"""
Fix broken import paths in capture hook files.

Bug: 4 files use 'from live_capture.' which fails at runtime.
Fix: Change to 'from src.live_capture.'
"""

import re
from pathlib import Path


def fix_file(file_path: Path) -> tuple[bool, int]:
    """Fix import paths in a single file."""
    content = file_path.read_text()
    original_content = content

    # Pattern: from live_capture. → from src.live_capture.
    pattern = r"from live_capture\."
    replacement = r"from src.live_capture."

    content, count = re.subn(pattern, replacement, content)

    if count > 0:
        file_path.write_text(content)
        return True, count

    return False, 0


def main():
    """Fix all hook files with broken imports."""
    files_to_fix = [
        Path("src/live_capture/openai_hook.py"),
        Path("src/live_capture/cursor_hook.py"),
        Path("src/live_capture/windsurf_hook.py"),
        Path("src/live_capture/anthropic_hook.py"),
    ]

    total_fixes = 0

    for file_path in files_to_fix:
        if not file_path.exists():
            print(f"[WARN]  File not found: {file_path}")
            continue

        modified, count = fix_file(file_path)
        if modified:
            print(f"[OK] Fixed {count} import(s) in {file_path.name}")
            total_fixes += count
        else:
            print(f"  No changes needed in {file_path.name}")

    print(f"\n Total imports fixed: {total_fixes}")
    if total_fixes > 0:
        print("[OK] All import paths corrected!")


if __name__ == "__main__":
    main()
