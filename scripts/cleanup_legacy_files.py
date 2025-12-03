#!/usr/bin/env python3
"""
Cleanup script to remove legacy fix scripts and patches.
This script identifies and optionally removes one-off fixes that have been integrated.
"""

import shutil
from pathlib import Path
from typing import Dict

# Files to remove (confirmed legacy/temporary fixes)
LEGACY_FILES = [
    "fix_get_capsule.py",
    "fix_duplicate_route.py",
    "fix_parse_bool_param.py",
    "fix_test_suite.py",
    "debug_compressed_response.py",
    "direct_fix_compression.py",
    "final_fix_updated.py",
    "fix_direct.py",
    "clean_server_fix.py",
    "fix_compressed_response.py",
    "fix_clear_cache.py",
    "final_fix.py",
    "fix_duplicate_raw_data.py",
    "debug_endpoints.py",
    "fix_raw_data_inclusion.py",
    "debug_test_request.py",
    "fix_compressed_response_format.py",
    "fix_syntax_error.py",
    "fix_duplicate_endpoint.py",
    "fix_endpoints.py",
    "fix_include_raw.py",
    "fix_list_capsules_compressed.py",
    "fix_parse_bool_param_corrected.py",
    "fix_raw_data.py",
    "fix_raw_data_corrected.py",
    "fix_server_syntax.py",
    "fix_step_type.py",
    "clean_server_fix_corrected.py",
    "debug_integration.py",
    "debug_raw_data.py",
    "debug_test_failures.py",
    "detailed_raw_data_debug.py",
    "direct_api_test.py",
    "direct_fix_raw_data.py",
    "manual_raw_data_fix.py",
    "implement_get_capsule.py",
    "add_parse_bool.py",
]

# Test files that should be consolidated
TEST_FILES_TO_CONSOLIDATE = [
    "test_ethics_circuit_breaker.py",
    "test_governance_viz.py",
    "test_llm_registry.py",
    "test_observability_complete.py",
]

# Demo files that should be in examples/
DEMO_FILES = [
    "demo_merging.py",
    "demo_reasoning.py",
    "quick_start.py",
    "simple_demo.py",
    "compare_requests.py",
]


def analyze_codebase():
    """Analyze the current state of the codebase."""

    root_dir = Path("/Users/kay/uatp-capsule-engine")

    analysis = {
        "legacy_files": [],
        "test_files": [],
        "demo_files": [],
        "total_python_files": 0,
        "src_files": 0,
        "root_clutter": 0,
    }

    # Count all Python files
    for py_file in root_dir.glob("**/*.py"):
        analysis["total_python_files"] += 1

        if py_file.is_relative_to(root_dir / "src"):
            analysis["src_files"] += 1

    # Find legacy files
    for legacy_file in LEGACY_FILES:
        file_path = root_dir / legacy_file
        if file_path.exists():
            analysis["legacy_files"].append(file_path)
            analysis["root_clutter"] += 1

    # Find test files in root
    for test_file in TEST_FILES_TO_CONSOLIDATE:
        file_path = root_dir / test_file
        if file_path.exists():
            analysis["test_files"].append(file_path)
            analysis["root_clutter"] += 1

    # Find demo files in root
    for demo_file in DEMO_FILES:
        file_path = root_dir / demo_file
        if file_path.exists():
            analysis["demo_files"].append(file_path)
            analysis["root_clutter"] += 1

    return analysis


def create_cleanup_plan(analysis: Dict) -> Dict:
    """Create a cleanup plan based on analysis."""

    plan = {"remove": [], "move_to_examples": [], "move_to_tests": [], "archive": []}

    # Legacy files to remove
    plan["remove"] = analysis["legacy_files"]

    # Demo files to move to examples
    plan["move_to_examples"] = analysis["demo_files"]

    # Test files to move to tests
    plan["move_to_tests"] = analysis["test_files"]

    return plan


def execute_cleanup(plan: Dict, dry_run: bool = True):
    """Execute the cleanup plan."""

    print(f"🧹 Executing cleanup plan (dry_run={dry_run})")
    print("=" * 60)

    # Remove legacy files
    print(f"\n📁 Removing {len(plan['remove'])} legacy files:")
    for file_path in plan["remove"]:
        print(f"   - {file_path.name}")
        if not dry_run:
            file_path.unlink()

    # Move demo files
    print(f"\n📦 Moving {len(plan['move_to_examples'])} demo files to examples/:")
    examples_dir = Path("/Users/kay/uatp-capsule-engine/examples")
    examples_dir.mkdir(exist_ok=True)

    for file_path in plan["move_to_examples"]:
        dest = examples_dir / file_path.name
        print(f"   - {file_path.name} → {dest}")
        if not dry_run and file_path.exists():
            shutil.move(str(file_path), str(dest))

    # Move test files
    print(f"\n🧪 Moving {len(plan['move_to_tests'])} test files to tests/:")
    tests_dir = Path("/Users/kay/uatp-capsule-engine/tests")
    tests_dir.mkdir(exist_ok=True)

    for file_path in plan["move_to_tests"]:
        dest = tests_dir / file_path.name
        print(f"   - {file_path.name} → {dest}")
        if not dry_run and file_path.exists():
            shutil.move(str(file_path), str(dest))


def generate_cleanup_report(analysis: Dict, plan: Dict):
    """Generate a cleanup report."""

    report = f"""
# UATP Codebase Cleanup Report

## Current State Analysis

- **Total Python files**: {analysis['total_python_files']}
- **Files in src/**: {analysis['src_files']}
- **Root directory clutter**: {analysis['root_clutter']} files
- **Organization ratio**: {analysis['src_files'] / analysis['total_python_files'] * 100:.1f}% properly organized

## Issues Identified

### 1. Module Sprawl
- **{len(analysis['legacy_files'])} legacy fix scripts** in root directory
- **{len(analysis['demo_files'])} demo files** scattered in root
- **{len(analysis['test_files'])} test files** outside tests/ directory

### 2. Root Directory Pollution
Files that should be organized:
"""

    if analysis["legacy_files"]:
        report += "\n**Legacy Files (to remove):**\n"
        for f in analysis["legacy_files"]:
            report += f"- {f.name}\n"

    if analysis["demo_files"]:
        report += "\n**Demo Files (move to examples/):**\n"
        for f in analysis["demo_files"]:
            report += f"- {f.name}\n"

    if analysis["test_files"]:
        report += "\n**Test Files (move to tests/):**\n"
        for f in analysis["test_files"]:
            report += f"- {f.name}\n"

    report += f"""

## Cleanup Plan

1. **Remove** {len(plan['remove'])} legacy/temporary files
2. **Organize** {len(plan['move_to_examples'])} demo files into examples/
3. **Consolidate** {len(plan['move_to_tests'])} test files into tests/

## Expected Outcome

- **Root directory**: Clean, only essential files
- **Organization ratio**: ~90%+ properly organized
- **Maintainability**: Significantly improved
- **Developer experience**: Clear structure

## Next Steps

1. Run cleanup script: `python3 scripts/cleanup_legacy_files.py --execute`
2. Update documentation to reflect new structure
3. Create proper module organization guidelines
"""

    return report


def main():
    """Main cleanup function."""

    import argparse

    parser = argparse.ArgumentParser(description="Clean up UATP codebase")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute cleanup (default: dry run)",
    )
    parser.add_argument("--report", action="store_true", help="Generate cleanup report")

    args = parser.parse_args()

    print("🔍 UATP Codebase Cleanup Analysis")
    print("=" * 60)

    # Analyze current state
    analysis = analyze_codebase()

    print("📊 Analysis Results:")
    print(f"   - Total Python files: {analysis['total_python_files']}")
    print(f"   - Properly organized: {analysis['src_files']}")
    print(f"   - Root clutter: {analysis['root_clutter']} files")
    print(
        f"   - Organization ratio: {analysis['src_files'] / analysis['total_python_files'] * 100:.1f}%"
    )

    # Create cleanup plan
    plan = create_cleanup_plan(analysis)

    if args.report:
        # Generate report
        report = generate_cleanup_report(analysis, plan)

        with open("docs/CODEBASE_CLEANUP_REPORT.md", "w") as f:
            f.write(report)

        print("\n📋 Cleanup report generated: docs/CODEBASE_CLEANUP_REPORT.md")

    # Execute cleanup
    execute_cleanup(plan, dry_run=not args.execute)

    if not args.execute:
        print("\n💡 This was a dry run. Use --execute to actually perform cleanup.")
        print("   Use --report to generate detailed cleanup report.")

    return True


if __name__ == "__main__":
    main()
