#!/usr/bin/env python3
"""
UATP Capsule Engine Demo Runner
===============================

Simple script to run the end-to-end integration demo with different configurations.

Usage:
    python3 demo/run_demo.py [quick|full|stress]

Examples:
    python3 demo/run_demo.py quick    # 2-minute quick demo
    python3 demo/run_demo.py full     # 5-minute full demo
    python3 demo/run_demo.py stress   # 10-minute stress test
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from demo.e2e_integration_demo import E2EIntegrationDemo


async def run_demo_scenario(scenario: str = "full"):
    """Run demo with specified scenario configuration."""

    # Load demo configuration
    config_path = project_root / "demo" / "demo_config.json"
    try:
        with open(config_path) as f:
            config = json.load(f)
    except FileNotFoundError:
        print("[ERROR] Demo configuration file not found!")
        return

    print(f" Running {scenario} demo scenario")
    print(f" Configuration: {config['demo_scenarios'].get(scenario, 'default')}")
    print("=" * 60)

    # Run the demo
    demo = E2EIntegrationDemo()
    await demo.run_complete_demo()


def main():
    """Main entry point for demo runner."""

    # Parse command line arguments
    scenario = "full"  # default
    if len(sys.argv) > 1:
        scenario = sys.argv[1].lower()

    # Validate scenario
    valid_scenarios = ["quick", "full", "stress"]
    if scenario not in valid_scenarios:
        print(f"[ERROR] Invalid scenario: {scenario}")
        print(f"Valid options: {', '.join(valid_scenarios)}")
        print("\nUsage: python3 demo/run_demo.py [quick|full|stress]")
        sys.exit(1)

    print(" UATP Capsule Engine - End-to-End Integration Demo")
    print("=" * 60)
    print(f" Scenario: {scenario}")
    print(f" Working directory: {os.getcwd()}")
    print(f" Python version: {sys.version}")
    print()

    try:
        asyncio.run(run_demo_scenario(scenario))
    except KeyboardInterrupt:
        print("\n\n Demo interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Demo failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
