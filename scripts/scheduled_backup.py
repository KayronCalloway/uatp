#!/usr/bin/env python3
"""
Scheduled Database Backup System
================================

This script provides automated scheduled backups for the UATP database
with configurable intervals and retention policies.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from scripts.database_backup import DatabaseBackupManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("backup_scheduler.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class BackupScheduler:
    """Scheduler for automated database backups."""

    def __init__(self, config_file: str = "backup_config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
        self.backup_manager = DatabaseBackupManager(
            self.config.get("backup_dir", "./backups")
        )
        self.running = False

        logger.info(" Backup Scheduler initialized")
        logger.info(
            f"   Backup interval: {self.config.get('backup_interval_hours', 24)} hours"
        )
        logger.info(f"   Retention days: {self.config.get('retention_days', 30)}")

    def load_config(self) -> dict:
        """Load backup configuration from file."""
        default_config = {
            "backup_interval_hours": 24,
            "retention_days": 30,
            "backup_dir": "./backups",
            "max_backup_attempts": 3,
            "backup_on_startup": True,
            "verify_backups": True,
            "cleanup_on_startup": True,
        }

        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    config = json.load(f)
                    # Merge with defaults
                    default_config.update(config)
                    logger.info(f" Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.warning(
                    f"[WARN] Could not load config file: {e}, using defaults"
                )

        return default_config

    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f" Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"[ERROR] Could not save config file: {e}")

    async def create_scheduled_backup(self) -> dict:
        """Create a scheduled backup with retry logic."""

        backup_result = {"status": "failed", "attempts": 0}
        max_attempts = self.config.get("max_backup_attempts", 3)

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f" Creating backup (attempt {attempt}/{max_attempts})")
                backup_result = await self.backup_manager.create_sqlite_backup()
                backup_result["attempts"] = attempt

                if backup_result["status"] == "completed":
                    logger.info("[OK] Scheduled backup completed successfully")

                    # Verify backup if enabled
                    if self.config.get("verify_backups", True):
                        verification_result = await self.backup_manager.verify_backup(
                            backup_result["backup_file"]
                        )
                        backup_result["verification"] = verification_result

                        if verification_result["status"] == "passed":
                            logger.info("[OK] Backup verification passed")
                        else:
                            logger.warning("[WARN] Backup verification failed")

                    break

                else:
                    logger.warning(
                        f"[WARN] Backup attempt {attempt} failed: {backup_result.get('error', 'Unknown error')}"
                    )
                    if attempt < max_attempts:
                        await asyncio.sleep(60)  # Wait 1 minute before retry

            except Exception as e:
                logger.error(
                    f"[ERROR] Backup attempt {attempt} failed with exception: {e}"
                )
                if attempt < max_attempts:
                    await asyncio.sleep(60)

        return backup_result

    async def run_scheduled_backups(self):
        """Run the backup scheduler."""

        self.running = True
        logger.info(" Starting backup scheduler")

        # Initial cleanup if enabled
        if self.config.get("cleanup_on_startup", True):
            logger.info("️ Running initial cleanup...")
            cleanup_result = self.backup_manager.cleanup_old_backups()
            if cleanup_result["status"] == "completed":
                logger.info(
                    f"[OK] Initial cleanup completed: {len(cleanup_result['deleted_files'])} files deleted"
                )

        # Initial backup if enabled
        if self.config.get("backup_on_startup", True):
            logger.info(" Creating initial backup...")
            await self.create_scheduled_backup()

        # Calculate next backup time
        backup_interval = timedelta(hours=self.config.get("backup_interval_hours", 24))
        next_backup = datetime.now() + backup_interval

        logger.info(
            f" Next backup scheduled for: {next_backup.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        try:
            while self.running:
                now = datetime.now()

                if now >= next_backup:
                    logger.info(" Backup time reached, creating backup...")

                    # Create backup
                    backup_result = await self.create_scheduled_backup()

                    # Log backup result
                    if backup_result["status"] == "completed":
                        logger.info(
                            f"[OK] Scheduled backup completed: {backup_result['backup_file']}"
                        )
                    else:
                        logger.error(
                            f"[ERROR] Scheduled backup failed: {backup_result.get('error', 'Unknown error')}"
                        )

                    # Schedule next backup
                    next_backup = now + backup_interval
                    logger.info(
                        f" Next backup scheduled for: {next_backup.strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                    # Cleanup old backups
                    cleanup_result = self.backup_manager.cleanup_old_backups()
                    if cleanup_result["status"] == "completed":
                        logger.info(
                            f"️ Cleanup completed: {len(cleanup_result['deleted_files'])} files deleted"
                        )

                # Check every minute
                await asyncio.sleep(60)

        except KeyboardInterrupt:
            logger.info(" Backup scheduler stopped by user")
        except Exception as e:
            logger.error(f"[ERROR] Backup scheduler error: {e}")
        finally:
            self.running = False
            logger.info(" Backup scheduler stopped")

    def stop(self):
        """Stop the backup scheduler."""
        self.running = False
        logger.info(" Backup scheduler stop requested")


async def main():
    """Main scheduled backup function."""

    print(" UATP Scheduled Backup System")
    print("=" * 40)

    scheduler = BackupScheduler()

    try:
        await scheduler.run_scheduled_backups()
    except KeyboardInterrupt:
        print("\n Backup scheduler stopped by user")
    except Exception as e:
        print(f"[ERROR] Scheduler error: {e}")
        logger.error(f"Scheduler error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
