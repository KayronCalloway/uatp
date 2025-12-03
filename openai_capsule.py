#!/usr/bin/env python3
"""
Simple CLI utility to create OpenAI capsules automatically
"""

import argparse
import asyncio
import json
import os
import sys
import traceback
from datetime import datetime
from typing import Optional

print("Script starting...")

# Write credentials to .env file if it doesn't exist
env_file = ".env"
if not os.path.exists(env_file):
    with open(env_file, "w") as f:
        f.write(
            "OPENAI_API_KEY=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\n"
        )
        f.write(
            "UATP_SIGNING_KEY=b37a06de670822232034c6e9e657339d9eb4fd84f9a7cfd11c33c8a2a7d5d512\n"
        )
        f.write(
            "UATP_VERIFY_KEY=06c6b69c199f097a0934fd8b3fef3fe67e824df308f1d3fe6461a7bcdc026754\n"
        )
        f.write("UATP_USER_ID=kay\n")
    print(f"Created {env_file} with credentials")

# Try to load .env file if available
try:
    from dotenv import load_dotenv

    load_dotenv()
    print("Loaded environment from .env file")
except ImportError:
    print("dotenv package not found. Using system environment variables.")
    print("Tip: Install with 'pip install python-dotenv' to use .env files")

# Import UATP modules
try:
    print("Importing UATP modules...")
    # Add the project root to Python path so imports work properly
    import sys

    sys.path.insert(0, os.getcwd())

    from src.capsule_schema import CapsuleType
    from src.integrations.openai_attribution import (
        AttributionContext,
        create_attribution_client,
    )

    print("UATP modules imported successfully")
except ImportError as e:
    print(f"Error importing UATP modules: {e}")
    traceback.print_exc()
    print("Make sure you're running this script from the UATP project root")
    sys.exit(1)


async def create_openai_capsule(
    prompt: str, model: str = "gpt-4", user_id: Optional[str] = None
):
    """Create a capsule from an OpenAI interaction"""

    print("Creating OpenAI capsule...")

    # Create attribution client
    print("Creating attribution client...")
    client = create_attribution_client()
    print("Attribution client created")

    # Create attribution context
    context = AttributionContext(
        user_id=user_id or os.environ.get("UATP_USER_ID", "default_user"),
        conversation_id=f"cli_convo_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    )

    print(f"\nSending prompt to OpenAI ({model}): {prompt!r}")

    try:
        # Get completion with attribution
        print("Calling OpenAI API...")
        completion, attribution = await client.get_completion_with_attribution(
            prompt=prompt, attribution_context=context, model=model
        )

        print("\n--- Response ---\n")
        print(completion)
        print("\n--- Capsule Created ---")
        print(f"Attribution Total Value: ${attribution.total_value}")

        # List the newest capsule
        import glob
        import time

        print("Looking for created capsule...")
        time.sleep(1)  # Give filesystem time to update

        # Create capsules directory if it doesn't exist
        os.makedirs("capsules", exist_ok=True)

        capsules = glob.glob("capsules/*.json")
        if capsules:
            newest_capsule = max(capsules, key=os.path.getctime)
            print(f"Capsule saved as: {newest_capsule}")

            # Display capsule content
            try:
                with open(newest_capsule) as f:
                    capsule_data = json.load(f)
                print(f"Capsule ID: {capsule_data.get('capsule_id', 'unknown')}")
                print(f"Created: {capsule_data.get('created_at', 'unknown')}")
                print(f"Type: {capsule_data.get('capsule_type', 'unknown')}")
            except Exception as e:
                print(f"Error reading capsule: {e}")
        else:
            print("No capsules found in capsules/ directory")

            # Check the entire directory structure
            print("Checking directory structure for capsules:")
            for root, dirs, files in os.walk("."):
                if root.startswith("./.git"):
                    continue
                json_files = [f for f in files if f.endswith(".json")]
                if json_files:
                    print(f"Found {len(json_files)} JSON files in: {root}")
                    for json_file in json_files[:3]:  # Show up to 3 examples
                        print(f" - {json_file}")

    except Exception as e:
        print(f"Error during OpenAI call: {e}")
        traceback.print_exc()
        print("Check if your OpenAI API key is valid and has sufficient credits")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Create OpenAI capsules automatically")
    parser.add_argument("prompt", nargs="?", help="The prompt to send to OpenAI")
    parser.add_argument("--model", default="gpt-4", help="OpenAI model to use")
    parser.add_argument("--user", help="User ID for attribution")
    args = parser.parse_args()

    print(f"Arguments: prompt={args.prompt!r}, model={args.model}")

    # Check if OpenAI API key is set
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("Error: OPENAI_API_KEY environment variable is not set")
        print("Please set it in your .env file or export it in your shell")
        sys.exit(1)
    else:
        print(f"OpenAI API key found: {openai_key[:5]}...{openai_key[-5:]}")

    # Check if UATP keys are set
    signing_key = os.environ.get("UATP_SIGNING_KEY")
    verify_key = os.environ.get("UATP_VERIFY_KEY")
    if not signing_key or not verify_key:
        print("Warning: UATP_SIGNING_KEY and/or UATP_VERIFY_KEY not set")
        print("Capsules may be created without proper signing")
    else:
        print(f"UATP signing key found: {signing_key[:5]}...{signing_key[-5:]}")
        print(f"UATP verify key found: {verify_key[:5]}...{verify_key[-5:]}")

    # Get prompt from argument or stdin if piped
    prompt = args.prompt
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()

    if not prompt:
        parser.print_help()
        sys.exit(1)

    print("Running async function...")

    # Run async function
    try:
        asyncio.run(create_openai_capsule(prompt, args.model, args.user))
    except Exception as e:
        print(f"Unhandled exception: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("Script main block executing...")
    main()
