#!/usr/bin/env python3
"""
Database Backup and Recovery CLI
================================

Command-line interface for database backup and recovery operations.
"""

import argparse
import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from scripts.database_backup import DatabaseBackupManager


async def cmd_backup(args):
    """Create a database backup."""

    backup_manager = DatabaseBackupManager(args.backup_dir)

    print("📦 Creating database backup...")
    backup_result = await backup_manager.create_sqlite_backup()

    if backup_result["status"] == "completed":
        print(f"✅ Backup created successfully!")
        print(f"   File: {backup_result['backup_file']}")
        print(f"   Size: {backup_result['backup_size'] / 1024 / 1024:.1f} MB")
        print(f"   Files: {len(backup_result['files'])}")

        if args.verify:
            print("\n🔍 Verifying backup...")
            verification_result = await backup_manager.verify_backup(
                backup_result["backup_file"]
            )

            if verification_result["status"] == "passed":
                print("✅ Backup verification passed")
            else:
                print(f"❌ Backup verification failed")
                if args.verbose:
                    print(
                        f"   Error: {verification_result.get('error', 'Unknown error')}"
                    )
                return 1
    else:
        print(f"❌ Backup failed: {backup_result.get('error', 'Unknown error')}")
        return 1

    return 0


async def cmd_restore(args):
    """Restore database from backup."""

    backup_manager = DatabaseBackupManager(args.backup_dir)

    if not args.backup_file:
        print("❌ Backup file required for restore operation")
        return 1

    if not Path(args.backup_file).exists():
        print(f"❌ Backup file not found: {args.backup_file}")
        return 1

    if not args.force:
        response = input(
            f"⚠️ This will overwrite the current database. Continue? (y/N): "
        )
        if response.lower() != "y":
            print("Restore cancelled")
            return 0

    print(f"🔄 Restoring database from: {args.backup_file}")
    restore_result = await backup_manager.restore_from_backup(args.backup_file)

    if restore_result["status"] == "completed":
        print("✅ Database restored successfully!")
        print(f"   Files restored: {len(restore_result['restored_files'])}")
        for file in restore_result["restored_files"]:
            print(f"   • {file}")
    else:
        print(f"❌ Restore failed: {restore_result.get('error', 'Unknown error')}")
        return 1

    return 0


async def cmd_list(args):
    """List available backups."""

    backup_manager = DatabaseBackupManager(args.backup_dir)
    backups = backup_manager.list_backups()

    if not backups:
        print("No backups found")
        return 0

    print(f"📋 Available backups ({len(backups)}):")
    print()

    for i, backup in enumerate(backups, 1):
        print(f"{i:2d}. {backup['filename']}")
        print(f"    Size: {backup['size'] / 1024 / 1024:.1f} MB")
        print(f"    Created: {backup['created']}")
        print(f"    Age: {backup['age_days']} days")

        if args.verbose and "metadata" in backup:
            metadata = backup["metadata"]
            print(f"    Capsules: {metadata.get('capsule_count', 'N/A')}")
            print(f"    Platforms: {list(metadata.get('platforms', {}).keys())}")

        print()

    return 0


async def cmd_verify(args):
    """Verify backup integrity."""

    backup_manager = DatabaseBackupManager(args.backup_dir)

    if not args.backup_file:
        print("❌ Backup file required for verification")
        return 1

    if not Path(args.backup_file).exists():
        print(f"❌ Backup file not found: {args.backup_file}")
        return 1

    print(f"🔍 Verifying backup: {args.backup_file}")
    verification_result = await backup_manager.verify_backup(args.backup_file)

    if verification_result["status"] == "passed":
        print("✅ Backup verification passed")

        if args.verbose:
            print(f"   Checks performed: {len(verification_result['checks'])}")
            for check in verification_result["checks"]:
                status_emoji = "✅" if check["status"] == "passed" else "❌"
                print(f"   {status_emoji} {check['check']}")
    else:
        print(f"❌ Backup verification failed")

        if args.verbose:
            failed_checks = [
                c for c in verification_result["checks"] if c["status"] == "failed"
            ]
            print(f"   Failed checks: {len(failed_checks)}")
            for check in failed_checks:
                print(f"   ❌ {check['check']}: {check.get('error', 'Unknown error')}")

        return 1

    return 0


async def cmd_cleanup(args):
    """Clean up old backups."""

    backup_manager = DatabaseBackupManager(args.backup_dir)

    if args.retention_days:
        backup_manager.retention_days = args.retention_days

    if not args.force:
        response = input(
            f"⚠️ This will delete backups older than {backup_manager.retention_days} days. Continue? (y/N): "
        )
        if response.lower() != "y":
            print("Cleanup cancelled")
            return 0

    print(f"🗑️ Cleaning up backups older than {backup_manager.retention_days} days...")
    cleanup_result = backup_manager.cleanup_old_backups()

    if cleanup_result["status"] == "completed":
        print(f"✅ Cleanup completed!")
        print(f"   Deleted: {len(cleanup_result['deleted_files'])} files")
        print(f"   Kept: {len(cleanup_result['kept_files'])} files")

        if args.verbose:
            if cleanup_result["deleted_files"]:
                print("\n   Deleted files:")
                for file_info in cleanup_result["deleted_files"]:
                    print(f"   • {file_info['name']} ({file_info['date']})")
    else:
        print(f"❌ Cleanup failed: {cleanup_result.get('error', 'Unknown error')}")
        return 1

    return 0


def main():
    """Main CLI function."""

    parser = argparse.ArgumentParser(
        description="UATP Database Backup and Recovery CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--backup-dir",
        default="./backups",
        help="Backup directory (default: ./backups)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a database backup")
    backup_parser.add_argument(
        "--verify", action="store_true", help="Verify backup after creation"
    )
    backup_parser.set_defaults(func=cmd_backup)

    # Restore command
    restore_parser = subparsers.add_parser(
        "restore", help="Restore database from backup"
    )
    restore_parser.add_argument("backup_file", help="Backup file to restore from")
    restore_parser.add_argument(
        "--force", action="store_true", help="Skip confirmation prompt"
    )
    restore_parser.set_defaults(func=cmd_restore)

    # List command
    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.set_defaults(func=cmd_list)

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify backup integrity")
    verify_parser.add_argument("backup_file", help="Backup file to verify")
    verify_parser.set_defaults(func=cmd_verify)

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old backups")
    cleanup_parser.add_argument(
        "--retention-days", type=int, help="Retention period in days"
    )
    cleanup_parser.add_argument(
        "--force", action="store_true", help="Skip confirmation prompt"
    )
    cleanup_parser.set_defaults(func=cmd_cleanup)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        return asyncio.run(args.func(args))
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
