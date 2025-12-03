#!/usr/bin/env python3
"""
Fix malformed payload JSON where steps are stored as strings.
"""
import sqlite3
import json


def fix_payload_json():
    """Fix malformed payload JSON."""

    # Connect to database
    conn = sqlite3.connect("uatp_dev.db")
    cursor = conn.cursor()

    # Get all capsules
    cursor.execute("SELECT id, capsule_id, payload FROM capsules")
    capsules = cursor.fetchall()

    print(f"Checking {len(capsules)} capsules for JSON payload issues")

    fixed_count = 0

    for capsule in capsules:
        id_, capsule_id, payload_json = capsule

        try:
            # Parse the payload
            payload = json.loads(payload_json)

            # Check if steps is a string
            if "steps" in payload and isinstance(payload["steps"], str):
                print(f"Fixing capsule {capsule_id}: steps is a string")

                # Parse the string as JSON
                try:
                    payload["steps"] = json.loads(payload["steps"])
                    fixed_count += 1

                    # Update the database
                    cursor.execute(
                        "UPDATE capsules SET payload = ? WHERE id = ?",
                        (json.dumps(payload), id_),
                    )

                except json.JSONDecodeError as e:
                    print(f"Warning: Could not parse steps JSON for {capsule_id}: {e}")
                    # Set to empty list as fallback
                    payload["steps"] = []
                    cursor.execute(
                        "UPDATE capsules SET payload = ? WHERE id = ?",
                        (json.dumps(payload), id_),
                    )

        except json.JSONDecodeError as e:
            print(f"Error: Could not parse payload JSON for {capsule_id}: {e}")
            continue

    # Commit changes
    conn.commit()
    conn.close()

    print(f"Fixed {fixed_count} capsules with malformed payload JSON")


if __name__ == "__main__":
    fix_payload_json()
