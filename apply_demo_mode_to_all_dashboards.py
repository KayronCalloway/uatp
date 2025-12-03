#!/usr/bin/env python3
"""
Apply demo mode conditionals to all remaining dashboards.
This script wraps all mock data in DEMO_MODE conditionals to ensure
mock data only appears when NEXT_PUBLIC_DEMO_MODE=true.
"""

import re
from pathlib import Path


def add_demo_mode_check(content: str, component_name: str) -> str:
    """Add DEMO_MODE check at the beginning of the component function."""
    # Check if DEMO_MODE already exists
    if "const DEMO_MODE" in content:
        print(f"  ℹ️  {component_name} already has DEMO_MODE check")
        return content

    # Find the export function line
    export_match = re.search(r"export function (\w+Dashboard)\(\) \{", content)
    if not export_match:
        print(f"  ⚠️  Could not find export function in {component_name}")
        return content

    # Insert DEMO_MODE check after the opening brace
    insert_pos = export_match.end()
    demo_mode_check = "\n  // Demo mode - mock data only shown when NEXT_PUBLIC_DEMO_MODE=true\n  const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === 'true';\n"

    return content[:insert_pos] + demo_mode_check + content[insert_pos:]


def wrap_mock_object(content: str) -> str:
    """Wrap mock object declarations with DEMO_MODE conditionals."""
    # Pattern: const mockXXX: Type = { ... };
    # Replace with: const mockXXX: Type = DEMO_MODE ? { ... } : { zero values };

    # For stats objects (objects with number fields)
    pattern = r"(const mock\w+:\s*\w+\s*=\s*)(\{[^}]+\});"

    def replacer(match):
        var_decl = match.group(1)
        obj_content = match.group(2)

        # Skip if already wrapped
        if "DEMO_MODE" in var_decl:
            return match.group(0)

        # Create empty version with zero values
        # Extract fields and set them to 0
        fields = re.findall(r"(\w+):\s*[^,}]+", obj_content)
        empty_obj = (
            "{\n    " + ",\n    ".join(f"{field}: 0" for field in fields) + "\n  }"
        )

        return f"{var_decl}DEMO_MODE ? {obj_content} : {empty_obj};"

    return re.sub(pattern, replacer, content, flags=re.DOTALL)


def wrap_mock_array(content: str) -> str:
    """Wrap mock array declarations with DEMO_MODE conditionals."""
    # Pattern: const mockXXX: Type[] = [ ... ];
    # Replace with: const mockXXX: Type[] = DEMO_MODE ? [ ... ] : [];

    pattern = r"(const mock\w+:\s*\w+\[\]\s*=\s*)(\[[^\]]*?\]);"

    def replacer(match):
        var_decl = match.group(1)
        array_content = match.group(2)

        # Skip if already wrapped
        if "DEMO_MODE" in var_decl:
            return match.group(0)

        return f"{var_decl}DEMO_MODE ? {array_content} : [];"

    # Handle multi-line arrays
    content = re.sub(
        r"(const mock\w+:\s*\w+\[\]\s*=\s*)(\[[\s\S]*?\n\s*\]);",
        lambda m: f"{m.group(1)}DEMO_MODE ? {m.group(2)} : [];"
        if "DEMO_MODE" not in m.group(1)
        else m.group(0),
        content,
    )

    return content


def process_dashboard(file_path: Path, dashboard_name: str) -> bool:
    """Process a single dashboard file to add demo mode conditionals."""
    if not file_path.exists():
        print(f"  ⚠️  {dashboard_name} not found at {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if already has DEMO_MODE
    if "const DEMO_MODE" in content and "DEMO_MODE ?" in content:
        print(f"  ✅ {dashboard_name} already has demo mode implementation")
        return True

    # Add DEMO_MODE check
    content = add_demo_mode_check(content, dashboard_name)

    # Wrap mock data
    content = wrap_mock_object(content)
    content = wrap_mock_array(content)

    # Write back
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  ✅ Updated {dashboard_name}")
    return True


def main():
    print("=" * 70)
    print("APPLYING DEMO MODE TO ALL DASHBOARDS")
    print("=" * 70)
    print()

    base_path = Path("/Users/kay/uatp-capsule-engine/frontend/src/components")

    dashboards = [
        (base_path / "akc/akc-dashboard.tsx", "AKC Dashboard"),
        (base_path / "reasoning/reasoning-dashboard.tsx", "Reasoning Dashboard"),
        (base_path / "federation/federation-dashboard.tsx", "Federation Dashboard"),
        (base_path / "economics/economic-dashboard.tsx", "Economic Dashboard"),
        (base_path / "mirror-mode/mirror-mode-dashboard.tsx", "Mirror Mode Dashboard"),
        (
            base_path / "organization/organization-dashboard.tsx",
            "Organization Dashboard",
        ),
        (base_path / "trust/trust-dashboard.tsx", "Trust Dashboard"),
    ]

    successful = 0
    for file_path, name in dashboards:
        print(f"\nProcessing: {name}...")
        if process_dashboard(file_path, name):
            successful += 1

    print()
    print("=" * 70)
    print(f"COMPLETED: {successful}/{len(dashboards)} dashboards updated")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Test with NEXT_PUBLIC_DEMO_MODE=false (production mode)")
    print("2. Test with NEXT_PUBLIC_DEMO_MODE=true (demo mode)")
    print("3. Verify no mock data appears in production")
    print()


if __name__ == "__main__":
    main()
