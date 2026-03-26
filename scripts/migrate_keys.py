#!/usr/bin/env python3
"""
Key Migration Script
====================
Migrates signing keys from old machine-derived password to new scheme.

Usage:
    python scripts/migrate_keys.py

This will:
1. Try to decrypt keys with old machine-derived password
2. Re-encrypt with new password (UATP_KEY_PASSWORD or dev default)
3. Backup old keys first
"""

import hashlib
import os
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def get_old_machine_uuid() -> str:
    """Replicate the old machine UUID detection."""
    system = platform.system()
    try:
        if system == "Darwin":
            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.split("\n"):
                if "IOPlatformUUID" in line:
                    return line.split('"')[-2]
        elif system == "Linux":
            if os.path.exists("/etc/machine-id"):
                with open("/etc/machine-id") as f:
                    return f.read().strip()
        elif system == "Windows":
            result = subprocess.run(
                ["wmic", "csproduct", "get", "UUID"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                return lines[1].strip()
    except Exception:
        pass

    return "-".join(
        [platform.node(), platform.machine(), os.environ.get("USER", "unknown")]
    )


def derive_old_password() -> bytes:
    """Derive the old machine-specific password."""
    machine_uuid = get_old_machine_uuid()
    factors = [
        machine_uuid,
        os.environ.get("USER", ""),
        platform.node(),
        "uatp-capsule-engine-v7-key",
    ]
    combined = ":".join(factors).encode("utf-8")
    salt = hashlib.sha256(f"uatp-v7-{machine_uuid}".encode()).digest()[:16]
    return hashlib.pbkdf2_hmac("sha256", combined, salt, 480_000)


def get_new_password() -> bytes:
    """Get the new password."""
    password = os.environ.get("UATP_KEY_PASSWORD")
    if password:
        return password.encode("utf-8")
    return b"uatp-dev-key-not-for-production"


def migrate_keys(key_dir: str = ".uatp_keys"):
    """Migrate keys from old to new password scheme."""
    from cryptography.hazmat.primitives import serialization

    key_path = Path(key_dir)
    if not key_path.exists():
        print(f"No keys found at {key_dir}")
        return

    # Backup first
    backup_dir = f"{key_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copytree(key_dir, backup_dir)
    print(f"Backed up keys to {backup_dir}")

    old_password = derive_old_password()
    new_password = get_new_password()

    if old_password == new_password:
        print("Passwords are the same, no migration needed")
        return

    # Migrate Ed25519 key
    ed_key_path = key_path / "ed25519_private.pem.enc"
    if ed_key_path.exists():
        try:
            with open(ed_key_path, "rb") as f:
                key_data = f.read()

            # Decrypt with old password
            private_key = serialization.load_pem_private_key(
                key_data, password=old_password
            )
            print("Decrypted Ed25519 key with old password")

            # Re-encrypt with new password
            new_key_data = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(
                    new_password
                ),
            )

            with open(ed_key_path, "wb") as f:
                f.write(new_key_data)
            print("Re-encrypted Ed25519 key with new password")

        except Exception as e:
            print(f"Failed to migrate Ed25519 key: {e}")
            print("You may need to regenerate keys with: rm -rf .uatp_keys")
            return

    print("\nMigration complete!")
    print("Set UATP_KEY_PASSWORD env var for production use.")


if __name__ == "__main__":
    migrate_keys()
