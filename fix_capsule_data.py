#!/usr/bin/env python3
"""
Fix capsule data in SQLite database to match UATP 7.0 schema.
"""
import sqlite3
import json
import hashlib
from datetime import datetime


def fix_capsule_data():
    """Fix capsule data to match UATP 7.0 schema."""

    # Connect to database
    conn = sqlite3.connect("uatp_dev.db")
    cursor = conn.cursor()

    # Get all capsules
    cursor.execute(
        "SELECT id, capsule_id, capsule_type, version, status, verification, payload FROM capsules"
    )
    capsules = cursor.fetchall()

    print(f"Found {len(capsules)} capsules to fix")

    for capsule in capsules:
        (
            id_,
            capsule_id,
            capsule_type,
            version,
            status,
            verification_json,
            payload_json,
        ) = capsule

        # Parse JSON fields
        verification = json.loads(verification_json) if verification_json else {}
        payload = json.loads(payload_json) if payload_json else {}

        # Fix capsule_id format if needed
        if not capsule_id.startswith("caps_"):
            # Generate a new UATP 7.0 compatible capsule_id
            # Format: caps_YYYY_MM_DD_16hexchars
            now = datetime.now()
            hex_suffix = hashlib.sha256(capsule_id.encode()).hexdigest()[:16]
            new_capsule_id = (
                f"caps_{now.year}_{now.month:02d}_{now.day:02d}_{hex_suffix}"
            )
            print(f"Fixing capsule_id: {capsule_id} -> {new_capsule_id}")
            capsule_id = new_capsule_id

        # Fix version
        if version != "7.0":
            print(f"Fixing version: {version} -> 7.0")
            version = "7.0"

        # Fix status
        if status == "SEALED":
            print(f"Fixing status: {status} -> sealed")
            status = "sealed"

        # Fix verification fields
        if "hash" not in verification or not verification["hash"]:
            verification["hash"] = "0" * 64
        if "signature" not in verification or not verification["signature"]:
            verification["signature"] = "ed25519:" + "0" * 128
        if "merkle_root" not in verification:
            verification["merkle_root"] = "sha256:" + "0" * 64

        # Update the database
        cursor.execute(
            "UPDATE capsules SET capsule_id = ?, version = ?, status = ?, verification = ? WHERE id = ?",
            (capsule_id, version, status, json.dumps(verification), id_),
        )

    # Commit changes
    conn.commit()
    conn.close()

    print(f"Successfully fixed {len(capsules)} capsules")


if __name__ == "__main__":
    fix_capsule_data()
