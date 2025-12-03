#!/usr/bin/env python3
"""
Migration script to update capsule chain data to match the new Pydantic schema.

This script:
1. Reads the existing capsule_chain.jsonl file
2. Updates each capsule record to conform to the Pydantic schema
   - Adds missing required fields with sensible defaults
   - Maps fields that need to be renamed
3. Writes updated records to a new file
4. Replaces the original file with the fixed version
"""

import json
import os
import shutil
import sys

CHAIN_FILE = "capsule_chain.jsonl"
BACKUP_FILE = "capsule_chain.jsonl.bak"
TEMP_FILE = "capsule_chain.jsonl.new"


def get_json_str_from_list(item_list):
    """Convert a list to a JSON string or return a reasonable default."""
    if not item_list:
        return "No reasoning provided"

    if isinstance(item_list, list):
        return json.dumps(item_list)
    return str(item_list)


def migrate_capsule(capsule):
    """Migrate a single capsule record to match the new schema."""
    # Create a copy to avoid modifying the original
    updated = capsule.copy()

    # Add required fields if missing
    if "input" not in updated and "input_data" not in updated:
        # Try to infer input from reasoning_trace or use default
        if "reasoning_trace" in updated and updated["reasoning_trace"]:
            first_trace = (
                updated["reasoning_trace"][0]
                if isinstance(updated["reasoning_trace"], list)
                else updated["reasoning_trace"]
            )
            if isinstance(first_trace, str) and first_trace.startswith("Asked:"):
                # Extract the question from the trace
                input_text = first_trace.replace("Asked:", "").strip()
            else:
                input_text = "Inferred input from capsule creation"
        else:
            input_text = "Inferred input from capsule creation"

        updated["input"] = input_text

    if "output" not in updated:
        # Try to infer output from reasoning_trace or use default
        if "reasoning_trace" in updated and updated["reasoning_trace"]:
            traces = (
                updated["reasoning_trace"]
                if isinstance(updated["reasoning_trace"], list)
                else [updated["reasoning_trace"]]
            )
            for trace in traces:
                if isinstance(trace, str) and trace.startswith("Model:"):
                    output_text = trace.replace("Model:", "").strip()
                    break
            else:
                output_text = "Generated output based on reasoning"
        else:
            output_text = "Generated output based on reasoning"

        updated["output"] = output_text

    if "reasoning" not in updated:
        # Map reasoning_trace to reasoning
        if "reasoning_trace" in updated:
            updated["reasoning"] = get_json_str_from_list(updated["reasoning_trace"])
        else:
            updated["reasoning"] = "No explicit reasoning provided for this capsule"

    if "model_version" not in updated:
        # Default model version
        updated["model_version"] = "legacy-pre-schema-update"

    # Map field names that need to be renamed
    if "previous_capsule_id" in updated and "parent_capsule" not in updated:
        updated["parent_capsule"] = updated["previous_capsule_id"]

    if "capsule_type" in updated and "type" not in updated:
        updated["type"] = updated["capsule_type"]

    return updated


def migrate_chain_file():
    """Migrate the entire capsule chain file."""
    if not os.path.exists(CHAIN_FILE):
        print(f"Error: Chain file '{CHAIN_FILE}' not found.")
        return False

    # Create a backup of the original file
    try:
        shutil.copy2(CHAIN_FILE, BACKUP_FILE)
        print(f"Created backup of original chain file as '{BACKUP_FILE}'")
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

    migrated_count = 0
    error_count = 0

    try:
        with open(CHAIN_FILE) as infile, open(TEMP_FILE, "w") as outfile:
            for line_num, line in enumerate(infile, 1):
                try:
                    if not line.strip():
                        continue

                    capsule = json.loads(line)
                    updated_capsule = migrate_capsule(capsule)
                    outfile.write(json.dumps(updated_capsule) + "\n")
                    migrated_count += 1
                except Exception as e:
                    print(f"Error processing line {line_num}: {e}")
                    error_count += 1

        # Replace the original file with the updated one
        os.replace(TEMP_FILE, CHAIN_FILE)
        print(
            f"Migration completed: {migrated_count} capsules migrated, {error_count} errors"
        )
        return True
    except Exception as e:
        print(f"Migration failed: {e}")
        if os.path.exists(TEMP_FILE):
            os.unlink(TEMP_FILE)
        return False


if __name__ == "__main__":
    print("Starting capsule chain migration...")
    success = migrate_chain_file()

    if success:
        print(f"Migration successful. Original file backed up as {BACKUP_FILE}")
        sys.exit(0)
    else:
        print("Migration failed. See errors above.")
        sys.exit(1)
