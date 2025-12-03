#!/usr/bin/env python3
"""
Wrap all mock/demo data in frontend dashboards with demo mode conditionals.
This allows mock data to be shown only when NEXT_PUBLIC_DEMO_MODE=true.
"""

import re
from pathlib import Path

# Demo mode header to add to each dashboard
DEMO_MODE_CHECK = """
// Demo mode - mock data only shown when NEXT_PUBLIC_DEMO_MODE=true
const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === 'true';
"""

def wrap_mock_data_platform_dashboard():
    """Wrap mock data in platform-dashboard.tsx"""
    file_path = Path('/Users/kay/uatp-capsule-engine/frontend/src/components/platform/platform-dashboard.tsx')

    with open(file_path, 'r') as f:
        content = f.read()

    # Add demo mode check after imports and interfaces
    # Find where mockStats starts (after line 96 approximately)
    content = content.replace(
        "  // Mock data - in real implementation, these would come from API endpoints\n  const mockStats",
        f"{DEMO_MODE_CHECK}\n  // Mock data - only shown in demo mode\n  const mockStats"
    )

    # Wrap the mock data initializations
    # Replace mockStats assignment
    content = re.sub(
        r'const mockStats: APIKeyStats = \{[^}]+\};',
        lambda m: f"const mockStats: APIKeyStats = DEMO_MODE ? {m.group(0).split('= ')[1]} : {{\n    total_keys: 0,\n    active_keys: 0,\n    keys_used_today: 0,\n    total_platforms: 0,\n    total_requests_today: 0,\n    total_cost_this_month: 0\n  };",
        content,
        flags=re.DOTALL
    )

    # Replace mockPlatforms assignment
    content = re.sub(
        r'const mockPlatforms: Platform\[\] = \[[^\]]+\];',
        'const mockPlatforms: Platform[] = DEMO_MODE ? [...] : [];  // Demo data omitted for brevity',
        content,
        flags=re.DOTALL
    )

    print(f"✅ Updated {file_path}")

    # Write back
    with open(file_path, 'w') as f:
        f.write(content)


def process_dashboard_file(file_path_str, dashboard_name):
    """Generic function to wrap mock data in any dashboard file"""
    file_path = Path(file_path_str)

    if not file_path.exists():
        print(f"⚠️  Skipping {dashboard_name} - file not found")
        return

    with open(file_path, 'r') as f:
        content = f.read()

    # Check if demo mode already added
    if 'const DEMO_MODE' in content:
        print(f"ℹ️  {dashboard_name} already has demo mode check")
        return

    # Add demo mode check after the last import and before any const declarations
    # Find the export function line
    export_match = re.search(r'export function \w+Dashboard\(\)', content)
    if not export_match:
        print(f"⚠️  Could not find export function in {dashboard_name}")
        return

    # Insert demo mode check right after the opening brace of the function
    insert_pos = content.find('{', export_match.end()) + 1
    content = content[:insert_pos] + f"\n{DEMO_MODE_CHECK}\n" + content[insert_pos:]

    # Find and wrap mock data declarations
    # Pattern: const mockXXX: Type = { ... };
    # Pattern: const mockXXX: Type[] = [ ... ];

    # For object mock data
    content = re.sub(
        r'(const mock\w+: \w+(?:<[^>]+>)? = )(\{[^;]+\});',
        lambda m: f'{m.group(1)}DEMO_MODE ? {m.group(2)} : {get_empty_value(m.group(0))};',
        content,
        flags=re.DOTALL
    )

    # For array mock data
    content = re.sub(
        r'(const mock\w+: \w+\[\] = )(\[[^\]]*\]);',
        lambda m: f'{m.group(1)}DEMO_MODE ? {m.group(2)} : [];',
        content
    )

    print(f"✅ Updated {file_path}")

    with open(file_path, 'w') as f:
        f.write(content)


def get_empty_value(mock_declaration):
    """Get appropriate empty value based on the mock data type"""
    if 'Array' in mock_declaration or '[]' in mock_declaration:
        return '[]'
    else:
        # Return empty object with zero/empty values for stats objects
        # This is a simplified version - could be enhanced to parse the actual type
        return '{}'


def main():
    print("=" * 60)
    print("WRAPPING MOCK DATA IN DEMO MODE CONDITIONALS")
    print("=" * 60)
    print()

    dashboards = [
        ('/Users/kay/uatp-capsule-engine/frontend/src/components/platform/platform-dashboard.tsx', 'Platform Dashboard'),
        ('/Users/kay/uatp-capsule-engine/frontend/src/components/akc/akc-dashboard.tsx', 'AKC Dashboard'),
        ('/Users/kay/uatp-capsule-engine/frontend/src/components/reasoning/reasoning-dashboard.tsx', 'Reasoning Dashboard'),
        ('/Users/kay/uatp-capsule-engine/frontend/src/components/federation/federation-dashboard.tsx', 'Federation Dashboard'),
        ('/Users/kay/uatp-capsule-engine/frontend/src/components/economics/economic-dashboard.tsx', 'Economic Dashboard'),
        ('/Users/kay/uatp-capsule-engine/frontend/src/components/mirror-mode/mirror-mode-dashboard.tsx', 'Mirror Mode Dashboard'),
        ('/Users/kay/uatp-capsule-engine/frontend/src/components/organization/organization-dashboard.tsx', 'Organization Dashboard'),
    ]

    for file_path, name in dashboards:
        print(f"\nProcessing: {name}...")
        try:
            process_dashboard_file(file_path, name)
        except Exception as e:
            print(f"❌ Error processing {name}: {e}")

    print()
    print("=" * 60)
    print("DEMO MODE WRAPPING COMPLETE")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Add NEXT_PUBLIC_DEMO_MODE=false to frontend/.env.local for production")
    print("2. Add NEXT_PUBLIC_DEMO_MODE=true to frontend/.env.development for demos")
    print("3. Test both production and demo modes")
    print()


if __name__ == '__main__':
    main()
