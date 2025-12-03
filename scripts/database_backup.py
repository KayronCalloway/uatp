#!/usr/bin/env python3
"""
Database Backup and Recovery System
===================================

This script provides automated backup and recovery procedures for the UATP
capsule database, supporting both SQLite and PostgreSQL backends.
"""

import asyncio
import datetime
import json
import logging
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import zipfile
import hashlib

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from core.database import db
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseBackupManager:
    """Manager for database backup and recovery operations."""

    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

        # Database paths
        self.sqlite_db_path = Path("./uatp_dev.db")
        self.jsonl_backup_path = Path("./capsule_chain.jsonl")

        # Backup retention (days)
        self.retention_days = 30

        logger.info(f"🔒 Database Backup Manager initialized")
        logger.info(f"   Backup directory: {self.backup_dir}")
        logger.info(f"   Retention period: {self.retention_days} days")

    def generate_backup_filename(self, backup_type: str) -> str:
        """Generate a timestamped backup filename."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"uatp_backup_{backup_type}_{timestamp}"

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    async def create_sqlite_backup(self) -> Dict[str, Any]:
        """Create a comprehensive SQLite database backup."""

        backup_info = {
            "timestamp": datetime.datetime.now().isoformat(),
            "backup_type": "sqlite",
            "status": "started",
            "files": [],
            "metadata": {},
        }

        try:
            if not self.sqlite_db_path.exists():
                logger.warning("SQLite database file not found, creating empty backup")
                backup_info["status"] = "warning"
                backup_info["message"] = "No database file found"
                return backup_info

            backup_name = self.generate_backup_filename("sqlite")
            backup_zip = self.backup_dir / f"{backup_name}.zip"

            logger.info(f"📦 Creating SQLite backup: {backup_name}")

            # Create backup directory structure
            temp_backup_dir = self.backup_dir / f"temp_{backup_name}"
            temp_backup_dir.mkdir(exist_ok=True)

            try:
                # 1. Create SQLite database copy
                db_backup_path = temp_backup_dir / "uatp_database.db"
                shutil.copy2(self.sqlite_db_path, db_backup_path)
                backup_info["files"].append(
                    {
                        "name": "uatp_database.db",
                        "size": db_backup_path.stat().st_size,
                        "hash": self.calculate_file_hash(db_backup_path),
                    }
                )

                # 2. Create SQL dump for portability
                sql_dump_path = temp_backup_dir / "database_dump.sql"
                await self._create_sql_dump(sql_dump_path)
                backup_info["files"].append(
                    {
                        "name": "database_dump.sql",
                        "size": sql_dump_path.stat().st_size,
                        "hash": self.calculate_file_hash(sql_dump_path),
                    }
                )

                # 3. Backup JSONL file if exists
                if self.jsonl_backup_path.exists():
                    jsonl_backup_path = temp_backup_dir / "capsule_chain.jsonl"
                    shutil.copy2(self.jsonl_backup_path, jsonl_backup_path)
                    backup_info["files"].append(
                        {
                            "name": "capsule_chain.jsonl",
                            "size": jsonl_backup_path.stat().st_size,
                            "hash": self.calculate_file_hash(jsonl_backup_path),
                        }
                    )

                # 4. Get database statistics
                stats = await self._get_database_stats()
                backup_info["metadata"] = stats

                # 5. Create backup metadata file
                metadata_path = temp_backup_dir / "backup_metadata.json"
                with open(metadata_path, "w") as f:
                    json.dump(backup_info, f, indent=2)

                # 6. Create compressed backup
                with zipfile.ZipFile(backup_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in temp_backup_dir.rglob("*"):
                        if file_path.is_file():
                            zipf.write(
                                file_path, file_path.relative_to(temp_backup_dir)
                            )

                backup_info["backup_file"] = str(backup_zip)
                backup_info["backup_size"] = backup_zip.stat().st_size
                backup_info["status"] = "completed"

                logger.info(f"✅ SQLite backup completed: {backup_zip}")
                logger.info(f"   Files backed up: {len(backup_info['files'])}")
                logger.info(
                    f"   Backup size: {backup_info['backup_size'] / 1024 / 1024:.1f} MB"
                )

            finally:
                # Clean up temporary directory
                if temp_backup_dir.exists():
                    shutil.rmtree(temp_backup_dir)

        except Exception as e:
            backup_info["status"] = "failed"
            backup_info["error"] = str(e)
            logger.error(f"❌ SQLite backup failed: {e}")

        return backup_info

    async def _create_sql_dump(self, output_path: Path):
        """Create a SQL dump of the SQLite database."""
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            with open(output_path, "w") as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            conn.close()
            logger.info(f"📄 SQL dump created: {output_path}")
        except Exception as e:
            logger.error(f"❌ SQL dump creation failed: {e}")
            raise

    async def _get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics for backup metadata."""
        try:
            async with db.get_session() as session:
                # Get capsule counts
                capsule_result = await session.execute(
                    text("SELECT COUNT(*) FROM capsules_filter")
                )
                capsule_count = capsule_result.scalar() or 0

                # Get attribution counts
                attribution_result = await session.execute(
                    text("SELECT COUNT(*) FROM attributions_filter")
                )
                attribution_count = attribution_result.scalar() or 0

                # Get platform distribution
                platform_result = await session.execute(
                    text(
                        """
                    SELECT platform, COUNT(*) as count
                    FROM attributions_filter
                    GROUP BY platform
                """
                    )
                )

                platforms = {}
                for row in platform_result.fetchall():
                    platforms[row[0]] = row[1]

                # Get date range
                date_result = await session.execute(
                    text(
                        """
                    SELECT MIN(timestamp), MAX(timestamp)
                    FROM capsules_filter
                """
                    )
                )

                date_range = date_result.fetchone()

                return {
                    "capsule_count": capsule_count,
                    "attribution_count": attribution_count,
                    "platforms": platforms,
                    "date_range": {
                        "earliest": date_range[0] if date_range else None,
                        "latest": date_range[1] if date_range else None,
                    },
                    "database_size": self.sqlite_db_path.stat().st_size
                    if self.sqlite_db_path.exists()
                    else 0,
                }

        except Exception as e:
            logger.error(f"❌ Database stats collection failed: {e}")
            return {"error": str(e)}

    async def restore_from_backup(self, backup_file: str) -> Dict[str, Any]:
        """Restore database from backup file."""

        backup_path = Path(backup_file)
        if not backup_path.exists():
            return {"status": "failed", "error": "Backup file not found"}

        restore_info = {
            "timestamp": datetime.datetime.now().isoformat(),
            "backup_file": backup_file,
            "status": "started",
            "restored_files": [],
        }

        try:
            logger.info(f"🔄 Starting database restore from: {backup_file}")

            # Create temporary extraction directory
            temp_restore_dir = (
                self.backup_dir
                / f"temp_restore_{int(datetime.datetime.now().timestamp())}"
            )
            temp_restore_dir.mkdir(exist_ok=True)

            try:
                # Extract backup
                with zipfile.ZipFile(backup_path, "r") as zipf:
                    zipf.extractall(temp_restore_dir)

                # Load backup metadata
                metadata_path = temp_restore_dir / "backup_metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, "r") as f:
                        backup_metadata = json.load(f)
                    restore_info["backup_metadata"] = backup_metadata

                # Restore database file
                db_backup_path = temp_restore_dir / "uatp_database.db"
                if db_backup_path.exists():
                    # Create backup of current database
                    if self.sqlite_db_path.exists():
                        current_backup = self.sqlite_db_path.with_suffix(".db.backup")
                        shutil.copy2(self.sqlite_db_path, current_backup)
                        logger.info(
                            f"📋 Current database backed up to: {current_backup}"
                        )

                    # Restore database
                    shutil.copy2(db_backup_path, self.sqlite_db_path)
                    restore_info["restored_files"].append("uatp_database.db")
                    logger.info(f"✅ Database restored: {self.sqlite_db_path}")

                # Restore JSONL file if exists
                jsonl_backup_path = temp_restore_dir / "capsule_chain.jsonl"
                if jsonl_backup_path.exists():
                    shutil.copy2(jsonl_backup_path, self.jsonl_backup_path)
                    restore_info["restored_files"].append("capsule_chain.jsonl")
                    logger.info(f"✅ JSONL file restored: {self.jsonl_backup_path}")

                restore_info["status"] = "completed"
                logger.info(f"✅ Database restore completed successfully")

            finally:
                # Clean up temporary directory
                if temp_restore_dir.exists():
                    shutil.rmtree(temp_restore_dir)

        except Exception as e:
            restore_info["status"] = "failed"
            restore_info["error"] = str(e)
            logger.error(f"❌ Database restore failed: {e}")

        return restore_info

    def cleanup_old_backups(self) -> Dict[str, Any]:
        """Clean up old backup files based on retention policy."""

        cleanup_info = {
            "timestamp": datetime.datetime.now().isoformat(),
            "retention_days": self.retention_days,
            "deleted_files": [],
            "kept_files": [],
            "status": "started",
        }

        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(
                days=self.retention_days
            )

            for backup_file in self.backup_dir.glob("uatp_backup_*.zip"):
                file_mtime = datetime.datetime.fromtimestamp(
                    backup_file.stat().st_mtime
                )

                if file_mtime < cutoff_date:
                    backup_file.unlink()
                    cleanup_info["deleted_files"].append(
                        {"name": backup_file.name, "date": file_mtime.isoformat()}
                    )
                    logger.info(f"🗑️ Deleted old backup: {backup_file.name}")
                else:
                    cleanup_info["kept_files"].append(
                        {"name": backup_file.name, "date": file_mtime.isoformat()}
                    )

            cleanup_info["status"] = "completed"
            logger.info(f"✅ Backup cleanup completed")
            logger.info(f"   Deleted: {len(cleanup_info['deleted_files'])} files")
            logger.info(f"   Kept: {len(cleanup_info['kept_files'])} files")

        except Exception as e:
            cleanup_info["status"] = "failed"
            cleanup_info["error"] = str(e)
            logger.error(f"❌ Backup cleanup failed: {e}")

        return cleanup_info

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""

        backups = []

        for backup_file in sorted(self.backup_dir.glob("uatp_backup_*.zip")):
            try:
                stat = backup_file.stat()
                backup_info = {
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "size": stat.st_size,
                    "created": datetime.datetime.fromtimestamp(
                        stat.st_mtime
                    ).isoformat(),
                    "age_days": (
                        datetime.datetime.now()
                        - datetime.datetime.fromtimestamp(stat.st_mtime)
                    ).days,
                }

                # Try to read metadata from backup
                try:
                    with zipfile.ZipFile(backup_file, "r") as zipf:
                        if "backup_metadata.json" in zipf.namelist():
                            with zipf.open("backup_metadata.json") as f:
                                metadata = json.load(f)
                                backup_info["metadata"] = metadata.get("metadata", {})
                except:
                    pass

                backups.append(backup_info)

            except Exception as e:
                logger.warning(f"⚠️ Could not read backup info for {backup_file}: {e}")

        return backups

    async def verify_backup(self, backup_file: str) -> Dict[str, Any]:
        """Verify the integrity of a backup file."""

        backup_path = Path(backup_file)
        if not backup_path.exists():
            return {"status": "failed", "error": "Backup file not found"}

        verification_info = {
            "timestamp": datetime.datetime.now().isoformat(),
            "backup_file": backup_file,
            "status": "started",
            "checks": [],
        }

        try:
            logger.info(f"🔍 Verifying backup: {backup_file}")

            # Check if it's a valid ZIP file
            try:
                with zipfile.ZipFile(backup_path, "r") as zipf:
                    # Test ZIP integrity
                    bad_files = zipf.testzip()
                    if bad_files:
                        verification_info["checks"].append(
                            {
                                "check": "zip_integrity",
                                "status": "failed",
                                "error": f"Corrupt files: {bad_files}",
                            }
                        )
                    else:
                        verification_info["checks"].append(
                            {"check": "zip_integrity", "status": "passed"}
                        )

                    # Check for required files
                    required_files = ["backup_metadata.json"]
                    for required_file in required_files:
                        if required_file in zipf.namelist():
                            verification_info["checks"].append(
                                {
                                    "check": f"required_file_{required_file}",
                                    "status": "passed",
                                }
                            )
                        else:
                            verification_info["checks"].append(
                                {
                                    "check": f"required_file_{required_file}",
                                    "status": "failed",
                                    "error": "File missing",
                                }
                            )

                    # Verify metadata
                    if "backup_metadata.json" in zipf.namelist():
                        with zipf.open("backup_metadata.json") as f:
                            metadata = json.load(f)

                            # Check metadata structure
                            if "files" in metadata and "metadata" in metadata:
                                verification_info["checks"].append(
                                    {"check": "metadata_structure", "status": "passed"}
                                )
                            else:
                                verification_info["checks"].append(
                                    {
                                        "check": "metadata_structure",
                                        "status": "failed",
                                        "error": "Invalid metadata structure",
                                    }
                                )

            except zipfile.BadZipFile:
                verification_info["checks"].append(
                    {
                        "check": "zip_format",
                        "status": "failed",
                        "error": "Not a valid ZIP file",
                    }
                )

            # Determine overall status
            failed_checks = [
                c for c in verification_info["checks"] if c["status"] == "failed"
            ]
            if failed_checks:
                verification_info["status"] = "failed"
                verification_info["failed_checks"] = len(failed_checks)
            else:
                verification_info["status"] = "passed"

            logger.info(f"✅ Backup verification completed")
            logger.info(f"   Status: {verification_info['status']}")
            logger.info(
                f"   Checks passed: {len([c for c in verification_info['checks'] if c['status'] == 'passed'])}"
            )

        except Exception as e:
            verification_info["status"] = "failed"
            verification_info["error"] = str(e)
            logger.error(f"❌ Backup verification failed: {e}")

        return verification_info


async def main():
    """Main backup management function."""

    print("🔒 UATP Database Backup and Recovery System")
    print("=" * 50)

    backup_manager = DatabaseBackupManager()

    # Create backup
    print("\n📦 Creating database backup...")
    backup_result = await backup_manager.create_sqlite_backup()

    if backup_result["status"] == "completed":
        print(f"✅ Backup created successfully: {backup_result['backup_file']}")
        print(f"   Size: {backup_result['backup_size'] / 1024 / 1024:.1f} MB")
        print(f"   Files: {len(backup_result['files'])}")

        # Verify backup
        print("\n🔍 Verifying backup...")
        verification_result = await backup_manager.verify_backup(
            backup_result["backup_file"]
        )

        if verification_result["status"] == "passed":
            print("✅ Backup verification passed")
        else:
            print(
                f"❌ Backup verification failed: {verification_result.get('error', 'Unknown error')}"
            )

    else:
        print(f"❌ Backup failed: {backup_result.get('error', 'Unknown error')}")

    # List all backups
    print("\n📋 Available backups:")
    backups = backup_manager.list_backups()

    if backups:
        for backup in backups[-5:]:  # Show last 5 backups
            print(
                f"   • {backup['filename']} ({backup['size'] / 1024 / 1024:.1f} MB, {backup['age_days']} days old)"
            )
    else:
        print("   No backups found")

    # Cleanup old backups
    print("\n🗑️ Cleaning up old backups...")
    cleanup_result = backup_manager.cleanup_old_backups()

    if cleanup_result["status"] == "completed":
        print(
            f"✅ Cleanup completed: {len(cleanup_result['deleted_files'])} files deleted"
        )
    else:
        print(f"❌ Cleanup failed: {cleanup_result.get('error', 'Unknown error')}")

    print("\n✅ Database backup and recovery system ready!")
    print("   Use this script to create automated backups and recovery procedures")


if __name__ == "__main__":
    asyncio.run(main())
